"""Aggregate the 10 replicate query sets (scripts/run_replicates.sh; data/pools/replicates/).

usage: .venv/bin/python eval/replicates.py   -> results/replicates/{per_replicate.tsv, tables.md, pooled_compare.tsv}

Two views (decision 2026-10-20):
  1. Across replicates: each replicate scored on its own 100 queries per set; mean, SD and min-max over the
     10 replicates, and per comparison the number of replicates in which A is significantly better / not
     different / significantly worse (paired query bootstrap within the replicate, eval/paired.py).
  2. Pooled, clustered by functionality: the distinct queries of all replicates per set (a query drawn in
     several replicates counts once); paired bootstrap that resamples functionalities, not queries, because
     queries of one functionality are not independent. A query in several functionalities is assigned to its
     lowest functionality id. mean5 resamples within each type. 2,000 resamples, seed 20261020.
Measures: T1..MT3 = MAP (micro), mean5 = mean of the five, functional = MAP@R.
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
import paired  # noqa: E402

R = ROOT / "results/replicates"
TYPES = paired.TYPES
MEASURES = TYPES + ["mean5", "functional"]
SEEDS = sorted((p.name for p in R.glob("seed*")), key=lambda s: int(s[4:]))
METHODS = [("D STK", "D_STK"), ("D SSTK", "D_SSTK"), ("D PTK", "D_PTK"), ("BM25", "bm25"),
           ("CodeBERT zs", "codebert_zs"), ("CodeBERT ft", "codebert_ft"),
           ("PTK+BM25 wsum", "PTK_BM25_wsum"), ("PTK+BM25 RRF", "PTK_BM25_rrf"),
           ("STK+BM25 wsum", "STK_BM25_wsum"), ("STK+BM25 RRF", "STK_BM25_rrf"),
           ("PTK+CodeBERT ft wsum", "PTK_CBft_wsum"), ("PTK+CodeBERT ft RRF", "PTK_CBft_rrf"),
           ("STK+CodeBERT ft wsum", "STK_CBft_wsum"), ("STK+CodeBERT ft RRF", "STK_CBft_rrf")]
NAME = dict(METHODS)
COMPARE = [("D PTK", "BM25", MEASURES), ("D PTK", "CodeBERT ft", MEASURES), ("CodeBERT ft", "BM25", MEASURES),
           ("D STK", "BM25", ["mean5", "functional"]), ("D SSTK", "BM25", ["mean5", "functional"]),
           ("D STK", "CodeBERT ft", ["mean5", "functional"]), ("D SSTK", "CodeBERT ft", ["mean5", "functional"]),
           ("CodeBERT ft", "CodeBERT zs", ["mean5", "functional"]),
           ("PTK+BM25 wsum", "D PTK", ["ST3", "MT3", "mean5"]), ("PTK+BM25 wsum", "BM25", ["ST3", "MT3", "mean5"]),
           ("PTK+CodeBERT ft wsum", "D PTK", ["ST3", "MT3", "mean5"]),
           ("PTK+CodeBERT ft wsum", "CodeBERT ft", ["ST3", "MT3", "mean5"]),
           ("STK+CodeBERT ft wsum", "CodeBERT ft", ["functional"])]


def run(seed, label):
    return str(R / seed / NAME[label])


def value(r, m):
    pq = paired.per_query(r)
    if m == "mean5":
        return float(np.mean([np.mean(list(pq[t].values())) for t in TYPES]))
    return float(np.mean(list(pq[m].values())))


present = [(lab, d) for lab, d in METHODS if all((R / s / d / "eval/per_query.tsv").exists() for s in SEEDS)]
labels = [lab for lab, _ in present]

# ---- view 1: per replicate
vals = {(lab, s, m): value(run(s, lab), m) for lab in labels for s in SEEDS for m in MEASURES}
with open(R / "per_replicate.tsv", "w") as o:
    o.write("method\tseed\t" + "\t".join(MEASURES) + "\n")
    for lab in labels:
        for s in SEEDS:
            o.write(f"{lab}\t{s[4:]}\t" + "\t".join(f"{vals[(lab, s, m)]:.4f}" for m in MEASURES) + "\n")

L = ["# Replication over 10 query sets", "",
     f"Seeds {', '.join(s[4:] for s in SEEDS)} (the user's seeds from the earlier study); each replicate = 100 queries per "
     "clone type + 100 functional queries (`data/pools/replicates/`). Variant D at the tuned settings; fusion at the W "
     "tuned on the tuning queries. MAP per type, mean5 = mean of the five types, functional = MAP@R.", "",
     "## Across replicates: mean ± SD (min–max)", "",
     "| Method | " + " | ".join(MEASURES) + " |", "|---" * (len(MEASURES) + 1) + "|"]
for lab in labels:
    cells = []
    for m in MEASURES:
        v = np.array([vals[(lab, s, m)] for s in SEEDS])
        cells.append(f"{v.mean():.3f} ± {v.std(ddof=1):.3f} ({v.min():.3f}–{v.max():.3f})")
    L.append(f"| {lab} | " + " | ".join(cells) + " |")

L += ["", "## Comparisons per replicate", "",
      "Paired query bootstrap within each replicate (2,000 resamples). Better / n.s. / worse = number of the 10 replicates "
      "in which A is significantly better than B, not significantly different, significantly worse. Mean Δ = mean of A − B "
      "over replicates.", "", "| A | B | Measure | Mean Δ (min–max) | Better / n.s. / worse |", "|---|---|---|---|---|"]
for a, b, ms in COMPARE:
    if a not in labels or b not in labels:
        continue
    for m in ms:
        d, cnt = [], [0, 0, 0]
        for s in SEEDS:
            _, _, diff, lo, hi, _ = paired.compare(run(s, a), run(s, b), m)
            d.append(diff)
            cnt[0 if lo > 0 else 2 if hi < 0 else 1] += 1
        L.append(f"| {a} | {b} | {m} | {np.mean(d):+.3f} ({min(d):+.3f} to {max(d):+.3f}) | {cnt[0]} / {cnt[1]} / {cnt[2]} |")

# ---- view 2: pooled distinct queries, functionality-clustered bootstrap
pool = defaultdict(lambda: defaultdict(dict))    # label -> type -> query -> value
cluster = defaultdict(dict)                      # type -> query -> functionality
for lab in labels:
    for s in SEEDS:
        for r in csv.DictReader(open(Path(run(s, lab)) / "eval/per_query.tsv"), delimiter="\t"):
            t = r["type"]
            v = float(r["AP@R" if t == "functional" else "AP"])
            q = r["function_id"]
            if q in pool[lab][t]:
                assert abs(pool[lab][t][q] - v) < 1e-9, (lab, t, q)   # same run, same query -> same score
            pool[lab][t][q] = v
            cluster[t][q] = min(int(x) for x in r["functionality_ids"].split(","))


def clustered(a, b, m, boot=2000, seed=20261020):
    rng = np.random.default_rng(seed)
    types = TYPES if m == "mean5" else [m]
    va = np.mean([np.mean(list(pool[a][t].values())) for t in types])
    vb = np.mean([np.mean(list(pool[b][t].values())) for t in types])
    diffs = np.zeros(boot)
    for t in types:
        qs = sorted(pool[a][t])
        cl = defaultdict(list)
        for q in qs:
            cl[cluster[t][q]].append(pool[a][t][q] - pool[b][t][q])
        sums = np.array([sum(x) for x in cl.values()])
        ns = np.array([len(x) for x in cl.values()])
        idx = rng.integers(0, len(sums), (boot, len(sums)))
        diffs += sums[idx].sum(1) / ns[idx].sum(1) / len(types)
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return va, vb, lo, hi


nq = {t: len(pool[labels[0]][t]) for t in MEASURES if t != "mean5"}
ncl = {t: len(set(cluster[t].values())) for t in nq}
L += ["", "## Pooled over the replicates, bootstrap over functionalities", "",
      "Distinct queries (functionalities): " + ", ".join(f"{t} {nq[t]} ({ncl[t]})" for t in nq) + ". "
      "Paired bootstrap resampling whole functionalities (2,000 resamples), so queries from the same functionality move "
      "together; * = 95% CI excludes 0.", "",
      "| Method | " + " | ".join(MEASURES) + " |", "|---" * (len(MEASURES) + 1) + "|"]
for lab in labels:
    L.append(f"| {lab} | " + " | ".join(
        f"{np.mean([np.mean(list(pool[lab][t].values())) for t in (TYPES if m == 'mean5' else [m])]):.3f}" for m in MEASURES) + " |")
L += ["", "| A | B | Measure | A | B | A − B | 95% CI (clustered) |", "|---|---|---|---|---|---|---|"]
for a, b, ms in COMPARE:
    if a not in labels or b not in labels:
        continue
    for m in ms:
        va, vb, lo, hi = clustered(a, b, m)
        sig = " *" if lo > 0 or hi < 0 else ""
        L.append(f"| {a} | {b} | {m} | {va:.3f} | {vb:.3f} | {va - vb:+.3f}{sig} | {lo:+.3f} to {hi:+.3f} |")
(R / "tables.md").write_text("\n".join(L) + "\n")

# ---- pooled clustered tests used for the paper's significance marks (paper/make_assets.py)
TESTS = [(k, o, m) for k in ("D STK", "D SSTK", "D PTK", "CodeBERT zs", "CodeBERT ft") for o in ("BM25", "CodeBERT ft")
         for m in MEASURES if k != o]
for fus, comps, ms in (("PTK+BM25", ("D PTK", "BM25"), ["ST3", "MT3", "mean5"]),
                       ("PTK+CodeBERT ft", ("D PTK", "CodeBERT ft"), ["ST3", "MT3", "mean5"]),
                       ("STK+BM25", ("D STK", "BM25"), ["functional"]),
                       ("STK+CodeBERT ft", ("D STK", "CodeBERT ft"), ["functional"])):
    TESTS += [(f"{fus} {how}", c, m) for how in ("wsum", "RRF") for c in comps for m in ms]
with open(R / "pooled_compare.tsv", "w") as o:
    o.write("a\tb\tmeasure\ta_value\tb_value\tdiff\tci_low\tci_high\n")
    for a, b, m in TESTS:
        if a in labels and b in labels:
            va, vb, lo, hi = clustered(a, b, m)
            o.write(f"{a}\t{b}\t{m}\t{va:.4f}\t{vb:.4f}\t{va - vb:.4f}\t{lo:.4f}\t{hi:.4f}\n")
print("\n".join(L))
