package treekernel;

import gnu.trove.map.hash.TLongDoubleHashMap;
import it.uniroma2.sag.kelp.data.representation.tree.TreeRepresentation;
import it.uniroma2.sag.kelp.data.representation.tree.node.TreeNode;

import java.util.Arrays;
import java.util.List;

/**
 * KeLP's Partial Tree Kernel (Moschitti 2006), ported to double precision.
 *
 * KeLP's PartialTreeKernel computes in 32-bit floats and overflows (Infinity, then NaN
 * from Infinity - Infinity in the dynamic programme) on large methods when lambda and mu
 * are large, e.g. a 983-node method at lambda = mu = 0.8. This port follows KeLP's
 * evaluateKernelNotNormalize / ptkDeltaFunction / stringKernelDeltaFunction exactly,
 * with maxSubseqLeng = unlimited (KeLP's default):
 *
 *   K(a,b) = sum over node pairs with equal labels of Delta(n1, n2)
 *   Delta(n1,n2) = 0                                     if labels differ
 *                = mu * lambda^2 * terminalFactor        if either node has no children
 *                = mu * (lambda^2 + SK(children1, children2))   otherwise
 *   SK = string-kernel recursion over child sequences with decay lambda (KeLP's DP/DPS).
 *
 * Unlike KeLP, it never materialises the list of node pairs and sizes its tables per
 * thread on demand. Not thread-safe per instance; use one instance per thread.
 */
public final class PartialTreeKernelDouble {

    private static final int DENSE_LIMIT = 4_000_000;

    private final double lambda, lambda2, mu, terminalFactor;

    // memo of Delta values: dense table with generation stamps, or a primitive hash map
    private double[] memoValues = new double[0];
    private int[] memoStamps = new int[0];
    private int generation = 0;
    private int width;
    private boolean dense;
    private final TLongDoubleHashMap sparse = new TLongDoubleHashMap();

    // per-recursion-depth DP buffers, grown on demand
    private double[][] dpBuf = new double[0][];
    private double[][] dpsBuf = new double[0][];
    private double[][] kmBuf = new double[0][];
    private int depth = 0;

    public PartialTreeKernelDouble(double lambda, double mu, double terminalFactor) {
        this.lambda = lambda;
        this.lambda2 = lambda * lambda;
        this.mu = mu;
        this.terminalFactor = terminalFactor;
    }

    /** K(a, b). Trees must have warmed caches (label-sorted node lists computed). */
    public double kernel(TreeRepresentation a, TreeRepresentation b) {
        resetMemo(a.getMaxId(), b.getMaxId());
        List<TreeNode> na = a.getOrderedNodeSetByLabel(), nb = b.getOrderedNodeSetByLabel();
        double k = 0;
        int i = 0, j = 0;
        while (i < na.size() && j < nb.size()) {
            String li = na.get(i).getContent().getTextFromData();
            String lj = nb.get(j).getContent().getTextFromData();
            int cmp = li.compareTo(lj);
            if (cmp < 0) { i++; continue; }
            if (cmp > 0) { j++; continue; }
            int iEnd = i, jEnd = j;
            while (iEnd < na.size() && na.get(iEnd).getContent().getTextFromData().equals(li)) iEnd++;
            while (jEnd < nb.size() && nb.get(jEnd).getContent().getTextFromData().equals(lj)) jEnd++;
            for (int x = i; x < iEnd; x++) {
                for (int y = j; y < jEnd; y++) k += delta(na.get(x), nb.get(y));
            }
            i = iEnd;
            j = jEnd;
        }
        return k;
    }

    private double delta(TreeNode nx, TreeNode nz) {
        double cached = memoGet(nx.getId(), nz.getId());
        if (!Double.isNaN(cached)) return cached;
        double result;
        if (!nx.getContent().getTextFromData().equals(nz.getContent().getTextFromData())) {
            result = 0;
        } else if (nx.getNoOfChildren() == 0 || nz.getNoOfChildren() == 0) {
            result = mu * lambda2 * terminalFactor;
        } else {
            result = mu * (lambda2 + stringKernel(nx.getChildren(), nz.getChildren()));
        }
        memoPut(nx.getId(), nz.getId(), result);
        return result;
    }

    /** KeLP's stringKernelDeltaFunction, in double precision. */
    private double stringKernel(List<TreeNode> sx, List<TreeNode> sz) {
        int n = sx.size(), m = sz.size();
        int w = m + 1;
        ensureBuffers(depth, (n + 1) * w, Math.min(n, m) + 1);
        double[] dps = dpsBuf[depth], dp = dpBuf[depth], km = kmBuf[depth];
        depth++;
        int p = Math.min(n, m);

        String[] lx = new String[n], lz = new String[m];
        for (int i = 0; i < n; i++) lx[i] = sx.get(i).getContent().getTextFromData();
        for (int j = 0; j < m; j++) lz[j] = sz.get(j).getContent().getTextFromData();

        km[0] = 0;
        for (int i = 1; i <= n; i++) {
            for (int j = 1; j <= m; j++) {
                if (lx[i - 1].equals(lz[j - 1])) {
                    dps[i * w + j] = delta(sx.get(i - 1), sz.get(j - 1));
                    km[0] += dps[i * w + j];
                } else {
                    dps[i * w + j] = 0;
                }
            }
        }
        for (int l = 1; l < p; l++) {
            km[l] = 0;
            for (int j = 0; j <= m; j++) dp[(l - 1) * w + j] = 0;
            for (int i = 0; i <= n; i++) dp[i * w + (l - 1)] = 0;
            for (int i = l; i <= n; i++) {
                for (int j = l; j <= m; j++) {
                    dp[i * w + j] = dps[i * w + j] + lambda * dp[(i - 1) * w + j]
                        + lambda * dp[i * w + (j - 1)] - lambda2 * dp[(i - 1) * w + (j - 1)];
                    if (lx[i - 1].equals(lz[j - 1])) {
                        dps[i * w + j] = delta(sx.get(i - 1), sz.get(j - 1)) * dp[(i - 1) * w + (j - 1)];
                        km[l] += dps[i * w + j];
                    }
                }
            }
        }
        double k = 0;
        for (int l = 0; l < p; l++) k += km[l];
        depth--;
        return k;
    }

    private void ensureBuffers(int d, int cells, int lengths) {
        if (dpBuf.length <= d) {
            int cap = Math.max(d + 1, dpBuf.length * 2);
            dpBuf = Arrays.copyOf(dpBuf, cap);
            dpsBuf = Arrays.copyOf(dpsBuf, cap);
            kmBuf = Arrays.copyOf(kmBuf, cap);
        }
        if (dpBuf[d] == null || dpBuf[d].length < cells) {
            dpBuf[d] = new double[cells];
            dpsBuf[d] = new double[cells];
        }
        if (kmBuf[d] == null || kmBuf[d].length < lengths) kmBuf[d] = new double[lengths];
    }

    private void resetMemo(int maxIdA, int maxIdB) {
        width = maxIdB + 1;
        long size = (long) (maxIdA + 1) * width;
        dense = size <= DENSE_LIMIT;
        sparse.clear();
        if (sparse.capacity() > 1 << 20) sparse.compact();   // don't keep giant-pair memory
        if (dense) {
            if (memoValues.length < size) {
                int cap = (int) Math.min(DENSE_LIMIT, Math.max(size, 2L * memoValues.length));
                memoValues = new double[cap];
                memoStamps = new int[cap];
                generation = 0;
            }
            if (++generation == Integer.MAX_VALUE) {
                Arrays.fill(memoStamps, 0);
                generation = 1;
            }
        }
    }

    private double memoGet(int i, int j) {
        if (dense) {
            int k = i * width + j;
            return memoStamps[k] == generation ? memoValues[k] : Double.NaN;
        }
        long key = LogTreeKernels.pairKey(i, j);
        return sparse.containsKey(key) ? sparse.get(key) : Double.NaN;
    }

    private void memoPut(int i, int j, double v) {
        if (dense) {
            int k = i * width + j;
            memoValues[k] = v;
            memoStamps[k] = generation;
        } else {
            sparse.put(LogTreeKernels.pairKey(i, j), v);
        }
    }
}
