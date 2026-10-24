"""First stage of the hybrid: BM25's top k candidates per query (exp_v2, decision 2026-10-20/23).

usage: .venv/bin/python -I exp_v2/hybrid/bm25_topk.py INDEX QUERIES.tsv OUT_DIR [--k 200]
  -> OUT_DIR/topk.tsv    query_id, rank (1..k), candidate_id, bm25_score
     OUT_DIR/timing.tsv  query_id, es_took_ms, client_ms (the cost of the first stage)
Same query as bm25/run_bm25.py (mode "all": every token of the query, boosted by its count) on the same index, but
Elasticsearch returns only the k + 1 best hits; the query itself is dropped, the next k are kept. Ties at the cut are
broken by Elasticsearch (internal document order). The top 100 for k = 100 are the first 100 rows here.
"""
import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bm25"))
from code_tokens import tokens  # noqa: E402
from run_bm25 import es, read_sources  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("index")
ap.add_argument("queries")
ap.add_argument("out", type=Path)
ap.add_argument("--k", type=int, default=200)
a = ap.parse_args()
a.out.mkdir(parents=True, exist_ok=True)
meta_idx = json.loads((ROOT / f"results/bm25/index_{a.index}.json").read_text())
src = read_sources(meta_idx["sources"])
qids = [l.split("\t", 1)[0] for l in Path(a.queries).read_text().splitlines()[1:] if l.strip()]
t_all = time.time()
with open(a.out / "topk.tsv", "w") as o, open(a.out / "timing.tsv", "w") as ot:
    o.write("query_id\trank\tcandidate_id\tbm25_score\n")
    ot.write("query_id\tes_took_ms\tclient_ms\n")
    for q in qids:
        tf = Counter(tokens(src[q]))
        body = {"bool": {"should": [{"term": {"code": {"value": t, "boost": n}}} for t, n in tf.items()]}}
        t0 = time.time()
        res = es("POST", f"/{a.index}/_search?filter_path=took,hits.hits._id,hits.hits._score",
                 {"size": a.k + 1, "_source": False, "track_total_hits": False, "query": body})
        ms = (time.time() - t0) * 1000
        hits = [h for h in res.get("hits", {}).get("hits", []) if h["_id"] != q][:a.k]
        o.writelines(f"{q}\t{r}\t{h['_id']}\t{h['_score']!r}\n" for r, h in enumerate(hits, 1))
        ot.write(f"{q}\t{res['took']}\t{ms:.1f}\n")
(a.out / "meta.json").write_text(json.dumps({
    "stage": "BM25 top k", "index": a.index, "queries": a.queries, "n_queries": len(qids), "k": a.k,
    "wall_seconds": round(time.time() - t_all, 1), "elasticsearch": es("GET", "/")["version"]["number"]}, indent=2))
print(f"top {a.k}: {len(qids)} queries -> {a.out} ({time.time() - t_all:.0f}s)")
