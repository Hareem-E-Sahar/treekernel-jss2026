"""exp_v3_all_queries analysis on every eligible query (revision_plan.md: R1-C1a, R1-C3, R2-C4, R2-C5).

usage: .venv/bin/python exp_v3_all_queries/eval/analyze.py
  -> exp_v3_all_queries/results/analysis/
       values.tsv       per method (kernels, BM25, CodeBERT zs/ft, hybrids), measure (T1..MT3, mean5, functional) and
                        metric (nP@5, nP@10, MRR, MAP): value over all eligible queries
       compare.tsv      paired differences A - B and A12 for every pair, measure and metric; the tested comparisons
                        (MAP; RQ1, RQ2 and RQ4: 9 per measure) also have the Bonferroni-adjusted
                        percentile CI, its level and the matching adjusted p
       rq3_groups.tsv   MAP per LOC quartile and McCabe bin, RQ1 (mean over the five types) and RQ2
       rq3_trend.tsv    slope of AP on log LOC and on log McCabe (clone type as fixed effect in RQ1), per method, and
                        each kernel's slope minus BM25's and CodeBERT ft's
       rq3_mccabe10.tsv MAP at McCabe <= 10 and > 10 and the difference, per method
       noise.tsv        RQ1 mean5 and RQ2 MAP / nP@10 per method under the three label settings (default; Type-2 copies
                        ignored; false positives removed); noise_compare.tsv: kernel-vs-baseline differences and A12
Only the tested comparisons are resampled (common.py: bootstrap over functionalities, B = 10,000, Bonferroni).
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (RES, TYPES, MEASURES, METRICS, KERNELS, HYB, METHODS, LABEL, LOC_LABELS, CC_LABELS,  # noqa: E402
                    Boot, load, point, boot_diff, bonferroni, a12, a12_label, query_attributes, write_tsv, eval_dir)

A = RES / "analysis"
ALL = METHODS + HYB
PRIMARY = "MAP"
COLS = ["setting", "table", "test_family", "a", "b", "measure", "metric", "diff", "A12", "A12_label", "m",
        "ci_level", "adj_ci_low", "adj_ci_high", "p_adj"]
KK = [("D_SSTK", "D_STK"), ("D_PTK", "D_STK"), ("D_PTK", "D_SSTK")]
KB = [(f"D_{k}", b) for k in KERNELS for b in ("bm25", "codebert_ft")]


def tables():
    """table -> (tested pairs, descriptive pairs, measures). Tested: MAP, Bonferroni within each measure."""
    zs = [(f"D_{k}", "codebert_zs") for k in KERNELS] + [("codebert_ft", "codebert_zs")]
    rq4 = [(h, o) for h in HYB for o in (f"D_{h.split('_')[1]}", "bm25", "codebert_ft")]
    desc = [("codebert_zs", "bm25"), ("codebert_ft", "bm25")]
    return {"RQ1": (KK + KB, desc, TYPES + ["mean5"]), "RQ2": (KK + KB, desc, ["functional"]),
            "CodeBERT zs": ([], zs, MEASURES), "RQ4": (rq4, [], ["mean5", "functional"])}


def compare_rows(ev, boot, spec, setting="default"):
    out = []
    for table, (tested, desc, measures) in spec.items():
        for ms in measures:
            for a, b in tested + desc:
                for m in METRICS:
                    x = a12(ev[a], ev[b], m, ms)
                    r = dict(setting=setting, table=table, test_family="", a=LABEL[a], b=LABEL[b], measure=ms,
                             metric=m, diff=point(ev[a], m, ms, ev[b]), A12=x, A12_label=a12_label(x), m="",
                             ci_level="", adj_ci_low="", adj_ci_high="", p_adj="")
                    if boot is not None and m == PRIMARY and (a, b) in tested:
                        s = bonferroni(*boot_diff(boot, ev[a], ev[b], m, ms), len(tested))
                        r.update(test_family=f"{table} {ms}", m=len(tested), ci_level=s["level"], adj_ci_low=s["lo"],
                                 adj_ci_high=s["hi"], p_adj=s["p_adj"])
                    out.append(r)
    return out


def write_compare(path, rows):
    def f(k, v):
        if v == "" or isinstance(v, str) or k == "m":
            return v
        return f"{v:.3g}" if k == "p_adj" else f"{v:.4f}"
    write_tsv(path, COLS, [[f(k, r[k]) for k in COLS] for r in rows])


def fe_slope(x, tid, Y):
    """Slope of each column of Y on x with a fixed effect per tid (OLS) -> M."""
    xc = x.copy()
    for t in np.unique(tid):
        s = tid == t
        xc[s] = x[s] - x[s].mean()
    return (xc @ Y) / (xc @ xc)


def main():
    A.mkdir(parents=True, exist_ok=True)
    ev, clusters = {}, {}
    for r in ALL:
        ev[r], cl = load(r)
        clusters.update(cl)
    boot = Boot(clusters)

    # ---- values
    vals = []
    for r in ALL:
        for ms in MEASURES:
            for m in METRICS:
                n = len(ev[r][ms][m]) if ms != "mean5" else sum(len(ev[r][t][m]) for t in TYPES)
                vals.append([LABEL[r], ms, m, f"{point(ev[r], m, ms):.4f}", n])
    write_tsv(A / "values.tsv", ["method", "measure", "metric", "value", "n_queries"], vals)

    # ---- comparisons (R2-C5)
    write_compare(A / "compare.tsv", compare_rows(ev, boot, tables()))

    # ---- RQ3 groups (R2-C4)
    attrs = query_attributes()
    g3 = []
    for gname, key, labels in (("LOC quartile", "loc_group", LOC_LABELS), ("McCabe", "cc_group", CC_LABELS)):
        for g, lab in enumerate(labels):
            sub = {q for q, a in attrs.items() if a[key] == g}
            for rq, ms in (("RQ1", "mean5"), ("RQ2", "functional")):
                n = (sum(len(set(ev["D_STK"][t]["MAP"]) & sub) for t in TYPES) if rq == "RQ1"
                     else len(set(ev["D_STK"]["functional"]["MAP"]) & sub))
                nt = {t: len(set(ev["D_STK"][t]["MAP"]) & sub) for t in TYPES}
                for r in METHODS:
                    g3.append([gname, lab, rq, LABEL[r], f"{point(ev[r], 'MAP', ms, subset=sub):.4f}", n,
                               " ".join(f"{t}:{nt[t]}" for t in TYPES) if rq == "RQ1" else ""])
    write_tsv(A / "rq3_groups.tsv", ["grouping", "group", "rq", "method", "MAP", "type_queries", "per_type"], g3)

    # ---- RQ3 trends: slope of AP on log LOC / log McCabe
    tr = []
    for rq in ("RQ1", "RQ2"):
        sets = TYPES if rq == "RQ1" else ["functional"]
        obs = [(t, q) for t in sets for q in ev["D_STK"][t]["MAP"] if attrs[q]["cc"] is not None]
        tid = np.array([sets.index(t) for t, _ in obs])
        Y = np.array([[ev[r][t]["MAP"][q] for r in METHODS] for t, q in obs])
        for pname, x in (("log LOC", np.log([attrs[q]["loc"] for _, q in obs])),
                         ("log McCabe", np.log([attrs[q]["cc"] for _, q in obs]))):
            est = fe_slope(x, tid, Y)
            for j, r in enumerate(METHODS):
                tr.append([rq, pname, LABEL[r], "slope", f"{est[j]:.4f}"])
            for k in KERNELS:
                for b in ("bm25", "codebert_ft"):
                    i, j = METHODS.index(f"D_{k}"), METHODS.index(b)
                    tr.append([rq, pname, LABEL[f"D_{k}"], f"minus {LABEL[b]}", f"{est[i] - est[j]:.4f}"])
    write_tsv(A / "rq3_trend.tsv", ["rq", "predictor", "method", "statistic", "value"], tr)

    # ---- McCabe <= 10 vs > 10 (McCabe's threshold, sensitivity)
    lo_q = {q for q, a in attrs.items() if a["cc"] is not None and a["cc"] <= 10}
    hi_q = {q for q, a in attrs.items() if a["cc"] is not None and a["cc"] > 10}
    mc = []
    for rq, ms in (("RQ1", "mean5"), ("RQ2", "functional")):
        for r in METHODS:
            lo, hi = point(ev[r], "MAP", ms, subset=lo_q), point(ev[r], "MAP", ms, subset=hi_q)
            mc.append([rq, LABEL[r], f"{lo:.4f}", f"{hi:.4f}", f"{hi - lo:.4f}"])
    write_tsv(A / "rq3_mccabe10.tsv", ["rq", "method", "low_value", "high_value", "high_minus_low"], mc)

    # ---- label noise (R1-C3)
    if not all((eval_dir(r, s) / "per_query.tsv").exists() for r in METHODS for s in ("t2", "no_fp")):
        print("label-noise evaluations not complete; noise tables skipped")
        return
    nz, nzc = [], []
    spec = {"noise": ([], KB + [("codebert_ft", "bm25")], ["mean5", "functional"])}
    for setting in ("default", "t2", "no_fp"):
        evs = ev if setting == "default" else {r: load(r, setting)[0] for r in METHODS}
        for r in METHODS:
            for ms in ("mean5", "functional"):
                for m in ("MAP", "nP@10"):
                    nz.append([setting, LABEL[r], ms, m, f"{point(evs[r], m, ms):.4f}"])
        nzc += compare_rows(evs, None, spec, setting)
    write_tsv(A / "noise.tsv", ["setting", "method", "measure", "metric", "value"], nz)
    write_compare(A / "noise_compare.tsv", nzc)
    print("analysis done")


if __name__ == "__main__":
    main()
