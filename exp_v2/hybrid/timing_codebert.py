"""CodeBERT cost per query for a given query file (exp_v2 timing; embed/codebert.py's `timing` is fixed to the frozen
experiment's 20 timing queries).

usage: HF_HOME=third_party/hf HF_HUB_OFFLINE=1 .venv/bin/python exp_v2/hybrid/timing_codebert.py QUERIES.tsv OUT.json
       ... timing_codebert.py --encode-sample N OUT.json   (one-off corpus encoding, estimated from N random methods)
Same measurement as embed/codebert.py timing: one thread; model load (one-off); per query = encoding the query + cosine
against the stored corpus embeddings (zero-shot weights; the fine-tuned models have the same architecture and cost).
Corpus encoding: encoding N random corpus methods one at a time (seed 20261027), mean x corpus size.
"""
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "embed"))
import codebert as cb  # noqa: E402

SAMPLE = int(sys.argv[2]) if sys.argv[1] == "--encode-sample" else 0
queries, out = (None, sys.argv[3]) if SAMPLE else sys.argv[1:3]
torch = cb.torch_setup()
torch.set_num_threads(1)
t = time.time()
tok, m = cb.load_model(cb.MODEL)
m.eval()
load_s = time.time() - t
trees, source = ROOT / "data/trees_e5/D.tsv", ROOT / "data/trees_e5/source.tsv"
corpus = cb.ids_of(trees)
col = {c: i for i, c in enumerate(corpus)}
src = cb.sources(source)
E = torch.from_numpy(np.load(ROOT / "data/codebert/emb/zeroshot_e5.npy"))
assert len(E) == len(corpus), (len(E), len(corpus))
qs = [] if SAMPLE else [r["function_id"] for r in csv.DictReader(open(queries), delimiter="\t")]


def enc(i):
    x = tok([src[i]], truncation=True, max_length=512, return_tensors="pt")
    v = m(**x).last_hidden_state[:, 0].float()
    return torch.nn.functional.normalize(v, dim=-1)[0]


per_query, per_method = [], []
with torch.no_grad(), torch.autocast("cpu", dtype=torch.bfloat16):
    enc(corpus[0])                                      # warm-up
    for i in np.random.default_rng(20261027).choice(len(corpus), SAMPLE, replace=False):
        t = time.time()
        enc(corpus[i])
        per_method.append(time.time() - t)
    for q in qs:
        t = time.time()
        s = E @ enc(q)
        s[col[q]] = float("nan")
        per_query.append(time.time() - t)
if SAMPLE:
    Path(out).write_text(json.dumps({
        "threads": 1, "n_corpus": len(corpus), "model_load_s": round(load_s, 2), "sample_methods": SAMPLE,
        "encode_ms_per_method_mean": round(1000 * float(np.mean(per_method)), 1),
        "encode_ms_per_method_median": round(1000 * float(np.median(per_method)), 1),
        "corpus_encoding_s_estimate": round(float(np.mean(per_method)) * len(corpus), 1)}, indent=1))
    print(Path(out).read_text())
    sys.exit()
Path(out).write_text(json.dumps({
    "threads": 1, "queries": queries, "n_queries": len(qs), "n_corpus": len(corpus), "model_load_s": round(load_s, 2),
    "query_s_mean": round(float(np.mean(per_query)), 4), "query_s_median": round(float(np.median(per_query)), 4),
    "query_s_min": round(min(per_query), 4), "query_s_max": round(max(per_query), 4),
    "query_s_total": round(float(np.sum(per_query)), 2)}, indent=1))
print(Path(out).read_text())
