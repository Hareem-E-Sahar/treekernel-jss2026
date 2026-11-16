"""Type-2 copies of each eligible query outside its functionality labels (revision_plan.md, R1-C3 option B).

usage: .venv/bin/python exp_v3_all_queries/prep/t2_copies.py
  -> exp_v3_all_queries/data/t2_copies.tsv (query_id, fp_id, kind), exp_v3_all_queries/data/t2_copies_summary.tsv

Type-2 copy = identical token sequence after the usual Type-2 normalisation: comments and whitespace removed, every
identifier (including type names) replaced by ID, every literal (string, character, number, true/false/null) by LIT;
keywords, primitive types, operators and separators kept. For each eligible query (exp_v2/data/full/union.tsv), the
listed methods are its Type-2 copies that BigCloneBench does not label as sharing a functionality with it:
  kind = fp     a BigCloneBench false positive (exp_v2/data/fp_copies.tsv lists the whitespace-identical ones)
  kind = other  a true positive of other functionalities only
Such a method is very likely mislabelled for this query (a copy implements what the query implements), so the
sensitivity evaluation ignores it in the query's ranking, as the exact copies are ignored now. The column is named
fp_id so that the file works with evaluate.py --ignore.
"""
import csv
import hashlib
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "exp_v3_all_queries/data"

KEYWORDS = set("""abstract assert boolean break byte case catch char class const continue default do double else enum
extends final finally float for goto if implements import instanceof int interface long native new package private
protected public return short static strictfp super switch synchronized this throw throws transient try void volatile
while var""".split())
LITERAL_WORDS = {"true", "false", "null"}
TOKEN = re.compile(r"""
    (?P<ws>\s+)
  | (?P<comment>//[^\n]*|/\*.*?\*/)
  | (?P<str>"(?:\\.|[^"\\])*")
  | (?P<chr>'(?:\\.|[^'\\])*')
  | (?P<num>(?:0[xX][0-9a-fA-F_]+|0[bB][01_]+|(?:\d[\d_]*\.?[\d_]*|\.\d[\d_]*)(?:[eE][+-]?\d+)?)[lLfFdD]?)
  | (?P<word>[A-Za-z_$][A-Za-z0-9_$]*)
  | (?P<op>>>>=|<<=|>>=|\.\.\.|->|::|\+\+|--|&&|\|\||[=!<>+\-*/&|^%]=|[{}()\[\];,.@=<>!~?:+\-*/&|^%])
  | (?P<other>.)
""", re.S | re.X)
ESC = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\"}


def unescape(s):
    return re.sub(r"\\(.)", lambda m: ESC.get(m.group(1), "\\" + m.group(1)), s)


def t2_hash(src):
    out = []
    for m in TOKEN.finditer(src):
        k = m.lastgroup
        if k in ("ws", "comment"):
            continue
        x = m.group()
        if k in ("str", "chr", "num"):
            out.append("LIT")
        elif k == "word":
            out.append("LIT" if x in LITERAL_WORDS else x if x in KEYWORDS else "ID")
        else:
            out.append(x)
    return hashlib.sha1(" ".join(out).encode()).hexdigest()


def main():
    tasks = defaultdict(set)
    for r in csv.DictReader(open(ROOT / "data/full_bcb/tp_functionalities.tsv"), delimiter="\t"):
        tasks[r["function_id"]].add(r["functionality_id"])
    by_hash, h_of = defaultdict(list), {}
    with open(ROOT / "data/trees_e5/source.tsv", newline="\n") as f:   # a raw \r occurs inside some sources
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            h = t2_hash(unescape(p[-1]))
            h_of[p[0]] = h
            by_hash[h].append(p[0])
    queries = [r["function_id"] for r in csv.DictReader(open(ROOT / "exp_v2/data/full/union.tsv"), delimiter="\t")]
    exact = defaultdict(set)
    for r in csv.DictReader(open(ROOT / "exp_v2/data/fp_copies.tsv"), delimiter="\t"):
        exact[r["query_id"]].add(r["fp_id"])
    rows = []
    for q in queries:
        for x in by_hash[h_of[q]]:
            if x == q or tasks[x] & tasks[q]:
                continue
            rows.append((q, x, "other" if tasks[x] else "fp"))
    rows.sort(key=lambda r: (int(r[0]), int(r[1])))
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "t2_copies.tsv", "w") as o:
        o.write("query_id\tfp_id\tkind\n")
        o.writelines("\t".join(r) + "\n" for r in rows)
    fp = [r for r in rows if r[2] == "fp"]
    oth = [r for r in rows if r[2] == "other"]
    summ = [
        ("eligible queries", len(queries)),
        ("queries with a Type-2 copy among false positives", len({r[0] for r in fp})),
        ("query-false positive pairs", len(fp)),
        ("  of which whitespace-identical (exp_v2/data/fp_copies.tsv)", sum(1 for q, x, _ in fp if x in exact[q])),
        ("distinct false positives involved", len({r[1] for r in fp})),
        ("queries with a Type-2 copy among other functionalities' true positives", len({r[0] for r in oth})),
        ("query-other true positive pairs", len(oth)),
        ("distinct other true positives involved", len({r[1] for r in oth})),
        ("queries with any Type-2 copy outside their functionality", len({r[0] for r in rows})),
    ]
    with open(OUT / "t2_copies_summary.tsv", "w") as o:
        o.write("statistic\tvalue\n")
        o.writelines(f"{a}\t{b}\n" for a, b in summ)
    for a, b in summ:
        print(f"{b:>8}  {a}")


if __name__ == "__main__":
    main()
