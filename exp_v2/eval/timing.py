"""Summarise exp_v2/scripts/run_timing.sh: cost of evaluating the 100 RQ2 queries of one replicate set, one thread,
corpus with false positives (72,782 methods).

usage: .venv/bin/python exp_v2/eval/timing.py   -> exp_v2/results/timing/{summary.tsv, tables.md}

Java steps (java.tsv): per query = (wall time with the 100 queries - wall time with 0 queries) / 100; set-up = the
0-query time (JVM start and reading the trees; for full rankings also the corpus self-similarities).
BM25: Elasticsearch's `took` and the client time (incl. returning the scores) per query. CodeBERT: encode + cosine.
Hybrid per query = BM25 top-200 client time + re-ranking time per query (k = 100 or 200).
"""
import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
O = ROOT / "exp_v2/results/timing"
KERNELS = ["STK", "SSTK", "PTK"]
J = {(r["step"], int(r["queries"])): float(r["wall_s"]) for r in csv.DictReader(open(O / "java.tsv"), delimiter="\t")}
N = len(list(csv.DictReader(open(O / "queries.tsv"), delimiter="\t")))


def es(path):
    rows = list(csv.DictReader(open(path), delimiter="\t"))
    return np.mean([float(r["es_took_ms"]) for r in rows]) / 1000, np.mean([float(r["client_ms"]) for r in rows]) / 1000


def kernel_only(path):
    """mean summed kernel time per query (s) from HybridRerank's timing file"""
    return np.mean([int(r["kernel_ns"]) / 1e9 for r in csv.DictReader(open(path), delimiter="\t")])


rows = []   # (group, method, setup_s, per_query_s, total_100_s, note)
for k in KERNELS:
    setup, full = J[(f"full_{k}", 0)], J[(f"full_{k}", N)]
    rows.append(("full ranking", k, setup, (full - setup) / N, full, ""))
bm_took, bm_client = es(O / "runs/bm25_full/timing.tsv")
rows.append(("full ranking", "BM25", float("nan"), bm_client, bm_client * N, f"Elasticsearch took {bm_took:.3f} s per query"))
cb = json.loads((O / "codebert.json").read_text())
rows.append(("full ranking", "CodeBERT", cb["model_load_s"], cb["query_s_mean"], cb["query_s_mean"] * N,
             "encode + cosine; corpus embeddings precomputed"))
st_took, st_client = es(O / "runs/bm25_top200/timing.tsv")
rows.append(("hybrid stage 1", "BM25 top 200", float("nan"), st_client, st_client * N, f"Elasticsearch took {st_took:.3f} s"))
for k in KERNELS:
    setup = J[(f"hybrid_{k}_empty", 0)]
    for K in (100, 200):
        w = J[(f"hybrid_{k}_k{K}", N)]
        per = (w - setup) / N
        ko = kernel_only(O / f"runs/hybrid_{k}_k{K}.tsv.timing.tsv")
        rows.append((f"hybrid stage 2 (k={K})", k, setup, per, w, f"kernel evaluations alone {ko:.3f} s per query"))
with open(O / "summary.tsv", "w") as o:
    o.write("group\tmethod\tsetup_s\tper_query_s\ttotal_s\tnote\n")
    o.writelines(f"{g}\t{m}\t{s:.2f}\t{p:.4f}\t{t:.1f}\t{n}\n" for g, m, s, p, t, n in rows)

per = {(g, m): p for g, m, _, p, _, _ in rows}
L = [f"# Cost of evaluating the {N} RQ2 queries of one replicate set (one thread, 72,782-method corpus)", "",
     "| Group | Method | Set-up (s) | Per query (s) | 100 queries (s) | Note |", "|---|---|---|---|---|---|"]
L += [f"| {g} | {m} | {'' if np.isnan(s) else f'{s:.1f}'} | {p:.3f} | {t:.0f} | {n} |" for g, m, s, p, t, n in rows]
L += ["", "## Hybrid against the full kernel ranking (per query)", "",
      "| Kernel | k | Hybrid (stage 1 + 2), s | Full ranking, s | Speed-up |", "|---|---|---|---|---|"]
for k in KERNELS:
    for K in (100, 200):
        h = per[("hybrid stage 1", "BM25 top 200")] + per[(f"hybrid stage 2 (k={K})", k)]
        f = per[("full ranking", k)]
        L.append(f"| {k} | {K} | {h:.3f} | {f:.2f} | {f / h:.0f}× |")
(O / "tables.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
