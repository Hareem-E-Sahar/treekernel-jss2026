"""Tree statistics and fragments of every corpus method (revision_plan.md, R1-C4 D1 and D2).

usage: .venv/bin/python exp_v3_all_queries/eval/trees.py
  -> exp_v3_all_queries/results/diagnostics/tree_stats.tsv   per method: nodes, height, leaves, internal nodes,
                                                              mean and max branching, leaf share, distinct productions
     exp_v3_all_queries/results/diagnostics/fragments.npz    per method, as sorted unique ids with counts:
       productions   node label + ordered child labels, one per internal node (the fragments SSTK builds on; the
                     proxy for SSTK and PTK, whose fragments cannot be enumerated)
       subtrees      complete subtrees rooted at internal nodes (STK's fragments)
Trees: data/trees_e5/D.tsv (variant D). Leaves, including placeholders such as (ID), are not fragments of their own;
they enter as child labels of productions and as parts of subtrees, as in the kernels. Node counts are checked
against D.tsv's nodes, height and max_branching columns.
"""
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "exp_v3_all_queries/results/diagnostics"
TOK = re.compile(r"\(|\)|[^\s()]+")


def parse(s):
    """-> list of nodes (label, children indices), root first."""
    nodes, stack, expect_label = [], [], False
    for t in TOK.findall(s):
        if t == "(":
            expect_label = True
        elif t == ")":
            stack.pop()
        else:
            assert expect_label, s[:80]
            i = len(nodes)
            nodes.append((t, []))
            if stack:
                nodes[stack[-1]][1].append(i)
            stack.append(i)
            expect_label = False
    assert not stack
    return nodes


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    prod_id, sub_id = {}, {}
    ids, stats = [], []
    prods, subs = [], []
    with open(ROOT / "data/trees_e5/D.tsv") as f:
        next(f)
        for line in f:
            fid, n, h, mb, tree = line.rstrip("\n").split("\t", 4)
            nodes = parse(tree)
            N = len(nodes)
            height = [0] * N
            sig = [None] * N
            for i in range(N - 1, -1, -1):            # children have larger indices than their parent
                lab, ch = nodes[i]
                height[i] = 1 + max((height[c] for c in ch), default=0)
                sig[i] = lab if not ch else f"({lab} {' '.join(sig[c] for c in ch)})"
            internal = [i for i in range(N) if nodes[i][1]]
            br = [len(nodes[i][1]) for i in internal]
            assert (N, height[0], max(br, default=0)) == (int(n), int(h), int(mb)), fid
            p = [prod_id.setdefault(nodes[i][0] + " -> " + " ".join(nodes[c][0] for c in nodes[i][1]), len(prod_id))
                 for i in internal]
            s = [sub_id.setdefault(sig[i], len(sub_id)) for i in internal]
            for lst, frag in ((prods, p), (subs, s)):
                u, c = np.unique(np.array(frag, dtype=np.int64), return_counts=True)
                lst.append((u, c))
            ids.append(fid)
            stats.append((fid, N, height[0], N - len(internal), len(internal),
                          np.mean(br) if br else 0.0, max(br, default=0), (N - len(internal)) / N, len(prods[-1][0])))
    with open(OUT / "tree_stats.tsv", "w") as o:
        o.write("function_id\tnodes\theight\tleaves\tinternal\tmean_branching\tmax_branching\tleaf_share\t"
                "distinct_productions\n")
        for r in stats:
            o.write("\t".join(f"{x:.4f}" if isinstance(x, float) else str(x) for x in r) + "\n")

    def pack(lst):
        off = np.cumsum([0] + [len(u) for u, _ in lst])
        return off, np.concatenate([u for u, _ in lst]), np.concatenate([c for _, c in lst])

    po, pu, pc = pack(prods)
    so, su, sc = pack(subs)
    np.savez(OUT / "fragments.npz", ids=np.array(ids), prod_off=po, prod_ids=pu, prod_cnt=pc,
             sub_off=so, sub_ids=su, sub_cnt=sc)
    print(f"{len(ids)} methods; {len(prod_id)} distinct productions, {len(sub_id)} distinct complete subtrees")


if __name__ == "__main__":
    main()
