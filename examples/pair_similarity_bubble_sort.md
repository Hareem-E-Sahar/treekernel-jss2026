# Example: STK, SSTK and PTK similarity for one query and one candidate

*Computed 2026-10-13/14 with KeLP tree kernels on the revised trees (`docs/tree_variants.md`). λ = 0.4 and μ = 0.4 (the pilot settings, not tuned). Raw tool output: `examples/pair_similarity_bubble_sort.output.txt`.*

## The methods

The numbers below are **BigCloneBench function IDs**, not file names. They come from the `functions` table of the BCB database (`data/full_bcb/functions.tsv`). That table records which file in `IJaDataset_BCEvalVersion/bcb_reduced/` contains each method, and on which lines:

| Role | Function ID | Task (functionality) | File in `bcb_reduced/` | Lines | Original project and path |
|---|---|---|---|---|---|
| Query | 81754 | Bubble Sort Array (7) | `7/default/22842.java` | 27–37 | gt-camouflage, `/javapathfinder/extensions/symbolic/examples/BubbleSort.java` |
| Candidate (clone) | 5127007 | Bubble Sort Array (7) | `7/selected/2070032.java` | 15–25 | algstudy, `/java/src/main/java/com/algorithmstudy/sort/BubbleSort.java` |
| Contrast (non-clone) | 588571 | Copy File (4) | `4/default/127477.java` | 10–21 | loonglab, `/hadoop-tutorial/.../FileSystemCat.java` |

To see a method in the raw data, print its lines:

```bash
sed -n '27,37p' data/IJaDataset_BCEvalVersion/bcb_reduced/7/default/22842.java
```

The query and the candidate are a BCB **strong Type-3 (ST3)** clone pair (line similarity 0.77, token similarity 0.92), from two different projects. The contrast method is a true positive of a different task, so it is not a clone of the query.

**Query 81754:**
```java
public void Sort(int a[]) {
    for (int i = a.length; --i >= 0; ) {
        for (int j = 0; j < i; j++) {
            if (a[j] > a[j + 1]) {
                int temp = a[j];
                a[j] = a[j + 1];
                a[j + 1] = temp;
            }
        }
    }
}
```

**Candidate 5127007 (clone):**
```java
public static void bubbleSort(int[] a) {
    for (int i = a.length - 1; i > 0; i--) {
        for (int j = 0; j < i; j++) {
            if (a[j] > a[j + 1]) {
                int tmp = a[j];
                a[j] = a[j + 1];
                a[j + 1] = tmp;
            }
        }
    }
}
```

Differences: `int a[]` vs `int[] a`; the outer loop header (`--i >= 0` vs `i > 0; i--`); `temp` vs `tmp`; `static`; and the method name.

**Contrast 588571 (non-clone, Copy File):**
```java
public static void main(String[] args) throws Exception {
    String uri = args[0];
    Configuration conf = new Configuration();
    FileSystem fs = FileSystem.get(URI.create(uri), conf);
    InputStream in = null;
    try {
        in = fs.open(new Path(uri));
        IOUtils.copyBytes(in, System.out, 4096, false);
    } finally {
        IOUtils.closeStream(in);
    }
}
```

## Results

Normalised similarity, K(q,c) / √(K(q,q)·K(c,c)), where 1 means identical:

| Variant | Kernel | Query vs clone | Query vs non-clone |
|---|---|---|---|
| **A, raw** | STK | 0.981 | 0.378 |
| | SSTK | 0.908 | 0.249 |
| | PTK | 0.986 | 0.611 |
| **B, pruned** | STK | 0.967 | 0.054 |
| | SSTK | 0.870 | 0.026 |
| | PTK | 0.983 | 0.623 |
| **C, abstracted** | STK | 0.994 | 0.871 |
| | SSTK | 0.965 | 0.792 |
| | PTK | 0.989 | 0.741 |
| **D, abstracted + API names** | STK | 0.994 | 0.874 |
| | SSTK | 0.965 | 0.741 |
| | PTK | 0.989 | 0.694 |

Tree sizes (nodes), query / clone / non-clone: A 161 / 169 / 171; B 115 / 123 / 112; C 85 / 91 / 74; D 85 / 91 / 87.

Raw kernel values (K(q,q), K(c,c), K(q,c)) for every row are in the output file.

## What this shows

- **All three kernels score the clone near 1 on every variant.**
- **Abstraction compresses the scale.**
  - On B (names kept, punctuation removed), STK and SSTK give the non-clone almost nothing (0.05 and 0.03): bubble sort and a Hadoop file reader share hardly any names.
  - On C, where names become `ID`/`TYPE`, the non-clone rises to 0.74–0.87, because all Java code shares many small abstract fragments such as `(ID)` and `(method_invocation (ID) (ID) ...)`.
  - So absolute values mean little across variants; what is evaluated is the *ranking* of candidates for each query.
- **PTK behaves differently.** It scores the non-clone about 0.6–0.7 on every variant. Because it matches partial child sequences, it finds common sub-structure (statements in a block, arguments in a call) even when names differ.
- **SSTK is the strictest.** It counts larger fragments, so the different loop headers break more of them (0.87–0.97 for the clone vs 0.97–0.99 for STK and PTK).
- **D equals C for the clone pair**, because bubble sort calls no methods and uses only the primitive type `int`. D differs from C only for the non-clone, which calls `get`, `open`, `copyBytes` and uses class types.
- **Raw values can mislead.** STK's raw score for query vs clone (A: 260.9) is higher than the query's score with itself (260.0). Raw kernels *count shared fragments*, and fragments repeated in one tree can match several times. Normalisation fixes this, since the normalised value is at most 1.

## Reproduce

```bash
cd kernels
CP=target/kernels-0.1.jar:$(cat classpath.txt)
for v in A B C D; do
  java -Dorg.slf4j.simpleLogger.defaultLogLevel=error -cp $CP treekernel.PairSimilarity ../data/trees/$v.tsv 81754 5127007 0.4 0.4
  java -Dorg.slf4j.simpleLogger.defaultLogLevel=error -cp $CP treekernel.PairSimilarity ../data/trees/$v.tsv 81754 588571 0.4 0.4
done
```

Tool: `kernels/src/main/java/treekernel/PairSimilarity.java`. Method IDs and source code: `data/trees/source.tsv`; the location of each method in the raw data: `data/full_bcb/functions.tsv`.

* Where 81754 and 5127007 come from

They aren't file names. They're function IDs from the BigCloneBench database. Its functions table (extracted to data/full_bcb/functions.tsv) records, for each method, which file in your bcb_reduced folder contains it and on which lines:

┌────────────────────┬───────────────────────────────────────────────┬───────┬────────────────────────────────────┐
│    Function ID     │ File in IJaDataset_BCEvalVersion/bcb_reduced/ │ Lines │          Original project          │
├────────────────────┼───────────────────────────────────────────────┼───────┼────────────────────────────────────┤
│ 81754 (query)      │ 7/default/22842.java                          │ 27–37 │ gt-camouflage, .../BubbleSort.java │
├────────────────────┼───────────────────────────────────────────────┼───────┼────────────────────────────────────┤
│ 5127007 (clone)    │ 7/selected/2070032.java                       │ 15–25 │ algstudy, .../BubbleSort.java      │
├────────────────────┼───────────────────────────────────────────────┼───────┼────────────────────────────────────┤
│ 588571 (non-clone) │ 4/default/127477.java                         │ 10–21 │ loonglab, .../FileSystemCat.java   │
└────────────────────┴───────────────────────────────────────────────┴───────┴────────────────────────────────────┘


