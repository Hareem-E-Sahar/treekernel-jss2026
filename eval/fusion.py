"""Score fusion of a tree-kernel run and a BM25 run (RQ4, PLAN.md §5: complementarity).

usage: fusion.py TK_RUN BM25_RUN OUT_DIR --method rrf|wsum [--w W] [--k 60]

Both runs must score the same queries against the same corpus in the same order.
  tree kernel: normalised kernel exp(logk - (logself_q + logself_c)/2), in [0, 1]
  BM25:        raw score exp(logk), divided by the query's maximum over the corpus -> [0, 1]
  rrf:  1/(k + rank_TK) + 1/(k + rank_BM25); ranks over the whole corpus (query excluded),
        tied scores share their average rank
  wsum: W * TK + (1 - W) * BM25_normalised
Writes OUT_DIR in RetrievalRunner's format (logk = log fused score, logself = 0), so
eval/evaluate.py evaluates it unchanged.
"""
import argparse
import json
from pathlib import Path

import numpy as np


def load(run, normalise):
    run = Path(run)
    q = (run / "query_ids.txt").read_text().split()
    c = (run / "corpus_ids.txt").read_text().split()
    logk = np.fromfile(run / "logk.f64", dtype="<f8").reshape(len(q), len(c))
    logself = np.fromfile(run / "logself.f64", dtype="<f8")
    col = {x: i for i, x in enumerate(c)}
    qcol = np.array([col[x] for x in q])
    with np.errstate(invalid="ignore"):
        s = np.exp(logk - 0.5 * (logself[qcol][:, None] + logself[None, :])) if normalise else np.exp(logk)
    s[np.arange(len(q)), qcol] = np.nan          # the query itself
    return q, c, s


def avg_ranks(s):
    """1-based descending ranks of one row, ties averaged; NaN (the query) gets NaN."""
    ok = ~np.isnan(s)
    v = s[ok]
    order = np.argsort(-v, kind="stable")
    sv = v[order]
    starts = np.flatnonzero(np.r_[True, sv[1:] != sv[:-1]])
    ends = np.r_[starts[1:], len(sv)]
    r = np.repeat((starts + 1 + ends) / 2, ends - starts)
    out = np.full(len(s), np.nan)
    tmp = np.empty(len(sv))
    tmp[order] = r
    out[ok] = tmp
    return out


def fuse(tk_run, bm_run, method, w=0.5, k=60):
    q, c, tk = load(tk_run, True)
    q2, c2, bm = load(bm_run, False)
    assert q == q2 and c == c2, "runs differ in queries or corpus order"
    if method == "rrf":
        f = np.vstack([1 / (k + avg_ranks(a)) + 1 / (k + avg_ranks(b)) for a, b in zip(tk, bm)])
    else:
        mx = np.nanmax(bm, axis=1, keepdims=True)
        f = w * tk + (1 - w) * np.where(mx > 0, bm / np.where(mx > 0, mx, 1), 0)
    return q, c, f


def write(out, q, c, f, meta):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        np.log(f).astype("<f8").tofile(out / "logk.f64")
    np.zeros(len(c)).astype("<f8").tofile(out / "logself.f64")
    (out / "query_ids.txt").write_text("\n".join(q) + "\n")
    (out / "corpus_ids.txt").write_text("\n".join(c) + "\n")
    (out / "meta.json").write_text(json.dumps(meta, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("tk")
    ap.add_argument("bm25")
    ap.add_argument("out")
    ap.add_argument("--method", choices=["rrf", "wsum"], required=True)
    ap.add_argument("--w", type=float, default=0.5)
    ap.add_argument("--k", type=int, default=60)
    a = ap.parse_args()
    q, c, f = fuse(a.tk, a.bm25, a.method, a.w, a.k)
    write(a.out, q, c, f, {"fusion": a.method, "w": a.w if a.method == "wsum" else None,
                           "k": a.k if a.method == "rrf" else None, "tree_kernel_run": a.tk, "bm25_run": a.bm25})
    print(f"{a.method} -> {a.out}")
