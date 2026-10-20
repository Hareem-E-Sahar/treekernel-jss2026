"""Extract source for every BigCloneBench true-positive function, sample the
100 retrieval queries, and write KeLP tree strings for variants A-D.

usage: build_trees.py <data/full_bcb> <bcb_reduced dir> <out dir> [--seed N] [--queries N]

Variants (see PLAN.md §3):
  A  raw: full tree-sitter tree, including anonymous tokens (keywords, punctuation)
  B  pruned: named nodes only (operators, modifiers and primitive type keywords kept),
     single-child chains collapsed except through statements and blocks
  C  B + abstraction: identifiers -> ID, type names -> TYPE, literals -> NUM/STR/CHAR/BOOL/NULL
  D  C but method-call names and type names keep their text
"""
import argparse
import csv
import os
import random
import re
import sys
from collections import Counter, defaultdict

import tree_sitter
import tree_sitter_java

PARSER = tree_sitter.Parser(tree_sitter.Language(tree_sitter_java.language()))
WRAP_PREFIX = b"class __W__ {\n"
WRAP_SUFFIX = b"\n}\n"
METHOD_TYPES = {"method_declaration", "constructor_declaration"}
LITERALS = {
    "decimal_integer_literal": "NUM", "hex_integer_literal": "NUM",
    "octal_integer_literal": "NUM", "binary_integer_literal": "NUM",
    "decimal_floating_point_literal": "NUM", "hex_floating_point_literal": "NUM",
    "string_literal": "STR", "text_block": "STR", "character_literal": "CHAR",
    "true": "BOOL", "false": "BOOL", "null_literal": "NULL",
}
# Anonymous tokens kept in B-D, by parent node type: operators, modifier keywords,
# and the keyword of a primitive type (so that int and long stay distinguishable).
KEEP_TOKENS_UNDER = {"binary_expression", "unary_expression", "update_expression",
                     "assignment_expression", "modifiers", "integral_type",
                     "floating_point_type"}
# Single-child chains are never collapsed *through* these nodes, so statement kinds
# survive: `return x;` stays (return_statement (ID)) instead of becoming just (ID).
NO_COLLAPSE = {"block", "constructor_body", "switch_block", "class_body"}

# KeLP reads "(label child child)", so a label must not contain parentheses or
# whitespace. It also gives "##" (type##content) and "::" (lemma::pos) a meaning.
# Everything else is written as is.
CHAR_NAMES = {"(": "-LRB-", ")": "-RRB-", " ": "·", "\t": "-TAB-", "\n": "-NL-", "\r": "-CR-",
              "#": "-HASH-"}

def label(s):
    """Make a KeLP-safe, human-readable label (see CHAR_NAMES)."""
    out = []
    for c in s:
        if c in CHAR_NAMES:
            out.append(CHAR_NAMES[c])
        elif c.isspace() or ord(c) < 32:
            out.append(f"-U{ord(c):04X}-")
        else:
            out.append(c)
    out = "".join(out).replace("::", "-DCOLON-")
    return out[:60] if out else "-EMPTY-"

def collapsible(node):
    return not (node.type.endswith("_statement") or node.type in NO_COLLAPSE)

def text(node):
    return node.text.decode("utf-8", "replace")

# ------------------------------------------------------------------ variants
def tree_a(node):
    if node.child_count == 0:
        lab = label(node.type)
        if node.is_named:          # identifier / literal: keep token text as a leaf
            return f"({lab} ({label(text(node))}))"
        return f"({lab})"          # keyword or punctuation token
    return f"({label(node.type)} " + " ".join(tree_a(c) for c in node.children) + ")"

def kept_children(node):
    kids = []
    for c in node.children:
        if c.is_named and c.type not in ("line_comment", "block_comment"):
            kids.append(c)
        elif not c.is_named and node.type in KEEP_TOKENS_UNDER:
            kids.append(c)         # operator ('+'), modifier ('public') or primitive type ('int')
    return kids

def literal_leaf(node, variant):
    if variant == "B":
        return f"({label(node.type)} ({label(text(node))}))"
    return f"({LITERALS[node.type]})"

def method_name_nodes(root):
    """Identifier nodes that name an invoked method or a referenced type (kept in D)."""
    keep = set()
    stack = [root]
    while stack:
        n = stack.pop()
        if n.type == "method_invocation":
            nm = n.child_by_field_name("name")
            if nm is not None:
                keep.add(nm.id)
        stack.extend(n.children)
    return keep

def tree_bcd(node, variant, keep_ids):
    if node.type in LITERALS:      # literals are atomic: never descend into string_fragment etc.
        return literal_leaf(node, variant)
    kids = kept_children(node)
    # collapse single-child chains (the node is replaced by its only child), but never
    # through a statement or block, so e.g. return_statement is kept
    while len(kids) == 1 and kids[0].is_named and collapsible(node):
        node = kids[0]
        if node.type in LITERALS:
            return literal_leaf(node, variant)
        kids = kept_children(node)
    t = node.type
    if not kids:
        if not node.is_named:
            return f"({label(t)})"
        if variant == "B":
            return f"({label(t)} ({label(text(node))}))" if node.child_count == 0 else f"({label(t)})"
        if t == "type_identifier":
            return f"(type_identifier ({label(text(node))}))" if variant == "D" else "(TYPE)"
        if t == "identifier":
            if variant == "D" and node.id in keep_ids:
                return f"(identifier ({label(text(node))}))"
            return "(ID)"
        return f"({label(t)})"
    return f"({label(t)} " + " ".join(tree_bcd(c, variant, keep_ids) for c in kids) + ")"

def stats(tree_str):
    """nodes, height, max branching factor of a KeLP bracketed tree string."""
    nodes = depth = height = 0
    child_count = [0]
    max_branch = 0
    for ch in tree_str:
        if ch == "(":
            nodes += 1
            child_count[-1] += 1
            max_branch = max(max_branch, child_count[-1])
            depth += 1
            height = max(height, depth)
            child_count.append(0)
        elif ch == ")":
            depth -= 1
            child_count.pop()
    return nodes, height, max_branch

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bcb_dir")
    ap.add_argument("src_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--seed", type=int, default=20261011)
    ap.add_argument("--queries", type=int, default=100)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    csv.field_size_limit(10**9)

    funcs = {}
    for r in csv.DictReader(open(f"{args.bcb_dir}/functions.tsv"), delimiter="\t", quoting=csv.QUOTE_NONE):
        funcs[int(r["id"])] = r
    tp = defaultdict(set)
    for r in csv.DictReader(open(f"{args.bcb_dir}/tp_functionalities.tsv"), delimiter="\t"):
        tp[int(r["function_id"])].add(int(r["functionality_id"]))
    ids = sorted(tp)
    print(f"true-positive functions: {len(ids)}")

    index = defaultdict(list)
    for root, _, files in os.walk(args.src_dir):
        for fn in files:
            index[(os.path.basename(root), fn)].append(os.path.join(root, fn))

    # ------------------------------------------------------------------ queries
    rng = random.Random(args.seed)
    queries = sorted(rng.sample(ids, args.queries))
    os.makedirs(f"{args.out_dir}/../pools", exist_ok=True)
    with open(f"{args.out_dir}/../pools/queries.tsv", "w") as o:
        o.write("function_id\tfunctionality_ids\n")
        for q in queries:
            o.write(f"{q}\t{','.join(map(str, sorted(tp[q])))}\n")
    qf = Counter(f for q in queries for f in tp[q])
    print(f"queries: {len(queries)} (seed {args.seed}), covering {len(qf)} functionalities")

    # ------------------------------------------------------------------ build
    status = Counter()
    outs = {v: open(f"{args.out_dir}/{v}.tsv", "w") for v in "ABCD"}
    for o in outs.values():
        o.write("function_id\tnodes\theight\tmax_branching\ttree\n")
    src_out = open(f"{args.out_dir}/source.tsv", "w")
    src_out.write("function_id\tfunctionality_ids\tsource_escaped\n")
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
        keep = method_name_nodes(node)
        trees = {"A": tree_a(node)}
        for v in "BCD":
            trees[v] = tree_bcd(node, v, keep)
        for v, s in trees.items():
            n, h, b = stats(s)
            outs[v].write(f"{i}\t{n}\t{h}\t{b}\t{s}\n")
        esc = code.decode("utf-8", "replace").replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n")
        src_out.write(f"{i}\t{','.join(map(str, sorted(tp[i])))}\t{esc}\n")
    for o in list(outs.values()) + [src_out]:
        o.close()
    print("parse status:")
    for k, v in status.most_common():
        print(f"  {k:32s} {v}")


if __name__ == "__main__":
    main()
