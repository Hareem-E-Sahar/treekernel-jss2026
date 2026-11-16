"""Evaluate one RetrievalRunner output directory: exp_v3_all_queries copy of exp_v2/eval/evaluate.py.

exp_v3 changes (revision_plan.md, R1-C3, label-noise sensitivity; everything else unchanged):
  - --ignore may be given several times (the lists are combined);
  - --drop-fp: every BigCloneBench false positive (a corpus method without a true-positive functionality) is removed
    from every ranking, as if unjudged; the other extreme of the default (false positives count as non-relevant).

exp_v2 notes:

Differences from eval/evaluate.py (everything else is unchanged):
  - the score matrix is memory-mapped and read one query row at a time (runs on the 72,782-method corpus
    are 2.5 GB and more);
  - --ignore FILE (query_id, fp_id): methods removed from that query's ranking before scoring, as the
    query's other same-task methods are for RQ1 (exp_v2/data/fp_copies.tsv: false positives that are
    exact copies of the query).


usage: evaluate.py RUN_DIR [--syntactic FILE[:TYPE] ...] [--functional FILE ...] [--ignore FILE]
                   [--bcb data/full_bcb] [--boot 1000] [--out RUN_DIR/eval]

--syntactic  RQ1 / tuning ground truth. The clone type comes from the file's `clone_type`
             column (tuning.tsv) or from :TYPE (e.g. data/pools/syntactic_T1.tsv:T1).
             Relevant = the query's clones of that type. Removed from the ranking = the
             query's other same-task methods. Candidates = relevant + methods of other tasks.
--functional RQ2 ground truth. Relevant = every method sharing a task with the query.

Scores: exp(log K(q,c) - (log K(q,q) + log K(c,c)) / 2), i.e. the normalised kernel.

Ties (evaluation_design §2.1): tied items are treated by their expected positions under a
random order within the tie. Cut-off metrics (P@k, Recall@k, R-precision) use the expected
number of relevant items above the cut-off; rank metrics place the j-th of h relevant items
in a tie group of m items starting at position a at a - 1 + j(m+1)/(h+1), its expected
position. Mean rank therefore equals the average-of-tied-positions rank.

Writes to --out:
  per_query.tsv  one row per (query set, type, query): every metric, R, candidates, tasks, category
  summary.tsv    per (set, type, averaging, metric): value, bootstrap 95% CI, queries, tasks
                 averaging = micro (mean over queries) or macro (over represented tasks; a
                 query in two tasks counts ½ in each); also per category (pattern/name).
                 For tuning-style sets with several types, type `mean5` = mean over the types.
"""
import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "eval"))
from ranking import evaluate as _evaluate  # noqa: E402

TYPES = ["T1", "T2", "VST3", "ST3", "MT3"]
PATTERN_TASKS = {7, 12, 14, 20, 26, 41}   # BCB search by code pattern (evaluation_design §4.8)
METRICS = ["P@1", "P@5", "P@10", "nP@5", "nP@10", "R@1", "R@5", "R@10", "R@100", "R-prec", "RR", "AP", "AP@R",
           "median_rank", "mean_rank", "median_rank_pct"]


def evaluate(s, cand, rel):
    """ranking.evaluate plus normalised precision: nP@k = (expected) hits in the top k / min(k, R),
    i.e. P@k against the best a query with fewer than k relevant methods can reach."""
    m, R, n = _evaluate(s, cand, rel)
    for k in (5, 10):
        m[f"nP@{k}"] = m[f"P@{k}"] * k / min(k, R)
    return m, R, n

ap = argparse.ArgumentParser()
ap.add_argument("run_dir", type=Path)
ap.add_argument("--syntactic", action="append", default=[])
ap.add_argument("--functional", action="append", default=[])
ap.add_argument("--bcb", type=Path, default=ROOT / "data/full_bcb")
ap.add_argument("--ignore", type=Path, action="append", default=[])
ap.add_argument("--drop-fp", action="store_true")
ap.add_argument("--boot", type=int, default=1000)
ap.add_argument("--seed", type=int, default=20261016)
ap.add_argument("--out", type=Path)
args = ap.parse_args()
out = args.out or args.run_dir / "eval"
out.mkdir(parents=True, exist_ok=True)

# ---------- run
qids = [int(x) for x in (args.run_dir / "query_ids.txt").read_text().split()]
cids = np.array([int(x) for x in (args.run_dir / "corpus_ids.txt").read_text().split()])
nQ, nC = len(qids), len(cids)
logk = np.memmap(args.run_dir / "logk.f64", dtype="<f8", mode="r", shape=(nQ, nC))
logself = np.fromfile(args.run_dir / "logself.f64", dtype="<f8")
col = {c: i for i, c in enumerate(cids.tolist())}
qrow = {q: i for i, q in enumerate(qids)}
assert np.isfinite(logself).all(), "non-finite self-similarity"

# ---------- ground truth
tasks = defaultdict(set)
for r in csv.DictReader(open(args.bcb / "tp_functionalities.tsv"), delimiter="\t"):
    tasks[int(r["function_id"])].add(int(r["functionality_id"]))
task_cols = defaultdict(list)
for c in cids.tolist():
    for t in tasks[c]:
        task_cols[t].append(col[c])
partners = {t: defaultdict(set) for t in TYPES}
for r in csv.DictReader(open(args.bcb / "syntactic_clone_pairs.tsv"), delimiter="\t"):
    a, b = int(r["function_id_one"]), int(r["function_id_two"])
    partners[r["clone_type"]][a].add(b)
    partners[r["clone_type"]][b].add(a)


ignored = defaultdict(list)
for path in args.ignore:
    for r in csv.DictReader(open(path), delimiter="\t"):
        if int(r["fp_id"]) in col:
            ignored[int(r["query_id"])].append(col[int(r["fp_id"])])
is_fp = np.array([not tasks[c] for c in cids.tolist()])


def scores(q):
    i = qrow[q]
    s = np.exp(np.asarray(logk[i]) - 0.5 * (logself[col[q]] + logself))
    return s


rows = []   # (set, type, query, R, n, tasks, category, metrics)


def category(q):
    return "pattern" if tasks[q] & PATTERN_TASKS else "name"


def same_task_mask(q):
    mask = np.zeros(nC, bool)
    for t in tasks[q]:
        mask[task_cols[t]] = True
    return mask


for spec in args.syntactic:
    path, _, fixed_type = spec.partition(":")
    name = Path(path).stem
    for r in csv.DictReader(open(path), delimiter="\t"):
        q = int(r["function_id"])
        t = r.get("clone_type") or fixed_type
        assert t in TYPES, spec
        rel = np.zeros(nC, bool)
        rel[[col[p] for p in partners[t][q] if p in col]] = True
        if not rel.any():
            print(f"warning: {name} {t} query {q} has no {t} clone in the corpus; skipped", file=sys.stderr)
            continue
        cand = ~same_task_mask(q) | rel
        cand[col[q]] = False
        cand[ignored[q]] = False
        if args.drop_fp:
            cand[is_fp] = False
        m, R, n = evaluate(scores(q), cand, rel)
        rows.append((name, t, q, R, n, tasks[q], category(q), m))

for path in args.functional:
    name = Path(path).stem
    for r in csv.DictReader(open(path), delimiter="\t"):
        q = int(r["function_id"])
        rel = same_task_mask(q)
        rel[col[q]] = False
        cand = np.ones(nC, bool)
        cand[col[q]] = False
        cand[ignored[q]] = False
        if args.drop_fp:
            cand[is_fp] = False
        m, R, n = evaluate(scores(q), cand, rel)
        rows.append((name, "functional", q, R, n, tasks[q], category(q), m))

with open(out / "per_query.tsv", "w") as o:
    o.write("set\ttype\tfunction_id\tR\tn_candidates\tfunctionality_ids\tcategory\t" + "\t".join(METRICS) + "\n")
    for name, t, q, R, n, ts, cat, m in rows:
        o.write(f"{name}\t{t}\t{q}\t{R}\t{n}\t{','.join(map(str, sorted(ts)))}\t{cat}\t"
                + "\t".join(f"{m[k]:.6g}" for k in METRICS) + "\n")

# ---------- aggregation
rng = np.random.default_rng(args.seed)


def micro(vals, idx=None):
    return float(np.mean(vals if idx is None else vals[idx]))


def macro(vals, qtasks, idx=None):
    idx = np.arange(len(vals)) if idx is None else idx
    per_task = defaultdict(lambda: [0.0, 0.0])      # task -> [weighted sum, weight]
    for i in idx:
        w = 1 / len(qtasks[i])
        for t in qtasks[i]:
            per_task[t][0] += w * vals[i]
            per_task[t][1] += w
    return float(np.mean([s / w for s, w in per_task.values()]))


def ci(fn, n):
    """Percentile bootstrap over queries."""
    if args.boot <= 0:
        return math.nan, math.nan
    b = [fn(rng.integers(0, n, n)) for _ in range(args.boot)]
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


summary = []
groups = defaultdict(list)
for row in rows:
    groups[(row[0], row[1])].append(row)
for (name, t), rs in groups.items():
    qtasks = [r[5] for r in rs]
    for cat in ["all", "pattern", "name"]:
        sel = [i for i, r in enumerate(rs) if cat == "all" or r[6] == cat]
        if not sel:
            continue
        sub_tasks = [qtasks[i] for i in sel]
        for metric in METRICS:
            vals = np.array([rs[i][7][metric] for i in sel])
            boot = args.boot if cat == "all" else 0
            for avg, fn in (("micro", lambda idx=None, v=vals: micro(v, idx)),
                            ("macro", lambda idx=None, v=vals, qt=sub_tasks: macro(v, qt, idx))):
                lo, hi = ci(fn, len(vals)) if boot else (math.nan, math.nan)
                summary.append((name, t, cat, avg, metric, fn(), lo, hi, len(vals),
                                len(set().union(*sub_tasks))))

# mean over the five clone types (tuning objective) for sets that contain several types
by_set = defaultdict(dict)
for name, t, cat, avg, metric, v, lo, hi, nq, nt in summary:
    if cat == "all" and t in TYPES:
        by_set[(name, avg, metric)][t] = v
for (name, avg, metric), d in by_set.items():
    if len(d) == len(TYPES):
        summary.append((name, "mean5", "all", avg, metric, float(np.mean(list(d.values()))),
                        math.nan, math.nan, sum(1 for r in rows if r[0] == name), math.nan))

with open(out / "summary.tsv", "w") as o:
    o.write("set\ttype\tcategory\taveraging\tmetric\tvalue\tci_low\tci_high\tn_queries\tn_tasks\n")
    for r in summary:
        o.write("\t".join(f"{x:.6g}" if isinstance(x, float) else str(x) for x in r) + "\n")
meta = json.loads((args.run_dir / "meta.json").read_text())
(out / "eval_meta.json").write_text(json.dumps({"run": str(args.run_dir), "run_meta": meta,
    "syntactic": args.syntactic, "functional": args.functional, "ignore": str(args.ignore) if args.ignore else None,
    "bootstrap": args.boot,
    "seed": args.seed}, indent=2))
print(f"{len(rows)} query evaluations -> {out}")
