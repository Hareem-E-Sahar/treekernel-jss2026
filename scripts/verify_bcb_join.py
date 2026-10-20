"""Verify that CodeXGLUE BCB lines up with the BigCloneBench database, and
attach clone type + functionality to every CodeXGLUE pair.

usage: verify_bcb_join.py <codexglue dir> <bcb_subset dir> <bcb_reduced dir> <out dir>
"""
import csv
import difflib
import json
import os
import re
import sys
from collections import Counter, defaultdict

cx_dir, sub_dir, src_dir, out_dir = sys.argv[1:5]
os.makedirs(out_dir, exist_ok=True)
csv.field_size_limit(10**9)

def read_tsv(name):
    with open(f"{sub_dir}/{name}.tsv", newline="") as f:
        yield from csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)

funcs = {}
with open(f"{cx_dir}/data.jsonl") as f:
    for line in f:
        d = json.loads(line)
        funcs[int(d["idx"])] = d["func"]

meta = {int(r["id"]): r for r in read_tsv("functions")}
fnames = {int(r["id"]): r["name"] for r in read_tsv("functionalities")}

# ---------------------------------------------------------------- source check
print("== 1. source text check (IJaDataset file lines vs CodeXGLUE func)")
index = defaultdict(list)
for root, _, files in os.walk(src_dir):
    for fn in files:
        index[(os.path.basename(root), fn)].append(os.path.join(root, fn))

COMMENT = re.compile(r"/\*.*?\*/|//[^\n]*", re.S)
def norm(s):
    return re.sub(r"\s+", "", COMMENT.sub("", s))

status = Counter()
examples = []
for i, code in funcs.items():
    m = meta[i]
    paths = index.get((m["type"], m["name"]), [])
    if not paths:
        status["file not found"] += 1
        continue
    with open(paths[0], encoding="utf-8", errors="replace") as fh:
        lines = fh.read().split("\n")
    snippet = "\n".join(lines[int(m["startline"]) - 1:int(m["endline"])])
    if snippet.strip() == code.strip():
        status["exact"] += 1
    elif norm(snippet) == norm(code):
        status["equal ignoring whitespace/comments"] += 1
    else:
        r = difflib.SequenceMatcher(None, norm(snippet), norm(code), autojunk=False).ratio()
        key = "similar (ratio>=0.9)" if r >= 0.9 else "DIFFERENT"
        status[key] += 1
        if len(examples) < 3:
            examples.append((i, round(r, 3), paths[0], m["startline"], m["endline"]))
for k, v in status.most_common():
    print(f"  {k:38s} {v}")
for e in examples:
    print("  mismatch example:", e)

# ---------------------------------------------------------------- pair labels
splits = {}
wanted = set()
for name in ("train", "valid", "test"):
    pairs = {}
    with open(f"{cx_dir}/{name}.txt") as fh:
        for line in fh:
            a, b, y = map(int, line.split())
            pairs[(min(a, b), max(a, b))] = y
    splits[name] = pairs
    wanted |= pairs.keys()

clones = {}
for r in read_tsv("clones"):
    k = (int(r["function_id_one"]), int(r["function_id_two"]))
    if k in wanted:
        clones[k] = (int(r["functionality_id"]), int(r["syntactic_type"]),
                     float(r["similarity_line"]), float(r["similarity_token"]))
fps = {}
for r in read_tsv("false_positives"):
    a, b = int(r["function_id_one"]), int(r["function_id_two"])
    k = (min(a, b), max(a, b))
    if k in wanted:
        fps[k] = int(r["functionality_id"])

def clone_type(c):
    if c[1] == 1:
        return "T1"
    if c[1] == 2:
        return "T2"
    s = min(c[2], c[3])  # BigCloneEval: min of line- and token-based similarity
    return "VST3" if s >= 0.9 else "ST3" if s >= 0.7 else "MT3" if s >= 0.5 else "WT3/T4"

print("\n== 2. CodeXGLUE labels vs BCB tables (unique unordered pairs)")
print(f"  {'split':5s} {'label':5s} {'in clones':>10s} {'in false_pos':>13s} {'in neither':>11s}")
for name, pairs in splits.items():
    for y in (1, 0):
        c = Counter("clones" if k in clones else "fp" if k in fps else "none"
                    for k, lab in pairs.items() if lab == y)
        print(f"  {name:5s} {y:5d} {c['clones']:10d} {c['fp']:13d} {c['none']:11d}")

print("\n== 3. clone types of positive pairs")
order = ["T1", "T2", "VST3", "ST3", "MT3", "WT3/T4"]
print(f"  {'split':5s} " + " ".join(f"{t:>8s}" for t in order))
for name, pairs in splits.items():
    c = Counter(clone_type(clones[k]) for k, y in pairs.items() if y == 1 and k in clones)
    print(f"  {name:5s} " + " ".join(f"{c[t]:8d}" for t in order))

print("\n== 4. functionalities per split (positive pairs)")
for name, pairs in splits.items():
    c = Counter(clones[k][0] for k, y in pairs.items() if y == 1 and k in clones)
    print(f"  {name}: {len(c)} functionalities")
    for fid, n in c.most_common():
        print(f"     {fid:3d} {fnames[fid][:40]:40s} {n:7d}")

print("\n== 5. test/valid clone groups -> functionality")
for name in ("valid", "test"):
    pairs = splits[name]
    nodes = {x for k in pairs for x in k}
    parent = {i: i for i in nodes}
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for (a, b), y in pairs.items():
        if y == 1:
            parent[find(a)] = find(b)
    groups = defaultdict(list)
    for i in nodes:
        groups[find(i)].append(i)
    for g in sorted(groups.values(), key=len, reverse=True):
        if len(g) < 2:
            break
        gs = set(g)
        fc = Counter(clones[k][0] for k, y in pairs.items() if y == 1 and k[0] in gs and k in clones)
        print(f"  {name} group size {len(g):4d}: " + ", ".join(f"{fnames[f]} ({n})" for f, n in fc.most_common()))
    single = [i for i, g in ((i, find(i)) for i in nodes) if len(groups[g]) == 1]
    fc = Counter()
    for i in single:
        # functionality of a non-clone function: from any BCB relation it has
        hits = {v[0] for k, v in clones.items() if i in k} | {v for k, v in fps.items() if i in k}
        fc[tuple(sorted(hits))] += 1
    print(f"  {name} singletons: {len(single)}; functionality via clones/fp tables:",
          ", ".join(f"{[fnames[x] for x in k] or 'none'}: {n}" for k, n in fc.most_common(6)))

# ---------------------------------------------------------------- write labels
for name, pairs in splits.items():
    with open(f"{out_dir}/{name}_pairs_labelled.tsv", "w") as out:
        out.write("idx1\tidx2\tlabel\tbcb_relation\tfunctionality_id\tclone_type\tsim_line\tsim_token\n")
        for (a, b), y in sorted(pairs.items()):
            if (a, b) in clones:
                c = clones[(a, b)]
                out.write(f"{a}\t{b}\t{y}\tclone\t{c[0]}\t{clone_type(c)}\t{c[2]:.4f}\t{c[3]:.4f}\n")
            elif (a, b) in fps:
                out.write(f"{a}\t{b}\t{y}\tfalse_positive\t{fps[(a, b)]}\t\t\t\n")
            else:
                out.write(f"{a}\t{b}\t{y}\tnone\t\t\t\t\n")
print(f"\nwrote {out_dir}/<split>_pairs_labelled.tsv")
