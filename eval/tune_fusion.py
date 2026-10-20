"""Tune the weighted-sum fusion weight on the tuning queries, then fuse the evaluation runs (RQ4).

usage: tune_fusion.py NAME TK_TUNING BM25_TUNING TK_EVAL BM25_EVAL --objective rq1|rq2 [--out results/rq4]

Objective on the 50 tuning queries: rq1 = mean MAP over the five clone types (as for the kernels);
rq2 = functional MAP@R (relevant = same task as the query). W in {0, 0.1, ..., 1}; the best W
(ties -> the larger W, i.e. more tree kernel) is applied to the evaluation runs. RRF (k = 60) has
no parameter. Writes OUT/NAME/{tuning.tsv, wsum_w<W>/, rrf/} and evaluates the evaluation runs.
"""
import argparse
import csv
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fusion import fuse, write  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
ap = argparse.ArgumentParser()
for a in ["name", "tk_tuning", "bm_tuning", "tk_eval", "bm_eval"]:
    ap.add_argument(a)
ap.add_argument("--objective", choices=["rq1", "rq2"], required=True)
ap.add_argument("--out", type=Path, default=ROOT / "results/rq4")
a = ap.parse_args()
out = a.out / a.name
SYN = [x for t in ["T1", "T2", "VST3", "ST3", "MT3"] for x in ("--syntactic", f"data/pools/syntactic_{t}.tsv:{t}")]


def evaluate(run, tuning):
    args = ["--syntactic", "data/pools/tuning.tsv", "--functional", "data/pools/tuning.tsv", "--boot", "0"] if tuning \
        else SYN + ["--functional", "data/pools/functional.tsv"]
    subprocess.run([PY, "eval/evaluate.py", str(run)] + args, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    for r in csv.DictReader(open(Path(run) / "eval/summary.tsv"), delimiter="\t"):
        if r["category"] == "all" and r["averaging"] == "micro":
            if a.objective == "rq1" and r["type"] == "mean5" and r["metric"] == "AP":
                return float(r["value"])
            if a.objective == "rq2" and r["type"] == "functional" and r["metric"] == "AP@R":
                return float(r["value"])


rows = []
for i in range(11):
    w = i / 10
    q, c, f = fuse(a.tk_tuning, a.bm_tuning, "wsum", w)
    d = out / "tuning_runs" / f"wsum_w{w:.1f}"
    write(d, q, c, f, {"fusion": "wsum", "w": w, "tree_kernel_run": a.tk_tuning, "bm25_run": a.bm_tuning})
    rows.append((w, evaluate(d, True)))
    print(f"w={w:.1f} {a.objective}={rows[-1][1]:.4f}")
best = max(rows, key=lambda r: (round(r[1], 6), r[0]))[0]
with open(out / "tuning.tsv", "w") as o:
    o.write(f"w\t{a.objective}\n" + "".join(f"{w:.1f}\t{v:.6f}\n" for w, v in rows))
for method, w in [("wsum", best), ("rrf", None)]:
    q, c, f = fuse(a.tk_eval, a.bm_eval, method, w if w is not None else 0.5)
    d = out / (f"wsum_w{best:.1f}" if method == "wsum" else "rrf")
    write(d, q, c, f, {"fusion": method, "w": w, "k": 60 if method == "rrf" else None, "objective": a.objective,
                       "tree_kernel_run": a.tk_eval, "bm25_run": a.bm_eval})
    evaluate(d, False)
    print(f"{method} -> {d}")
print(f"best w = {best:.1f}")
