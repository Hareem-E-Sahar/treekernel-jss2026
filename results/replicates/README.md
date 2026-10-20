# Replication over 10 query sets (variant D)

Decision 2026-10-20: repeat RQ1, RQ2 and RQ4 on 10 independently drawn query sets, using the seeds from the user's earlier
study (55, 1375, 2084, 2802, 3389, 3501, 6251, 8241, 8828, 9080). Variant D only; RQ3, E5 and RQ5 stay on the original sets.

## How it was run
- Query sets: `prep/sample_replicates.py` → `data/pools/replicates/seed<S>/` (see the README there).
  - 100 queries per clone type plus 100 functional queries per replicate.
  - Set k of replicate s is drawn with `random.Random(10·s + k)`.
  - Pools exclude the 50 tuning queries and the 42 methods whose functionalities span CodeBERT folds.
- Runs: `scripts/run_replicates.sh` → `runs/`. Each method is run once over the union of all replicate queries (4,260 distinct
  methods), and each replicate is then evaluated from those runs (`seed<S>/<method>/eval`).
  - All methods are deterministic, so this equals running each replicate separately.
  - Tuned settings and fusion weights W come from the tuning queries and are the same in every replicate.
- Aggregation:
  - `eval/replicates.py` → `per_replicate.tsv`, `tables.md`, `pooled_compare.tsv`
  - `eval/replicates_complementarity.py` → `complementarity.tsv`
- Paper assets:
  - tables `paper/tables/rq1_rq2_replicates.tex` and `paper/tables/rq4_fusion_replicates.tex` (from `paper/make_assets.py`);
  - box plots `paper/figures/rq1_map_by_type.pdf` (`paper/rq1_boxplot.R`) and `paper/figures/rq4_*_replicates.pdf`
    (`paper/rq4_boxplots.R`).

## Two views of the results
1. **Across replicates:** mean ± SD (min–max) over the 10 replicates. Per comparison, the number of replicates in which A
   is significantly better / not different / worse (paired query bootstrap within the replicate).
2. **Pooled:** all distinct replicate queries per set. Paired bootstrap resampling functionalities (2,000 resamples, seed
   20261020), because queries of one functionality are not independent. This test gives the significance marks in the
   paper tables.

## Findings
- **RQ1:**
  - PTK leads on the mean (0.935 ± 0.007) and is significantly better than BM25 (9/10 replicates; pooled +0.036*).
  - PTK and fine-tuned CodeBERT tie (pooled +0.008, n.s.).
  - PTK is better on ST3 pooled (+0.041*), but only in 3/10 replicates.
  - On MT3 they tie, with CodeBERT ahead (−0.016, n.s.).
- **RQ2:** every kernel is significantly worse than BM25 and fine-tuned CodeBERT in 10/10 replicates.
  - The MAP@R values are higher than on the original functional set for every method (BM25 0.555 ± 0.021 vs 0.477). That
    set happened to over-sample the two hardest functionalities (4 and 35).
- **RQ4 fusion:**
  - The weighted sum of PTK with BM25 or with fine-tuned CodeBERT is significantly better than both components on ST3, MT3
    and the mean, pooled. Per replicate it beats both on MT3 and the mean in 10/10 replicates; on ST3 it beats PTK in 7/10
    (with BM25) and 8/10 (with CodeBERT). Mean 0.968 and 0.970; MT3 +0.14 to +0.19.
  - RRF of PTK + fine-tuned CodeBERT is also better than both. RRF of PTK + BM25 is better than both only on the mean.
  - RQ2: STK + BM25 has W = 0, so it equals BM25. STK + fine-tuned CodeBERT (W = 0.1) equals CodeBERT (+0.002, n.s.).
- **RQ4 complementarity** (share of relevant items in the top R, mean ± SD over replicates):

  | | Both | PTK only | Other only | Neither |
  |---|---|---|---|---|
  | vs BM25, ST3 | 84% ± 4% | 12% ± 2% | 3% ± 2% | 1% ± 1% |
  | vs BM25, MT3 | 52% ± 5% | 22% ± 4% | 12% ± 2% | 14% ± 4% |
  | vs BM25, functional | 24% ± 1% | 8% ± 0% | 38% ± 1% | 30% ± 2% |
  | vs CodeBERT ft, ST3 | 90% ± 3% | 6% ± 2% | 3% ± 2% | 1% ± 1% |
  | vs CodeBERT ft, MT3 | 63% ± 6% | 11% ± 2% | 15% ± 3% | 11% ± 4% |
  | vs CodeBERT ft, functional | 24% ± 1% | 8% ± 1% | 39% ± 2% | 29% ± 2% |
