"""Hand-checked cases for ranking.evaluate (run: python eval/test_ranking.py)."""
import math
import numpy as np
from ranking import evaluate


def run(scores, rel):
    s = np.array(scores, float)
    r = np.array(rel, bool)
    return evaluate(s, np.ones(len(s), bool), r)[0]


def close(a, b):
    assert math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12), (a, b)


# no ties: relevant at ranks 1 and 3 of 5
m = run([.9, .8, .7, .6, .5], [1, 0, 1, 0, 0])
close(m["P@1"], 1); close(m["RR"], 1); close(m["AP"], (1 + 2 / 3) / 2)
close(m["AP@R"], 1 / 2); close(m["R-prec"], .5); close(m["P@5"], .4); close(m["mean_rank"], 2)

# all three tied and all relevant: perfect
m = run([1, 1, 1, .2], [1, 1, 1, 0])
close(m["AP"], 1); close(m["P@1"], 1); close(m["RR"], 1); close(m["mean_rank"], 2)

# one relevant tied with two others at the top: expected position 2, P@1 = 1/3
m = run([1, 1, 1, .2], [1, 0, 0, 0])
close(m["P@1"], 1 / 3); close(m["RR"], 1 / 2); close(m["AP"], 1 / 2); close(m["R@1"], 1 / 3)
close(m["AP@R"], 0)           # R = 1 and expected position 2 > R

# 2 relevant in a tie group of 4 at positions 2-5: expected positions 2 + {5/3, 10/3} - 1
m = run([.9, .5, .5, .5, .5], [0, 1, 1, 0, 0])
p1, p2 = 1 + 5 / 3, 1 + 10 / 3
close(m["AP"], (1 / p1 + 2 / p2) / 2); close(m["mean_rank"], 3.5)
close(m["P@1"], 0); close(m["R-prec"], (1 * 2 / 4) / 2)   # top 2: one slot of the group
print("all ranking tests passed")
