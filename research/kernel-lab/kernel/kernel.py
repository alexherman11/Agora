"""The kernel: one act loop for a press, an agent's line and a module's answer (SHAPE section 9).

    line -> parse -> find the word's entry -> may? -> seen? -> run -> facts -> one record -> receipt

Everything here is world data except the keep (accounts, the seal secret) and the fence's seen marks, which live beside
the world. The lock is held only while a kernel word runs and its record is written; never while a module computes.
"""
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from pathlib import Path

from . import lines as L
from .store import GONE, Log, h, canon

FLOOR = {"look", "help", "undo", "off", "status"}     # stewards may always use these, whatever an entry says
MAY_WORDS = {"anyone", "members", "leaders", "stewards", "maker", "nobody"}


class Refused(Exception):
    """A refusal: nothing was written. Its text names the way that is open."""


class Actor:
    """Who acts. `person` is whose rights are used; a module answering a call acts for its caller, narrowed."""

    def __init__(self, id, person, kind, module=None, caller=None):
        self.id, self.person, self.kind, self.module, self.caller = id, person, kind, module, caller

    def __repr__(self):
        return f"Actor({self.id} for {self.person}, {self.kind})"


class Tx:
    """One use of a word (however many steps it runs): its facts, kept in an overlay until the record is written."""

    def __init__(self, k):
        self.k, self.over, self.parts, self.minted, self.made = k, {}, [], 0, []
        self.extra = {}                 # what a word adds to its record (undo: `undoes`, and the seal it acts under)

    def part(self, word, target, words):
        self.parts.append({"word": word, "target": target, "words": words, "facts": []})

    def get(self, t, a, default=None):
        v = self.over.get((t, a), self.k.state.things.get(t, {}).get(a, GONE))
        return default if v is GONE else v

    def set(self, t, a, v=GONE):
        now = self.over.get((t, a), self.k.state.things.get(t, {}).get(a, GONE))
        if h(now) == h(v) and now is not GONE and v is not GONE:
            return
        self.parts[-1]["facts"].append([t, a, h(now)] + ([] if v is GONE else [v]))
        self.over[(t, a)] = v

    def mint(self):
        self.minted += 1
        tid = f"{self.k.tag}{self.k.state.top.get(self.k.tag, 0) + self.minted}"
        self.made.append(tid)
        return tid

    @property
    def empty(self):
        return not any(p["facts"] for p in self.parts)


class Kernel:
    def __init__(self, world_dir, genesis=None):
        self.dir = Path(world_dir)
        self.lock = threading.RLock()
        self.log = Log(self.dir)
        self.state = self.log.replay()
        self.keep_dir = self.dir / "keep"
        self.keep_dir.mkdir(parents=True, exist_ok=True)
        self.accounts = self._keep_read("accounts.json", {})
        seal = self.keep_dir / "seal.key"
        if not seal.exists():
            seal.write_bytes(secrets.token_bytes(32))
        self._seal_key = seal.read_bytes()
        self.seen = {}                                 # actor id -> {thing: {aspect: seq}}; beside the world
        self.notices = []                              # what stewards should be told (a module offer that no longer fits)
        self.modules = None                            # set by attach_modules
        if not self.log.records:
            if genesis is None:
                raise ValueError("an empty world needs a genesis")
            self._genesis(genesis)
        self.tag = self.state.get("world", "tag")
        self.place = self.state.get("world", "place")

    # ------------------------------------------------------------------ keep
    def _keep_read(self, name, default):
        p = self.keep_dir / name
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default

    def _keep_write(self, name, value):
        p = self.keep_dir / name
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(value, indent=1), encoding="utf-8")
        os.replace(tmp, p)

    def seal(self, person, entry_id, target):
        """A sealed act's author, as the log keeps it: HMAC(seal secret, person, entry, target) (SHAPE section 8)."""
        return hmac.new(self._seal_key, f"{person}|{entry_id}|{target}".encode(), hashlib.sha256).hexdigest()[:20]

    # ------------------------------------------------------------------ genesis
    def _genesis(self, g):
        """The world's first record, by the kernel: its tag, the place, the steward, the dictionary's kernel words,
        invites, groups and the modules the steward installs."""
        self.tag = g["tag"]
        tx = Tx(self)
        tx.part("genesis", None, "genesis")
        tx.set("world", "tag", self.tag)
        tx.set("world", "invites_counted_by", g.get("invites_counted_by", "entry"))
        place = tx.mint()
        tx.set("world", "place", place)
        tx.set(place, "kind", "place")
        tx.set(place, "name", g.get("name", "the place"))
        steward = tx.mint()
        tx.set(steward, "kind", "person")
        tx.set(steward, "name", g["steward"]["name"])
        tx.set(place, f"member:{steward}", "leader")
        self.accounts[g["steward"]["account"]] = steward
        from .words import KERNEL_ENTRIES
        for e in KERNEL_ENTRIES:
            eid = tx.mint()
            tx.set(eid, "kind", "word")
            for k, v in e.items():
                tx.set(eid, k, v)
            tx.set(eid, "lives", place)
        for inv in g.get("invites", []):
            iid = tx.mint()
            tx.set(iid, "kind", "invite")
            tx.set(iid, "code", hashlib.sha256(inv["code"].encode()).hexdigest()[:16])
            tx.set(iid, "channel", inv.get("channel", ""))
            tx.set(iid, "uses_left", inv.get("uses", 50))
            tx.set(iid, "sees", "leaders")
        for grp in g.get("groups", []):
            gid = tx.mint()
            tx.set(gid, "kind", "group")
            tx.set(gid, "name", grp["name"])
            tx.set(gid, f"in:{place}", 1)
            tx.set(gid, f"member:{steward}", "leader")
        for m in g.get("modules", []):
            mid = tx.mint()
            tx.set(mid, "kind", "module")
            tx.set(mid, "name", m["name"])
            tx.set(mid, "run", m["run"])
            tx.set(mid, "publishes", m["publishes"])
            tx.set(mid, "on", True)
            gr = tx.mint()
            tx.set(gr, "kind", "grant")
            tx.set(gr, "to", mid)
            tx.set(gr, "words", m.get("grants", ""))
            tx.set(gr, "where", place)
            tx.set(gr, "by", steward)
        self._commit(tx, by="kernel", words="genesis")
        self._keep_write("accounts.json", self.accounts)

    # ------------------------------------------------------------------ reading the world
    def things(self, kind):
        return [t for t, a in self.state.things.items() if a.get("kind") == kind]

    def name(self, t):
        a = self.state.things.get(t, {})
        if a.get("kind") == "agent":
            return f"agent for {self.name(a.get('for'))}"
        return a.get("name") or t

    def module_named(self, name):
        for m in self.things("module"):
            if self.state.get(m, "name") == name or m == name:
                return m
        return None

    def groups_of(self, t):
        """The groups a thing is placed in (its `in:` aspects that name a place or group)."""
        return [a[3:] for a in self.state.things.get(t, {}) if a.startswith("in:")
                and self.state.get(a[3:], "kind") in ("place", "group")]

    def up(self, g):
        """A group and the groups around it, nearest first, ending at the place."""
        out, seen = [], set()
        while g and g not in seen:
            out.append(g)
            seen.add(g)
            parents = self.groups_of(g)
            g = parents[0] if parents else None
        return out

    def is_leader(self, person, group):
        return any(self.state.get(g, f"member:{person}") == "leader" for g in self.up(group))

    def is_member(self, person, group):
        if self.state.get(person, "kind") != "person":
            return False
        if group == self.place:
            return True                                     # every person who joined is a member of the place
        return bool(self.state.get(group, f"member:{person}")) or self.is_leader(person, group)

    def is_steward(self, person):
        return self.is_leader(person, self.place)

    # ------------------------------------------------------------------ who sees
    def _sees(self, reader, rule, thing):
        for tok in str(rule).split("|"):
            tok = tok.strip()
            if tok == "public":
                return True
            if tok == "place" and reader and self.state.get(reader, "kind") == "person":
                return True
            if tok == "leaders" and reader and self.is_steward(reader):
                return True
            if tok.startswith("group:") and reader and self.is_member(reader, tok[6:]):
                return True
            if tok.startswith("person:") and reader == tok[7:]:
                return True
        return False

    def shown(self, reader, t):
        """The thing as `reader` (a person id) may see it, or None. Every read passes here (SHAPE section 7). Sealed
        likes are shown only as a count."""
        a = self.state.things.get(t)
        if a is None or t == "world":
            return None
        if not self._sees(reader, a.get("sees", "place"), t):
            return None
        out = {}
        likes = 0
        for k, v in a.items():
            if k.startswith("like:"):
                likes += 1
                continue
            rule = a.get(f"sees.{k}")
            if rule is not None and not self._sees(reader, rule, t):
                continue
            out[k] = v
        if a.get("kind") == "post":
            out["likes"] = likes
        return out

    def no_such(self, t):
        return Refused(f"no thing called {t} here; look shows what there is")

    # ------------------------------------------------------------------ the dictionary
    def entries(self):
        return [e for e in self.things("word") if self.state.get(e, "status", "live") != "hidden"]

    def find_entry(self, word, group=None):
        """The word's entry, nearest first from `group` (the line's), else None. Two at one level refuse."""
        word = word.lower()
        levels = self.up(group or self.place)
        for said in ("named", "bound"):
            # a word is said by its entry's word or an alias; failing that, the bound name still answers, so a rename
            # never breaks a word that worked (DICTIONARY-ENTRY.md, Saying a word)
            for g in levels:
                hits = [e for e in self.entries() if self.state.get(e, "lives") == g and (
                        (said == "named" and (self.state.get(e, "word") == word or
                                              word in (self.state.get(e, "aliases") or "").split()))
                        or (said == "bound" and self.state.get(e, "bound") == word))]
                if len(hits) > 1:
                    raise Refused(f"{word} has two entries in {self.name(g)}: {', '.join(hits)}; a steward should hide one")
                if hits:
                    return hits[0]
        return None

    def entry(self, e):
        return dict(self.state.things.get(e, {}), id=e)

    @staticmethod
    def source(entry):
        """Where an entry's implementation comes from -> ("kernel", name) | ("module", module name) | (other, None)."""
        frm, bound = entry.get("from") or "", entry.get("bound") or entry.get("word")
        if frm == "kernel":
            return "kernel", bound
        if frm.startswith("module:"):
            return "module", frm[7:]
        return frm or "nothing", None

    @staticmethod
    def takes_id(takes):
        """From the usage notation: whether a word takes a thing -> "required" | "optional" | None."""
        takes = takes or ""
        if "[<id>]" in takes or "r<n>" in takes or "<module>" in takes:
            return "optional"
        return "required" if "<id>" in takes else None

    # ------------------------------------------------------------------ who may
    def _grants_to(self, who):
        return [g for g in self.things("grant") if self.state.get(g, "to") == who and not self.state.get(g, "revoked")]

    @staticmethod
    def _matches(pattern_list, word):
        for p in (pattern_list or "").split():
            if p == word or (p.endswith(".*") and word.startswith(p[:-1])) or p == "*":
                return True
        return False

    def _may_person(self, person, entry, target, group, depth=0):
        word = entry["word"]
        if word in FLOOR and self.is_steward(person):
            return True
        for tok in (entry.get("may") or "nobody").split(" or "):
            tok = tok.strip()
            if tok == "anyone" and self.state.get(person, "kind") == "person":
                return True
            if tok == "members" and self.is_member(person, group):
                return True
            if tok == "leaders" and self.is_leader(person, group):
                return True
            if tok == "stewards" and self.is_steward(person):
                return True
            if tok == "maker" and target and self.state.get(target, "made_by") in (person,) + tuple(
                    a for a in self.things("agent") if self.state.get(a, "for") == person):
                return True
        return self._granted(person, word, group, depth)

    def _granted(self, who, word, group, depth=0):
        """A live grant to `who` for `word` reaching `group`, whose grantor still may use the word (SHAPE section 6)."""
        if depth > 4:
            return False
        for g in self._grants_to(who):
            if not self._matches(self.state.get(g, "words"), word):
                continue
            if self.state.get(g, "where") not in self.up(group):
                continue
            grantor = self.state.get(g, "by")
            e = self.find_entry(word)
            if grantor and e and self._may_person(grantor, self.entry(e), None, group, depth + 1):
                return True
        return False

    def may(self, actor, entry, target, group):
        if actor.kind == "module":
            # a module answering a call: the caller's rights, narrowed to the module's grants. Both must allow it.
            on = self.state.get(actor.module, "on")
            return bool(on) and self._granted(actor.module, entry["word"], group) and \
                self._may_person(actor.person, entry, target, group)
        return self._may_person(actor.person, entry, target, group)

    def refusal_for(self, entry, group):
        may = entry.get("may") or "nobody"
        who = {"leaders": f"leaders of {self.name(group)}", "stewards": "stewards", "members": f"members of {self.name(group)}",
               "maker": "whoever made it", "nobody": "no one", "anyone": "anyone here"}
        said = " or ".join(who.get(t.strip(), t) for t in may.split(" or "))
        return Refused(f"{entry['word']} is for {said}; help {entry['word']} says more")

    # ------------------------------------------------------------------ the fence
    def mark(self, actor, t, shown):
        m = self.seen.setdefault(actor.id, {}).setdefault(t, {})
        for a in shown:
            m[a] = self.state.last_seq(t, a)
        m["*"] = self.state.rev.get(t, 0)

    def fence(self, actor, t, aspects, saw=None):
        """Refuse an act on `t` whose author has not looked, or whose look is older than a change to what it writes.
        A module or a page says what it saw (`saw`: thing -> the rev it read); a typed line has its seen marks."""
        if saw is not None:
            if t not in saw:
                raise Refused(f"{t} was not among what was read before acting on it; nothing was done")
            if self.state.rev.get(t, 0) > int(saw[t]):
                raise Refused(f"stale: {t} changed since it was read (now at r{self.state.rev.get(t)}); nothing was done")
            return
        m = self.seen.get(actor.id, {}).get(t)
        if m is None:
            raise Refused(f"you have not looked at {t} yet; look {t} first")
        for a in aspects:
            last = self.state.last_seq(t, a)
            if last > m.get(a, m.get("*", 0)):
                rec = self.log.records[last - 1]
                who = "someone" if rec.get("by") == "sealed" else self.name(rec.get("for") or rec.get("by"))
                raise Refused(f"stale: {t} changed since you looked (r{last} by {who}); look {t} again")

    # ------------------------------------------------------------------ commit
    def _commit(self, tx, by, words, **extra):
        rec = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "by": by, "words": words,
               "parts": tx.parts}
        rec.update({k: v for k, v in extra.items() if v is not None})
        rec = self.log.append(rec)
        for p in rec["parts"]:
            self.state.apply(p["facts"], rec["seq"])
        return rec

    def undone(self):
        return {r["undoes"] for r in self.log.records if r.get("undoes")}

    # ------------------------------------------------------------------ the act loop
    def run(self, actor, line, press=None, saw=None, mode="do"):
        """A whole line: its steps in order, each its own record; stops at the first refusal, naming what did not run.
        -> {ok, text, rows, records, made}"""
        if press:
            with self.lock:
                for r in self.log.records:
                    if r.get("press") == press:
                        return {"ok": True, "text": f"already done, as r{r['seq']}", "rows": [], "records": [], "made": []}
        steps = L.split_batch(line)
        out = {"ok": True, "text": "", "rows": [], "records": [], "made": []}
        texts = []
        for i, s in enumerate(steps):
            try:
                r = self.step(actor, s, press=press if len(steps) == 1 else None, saw=saw, mode=mode)
            except Refused as exc:
                texts.append(f"refused: {exc}")
                if steps[i + 1:]:
                    texts.append(f"not run: {' | '.join(steps[i + 1:])}")
                out["ok"] = False
                break
            texts.append(r["text"])
            out["rows"] += r.get("rows", [])
            if r.get("record"):
                out["records"].append(f"r{r['record']}")
            out["made"] += r.get("made", [])
        out["text"] = "\n".join(t for t in texts if t)
        if self.modules:
            self.modules.reconcile()
        return out

    def step(self, actor, text, press=None, saw=None, mode="do"):
        from .words import KERNEL
        st = L.parse(text)
        if not st.word:
            raise Refused("an empty line; help lists the words you may use")
        with self.lock:
            group = st.kv.get("in") or None
            if group and self.state.get(group, "kind") not in ("place", "group"):
                raise self.no_such(group)
            eid = self.find_entry(st.word, group)
            if eid is None:
                raise Refused(f"nothing answers to '{st.word}' here; help lists the words you may use")
            entry = self.entry(eid)
            takes = self.takes_id(entry.get("takes"))
            if st.target and takes is None:
                st.words = (st.target + " " + st.words).strip()       # a word that takes no thing: an id is words
                st.target = None
            if st.target and L.ID.match(st.target):
                if self.shown(actor.person, st.target) is None:
                    raise self.no_such(st.target)                     # the same words as for a thing that isn't there
                group = group or (self.groups_of(st.target) or [None])[0]
            elif takes == "required":
                raise Refused(f"{st.word} needs a thing: {entry.get('help', '').splitlines()[0]}")
            group = group or self.place
            if not self.may(actor, entry, st.target, group):
                if actor.kind == "module" and self._may_person(actor.person, entry, st.target, group):
                    raise Refused(f"{self.name(actor.module)} holds no grant for {st.word}; nothing was done")
                raise self.refusal_for(entry, group)
            src, name = self.source(entry)
            if mode == "see" and entry.get("word_kind") != "see":
                raise Refused(f"{st.word} is an act; /see runs only readings")
            if src == "kernel":
                fn = KERNEL.get(name)
                if fn is None:
                    raise Refused(f"{st.word} is unbound: the kernel has no word {name}")
                if entry.get("word_kind") == "see":
                    return fn(self, actor, st, entry, None, group)
                tx = Tx(self)
                tx.part(st.word, st.target, text)
                res = fn(self, actor, st, entry, tx, group)
                if tx.empty:
                    return res
                rec = self._commit_use(tx, actor, text, entry, press, saw, st)
                res["record"] = rec["seq"]
                res["made"] = tx.made
                res["text"] = res["text"].replace("[r?]", f"[r{rec['seq']}]")
                return res
        if src == "module":
            return self.module_word(actor, st, entry, group, text, press)       # no lock held while the module works
        raise Refused(f"{st.word} is unbound: its entry says it comes from {src}, which this kernel does not run yet")

    def _commit_use(self, tx, actor, words, entry, press, saw, st):
        rec = self._commit_use_record(tx, actor, words, entry, press, saw, st)
        # your own act marks what it wrote as seen (the desk's rule): a thing it made, whole; a thing you had looked
        # at, the aspects it changed. A thing you never looked at stays unlooked.
        marks = self.seen.setdefault(actor.id, {})
        for p in tx.parts:
            for f in p["facts"]:
                if f[0] in tx.made or f[0] in marks:
                    m = marks.setdefault(f[0], {})
                    m[f[1]] = rec["seq"]
                    if f[0] in tx.made:
                        m["*"] = rec["seq"]
        return rec

    def _commit_use_record(self, tx, actor, words, entry, press, saw, st):
        undoes = tx.extra.get("undoes")
        if tx.extra.get("sealed_as"):
            # the undo of a sealed act is sealed too, or it would say who took their like back
            return self._commit(tx, by="sealed", words=words, entry=entry["id"], seal=tx.extra["sealed_as"],
                                press=press, undoes=undoes)
        sealed = entry.get("sealed") == "yes" or any(
            self.state.get(self.find_entry(p["word"]) or "", "sealed") == "yes" for p in tx.parts)
        if sealed:
            seal = self.seal(actor.person, entry["id"], st.target)
            return self._commit(tx, by="sealed", words=words, entry=entry["id"], seal=seal, press=press)
        by = actor.module if actor.kind == "module" else actor.id
        return self._commit(tx, by=by, words=words, entry=entry["id"], press=press, undoes=undoes,
                            **{"for": actor.person if by != actor.person else None,
                               "via": "module" if actor.kind == "module" else ("agent" if actor.kind == "agent" else None),
                               "saw": saw})

    # ------------------------------------------------------------------ module words
    def module_word(self, actor, st, entry, group, text, press):
        mname = self.source(entry)[1]
        mid = self.module_named(mname)
        if not mid or not self.state.get(mid, "on"):
            raise Refused(f"{st.word} is unbound: {mname} is off; look {mname} says more")
        if not self.modules or not self.modules.running(mid):
            why = self.modules.why_down(mid) if self.modules else None
            raise Refused(f"{st.word} is unbound: {mname} is not running" + (f": {why}" if why else ""))
        # the module is asked by the entry's bound name (DICTIONARY-ENTRY.md `bound=`), never the word as typed, so an
        # alias or a rename made in the world reaches a module that knows only its own name
        ans = self.modules.call(mid, entry.get("bound") or entry["word"],
                                {"target": st.target, "words": st.words, "kv": st.kv}, caller=actor)
        if ans.get("refused"):
            raise Refused(f"{mname}: {ans['refused']}")
        if entry.get("word_kind") == "see" or not ans.get("lines"):
            return {"text": ans.get("text", ""), "rows": ans.get("rows", [])}
        return self.admit(mid, actor, text, entry, ans, press)

    def admit(self, mid, caller, text, entry, ans, press=None):
        """A module's answer: its lines run as one use, one record, as the caller narrowed to the module, and only if
        what it read is unchanged (SHAPE section 11). Refused whole otherwise."""
        from .words import KERNEL
        author = Actor(mid, caller.person, "module", module=mid, caller=caller)
        saw = {k: int(v) for k, v in (ans.get("saw") or {}).items()}
        with self.lock:
            tx = Tx(self)
            notes = []
            for line in ans["lines"]:
                st = L.parse(line)
                eid = self.find_entry(st.word)
                if eid is None:
                    raise Refused(f"{self.name(mid)} answered with '{st.word}', which nothing answers to; nothing was done")
                e = self.entry(eid)
                if self.source(e)[0] != "kernel" or e.get("word_kind") != "do":
                    raise Refused(f"{self.name(mid)} answered with {st.word}; a module's answer may hold only acts the "
                                  f"kernel runs; nothing was done")
                if st.target and self.shown(caller.person, st.target) is None:
                    raise self.no_such(st.target)
                group = (self.groups_of(st.target) or [self.place])[0] if st.target else self.place
                if not self.may(author, e, st.target, group):
                    if not self._may_person(caller.person, e, st.target, group):
                        raise Refused(f"{entry['word']} would {st.word} {st.target or ''}, and {self.refusal_for(e, group)}; "
                                      f"nothing was done")
                    raise Refused(f"{self.name(mid)} holds no grant for {st.word}; nothing was done")
                tx.part(st.word, st.target, line)
                res = KERNEL[self.source(e)[1]](self, author, st, e, tx, group, saw=saw)
                notes.append(res["text"])
            if tx.empty:
                return {"text": "\n".join(notes)}
            rec = self._commit_use(tx, author, text, entry, press, saw, L.parse(text))
            body = "\n".join(n.replace("[r?]", f"[r{rec['seq']}]") for n in notes)
            return {"text": f"{body}\n~ by {self.name(mid)} for {self.name(caller.person)}", "record": rec["seq"],
                    "made": tx.made}

    def module_see(self, mid, caller, line):
        """A module reading while it answers a call: a see word, run as the caller narrowed to the module."""
        author = Actor(mid, caller.person, "module", module=mid, caller=caller)
        try:
            return self.step(author, line, mode="see")
        except Refused as exc:
            return {"refused": str(exc), "text": f"refused: {exc}", "rows": []}

    def on_offer(self, mid, words):
        """A module offers its words. Each becomes an entry only in its own namespace, only with help, and only if
        absent; after that the entry is the world's (SHAPE section 11). -> receipt text."""
        out = []
        with self.lock:
            pattern = self.state.get(mid, "publishes")
            for w in words:
                word = (w.get("word") or "").lower()
                if not self._matches(pattern, word):
                    out.append(f"refused: {word} is outside {self.name(mid)}'s namespace ({pattern})")
                    continue
                if not (w.get("help") or "").strip():
                    out.append(f"refused: {word} has no help, so it is not published")
                    continue
                eid = next((e for e in self.things("word") if self.state.get(e, "from") ==
                            f"module:{self.state.get(mid, 'name')}" and self.state.get(e, "bound") == word), None) \
                    or self.find_entry(word)
                if eid:
                    if (self.state.get(eid, "takes") or "") != (w.get("takes") or ""):
                        self.notices.append(f"{self.name(mid)} offers {word} taking '{w.get('takes')}', "
                                            f"but its entry {eid} says '{self.state.get(eid, 'takes')}'; nothing overwritten")
                    out.append(f"bound {word} to {eid}")
                    continue
                kind = w.get("kind", "do")
                if kind not in ("do", "see"):
                    out.append(f"refused: {word} is a {kind} word; this skeleton publishes do and see words only")
                    continue
                may = w.get("may") or "anyone"
                if not all(t.strip() in MAY_WORDS for t in may.split(" or ")):
                    may = "anyone"
                tx = Tx(self)
                tx.part("offer", None, f"offer {word}")
                e = tx.mint()
                tx.set(e, "kind", "word")
                tx.set(e, "word", word)
                tx.set(e, "word_kind", kind)
                tx.set(e, "takes", w.get("takes") or "")
                tx.set(e, "help", w["help"].strip())
                tx.set(e, "may", may)
                tx.set(e, "undo", "yes")
                tx.set(e, "from", f"module:{self.state.get(mid, 'name')}")
                tx.set(e, "bound", word)            # what the module answers to, whatever the entry is called later
                tx.set(e, "lives", self.place)
                rec = self._commit(tx, by=mid, words=f"offer {word}", via="offer")
                out.append(f"published {word} as {e} [r{rec['seq']}]")
        return out

    # ------------------------------------------------------------------ persons
    def join(self, account, name, invite=None, answers=None, agent=None):
        """The seam with sign-in (SHAPE section 3): an account the entry service has verified -> its person.
        A new account needs a live invite; its first act is `join`, and its answers are its first facts."""
        if not account or not isinstance(account, str):
            raise Refused("no account: the entry service must say which account this is")
        with self.lock:
            pid = self.accounts.get(account)
            if pid is None:
                # exactly one side counts an invite's uses (SEAM.md section 5); the world says which
                counter = self.state.get("world", "invites_counted_by", "entry")
                tx = Tx(self)
                tx.part("join", None, "join")
                if counter == "entry":
                    if not isinstance(invite, dict):
                        raise Refused("no invite: the entry service admits people here, and said no invite")
                    via = {k: invite.get(k) for k in ("invite_id", "channel", "maker_account_id", "admitted")
                           if invite.get(k) is not None}
                else:
                    code = hashlib.sha256(str(invite or "").encode()).hexdigest()[:16]
                    inv = next((i for i in self.things("invite") if self.state.get(i, "code") == code), None)
                    if inv is None:
                        raise Refused("no invite: joining needs a link from someone already here")
                    if self.state.get(inv, "frozen"):
                        raise Refused("invite frozen: a leader has stopped this link")
                    if int(self.state.get(inv, "uses_left", 0)) <= 0:
                        raise Refused("invite used up: ask whoever shared it for another")
                    tx.set(inv, "uses_left", int(self.state.get(inv, "uses_left")) - 1)
                    via = inv
                pid = tx.mint()
                tx.set(pid, "kind", "person")
                tx.set(pid, "name", name or "someone")
                tx.set(pid, "joined_via", via)
                for k, v in (answers or {}).items():
                    tx.set(pid, f"answer:{k}", v)
                    tx.set(pid, f"sees.answer:{k}", f"person:{pid}|leaders")   # decided 23 Oct
                self._commit(tx, by=pid, words="join", via="sign-in")
                self.accounts[account] = pid
                self._keep_write("accounts.json", self.accounts)
                new = True
            else:
                new = False
            actor = self.actor_for(pid, agent)
        return {"person": pid, "new": new, "actor": actor.id}

    def actor_for(self, pid, agent=None):
        """The actor for a session: the person, or (for an agent's session) that person's agent of that name."""
        if not agent:
            return Actor(pid, pid, "person")
        with self.lock:
            for a in self.things("agent"):
                if self.state.get(a, "for") == pid and self.state.get(a, "label") == agent:
                    return Actor(a, pid, "agent")
            tx = Tx(self)
            tx.part("agent", None, f"agent new name={agent}")
            a = tx.mint()
            tx.set(a, "kind", "agent")
            tx.set(a, "for", pid)
            tx.set(a, "label", agent)
            self._commit(tx, by=pid, words=f"agent new name={agent}", via="sign-in")
            return Actor(a, pid, "agent")
