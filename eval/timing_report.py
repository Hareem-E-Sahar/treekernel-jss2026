"""Summarise kernel timing runs and predict the cost of the full retrieval run
(100 queries x every other true positive) from the real tree sizes.

usage: timing_report.py <results/timing> <data/trees> <data/pools/queries.tsv> <threads_speedup_file?>

For each run file <variant>_<kernel>.tsv (one row per evaluated pair):
  * sampled per-pair CPU time (mean / median / p99) and the observed parallel speed-up
  * a size model: log(time) = a + b*log(nodes_q * nodes_c), least squares, fitted on the sample
  * predicted full-run wall time = sum of modelled times over all real pairs / speed-up
  * the same prediction if trees above a node cap were excluded from the corpus
"""
import csv
import math
import re
import sys
from collections import defaultdict

timing_dir, trees_dir, queries_path = sys.argv[1:4]
csv.field_size_limit(10**9)

# Wall-clock throughput and mean CPU per eval from summary.log -> parallel speed-up
summary = open(f"{timing_dir}/summary.log").read()
speed = {}
for m in re.finditer(r"\[(\w)\] kernel=(\w+).*?\n.*?completed (\d+)(.*?)\n.*?mean per-evaluation CPU time ([\d.]+) ms; "
                     r"throughput (\d+) evals/s \(wall ([\d.]+)s\)", summary):
    v, k, done, cut, ms, tput, wall = m.groups()
    speed[(v, k)] = dict(completed=int(done), cut="budget" in cut, cpu_ms=float(ms),
                         tput=float(tput), speedup=float(tput) * float(ms) / 1000)

queries = [int(l.split("\t")[0]) for l in open(queries_path).read().splitlines()[1:]]
sizes = {}
for v in "ABCD":
    sizes[v] = {}
    with open(f"{trees_dir}/{v}.tsv") as f:
        next(f)
        for line in f:
            i, n = line.split("\t", 2)[:2]
            sizes[v][int(i)] = int(n)

def fit(xs, ys):
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs); sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    b = sxy / sxx
    a = my - b * mx
    resid = [y - (a + b * x) for x, y in zip(xs, ys)]
    s2 = sum(r * r for r in resid) / (n - 2)
    return a, b, s2

def q(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))]

CAPS = (None, 2000, 1000, 500)
print("variant kernel  pairs   cpu ms/pair: mean  median    p99 | speed-up | model slope | "
      "full run (1.48M evals) predicted wall minutes: no cap / cap 2000 / 1000 / 500 nodes "
      "[corpus kept]")
for v in "CDBA":
    for k in ("STK", "SSTK", "PTK"):
        path = f"{timing_dir}/{v}_{k}.tsv"
        try:
            rows = list(csv.DictReader(open(path), delimiter="\t"))
        except FileNotFoundError:
            continue
        if not rows:
            continue
        ms = [int(r["nanos"]) / 1e6 for r in rows]
        xs = [math.log(int(r["query_nodes"]) * int(r["candidate_nodes"])) for r in rows]
        ys = [math.log(max(t, 1e-4)) for t in ms]
        a, b, s2 = fit(xs, ys)
        sp = speed.get((v, k), {}).get("speedup", 8.0)
        preds = []
        for cap in CAPS:
            keep = {i: n for i, n in sizes[v].items() if cap is None or n <= cap}
            qs = [sizes[v][x] for x in queries if x in keep]
            # E[exp(a + b log(x) + eps)] = exp(a + s2/2) * x^b   (lognormal correction).
            # (nq*nc)^b = nq^b * nc^b, so the sum over all pairs factorises.
            total_ms = (math.exp(a + s2 / 2) * sum(nq ** b for nq in qs)
                        * sum(nc ** b for nc in keep.values()))
            # subtract self-pairs approximately (negligible) and convert to wall minutes
            preds.append((total_ms / sp / 60000, len(keep)))
        cut = " (budget hit)" if speed.get((v, k), {}).get("cut") else ""
        print(f"{v:7s} {k:5s} {len(rows):6d} {sum(ms)/len(ms):17.3f} {q(ms,.5):7.3f} {q(ms,.99):7.1f} | "
              f"{sp:8.1f} | {b:11.2f} | " +
              " / ".join(f"{p:8.1f} [{n}]" for p, n in preds) + cut)
