"""Tie-aware retrieval metrics for one query (see evaluate.py for the tie convention)."""
import numpy as np


def evaluate(s, cand, rel):
    """s: scores over the corpus; cand: bool mask of candidates; rel: bool mask of relevant (subset of cand)."""
    sc, rl = s[cand], rel[cand]
    n, R = len(sc), int(rl.sum())
    order = np.argsort(-sc, kind="stable")
    sc, rl = sc[order], rl[order]
    # tie groups over the sorted scores
    starts = np.flatnonzero(np.r_[True, sc[1:] != sc[:-1]])
    sizes = np.diff(np.r_[starts, n])
    hits = np.add.reduceat(rl.astype(np.int64), starts)
    a = starts + 1                                  # 1-based start of each group
    # expected positions of relevant items
    pos = []
    for g in np.flatnonzero(hits):
        m, h = sizes[g], hits[g]
        pos.extend(a[g] - 1 + np.arange(1, h + 1) * (m + 1) / (h + 1))
    pos = np.array(pos)

    def expected_in_top(k):
        overlap = np.clip(k - a + 1, 0, sizes)
        return float((hits * overlap / sizes).sum())

    prec_at = np.arange(1, R + 1) / pos             # precision at each relevant item (sorted positions)
    m = {f"P@{k}": expected_in_top(k) / k for k in (1, 5, 10)}
    m.update({f"R@{k}": expected_in_top(k) / R for k in (1, 5, 10, 100)})
    m["R-prec"] = expected_in_top(R) / R
    m["RR"] = 1 / pos[0]
    m["AP"] = float(prec_at.mean())
    m["AP@R"] = float(prec_at[pos <= R].sum() / R)
    m["median_rank"] = float(np.median(pos))
    m["mean_rank"] = float(pos.mean())
    m["median_rank_pct"] = float(np.median(pos) / n * 100)
    return m, R, n
