#!/usr/bin/env bash
# exp_v2: fine-tune CodeBERT with false positives as hard negatives (exp_v2/embed/finetune_fp.py), 5 folds, then
# encode the corpus with false positives (72,782 methods) with each model. Resumes: finished folds are skipped.
# usage: exp_v2/scripts/run_codebert_fp.sh   -> data/codebert/models_fp/, data/codebert/emb/fpft_fold{k}_e5.npy
set -euo pipefail
cd "$(dirname "$0")/../.."
if [ -z "${INHIBITED:-}" ]; then
  exec env INHIBITED=1 systemd-inhibit --what=sleep:idle:handle-lid-switch --who=treekernel \
    --why="exp_v2 CodeBERT fine-tuning with false positives" "$0" "$@"
fi
export HF_HOME=third_party/hf HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false
PY=".venv/bin/python exp_v2/embed/finetune_fp.py"
for k in 0 1 2 3 4; do
  [ -f data/codebert/models_fp/fold$k/train_meta.json ] || { echo "== fold $k: fine-tune $(date +%T)"; $PY finetune $k; }
done
for k in 0 1 2 3 4; do
  [ -f data/codebert/emb/fpft_fold${k}_e5.npy ] || { echo "== fold $k: encode $(date +%T)"; $PY encode $k; }
done
echo "all done $(date +%T)"
