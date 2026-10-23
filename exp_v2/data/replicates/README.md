# Replicate query sets

Drawn by `prep/sample_replicates.py` (seeds 6251, 9080, 8241, 8828, 55, 1375, 2084, 2802, 3501, 3389: the user's seeds from the earlier study).
Each replicate: 100 queries per clone type and 100 functional queries, drawn independently; pools = main corpus minus the 50 tuning queries and the methods whose functionalities span CodeBERT folds. The original sets in `data/pools/` are not part of the replicates.

Pool sizes: T1 3,746, T2 998, VST3 1,991, ST3 4,652, MT3 7,722, functional 14,587.

| Seed | Set | Queries | Pattern-task queries | Tasks represented |
|---|---|---|---|---|
| 6251 | T1 | 100 | 8 | 23 |
| 6251 | T2 | 100 | 4 | 22 |
| 6251 | VST3 | 100 | 11 | 22 |
| 6251 | ST3 | 100 | 19 | 21 |
| 6251 | MT3 | 100 | 11 | 24 |
| 6251 | functional | 100 | 11 | 24 |
| 9080 | T1 | 100 | 10 | 22 |
| 9080 | T2 | 100 | 9 | 21 |
| 9080 | VST3 | 100 | 12 | 23 |
| 9080 | ST3 | 100 | 21 | 25 |
| 9080 | MT3 | 100 | 16 | 26 |
| 9080 | functional | 100 | 10 | 28 |
| 8241 | T1 | 100 | 16 | 22 |
| 8241 | T2 | 100 | 9 | 19 |
| 8241 | VST3 | 100 | 16 | 21 |
| 8241 | ST3 | 100 | 11 | 26 |
| 8241 | MT3 | 100 | 12 | 25 |
| 8241 | functional | 100 | 8 | 28 |
| 8828 | T1 | 100 | 14 | 23 |
| 8828 | T2 | 100 | 14 | 21 |
| 8828 | VST3 | 100 | 10 | 21 |
| 8828 | ST3 | 100 | 10 | 26 |
| 8828 | MT3 | 100 | 9 | 22 |
| 8828 | functional | 100 | 4 | 26 |
| 55 | T1 | 100 | 11 | 23 |
| 55 | T2 | 100 | 12 | 22 |
| 55 | VST3 | 100 | 13 | 24 |
| 55 | ST3 | 100 | 13 | 24 |
| 55 | MT3 | 100 | 10 | 25 |
| 55 | functional | 100 | 10 | 27 |
| 1375 | T1 | 100 | 9 | 23 |
| 1375 | T2 | 100 | 9 | 21 |
| 1375 | VST3 | 100 | 17 | 24 |
| 1375 | ST3 | 100 | 17 | 26 |
| 1375 | MT3 | 100 | 9 | 23 |
| 1375 | functional | 100 | 6 | 28 |
| 2084 | T1 | 100 | 9 | 23 |
| 2084 | T2 | 100 | 4 | 18 |
| 2084 | VST3 | 100 | 6 | 25 |
| 2084 | ST3 | 100 | 10 | 23 |
| 2084 | MT3 | 100 | 17 | 26 |
| 2084 | functional | 100 | 10 | 27 |
| 2802 | T1 | 100 | 14 | 22 |
| 2802 | T2 | 100 | 7 | 21 |
| 2802 | VST3 | 100 | 10 | 24 |
| 2802 | ST3 | 100 | 16 | 22 |
| 2802 | MT3 | 100 | 15 | 25 |
| 2802 | functional | 100 | 7 | 23 |
| 3501 | T1 | 100 | 15 | 21 |
| 3501 | T2 | 100 | 6 | 19 |
| 3501 | VST3 | 100 | 11 | 21 |
| 3501 | ST3 | 100 | 15 | 28 |
| 3501 | MT3 | 100 | 13 | 25 |
| 3501 | functional | 100 | 13 | 27 |
| 3389 | T1 | 100 | 13 | 23 |
| 3389 | T2 | 100 | 10 | 21 |
| 3389 | VST3 | 100 | 7 | 20 |
| 3389 | ST3 | 100 | 15 | 24 |
| 3389 | MT3 | 100 | 12 | 23 |
| 3389 | functional | 100 | 6 | 28 |

Distinct queries over all replicates: T1 901, T2 650, VST3 823, ST3 916, MT3 924, functional 975; union 4,260 (`union.tsv`, runner input).
