#!/usr/bin/env bash
# exp_v3_all_queries: evaluate the kernel runs on every eligible query (RQ1 per clone type, RQ2 functional), as
# exp_v2/scripts/run_hybrid.sh step 4 evaluated BM25, CodeBERT and the hybrids (exp_v2/results/hybrid/full/, reused).
# usage: exp_v3_all_queries/scripts/run_eval_main.sh  -> exp_v3_all_queries/results/full/D_{STK,SSTK,PTK}/eval
set -euo pipefail
cd "$(dirname "$0")/../.."
F=exp_v2/data/full
R=exp_v3_all_queries/results
SYN=""
for t in T1 T2 VST3 ST3 MT3; do SYN="$SYN --syntactic $F/syntactic_$t.tsv:$t"; done
for k in STK SSTK PTK; do
  e=$R/full/D_$k/eval
  [ -f $e/summary.tsv ] || echo ".venv/bin/python exp_v2/eval/evaluate.py $R/runs/D_$k $SYN --functional $F/functional.tsv --ignore exp_v2/data/fp_copies.tsv --boot 0 --out $e"
done | xargs -P 3 -I{} sh -c "{} > /dev/null"
echo "main evaluation done $(date '+%F %T')"
