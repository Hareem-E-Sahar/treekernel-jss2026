"""exp_v2 paper tables: corpus with false positives, 10 replicate query sets, mean ± SD over the replicates.

usage: .venv/bin/python exp_v2/paper/make_tables.py   -> exp_v2/paper/tables/{rq1_map,rq1_rq2_metrics,rq4_fusion}.tex
Inputs: exp_v2/results/fp/{per_replicate_metrics,pooled_compare_metrics}.tsv (exp_v2/eval/replicate_metrics.py),
        exp_v2/results/fp/selected.json (settings and W). Figures are drawn in R: exp_v2/paper/figures.R.
Significance marks: pooled paired bootstrap over functionalities (95%), per metric.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "exp_v2/results/fp"
TAB = Path(__file__).resolve().parent / "tables"
TAB.mkdir(exist_ok=True)
TYPES = ["T1", "T2", "VST3", "ST3", "MT3"]
KERNELS = ["STK", "SSTK", "PTK"]
FULL = {k: f"D {k}" for k in KERNELS}
SEL = json.loads((R / "selected.json").read_text())

REP = defaultdict(list)    # (method, measure, metric) -> values over replicates
for r in csv.DictReader(open(R / "per_replicate_metrics.tsv"), delimiter="\t"):
    REP[(r["method"], r["measure"], r["metric"])].append(float(r["value"]))
NREP = len(REP[("D PTK", "T1", "MAP")])
POOLED = {(r["a"], r["b"], r["measure"], r["metric"]): (float(r["ci_low"]), float(r["ci_high"]))
          for r in csv.DictReader(open(R / "pooled_compare_metrics.tsv"), delimiter="\t")}

SEEDS = "55, 1375, 2084, 2802, 3389, 3501, 6251, 8241, 8828, 9080"
SETUP = (f"Corpus: BigCloneBench true positives plus its 58,103 false positives (72,782 methods); false positives count as "
         f"non-relevant, except exact copies of the query (ignored). {NREP} replicate query sets (seeds {SEEDS}), each with "
         "100 queries per clone type and 100 functional queries, drawn independently; tuning queries excluded. "
         f"Mean $\\pm$ standard deviation over the {NREP} replicates.")
SIG = ("Significance: all distinct queries of the replicates pooled, paired bootstrap resampling functionalities, 95\\%.")


def stat(lab, measure, metric):
    v = REP[(FULL.get(lab, lab), measure, metric)]
    return np.mean(v), np.std(v, ddof=1)


def sig(a, b, measure, metric):
    lo, hi = POOLED[(FULL.get(a, a), FULL.get(b, b), measure, metric)]
    return 1 if lo > 0 else -1 if hi < 0 else 0


def marks(lab, measure, metric):
    s = ""
    if lab != "BM25":
        s += {1: "+", -1: "-", 0: ""}[sig(lab, "BM25", measure, metric)]
    if lab in KERNELS:
        s += {1: "\\uparrow", -1: "\\downarrow", 0: ""}[sig(lab, "CodeBERT ft", measure, metric)]
    return f"$^{{{s}}}$" if s else ""


def cell(mean, sd, best, mark=""):
    m = f"{mean:.3f}"
    return ("\\textbf{" + m + "}" if best else m) + f"$\\pm${sd:.3f}" + mark


def setting(k):
    p = SEL["settings"][k]["run"].split("_")[1:]
    return ", ".join(("$\\lambda$=" if s[0] == "l" else "$\\mu$=") + s[1:] for s in p)


def write(name, lines):
    (TAB / name).write_text("\n".join(lines) + "\n")
    print("table", name)


ALL = KERNELS + ["BM25", "CodeBERT zs", "CodeBERT ft"]
SETTINGS = {**{k: setting(k) for k in KERNELS}, "BM25": "$k_1$=1.2, $b$=0.75", "CodeBERT zs": "zero-shot",
            "CodeBERT ft": "fine-tuned"}
MARKS_NOTE = ("$^{+}$/$^{-}$: significantly better/worse than BM25; $^{\\uparrow}$/$^{\\downarrow}$: tree kernel "
              "significantly better/worse than fine-tuned CodeBERT. ")


def method_table(cols, label, caption, header, with_setting=True, sep="3.5pt", size="footnotesize"):
    """cols: [(measure, metric)]; one row per method in ALL, best mean per column in bold."""
    stats = {lab: [stat(lab, m, x) for m, x in cols] for lab in ALL}
    best = [max(stats[lab][i][0] for lab in ALL) for i in range(len(cols))]
    L = ["\\begin{table*}[t]", "\\centering", f"\\caption{{{caption}}}", f"\\label{{{label}}}", f"\\{size}",
         f"\\setlength{{\\tabcolsep}}{{{sep}}}", "\\begin{tabular}{" + ("ll" if with_setting else "l") + "c" * len(cols) + "}",
         "\\toprule", *header, "\\midrule"]
    for lab in ALL:
        if lab == "BM25":
            L.append("\\midrule")
        L.append(f"{lab} & " + (f"{SETTINGS[lab]} & " if with_setting else "") + " & ".join(
            cell(mu, sd, mu >= best[i] - 5e-4, marks(lab, m, x)) for i, ((mu, sd), (m, x)) in enumerate(zip(stats[lab], cols)))
            + " \\\\")
    L += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    return L


# ---- RQ1: MAP per clone type
write("rq1_map.tex", method_table(
    [(t, "MAP") for t in TYPES + ["mean5"]], "tab:rq1",
    "RQ1: MAP per clone type (relevant = the query's clones of that type; the query's other same-functionality methods "
    "are removed from its ranking). Tree kernels on variant D at the settings tuned on separate queries. Mean = mean over "
    "the five types. " + SETUP + " Best mean per column in bold. " + MARKS_NOTE + SIG,
    ["Method & Setting & T1 & T2 & VST3 & ST3 & MT3 & Mean \\\\"]))

# ---- RQ1 and RQ2: the four metrics
NP_NOTE = ("nP@$k$ = relevant methods in the top $k$ divided by $\\min(k, R)$, $R$ = the query's number of relevant "
           "methods; MRR = mean reciprocal rank of the first relevant method. ")
write("rq1_rq2_metrics.tex", method_table(
    [("mean5", x) for x in ("nP@5", "nP@10", "MRR", "MAP")] + [("functional", x) for x in ("nP@5", "nP@10", "MRR", "MAP@R")],
    "tab:metrics",
    "RQ1 and RQ2 under four metrics. RQ1: mean over the five clone types; RQ2: functional similarity (relevant = every "
    "method of the query's functionality, candidates = the whole corpus). " + NP_NOTE + SETUP +
    " Settings as in Table~\\ref{tab:rq1}. Best mean per column in bold. " + MARKS_NOTE + SIG,
    [" & \\multicolumn{4}{c}{RQ1 (mean over the five types)} & \\multicolumn{4}{c}{RQ2 (functional)} \\\\ "
     "\\cmidrule(lr){2-5}\\cmidrule(lr){6-9}",
     "Method & nP@5 & nP@10 & MRR & MAP & nP@5 & nP@10 & MRR & MAP@R \\\\"], with_setting=False, sep="2pt", size="scriptsize"))

# ---- RQ4: fusion
OTHER = {"bm25": "BM25", "codebert_ft": "CodeBERT ft"}


def block(name):
    f = SEL["fusion"][name]
    k, other = f["kernel"], OTHER[name.split(f"{f['kernel']}_")[1]]
    fus = f"{k}+{other}"
    return f"{k} + {other}", f["objective"], [(k, k), (other, other), (f"Weighted sum ($W$={f['w']:.1f})", f"{fus} wsum"),
                                              ("RRF", f"{fus} RRF")]


L = ["\\begin{table}[t]", "\\centering",
     "\\caption{RQ4: fusion of a tree kernel (variant D, tuned) with BM25 or with fine-tuned CodeBERT. Weighted sum = "
     "$W\\cdot$TK + $(1-W)\\cdot$other/max, $W$ tuned on the tuning queries for the RQ's measure; RRF = reciprocal rank "
     "fusion ($k$=60). The RQ1 fusions use PTK, the best kernel on RQ1; the RQ2 fusions use STK. " + SETUP +
     " Best mean per block and column in bold. $^{\\dagger}$: significantly better than both components. " + SIG + "}",
     "\\label{tab:rq4}", "\\footnotesize", "\\setlength{\\tabcolsep}{3.5pt}", "\\begin{tabular}{lcccc}", "\\toprule",
     " & \\multicolumn{3}{c}{RQ1 (MAP)} & RQ2 \\\\ \\cmidrule(lr){2-4} \\cmidrule(lr){5-5}",
     "Method & ST3 & MT3 & Mean & MAP@R \\\\", "\\midrule"]
blocks = [block(n) for n in SEL["fusion"]]
blocks.sort(key=lambda b: b[1])            # RQ1 blocks first
for i, (title, obj, rows) in enumerate(blocks):
    ms = [("ST3", "MAP"), ("MT3", "MAP"), ("mean5", "MAP")] if obj == "rq1" else [("functional", "MAP@R")]
    L.append(f"\\multicolumn{{5}}{{l}}{{\\emph{{{title}, $W$ tuned for RQ{obj[-1]}}}}} \\\\")
    st = {lab: [stat(r, m, x) for m, x in ms] for lab, r in rows}
    best = [max(st[lab][j][0] for lab, _ in rows) for j in range(len(ms))]
    for j, (lab, r) in enumerate(rows):
        cells = []
        for c, (m, x) in enumerate(ms):
            dag = "$^{\\dagger}$" if j >= 2 and all(sig(r, comp, m, x) > 0 for comp in (rows[0][1], rows[1][1])) else ""
            cells.append(cell(*st[lab][c], st[lab][c][0] >= best[c] - 5e-4, dag))
        cells = cells + ["--"] if obj == "rq1" else ["--"] * 3 + cells
        L.append(f"\\quad {lab} & " + " & ".join(cells) + " \\\\")
    if i < len(blocks) - 1:
        L.append("\\midrule")
L += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
L = [x.replace("\\begin{table}", "\\begin{table*}").replace("\\end{table}", "\\end{table*}") for x in L]
write("rq4_fusion.tex", L)
