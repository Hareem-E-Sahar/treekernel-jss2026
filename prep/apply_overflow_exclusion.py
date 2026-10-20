"""Exclude the methods on which KeLP's SSTK at its default lambda = 0.4 overflows (decision 2026-10-16).

usage: apply_overflow_exclusion.py <repo root> [--seed 20261016]

Exclusion rule: a method is excluded if KeLP's SSTK self-similarity K(x, x) at lambda = 0.4 is
not finite (32-bit float overflow) on any of the tree variants A-D. The ids come from
GridFiniteScan -DdumpDir (results/grid_scan/nonfinite_ids/<variant>_SSTK_0.4.ids).

Writes:
  data/corpus/excluded_overflow.tsv   excluded methods with node counts per variant
  data/trees_main/{A,B,C,D,source}.tsv  the tree/source files without the excluded methods
  data/pools/functional.tsv etc.      excluded queries replaced by a random true positive that
                                      is excluded from nothing and is not already a query
The tuning and syntactic sets contain no excluded method and are left unchanged (checked).
"""
import argparse
import csv
import random
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("root", type=Path)
ap.add_argument("--seed", type=int, default=20261016)
args = ap.parse_args()
R = args.root
VARIANTS = ["A", "B", "C", "D"]

nodes = {v: {} for v in VARIANTS}
for v in VARIANTS:
    for line in open(R / f"results/grid_scan/nonfinite_ids/{v}_SSTK_0.4.ids"):
        fid, n = line.split()
        nodes[v][fid] = n
excluded = set().union(*nodes.values())

# node counts of every excluded method on every variant (from the tree files)
size = {v: {} for v in VARIANTS}
for v in VARIANTS:
    with open(R / f"data/trees/{v}.tsv") as f:
        next(f)
        for line in f:
            fid, n, _ = line.split("\t", 2)
            if fid in excluded:
                size[v][fid] = n
out = R / "data/corpus"
out.mkdir(exist_ok=True)
with open(out / "excluded_overflow.tsv", "w") as o:
    o.write("function_id\t" + "\t".join(f"nodes_{v}" for v in VARIANTS) + "\toverflows_on\n")
    for fid in sorted(excluded, key=int):
        o.write(f"{fid}\t" + "\t".join(size[v][fid] for v in VARIANTS) + "\t"
                + ",".join(v for v in VARIANTS if fid in nodes[v]) + "\n")

main = R / "data/trees_main"
main.mkdir(exist_ok=True)
for name in VARIANTS + ["source"]:
    kept = 0
    # bytes, split on \n only: the source text contains raw \r (CRLF files), which text mode
    # would turn into line breaks (bug fixed 2026-10-18; trees were unaffected)
    lines = (R / f"data/trees/{name}.tsv").read_bytes().split(b"\n")
    with open(main / f"{name}.tsv", "wb") as o:
        o.write(lines[0] + b"\n")
        for line in lines[1:]:
            if line and line.split(b"\t", 1)[0].decode() not in excluded:
                o.write(line + b"\n")
                kept += 1
    print(f"{name}: {kept} methods kept")

# --- queries
pools = R / "data/pools"
def ids(name):
    return [r["function_id"] for r in csv.DictReader(open(pools / name), delimiter="\t")]
for name in ["tuning.tsv"] + [f"syntactic_{t}.tsv" for t in ["T1", "T2", "VST3", "ST3", "MT3"]]:
    assert not set(ids(name)) & excluded, name

all_rows = list(csv.DictReader(open(pools / "all_queries.tsv"), delimiter="\t"))
taken = {r["function_id"] for r in all_rows}
tps = sorted({r["function_id"] for r in csv.DictReader(open(R / "data/full_bcb/tp_functionalities.tsv"), delimiter="\t")}, key=int)
candidates = [f for f in tps if f not in excluded and f not in taken]
rng = random.Random(args.seed)

func_rows = list(csv.DictReader(open(pools / "functional.tsv"), delimiter="\t"))
tp = {}
for r in csv.DictReader(open(R / "data/full_bcb/tp_functionalities.tsv"), delimiter="\t"):
    tp.setdefault(r["function_id"], set()).add(r["functionality_id"])
PATTERN_TASKS = {"7", "12", "14", "20", "26", "41"}
replaced = []
for r in func_rows:
    if r["function_id"] in excluded:
        new = rng.choice(candidates)
        candidates.remove(new)
        replaced.append((r["function_id"], new))
        r["function_id"] = new
        r["functionality_ids"] = ",".join(sorted(tp[new], key=int))
        r["category"] = "pattern" if tp[new] & PATTERN_TASKS else "name"
func_rows.sort(key=lambda r: int(r["function_id"]))
with open(pools / "functional.tsv", "w") as o:
    o.write("function_id\tfunctionality_ids\tcategory\n")
    for r in func_rows:
        o.write(f"{r['function_id']}\t{r['functionality_ids']}\t{r['category']}\n")

sets = {r["function_id"]: r["sets"].split(",") for r in all_rows}
for old, new in replaced:
    rest = [s for s in sets.pop(old) if s != "functional"]
    if rest:
        raise SystemExit(f"{old} is also in {rest}; handle by hand")
    sets[new] = ["functional"]
with open(pools / "all_queries.tsv", "w") as o:
    o.write("function_id\tsets\n")
    for f in sorted(sets, key=int):
        o.write(f"{f}\t{','.join(sets[f])}\n")
with open(pools / "eval_queries.tsv", "w") as o:
    o.write("function_id\n")
    for f in sorted(sets, key=int):
        if not all(s.startswith("tuning_") for s in sets[f]):
            o.write(f"{f}\n")
print(f"excluded {len(excluded)} methods; replaced functional queries: {replaced}")
