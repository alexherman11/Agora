"""kext: the little the desktop needs from the kernel that the kernel does not have yet, as an extension in my folder.

Draft by Claude (PROOF a13428), 23 Oct 2026, for the kernel builder (story a13310) to adopt, change or replace. It
imports research/kernel-lab/kernel unchanged and subclasses it; nothing in kernel-lab is edited. Since 18:54 the kernel
has its own make, set, forget, holds, hear (happenings, `hear:` grants, the stream), hold (leases) and the painter's
routes; this file uses those and adds only:

    rows <kind|any> [k=v ...]   a reading: the things of a kind the reader may see, filtered by aspects (the design's
                                `rows windows`), with each thing's rev, for a module that will act on what it read.
    verb <word> steps=".." help=".."   a verb note: a new word, its own entry (from=verb), whose steps run as its
                                caller, step by step (SHAPE 4 and 6). The kernel keeps entries out of make and set. Each step is its own record, a departure
                                from SHAPE 9.7 (one use, one record).
    rules                       `make kind=rule on=<word> do="<line>"` runs its line as its author after each happening
                                of that word ($target, $by filled), on a thread of its own, at most three deep.
    a module on its own         `{t: "do"|"see", id, line}` outside any call runs with the module's grants alone
                                (SHAPE 6, last row), answered `{t: "done"|"rows", id, ...}`. A module reading on its own
                                sees what the place sees.
    narrowed grants             a grant with only=kind:window lets its make, set and forget reach only those kinds.
    hello                       also says the module's id, the place's steward (its owner) and the world's folder.

What would make this file go: ModuleProcess handling unknown message types through one method (so `do` and `see` on a
module's own could be added without copying `_read`), and the four words and rules in the kernel.
"""
import json
import queue
import re
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1] / "kernel-lab"
sys.path.insert(0, str(LAB))

from kernel import lines as L                                   # noqa: E402
from kernel import modules as KM                                # noqa: E402
from kernel import words as KW                                  # noqa: E402
from kernel.kernel import Kernel, Refused, Actor, MAY_WORDS     # noqa: E402

RULE_DEPTH = 3
NAME = re.compile(r"^[a-z][a-z0-9-]*$")


def _k(word, kind, takes, may, undo, help):
    return {"word": word, "word_kind": kind, "takes": takes, "may": may, "undo": undo, "from": "kernel",
            "bound": word, "help": help}


EXT_ENTRIES = [
    _k("rows", "see", "<kind> [k=<v> ...]", "anyone", "no",
       "rows <kind|any> [k=v ...]: the things of that kind you may see, as rows, filtered by their aspects.\n"
       "e.g. rows button bar=taskbar, rows window, rows rule."),
    _k("verb", "do", "<word> steps=<lines> help=<text> [may=<who>] [kind_of=do|see]", "members", "yes",
       "verb <word> steps=\"<lines>\" help=\"<what it does>\": make a new word from other words, a verb note. Its steps run "
       "as whoever says it, so it never adds power; $1 $2 ... and $* are what follows the word.\n"
       "e.g. verb stop steps=\"off $1\" help=\"stop <module>: the same as off\". undo takes the word back."),
]


def _num(t):
    m = re.search(r"\d+$", t or "")
    return int(m.group()) if m else 0


def rows(k, actor, st, entry, tx, group, saw=None):
    toks = st.words.split()
    kind = toks[0].lower() if toks else "any"
    out = []
    for t in list(k.state.things):
        a = k.state.things[t]
        if t == "world" or (kind != "any" and a.get("kind") != kind):
            continue
        if any(str(a.get(fk, "")) != fv for fk, fv in st.kv.items()):
            continue
        s = k.shown(actor.person, t)
        if s is None:
            continue
        k.mark(actor, t, s)
        row = {x: v for x, v in s.items() if not x.startswith(("like:", "sees.", "member:", "in:"))}
        row.update(id=t, rev=k.state.rev.get(t, 0))
        if s.get("made_by"):
            row["by"] = k.name(s["made_by"])
        out.append(row)

    def order(r):
        try:
            return (float(r.get("order", 1e9)), _num(r["id"]))
        except (TypeError, ValueError):
            return (1e9, _num(r["id"]))
    out.sort(key=order)
    what = kind if kind != "any" else "thing"
    if not out:
        return {"text": f"no {what}s you may see" + (" with " + " ".join(f"{a}={v}" for a, v in st.kv.items())
                                                     if st.kv else ""), "rows": []}
    lines = [f"{len(out)} {what}{'' if len(out) == 1 else 's'}:"]
    for r in out:
        bits = [r.get("name") or r.get("label") or r.get("word") or "", (r.get("text") or "")[:60]]
        lines.append(f"  {r['id']} · {r.get('kind')}" + "".join(f" · {b}" for b in bits if b))
    return {"text": "\n".join(lines), "rows": out}


def verb(k, actor, st, entry, tx, group, saw=None):
    """A verb note: a new word made of other words, its own dictionary entry (from=verb), run as its caller."""
    kv = dict(st.kv)
    toks = st.words.split()
    w = (toks[0] if toks else "").lower()
    if not w or not NAME.match(w):
        raise Refused("verb needs a word: verb <word> steps=\"<lines>\" help=\"...\" (one plain word; dotted words "
                      "belong to modules)")
    if k.find_entry(w):
        raise Refused(f"{w} already has an entry here; choose another word, or undo the act that made it")
    steps, help_ = kv.pop("steps", ""), kv.pop("help", "").strip()
    if not steps:
        raise Refused('a verb note needs steps="<lines>", the words it runs')
    if not help_:
        raise Refused('a word with no help is not published: add help="<what it does>"')
    wk = kv.pop("kind_of", "do")
    if wk not in ("do", "see"):
        raise Refused("a verb note is a do or a see word (kind_of=do|see)")
    may = kv.pop("may", "anyone")
    if not all(t.strip() in MAY_WORDS for t in may.split(" or ")):
        raise Refused(f"may={may}: say anyone, members, leaders, stewards, maker or nobody, joined by or")
    e = tx.mint()
    for a, v in [("kind", "word"), ("word", w), ("word_kind", wk), ("takes", kv.pop("takes", "[<words>]")),
                 ("help", help_), ("may", may), ("undo", "yes"), ("from", "verb"), ("steps", steps),
                 ("lives", k.place), ("made_by", actor.id)]:
        tx.set(e, a, v)
    return {"text": f"ok verb {w} ({e}) [r?] · a new word: {steps}"}


def _narrowed(fn, word):
    """The kernel's own make, set or forget, refused for a module whose grant for it says only=kind:<kinds> when the
    thing is of another kind."""
    def wrapped(k, actor, st, entry, tx, group, saw=None):
        if actor.kind == "module":
            kind = st.kv.get("kind") if word == "make" else k.state.get(st.target, "kind")
            fits = [g for g in k._grants_to(actor.module) if k._matches(k.state.get(g, "words"), word)]
            onlys = [k.state.get(g, "only") for g in fits]
            if fits and all(onlys) and not any(o.startswith("kind:") and kind in o[5:].split(",") for o in onlys):
                raise Refused(f"{k.name(actor.module)}'s grant for {word} reaches {', '.join(o[5:] for o in onlys)} "
                              f"things, not a {kind}; nothing was done")
        return fn(k, actor, st, entry, tx, group, saw=saw)
    wrapped.narrowed = True
    return wrapped


KW.KERNEL["rows"] = rows
KW.KERNEL["verb"] = verb
for _w in ("make", "set", "forget"):
    if not getattr(KW.KERNEL[_w], "narrowed", False):
        KW.KERNEL[_w] = _narrowed(KW.KERNEL[_w], _w)
for _e in EXT_ENTRIES:
    if not any(x["word"] == _e["word"] for x in KW.KERNEL_ENTRIES):
        KW.KERNEL_ENTRIES.append(_e)


class DeskKernel(Kernel):
    """The kernel with rows, verb notes, rules, and modules acting on their own."""

    def __init__(self, world_dir, genesis=None):
        self.rule_q = queue.Queue()
        self.local = threading.local()
        self.fired = 0
        super().__init__(world_dir, genesis)
        self._add_missing_entries()
        threading.Thread(target=self._rules, daemon=True, name="rules").start()

    def _add_missing_entries(self):
        """A world founded before an extension word existed gets its entry by a record of its own."""
        from kernel.kernel import Tx
        with self.lock:
            have = {self.state.get(e, "word") for e in self.things("word")}
            missing = [e for e in EXT_ENTRIES if e["word"] not in have]
            if not missing:
                return
            tx = Tx(self)
            tx.part("extend", None, "extend " + " ".join(e["word"] for e in missing))
            for e in missing:
                eid = tx.mint()
                tx.set(eid, "kind", "word")
                for a, v in e.items():
                    tx.set(eid, a, v)
                tx.set(eid, "lives", self.place)
            self._commit(tx, by="kernel", words="extend " + " ".join(e["word"] for e in missing))

    def own_actor(self, mid):
        return Actor(mid, mid, "module", module=mid, caller=None)

    # -- who sees: a module reading on its own sees what the place sees
    def _sees(self, reader, rule, thing):
        if reader and self.state.get(reader, "kind") == "module":
            return any(tok.strip() in ("public", "place") for tok in str(rule).split("|"))
        return super()._sees(reader, rule, thing)

    # -- who may: a module on its own uses its grants alone (SHAPE 6)
    def may(self, actor, entry, target, group):
        if actor.kind == "module" and actor.caller is None:
            return bool(self.state.get(actor.module, "on")) and self._granted(actor.module, entry["word"], group)
        return super().may(actor, entry, target, group)

    # -- verb notes
    def step(self, actor, text, press=None, saw=None, mode="do"):
        st = L.parse(text)
        if st.word:
            with self.lock:
                eid = self.find_entry(st.word)
            if eid and self.state.get(eid, "from") == "verb":
                return self._verb_note(actor, st, self.entry(eid), mode)
        return super().step(actor, text, press=press, saw=saw, mode=mode)

    def _verb_note(self, actor, st, entry, mode):
        depth = getattr(self.local, "verb_depth", 0)
        if depth > 6:
            raise Refused(f"{entry['word']} calls itself too deep; nothing more was done")
        if not (entry.get("help") or "").strip():
            raise Refused(f"{entry['word']} has no help, so it is not published; set its help first")
        may = entry.get("may") or "anyone"
        if not all(t.strip() in MAY_WORDS for t in may.split(" or ")):
            raise Refused(f"{entry['word']}'s may ({may}) is not in the kernel's words; a steward should set it")
        with self.lock:
            if not self.may(actor, entry, st.target, self.place):
                raise self.refusal_for(entry, self.place)
        kind = entry.get("word_kind") or "do"
        if mode == "see" and kind != "see":
            raise Refused(f"{entry['word']} is an act; /see runs only readings")
        args = ([st.target] if st.target else []) + st.words.split()
        steps = L.split_batch(entry.get("steps", ""))

        def fill(s):
            s = s.replace("$target", st.target or (args[0] if args else ""))
            s = s.replace("$*", " ".join(args))
            for i in range(9, 0, -1):
                s = s.replace(f"${i}", args[i - 1] if len(args) >= i else "")
            return s
        texts, out_rows, made, last = [], [], [], None
        self.local.verb_depth = depth + 1
        try:
            for i, s in enumerate(steps, 1):
                try:
                    r = self.step(actor, fill(s), mode=mode)
                except Refused as exc:
                    raise Refused(f"{entry['word']} stopped at step {i} ({fill(s)}): {exc}")
                texts.append(r.get("text", ""))
                out_rows += r.get("rows", [])
                made += r.get("made", [])
                last = r.get("record") or last
        finally:
            self.local.verb_depth = depth
        out = {"text": "\n".join(t for t in texts if t), "rows": out_rows, "made": made}
        if last:
            out["record"] = last
        return out

    # -- rules: every happening the kernel makes also goes to the rules' thread
    def _happen(self, h):
        super()._happen(h)
        self.rule_q.put((dict(h), getattr(self.local, "rule_depth", 0)))

    def _rules(self):
        while True:
            h, depth = self.rule_q.get()
            if depth >= RULE_DEPTH:
                continue
            try:
                self._fire(h, depth)
            except Exception as exc:                       # a rule never stops the kernel
                print(f"kext: rule failed: {exc!r}", file=sys.stderr, flush=True)

    def _fire(self, h, depth):
        with self.lock:
            rules = [(r, dict(self.state.things[r])) for r in self.things("rule")
                     if self.state.get(r, "on") == h.get("word") and not self.state.get(r, "forgotten")
                     and self.state.get(r, "off") not in ("yes", True)]
        for rid, r in rules:
            author = r.get("made_by")
            ak = self.state.get(author, "kind")
            if ak == "person":
                actor = Actor(author, author, "person")
            elif ak == "agent":
                actor = Actor(author, self.state.get(author, "for"), "agent")
            elif ak == "module":
                actor = self.own_actor(author)
            else:
                continue
            line = str(r.get("do", "")).replace("$target", h.get("target") or "").replace("$by", str(h.get("by") or ""))
            self.local.rule_depth = depth + 1
            try:
                out = self.run(actor, line)
                self.fired += 1
                print(f"kext: rule {rid} on {h.get('word')} {h.get('target')}: {out['text'][:160]}", flush=True)
            finally:
                self.local.rule_depth = 0


class DeskModuleProcess(KM.ModuleProcess):
    """The kernel's module process (kernel/modules.py as of 18:40), plus a module's own acts and reads, a log file of
    what it says on stderr, and a fuller hello."""

    def send(self, msg):
        if msg.get("t") == "hello":
            k = self.host.kernel
            with k.lock:
                owner = next((t for t, a in k.state.things.items() if a.get("kind") == "person" and k.is_steward(t)),
                             None)
            msg = dict(msg, id=self.mid, owner=owner, place=k.place, world=str(k.dir))
        super().send(msg)

    def _read_err(self):
        k = self.host.kernel
        import time
        try:
            logs = Path(k.dir) / "logs"
            logs.mkdir(exist_ok=True)
            fh = open(logs / f"{k.state.get(self.mid, 'name') or self.mid}.log", "a", encoding="utf-8")
            fh.write(f"--- started {time.strftime('%Y-%m-%d %H:%M:%S')} pid {self.proc.pid}\n")
            fh.flush()
        except OSError:
            fh = None                                   # no log file (a test world already gone): keep the last lines only
        for line in self.proc.stderr:
            self.err = (self.err + [line.rstrip()])[-20:]
            if fh:
                try:
                    fh.write(line)
                    fh.flush()
                except (OSError, ValueError):
                    fh = None

    def _read(self):
        # a copy of the kernel's ModuleProcess._read (18:40) with one addition, marked: `do` and `see` on its own
        k = self.host.kernel
        for line in self.proc.stdout:
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                self.err = (self.err + [f"not JSON: {line.strip()[:200]}"])[-20:]
                continue
            t = msg.get("t")
            if t == "offer":
                self.offer_receipt = k.on_offer(self.mid, msg.get("words") or [])
                self.offered.set()
            elif t == "see" and msg.get("use") in self.pending:
                p = self.pending[msg["use"]]
                threading.Thread(target=self._see, args=(p["caller"], msg), daemon=True).start()
            elif t in ("see", "do") and msg.get("id"):                       # added: a module on its own
                threading.Thread(target=self._own, args=(msg,), daemon=True).start()
            elif t == "see":
                self.send({"t": "rows", "use": msg.get("use"), "refused": "no call of yours is open with that use"})
            elif t in ("answer", "status"):
                p = self.pending.get(msg.get("use"))
                if p is not None:
                    p["answer"] = msg
                    p["event"].set()
            elif t == "happen":
                said = k.announce(self.mid, str(msg.get("word") or ""), msg.get("target"), msg.get("text") or "")
                if said != "ok":
                    self.send({"t": "refused", "about": "happen", "word": msg.get("word"), "why": said})
            elif t == "hold":
                lease, why = k.hold(self.mid, str(msg.get("word") or ""))
                self.send({"t": "held", "use": msg.get("use"), "word": msg.get("word"),
                           **({"lease": lease} if lease else {"refused": why})})
            elif t == "release":
                k.release(lease=msg.get("lease"))
        self.stdout_closed.set()
        for p in list(self.pending.values()):
            p["event"].set()

    def _own(self, msg):
        k = self.host.kernel
        mode = "see" if msg["t"] == "see" else "do"
        try:
            r = k.run(k.own_actor(self.mid), msg.get("line", ""), saw=msg.get("saw"), mode=mode)
        except Exception as exc:
            r = {"ok": False, "text": f"refused: {exc}", "rows": []}
        self.send({"t": "rows" if mode == "see" else "done", "id": msg.get("id"), "ok": r.get("ok", True),
                   "text": r.get("text", ""), "rows": r.get("rows", []),
                   **({"refused": r["text"]} if not r.get("ok", True) else {})})


# the kernel's Host makes its processes by this module-level name (kernel/modules.py); in this process they are ours
KM.ModuleProcess = DeskModuleProcess
DeskHost = KM.Host
