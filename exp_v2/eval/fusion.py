"""Score fusion of a tree-kernel run and another run (BM25 or CodeBERT): exp_v2 copy of eval/fusion.py.

usage: fusion.py TK_RUN OTHER_RUN OUT_DIR --method rrf|wsum [--w W] [--k 60]

Same definitions as eval/fusion.py (tree kernel: normalised kernel; other run: exp(logk) divided by the
query's maximum; rrf: 1/(k + rank_TK) + 1/(k + rank_other), average ranks over the whole corpus;
wsum: W * TK + (1 - W) * other_normalised). Difference: both runs are memory-mapped and fused in blocks
of query rows, and the output is written block by block (runs on the 72,782-method corpus are 2.5 GB).
"""
import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("fusion_orig", ROOT / "eval/fusion.py")   # same name as this file
_orig = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_orig)
avg_ranks = _orig.avg_ranks

BLOCK = 128


def open_run(run):
    run = Path(run)
    q = (run / "query_ids.txt").read_text().split()
    c = (run / "corpus_ids.txt").read_text().split()
    logk = np.memmap(run / "logk.f64", dtype="<f8", mode="r", shape=(len(q), len(c)))
    logself = np.fromfile(run / "logself.f64", dtype="<f8")
    col = {x: i for i, x in enumerate(c)}
    return q, c, logk, logself, np.array([col[x] for x in q])


def block_scores(logk, logself, qcol, rows, normalise):
    with np.errstate(invalid="ignore"):
        s = np.exp(np.asarray(logk[rows]) - 0.5 * (logself[qcol[rows]][:, None] + logself[None, :])) if normalise \
            else np.exp(np.asarray(logk[rows]))
    s[np.arange(len(rows)), qcol[rows]] = np.nan          # the query itself
    return s


def fuse(tk_run, other_run, out, method, w=0.5, k=60, meta=None):
    q, c, tk_k, tk_s, qcol = open_run(tk_run)
    q2, c2, ot_k, ot_s, _ = open_run(other_run)
    assert q == q2 and c == c2, "runs differ in queries or corpus order"
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "logk.f64", "wb") as fo:
        for start in range(0, len(q), BLOCK):
            rows = np.arange(start, min(start + BLOCK, len(q)))
            a = block_scores(tk_k, tk_s, qcol, rows, True)
            b = block_scores(ot_k, ot_s, qcol, rows, False)
            if method == "rrf":
                f = np.vstack([1 / (k + avg_ranks(x)) + 1 / (k + avg_ranks(y)) for x, y in zip(a, b)])
            else:
                mx = np.nanmax(b, axis=1, keepdims=True)
                f = w * a + (1 - w) * np.where(mx > 0, b / np.where(mx > 0, mx, 1), 0)
            with np.errstate(divide="ignore", invalid="ignore"):
                np.log(f).astype("<f8").tofile(fo)
    np.zeros(len(c)).astype("<f8").tofile(out / "logself.f64")
    (out / "query_ids.txt").write_text("\n".join(q) + "\n")
    (out / "corpus_ids.txt").write_text("\n".join(c) + "\n")
    (out / "meta.json").write_text(json.dumps({"fusion": method, "w": w if method == "wsum" else None,
                                               "k": k if method == "rrf" else None, "tree_kernel_run": str(tk_run),
                                               "other_run": str(other_run), **(meta or {})}, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("tk")
    ap.add_argument("other")
    ap.add_argument("out")
    ap.add_argument("--method", choices=["rrf", "wsum"], required=True)
    ap.add_argument("--w", type=float, default=0.5)
    ap.add_argument("--k", type=int, default=60)
    a = ap.parse_args()
    fuse(a.tk, a.other, a.out, a.method, a.w, a.k)
    print(f"{a.method} -> {a.out}")
