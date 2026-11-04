"""exp_v2 PTK terminal-factor analysis (revision_plan.md, R1-C1b): evaluates the runs of
exp_v2/scripts/run_terminal_factor.sh like the lambda/mu grid (exp_v2/eval/tune.py: 50 tuning queries, exact copies
ignored; RQ1 = mean over T1-MT3 of micro MAP, RQ2 = functional MAP).
Lexical check: per factor, the mean overlap of PTK's top 10 and top 100 with BM25's (exp_v2/tuning/runs/bm25) on the
same queries, the query itself and its ignored exact copies excluded from both rankings.

usage: .venv/bin/python exp_v2/eval/terminal_factor.py   -> exp_v2/tuning/terminal_factor.tsv
"""
import csv
from collections import defaultdict

import numpy as np
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
T = ROOT / "exp_v2/tuning"
O = T / "terminal_factor"
TQ = ROOT / "exp_v2/data/tuning.tsv"
IGN = ROOT / "exp_v2/data/fp_copies.tsv"
FACTORS = ["0.25", "0.5", "0.75", "1", "1.25", "1.5", "1.75", "2", "4"]
BM25 = T / "runs/bm25"


def evaluate(run):
    """as exp_v2/eval/tune.py evaluate (tune.py selects on import, so it is not imported)"""
    if not (Path(run) / "eval/summary.tsv").exists():
        subprocess.run([sys.executable, str(ROOT / "exp_v2/eval/evaluate.py"), str(run), "--syntactic", str(TQ),
                        "--functional", str(TQ), "--ignore", str(IGN), "--boot", "0"], check=True, stdout=subprocess.DEVNULL)
    v = {}
    for r in csv.DictReader(open(Path(run) / "eval/summary.tsv"), delimiter="\t"):
        if r["category"] == "all" and r["averaging"] == "micro":
            if r["type"] == "mean5" and r["metric"] == "AP":
                v["rq1"] = float(r["value"])
            if r["type"] == "functional" and r["metric"] == "AP":
                v["rq2"] = float(r["value"])
    return v


def scores(run):
    """query x corpus, rank-equivalent to the normalised score; ids in row and column order"""
    q = Path(run, "query_ids.txt").read_text().split()
    c = Path(run, "corpus_ids.txt").read_text().split()
    k = np.fromfile(Path(run, "logk.f64"), dtype="<f8").reshape(len(q), len(c))
    s = np.fromfile(Path(run, "logself.f64"), dtype="<f8")
    col = {x: i for i, x in enumerate(c)}
    return k - (s[[col[x] for x in q]][:, None] + s[None, :]) / 2, q, c


def overlap(run, ref, ks=(10, 100)):
    a, q, c = scores(run)
    b, qb, cb = ref
    assert q == qb and c == cb, "row or column order differs from BM25's"
    col = {x: i for i, x in enumerate(c)}
    ign = defaultdict(set)
    for r in csv.DictReader(open(IGN), delimiter="\t"):
        ign[r["query_id"]].add(r["fp_id"])
    out = {k: [] for k in ks}
    for i, qid in enumerate(q):
        drop = [col[qid]] + [col[x] for x in ign[qid] if x in col]
        x, y = a[i].copy(), b[i].copy()
        x[drop] = -np.inf
        y[drop] = -np.inf
        x[np.isnan(x)] = -np.inf
        y[np.isnan(y)] = -np.inf
        ox, oy = np.argsort(-x, kind="stable"), np.argsort(-y, kind="stable")
        for k in ks:
            out[k].append(len(set(ox[:k]) & set(oy[:k])) / k)
    return {k: float(np.mean(v)) for k, v in out.items()}


def main():
    rows = []
    ref = scores(BM25)
    for t in FACTORS:
        d = O / f"PTK_l0.4_m0.6_t{t}"
        if (d / "meta.json").exists():
            v = evaluate(d)
            o = overlap(d, ref)
            rows.append((t, "ok", f"{v['rq1']:.6f}", f"{v['rq2']:.6f}", f"{o[10]:.4f}", f"{o[100]:.4f}"))
        elif (d / "NOT_COMPUTABLE").exists():
            rows.append((t, (d / "NOT_COMPUTABLE").read_text().strip(), "", "", "", ""))
    with open(T / "terminal_factor.tsv", "w") as o:
        o.write("terminal_factor\tstatus\trq1_mean5_map\trq2_map\tbm25_overlap_top10\tbm25_overlap_top100\n")
        o.writelines("\t".join(r) + "\n" for r in rows)
    for r in rows:
        print(*r, sep="\t")


if __name__ == "__main__":
    main()
