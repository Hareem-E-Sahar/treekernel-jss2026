"""Aggregate the hybrid (exp_v2/scripts/run_hybrid.sh).

usage: .venv/bin/python exp_v2/eval/hybrid.py
  -> exp_v2/results/hybrid/{full_values,full_compare,replicate_values,replicate_compare,timing}.tsv, tables.md

1. Full query set (every eligible query): each method's value with a 95% CI, and paired differences with 95% CIs;
   bootstrap resampling functionalities (2,000 resamples, seed 20261023; a query in several functionalities is
   assigned to its lowest functionality id; mean5 = mean of the five types, resampled jointly).
2. Replicate sets (10 seeds): hybrids per seed (mean ± SD) next to the full-ranking kernels, BM25 and CodeBERT of
   exp_v2/results/fp; pooled distinct queries, paired test hybrid vs its kernel's full ranking and vs BM25.
3. Cost per query: first stage (Elasticsearch `took` for the top 200), second stage (summed kernel time of the query's
   pairs; k = 100 from the separate timing run if present), and the full-ranking kernel runs (wall time x threads /
   queries, i.e. CPU seconds per query).
Metrics: MAP, MAP@R, MRR, nP@5, nP@10 (micro).
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "exp_v2/results/hybrid"
FP = ROOT / "exp_v2/results/fp"
TYPES = ["T1", "T2", "VST3", "ST3", "MT3"]
MEASURES = TYPES + ["mean5", "functional"]
METRICS = {"MAP": "AP", "MAP@R": "AP@R", "MRR": "RR", "nP@5": "nP@5", "nP@10": "nP@10"}
KERNELS = ["STK", "SSTK", "PTK"]
HYB = [f"hybrid_{k}_k{K}" for k in KERNELS for K in (100, 200)]
FULL_RUNS = ["bm25", "codebert_zs", "codebert_ft"] + HYB
LABEL = {"bm25": "BM25", "codebert_zs": "CodeBERT zs", "codebert_ft": "CodeBERT ft",
         **{f"D_{k}": k for k in KERNELS}, **{h: f"BM25→{h.split('_')[1]} (k={h.split('k')[-1]})" for h in HYB}}
BOOT = 2000


def load(path):
    """type -> metric -> {query: value}; and query -> functionality cluster."""
    v, cl = defaultdict(lambda: defaultdict(dict)), {}
    for r in csv.DictReader(open(path), delimiter="\t"):
        cl[r["function_id"]] = min(int(x) for x in r["functionality_ids"].split(","))
        for m, c in METRICS.items():
            v[r["type"]][m][r["function_id"]] = float(r[c])
    return v, cl


class Boot:
    """Functionality bootstrap with one set of resampling weights shared by every statistic (paired comparisons)."""

    def __init__(self, clusters, seed):
        self.cl = sorted(set(clusters.values()))
        self.ix = {c: i for i, c in enumerate(self.cl)}
        self.of = clusters
        rng = np.random.default_rng(seed)
        self.W = rng.multinomial(len(self.cl), np.full(len(self.cl), 1 / len(self.cl)), size=BOOT).astype(float)

    def mean(self, vals):
        """vals: {query: value} -> point estimate, bootstrap replicates."""
        S, N = np.zeros(len(self.cl)), np.zeros(len(self.cl))
        for q, x in vals.items():
            S[self.ix[self.of[q]]] += x
            N[self.ix[self.of[q]]] += 1
        with np.errstate(invalid="ignore", divide="ignore"):
            return S.sum() / N.sum(), (self.W @ S) / (self.W @ N)

    def stat(self, va, m, measure, vb=None):
        """mean of A (or of A - B) over the measure's types; mean5 averages the types' means."""
        types = TYPES if measure == "mean5" else [measure]
        est, bs = 0.0, np.zeros(BOOT)
        for t in types:
            a = va[t][m]
            d = {q: a[q] - vb[t][m][q] for q in a} if vb is not None else a
            e, b = self.mean(d)
            est += e / len(types)
            bs += b / len(types)
        bs = bs[np.isfinite(bs)]
        return est, *np.percentile(bs, [2.5, 97.5])


# ---- 1. full query set
full, clusters = {}, {}
for r in FULL_RUNS:
    full[r], cl = load(R / "full" / r / "eval/per_query.tsv")
    clusters.update(cl)
B = Boot(clusters, 20261023)
with open(R / "full_values.tsv", "w") as o:
    o.write("method\tmeasure\tmetric\tvalue\tci_low\tci_high\tn_queries\n")
    for r in FULL_RUNS:
        for ms in MEASURES:
            for m in METRICS:
                v, lo, hi = B.stat(full[r], m, ms)
                n = sum(len(full[r][t][m]) for t in (TYPES if ms == "mean5" else [ms]))
                o.write(f"{LABEL[r]}\t{ms}\t{m}\t{v:.4f}\t{lo:.4f}\t{hi:.4f}\t{n}\n")
FULL_PAIRS = [(h, b) for h in HYB for b in ("bm25", "codebert_ft")] + [(f"hybrid_{k}_k200", f"hybrid_{k}_k100") for k in KERNELS] \
    + [("codebert_ft", "bm25")]
with open(R / "full_compare.tsv", "w") as o:
    o.write("a\tb\tmeasure\tmetric\tdiff\tci_low\tci_high\n")
    for a, b in FULL_PAIRS:
        for ms in MEASURES:
            for m in METRICS:
                d, lo, hi = B.stat(full[a], m, ms, full[b])
                o.write(f"{LABEL[a]}\t{LABEL[b]}\t{ms}\t{m}\t{d:.4f}\t{lo:.4f}\t{hi:.4f}\n")

# ---- 2. replicate sets
SEEDS = sorted((p.name for p in (R / "replicates").glob("seed*")), key=lambda s: int(s[4:]))
REP_RUNS = [f"D_{k}" for k in KERNELS] + ["bm25", "codebert_ft"] + HYB
per_seed, pooled, rcl = defaultdict(dict), defaultdict(lambda: defaultdict(lambda: defaultdict(dict))), {}
for s in SEEDS:
    for r in REP_RUNS:
        path = (R / "replicates" / s / r if r.startswith("hybrid") else FP / s / r) / "eval/per_query.tsv"
        v, cl = load(path)
        rcl.update(cl)
        per_seed[r][s] = v
        for t in v:
            for m in v[t]:
                pooled[r][t][m].update(v[t][m])


def seed_value(v, ms, m):
    return float(np.mean([np.mean(list(v[t][m].values())) for t in (TYPES if ms == "mean5" else [ms])]))


with open(R / "replicate_values.tsv", "w") as o:
    o.write("method\tseed\tmeasure\tmetric\tvalue\n")
    for r in REP_RUNS:
        for s in SEEDS:
            for ms in MEASURES:
                for m in METRICS:
                    o.write(f"{LABEL[r]}\t{s[4:]}\t{ms}\t{m}\t{seed_value(per_seed[r][s], ms, m):.6f}\n")
RB = Boot(rcl, 20261023)
REP_PAIRS = [(h, f"D_{h.split('_')[1]}") for h in HYB] + [(h, "bm25") for h in HYB]
with open(R / "replicate_compare.tsv", "w") as o:
    o.write("a\tb\tmeasure\tmetric\tdiff\tci_low\tci_high\n")
    for a, b in REP_PAIRS:
        for ms in MEASURES:
            for m in METRICS:
                d, lo, hi = RB.stat(pooled[a], m, ms, pooled[b])
                o.write(f"{LABEL[a]}\t{LABEL[b]}\t{ms}\t{m}\t{d:.4f}\t{lo:.4f}\t{hi:.4f}\n")

# ---- 3. cost per query
st1 = [float(r["es_took_ms"]) for r in csv.DictReader(open(R / "stage1/timing.tsv"), delimiter="\t")]
rows = [("BM25 top 200 (first stage)", "Elasticsearch took", np.median(st1), np.mean(st1), len(st1))]
for k in KERNELS:
    for K, f in ((200, R / f"pairs/{k}.tsv.timing.tsv"), (100, R / f"pairs_k100/{k}.tsv.timing.tsv")):
        if f.exists():
            ms_ = [int(r["kernel_ns"]) / 1e6 for r in csv.DictReader(open(f), delimiter="\t")]
            rows.append((f"{k} on the top {K} (second stage)", "summed kernel CPU time", np.median(ms_), np.mean(ms_), len(ms_)))
    meta = json.loads((FP / f"runs/D_{k}/meta.json").read_text())
    cpu = meta["wall_seconds"] * meta["threads"] / meta["n_queries"] * 1000
    rows.append((f"{k} full ranking (72,782 methods)", "wall x threads / queries", float("nan"), cpu, meta["n_queries"]))
with open(R / "timing.tsv", "w") as o:
    o.write("step\tmeasure\tmedian_ms\tmean_ms\tqueries\n")
    o.writelines(f"{a}\t{b}\t{c:.1f}\t{d:.1f}\t{n}\n" for a, b, c, d, n in rows)

# ---- tables.md
fv = {(r["method"], r["measure"], r["metric"]): r for r in csv.DictReader(open(R / "full_values.tsv"), delimiter="\t")}
fc = {(r["a"], r["b"], r["measure"], r["metric"]): r for r in csv.DictReader(open(R / "full_compare.tsv"), delimiter="\t")}
L = ["# Hybrid: BM25 top k re-ranked by a tree kernel", "",
     "Corpus with false positives; every eligible query (T1 3,746, T2 998, VST3 1,991, ST3 4,652, MT3 7,722, functional "
     "14,587). Below rank k the BM25 order is kept. 95% CIs: bootstrap over functionalities.", "",
     "## Full query set: value [95% CI]", "",
     "| Method | " + " | ".join(f"{t} MAP" for t in TYPES) + " | mean5 MAP | functional MAP@R |", "|---" * 8 + "|"]
for r in FULL_RUNS:
    cells = [fv[(LABEL[r], ms, "MAP@R" if ms == "functional" else "MAP")] for ms in MEASURES]
    L.append(f"| {LABEL[r]} | " + " | ".join(f"{float(c['value']):.3f} [{float(c['ci_low']):.3f}, {float(c['ci_high']):.3f}]"
                                            for c in cells) + " |")
L += ["", "### Other metrics (mean5 / functional)", "",
      "| Method | mean5 nP@5 | mean5 nP@10 | mean5 MRR | func nP@5 | func nP@10 | func MRR |", "|---" * 7 + "|"]
for r in FULL_RUNS:
    L.append(f"| {LABEL[r]} | " + " | ".join(f"{float(fv[(LABEL[r], ms, m)]['value']):.3f}"
                                            for ms in ("mean5", "functional") for m in ("nP@5", "nP@10", "MRR")) + " |")
L += ["", "## Full query set: differences [95% CI], * = CI excludes 0", "",
      "| A | B | " + " | ".join(f"{t}" for t in TYPES) + " | mean5 | functional MAP@R |", "|---" * 9 + "|"]
for a, b in FULL_PAIRS:
    cells = [fc[(LABEL[a], LABEL[b], ms, "MAP@R" if ms == "functional" else "MAP")] for ms in MEASURES]
    L.append(f"| {LABEL[a]} | {LABEL[b]} | " + " | ".join(
        f"{float(c['diff']):+.3f}{' *' if float(c['ci_low']) > 0 or float(c['ci_high']) < 0 else ''}" for c in cells) + " |")
rv = defaultdict(list)
for r in csv.DictReader(open(R / "replicate_values.tsv"), delimiter="\t"):
    rv[(r["method"], r["measure"], r["metric"])].append(float(r["value"]))
rc = {(r["a"], r["b"], r["measure"], r["metric"]): r for r in csv.DictReader(open(R / "replicate_compare.tsv"), delimiter="\t")}
L += ["", "## Replicate sets (10 seeds): mean ± SD", "",
      "| Method | " + " | ".join(f"{t} MAP" for t in TYPES) + " | mean5 MAP | functional MAP@R |", "|---" * 8 + "|"]
for r in REP_RUNS:
    L.append(f"| {LABEL[r]} | " + " | ".join(
        f"{np.mean(v):.3f} ± {np.std(v, ddof=1):.3f}" for ms in MEASURES
        for v in [rv[(LABEL[r], ms, 'MAP@R' if ms == 'functional' else 'MAP')]]) + " |")
L += ["", "Pooled distinct replicate queries, differences [95% CI]:", "",
      "| A | B | " + " | ".join(TYPES) + " | mean5 | functional MAP@R |", "|---" * 9 + "|"]
for a, b in REP_PAIRS:
    cells = [rc[(LABEL[a], LABEL[b], ms, "MAP@R" if ms == "functional" else "MAP")] for ms in MEASURES]
    L.append(f"| {LABEL[a]} | {LABEL[b]} | " + " | ".join(
        f"{float(c['diff']):+.3f}{' *' if float(c['ci_low']) > 0 or float(c['ci_high']) < 0 else ''}" for c in cells) + " |")
L += ["", "## Cost per query", "", "| Step | Measure | Median ms | Mean ms | Queries |", "|---|---|---|---|---|"]
L += [f"| {a} | {b} | {c:.1f} | {d:.1f} | {n:,} |" for a, b, c, d, n in rows]
(R / "tables.md").write_text("\n".join(L) + "\n")
print(f"{R}/tables.md")
