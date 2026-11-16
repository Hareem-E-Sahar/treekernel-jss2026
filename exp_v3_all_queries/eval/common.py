"""Shared definitions for the exp_v3_all_queries analyses (revision_plan.md).

- Runs and labels: kernels from exp_v3_all_queries/results/full, BM25, CodeBERT and the hybrids from
  exp_v2/results/hybrid/full (evaluated on the same 14,587 eligible queries).
- Groups (R2-C4): LOC quartiles of the eligible queries and McCabe bins 1, 2-3, 4-5, 6-10, >10.
- Inference (R2-C5, revision_plan.md): only the tested comparisons get an interval. Paired bootstrap over
  functionalities (a query in several functionalities belongs to its lowest functionality id, as in
  exp_v2/eval/hybrid.py), B = 10,000, one set of resampling weights for every statistic. Tested = MAP, RQ1 per clone
  type and the mean of the types, RQ2 and RQ4 per measure: 9 comparisons per family. Bonferroni: the percentile
  CI at level 1 - 0.05 / m; significant when it excludes 0. The matching p-value (2 x the smaller share of resampled
  differences on either side of 0, times m) is kept for the response letter. Everything else is a plain value
  (point estimate over all eligible queries). Effect size: paired Vargha-Delaney A12 (share of queries where A beats B
  plus half the ties).
"""
import csv
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
V3 = ROOT / "exp_v3_all_queries"
RES = V3 / "results"
TYPES = ["T1", "T2", "VST3", "ST3", "MT3"]
MEASURES = TYPES + ["mean5", "functional"]
METRICS = {"nP@5": "nP@5", "nP@10": "nP@10", "MRR": "RR", "MAP": "AP"}
KERNELS = ["STK", "SSTK", "PTK"]
BASELINES = ["bm25", "codebert_zs", "codebert_ft"]
HYB = [f"hybrid_{k}_k100" for k in KERNELS]   # the hybrid: BM25's top 100 re-ranked by the kernel
LABEL = {"bm25": "BM25", "codebert_zs": "CodeBERT zs", "codebert_ft": "CodeBERT ft",
         **{f"D_{k}": k for k in KERNELS}, **{h: f"{h.split('_')[1]}-Hybrid" for h in HYB}}
METHODS = [f"D_{k}" for k in KERNELS] + BASELINES
BOOT = 10000
SEED = 20261104

LOC_EDGES = (13, 21, 35)           # quartiles of the eligible queries' LOC: Q1 <= 13, Q2 14-21, Q3 22-35, Q4 >= 36
LOC_LABELS = ["Q1 (3–13)", "Q2 (14–21)", "Q3 (22–35)", "Q4 (36–433)"]
CC_BINS = [(1, 1), (2, 3), (4, 5), (6, 10), (11, 10 ** 9)]
CC_LABELS = ["1", "2–3", "4–5", "6–10", ">10"]


def eval_dir(run, setting="default"):
    """per_query.tsv directory of a run: default = the main evaluation; t2 / no_fp = label-noise sensitivity."""
    if setting != "default":
        return RES / "noise" / setting / run / "eval"
    if run.startswith("D_"):
        return RES / "full" / run / "eval"
    return ROOT / "exp_v2/results/hybrid/full" / run / "eval"


def load(run, setting="default", cols=METRICS):
    """measure -> metric -> {query: value}; query -> cluster (lowest functionality id)."""
    v, cl = defaultdict(lambda: defaultdict(dict)), {}
    for r in csv.DictReader(open(eval_dir(run, setting) / "per_query.tsv"), delimiter="\t"):
        cl[r["function_id"]] = min(int(x) for x in r["functionality_ids"].split(","))
        for m, c in cols.items():
            v[r["type"]][m][r["function_id"]] = float(r[c])
    return v, cl


def query_attributes():
    """query -> dict(loc, cc, loc_group, cc_group) for the eligible queries (cc_group None if McCabe unavailable)."""
    out = {}
    for r in csv.DictReader(open(ROOT / "exp_v2/data/size_complexity.tsv"), delimiter="\t"):
        loc = int(r["loc"])
        cc = int(r["cc"]) if r["cc_status"] == "ok" else None
        lg = sum(loc > e for e in LOC_EDGES)
        cg = None if cc is None else next(i for i, (a, b) in enumerate(CC_BINS) if a <= cc <= b)
        out[r["function_id"]] = dict(loc=loc, cc=cc, loc_group=lg, cc_group=cg)
    return out


class Boot:
    """Functionality bootstrap; every statistic uses the same weights, so differences are paired."""

    def __init__(self, clusters, seed=SEED, B=BOOT):
        self.cl = sorted(set(clusters.values()))
        self.ix = {c: i for i, c in enumerate(self.cl)}
        self.of = clusters
        rng = np.random.default_rng(seed)
        self.W = rng.multinomial(len(self.cl), np.full(len(self.cl), 1 / len(self.cl)), size=B).astype(float)

    def mean(self, vals):
        """{query: value} -> (estimate, replicates)."""
        S, N = np.zeros(len(self.cl)), np.zeros(len(self.cl))
        for q, x in vals.items():
            S[self.ix[self.of[q]]] += x
            N[self.ix[self.of[q]]] += 1
        with np.errstate(invalid="ignore", divide="ignore"):
            return S.sum() / N.sum(), (self.W @ S) / (self.W @ N)

    def weights(self, queries):
        """B x len(queries) resampling weight of each query."""
        return self.W[:, [self.ix[self.of[q]] for q in queries]]


def bonferroni(est, reps, m, alpha=0.05):
    """Bonferroni over m tests: percentile CI at level 1 - alpha / m and the matching adjusted p
    (2 x the smaller share of replicates on either side of 0, times m)."""
    reps = reps[np.isfinite(reps)]
    a = alpha / m
    lo, hi = np.percentile(reps, [100 * a / 2, 100 * (1 - a / 2)])
    p = 2 * min((reps <= 0).mean(), (reps >= 0).mean())
    return dict(est=float(est), lo=float(lo), hi=float(hi), level=1 - a, p_adj=float(min(1.0, m * p)))


def _diffs(va, metric, measure, vb, subset):
    types = TYPES if measure == "mean5" else [measure]
    for t in types:
        a = va[t][metric]
        qs = [q for q in a if subset is None or q in subset]
        yield {q: a[q] - vb[t][metric][q] for q in qs} if vb is not None else {q: a[q] for q in qs}


def point(va, metric, measure, vb=None, subset=None):
    """Mean of A (or of A - B) over all eligible queries; mean5 = mean of the five types' means."""
    vals = [np.mean(list(d.values())) for d in _diffs(va, metric, measure, vb, subset)]
    return float(np.mean(vals))


def boot_diff(boot, va, vb, metric, measure):
    """(estimate, replicates) of the paired difference A - B; mean5 = mean of the types (resampled jointly)."""
    types = TYPES if measure == "mean5" else [measure]
    est, reps = 0.0, np.zeros(boot.W.shape[0])
    for d in _diffs(va, metric, measure, vb, None):
        e, r = boot.mean(d)
        est += e / len(types)
        reps += r / len(types)
    return est, reps


def a12(va, vb, metric, measure, subset=None, tol=1e-9):
    """Paired Vargha-Delaney A12: P(A > B) + P(A = B) / 2 over queries; mean5 = mean over the five types."""
    types = TYPES if measure == "mean5" else [measure]
    vals = []
    for t in types:
        a, b = va[t][metric], vb[t][metric]
        d = np.array([a[q] - b[q] for q in a if subset is None or q in subset])
        vals.append(((d > tol).sum() + 0.5 * (np.abs(d) <= tol).sum()) / len(d))
    return float(np.mean(vals))


def a12_label(a):
    """Vargha-Delaney label of A12 as printed (two decimals), so equal printed values get equal labels."""
    x = abs(round(float(f"{a:.2f}") * 100) - 50)    # |A12 - 0.5| in hundredths, integer to avoid float edges
    return "negligible" if x < 6 else "small" if x < 14 else "medium" if x < 21 else "large"


def fmt_p(p):
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def write_tsv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as o:
        o.write("\t".join(header) + "\n")
        for r in rows:
            o.write("\t".join(str(x) for x in r) + "\n")
