package treekernel;

import it.uniroma2.sag.kelp.data.representation.tree.TreeRepresentation;
import it.uniroma2.sag.kelp.kernel.tree.PartialTreeKernel;
import it.uniroma2.sag.kelp.kernel.tree.SubSetTreeKernel;
import it.uniroma2.sag.kelp.kernel.tree.SubTreeKernel;
import it.uniroma2.sag.kelp.kernel.tree.deltamatrix.DeltaMatrix;
import it.uniroma2.sag.kelp.kernel.tree.deltamatrix.DynamicDeltaMatrix;
import it.uniroma2.sag.kelp.kernel.tree.deltamatrix.StaticDeltaMatrix;

import java.io.BufferedReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * For each kernel setting, computes KeLP's self-similarity K(x, x) of every tree (KeLP as
 * is, 32-bit float) and reports how many are not finite. A setting is usable only if all
 * are finite: by Cauchy-Schwarz K(a,b) <= sqrt(K(a,a) K(b,b)), so finite self-similarities
 * bound every cross value.
 *
 * usage: GridFiniteScan trees.tsv threads budgetSecondsPerSetting KERNEL:lambda[:mu] ...
 *   e.g. SSTK:0.4  STK:1.0  PTK:0.4:0.8
 * A setting that exceeds the time budget is reported as NOT FINISHED.
 * With -DdumpDir=dir, the ids of the non-finite trees are written to dir/<variant>_<setting>.ids.
 */
public class GridFiniteScan {
    interface K { float eval(TreeRepresentation a, TreeRepresentation b); }

    static K make(String kind, float lambda, float mu, DeltaMatrix dm) {
        switch (kind) {
            case "STK": { SubTreeKernel k = new SubTreeKernel(lambda, "ast"); k.setDeltaMatrix(dm); return k::kernelComputation; }
            case "SSTK": { SubSetTreeKernel k = new SubSetTreeKernel(lambda, "ast"); k.setDeltaMatrix(dm); return k::kernelComputation; }
            case "PTK": { PartialTreeKernel k = new PartialTreeKernel(lambda, mu, 1f, "ast"); k.setDeltaMatrix(dm); return k::kernelComputation; }
            default: throw new IllegalArgumentException(kind);
        }
    }

    public static void main(String[] args) throws Exception {
        Path treesPath = Path.of(args[0]);
        int threads = Integer.parseInt(args[1]);
        long budget = Long.parseLong(args[2]);
        List<String[]> rows = new ArrayList<>();
        try (BufferedReader r = Files.newBufferedReader(treesPath)) {
            r.readLine();
            for (String l; (l = r.readLine()) != null; ) rows.add(l.split("\t", 5));
        }
        // trees are parsed inside each task (keeps memory small for the raw variant)
        int[] nodes = new int[rows.size()];
        for (int i = 0; i < rows.size(); i++) nodes[i] = Integer.parseInt(rows.get(i)[1]);
        Integer[] order = new Integer[rows.size()];   // biggest first, so giants don't finish last
        for (int i = 0; i < order.length; i++) order[i] = i;
        Arrays.sort(order, (x, y) -> nodes[y] - nodes[x]);

        for (int s = 3; s < args.length; s++) {
            String[] p = args[s].split(":");
            String kind = p[0];
            float lambda = Float.parseFloat(p[1]);
            float mu = p.length > 2 ? Float.parseFloat(p[2]) : 0f;
            ThreadLocal<K> small = ThreadLocal.withInitial(() -> make(kind, lambda, mu, new StaticDeltaMatrix(KernelTiming.STATIC_MATRIX_MAX_NODES + 1)));
            Semaphore giants = new Semaphore(2);
            float[] vals = new float[rows.size()];
            boolean[] done = new boolean[rows.size()];
            ExecutorService pool = Executors.newFixedThreadPool(threads);
            long t0 = System.nanoTime();
            for (int idx : order) {
                pool.submit(() -> {
                    boolean giant = nodes[idx] > KernelTiming.STATIC_MATRIX_MAX_NODES;
                    try {
                        if (giant) giants.acquire();
                        K k = giant ? make(kind, lambda, mu, new DynamicDeltaMatrix()) : small.get();
                        TreeRepresentation t = RetrievalRunner.parse(rows.get(idx)[4]);
                        vals[idx] = k.eval(t, t);
                        done[idx] = true;
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                    } catch (Exception e) {
                        throw new RuntimeException(e);
                    } finally {
                        if (giant) giants.release();
                    }
                });
            }
            pool.shutdown();
            boolean finished = pool.awaitTermination(budget, TimeUnit.SECONDS);
            if (!finished) pool.shutdownNow();
            int nonFinite = 0, completed = 0, smallest = Integer.MAX_VALUE;
            float max = 0;
            for (int i = 0; i < vals.length; i++) {
                if (!done[i]) continue;
                completed++;
                if (!Float.isFinite(vals[i])) { nonFinite++; smallest = Math.min(smallest, nodes[i]); }
                else max = Math.max(max, vals[i]);
            }
            System.out.printf(Locale.ROOT, "%s\t%s\tlambda=%s%s\t%s\tnon-finite=%d%s\tlargest=%.2e\t%.0fs%n",
                treesPath.getFileName(), kind, lambda, kind.equals("PTK") ? ",mu=" + p[2] : "",
                finished ? "complete" : "NOT FINISHED (" + completed + "/" + vals.length + " done)",
                nonFinite, nonFinite > 0 ? " (smallest tree " + smallest + " nodes)" : "", max,
                (System.nanoTime() - t0) / 1e9);
            System.out.flush();
            String dumpDir = System.getProperty("dumpDir");
            if (dumpDir != null) {
                List<String> ids = new ArrayList<>();
                for (int i = 0; i < vals.length; i++)
                    if (done[i] && !Float.isFinite(vals[i])) ids.add(rows.get(i)[0] + "\t" + nodes[i]);
                String variant = treesPath.getFileName().toString().replace(".tsv", "");
                Files.write(Path.of(dumpDir, variant + "_" + args[s].replace(':', '_') + ".ids"), ids);
            }
        }
        System.exit(0);   // abandoned giant tasks may still be running after a budget overrun
    }
}
