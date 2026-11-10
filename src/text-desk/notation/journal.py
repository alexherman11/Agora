"""journal: the world as an append-only log of batches of per-(referent, aspect) operations. Sable's prototype.

Not wired into the desk. Nothing running imports it; test_journal.py exercises it beside the baseline. Design:
research/object-facet-frontier/sable-7-journal-draft-2.md.

    j = Journal(path)                          open (a torn last line is dropped: that batch was never acknowledged)
    seq = j.commit(actor, observer, cmd, ops=[(gid, aspect, value)], reads=[[gid, aspects, seen]])
    j.value(gid, aspect)                       the current value, by assignment replay (no verb, rule or script runs)
    j.undo(seq, actor, observer)               inverse ops, per aspect, while each aspect still holds its after
    merge(base, fork, F, name, by)             ops after F: clean ones land, agreed ones are counted, the rest are held

A line is {v, seq, at, actor, observer, cmd, cause, reads, ops} or, for a refused batch, the same with `refused`
and no ops. `seq` is the line number and is never reused. The receipt comes back only after fsync.
"""

import json
import os
import secrets
import time
from pathlib import Path

V = 1
ABSENT = None       # the value of an aspect nothing has written


class Refusal(Exception):
    def __init__(self, why, seq=None):
        super().__init__(why)
        self.why, self.seq = why, seq


def gid():
    """A global id: millisecond time plus 40 random bits (Milestone One's shape). A fork keeps it."""
    return f"{int(time.time() * 1000):011x}{secrets.token_hex(5)}"


class Journal:
    def __init__(self, path, fsync=True):
        self.path, self.fsync = Path(path), fsync
        self.lines, self.torn = [], 0
        self._state = {}                  # (gid, aspect) -> value
        self._last = {}                   # (gid, aspect) -> seq of the last op that wrote it
        self._writes = {}                 # (gid, aspect) -> [seq, ...] in order
        if self.path.exists():
            raw = self.path.read_bytes()
            keep = raw.rfind(b"\n") + 1
            self.torn = len(raw) - keep
            if self.torn:                 # an unacknowledged tail: drop it so the next line starts clean
                with open(self.path, "r+b") as f:
                    f.truncate(keep)
            for line in raw[:keep].decode("utf-8").splitlines():
                if line.strip():
                    self._take(json.loads(line))

    # ---- reading --------------------------------------------------------------------------------------------
    def _take(self, rec):
        self.lines.append(rec)
        for op in rec.get("ops") or []:
            key = tuple(op["target"])
            self._state[key] = op["after"]
            self._last[key] = rec["seq"]
            self._writes.setdefault(key, []).append(rec["seq"])

    def value(self, g, aspect):
        return self._state.get((g, aspect), ABSENT)

    def line(self, seq):
        return self.lines[seq - 1]

    @property
    def head(self):
        return len(self.lines)

    def written_since(self, g, aspects, seen, observer=None):
        """The first committed op on (g, any of aspects) after seq `seen`, not by this observer; None if none.
        aspects '*' means every aspect of g. An undo's inverse ops are ordinary ops, so an undo is seen."""
        for rec in self.lines[seen:]:
            if rec.get("refused") or (observer and rec.get("observer") == observer):
                continue
            for op in rec["ops"]:
                if op["target"][0] == g and (aspects == "*" or op["target"][1] in aspects):
                    return rec, op
        return None

    def readers_since(self, g, aspect, seq):
        """Later batches that read (g, aspect): what rests on a value, for undo's one sentence."""
        out = []
        for rec in self.lines[seq:]:
            for r in rec.get("reads") or []:
                if r[0] == g and (r[1] == "*" or aspect in r[1]):
                    out.append(rec)
                    break
        return out

    # ---- writing --------------------------------------------------------------------------------------------
    def _append(self, rec):
        rec = dict(rec, v=V, seq=self.head + 1, at=rec.get("at") or time.strftime("%Y-%m-%dT%H:%M:%S"))
        data = (json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        with open(self.path, "ab") as f:
            f.write(data)
            f.flush()
            if self.fsync:
                os.fsync(f.fileno())
        self._take(rec)
        return rec["seq"]

    def _refuse(self, actor, observer, cmd, reads, aspects, why, public=None):
        """The line keeps the fact (who, when, which aspects, the reads, the fence's sentence without values); the
        person gets the full sentence, and the refused values go to their viewer store, not to shared history."""
        seq = self._append({"actor": actor, "observer": observer, "cmd": (cmd or "").split(" ", 1)[0], "reads": reads or [],
                            "refused": {"aspects": aspects, "why": public or why}, "ops": []})
        raise Refusal(why, seq)

    def commit(self, actor, observer, cmd, ops, reads=(), cause=None, by_def=None, extra=None):
        """One batch: every op lands in one line, or a refusal line is written and Refusal raised.
        ops: [(gid, aspect, after)] or [(gid, aspect, after, by_def)]. Equal writes coalesce; unequal refuse."""
        reads = [list(r) for r in reads]
        staged, who = {}, {}
        for op in ops:
            g, a, after = op[0], op[1], op[2]
            src = op[3] if len(op) > 3 else by_def
            if (g, a) in staged and staged[(g, a)] != after:
                both = f"{who[(g, a)] or 'your line'} and {src or 'your line'} both wrote {a} of {g}"
                self._refuse(actor, observer, cmd, reads, [[g, a]],
                             f"{both}: {staged[(g, a)]!r} and {after!r}; nothing was written", f"{both}; nothing was written")
            staged[(g, a)], who[(g, a)] = after, src
        for g, aspects, seen in reads:
            hit = self.written_since(g, aspects, seen, observer)
            if hit:
                rec, op = hit
                self._refuse(actor, observer, cmd, reads, [op["target"]],
                             f"stale: {op['target'][1]} of {g} changed at seq {rec['seq']} by {rec['actor']}"
                             f"{' (an undo of seq ' + str(rec['undo']) + ')' if rec.get('undo') else ''} after you saw seq {seen}; look again")
        rows = []
        for (g, a), after in staged.items():
            before = self.value(g, a)
            if before == after:
                continue                                  # a write that changes nothing is not an op
            row = {"target": [g, a], "before": before, "after": after}
            if who[(g, a)]:
                row["by_def"] = who[(g, a)]
            rows.append(row)
        rec = {"actor": actor, "observer": observer, "cmd": cmd, "cause": cause, "reads": reads, "ops": rows}
        rec.update(extra or {})
        return self._append(rec)

    def undo(self, seq, actor, observer, cmd=None):
        """Inverse of batch `seq`, per (gid, aspect): allowed while each aspect still holds that batch's after.
        Returns (new seq, notes): notes say which later batches read a value the undo changes (they keep theirs)."""
        rec = self.line(seq)
        if rec.get("refused"):
            raise Refusal(f"seq {seq} was refused; there is nothing to undo")
        if not rec["ops"]:
            raise Refusal(f"seq {seq} changed nothing")
        inv, notes = [], []
        for op in rec["ops"]:
            g, a = op["target"]
            if self.value(g, a) != op["after"]:
                later = self.line(self._last[(g, a)])
                raise Refusal(f"{a} of {g} was changed after seq {seq} by {later['actor']} at seq {later['seq']} "
                              f"({later['cmd']!r}); undo that first, or write the value you want: {a}={op['before']!r}")
            inv.append((g, a, op["before"]))
            for r in self.readers_since(g, a, seq):
                if r["actor"] != actor or r.get("cause") != seq:
                    notes.append(f"seq {r['seq']} ({r['cmd']!r}, {r['actor']}) read {a} of {g} and keeps what it read")
        return self.commit(actor, observer, cmd or f"undo {seq}", inv, cause=seq, extra={"undo": seq}), notes

    def undone(self, seq):
        return any(r.get("undo") == seq for r in self.lines[seq:])


def fork(base, path):
    """A fork is a copy of the base's lines to its head; F is that head."""
    Path(path).write_bytes(base.path.read_bytes() if base.path.exists() else b"")
    return Journal(path, base.fsync), base.head


def merge(base, fork_j, F, name, by):
    """Merge the fork's ops after F into the base. Per (gid, aspect): clean (only the fork wrote it), agreed
    (both wrote the same last value) or held (both wrote, differently). Clean ones land now in one batch that
    keeps each op's author and time; held ones are returned for take / keep / set. Nothing is re-run.
    Where the last merge of this fork stopped is recorded in the base, so the fork is only read."""
    upto = max([r.get("merged", {}).get("upto", F) for r in base.lines if r.get("merged", {}).get("from") == name] + [F])
    mine = {}
    for rec in fork_j.lines[upto:]:
        if rec.get("refused"):
            continue
        for op in rec["ops"]:
            key = tuple(op["target"])
            first = mine.get(key, {}).get("before", op["before"])
            mine[key] = {"before": first, "after": op["after"], "actor": rec["actor"], "at": rec["at"], "seq": rec["seq"]}
    clean, agreed, held = [], [], []
    for key, m in mine.items():
        theirs = [s for s in base._writes.get(key, []) if s > F and not base.line(s).get("merged", {}).get("from") == name]
        if not theirs:
            clean.append((key, m))
        elif base.value(*key) == m["after"]:
            agreed.append((key, m))
        else:
            held.append({"target": list(key), "here": base.value(*key), "there": m["after"], "by_there": m["actor"],
                         "by_here": base.line(theirs[-1])["actor"]})
    seq = None
    if clean:
        ops = [(k[0], k[1], m["after"]) for k, m in clean]
        seq = base.commit(by, by, f"merge {name}", ops,
                          extra={"merged": {"from": name, "upto": fork_j.head, "by": by},
                                 "origin": {f"{k[0]} {k[1]}": [m["actor"], m["at"], m["seq"]] for k, m in clean}})
    elif mine:
        seq = base._append({"actor": by, "observer": by, "cmd": f"merge {name}", "ops": [],
                            "merged": {"from": name, "upto": fork_j.head, "by": by}})
    return {"seq": seq, "clean": len(clean), "agreed": len(agreed), "held": held}


def resolve(base, held, choice, by, value=None):
    """take: the fork's value; keep: the base's (records the decision, writes nothing); set: a new value."""
    g, a = held["target"]
    if choice == "keep":
        return base._append({"actor": by, "observer": by, "cmd": f"keep {a} of {g}", "ops": [], "kept": held})
    after = held["there"] if choice == "take" else value
    return base.commit(by, by, f"{choice} {a} of {g}", [(g, a, after)])


class Aliases:
    """Short ids per world, one space per family. A fork gets a disjoint block, so a merge inside the family never
    renames. A write by short id is refused when the writer last saw that alias name another gid."""

    BLOCK = 1000

    def __init__(self):
        self.to_gid, self.of_gid, self.n, self.reserved = {}, {}, 0, []

    def _free(self, n):
        return not any(lo <= n < hi for lo, hi in self.reserved)

    def mint(self, prefix, g):
        self.n += 1
        while not self._free(self.n):
            self.n += 1
        short = f"{prefix}{self.n:02d}"
        self.to_gid[short], self.of_gid[g] = g, short
        return short

    def fork(self):
        lo = (max([self.n] + [hi for _, hi in self.reserved]) // self.BLOCK + 1) * self.BLOCK
        self.reserved.append((lo, lo + self.BLOCK))
        child = Aliases()
        child.to_gid, child.of_gid = dict(self.to_gid), dict(self.of_gid)
        child.n, child.reserved = lo - 1, [(0, lo), (lo + self.BLOCK, 10 ** 9)]
        return child

    def adopt(self, g, short):
        """A merge brings a thing home: it keeps its short id unless that id names something else here."""
        if self.to_gid.get(short, g) == g:
            self.to_gid[short], self.of_gid[g] = g, short
            return short
        return self.mint(short.rstrip("0123456789"), g)

    def resolve(self, short, was=None):
        """`was` is the gid this person's last read of `short` resolved to, in whatever world (their viewer store)."""
        g = self.to_gid.get(short)
        if g is None:
            raise Refusal(f"no {short} here")
        if was is not None and was != g:
            raise Refusal(f"{short} here is {g[-6:]}, but you last saw {short} as {was[-6:]}; "
                          f"that thing is {self.of_gid.get(was, 'not here')} here")
        return g


# ---- text as hunks: where the journal meets the text gateway ------------------------------------------------------
# A document's text is not one value but hunks, each its own aspect text:<hid> with value {after, body}. `after` is
# the hunk it was inserted after (None = the top); it never changes, and a deleted hunk keeps its place with body None
# (a tombstone), so an insert never needs to read its neighbour. Siblings after one anchor order newest first (RGA).
# The whole text is derived. The prototype's hunk is a line; the anchors experiment argues for quote-fenced sentences.

def _hunks_in(state, doc):
    items = {a[5:]: v for (g, a), v in state.items() if g == doc and a.startswith("text:") and v is not None}
    kids = {}
    for hid, v in items.items():
        kids.setdefault(v["after"], []).append(hid)
    out, order = [], []

    def walk(anchor):
        for hid in sorted(kids.get(anchor, []), reverse=True):
            order.append(hid)
            walk(hid)
    walk(None)
    for hid in order:
        out.append((hid, items[hid]["body"]))
    return out


def state_at(j, upto):
    st = {}
    for rec in j.lines[:upto]:
        for op in rec.get("ops") or []:
            st[tuple(op["target"])] = op["after"]
    return st


def hunks(j, doc, upto=None):
    return _hunks_in(j._state if upto is None else state_at(j, upto), doc)


def text(j, doc, upto=None):
    return "\n".join(b for _, b in hunks(j, doc, upto) if b is not None)


def text_ops(j, doc, new_text, seen=None):
    """The gateway: diff new_text against the hunks the writer SAW (at seq `seen`), never against what is there now,
    and return (ops, reads). A changed or deleted hunk is read; an inserted one reads nothing."""
    import difflib
    seen = j.head if seen is None else seen
    st = state_at(j, seen)
    saw = [(h, b) for h, b in _hunks_in(st, doc) if b is not None]
    old, new = [b for _, b in saw], new_text.split("\n")
    ops, touched = [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        pairs = min(i2 - i1, j2 - j1) if tag == "replace" else 0
        for k in range(pairs):
            h = saw[i1 + k][0]
            ops.append((doc, f"text:{h}", {"after": st[(doc, f"text:{h}")]["after"], "body": new[j1 + k]}))
            touched.append(f"text:{h}")
        for k in range(i1 + pairs, i2):                       # deleted: a tombstone keeps its place
            h = saw[k][0]
            ops.append((doc, f"text:{h}", {"after": st[(doc, f"text:{h}")]["after"], "body": None}))
            touched.append(f"text:{h}")
        anchor = saw[i1 + pairs - 1][0] if i1 + pairs > 0 else None
        for k in range(j1 + pairs, j2):                       # inserted: after the hunk before it, as a chain
            h = gid()
            ops.append((doc, f"text:{h}", {"after": anchor, "body": new[k]}))
            anchor = h
    reads = [[doc, touched, seen]] if touched else []
    return ops, reads
