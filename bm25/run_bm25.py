"""BM25 retrieval with Elasticsearch (PLAN.md §5.2), written in the same format as RetrievalRunner,
so that eval/evaluate.py evaluates it unchanged.

usage:
  run_bm25.py index INDEX TREES.tsv SOURCE.tsv [SOURCE.tsv ...]
      Corpus = the ids of TREES.tsv, in that order (e.g. data/trees_main/D.tsv); source text from
      the SOURCE files (function_id, ..., source_escaped). One shard, so IDF is corpus-wide.
  run_bm25.py query INDEX QUERIES.tsv OUT_DIR [--mode all|mlt]
      all: every token of the query method is a term; a term occurring n times in the query is a
           term query with boost n (= Lucene's match query on the token stream, without the
           clause-per-occurrence blow-up).
      mlt: More Like This with Elasticsearch's defaults (max_query_terms 25, min_term_freq 2,
           min_doc_freq 5), as in the user's earlier BM25 study.
Elasticsearch on localhost:9201 (scripts/es_start.sh). BM25 k1 = 1.2, b = 0.75 (defaults).

Output (OUT_DIR): logk.f64 = log BM25 score (non-matching = -inf; the query itself = NaN),
logself.f64 = zeros (so evaluate.py's "normalised score" is the raw BM25 score), query_ids.txt,
corpus_ids.txt, meta.json, timing.tsv (per query: Elasticsearch `took` and client wall time, ms).
"""
import json
import math
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from code_tokens import tokens, unescape  # noqa: E402

ES = "http://127.0.0.1:9201"


def es(method, path, body=None, ndjson=False):
    data = None
    if body is not None:
        data = body.encode() if ndjson else json.dumps(body).encode()
    req = urllib.request.Request(ES + path, data=data, method=method,
                                 headers={"Content-Type": "application/x-ndjson" if ndjson else "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def corpus_ids(trees):
    with open(trees, "rb") as f:
        next(f)
        return [l.split(b"\t", 1)[0].decode() for l in f if l.strip()]


def read_sources(paths):
    src = {}
    for p in paths:
        lines = Path(p).read_bytes().split(b"\n")   # split on \n only: the code contains raw \r
        head = lines[0].decode().split("\t")
        k = head.index("source_escaped")
        for l in lines[1:]:
            if l:
                f = l.decode("utf-8", "replace").split("\t")
                src[f[0]] = unescape(f[k])
    return src


def index(name, trees, sources):
    ids = corpus_ids(trees)
    src = read_sources(sources)
    missing = [i for i in ids if i not in src]
    assert not missing, f"{len(missing)} corpus ids without source, e.g. {missing[:3]}"
    try:
        es("DELETE", f"/{name}")
    except urllib.error.HTTPError:
        pass
    es("PUT", f"/{name}", {
        "settings": {"number_of_shards": 1, "number_of_replicas": 0, "max_result_window": 200000,
                     "refresh_interval": "-1",
                     "similarity": {"default": {"type": "BM25", "k1": 1.2, "b": 0.75}},
                     "analysis": {"analyzer": {"ws_lower": {"type": "custom", "tokenizer": "whitespace",
                                                            "filter": ["lowercase"]}}}},
        "mappings": {"properties": {"code": {"type": "text", "analyzer": "ws_lower"}}}})
    t0 = time.time()
    for s in range(0, len(ids), 1000):
        body = "".join(json.dumps({"index": {"_id": i}}) + "\n" + json.dumps({"code": " ".join(tokens(src[i]))}) + "\n"
                       for i in ids[s:s + 1000])
        r = es("POST", f"/{name}/_bulk", body, ndjson=True)
        assert not r["errors"], r
    es("POST", f"/{name}/_refresh")
    es("POST", f"/{name}/_forcemerge?max_num_segments=1")
    n = es("GET", f"/{name}/_count")["count"]
    assert n == len(ids), (n, len(ids))
    secs = time.time() - t0
    Path(f"results/bm25/index_{name}.json").parent.mkdir(parents=True, exist_ok=True)
    Path(f"results/bm25/index_{name}.json").write_text(json.dumps(
        {"index": name, "trees": trees, "sources": sources, "docs": n, "index_seconds": round(secs, 1),
         "store_bytes": es("GET", f"/{name}/_stats/store")["_all"]["primaries"]["store"]["size_in_bytes"]}, indent=2))
    print(f"indexed {n} methods into {name} in {secs:.1f}s")


def query(name, queries, out, mode="all"):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    qids = [l.split("\t", 1)[0] for l in Path(queries).read_text().splitlines()[1:] if l.strip()]
    meta_idx = json.loads(Path(f"results/bm25/index_{name}.json").read_text())
    ids = corpus_ids(meta_idx["trees"])          # column order = the trees file, as for the kernels
    col = {c: i for i, c in enumerate(ids)}
    src = read_sources(meta_idx["sources"])
    logk = np.full((len(qids), len(ids)), -np.inf)
    timing = []
    t_all = time.time()
    for r, q in enumerate(qids):
        if mode == "all":
            tf = Counter(tokens(src[q]))
            body = {"bool": {"should": [{"term": {"code": {"value": t, "boost": n}}} for t, n in tf.items()]}}
        else:
            body = {"more_like_this": {"fields": ["code"], "like": [{"_index": name, "_id": q}]}}
        t0 = time.time()
        res = es("POST", f"/{name}/_search?filter_path=took,hits.hits._id,hits.hits._score",
                 {"size": len(ids), "_source": False, "track_total_hits": False, "query": body})
        timing.append((q, res["took"], round((time.time() - t0) * 1000, 1)))
        for h in res.get("hits", {}).get("hits", []):
            logk[r, col[h["_id"]]] = math.log(h["_score"]) if h["_score"] > 0 else -np.inf
        logk[r, col[q]] = np.nan
    logk.astype("<f8").tofile(out / "logk.f64")
    np.zeros(len(ids)).astype("<f8").tofile(out / "logself.f64")
    (out / "query_ids.txt").write_text("\n".join(qids) + "\n")
    (out / "corpus_ids.txt").write_text("\n".join(ids) + "\n")
    with open(out / "timing.tsv", "w") as o:
        o.write("function_id\tes_took_ms\tclient_ms\n")
        o.writelines(f"{q}\t{a}\t{b}\n" for q, a, b in timing)
    (out / "meta.json").write_text(json.dumps({
        "kernel": "BM25", "mode": mode, "k1": 1.2, "b": 0.75, "index": name, "queries": queries,
        "n_queries": len(qids), "n_corpus": len(ids), "wall_seconds": round(time.time() - t_all, 1),
        "elasticsearch": es("GET", "/")["version"]["number"], "tokenisation": "bm25/code_tokens.py"}, indent=2))
    print(f"{mode}: {len(qids)} queries x {len(ids)} -> {out} ({time.time() - t_all:.0f}s)")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "index":
        index(a[1], a[2], a[3:])
    else:
        mode = a[a.index("--mode") + 1] if "--mode" in a else "all"
        query(a[1], a[2], a[3], mode)
