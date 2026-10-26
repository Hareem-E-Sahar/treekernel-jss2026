#!/usr/bin/env bash
# exp_v2: fusion without tuning W (question 2026-10-26: "how will it change if we don't tune for W"). The four weighted
# sums of exp_v2/results/fp/fusion_jobs.txt at the default W = 0.5 instead of the tuned W, on the 10 replicate sets
# (corpus with false positives), evaluated like every other replicate run. RRF needs no tuning and is already in
# exp_v2/results/fp. Runs go to a separate folder so the replicate results stay as they are.
# usage: exp_v2/scripts/run_fusion_untuned.sh   -> exp_v2/results/fusion_untuned/{runs,seed<S>/<run>/eval}
set -euo pipefail
cd "$(dirname "$0")/../.."
W=0.5
FP=exp_v2/results/fp
R=exp_v2/results/fusion_untuned
mkdir -p $R/runs
while read -r name k other w; do
  d=$R/runs/${name}_wsum_w$W
  [ -f $d/meta.json ] || .venv/bin/python exp_v2/eval/fusion.py $FP/runs/D_$k $FP/runs/$other $d --method wsum --w $W
done < $FP/fusion_jobs.txt
for d in exp_v2/data/replicates/seed*; do
  SYN=""
  for t in T1 T2 VST3 ST3 MT3; do SYN="$SYN --syntactic $d/syntactic_$t.tsv:$t"; done
  for r in $R/runs/*; do
    e=$R/$(basename $d)/$(basename $r)/eval
    [ -f $e/summary.tsv ] || echo ".venv/bin/python exp_v2/eval/evaluate.py $r $SYN --functional $d/functional.tsv --ignore exp_v2/data/fp_copies.tsv --boot 0 --out $e"
  done
done | xargs -P 4 -I{} sh -c "{} > /dev/null"
echo "done"
