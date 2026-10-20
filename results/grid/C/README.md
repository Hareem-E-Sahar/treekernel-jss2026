# Grid search on variant C

KeLP as is, 50 tuning queries (10 per clone type), reduced corpus of 14,679 methods (`data/trees_main/C.tsv`). Objective: MAP per clone type, averaged over T1–MT3 (micro).
Common grid (decided 2026-10-17): λ, μ ∈ {0.1, 0.2, 0.4, 0.6, 0.8, 1.0}. Run: `scripts/run_grid.sh C 14` (log: `run.log`); tables: `eval/grid_tables.py C` → `tables_AP.md` (`tables_AP@R.md` for MAP@R).
Compute time: about 24 min (01:36–02:00, 2026-10-17).
n/c (N) = not computable with KeLP as is; N methods overflow.

**STK**

| λ | 0.1 | 0.2 | 0.4 | 0.6 | 0.8 | 1.0 |
|---|---|---|---|---|---|---|
| AP | 0.689 | 0.724 | 0.800 | 0.877 | **0.882** | 0.880 |

**SSTK**

| λ | 0.1 | 0.2 | 0.4 | 0.6 | 0.8 | 1.0 |
|---|---|---|---|---|---|---|
| AP | **0.884** | 0.866 | 0.738 | n/c (110) | n/c (515) | n/c (1,113) |

**PTK** (rows λ, columns μ)

| λ \ μ | 0.1 | 0.2 | 0.4 | 0.6 | 0.8 | 1.0 |
|---|---|---|---|---|---|---|
| **0.1** | 0.888 | 0.891 | 0.899 | 0.901 | 0.883 | 0.884 |
| **0.2** | 0.888 | 0.891 | 0.899 | 0.903 | 0.887 | 0.883 |
| **0.4** | 0.888 | 0.891 | 0.905 | **0.932** | n/c (25) | n/c (470) |
| **0.6** | 0.888 | 0.893 | 0.930 | n/c (40) | n/c (661) | n/c (1,778) |
| **0.8** | 0.889 | 0.901 | n/c (1) | n/c (577) | n/c (1,896) | n/c (3,263) |
| **1.0** | 0.877 | 0.915 | n/c (211) | n/c (1,479) | n/c (3,189) | n/c (4,954) |

**Best setting per kernel**

| Kernel | Setting | AP |
|---|---|---|
| STK | λ = 0.8 | 0.882 |
| SSTK | λ = 0.1 | 0.884 |
| PTK | λ = 0.4, μ = 0.6 | 0.932 |

AP@R picks the same setting for every kernel.

## Reading

- **STK and SSTK depend strongly on λ, in opposite directions.** STK rises from 0.689 at λ = 0.1 to 0.882 at λ = 0.8: on abstracted trees small shared fragments are uninformative (everything looks alike), so only large fragments separate methods. SSTK is again best at λ = 0.1 (0.884) and falls to 0.738 at the default 0.4; λ ≥ 0.6 overflows.
- **PTK** is best at (0.4, 0.6), 0.932, on the overflow boundary like D; the default (0.4, 0.4) gives 0.905.
- Tuning narrows the gap to D (STK 0.882 vs 0.905, was 0.800 vs 0.895 at defaults); see `../tuned_comparison/`.
- T1, T2 and VST3 are at or near 1.0 for every selected setting; the tuning signal comes from ST3 and MT3.
