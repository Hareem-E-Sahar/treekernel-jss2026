# Tree kernels for similar source code retrieval

Code and results for "An Empirical Evaluation of Tree Kernels for Similar Source Code Retrieval"
(Sahar, Hindle, Barbosa; Journal of Systems and Software, revision submitted 2026-11-16).

## Final results: `exp_v3_all_queries/`

The revised evaluation, on every eligible query (14,587), is in **`exp_v3_all_queries/`**. Its README lists the
steps; the paper's tables come from `exp_v3_all_queries/paper/make_tables.py` and the numbers from
`exp_v3_all_queries/results/analysis/`. The response letter source is in
`exp_v3_all_queries/revision_october_2026/revision.tex`. The submitted state is tagged `jss-revision-submitted`.

## Earlier stages (read by exp_v3)

- `prep/`, `kernels/`, `bm25/`, `embed/`, `eval/`, `scripts/`: the pipeline (trees, KeLP kernels, BM25, CodeBERT, ranking and metrics).
- `exp_v2/`: query lists, hyper-parameter tuning, CodeBERT fine-tuning, the hybrid and its timing.
- `results/`: results of earlier runs.

Large outputs (trees, embeddings, the 24 GB of kernel rankings in `exp_v3_all_queries/results/runs`) are not in git;
the code regenerates them from BigCloneBench.
