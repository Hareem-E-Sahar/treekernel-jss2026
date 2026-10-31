"""exp_v2 paper cost tables: evaluating the 100 RQ2 queries of one replicate set (seed 6251), one thread, corpus with
false positives (72,782 methods).

usage: .venv/bin/python exp_v2/paper/timing_tables.py   (after exp_v2/eval/timing.py)
  -> exp_v2/paper/tables/{rq2_cost,hybrid_cost}.tex
Inputs: exp_v2/results/timing/summary.tsv (exp_v2/scripts/run_timing.sh), codebert_encoding.json
(exp_v2/hybrid/timing_codebert.py --encode-sample 2000), trees.tsv and bm25_index.json
(exp_v2/scripts/run_timing_one_off.sh).
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAB = Path(__file__).resolve().parent / "tables"
TAB.mkdir(exist_ok=True)
KERNELS = ["STK", "SSTK", "PTK"]
S = {(r["group"], r["method"]): r for r in csv.DictReader(open(ROOT / "exp_v2/results/timing/summary.tsv"), delimiter="\t")}


def write(name, lines):
    (TAB / name).write_text("\n".join(lines) + "\n")


def per(g, m):
    return float(S[(g, m)]["per_query_s"])


# ---- RQ2: full rankings; per query is the main result, one-off costs (preparation + start-up) in one column
O = ROOT / "exp_v2/results/timing"
enc = json.loads((O / "codebert_encoding.json").read_text())
trees = {r["step"]: float(r["seconds"]) for r in csv.DictReader(open(O / "trees.tsv"), delimiter="\t")}
prep = {k: trees["parse"] + trees["variant D"] for k in KERNELS}
prep |= {"BM25": json.loads((O / "bm25_index.json").read_text())["index_seconds"],
         "CodeBERT": enc["corpus_encoding_s_estimate"]}
L = ["\\begin{table}[!htbp]", "\\centering",
     "\\caption{RQ2: time to evaluate the 100 functional queries of one replicate query set (seed 6251) against the "
     "corpus with false positives (72,782 methods), one thread. Per query = (time with the 100 queries $-$ time with "
     "none) / 100; 100 queries = 100 $\\times$ per query. One-off: paid once, not per query (tree kernels: parsing "
     "the methods, building the variant-D trees, reading them and computing the corpus self-similarities; BM25: "
     "building the Elasticsearch index, which uses Elasticsearch's own threads; CodeBERT: loading the model and "
     "encoding the corpus, estimated from "
     f"{enc['sample_methods']:,} random methods encoded one at a time). Fine-tuned CodeBERT has the same per-query "
     "cost as zero-shot and in addition needs fine-tuning, 75--87 min per model on 8 threads (not measured on one "
     "thread). Tree kernels at the tuned settings.}",
     "\\label{tab:rq2cost}", "\\footnotesize", "\\setlength{\\tabcolsep}{4pt}", "\\begin{tabular}{lrrr}", "\\toprule",
     "Method & Per query (s) & 100 queries (s) & One-off (s) \\\\", "\\midrule"]
for m in KERNELS + ["BM25", "CodeBERT"]:
    r = S[("full ranking", m)]
    p = float(r["per_query_s"])
    one = prep[m] + (0 if r["setup_s"] == "nan" else float(r["setup_s"]))
    L.append(f"{m} & {p:.2f} & {100 * p:,.0f} & {one:,.0f} \\\\")
L += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
write("rq2_cost.tex", L)

# ---- RQ4: hybrid against the full ranking
first = per("hybrid stage 1", "BM25 top 200")
L = ["\\begin{table}[!htbp]", "\\centering",
     "\\caption{RQ4, hybrid: time per query on the same 100 functional queries, corpus and machine as "
     "Table~\\ref{tab:rq2cost}, one thread. First stage: BM25's top 200 from Elasticsearch (client time). Second stage: "
     "the tree kernel on the top $k$ pairs, including reading those candidates' trees. Full ranking: from "
     "Table~\\ref{tab:rq2cost}, without its set-up. Speed-up = full ranking / hybrid.}",
     "\\label{tab:hybridcost}", "\\footnotesize", "\\setlength{\\tabcolsep}{4pt}", "\\begin{tabular}{lrrrrr}", "\\toprule",
     "Kernel & $k$ & First stage (s) & Second stage (s) & Hybrid (s) & Speed-up \\\\", "\\midrule"]
for k in KERNELS:
    full = per("full ranking", k)
    for K in (100, 200):
        sec = per(f"hybrid stage 2 (k={K})", k)
        L.append(f"{k if K == 100 else ''} & {K} & {first:.3f} & {sec:.3f} & {first + sec:.3f} & "
                 f"{full / (first + sec):.0f}$\\times$ \\\\")
    L.append(f" & full & & & {full:.2f} & \\\\")
    if k != KERNELS[-1]:
        L.append("\\midrule")
L += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
write("hybrid_cost.tex", L)
