"""Size and complexity analysis: aggregate exp_v2/scripts/run_size_complexity.sh.

usage: .venv/bin/python exp_v2/eval/size_complexity.py
  -> exp_v2/results/size_complexity/{per_seed.tsv, pooled.tsv, interaction.tsv, tables.md}

Groups (exp_v2/prep/sample_size_complexity.py): small (LOC <= 6), large (LOC >= 10), low (McCabe <= 10),
high (McCabe > 10). Size and complexity are correlated (every small method has McCabe <= 10), so complexity is also
compared within large methods: low_large / high_large = the low / high group's queries with LOC >= 10 (a view of the
same sampled queries, no extra sampling).
Metrics: MAP, MAP@R, MRR, nP@5, nP@10 (micro); measures T1..MT3, mean5 (mean of the five types), functional.
1. per_seed.tsv: value per (group, seed, method, measure, metric); mean ± SD over the 10 seeds in tables.md. Sets whose
   pool has at most 100 queries are the whole pool in every seed (SD 0; marked "all" in tables.md).
2. pooled.tsv: value over each group's distinct queries (all seeds pooled).
3. interaction.tsv: does a method's advantage depend on the group? D = (A - B on group 1) - (A - B on group 2) over the
   pooled queries; 95% CI from a paired bootstrap that resamples functionalities jointly for both groups (a
   functionality can have queries in both), 2,000 resamples, seed 20261022. A query in several functionalities is
   assigned to its lowest functionality id. mean5: the mean of the five types' D.
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "exp_v2/data/size_complexity"
R = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "exp_v2/results/size_complexity"   # argument: for testing
TYPES = ["T1", "T2", "VST3", "ST3", "MT3"]
MEASURES = TYPES + ["mean5", "functional"]
METRICS = {"MAP": "AP", "MAP@R": "AP@R", "MRR": "RR", "nP@5": "nP@5", "nP@10": "nP@10"}
METHODS = [("STK", "D_STK"), ("SSTK", "D_SSTK"), ("PTK", "D_PTK"), ("BM25", "bm25"), ("CodeBERT zs", "codebert_zs"),
           ("CodeBERT ft", "codebert_ft")]
SEEDS = sorted((p.name for p in P.glob("seed*")), key=lambda s: int(s[4:]))
GROUPS = ["small", "large", "low", "high", "low_large", "high_large"]
CONTRASTS = [("small", "large"), ("low", "high"), ("low_large", "high_large")]
PAIRS = [(k, b) for k in ("PTK", "STK", "SSTK") for b in ("BM25", "CodeBERT ft")] + [("CodeBERT ft", "BM25")]
LOC = {r["function_id"]: int(r["loc"]) for r in csv.DictReader(open(ROOT / "exp_v2/data/size_complexity.tsv"), delimiter="\t")}
WHOLE = {(r["group"], r["set"]) for r in csv.DictReader(open(P / "pools.tsv"), delimiter="\t") if r["sampled"] != "yes"}

# per-query values: vals[group][seed][method][type][metric][query]; pooled[group][method][type][metric][query]
vals = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))))
pooled = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict))))
cluster = {}
for g in ("small", "large", "low", "high"):
    for s in SEEDS:
        for lab, d in METHODS:
            for r in csv.DictReader(open(R / s / g / d / "eval/per_query.tsv"), delimiter="\t"):
                t, q = r["type"], r["function_id"]
                cluster[q] = min(int(x) for x in r["functionality_ids"].split(","))
                targets = [g] + ([f"{g}_large"] if g in ("low", "high") and LOC[q] >= 10 else [])
                for gg in targets:
                    for m, col in METRICS.items():
                        v = float(r[col])
                        vals[gg][s][lab][t][m][q] = v
                        old = pooled[gg][lab][t][m].setdefault(q, v)
                        assert abs(old - v) < 1e-9, (gg, lab, t, q, m)


def mean_of(d, measure, metric):
    types = TYPES if measure == "mean5" else [measure]
    return float(np.mean([np.mean(list(d[t][metric].values())) for t in types]))


# ---- 1. per seed
with open(R / "per_seed.tsv", "w") as o:
    o.write("group\tseed\tmethod\tmeasure\tmetric\tvalue\tn_queries\n")
    for g in GROUPS:
        for s in SEEDS:
            for lab, _ in METHODS:
                for ms in MEASURES:
                    for m in METRICS:
                        n = sum(len(vals[g][s][lab][t][m]) for t in (TYPES if ms == "mean5" else [ms]))
                        o.write(f"{g}\t{s[4:]}\t{lab}\t{ms}\t{m}\t{mean_of(vals[g][s][lab], ms, m):.6f}\t{n}\n")

# ---- 2. pooled
with open(R / "pooled.tsv", "w") as o:
    o.write("group\tmethod\tmeasure\tmetric\tvalue\tn_queries\tn_functionalities\n")
    for g in GROUPS:
        for lab, _ in METHODS:
            for ms in MEASURES:
                for m in METRICS:
                    qs = [q for t in (TYPES if ms == "mean5" else [ms]) for q in pooled[g][lab][t][m]]
                    o.write(f"{g}\t{lab}\t{ms}\t{m}\t{mean_of(pooled[g][lab], ms, m):.6f}\t{len(qs)}\t"
                            f"{len({cluster[q] for q in qs})}\n")

# ---- 3. interaction
CL = sorted(set(cluster.values()))
CIX = {c: i for i, c in enumerate(CL)}
rng = np.random.default_rng(20261022)
BOOT = 2000
W = rng.multinomial(len(CL), np.full(len(CL), 1 / len(CL)), size=BOOT).astype(float)   # cluster counts per resample


def diff_stats(g, a, b, t, m):
    """Point estimate of mean(A - B) on group g and its bootstrap replicates (shared cluster weights W)."""
    S, N = np.zeros(len(CL)), np.zeros(len(CL))
    for q, va in pooled[g][a][t][m].items():
        c = CIX[cluster[q]]
        S[c] += va - pooled[g][b][t][m][q]
        N[c] += 1
    with np.errstate(invalid="ignore", divide="ignore"):
        return S.sum() / N.sum(), (W @ S) / (W @ N)


rows = []
for g1, g2 in CONTRASTS:
    for a, b in PAIRS:
        for ms in MEASURES:
            for m in METRICS:
                types = TYPES if ms == "mean5" else [ms]
                est, bs, d1s, d2s = 0.0, np.zeros(BOOT), 0.0, 0.0
                for t in types:
                    e1, b1 = diff_stats(g1, a, b, t, m)
                    e2, b2 = diff_stats(g2, a, b, t, m)
                    d1s += e1 / len(types)
                    d2s += e2 / len(types)
                    est += (e1 - e2) / len(types)
                    bs += (b1 - b2) / len(types)
                bs = bs[np.isfinite(bs)]          # a resample can miss every query of a small group
                lo, hi = np.percentile(bs, [2.5, 97.5])
                rows.append((g1, g2, a, b, ms, m, d1s, d2s, est, lo, hi, len(bs)))
with open(R / "interaction.tsv", "w") as o:
    o.write("group1\tgroup2\ta\tb\tmeasure\tmetric\tdiff_group1\tdiff_group2\tinteraction\tci_low\tci_high\tvalid_resamples\n")
    for r in rows:
        o.write("\t".join(f"{x:.4f}" if isinstance(x, float) else str(x) for x in r) + "\n")

# ---- tables.md
L = ["# Size and complexity", "",
     "Corpus with false positives; variant D at the tuned settings; 10 seeds. Groups: small LOC <= 6, large LOC >= 10, "
     "low McCabe <= 10, high McCabe > 10 (Checkstyle); low_large / high_large = low / high queries with LOC >= 10.", ""]
for metric_view, cols in (("MAP per type, mean5, MAP@R (functional)", [(t, "MAP") for t in TYPES + ["mean5"]] + [("functional", "MAP@R")]),
                          ("Mean over the five types (RQ1) and functional (RQ2): nP@5, nP@10, MRR",
                           [("mean5", x) for x in ("nP@5", "nP@10", "MRR")] + [("functional", x) for x in ("nP@5", "nP@10", "MRR")])):
    L += [f"## Mean ± SD over the seeds: {metric_view}", ""]
    ps = defaultdict(list)
    for r in csv.DictReader(open(R / "per_seed.tsv"), delimiter="\t"):
        ps[(r["group"], r["method"], r["measure"], r["metric"])].append(float(r["value"]))
    L += ["| Group | Method | " + " | ".join(f"{ms} {m}" for ms, m in cols) + " |", "|---" * (len(cols) + 2) + "|"]
    for g in GROUPS:
        for lab, _ in METHODS:
            cells = []
            for ms, m in cols:
                v = np.array(ps[(g, lab, ms, m)])
                whole = ms != "mean5" and (g.split("_")[0], ms) in WHOLE and "_" not in g
                cells.append(f"{v.mean():.3f} ± {v.std(ddof=1):.3f}" + (" (all)" if whole else ""))
            L.append(f"| {g} | {lab} | " + " | ".join(cells) + " |")
    L.append("")
nq = {}
for r in csv.DictReader(open(R / "pooled.tsv"), delimiter="\t"):
    if r["method"] == "PTK" and r["metric"] == "MAP":
        nq[(r["group"], r["measure"])] = (r["n_queries"], r["n_functionalities"])
L += ["## Distinct queries per group (functionalities)", "",
      "| Group | " + " | ".join(MEASURES) + " |", "|---" * (len(MEASURES) + 1) + "|"]
L += [f"| {g} | " + " | ".join(f"{nq[(g, ms)][0]} ({nq[(g, ms)][1]})" for ms in MEASURES) + " |" for g in GROUPS]
L += ["", "## Interaction: does A's advantage over B change between the groups?", "",
      "D = (A − B on group 1) − (A − B on group 2), pooled distinct queries; * = 95% CI excludes 0 (bootstrap over "
      "functionalities, jointly for both groups). MAP for the types and mean5, MAP@R for functional.", "",
      "| Group 1 vs 2 | A | B | Measure | A − B (1) | A − B (2) | D | 95% CI |", "|---|---|---|---|---|---|---|---|"]
for g1, g2, a, b, ms, m, d1, d2, est, lo, hi, nb in rows:
    if m == ("MAP@R" if ms == "functional" else "MAP"):
        L.append(f"| {g1} vs {g2} | {a} | {b} | {ms} | {d1:+.3f} | {d2:+.3f} | {est:+.3f}{' *' if lo > 0 or hi < 0 else ''} | "
                 f"{lo:+.3f} to {hi:+.3f} |")
(R / "tables.md").write_text("\n".join(L) + "\n")
print(f"{R}/tables.md")
