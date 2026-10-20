#!/usr/bin/env bash
# RQ5 cost on the E5 corpus (72,782 methods = main + 58,103 false positives), same protocol as
# scripts/run_timing.sh: one thread, the 20 timing queries and a 0-query run; variant D tuned kernels,
# BM25 (fresh index, timed) and CodeBERT (encode + cosine; zero-shot weights, same cost as fine-tuned).
# Kernels and CodeBERT run with Elasticsearch stopped; ES is started only for the BM25 step, then stopped.
# usage: scripts/run_timing_e5.sh   -> results/rq5/e5/
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -z "${INHIBITED:-}" ]; then
  exec env INHIBITED=1 systemd-inhibit --what=sleep:idle:handle-lid-switch --who=treekernel \
    --why="RQ5 timing on E5 corpus" "$0" "$@"
fi
CP=kernels/target/classes:$(cat kernels/classpath.txt)
O=results/rq5/e5; mkdir -p $O
T=data/trees_e5/D.tsv
if [ ! -f $O/tree_kernels.tsv ]; then
  echo -e "variant\tkernel\tsetting\tqueries\twall_s\tmax_rss_kb" > $O/tree_kernels.tmp
  for s in D:STK:0.8:0 D:SSTK:0.1:0 D:PTK:0.4:0.6; do
    IFS=: read -r V k l m <<< "$s"
    for qf in timing_empty timing_queries; do
      d=$O/runs/${V}_${k}_$qf
      /usr/bin/time -f "%e\t%M" -o $O/time.tmp java -Xmx6g -Dorg.slf4j.simpleLogger.defaultLogLevel=error -cp "$CP" \
        treekernel.RetrievalRunner $T data/pools/$qf.tsv "$k" "$l" "$m" 1 "$d" > /dev/null
      n=$(($(wc -l < data/pools/$qf.tsv) - 1))
      echo -e "$V\t$k\tl=$l,m=$m\t$n\t$(cat $O/time.tmp)" | tee -a $O/tree_kernels.tmp
    done
  done
  rm -f $O/time.tmp
  mv $O/tree_kernels.tmp $O/tree_kernels.tsv
fi
[ -f $O/codebert.json ] || HF_HOME=third_party/hf HF_HUB_OFFLINE=1 .venv/bin/python embed/codebert.py timing \
  data/codebert/emb/zeroshot_e5.npy $O/codebert.json $T data/trees_e5/source.tsv
if [ ! -f $O/runs/bm25_timing_queries/timing.tsv ]; then
  scripts/es_start.sh > $O/es.log 2>&1 &
  ES=$!
  until curl -s localhost:9201 > /dev/null; do sleep 5; done
  .venv/bin/python -I bm25/run_bm25.py index bcb_timing_e5 $T data/trees_e5/source.tsv > $O/bm25_index.log
  cp results/bm25/index_bcb_timing_e5.json $O/bm25_index.json
  .venv/bin/python -I bm25/run_bm25.py query bcb_timing_e5 data/pools/timing_queries.tsv $O/runs/bm25_timing_queries > /dev/null
  curl -s -X DELETE localhost:9201/bcb_timing_e5 > /dev/null
  kill $ES; wait $ES || true
fi
echo "all done $(date +%T)"
