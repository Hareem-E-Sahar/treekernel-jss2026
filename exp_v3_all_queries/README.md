# exp_v3_all_queries: every eligible query (revision)

The revised evaluation planned in `revision_plan.md`. All methods are evaluated on every eligible query instead of
samples of 100 (R1-C1a). Same setting as exp_v2: corpus with false positives (`data/trees_e5/D.tsv`, 72,782 methods),
variant D, settings tuned in exp_v2 (`exp_v2/tuning/selected.json`: STK λ 1.0; SSTK λ 0.1; PTK λ 0.4, μ 0.6, terminal
factor 1). exp_v2 code and results are only read; new or changed code lives here.

Queries: `exp_v2/data/full/` (14,587 = 14,679 true positives − 50 tuning queries − 42 spanning CodeBERT folds; T1
3,746, T2 998, VST3 1,991, ST3 4,652, MT3 7,722, functional 14,587).

## Steps

| Step | Command | Output | Plan |
|---|---|---|---|
| 1 | `scripts/run_kernels.sh` (2026-11-04, 00:49–10:27) | `results/runs/D_{STK,SSTK,PTK}`: rows of 8,972 queries reused from the exp_v2 replicate and size-complexity runs, 5,615 scored | R1-C1a |
| 2 | `scripts/run_eval_main.sh` | `results/full/D_*/eval` (BM25, CodeBERT and the hybrids: `exp_v2/results/hybrid/full`, same queries) | R1-C1a |
| 3 | `.venv/bin/python exp_v3_all_queries/prep/t2_copies.py` | `data/t2_copies.tsv`, `data/t2_copies_summary.tsv` | R1-C3 B |
| 4 | `scripts/run_eval_noise.sh` | `results/noise/{t2,no_fp}/<run>/eval` (`eval/evaluate.py`: exp_v2 copy with `--drop-fp` and repeatable `--ignore`) | R1-C3 A, B |
| 5 | `.venv/bin/python exp_v3_all_queries/eval/analyze.py` | `results/analysis/`: values, comparisons (Δ, A₁₂; tested: adjusted CI and p), RQ3 groups and trends, McCabe 10, label noise | R1-C1a, R1-C3, R2-C4, R2-C5 |
| 6 | `.venv/bin/python exp_v3_all_queries/eval/trees.py` then `eval/diagnostics.py` | `results/diagnostics/`: D1 tree shape, D2 overlap, D3 branching, D4 per-query model | R1-C4 |
| 7 | `.venv/bin/python exp_v3_all_queries/paper/make_tables.py`, `paper/figures.py`, then `pdflatex paper.tex` (twice) in `paper/` | `paper/tables/`, `paper/figures/`, `paper/paper.pdf`; `Oct/revision.tex` holds the hyper-parameter, label-noise and diagnostics sections for now | all |

`eval/common.py` holds the shared definitions: groups (LOC quartiles 3–13, 14–21, 22–35, 36–433; McCabe bins 1, 2–3,
4–5, 6–10, > 10) and inference (bootstrap over the 43 functionalities, B = 10,000, a query in several functionalities
assigned to its lowest functionality id; Bonferroni-adjusted percentile CIs for the tested comparisons only (see
Notes); paired Vargha–Delaney A₁₂).

## Notes

- Tests (revision_plan.md, R2-C5 2a): only MAP in RQ1 (per clone type and the mean of types), RQ2 and RQ4 (9 comparisons
  each; one hybrid per kernel, BM25's top 100). Bonferroni-adjusted percentile CI from 10,000 functionality resamples (level
  1 − 0.05/m); significant when it excludes 0. `compare.tsv`: `test_family`, `m`, `ci_level`, `adj_ci_*`, and `p_adj`
  (the matching adjusted p, for the response letter). Everything else (other metrics, baseline pairs, zero-shot, RQ3,
  label noise, D1–D4) is a plain value, without CIs or tests.
- Every comparison (all metrics, all clone types) is in `results/analysis/compare.tsv`, not in paper.pdf.
- Time columns (RQ2 table) and hybrid cost table: per-query times measured in exp_v2 on a timing sample of 100 functional queries (one thread); the exp_v3
  run itself was not a timing run. The all-queries column is an estimate (per query × 14,587).
- Score fusion (future RQs in exp_v2) is not part of this document.
