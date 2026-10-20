package treekernel;

import it.uniroma2.sag.kelp.data.representation.tree.TreeRepresentation;
import it.uniroma2.sag.kelp.kernel.tree.SubSetTreeKernel;
import it.uniroma2.sag.kelp.kernel.tree.SubTreeKernel;
import it.uniroma2.sag.kelp.kernel.tree.deltamatrix.DynamicDeltaMatrix;

import java.io.BufferedReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

/**
 * Verifies LogTreeKernels against KeLP and against hand-computed values.
 *
 * usage: LogKernelCheck trees.tsv nPairs seed
 */
public class LogKernelCheck {
    static TreeRepresentation t(String s) throws Exception {
        TreeRepresentation r = new TreeRepresentation();
        r.setDataFromText(s);
        KernelTiming.warmCaches(r);
        return r;
    }

    public static void main(String[] args) throws Exception {
        // 1. Hand examples, lambda = 1.
        String[][] cases = {
            {"(S (A x))", "(S (A y))", "SSTK 1, STK(KeLP) 1, STK(textbook) 0"},
            {"(S (A x) (B z))", "(S (A y) (B z))", "SSTK 4, STK(KeLP) 3, STK(textbook) 2"},
            {"(S (A a) (B b))", "(S (A a) (B b))", "SSTK 8, STK(KeLP) 5, STK(textbook) 5"},
        };
        for (String[] c : cases) {
            TreeRepresentation a = t(c[0]), b = t(c[1]);
            System.out.printf(Locale.ROOT, "%-18s vs %-18s  SSTK %.4g  STK(KeLP) %.4g  STK(textbook) %.4g   expected: %s%n",
                c[0], c[1],
                Math.exp(LogTreeKernels.logKernel(a, b, LogTreeKernels.Kind.SSTK, 1)),
                Math.exp(LogTreeKernels.logKernel(a, b, LogTreeKernels.Kind.STK_KELP, 1)),
                Math.exp(LogTreeKernels.logKernel(a, b, LogTreeKernels.Kind.STK_TEXTBOOK, 1)), c[2]);
        }

        // 2. Against KeLP on real pairs (where KeLP's float does not overflow).
        Path treesPath = Path.of(args[0]);
        int n = Integer.parseInt(args[1]);
        Random rnd = new Random(Long.parseLong(args[2]));
        List<String[]> rows = new ArrayList<>();
        try (BufferedReader r = Files.newBufferedReader(treesPath)) {
            r.readLine();
            for (String l; (l = r.readLine()) != null; ) {
                String[] f = l.split("\t", 5);
                if (Integer.parseInt(f[1]) <= 1500) rows.add(f);
            }
        }
        Collections.shuffle(rows, rnd);
        for (double lambda : new double[]{0.1, 0.4, 1.0}) {
            double maxRelSstk = 0, maxRelStk = 0;
            int sstkCompared = 0, sstkKelpOverflow = 0, stkCompared = 0;
            for (int i = 0; i < n; i++) {
                TreeRepresentation a = t(rows.get(2 * i)[4]), b = t(rows.get(2 * i + 1)[4]);
                for (TreeRepresentation[] p : new TreeRepresentation[][]{{a, b}, {a, a}}) {
                    SubSetTreeKernel sst = new SubSetTreeKernel((float) lambda, "x");
                    sst.setDeltaMatrix(new DynamicDeltaMatrix());
                    float kelp = sst.kernelComputation(p[0], p[1]);
                    double mine = Math.exp(LogTreeKernels.logKernel(p[0], p[1], LogTreeKernels.Kind.SSTK, lambda));
                    if (Float.isInfinite(kelp)) {
                        sstkKelpOverflow++;
                    } else {
                        sstkCompared++;
                        maxRelSstk = Math.max(maxRelSstk, Math.abs(mine - kelp) / Math.max(Math.abs(kelp), 1e-30));
                    }
                    SubTreeKernel st = new SubTreeKernel((float) lambda, "x");
                    st.setDeltaMatrix(new DynamicDeltaMatrix());
                    float kelpSt = st.kernelComputation(p[0], p[1]);
                    double mineSt = Math.exp(LogTreeKernels.logKernel(p[0], p[1], LogTreeKernels.Kind.STK_KELP, lambda));
                    stkCompared++;
                    maxRelStk = Math.max(maxRelStk, Math.abs(mineSt - kelpSt) / Math.max(Math.abs(kelpSt), 1e-30));
                }
            }
            System.out.printf(Locale.ROOT,
                "%s lambda=%.1f: SSTK max relative diff vs KeLP %.1e over %d values (%d where KeLP overflowed); STK(KeLP mode) max relative diff %.1e over %d values%n",
                treesPath.getFileName(), lambda, maxRelSstk, sstkCompared, sstkKelpOverflow, maxRelStk, stkCompared);
        }
    }
}
