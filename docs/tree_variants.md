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
