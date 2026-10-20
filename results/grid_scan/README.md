# Which kernel settings KeLP can compute without overflow (2026-10-15)

**Decision 2026-10-15: KeLP is used as is** (32-bit float). Grid settings that produce non-finite values are removed from tuning.

**Method.** `kernels/.../GridFiniteScan.java` computes KeLP's self-similarity K(x, x) of all 14,780 methods for each setting and counts non-finite values (`Infinity`/`NaN`).
- If every self-similarity is finite, every cross-similarity is too, because by Cauchy–Schwarz K(a, b) ≤ √(K(a,a)·K(b,b)).
- So a setting is **usable for a variant iff it has 0 non-finite self-similarities on that variant**.

Files:
- `scan.tsv`: the planned grid, 19 settings × 4 variants.
- `scan_extra_sstk.tsv`: extra SSTK λ values below and between grid points.

Each row gives the count of non-finite values, the smallest affected tree, the largest finite value (float max ≈ 3.4·10³⁸), and the time.

## Result: non-finite self-similarities per setting

✓ = all finite (usable); a number = how many methods overflow.

**SSTK** (planned grid: 0.1, 0.2, 0.4, 0.6, 0.8, 1.0; extra: 0.02, 0.05, 0.15, 0.3):

| λ | A (raw) | B (pruned) | C (abstracted) | D (+API names) |
|---|---|---|---|---|
| 0.02 | ✓ | | | |
| 0.05 | 2 | ✓ | ✓ | ✓ |
| 0.1 | 3 | ✓ | ✓ | ✓ |
| 0.15 | | ✓ | ✓ | ✓ |
| 0.2 | 4 | 1 | ✓ | ✓ |
| 0.3 | | | 9 | 12 |
| 0.4 (KeLP default) | 100 | 91 | 39 | 50 |
| 0.6 | 923 | 774 | 207 | 330 |
| 0.8 | 2,586 | 2,163 | 612 | 930 |
| 1.0 | 4,444 | 3,573 | 1,210 | 1,815 |

**STK** (λ = 0.1, 0.4, 0.8, 1.0): ✓ on all four variants. The largest value is 8.9·10⁶, far below the float limit.

**PTK** (λ, μ ∈ {0.1, 0.4, 0.8}). Every variant gives the same picture:

| λ \ μ | 0.1 | 0.4 | 0.8 |
|---|---|---|---|
| **0.1** | ✓ | ✓ | ✓ |
| **0.4** | ✓ | ✓ | ✗ (102–517) |
| **0.8** | ✓ | ✗ (79–300) | ✗ (1,994–5,917) |

## Reading

- **STK:** the full planned grid is usable.
- **PTK:** 6 of the 9 planned settings are usable on every variant. The three with both λ and μ large are removed. KeLP's default (0.4, 0.4) is usable.
- **SSTK:** most of the planned grid is unusable, including KeLP's default λ = 0.4 on every variant.
  - C and D: λ ≤ 0.2 is usable.
  - B: λ ≤ 0.15.
  - A (raw): only λ = 0.02. Even λ = 0.05 overflows, on the 2 largest methods (3,838+ nodes).
  - SSTK counts every combination of fragments, so its values grow explosively with tree size. Only a strong decay λ keeps them within float range.

Scan time with KeLP as is: about 5–25 s per setting on B–D and 20–145 s on A.
