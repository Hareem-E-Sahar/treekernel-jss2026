#!/usr/bin/env bash
# exp_v2 hybrid: BM25 top k (k = 100, 200; not tuned) re-ranked by a tree kernel (STK, SSTK, PTK at the tuned settings),
# on every eligible query (exp_v2/data/full, 14,587 queries), corpus with false positives (data/trees_e5/D.tsv).
# Below rank k the BM25 order is kept, so every metric is defined over the full ranking.
# Steps (finished steps are skipped):
#   1. first stage: BM25 top 200 per query (exp_v2/hybrid/bm25_topk.py, index bcb_e5), with its timing
#   2. full BM25 and CodeBERT runs over all queries (the baselines, and BM25's order below k): rows of the replicate and
#      size-complexity runs are reused, the missing queries scored in chunks, then exp_v2/eval/merge_runs.py
#   3. second stage: HybridRerank scores the top-200 pairs per kernel (with timing); build_hybrid.py builds the runs
#   4. evaluation on the full query sets (all methods) and on the 10 replicate sets (hybrids; the other methods'
#      replicate evaluations are in exp_v2/results/fp)
# usage: exp_v2/scripts/run_hybrid.sh [threads]   -> exp_v2/results/hybrid/
set -euo pipefail
cd "$(dirname "$0")/../.."
if [ -z "${INHIBITED:-}" ]; then
  exec env INHIBITED=1 systemd-inhibit --what=sleep:idle:handle-lid-switch --who=treekernel \
    --why="exp_v2 hybrid" "$0" "$@"
fi
THREADS=${1:-14}
CP=kernels/target/classes:$(cat kernels/classpath.txt)
HCP=exp_v2/kernels/classes:$CP
TREES=data/trees_e5/D.tsv
F=exp_v2/data/full
U=$F/union.tsv
R=exp_v2/results/hybrid
O=$R/runs
N=$R/new_queries
SEL=exp_v2/tuning/selected.json
REP=exp_v2/results/fp/runs
SZ=exp_v2/results/size_complexity/runs
CHUNK=1500
mkdir -p $O $N $R/stage1 $R/pairs
export HF_HOME=third_party/hf HF_HUB_OFFLINE=1
cp $SEL $R/selected.json
[ -f exp_v2/kernels/classes/treekernel/HybridRerank.class ] || javac -cp "$CP" -d exp_v2/kernels/classes \
  exp_v2/kernels/src/treekernel/HybridRerank.java

# queries without a full BM25 / CodeBERT row in the replicate or size-complexity runs, in chunks
if [ ! -f $N/done ]; then
  comm -23 <(tail -n +2 $U | sort) <(cat <(tail -n +2 exp_v2/data/replicates/union.tsv) \
    <(tail -n +2 exp_v2/data/size_complexity/union.tsv) | sort -u) | sort -n > $N/all.txt
  rm -f $N/part*.tsv
  split -l $CHUNK -d -a 2 $N/all.txt $N/chunk
  for c in $N/chunk*; do { echo function_id; cat $c; } > $N/part${c##*chunk}.tsv; rm $c; done
  touch $N/done
fi
echo "queries: $(($(wc -l < $U) - 1)); without full BM25/CodeBERT rows: $(wc -l < $N/all.txt) in $(ls $N/part*.tsv | wc -l) chunks"

# ---- 1 and 2a: BM25 (Elasticsearch)
if [ ! -f $R/stage1/meta.json ] || [ ! -f $O/bm25/meta.json ]; then
  scripts/es_start.sh > $R/es.log 2>&1 &
  ES=$!
  until curl -s localhost:9201 > /dev/null; do sleep 5; done
  curl -s "localhost:9201/_cluster/health/bcb_e5?wait_for_status=yellow&timeout=120s" > /dev/null || true
  curl -sf localhost:9201/bcb_e5 > /dev/null || { echo "index bcb_e5 missing"; kill $ES; exit 1; }
  if [ ! -f $R/stage1/meta.json ]; then
    echo "== stage 1: BM25 top 200 $(date +%T)"
    .venv/bin/python -I exp_v2/hybrid/bm25_topk.py bcb_e5 $U $R/stage1 --k 200
  fi
  if [ ! -f $O/bm25/meta.json ]; then
    parts=""
    for p in $N/part*.tsv; do
      d=$N/bm25_$(basename $p .tsv); parts="$parts $d"
      [ -f $d/meta.json ] && continue
      echo "== BM25 full $(basename $p) $(date +%T)"
      .venv/bin/python -I bm25/run_bm25.py query bcb_e5 $p $d
    done
    .venv/bin/python exp_v2/eval/merge_runs.py $U $O/bm25 $REP/bm25 $SZ/bm25 $parts
    rm -r $parts
  fi
  kill $ES; wait $ES || true
fi

# ---- 2b: CodeBERT (held in memory whole: chunks)
for r in codebert_zs codebert_ft; do
  [ -f $O/$r/meta.json ] && continue
  parts=""
  for p in $N/part*.tsv; do
    d=$N/${r}_$(basename $p .tsv); parts="$parts $d"
    [ -f $d/meta.json ] && continue
    if [ $r = codebert_zs ]; then
      .venv/bin/python embed/codebert.py run $d data/codebert/emb/zeroshot_e5.npy --trees $TREES --queries $p
    else
      .venv/bin/python embed/codebert.py run $d "data/codebert/emb/fold{k}_e5.npy" --folds --trees $TREES --queries $p
    fi
  done
  .venv/bin/python exp_v2/eval/merge_runs.py $U $O/$r $REP/$r $SZ/$r $parts
  rm -r $parts
done

# ---- 3: second stage and the hybrid runs
cut -f1,3 $R/stage1/topk.tsv > $R/pairs/pairs.tsv
for k in STK SSTK PTK; do
  name=$(.venv/bin/python -c "import json; print(json.load(open('$SEL'))['settings']['$k']['run'])")
  l=$(sed -E 's/^[A-Z]+_l([0-9.]+).*/\1/' <<< "$name")
  m=$(sed -nE 's/.*_m([0-9.]+)$/\1/p' <<< "$name"); m=${m:-0}
  if [ ! -f $R/pairs/$k.tsv.timing.tsv ]; then
    echo "== stage 2: $k ($name) on the top-200 pairs $(date +%T)"
    java -Xmx8g -Dorg.slf4j.simpleLogger.defaultLogLevel=error -cp "$HCP" treekernel.HybridRerank \
      $TREES $R/pairs/pairs.tsv "$k" "$l" "$m" "$THREADS" $R/pairs/$k.tsv
  fi
  for K in 100 200; do
    [ -f $O/hybrid_${k}_k$K/meta.json ] || .venv/bin/python exp_v2/hybrid/build_hybrid.py $O/bm25 $R/stage1/topk.tsv \
      $R/pairs/$k.tsv $REP/D_$k $K $O/hybrid_${k}_k$K
  done
done

# ---- 4: evaluation
echo "== evaluate $(date +%T)"
IGN="--ignore exp_v2/data/fp_copies.tsv --boot 0"
{
  SYN=""
  for t in T1 T2 VST3 ST3 MT3; do SYN="$SYN --syntactic $F/syntactic_$t.tsv:$t"; done
  for r in $O/*; do
    e=$R/full/$(basename $r)/eval
    [ -f $e/summary.tsv ] || echo ".venv/bin/python exp_v2/eval/evaluate.py $r $SYN --functional $F/functional.tsv $IGN --out $e"
  done
  for d in exp_v2/data/replicates/seed*; do
    SYN=""
    for t in T1 T2 VST3 ST3 MT3; do SYN="$SYN --syntactic $d/syntactic_$t.tsv:$t"; done
    for r in $O/hybrid_*; do
      e=$R/replicates/$(basename $d)/$(basename $r)/eval
      [ -f $e/summary.tsv ] || echo ".venv/bin/python exp_v2/eval/evaluate.py $r $SYN --functional $d/functional.tsv $IGN --out $e"
    done
  done
} | xargs -P 4 -I{} sh -c "{} > /dev/null"
echo "all done $(date +%T)"
