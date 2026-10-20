"""Complementarity of a tree-kernel run and a BM25 run (RQ4).

usage: complementarity.py TK_RUN BM25_RUN  -> printed markdown (used by eval/rq_tables.py)

Same candidates and ground truth as eval/evaluate.py.
  queries:  per query, which run has the higher primary metric (AP per clone type; MAP@R for
            the functional set); ties = equal within 1e-9
  items:    every relevant (query, item) pair is "found" by a run if its rank is <= R, the
            query's number of relevant items (the R-precision cut-off);
            counted as found by both, tree kernel only, BM25 only, or neither.
            Ranks of tied items = average of the tied positions.
  overlap:  mean share of the top-10 candidates that both runs return (ties broken by corpus order)
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fusion import load, avg_ranks  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TYPES = ["T1", "T2", "VST3", "ST3", "MT3"]


def ground_truth(corpus):
    tasks = defaultdict(set)
    for r in csv.DictReader(open(ROOT / "data/full_bcb/tp_functionalities.tsv"), delimiter="\t"):
        tasks[r["function_id"]].add(r["functionality_id"])
    partners = {t: defaultdict(set) for t in TYPES}
    for r in csv.DictReader(open(ROOT / "data/full_bcb/syntactic_clone_pairs.tsv"), delimiter="\t"):
        a, b = r["function_id_one"], r["function_id_two"]
        partners[r["clone_type"]][a].add(b)
        partners[r["clone_type"]][b].add(a)
    task_of = [tasks[c] for c in corpus]
    return tasks, partners, task_of


def query_sets(pools=ROOT / "data/pools"):
    sets = []
    for t in TYPES:
        sets.append((t, [r["function_id"] for r in csv.DictReader(open(pools / f"syntactic_{t}.tsv"), delimiter="\t")]))
    sets.append(("functional", [r["function_id"] for r in csv.DictReader(open(pools / "functional.tsv"), delimiter="\t")]))
    return sets


def analyse(tk_run, bm_run, pools=None, evals=None):
    """pools: query-set folder (default data/pools); evals: (tk, other) folders holding per_query.tsv
    (default <run>/eval). Used by eval/replicates_complementarity.py for the replicate query sets."""
    q, c, tk = load(tk_run, True)
    _, _, bm = load(bm_run, False)
    tasks, partners, task_of = ground_truth(c)
    row = {x: i for i, x in enumerate(q)}
    col = {x: i for i, x in enumerate(c)}
    pq = {}
    for name, ev in zip(("tk", "bm"), evals or (Path(tk_run) / "eval", Path(bm_run) / "eval")):
        d = {}
        for r in csv.DictReader(open(Path(ev) / "per_query.tsv"), delimiter="\t"):
            d[(r["type"], r["function_id"])] = float(r["AP@R" if r["type"] == "functional" else "AP"])
        pq[name] = d
    out = []
    for t, qids in query_sets(*([Path(pools)] if pools else [])):
        win = loss = tie = 0
        found = np.zeros(4, int)        # both, tk only, bm only, neither
        overlap = []
        for qid in qids:
            a, b = pq["tk"][(t, qid)], pq["bm"][(t, qid)]
            win += a > b + 1e-9
            loss += b > a + 1e-9
            tie += abs(a - b) <= 1e-9
            same = np.array([bool(tasks[qid] & x) for x in task_of])
            if t == "functional":
                rel = same.copy()
                cand = np.ones(len(c), bool)
            else:
                rel = np.zeros(len(c), bool)
                rel[[col[p] for p in partners[t][qid] if p in col]] = True
                cand = ~same | rel
            rel[col[qid]] = False
            cand[col[qid]] = False
            cut = rel.sum()
            ranks = []
            for s in (tk[row[qid]], bm[row[qid]]):
                x = np.where(cand, s, np.nan)
                ranks.append(avg_ranks(x))
            fa, fb = ranks[0][rel] <= cut, ranks[1][rel] <= cut
            found += [np.sum(fa & fb), np.sum(fa & ~fb), np.sum(~fa & fb), np.sum(~fa & ~fb)]
            top = []
            for s in (tk[row[qid]], bm[row[qid]]):
                x = np.where(cand, s, -np.inf)
                top.append(set(np.argsort(-x, kind="stable")[:10]))
            overlap.append(len(top[0] & top[1]) / 10)
        out.append((t, len(qids), win, tie, loss, found, float(np.mean(overlap))))
    return out


def markdown(tk_label, tk_run, bm_run, other="BM25"):
    """other: label of the second run (BM25, or e.g. CodeBERT, which is loaded the same way)."""
    res = analyse(tk_run, bm_run)
    L = [f"**{tk_label} vs {other}: queries won, items found, top-10 overlap**", "",
         f"| Set | Queries | {tk_label} better | Tie | {other} better | Items | Found by both | {tk_label} only | {other} only | Neither | Top-10 overlap |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for t, n, w, ti, lo, f, ov in res:
        tot = f.sum()
        L.append(f"| {t} | {n} | {w} | {ti} | {lo} | {tot:,} | " + " | ".join(f"{x:,} ({x / tot:.0%})" for x in f) + f" | {ov:.0%} |")
    return "\n".join(L)


if __name__ == "__main__":
    print(markdown("TK", sys.argv[1], sys.argv[2]))
