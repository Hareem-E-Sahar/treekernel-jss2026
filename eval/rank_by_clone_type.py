"""Where does the kernel rank each true clone, broken down by BCB clone type?

usage: rank_by_clone_type.py <query_clone_types.tsv> NAME:run.tsv:self.tsv [...]
For every query, candidates are ranked by normalised kernel score. For each true clone of
the query (from the BCB clones table) we record its rank, and summarise by clone type.
"""
import bisect
import csv
import math
import sys
from collections import defaultdict
from statistics import median

types_path = sys.argv[1]
ctype = {}
for r in csv.DictReader(open(types_path), delimiter="\t"):
    ctype.setdefault((int(r["query_id"]), int(r["other_id"])), r["clone_type"])
ORDER = ["T1", "T2", "VST3", "ST3", "MT3", "WT3/T4"]

for spec in sys.argv[2:]:
    name, run_path, self_path = spec.split(":")
    selfk = {int(r["function_id"]): float(r["self_kernel"]) for r in csv.DictReader(open(self_path), delimiter="\t")}
    scores = defaultdict(list)
    with open(run_path) as f:
        next(f)
        for line in f:
            q, c, _, _, _, v = line.rstrip("\n").split("\t")
            q, c = int(q), int(c)
            scores[q].append((float(v) / math.sqrt(selfk[q] * selfk[c]), c))
    by_type = defaultdict(list)       # (rank percentile, in top R, in top 10, score)
    nonrel_scores = []
    for q, cand in scores.items():
        cand.sort(key=lambda x: (-x[0], x[1]))
        R = sum(1 for _, c in cand if (q, c) in ctype)
        for rank, (s, c) in enumerate(cand, 1):
            t = ctype.get((q, c))
            if t is None:
                if rank % 7 == 0:
                    nonrel_scores.append(s)
                continue
            by_type[t].append((rank / len(cand), rank <= R, rank <= 10, s))
    print(f"\n== {name}: where true clones are ranked (14,680 candidates per query)")
    print(f"{'clone type':10s} {'pairs':>7s} {'median score':>13s} {'median rank (top %)':>20s} {'in top R':>9s} {'in top 10':>10s}")
    for t in ORDER:
        v = by_type.get(t, [])
        if not v:
            continue
        print(f"{t:10s} {len(v):7d} {median(x[3] for x in v):13.3f} {100*median(x[0] for x in v):19.1f}% "
              f"{100*sum(x[1] for x in v)/len(v):8.1f}% {100*sum(x[2] for x in v)/len(v):9.2f}%")
    print(f"{'not a clone':10s} {len(nonrel_scores):7d} {median(nonrel_scores):13.3f}   (1-in-7 sample of non-relevant candidates)")
