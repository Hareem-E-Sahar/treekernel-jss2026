"""exp_v3_all_queries figures (matplotlib), from exp_v3_all_queries/results/{analysis,diagnostics}.

usage: .venv/bin/python exp_v3_all_queries/paper/figures.py   -> exp_v3_all_queries/paper/figures/*.pdf
Every point is a value on all eligible queries; only the RQ1 tests figure has CIs (the tested differences).
Colours as in exp_v2 (Okabe-Ito). 
"""
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "exp_v3_all_queries/results"
OUT = Path(__file__).resolve().parent / "figures"
COL = {"STK": "#0072B2", "SSTK": "#56B4E9", "PTK": "#D55E00", "BM25": "#555555", "CodeBERT zs": "#CC79A7",
       "CodeBERT ft": "#009E73"}
METHODS = ["STK", "SSTK", "PTK", "BM25", "CodeBERT zs", "CodeBERT ft"]
TYPES = ["T1", "T2", "VST3", "ST3", "MT3"]
plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": "#e6e6e6", "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "legend.frameon": False, "pdf.fonttype": 42})


def read(path):
    return list(csv.DictReader(open(path), delimiter="\t"))


FOREST_ROWS = [("STK", "BM25"), ("SSTK", "BM25"), ("PTK", "BM25"), None,
               ("STK", "CodeBERT ft"), ("SSTK", "CodeBERT ft"), ("PTK", "CodeBERT ft"), None,
               ("SSTK", "STK"), ("PTK", "STK"), ("PTK", "SSTK")]


def forest_panel(ax, cmp, ms, a12_size):
    """One measure of the tested comparisons: Delta with the adjusted CI, filled = it excludes 0; A12 at the right."""
    ys = [len(FOREST_ROWS) - 1 - i for i in range(len(FOREST_ROWS))]
    ax.axvline(0, color="#444444", lw=0.8, zorder=1)
    for y, row in zip(ys, FOREST_ROWS):
        if row is None:
            continue
        r = cmp[(row[0], row[1], ms)]
        d, lo, hi = float(r["diff"]), float(r["adj_ci_low"]), float(r["adj_ci_high"])
        ax.plot([lo, hi], [y, y], color=COL[row[0]], lw=1.2, solid_capstyle="round", zorder=2)
        ax.plot(d, y, "o", ms=4.5, color=COL[row[0]], mfc=COL[row[0]] if lo > 0 or hi < 0 else "white", mew=1.1,
                zorder=3)
        ax.text(1.03, y, f"{float(r['A12']):.2f}", transform=ax.get_yaxis_transform(), va="center", fontsize=a12_size,
                color="#555555")
    ax.text(1.03, len(FOREST_ROWS) - 0.2, "$A_{12}$", transform=ax.get_yaxis_transform(), va="center",
            fontsize=a12_size, color="#555555")
    ax.set_ylim(-0.6, len(FOREST_ROWS) - 0.4)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)
    ax.set_yticks([y for y, r in zip(ys, FOREST_ROWS) if r])
    ax.set_yticklabels([f"{r[0]} − {r[1]}" for r in FOREST_ROWS if r])


def forest_legend(fig):
    fig.legend(handles=[Line2D([], [], marker="o", ls="-", color="#555555", ms=4.5, label="significant (CI excludes 0)"),
                        Line2D([], [], marker="o", ls="-", color="#555555", mfc="white", ms=4.5,
                               label="not significant")], loc="lower center", ncol=2)


def fig_rq12_forest():
    """RQ1 and RQ2 tested comparisons: difference in MAP with the Bonferroni-adjusted 99.4% CI and A12."""
    cmp = {}
    for r in read(RES / "analysis/compare.tsv"):
        if r["table"] in ("RQ1", "RQ2") and r["metric"] == "MAP" and r["adj_ci_low"] != "":
            cmp[(r["a"], r["b"], r["measure"])] = r
    with plt.rc_context({"axes.spines.left": False}):
        fig, axs = plt.subplots(1, 6, figsize=(7.2, 3.3), sharey=True, sharex=True)
    for ax, ms in zip(axs, TYPES + ["mean5"]):
        forest_panel(ax, cmp, ms, 5)
        ax.set_title(ms if ms != "mean5" else "Mean of 5 types", pad=8)
    axs[0].set_xlim(-0.14, 0.27)
    axs[0].set_xticks([-0.1, 0, 0.2])
    axs[0].set_xticklabels(["", "0", "0.2"])
    fig.supxlabel("Difference in MAP, with Bonferroni-adjusted 99.4% CI", fontsize=8, y=0.095)
    forest_legend(fig)
    fig.subplots_adjust(left=0.175, right=0.975, top=0.91, bottom=0.215, wspace=0.36)
    fig.savefig(OUT / "rq1_forest.pdf")
    plt.close(fig)
    with plt.rc_context({"axes.spines.left": False}):
        fig, ax = plt.subplots(figsize=(4.4, 2.9))
    forest_panel(ax, cmp, "functional", 6.5)
    ax.set_xlim(-0.46, 0.06)
    ax.set_xticks([-0.4, -0.3, -0.2, -0.1, 0])
    ax.set_xticklabels(["−0.4", "−0.3", "−0.2", "−0.1", "0"])
    ax.set_xlabel("Difference in MAP, with Bonferroni-adjusted 99.4% CI")
    forest_legend(fig)
    fig.subplots_adjust(left=0.32, right=0.92, top=0.95, bottom=0.25)
    fig.savefig(OUT / "rq2_forest.pdf")
    plt.close(fig)


def curves(ax, rows, ylab=None):
    groups = list(dict.fromkeys(r["group"] for r in rows))
    x = np.arange(len(groups))
    for j, m in enumerate(METHODS):
        rr = [next(r for r in rows if r["method"] == m and r["group"] == g) for g in groups]
        y = np.array([float(r["MAP"]) for r in rr])
        ax.plot(x, y, color=COL[m], marker="o", ms=3, lw=1.5, label=m)
    ax.set_xticks(x)
    ax.set_xticklabels(groups)
    ax.grid(axis="x", visible=False)
    if ylab:
        ax.set_ylabel(ylab)


def fig_rq3():
    rows = read(RES / "analysis/rq3_groups.tsv")
    fig, axs = plt.subplots(2, 2, figsize=(7.2, 5.0))
    for i, rq in enumerate(("RQ1", "RQ2")):
        for j, (gname, xl) in enumerate((("LOC quartile", "Lines of code (quartile)"),
                                          ("McCabe", "McCabe cyclomatic complexity"))):
            sel = [r for r in rows if r["rq"] == rq and r["grouping"] == gname]
            curves(axs[i, j], sel, ("Syntactic similarity:\nMAP, mean of 5 types" if rq == "RQ1" else "Functional similarity:\nMAP")
                   if j == 0 else None)
            axs[i, j].set_xlabel(xl)
    h, lab = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, lab, loc="lower center", ncol=6, fontsize=7)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(OUT / "rq3_size_complexity.pdf")
    plt.close(fig)


def fig_rq4_forest():
    """RQ4 tested comparisons: hybrid minus opponent, MAP, Bonferroni-adjusted 99.4% CI; filled = the CI excludes 0;
    right of each panel: paired A12. The same numbers as a table: tables/rq4_effects.tex."""
    cmp = {(r["a"], r["b"], r["measure"]): r for r in read(RES / "analysis/compare.tsv")
           if r["table"] == "RQ4" and r["metric"] == "MAP" and r["adj_ci_low"] != ""}
    kernels = ["STK", "SSTK", "PTK"]
    ys = [2, 1, 0]
    cols = [("own kernel's full ranking", None, (-0.14, 0.47)), ("BM25", "BM25", (-0.09, 0.11)),
            ("fine-tuned CodeBERT", "CodeBERT ft", (-0.09, 0.11))]
    with plt.rc_context({"axes.spines.left": False}):
        fig, axs = plt.subplots(2, 3, figsize=(6.2, 2.9), sharey=True,
                                gridspec_kw={"width_ratios": [1.5, 1, 1], "wspace": 0.42})
    for i, (ms, name) in enumerate((("mean5", "Mean of\n5 types"), ("functional", "Functional"))):
        for j, (title, b, xl) in enumerate(cols):
            ax = axs[i, j]
            ax.axvline(0, color="#444444", lw=0.8, zorder=1)
            for y, k in zip(ys, kernels):
                r = cmp[(f"{k}-Hybrid", b or k, ms)]
                d, lo, hi = float(r["diff"]), float(r["adj_ci_low"]), float(r["adj_ci_high"])
                ax.plot([lo, hi], [y, y], color=COL[k], lw=1.2, solid_capstyle="round", zorder=2)
                ax.plot(d, y, "o", ms=4.5, color=COL[k], mfc=COL[k] if lo > 0 or hi < 0 else "white", mew=1.1, zorder=3)
                ax.text(1.02, y, f"{float(r['A12']):.2f}", transform=ax.get_yaxis_transform(), va="center", fontsize=6,
                        color="#555555")
            ax.set_xlim(*xl)
            ax.set_ylim(-0.5, 2.5)
            ax.grid(axis="y", visible=False)
            ax.tick_params(axis="y", length=0)
            ax.text(1.02, 2.62, "$A_{12}$", transform=ax.get_yaxis_transform(), va="center", fontsize=6,
                    color="#555555")
            if i == 0:
                ax.set_title("vs " + title, pad=9)
        axs[i, 0].set_ylabel(name, labelpad=6)
    axs[0, 0].set_yticks(ys)
    axs[0, 0].set_yticklabels([f"{k}-Hybrid" for k in kernels])
    fig.supxlabel("Hybrid minus opponent, MAP, with Bonferroni-adjusted 99.4% CI", fontsize=8, y=0.085)
    fig.legend(handles=[Line2D([], [], marker="o", ls="-", color="#555555", ms=4.5, label="significant (CI excludes 0)"),
                        Line2D([], [], marker="o", ls="-", color="#555555", mfc="white", ms=4.5,
                               label="not significant")], loc="lower center", ncol=2)
    fig.subplots_adjust(left=0.19, right=0.955, top=0.89, bottom=0.235, hspace=0.42)
    fig.savefig(OUT / "rq4_forest.pdf")
    plt.close(fig)


def fig_sensitivity():
    grid = {r["setting"]: r for r in read(ROOT / "exp_v2/tuning/grid.tsv")}
    tf = read(ROOT / "exp_v2/tuning/terminal_factor.tsv")
    lam = [0.1, 0.2, 0.4, 0.6, 0.8, 1.0]
    fig, axs = plt.subplots(1, 4, figsize=(7.2, 2.2), gridspec_kw={"width_ratios": [1, 1, 1.25, 1]}, squeeze=False)
    for i, (key, ylab) in enumerate((("rq1_mean5_map", "Syntactic MAP (tuning queries)"),)):
        for j, k in enumerate(("STK", "SSTK")):
            ax = axs[i, j]
            xs = [l for l in lam if f"{k}_l{l}" in grid and grid[f"{k}_l{l}"]["status"] == "ok"]
            ys = [float(grid[f"{k}_l{l}"][key]) for l in xs]
            ax.plot(xs, ys, "o-", color=COL[k], ms=3, lw=1.5)
            sel = {"STK": 1.0, "SSTK": 0.1}[k]
            ax.plot([sel], [float(grid[f"{k}_l{sel}"][key])], "o", ms=7, mfc="none", color="black")
            for l in lam:
                if l not in xs:
                    ax.axvspan(l - 0.05, l + 0.05, color="#dddddd", lw=0)
            ax.set_xticks(lam)
            ax.set_xticklabels(["0.1", "", "0.4", "0.6", "0.8", "1.0"])
            ax.set_xlabel("λ")
            if i == 0:
                ax.set_title(k)
            if j == 0:
                ax.set_ylabel(ylab)
        ax = axs[i, 2]
        M = np.full((6, 6), np.nan)
        for a, l in enumerate(lam):
            for b, mu in enumerate(lam):
                g = grid.get(f"PTK_l{l}_m{mu}")
                if g and g["status"] == "ok":
                    M[a, b] = float(g[key])
        im = ax.imshow(M, origin="lower", cmap="Oranges", aspect="auto")
        for a in range(6):
            for b in range(6):
                ax.text(b, a, "n.c." if np.isnan(M[a, b]) else f"{M[a, b]:.3f}"[1:], ha="center", va="center",
                        fontsize=5.5, color="#777777" if np.isnan(M[a, b]) else
                        ("white" if M[a, b] > np.nanpercentile(M, 70) else "black"))
        ax.add_patch(plt.Rectangle((3 - 0.5, 2 - 0.5), 1, 1, fill=False, ec="black", lw=1.2))
        ax.set_xticks(range(6))
        ax.set_xticklabels(lam)
        ax.set_yticks(range(6))
        ax.set_yticklabels(lam)
        ax.set_xlabel("μ")
        ax.set_ylabel("λ")
        ax.grid(False)
        if i == 0:
            ax.set_title("PTK (λ × μ)")
        ax = axs[i, 3]
        ok = [r for r in tf if r["status"] == "ok" and r["terminal_factor"] != "1.25"]   # 1.25 not shown
        xs = [float(r["terminal_factor"]) for r in ok]
        ax.plot(xs, [float(r[key]) for r in ok], "o-", color=COL["PTK"], ms=3, lw=1.5)
        ax.plot([1], [float(next(r for r in ok if r["terminal_factor"] == "1")[key])], "o", ms=7, mfc="none",
                color="black")
        ax.axvspan(1.4, 4.1, color="#dddddd", lw=0)
        ax.text(2.7, ax.get_ylim()[0] + 0.5 * (ax.get_ylim()[1] - ax.get_ylim()[0]), "not computable\n(1.5–4)",
                ha="center", va="center", fontsize=6, color="#555555")
        ax.set_xlim(0, 4.2)
        ax.set_xlabel("terminal factor")
        if i == 0:
            ax.set_title("PTK terminal factor")
    fig.tight_layout()
    fig.savefig(OUT / "sensitivity.pdf")
    plt.close(fig)


def fig_d2():
    rows = read(RES / "diagnostics/d2_overlap.tsv")
    fig, axs = plt.subplots(2, 2, figsize=(7.2, 4.8))
    for i, rq in enumerate(("RQ1", "RQ2")):
        for j, g in enumerate(("LOC quartile", "McCabe")):
            ax = axs[i, j]
            for k in ("STK", "SSTK", "PTK"):
                for what, ls in (("relevant", "-"), ("top-10 non-relevant", "--")):
                    sel = [r for r in rows if r["rq"] == rq and r["grouping"] == g and r["kernel"] == k
                           and r["statistic"] == what]
                    x = np.arange(len(sel))
                    y = np.array([float(r["value"]) for r in sel])
                    ax.plot(x, y, color=COL[k], ls=ls, marker="o", ms=2.5, lw=1.3, label=f"{k}, {what}")
                ax.set_xticks(x)
                ax.set_xticklabels([r["group"] for r in sel])
            ax.grid(axis="x", visible=False)
            ax.set_xlabel("Lines of code (quartile)" if g == "LOC quartile" else "McCabe cyclomatic complexity")
            if j == 0:
                ax.set_ylabel(("Syntactic" if rq == "RQ1" else "Functional") + " similarity:\nDice overlap with the query")
    h, lab = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, lab, loc="lower center", ncol=3, fontsize=6.5)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(OUT / "d2_overlap.pdf")
    plt.close(fig)


def fig_noise():
    rows = read(RES / "analysis/noise.tsv")
    settings = [("default", "default", "o"), ("t2", "Type-2 copies ignored", "s"), ("no_fp", "false positives removed", "^")]
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.4))
    for i, (ms, title) in enumerate((("mean5", "Syntactic similarity: MAP, mean of 5 types"), ("functional", "Functional similarity: MAP"))):
        ax = axs[i]
        for s, (key, lab, mk) in enumerate(settings):
            for j, m in enumerate(METHODS):
                r = next(r for r in rows if r["setting"] == key and r["method"] == m and r["measure"] == ms
                         and r["metric"] == "MAP")
                ax.plot(j + (s - 1) * 0.22, float(r["value"]), mk, ms=3.5, color=COL[m],
                        mfc="white" if s else COL[m], label=lab if j == 0 else None)
        ax.set_xticks(range(len(METHODS)))
        ax.set_xticklabels(METHODS, rotation=30, ha="right")
        ax.grid(axis="x", visible=False)
        ax.set_title(title)
    h, lab = axs[0].get_legend_handles_labels()
    for hh in h:
        hh.set_color("black")
    fig.legend(h, lab, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.02))
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(OUT / "noise.pdf")
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    fig_sensitivity()
    fig_rq12_forest()
    fig_rq3()
    fig_rq4_forest()
    fig_d2()
    fig_noise()
    print("figures done")


if __name__ == "__main__":
    main()
