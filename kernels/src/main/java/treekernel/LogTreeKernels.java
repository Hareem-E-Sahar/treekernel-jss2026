package treekernel;

import it.uniroma2.sag.kelp.data.representation.tree.TreeRepresentation;
import it.uniroma2.sag.kelp.data.representation.tree.node.TreeNode;
import it.uniroma2.sag.kelp.kernel.tree.TreeKernelUtils;
import gnu.trove.map.hash.TLongDoubleHashMap;

import java.util.*;

/**
 * Subset tree kernel (SSTK) and subtree kernel (STK) computed in log space, so that
 * values never overflow. KeLP computes them in 32-bit floats, and SSTK overflows to
 * Infinity on large methods (see third_party/README.md, item 4).
 *
 * Returns log K(a, b); a kernel value of 0 is returned as -Infinity.
 * Normalised similarity = exp(logK(a,b) - (logK(a,a) + logK(b,b)) / 2).
 *
 * Same definitions as KeLP's TreeKernelUtils.productionBasedDeltaFunction with leaves
 * included (the KeLP default). K(a,b) = sum over node pairs with identical productions
 * of Delta(n1, n2), where:
 *   - both nodes preterminal (all children are leaves):    Delta = lambda
 *   - otherwise Delta = lambda * product over children i of a factor f_i:
 *       children both internal, same production:  f = sigma + Delta(c1, c2)
 *       one child internal, the other a leaf:     f = sigma
 *       both children leaves:                     f = 1
 *       children both internal, different productions:
 *           SSTK (sigma = 1):   f = 1   (= 1 + 0; same as KeLP)
 *           STK, KELP mode:     f = 1   (KeLP leaves the product unchanged)
 *           STK, TEXTBOOK mode: f = 0   (the complete subtree is not shared)
 * sigma = 1 for SSTK and 0 for STK.
 */
public final class LogTreeKernels {

    public enum Kind { SSTK, STK_KELP, STK_TEXTBOOK }

    private LogTreeKernels() {}

    /** log K(a, b). Trees must have warmed caches (sorted production lists computed). */
    public static double logKernel(TreeRepresentation a, TreeRepresentation b, Kind kind, double lambda) {
        double logLambda = Math.log(lambda);
        int sigma = kind == Kind.SSTK ? 1 : 0;
        boolean mismatchKills = kind == Kind.STK_TEXTBOOK;
        Memo memo = MEMO.get();
        memo.reset(a.getMaxId(), b.getMaxId());

        // Merge the two production-sorted node lists (as KeLP's findCommonNodesByProduction),
        // accumulating log-sum-exp of Delta over all pairs with identical productions.
        List<TreeNode> na = a.getOrderedNodeSetByProduction(), nb = b.getOrderedNodeSetByProduction();
        double max = Double.NEGATIVE_INFINITY, sum = 0;   // sum of exp(term - max)
        int i = 0, j = 0;
        while (i < na.size() && j < nb.size()) {
            char[] pi = na.get(i).getProduction(), pj = nb.get(j).getProduction();
            int cmp = TreeKernelUtils.compareTo(pi, pj);
            if (cmp < 0) { i++; continue; }
            if (cmp > 0) { j++; continue; }
            int iEnd = i, jEnd = j;
            while (iEnd < na.size() && Arrays.equals(na.get(iEnd).getProduction(), pi)) iEnd++;
            while (jEnd < nb.size() && Arrays.equals(nb.get(jEnd).getProduction(), pj)) jEnd++;
            for (int x = i; x < iEnd; x++) {
                for (int y = j; y < jEnd; y++) {
                    double d = logDelta(na.get(x), nb.get(y), logLambda, sigma, mismatchKills, memo);
                    if (d == Double.NEGATIVE_INFINITY) continue;
                    if (d > max) {
                        sum = sum * Math.exp(max - d) + 1;   // rescale the running sum to the new max
                        max = d;
                    } else {
                        sum += Math.exp(d - max);
                    }
                }
            }
            i = iEnd;
            j = jEnd;
        }
        return max == Double.NEGATIVE_INFINITY ? Double.NEGATIVE_INFINITY : max + Math.log(sum);
    }

    /** Normalised similarity in [0, 1] from three log-kernel values. */
    public static double normalise(double logAB, double logAA, double logBB) {
        if (logAB == Double.NEGATIVE_INFINITY) return 0;
        return Math.exp(logAB - 0.5 * (logAA + logBB));
    }

    private static double logDelta(TreeNode n1, TreeNode n2, double logLambda, int sigma,
                                   boolean mismatchKills, Memo memo) {
        double cached = memo.get(n1.getId(), n2.getId());
        if (!Double.isNaN(cached)) return cached;

        double result;
        if (n1.isPreterminal() && n2.isPreterminal()) {
            result = logLambda;
        } else {
            result = logLambda;
            List<TreeNode> c1 = n1.getChildren(), c2 = n2.getChildren();
            for (int i = 0; i < c1.size(); i++) {
                TreeNode x = c1.get(i), y = c2.get(i);
                boolean xi = x.hasChildren(), yi = y.hasChildren();
                if (xi && yi) {
                    if (Arrays.equals(x.getProduction(), y.getProduction())) {
                        double d = logDelta(x, y, logLambda, sigma, mismatchKills, memo);
                        // log(sigma + Delta): sigma = 1 -> softplus(d); sigma = 0 -> d
                        result += sigma == 1 ? softplus(d) : d;
                    } else if (mismatchKills) {
                        result = Double.NEGATIVE_INFINITY;
                    }
                    // otherwise factor 1: SSTK (1 + 0) and KeLP's STK
                } else if (xi != yi) {
                    if (sigma == 0) result = Double.NEGATIVE_INFINITY;   // factor sigma = 0
                    // sigma = 1: factor 1
                }
                // both leaves: factor 1
                if (result == Double.NEGATIVE_INFINITY) break;
            }
        }
        memo.put(n1.getId(), n2.getId(), result);
        return result;
    }

    /**
     * Unique 64-bit key for a node pair, scrambled with MurmurHash3's fmix64 (a bijection,
     * so keys stay unique). Trove hashes a long by XOR-ing its halves, which for the plain
     * key (i << 32) | j gives i ^ j: every self pair (i, i) would collide on 0.
     */
    static long pairKey(int i, int j) {
        long k = ((long) i << 32) | (j & 0xffffffffL);
        k ^= k >>> 33;
        k *= 0xff51afd7ed558ccdL;
        k ^= k >>> 33;
        k *= 0xc4ceb9fe1a85ec53L;
        k ^= k >>> 33;
        return k;
    }

    /** log(1 + e^x), stable for all x (including -Infinity -> 0). */
    static double softplus(double x) {
        if (x == Double.NEGATIVE_INFINITY) return 0;
        return x > 0 ? x + Math.log1p(Math.exp(-x)) : Math.log1p(Math.exp(x));
    }

    private static final ThreadLocal<Memo> MEMO = ThreadLocal.withInitial(Memo::new);

    /**
     * Per-thread memo of computed log-deltas, reused across evaluations. A dense table
     * (cleared in O(1) with a generation stamp) for normal pairs; a hash map for giant pairs.
     */
    private static final class Memo {
        private static final int DENSE_LIMIT = 4_000_000;   // entries: 32 MB values + 16 MB stamps
        private double[] values = new double[0];
        private int[] stamps = new int[0];
        private int generation = 0;
        private int width;
        private boolean dense;
        private final TLongDoubleHashMap sparse = new TLongDoubleHashMap();

        void reset(int maxIdA, int maxIdB) {
            width = maxIdB + 1;
            long size = (long) (maxIdA + 1) * width;
            dense = size <= DENSE_LIMIT;
            if (dense) {
                if (values.length < size) {
                    int cap = (int) Math.min(DENSE_LIMIT, Math.max(size, 2L * values.length));
                    values = new double[cap];
                    stamps = new int[cap];
                    generation = 0;
                }
                generation++;
                if (generation == Integer.MAX_VALUE) {   // stamps would wrap: clear once
                    Arrays.fill(stamps, 0);
                    generation = 1;
                }
            }
            sparse.clear();
            if (sparse.capacity() > 1 << 20) sparse.compact();   // don't keep giant-pair memory
        }

        double get(int i, int j) {
            if (dense) {
                int k = i * width + j;
                return stamps[k] == generation ? values[k] : Double.NaN;
            }
            long key = LogTreeKernels.pairKey(i, j);
            return sparse.containsKey(key) ? sparse.get(key) : Double.NaN;
        }

        void put(int i, int j, double v) {
            if (dense) {
                int k = i * width + j;
                values[k] = v;
                stamps[k] = generation;
            } else {
                sparse.put(LogTreeKernels.pairKey(i, j), v);
            }
        }
    }
}
