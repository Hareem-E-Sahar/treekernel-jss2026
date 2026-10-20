# Paper figures and tables

`make_assets.py` regenerates everything from the evaluated runs (`.venv/bin/python paper/make_assets.py`, ~10 s), except the replicate box plots, which are drawn in R with ggplot2 (packages ggplot2 ≥ 4.0, dplyr, tidyr): `Rscript paper/rq1_boxplot.R` (`figures/rq1_map_by_type.pdf`) and `Rscript paper/rq4_boxplots.R` (`figures/rq4_*_replicates.pdf`). Replicate inputs: `eval/replicates.py` and `eval/replicates_complementarity.py`.
`preview.tex` includes all of them in a two-column article to check the layout. Tables use `booktabs`; wide tables are `table*`.

| RQ | Table | Figure |
|---|---|---|
| RQ1 syntactic | `tables/rq1_map.tex` (original query sets), `tables/rq1_rq2_replicates.tex` (10 replicate sets, RQ1 + RQ2 MAP@R, mean ± SD) | `figures/rq1_map_by_type.pdf` |
| RQ2 functional | `tables/rq2_functional.tex` | `figures/rq1_rq2_by_category.pdf` (RQ1 and RQ2 by category) |
| RQ3 representation | `tables/rq3_variants.tex` | `figures/rq3_variant_kernel.pdf` |
| RQ4 complementarity | `tables/rq4_fusion.tex` (original query sets), `tables/rq4_fusion_replicates.tex` (10 replicate sets, mean ± SD) | `figures/rq4_complementarity_fusion.pdf` (two-column); replicates: `figures/rq4_fusion_replicates.pdf`, `figures/rq4_complementarity_replicates.pdf` (box plots, R) |
| Robustness (E5) | `tables/e5_false_positives.tex` | – |
| RQ5 cost | `tables/rq5_cost.tex` | `figures/rq5_time_per_query.pdf`, `figures/rq5_time_e5.pdf` |

Suggested figure captions (figures carry no caption of their own):
- rq1_map_by_type: MAP per clone type, variant D at tuned settings vs BM25 and CodeBERT, over the 10 replicate query sets (results/replicates; 100 queries per type each); box = IQR and median, whiskers = min–max. T1 is 1.000 for every method in every replicate.
- rq1_rq2_by_category: Results by functionality category (pattern: found in BigCloneBench by code pattern; name: by API names). Only 6 functional queries are from pattern functionalities.
- rq3_variant_kernel: Tree variant × kernel at tuned settings; left RQ1 mean MAP over the five clone types, right RQ2 MAP@R. Best in bold.
- rq4_fusion_replicates: MAP (ST3, MT3, mean of the five types) of PTK, BM25 or fine-tuned CodeBERT, and their weighted-sum (tuned W) and RRF fusions over the 10 replicate query sets; box = IQR and median, whiskers = min–max.
- rq4_complementarity_replicates: share of relevant items ranked within the top R by both, PTK only, the other only, or neither, over the 10 replicate query sets (ST3, MT3, functional).
- rq4_complementarity_fusion: (a) Relevant items ranked within the top R by both, one, or neither of PTK (variant D) and BM25. (b) Weighted-sum fusion on the 50 tuning queries as a function of W.
- rq5_time_per_query: Time to score one query against the 14,679-method corpus, one thread, log scale.
- rq5_time_e5: Time per query on the main corpus (14,679 methods, hatched) and on the corpus enlarged with 58,103 BigCloneBench false positives (72,782 methods, solid), variant D at tuned settings, one thread, mean over the same 20 queries, log scale; right column = enlarged ÷ main. A corpus 5× larger costs the tree kernels about 4.5× and BM25 (returning all scores) 6.8×; CodeBERT barely changes because encoding the query dominates and the cosine against stored embeddings is cheap (encoding the corpus is the one-off cost).
