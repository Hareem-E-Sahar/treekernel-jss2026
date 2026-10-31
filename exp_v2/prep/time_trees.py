"""exp_v2 one-off cost: turning the corpus methods into variant-D trees (tree-sitter parse + variant D), one thread.

Same code as prep/time_trees.py (which is fixed to the main corpus), on a given source file; only variant D, the
variant exp_v2 uses. Prints a TSV: step, seconds, per method (ms).
usage: .venv/bin/python exp_v2/prep/time_trees.py [data/trees_e5/source.tsv]
"""
import sys
import time
from pathlib import Path

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "prep"))
sys.path.insert(0, str(R / "bm25"))
from build_trees import METHOD_TYPES, PARSER, WRAP_PREFIX, WRAP_SUFFIX, method_name_nodes, tree_bcd  # noqa: E402
from code_tokens import tokens, unescape  # noqa: E402

lines = (R / (sys.argv[1] if len(sys.argv) > 1 else "data/trees_e5/source.tsv")).read_bytes().split(b"\n")
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
    tree_bcd(n, "D", method_name_nodes(n))
times["variant D"] = time.perf_counter() - t
t = time.perf_counter()
for c in codes:
    tokens(c.decode())
times["BM25 tokens"] = time.perf_counter() - t
print("step\tseconds\tms_per_method")
for k, s in times.items():
    print(f"{k}\t{s:.2f}\t{s / len(codes) * 1000:.3f}")
