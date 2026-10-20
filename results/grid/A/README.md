# Grid search on variant A

KeLP as is, 50 tuning queries (10 per clone type), reduced corpus of 14,679 methods (`data/trees_main/A.tsv`). Objective: MAP per clone type, averaged over T1–MT3 (micro).
Common grid (decided 2026-10-17): λ, μ ∈ {0.1, 0.2, 0.4, 0.6, 0.8, 1.0}. Run: `scripts/run_grid.sh A 14` (log: `run.log`); tables: `eval/grid_tables.py A` → `tables_AP.md` (`tables_AP@R.md` for MAP@R).
Compute time: about 79 min (02:31–03:50, 2026-10-17).
n/c (N) = not computable with KeLP as is; N methods overflow.

**STK**

| λ | 0.1 | 0.2 | 0.4 | 0.6 | 0.8 | 1.0 |
|---|---|---|---|---|---|---|
| AP | 0.863 | 0.864 | 0.866 | 0.870 | 0.878 | **0.893** |

**SSTK**

| λ | 0.1 | 0.2 | 0.4 | 0.6 | 0.8 | 1.0 |
|---|---|---|---|---|---|---|
| AP | **0.896** | 0.883 | 0.735 | n/c (822) | n/c (2,485) | n/c (4,343) |

**PTK** (rows λ, columns μ)

| λ \ μ | 0.1 | 0.2 | 0.4 | 0.6 | 0.8 | 1.0 |
|---|---|---|---|---|---|---|
| **0.1** | 0.889 | 0.891 | 0.899 | 0.908 | 0.911 | 0.894 |
| **0.2** | 0.889 | 0.891 | 0.899 | 0.916 | 0.902 | n/c (23) |
| **0.4** | 0.889 | 0.892 | 0.918 | 0.901 | n/c (423) | n/c (1,747) |
| **0.6** | 0.889 | 0.892 | **0.931** | n/c (536) | n/c (2,503) | n/c (4,913) |
| **0.8** | 0.890 | 0.901 | n/c (199) | n/c (2,484) | n/c (5,816) | n/c (8,589) |
| **1.0** | 0.887 | n/c (5) | n/c (1,359) | n/c (5,401) | n/c (9,039) | n/c (11,248) |

**Best setting per kernel**

| Kernel | Setting | AP |
|---|---|---|
| STK | λ = 1.0 | 0.893 |
| SSTK | λ = 0.1 | 0.896 |
| PTK | λ = 0.6, μ = 0.4 | 0.931 |

AP@R picks the same setting for every kernel.

## Reading

- **STK** is flat up to λ = 0.8 (0.863–0.878) and best at **λ = 1.0 (0.893), the upper edge of the grid**, as on B.
- **SSTK** is best at λ = 0.1 (0.896), 0.735 at the default 0.4; λ ≥ 0.6 overflows.
- **PTK** is best at **(0.6, 0.4)**, 0.931, on the overflow boundary ((0.6, 0.6) and (0.8, 0.4) overflow). A is the only variant whose PTK optimum is not (0.4, 0.6); there (0.4, 0.6) gives 0.901, below (0.4, 0.4) 0.918, so the surface is not smooth near the boundary. A has the largest trees and the most non-computable cells (18 of 48 settings).
- T1, T2 and VST3 are at or near 1.0 for every selected setting; the tuning signal comes from ST3 and MT3.
