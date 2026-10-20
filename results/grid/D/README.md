# Grid search on variant D

KeLP as is, 50 tuning queries (10 per clone type), reduced corpus of 14,679 methods (`data/trees_main/D.tsv`). Objective: MAP per clone type, averaged over T1–MT3 (micro).
Common grid (decided 2026-10-17): λ, μ ∈ {0.1, 0.2, 0.4, 0.6, 0.8, 1.0}. Run: `scripts/run_grid.sh D 14`; tables: `eval/grid_tables.py D` → `tables_AP.md` (`tables_AP@R.md` for MAP@R).
Compute time: about 5 min for the first 17 settings (2026-10-16; the wall-clock 34 min included a 29-min laptop suspend) and 13 min for the extension (2026-10-17).
The extra small SSTK values tried earlier (λ = 0.02, 0.05, 0.15, 0.3; MAP 0.915, 0.915, 0.906, 0.853) are outside the grid and kept in `extra_sstk_small_lambda/`.

n/c (N) = not computable with KeLP as is; N methods overflow.

**STK**

| λ | 0.1 | 0.2 | 0.4 | 0.6 | 0.8 | 1.0 |
|---|---|---|---|---|---|---|
| AP | 0.889 | 0.890 | 0.895 | 0.903 | **0.905** | 0.902 |

**SSTK**

| λ | 0.1 | 0.2 | 0.4 | 0.6 | 0.8 | 1.0 |
|---|---|---|---|---|---|---|
| AP | **0.914** | 0.897 | 0.756 | n/c (233) | n/c (833) | n/c (1,718) |

**PTK** (rows λ, columns μ)

| λ \ μ | 0.1 | 0.2 | 0.4 | 0.6 | 0.8 | 1.0 |
|---|---|---|---|---|---|---|
| **0.1** | 0.924 | 0.925 | 0.929 | 0.924 | 0.918 | 0.895 |
| **0.2** | 0.924 | 0.925 | 0.930 | 0.936 | 0.910 | 0.895 |
| **0.4** | 0.924 | 0.926 | 0.931 | **0.940** | n/c (27) | n/c (490) |
| **0.6** | 0.924 | 0.926 | 0.937 | n/c (36) | n/c (676) | n/c (1,886) |
| **0.8** | 0.924 | 0.928 | n/c (1) | n/c (537) | n/c (1,962) | n/c (3,502) |
| **1.0** | 0.914 | 0.926 | n/c (189) | n/c (1,474) | n/c (3,345) | n/c (5,309) |

**Best setting per kernel**

| Kernel | Setting | AP |
|---|---|---|
| STK | λ = 0.8 | 0.905 |
| SSTK | λ = 0.1 | 0.914 |
| PTK | λ = 0.4, μ = 0.6 | 0.940 |

AP@R, MRR and Recall@10 agree on the STK and SSTK choices; AP@R also picks PTK (0.4, 0.6).

## Reading

- **SSTK is very sensitive, in one direction:** 0.914 at λ = 0.1 → 0.756 at KeLP's default 0.4. The settings that overflow (λ ≥ 0.6) lie beyond a decline that is already steep, consistent with the "diagonal problem" of large decay values.
- **PTK is flat over most of its grid** (0.895–0.940). Its best setting, (λ 0.4, μ 0.6), lies **on the overflow boundary**: (0.4, 0.8) and (0.6, 0.6) are not computable. It beats the default (0.4, 0.4) by +0.009 (paired bootstrap CI +0.001 to +0.020) and its computable neighbours by +0.003 to +0.004. *Caveat for the paper:* we cannot tell whether settings beyond the boundary would be better still. The gain from moving into larger μ is small and comes from MT3.
- **STK changes little** (0.889–0.905); mild preference for large λ.
- **T1, T2 and VST3 are near 1.0 for every setting**; the tuning signal comes from ST3 and above all MT3 (10 queries each).
