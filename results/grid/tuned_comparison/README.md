# Tuned variants compared (2026-10-17)

Each variant at its own best grid setting (`results/grid/<V>/README.md`), on the same 50 tuning queries.
Made with `eval/compare_runs.py comparison_AP.md D_STK=results/grid/D/STK_l0.8 ...` (paired bootstrap, 2000 resamples within clone type).

| Kernel | D | C | B | A |
|---|---|---|---|---|
| STK | **0.905** (λ 0.8) | 0.882 (λ 0.8) | 0.900 (λ 1.0) | 0.893 (λ 1.0) |
| SSTK | **0.914** (λ 0.1) | 0.884 (λ 0.1) | 0.906 (λ 0.1) | 0.896 (λ 0.1) |
| PTK | **0.940** (0.4, 0.6) | 0.932 (0.4, 0.6) | 0.938 (0.4, 0.6) | 0.931 (0.6, 0.4) |

- **D stays best for every kernel after tuning**, including SSTK (where B led at defaults). The choice of D is confirmed.
- **Tuning shrinks the gaps.** D vs C for STK: +0.095 at defaults (significant) → +0.023 tuned (CI −0.013 to +0.058, not significant). Only PTK keeps significant differences: D > C +0.008 (CI +0.001 to +0.019) and D > A +0.010 (+0.001 to +0.020).
- The lexical contribution of D (API names) over C is therefore small once λ is tuned: about +0.01 to +0.03 MAP, mostly on MT3 and ST3.
- All differences are on 10 queries per type; the evaluation queries (584) will give the real test.
