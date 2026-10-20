package treekernel;

import it.uniroma2.sag.kelp.data.representation.tree.TreeRepresentation;
import it.uniroma2.sag.kelp.kernel.tree.deltamatrix.DynamicDeltaMatrix;
import it.uniroma2.sag.kelp.kernel.tree.deltamatrix.StaticDeltaMatrix;

import java.io.BufferedReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

/**
 * Correctness checks for the timing harness:
 *  1. hand example on (S (A a) (B b)) with lambda=1, where values can be counted by hand
 *  2. dense (Static) and hash (Dynamic) delta matrices give the same values on real trees,
 *     including when one matrix instance is reused across many pairs (stale entries).
 *
 * usage: KernelCheck trees.tsv nPairs seed
 */
public class KernelCheck {
    public static void main(String[] args) throws Exception {
        // 1. Hand example. Tree (S (A a) (B b)), lambda=1, leaves included (KeLP default).
        // SSTK: at S (1+1)(1+1)=4, at A 1, at B 1, at leaves a and b 1 each -> 8.
        // STK: one complete subtree at each of the 5 nodes -> 5.
        TreeRepresentation t = new TreeRepresentation();
        t.setDataFromText("(S (A a) (B b))");
        for (String kind : new String[]{"SSTK", "STK", "PTK"}) {
            float v = KernelTiming.make(kind, 1f, 1f, new StaticDeltaMatrix(10)).eval(t, t);
            System.out.printf(Locale.ROOT, "hand example %-4s K(T,T) = %.4f%n", kind, v);
        }

        // 2. Static vs dynamic on real trees.
        Path treesPath = Path.of(args[0]);
        int n = Integer.parseInt(args[1]);
        Random rnd = new Random(Long.parseLong(args[2]));
        List<String[]> rows = new ArrayList<>();
        try (BufferedReader r = Files.newBufferedReader(treesPath)) {
            r.readLine();
            for (String l; (l = r.readLine()) != null; ) {
                String[] f = l.split("\t", 5);
                if (Integer.parseInt(f[1]) <= 600) rows.add(f);
            }
        }
        Collections.shuffle(rows, rnd);
        List<TreeRepresentation> reps = new ArrayList<>();
        for (int i = 0; i < 2 * n; i++) {
            TreeRepresentation rep = new TreeRepresentation();
            rep.setDataFromText(rows.get(i)[4]);
            reps.add(rep);
        }
        for (String kind : new String[]{"STK", "SSTK", "PTK"}) {
            KernelTiming.Kernel st = KernelTiming.make(kind, 0.4f, 0.4f, new StaticDeltaMatrix(2001));
            double maxRel = 0;
            int nonzero = 0;
            for (int i = 0; i < n; i++) {
                TreeRepresentation a = reps.get(2 * i), b = reps.get(2 * i + 1);
                float vs = st.eval(a, b);   // same static instance reused: tests stale entries
                float vd = KernelTiming.make(kind, 0.4f, 0.4f, new DynamicDeltaMatrix()).eval(a, b);
                if (vd != 0) nonzero++;
                double rel = Math.abs(vs - vd) / Math.max(1e-12, Math.abs(vd));
                maxRel = Math.max(maxRel, rel);
            }
            System.out.printf(Locale.ROOT, "%-4s static vs dynamic over %d pairs: max relative diff %.2e (%d non-zero)%n",
                kind, n, maxRel, nonzero);
        }
    }
}
