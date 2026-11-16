"""Size x complexity quadrants for the response letter (R2-C4): MAP per method in four groups of eligible queries,
split at the median lines of code and the median McCabe complexity (small = LOC <= median, simple = McCabe <= median).

usage: .venv/bin/python exp_v3_all_queries/eval/quadrants.py
  -> exp_v3_all_queries/results/analysis/rq3_quadrants.tsv
       measure (mean5 = syntactic similarity, mean of the five types; functional), size, complexity, method, MAP,
       queries (type-queries for mean5), loc_median, cc_median
Plain values, no tests (as the rest of RQ3). A split at McCabe's limit of 10 is not used: its small-and-complex group
would hold 10 queries.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import RES, TYPES, METHODS, LABEL, load, point, query_attributes, write_tsv  # noqa: E402


def main():
    ev = {r: load(r)[0] for r in METHODS}
    eligible = set(ev["D_STK"]["functional"]["MAP"])
    attrs = {q: a for q, a in query_attributes().items() if q in eligible and a["cc"] is not None}
    loc_med = float(np.median([a["loc"] for a in attrs.values()]))
    cc_med = float(np.median([a["cc"] for a in attrs.values()]))
    cells = {}
    for q, a in attrs.items():
        cells.setdefault(("large" if a["loc"] > loc_med else "small", "complex" if a["cc"] > cc_med else "simple"),
                         set()).add(q)
    rows = []
    for ms in ("mean5", "functional"):
        for size in ("small", "large"):
            for cx in ("simple", "complex"):
                sub = cells[(size, cx)]
                n = (sum(len(set(ev["D_STK"][t]["MAP"]) & sub) for t in TYPES) if ms == "mean5"
                     else len(set(ev["D_STK"]["functional"]["MAP"]) & sub))
                for r in METHODS:
                    rows.append([ms, size, cx, LABEL[r], f"{point(ev[r], 'MAP', ms, subset=sub):.4f}", n,
                                 f"{loc_med:g}", f"{cc_med:g}"])
    write_tsv(RES / "analysis/rq3_quadrants.tsv",
              ["measure", "size", "complexity", "method", "MAP", "queries", "loc_median", "cc_median"], rows)
    print(f"medians: LOC {loc_med:g}, McCabe {cc_med:g}; quadrants written")


if __name__ == "__main__":
    main()
