"""Compare several evaluated runs on the same syntactic query set (e.g. variant selection).

usage: compare_runs.py OUT.md NAME=RUN_DIR [NAME=RUN_DIR ...] [--metric AP] [--boot 2000]

Reads RUN_DIR/eval/per_query.tsv (from evaluate.py). Score = mean over the clone types of the
micro-averaged metric (the tuning objective). Confidence intervals: bootstrap over queries,
resampling within each clone type. Differences are paired (same resampled queries).
Names have the form VARIANT_KERNEL; within each kernel the best variant is compared with the others.
"""
import argparse
import csv
from collections import defaultdict
from pathlib import Path

import numpy as np

TYPES = ["T1", "T2", "VST3", "ST3", "MT3"]
ap = argparse.ArgumentParser()
ap.add_argument("out", type=Path)
ap.add_argument("runs", nargs="+")
ap.add_argument("--metric", default="AP")
ap.add_argument("--boot", type=int, default=2000)
ap.add_argument("--seed", type=int, default=20261016)
args = ap.parse_args()

vals = {}            # name -> type -> {query: value}
for spec in args.runs:
    name, path = spec.split("=", 1)
    d = defaultdict(dict)
    for r in csv.DictReader(open(Path(path) / "eval/per_query.tsv"), delimiter="\t"):
        d[r["type"]][r["function_id"]] = float(r[args.metric])
    vals[name] = d
names = list(vals)
queries = {t: sorted(vals[names[0]][t]) for t in TYPES}
for n in names:
    assert all(sorted(vals[n][t]) == queries[t] for t in TYPES), f"{n}: different queries"
M = {n: {t: np.array([vals[n][t][q] for q in queries[t]]) for t in TYPES} for n in names}

rng = np.random.default_rng(args.seed)
samples = [{t: rng.integers(0, len(queries[t]), len(queries[t])) for t in TYPES} for _ in range(args.boot)]


def score(n, idx=None):
    return float(np.mean([M[n][t].mean() if idx is None else M[n][t][idx[t]].mean() for t in TYPES]))


boot = {n: np.array([score(n, s) for s in samples]) for n in names}
lines = [f"# Run comparison ({args.metric}, mean over clone types)", "",
         f"Queries per type: {', '.join(f'{t} {len(queries[t])}' for t in TYPES)}. "
         f"95% CI: bootstrap over queries within type ({args.boot} resamples).", "",
         "| Run | " + " | ".join(TYPES) + f" | **mean** | 95% CI |", "|---" * (len(TYPES) + 3) + "|"]
for n in names:
    lo, hi = np.percentile(boot[n], [2.5, 97.5])
    lines.append(f"| {n} | " + " | ".join(f"{M[n][t].mean():.3f}" for t in TYPES)
                 + f" | **{score(n):.3f}** | {lo:.3f}–{hi:.3f} |")

kernels = defaultdict(list)
for n in names:
    kernels[n.split("_", 1)[1] if "_" in n else n].append(n)
lines += ["", "## Best variant per kernel vs the others (paired)", "",
          "| Kernel | Best | Other | Difference | 95% CI | Share of resamples where best wins |", "|---|---|---|---|---|---|"]
for k, ns in kernels.items():
    best = max(ns, key=score)
    for n in ns:
        if n == best:
            continue
        diff = boot[best] - boot[n]
        lo, hi = np.percentile(diff, [2.5, 97.5])
        lines.append(f"| {k} | {best} | {n} | {score(best) - score(n):+.3f} | {lo:+.3f} to {hi:+.3f} | {(diff > 0).mean():.0%} |")
args.out.write_text("\n".join(lines) + "\n")
print("\n".join(lines))
