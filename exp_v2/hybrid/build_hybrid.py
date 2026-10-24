"""Build a hybrid run (BM25 top k re-ranked by a tree kernel) in the run format, so exp_v2/eval/evaluate.py scores it.

usage: build_hybrid.py BM25_RUN TOPK.tsv PAIRS_SCORED.tsv KERNEL_RUN K OUT_DIR
  BM25_RUN      full BM25 run over the queries (exp_v2/results/full/runs/bm25)
  TOPK.tsv      exp_v2/hybrid/bm25_topk.py output (top 200; the first K ranks are used)
  PAIRS_SCORED  HybridRerank output: log K(q, c) for those pairs
  KERNEL_RUN    a full run of the same kernel and setting on the same corpus: only its logself.f64 is used
Ranking per query: BM25's top K first, ordered by the normalised kernel exp(log K(q,c) - (log K(q,q) + log K(c,c))/2);
then every other method in BM25 order (BM25 non-matches last, as in the BM25 run). Stored as logk = log(2 + kernel)
for the top K and log(BM25 / the query's best BM25 score) below, so the top K always come first; logself = 0.
Checks that the top-k scores equal the BM25 run's scores (same index, same query).
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

bm, topk, scored, krun, K, out = sys.argv[1:]
K, out = int(K), Path(out)
bq = (Path(bm) / "query_ids.txt").read_text().split()
bc = (Path(bm) / "corpus_ids.txt").read_text().split()
assert (Path(krun) / "corpus_ids.txt").read_text().split() == bc, "corpus order differs"
B = np.memmap(Path(bm) / "logk.f64", dtype="<f8", mode="r", shape=(len(bq), len(bc)))
logself = np.fromfile(Path(krun) / "logself.f64", dtype="<f8")
col = {c: i for i, c in enumerate(bc)}

top = defaultdict(list)                                 # query -> [(column, bm25 score)] by rank
for r in csv.DictReader(open(topk), delimiter="\t"):
    if int(r["rank"]) <= K:
        top[r["query_id"]].append((col[r["candidate_id"]], float(r["bm25_score"])))
lk = {}
for r in csv.DictReader(open(scored), delimiter="\t"):
    lk[(r["query_id"], col[r["candidate_id"]])] = float(r["logk"])

out.mkdir(parents=True, exist_ok=True)
worst = 0.0
with open(out / "logk.f64", "wb") as fo:
    for i, q in enumerate(bq):
        row = np.asarray(B[i], dtype="<f8").copy()     # log BM25; -inf non-matches; NaN the query
        mx = np.nanmax(row)
        with np.errstate(invalid="ignore"):
            row = row - mx                              # log(BM25 / max) <= 0
        cols = np.array([c for c, _ in top[q]], dtype=int)
        bm_es = np.log([s for _, s in top[q]])
        worst = max(worst, float(np.max(np.abs(bm_es - mx - row[cols]))) if len(cols) else 0.0)
        kv = np.array([lk[(q, c)] for c in cols])
        with np.errstate(invalid="ignore"):
            norm = np.exp(kv - 0.5 * (logself[col[q]] + logself[cols]))
        row[cols] = np.log(2.0 + np.nan_to_num(norm, nan=0.0))
        row.astype("<f8").tofile(fo)
assert worst < 1e-5, f"top-k BM25 scores differ from the BM25 run by up to {worst}"
np.zeros(len(bc)).astype("<f8").tofile(out / "logself.f64")
(out / "query_ids.txt").write_text("\n".join(bq) + "\n")
(out / "corpus_ids.txt").write_text("\n".join(bc) + "\n")
(out / "meta.json").write_text(json.dumps({
    "kernel": "hybrid", "first_stage": "BM25", "k": K, "bm25_run": bm, "topk": topk, "pairs_scored": scored,
    "kernel_run_logself": krun, "kernel_meta": json.loads((Path(krun) / "meta.json").read_text()),
    "n_queries": len(bq), "n_corpus": len(bc), "max_bm25_score_mismatch_log": worst}, indent=2))
print(f"hybrid k={K}: {len(bq)} queries -> {out} (top-k BM25 mismatch {worst:.1e})")
