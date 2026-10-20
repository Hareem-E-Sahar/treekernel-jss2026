package treekernel;

import it.uniroma2.sag.kelp.data.representation.tree.TreeRepresentation;
import it.uniroma2.sag.kelp.data.representation.tree.node.TreeNode;

import java.io.BufferedReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

/**
 * Checks that KeLP parses every tree string exactly as written: the parsed tree must
 * have the same node count and the same node labels in pre-order as the string.
 * Catches labels that KeLP would split or reinterpret (e.g. containing "::" or "##").
 *
 * usage: ParseCheck trees.tsv [trees.tsv ...]
 */
public class ParseCheck {
    static List<String> labelsFromString(String s) {
        List<String> out = new ArrayList<>();
        for (int i = 0; i < s.length(); i++) {
            if (s.charAt(i) == '(') {
                int j = i + 1;
                while (j < s.length() && s.charAt(j) != '(' && s.charAt(j) != ')' && s.charAt(j) != ' ') j++;
                out.add(s.substring(i + 1, j));
            }
        }
        return out;
    }

    static void preorder(TreeNode n, List<String> out) {
        out.add(n.getContent().getTextFromData());
        for (TreeNode c : n.getChildren()) preorder(c, out);
    }

    public static void main(String[] args) throws Exception {
        for (String file : args) {
            int trees = 0, bad = 0;
            long nodes = 0;
            Set<String> types = new TreeSet<>();
            String firstBad = null;
            try (BufferedReader r = Files.newBufferedReader(Path.of(file))) {
                r.readLine();
                for (String l; (l = r.readLine()) != null; ) {
                    String[] f = l.split("\t", 5);
                    TreeRepresentation rep = new TreeRepresentation();
                    rep.setDataFromText(f[4]);
                    List<String> expected = labelsFromString(f[4]);
                    List<String> got = new ArrayList<>();
                    preorder(rep.getRoot(), got);
                    collectTypes(rep.getRoot(), types);
                    trees++;
                    nodes += got.size();
                    if (!expected.equals(got) || got.size() != Integer.parseInt(f[1])) {
                        bad++;
                        if (firstBad == null) firstBad = f[0];
                    }
                }
            }
            System.out.printf("%s: %d trees, %d nodes, %d mismatched%s; element classes used: %s%n",
                Path.of(file).getFileName(), trees, nodes, bad,
                firstBad == null ? "" : " (first: " + firstBad + ")", types);
        }
    }

    static void collectTypes(TreeNode n, Set<String> types) {
        types.add(n.getContent().getClass().getSimpleName());
        for (TreeNode c : n.getChildren()) collectTypes(c, types);
    }
}
