#!/usr/bin/env bash
# exp_v2 cost: time to evaluate the 100 RQ2 queries of one replicate set (seed 6251) on the corpus with false positives
# (72,782 methods), for the full rankings (tree kernels, BM25, CodeBERT; reported with RQ2) and the hybrid (RQ4).
# Protocol of the frozen experiment (scripts/run_timing.sh, run_timing_e5.sh): one thread; each Java step also run with
# 0 queries (JVM start, reading the trees; the kernels' self-similarities), so per query = (100-query time - 0-query
# time) / 100. Elasticsearch runs only for the BM25 steps; nothing else runs meanwhile.
#   tree kernels, full ranking: RetrievalRunner, 1 thread, tuned settings (exp_v2/tuning/selected.json)
#   BM25, full ranking: bm25/run_bm25.py on index bcb_e5 (per query: Elasticsearch `took`, and client time incl. all scores)
#   CodeBERT: encode the query + cosine (exp_v2/hybrid/timing_codebert.py)
#   hybrid: stage 1 = BM25 top 200 (exp_v2/hybrid/bm25_topk.py); stage 2 = HybridRerank, 1 thread, top 100 or 200 pairs
# usage: exp_v2/scripts/run_timing.sh [seed]   -> exp_v2/results/timing/
set -euo pipefail
cd "$(dirname "$0")/../.."
if [ -z "${INHIBITED:-}" ]; then
  exec env INHIBITED=1 systemd-inhibit --what=sleep:idle:handle-lid-switch --who=treekernel \
    --why="exp_v2 timing" "$0" "$@"
fi
SEED=${1:-6251}
CP=kernels/target/classes:$(cat kernels/classpath.txt)
HCP=exp_v2/kernels/classes:$CP
TREES=data/trees_e5/D.tsv
Q=exp_v2/data/replicates/seed$SEED/functional.tsv
O=exp_v2/results/timing
SEL=exp_v2/tuning/selected.json
mkdir -p $O/runs
export HF_HOME=third_party/hf HF_HUB_OFFLINE=1
head -1 $Q > $O/empty.tsv
cp $Q $O/queries.tsv
[ -f exp_v2/kernels/classes/treekernel/HybridRerank.class ] || javac -cp "$CP" -d exp_v2/kernels/classes \
  exp_v2/kernels/src/treekernel/HybridRerank.java
pgrep -f "org.elasticsearch|RetrievalRunner|HybridRerank" > /dev/null && { echo "another run is active; timing needs an idle machine"; exit 1; }

# hybrid pairs for these queries (from the stage-1 top 200 of every eligible query)
for K in 100 200; do
  awk -F'\t' -v K=$K 'NR==FNR { if (FNR > 1) q[$1] = 1; next } FNR == 1 { print "query_id\tcandidate_id"; next } ($1 in q) && $2 <= K { print $1 "\t" $3 }' \
    $Q exp_v2/results/hybrid/stage1/topk.tsv > $O/pairs_k$K.tsv
done
printf 'query_id\tcandidate_id\n' > $O/pairs_empty.tsv

run_timed() {   # label, then the command; appends label, wall seconds, max RSS (KB)
  local label=$1; shift
  /usr/bin/time -f "%e\t%M" -o $O/time.tmp "$@" > /dev/null
  echo -e "$label\t$(cat $O/time.tmp)" | tee -a $O/java.tsv
}

if [ ! -f $O/java.done ]; then
  echo -e "step\tqueries\twall_s\tmax_rss_kb" > $O/java.tsv
  for k in STK SSTK PTK; do
    name=$(.venv/bin/python -c "import json; print(json.load(open('$SEL'))['settings']['$k']['run'])")
    l=$(sed -E 's/^[A-Z]+_l([0-9.]+).*/\1/' <<< "$name")
    m=$(sed -nE 's/.*_m([0-9.]+)$/\1/p' <<< "$name"); m=${m:-0}
    for qf in empty queries; do
      n=$(($(wc -l < $O/$qf.tsv) - 1))
      run_timed "full_$k	$n" java -Xmx6g -Dorg.slf4j.simpleLogger.defaultLogLevel=error -cp "$CP" \
        treekernel.RetrievalRunner $TREES $O/$qf.tsv "$k" "$l" "$m" 1 $O/runs/full_${k}_$qf
      rm -f $O/runs/full_${k}_$qf/logk.f64
    done
    for pf in empty k100 k200; do
      n=$([ $pf = empty ] && echo 0 || echo 100)
      run_timed "hybrid_${k}_$pf	$n" java -Xmx6g -Dorg.slf4j.simpleLogger.defaultLogLevel=error -cp "$HCP" \
        treekernel.HybridRerank $TREES $O/pairs_$pf.tsv "$k" "$l" "$m" 1 $O/runs/hybrid_${k}_$pf.tsv
    done
  done
  touch $O/java.done
fi

[ -f $O/codebert.json ] || .venv/bin/python exp_v2/hybrid/timing_codebert.py $Q $O/codebert.json

if [ ! -f $O/runs/bm25_full/timing.tsv ] || [ ! -f $O/runs/bm25_top200/timing.tsv ]; then
  scripts/es_start.sh > $O/es.log 2>&1 &
  ES=$!
  until curl -s localhost:9201 > /dev/null; do sleep 5; done
  curl -s "localhost:9201/_cluster/health/bcb_e5?wait_for_status=yellow&timeout=120s" > /dev/null || true
  # warm-up on the 50 tuning queries (not timed): a freshly started node answers its first queries slowly
  .venv/bin/python -I exp_v2/hybrid/bm25_topk.py bcb_e5 exp_v2/data/tuning.tsv $O/runs/warmup --k 200 > /dev/null
  .venv/bin/python -I bm25/run_bm25.py query bcb_e5 exp_v2/data/tuning.tsv $O/runs/warmup_full > /dev/null
  rm -r $O/runs/warmup $O/runs/warmup_full
  .venv/bin/python -I bm25/run_bm25.py query bcb_e5 $Q $O/runs/bm25_full > /dev/null
  rm -f $O/runs/bm25_full/logk.f64
  .venv/bin/python -I exp_v2/hybrid/bm25_topk.py bcb_e5 $Q $O/runs/bm25_top200 --k 200 > /dev/null
  kill $ES; wait $ES || true
fi
rm -f $O/time.tmp
echo "all done $(date +%T)"
