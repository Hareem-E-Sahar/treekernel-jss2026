"""Write every BigCloneBench clone pair of type T1, T2, VST3, ST3 or MT3 (the
syntactically similar types) and summarise how many pairs and functions each type has.

usage: extract_syntactic_clones.py <bcb.pgdump file> <out.tsv>
"""
import sys
from collections import Counter, defaultdict

dump_path, out_path = sys.argv[1:3]

def clone_type(syn, sl, st):
    if syn == b"1":
        return "T1"
    if syn == b"2":
        return "T2"
    s = min(float(sl), float(st))
    return "VST3" if s >= 0.9 else "ST3" if s >= 0.7 else "MT3" if s >= 0.5 else "WT3/T4"

pairs = Counter()
funcs = defaultdict(set)
functionalities = defaultdict(set)
inside = False
with open(dump_path, "rb") as f, open(out_path, "w") as out:
    out.write("function_id_one\tfunction_id_two\tfunctionality_id\tclone_type\tsim_line\tsim_token\n")
    for line in f:
        if not inside:
            inside = line.startswith(b"COPY public.clones ")
            continue
        if line == b"\\.\n":
            break
        p = line.split(b"\t")
        t = clone_type(p[4], p[5], p[6])
        pairs[t] += 1
        if t == "WT3/T4":
            continue
        funcs[t].update((p[0], p[1]))
        functionalities[t].add(p[2])
        out.write(f"{p[0].decode()}\t{p[1].decode()}\t{p[2].decode()}\t{t}\t{p[5].decode()}\t{p[6].decode()}\n")

total = sum(pairs.values())
print(f"{'type':8s} {'pairs':>10s} {'share':>7s} {'functions':>10s} {'functionalities':>16s}")
for t in ("T1", "T2", "VST3", "ST3", "MT3", "WT3/T4"):
    nf = len(funcs[t]) if t != "WT3/T4" else "-"
    nfx = len(functionalities[t]) if t != "WT3/T4" else "-"
    print(f"{t:8s} {pairs[t]:10,d} {100*pairs[t]/total:6.2f}% {nf!s:>10s} {nfx!s:>16s}")
allf = set().union(*funcs.values())
print(f"T1-MT3 together: {sum(pairs[t] for t in funcs):,} pairs, {len(allf):,} distinct functions")
