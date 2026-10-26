# exp_v2 paper assets

Corpus with false positives only (the main-corpus results in `exp_v2/results/main/` are kept but not used in the paper).
10 replicate query sets; every table cell is mean ± SD over the replicates, every box plot shows the 10 replicate values.

Order:
1. `.venv/bin/python exp_v2/eval/replicate_metrics.py fp` → `exp_v2/results/fp/{per_replicate_metrics,pooled_compare_metrics}.tsv`
   (MAP, MAP@R, MRR, nP@5, nP@10 per replicate; pooled paired bootstrap over functionalities per metric).
2. `.venv/bin/python exp_v2/paper/make_tables.py` → `tables/`
3. `Rscript exp_v2/paper/figures.R` → `figures/` (ggplot2, `geom_boxplot` with its defaults)
4. Size and complexity: `.venv/bin/python exp_v2/paper/size_complexity_tables.py` → `tables/size_complexity*.tex`;
   `Rscript exp_v2/paper/size_complexity.R` → `figures/size_complexity_rq{1,2}.pdf`
   (inputs from `exp_v2/eval/size_complexity.py`).
5. Hybrid: `.venv/bin/python exp_v2/paper/hybrid_tables.py` → `tables/hybrid_*.tex`; `Rscript exp_v2/paper/hybrid.R`
   → `figures/hybrid_*.pdf` (inputs from `exp_v2/eval/hybrid.py`).
6. `pdflatex preview.tex` (twice, from this folder) → `preview.pdf`, all tables and figures.

| File | Contents |
|---|---|
| `tables/rq1.tex` | RQ1: nP@5, nP@10, MRR, MAP as columns; one row block per clone type and for the mean over the types |
| `tables/rq2.tex` | RQ2 (functional): the same four metrics, one row per method |
| `tables/rq4_fusion.tex` | RQ4: PTK fusions (ST3, MT3, mean MAP) and STK fusions (functional MAP) next to their components |
| `tables/size_complexity.tex` | Size and complexity: RQ1 and RQ2 MAP per group (small/large LOC, low/high McCabe) |
| `tables/size_complexity_interaction.tex` | Size and complexity: change of each method difference between groups, with 95% CIs |
| `tables/hybrid_full.tex` | Hybrid on every eligible query: MAP per type, mean and functional, each with its 95% CI |
| `tables/hybrid_replicates.tex` | Hybrid vs the full-ranking kernels on the 10 replicate sets, mean ± SD |
| `tables/hybrid_cost.tex` | Hybrid cost per query: first stage, re-ranking top 100 / 200, full ranking |
| `figures/rq1_metrics.pdf` | RQ1 per clone type, four panels: nP@5, nP@10, MRR, MAP |
| `figures/rq2_metrics.pdf` | RQ2, four panels: nP@5, nP@10, MRR, MAP |
| `figures/rq4_fusion_rq1.pdf` | RQ4, PTK fusions, mean over the types, four panels |
| `figures/rq4_fusion_rq2.pdf` | RQ4, STK fusions, functional, four panels |
| `figures/size_complexity_rq1.pdf` | Size and complexity, mean over the types per group: nP@5, nP@10, MRR, MAP |
| `figures/size_complexity_rq2.pdf` | Size and complexity, functional per group: nP@5, nP@10, MRR, MAP |
| `figures/hybrid_full.pdf` | Hybrid on every eligible query: value and 95% CI; RQ1 and RQ2, four metrics each |
| `figures/hybrid_rq1.pdf` | Hybrid vs full ranking, replicate sets, mean over the types: nP@5, nP@10, MRR, MAP |
| `figures/hybrid_rq2.pdf` | Hybrid vs full ranking, replicate sets, functional: nP@5, nP@10, MRR, MAP |

Notes:
- **nP@k instead of P@k:** nP@k = relevant methods in the top k / min(k, R). Many clone-type queries have fewer than 5
  or 10 clones, so plain P@k cannot reach 1 for them; for functional queries R is large and nP@k = P@k.
- **MAP for both RQs** (decision 2026-10-25): tables and figures report nP@5, nP@10, MRR and MAP for RQ1 and RQ2.
  MAP@R is not in the paper (reviewers did not ask for it) but stays in the raw results (`AP@R` in the evaluation
  files). Fusion W is tuned on MAP for both RQs.
- **Significance marks** on every column (pooled_compare_metrics.tsv): +/− against BM25, ↑/↓ kernel against
  fine-tuned CodeBERT, † fusion better than both components.
