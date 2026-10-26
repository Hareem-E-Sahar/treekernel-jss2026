"""exp_v2 paper tables for the size and complexity analysis (corpus with false positives, 10 seeds).

usage: .venv/bin/python exp_v2/paper/size_complexity_tables.py
  -> exp_v2/paper/tables/{size_complexity,size_complexity_interaction}.tex
Inputs: exp_v2/results/size_complexity/{per_seed,pooled,interaction}.tsv (exp_v2/eval/size_complexity.py).
Figures: exp_v2/paper/size_complexity.R.
"""
import csv
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "exp_v2/results/size_complexity"
TAB = Path(__file__).resolve().parent / "tables"
TAB.mkdir(exist_ok=True)
METHODS = ["STK", "SSTK", "PTK", "BM25", "CodeBERT zs", "CodeBERT ft"]
GROUPS = [("small", "small"), ("large", "large"), ("low", "low"), ("high", "high")]
PS = defaultdict(list)
for r in csv.DictReader(open(R / "per_seed.tsv"), delimiter="\t"):
    PS[(r["group"], r["method"], r["measure"], r["metric"])].append(float(r["value"]))
NSEED = len(PS[("small", "PTK", "mean5", "MAP")])
POOL = {(r["group"], r["measure"]): (int(r["n_queries"]), int(r["n_functionalities"]))
        for r in csv.DictReader(open(R / "pooled.tsv"), delimiter="\t") if r["method"] == "PTK" and r["metric"] == "MAP"}
INTER = {(r["group1"], r["a"], r["b"], r["measure"], r["metric"]): r
         for r in csv.DictReader(open(R / "interaction.tsv"), delimiter="\t")}

GROUP_DEF = ("Groups of the query: small = at most 6 lines of code (physical lines of the method), large = at least 10; "
             "low = McCabe cyclomatic complexity at most 10, high = above 10 (Checkstyle 10.21.1, default counting). ")
SETUP = ("Corpus: BigCloneBench true positives plus its 58,103 false positives (72,782 methods); false positives count as "
         "non-relevant, except exact copies of the query (ignored); candidates are not restricted by group. Per seed "
         f"({NSEED} seeds, those of the replicate query sets) and group: for RQ1, 100 queries per clone type, and for RQ2, 100 "
         "functional queries, at random from the group, or the whole group when it has fewer (small T2: 53, small VST3: "
         "12, high T2: 57 queries). Tree kernels on variant D "
         "at the tuned settings. ")


def write(name, lines):
    (TAB / name).write_text("\n".join(lines) + "\n")
    print("table", name)


BLOCKS = [(None, "MAP")]   # MAP only in the paper (decision 2026-10-25); MAP@R stays in the raw results
METRIC_NOTE = ""

# ---- per group: mean ± SD over the seeds
L = ["\\begin{table*}[!htbp]", "\\centering",
     "\\caption{RQ3, size and complexity: syntactic clones (as in RQ1, mean over the five clone types) and functional "
     "similarity (as in RQ2) per group of the query. " + GROUP_DEF + SETUP + METRIC_NOTE + f"Mean $\\pm$ standard deviation over the {NSEED} seeds; best mean per "
     "column in bold. Last row: distinct queries over all seeds (functionalities). Table~\\ref{tab:sizecxint} "
     "tests whether the differences between methods change between groups.}",
     "\\label{tab:sizecx}", "\\scriptsize", "\\setlength{\\tabcolsep}{3pt}", "\\begin{tabular}{lcccccccc}", "\\toprule",
     " & \\multicolumn{4}{c}{RQ1: MAP (mean over the five types)} & \\multicolumn{4}{c}{RQ2: MAP (functional)} \\\\ "
     "\\cmidrule(lr){2-5}\\cmidrule(lr){6-9}",
     " & \\multicolumn{2}{c}{Size} & \\multicolumn{2}{c}{Complexity} & \\multicolumn{2}{c}{Size} & \\multicolumn{2}{c}{Complexity} \\\\ "
     "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\\cmidrule(lr){8-9}",
     "Method & small & large & low & high & small & large & low & high \\\\", "\\midrule"]
for b, (title, metric) in enumerate(BLOCKS):
    if b:
        L.append("\\midrule")
    if title:
        L.append(f"\\multicolumn{{9}}{{l}}{{\\emph{{{title}}}}} \\\\")
    cols = [(g, "mean5", metric) for g, _ in GROUPS] + [(g, "functional", metric) for g, _ in GROUPS]
    stats = {m: [(np.mean(PS[(g, m, ms, x)]), np.std(PS[(g, m, ms, x)], ddof=1)) for g, ms, x in cols] for m in METHODS}
    best = [max(stats[m][i][0] for m in METHODS) for i in range(len(cols))]
    for m in METHODS:
        if m == "BM25":
            L.append("\\cmidrule(lr){1-9}")
        L.append(f"\\quad {m} & " + " & ".join(("\\textbf{" + f"{mu:.3f}" + "}" if mu >= best[i] - 5e-4 else f"{mu:.3f}")
                                              + f"$\\pm${sd:.3f}" for i, (mu, sd) in enumerate(stats[m])) + " \\\\")
L.append("\\midrule")
L.append("Queries & " + " & ".join(f"{POOL[(g, ms)][0]:,} ({POOL[(g, ms)][1]})" for g, ms in
                                   [(g, "mean5") for g, _ in GROUPS] + [(g, "functional") for g, _ in GROUPS]) + " \\\\")
L += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
write("size_complexity.tex", L)

# ---- interaction
PAIRS = [("PTK", "BM25"), ("PTK", "CodeBERT ft"), ("STK", "BM25"), ("STK", "CodeBERT ft"), ("SSTK", "BM25"),
         ("SSTK", "CodeBERT ft"), ("CodeBERT ft", "BM25")]
CONTRASTS = [("small", "small $-$ large", ""), ("low", "low $-$ high", ""), ("low_large", "low $-$ high", "(large only)")]
SHORT = {"CodeBERT ft": "CB ft"}


def icell(g1, a, b, ms, metric):
    """(D, its CI): the D row and the CI row below it."""
    r = INTER[(g1, a, b, ms, metric)]
    d, lo, hi = float(r["interaction"]), float(r["ci_low"]), float(r["ci_high"])
    s = f"{d:+.3f}"
    if lo > 0 or hi < 0:
        s = "\\textbf{" + s + "}"
    return s, f"[{lo:+.3f}, {hi:+.3f}]"


L = ["\\begin{table*}[!htbp]", "\\centering",
     "\\caption{RQ3, size and complexity: does the difference between two methods change between groups? Each cell is "
     "$D = (A - B)_{1} - (A - B)_{2}$, the difference between methods $A$ and $B$ on the first group minus that on the "
     "second, with its 95\\% confidence interval in the row below; positive: $A$'s advantage is larger (or its "
     "disadvantage smaller) on the first group. Bold: the interval excludes 0. All distinct queries of the seeds pooled; "
     "paired bootstrap resampling functionalities jointly for both groups (2,000 resamples). RQ1: mean over the five clone "
     "types; RQ2: functional similarity. " + METRIC_NOTE + "\\emph{Large only}: complexity compared among queries with at "
     "least 10 lines (every high-complexity query is large). Groups and setup as in Table~\\ref{tab:sizecx}.}",
     "\\label{tab:sizecxint}", "\\scriptsize", "\\setlength{\\tabcolsep}{3pt}", "\\begin{tabular}{lcccccc}", "\\toprule",
     " & \\multicolumn{3}{c}{RQ1: MAP (mean over the five types)} & \\multicolumn{3}{c}{RQ2: MAP (functional)} \\\\ "
     "\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}",
     "$A - B$ & " + " & ".join(c for _, c, _ in CONTRASTS) + " & " + " & ".join(c for _, c, _ in CONTRASTS) + " \\\\",
     " & " + " & ".join(x for _, _, x in CONTRASTS) + " & " + " & ".join(x for _, _, x in CONTRASTS) + " \\\\", "\\midrule"]
for bl, (title, metric) in enumerate(BLOCKS):
    if bl:
        L.append("\\midrule")
    if title:
        L.append(f"\\multicolumn{{7}}{{l}}{{\\emph{{{title}}}}} \\\\")
    for a, b in PAIRS:
        if a == "CodeBERT ft":
            L.append("\\cmidrule(lr){1-7}")
        cells = ([icell(g, a, b, "mean5", metric) for g, _, _ in CONTRASTS]
                 + [icell(g, a, b, "functional", metric) for g, _, _ in CONTRASTS])
        L.append(f"\\quad {SHORT.get(a, a)} $-$ {SHORT.get(b, b)} & " + " & ".join(d for d, _ in cells) + " \\\\")
        L.append(" & " + " & ".join(ci for _, ci in cells) + " \\\\[2pt]")
L += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
write("size_complexity_interaction.tex", L)
