"""Stratified query sets for the size and complexity analysis (decision 2026-10-22).

usage: .venv/bin/python exp_v2/prep/sample_size_complexity.py   -> exp_v2/data/size_complexity/

Groups of the query (exp_v2/data/size_complexity.tsv, prep/size_complexity.py), fixed before any result:
  small  LOC <= 6         large  LOC >= 10          (LOC = physical lines of the method; 7-9 in neither)
  low    McCabe <= 10     high   McCabe > 10        (Checkstyle CyclomaticComplexity; 1 method unparsable: in neither)
For each of the user's 10 seeds, group and set (T1..MT3, functional): 100 queries at random from the group's pool, or
the whole pool if it has 100 or fewer (then every seed has the same queries). Pools as for the replicates
(prep/sample_replicates.py): methods with a clone of that type (functional: all true positives) in the main corpus,
minus the 50 tuning queries and the 42 methods whose functionalities span CodeBERT folds. Candidates are not
restricted: every query is ranked against the whole corpus with false positives.
Random stream per (seed, group, set): random.Random(f"size_complexity|{seed}|{group}|{set}").
Writes seed<S>/<group>/{syntactic_<T>,functional}.tsv (format of exp_v2/data/replicates), union.tsv, pools.tsv,
README.md.
"""
import csv
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TYPES = ["T1", "T2", "VST3", "ST3", "MT3"]
SETS = TYPES + ["functional"]
PATTERN_TASKS = {"7", "12", "14", "20", "26", "41"}
SEEDS = [6251, 9080, 8241, 8828, 55, 1375, 2084, 2802, 3501, 3389]   # the user's seeds
PER_SET = 100

sc = {r["function_id"]: r for r in csv.DictReader(open(ROOT / "exp_v2/data/size_complexity.tsv"), delimiter="\t")}
GROUPS = {
    "small": lambda r: int(r["loc"]) <= 6,
    "large": lambda r: int(r["loc"]) >= 10,
    "low": lambda r: r["cc_status"] == "ok" and int(r["cc"]) <= 10,
    "high": lambda r: r["cc_status"] == "ok" and int(r["cc"]) > 10,
}

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
base = {t: {f for f in partners[t] if f not in skip} for t in TYPES}
base["functional"] = {f for f in corpus if f in tp and f not in skip}
assert all(f in sc for s in base.values() for f in s)
pools = {(g, n): sorted((f for f in base[n] if ok(sc[f])), key=int) for g, ok in GROUPS.items() for n in SETS}


def category(fid):
    return "pattern" if tp[fid] & PATTERN_TASKS else "name"


out = ROOT / "exp_v2/data/size_complexity"
union = set()
for s in SEEDS:
    for g in GROUPS:
        d = out / f"seed{s}" / g
        d.mkdir(parents=True, exist_ok=True)
        for n in SETS:
            pool = pools[(g, n)]
            pick = pool if len(pool) <= PER_SET else sorted(random.Random(f"size_complexity|{s}|{g}|{n}").sample(pool, PER_SET), key=int)
            union.update(pick)
            with open(d / (f"syntactic_{n}.tsv" if n in TYPES else "functional.tsv"), "w") as o:
                o.write("function_id\tfunctionality_ids\tcategory" + (f"\tn_{n}_clones" if n in TYPES else "") + "\n")
                for f in pick:
                    o.write(f"{f}\t{','.join(sorted(tp[f], key=int))}\t{category(f)}"
                            + (f"\t{len(partners[n][f])}" if n in TYPES else "") + "\n")
assert not (union & skip)
with open(out / "union.tsv", "w") as o:
    o.write("function_id\n" + "".join(f"{f}\n" for f in sorted(union, key=int)))
with open(out / "pools.tsv", "w") as o:
    o.write("group\tset\tpool\tper_seed\tsampled\n")
    for (g, n), p in pools.items():
        o.write(f"{g}\t{n}\t{len(p)}\t{min(len(p), PER_SET)}\t{'yes' if len(p) > PER_SET else 'no (whole pool)'}\n")
L = ["# Query sets for the size and complexity analysis", "",
     "Drawn by `exp_v2/prep/sample_size_complexity.py`; groups, pools and streams are described there.", "",
     "| Group | " + " | ".join(SETS) + " |", "|---" * (len(SETS) + 1) + "|"]
for g in GROUPS:
    L.append(f"| {g} | " + " | ".join(f"{len(pools[(g, n)]):,}" + ("" if len(pools[(g, n)]) > PER_SET else " (all)")
                                      for n in SETS) + " |")
L += ["", f"Pool sizes; per seed min(pool, {PER_SET}) queries; (all) = whole pool, identical in every seed. "
      f"Union of all queries: {len(union):,}."]
(out / "README.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
