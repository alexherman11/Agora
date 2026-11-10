"""EDITING THE KERNEL (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
The kernel changes only to give every world a general capability: a word, a check, a kind of fact any app, module or
person can use. It never names its tenants: no app, module, person, kind or field name appears in this code except the
kernel's own (word, rule, kind, grant, person, ...). If your change needs `if kind == "..."`, a person's name or one app's
field, stop: the missing piece is a general word (a kind's policy, a rule step, a reading). Build that, or put it on the
Board. Names already here are debt (docs/design/source-edits/SOURCE-AUDIT-KERNEL.md lists them); take them out when you can.

Lines: the one language in (SHAPE section 9, steps 1 and 2).

`split_batch` is the desk's own, copied unchanged from src/text-desk/notation/desk.py (reused, SHAPE section 12).
`parse` is new: the desk has no single parser to lift, so this one gives every word the same surface:
    word [target] [k=v ...] [words]
"""
import re
import shlex

ID = re.compile(r"^[a-z]{2,4}\d+$")        # a thing's id: its world's tag, then a number (sb42)
RECORD = re.compile(r"^r\d+$")             # a record in this world's log (r812)
KEY = re.compile(r"^[a-z_][a-z0-9_.-]*=")


def split_batch(line):
    """Split on ; or newlines outside quotes."""
    out, cur, q, esc = [], "", None, False
    for ch in line or "":
        if q:
            cur += ch
            if esc:
                esc = False
            elif ch == "\\":
                esc = True   # an escaped quote inside a value does not close it (export writes \" inside text=)
            elif ch == q:
                q = None
        elif ch in "\"'":
            q = ch
            cur += ch
        elif ch in ";\n":
            if cur.strip():
                out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out or [""]


class Step:
    def __init__(self, text, word, target, kv, words):
        self.text, self.word, self.target, self.kv, self.words = text, word, target, kv, words

    def __repr__(self):
        return f"Step({self.word!r}, target={self.target!r}, kv={self.kv!r}, words={self.words!r})"


def parse(text):
    """One step -> Step. Quotes group words; a line shlex can't split (an apostrophe: `post it's fine`) is split on
    spaces, as the desk does for a verb's words."""
    text = text.strip()
    try:
        toks = shlex.split(text)
    except ValueError:
        toks = text.split()
    if not toks:
        return Step(text, "", None, {}, "")
    word, rest = toks[0].lower(), toks[1:]
    target, kv, words = None, {}, []
    for i, t in enumerate(rest):
        if KEY.match(t):
            k, v = t.split("=", 1)
            kv[k] = v
        elif target is None and not words and (ID.match(t) or RECORD.match(t)):
            target = t
        else:
            words.append(t)
    step = Step(text, word, target, kv, " ".join(words))
    # Modules handling file paths need the original argument boundaries.
    step.positional = [t for t in rest if not KEY.match(t)]
    return step
