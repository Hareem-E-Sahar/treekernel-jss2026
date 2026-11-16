#!/usr/bin/env bash
# exp_v3_all_queries, label-noise sensitivity (revision_plan.md, R1-C3): every method re-evaluated on every eligible
# query under two alternatives to the default (false positives non-relevant, exact copies of the query ignored):
#   t2      Type-2 copies of the query outside its functionality labels also ignored (option B;
#           exp_v3_all_queries/data/t2_copies.tsv from prep/t2_copies.py)
#   no_fp   every false positive removed from every ranking, as if unjudged (option A; evaluate.py --drop-fp)
# Runs: the kernels (exp_v3_all_queries/results/runs), BM25 and CodeBERT zs/ft (exp_v2/results/hybrid/runs).
# usage: exp_v3_all_queries/scripts/run_eval_noise.sh [parallel]  -> exp_v3_all_queries/results/noise/{t2,no_fp}/<run>/eval
set -euo pipefail
cd "$(dirname "$0")/../.."
P=${1:-4}
F=exp_v2/data/full
R=exp_v3_all_queries/results
SYN=""
for t in T1 T2 VST3 ST3 MT3; do SYN="$SYN --syntactic $F/syntactic_$t.tsv:$t"; done
RUNS="$(ls -d $R/runs/D_*) exp_v2/results/hybrid/runs/bm25 exp_v2/results/hybrid/runs/codebert_zs exp_v2/results/hybrid/runs/codebert_ft"
{
  for r in $RUNS; do
    base=".venv/bin/python exp_v3_all_queries/eval/evaluate.py $r $SYN --functional $F/functional.tsv --ignore exp_v2/data/fp_copies.tsv --boot 0"
    e=$R/noise/t2/$(basename $r)/eval
    [ -f $e/summary.tsv ] || echo "$base --ignore exp_v3_all_queries/data/t2_copies.tsv --out $e"
    e=$R/noise/no_fp/$(basename $r)/eval
    [ -f $e/summary.tsv ] || echo "$base --drop-fp --out $e"
  done
} | xargs -P $P -I{} sh -c "{} > /dev/null"
echo "noise evaluation done $(date '+%F %T')"
