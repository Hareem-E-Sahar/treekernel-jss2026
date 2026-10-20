#!/usr/bin/env bash
# RQ4 with CodeBERT (after scripts/run_codebert.sh has the main-corpus embeddings and the RQ5 timing):
# CodeBERT runs on the 50 tuning queries, then fusion of the tree kernel with fine-tuned CodeBERT, as for BM25.
# usage: scripts/run_codebert_rq4.sh   -> results/codebert/tuning/{zeroshot,finetuned}/, results/rq4/{rq1_PTK,rq2_STK}_codebert/
set -euo pipefail
cd "$(dirname "$0")/.."
export HF_HOME=third_party/hf HF_HUB_OFFLINE=1
PY=".venv/bin/python embed/codebert.py"
E=data/codebert/emb
T=data/pools/tuning.tsv
[ -f results/codebert/tuning/zeroshot/meta.json ] || $PY run results/codebert/tuning/zeroshot $E/zeroshot_main.npy --queries $T
[ -f results/codebert/tuning/finetuned/meta.json ] || $PY run results/codebert/tuning/finetuned "$E/fold{k}_main.npy" --folds --queries $T
CB=results/codebert/eval/finetuned
[ -f results/rq4/rq1_PTK_codebert/rrf/eval/summary.tsv ] || .venv/bin/python eval/tune_fusion.py rq1_PTK_codebert \
  results/grid/D/PTK_l0.4_m0.6 results/codebert/tuning/finetuned results/eval/D/PTK_l0.4_m0.6 $CB --objective rq1
[ -f results/rq4/rq2_STK_codebert/rrf/eval/summary.tsv ] || .venv/bin/python eval/tune_fusion.py rq2_STK_codebert \
  results/grid/D/STK_l0.8 results/codebert/tuning/finetuned results/eval/D/STK_l0.8 $CB --objective rq2
echo "rq4 done $(date +%T)"
