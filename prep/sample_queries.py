"""Sample the query sets for the tree-kernel / BM25 experiments (PLAN.md §4.2).

usage: sample_queries.py <data/full_bcb> <data/pools> [--seed 20261014]

Writes to <data/pools>:
  tuning.tsv           50 queries, 10 per clone type T1, T2, VST3, ST3, MT3
  syntactic_<T>.tsv    100 queries per clone type (RQ1), random from that type's pool
  functional.tsv       100 queries (RQ2): the existing random pilot sample (queries.tsv)
  all_queries.tsv      union of every query set, with the sets each method belongs to
  eval_queries.tsv     union of the evaluation sets only (runner input for E2/E3)
  README.md            how the sets were drawn, with counts

Rules: tuning queries are drawn first, from each type's pool minus the functional set, and
are then excluded from every evaluation set. Evaluation sets may overlap each other: one
method can be a query for several clone types and for RQ2; it is scored once.
"""
import argparse
import csv
import random
from collections import Counter, defaultdict

TYPES = ["T1", "T2", "VST3", "ST3", "MT3"]
PATTERN_TASKS = {"7", "12", "14", "20", "26", "41"}   # BCB search by code pattern (evaluation_design §4.8)

ap = argparse.ArgumentParser()
ap.add_argument("bcb_dir")
ap.add_argument("pools_dir")
ap.add_argument("--seed", type=int, default=20261014)
ap.add_argument("--tuning-per-type", type=int, default=10)
ap.add_argument("--eval-per-type", type=int, default=100)
args = ap.parse_args()

tp = defaultdict(set)
for r in csv.DictReader(open(f"{args.bcb_dir}/tp_functionalities.tsv"), delimiter="\t"):
    tp[r["function_id"]].add(r["functionality_id"])

# clones of each type per function (unique partners)
partners = {t: defaultdict(set) for t in TYPES}
for r in csv.DictReader(open(f"{args.bcb_dir}/syntactic_clone_pairs.tsv"), delimiter="\t"):
    a, b, t = r["function_id_one"], r["function_id_two"], r["clone_type"]
    partners[t][a].add(b)
    partners[t][b].add(a)
pools = {t: sorted(f for f in partners[t] if f in tp) for t in TYPES}
missing = {t: sum(1 for f in partners[t] if f not in tp) for t in TYPES}
assert not any(missing.values()), missing     # every clone-pair function is a corpus true positive

functional = [l.split("\t")[0] for l in open(f"{args.pools_dir}/queries.tsv").read().splitlines()[1:]]
assert len(functional) == 100

def category(fid):
    return "pattern" if tp[fid] & PATTERN_TASKS else "name"

# --- tuning: drawn first, avoiding the functional set and earlier tuning picks
rng = random.Random(args.seed)
tuning = {}
taken = set(functional)
for t in TYPES:
    avail = [f for f in pools[t] if f not in taken]
    pick = rng.sample(avail, args.tuning_per_type)
    tuning[t] = sorted(pick, key=int)
    taken.update(pick)
tuning_all = set().union(*tuning.values())

# --- evaluation sets per type: random from the pool minus all tuning queries
syntactic = {}
for t in TYPES:
    avail = [f for f in pools[t] if f not in tuning_all]
    syntactic[t] = sorted(random.Random(args.seed + 1 + TYPES.index(t)).sample(avail, args.eval_per_type), key=int)

assert not (tuning_all & set(functional))
assert not any(tuning_all & set(s) for s in syntactic.values())

def write(path, rows, t=None):
    with open(path, "w") as o:
        o.write("function_id\tfunctionality_ids\tcategory" + (f"\tn_{t}_clones" if t else "") + "\n")
        for f in rows:
            o.write(f"{f}\t{','.join(sorted(tp[f], key=int))}\t{category(f)}" + (f"\t{len(partners[t][f])}" if t else "") + "\n")

with open(f"{args.pools_dir}/tuning.tsv", "w") as o:
    o.write("function_id\tclone_type\tfunctionality_ids\tcategory\tn_type_clones\n")
    for t in TYPES:
        for f in tuning[t]:
            o.write(f"{f}\t{t}\t{','.join(sorted(tp[f], key=int))}\t{category(f)}\t{len(partners[t][f])}\n")
for t in TYPES:
    write(f"{args.pools_dir}/syntactic_{t}.tsv", syntactic[t], t)
write(f"{args.pools_dir}/functional.tsv", functional)

union = sorted(tuning_all | set(functional) | set().union(*map(set, syntactic.values())), key=int)
with open(f"{args.pools_dir}/all_queries.tsv", "w") as o:
    o.write("function_id\tsets\n")
    for f in union:
        sets = [f"tuning_{t}" for t in TYPES if f in tuning[t]]
        sets += ["functional"] if f in functional else []
        sets += [f"syntactic_{t}" for t in TYPES if f in syntactic[t]]
        o.write(f"{f}\t{','.join(sets)}\n")

with open(f"{args.pools_dir}/eval_queries.tsv", "w") as o:
    o.write("function_id\n")
    for f in union:
        if f not in tuning_all:
            o.write(f"{f}\n")

# --- summary
lines = ["# Query sets", "",
         f"Drawn by `prep/sample_queries.py` on 2026-10-14 (seed {args.seed}; per-type evaluation seeds {args.seed + 1}–{args.seed + 5}).",
         "See `PLAN.md` §4.2 and `docs/evaluation_design.md`.", "",
         "| Set | Queries | Pool it was drawn from | Pattern-task queries | Tasks represented | Median clones of the type per query |",
         "|---|---|---|---|---|---|"]
for t in TYPES:
    s = syntactic[t]
    med = sorted(len(partners[t][f]) for f in s)[len(s) // 2]
    lines.append(f"| `syntactic_{t}.tsv` | {len(s)} | {len(pools[t]):,} methods with a {t} clone, minus tuning queries | "
                 f"{sum(category(f) == 'pattern' for f in s)} | {len(set().union(*(tp[f] for f in s)))} | {med} |")
f_ = functional
lines.append(f"| `functional.tsv` | {len(f_)} | all 14,780 true positives (pilot sample, seed 20261011) | "
             f"{sum(category(f) == 'pattern' for f in f_)} | {len(set().union(*(tp[f] for f in f_)))} | – |")
lines.append(f"| `tuning.tsv` | {len(tuning_all)} | 10 per type from each type's pool, excluding the functional set | "
             f"{sum(category(f) == 'pattern' for f in tuning_all)} | {len(set().union(*(tp[f] for f in tuning_all)))} | – |")
lines += ["", f"`all_queries.tsv`: {len(union)} distinct methods (evaluation sets overlap; tuning is disjoint from all of them).",
          f"`eval_queries.tsv`: {len(union) - len(tuning_all)} distinct evaluation queries (runner input for E2/E3); `tuning.tsv` is the runner input for E1.", "",
          "Overlap between evaluation sets (methods in more than one):",
          f"{sum(1 for f in union if sum(f in set(s) for s in list(syntactic.values()) + [functional]) > 1)} methods.", ""]
open(f"{args.pools_dir}/README.md", "w").write("\n".join(lines))
print("\n".join(lines))
