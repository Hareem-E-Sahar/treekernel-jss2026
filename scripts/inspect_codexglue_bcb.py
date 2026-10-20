"""Sanity checks on the CodeXGLUE BigCloneBench files, and recovery of
functionality-like groups from the positive clone pairs."""
import json
import sys
from collections import Counter, defaultdict

data_dir = sys.argv[1]

funcs = {}
with open(f"{data_dir}/data.jsonl") as f:
    for line in f:
        d = json.loads(line)
        funcs[int(d["idx"])] = d["func"]
print(f"functions: {len(funcs)}  (unique ids, from data.jsonl)")
ids = sorted(funcs)
print(f"id range: {ids[0]} .. {ids[-1]}")

splits = {}
for name in ("train", "valid", "test"):
    pairs = []
    with open(f"{data_dir}/{name}.txt") as f:
        for line in f:
            a, b, y = line.split()
            pairs.append((int(a), int(b), int(y)))
    splits[name] = pairs

print("\n== pairs per split")
for name, pairs in splits.items():
    labels = Counter(y for _, _, y in pairs)
    missing = sum(a not in funcs or b not in funcs for a, b, _ in pairs)
    unordered = {(min(a, b), max(a, b)) for a, b, _ in pairs}
    self_pairs = sum(a == b for a, b, _ in pairs)
    print(f"{name:5s} pairs={len(pairs):7d} pos={labels[1]:7d} neg={labels[0]:7d} "
          f"missing_ids={missing} dup_unordered={len(pairs) - len(unordered)} self_pairs={self_pairs}")

print("\n== function overlap between splits")
fsets = {n: {x for a, b, _ in p for x in (a, b)} for n, p in splits.items()}
for n, s in fsets.items():
    print(f"{n:5s} uses {len(s)} functions")
for x, y in (("train", "valid"), ("train", "test"), ("valid", "test")):
    print(f"{x}&{y}: {len(fsets[x] & fsets[y])} shared functions")
print(f"functions in no split: {len(set(funcs) - set().union(*fsets.values()))}")

print("\n== pair overlap / label conflicts across splits")
lab = defaultdict(set)
for n, p in splits.items():
    for a, b, y in p:
        lab[(min(a, b), max(a, b))].add(y)
print(f"unordered pairs with conflicting labels: {sum(len(v) > 1 for v in lab.values())}")
pset = {n: {(min(a, b), max(a, b)) for a, b, _ in p} for n, p in splits.items()}
for x, y in (("train", "valid"), ("train", "test"), ("valid", "test")):
    print(f"{x}&{y}: {len(pset[x] & pset[y])} shared pairs")

print("\n== connected components of the positive (clone) graph, all splits")
parent = {i: i for i in funcs}
def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i
for p in splits.values():
    for a, b, y in p:
        if y == 1:
            parent[find(a)] = find(b)
comp = {i: find(i) for i in funcs}
sizes = Counter(comp.values())
in_pos = {x for p in splits.values() for a, b, y in p if y == 1 for x in (a, b)}
big = [s for s in sizes.values() if s > 1]
print(f"components with >1 function: {len(big)}; singletons: {sum(1 for s in sizes.values() if s == 1)}")
print(f"functions in any positive pair: {len(in_pos)}")
print("largest component sizes:", sorted(big, reverse=True)[:20])

neg_same = neg_diff = 0
for p in splits.values():
    for a, b, y in p:
        if y == 0:
            if comp[a] == comp[b]:
                neg_same += 1
            else:
                neg_diff += 1
print(f"negative pairs inside one component: {neg_same}; across components: {neg_diff}")

# Is the positive graph complete within each component (clone classes) or sparse?
pos_pairs = {(min(a, b), max(a, b)) for p in splits.values() for a, b, y in p if y == 1}
members = defaultdict(list)
for i, c in comp.items():
    members[c].append(i)
print("\ncomponent  size  labelled_pos_pairs  possible_pairs  density")
for c, m in sorted(members.items(), key=lambda kv: -len(kv[1]))[:15]:
    if len(m) < 2:
        break
    n = len(m)
    k = sum(1 for (a, b) in pos_pairs if comp[a] == c)
    print(f"{c:10d} {n:5d} {k:18d} {n*(n-1)//2:15d} {k/(n*(n-1)/2):8.3f}")

with open(f"{data_dir}/../derived_components.tsv", "w") as out:
    out.write("idx\tcomponent\tcomponent_size\n")
    for i in ids:
        out.write(f"{i}\t{comp[i]}\t{sizes[comp[i]]}\n")
