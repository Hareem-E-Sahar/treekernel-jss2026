"""Stream the BigCloneBench pg_dump once and keep only rows that involve the
CodeXGLUE functions. Writes TSVs to the output directory.

usage: extract_bcb_subset.py <bcb.pgdump file> <codexglue data.jsonl> <out dir>
"""
import json
import os
import sys
import time

dump_path, jsonl_path, out_dir = sys.argv[1:4]
os.makedirs(out_dir, exist_ok=True)

ids = set()
with open(jsonl_path) as f:
    for line in f:
        ids.add(int(json.loads(line)["idx"]))
ids_b = {str(i).encode() for i in ids}

# table -> (indices of id columns, keep rule: "all" | "any" | "both" | "every")
WANTED = {
    "public.functionalities": ((), "every"),
    "public.functions": ((4,), "any"),
    "public.clones": ((0, 1), "both"),
    "public.false_positives": ((0, 1), "both"),
    "public.tagged": ((1,), "any"),
    "public.judged": ((1,), "any"),
    "public.samples": ((1,), "any"),
}

outs, counts, scanned = {}, {}, {}
current = None
t0 = time.time()
with open(dump_path, "rb") as f:
    for n, line in enumerate(f):
        if current is None:
            if line.startswith(b"COPY "):
                head = line.decode()
                table = head.split()[1]
                if table in WANTED:
                    cols = head[head.index("(") + 1:head.index(")")]
                    current = table
                    name = table.split(".")[1]
                    outs[table] = open(f"{out_dir}/{name}.tsv", "w")
                    outs[table].write(cols.replace(", ", "\t").replace('"', "") + "\n")
                    counts[table] = scanned[table] = 0
                    print(f"[{time.time()-t0:6.0f}s] reading {table}", flush=True)
            continue
        if line == b"\\.\n":
            outs[current].close()
            print(f"[{time.time()-t0:6.0f}s]   kept {counts[current]} of {scanned[current]} rows", flush=True)
            current = None
            continue
        scanned[current] += 1
        cols, rule = WANTED[current]
        if rule != "every":
            fields = line.rstrip(b"\n").split(b"\t")
            hits = [fields[c] in ids_b for c in cols]
            if not (all(hits) if rule == "both" else any(hits)):
                continue
        outs[current].write(line.decode("utf-8", "replace"))
        counts[current] += 1
print(f"done in {time.time()-t0:.0f}s")
