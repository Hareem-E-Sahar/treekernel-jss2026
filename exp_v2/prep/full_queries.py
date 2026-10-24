"""Every eligible query, for the hybrid (decision 2026-10-23: "the entire set of queries").

usage: .venv/bin/python exp_v2/prep/full_queries.py   -> exp_v2/data/full/{syntactic_<T>,functional,union}.tsv

Pools as for the replicates (prep/sample_replicates.py): syntactic_<T> = every method with a clone of type T in the
main corpus, functional = every true positive in the main corpus; minus the 50 tuning queries and the 42 methods whose
functionalities span CodeBERT folds. Same file format as exp_v2/data/replicates.
"""
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TYPES = ["T1", "T2", "VST3", "ST3", "MT3"]
PATTERN_TASKS = {"7", "12", "14", "20", "26", "41"}

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
    if a in corpus and b in corpus:
        partners[t][a].add(b)
        partners[t][b].add(a)
pools = {t: sorted((f for f in partners[t] if f not in skip), key=int) for t in TYPES}
pools["functional"] = sorted((f for f in corpus if f in tp and f not in skip), key=int)

out = ROOT / "exp_v2/data/full"
out.mkdir(parents=True, exist_ok=True)
for name, pick in pools.items():
    with open(out / (f"syntactic_{name}.tsv" if name in TYPES else "functional.tsv"), "w") as o:
        o.write("function_id\tfunctionality_ids\tcategory" + (f"\tn_{name}_clones" if name in TYPES else "") + "\n")
        for f in pick:
            o.write(f"{f}\t{','.join(sorted(tp[f], key=int))}\t{'pattern' if tp[f] & PATTERN_TASKS else 'name'}"
                    + (f"\t{len(partners[name][f])}" if name in TYPES else "") + "\n")
union = sorted(set().union(*pools.values()), key=int)
with open(out / "union.tsv", "w") as o:
    o.write("function_id\n" + "".join(f"{f}\n" for f in union))
print(", ".join(f"{n} {len(p):,}" for n, p in pools.items()) + f"; union {len(union):,}")
