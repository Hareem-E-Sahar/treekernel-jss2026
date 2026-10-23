# RQ2 tuning check: tuning the kernels for MAP@R instead of the RQ1 objective

Question (2026-10-20): every kernel was tuned for the RQ1 objective (mean over T1–MT3 of micro MAP, on the 50 tuning
queries) and those settings are reused for RQ2. Would tuning for RQ2's MAP@R pick different settings?

Method: every existing grid run (`results/grid/<V>/`, 125 settings over variants A–D, 50 tuning queries × 14,679 methods)
re-evaluated with functional relevance (relevant = every method sharing a functionality with the query, candidates = the
whole corpus), as in RQ2. No new kernel runs; `results/grid/` is untouched.
Run: `scripts/run_rq2_tuning_check.sh` (26 s), then `.venv/bin/python eval/rq2_tuning_check.py` → `selection.tsv`.

| Variant | Kernel | Settings | Chosen by RQ1 objective | its MAP@R | Chosen by MAP@R | its MAP@R | Δ MAP@R | its RQ1 mean |
|---|---|---|---|---|---|---|---|---|
| A | STK | 6 | STK_l1.0 | 0.237 | STK_l1.0 | 0.237 | +0.000 | 0.893 |
| A | SSTK | 3 | SSTK_l0.1 | 0.239 | SSTK_l0.2 | 0.246 | +0.007 | 0.883 |
| A | PTK | 21 | PTK_l0.6_m0.4 | 0.255 | PTK_l0.6_m0.4 | 0.255 | +0.000 | 0.931 |
| B | STK | 6 | STK_l1.0 | 0.332 | STK_l1.0 | 0.332 | +0.000 | 0.900 |
| B | SSTK | 3 | SSTK_l0.1 | 0.332 | SSTK_l0.2 | 0.341 | +0.009 | 0.896 |
| B | PTK | 22 | PTK_l0.4_m0.6 | 0.266 | PTK_l0.4_m0.6 | 0.266 | +0.000 | 0.938 |
| C | STK | 6 | STK_l0.8 | 0.176 | STK_l0.8 | 0.176 | +0.000 | 0.882 |
| C | SSTK | 3 | SSTK_l0.1 | 0.175 | SSTK_l0.1 | 0.175 | +0.000 | 0.884 |
| C | PTK | 23 | PTK_l0.4_m0.6 | 0.232 | PTK_l0.4_m0.6 | 0.232 | +0.000 | 0.932 |
| D | STK | 6 | STK_l0.8 | 0.286 | STK_l0.8 | 0.286 | +0.000 | 0.905 |
| D | SSTK | 3 | SSTK_l0.1 | 0.280 | SSTK_l0.2 | 0.281 | +0.001 | 0.897 |
| D | PTK | 23 | PTK_l0.4_m0.6 | 0.270 | PTK_l0.4_m0.6 | 0.270 | +0.000 | 0.940 |

Settings = computable grid settings (non-computable ones overflow in KeLP and are excluded, as in tuning).
MAP@R and RQ1 mean are on the 50 tuning queries.

## Finding
- 9 of 12 variant × kernel combinations pick the **same setting** under either objective.
- The other 3 are SSTK, where MAP@R prefers λ = 0.2 over 0.1, gaining 0.001–0.009 MAP@R on the tuning queries.
- The kernels' RQ2 gap to BM25 and fine-tuned CodeBERT is about 0.3 MAP@R, so the RQ2 conclusions do not depend on the
  tuning objective. No re-run on the evaluation queries is needed.

## Caveats
- The 50 tuning queries were drawn per clone type (methods with a clone of that type) and cover 18 functionalities; the
  RQ2 evaluation queries are random true positives. They are the only held-out-safe queries available for tuning.
