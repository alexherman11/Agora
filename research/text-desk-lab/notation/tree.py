"""tree: the one reader of an indented text (9 Oct 2026, step 5 of the grammar unification).

A lens, a style and a kind note's slot lines are all written the same way: a line is a thing said, and a line indented
under another belongs to it. Before this module each reader counted its own spaces (scene.parse, style.parse and
table.declared each had a copy of the rule, and juniper-7 found that a chat's print re-indented at column zero broke
every one of them in its own way). Now there is one rule, here, and the readers say what the lines mean.

    nodes = tree.read(text)            # -> [Node]; Node.text is the line without its comment, Node.kids its children
    for n in tree.walk(nodes): ...     # every node, in line order

A comment is a line beginning with `#`, or ` # ` with a space either side outside quotes (a colour `#2F6B4F` on a token
line is not one, since the `#` has no space after it). Blank lines are skipped. A child is a line indented more than
the nearest line above it with a smaller indent. What an unindented line must be (a lens's part, a style's token or
role) is each reader's own rule.
"""
import re


class Node:
    __slots__ = ("line", "indent", "text", "raw", "kids", "parent")

    def __init__(self, line, indent, text, raw):
        self.line, self.indent, self.text, self.raw = line, indent, text, raw
        self.kids, self.parent = [], None

    def __repr__(self):
        return f"Node({self.line}, {self.indent}, {self.text!r}, kids={len(self.kids)})"


def outside_quotes(line, sep):
    """Split `line` at `sep` wherever it is not inside double quotes (a `\"` does not close them) and not inside
    brackets (9 Oct: `let wk = week-of(day-n(d, 10)), role x` is two words; the comma in the call is the call's)."""
    out, cur, q, depth, i = [], "", False, 0, 0
    while i < len(line):
        if line[i] == '"' and (i == 0 or line[i - 1] != "\\"):
            q = not q
        if not q and line[i] in "()":
            depth = max(0, depth + (1 if line[i] == "(" else -1))
        if not q and depth == 0 and line.startswith(sep, i):
            out.append(cur)
            cur, i = "", i + len(sep)
            continue
        cur += line[i]
        i += 1
    out.append(cur)
    return out


def is_comment(text):
    """A line that is a comment: `#` first, unless it is a colour (`#fff`, `#2F6B4F`) written where a value goes."""
    return text.startswith("#") and not re.match(r"^#[0-9a-fA-F]{3,8}\b", text)


def read(src, skip=None):
    """-> the top-level nodes of `src`, each with its kids. `skip(text)` may say a further line is not a node (a lens's
    `lens <name>` header)."""
    roots, stack = [], []
    for n, raw in enumerate(re.split(r"\r?\n", src or ""), 1):
        line = outside_quotes(raw, " # ")[0].rstrip()
        text = line.strip()
        if not text or is_comment(text) or (skip and skip(text, len(line) - len(line.lstrip()))):
            continue
        indent = len(line) - len(line.lstrip())
        node = Node(n, indent, text, raw)
        while stack and stack[-1].indent >= indent:
            stack.pop()
        if stack:
            node.parent = stack[-1]
            stack[-1].kids.append(node)
        else:
            roots.append(node)
        stack.append(node)
    return roots


def walk(nodes):
    """Every node under `nodes`, in line order."""
    for n in nodes:
        yield n
        yield from walk(n.kids)


def lines(src, skip=None):
    """The nodes as a flat list, for a reader that wants lines with the comment rule and nothing else."""
    return list(walk(read(src, skip)))
