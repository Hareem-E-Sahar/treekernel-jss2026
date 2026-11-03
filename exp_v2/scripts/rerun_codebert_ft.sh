#!/usr/bin/env bash
# exp_v2: rerun everything that uses fine-tuned CodeBERT with the models fine-tuned with false positives as hard
# negatives (exp_v2/scripts/run_codebert_fp.sh -> data/codebert/emb/fpft_fold{k}_e5.npy; decided 2026-10-31).
# 1. The runs and evaluations of the models fine-tuned on true positives only are moved, with their paths, to
#    exp_v2/results/archive_codebert_tp/ (kept for comparison), and tuning/selected.json is kept as selected_tp.json.
# 2. The run scripts are rerun in order; each skips its finished steps, so only CodeBERT ft and the fusions with it
#    are recomputed: tuning (fusion W with CodeBERT ft), replicates, untuned fusion, size and complexity, hybrid.
#    The secondary main-corpus setting (results/main) keeps the true-positive models.
# 3. Aggregations and paper assets.
# usage: exp_v2/scripts/rerun_codebert_ft.sh [threads]
set -euo pipefail
cd "$(dirname "$0")/../.."
if [ -z "${INHIBITED:-}" ]; then
  exec env INHIBITED=1 systemd-inhibit --what=sleep:idle:handle-lid-switch --who=treekernel \
    --why="exp_v2 CodeBERT ft rerun" "$0" "$@"
fi
THREADS=${1:-14}
for k in 0 1 2 3 4; do [ -f data/codebert/emb/fpft_fold${k}_e5.npy ] || { echo "fold $k not encoded yet"; exit 1; }; done
A=exp_v2/results/archive_codebert_tp
if [ ! -f $A/done ]; then
  echo "== archive the true-positive CodeBERT ft runs $(date +%T)"
  mkdir -p $A
  cp -n exp_v2/tuning/selected.json exp_v2/tuning/selected_tp.json
  for p in exp_v2/tuning/runs/codebert_ft exp_v2/tuning/fusion/*codebert_ft* \
           exp_v2/results/fp/runs/*codebert_ft* exp_v2/results/fp/seed*/*codebert_ft* \
           exp_v2/results/fusion_untuned/runs/*codebert_ft* exp_v2/results/fusion_untuned/seed*/*codebert_ft* \
           exp_v2/results/size_complexity/runs/codebert_ft exp_v2/results/size_complexity/seed*/*/codebert_ft \
           exp_v2/results/hybrid/runs/codebert_ft exp_v2/results/hybrid/full/codebert_ft; do
    [ -e "$p" ] || continue
    mkdir -p $A/$(dirname ${p#exp_v2/})
    mv "$p" $A/${p#exp_v2/}
  done
  touch $A/done
fi
for s in run_tuning run_replicates run_fusion_untuned run_size_complexity run_hybrid; do
  echo "== $s $(date +%T)"
  INHIBITED=1 exp_v2/scripts/$s.sh $THREADS
done
echo "== aggregate $(date +%T)"
.venv/bin/python exp_v2/eval/replicates.py fp
.venv/bin/python exp_v2/eval/replicate_metrics.py fp
.venv/bin/python exp_v2/eval/size_complexity.py
.venv/bin/python exp_v2/eval/hybrid.py
.venv/bin/python exp_v2/eval/fusion_untuned.py
echo "all done $(date +%T)"
