"""Fusion with and without tuning W, next to the hybrid, on the 10 replicate sets (corpus with false positives).

usage: .venv/bin/python exp_v2/eval/fusion_untuned.py   (after exp_v2/scripts/run_fusion_untuned.sh and run_hybrid.sh)
  -> exp_v2/results/fusion_untuned/{values,compare}.tsv, tables.md

Methods per RQ: the tree kernel fused for that RQ (PTK for RQ1, STK for RQ2) alone; BM25 and CodeBERT ft alone; the
weighted sums at the tuned W and at W = 0.5; RRF; and the hybrid (BM25 top k re-ranked by the same kernel, k = 100,
200). RQ1: MAP, mean over the five clone types; RQ2: functional MAP. Per seed mean ± SD; pooled distinct queries, paired
bootstrap over functionalities (2,000 resamples, seed 20261026) for the differences.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FP, U, H = (ROOT / "exp_v2/results" / x for x in ("fp", "fusion_untuned", "hybrid"))
TYPES = ["T1", "T2", "VST3", "ST3", "MT3"]
SEEDS = sorted((p.name for p in (FP / "replicates").glob("seed*")) if (FP / "replicates").exists() else
               (p.name for p in FP.glob("seed*")), key=lambda s: int(s[4:]))
W = {l.split()[0]: l.split()[3] for l in open(FP / "fusion_jobs.txt") if l.strip()}
OTHER = {"bm25": "BM25", "codebert_ft": "CodeBERT ft"}


def methods(rq, k):
    """(label, path of the run's eval for a seed)"""
    m = [(k, lambda s: FP / s / f"D_{k}"), ("BM25", lambda s: FP / s / "bm25"), ("CodeBERT ft", lambda s: FP / s / "codebert_ft")]
    for o in ("bm25", "codebert_ft"):
        name = f"{rq}_{k}_{o}"
        m += [(f"{k}+{OTHER[o]} wsum, tuned W={float(W[name]):.1f}", lambda s, n=name: FP / s / f"{n}_wsum"),
              (f"{k}+{OTHER[o]} wsum, W=0.5 (untuned)", lambda s, n=name: U / s / f"{n}_wsum_w0.5"),
              (f"{k}+{OTHER[o]} RRF (no parameter)", lambda s, n=name: FP / s / f"{n}_rrf")]
    m += [(f"BM25→{k} hybrid, k={K}", lambda s, K=K: H / "replicates" / s / f"hybrid_{k}_k{K}") for K in (100, 200)]
    return m


def load(path, types):
    v, cl = defaultdict(dict), {}
    for r in csv.DictReader(open(path / "eval/per_query.tsv"), delimiter="\t"):
        if r["type"] in types:
            v[r["type"]][r["function_id"]] = float(r["AP"])
            cl[r["function_id"]] = min(int(x) for x in r["functionality_ids"].split(","))
    return v, cl


RQS = [("RQ1 (MAP, mean over the five types)", "rq1", "PTK", TYPES), ("RQ2 (functional MAP)", "rq2", "STK", ["functional"])]
rows, cmp_rows = [], []
for title, rq, k, types in RQS:
    ms = methods(rq, k)
    per_seed, pooled, cl = defaultdict(list), defaultdict(lambda: defaultdict(dict)), {}
    for lab, f in ms:
        for s in SEEDS:
            v, c = load(f(s), types)
            cl.update(c)
            per_seed[lab].append(np.mean([np.mean(list(v[t].values())) for t in types]))
            for t in types:
                pooled[lab][t].update(v[t])
    for lab, _ in ms:
        rows.append((title, lab, np.mean(per_seed[lab]), np.std(per_seed[lab], ddof=1)))
    C = sorted(set(cl.values()))
    ix = {c: i for i, c in enumerate(C)}
    Wt = np.random.default_rng(20261026).multinomial(len(C), np.full(len(C), 1 / len(C)), size=2000).astype(float)

    def diff(a, b):
        est, bs = 0.0, np.zeros(len(Wt))
        for t in types:
            S, N = np.zeros(len(C)), np.zeros(len(C))
            for q, x in pooled[a][t].items():
                S[ix[cl[q]]] += x - pooled[b][t][q]
                N[ix[cl[q]]] += 1
            est += S.sum() / N.sum() / len(types)
            bs += (Wt @ S) / (Wt @ N) / len(types)
        lo, hi = np.percentile(bs, [2.5, 97.5])
        return est, lo, hi

    labs = [l for l, _ in ms]
    for o in ("BM25", "CodeBERT ft"):
        tuned = next(l for l in labs if l.startswith(f"{k}+{o} wsum, tuned"))
        untuned = next(l for l in labs if l.startswith(f"{k}+{o} wsum, W=0.5"))
        for a, b in ((untuned, tuned), (untuned, k), (untuned, o), (tuned, k), (tuned, o)):
            cmp_rows.append((title, a, b, *diff(a, b)))
    for K in (100, 200):
        hy = f"BM25→{k} hybrid, k={K}"
        best_fusion = next(l for l in labs if l.startswith(f"{k}+BM25 wsum, tuned"))
        for b in (k, "BM25", best_fusion):
            cmp_rows.append((title, hy, b, *diff(hy, b)))

with open(U / "values.tsv", "w") as o:
    o.write("rq\tmethod\tmean\tsd\n")
    o.writelines(f"{a}\t{b}\t{c:.4f}\t{d:.4f}\n" for a, b, c, d in rows)
with open(U / "compare.tsv", "w") as o:
    o.write("rq\ta\tb\tdiff\tci_low\tci_high\n")
    o.writelines(f"{a}\t{b}\t{c}\t{d:.4f}\t{e:.4f}\t{f:.4f}\n" for a, b, c, d, e, f in cmp_rows)
T = {r["step"]: r for r in csv.DictReader(open(H / "timing.tsv"), delimiter="\t")}
L = ["# Fusion with and without tuning W, and the hybrid (10 replicate sets, corpus with false positives)", ""]
for title, *_ in RQS:
    L += [f"## {title}", "", "| Method | mean ± SD over the 10 seeds |", "|---|---|"]
    L += [f"| {b} | {c:.3f} ± {d:.3f} |" for a, b, c, d in rows if a == title]
    L += ["", "| A | B | A − B | 95% CI |", "|---|---|---|---|"]
    L += [f"| {b} | {c} | {d:+.3f}{' *' if e > 0 or f < 0 else ''} | {e:+.3f} to {f:+.3f} |" for a, b, c, d, e, f in cmp_rows if a == title]
    L.append("")
L += ["## Cost per query (exp_v2/results/hybrid/timing.tsv)", "",
      "| Step | mean ms |", "|---|---|"] + [f"| {s} | {float(r['mean_ms']):,.0f} |" for s, r in T.items()]
(U / "tables.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
