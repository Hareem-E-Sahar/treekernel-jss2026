#!/usr/bin/env bash
# exp_v2 step 2: the 10 replicate query sets on the corpus with false positives (data/trees_e5/D.tsv), variant D,
# at the settings and fusion weights selected in step 1 (exp_v2/tuning/selected.json).
# Query sets: exp_v2/data/replicates (copied from data/pools/replicates; seeds 55, 1375, 2084, 2802, 3389, 3501,
# 6251, 8241, 8828, 9080). One run per method over the union of all replicate queries, then each replicate is
# evaluated from those runs, with false positives that are exact copies of the query ignored.
# usage: exp_v2/scripts/run_replicates.sh [threads]   -> exp_v2/results/fp/{runs,seed<S>/<method>/eval}
set -euo pipefail
cd "$(dirname "$0")/../.."
if [ -z "${INHIBITED:-}" ]; then
  exec env INHIBITED=1 systemd-inhibit --what=sleep:idle:handle-lid-switch --who=treekernel \
    --why="exp_v2 replicates" "$0" "$@"
fi
THREADS=${1:-14}
CP=kernels/target/classes:$(cat kernels/classpath.txt)
TREES=data/trees_e5/D.tsv
P=exp_v2/data/replicates
U=$P/union.tsv
R=exp_v2/results/fp
O=$R/runs
SEL=exp_v2/tuning/selected.json
mkdir -p $O
export HF_HOME=third_party/hf HF_HUB_OFFLINE=1
[ -f $SEL ] || { echo "no $SEL: run exp_v2/scripts/run_tuning.sh first"; exit 1; }
cp $SEL $R/selected.json

# kernels at the selected settings (run name <K>_l<λ>[_m<μ>] -> kernel, lambda, mu).
# The runner writes its matrix through one Java ByteBuffer (at most 2 GB); the union on this corpus is 2.5 GB, so it
# runs in two halves of the union (rows in the same order), which are then joined into one run.
H=$R/union_parts
mkdir -p $H
head -1 $U > $H/h.tsv
n=$(( ($(wc -l < $U) - 1 + 1) / 2 ))
{ cat $H/h.tsv; tail -n +2 $U | head -n $n; } > $H/part1.tsv
{ cat $H/h.tsv; tail -n +2 $U | tail -n +$((n + 1)); } > $H/part2.tsv
for k in STK SSTK PTK; do
  name=$(.venv/bin/python -c "import json; print(json.load(open('$SEL'))['settings']['$k']['run'])")
  l=$(sed -E 's/^[A-Z]+_l([0-9.]+).*/\1/' <<< "$name")
  m=$(sed -nE 's/.*_m([0-9.]+)$/\1/p' <<< "$name"); m=${m:-0}
  [ -f $O/D_$k/meta.json ] && continue
  for p in 1 2; do
    [ -f $H/D_${k}_$p/meta.json ] && continue
    echo "== D $k ($name) part $p $(date +%T)"
    java -Xmx8g -Dorg.slf4j.simpleLogger.defaultLogLevel=error -cp "$CP" treekernel.RetrievalRunner \
      $TREES $H/part$p.tsv "$k" "$l" "$m" "$THREADS" $H/D_${k}_$p 2>&1 | grep -v "corpus methods scored" || true
    [ -f $H/D_${k}_$p/meta.json ]
  done
  cmp $H/D_${k}_1/logself.f64 $H/D_${k}_2/logself.f64
  cmp $H/D_${k}_1/corpus_ids.txt $H/D_${k}_2/corpus_ids.txt
  mkdir -p $O/D_$k
  cat $H/D_${k}_1/logk.f64 $H/D_${k}_2/logk.f64 > $O/D_$k/logk.f64
  cat $H/D_${k}_1/query_ids.txt $H/D_${k}_2/query_ids.txt > $O/D_$k/query_ids.txt
  cp $H/D_${k}_1/logself.f64 $H/D_${k}_1/corpus_ids.txt $O/D_$k/
  .venv/bin/python - $H/D_${k}_1/meta.json $H/D_${k}_2/meta.json $U > $O/D_$k/meta.json <<'EOF'
import json, sys
a, b = (json.load(open(p)) for p in sys.argv[1:3])
a.update(queries=sys.argv[3], n_queries=a["n_queries"] + b["n_queries"], evaluations=a["evaluations"] + b["evaluations"],
         wall_seconds=round(a["wall_seconds"] + b["wall_seconds"], 1), finished=b["finished"],
         parts=[a["queries"], b["queries"]])
print(json.dumps(a, indent=2))
EOF
  rm -r $H/D_${k}_1 $H/D_${k}_2
done

[ -f $O/codebert_zs/meta.json ] || .venv/bin/python embed/codebert.py run $O/codebert_zs \
  data/codebert/emb/zeroshot_e5.npy --trees $TREES --queries $U
[ -f $O/codebert_ft/meta.json ] || .venv/bin/python embed/codebert.py run $O/codebert_ft \
  "data/codebert/emb/fold{k}_e5.npy" --folds --trees $TREES --queries $U

if [ ! -f $O/bm25/meta.json ]; then
  echo "== BM25 $(date +%T)"
  scripts/es_start.sh > $R/es.log 2>&1 &
  ES=$!
  until curl -s localhost:9201 > /dev/null; do sleep 5; done
  curl -s "localhost:9201/_cluster/health/bcb_e5?wait_for_status=yellow&timeout=120s" > /dev/null || true
  curl -sf localhost:9201/bcb_e5 > /dev/null || { echo "index bcb_e5 missing"; kill $ES; exit 1; }
  .venv/bin/python -I bm25/run_bm25.py query bcb_e5 $U $O/bm25
  kill $ES; wait $ES || true
fi

# fusion at the selected kernels and weights: <obj>_<kernel>_<other>_{wsum,rrf}
.venv/bin/python - "$SEL" <<'EOF' > $R/fusion_jobs.txt
import json, sys
s = json.load(open(sys.argv[1]))
for name, f in s["fusion"].items():
    print(name, f["kernel"], "bm25" if f["other"] == "BM25" else "codebert_ft", f["w"])
EOF
while read -r name k other w; do
  [ -f $O/${name}_wsum/meta.json ] || .venv/bin/python exp_v2/eval/fusion.py $O/D_$k $O/$other $O/${name}_wsum --method wsum --w $w
  [ -f $O/${name}_rrf/meta.json ] || .venv/bin/python exp_v2/eval/fusion.py $O/D_$k $O/$other $O/${name}_rrf --method rrf
done < $R/fusion_jobs.txt

echo "== evaluate $(date +%T)"
for d in $P/seed*; do
  s=$(basename $d)
  SYN=""
  for t in T1 T2 VST3 ST3 MT3; do SYN="$SYN --syntactic $d/syntactic_$t.tsv:$t"; done
  for r in $O/*/; do
    r=${r%/}
    e=$R/$s/$(basename $r)/eval
    [ -f $e/summary.tsv ] || echo ".venv/bin/python exp_v2/eval/evaluate.py $r $SYN --functional $d/functional.tsv --ignore exp_v2/data/fp_copies.tsv --boot 0 --out $e"
  done
done | xargs -P 4 -I{} sh -c "{} > /dev/null"
echo "all done $(date +%T)"
