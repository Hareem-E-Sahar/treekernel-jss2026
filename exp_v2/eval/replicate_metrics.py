"""Per-replicate values and pooled tests for every reported metric (companion to exp_v2/eval/replicates.py, which
covers MAP and MAP@R only).

usage: .venv/bin/python exp_v2/eval/replicate_metrics.py [fp]
  -> exp_v2/results/<setting>/per_replicate_metrics.tsv   method, seed, measure, metric, value (long format)
     exp_v2/results/<setting>/pooled_compare_metrics.tsv  pooled paired test per (A, B, measure, metric)

Metrics (micro average over queries): MAP (AP), MAP@R (AP@R), MRR (RR), nP@5, nP@10 (exp_v2/eval/evaluate.py).
Measures: T1..MT3, mean5 = mean over the five types, functional.
Pooled test: as in replicates.py (distinct queries of all replicates; paired bootstrap resampling functionalities,
2,000 resamples, seed 20261020; a query in several functionalities is assigned to its lowest functionality id).
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SETTING = sys.argv[1] if len(sys.argv) > 1 else "fp"
R = ROOT / "exp_v2/results" / SETTING
TYPES = ["T1", "T2", "VST3", "ST3", "MT3"]
MEASURES = TYPES + ["mean5", "functional"]
METRICS = {"MAP": "AP", "MAP@R": "AP@R", "MRR": "RR", "nP@5": "nP@5", "nP@10": "nP@10"}
SEEDS = sorted((p.name for p in R.glob("seed*")), key=lambda s: int(s[4:]))
OTHER_LAB = {"bm25": "BM25", "codebert_ft": "CodeBERT ft"}
JOBS = [line.split() for line in open(R / "fusion_jobs.txt") if line.strip()]   # name kernel other w
METHODS = [("D STK", "D_STK"), ("D SSTK", "D_SSTK"), ("D PTK", "D_PTK"), ("BM25", "bm25"),
           ("CodeBERT zs", "codebert_zs"), ("CodeBERT ft", "codebert_ft")]
for name, k, other, w in JOBS:
    METHODS += [(f"{k}+{OTHER_LAB[other]} wsum", f"{name}_wsum"), (f"{k}+{OTHER_LAB[other]} RRF", f"{name}_rrf")]

# per-query values: label -> seed -> type -> metric -> {query: value}; pooled: label -> type -> metric -> {query: value}
per = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict))))
pool = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
cluster = defaultdict(dict)
for lab, d in METHODS:
    for s in SEEDS:
        for r in csv.DictReader(open(R / s / d / "eval/per_query.tsv"), delimiter="\t"):
            t, q = r["type"], r["function_id"]
            cluster[t][q] = min(int(x) for x in r["functionality_ids"].split(","))
            for m, col in METRICS.items():
                v = float(r[col])
                per[lab][s][t][m][q] = v
                if q in pool[lab][t][m]:
                    assert abs(pool[lab][t][m][q] - v) < 1e-9, (lab, t, q, m)   # same run, same query -> same value
                pool[lab][t][m][q] = v


def mean_of(d, m, metric):
    types = TYPES if m == "mean5" else [m]
    return float(np.mean([np.mean(list(d[t][metric].values())) for t in types]))


with open(R / "per_replicate_metrics.tsv", "w") as o:
    o.write("method\tseed\tmeasure\tmetric\tvalue\n")
    for lab, _ in METHODS:
        for s in SEEDS:
            for m in MEASURES:
                for metric in METRICS:
                    o.write(f"{lab}\t{s[4:]}\t{m}\t{metric}\t{mean_of(per[lab][s], m, metric):.6f}\n")


def clustered(a, b, m, metric, boot=2000, seed=20261020):
    rng = np.random.default_rng(seed)
    types = TYPES if m == "mean5" else [m]
    diffs = np.zeros(boot)
    for t in types:
        cl = defaultdict(list)
        for q in sorted(pool[a][t][metric]):
            cl[cluster[t][q]].append(pool[a][t][metric][q] - pool[b][t][metric][q])
        sums = np.array([sum(x) for x in cl.values()])
        ns = np.array([len(x) for x in cl.values()])
        idx = rng.integers(0, len(sums), (boot, len(sums)))
        diffs += sums[idx].sum(1) / ns[idx].sum(1) / len(types)
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return mean_of(pool[a], m, metric), mean_of(pool[b], m, metric), lo, hi


# tests behind the paper's marks: each method vs BM25 and vs CodeBERT ft; each fusion vs its two components
TESTS = [(a, b) for a in ("D STK", "D SSTK", "D PTK", "CodeBERT zs", "CodeBERT ft") for b in ("BM25", "CodeBERT ft") if a != b]
for name, k, other, w in JOBS:
    for how in ("wsum", "RRF"):
        lab = f"{k}+{OTHER_LAB[other]} {how}"
        TESTS += [(lab, f"D {k}"), (lab, OTHER_LAB[other])]
with open(R / "pooled_compare_metrics.tsv", "w") as o:
    o.write("a\tb\tmeasure\tmetric\ta_value\tb_value\tdiff\tci_low\tci_high\n")
    for a, b in TESTS:
        for m in MEASURES:
            for metric in METRICS:
                va, vb, lo, hi = clustered(a, b, m, metric)
                o.write(f"{a}\t{b}\t{m}\t{metric}\t{va:.4f}\t{vb:.4f}\t{va - vb:.4f}\t{lo:.4f}\t{hi:.4f}\n")
print(f"{R}/per_replicate_metrics.tsv, pooled_compare_metrics.tsv")
