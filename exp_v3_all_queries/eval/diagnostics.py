"""Diagnostics for the tree kernels on large and complex code (revision_plan.md, R1-C4 D1-D4; groups of R2-C4).

usage: .venv/bin/python exp_v3_all_queries/eval/diagnostics.py
  needs exp_v3_all_queries/eval/trees.py (tree_stats.tsv, fragments.npz) and the main evaluation
  -> exp_v3_all_queries/results/diagnostics/
       scan_<kernel>.tsv     per query: the kernel's 10 highest-scoring non-relevant methods, and per relevant set
                             (T1..MT3, functional) the share of relevant methods scoring above the 10th of them
       per_query.tsv         per (set, query): tree statistics, overlaps (D2), the D3 share, AP of every method
       d1_tree_shape.tsv     D1: tree shape per LOC quartile and McCabe bin (medians and IQR)
       d2_overlap.tsv        D2: Dice overlap of the query with its relevant methods and with each kernel's top-10
                             non-relevant methods, per group
       d3_branching.tsv      D3: per quartile of the query's maximum branching, PTK and STK: MAP and the share of
                             relevant methods above the 10th non-relevant one (RQ1 mean over types; RQ2)
       d4_model.tsv          D4: per method, standardised coefficients of AP on log LOC, log McCabe, log nodes,
                             height, log max branching and relevant overlap (clone type as fixed effect in RQ1)
All diagnostics are descriptive (plain values over the eligible queries; no CIs or tests).
Definitions:
  non-relevant  for both RQs, every method that shares no functionality with the query (BigCloneBench false positives
                and true positives of other functionalities), minus the query and its ignored exact copies
  overlap       Dice of fragment multisets, 2 |F(q) ∩ F(c)| / (|F(q)| + |F(c)|); fragments: complete subtrees for STK,
                productions for SSTK and PTK (trees.py); the method-independent D4 predictor uses productions
  relevant      RQ1: the query's clones of the type; RQ2: every method of its functionality. D2 averages over at most
                20 relevant methods per query and set (random, seed 20261104)
"""
import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ROOT, RES, TYPES, KERNELS, METHODS, LABEL, LOC_LABELS, CC_LABELS, SEED, load,  # noqa: E402
                    query_attributes, write_tsv)

D = RES / "diagnostics"
SETS = TYPES + ["functional"]
TOPF = 10
CAP = 20


def ground_truth(corpus):
    tasks = defaultdict(set)
    for r in csv.DictReader(open(ROOT / "data/full_bcb/tp_functionalities.tsv"), delimiter="\t"):
        tasks[r["function_id"]].add(r["functionality_id"])
    members = defaultdict(list)
    for c in corpus:
        for t in tasks[c]:
            members[t].append(c)
    partners = {t: defaultdict(set) for t in TYPES}
    for r in csv.DictReader(open(ROOT / "data/full_bcb/syntactic_clone_pairs.tsv"), delimiter="\t"):
        a, b = r["function_id_one"], r["function_id_two"]
        partners[r["clone_type"]][a].add(b)
        partners[r["clone_type"]][b].add(a)
    return tasks, members, partners


def query_sets():
    """set -> list of queries (exp_v2/data/full)."""
    F = ROOT / "exp_v2/data/full"
    out = {t: [r["function_id"] for r in csv.DictReader(open(F / f"syntactic_{t}.tsv"), delimiter="\t")] for t in TYPES}
    out["functional"] = [r["function_id"] for r in csv.DictReader(open(F / "functional.tsv"), delimiter="\t")]
    return out


def relevant(q, s, tasks, members, partners, col):
    if s == "functional":
        r = {c for t in tasks[q] for c in members[t]} - {q}
    else:
        r = partners[s][q]
    return [c for c in r if c in col]


def scan(kernel, sets, tasks, members, partners):
    """The kernel's top-10 non-relevant methods per query, and the D3 share per relevant set."""
    out = D / f"scan_{kernel}.tsv"
    if out.exists():
        return
    run = RES / "runs" / f"D_{kernel}"
    qids = (run / "query_ids.txt").read_text().split()
    cids = (run / "corpus_ids.txt").read_text().split()
    col = {c: i for i, c in enumerate(cids)}
    logk = np.memmap(run / "logk.f64", dtype="<f8", mode="r", shape=(len(qids), len(cids)))
    logself = np.fromfile(run / "logself.f64", dtype="<f8")
    task_cols = defaultdict(list)
    for c in cids:
        for t in tasks[c]:
            task_cols[t].append(col[c])
    ign = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "exp_v2/data/fp_copies.tsv"), delimiter="\t"):
        if r["fp_id"] in col:
            ign[r["query_id"]].append(col[r["fp_id"]])
    in_set = {s: set(v) for s, v in sets.items()}
    with open(out, "w") as o:
        o.write("function_id\ttop_false\t" + "\t".join(f"above_{s}" for s in SETS) + "\n")
        for i, q in enumerate(qids):
            s = np.asarray(logk[i]) - 0.5 * (logself[col[q]] + logself)   # log of the normalised kernel
            s = np.where(np.isnan(s), -np.inf, s)
            non = np.ones(len(cids), bool)
            for t in tasks[q]:
                non[task_cols[t]] = False
            non[col[q]] = False
            non[ign[q]] = False
            idx = np.flatnonzero(non)
            top = idx[np.argpartition(-s[idx], TOPF)[:TOPF]]
            top = top[np.argsort(-s[top], kind="stable")]
            s10 = s[top[-1]]
            above = []
            for st in SETS:
                if q not in in_set[st]:
                    above.append("")
                    continue
                rel = [col[c] for c in relevant(q, st, tasks, members, partners, col)]
                above.append(f"{np.mean(s[rel] > s10):.6f}" if rel else "")
            o.write(f"{q}\t{','.join(cids[j] for j in top)}\t" + "\t".join(above) + "\n")
    print(f"scan {kernel} done")


class Frags:
    def __init__(self):
        z = np.load(D / "fragments.npz")
        self.row = {x: i for i, x in enumerate(z["ids"].tolist())}
        self.z = {k: z[k] for k in z.files if k != "ids"}

    def get(self, kind, fid):
        i = self.row[fid]
        o = self.z[f"{kind}_off"]
        return self.z[f"{kind}_ids"][o[i]:o[i + 1]], self.z[f"{kind}_cnt"][o[i]:o[i + 1]]

    def dice(self, kind, a, b):
        ua, ca = self.get(kind, a)
        ub, cb = self.get(kind, b)
        _, ia, ib = np.intersect1d(ua, ub, assume_unique=True, return_indices=True)
        return 2 * np.minimum(ca[ia], cb[ib]).sum() / (ca.sum() + cb.sum())


def frag_kind(kernel):
    return "sub" if kernel == "STK" else "prod"


def main():
    sets = query_sets()
    union = sorted({q for v in sets.values() for q in v}, key=int)
    corpus = (RES / "runs/D_STK/corpus_ids.txt").read_text().split()
    col = {c: i for i, c in enumerate(corpus)}
    tasks, members, partners = ground_truth(corpus)
    for k in KERNELS:
        scan(k, sets, tasks, members, partners)

    attrs = query_attributes()
    ts = {r["function_id"]: r for r in csv.DictReader(open(D / "tree_stats.tsv"), delimiter="\t")}
    fr = Frags()
    rng = np.random.default_rng(SEED)
    scans = {k: {r["function_id"]: r for r in csv.DictReader(open(D / f"scan_{k}.tsv"), delimiter="\t")}
             for k in KERNELS}
    ev = {m: load(m)[0] for m in METHODS}
    clusters = load(METHODS[0])[1]

    # ---- per (set, query) table
    rows = []
    for st in SETS:
        for q in sets[st]:
            rel = relevant(q, st, tasks, members, partners, col)
            samp = rel if len(rel) <= CAP else list(rng.choice(sorted(rel, key=int), CAP, replace=False))
            t = ts[q]
            a = attrs[q]
            row = dict(set=st, function_id=q, cluster=clusters[q], loc=a["loc"], cc=a["cc"] if a["cc"] else "",
                       loc_group=a["loc_group"], cc_group="" if a["cc_group"] is None else a["cc_group"],
                       nodes=t["nodes"], height=t["height"], mean_branching=t["mean_branching"],
                       max_branching=t["max_branching"], n_relevant=len(rel),
                       ov_rel_prod=np.mean([fr.dice("prod", q, c) for c in samp]),
                       ov_rel_sub=np.mean([fr.dice("sub", q, c) for c in samp]))
            for k in KERNELS:
                top = scans[k][q]["top_false"].split(",")
                kind = frag_kind(k)
                row[f"ov_rel_{k}"] = row["ov_rel_sub"] if kind == "sub" else row["ov_rel_prod"]
                row[f"ov_false_{k}"] = np.mean([fr.dice(kind, q, c) for c in top])
                row[f"size_ratio_false_{k}"] = np.mean([int(ts[c]["nodes"]) for c in top]) / int(t["nodes"])
                row[f"above_{k}"] = scans[k][q][f"above_{st}"]
            row["size_ratio_rel"] = np.mean([int(ts[c]["nodes"]) for c in samp]) / int(t["nodes"])
            for m in METHODS:
                row[f"AP_{m}"] = ev[m][st]["MAP"][q]
            rows.append(row)
    hdr = list(rows[0].keys())
    write_tsv(D / "per_query.tsv", hdr, [[f"{r[h]:.6g}" if isinstance(r[h], float) else r[h] for h in hdr]
                                         for r in rows])

    # ---- D1: tree shape per group (eligible queries = the functional set)
    d1 = []
    fq = [r for r in rows if r["set"] == "functional"]
    for gname, key, labels in (("LOC quartile", "loc_group", LOC_LABELS), ("McCabe", "cc_group", CC_LABELS)):
        for g, lab in enumerate(labels):
            sel = [r for r in fq if r[key] == g]
            line = [gname, lab, len(sel), len({r["cluster"] for r in sel})]
            for f in ("loc", "cc", "nodes", "height", "mean_branching", "max_branching"):
                x = np.array([float(r[f]) for r in sel if r[f] != ""])
                q1, med, q3 = np.percentile(x, [25, 50, 75])
                line += [f"{med:.4g}", f"{q1:.4g}", f"{q3:.4g}"]
            lsh = np.array([float(ts[r["function_id"]]["leaf_share"]) for r in sel])
            dp = np.array([float(ts[r["function_id"]]["distinct_productions"]) for r in sel])
            line += [f"{np.median(lsh):.4g}", f"{np.median(dp):.4g}"]
            d1.append(line)
    write_tsv(D / "d1_tree_shape.tsv",
              ["grouping", "group", "queries", "functionalities"]
              + [f"{f}_{s}" for f in ("loc", "mccabe", "nodes", "height", "mean_branching", "max_branching")
                 for s in ("median", "q1", "q3")] + ["leaf_share_median", "distinct_productions_median"], d1)

    # ---- D2: overlaps per group, RQ1 = mean over the five types of the per-type means; RQ2 = functional
    def grouped(field, rq, key, g):
        """mean over the group's queries; RQ1 = mean over the five types of the per-type means"""
        types = TYPES if rq == "RQ1" else ["functional"]
        est = 0.0
        for t in types:
            vals = [float(r[field]) for r in rows if r["set"] == t and r[key] == g and r[field] != ""]
            if not vals:
                return None
            est += np.mean(vals) / len(types)
        return est

    d2 = []
    for rq in ("RQ1", "RQ2"):
        for gname, key, labels in (("LOC quartile", "loc_group", LOC_LABELS), ("McCabe", "cc_group", CC_LABELS)):
            for g, lab in enumerate(labels):
                for k in KERNELS:
                    for what, field in (("relevant", f"ov_rel_{k}"), ("top-10 non-relevant", f"ov_false_{k}"),
                                        ("size ratio top-10 non-relevant", f"size_ratio_false_{k}")):
                        s = grouped(field, rq, key, g)
                        if s:
                            d2.append([rq, gname, lab, LABEL[f"D_{k}"], what, f"{s:.4f}"])
                s = grouped("size_ratio_rel", rq, key, g)
                if s:
                    d2.append([rq, gname, lab, "all", "size ratio relevant", f"{s:.4f}"])
    write_tsv(D / "d2_overlap.tsv", ["rq", "grouping", "group", "kernel", "statistic", "value"], d2)

    # ---- D3: maximum branching quartiles (eligible queries), PTK vs STK
    mb = np.array([int(ts[q]["max_branching"]) for q in sets["functional"]])
    edges = np.percentile(mb, [25, 50, 75])
    bq = {q: int(sum(int(ts[q]["max_branching"]) > e for e in edges)) for q in union}
    blabels = []
    lo = int(mb.min())
    for i in range(4):
        hi = int(edges[i]) if i < 3 else int(mb.max())
        blabels.append(f"B{i + 1} ({lo}–{hi})")
        lo = hi + 1
    for r in rows:
        r["b_group"] = bq[r["function_id"]]
    d3 = []
    for rq in ("RQ1", "RQ2"):
        for g, lab in enumerate(blabels):
            line = [rq, lab]
            for k in ("PTK", "STK"):
                for field in (f"AP_D_{k}", f"above_{k}"):
                    line.append(f"{grouped(field, rq, 'b_group', g):.4f}")
            line.append(f"{grouped('AP_D_PTK', rq, 'b_group', g) - grouped('AP_D_STK', rq, 'b_group', g):.4f}")
            line += [sum(1 for r in rows if r["set"] == "functional" and r["b_group"] == g)]
            d3.append(line)
    write_tsv(D / "d3_branching.tsv",
              ["rq", "max_branching_quartile"]
              + [f"{k}_{f}" for k in ("PTK", "STK") for f in ("MAP", "above10")] + ["PTK_minus_STK_MAP", "queries"], d3)

    # ---- D4: per-query model
    preds = ["log LOC", "log McCabe", "log nodes", "height", "log max branching", "relevant overlap"]

    def X_of(r):
        return [math.log(r["loc"]), math.log(float(r["cc"])), math.log(int(r["nodes"])), float(r["height"]),
                math.log(int(r["max_branching"])), float(r["ov_rel_prod"])]

    d4 = []
    for rq in ("RQ1", "RQ2"):
        sel = [r for r in rows if (r["set"] in TYPES if rq == "RQ1" else r["set"] == "functional") and r["cc"] != ""]
        X = np.array([X_of(r) for r in sel])
        X = (X - X.mean(0)) / X.std(0)
        tid = np.array([SETS.index(r["set"]) for r in sel])
        W0 = np.ones((1, len(sel)))
        for m in METHODS:
            y = np.array([float(r[f"AP_{m}"]) for r in sel])

            def fit(W):
                """weighted least squares with a fixed effect per set (type), for each row of W"""
                Xc, yc = np.zeros((W.shape[0],) + X.shape), np.zeros(W.shape)
                for t in np.unique(tid):
                    s = tid == t
                    w = W[:, s]
                    sw = w.sum(1, keepdims=True)
                    Xc[:, s] = X[s][None] - ((w @ X[s]) / sw)[:, None, :]
                    yc[:, s] = y[s][None] - (w @ y[s] / sw[:, 0])[:, None]
                XtWX = np.einsum("bn,bni,bnj->bij", W, Xc, Xc)
                XtWy = np.einsum("bn,bni,bn->bi", W, Xc, yc)
                return np.linalg.solve(XtWX, XtWy[..., None])[..., 0]

            est = fit(W0)[0]
            for j, pname in enumerate(preds):
                d4.append([rq, LABEL[m], pname, f"{est[j]:.4f}"])
    write_tsv(D / "d4_model.tsv", ["rq", "method", "predictor", "coef"], d4)
    corr = np.corrcoef(np.array([X_of(r) for r in fq if r["cc"] != ""]).T)
    write_tsv(D / "d4_predictor_correlations.tsv", ["predictor"] + preds,
              [[p] + [f"{x:.2f}" for x in corr[i]] for i, p in enumerate(preds)])
    print("diagnostics done")


if __name__ == "__main__":
    main()
