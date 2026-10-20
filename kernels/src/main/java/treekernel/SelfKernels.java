package treekernel;

import it.uniroma2.sag.kelp.data.representation.tree.TreeRepresentation;

import java.io.BufferedReader;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import java.util.concurrent.*;

/**
 * Computes K(x, x) for every tree in a trees file. Needed for the normalised kernel
 * K(a,b) / sqrt(K(a,a) K(b,b)).
 *
 * usage: SelfKernels trees.tsv kernel lambda mu threads out.tsv
 */
public class SelfKernels {
    public static void main(String[] args) throws Exception {
        Path treesPath = Path.of(args[0]);
        String kind = args[1];
        float lambda = Float.parseFloat(args[2]);
        float mu = Float.parseFloat(args[3]);
        int threads = Integer.parseInt(args[4]);
        Path out = Path.of(args[5]);

        List<KernelTiming.Tree> trees = new ArrayList<>();
        try (BufferedReader r = Files.newBufferedReader(treesPath)) {
            r.readLine();
            for (String l; (l = r.readLine()) != null; ) {
                String[] f = l.split("\t", 5);
                TreeRepresentation rep = new TreeRepresentation();
                rep.setDataFromText(f[4]);
                KernelTiming.warmCaches(rep);
                trees.add(new KernelTiming.Tree(Long.parseLong(f[0]), Integer.parseInt(f[1]), rep));
            }
        }
        ThreadLocal<KernelTiming.Worker> workers =
            ThreadLocal.withInitial(() -> new KernelTiming.Worker(kind, lambda, mu));
        ExecutorService pool = Executors.newFixedThreadPool(threads);
        double[] values = new double[trees.size()];
        List<Future<?>> futures = new ArrayList<>();
        long t0 = System.nanoTime();
        for (int i = 0; i < trees.size(); i++) {
            final int idx = i;
            futures.add(pool.submit(() -> {
                KernelTiming.Tree t = trees.get(idx);
                KernelTiming.Worker w = workers.get();
                var k = t.nodes() > KernelTiming.STATIC_MATRIX_MAX_NODES ? w.large : w.small;
                values[idx] = k.eval(t.rep(), t.rep());
            }));
        }
        for (Future<?> f : futures) f.get();
        pool.shutdown();
        try (PrintWriter w = new PrintWriter(Files.newBufferedWriter(out))) {
            w.println("function_id\tself_kernel");
            for (int i = 0; i < trees.size(); i++) w.printf("%d\t%g%n", trees.get(i).id(), values[i]);
        }
        System.out.printf(Locale.ROOT, "self-kernels: %d trees in %.1fs%n", trees.size(), (System.nanoTime() - t0) / 1e9);
    }
}
