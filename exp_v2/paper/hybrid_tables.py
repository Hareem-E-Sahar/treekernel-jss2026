"""exp_v2 paper tables for the hybrid (BM25 top k re-ranked by a tree kernel), corpus with false positives.

usage: .venv/bin/python exp_v2/paper/hybrid_tables.py
  -> exp_v2/paper/tables/{hybrid_full,hybrid_replicates,hybrid_cost}.tex
Inputs: exp_v2/results/hybrid/{full_values,full_compare,replicate_values,replicate_compare,timing}.tsv
(exp_v2/eval/hybrid.py). Figures: exp_v2/paper/hybrid.R.
"""
import csv
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "exp_v2/results/hybrid"
TAB = Path(__file__).resolve().parent / "tables"
TAB.mkdir(exist_ok=True)
TYPES = ["T1", "T2", "VST3", "ST3", "MT3"]
KERNELS = ["STK", "SSTK", "PTK"]


def hyb(k, K):
    return f"BM25→{k} (k={K})"


def tex(lab):
    return lab.replace("BM25→", "BM25$\\rightarrow$").replace("(k=", "($k$=")


FV = {(r["method"], r["measure"], r["metric"]): r for r in csv.DictReader(open(R / "full_values.tsv"), delimiter="\t")}
FC = {(r["a"], r["b"], r["measure"], r["metric"]): r for r in csv.DictReader(open(R / "full_compare.tsv"), delimiter="\t")}
RV = defaultdict(list)
for r in csv.DictReader(open(R / "replicate_values.tsv"), delimiter="\t"):
    RV[(r["method"], r["measure"], r["metric"])].append(float(r["value"]))
RC = {(r["a"], r["b"], r["measure"], r["metric"]): r for r in csv.DictReader(open(R / "replicate_compare.tsv"), delimiter="\t")}
NSEED = len(RV[("PTK", "T1", "MAP")])
N = {ms: int(FV[("BM25", ms, "MAP")]["n_queries"]) for ms in TYPES + ["functional"]}

SETUP = ("Corpus: BigCloneBench true positives plus its 58,103 false positives (72,782 methods); false positives count as "
         "non-relevant, except exact copies of the query (ignored). Hybrid: BM25's top $k$ ($k$ = 100, 200, not tuned) "
         "re-ranked by the tree kernel (variant D, tuned settings); below rank $k$ the BM25 order is kept. ")


def sig(table, a, b, ms, m):
    r = table[(a, b, ms, m)]
    lo, hi = float(r["ci_low"]), float(r["ci_high"])
    return 1 if lo > 0 else -1 if hi < 0 else 0


def mark(s, sym):
    return f"$^{{{s}}}$" if s else ""


def write(name, lines):
    (TAB / name).write_text("\n".join(lines) + "\n")
    print("table", name)


BLOCKS = [(None, "MAP")]   # MAP only in the paper (decision 2026-10-25); MAP@R stays in the raw results
HEADER = [" & \\multicolumn{6}{c}{RQ1: MAP} & RQ2: MAP \\\\ \\cmidrule(lr){2-7}\\cmidrule(lr){8-8}",
          "Method & T1 & T2 & VST3 & ST3 & MT3 & Mean & functional \\\\", "\\midrule"]
METRIC_NOTE = ""


def cols(metric):
    return [(t, metric) for t in TYPES + ["mean5"]] + [("functional", metric)]


# ---- full query set: value, 95% CI below
rows = ["BM25", "CodeBERT zs", "CodeBERT ft"] + [hyb(k, K) for k in KERNELS for K in (100, 200)]
L = ["\\begin{table*}[t]", "\\centering",
     "\\caption{Hybrid on every eligible query (" + ", ".join(f"{t} {N[t]:,}" for t in TYPES) + f", functional "
     f"{N['functional']:,}). " + SETUP + "Each cell: value over all queries, 95\\% confidence interval below (bootstrap "
     "resampling functionalities). RQ1: per clone type and Mean over the five types; RQ2: functional similarity. "
     + METRIC_NOTE + "Best value per column in bold. $^{+}$/$^{-}$: significantly better/worse than BM25; "
     "$^{\\uparrow}$/$^{\\downarrow}$: significantly better/worse than fine-tuned CodeBERT (paired bootstrap over "
     "functionalities, 95\\%). Full-ranking tree kernels were run on the replicate query sets only "
     "(Table~\\ref{tab:hybridrep}).}",
     "\\label{tab:hybridfull}", "\\scriptsize", "\\setlength{\\tabcolsep}{3pt}", "\\begin{tabular}{lccccccc}", "\\toprule",
     *HEADER]
for b, (title, metric) in enumerate(BLOCKS):
    if b:
        L.append("\\midrule")
    if title:
        L.append(f"\\multicolumn{{8}}{{l}}{{\\emph{{{title}}}}} \\\\")
    C = cols(metric)
    best = [max(float(FV[(r, ms, m)]["value"]) for r in rows) for ms, m in C]
    for j, r in enumerate(rows):
        if j == 3:
            L.append("\\cmidrule(lr){1-8}")
        vals, cis = [], []
        for i, (ms, m) in enumerate(C):
            c = FV[(r, ms, m)]
            v = float(c["value"])
            s = ""
            if r.startswith("BM25→"):
                s = {1: "+", -1: "-", 0: ""}[sig(FC, r, "BM25", ms, m)] + {1: "\\uparrow", -1: "\\downarrow", 0: ""}[sig(FC, r, "CodeBERT ft", ms, m)]
            elif r == "CodeBERT ft":
                s = {1: "+", -1: "-", 0: ""}[sig(FC, r, "BM25", ms, m)]
            vals.append(("\\textbf{" + f"{v:.3f}" + "}" if v >= best[i] - 5e-4 else f"{v:.3f}") + mark(s, s))
            cis.append(f"[{float(c['ci_low']):.3f}, {float(c['ci_high']):.3f}]")
        L.append(f"\\quad {tex(r)} & " + " & ".join(vals) + " \\\\")
        L.append(" & " + " & ".join(cis) + " \\\\[2pt]")
L += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
write("hybrid_full.tex", L)

# ---- replicate sets: hybrids next to the full-ranking kernels
rows = [x for k in KERNELS for x in (k, hyb(k, 100), hyb(k, 200))] + ["BM25", "CodeBERT ft"]
L = ["\\begin{table*}[t]", "\\centering",
     f"\\caption{{Hybrid against the full-ranking tree kernels on the {NSEED} replicate query sets (each with 100 queries "
     "per clone type for RQ1 and 100 functional queries for RQ2, as in Table~\\ref{tab:rq1}). " + SETUP + METRIC_NOTE
     + "Mean $\\pm$ standard deviation over the replicates; best mean per column in bold. "
     "$^{\\triangledown}$/$^{\\vartriangle}$: hybrid significantly worse/better than the same kernel ranking the whole "
     "corpus; $^{+}$/$^{-}$: significantly better/worse than BM25 (all distinct queries of the replicates pooled, paired "
     "bootstrap over functionalities, 95\\%).}",
     "\\label{tab:hybridrep}", "\\scriptsize", "\\setlength{\\tabcolsep}{3pt}", "\\begin{tabular}{lccccccc}", "\\toprule",
     *HEADER]
for b, (title, metric) in enumerate(BLOCKS):
    if b:
        L.append("\\midrule")
    if title:
        L.append(f"\\multicolumn{{8}}{{l}}{{\\emph{{{title}}}}} \\\\")
    C = cols(metric)
    st = {r: [(np.mean(RV[(r, ms, m)]), np.std(RV[(r, ms, m)], ddof=1)) for ms, m in C] for r in rows}
    best = [max(st[r][i][0] for r in rows) for i in range(len(C))]
    for j, r in enumerate(rows):
        if j and (r in KERNELS or r == "BM25"):
            L.append("\\cmidrule(lr){1-8}")
        cells = []
        for i, (ms, m) in enumerate(C):
            mu, sd = st[r][i]
            s = ""
            if r.startswith("BM25→"):
                k = r.split("→")[1].split()[0]
                s = {1: "\\vartriangle", -1: "\\triangledown", 0: ""}[sig(RC, r, k, ms, m)] + {1: "+", -1: "-", 0: ""}[sig(RC, r, "BM25", ms, m)]
            cells.append(("\\textbf{" + f"{mu:.3f}" + "}" if mu >= best[i] - 5e-4 else f"{mu:.3f}") + f"$\\pm${sd:.3f}" + mark(s, s))
        L.append(f"\\quad {tex(r)} & " + " & ".join(cells) + " \\\\")
L += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
write("hybrid_replicates.tex", L)

# ---- cost per query
T = {r["step"]: r for r in csv.DictReader(open(R / "timing.tsv"), delimiter="\t")}
first = T["BM25 top 200 (first stage)"]
L = ["\\begin{table}[t]", "\\centering",
     "\\caption{Hybrid: cost per query on the corpus with false positives (72,782 methods). First stage: Elasticsearch's "
     "reported search time for BM25's top 200. Second stage: the summed CPU time of the query's kernel evaluations. "
     "Full ranking: the tree kernel against the whole corpus, wall time $\\times$ threads / queries of the replicate runs "
     "(includes tree parsing, so the ratio is approximate). Ratio = full ranking / second stage (means).}",
     "\\label{tab:hybridcost}", "\\footnotesize", "\\setlength{\\tabcolsep}{4pt}", "\\begin{tabular}{llrrr}", "\\toprule",
     "Kernel & Step & Median ms & Mean ms & Ratio \\\\", "\\midrule",
     f"-- & BM25 top 200 & {float(first['median_ms']):.0f} & {float(first['mean_ms']):.0f} & \\\\", "\\midrule"]
for k in KERNELS:
    full = float(T[f"{k} full ranking (72,782 methods)"]["mean_ms"])
    for K in (100, 200):
        t = T[f"{k} on the top {K} (second stage)"]
        L.append(f"{k if K == 100 else ''} & re-rank top {K} & {float(t['median_ms']):.0f} & {float(t['mean_ms']):.0f} & "
                 f"{full / float(t['mean_ms']):.0f}$\\times$ \\\\")
    L.append(f" & full ranking & -- & {full:,.0f} & \\\\")
    if k != KERNELS[-1]:
        L.append("\\midrule")
L += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
write("hybrid_cost.tex", L)
