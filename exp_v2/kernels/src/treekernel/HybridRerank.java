package treekernel;

import it.uniroma2.sag.kelp.data.representation.tree.TreeRepresentation;

import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLongArray;
import java.util.concurrent.atomic.AtomicReference;

/**
 * Second stage of the hybrid (exp_v2): tree-kernel scores for given (query, candidate) pairs only.
 *
 * usage: HybridRerank trees.tsv pairs.tsv kernel lambda mu threads out.tsv [chunk]
 *   pairs.tsv  header, then query_id \t candidate_id (e.g. BM25's top k per query)
 *   out.tsv    query_id \t candidate_id \t logk, in the order of pairs.tsv; log K(q, c) as RetrievalRunner stores it
 *   out.tsv.timing.tsv  query_id \t pairs \t kernel_ns: summed time of that query's kernel evaluations
 * The kernels are RetrievalRunner's Scorer (KeLP as is, same harness), so a value equals the corresponding entry of a
 * full RetrievalRunner run. Queries are processed in chunks (default 2,000): the chunk's query trees are kept, the
 * corpus is streamed and each candidate is parsed once per chunk and scored against the chunk's queries that list it.
 * Normalisation needs log K(c, c), which a full run of the same setting already holds (logself.f64).
 */
public class HybridRerank {
    public static void main(String[] args) throws Exception {
        Path trees = Path.of(args[0]), pairsPath = Path.of(args[1]), out = Path.of(args[6]);
        String kernel = args[2];
        double lambda = Double.parseDouble(args[3]), mu = Double.parseDouble(args[4]);
        int threads = Integer.parseInt(args[5]);
        int chunk = args.length > 7 ? Integer.parseInt(args[7]) : 2000;
        long t0 = System.nanoTime();

        LinkedHashMap<Long, List<Long>> pairs = new LinkedHashMap<>();
        try (BufferedReader r = Files.newBufferedReader(pairsPath)) {
            r.readLine();
            for (String l; (l = r.readLine()) != null; ) {
                if (l.isBlank()) continue;
                String[] f = l.split("\t");
                pairs.computeIfAbsent(Long.parseLong(f[0]), x -> new ArrayList<>()).add(Long.parseLong(f[1]));
            }
        }
        List<Long> queryIds = new ArrayList<>(pairs.keySet());
        Map<Long, double[]> logk = new HashMap<>();
        Map<Long, Long> nanos = new HashMap<>();
        RetrievalRunner.Scorer scorer = new RetrievalRunner.Scorer(kernel, lambda, mu);

        for (int s = 0; s < queryIds.size(); s += chunk) {
            List<Long> qs = queryIds.subList(s, Math.min(s + chunk, queryIds.size()));
            Map<Long, Integer> qIndex = new HashMap<>();
            for (int i = 0; i < qs.size(); i++) qIndex.put(qs.get(i), i);
            // candidate -> (query index in chunk, position in that query's list)
            Map<Long, List<int[]>> byCand = new HashMap<>();
            double[][] vals = new double[qs.size()][];
            for (int i = 0; i < qs.size(); i++) {
                List<Long> cs = pairs.get(qs.get(i));
                vals[i] = new double[cs.size()];
                for (int p = 0; p < cs.size(); p++) {
                    if (cs.get(p).equals(qs.get(i))) throw new IllegalArgumentException("query " + qs.get(i) + " is its own candidate");
                    byCand.computeIfAbsent(cs.get(p), x -> new ArrayList<>()).add(new int[]{i, p});
                }
            }
            TreeRepresentation[] qTree = new TreeRepresentation[qs.size()];
            int[] qNodes = new int[qs.size()];
            try (BufferedReader r = Files.newBufferedReader(trees)) {
                r.readLine();
                for (String l; (l = r.readLine()) != null; ) {
                    String[] f = l.split("\t", 5);
                    Integer i = qIndex.get(Long.parseLong(f[0]));
                    if (i != null) { qTree[i] = RetrievalRunner.parse(f[4]); qNodes[i] = Integer.parseInt(f[1]); }
                }
            }
            for (int i = 0; i < qs.size(); i++) if (qTree[i] == null) throw new IllegalArgumentException("query " + qs.get(i) + " not in " + trees);

            AtomicLongArray ns = new AtomicLongArray(qs.size());
            AtomicReference<Throwable> failed = new AtomicReference<>();
            ExecutorService pool = Executors.newFixedThreadPool(threads);
            Semaphore inFlight = new Semaphore(threads * 4);
            List<Future<?>> futures = new ArrayList<>();
            int found = 0;
            try (BufferedReader r = Files.newBufferedReader(trees)) {
                r.readLine();
                for (String l; (l = r.readLine()) != null; ) {
                    if (failed.get() != null) break;
                    String[] f = l.split("\t", 5);
                    List<int[]> users = byCand.get(Long.parseLong(f[0]));
                    if (users == null) continue;
                    found++;
                    final int nodes = Integer.parseInt(f[1]);
                    final String text = f[4];
                    inFlight.acquire();
                    futures.add(pool.submit(() -> {
                        try {
                            TreeRepresentation c = RetrievalRunner.parse(text);
                            for (int[] u : users) {
                                long a = System.nanoTime();
                                vals[u[0]][u[1]] = scorer.logK(qTree[u[0]], c, qNodes[u[0]], nodes);
                                ns.addAndGet(u[0], System.nanoTime() - a);
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
                for (Future<?> fu : futures) fu.get();
            } finally {
                pool.shutdownNow();
            }
            if (found != byCand.size()) throw new IllegalArgumentException((byCand.size() - found) + " candidates not in " + trees);
            for (int i = 0; i < qs.size(); i++) { logk.put(qs.get(i), vals[i]); nanos.put(qs.get(i), ns.get(i)); }
            System.out.printf(Locale.ROOT, "  %d / %d queries (%.0fs)%n", s + qs.size(), queryIds.size(), (System.nanoTime() - t0) / 1e9);
        }

        try (PrintWriter w = new PrintWriter(Files.newBufferedWriter(out))) {
            w.println("query_id\tcandidate_id\tlogk");
            for (Long q : queryIds) {
                List<Long> cs = pairs.get(q);
                double[] v = logk.get(q);
                for (int p = 0; p < cs.size(); p++) w.println(q + "\t" + cs.get(p) + "\t" + Double.toString(v[p]));
            }
        }
        try (PrintWriter w = new PrintWriter(Files.newBufferedWriter(Path.of(out + ".timing.tsv")))) {
            w.println("query_id\tpairs\tkernel_ns");
            for (Long q : queryIds) w.println(q + "\t" + pairs.get(q).size() + "\t" + nanos.get(q));
        }
        System.out.printf(Locale.ROOT, "done: %s %s lambda=%s mu=%s, %d queries, %.1fs -> %s%n", kernel, trees.getFileName(),
            lambda, mu, queryIds.size(), (System.nanoTime() - t0) / 1e9, out);
    }
}
