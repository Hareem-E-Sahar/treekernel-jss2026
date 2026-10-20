"""Print the KeLP tree variants A-D for every method in a Java source file,
both as the one-line string KeLP reads and as an indented outline.

usage: show_variants.py <File.java> [--variants ABCD]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_trees as bt  # noqa: E402


def indented(tree_str):
    """Render a bracketed tree string as an indented outline, one node per line."""
    out, depth, i = [], -1, 0
    while i < len(tree_str):
        c = tree_str[i]
        if c == "(":
            depth += 1
            j = i + 1
            while j < len(tree_str) and tree_str[j] not in "() ":
                j += 1
            out.append("  " * depth + tree_str[i + 1:j])
            i = j
            continue
        if c == ")":
            depth -= 1
        i += 1
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("java_file")
    ap.add_argument("--variants", default="ABCD")
    args = ap.parse_args()
    code = open(args.java_file, "rb").read()
    root = bt.PARSER.parse(code).root_node
    methods, stack = [], [root]
    while stack:
        n = stack.pop()
        if n.type in bt.METHOD_TYPES:
            methods.append(n)
        stack.extend(reversed(n.children))
    for m in methods:
        name = m.child_by_field_name("name")
        print(f"=== method {bt.text(name)}  (parse errors: {m.has_error})")
        keep = bt.method_name_nodes(m)
        for v in args.variants:
            s = bt.tree_a(m) if v == "A" else bt.tree_bcd(m, v, keep)
            nodes, height, branch = bt.stats(s)
            print(f"\n--- variant {v}: {nodes} nodes, height {height}, max branching {branch}")
            print(s)
            print()
            print(indented(s))


if __name__ == "__main__":
    main()
