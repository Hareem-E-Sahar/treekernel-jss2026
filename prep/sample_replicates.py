"""Sample 10 replicate query sets (decision 2026-10-20, user: replication with the user's own seeds).

usage: sample_replicates.py [--seeds 6251,9080,...]   -> data/pools/replicates/

Each replicate draws, independently of the others and of the original sets (data/pools/syntactic_*.tsv,
functional.tsv, which stay the primary sets for E5 and RQ5):
  syntactic_<T>.tsv  100 queries per clone type, random from the methods with a clone of that type
  functional.tsv     100 queries, random from all true positives
Pools: methods in the main corpus (data/trees_main, i.e. after the overflow exclusion) minus the 50
tuning queries, so tuned settings stay untouched by every replicate, minus the 42 methods (0.29%) whose
functionalities lie in different CodeBERT folds (no fold model is blind to all of their functionalities, so
fine-tuned CodeBERT would be scored with leakage; they stay in the corpus as candidates). Within a replicate a method may
serve several sets (as in the original design); across replicates sets may overlap.
Random streams: random.Random(seed * 10 + k), k = 0..4 for T1..MT3 and k = 5 for functional, so every
set has its own stream and none collides across the seeds used.
Also writes union.tsv (every query of every replicate; runner input) and README.md.
"""
import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TYPES = ["T1", "T2", "VST3", "ST3", "MT3"]
PATTERN_TASKS = {"7", "12", "14", "20", "26", "41"}
SEEDS = "6251,9080,8241,8828,55,1375,2084,2802,3501,3389"   # the user's seeds from the earlier study

ap = argparse.ArgumentParser()
ap.add_argument("--seeds", default=SEEDS)
ap.add_argument("--per-set", type=int, default=100)
args = ap.parse_args()
seeds = [int(s) for s in args.seeds.split(",")]
assert len(set(seeds)) == len(seeds)
assert len({s * 10 + k for s in seeds for k in range(6)}) == 6 * len(seeds)

tp = defaultdict(set)
for r in csv.DictReader(open(ROOT / "data/full_bcb/tp_functionalities.tsv"), delimiter="\t"):
    tp[r["function_id"]].add(r["functionality_id"])
with open(ROOT / "data/trees_main/D.tsv") as f:
    next(f)
    corpus = {line.split("\t", 1)[0] for line in f}
tuning = {r["function_id"] for r in csv.DictReader(open(ROOT / "data/pools/tuning.tsv"), delimiter="\t")}
fold = {r["functionality_id"]: r["fold"] for r in csv.DictReader(open(ROOT / "data/codebert/folds.tsv"), delimiter="\t")}
split = {f for f in corpus if f in tp and len({fold[x] for x in tp[f]}) > 1}
skip = tuning | split

partners = {t: defaultdict(set) for t in TYPES}
for r in csv.DictReader(open(ROOT / "data/full_bcb/syntactic_clone_pairs.tsv"), delimiter="\t"):
    a, b, t = r["function_id_one"], r["function_id_two"], r["clone_type"]
    if a in corpus and b in corpus:            # a clone outside the corpus cannot be retrieved
        partners[t][a].add(b)
        partners[t][b].add(a)
pools = {t: sorted((f for f in partners[t] if f not in skip), key=int) for t in TYPES}
pools["functional"] = sorted((f for f in corpus if f in tp and f not in skip), key=int)
SETS = TYPES + ["functional"]


def category(fid):
    return "pattern" if tp[fid] & PATTERN_TASKS else "name"


out = ROOT / "data/pools/replicates"
out.mkdir(parents=True, exist_ok=True)
union = set()
rows = []
for s in seeds:
    d = out / f"seed{s}"
    d.mkdir(exist_ok=True)
    for k, name in enumerate(SETS):
        pick = sorted(random.Random(s * 10 + k).sample(pools[name], args.per_set), key=int)
        union.update(pick)
        fn = d / (f"syntactic_{name}.tsv" if name in TYPES else "functional.tsv")
        with open(fn, "w") as o:
            o.write("function_id\tfunctionality_ids\tcategory" + (f"\tn_{name}_clones" if name in TYPES else "") + "\n")
            for f in pick:
                o.write(f"{f}\t{','.join(sorted(tp[f], key=int))}\t{category(f)}"
                        + (f"\t{len(partners[name][f])}" if name in TYPES else "") + "\n")
        rows.append((s, name, len(pick), sum(category(f) == "pattern" for f in pick), len(set().union(*(tp[f] for f in pick)))))
assert not (union & skip)
with open(out / "union.tsv", "w") as o:
    o.write("function_id\n" + "".join(f"{f}\n" for f in sorted(union, key=int)))

L = ["# Replicate query sets", "",
     f"Drawn by `prep/sample_replicates.py` (seeds {', '.join(map(str, seeds))}: the user's seeds from the earlier study).",
     "Each replicate: 100 queries per clone type and 100 functional queries, drawn independently; pools = main corpus minus the "
     "50 tuning queries and the methods whose functionalities span CodeBERT folds. The original sets in `data/pools/` are not part of the replicates.", "",
     "Pool sizes: " + ", ".join(f"{n} {len(pools[n]):,}" for n in SETS) + ".", "",
     "| Seed | Set | Queries | Pattern-task queries | Tasks represented |", "|---|---|---|---|---|"]
L += [f"| {s} | {n} | {q} | {p} | {t} |" for s, n, q, p, t in rows]
per = defaultdict(set)
for s in seeds:
    for name in SETS:
        fn = out / f"seed{s}" / (f"syntactic_{name}.tsv" if name in TYPES else "functional.tsv")
        per[name].update(l.split("\t")[0] for l in fn.read_text().splitlines()[1:])
L += ["", "Distinct queries over all replicates: " + ", ".join(f"{n} {len(per[n]):,}" for n in SETS)
      + f"; union {len(union):,} (`union.tsv`, runner input).", ""]
(out / "README.md").write_text("\n".join(L))
print("\n".join(L[:6] + L[-2:]))
