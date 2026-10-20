# Grid search on variant B

KeLP as is, 50 tuning queries (10 per clone type), reduced corpus of 14,679 methods (`data/trees_main/B.tsv`). Objective: MAP per clone type, averaged over T1–MT3 (micro).
Common grid (decided 2026-10-17): λ, μ ∈ {0.1, 0.2, 0.4, 0.6, 0.8, 1.0}. Run: `scripts/run_grid.sh B 14` (log: `run.log`); tables: `eval/grid_tables.py B` → `tables_AP.md` (`tables_AP@R.md` for MAP@R).
Compute time: about 31 min (02:00–02:31, 2026-10-17).
n/c (N) = not computable with KeLP as is; N methods overflow.

**STK**

| λ | 0.1 | 0.2 | 0.4 | 0.6 | 0.8 | 1.0 |
|---|---|---|---|---|---|---|
| AP | 0.863 | 0.863 | 0.864 | 0.868 | 0.875 | **0.900** |

**SSTK**

| λ | 0.1 | 0.2 | 0.4 | 0.6 | 0.8 | 1.0 |
|---|---|---|---|---|---|---|
| AP | **0.906** | 0.896 | 0.767 | n/c (676) | n/c (2,065) | n/c (3,475) |

**PTK** (rows λ, columns μ)

| λ \ μ | 0.1 | 0.2 | 0.4 | 0.6 | 0.8 | 1.0 |
|---|---|---|---|---|---|---|
| **0.1** | 0.905 | 0.910 | 0.915 | 0.919 | 0.917 | 0.895 |
| **0.2** | 0.905 | 0.910 | 0.915 | 0.920 | 0.926 | n/c (6) |
| **0.4** | 0.905 | 0.910 | 0.916 | **0.938** | n/c (111) | n/c (950) |
| **0.6** | 0.905 | 0.910 | 0.927 | n/c (129) | n/c (1,232) | n/c (2,653) |
| **0.8** | 0.909 | 0.913 | n/c (10) | n/c (946) | n/c (2,709) | n/c (4,818) |
| **1.0** | 0.905 | 0.913 | n/c (280) | n/c (2,076) | n/c (4,542) | n/c (7,033) |

**Best setting per kernel**

| Kernel | Setting | AP |
|---|---|---|
| STK | λ = 1.0 | 0.900 |
| SSTK | λ = 0.1 | 0.906 |
| PTK | λ = 0.4, μ = 0.6 | 0.938 |

AP@R picks the same setting for every kernel.

## Reading

- **STK** is flat up to λ = 0.8 (0.863–0.875) and best at **λ = 1.0 (0.900), the upper edge of the grid** (no decay). Values above 1 are not conventional and were not tried.
- **SSTK** is best at λ = 0.1 (0.906), 0.767 at the default 0.4; λ ≥ 0.6 overflows.
- **PTK** is best at (0.4, 0.6), 0.938, on the overflow boundary. Overflow starts earlier than on C/D ((0.2, 1.0) already overflows) because the trees are larger.
- T1, T2 and VST3 are at or near 1.0 for every selected setting; the tuning signal comes from ST3 and MT3.
