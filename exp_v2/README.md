# exp_v2: false positives in the corpus, variant D, tuned once

Design and rationale: `DESIGN.md`. Order of steps:

1. `prep/fp_copies.py` → `data/fp_copies.tsv` (false positives that are exact copies of a true positive).
2. `scripts/run_tuning.sh` → `tuning/` (grid on the 50 tuning queries, then `eval/tune.py` → `tuning/selected.json`).
3. `scripts/run_replicates.sh` → `results/fp/` (10 replicates at the selected settings), then
   `.venv/bin/python exp_v2/eval/replicates.py fp`.
4. `scripts/run_replicates_main.sh` → `results/main/` (secondary setting: main corpus, same settings and weights;
   frozen runs at an identical setting are linked, not recomputed), then `.venv/bin/python exp_v2/eval/replicates.py main`.
5. Size and complexity: `prep/size_complexity.py` → `data/size_complexity.tsv` (LOC, Checkstyle McCabe);
   `prep/sample_size_complexity.py` → `data/size_complexity/` (stratified query sets); `scripts/run_size_complexity.sh`
   → `results/size_complexity/`; then `.venv/bin/python exp_v2/eval/size_complexity.py`.
6. Hybrid: `prep/full_queries.py` → `data/full/`; `scripts/run_hybrid.sh` → `results/hybrid/` (BM25 top k → tree kernel,
   k = 100, 200; all eligible queries).

## Tuning result (2026-10-21, corpus with false positives)

| Kernel | Selected | RQ1 objective (tuning queries) | Frozen experiment (main corpus) |
|---|---|---|---|
| STK | **λ 1.0** (upper edge of the grid) | 0.868 (λ 0.8: 0.852) | λ 0.8 |
| SSTK | λ 0.1 | 0.889 | λ 0.1 |
| PTK | λ 0.4, μ 0.6 | 0.916 | λ 0.4, μ 0.6 |

- **Not computable on the false positives** (in addition to the main corpus's): PTK (0.2, 1.0) with 41 methods,
  (1.0, 0.1) with 13 and (1.0, 0.2) with 63.
- **Fusion kernels:**
  - RQ1: PTK.
  - RQ2: **STK**, by decision (2026-10-21). The rule picks SSTK, whose MAP@R of 0.1728 narrowly beats STK's 0.1722;
    the difference is within noise, and STK is the kernel the frozen experiment fused. `selected.json` records both.
- **Fusion W:**

  | Fusion | W | Frozen experiment |
  |---|---|---|
  | PTK + BM25 | **0.9** | 0.8 |
  | PTK + CodeBERT ft | 0.6 | 0.6 |
  | STK + BM25 (RQ2) | 0.0 | 0.0 |
  | STK + CodeBERT ft (RQ2) | 0.2 | 0.1 |

- **On the tuning queries:** BM25 RQ1 0.819, MAP@R 0.349; CodeBERT ft RQ1 0.814, MAP@R 0.377.
