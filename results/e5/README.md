# E5: robustness, false positives added to the corpus

Corpus: the 14,679 main-corpus true positives plus 58,103 BigCloneBench false positives (methods judged false positive for some functionality and true positive for none), 72,782 methods, variant D only (`data/trees_e5/`, built by `prep/build_fp_trees.py` and `prep/build_e5_corpus.py`). Same 584 evaluation queries and ground truth as the main runs; false positives are never relevant, so they can only push relevant items down.

Excluded: 219 of the 58,322 false positives, those whose SSTK λ = 0.4 self-similarity overflows on D (same rule as the 101 main-corpus exclusions). The overflows at the E5 settings (SSTK 0.1: 5, PTK (0.4, 0.6): 22, STK 0.8: 0) are all among these 219. Scan: `scan/`; list: `data/corpus/e5_excluded_fp.tsv`.

Runs: D at tuned settings, `scripts/run_e5.sh 14 STK:0.8:0 SSTK:0.1:0 PTK:0.4:0.6` (log `run.log`; 21 min STK, 21 min SSTK, 49 min PTK on 14 threads). BM25: `results/bm25/e5/all` (same index settings, `bcb_e5`). Tables: `results/eval/tables.md` § E5.

Findings:
- Every method loses; BM25 loses most on RQ1 (mean MAP −0.085 vs −0.043 to −0.052 for the kernels), so the kernels' lead over BM25 grows: PTK − BM25 = +0.078 (main corpus +0.037), and on MT3 PTK is now significantly better (+0.083).
- RQ2 (functional MAP@R) roughly halves for every method; BM25 still leads clearly (0.259 vs 0.078–0.089).
- T1 falls by 0.014 for every method, from three queries (6550, 5245204, 8682423). The false positives contain exact copies of these queries (PTK score 1.0: 14, 2 and 1 copies), which are tied with the true T1 clones but never relevant. This is a labelling property of BigCloneBench (the same code judged false positive for one functionality), not a retrieval failure.

## CodeBERT (added 2026-10-19)

Fine-tuned CodeBERT on the enlarged corpus: RQ1 mean 0.831 (−0.079), MAP@R 0.249 (−0.237). It degrades like BM25. PTK and STK are significantly better than fine-tuned CodeBERT on the RQ1 mean, but significantly worse on MAP@R. Output: `results/codebert/e5/`.
