"""Code-aware tokenisation for BM25 (PLAN.md §5.2, decided 2026-10-18).

Every word-like token of the method source is kept (keywords, identifiers, numbers, and the
words inside literals and comments); punctuation and operators are dropped. An identifier made
of several parts (camelCase, snake_case, digits) is emitted in full and as its parts, all
lowercased:  getConnection -> getconnection get connection;  MAX_SIZE -> max_size max size;
XMLParser2 -> xmlparser2 xml parser 2.
The result is a whitespace-separated string, indexed with a whitespace tokenizer.
"""
import re

WORD = re.compile(r"[A-Za-z_$À-￿][A-Za-z0-9_$À-￿]*|\d+")
PART = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-zÀ-￿]+|[A-Z]+|\d+")


def tokens(code):
    out = []
    for w in WORD.findall(code):
        out.append(w.lower())
        parts = [p for s in re.split(r"[_$]+", w) if s for p in PART.findall(s)]
        if len(parts) > 1:
            out.extend(p.lower() for p in parts)
    return out


def unescape(s):
    """Inverse of build_trees.py's escaping of source_escaped (\\\\, \\t, \\n)."""
    return re.sub(r"\\(\\|t|n)", lambda m: {"\\": "\\", "t": "\t", "n": "\n"}[m.group(1)], s)


if __name__ == "__main__":
    for s in ["getConnection", "MAX_SIZE", "XMLParser2", "fis.read(b) > 0", "label.setText(\"您没有\")"]:
        print(s, "->", " ".join(tokens(s)))
