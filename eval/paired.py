"""Paired bootstrap comparisons between evaluated runs (same evaluation queries).

Used by eval/rq_tables.py. For one pair of runs and one measure:
  per type   T1 ... MT3: micro MAP over that type's queries; functional: MAP@R
  mean5      mean over the five types of micro MAP; resampled within each type
Difference = A - B on the same resampled queries (2,000 resamples, seed 20261018);
95% percentile CI and the share of resamples in which A > B.
"""
import csv
from collections import defaultdict
from pathlib import Path

import numpy as np

TYPES = ["T1", "T2", "VST3", "ST3", "MT3"]
MEASURES = TYPES + ["mean5", "functional"]
_cache = {}


def per_query(run):
    if run not in _cache:
        d = defaultdict(dict)
        for r in csv.DictReader(open(Path(run) / "eval/per_query.tsv"), delimiter="\t"):
            m = "AP@R" if r["type"] == "functional" else "AP"
            d[r["type"]][r["function_id"]] = float(r[m])
        _cache[run] = d
    return _cache[run]


def compare(run_a, run_b, measure, boot=2000, seed=20261018):
    A, B = per_query(run_a), per_query(run_b)
    types = TYPES if measure == "mean5" else [measure]
    qs = {t: sorted(A[t]) for t in types}
    for t in types:
        assert qs[t] == sorted(B[t]), f"{run_a} vs {run_b}: different {t} queries"
    da = {t: np.array([A[t][q] for q in qs[t]]) for t in types}
    db = {t: np.array([B[t][q] for q in qs[t]]) for t in types}
    rng = np.random.default_rng(seed)
    va = np.mean([da[t].mean() for t in types])
    vb = np.mean([db[t].mean() for t in types])
    diffs = np.zeros(boot)
    for t in types:
        n = len(qs[t])
        idx = rng.integers(0, n, (boot, n))
        diffs += (da[t][idx].mean(1) - db[t][idx].mean(1)) / len(types)
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return va, vb, va - vb, lo, hi, float((diffs > 0).mean())


def row(label_a, run_a, label_b, run_b, measure):
    va, vb, d, lo, hi, share = compare(run_a, run_b, measure)
    sig = "" if lo <= 0 <= hi else " *"
    return f"| {label_a} | {label_b} | {measure} | {va:.3f} | {vb:.3f} | {d:+.3f}{sig} | {lo:+.3f} to {hi:+.3f} | {share:.0%} |"


HEAD = ["| A | B | Measure | A | B | A − B | 95% CI | A > B in |", "|---|---|---|---|---|---|---|---|"]
