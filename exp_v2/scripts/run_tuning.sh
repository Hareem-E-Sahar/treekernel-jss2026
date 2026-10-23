#!/usr/bin/env bash
# exp_v2 step 1: tuning on the corpus with false positives (data/trees_e5/D.tsv, 72,782 methods), variant D.
# Runs every grid setting that is computable on the main corpus (results/grid_scan/main_corpus/scan.tsv; a setting
# that overflows there overflows here too) on the 50 tuning queries. A setting that overflows on the false positives
# stops the KeLP runner; it is then marked not computable and GridFiniteScan counts the overflowing methods.
# Then BM25 and CodeBERT (zero-shot, fine-tuned) on the tuning queries, and exp_v2/eval/tune.py selects.
# usage: exp_v2/scripts/run_tuning.sh [threads]   -> exp_v2/tuning/; finished steps are skipped.
set -euo pipefail
cd "$(dirname "$0")/../.."
if [ -z "${INHIBITED:-}" ]; then
  exec env INHIBITED=1 systemd-inhibit --what=sleep:idle:handle-lid-switch --who=treekernel \
    --why="exp_v2 tuning" "$0" "$@"
fi
THREADS=${1:-14}
CP=kernels/target/classes:$(cat kernels/classpath.txt)
TREES=data/trees_e5/D.tsv
TQ=exp_v2/data/tuning.tsv
T=exp_v2/tuning
mkdir -p $T/grid $T/runs $T/scan
export HF_HOME=third_party/hf HF_HUB_OFFLINE=1

G="0.1 0.2 0.4 0.6 0.8 1.0"
SETTINGS=""
for l in $G; do SETTINGS="$SETTINGS STK:$l:0"; done
for l in $G; do SETTINGS="$SETTINGS SSTK:$l:0"; done
for l in $G; do for m in $G; do SETTINGS="$SETTINGS PTK:$l:$m"; done; done

for s in $SETTINGS; do
  IFS=: read -r k l m <<< "$s"
  label="lambda=$l"; d=$T/grid/${k}_l$l; spec="$k:$l"
  if [ "$k" = PTK ]; then label="$label,mu=$m"; d=${d}_m$m; spec="$spec:$m"; fi
  key=$(printf 'D.tsv\t%s\t%s\t' "$k" "$label")
  grep -F "$key" results/grid_scan/main_corpus/scan.tsv | grep -q "non-finite=0" || continue   # not computable on main
  [ -f $d/meta.json ] || [ -f $d/NOT_COMPUTABLE ] && continue
  echo "== $k $label $(date +%T)"
  mkdir -p $d
  if java -Xmx8g -Dorg.slf4j.simpleLogger.defaultLogLevel=error -cp "$CP" treekernel.RetrievalRunner \
       $TREES $TQ "$k" "$l" "$m" "$THREADS" $d > $d/runner.log 2>&1; then
    rm -f $d/runner.log
  else
    grep -q "not finite" $d/runner.log || { echo "runner failed (not an overflow): $d/runner.log"; exit 1; }
    java -Xmx8g -DdumpDir=$T/scan -cp "$CP" treekernel.GridFiniteScan $TREES "$THREADS" 3600 "$spec" 2>/dev/null \
      | tee -a $T/scan.tsv | cut -f5 > $d/NOT_COMPUTABLE
    echo "   not computable: $(cat $d/NOT_COMPUTABLE)"
  fi
done

[ -f $T/runs/codebert_zs/meta.json ] || .venv/bin/python embed/codebert.py run $T/runs/codebert_zs \
  data/codebert/emb/zeroshot_e5.npy --trees $TREES --queries $TQ
[ -f $T/runs/codebert_ft/meta.json ] || .venv/bin/python embed/codebert.py run $T/runs/codebert_ft \
  "data/codebert/emb/fold{k}_e5.npy" --folds --trees $TREES --queries $TQ

if [ ! -f $T/runs/bm25/meta.json ]; then
  echo "== BM25 $(date +%T)"
  scripts/es_start.sh > $T/es.log 2>&1 &
  ES=$!
  until curl -s localhost:9201 > /dev/null; do sleep 5; done
  curl -s "localhost:9201/_cluster/health/bcb_e5?wait_for_status=yellow&timeout=120s" > /dev/null || true
  curl -sf localhost:9201/bcb_e5 > /dev/null || { echo "index bcb_e5 missing"; kill $ES; exit 1; }
  .venv/bin/python -I bm25/run_bm25.py query bcb_e5 $TQ $T/runs/bm25
  kill $ES; wait $ES || true
fi

.venv/bin/python exp_v2/eval/tune.py
echo "tuning done $(date +%T)"
