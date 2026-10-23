"""False positives that are exact copies of a true positive (exp_v2 design: ignored in scoring for that query).

usage: .venv/bin/python exp_v2/prep/fp_copies.py   -> exp_v2/data/fp_copies.tsv (query_id, fp_id)

Copy = identical source text after removing all whitespace. BigCloneBench judged these false positive for
some functionality while an identical method is a true positive, so counting them as non-relevant would
penalise retrieving an exact clone of the query. Listed for every true positive of the main corpus.
"""
import hashlib
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
tp = {line.split("\t", 1)[0] for line in list(open(ROOT / "data/trees_main/D.tsv"))[1:]}
h_tp, h_fp = defaultdict(list), defaultdict(list)
with open(ROOT / "data/trees_e5/source.tsv") as f:
    next(f)
    for line in f:
        p = line.rstrip("\n").split("\t")
        h = hashlib.sha1(re.sub(r"\s+", "", p[-1]).encode()).hexdigest()
        (h_tp if p[0] in tp else h_fp)[h].append(p[0])
pairs = sorted(((q, x) for h, qs in h_tp.items() if h in h_fp for q in qs for x in h_fp[h]), key=lambda r: (int(r[0]), int(r[1])))
out = ROOT / "exp_v2/data/fp_copies.tsv"
out.write_text("query_id\tfp_id\n" + "".join(f"{q}\t{x}\n" for q, x in pairs))
print(f"{len(pairs)} pairs, {len({q for q, _ in pairs})} queries, {len({x for _, x in pairs})} false positives -> {out}")
