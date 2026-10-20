"""Stream the BigCloneBench pg_dump once and write the function-level tables
needed for the full-benchmark experiments.

usage: extract_full_bcb.py <bcb.pgdump file> <out dir>

Writes:
  tp_functionalities.tsv  function_id, functionality_id   (from `clones`: true positives)
  judged.tsv              functionality_id, function_id, tp, fp
  functions.tsv           `functions` rows for every id in clones or false_positives
  functionalities.tsv     all 43 rows
  clone_type_counts.tsv   clone pairs per functionality and clone type
"""
import os
import sys
import time
from collections import Counter, defaultdict

dump_path, out_dir = sys.argv[1:3]
os.makedirs(out_dir, exist_ok=True)

def clone_type(syn, sl, st):
    if syn == b"1":
        return "T1"
    if syn == b"2":
        return "T2"
    s = min(float(sl), float(st))
    return "VST3" if s >= 0.9 else "ST3" if s >= 0.7 else "MT3" if s >= 0.5 else "WT3/T4"

tp = defaultdict(set)          # function id -> functionalities (true positive)
fp_ids = set()                 # ids appearing in false_positives
type_counts = Counter()
t0 = time.time()
current = None
out = None
with open(dump_path, "rb") as f:
    for line in f:
        if current is None:
            if line.startswith(b"COPY "):
                table = line.split()[1].decode()
                if table in ("public.clones", "public.false_positives", "public.functions",
                             "public.functionalities", "public.judged"):
                    current = table
                    cols = line.decode()
                    cols = cols[cols.index("(") + 1:cols.index(")")].replace(", ", "\t").replace('"', "")
                    if table in ("public.functions", "public.functionalities", "public.judged"):
                        out = open(f"{out_dir}/{table.split('.')[1]}.tsv", "w")
                        out.write(cols + "\n")
                    print(f"[{time.time()-t0:5.0f}s] {table}", flush=True)
            continue
        if line == b"\\.\n":
            if out:
                out.close()
                out = None
            current = None
            continue
        p = line.rstrip(b"\n").split(b"\t")
        if current == "public.clones":
            a, b, func = int(p[0]), int(p[1]), int(p[2])
            tp[a].add(func)
            tp[b].add(func)
            type_counts[(func, clone_type(p[4], p[5], p[6]))] += 1
        elif current == "public.false_positives":
            fp_ids.add(int(p[0]))
            fp_ids.add(int(p[1]))
        elif current == "public.functions":
            fid = int(p[4])
            if fid in tp or fid in fp_ids:
                out.write(line.decode("utf-8", "replace"))
        else:
            out.write(line.decode("utf-8", "replace"))

with open(f"{out_dir}/tp_functionalities.tsv", "w") as o:
    o.write("function_id\tfunctionality_id\n")
    for fid in sorted(tp):
        for func in sorted(tp[fid]):
            o.write(f"{fid}\t{func}\n")
with open(f"{out_dir}/clone_type_counts.tsv", "w") as o:
    o.write("functionality_id\tclone_type\tpairs\n")
    for (func, t), n in sorted(type_counts.items()):
        o.write(f"{func}\t{t}\t{n}\n")
print(f"done in {time.time()-t0:.0f}s: {len(tp)} true-positive functions, "
      f"{sum(type_counts.values())} clone pairs")
