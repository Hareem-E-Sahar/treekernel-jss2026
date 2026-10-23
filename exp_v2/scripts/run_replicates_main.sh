#!/usr/bin/env bash
# exp_v2 secondary setting: the 10 replicate query sets on the main corpus (true positives only, data/trees_main/D.tsv),
# variant D, at the settings and fusion weights tuned on the corpus with false positives (exp_v2/tuning/selected.json).
# Runs of the frozen experiment (results/replicates/runs) made at exactly the selected setting, on the same query union
# and corpus, are linked read-only instead of recomputed (checked from their meta.json); BM25 and CodeBERT do not depend
# on the tuning. Everything else (STK at its new setting, every fusion) is computed here.
# usage: exp_v2/scripts/run_replicates_main.sh [threads]   -> exp_v2/results/main/{runs,seed<S>/<method>/eval}
set -euo pipefail
cd "$(dirname "$0")/../.."
if [ -z "${INHIBITED:-}" ]; then
  exec env INHIBITED=1 systemd-inhibit --what=sleep:idle:handle-lid-switch --who=treekernel \
    --why="exp_v2 replicates (main corpus)" "$0" "$@"
fi
THREADS=${1:-14}
CP=kernels/target/classes:$(cat kernels/classpath.txt)
TREES=data/trees_main/D.tsv
P=exp_v2/data/replicates
U=$P/union.tsv
R=exp_v2/results/main
O=$R/runs
F=results/replicates/runs
SEL=exp_v2/tuning/selected.json
mkdir -p $O
cmp -s $U data/pools/replicates/union.tsv || { echo "query union differs from the frozen experiment's"; exit 1; }
cp $SEL $R/selected.json

# kernels: link the frozen run if its kernel, lambda, mu, corpus and queries match the selection, else compute
for k in STK SSTK PTK; do
  name=$(.venv/bin/python -c "import json; print(json.load(open('$SEL'))['settings']['$k']['run'])")
  l=$(sed -E 's/^[A-Z]+_l([0-9.]+).*/\1/' <<< "$name")
  m=$(sed -nE 's/.*_m([0-9.]+)$/\1/p' <<< "$name"); m=${m:-0}
  [ -e $O/D_$k ] && continue
  if .venv/bin/python - $F/D_$k/meta.json "$k" "$l" "$m" <<'EOF'
import json, sys
from pathlib import Path
p, k, l, m = sys.argv[1:]
if not Path(p).exists():
    sys.exit(1)
x = json.load(open(p))
ok = (x["kernel"] == k and float(x["lambda"]) == float(l) and (k != "PTK" or float(x["mu"]) == float(m))
      and x["trees"].endswith("data/trees_main/D.tsv") and x["queries"].endswith("data/pools/replicates/union.tsv"))
sys.exit(0 if ok else 1)
EOF
  then
    ln -s "$(realpath $F/D_$k)" $O/D_$k
    echo "== D $k ($name): frozen run reused (same setting)"
  else
    echo "== D $k ($name) $(date +%T)"
    java -Xmx8g -Dorg.slf4j.simpleLogger.defaultLogLevel=error -cp "$CP" treekernel.RetrievalRunner \
      $TREES $U "$k" "$l" "$m" "$THREADS" $O/D_$k 2>&1 | grep -v "corpus methods scored" || true
    [ -f $O/D_$k/meta.json ]
  fi
done

# BM25 (index bcb_main) and CodeBERT (main-corpus embeddings) on the same union: not tuned, reused as they are
for r in bm25 codebert_zs codebert_ft; do
  [ -e $O/$r ] || ln -s "$(realpath $F/$r)" $O/$r
done

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

# evaluation: no false positives in this corpus, so nothing to ignore
echo "== evaluate $(date +%T)"
for d in $P/seed*; do
  s=$(basename $d)
  SYN=""
  for t in T1 T2 VST3 ST3 MT3; do SYN="$SYN --syntactic $d/syntactic_$t.tsv:$t"; done
  for r in $O/*; do
    [ -f $r/meta.json ] || continue
    e=$R/$s/$(basename $r)/eval
    [ -f $e/summary.tsv ] || echo ".venv/bin/python exp_v2/eval/evaluate.py $r $SYN --functional $d/functional.tsv --boot 0 --out $e"
  done
done | xargs -P 4 -I{} sh -c "{} > /dev/null"
echo "all done $(date +%T)"
