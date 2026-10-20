package treekernel;

import it.uniroma2.sag.kelp.data.representation.tree.TreeRepresentation;
import it.uniroma2.sag.kelp.kernel.tree.PartialTreeKernel;
import it.uniroma2.sag.kelp.kernel.tree.SubSetTreeKernel;
import it.uniroma2.sag.kelp.kernel.tree.SubTreeKernel;
import it.uniroma2.sag.kelp.kernel.tree.deltamatrix.DeltaMatrix;
import it.uniroma2.sag.kelp.kernel.tree.deltamatrix.DynamicDeltaMatrix;
import it.uniroma2.sag.kelp.kernel.tree.deltamatrix.StaticDeltaMatrix;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Times KeLP tree kernels on query x candidate pairs.
 *
 * Every query is paired with a uniform random sample of candidates drawn from all
 * other functions in the trees file. Each worker thread owns its kernel instances and
 * delta matrices, because KeLP's default StaticDeltaMatrix is a shared singleton.
 *
 * usage: KernelTiming trees.tsv queries.tsv kernel lambda mu nCandidates threads seed
 *                     budgetSeconds out.tsv
 *   kernel: STK | SSTK | PTK   (mu is ignored for STK/SSTK)
 */
public class KernelTiming {

    /** Pairs whose larger tree exceeds this use a hash-based delta matrix (memory). */
    static final int STATIC_MATRIX_MAX_NODES = 2000;

    interface Kernel { float eval(TreeRepresentation a, TreeRepresentation b); }

    static Kernel make(String kind, float lambda, float mu, DeltaMatrix dm) {
        switch (kind) {
            case "STK": {
                SubTreeKernel k = new SubTreeKernel(lambda, "ast");
                k.setDeltaMatrix(dm);
                return k::kernelComputation;
            }
            case "SSTK": {
                SubSetTreeKernel k = new SubSetTreeKernel(lambda, "ast");
                k.setDeltaMatrix(dm);
                return k::kernelComputation;
            }
            case "PTK": {
                PartialTreeKernel k = new PartialTreeKernel(lambda, mu, 1f, "ast");
                k.setDeltaMatrix(dm);
                return k::kernelComputation;
            }
            default:
                throw new IllegalArgumentException("unknown kernel " + kind);
        }
    }

    /** Per-thread kernels: a dense matrix for normal pairs, a hash map for huge ones. */
    static final class Worker {
        final Kernel small, large;
        Worker(String kind, float lambda, float mu) {
            small = make(kind, lambda, mu, new StaticDeltaMatrix(STATIC_MATRIX_MAX_NODES + 1));
            large = make(kind, lambda, mu, new DynamicDeltaMatrix());
        }
    }

    record Tree(long id, int nodes, TreeRepresentation rep) {}

    /**
     * Fill every lazily-built cache of a tree before it is shared between threads.
     * KeLP's TreeRepresentation assigns its cached node list to the field *before*
     * sorting it, so a concurrent reader can see an unsorted list and the kernel then
     * silently pairs the wrong nodes (or throws IndexOutOfBoundsException).
     */
    static void warmCaches(TreeRepresentation rep) {
        rep.getOrderedNodeSetByProduction();
        rep.getOrderedNodeSetByProductionIgnoringLeaves();
        rep.getOrderedNodeSetByLabel();
        rep.getHeight();
        rep.getBranchingFactor();
        for (var node : rep.getAllNodes()) {
            node.getProduction();
            node.getProductionIgnoringLeaves();
        }
    }

    public static void main(String[] args) throws Exception {
        Path treesPath = Path.of(args[0]);
        Path queriesPath = Path.of(args[1]);
        String kind = args[2];
        float lambda = Float.parseFloat(args[3]);
        float mu = Float.parseFloat(args[4]);
        int nCandidates = Integer.parseInt(args[5]);
        int threads = Integer.parseInt(args[6]);
        long seed = Long.parseLong(args[7]);
        long budgetSeconds = Long.parseLong(args[8]);
        Path out = Path.of(args[9]);

        Set<Long> queryIds = new TreeSet<>();
        try (BufferedReader r = Files.newBufferedReader(queriesPath)) {
            r.readLine();
            for (String l; (l = r.readLine()) != null; ) queryIds.add(Long.parseLong(l.split("\t")[0]));
        }

        // Pass 1: ids only, to sample candidates without parsing every tree.
        List<Long> others = new ArrayList<>();
        try (BufferedReader r = Files.newBufferedReader(treesPath)) {
            r.readLine();
            for (String l; (l = r.readLine()) != null; ) {
                long id = Long.parseLong(l.substring(0, l.indexOf('\t')));
                if (!queryIds.contains(id)) others.add(id);
            }
        }
        Collections.shuffle(others, new Random(seed));
        Set<Long> candIds = new HashSet<>(others.subList(0, Math.min(nCandidates, others.size())));
        long corpusSize = others.size() + queryIds.size();

        // Pass 2: parse the trees we need.
        Map<Long, Tree> trees = new HashMap<>();
        long t0 = System.nanoTime();
        try (BufferedReader r = Files.newBufferedReader(treesPath)) {
            r.readLine();
            for (String l; (l = r.readLine()) != null; ) {
                String[] f = l.split("\t", 5);
                long id = Long.parseLong(f[0]);
                if (!queryIds.contains(id) && !candIds.contains(id)) continue;
                TreeRepresentation rep = new TreeRepresentation();
                rep.setDataFromText(f[4]);
                warmCaches(rep);
                trees.put(id, new Tree(id, Integer.parseInt(f[1]), rep));
            }
        }
        double parseSec = (System.nanoTime() - t0) / 1e9;

        List<Tree> queries = new ArrayList<>(), cands = new ArrayList<>();
        for (long q : queryIds) queries.add(trees.get(q));
        for (long c : candIds) cands.add(trees.get(c));

        // Work list: every query x every sampled candidate, in random order so that a
        // budget cut-off still leaves an unbiased-by-position sample.
        List<Tree[]> pairs = new ArrayList<>();
        for (Tree q : queries) for (Tree c : cands) pairs.add(new Tree[]{q, c});
        Collections.shuffle(pairs, new Random(seed + 1));

        ThreadLocal<Worker> workers = ThreadLocal.withInitial(() -> new Worker(kind, lambda, mu));
        ExecutorService pool = Executors.newFixedThreadPool(threads);
        long[] nanos = new long[pairs.size()];
        float[] values = new float[pairs.size()];
        boolean[] done = new boolean[pairs.size()];
        AtomicLong busyNanos = new AtomicLong();
        List<String> failures = new ArrayList<>();
        long deadline = System.nanoTime() + budgetSeconds * 1_000_000_000L;

        long wallStart = System.nanoTime();
        List<Future<?>> futures = new ArrayList<>();
        for (int i = 0; i < pairs.size(); i++) {
            final int idx = i;
            futures.add(pool.submit(() -> {
                if (System.nanoTime() > deadline) return;
                Tree a = pairs.get(idx)[0], b = pairs.get(idx)[1];
                Worker w = workers.get();
                Kernel k = Math.max(a.nodes(), b.nodes()) > STATIC_MATRIX_MAX_NODES ? w.large : w.small;
                long s = System.nanoTime();
                try {
                    values[idx] = k.eval(a.rep(), b.rep());
                } catch (RuntimeException ex) {
                    synchronized (failures) {
                        failures.add(a.id() + "\t" + b.id() + "\t" + ex);
                    }
                    return;
                }
                long e = System.nanoTime() - s;
                nanos[idx] = e;
                busyNanos.addAndGet(e);
                done[idx] = true;
            }));
        }
        for (Future<?> f : futures) f.get();
        pool.shutdown();
        double wallSec = (System.nanoTime() - wallStart) / 1e9;

        int completed = 0;
        try (PrintWriter w = new PrintWriter(Files.newBufferedWriter(out))) {
            w.println("query_id\tcandidate_id\tquery_nodes\tcandidate_nodes\tnanos\tvalue");
            for (int i = 0; i < pairs.size(); i++) {
                if (!done[i]) continue;
                completed++;
                Tree a = pairs.get(i)[0], b = pairs.get(i)[1];
                w.printf("%d\t%d\t%d\t%d\t%d\t%g%n", a.id(), b.id(), a.nodes(), b.nodes(), nanos[i], values[i]);
            }
        }

        if (!failures.isEmpty()) {
            System.out.printf("  FAILED pairs: %d (first: %s)%n", failures.size(), failures.get(0));
            Files.write(Path.of(out + ".failures"), failures);
        }
        long fullRun = (long) queries.size() * (corpusSize - 1);
        double perEvalMs = busyNanos.get() / 1e6 / completed;
        double evalsPerSec = completed / wallSec;
        System.out.printf(Locale.ROOT,
            "kernel=%s lambda=%.2f mu=%.2f trees=%s threads=%d%n" +
            "  parsed %d trees in %.1fs; pairs planned %d, completed %d%s%n" +
            "  mean per-evaluation CPU time %.3f ms; throughput %.0f evals/s (wall %.1fs)%n" +
            "  extrapolated full run (%d queries x %d other true positives = %,d evals): %.1f min%n",
            kind, lambda, mu, treesPath.getFileName(), threads,
            trees.size(), parseSec, pairs.size(), completed,
            completed < pairs.size() ? " (time budget hit)" : "",
            perEvalMs, evalsPerSec, wallSec,
            queries.size(), corpusSize - 1, fullRun, fullRun / evalsPerSec / 60);
    }
}
