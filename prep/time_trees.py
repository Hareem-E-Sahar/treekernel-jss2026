"""RQ5: time to turn the 14,679 corpus methods into KeLP trees (tree-sitter parse + each variant).

Same code as build_trees.py, without writing files. Prints a TSV: step, seconds, per method (ms).
usage: time_trees.py   (run from the repository root; used by scripts/run_timing.sh)
"""
import sys
import time
from pathlib import Path

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "prep"))
sys.path.insert(0, str(R / "bm25"))
from build_trees import METHOD_TYPES, PARSER, WRAP_PREFIX, WRAP_SUFFIX, method_name_nodes, tree_a, tree_bcd  # noqa: E402
from code_tokens import tokens, unescape  # noqa: E402

lines = (R / "data/trees_main/source.tsv").read_bytes().split(b"\n")
codes = [unescape(l.decode("utf-8", "replace").split("\t")[2]).encode() for l in lines[1:] if l]
t = time.perf_counter()
nodes = []
for c in codes:
    tree = PARSER.parse(WRAP_PREFIX + c + WRAP_SUFFIX)
    body = tree.root_node.children[0].child_by_field_name("body")
    nodes.append([m for m in body.named_children if m.type in METHOD_TYPES][0])
times = {"parse": time.perf_counter() - t}
t = time.perf_counter()
for n in nodes:
    tree_a(n)
times["variant A"] = time.perf_counter() - t
for v in "BCD":
    t = time.perf_counter()
    for n in nodes:
        tree_bcd(n, v, method_name_nodes(n))
    times[f"variant {v}"] = time.perf_counter() - t
t = time.perf_counter()
for c in codes:
    tokens(c.decode())
times["BM25 tokens"] = time.perf_counter() - t
print("step\tseconds\tms_per_method")
for k, s in times.items():
    print(f"{k}\t{s:.2f}\t{s / len(codes) * 1000:.3f}")
