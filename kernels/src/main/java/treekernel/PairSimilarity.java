package treekernel;

import it.uniroma2.sag.kelp.data.representation.tree.TreeRepresentation;
import it.uniroma2.sag.kelp.kernel.tree.deltamatrix.DynamicDeltaMatrix;

import java.io.BufferedReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;

/**
 * STK, SSTK and PTK similarity between two methods, raw and normalised.
 *
 * usage: PairSimilarity trees.tsv idA idB lambda mu
 * Normalised value: K(a,b) / sqrt(K(a,a) * K(b,b)), in [0, 1].
 */
public class PairSimilarity {
    public static void main(String[] args) throws Exception {
        Path trees = Path.of(args[0]);
        String idA = args[1], idB = args[2];
        float lambda = Float.parseFloat(args[3]), mu = Float.parseFloat(args[4]);
        TreeRepresentation a = null, b = null;
        int na = 0, nb = 0;
        try (BufferedReader r = Files.newBufferedReader(trees)) {
            r.readLine();
            for (String l; (l = r.readLine()) != null; ) {
                String[] f = l.split("\t", 5);
                if (f[0].equals(idA) || f[0].equals(idB)) {
                    TreeRepresentation t = new TreeRepresentation();
                    t.setDataFromText(f[4]);
                    if (f[0].equals(idA)) { a = t; na = Integer.parseInt(f[1]); }
                    if (f[0].equals(idB)) { b = t; nb = Integer.parseInt(f[1]); }
                }
            }
        }
        if (a == null || b == null) throw new IllegalArgumentException("id not found in " + trees);
        System.out.printf(Locale.ROOT, "%s: %s has %d nodes, %s has %d nodes (lambda=%.2f, mu=%.2f)%n",
            trees.getFileName(), idA, na, idB, nb, lambda, mu);
        System.out.printf("%-5s %14s %14s %14s %11s%n", "kernel", "K(q,q)", "K(c,c)", "K(q,c)", "normalised");
        for (String kind : new String[]{"STK", "SSTK", "PTK"}) {
            KernelTiming.Kernel k = KernelTiming.make(kind, lambda, mu, new DynamicDeltaMatrix());
            double aa = k.eval(a, a), bb = k.eval(b, b), ab = k.eval(a, b);
            System.out.printf(Locale.ROOT, "%-5s %14.4f %14.4f %14.4f %11.4f%n", kind, aa, bb, ab, ab / Math.sqrt(aa * bb));
        }
    }
}
