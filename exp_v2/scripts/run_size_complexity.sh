#!/usr/bin/env bash
# exp_v2 size and complexity analysis: the stratified query sets (exp_v2/data/size_complexity, 10 seeds x 4 groups) on
# the corpus with false positives, variant D, at the settings tuned in exp_v2/tuning (no fusion).
# Kernels and BM25: only queries without a row in the replicate runs (exp_v2/results/fp/runs) are scored, in chunks
# below the runner's 2 GB buffer limit; exp_v2/eval/merge_runs.py then assembles one run per method over the union
# (rows copied unchanged). CodeBERT likewise (its runs are held in memory whole).
# usage: exp_v2/scripts/run_size_complexity.sh [threads]   -> exp_v2/results/size_complexity/{runs,seed<S>/<group>/<method>/eval}
set -euo pipefail
cd "$(dirname "$0")/../.."
if [ -z "${INHIBITED:-}" ]; then
  exec env INHIBITED=1 systemd-inhibit --what=sleep:idle:handle-lid-switch --who=treekernel \
    --why="exp_v2 size and complexity" "$0" "$@"
fi
THREADS=${1:-14}
CP=kernels/target/classes:$(cat kernels/classpath.txt)
TREES=data/trees_e5/D.tsv
P=exp_v2/data/size_complexity
U=$P/union.tsv
REP=exp_v2/results/fp/runs
R=exp_v2/results/size_complexity
O=$R/runs
N=$R/new_queries
SEL=exp_v2/tuning/selected.json
CHUNK=1600
mkdir -p $O $N
export HF_HOME=third_party/hf HF_HUB_OFFLINE=1
cp $SEL $R/selected.json

# queries without a row in the replicate runs, in chunks
if [ ! -f $N/done ]; then
  comm -23 <(tail -n +2 $U | sort) <(tail -n +2 exp_v2/data/replicates/union.tsv | sort) | sort -n > $N/all.txt
  rm -f $N/part*.tsv
  split -l $CHUNK -d -a 2 $N/all.txt $N/chunk
  for c in $N/chunk*; do { echo function_id; cat $c; } > $N/part${c##*chunk}.tsv; rm $c; done
  { echo function_id; cat $N/all.txt; } > $N/all.tsv
  touch $N/done
fi
echo "new queries: $(wc -l < $N/all.txt) in $(ls $N/part*.tsv | wc -l) chunks"

for k in STK SSTK PTK; do
  name=$(.venv/bin/python -c "import json; print(json.load(open('$SEL'))['settings']['$k']['run'])")
  l=$(sed -E 's/^[A-Z]+_l([0-9.]+).*/\1/' <<< "$name")
  m=$(sed -nE 's/.*_m([0-9.]+)$/\1/p' <<< "$name"); m=${m:-0}
  [ -f $O/D_$k/meta.json ] && continue
  parts=""
  for p in $N/part*.tsv; do
    d=$N/D_${k}_$(basename $p .tsv)
    parts="$parts $d"
    [ -f $d/meta.json ] && continue
    echo "== D $k ($name) $(basename $p) $(date +%T)"
    java -Xmx8g -Dorg.slf4j.simpleLogger.defaultLogLevel=error -cp "$CP" treekernel.RetrievalRunner \
      $TREES $p "$k" "$l" "$m" "$THREADS" $d 2>&1 | grep -v "corpus methods scored" || true
    [ -f $d/meta.json ]
  done
  .venv/bin/python exp_v2/eval/merge_runs.py $U $O/D_$k $REP/D_$k $parts
  rm -r $parts
done

if [ ! -f $O/bm25/meta.json ]; then
  if [ ! -f $N/bm25/meta.json ]; then
    echo "== BM25 $(date +%T)"
    scripts/es_start.sh > $R/es.log 2>&1 &
    ES=$!
    until curl -s localhost:9201 > /dev/null; do sleep 5; done
    curl -s "localhost:9201/_cluster/health/bcb_e5?wait_for_status=yellow&timeout=120s" > /dev/null || true
    curl -sf localhost:9201/bcb_e5 > /dev/null || { echo "index bcb_e5 missing"; kill $ES; exit 1; }
    .venv/bin/python -I bm25/run_bm25.py query bcb_e5 $N/all.tsv $N/bm25
    kill $ES; wait $ES || true
  fi
  .venv/bin/python exp_v2/eval/merge_runs.py $U $O/bm25 $REP/bm25 $N/bm25
  rm -r $N/bm25
fi

# CodeBERT holds its whole matrix in memory (and a copy when writing): new queries only, then merged as above
for r in codebert_zs codebert_ft; do
  [ -f $O/$r/meta.json ] && continue
  if [ ! -f $N/$r/meta.json ]; then
    if [ $r = codebert_zs ]; then
      .venv/bin/python embed/codebert.py run $N/$r data/codebert/emb/zeroshot_e5.npy --trees $TREES --queries $N/all.tsv
    else
      .venv/bin/python embed/codebert.py run $N/$r "data/codebert/emb/fold{k}_e5.npy" --folds --trees $TREES --queries $N/all.tsv
    fi
  fi
  .venv/bin/python exp_v2/eval/merge_runs.py $U $O/$r $REP/$r $N/$r
  rm -r $N/$r
done

echo "== evaluate $(date +%T)"
for d in $P/seed*/*/; do
  d=${d%/}
  g=$(basename $d); s=$(basename $(dirname $d))
  SYN=""
  for t in T1 T2 VST3 ST3 MT3; do SYN="$SYN --syntactic $d/syntactic_$t.tsv:$t"; done
  for r in $O/*; do
    [ -f $r/meta.json ] || continue
    e=$R/$s/$g/$(basename $r)/eval
    [ -f $e/summary.tsv ] || echo ".venv/bin/python exp_v2/eval/evaluate.py $r $SYN --functional $d/functional.tsv --ignore exp_v2/data/fp_copies.tsv --boot 0 --out $e"
  done
done | xargs -P 4 -I{} sh -c "{} > /dev/null"
echo "all done $(date +%T)"
