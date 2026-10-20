"""E5: trees (variant D) and source of BigCloneBench's false-positive functions (PLAN.md §6, E5).

False positive = judged false positive for some functionality and true positive for none
(58,322 functions). Same extraction and tree building as build_trees.py.

usage: build_fp_trees.py <data/full_bcb> <bcb_reduced dir> <out dir>
Writes <out>/D.tsv and <out>/source.tsv (functionality_ids = the tasks it was judged false for).
"""
import csv
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_trees import METHOD_TYPES, PARSER, WRAP_PREFIX, WRAP_SUFFIX, method_name_nodes, stats, tree_bcd  # noqa: E402

bcb, src_dir, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
csv.field_size_limit(10**9)
funcs = {int(r["id"]): r for r in csv.DictReader(open(f"{bcb}/functions.tsv"), delimiter="\t", quoting=csv.QUOTE_NONE)}
tps = {int(r["function_id"]) for r in csv.DictReader(open(f"{bcb}/tp_functionalities.tsv"), delimiter="\t")}
tp, fp = defaultdict(int), defaultdict(set)
for r in csv.DictReader(open(f"{bcb}/judged.tsv"), delimiter="\t"):
    f = int(r["function_id"])
    tp[f] += int(r["tp"])
    if int(r["fp"]):
        fp[f].add(int(r["functionality_id"]))
ids = sorted(f for f in fp if tp[f] == 0 and f not in tps)
print(f"false-positive functions: {len(ids)}")

index = defaultdict(list)
for root, _, files in os.walk(src_dir):
    for fn in files:
        index[(os.path.basename(root), fn)].append(os.path.join(root, fn))

status = Counter()
with open(f"{out}/D.tsv", "w") as td, open(f"{out}/source.tsv", "w") as so:
    td.write("function_id\tnodes\theight\tmax_branching\ttree\n")
    so.write("function_id\tfunctionality_ids\tsource_escaped\n")
    for i in ids:
        m = funcs[i]
        paths = index.get((m["type"], m["name"]), [])
        if not paths:
            status["source file missing"] += 1
            continue
        lines = open(paths[0], "rb").read().split(b"\n")
        code = b"\n".join(lines[int(m["startline"]) - 1:int(m["endline"])])
        tree = PARSER.parse(WRAP_PREFIX + code + WRAP_SUFFIX)
        body = tree.root_node.children[0].child_by_field_name("body") if tree.root_node.children else None
        members = [c for c in body.named_children if c.type in METHOD_TYPES] if body else []
        if not members:
            status["no method node"] += 1
            continue
        node = members[0]
        if len(members) > 1:
            status["several methods (first used)"] += 1
        status["has ERROR/MISSING" if node.has_error else "clean parse"] += 1
        s = tree_bcd(node, "D", method_name_nodes(node))
        n, h, b = stats(s)
        td.write(f"{i}\t{n}\t{h}\t{b}\t{s}\n")
        esc = code.decode("utf-8", "replace").replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n")
        so.write(f"{i}\t{','.join(map(str, sorted(fp[i])))}\t{esc}\n")
print("parse status:")
for k, v in status.most_common():
    print(f"  {k:32s} {v}")
