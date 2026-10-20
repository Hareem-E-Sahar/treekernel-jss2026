#!/usr/bin/env bash
# RQ5 cost (PLAN.md §6, E7). Run on an otherwise idle machine, one thread, no other jobs.
#   Tree kernels: RetrievalRunner with 1 thread, 20 timing queries (data/pools/timing_queries.tsv,
#     random from the evaluation queries, seed 20261018) and with 0 queries. The 0-query run
#     costs parsing + the 14,679 self-similarities (a one-off "index" cost); the difference / 20
#     is the time per query against the whole corpus. Peak memory: max RSS (/usr/bin/time).
#   BM25: index build, and the 20 timing queries one at a time (Elasticsearch `took` and client
#     time), with the node at 2 GB heap.
#   Tree building (tree-sitter parse + variant): prep/time_trees.py.
# usage: scripts/run_timing.sh   -> results/rq5/
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -z "${INHIBITED:-}" ]; then
  exec env INHIBITED=1 systemd-inhibit --what=sleep:idle:handle-lid-switch --who=treekernel \
    --why="RQ5 timing" "$0" "$@"
fi
CP=kernels/target/classes:$(cat kernels/classpath.txt)
O=results/rq5; mkdir -p $O
echo -e "variant\tkernel\tsetting\tqueries\twall_s\tmax_rss_kb" > $O/tree_kernels.tsv
for s in D:STK:0.8:0 D:SSTK:0.1:0 D:PTK:0.4:0.6 C:STK:0.8:0 C:SSTK:0.1:0 C:PTK:0.4:0.6 \
         B:STK:1.0:0 B:SSTK:0.1:0 B:PTK:0.4:0.6 A:STK:1.0:0 A:SSTK:0.1:0 A:PTK:0.6:0.4; do
  IFS=: read -r V k l m <<< "$s"
  for qf in timing_empty timing_queries; do
    d=$O/runs/${V}_${k}_$qf
    /usr/bin/time -f "%e\t%M" -o $O/time.tmp java -Xmx3g -Dorg.slf4j.simpleLogger.defaultLogLevel=error -cp "$CP" \
      treekernel.RetrievalRunner data/trees_main/$V.tsv data/pools/$qf.tsv "$k" "$l" "$m" 1 "$d" > /dev/null
    n=$(($(wc -l < data/pools/$qf.tsv) - 1))
    echo -e "$V\t$k\tl=$l,m=$m\t$n\t$(cat $O/time.tmp)" | tee -a $O/tree_kernels.tsv
  done
done
.venv/bin/python -I prep/time_trees.py > $O/tree_building.tsv
.venv/bin/python -I bm25/run_bm25.py index bcb_timing data/trees_main/D.tsv data/trees_main/source.tsv > $O/bm25_index.log
cp results/bm25/index_bcb_timing.json $O/bm25_index.json
.venv/bin/python -I bm25/run_bm25.py query bcb_timing data/pools/timing_queries.tsv $O/runs/bm25_timing_queries > /dev/null
curl -s "localhost:9201/_nodes/stats/jvm" | .venv/bin/python -c "import json,sys; n=list(json.load(sys.stdin)['nodes'].values())[0]['jvm']['mem']; print(json.dumps(n, indent=1))" > $O/bm25_jvm.json
curl -s -X DELETE localhost:9201/bcb_timing > /dev/null
echo "all done $(date +%T)"
