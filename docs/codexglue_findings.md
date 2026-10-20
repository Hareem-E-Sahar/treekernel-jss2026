# CodeXGLUE version of BigCloneBench: findings (checked 2026-10-11)

*Not used in the current study (decided 2026-10-12: BigCloneBench full database only). Kept for reference.*

Data: `data/codexglue_bcb/`. Scripts: `scripts/inspect_codexglue_bcb.py`, `scripts/split_components.py`, `scripts/verify_bcb_join.py`. Annotated pairs: `data/bcb_joined/{train,valid,test}_pairs_labelled.tsv`.

- **Basic counts.** There are 9,126 functions. Every function ID used in a pair exists in `data.jsonl`, and no pair has conflicting labels.
- **No function leakage between splits.** Train uses 7,302 functions, valid 912 and test 912, and no function appears in more than one split.
- **Duplicated training pairs.** `train.txt` lists 225,431 pairs twice, once in each order. That leaves 675,597 unique pairs: 225,431 positive and 450,166 negative.
- **Valid and test are fully labelled.** Each has 912 × 911 / 2 = 415,416 pairs, which is every possible pair.
- **The join with full BCB is exact.** CodeXGLUE `idx` is the BCB `functions.id`. For 9,118 of the 9,126 functions, the source text matches the IJaDataset file lines exactly, and the other 8 differ slightly. Every CodeXGLUE positive pair is a BCB clone. In train, 1 negative is actually a BCB clone, and 90 negatives are BCB false positives.
- **Clone types are about 98% WT3/T4.**

  | split | T1 | T2 | VST3 | ST3 | MT3 | WT3/T4 |
  |---|---|---|---|---|---|---|
  | train | 572 | 118 | 84 | 359 | 2,046 | 222,252 |
  | valid | 244 | 38 | 26 | 68 | 525 | 52,938 |
  | test | 143 | 68 | 16 | 141 | 592 | 55,860 |

- **Test clone groups map to functionalities.** The groups are Copy File (285, which also contains a Zip Files clique of 8), Secure Hash (138), Download From Web (90), Execute update and rollback (73), Connect to FTP Server (19), Bubble Sort Array (14), Setup SGV (2) and Initialize Java Eclipse Project (2). The other 289 test functions are rejected "Download From Web" candidates.
- **Validation.** Its 189-function group joins Secure Hash and Execute update and rollback through shared functions, so it isn't transitive. Use the pair labels as relevance judgements, not group membership.
- **Coverage.** Test covers only 9 of the 43 functionalities, and one functionality (Copy File) holds 285 of the 623 functions that have a clone. Its value would be comparability with machine-learning papers that report F1 on these splits.
