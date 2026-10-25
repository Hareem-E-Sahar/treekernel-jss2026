# exp_v2: design

A separate experiment (decided 2026-10-20/21). The frozen experiment (git tag `replicates-10`) is not modified; shared
code (KeLP runner, BM25, CodeBERT encoder) is reused read-only, and only code that had to change is copied here.

## What changes compared with the frozen experiment

| | Frozen experiment | exp_v2 |
|---|---|---|
| Primary corpus | 14,679 true positives | **72,782 methods: true positives + 58,103 BCB false positives** (`data/trees_e5/D.tsv`) |
| False positives in scoring | not in the corpus | **non-relevant**, except exact copies of the query, which are **ignored** |
| Secondary setting | – | the main corpus (true positives only) |
| Tuning | on the main corpus | **on the primary corpus**, same procedure, queries and grid |
| Variant | A–D (RQ3) | **D only** |
| Queries | original sets + 10 replicates | the same 10 replicates (`data/replicates/`, copied unchanged) |
| Hybrid (BM25 top-k → tree kernel) | – | planned, all eligible queries, k = 100 and 200 (not tuned) |

**Why the false-positive corpus is primary:**
- Raw numbers on the main corpus overstate absolute performance. Every true positive contains its task's search keywords,
  and the main corpus has no lookalikes that share them.
- BCB's false positives are such lookalikes: they matched the keyword search but were judged not to implement the task.
- Absolute values still describe BigCloneBench under this setting, not real codebases.

**Exact copies ignored** (`prep/fp_copies.py` → `data/fp_copies.tsv`):
- A false positive whose source is identical to the query's after removing whitespace is skipped in that query's ranking.
- These are 367 pairs covering 145 true positives. BCB judged them false positive for some functionality while an
  identical method is a true positive. Counting them as wrong would penalise retrieving an exact clone.

## Tune once
- **Selection:** KeLP settings and fusion weights are selected once, on the 50 tuning queries in the primary setting.
- **Use:** they are then used unchanged for every RQ and both settings.
- **Analyses:** analyses by query property (e.g. method size or complexity) split the results; they do not re-tune.

Procedure (`scripts/run_tuning.sh`, `eval/tune.py`):
1. **Grid:** λ, μ ∈ {0.1, 0.2, 0.4, 0.6, 0.8, 1.0}, restricted to settings computable on the main corpus.
   - A setting that overflows in KeLP on the false positives is not computable. The overflowing methods are counted
     (`tuning/scan.tsv`, ids in `tuning/scan/`).
2. **Setting per kernel:** the highest mean over T1–MT3 of micro MAP. Ties keep the first setting in grid order.
3. **Fusion kernels:** the best kernel by that objective is fused for RQ1, and the best by functional MAP for RQ2. This
   is the rule the frozen experiment followed implicitly (PTK for RQ1, STK for RQ2), now written down.
   - **RQ2 objective:** MAP since 2026-10-25 (MAP@R before; same W, no run changed). Under MAP@R the rule picked SSTK
     (0.1728 vs 0.1722) and STK was used by decision; under MAP the rule picks STK (0.2272 vs SSTK 0.2271).
4. **Fusion weight:** W ∈ {0, 0.1, …, 1} for the weighted sum, by the same objective; ties go to the larger W. RRF has no
   parameter.

## Code in exp_v2 (copies of frozen code, changed only as stated)
- **`eval/evaluate.py`:** memory-maps the score matrix, adds `--ignore`, and adds normalised precision
  nP@k = hits in the top k / min(k, R) for k = 5, 10 (2026-10-21; tie-aware like P@k, computed from it).
  Before nP@k was added, its output without `--ignore` was byte-identical to `eval/evaluate.py` (checked on
  `results/e5/D/PTK_l0.4_m0.6`); the addition leaves every other column unchanged (checked on the PTK tuning run).
- **`eval/fusion.py`:** fuses in blocks of query rows. Its output is byte-identical to `eval/fusion.py` (wsum and RRF,
  checked).
- **`eval/replicates.py`:** reads the fusion runs from the selection, not from hard-coded names.
- **New:** `eval/tune.py`, `prep/fp_copies.py`, `scripts/run_tuning.sh`, `scripts/run_replicates.sh`.

## Size and complexity (decided 2026-10-22)
- **Groups of the query**, fixed before any result: small LOC ≤ 6, large LOC ≥ 10 (LOC = physical lines of the method,
  as in the user's earlier study; 7–9 in neither); low McCabe ≤ 10, high McCabe > 10 (Checkstyle 10.21.1
  CyclomaticComplexity with defaults; one method Checkstyle cannot parse, 16226644, is in neither complexity group).
- **Correlation:** LOC and McCabe have Spearman 0.76 and no small method has McCabe > 10, so complexity is also compared
  within large methods (low_large vs high_large: the same sampled queries restricted to LOC ≥ 10).
- **Sampling:** per seed (the 10 replicate seeds), group and set, 100 queries at random from the group's pool, or the
  whole pool when it has ≤ 100 (small T2 53, small VST3 12, high T2 57: identical in every seed). Same pools as the
  replicates otherwise. Candidates are not restricted by group.
- **Methods:** three kernels, BM25, CodeBERT zero-shot and fine-tuned; no fusion (user, 2026-10-22). No re-tuning.
- **Analysis:** mean ± SD over seeds per group; the interaction (A − B on one group minus on the other) with a
  functionality bootstrap that resamples jointly across both groups.
- **Compute:** only the 4,712 queries without a row in the replicate runs are scored; `eval/merge_runs.py` assembles
  one run per method (rows copied unchanged; checked byte-identical to a direct run).

## Hybrid (run 2026-10-23)
- **Pipeline:** BM25 top k (same query and index as the BM25 baseline; k = 100 and 200, not tuned), re-ranked by a
  tree kernel (STK, SSTK, PTK at the tuned settings). Below rank k the BM25 order is kept, so MAP and MAP@R are defined
  over the full ranking; the hybrid differs from BM25 only inside the top k.
- **Queries:** every eligible query (`data/full`, `prep/full_queries.py`): T1 3,746, T2 998, VST3 1,991, ST3 4,652,
  MT3 7,722, functional 14,587 (same pools as the replicates). Corpus with false positives; exact copies ignored.
- **Baselines on the same queries:** BM25 and CodeBERT (zero-shot, fine-tuned) full runs. Full-ranking tree kernels
  exist only for the replicate queries, so hybrid vs full kernel is compared on the 10 replicate sets.
- **Second stage:** `kernels/src/treekernel/HybridRerank.java` (compiled to `kernels/classes`, separate from the
  shared runner) scores only the given pairs with RetrievalRunner's scorer; values checked identical to full runs
  (250/250 pairs for PTK and STK). It records each query's summed kernel time (cost, RQ5).
- **Top-k at the cut:** ties at rank k are broken by Elasticsearch's internal document order.
