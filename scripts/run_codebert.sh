#!/usr/bin/env bash
# CodeBERT baseline (embed/codebert.py): zero-shot and fine-tuned (5 functionality folds), main corpus
# (RQ1, RQ2, RQ4) and E5 corpus, then RQ5 timing. Finished steps are skipped. Holds a sleep inhibitor.
# usage: scripts/run_codebert.sh
# Output: data/codebert/{models,emb}/, results/codebert/{eval,e5}/{zeroshot,finetuned}/, results/rq5/codebert.json
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -z "${INHIBITED:-}" ]; then
  exec env INHIBITED=1 systemd-inhibit --what=sleep:idle:handle-lid-switch --who=treekernel \
    --why="CodeBERT runs" "$0" "$@"
fi
export HF_HOME=third_party/hf HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false
PY=".venv/bin/python embed/codebert.py"
E=data/codebert/emb
mkdir -p $E
SYN=""
for t in T1 T2 VST3 ST3 MT3; do SYN="$SYN --syntactic data/pools/syntactic_$t.tsv:$t"; done
evaluate() { [ -f "$1/eval/summary.tsv" ] || .venv/bin/python eval/evaluate.py "$1" $SYN --functional data/pools/functional.tsv; }
step() { echo "== $* $(date +%T)"; }

# false positives of the E5 corpus, in its order (the main corpus comes first)
FP=data/codebert/e5_fp_ids.tsv
[ -f $FP ] || { echo function_id; tail -n +2 data/trees_e5/D.tsv | tail -n +14680 | cut -f1; } > $FP

# 1. zero-shot, main corpus
[ -f $E/zeroshot_main.npy ] || { step encode zero-shot main; $PY encode microsoft/codebert-base data/trees_main/D.tsv data/trees_main/source.tsv $E/zeroshot_main.npy; }
[ -f results/codebert/eval/zeroshot/meta.json ] || $PY run results/codebert/eval/zeroshot $E/zeroshot_main.npy
evaluate results/codebert/eval/zeroshot

# 2. fine-tuning, one model per fold, main corpus
for k in 0 1 2 3 4; do
  M=data/codebert/models/fold$k
  [ -f $M/train_meta.json ] || { step fine-tune fold $k; $PY finetune $k; }
  [ -f $E/fold${k}_main.npy ] || { step encode fold $k main; $PY encode $M data/trees_main/D.tsv data/trees_main/source.tsv $E/fold${k}_main.npy; }
done
[ -f results/codebert/eval/finetuned/meta.json ] || $PY run results/codebert/eval/finetuned "$E/fold{k}_main.npy" --folds
evaluate results/codebert/eval/finetuned

# 3. RQ5 timing (before E5, so results/rq5 is complete early)
[ -f results/rq5/codebert.json ] || { step timing; $PY timing $E/zeroshot_main.npy results/rq5/codebert.json; }

# 4. E5: encode the false positives, append to the main-corpus embeddings
for m in zeroshot fold0 fold1 fold2 fold3 fold4; do
  M=microsoft/codebert-base; [ $m = zeroshot ] || M=data/codebert/models/$m
  [ -f $E/${m}_fp.npy ] || { step encode $m false positives; $PY encode $M $FP data/trees_e5/source.tsv $E/${m}_fp.npy; }
  [ -f $E/${m}_e5.npy ] || .venv/bin/python -c "import numpy as np; np.save('$E/${m}_e5.npy', np.vstack([np.load('$E/${m}_main.npy'), np.load('$E/${m}_fp.npy')]))"
done
[ -f results/codebert/e5/zeroshot/meta.json ] || $PY run results/codebert/e5/zeroshot $E/zeroshot_e5.npy --trees data/trees_e5/D.tsv
[ -f results/codebert/e5/finetuned/meta.json ] || $PY run results/codebert/e5/finetuned "$E/fold{k}_e5.npy" --folds --trees data/trees_e5/D.tsv
evaluate results/codebert/e5/zeroshot
evaluate results/codebert/e5/finetuned
echo "all done $(date +%T)"
