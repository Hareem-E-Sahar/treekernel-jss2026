"""Clone-graph components within each split, for judging whether they can
serve as retrieval relevance groups."""
import sys
from collections import Counter, defaultdict

data_dir = sys.argv[1]
for name in ("train", "valid", "test"):
    pairs = [tuple(map(int, l.split())) for l in open(f"{data_dir}/{name}.txt")]
    nodes = {x for a, b, _ in pairs for x in (a, b)}
    parent = {i: i for i in nodes}
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for a, b, y in pairs:
        if y == 1:
            parent[find(a)] = find(b)
    comp = {i: find(i) for i in nodes}
    sizes = Counter(comp.values())
    pos = {(min(a, b), max(a, b)) for a, b, y in pairs if y == 1}
    neg = {(min(a, b), max(a, b)) for a, b, y in pairs if y == 0}
    print(f"== {name}: {len(nodes)} functions, {len(pos)} unique pos, {len(neg)} unique neg")
    print(f"  components >1: {sum(s > 1 for s in sizes.values())}, singletons: {sum(s == 1 for s in sizes.values())}")
    print("  size  pos_pairs  neg_in_comp  possible  pos_density")
    per = defaultdict(lambda: [0, 0])
    for a, b in pos:
        per[comp[a]][0] += 1
    for a, b in neg:
        if comp[a] == comp[b]:
            per[comp[a]][1] += 1
    for c, s in sorted(sizes.items(), key=lambda kv: -kv[1]):
        if s < 2:
            break
        p, n = per[c]
        print(f"  {s:4d} {p:10d} {n:12d} {s*(s-1)//2:9d} {p/(s*(s-1)/2):12.3f}")
    # How complete is the labelling? fraction of all function pairs that have a label
    n = len(nodes)
    print(f"  labelled pairs / all pairs: {(len(pos)+len(neg))/(n*(n-1)/2):.3f}")
