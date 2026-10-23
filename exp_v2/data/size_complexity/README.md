# Query sets for the size and complexity analysis

Drawn by `exp_v2/prep/sample_size_complexity.py`; groups, pools and streams are described there.

| Group | T1 | T2 | VST3 | ST3 | MT3 | functional |
|---|---|---|---|---|---|---|
| small | 461 | 53 (all) | 12 (all) | 507 | 567 | 835 |
| large | 2,955 | 736 | 1,854 | 3,551 | 6,234 | 12,636 |
| low | 3,254 | 941 | 1,706 | 4,316 | 7,414 | 12,708 |
| high | 492 | 57 (all) | 285 | 336 | 308 | 1,878 |

Pool sizes; per seed min(pool, 100) queries; (all) = whole pool, identical in every seed. Union of all queries: 7,794.
