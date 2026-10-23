"""Assemble a run for a query list from the rows of existing runs over the same corpus.

usage: merge_runs.py QUERIES OUT_DIR RUN [RUN ...]
  QUERIES  tsv with a function_id column; the output's rows follow its order
  RUN      run directories (logk.f64, logself.f64, query_ids.txt, corpus_ids.txt, meta.json); a query's row is taken
           from the first run that has it. All runs must have the same corpus order and the same logself (the
           self-similarities depend only on the corpus and the setting), which is checked.
Rows are copied unchanged, so the output equals a single run over QUERIES with the same method and setting.
"""
import json
import sys
from pathlib import Path

import numpy as np

qfile, out, *runs = sys.argv[1:]
out = Path(out)
queries = [l.split("\t", 1)[0] for l in open(qfile).read().splitlines()[1:] if l]
src = []
for r in map(Path, runs):
    q = (r / "query_ids.txt").read_text().split()
    c = (r / "corpus_ids.txt").read_text().split()
    src.append((r, {x: i for i, x in enumerate(q)}, c,
                np.memmap(r / "logk.f64", dtype="<f8", mode="r", shape=(len(q), len(c)))))
corpus = src[0][2]
logself = (src[0][0] / "logself.f64").read_bytes()
for r, _, c, _ in src[1:]:
    assert c == corpus, f"corpus order differs: {r}"
    assert (r / "logself.f64").read_bytes() == logself, f"logself differs: {r}"
where = {}
for k, (_, rows, _, _) in enumerate(src):
    for q in queries:
        if q not in where and q in rows:
            where[q] = k
missing = [q for q in queries if q not in where]
assert not missing, f"{len(missing)} queries in no run, e.g. {missing[:5]}"

out.mkdir(parents=True, exist_ok=True)
with open(out / "logk.f64", "wb") as fo:
    for q in queries:
        k = where[q]
        np.asarray(src[k][3][src[k][1][q]]).astype("<f8").tofile(fo)
(out / "logself.f64").write_bytes(logself)
(out / "query_ids.txt").write_text("\n".join(queries) + "\n")
(out / "corpus_ids.txt").write_text("\n".join(corpus) + "\n")
meta = json.loads((src[0][0] / "meta.json").read_text())
meta.update(queries=qfile, n_queries=len(queries),
            merged_from={str(r): sum(1 for q in queries if where[q] == k) for k, (r, _, _, _) in enumerate(src)})
for key in ("wall_seconds", "evaluations", "finished"):
    meta.pop(key, None)
(out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
print(f"{out}: {len(queries)} queries from " + ", ".join(f"{Path(r).name}: {n}" for r, n in meta["merged_from"].items()))
