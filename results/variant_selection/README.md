# Variant selection (2026-10-16)

Every tree variant × kernel at KeLP's default setting (λ = μ = 0.4), KeLP as is, on the 50 tuning queries (10 per clone type), against the reduced corpus of 14,679 methods (`data/trees_main/`). Objective: MAP per clone type (RQ1 ground truth), averaged over the five types. Decision rule (PLAN.md §5.1): best variant; on a near-tie prefer C.

Reproduce:
```bash
scripts/run_variant_selection.sh 14          # 12 runs, about 6 min in total
for d in results/variant_selection/?_*/; do .venv/bin/python eval/evaluate.py $d --syntactic data/pools/tuning.tsv; done
.venv/bin/python eval/compare_runs.py results/variant_selection/comparison_AP.md A_STK=results/variant_selection/A_STK ...
```
Per-run outputs: `<V>_<K>/` (scores), `<V>_<K>/eval/` (per-query metrics and summary). Comparison table: `comparison_AP.md`.

Queries per type: T1 10, T2 10, VST3 10, ST3 10, MT3 10. 95% CI: bootstrap over queries within type (2000 resamples).

| Run | T1 | T2 | VST3 | ST3 | MT3 | **mean** | 95% CI |
|---|---|---|---|---|---|---|---|
| A_STK | 1.000 | 0.936 | 0.995 | 0.927 | 0.474 | **0.866** | 0.801–0.927 |
| B_STK | 1.000 | 0.936 | 0.999 | 0.864 | 0.522 | **0.864** | 0.795–0.931 |
| C_STK | 0.958 | 0.897 | 0.933 | 0.803 | 0.406 | **0.800** | 0.727–0.874 |
| D_STK | 1.000 | 1.000 | 1.000 | 0.989 | 0.487 | **0.895** | 0.850–0.944 |
| A_SSTK | 1.000 | 1.000 | 0.900 | 0.434 | 0.339 | **0.735** | 0.654–0.809 |
| B_SSTK | 1.000 | 1.000 | 0.900 | 0.584 | 0.354 | **0.767** | 0.681–0.846 |
| C_SSTK | 1.000 | 1.000 | 0.900 | 0.468 | 0.323 | **0.738** | 0.656–0.815 |
| D_SSTK | 1.000 | 1.000 | 0.900 | 0.496 | 0.385 | **0.756** | 0.673–0.833 |
| A_PTK | 1.000 | 1.000 | 1.000 | 0.985 | 0.605 | **0.918** | 0.863–0.969 |
| B_PTK | 1.000 | 1.000 | 1.000 | 0.965 | 0.615 | **0.916** | 0.861–0.967 |
| C_PTK | 1.000 | 1.000 | 1.000 | 0.980 | 0.546 | **0.905** | 0.856–0.953 |
| D_PTK | 1.000 | 1.000 | 1.000 | 0.998 | 0.657 | **0.931** | 0.878–0.977 |

## Best variant per kernel vs the others (paired)

| Kernel | Best | Other | Difference | 95% CI | Share of resamples where best wins |
|---|---|---|---|---|---|
| STK | D_STK | A_STK | +0.029 | -0.006 to +0.069 | 94% |
| STK | D_STK | B_STK | +0.031 | -0.025 to +0.088 | 86% |
| STK | D_STK | C_STK | +0.095 | +0.040 to +0.154 | 100% |
| SSTK | B_SSTK | A_SSTK | +0.033 | -0.001 to +0.076 | 97% |
| SSTK | B_SSTK | C_SSTK | +0.029 | -0.029 to +0.092 | 85% |
| SSTK | B_SSTK | D_SSTK | +0.011 | -0.026 to +0.058 | 69% |
| PTK | D_PTK | A_PTK | +0.013 | +0.002 to +0.030 | 100% |
| PTK | D_PTK | B_PTK | +0.015 | -0.003 to +0.040 | 90% |
| PTK | D_PTK | C_PTK | +0.026 | +0.005 to +0.056 | 100% |
