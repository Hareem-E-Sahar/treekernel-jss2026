"""exp_v3_all_queries LaTeX tables, from exp_v3_all_queries/results/{analysis,diagnostics} and the exp_v2 tuning runs.

usage: .venv/bin/python exp_v3_all_queries/paper/make_tables.py   -> exp_v3_all_queries/paper/tables/*.tex
The time columns of the RQ2 table and the hybrid cost table are built from exp_v2/paper/tables: the timings were measured on a sample of
100 functional queries, one thread (exp_v2/scripts/run_timing.sh); the time for all queries is per query x 14,587.
"""
import re
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "exp_v3_all_queries/results"
A = RES / "analysis"
DG = RES / "diagnostics"
OUT = Path(__file__).resolve().parent / "tables"
TYPES = ["T1", "T2", "VST3", "ST3", "MT3"]
METRICS = ["nP@5", "nP@10", "MRR", "MAP"]
KERN = ["STK", "SSTK", "PTK"]
BASE = ["BM25", "CodeBERT zs", "CodeBERT ft"]
METHODS = KERN + BASE
MLAB = {"nP@5": "nP@5", "nP@10": "nP@10", "MRR": "MRR", "MAP": "MAP"}
N_QUERIES = 14587
HYBS = {k: [f"{k}-Hybrid"] for k in KERN}

# Setting, metrics and inference are described once in the text (paper.tex, section "Setup"), not in captions.


def read(path):
    return list(csv.DictReader(open(path), delimiter="\t"))


FIT = set()


def write(name, lines):
    """tables in FIT are scaled to the text width"""
    if name in FIT:
        i = next(i for i, l in enumerate(lines) if l.startswith("\\begin{tabular}"))
        j = next(i for i, l in enumerate(lines) if l.startswith("\\end{tabular}"))
        lines = lines[:i] + ["\\resizebox{\\textwidth}{!}{%"] + lines[i:j + 1] + ["}"] + lines[j + 1:]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text("\n".join(lines) + "\n")


RQNAME = {"RQ1": "Syntactic", "RQ2": "Functional"}   # row labels; the RQ numbers are not printed


def f3(x):
    return f"{float(x):.3f}"


def tex(s):
    return s.replace("→", "$\\rightarrow$").replace("&", "\\&")


def values():
    return {(r["method"], r["measure"], r["metric"]): r for r in read(A / "values.tsv")}


def compare(path=A / "compare.tsv"):
    return {(r["setting"], r["table"], r["a"], r["b"], r["measure"], r["metric"]): r for r in read(path)}


def mark(cmp, fam, a, ms, m, against, up, down, setting="default"):
    r = cmp.get((setting, fam, a, against, ms, m))
    if r is None or r["adj_ci_low"] == "":
        return ""
    if float(r["adj_ci_low"]) > 0:
        return up
    if float(r["adj_ci_high"]) < 0:
        return down
    return ""


def rq12_table(v, cmp, measures, label, caption, fam, cost=None):
    """cost: method -> time cells, appended as extra columns (RQ2). Several measures: the measure is a first column,
    centred vertically over its methods."""
    hdr = ["Per query (s)", "All queries (h)", "One-off (s)"] if cost else []
    group = len(measures) > 1
    n = len(METRICS) + len(hdr) + 1 + group
    lines = ["\\begin{table*}[!htbp]", "\\centering", f"\\caption{{{caption}}}", f"\\label{{{label}}}",
             "\\footnotesize", "\\setlength{\\tabcolsep}{4pt}",
             "\\begin{tabular}{" + ("l|l" if group else "l") + "c" * len(METRICS) + "r" * len(hdr) + "}", "\\toprule",
             ("Clone type & " if group else "") + "Method & " + " & ".join([MLAB[m] for m in METRICS] + hdr) + " \\\\",
             "\\midrule"]
    for bi, ms in enumerate(measures):
        best = {m: max(float(v[(x, ms, m)]["value"]) for x in METHODS) for m in METRICS}
        name = "\\begin{tabular}{@{}l@{}}Mean of\\\\5 types\\end{tabular}" if ms == "mean5" else ms
        for i, x in enumerate(METHODS):
            if i == 3 and not group:       # kernels / baselines rule only in the single-measure table (RQ2)
                lines.append(f"\\cmidrule(lr){{{1 + group}-{n}}}")
            cells = []
            for m in METRICS:
                val = float(v[(x, ms, m)]["value"])
                s = f"\\textbf{{{val:.3f}}}" if round(val, 3) == round(best[m], 3) else f"{val:.3f}"
                sup = ""
                if x != "BM25":
                    sup += mark(cmp, fam, x, ms, m, "BM25", "+", "-")
                if x in KERN:
                    sup += mark(cmp, fam, x, ms, m, "CodeBERT ft", "\\uparrow", "\\downarrow")
                cells.append(s + (f"$^{{{sup}}}$" if sup else ""))
            cells += cost[x] if cost else []
            first = ""
            if group:
                first = f"\\multirow{{{len(METHODS)}}}{{*}}{{{name}}} & " if i == 0 else " & "
            lines.append(first + x + " & " + " & ".join(cells) + " \\\\")
        if bi < len(measures) - 1:
            lines.append("\\midrule")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    return lines


def tested_table(cmp, rows, label, caption):
    """MAP comparisons tested with Bonferroni-adjusted CIs; rows: (table, a, b, measure). Bold: CI excludes 0."""
    lines = ["\\begin{table*}[!htbp]", "\\centering", f"\\caption{{{caption}}}", f"\\label{{{label}}}",
             "\\footnotesize", "\\setlength{\\tabcolsep}{4pt}", "\\begin{tabular}{lllrc}", "\\toprule",
             "Measure & A & B & $\\Delta$ MAP [adjusted CI] & $A_{12}$ \\\\", "\\midrule"]
    prev = None
    for table, a, b, ms in rows:
        if prev is not None and ms != prev:
            lines.append("\\midrule")
        prev = ms
        r = cmp[("default", table, a, b, ms, "MAP")]
        lo, hi = float(r["adj_ci_low"]), float(r["adj_ci_high"])
        d = f"{float(r['diff']):+.3f} [{lo:+.3f}, {hi:+.3f}]"
        if lo > 0 or hi < 0:
            d = f"\\textbf{{{d}}}"
        msl = {"mean5": "Mean of types", "functional": "Functional"}.get(ms, ms)
        lines.append(f"{msl} & {tex(a)} & {tex(b)} & {d} & {float(r['A12']):.2f} {r['A12_label'][:3]}. \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    return lines


def rq3_tables():
    rows = read(A / "rq3_groups.tsv")
    groups = {g: list(dict.fromkeys(r["group"] for r in rows if r["grouping"] == g)) for g in ("LOC quartile", "McCabe")}
    lines = ["\\begin{table*}[!htbp]", "\\centering",
             "\\caption{RQ3: MAP per quartile of the query's lines of code and per bin of its McCabe complexity. Syntactic similarity: mean of the five clone types. Last rows: (type-)queries per group.}",
             "\\label{tab:rq3}", "\\footnotesize", "\\setlength{\\tabcolsep}{3.5pt}",
             "\\begin{tabular}{l" + "c" * 4 + "|" + "c" * 5 + "}", "\\toprule",
             " & \\multicolumn{4}{c|}{Lines of code (quartile)} & \\multicolumn{5}{c}{McCabe} \\\\",
             "Method & " + " & ".join(g.replace("–", "--") for g in groups["LOC quartile"] + groups["McCabe"]) + " \\\\"]
    for rq in ("RQ1", "RQ2"):
        lines += ["\\midrule", f"\\multicolumn{{10}}{{l}}{{\\emph{{{'Syntactic similarity, mean of the five types' if rq == 'RQ1' else 'Functional similarity'}}}}} \\\\"]
        best = {}
        for g in ("LOC quartile", "McCabe"):
            for grp in groups[g]:
                best[(g, grp)] = max(float(r["MAP"]) for r in rows if r["rq"] == rq and r["grouping"] == g and r["group"] == grp)
        for i, x in enumerate(METHODS):
            if i == 3:
                lines.append("\\cmidrule(lr){1-10}")
            cells = []
            for g in ("LOC quartile", "McCabe"):
                for grp in groups[g]:
                    r = next(r for r in rows if r["rq"] == rq and r["grouping"] == g and r["group"] == grp and r["method"] == x)
                    val = float(r["MAP"])
                    cells.append(f"\\textbf{{{val:.3f}}}" if round(val, 3) == round(best[(g, grp)], 3) else f"{val:.3f}")
            lines.append(f"\\quad {x} & " + " & ".join(cells) + " \\\\")
        n = []
        for g in ("LOC quartile", "McCabe"):
            for grp in groups[g]:
                r = next(r for r in rows if r["rq"] == rq and r["grouping"] == g and r["group"] == grp)
                n.append(f"{int(r['type_queries']):,}")
        lines.append("\\quad Queries & " + " & ".join(n) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    write("rq3_groups.tex", lines)

    tr = read(A / "rq3_trend.tsv")
    lines = ["\\begin{table*}[!htbp]", "\\centering",
             "\\caption{RQ3, trend: change in AP per unit of log lines of code and of log McCabe (one model per predictor; for syntactic similarity within clone type). Upper rows: each method's slope; lower rows: a kernel's slope minus BM25's or fine-tuned CodeBERT's (negative = the kernel falls faster).}",
             "\\label{tab:rq3trend}", "\\footnotesize", "\\setlength{\\tabcolsep}{4pt}",
             "\\begin{tabular}{lcccc}", "\\toprule",
             " & \\multicolumn{2}{c}{Syntactic similarity} & \\multicolumn{2}{c}{Functional similarity} \\\\",
             "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}", " & log LOC & log McCabe & log LOC & log McCabe \\\\", "\\midrule"]

    def cell(method, stat_):
        out = []
        for rq in ("RQ1", "RQ2"):
            for p in ("log LOC", "log McCabe"):
                r = next(r for r in tr if r["rq"] == rq and r["predictor"] == p and r["method"] == method
                         and r["statistic"] == stat_)
                out.append(f"{float(r['value']):+.3f}")
        return out

    for x in METHODS:
        lines.append(f"{x} & " + " & ".join(cell(x, "slope")) + " \\\\")
    lines.append("\\midrule")
    for k in KERN:
        for b in ("BM25", "CodeBERT ft"):
            lines.append(f"{k} $-$ {b} & " + " & ".join(cell(k, f"minus {b}")) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    write("rq3_trend.tex", lines)

    mc = read(A / "rq3_mccabe10.tsv")
    lines = ["\\begin{table}[!htbp]", "\\centering",
             "\\caption{RQ3, McCabe's threshold: MAP of queries with McCabe $\\leq$ 10 and $>$ 10, and the difference.}",
             "\\label{tab:mccabe10}", "\\footnotesize", "\\setlength{\\tabcolsep}{3.5pt}",
             "\\begin{tabular}{lccc}", "\\toprule", "Method & $\\leq$ 10 & $>$ 10 & $>$10 $-$ $\\leq$10 \\\\"]
    for rq in ("RQ1", "RQ2"):
        lines += ["\\midrule", f"\\multicolumn{{4}}{{l}}{{\\emph{{{'Syntactic similarity, mean of the five types' if rq == 'RQ1' else 'Functional similarity'}}}}} \\\\"]
        for r in (r for r in mc if r["rq"] == rq):
            d = f"{float(r['high_minus_low']):+.3f}"
            lines.append(f"\\quad {r['method']} & {f3(r['low_value'])} & {f3(r['high_value'])} & {d} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    write("rq3_mccabe10.tex", lines)


def rq4_table(v, cmp):
    cols = [("mean5", m) for m in METRICS] + [("functional", m) for m in METRICS]
    lines = ["\\begin{table*}[!htbp]", "\\centering",
             "\\caption{RQ4: hybrids (BM25's top 100 re-ranked by the kernel) next to each kernel's full ranking, BM25 and fine-tuned CodeBERT, every eligible query. Syntactic similarity: mean of the five clone types. Time: mean seconds per query over the timing sample of Table~\\ref{tab:rq2}, one thread; a hybrid's time is BM25's time plus the kernel's re-ranking of BM25's top 100. $^{\\ast}$/$^{\\circ}$: hybrid significantly better/worse than its kernel's full ranking; $^{+}$/$^{-}$: than BM25; $^{\\uparrow}$/$^{\\downarrow}$: than fine-tuned CodeBERT (MAP; Bonferroni-adjusted CI excludes 0, Figure~\\ref{fig:rq4}).}",
             "\\label{tab:rq4}", "\\footnotesize", "\\setlength{\\tabcolsep}{3.5pt}",
             "\\begin{tabular}{l" + "c" * 8 + "||r}", "\\toprule",
             " & \\multicolumn{4}{c}{Syntactic similarity: mean of the five types} & \\multicolumn{4}{c}{Functional similarity} & \\\\",
             "\\cmidrule(lr){2-5}\\cmidrule(lr){6-9}",
             "Method & " + " & ".join(MLAB[m] for _, m in cols) + " & Time (s) \\\\", "\\midrule"]
    hyb, cost = hybrid_timings(), cost_cells()
    time = {k: hyb[k]["full"][4] for k in KERN} | {x: cost[x][0] for x in ("BM25", "CodeBERT ft")}
    # hybrid = BM25 (whose order is kept below rank 100) + the hybrid's own retrieval and re-ranking of the top 100
    time |= {HYBS[k][0]: f"{float(time['BM25']) + float(hyb[k]['100'][4]):.3f}" for k in KERN}
    allm = [x for k in KERN for x in [k] + HYBS[k]] + ["BM25", "CodeBERT ft"]
    best = {c: max(float(v[(x, c[0], c[1])]["value"]) for x in allm) for c in cols}
    for k in KERN:
        for x in [k] + HYBS[k]:
            cells = []
            for ms, m in cols:
                val = float(v[(x, ms, m)]["value"])
                s = f"\\textbf{{{val:.3f}}}" if round(val, 3) == round(best[(ms, m)], 3) else f"{val:.3f}"
                sup = ""
                if x != k:
                    sup = (mark(cmp, "RQ4", x, ms, m, k, "\\ast", "\\circ") + mark(cmp, "RQ4", x, ms, m, "BM25", "+", "-")
                           + mark(cmp, "RQ4", x, ms, m, "CodeBERT ft", "\\uparrow", "\\downarrow"))
                cells.append(s + (f"$^{{{sup}}}$" if sup else ""))
            lines.append(f"{x} & " + " & ".join(cells) + f" & {time[x]} \\\\")
        lines.append("\\midrule")
    for x in ("BM25", "CodeBERT ft"):
        cells = []
        for ms, m in cols:
            val = float(v[(x, ms, m)]["value"])
            cells.append(f"\\textbf{{{val:.3f}}}" if round(val, 3) == round(best[(ms, m)], 3) else f"{val:.3f}")
        lines.append(f"{x} & " + " & ".join(cells) + f" & {time[x]} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    write("rq4_hybrid.tex", lines)


def cost_cells():
    """method -> [per query, all queries (estimate, h), one-off], from the exp_v2 timings (timing sample of 100
    queries). Fine-tuned CodeBERT: same per-query cost; its one-off cost (training, encoding per fold) is in the text."""
    out = {}
    for l in (ROOT / "exp_v2/paper/tables/rq2_cost.tex").read_text().splitlines():
        c = [x.strip() for x in l.rstrip(" \\").split("&")]
        if len(c) == 4 and c[0] != "Method":
            cells = [c[1], f"{float(c[1]) * N_QUERIES / 3600:.1f}", c[3]]
            if c[0] == "CodeBERT":
                out["CodeBERT zs"], out["CodeBERT ft"] = cells, cells[:2] + ["see text"]
            else:
                out[c[0]] = cells
    return out


def hybrid_timings():
    """kernel -> {"100": row, "full": row} of the exp_v2 hybrid timing table (row[4] = total seconds per query)."""
    rows = defaultdict(dict)
    kern = None
    for l in (ROOT / "exp_v2/paper/tables/hybrid_cost.tex").read_text().splitlines():
        c = [x.strip() for x in l.rstrip(" \\\\").split("&")]
        if len(c) == 6 and c[0] != "Kernel":
            kern = c[0] or kern
            rows[kern][c[1]] = c
    return rows


def cost_tables():
    """Stage-wise hybrid timing table (repository only; the paper has the total in the RQ4 table)."""
    rows = hybrid_timings()
    lines = ["\\begin{table}[!htbp]", "\\centering",
             "\\caption{RQ4: mean time per query of the hybrids over the timing sample of Table~\\ref{tab:rq2}, one thread. "
             "First stage: BM25's top 200 from Elasticsearch (client time), of which the hybrid uses the top 100. Second "
             "stage: the tree kernel on those 100 candidates, including reading their trees. Speed-up = full ranking / "
             "hybrid.}", "\\label{tab:hybridcost}", "\\footnotesize", "\\setlength{\\tabcolsep}{4pt}",
             "\\begin{tabular}{lrrrrr}", "\\toprule",
             "Method & First stage (s) & Second stage (s) & Hybrid (s) & Full ranking (s) & Speed-up \\\\", "\\midrule"]
    for k in KERN:
        c = rows[k]["100"]
        lines.append(f"{k}-Hybrid & {c[2]} & {c[3]} & {c[4]} & {rows[k]['full'][4]} & {c[5]} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    write("hybrid_cost.tex", lines)


def sensitivity_table():
    grid = {r["setting"]: r for r in read(ROOT / "exp_v2/tuning/grid.tsv")}
    nc = {}
    for f in (ROOT / "results/grid_scan/main_corpus").glob("D_*.ids"):
        n = sum(1 for l in open(f) if l.strip())
        if n:
            p = f.stem.split("_")
            nc["_".join([p[1], "l" + p[2]] + (["m" + p[3]] if len(p) > 3 else []))] = n
    for r in read(ROOT / "exp_v2/tuning/grid.tsv"):
        if r["status"] != "ok":
            nc[r["setting"]] = int(r["status"].split("=")[1].split()[0])
    lam = ["0.1", "0.2", "0.4", "0.6", "0.8", "1.0"]

    def cell(key):
        g = grid.get(key)
        if g and g["status"] == "ok":
            return f"{float(g['rq1_mean5_map']):.3f}"
        return f"n.c. ({nc[key]:,})" if key in nc else "--"

    lines = ["\\begin{table*}[!htbp]", "\\centering",
             "\\caption{Kernel hyper-parameters: MAP for syntactic similarity (mean of the five types) on the 50 tuning queries. n.c.\\ = not computable (KeLP's float overflows; in brackets the number of overflowing methods). Selected settings in bold. Last rows: PTK's terminal factor at $\\lambda$ = 0.4, $\\mu$ = 0.6.}",
             "\\label{tab:sensitivity}", "\\footnotesize", "\\setlength{\\tabcolsep}{3pt}",
             "\\begin{tabular}{ll" + "c" * 6 + "}", "\\toprule",
             "Kernel & & " + " & ".join(f"$\\lambda$ = {l}" for l in lam) + " \\\\", "\\midrule"]
    for k, sel in (("STK", "1.0"), ("SSTK", "0.1")):
        cells = [cell(f"{k}_l{l}") for l in lam]
        cells = [f"\\textbf{{{c}}}" if l == sel else c for c, l in zip(cells, lam)]
        lines.append(f"{k} & & " + " & ".join(cells) + " \\\\")
    lines.append("\\midrule")
    for mu in lam:
        cells = [cell(f"PTK_l{l}_m{mu}") for l in lam]
        cells = [f"\\textbf{{{c}}}" if (l, mu) == ("0.4", "0.6") else c for c, l in zip(cells, lam)]
        lines.append(f"{'PTK' if mu == '0.1' else ''} & $\\mu$ = {mu} & " + " & ".join(cells) + " \\\\")
    lines += ["\\midrule"]
    tf = read(ROOT / "exp_v2/tuning/terminal_factor.tsv")
    lines.append("PTK & terminal factor & " + " & ".join(r["terminal_factor"] for r in tf[:6]) + " \\\\")
    vals = []
    for r in tf[:6]:
        s = f"{float(r['rq1_mean5_map']):.3f}" if r["status"] == "ok" else "n.c."
        vals.append(f"\\textbf{{{s}}}" if r["terminal_factor"] == "1" else s)
    lines.append(" & ($\\lambda$ 0.4, $\\mu$ 0.6) & " + " & ".join(vals) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    write("sensitivity.tex", lines)


def noise_tables():
    if not (A / "noise.tsv").exists():
        return
    nz = {(r["setting"], r["method"], r["measure"], r["metric"]): r for r in read(A / "noise.tsv")}
    settings = [("default", "Default"), ("t2", "Type-2 ign."), ("no_fp", "FP removed")]
    lines = ["\\begin{table*}[!htbp]", "\\centering",
             "\\caption{Label noise: MAP on every eligible query with the default labels, with Type-2 copies of the query outside its functionality ignored, and with all false positives removed. Syntactic similarity: mean of the five types. Lower rows: differences.}",
             "\\label{tab:noise}", "\\footnotesize", "\\setlength{\\tabcolsep}{3.5pt}",
             "\\begin{tabular}{lcccccc}", "\\toprule",
             " & \\multicolumn{3}{c}{Syntactic similarity} & \\multicolumn{3}{c}{Functional similarity} \\\\",
             "\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}",
             "Method & " + " & ".join(s for _, s in settings) + " & " + " & ".join(s for _, s in settings) + " \\\\",
             "\\midrule"]
    for x in METHODS:
        lines.append(f"{x} & " + " & ".join(f3(nz[(s, x, ms, 'MAP')]["value"]) for ms in ("mean5", "functional")
                                            for s, _ in settings) + " \\\\")
    lines.append("\\midrule")
    nc = compare(A / "noise_compare.tsv")
    pairs = [(k, b) for k in KERN for b in ("BM25", "CodeBERT ft")] + [("CodeBERT ft", "BM25")]
    for a, b in pairs:
        cells = []
        for ms in ("mean5", "functional"):
            for s, _ in settings:
                r = nc[(s, "noise", a, b, ms, "MAP")]
                cells.append(f"{float(r['diff']):+.3f}")
        lines.append(f"{a} $-$ {b} & " + " & ".join(cells) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    write("noise.tex", lines)


def diag_overview():
    """Tree shape (D1) and fragment overlap (D2) per LOC quartile, for the revision document."""
    d1 = {r["group"]: r for r in read(DG / "d1_tree_shape.tsv") if r["grouping"] == "LOC quartile"}
    d2 = {(r["rq"], r["group"], r["kernel"], r["statistic"]): float(r["value"]) for r in read(DG / "d2_overlap.tsv")
          if r["grouping"] == "LOC quartile"}
    lines = ["\\begin{table}[!htbp]", "\\centering",
             "\\caption{Tree shape (medians) and fragment overlap with the query (means), per quartile of lines of code. "
             "Rel.: relevant methods; Wrong: the kernel's 10 highest-scoring non-relevant methods. Overlap is measured on "
             "complete subtrees for STK and on productions for SSTK and PTK, so their Rel.\\ values are the same.}",
             "\\label{tab:diag}", "\\footnotesize", "\\setlength{\\tabcolsep}{4pt}",
             "\\begin{tabular}{l|rrr|ccccc|ccccc}", "\\toprule",
             " & & & & \\multicolumn{5}{c}{Syntactic similarity} & \\multicolumn{5}{c}{Functional similarity} \\\\",
             "\\cmidrule(lr){5-9}\\cmidrule(lr){10-14}",
             " & & & Max & \\multicolumn{2}{c}{Rel.} & \\multicolumn{3}{c}{Wrong} & \\multicolumn{2}{c}{Rel.} & "
             "\\multicolumn{3}{c}{Wrong} \\\\",
             "\\cmidrule(lr){5-6}\\cmidrule(lr){7-9}\\cmidrule(lr){10-11}\\cmidrule(lr){12-14}",
             "LOC & Nodes & Height & branch. & STK & \\shortstack{SSTK,\\\\PTK} & STK & SSTK & PTK & STK & "
             "\\shortstack{SSTK,\\\\PTK} & STK & SSTK & PTK \\\\", "\\midrule"]
    for g, r in d1.items():
        cells = [g.split("(")[1].rstrip(")").replace("–", "--"), f"{float(r['nodes_median']):.0f}",
                 f"{float(r['height_median']):.0f}", f"{float(r['max_branching_median']):.0f}"]
        for rq in ("RQ1", "RQ2"):
            assert abs(d2[(rq, g, "SSTK", "relevant")] - d2[(rq, g, "PTK", "relevant")]) < 1e-9
            cells += [f"{d2[(rq, g, 'STK', 'relevant')]:.2f}", f"{d2[(rq, g, 'PTK', 'relevant')]:.2f}"]
            cells += [f"{d2[(rq, g, k, 'top-10 non-relevant')]:.2f}" for k in ("STK", "SSTK", "PTK")]
        lines.append(" & ".join(cells) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    write("diag_overview.tex", lines)


def diagnostics_tables():
    if not (DG / "d4_model.tsv").exists():
        return
    d1 = read(DG / "d1_tree_shape.tsv")
    lines = ["\\begin{table*}[!htbp]", "\\centering",
             "\\caption{Tree shape of the eligible queries per LOC quartile and McCabe bin, median [interquartile range].}",
             "\\label{tab:d1}", "\\scriptsize", "\\setlength{\\tabcolsep}{2.5pt}",
             "\\begin{tabular}{llrrcccc}", "\\toprule",
             "Grouping & Group & Queries & Funct. & Nodes & Height & Mean branching & Max branching \\\\", "\\midrule"]
    prev = None
    for r in d1:
        if prev and r["grouping"] != prev:
            lines.append("\\midrule")
        g = r["grouping"] if r["grouping"] != prev else ""
        prev = r["grouping"]

        def mi(f, nd=0):
            fmt = f"{{:.{nd}f}}"
            return (fmt.format(float(r[f + "_median"])) + " [" + fmt.format(float(r[f + "_q1"])) + "--"
                    + fmt.format(float(r[f + "_q3"])) + "]")
        lines.append(f"{g} & {r['group'].replace('–', '--').replace('>', '$>$')} & {int(r['queries']):,} & {r['functionalities']} & {mi('nodes')} & "
                     f"{mi('height')} & {mi('mean_branching', 2)} & {mi('max_branching')} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    write("d1.tex", lines)

    # paper version (RQ3): LOC quartiles only; d1.tex with the McCabe bins stays in the response letter
    lines = ["\\begin{table*}[!htbp]", "\\centering",
             "\\caption{Tree shape of the eligible queries per LOC quartile, median [interquartile range].}",
             "\\label{tab:d1}", "\\scriptsize", "\\setlength{\\tabcolsep}{2.5pt}",
             "\\begin{tabular}{lrrcccc}", "\\toprule",
             "LOC quartile & Queries & Funct. & Nodes & Height & Mean branching & Max branching \\\\", "\\midrule"]
    for r in d1:
        if r["grouping"] != "LOC quartile":
            continue

        def mi(f, nd=0):
            fmt = f"{{:.{nd}f}}"
            return (fmt.format(float(r[f + "_median"])) + " [" + fmt.format(float(r[f + "_q1"])) + "--"
                    + fmt.format(float(r[f + "_q3"])) + "]")
        lines.append(f"{r['group'].replace('–', '--')} & {int(r['queries']):,} & {r['functionalities']} & {mi('nodes')} & "
                     f"{mi('height')} & {mi('mean_branching', 2)} & {mi('max_branching')} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    write("d1_loc.tex", lines)

    d3 = read(DG / "d3_branching.tsv")
    lines = ["\\begin{table*}[!htbp]", "\\centering",
             "\\caption{MAP of PTK and STK by quartile of the query's maximum branching (lowest and highest value of each group in brackets); last column: PTK $-$ STK. Syntactic: mean of the five types.}",
             "\\label{tab:d3}", "\\footnotesize", "\\setlength{\\tabcolsep}{3pt}",
             "\\begin{tabular}{llccc}", "\\toprule",
             " & Max branching & PTK & STK & PTK $-$ STK \\\\",
             "\\midrule"]
    prev = None
    for r in d3:
        if prev and r["rq"] != prev:
            lines.append("\\midrule")
        g = RQNAME[r["rq"]] if r["rq"] != prev else ""
        prev = r["rq"]

        lab = re.sub(r"\((\d+)–\1\)", r"(\1)", r['max_branching_quartile']).replace('–', '--')   # B2 (7–7) -> B2 (7)
        lines.append(f"{g} & {lab} & {f3(r['PTK_MAP'])} & {f3(r['STK_MAP'])} & "
                     f"{float(r['PTK_minus_STK_MAP']):+.3f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    write("d3.tex", lines)

    d4 = read(DG / "d4_model.tsv")
    preds = list(dict.fromkeys(r["predictor"] for r in d4))
    lines = ["\\begin{table*}[!htbp]", "\\centering",
             "\\caption{D4: standardised coefficients of the per-query model of AP, one model per method (syntactic similarity within clone type).}",
             "\\label{tab:d4}", "\\footnotesize", "\\setlength{\\tabcolsep}{4pt}",
             "\\begin{tabular}{ll" + "c" * len(preds) + "}", "\\toprule",
             " & Method & " + " & ".join(preds) + " \\\\", "\\midrule"]
    for rq in ("RQ1", "RQ2"):
        if rq == "RQ2":
            lines.append("\\midrule")
        for i, x in enumerate(METHODS):
            cells = []
            for p in preds:
                r = next(r for r in d4 if r["rq"] == rq and r["method"] == x and r["predictor"] == p)
                cells.append(f"{float(r['coef']):+.3f}")
            lines.append(f"{RQNAME[rq] if i == 0 else ''} & {x} & " + " & ".join(cells) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    write("d4.tex", lines)

    c = read(DG / "d4_predictor_correlations.tsv")
    lines = ["\\begin{table}[!htbp]", "\\centering",
             "\\caption{D4 predictors: Pearson correlations over the eligible queries.}", "\\label{tab:d4corr}",
             "\\scriptsize", "\\setlength{\\tabcolsep}{2.5pt}", "\\begin{tabular}{l" + "c" * len(preds) + "}",
             "\\toprule", " & " + " & ".join(preds) + " \\\\", "\\midrule"]
    for r in c:
        lines.append(r["predictor"] + " & " + " & ".join(r[p] for p in preds) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    write("d4_corr.tex", lines)


def revision_table():
    """R2-C5, for the response letter (Oct/revision.tex): the RQ4 tests with their adjusted p-values, as a table like
    tables/sensitivity.tex (the letter's preamble defines table* as a plain block)."""
    cmp = compare()
    lines = ["\\begin{table*}[!htbp]", "\\centering",
             "\\caption{RQ4 test results. Each hybrid (BM25's top 100 re-ranked by a tree kernel) against "
             "its kernel's full ranking, BM25 and fine-tuned CodeBERT. Difference in MAP between hybrid and other model "
             "with Bonferroni-adjusted 99.4\\% CI and $p$-value (9 comparisons per measure), and effect size $A_{12}$. "
             "Bold values indicate that CI excludes 0.}", "\\label{tab:rq4_tests}", "\\footnotesize", "\\setlength{\\tabcolsep}{3pt}",
             "\\begin{tabular}{lllrrrl}", "\\toprule",
             "Measure & Hybrid & Against & $\\Delta$ MAP & Adjusted CI & Adjusted $p$ & $A_{12}$ \\\\", "\\midrule"]
    prev = None
    for ms, name in (("mean5", "Mean of types"), ("functional", "Functional")):
        for k in KERN:
            for h in HYBS[k]:
                for b in (k, "BM25", "CodeBERT ft"):
                    r = cmp[("default", "RQ4", h, b, ms, "MAP")]
                    if prev is not None and ms != prev:
                        lines.append("\\midrule")
                    prev = ms
                    lo, hi, p = float(r["adj_ci_low"]), float(r["adj_ci_high"]), float(r["p_adj"])
                    d, ci = f"{float(r['diff']):+.3f}", f"[{lo:+.3f}, {hi:+.3f}]"
                    ps = "$<$0.002" if p < 0.002 else f"{p:.3f}"    # smallest non-zero value: 9 x 2 / 10,000
                    if lo > 0 or hi < 0:
                        d, ci, ps = (f"\\textbf{{{x}}}" for x in (d, ci, ps))
                    lines.append(f"{name} & {h} & {b} & {d} & {ci} & {ps} & "
                                 f"{float(r['A12']):.2f} {r['A12_label']} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    (ROOT / "exp_v3_all_queries/Oct/rq4_tests_table.tex").write_text("\n".join(lines) + "\n")


def quadrant_table():
    """R2-C4, for the response letter only: MAP per size x complexity quadrant (median splits; eval/quadrants.py)."""
    if not (A / "rq3_quadrants.tsv").exists():
        return
    rows = read(A / "rq3_quadrants.tsv")
    lm, cm = rows[0]["loc_median"], rows[0]["cc_median"]
    cells = [("small", "simple"), ("small", "complex"), ("large", "simple"), ("large", "complex")]
    lines = ["\\begin{table}[!htbp]", "\\centering",
             f"\\caption{{MAP per group of queries split at the median lines of code ({lm}) and the median McCabe "
             f"complexity ({cm}), every eligible query. Syntactic similarity: mean of the five clone types; queries: "
             "type-queries.}", "\\label{tab:quadrants}", "\\footnotesize", "\\setlength{\\tabcolsep}{4pt}",
             "\\begin{tabular}{lcccc}", "\\toprule",
             f" & \\multicolumn{{2}}{{c}}{{LOC $\\le$ {lm}}} & \\multicolumn{{2}}{{c}}{{LOC $>$ {lm}}} \\\\",
             "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}",
             f"Method & McCabe $\\le$ {cm} & McCabe $>$ {cm} & McCabe $\\le$ {cm} & McCabe $>$ {cm} \\\\"]
    for ms, name in (("mean5", "Syntactic similarity"), ("functional", "Functional similarity")):
        sel = [r for r in rows if r["measure"] == ms]
        lines += ["\\midrule", f"\\multicolumn{{5}}{{l}}{{\\emph{{{name}}}}} \\\\"]
        for m in dict.fromkeys(r["method"] for r in sel):
            vals = [next(r for r in sel if r["method"] == m and (r["size"], r["complexity"]) == c)["MAP"] for c in cells]
            lines.append(f"\\quad {m} & " + " & ".join(f3(v) for v in vals) + " \\\\")
        n = [next(r for r in sel if (r["size"], r["complexity"]) == c)["queries"] for c in cells]
        lines.append("\\quad Queries & " + " & ".join(f"{int(x):,}" for x in n) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    write("rq3_quadrants.tex", lines)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cost_tables()
    sensitivity_table()
    v, cmp = values(), compare()
    leg = ("MAP: $^{+}$/$^{-}$ significantly better/worse than BM25; $^{\\uparrow}$/$^{\\downarrow}$: tree kernel "
           "significantly better/worse than fine-tuned CodeBERT (Bonferroni-adjusted CI excludes 0). Best value per "
           "block and column in bold. ")
    write("rq1.tex", rq12_table(v, cmp, TYPES + ["mean5"], "tab:rq1",
                                "Syntactic clones per clone type, every eligible query. " + leg
                                + "Test results are shown in Figure~\\ref{fig:rq1}.", "RQ1"))
    write("rq2.tex", rq12_table(v, cmp, ["functional"], "tab:rq2",
                                'Functional similarity on every eligible query, and mean runtime cost using one thread. Best metric value per block and column in bold. MAP: $^{+}$/$^{-}$ significantly better/worse than BM25; $^{\\uparrow}$/$^{\\downarrow}$: tree kernel significantly better/worse than fine-tuned CodeBERT (Bonferroni-adjusted CI excludes 0). Corresponding test results are in Figure~\\ref{fig:rq2}. One-off cost is paid once, not per query.', "RQ2", cost_cells()))
    pairs = [("SSTK", "STK"), ("PTK", "STK"), ("PTK", "SSTK")] + [(k, b) for k in KERN for b in ("BM25", "CodeBERT ft")]
    rq3_tables()
    rq4_table(v, cmp)
    rows4 = [("RQ4", h, b, ms) for ms in ("mean5", "functional") for k in KERN for h in HYBS[k]
             for b in (k, "BM25", "CodeBERT ft")]
    write("rq4_effects.tex", tested_table(
        cmp, rows4, "tab:rq4effects",
        "RQ4 tests on MAP: each hybrid against its kernel's full ranking, BM25 and fine-tuned CodeBERT; difference "
        "A $-$ B with Bonferroni-adjusted 99.4\\% CI (9 comparisons per measure) and effect size $A_{12}$. Bold: CI "
        "excludes 0."))
    revision_table()
    quadrant_table()
    noise_tables()
    diagnostics_tables()
    diag_overview()
    print("tables done")


if __name__ == "__main__":
    main()
