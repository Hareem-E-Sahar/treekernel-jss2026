#!/usr/bin/env bash
# RQ2 tuning check (decision 2026-10-20): would the kernels pick other settings if tuned for MAP@R instead of the
# RQ1 objective (mean MAP over the five clone types)? Step 1 re-evaluates every existing grid run (results/grid/<V>/,
# 50 tuning queries) with functional relevance; no new kernel runs. Results/grid stays untouched.
# usage: scripts/run_rq2_tuning_check.sh   -> results/rq2_tuning_check/grid/<V>/<setting>/eval
set -euo pipefail
cd "$(dirname "$0")/.."
O=results/rq2_tuning_check/grid
for d in results/grid/[ABCD]/*_l*/; do
  d=${d%/}
  [ -f $d/logk.f64 ] || continue
  e=$O/$(basename "$(dirname $d)")/$(basename $d)/eval
  [ -f $e/summary.tsv ] || echo ".venv/bin/python eval/evaluate.py $d --functional data/pools/tuning.tsv --boot 0 --out $e"
done | xargs -P 4 -I{} sh -c "{} > /dev/null"
echo "grid evaluated $(date +%T)"
