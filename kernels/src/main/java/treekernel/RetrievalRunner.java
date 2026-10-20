package treekernel;

import it.uniroma2.sag.kelp.data.representation.tree.TreeRepresentation;
import it.uniroma2.sag.kelp.kernel.tree.deltamatrix.DynamicDeltaMatrix;
import it.uniroma2.sag.kelp.kernel.tree.deltamatrix.StaticDeltaMatrix;

import java.io.*;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.channels.FileChannel;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Scores every query against every method in the corpus with one tree-kernel configuration.
 *
 * usage: RetrievalRunner trees.tsv queries.tsv kernel lambda mu threads outDir
 *   kernel: SSTK | STK | PTK   (mu is used by PTK only)
 *     KeLP's own SubSetTreeKernel, SubTreeKernel and PartialTreeKernel, used as is
 *     (32-bit float; decided 2026-10-15). The log of each value is stored. A value that is
 *     not finite (KeLP float overflow) stops the run with an error: such settings are
 *     excluded from the grid (results/grid_scan/).
 *     Harness workarounds that do not change values: caches warmed before trees are shared
 *     between threads; one kernel and delta matrix per thread; pairs with a tree above
 *     2,000 nodes use a fresh DynamicDeltaMatrix, at most 2 at a time.
 *   queries.tsv: header line, then one function id per line (first column)
 *
 * The corpus is streamed: each corpus method is parsed by the task that scores it against
 * all queries, with a bounded number of tasks in flight, so memory stays small and one
 * slow (giant) method never blocks the others.
 *
 * Writes to outDir:
 *   logk.f64       little-endian float64 matrix, nQueries x nCorpus, row-major: log K(q, c),
 *                  where K is KeLP's float value.
 *                  The query itself (q == c) is stored as NaN; K = 0 is stored as -Infinity.
 *   logself.f64    float64 vector, nCorpus: log K(c, c) (queries are corpus members)
 *   query_ids.txt  row order;  corpus_ids.txt  column order
 *   meta.json      configuration, sizes and timings
 * Normalised score = exp(logk[q][c] - (logself[q] + logself[c]) / 2).
 */
public class RetrievalRunner {

    /** Pairs whose larger tree exceeds this count as giant (memory-heavy). */
    static final int GIANT_NODES = KernelTiming.STATIC_MATRIX_MAX_NODES;
    /** At most this many evaluations involving a giant tree run at the same time. */
    static final int GIANT_CONCURRENCY = 2;

    record Query(long id, int nodes, TreeRepresentation tree) {}

    public static void main(String[] args) throws Exception {
        Path treesPath = Path.of(args[0]).toAbsolutePath().normalize();
        Path queriesPath = Path.of(args[1]).toAbsolutePath().normalize();
        String kernel = args[2];
        double lambda = Double.parseDouble(args[3]);
        double mu = Double.parseDouble(args[4]);
        int threads = Integer.parseInt(args[5]);
        Path outDir = Path.of(args[6]).toAbsolutePath().normalize();
        if (!Set.of("SSTK", "STK", "PTK").contains(kernel)) {
            throw new IllegalArgumentException("unknown kernel " + kernel);
        }
        Files.createDirectories(outDir);
        long t0 = System.nanoTime();

        List<Long> queryIds = new ArrayList<>();
        try (BufferedReader r = Files.newBufferedReader(queriesPath)) {
            r.readLine();
            for (String l; (l = r.readLine()) != null; ) {
                if (!l.isBlank()) queryIds.add(Long.parseLong(l.split("\t")[0]));
            }
        }
        Map<Long, Integer> queryRow = new HashMap<>();
        for (int i = 0; i < queryIds.size(); i++) queryRow.put(queryIds.get(i), i);

        // Pass 1: corpus order and the query trees (kept for the whole run).
        List<Long> corpusIds = new ArrayList<>();
        Query[] queries = new Query[queryIds.size()];
        try (BufferedReader r = Files.newBufferedReader(treesPath)) {
            r.readLine();
            for (String l; (l = r.readLine()) != null; ) {
                String[] f = l.split("\t", 5);
                long id = Long.parseLong(f[0]);
                corpusIds.add(id);
                Integer row = queryRow.get(id);
                if (row != null) queries[row] = new Query(id, Integer.parseInt(f[1]), parse(f[4]));
            }
        }
        for (int i = 0; i < queries.length; i++) {
            if (queries[i] == null) throw new IllegalArgumentException("query " + queryIds.get(i) + " not in " + treesPath);
        }
        int nQ = queries.length, nC = corpusIds.size();
        double[] logk = new double[nQ * nC];
        double[] logself = new double[nC];

        Scorer scorer = new Scorer(kernel, lambda, mu);
        ExecutorService pool = Executors.newFixedThreadPool(threads);
        Semaphore inFlight = new Semaphore(threads * 4);
        AtomicInteger done = new AtomicInteger();
        java.util.concurrent.atomic.AtomicReference<Throwable> failed = new java.util.concurrent.atomic.AtomicReference<>();
        List<Future<?>> futures = new ArrayList<>();

        // Pass 2: stream the corpus.
        try (BufferedReader r = Files.newBufferedReader(treesPath)) {
            r.readLine();
            int col = 0;
            for (String l; (l = r.readLine()) != null; col++) {
                if (failed.get() != null) break;   // stop feeding work after the first error
                String[] f = l.split("\t", 5);
                final int c = col;
                final long id = Long.parseLong(f[0]);
                final int nodes = Integer.parseInt(f[1]);
                final String treeText = f[4];
                inFlight.acquire();
                futures.add(pool.submit(() -> {
                    try {
                        TreeRepresentation cand = parse(treeText);
                        logself[c] = scorer.logK(cand, cand, nodes, nodes);
                        for (int q = 0; q < nQ; q++) {
                            logk[q * nC + c] = queries[q].id() == id
                                ? Double.NaN
                                : scorer.logK(queries[q].tree(), cand, queries[q].nodes(), nodes);
                        }
                        int k = done.incrementAndGet();
                        if (k % 2000 == 0 || k == nC) {
                            System.out.printf(Locale.ROOT, "  %d / %d corpus methods scored (%.0fs)%n", k, nC, (System.nanoTime() - t0) / 1e9);
                        }
                        return null;
                    } catch (Throwable e) {
                        failed.compareAndSet(null, e);
                        throw e;
                    } finally {
                        inFlight.release();
                    }
                }));
            }
        }
        try {
            for (Future<?> f : futures) f.get();
        } finally {
            pool.shutdownNow();   // on error too, so the JVM exits instead of hanging
        }

        writeDoubles(outDir.resolve("logk.f64"), logk);
        writeDoubles(outDir.resolve("logself.f64"), logself);
        Files.write(outDir.resolve("query_ids.txt"), queryIds.stream().map(String::valueOf).toList());
        Files.write(outDir.resolve("corpus_ids.txt"), corpusIds.stream().map(String::valueOf).toList());
        double wall = (System.nanoTime() - t0) / 1e9;
        long evals = (long) nC * (nQ + 1);
        String meta = String.format(Locale.ROOT,
            "{\n  \"kernel\": \"%s\",\n  \"lambda\": %s,\n  \"mu\": %s,\n  \"terminal_factor\": %s,\n" +
            "  \"implementation\": \"%s\",\n  \"trees\": \"%s\",\n  \"queries\": \"%s\",\n" +
            "  \"n_queries\": %d,\n  \"n_corpus\": %d,\n  \"evaluations\": %d,\n  \"threads\": %d,\n" +
            "  \"wall_seconds\": %.1f,\n  \"finished\": \"%s\",\n  \"java\": \"%s\"\n}\n",
            kernel, lambda, kernel.equals("PTK") ? String.valueOf(mu) : "null",
            kernel.equals("PTK") ? "1.0" : "null",
            "KeLP " + kernel + " as is (float), log taken afterwards",
            treesPath, queriesPath, nQ, nC, evals, threads, wall, Instant.now(), System.getProperty("java.version"));
        Files.writeString(outDir.resolve("meta.json"), meta);
        System.out.printf(Locale.ROOT, "done: %d queries x %d corpus, %,d evaluations, %.1fs -> %s%n", nQ, nC, evals, wall, outDir);
    }

    /** Computes log K for one configuration with KeLP's kernels; thread-safe. */
    static final class Scorer {
        private final String kernel;
        private final float lambda, mu;
        private final ThreadLocal<KernelTiming.Kernel> small;
        private final Semaphore giantPermits = new Semaphore(GIANT_CONCURRENCY);

        Scorer(String kernel, double lambda, double mu) {
            this.kernel = kernel;
            this.lambda = (float) lambda;
            this.mu = (float) mu;
            this.small = ThreadLocal.withInitial(() -> KernelTiming.make(kernel, this.lambda, this.mu,
                new StaticDeltaMatrix(GIANT_NODES + 1)));
        }

        double logK(TreeRepresentation a, TreeRepresentation b, int na, int nb) throws InterruptedException {
            float v;
            if (Math.max(na, nb) > GIANT_NODES) {
                giantPermits.acquire();   // cap memory: few giant pairs at once
                try {
                    v = KernelTiming.make(kernel, lambda, mu, new DynamicDeltaMatrix()).eval(a, b);   // discarded after use
                } finally {
                    giantPermits.release();
                }
            } else {
                v = small.get().eval(a, b);
            }
            if (!Float.isFinite(v) || v < 0) {
                throw new ArithmeticException(kernel + " value " + v + " is not finite/non-negative (trees of "
                    + na + " and " + nb + " nodes): this setting must be excluded from the grid");
            }
            return v == 0 ? Double.NEGATIVE_INFINITY : Math.log(v);
        }
    }

    public static TreeRepresentation parse(String tree) throws Exception {
        TreeRepresentation rep = new TreeRepresentation();
        rep.setDataFromText(tree);
        // Fill lazy caches before the tree is shared across threads (see KernelTiming.warmCaches).
        KernelTiming.warmCaches(rep);
        return rep;
    }

    static void writeDoubles(Path p, double[] v) throws IOException {
        ByteBuffer buf = ByteBuffer.allocate(v.length * 8).order(ByteOrder.LITTLE_ENDIAN);
        buf.asDoubleBuffer().put(v);
        try (FileChannel ch = FileChannel.open(p, StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING, StandardOpenOption.WRITE)) {
            ch.write(buf);
        }
    }
}
