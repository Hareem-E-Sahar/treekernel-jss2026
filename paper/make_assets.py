"""Figures (PDF) and LaTeX tables (booktabs) for the paper, one set per research question.

usage: .venv/bin/python paper/make_assets.py   -> paper/figures/*.pdf, paper/tables/*.tex
Reads only evaluated runs (same sources as eval/eval_tables.py). Micro averages; significance =
paired bootstrap 95% CI excluding 0 (eval/paired.py, 2,000 resamples).
"""
import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
import paired  # noqa: E402
from complementarity import analyse  # noqa: E402

R = ROOT / "results"
FIG = ROOT / "paper/figures"
TAB = ROOT / "paper/tables"
FIG.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)

TYPES = paired.TYPES
TUNED = {"D": ["STK_l0.8", "SSTK_l0.1", "PTK_l0.4_m0.6"], "C": ["STK_l0.8", "SSTK_l0.1", "PTK_l0.4_m0.6"],
         "B": ["STK_l1.0", "SSTK_l0.1", "PTK_l0.4_m0.6"], "A": ["STK_l1.0", "SSTK_l0.1", "PTK_l0.6_m0.4"]}
DEFAULT = {"STK": "STK_l0.4", "SSTK": "SSTK_l0.4", "PTK": "PTK_l0.4_m0.4"}
KERNELS = ["STK", "SSTK", "PTK"]
VARIANTS = ["A", "B", "C", "D"]
VLONG = {"A": "A (raw)", "B": "B (pruned)", "C": "C (abstracted)", "D": "D (abstracted + API names)"}
BM = str(R / "bm25/eval/all")
CBZ = str(R / "codebert/eval/zeroshot")
CBF = str(R / "codebert/eval/finetuned")
CBLAB = {CBZ: "CodeBERT zs", CBF: "CodeBERT ft"}
CBSET = {CBZ: "zero-shot", CBF: "fine-tuned, 5 folds"}
CBE5 = {CBZ: str(R / "codebert/e5/zeroshot"), CBF: str(R / "codebert/e5/finetuned")}
COL = {"STK": "#0072B2", "SSTK": "#56B4E9", "PTK": "#D55E00", "BM25": "#555555",
       "CodeBERT zs": "#CC79A7", "CodeBERT ft": "#009E73"}
MARK = {"STK": "s", "SSTK": "^", "PTK": "o", "BM25": "D", "CodeBERT zs": "v", "CodeBERT ft": "P"}

plt.rcParams.update({"font.family": "serif", "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
                     "legend.fontsize": 7, "xtick.labelsize": 7, "ytick.labelsize": 7, "pdf.fonttype": 42,
                     "axes.spines.top": False, "axes.spines.right": False})
W1 = 3.4          # one column (inches)
W2 = 7.0          # two columns


def run(v, k, root="eval"):
    return str(R / root / v / k)


def main(k):
    return run("D", dict(zip(KERNELS, TUNED["D"]))[k])


def done(r):
    return (Path(r) / "eval/summary.tsv").exists()


def summary(r):
    d = {}
    for x in csv.DictReader(open(Path(r) / "eval/summary.tsv"), delimiter="\t"):
        d[(x["type"], x["category"], x["averaging"], x["metric"])] = (float(x["value"]), float(x["ci_low"]), float(x["ci_high"]), int(x["n_queries"]))
    return d


def val(r, t, m="AP", cat="all"):
    return summary(r)[(t, cat, "micro", m)]


def mean5(r, cat="all"):
    return float(np.mean([val(r, t, "AP", cat)[0] for t in TYPES]))


def maprr(r, cat="all"):
    return val(r, "functional", "AP@R", cat)[0]


def sig(a, b, measure):
    """+1 if a significantly better than b, -1 if significantly worse, 0 otherwise."""
    _, _, _, lo, hi, _ = paired.compare(a, b, measure)
    return 1 if lo > 0 else -1 if hi < 0 else 0


def marks(r, measure, kernel):
    """+/-: vs BM25; for tree kernels also up/down arrow: vs fine-tuned CodeBERT (when that run exists)."""
    s = ""
    if r != BM:
        z = sig(r, BM, measure)
        s += "+" if z > 0 else "-" if z < 0 else ""
    if kernel and FT:
        z = sig(r, CBF, measure)
        s += "\\uparrow" if z > 0 else "\\downarrow" if z < 0 else ""
    return f"$^{{{s}}}$" if s else ""


def setting(k, name):
    p = name.split("_")[1:]
    return ", ".join(("$\\lambda$=" if s[0] == "l" else "$\\mu$=") + s[1:] for s in p)


def bold_max(vals, fmt="{:.3f}", eps=5e-4):
    m = max(vals)
    return [("\\textbf{" + fmt.format(x) + "}") if x >= m - eps else fmt.format(x) for x in vals]


def write(name, lines, wide=True):
    """wide: spans both columns of a two-column layout (table*)."""
    t = "\n".join(lines) + "\n"
    if wide:
        t = t.replace("\\begin{table}", "\\begin{table*}").replace("\\end{table}", "\\end{table*}")
    (TAB / name).write_text(t)
    print("table", name)


def save(fig, name):
    fig.savefig(FIG / name, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print("figure", name)


METHODS = [("STK", main("STK")), ("SSTK", main("SSTK")), ("PTK", main("PTK")), ("BM25", BM)]
CB = [(CBLAB[c], c) for c in (CBZ, CBF) if done(c)]       # CodeBERT runs that exist so far
FT = done(CBF)
ALL = METHODS + CB
SETTING = {"BM25": "$k_1$=1.2, $b$=0.75", **{CBLAB[c]: CBSET[c] for c in (CBZ, CBF)}}
NOTE_CB = ("CodeBERT: microsoft/codebert-base, CLS embedding, cosine, first 512 tokens; fine-tuned = contrastive "
           "fine-tuning in 5 folds by functionality, each query scored by the model whose training data excluded its "
           "functionality. ") if CB else ""
NOTE_ARROW = "$^{\\uparrow}$/$^{\\downarrow}$: tree kernel significantly better/worse than fine-tuned CodeBERT. " if FT else ""

# ======================================================================== RQ1
cols = TYPES + ["mean5"]
cells = {}
for lab, r in ALL:
    cells[lab] = [val(r, t)[0] for t in TYPES] + [mean5(r)]
L = ["\\begin{table}[t]", "\\centering",
     "\\caption{RQ1: MAP per clone type on the original query sets (100 queries per type; Table~\\ref{tab:rq1rep} "
     "repeats the evaluation on 10 replicate query sets; candidates = the query's clones of that type plus methods of other "
     "functionalities). Tree kernels on variant D at tuned settings. Mean = mean over the five types. " + NOTE_CB +
     "$^{+}$/$^{-}$: significantly better/worse than BM25 (paired bootstrap, 95\\%). " + NOTE_ARROW + "Best per column in bold.}",
     "\\label{tab:rq1}", "\\small", "\\begin{tabular}{llcccccc}", "\\toprule",
     "Method & Setting & T1 & T2 & VST3 & ST3 & MT3 & Mean \\\\", "\\midrule"]
col_b = [bold_max([cells[l][i] for l, _ in ALL]) for i in range(len(cols))]
for j, (lab, r) in enumerate(ALL):
    st = SETTING.get(lab) or setting(lab, Path(r).name)
    row = [col_b[i][j] + marks(r, m, lab in KERNELS) for i, m in enumerate(cols)]
    if lab == "BM25":
        L.append("\\midrule")
    L.append(f"{lab} & {st} & " + " & ".join(row) + " \\\\")
L += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
write("rq1_map.tex", L)

# Replicate query sets (results/replicates, eval/replicates.py). The RQ1 box-plot figure is drawn in R: paper/rq1_boxplot.R
REP = {}
for r in csv.DictReader(open(R / "replicates/per_replicate.tsv"), delimiter="\t"):
    REP.setdefault(r["method"].replace("D ", ""), []).append(r)
NREP = len(REP["PTK"])
POOLED = {(r["a"], r["b"], r["measure"]): (float(r["ci_low"]), float(r["ci_high"]))
          for r in csv.DictReader(open(R / "replicates/pooled_compare.tsv"), delimiter="\t")}


def rsig(a, b, m):
    """+1 / -1 / 0: pooled replicate test, bootstrap over functionalities (eval/replicates.py)."""
    full = {k: f"D {k}" for k in KERNELS}
    lo, hi = POOLED[(full.get(a, a), full.get(b, b), m)]
    return 1 if lo > 0 else -1 if hi < 0 else 0


def rmarks(lab, m):
    s = ""
    if lab != "BM25":
        s += {1: "+", -1: "-", 0: ""}[rsig(lab, "BM25", m)]
    if lab in KERNELS:
        s += {1: "\\uparrow", -1: "\\downarrow", 0: ""}[rsig(lab, "CodeBERT ft", m)]
    return f"$^{{{s}}}$" if s else ""



# Table: the same comparison over the 10 replicate query sets, mean ± SD (RQ1 types, mean, and RQ2 MAP@R)
cols_r = TYPES + ["mean5", "functional"]
mean_r = {lab: [np.mean([float(r[c]) for r in REP[lab]]) for c in cols_r] for lab, _ in ALL}
sd_r = {lab: [np.std([float(r[c]) for r in REP[lab]], ddof=1) for c in cols_r] for lab, _ in ALL}
col_b = [bold_max([mean_r[l][i] for l, _ in ALL]) for i in range(len(cols_r))]
L = ["\\begin{table}[t]", "\\centering",
     f"\\caption{{RQ1 and RQ2 over {NREP} replicate query sets (seeds 55, 1375, 2084, 2802, 3389, 3501, 6251, 8241, 8828, "
     "9080). Each replicate draws 100 queries per clone type and 100 functional queries at random, independently of the other "
     "replicates and of the original sets (Table~\\ref{tab:rq1}); tuning queries are excluded. Mean $\\pm$ standard deviation "
     "over the replicates; MAP per clone type, Mean = mean over the five types, MAP@R for RQ2. Tree kernels on variant D at "
     "tuned settings. Best mean per column in bold. $^{+}$/$^{-}$: significantly better/worse than BM25; "
     "$^{\\uparrow}$/$^{\\downarrow}$: tree kernel significantly better/worse than fine-tuned CodeBERT (all distinct queries "
     "of the replicates pooled; paired bootstrap over functionalities, 95\\%).}",
     "\\label{tab:rq1rep}", "\\footnotesize", "\\setlength{\\tabcolsep}{3.5pt}", "\\begin{tabular}{lccccccc}", "\\toprule",
     " & \\multicolumn{6}{c}{RQ1: MAP} & RQ2 \\\\ \\cmidrule(lr){2-7}\\cmidrule(lr){8-8}",
     "Method & T1 & T2 & VST3 & ST3 & MT3 & Mean & MAP@R \\\\", "\\midrule"]
for j, (lab, _) in enumerate(ALL):
    if lab == "BM25":
        L.append("\\midrule")
    L.append(f"{lab} & " + " & ".join(f"{col_b[i][j]}$\\pm${sd_r[lab][i]:.3f}{rmarks(lab, m)}" for i, m in enumerate(cols_r)) + " \\\\")
L += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
write("rq1_rq2_replicates.tex", L)

# ======================================================================== RQ2
best_all = run("B", "SSTK_l0.1")
M2 = METHODS[:3] + [("SSTK (variant B)", best_all), METHODS[3]] + CB
metrics = [("AP@R", "MAP@R"), ("AP", "MAP"), ("P@10", "P@10"), ("R-prec", "R-Prec")]
vals2 = {lab: [val(r, "functional", m)[0] for m, _ in metrics] + [maprr(r, "pattern"), maprr(r, "name")] for lab, r in M2}
npat = val(BM, "functional", "AP@R", "pattern")[3]
nname = val(BM, "functional", "AP@R", "name")[3]
L = ["\\begin{table}[t]", "\\centering",
     "\\caption{RQ2: functional similarity on the original query set (100 queries; Table~\\ref{tab:rq1rep} gives MAP@R over 10 replicate query sets; relevant = every method of the query's functionality, candidates = "
     f"the whole corpus). Tree kernels at tuned settings, variant D unless stated. Last two columns: MAP@R by functionality "
     f"category (pattern: {npat} queries, name: {nname} queries). " + NOTE_CB +
     "$^{+}$/$^{-}$: significantly better/worse than BM25 on MAP@R. " + NOTE_ARROW.replace(". ", " on MAP@R. ") + "}",
     "\\label{tab:rq2}", "\\small", "\\begin{tabular}{lcccccc}", "\\toprule",
     " & & & & & \\multicolumn{2}{c}{MAP@R by category} \\\\ \\cmidrule(lr){6-7}",
     "Method & MAP@R & MAP & P@10 & R-Prec & pattern & name \\\\", "\\midrule"]
cb = [bold_max([vals2[l][i] for l, _ in M2]) for i in range(6)]
for j, (lab, r) in enumerate(M2):
    row = [cb[i][j] for i in range(6)]
    row[0] += marks(r, "functional", lab.split()[0] in KERNELS)
    if lab == "BM25":
        L.append("\\midrule")
    L.append(f"{lab} & " + " & ".join(row) + " \\\\")
L += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
write("rq2_functional.tex", L)

# Figure: task category, RQ1 (mean MAP) and RQ2 (MAP@R)
fig, axes = plt.subplots(1, 2, figsize=(W1, 1.9), sharey=True)
n1 = {c: sum(val(BM, t, "AP", c)[3] for t in TYPES) for c in ("pattern", "name")}
for ax, title, f, n in ((axes[0], "RQ1 (mean MAP)", mean5, n1),
                        (axes[1], "RQ2 (MAP@R)", maprr, {"pattern": npat, "name": nname})):
    bw = 0.8 / len(ALL)
    for i, (lab, r) in enumerate(ALL):
        ys = [f(r, c) for c in ("pattern", "name")]
        ax.bar(np.arange(2) + (i - (len(ALL) - 1) / 2) * bw, ys, bw, color=COL[lab], label=lab)
    ax.set_xticks(range(2), [f"pattern\n(n={n['pattern']})", f"name\n(n={n['name']})"])
    ax.set_title(title)
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", lw=0.3, alpha=0.5)
axes[0].set_ylabel("score")
axes[0].legend(ncol=len(ALL) if len(ALL) <= 4 else 3, loc="upper left", bbox_to_anchor=(0, 1.32 if len(ALL) <= 4 else 1.45),
               frameon=False, handlelength=1, columnspacing=0.8)
save(fig, "rq1_rq2_by_category.pdf")

# ======================================================================== RQ3
rq1m = np.zeros((4, 3))
rq2m = np.zeros((4, 3))
for i, v in enumerate(VARIANTS):
    for j, k in enumerate(TUNED[v]):
        rq1m[i, j] = mean5(run(v, k))
        rq2m[i, j] = maprr(run(v, k))
fig, axes = plt.subplots(1, 2, figsize=(W1, 1.75))
for ax, m, title, cmap in ((axes[0], rq1m, "RQ1: mean MAP", "Blues"), (axes[1], rq2m, "RQ2: MAP@R", "Oranges")):
    lo = m.min() - (m.max() - m.min()) * 0.3
    ax.imshow(m, cmap=cmap, aspect="auto", vmin=lo, vmax=m.max())
    for i in range(4):
        for j in range(3):
            best = m[i, j] >= m.max() - 5e-4
            ax.text(j, i, f"{m[i, j]:.3f}", ha="center", va="center", fontsize=7, fontweight="bold" if best else "normal",
                    color="white" if (m[i, j] - lo) / (m.max() - lo) > 0.75 else "black")
    ax.set_xticks(range(3), KERNELS)
    ax.set_yticks(range(4), VARIANTS)
    ax.set_title(title)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
axes[0].set_ylabel("tree variant")
save(fig, "rq3_variant_kernel.pdf")

L = ["\\begin{table}[t]", "\\centering",
     "\\caption{RQ3: tree variant $\\times$ kernel, each at its tuned setting (tuned on 50 separate queries). "
     "$\\Delta$ tuning = RQ1 mean MAP at the tuned setting minus at KeLP's default ($\\lambda$=$\\mu$=0.4); "
     "$^{*}$: significant (paired bootstrap, 95\\%). Best per column in bold.}",
     "\\label{tab:rq3}", "\\small", "\\begin{tabular}{lllccccc}", "\\toprule",
     "Variant & Kernel & Setting & ST3 & MT3 & RQ1 mean & RQ2 MAP@R & $\\Delta$ tuning \\\\", "\\midrule"]
rows = []
for v in VARIANTS:
    for k in TUNED[v]:
        r = run(v, k)
        kk = k.split("_")[0]
        _, _, d, lo, hi, _ = paired.compare(r, run(v, DEFAULT[kk]), "mean5")
        rows.append((v, kk, setting(kk, k), val(r, "ST3")[0], val(r, "MT3")[0], mean5(r), maprr(r),
                     f"{d:+.3f}" + ("$^{*}$" if lo > 0 or hi < 0 else "")))
bc = [bold_max([x[i] for x in rows]) for i in range(3, 7)]
for j, x in enumerate(rows):
    if j and x[0] != rows[j - 1][0]:
        L.append("\\midrule")
    L.append(f"{x[0] if x[1] == 'STK' else ''} & {x[1]} & {x[2]} & " + " & ".join(bc[i][j] for i in range(4)) + f" & {x[7]} \\\\")
L += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
write("rq3_variants.tex", L)

# ======================================================================== RQ4
F1 = R / "rq4/rq1_PTK"
F2 = R / "rq4/rq2_STK"
F3 = R / "rq4/rq1_PTK_codebert"
F4 = R / "rq4/rq2_STK_codebert"
FUSE_CB = FT and done(F3 / "rrf") and done(F4 / "rrf")


def block(fdir, tk_lab, other_lab, other):
    w = next(fdir.glob("wsum_w*"))
    return [(tk_lab, main(tk_lab)), (other_lab, other), (f"Weighted sum ($W$={w.name.split('_w')[1]})", str(w)),
            ("RRF", str(fdir / "rrf"))]


L = ["\\begin{table}[t]", "\\centering",
     "\\caption{RQ4: fusion of a tree kernel (variant D, tuned) with BM25" + (" or with fine-tuned CodeBERT" if FUSE_CB else "") +
     ". Weighted sum = $W\\cdot$TK + $(1-W)\\cdot$other/max, "
     "$W$ tuned on the tuning queries; RRF = reciprocal rank fusion ($k$=60). "
     "$^{\\dagger}$: significantly better than both components (paired bootstrap, 95\\%).}",
     "\\label{tab:rq4}", "\\footnotesize", "\\setlength{\\tabcolsep}{4pt}", "\\begin{tabular}{lcccc}", "\\toprule",
     " & \\multicolumn{3}{c}{RQ1 (MAP)} & RQ2 \\\\ \\cmidrule(lr){2-4} \\cmidrule(lr){5-5}",
     "Method & ST3 & MT3 & Mean & MAP@R \\\\", "\\midrule"]
rq1_blocks = [("PTK + BM25", block(F1, "PTK", "BM25", BM))]
rq2_blocks = [("STK + BM25", block(F2, "STK", "BM25", BM))]
if FUSE_CB:
    rq1_blocks.append(("PTK + CodeBERT ft", block(F3, "PTK", "CodeBERT ft", CBF)))
    rq2_blocks.append(("STK + CodeBERT ft", block(F4, "STK", "CodeBERT ft", CBF)))
for title, blk in rq1_blocks:
    L.append(f"\\multicolumn{{5}}{{l}}{{\\emph{{{title}, $W$ tuned for RQ1}}}} \\\\")
    vv = [[val(r, "ST3")[0], val(r, "MT3")[0], mean5(r)] for _, r in blk]
    bb = [bold_max([x[i] for x in vv]) for i in range(3)]
    for j, (lab, r) in enumerate(blk):
        row = [bb[i][j] for i in range(3)]
        if j >= 2:
            for i, m in enumerate(["ST3", "MT3", "mean5"]):
                if sig(r, blk[0][1], m) > 0 and sig(r, blk[1][1], m) > 0:
                    row[i] += "$^{\\dagger}$"
        L.append(f"\\quad {lab} & " + " & ".join(row) + " & -- \\\\")
    L.append("\\midrule")
for k, (title, blk) in enumerate(rq2_blocks):
    L.append(f"\\multicolumn{{5}}{{l}}{{\\emph{{{title}, $W$ tuned for RQ2}}}} \\\\")
    bb = bold_max([maprr(r) for _, r in blk])
    for j, (lab, r) in enumerate(blk):
        dag = "$^{\\dagger}$" if j >= 2 and sig(r, blk[0][1], "functional") > 0 and sig(r, blk[1][1], "functional") > 0 else ""
        L.append(f"\\quad {lab} & -- & -- & -- & {bb[j]}{dag} \\\\")
    if k < len(rq2_blocks) - 1:
        L.append("\\midrule")
L += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
write("rq4_fusion.tex", L, wide=False)

# Table: RQ4 fusion over the replicate query sets (mean ± SD; W as tuned above, fixed across replicates)
def rcell(lab, m):
    v = [float(r[m]) for r in REP[lab]]
    return np.mean(v), np.std(v, ddof=1)


def rblock(fus, tk, other, fdir):
    w = next(fdir.glob("wsum_w*")).name.split("_w")[1]
    return [(tk, tk), (other, other), (f"Weighted sum ($W$={w})", f"{fus} wsum"), ("RRF", f"{fus} RRF")]


L = ["\\begin{table}[t]", "\\centering",
     f"\\caption{{RQ4 over the {NREP} replicate query sets (Table~\\ref{{tab:rq1rep}}): fusion of a tree kernel (variant D, "
     "tuned) with BM25 or with fine-tuned CodeBERT, at the $W$ tuned on the tuning queries (as in Table~\\ref{tab:rq4}). "
     "Mean $\\pm$ standard deviation over the replicates. $^{\\dagger}$: significantly better than both components (all "
     "distinct queries of the replicates pooled; paired bootstrap over functionalities, 95\\%).}",
     "\\label{tab:rq4rep}", "\\footnotesize", "\\setlength{\\tabcolsep}{4pt}", "\\begin{tabular}{lcccc}", "\\toprule",
     " & \\multicolumn{3}{c}{RQ1 (MAP)} & RQ2 \\\\ \\cmidrule(lr){2-4} \\cmidrule(lr){5-5}",
     "Method & ST3 & MT3 & Mean & MAP@R \\\\", "\\midrule"]
rq1_r = [("PTK + BM25", rblock("PTK+BM25", "PTK", "BM25", F1)), ("PTK + CodeBERT ft", rblock("PTK+CodeBERT ft", "PTK", "CodeBERT ft", F3))]
rq2_r = [("STK + BM25", rblock("STK+BM25", "STK", "BM25", F2)), ("STK + CodeBERT ft", rblock("STK+CodeBERT ft", "STK", "CodeBERT ft", F4))]


def dagger(blk, j, m):
    full = {k: f"D {k}" for k in KERNELS}
    ok = j >= 2 and all(POOLED[(blk[j][1], full.get(c, c), m)][0] > 0 for c in (blk[0][1], blk[1][1]))
    return "$^{\\dagger}$" if ok else ""


for k, (title, blk) in enumerate(rq1_r + rq2_r):
    rq1 = k < len(rq1_r)
    ms = ["ST3", "MT3", "mean5"] if rq1 else ["functional"]
    L.append(f"\\multicolumn{{5}}{{l}}{{\\emph{{{title}, $W$ tuned for RQ{1 if rq1 else 2}}}}} \\\\")
    bb = [bold_max([rcell(r, m)[0] for _, r in blk]) for m in ms]
    for j, (lab, r) in enumerate(blk):
        cells = [f"{bb[i][j]}$\\pm${rcell(r, m)[1]:.3f}{dagger(blk, j, m)}" for i, m in enumerate(ms)]
        cells = cells + ["--"] if rq1 else ["--"] * 3 + cells
        L.append(f"\\quad {lab} & " + " & ".join(cells) + " \\\\")
    if k < len(rq1_r + rq2_r) - 1:
        L.append("\\midrule")
L += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
write("rq4_fusion_replicates.tex", L)

# Figure: (a) complementarity, (b) fusion weight on the tuning queries
pairs = [("BM25", BM)] + ([("CodeBERT ft", CBF)] if FT else [])
sets = ["ST3", "MT3", "functional"]
fig, axes = plt.subplots(1, 2, figsize=(W2, 1.7 if len(pairs) == 1 else 2.4), gridspec_kw={"width_ratios": [1.5, 1]})
ax = axes[0]
parts = [("found by both", "#999999"), ("PTK only", COL["PTK"]), ("other only", "#333333"), ("neither", "#E8E8E8")]
ylab, y = [], 0
for p, (olab, orun) in enumerate(pairs):
    comp = {t: f for t, n, w, ti, lo, f, ov in analyse(main("PTK"), orun)}
    for s in sets:
        f = comp[s] / comp[s].sum()
        left = 0
        for (lab, c), x in zip(parts, f):
            ax.barh(y, x, left=left, color=c, label=lab if y == 0 else None, edgecolor="white", lw=0.5)
            if x > 0.06:
                ax.text(left + x / 2, y, f"{x:.0%}", ha="center", va="center", fontsize=6.5,
                        color="white" if lab in ("PTK only", "other only") else "black")
            left += x
        ylab.append((f"vs {olab}: " if len(pairs) > 1 else "") + ("functional (RQ2)" if s == "functional" else s))
        y += 1
    y += 0.4
ax.set_yticks([i + 0.4 * (i // 3) for i in range(len(ylab))], ylab)
ax.invert_yaxis()
ax.set_xlim(0, 1)
ax.set_xlabel("share of relevant items ranked within the top R")
ax.set_title("(a) PTK (variant D) vs " + " and vs ".join(o for o, _ in pairs))
ax.legend(ncol=4, loc="upper left", bbox_to_anchor=(0, -0.32 if len(pairs) == 1 else -0.22), frameon=False,
          handlelength=1, columnspacing=0.8)
ax = axes[1]
curves = [(F1, COL["PTK"], "PTK + BM25, RQ1 mean MAP", "o", "-"), (F2, COL["STK"], "STK + BM25, RQ2 MAP@R", "s", "-")]
if FUSE_CB:
    curves += [(F3, COL["PTK"], "PTK + CodeBERT ft, RQ1", "o", "--"), (F4, COL["STK"], "STK + CodeBERT ft, RQ2", "s", "--")]
for d, col, lab, mk, ls in curves:
    t = list(csv.DictReader(open(d / "tuning.tsv"), delimiter="\t"))
    key = [k for k in t[0] if k != "w"][0]
    ax.plot([float(x["w"]) for x in t], [float(x[key]) for x in t], marker=mk, ms=3, lw=1, ls=ls, color=col, label=lab,
            mfc="white" if ls == "--" else col)
ax.set_xlabel(f"$W$ (0 = {'other run' if FUSE_CB else 'BM25'} only, 1 = tree kernel only)")
ax.set_ylabel("score (tuning queries)")
ax.set_title("(b) weighted-sum fusion")
ax.set_ylim(0.0 if FUSE_CB else 0.2, 1.0)
ax.grid(lw=0.3, alpha=0.5)
ax.legend(loc="lower left" if FUSE_CB else "center left", bbox_to_anchor=(0, 0.0 if FUSE_CB else 0.66), frameon=False,
          fontsize=6, handlelength=1.6, labelspacing=0.25)
fig.subplots_adjust(wspace=0.35)
save(fig, "rq4_complementarity_fusion.pdf")

# ======================================================================== E5 (robustness)
E5CB = [(lab, c) for lab, c in CB if done(CBE5[c])]
E5FT = FT and done(CBE5[CBF])
L =["\\begin{table}[t]", "\\centering",
     "\\caption{Robustness: the same queries against a corpus enlarged with 58,103 BigCloneBench false positives "
     "(72,782 methods; variant D, tuned). Main = original corpus (14,679 methods). "
     "$^{+}$/$^{-}$: significantly better/worse than BM25 on the enlarged corpus. "
     + (NOTE_ARROW.replace(". ", " on the enlarged corpus. ") if E5FT else "") + "}",
     "\\label{tab:e5}", "\\small", "\\begin{tabular}{lcccccc}", "\\toprule",
     " & \\multicolumn{2}{c}{MT3 MAP} & \\multicolumn{2}{c}{RQ1 mean MAP} & \\multicolumn{2}{c}{RQ2 MAP@R} \\\\",
     "\\cmidrule(lr){2-3} \\cmidrule(lr){4-5} \\cmidrule(lr){6-7}",
     "Method & Main & Enlarged & Main & Enlarged & Main & Enlarged \\\\", "\\midrule"]
BME5 = str(R / "bm25/e5/all")
for lab, r in METHODS + E5CB:
    e = BME5 if lab == "BM25" else CBE5[r] if r in CBE5 else str(R / "e5/D" / Path(r).name)
    cells = []
    for m, f in (("MT3", lambda z: val(z, "MT3")[0]), ("mean5", mean5), ("functional", maprr)):
        s = f"{f(e):.3f}"
        mk = ""
        if lab != "BM25":
            z = sig(e, BME5, m)
            mk += "+" if z > 0 else "-" if z < 0 else ""
        if lab in KERNELS and E5FT:
            z = sig(e, CBE5[CBF], m)
            mk += "\\uparrow" if z > 0 else "\\downarrow" if z < 0 else ""
        s += f"$^{{{mk}}}$" if mk else ""
        cells += [f"{f(r):.3f}", s]
    if lab == "BM25":
        L.append("\\midrule")
    L.append(f"{lab} & " + " & ".join(cells) + " \\\\")
L += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
write("e5_false_positives.tex", L)

# ======================================================================== RQ5
tk = {}
for r in csv.DictReader(open(R / "rq5/tree_kernels.tsv"), delimiter="\t"):
    tk.setdefault((r["variant"], r["kernel"]), {})[int(r["queries"])] = float(r["wall_s"])
bt = list(csv.DictReader(open(R / "rq5/runs/bm25_timing_queries/timing.tsv"), delimiter="\t"))
bm_q = np.mean([float(x["client_ms"]) for x in bt]) / 1000
bm_took = np.mean([float(x["es_took_ms"]) for x in bt]) / 1000
bi = json.loads((R / "rq5/bm25_index.json").read_text())
prep = {r["step"]: float(r["seconds"]) for r in csv.DictReader(open(R / "rq5/tree_building.tsv"), delimiter="\t")}
NC = 14678

L = ["\\begin{table}[t]", "\\centering",
     "\\caption{RQ5: cost on one CPU thread (AMD Ryzen 7 8845HS laptop), corpus of 14,679 methods, mean over 20 queries. "
     "Preparation = parsing all methods into trees (tree kernels) or tokens and building the index (BM25); "
     "set-up = loading the corpus and computing self-similarities; per query = one query scored against the whole corpus. "
     "Tree kernels at tuned settings.}",
     "\\label{tab:rq5}", "\\small", "\\begin{tabular}{llrrrr}", "\\toprule",
     "Variant & Method & Preparation (s) & Set-up (s) & Per query (s) & Per pair ($\\mu$s) \\\\", "\\midrule"]
for v in VARIANTS:
    p = prep["parse"] + prep[f"variant {v}"]
    for k in KERNELS:
        x = tk[(v, k)]
        pq = (x[20] - x[0]) / 20
        first = k == "STK"
        L.append(f"{v if first else ''} & {k} & {f'{p:.1f}' if first else ''} & {x[0]:.1f} & {pq:.2f} & {pq / NC * 1e6:.0f} \\\\")
    L.append("\\midrule")
L.append(f"-- & BM25 & {prep['BM25 tokens'] + bi['index_seconds']:.1f} & -- & {bm_q:.2f} & {bm_q / NC * 1e6:.0f} \\\\")
cj = R / "rq5/codebert.json"
cbt = json.loads(cj.read_text()) if cj.exists() else None
tm = [json.loads(f.read_text()) for f in sorted((ROOT / "data/codebert/models").glob("fold*/train_meta.json"))]
if cbt:
    L.append(f"-- & CodeBERT & {cbt['corpus_encoding_s_estimate']:.0f} & {cbt['model_load_s']:.1f} & {cbt['query_s_mean']:.2f} & "
             f"{cbt['query_s_mean'] / NC * 1e6:.0f} \\\\")
L += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
if cbt:
    extra = ("CodeBERT: preparation = encoding the corpus one method at a time (estimated from 200 methods); set-up = loading "
             "the model; per query = encoding the query plus cosine against the stored corpus embeddings; zero-shot and "
             "fine-tuned models cost the same at inference.")
    if len(tm) == 5:
        extra += (f" Fine-tuning the five fold models took a further {sum(x['seconds'] for x in tm) / 3600:.1f} h "
                  "(8 threads).")
    L[2] = L[2][:-1] + " " + extra + "}"
write("rq5_cost.tex", L)

fig, ax = plt.subplots(figsize=(W1, 2.0))
labels, ys, cs = [], [], []
for v in VARIANTS:
    for k in KERNELS:
        x = tk[(v, k)]
        labels.append(f"{v} {k}")
        ys.append((x[20] - x[0]) / 20)
        cs.append(COL[k])
labels.append("BM25")
ys.append(bm_q)
cs.append(COL["BM25"])
if cbt:
    labels.append("CodeBERT")
    ys.append(cbt["query_s_mean"])
    cs.append(COL["CodeBERT ft"])
pos = []
p = 0
for i in range(len(labels)):
    pos.append(p)
    p += 1 + (0.6 if i % 3 == 2 else 0)
ax.barh(pos, ys, color=cs, height=0.8)
for y, p_ in zip(ys, pos):
    ax.text(y * 1.08, p_, f"{y:.2f} s" if y < 1 else f"{y:.1f} s", va="center", fontsize=6)
ax.set_yticks(pos, labels)
ax.invert_yaxis()
ax.set_xscale("log")
ax.set_xlim(0.05, 40)
ax.set_xlabel("time per query against 14,679 methods (s, log scale, 1 thread)")
ax.tick_params(axis="y", length=0)
save(fig, "rq5_time_per_query.pdf")

# Figure: per-query time on the main corpus vs the corpus enlarged with false positives (E5), same protocol
E5T = R / "rq5/e5"
if (E5T / "tree_kernels.tsv").exists() and (E5T / "codebert.json").exists() and (E5T / "runs/bm25_timing_queries/timing.tsv").exists():
    tk5 = {}
    for r in csv.DictReader(open(E5T / "tree_kernels.tsv"), delimiter="\t"):
        tk5.setdefault(r["kernel"], {})[int(r["queries"])] = float(r["wall_s"])
    bt5 = list(csv.DictReader(open(E5T / "runs/bm25_timing_queries/timing.tsv"), delimiter="\t"))
    cb5 = json.loads((E5T / "codebert.json").read_text())
    NC5 = cb5["n_corpus"]
    rows = [(f"D {k}", COL[k], (tk[("D", k)][20] - tk[("D", k)][0]) / 20, (tk5[k][20] - tk5[k][0]) / 20) for k in KERNELS]
    rows.append(("BM25", COL["BM25"], bm_q, np.mean([float(x["client_ms"]) for x in bt5]) / 1000))
    rows.append(("CodeBERT", COL["CodeBERT ft"], cbt["query_s_mean"], cb5["query_s_mean"]))
    from matplotlib.patches import Patch
    fig, ax = plt.subplots(figsize=(W1, 2.0))
    h = 0.36
    with plt.rc_context({"hatch.linewidth": 0.7}):
        for i, (lab, c, a, b) in enumerate(rows):
            # corpus is encoded by fill style (hatched outline = main, solid = enlarged), never by lightness
            ax.barh(i - h / 2 - 0.01, a, h, facecolor="white", edgecolor=c, hatch="//////", lw=0.8)
            ax.barh(i + h / 2 + 0.01, b, h, color=c, lw=0)
            for y, v in ((i - h / 2 - 0.01, a), (i + h / 2 + 0.01, b)):
                ax.text(v * 1.08, y, f"{v:.2f} s" if v < 1 else f"{v:.1f} s", va="center", fontsize=6, color="#222222")
            ax.text(250, i, f"×{b / a:.1f}", va="center", ha="right", fontsize=6.5, color="#222222")
        ax.set_yticks(range(len(rows)), [r[0] for r in rows])
        ax.invert_yaxis()
        ax.set_xscale("log")
        ax.set_xlim(0.05, 250)
        ax.text(250, -0.72, "enlarged\n÷ main", ha="right", va="bottom", fontsize=6, color="#222222", linespacing=1.0)
        ax.set_xlabel("time per query (s, log scale, 1 thread)")
        ax.tick_params(axis="y", length=0)
        handles = [Patch(facecolor="white", edgecolor="#555555", hatch="//////", lw=0.8, label=f"main corpus ({NC + 1:,} methods)"),
                   Patch(facecolor="#555555", label=f"with false positives ({NC5:,} methods)")]
        ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(-0.02, 0.99), ncol=1, frameon=False, handlelength=1.4,
                  columnspacing=0.8, handletextpad=0.4, fontsize=6.5)
    save(fig, "rq5_time_e5.pdf")
