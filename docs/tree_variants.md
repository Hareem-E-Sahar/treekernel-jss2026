# Tree variants A–D

Tree kernels compare two programs by counting the tree fragments they share. What counts as a fragment depends on how each method is turned into a tree. This project builds four versions of that tree for every method, called variants A–D. Each one keeps or discards different information. Comparing them answers RQ3: which preprocessing choices matter?

All four start from the same parse. tree-sitter-java parses each BigCloneBench function, and the tree is built from the `method_declaration` (or `constructor_declaration`) node. Code: `prep/build_trees.py`. To print the variants for any Java file:

```bash
.venv/bin/python -I prep/show_variants.py path/to/File.java
```

*Revised 2026-10-12: readable labels, statement nodes kept, primitive types kept. See "Change history" at the end.*

## Summary

| Variant | What it keeps | What it removes or replaces | Nodes in the example below |
|---|---|---|---|
| **A, raw** | Everything tree-sitter produces: every keyword, bracket, semicolon, operator, name and literal | nothing | 48 |
| **B, pruned** | Syntactic structure, statements, names, literal text, operators, modifiers (`public`), primitive types (`int`) | punctuation and other keywords (`{ } ( ) ; return if`); single-child chains are collapsed, except through statements and blocks | 27 |
| **C, abstracted** | Structure, statements, operators, modifiers, primitive types | every name becomes `ID`, every class/interface type becomes `TYPE`, literals become `NUM`, `STR`, `CHAR`, `BOOL` or `NULL` | 20 |
| **D, abstracted but keeping API names** | Like C, but **called method names** and **type names** keep their text (`getConnection`, `FileInputStream`) | same as C for everything else | 21 |

What each comparison isolates:
- **A vs B:** does surface syntax (punctuation and keywords) help or just add noise and cost?
- **B vs C:** do identifier and literal names matter? C is what lets the kernel match renamed copies, i.e. Type-2 clones.
- **C vs D:** do API names carry the meaning? Two methods that both call `getConnection` probably do similar things even if every variable is named differently.

## Rules in detail

**A, raw.** Every tree-sitter node becomes a tree node, labelled with its type. Named leaf nodes such as identifiers and literals get one extra child holding their source text. Anonymous tokens (keywords, punctuation) are leaves labelled by the token itself, e.g. `return` or `;`.

**B, pruned.**
1. Only *named* tree-sitter nodes are kept, plus three kinds of anonymous token:
   - operators under `binary_expression`, `unary_expression`, `update_expression` and `assignment_expression` (`==`, `+`, `++`, `+=`);
   - keywords under `modifiers` (`public`, `static`, `final`);
   - the keyword of a primitive type under `integral_type` or `floating_point_type` (`int`, `long`, `short`, `byte`, `char`, `float`, `double`). `boolean` and `void` have their own node types (`boolean_type`, `void_type`) and are distinguishable anyway.
2. Comments are dropped.
3. Literals are kept as single nodes holding their text. The parser splits a string literal into quote and fragment nodes; B doesn't.
4. **Single-child collapsing.** A node with exactly one kept child is replaced by that child. For example, `parenthesized_expression → binary_expression` becomes just `binary_expression`, and a parameter list with one parameter becomes just that parameter. Collapsing **stops at statements and blocks**: any node whose type ends in `_statement`, plus `block`, `constructor_body`, `switch_block` and `class_body`. That way `return x;` stays `(return_statement (ID))` and isn't confused with an expression `x`.

**C, abstracted.** Same as B, then: `identifier` becomes `ID`, `type_identifier` becomes `TYPE`, and literals become `NUM`, `STR`, `CHAR`, `BOOL` or `NULL`. Primitive types stay as they are (`(integral_type (int))`), because they belong to the language, not to the author's naming.

**D, abstracted but keeping API names.** Same as C, except:
- the name of an invoked method stays as `(identifier (getConnection))`;
- every `type_identifier` stays as `(type_identifier (String))`.

The method's own name, variable names and parameter names are still `ID`.

### How symbols are written in labels

KeLP reads a tree as text: `(label child child ...)`. Parentheses mark where a node starts and ends, and whitespace separates nodes, so neither can appear inside a label. KeLP also gives two character sequences a special meaning: `##` (type##content) and `::` (lemma::part-of-speech). Only these are replaced; every other character, including `=`, `;`, `{`, `"` and `!`, is written as is.

| In the code | In the tree | Why |
|---|---|---|
| `(` | `-LRB-` | parenthesis (Penn Treebank convention: Left Round Bracket) |
| `)` | `-RRB-` | parenthesis (Right Round Bracket) |
| space | `·` (middle dot) | whitespace separates nodes |
| tab, newline, carriage return | `-TAB-`, `-NL-`, `-CR-` | whitespace |
| other control or whitespace characters | `-U<hex code>-`, e.g. `-U00A0-` | whitespace |
| `#` | `-HASH-` | `##` is special to KeLP |
| `::` | `-DCOLON-` | special to KeLP; occurs in Java method references such as `String::valueOf` |

Labels are cut at 60 characters, so two string literals that share their first 60 characters get the same label. This is rare, and much rarer than with the previous encoding (see the change history).

Checks run on 2026-10-12 (`kernels/src/main/java/treekernel/ParseCheck.java`): KeLP reads all 19.3M nodes of the 4 × 14,780 trees exactly as written (same node count, same labels in the same order), and all of them as plain labels. No label triggered the `##` or `::` handling.

## Worked example

Input (`examples/Example.java`):

```java
public class Example {
public String foo ( int i ) {

    if ( i == 0) {
        return " Foo ! " ;
    }
    return " Not Foo ! " ;

    }
}
```

The output below is produced by `prep/show_variants.py`; the full output, including the one-line strings KeLP reads, is in `examples/Example.variants.txt`. It is shown as an indented outline: each line is a node, and its children are indented beneath it.

### Variant A, raw (48 nodes)

```
method_declaration
  modifiers
    public
  type_identifier
    String
  identifier
    foo
  formal_parameters
    -LRB-                       (
    formal_parameter
      integral_type
        int
      identifier
        i
    -RRB-                       )
  block
    {
    if_statement
      if
      parenthesized_expression
        -LRB-
        binary_expression
          identifier
            i
          ==
          decimal_integer_literal
            0
        -RRB-
      block
        {
        return_statement
          return
          string_literal
            "
            string_fragment
              ·Foo·!·           " Foo ! " without the quotes; · is a space
            "
          ;
        }
    return_statement
      return
      string_literal
        "
        string_fragment
          ·Not·Foo·!·
        "
      ;
    }
```

### Variant B, pruned (27 nodes)

```
method_declaration
  modifiers
    public
  type_identifier
    String
  identifier
    foo
  formal_parameter              ← formal_parameters had one child: collapsed
    integral_type
      int                       ← primitive type kept
    identifier
      i
  block
    if_statement                ← "if" keyword and the parentheses are gone
      binary_expression
        identifier
          i
        ==
        decimal_integer_literal
          0
      block                     ← blocks are never collapsed
        return_statement        ← statements are never collapsed
          string_literal
            "·Foo·!·"
    return_statement
      string_literal
        "·Not·Foo·!·"
```

### Variant C, abstracted (20 nodes)

```
method_declaration
  modifiers
    public
  TYPE                          String
  ID                            foo
  formal_parameter
    integral_type
      int
    ID                          i
  block
    if_statement
      binary_expression
        ID                      i
        ==
        NUM                     0
      block
        return_statement
          STR                   " Foo ! "
    return_statement
      STR                       " Not Foo ! "
```

### Variant D, abstracted but keeping API names (21 nodes)

```
method_declaration
  modifiers
    public
  type_identifier
    String                      ← type names keep their text
  ID                            foo  (the method's own name is still abstracted)
  formal_parameter
    integral_type
      int
    ID
  block
    if_statement
      binary_expression
        ID
        ==
        NUM
      block
        return_statement
          STR
    return_statement
      STR
```

This example calls no methods, so D differs from C only in `String`. On a typical BigCloneBench function the difference is larger. For example, `conn = DriverManager.getConnection(...)` is `(method_invocation (ID) (ID) ...)` in C but `(method_invocation (ID) (identifier (getConnection)) ...)` in D.

## Variant selection: D chosen (2026-10-16)

This selection was made at KeLP's default setting, when only one variant was going to get the full grid. All four were later tuned (2026-10-17); see "After tuning" below. The variant was picked from data: every variant × kernel at λ = μ = 0.4, on the 50 tuning queries, against the reduced corpus of 14,679 methods. Score = MAP per clone type (RQ1 ground truth), averaged over T1–MT3. Details and reproduction: `results/variant_selection/README.md`.

| Kernel | A raw | B pruned | C abstracted | D + API names |
|---|---|---|---|---|
| STK | 0.866 | 0.864 | 0.800 | **0.895** |
| SSTK | 0.735 | **0.767** | 0.738 | 0.756 |
| PTK | 0.918 | 0.916 | 0.905 | **0.931** |

**Findings.**
- **D is best or tied-best for every kernel.** It wins for STK and PTK; for SSTK, B leads D by 0.011, which is noise (B wins in 69% of bootstrap resamples).
- **D beats C significantly** (paired bootstrap, 95% CI excludes zero): STK +0.095 (+0.040 to +0.154), PTK +0.026 (+0.005 to +0.056). So the rule "prefer C on a near-tie" did not apply.
- **D vs A and B is close.** PTK: D − A = +0.013 (significant but small), D − B = +0.015 (not significant). STK: D − A = +0.029 and D − B = +0.031, both not significant.
- **The differences come almost entirely from ST3 and MT3.** T1, T2 and VST3 are near 1.0 for every variant, so they don't discriminate.
- **SSTK at λ = 0.4 is the weakest kernel on every variant**, mainly on ST3 (0.43–0.58) and MT3. The grid search will show whether a smaller λ helps.
- **Caveats.** Only 10 queries per type; per-variant CIs are about ±0.06. Only the default setting was compared, assuming the ranking of variants doesn't change much with λ and μ.

### C vs D: what differs and why D wins

The only difference is that D keeps the text of **called method names** and **type names** (`getConnection`, `FileInputStream`). C turns them into `ID` and `TYPE`. The method's own name and all variable names are abstracted in both.

- **C over-abstracts.** With every name replaced, different methods can produce *identical* trees. Example: tuning query 162674 (T1) ties at a perfect score of 1.0 with 3 unrelated methods under STK on C, so its true T1 copy no longer ranks first on its own. In D the API names keep such methods apart. STK suffers most (−0.095), because it only counts complete subtrees, and identical abstracted subtrees are common.
- **The gain is partly lexical.** D's API names are vocabulary, the same kind of signal BM25 uses. D is therefore "structure plus API vocabulary", not pure syntax. This must be stated in the paper. The RQ3 comparison of C vs D at default settings measures how much of the tree kernels' performance comes from these names. It also matters for RQ4: D may overlap more with BM25 than C would.
- **Sizes.** D trees are slightly larger: median 160 vs 138 nodes; largest 9,516 vs 8,529 on the full benchmark.

### After tuning (2026-10-17): D confirmed

All four variants were then tuned on the common grid (`results/grid/tuned_comparison/README.md`). Each variant at its own best setting:

| Kernel | A raw | B pruned | C abstracted | D + API names |
|---|---|---|---|---|
| STK | 0.893 | 0.900 | 0.882 | **0.905** |
| SSTK | 0.896 | 0.906 | 0.884 | **0.914** |
| PTK | 0.931 | 0.938 | 0.932 | **0.940** |

- D is best for every kernel, now including SSTK. The default-setting comparison and the tuned comparison agree on D.
- Tuning shrinks the gaps. C needs a large λ for STK (0.689 at λ = 0.1, 0.882 at 0.8): with abstracted names, small shared fragments say little. D − C for STK drops from +0.095 to +0.023 (not significant). So the lexical contribution of D's API names is small once λ is tuned (+0.01 to +0.03), mainly on ST3 and MT3.
- Only PTK keeps significant (and small) differences: D − C +0.008, D − A +0.010.

### Does D make the overflow problem worse than C?

**No: the tunable grid is identical.** This also holds on the common grid adopted on 2026-10-17: 32 of 48 settings are computable on both C and D, the same ones (B: 31, A: 30). The original check, on the earlier grid, follows. On the reduced corpus (`results/grid_scan/main_corpus/scan.tsv`), exactly the same settings are computable on C and D:
- STK: all 4 λ.
- SSTK: λ 0.02–0.4 (7 values).
- PTK: 6 of 9 settings.

D has more overflowing methods in the cells that are *not* computable on either variant:

| Not computable on C or D | Methods overflowing on C | on D |
|---|---|---|
| SSTK λ = 0.6 | 110 | 233 |
| SSTK λ = 0.8 | 515 | 833 |
| SSTK λ = 1.0 | 1,113 | 1,718 |
| PTK (0.4, 0.8) | 25 | 27 |
| PTK (0.8, 0.4) | 1 | 1 |
| PTK (0.8, 0.8) | 1,896 | 1,962 |

This only changes the annotation of those cells in the sensitivity tables. D sits closer to the float limit at the top of the computable range: the largest SSTK self-similarity at λ = 0.4 is 1.5·10²⁹ on D vs 7.9·10²⁴ on C. That is still 9 orders of magnitude below the limit of 3.4·10³⁸.

## Remaining design choices to state in the paper

- **The method's own name is abstracted in D.** Only *called* method names keep their text. That's deliberate, because declaration names like `foo` or `bubbleSort` are chosen by the author and say little about behaviour.
- **Label truncation at 60 characters** (see above).
- **A literal space in the source written as `·`** would collide with an encoded space. No BigCloneBench function was checked for this; it's considered negligible.

## Size of the trees on the full benchmark (14,780 functions)

| Variant | median nodes | 90th percentile | largest |
|---|---|---|---|
| A | 315 | 1,044 | 18,733 |
| B | 199 | 649 | 12,086 |
| C | 138 | 446 | 8,529 |
| D | 160 | 515 | 9,516 |

Kernel cost grows roughly with the product of the two trees' sizes; see `results/timing/README.md`.

## Change history

**2026-10-12.** Three changes, made after the first version was reviewed with `examples/Example.java`:

1. **Readable labels.** Previously every character outside `[A-Za-z0-9_$.]` was written as a hex code, e.g. `_x3d__x3d_` for `==`. Now only the characters in the table above are replaced.
   - Because the hex codes were 5–6 characters per symbol, the 60-character cut-off used to merge different strings. For example, a banner `"====…===="` and `"=================·READY·TO·CALL:·"` both became twelve `_x3d_`, so the kernels counted false matches between them. The new labels are short enough to stay distinct.
   - Variant A's structure is unchanged. On 30,000 query–candidate pairs, A's kernel values changed only by float rounding (median change 0, 99.9% of pairs < 5·10⁻⁵ relative), except where such false matches disappeared.
2. **Statements and blocks are no longer collapsed** (B–D). Before, `return " Foo ! ";` collapsed to just the string literal, so `return x;` and a bare `x;` looked identical.
3. **Primitive types are kept** (B–D). Before, `int`, `long`, `double` etc. all became an empty `integral_type`/`floating_point_type` node.

Changes 2 and 3 make B–D trees larger: B's median went from 187 to 199 nodes, C's from 127 to 138 and D's from 148 to 160. All timing and pilot-retrieval results were rerun on the new trees.
