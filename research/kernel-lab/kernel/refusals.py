"""EDITING THE KERNEL (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
The kernel changes only to give every world a general capability: a word, a check, a kind of fact any app, module or
person can use. It never names its tenants: no app, module, person, kind or field name appears in this code except the
kernel's own (word, rule, kind, grant, person, ...). If your change needs `if kind == "..."`, a person's name or one app's
field, stop: the missing piece is a general word (a kind's policy, a rule step, a reading). Build that, or put it on the
Board. Names already here are debt (research/source-edits/SOURCE-AUDIT-KERNEL.md lists them); take them out when you can.

Refusals and errors, kept where someone can read them (board card dk939, Alex 27 Oct 2026: "every refused line and
error, from any button, word or agent, should land in one readable log").

Every line runs through Kernel.run, so a refusal is caught there once, at the outermost run on that thread (a `press`
that runs its button's line inside is one refusal, not two). Also kept: a word that broke (an error, not a refusal),
a module that died or whose message failed in the kernel, a module's announcement refused, a painted drop refused before
its line ran, and what a page says failed outside any line (`failed why=…`: a frame that stopped, a native call).

Where it lives. Not in the world log: a refusal is the promise that nothing was written, and a world that recorded
every refused poll would grow without being changed. It is an event, not visual state, so it is not the screen's
either: it is kept beside the world, in <world>/keep/refusals.jsonl (the last KEEP entries, read back on start), the
way sessions and seen-marks are kept. The same refusal said again (a bar polling a word that is down) is counted on
its first entry, not written again, so one broken poll is one row with ×N.

Who sees: a steward sees everyone's; anyone else sees their own (and what a module or widget did for them).

    refusals [by=<name|me>] [limit=<n>] [errors] [all]
"""
import json
import re
import threading
import time
import traceback

KEEP = 1000          # entries kept in the file and in memory
SAME_WITHIN = 40     # a refusal equal to one of the last this many is counted on it, not kept again


class Refusals:
    def __init__(self, k):
        self.k = k
        self.lock = threading.Lock()
        self.path = k.keep_dir / "refusals.jsonl"
        self.rows = []
        self.n = 0
        self._writes = 0
        try:
            for line in self.path.read_text(encoding="utf-8").splitlines()[-KEEP:]:
                try:
                    self.rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        except OSError:
            pass
        self.n = max((r.get("n", 0) for r in self.rows), default=0)

    # ------------------------------------------------------------------ keeping
    def keep(self, why, line="", actor=None, by=None, via="line", kind="refused", where=None, mode=None,
             vouched=False, code=None):
        """One refusal or error. Never raises: a log that breaks must not break the act it is logging.
        vouched: the reason is a `Refused(kept=)` text, written to be read by others (ids and counts, no titles).
        code: an error's exception class and code place, which others may read without its message."""
        try:
            self._keep(why, line, actor, by, via, kind, where, mode, vouched, code)
        except Exception:                                  # noqa: BLE001
            pass

    def _keep(self, why, line, actor, by, via, kind, where, mode, vouched=False, code=None):
        why = str(why or "").removeprefix("refused: ").strip()[:1500]
        line = str(line or "").strip()[:500]
        if actor is not None:
            by, person = actor.id, actor.person
            caller = getattr(actor, "caller", None)
            if actor.kind == "module" and caller is None:
                person = None                              # a module on its own, for nobody
        else:
            person = None
        via = getattr(self.k._local, "via", None) or via
        if getattr(self.k._local, "rule", None):
            via = "rule"
        now = self.k.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        with self.lock:
            for r in reversed(self.rows[-SAME_WITHIN:]):
                if (r.get("by"), r.get("line"), r.get("why"), r.get("kind")) == (by, line, why, kind):
                    r["times"] = r.get("times", 1) + 1
                    r["last"] = now
                    self._write(rewrite=True)
                    return
            self.n += 1
            row = {"n": self.n, "at": now, "kind": kind, "by": by, "person": person, "via": via,
                   "line": line, "why": why}
            if where:
                row["where"] = str(where)[:120]
            if mode:
                row["mode"] = mode
            if vouched:
                row["vouched"] = True
            if code:
                row["code"] = str(code)[:160]
            if getattr(self.k._local, "rule", None):
                row["rule"] = self.k._local.rule
            self.rows.append(row)
            del self.rows[:-KEEP]
            self._write(row=row)

    def _write(self, row=None, rewrite=False):
        """Append; every so often (and on a repeat) write the kept tail whole, so the file stays KEEP long."""
        self._writes += 1
        try:
            if rewrite or self._writes % 200 == 0:
                tmp = self.path.with_suffix(".tmp")
                tmp.write_text("".join(json.dumps(r) + "\n" for r in self.rows), encoding="utf-8")
                tmp.replace(self.path)
            elif row is not None:
                with open(self.path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(row) + "\n")
        except OSError:
            pass

    def error(self, exc, line="", actor=None, via="line"):
        """A word that broke: its exception and the last place in our code it passed through."""
        try:
            exc.agora_kept = True                          # so an outer catcher does not keep it twice
        except AttributeError:
            pass
        tb = traceback.extract_tb(exc.__traceback__)
        at = f" at {tb[-1].filename.rsplit('kernel-lab', 1)[-1]}:{tb[-1].lineno}" if tb else ""
        self.keep(f"{type(exc).__name__}: {exc}{at}", line, actor=actor, via=via, kind="error",
                  code=f"{type(exc).__name__}{at}")

    # ------------------------------------------------------------------ reading
    def visible(self, reader):
        """The rows this reader may see: a steward all of them; anyone else their own."""
        k = self.k
        steward = k.is_steward(reader.person) or k.is_steward(reader.id)
        with self.lock:
            rows = list(self.rows)
        if steward:
            return rows
        return [r for r in rows if reader.id in (r.get("by"), r.get("person")) or
                (reader.person and r.get("person") == reader.person)]

    def who(self, r):
        by, person = r.get("by"), r.get("person")
        k = self.k
        if not by:
            return "a page"
        name = k.name(by) if by in k.state.things else str(by)
        if person and person != by:
            name += f" for {k.name(person) if person in k.state.things else person}"
        return name


def _seen_part(k, actor, r):
    """Someone else's line as this reader may see it: its word, and its thing when the reader can see that thing."""
    parts = str(r.get("line") or "").split()
    if not parts:
        return "(no line)"
    word = parts[0] if parts[0] != "do" or len(parts) == 1 else parts[1]
    rest = parts[1:] if parts[0] != "do" else parts[2:]
    target = rest[0] if rest and k.state.things.get(rest[0]) is not None else None
    if target is None:
        return f"{word} …" if rest else word
    if k.shown(actor.person, target) is None:
        return f"{word} (a thing you can't see) …"
    return f"{word} {target}" + (" …" if len(rest) > 1 else "")


CODE = re.compile(r"\b([A-Z][A-Za-z]*(?:Error|Exception|Interrupt|Exit|Warning))\b|\bat\s+([\w./\\-]+:\d+)")


def _someone_elses(k, r, mine):
    """Whether this row holds someone else's words: a person's line, or the line of a module acting for someone
    else (round 2: a relay installed for a member said the member's data). A module for nobody, or for the place,
    keeps its rows readable to stewards: they are how a broken module is found. (A module's faults stay readable
    either way; `_redacted` keeps their reason.) Only stewards read others' rows at all (`visible`), and a steward's
    own rows stay whole for the place's other stewards: they run it together, and dk939 asked for one readable log
    among them (Alex's and his agents' lines for JEFF). The redaction is for members' words."""
    if {r.get("by"), r.get("person")} & mine:
        return False
    if r.get("person"):
        return not k.is_steward(r["person"])
    by = r.get("by")
    if by and k.state.get(by, "kind") == "module":
        f = k.state.get(by, "for")
        return bool(f) and f not in mine and not k.is_steward(f)
    return False


def _redacted(k, actor, r):
    """Someone else's row without its line or its own reason."""
    seen_target_hidden = "(a thing you can't see)" in _seen_part(k, actor, r)
    out = {key: v for key, v in r.items() if key not in ("line", "why")}
    kind = r.get("kind")
    if kind == "refused":
        why = str(r.get("why") or "")
        out["why"] = why.split("\nnot run:")[0] if r.get("vouched") and not seen_target_hidden else "refused"
    elif not r.get("person"):
        out["why"] = r.get("why", "")                    # a module's own fault: its stderr tail, for whoever mends it
    else:
        code = r.get("code") or " ".join(a or f"at {b}" for a, b in CODE.findall(str(r.get("why") or "")))
        out["why"] = f"{kind}: {code}" if code else str(kind)
    return out


def refusals(k, actor, st, entry, tx, group, saw=None):
    """refusals [by=<name|me>] [limit=<n>] [errors] [all]: the latest refused lines and errors, newest first."""
    from .kernel import Refused
    kv, flags = st.kv, set((st.words or "").split())
    if st.target:
        flags.add(st.target)
    limit = str(kv.get("limit", "15"))
    if not limit.isdecimal():
        raise Refused("limit= takes a number, like limit=30")
    limit = min(int(limit), 200)
    by = kv.get("by")
    log = k.refusals
    rows = log.visible(actor)
    if "errors" in flags:
        rows = [r for r in rows if r.get("kind") != "refused"]
    if by == "me":
        mine = {actor.id, actor.person} - {None}
        rows = [r for r in rows if r.get("by") in mine or r.get("person") in mine]
    elif by:
        b = by.casefold()
        rows = [r for r in rows if b in log.who(r).casefold() or b in (str(r.get("by")).casefold(),
                                                                       str(r.get("person")).casefold())]
    if "all" not in flags:
        rows = rows[-limit:]
    rows = list(reversed(rows))
    out = []
    mine = {actor.id, actor.person} - {None}
    for r in rows:
        when = str(r.get("at", ""))[11:16]
        times = f" ×{r['times']} (last {str(r.get('last', ''))[11:16]})" if r.get("times", 1) > 1 else ""
        what = f"{r['line']}" if r.get("line") else "(no line)"
        if _someone_elses(k, r, mine):
            # someone else's line: never more than the reader could see (security review H2, 28 Oct: a steward
            # resident read a member's words to a chat he can't see; round 2: the rows carried the line too, and a
            # reason quoting a name showed whenever the line named a thing instead of giving its id). So the row
            # loses its line and reason; it says the word, its thing if visible, and only a reason its author
            # vouched for (`Refused(kept=)`), or an error's class and code place.
            what, r = _seen_part(k, actor, r), _redacted(k, actor, r)
            r["seen"] = what
        via = f" via {r['via']}" if r.get("via") not in (None, "line") else ""
        where = f" in {r['where']}" if r.get("where") else ""
        tag = "" if r.get("kind") == "refused" else f" [{r.get('kind')}]"
        out.append(dict(r, who=log.who(r),
                        text=f"#{r['n']} {when}{times} {log.who(r)}{via}{where}{tag}: {what}\n      → {r.get('why', '')}"))
    steward = k.is_steward(actor.person) or k.is_steward(actor.id)
    head = (f"{len(out)} latest refusal{'' if len(out) == 1 else 's'} and errors"
            + (" (everyone's: you are a steward)" if steward else " of yours")
            + (f" by {by}" if by else ""))
    if not out:
        return {"text": head + "; none kept. Every refused line, broken word, module that died and page failure "
                               "lands here.", "rows": []}
    return {"text": head + ", newest first:\n" + "\n".join("  " + r["text"] for r in out), "rows": out}


def failed(k, actor, st, entry, tx, group, saw=None):
    """failed why="…" [line="…"] [where=<page>]: a page or agent says something failed outside any line. It writes
    nothing in the world; it lands in refusals."""
    from .kernel import Refused
    why = st.kv.get("why") or st.words
    if not str(why or "").strip():
        raise Refused('failed why="what went wrong" [line="the line it was running"] [where=dock]')
    k.refusals.keep(why, st.kv.get("line", ""), actor=actor, via="page", kind="failed", where=st.kv.get("where"))
    return {"text": f"kept in refusals: {str(why)[:120]}"}
