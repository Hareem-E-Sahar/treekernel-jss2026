"""Write the BCB clone type of every clone pair that involves one of the queries.

usage: extract_query_clone_types.py <bcb.pgdump file> <queries.tsv> <out.tsv>
"""
import sys

dump_path, queries_path, out_path = sys.argv[1:4]
queries = {l.split("\t")[0].encode() for l in open(queries_path).read().splitlines()[1:]}

def clone_type(syn, sl, st):
    if syn == b"1":
        return "T1"
    if syn == b"2":
        return "T2"
    s = min(float(sl), float(st))
    return "VST3" if s >= 0.9 else "ST3" if s >= 0.7 else "MT3" if s >= 0.5 else "WT3/T4"

inside = False
n = 0
with open(dump_path, "rb") as f, open(out_path, "w") as out:
    out.write("query_id\tother_id\tfunctionality_id\tclone_type\tsim_line\tsim_token\n")
    for line in f:
        if not inside:
            if line.startswith(b"COPY public.clones "):
                inside = True
            continue
        if line == b"\\.\n":
            break
        p = line.split(b"\t")
        for q, o in ((p[0], p[1]), (p[1], p[0])):
            if q in queries:
                out.write(f"{q.decode()}\t{o.decode()}\t{p[2].decode()}\t{clone_type(p[4], p[5], p[6])}\t{p[5].decode()}\t{p[6].decode()}\n")
                n += 1
print(f"wrote {n} query clone pairs")
