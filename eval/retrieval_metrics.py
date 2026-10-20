"""Retrieval metrics for query x candidate kernel score files, plus a query-count
analysis for tuning.

usage: retrieval_metrics.py <data/full_bcb> <out dir> NAME:run.tsv:self.tsv [NAME:run.tsv:self.tsv ...]

Relevance: a candidate is relevant to a query if both are true positives of a common
functionality (checked against the size of the `clones` table below).
Scores are normalised: K(q,c) / sqrt(K(q,q) K(c,c)). Ties are broken by candidate id.

Metrics per query: MAP@R (Musgrave et al. 2020), R-precision, P@1, P@10.
"""
import csv
import math
import random
import sys
from collections import defaultdict
from statistics import mean, stdev

bcb_dir, out_dir = sys.argv[1:3]
runs = [a.split(":") for a in sys.argv[3:]]

tp = defaultdict(set)
for r in csv.DictReader(open(f"{bcb_dir}/tp_functionalities.tsv"), delimiter="\t"):
    tp[int(r["function_id"])].add(int(r["functionality_id"]))

# Sanity check: same-functionality pairs should be exactly the `clones` table.
members = defaultdict(set)
for f, fs in tp.items():
    for x in fs:
        members[x].add(f)
same_func_pairs = set()
for x, ms in members.items():
    ms = sorted(ms)
    for i in range(len(ms)):
        for j in range(i + 1, len(ms)):
            same_func_pairs.add((ms[i], ms[j]))
print(f"same-functionality true-positive pairs: {len(same_func_pairs):,} (clones table: 8,584,153)")
del same_func_pairs


def metrics(ranked_rel, total_rel):
    """ranked_rel: list of 0/1 in rank order; total_rel: relevant items among candidates."""
    R = total_rel
    hits = 0
    s = 0.0
    for i, rel in enumerate(ranked_rel[:R], 1):
        if rel:
            hits += 1
            s += hits / i
    return {
        "MAP@R": s / R,
        "R-prec": sum(ranked_rel[:R]) / R,
        "P@1": float(ranked_rel[0]),
        "P@10": sum(ranked_rel[:10]) / 10,
    }


per_query = {}
for name, run_path, self_path in runs:
    selfk = {int(r["function_id"]): float(r["self_kernel"])
             for r in csv.DictReader(open(self_path), delimiter="\t")}
    scores = defaultdict(list)
    with open(run_path) as f:
        next(f)
        for line in f:
            q, c, _, _, _, v = line.rstrip("\n").split("\t")
            q, c, v = int(q), int(c), float(v)
            scores[q].append((v / math.sqrt(selfk[q] * selfk[c]), c))
    res = {}
    for q, cand in scores.items():
        cand.sort(key=lambda x: (-x[0], x[1]))
        rel = [1 if tp[q] & tp[c] else 0 for _, c in cand]
        total = sum(rel)
        if total == 0:
            continue
        m = metrics(rel, total)
        m["R"] = total
        m["functionalities"] = ",".join(map(str, sorted(tp[q])))
        res[q] = m
    per_query[name] = res
    with open(f"{out_dir}/{name}_per_query.tsv", "w") as o:
        o.write("query_id\tfunctionalities\tR\tMAP@R\tR-prec\tP@1\tP@10\n")
        for q in sorted(res):
            m = res[q]
            o.write(f"{q}\t{m['functionalities']}\t{m['R']}\t{m['MAP@R']:.4f}\t{m['R-prec']:.4f}\t{m['P@1']:.0f}\t{m['P@10']:.2f}\n")

print("\n== retrieval quality (100 queries vs all other non-query true positives)")
print(f"{'config':10s} {'queries':>7s} {'MAP@R':>7s} {'R-prec':>7s} {'P@1':>6s} {'P@10':>6s}   per-query MAP@R sd")
for name, res in per_query.items():
    vals = list(res.values())
    print(f"{name:10s} {len(vals):7d} " + " ".join(f"{mean(v[k] for v in vals):6.3f} " for k in ("MAP@R", "R-prec", "P@1", "P@10"))
          + f"  {stdev(v['MAP@R'] for v in vals):.3f}")

print("\n== how precise is a MAP@R estimate from n queries?  (standard error = sd / sqrt(n))")
for name, res in per_query.items():
    sd = stdev(v["MAP@R"] for v in res.values())
    print(f"{name:10s} " + "  ".join(f"n={n}: ±{sd/math.sqrt(n):.3f}" for n in (10, 25, 50, 100, 200)))

if len(per_query) == 2:
    (n1, r1), (n2, r2) = per_query.items()
    common = sorted(set(r1) & set(r2))
    d = [r1[q]["MAP@R"] - r2[q]["MAP@R"] for q in common]
    md, sdd = mean(d), stdev(d)
    print(f"\n== paired comparison {n1} - {n2} on the same {len(common)} queries")
    print(f"mean MAP@R difference {md:+.3f}, per-query sd of difference {sdd:.3f}, "
          f"{n1} better on {sum(x > 0 for x in d)}, worse on {sum(x < 0 for x in d)}, tied on {sum(x == 0 for x in d)}")
    print("standard error of the difference: " + "  ".join(f"n={n}: ±{sdd/math.sqrt(n):.3f}" for n in (10, 25, 50, 100)))
    rng = random.Random(1)
    print("if tuning used only n of these queries, how often would it pick the same winner as all 100?")
    for n in (5, 10, 20, 30, 50):
        agree = 0
        trials = 2000
        for _ in range(trials):
            sub = rng.sample(d, n)
            agree += (mean(sub) > 0) == (md > 0)
        print(f"  n={n:3d}: {100*agree/trials:5.1f}% of random subsets")
