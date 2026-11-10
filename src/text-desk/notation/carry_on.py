"""carry_on (a6437): a refused line refuses only itself; the lines after it still run.

Alex, 17 Oct: "I need you to keep going if something gets refused; let's make it so just the one thing gets refused."
Until then a refused line stopped every later line of the reply ('stopped: N later line(s) not run'), and a reply lost
its chat line and three tasks to one stale prop. The property the stop protected (Sable and Juniper, a736: after a
refused create, the next line acted on an older $new) is kept by skipping only the lines that DEPEND on a refused one.

Two halves, one rule:
  - the desk (desk_knife.DeskKnife) judges each line of a reply against what the refused lines before it would have
    made: `$new` after a refused line that might have made something, a handle its `as=` or `set` was to name, a
    title its `title=` was to give. Such a line is not run; it answers 'skipped: depends on the refused line ...'.
    It works the same through deskd, the door, explore.py and the house, since the desk keeps it per reader and reply.
  - whoever sends a reply's lines one by one (explore.py through deskd or the file lock, house.deskd_do) keeps going
    after a refusal and ends with one receipt (Tally) that says what ran, what was refused and why, and what was
    skipped.

A `;` inside one line is still a batch that stops at its first refusal (desk.py): a verb's steps run that way, as a
script. One > line is one command, so a resident's reply never meets it.
"""
import re

import blanks

# Commands that make nothing $new could name. Anything else that is refused (a `do`, a world verb, `set`, a script)
# might have made something, so a later $new could name an older thing: it is skipped.
READS = {"look", "l", "read", "examine", "x", "ex", "find", "table", "why", "compare", "history", "go", "where", "pivot",
         "verbs", "open", "close", "help", "scene", "rows", "clock", "who", "news", "since", "tree"}
# `do` verbs that change a thing but make none, so a refusal of one leaves $new as it was
CHANGES = {"prop", "tag", "untag", "move", "append", "comment", "rewrite", "replace", "retitle", "rename", "due", "resolve",
           "fold", "unfold", "raise", "lower", "sort", "resize", "delete", "remove", "archive", "unlink", "react", "read"}
# values that are words, never a name of a thing: a title there is not a reach for the thing
PROSE = {"line", "text", "title", "why", "note", "words", "reason", "body", "say", "query", "desc", "description", "tip",
         "old", "new", "with"}
SKIP = "skipped: depends on the refused line"
KV = re.compile(r'(?<![^\s])([A-Za-z_][A-Za-z0-9_-]*)=("(?:[^"\\]|\\.)*"|\S+)')
QUOTED = re.compile(r'(?<![=\w])"((?:[^"\\]|\\.)*)"')


def _unq(v):
    return v[1:-1] if len(v) >= 2 and v[0] == v[-1] == '"' else v


def _words(line):
    w = line.strip().split()
    return [x.lower() for x in w[:2]]


def taint(line):
    """What a line that was refused (or skipped) would have made, that a later line might use:
    {'new': bool, 'names': {handle}, 'titles': {lower title}}."""
    w = _words(line)
    cmd = w[0] if w else ""
    out = {"new": False, "names": set(), "titles": set()}
    if not cmd or cmd in READS:
        return out
    if cmd == "set":
        name = line.strip()[3:].partition("=")[0].strip().lstrip("$")
        if name:
            out["names"].add(name)
        return out
    out["new"] = not (cmd == "do" and len(w) > 1 and w[1] in CHANGES)
    for k, v in KV.findall(line):
        if k == "as":
            out["names"].add(_unq(v).lstrip("$"))
        elif k == "title" and out["new"] or k == "title" and cmd == "do" and len(w) > 1 and w[1] in ("retitle", "rename"):
            out["titles"].add(_unq(v).strip().lower())
    out["titles"].discard("")
    return out


def merge(into, more):
    into["new"] = into.get("new") or more["new"]
    into.setdefault("names", {}).update({n: more["line"] for n in more["names"]})
    into.setdefault("titles", {}).update({t: more["line"] for t in more["titles"]})
    if more["new"]:
        into["new_line"] = more["line"]
    return into


def depends(line, held):
    """-> the sentence that skips `line`, or None when it does not use anything the refused lines held back."""
    if not held:
        return None
    for m in blanks.BLANK.finditer(blanks.protect(line)):
        if m.group(0) == blanks.LIT:
            continue
        name = m.group("name")
        if name == "new" and held.get("new"):
            return _skip(held["new_line"], "that line might have made something, so $new here would name an older thing")
        if name in (held.get("names") or {}):
            return _skip(held["names"][name], f"${name} is the name it was to make")
    titles = held.get("titles") or {}
    if titles:
        rest = KV.sub(lambda m: "" if m.group(1) in PROSE else m.group(0), line)
        vals = [_unq(v) for k, v in KV.findall(rest)] + QUOTED.findall(KV.sub("", rest))
        for v in vals:
            t = v.strip().lower()
            if t in titles:
                return _skip(titles[t], f'"{v.strip()}" is the title it was to give')
    return None


def _skip(refused_line, why):
    return (f"{SKIP} (> {_cut(refused_line)}): {why}. Nothing was done; send it again once that line works")


def _cut(text, n=80):
    first = (text or "").splitlines()[0] if text else ""
    return first if len(first) <= n and "\n" not in text else first[:n] + "…"


def refused(text, error=None):
    """Did the desk refuse this line? (the test every sender used before a6437: an error, or ERR in the receipt)"""
    return bool(error) or text.startswith("ERR") or "\nERR" in text


def kind_of(text, error=None):
    """ran | refused | skipped | missed"""
    if text.startswith(SKIP):
        return "skipped"
    if refused(text, error):
        return "refused"
    if text.startswith("MISS "):
        return "missed"
    return "ran"


def reason(text):
    """A refusal's reason, as a receipt quotes it: its first ERR line without the ERR, past any `!! since your last
    look` header (the header is news, not the reason; a5504's notebook entry), and before an `(ids: ...` lesson."""
    lines = text.splitlines()
    for i, l in enumerate(lines):
        if l.startswith("ERR"):
            for r in [l[3:].strip()] + lines[i + 1:]:
                r = r.strip()
                if r and not r.startswith("!!"):
                    return _cut(r.split(" (ids: ")[0], 120)
            return _cut(l[3:].strip(), 120)
    return _cut(text.strip(), 120)


class Tally:
    """The lines of one reply as they come back. summary() is the receipt's end: said only when something was refused
    or skipped, so nobody reads a skipped line as one that ran (a refusal never hides what happened)."""

    def __init__(self):
        self.rows = []

    def add(self, line, text, error=None):
        k = kind_of(text, error)
        self.rows.append((k, line, text))
        return k

    def summary(self):
        kinds = [k for k, _, _ in self.rows]
        if "refused" not in kinds and "skipped" not in kinds:
            return ""
        n = {k: kinds.count(k) for k in ("ran", "refused", "skipped", "missed")}
        head = (f"~ this reply: {len(kinds)} line{'s' if len(kinds) != 1 else ''}; {n['ran']} ran, {n['refused']} refused"
                + (f", {n['skipped']} skipped" if n["skipped"] else "") + (f", {n['missed']} missed" if n["missed"] else "")
                + ". A refused line refuses only itself: the lines after it ran"
                + (", except those that use what it would have made." if n["skipped"] else "."))
        out = [head]
        for k, line, text in self.rows:
            if k == "refused":
                out.append(f"  refused: {_cut(line)}  ({reason(text)})")
            elif k == "skipped":
                out.append(f"  skipped: {_cut(line)}  (depends on the refused line)")
        ran = [_cut(line, 60) for k, line, _ in self.rows if k == "ran"]
        if ran:
            out.append("  ran: " + " | ".join(ran))
        return "\n".join(out)
