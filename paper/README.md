# Paper figures and tables

`make_assets.py` regenerates everything from the evaluated runs (`.venv/bin/python paper/make_assets.py`, ~10 s).
`preview.tex` includes all of them in a two-column article to check the layout. Tables use `booktabs`; wide tables are `table*`.

| RQ | Table | Figure |
|---|---|---|
| RQ1 syntactic | `tables/rq1_map.tex` | `figures/rq1_map_by_type.pdf` |
| RQ2 functional | `tables/rq2_functional.tex` | `figures/rq1_rq2_by_category.pdf` (RQ1 and RQ2 by category) |
| RQ3 representation | `tables/rq3_variants.tex` | `figures/rq3_variant_kernel.pdf` |
| RQ4 complementarity | `tables/rq4_fusion.tex` | `figures/rq4_complementarity_fusion.pdf` (two-column) |
| Robustness (E5) | `tables/e5_false_positives.tex` | – |
| RQ5 cost | `tables/rq5_cost.tex` | `figures/rq5_time_per_query.pdf` |

Suggested figure captions (figures carry no caption of their own):
- rq1_map_by_type: MAP per clone type, variant D at tuned settings vs BM25; bars = 95% bootstrap CIs over the 100 queries per type.
- rq1_rq2_by_category: Results by functionality category (pattern: found in BigCloneBench by code pattern; name: by API names). Only 6 functional queries are from pattern functionalities.
- rq3_variant_kernel: Tree variant × kernel at tuned settings; left RQ1 mean MAP over the five clone types, right RQ2 MAP@R. Best in bold.
- rq4_complementarity_fusion: (a) Relevant items ranked within the top R by both, one, or neither of PTK (variant D) and BM25. (b) Weighted-sum fusion on the 50 tuning queries as a function of W.
- rq5_time_per_query: Time to score one query against the 14,679-method corpus, one thread, log scale.
