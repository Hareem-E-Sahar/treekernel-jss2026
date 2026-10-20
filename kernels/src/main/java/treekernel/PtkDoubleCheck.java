package treekernel;

import it.uniroma2.sag.kelp.data.representation.tree.TreeRepresentation;
import it.uniroma2.sag.kelp.kernel.tree.PartialTreeKernel;
import it.uniroma2.sag.kelp.kernel.tree.deltamatrix.DynamicDeltaMatrix;

import java.io.BufferedReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import java.util.concurrent.*;

/**
 * 1. Compares PartialTreeKernelDouble with KeLP's PartialTreeKernel on random real pairs.
 * 2. Computes the double-precision self-kernel of every tree for given (lambda, mu) and
 *    reports the largest value and any non-finite ones (does double precision suffice?).
 *
 * usage: PtkDoubleCheck trees.tsv nPairs seed threads lambda,mu [lambda,mu ...]
 */
public class PtkDoubleCheck {
    public static void main(String[] args) throws Exception {
        Path treesPath = Path.of(args[0]);
        int n = Integer.parseInt(args[1]);
        Random rnd = new Random(Long.parseLong(args[2]));
        int threads = Integer.parseInt(args[3]);
        List<String[]> rows = new ArrayList<>();
        try (BufferedReader r = Files.newBufferedReader(treesPath)) {
            r.readLine();
            for (String l; (l = r.readLine()) != null; ) rows.add(l.split("\t", 5));
        }
        List<String[]> small = new ArrayList<>();
        for (String[] f : rows) if (Integer.parseInt(f[1]) <= 800) small.add(f);
        Collections.shuffle(small, rnd);

        for (int s = 4; s < args.length; s++) {
            String[] lm = args[s].split(",");
            double lambda = Double.parseDouble(lm[0]), mu = Double.parseDouble(lm[1]);
            // 1. agreement with KeLP
            double maxRel = 0;
            int compared = 0, kelpNonFinite = 0;
            PartialTreeKernelDouble mine = new PartialTreeKernelDouble(lambda, mu, 1);
            for (int i = 0; i < n; i++) {
                TreeRepresentation a = RetrievalRunner.parse(small.get(2 * i)[4]);
                TreeRepresentation b = RetrievalRunner.parse(small.get(2 * i + 1)[4]);
                for (TreeRepresentation[] p : new TreeRepresentation[][]{{a, b}, {a, a}}) {
                    PartialTreeKernel kelp = new PartialTreeKernel((float) lambda, (float) mu, 1f, "x");
                    kelp.setDeltaMatrix(new DynamicDeltaMatrix());
                    float kv = kelp.kernelComputation(p[0], p[1]);
                    double mv = mine.kernel(p[0], p[1]);
                    if (!Float.isFinite(kv)) { kelpNonFinite++; continue; }
                    compared++;
                    maxRel = Math.max(maxRel, Math.abs(mv - kv) / Math.max(Math.abs(kv), 1e-30));
                }
            }
            // 2. self-kernels of every tree, in double
            ExecutorService pool = Executors.newFixedThreadPool(threads);
            ThreadLocal<PartialTreeKernelDouble> k = ThreadLocal.withInitial(() -> new PartialTreeKernelDouble(lambda, mu, 1));
            List<Future<double[]>> fs = new ArrayList<>();
            long t0 = System.nanoTime();
            for (String[] f : rows) {
                fs.add(pool.submit(() -> {
                    TreeRepresentation t = RetrievalRunner.parse(f[4]);
                    return new double[]{k.get().kernel(t, t), Integer.parseInt(f[1])};
                }));
            }
            double max = 0, maxNodes = 0;
            int nonFinite = 0, beyondFloat = 0, smallestBad = Integer.MAX_VALUE;
            for (Future<double[]> f : fs) {
                double[] v = f.get();
                if (!Double.isFinite(v[0])) { nonFinite++; smallestBad = Math.min(smallestBad, (int) v[1]); continue; }
                if (v[0] > Float.MAX_VALUE) beyondFloat++;
                if (v[0] > max) { max = v[0]; maxNodes = v[1]; }
            }
            pool.shutdownNow();
            System.out.printf(Locale.ROOT,
                "%s lambda=%.1f mu=%.1f: vs KeLP max relative diff %.1e over %d values (%d where KeLP was not finite); " +
                "self-kernels in double: %d non-finite%s, %d beyond float range, largest %.2e (tree of %.0f nodes); %.0fs%n",
                treesPath.getFileName(), lambda, mu, maxRel, compared, kelpNonFinite,
                nonFinite, nonFinite > 0 ? " (smallest tree " + smallestBad + " nodes)" : "", beyondFloat, max, maxNodes,
                (System.nanoTime() - t0) / 1e9);
        }
    }
}
