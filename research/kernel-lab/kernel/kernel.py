"""EDITING THE KERNEL (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
The kernel changes only to give every world a general capability: a word, a check, a kind of fact any app, module or
person can use. It never names its tenants: no app, module, person, kind or field name appears in this code except the
kernel's own (word, rule, kind, grant, person, ...). If your change needs `if kind == "..."`, a person's name or one app's
field, stop: the missing piece is a general word (a kind's policy, a rule step, a reading). Build that, or put it on the
Board. Names already here are debt (research/source-edits/SOURCE-AUDIT-KERNEL.md lists them); take them out when you can.

The kernel: one act loop for a press, an agent's line and a module's answer (SHAPE section 9).

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
import time  # noqa: F401  (holds keep their start time)
from pathlib import Path

from . import lines as L
from .store import GONE, Log, h, canon

FLOOR = {"look", "help", "undo", "off", "status"}     # stewards may always use these, whatever an entry says
MAY_WORDS = {"anyone", "members", "leaders", "stewards", "maker", "lead", "nobody"}


class Refused(Exception):
    """A refusal: nothing was written. Its text names the way that is open. `kept`, when given, is what the refusals
    log keeps instead: the log is read by stewards, who may not see what the refusal told its caller (a private title;
    kernel review H1, 28 Oct)."""

    def __init__(self, *args, kept=None):
        super().__init__(*args)
        self.kept = kept


class Actor:
    """Who acts. `person` is whose rights are used; a module answering a call acts for its caller, narrowed."""

    def __init__(self, id, person, kind, module=None, caller=None):
        self.id, self.person, self.kind, self.module, self.caller = id, person, kind, module, caller
        self.seen_key = id   # hosts may separate observations without changing lasting authorship
        self.session = None  # the door's sign-in this actor came through (a digest, never the token): as= names last for it

    def __repr__(self):
        return f"Actor({self.id} for {self.person}, {self.kind})"


class _Names(dict):
    """A sign-in's as= names, newest last; a supplied name (help $) is never kept, and the oldest go past the cap."""

    def __init__(self, supplied, cap):
        super().__init__()
        self.supplied, self.cap, self.new = supplied, cap, None      # new: the last thing made ($new)

    def __setitem__(self, name, thing):
        if name in self.supplied:
            return
        self.pop(name, None)
        super().__setitem__(name, thing)
        while len(self) > self.cap:
            del self[next(iter(self))]


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
        self.changed = threading.Condition()
        self.log = Log(self.dir)
        self.state = self.log.replay()
        self.keep_dir = self.dir / "keep"
        self.keep_dir.mkdir(parents=True, exist_ok=True)
        from .slow import SlowLog, TimedRLock
        self.slow = SlowLog(self.keep_dir / "kernel-slow.jsonl")
        self.lock = TimedRLock(self.slow)
        from .refusals import Refusals
        self.refusals = Refusals(self)                 # refused lines and errors, beside the world (refusals.py)
        self.accounts = self._keep_read("accounts.json", {})
        seal = self.keep_dir / "seal.key"
        if not seal.exists():
            seal.write_bytes(secrets.token_bytes(32))
        self._seal_key = seal.read_bytes()
        self.seen = {}                                 # actor id -> {thing: {aspect: seq}}; beside the world
        self.notices = []                              # what stewards should be told (a module offer that no longer fits)
        self.modules = None                            # set by attach_modules
        self.happenings = []                           # delivered, not recorded (SHAPE section 5); in memory
        self.leases, self.leases_made = {}, []         # holds: momentary, in memory (SHAPE section 5)
        self.dev_sessions = None                       # start_kernel.py --dev-entry: a callable -> {token: session}
        self.clock = None                              # a callable -> aware datetime, for a run with its own time
        self._local = threading.local()                # this thread's verb and rule depth, and the rule it runs
        self._rules_q = None                           # rules' own thread, started by the first happening one answers
        self.rules_fired = []                          # the last rules that ran: (rule, happening n, what it said)
        self.turns = {}                                # agent id -> the turn it is working: {because, work, since}
        self.names = {}                                # (actor, sign-in) -> {as= name: thing}: in memory, never the world
        from .kinds import Kinds
        from .bonds import Bonds
        self.kinds = Kinds(self)                       # kinds as needs, aspect spellings, promises (kinds.py)
        self.bonds = Bonds(self)                       # what things share, read from the log (bonds.py)
        if not self.log.records:
            if genesis is None:
                raise ValueError("an empty world needs a genesis")
            self._genesis(genesis)
        self.tag = self.state.get("world", "tag")
        self.place = self.state.get("world", "place")
        self._new_kernel_words()

    def _new_kernel_words(self):
        """A world founded before a kernel word existed gets its entry, by one record of the kernel's own. A word the
        world renamed is found by its bound name, so nothing is added twice."""
        from .words import KERNEL_ENTRIES, KERNEL, PRESS_MODE_HELP
        with self.lock:
            have = {self.state.get(e, "bound") or self.state.get(e, "word") for e in self.things("word")
                    if self.state.get(e, "from") == "kernel"}
            # a word this kernel no longer runs (held or removed, e.g. around while the graph is held, 28 Oct) rests
            # hidden rather than answering "unbound"; it comes back by itself when a kernel has it again
            mine = [e for e in self.things("word") if self.state.get(e, "from") == "kernel"]
            # dk2834: older dictionaries classified the button dispatcher as a reading.
            # Repair by implementation identity, including renamed words and group copies.
            presses = [e for e in mine if self.state.get(e, "bound") == "press"
                       and self.state.get(e, "word_kind") == "see"]
            if presses:
                tx = Tx(self)
                tx.part("words", None, "press acts; /see refuses it")
                for e in presses:
                    tx.set(e, "word_kind", "do")
                    help_text = self.state.get(e, "help", "")
                    if PRESS_MODE_HELP not in help_text:
                        tx.set(e, "help", (help_text + " " + PRESS_MODE_HELP).strip())
                self._commit(tx, by="kernel", words="press is a do word")
            gone = [e for e in mine if (self.state.get(e, "bound") or self.state.get(e, "word")) not in KERNEL
                    and self.state.get(e, "status", "live") != "hidden"]
            back = [e for e in mine if self.state.get(e, "retired") == "yes"
                    and (self.state.get(e, "bound") or self.state.get(e, "word")) in KERNEL]
            if gone or back:
                said = "; ".join(x for x in (
                    ("the kernel no longer runs: " + " ".join(self.state.get(e, "word") for e in gone)) if gone else "",
                    ("the kernel runs again: " + " ".join(self.state.get(e, "word") for e in back)) if back else "") if x)
                tx = Tx(self)
                tx.part("words", None, said)
                for e in gone:
                    tx.set(e, "status", "hidden")
                    tx.set(e, "retired", "yes")
                for e in back:
                    tx.set(e, "status", "live")
                    tx.set(e, "retired")
                self._commit(tx, by="kernel", words=said)
            missing = [e for e in KERNEL_ENTRIES if e["bound"] not in have]
            if not missing:
                return
            said = "the kernel's new words: " + " ".join(e["word"] for e in missing)
            tx = Tx(self)
            tx.part("words", None, said)
            for e in missing:
                eid = tx.mint()
                tx.set(eid, "kind", "word")
                e = dict(e)
                if e.get("aliases"):        # an alias the world already answers to stays with what answers to it
                    e["aliases"] = " ".join(a for a in e["aliases"].split() if not self.find_entry(a))
                for k, v in e.items():
                    if v != "":
                        tx.set(eid, k, v)
                tx.set(eid, "lives", self.place)
            self._commit(tx, by="kernel", words=said)

    def now(self):
        """The kernel's time (UTC). A run may give it a clock of its own; records are stamped with it."""
        from datetime import datetime, timezone
        return self.clock() if self.clock else datetime.now(timezone.utc)

    def once(self, actor, entry, target, tx=None):
        """The limits an entry's `once` says, read from the log: each clause is checked against this person's live
        acts of the same entry (a sealed act is theirs when its seal is theirs). Clauses are joined by ';':
            per person per target  ·  at most N per day per person  ·  at most N per person per <field>
        -> None, or the words of a refusal."""
        rule = (entry.get("once") or "").strip()
        if not rule:
            return None
        import re as _re
        undone = self.undone()

        def mine(r):
            if (r.get("entry") != entry["id"] and not any(p.get('entry') == entry['id'] for p in r.get('parts', []))) or r["seq"] in undone or r.get("undoes"):
                return False
            if r.get("by") == "sealed":
                t = r["parts"][0].get("target") if r.get("parts") else None
                return r.get("seal") == self.seal(actor.person, r.get('entry'), t)
            return actor.person in (r.get("by"), r.get("for"))

        def target_of(r):
            return r.get('_target')
        acts = []
        for r in self.log.records:
            if mine(r):
                parts = [p for p in r.get('parts', []) if p.get('entry') == entry['id']]
                acts.extend(dict(r, _target=p.get('target')) for p in (parts or r.get('parts', [])[:1]))
        if tx:
            acts.extend(dict(at=self.now().strftime('%Y-%m-%dT%H:%M:%SZ'), _target=p.get('target'))
                        for p in tx.parts if p.get('entry') == entry['id'] and p.get('facts'))
        for clause in [c.strip() for c in rule.split(";") if c.strip()]:
            if clause == "per person per target":
                if target and (self.used(actor.person, entry["id"], target) or any(target_of(r) == target for r in acts)):
                    return f"you have already said {entry['word']} on {target}; once each. undo takes yours back"
                continue
            m = _re.fullmatch(r"at most (\d+) per day per person", clause)
            if m:
                today = self.now().strftime("%Y-%m-%d")
                if sum(1 for r in acts if r["at"][:10] == today) >= int(m.group(1)):
                    return (f"you have said {entry['word']} {m.group(1)} times today, the most it takes from one "
                            f"person in a day")
                continue
            m = _re.fullmatch(r"at most (\d+) per person per ([a-z_][a-z0-9_]*)", clause)
            if m:
                field = m.group(2)
                mine_here = self.state.get(target, field) if target else None
                n = sum(1 for r in acts if target_of(r) and self.state.get(target_of(r), field) == mine_here)
                if mine_here is not None and n >= int(m.group(1)):
                    return (f"you have said {entry['word']} {n} time{'' if n == 1 else 's'} for this {field} "
                            f"({self.name(mine_here)}), the most it takes from one person; undo frees yours")
                continue
            return f"{entry['word']}'s entry says once '{clause}', which this kernel cannot read; nothing was done"
        return None

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
            if grp.get("open"):
                tx.set(gid, "open", True)               # its things are seen by the whole place
        for th in g.get("things", []):
            # things the steward founds the world with: lenses, styles, a taskbar's buttons. Same rules as `make`.
            tid = tx.mint()
            for k2, v in th.items():
                if k2 not in ("in",):
                    tx.set(tid, k2, v)
            tx.set(tid, "made_by", steward)
            tx.set(tid, f"in:{place}", 1)
        for m in g.get("modules", []):
            mid = tx.mint()
            tx.set(mid, "kind", "module")
            tx.set(mid, "name", m["name"])
            tx.set(mid, "run", m["run"])
            tx.set(mid, "publishes", m["publishes"])
            tx.set(mid, "on", True)
            if m.get("for") == "steward":
                tx.set(mid, "for", steward)         # a module installed for a person reads and hears as that person
            gr = tx.mint()
            tx.set(gr, "kind", "grant")
            tx.set(gr, "to", mid)
            tx.set(gr, "words", m.get("grants", ""))
            if m.get("only"):
                tx.set(gr, "only", m["only"])       # e.g. kind:window: its make, set and forget reach only those
            tx.set(gr, "where", place)
            tx.set(gr, "by", steward)
        self._commit(tx, by="kernel", words="genesis")
        self._keep_write("accounts.json", self.accounts)

    # ------------------------------------------------------------------ reading the world
    def things(self, kind):
        return [t for t, a in list(self.state.things.items()) if a.get("kind") == kind]

    def name(self, t):
        a = self.state.things.get(t, {})
        if a.get("kind") == "agent":
            return f"agent for {self.name(a.get('for'))}"
        return a.get("name") or t

    def module_named(self, name):
        for m in self.things("module") + self.things("widget"):
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

    def is_lead(self, person, target):
        """The person a thing names as its lead (lead=<person id or name>). 3 Nov: a resident handed a card could not
        change it, since it neither made it nor leads the place; a word whose may says `lead` lets its lead act on it."""
        lead = str(self.state.get(target, "lead") or "").strip()
        if not lead or not person:
            return False
        return lead == person or lead.casefold() == str(self.name(person) or "").strip().casefold()

    def is_leader(self, person, group):
        return any(self.state.get(g, f"member:{person}") == "leader" for g in self.up(group))

    def is_member(self, person, group):
        if self.state.get(person, "kind") != "person":
            return False
        if group == self.place or self.state.get(group, "open"):
            return True                                     # every person who joined is a member of the place, and of
            #                                                 an open group in it (a public channel); its leaders are
            #                                                 still appointed
        return bool(self.state.get(group, f"member:{person}")) or self.is_leader(person, group)

    def is_steward(self, person):
        return self.is_leader(person, self.place)

    # ------------------------------------------------------------------ who sees
    def used(self, person, eid, target):
        """An active use by this person (including their agents), without unsealing anyone else's."""
        undone = self.undone()
        for r in self.log.records:
            if r["seq"] in undone or r.get("undoes") or not r.get("parts"):
                continue
            first = r["parts"][0].get("target")
            own = (r.get("seal") == self.seal(person, r.get("entry"), first) if r.get("by") == "sealed"
                   else person in (r.get("by"), r.get("for")))
            if own and ((r.get("entry") == eid and first == target) or any(
                    p.get("entry") == eid and p.get("target") == target for p in r["parts"])):
                return True
        return False

    def bind_policy(self, value, group):
        """Bind a see word now, so subsequent renaming cannot redirect visibility or admission."""
        word = str(value).removeprefix("word:")
        eid = word if self.state.get(word, "kind") == "word" else self.find_entry(word, group)
        e = self.entry(eid) if eid else {}
        if e.get("word_kind") != "see" or self.source(e)[0] != "verb":
            raise Refused("a condition needs word:<see verb>; help test and help verb say how")
        return f"word:{eid}"

    def predicate(self, person, ref, target, value=""):
        """Fail closed; never execute module code or an act while deciding visibility/admission."""
        eid = str(ref).removeprefix("word:")
        e = self.entry(eid)
        group = (self.groups_of(target) or [self.place])[0]
        previous = getattr(self._local, "predicate", None)
        depth = getattr(self._local, "predicate_depth", 0)
        if depth >= 4 or e.get("word_kind") != "see" or self.source(e)[0] != "verb":
            return False
        actor = Actor(person, person, "person")
        if not self.may(actor, e, target, group):
            return False
        self._local.predicate = (target, value, True)
        self._local.predicate_depth = depth + 1
        try:
            out = self.verb_note(actor, L.parse(e["word"]), e, group, e["word"], mode="see")
            return out.get("value") is True
        except (Refused, RecursionError):
            return False
        finally:
            self._local.predicate, self._local.predicate_depth = previous, depth

    def guard(self, actor, entry, st):
        """Every place a word meets its thing passes here (a typed line, a verb's steps, a module's answer): the
        word's shape first (kinds.py: what its code reads), then the thing's own allows. test."""
        first = st.target or (st.words.split() or [""])[0]   # a word taking only words may still be given a thing
        if first and L.ID.fullmatch(str(first)):
            part = self.kinds.check_word(actor, entry, first, part=st.kv.get("part"))
            if part:
                # a word on a value kind reached the thing through a part (its likes, an upvote): the verb reads
                # $part, a module kv.part (kinds-all-the-way-down.md)
                st.kv = dict(st.kv, part=part)
        ref = self.state.get(st.target, "allows." + (entry.get("bound") or entry["word"]))
        if ref and not self.predicate(actor.person, ref, st.target, st.kv.get("answer", "")):
            raise Refused(self.state.get(st.target, "refusal", "That does not fit yet. Please try again."))

    def _sees(self, reader, rule, thing):
        if reader and self.state.get(reader, "kind") in ("module", "widget"):
            # a module reading on its own: as the person it is installed for, else as the place sees
            p = self.state.get(reader, "for")
            if p:
                return self._sees(p, rule, thing)
            return any(tok.strip() in ("public", "place") for tok in str(rule).split("|"))
        for tok in str(rule).split("|"):
            tok = tok.strip()
            if tok == "public":
                return True
            if tok == "place" and reader and self.state.get(reader, "kind") == "person":
                return True
            if tok == "leaders" and reader and any(self.is_leader(reader, g)
                                                   for g in (self.groups_of(thing) or [self.place])):
                return True                         # the leaders of the thing's own groups (and those above them)
            if tok.startswith("group:") and reader and self.is_member(reader, tok[6:]):
                return True
            if tok.startswith("person:") and reader == tok[7:]:
                return True
        return False

    def shown(self, reader, t):
        """The thing as `reader` (a person id) may see it, or None. Every read passes here (SHAPE section 7). Sealed
        likes are shown only as a count."""
        a = dict(self.state.things.get(t) or {})
        if not a or not a.get('kind') or t == "world" or a.get("forgotten"):
            return None                 # a forgotten thing is out of every view; undo of the forget brings it back
        if not self._sees(reader, a.get("sees", "place"), t):
            return None
        if a.get("sees_when") and not self.predicate(reader, a["sees_when"], t):
            return None
        # An attachment/child never widens its parent's visibility. Walk rather
        # than recurse so cycles and broken parents fail closed on every route.
        parent, visited = a.get('visibility_of'), {t}
        while parent:
            if parent in visited or len(visited) > 32:
                return None
            visited.add(parent)
            pa = self.state.things.get(parent)
            if not pa or pa.get('forgotten') or not self._sees(reader, pa.get('sees', 'place'), parent):
                return None
            if pa.get('sees_when') and not self.predicate(reader, pa['sees_when'], parent):
                return None
            parent = pa.get('visibility_of')
        out = {}
        likes, votes, claims, contacts = 0, {}, [], []
        for k, v in a.items():
            if k.startswith("like:"):
                likes += 1
                continue
            if k.startswith("vote:"):                    # sealed: only the count of each option is shown
                votes[v] = votes.get(v, 0) + 1
                continue
            if k.startswith(("sees.", "allows.")) or k in ("sees", "sees_when"):
                continue
            if k.startswith("claim:"):
                claims.append(k[6:])
            rule = a.get(f"sees.{k}")
            if rule is not None and not self._sees(reader, rule, t):
                continue
            out[k] = v
            if k.startswith("contact:"):
                contacts.append(f"{self.name(k[8:])} {v}")
        if contacts:
            out["contacts"] = ", ".join(contacts)                      # only those this reader may see
        if a.get("kind") == "post":
            out["likes"] = likes
            entry=self.find_entry('like',next(iter(self.groups_of(t)),self.place)) if likes else None
            out['you_liked']=bool(entry and a.get('like:'+self.seal(reader,entry,t)))
        if a.get("options"):
            for o in str(a.get("options") or "").split():
                out[f"votes_{o}"] = votes.get(o, 0)
            out["votes"] = sum(votes.values())
            entry=self.find_entry('vote',next(iter(self.groups_of(t)),self.place)) if votes else None
            out['your_vote']=a.get('vote:'+self.seal(reader,entry,t),'') if entry else ''
        if claims:
            out["claimed_by"] = ", ".join(self.name(p) for p in claims)       # in the order they were claimed
            out["claims"] = len(claims)
        if str(a.get("seats", "")).isdecimal():
            out["seats_left"] = max(0, int(a["seats"]) - len(claims))
        from .history import times
        out.update(times(self, t))
        if a.get('pin_until'):
            from .world_words import utc
            if self.now() >= utc(a['pin_until']):
                out.pop('pinned', None)
        return out

    def trail(self, reader, thing):
        from .history import trail
        return trail(self, reader, thing)

    def no_such(self, t):
        return Refused(f"no thing called {t} here; look shows what there is")

    # ------------------------------------------------------------------ the dictionary
    def entries(self):
        return [e for e in self.things("word") if self.state.get(e, "status", "live") != "hidden"]

    def find_entry(self, word, group=None):
        """The word's entry, nearest first from `group` (the line's), else None. Two at one level refuse."""
        word = word.lower()
        if L.ID.fullmatch(word):
            if self.state.get(word, 'kind') == 'word':
                return word
        from .dictionary import names
        levels = self.up(group or self.place)
        for said in ("named", "bound"):
            # a word is said by its entry's word or an alias; failing that, the bound name still answers, so a rename
            # never breaks a word that worked (DICTIONARY-ENTRY.md, Saying a word)
            for g in levels:
                hits = [e for e in self.entries() if self.state.get(e, "lives") == g and (
                        (said == "named" and word.casefold() in names(self.state.things[e]))
                        or (said == "bound" and self.state.get(e, "bound") == word))]
                if len(hits) > 1:
                    raise Refused(f"{word} has two entries in {self.name(g)}: {', '.join(hits)}; a steward should hide one")
                if hits:
                    return hits[0]
        return None

    def entry(self, e):
        return dict(self.state.things.get(e, {}), id=e)

    NOT_NAMED = ("topic", "word", "grant", "taskboard-event", "paint-report")

    def named(self, actor, name, hint=None):
        """Visible things whose name, title or label is `name` (any case), the hinted kind first (P1, Alex 27 Oct:
        names work where ids go). -> [(id, kind)]: one is the thing; more is a question to ask back."""
        want, hits = str(name).strip().strip("\"'").casefold(), []
        if not want:
            return []
        for t, a in list(self.state.things.items()):
            if a.get("kind") in self.NOT_NAMED or a.get("forgotten"):
                continue
            if want in {str(a.get(f, "")).casefold() for f in ("name", "title", "label")} \
                    and self.shown(actor.person, t) is not None:
                hits.append((t, a.get("kind")))
        hinted = [h for h in hits if hint and (h[1] == hint or h[1].endswith("-" + hint))]
        if hint and hits and not hinted:
            raise Refused(f"no {hint} you can see is called {name.strip()} (called that: "
                          + ", ".join(f"{t}, a {kd}" for t, kd in hits[:4]) + ")")
        return hinted or hits

    def usage_kind(self, entry):
        """The kind a word's usage names first (window.move <window> …: window), if things of that kind exist here
        (tidy <a> <b> names no kind: <a> is only a placeholder)."""
        first = (str(entry.get("help") or "").splitlines() or [""])[0]
        m = L.re.search(r"<([a-z][a-z0-9-]*)", first)
        kind = m.group(1) if m and m.group(1) not in ("id", "thing", "words", "text", "word") else None
        if kind and any(a.get("kind") == kind or str(a.get("kind", "")).endswith("-" + kind)
                        for a in list(self.state.things.values())):
            return kind
        return None

    TELLS_APART = ("start", "starts", "when", "due", "lane", "status", "state", "place", "location", "where", "chat",
                   "made")

    def choices(self, actor, ids, limit=6):
        """'dk1 (a meeting, start 2026-11-02), dk7 (a meeting, start 2026-11-09) and 15 more': the things a name could
        mean, each with the first fact that tells them apart, as the asker sees them (friction 9, trials 28 Oct:
        `done "Dentist"` matched 17 and the question listed no way to pick)."""
        rows = [(t, self.shown(actor.person, t) or {}) for t in ids]
        apart = next((f for f in self.TELLS_APART
                      if len({str(a.get(f, "")) for _, a in rows}) > 1 and all(a.get(f) for _, a in rows[:limit])), None)
        out = []
        for t, a in rows[:limit]:
            v = str(a.get(apart, ""))[:16 if apart == "made" else 40] if apart else ""
            kd = str(a.get("kind") or "thing")
            out.append(f"{t} (a{'n' if kd[:1] in 'aeiou' else ''} {kd}" + (f", {apart} {v}" if v else "") + ")")
        more = len(rows) - limit
        return ", ".join(out) + (f" and {more} more" if more > 0 else "")

    def resolve_name(self, actor, st, entry):
        """A name where a word takes a thing: the whole of its free words first ("buy milk"), then the first word.
        Sets st.target and returns True; refuses when two things share the name; False when nothing is called it."""
        shaped = self.kinds.word_shape(entry)
        hint = None if shaped else self.usage_kind(entry)
        tries = [(st.words, "")] + ([(st.words.split()[0], st.words.split(None, 1)[1])] if " " in st.words else [])
        for name, rest in tries:
            hits = self.named(actor, name, hint)
            if shaped and len(hits) > 1:
                # a word that says its shape: the things called that which it reaches (rsvp Beach cleanup: the event)
                hits = [h for h in hits if self.kinds.reaches(actor, entry, h[0])] or hits
            if len(hits) == 1:
                st.target, st.words = hits[0][0], rest.strip()
                return True
            if hits:
                raise Refused(f"{len(hits)} things are called {name.strip()}: "
                              + self.choices(actor, [t for t, _ in hits]) + f". Say {st.word} with one of those ids",
                              kept=f"{len(hits)} things share the name said; asked which")      # never the name: it can be a title
        return False

    def plain_verb(self, actor, st, group):
        """A plain verb nothing else answers to (close, open, move, done): the family word it means for its thing
        (P2, Alex 27 Oct: no declarations; work it out from the names, ask only when two fit). Words that say their
        shape come first (kinds.py, Alex 28 Oct): those whose shape the thing has, its own kind's first, then the shape
        needing most, then the nearest group; a tie asks. -> entry id or None."""
        word = st.word
        cands = []
        for e in self.entries():
            w = str(self.state.get(e, "word") or "")
            if "." in w and w.rsplit(".", 1)[1] == word and self.shown(actor.person, e) is not None \
                    and self._may_answer_plainly(e, actor):
                cands.append(e)
        if not cands:
            return None
        named = []                                  # the things the line names
        if st.target and L.ID.match(st.target):
            named = [st.target]
        elif st.words:
            for name in [st.words] + ([st.words.split()[0]] if " " in st.words else []):
                named = [t for t, _ in self.named(actor, name)]
                if named:
                    break
        # a word living in a group answers there and below, as find_entry looks: the line's group or the thing's
        scopes = set(self.up(group or self.place))
        for t in named:
            scopes |= set(self.up((self.groups_of(t) or [self.place])[0]))
        cands = [e for e in cands if (self.state.get(e, "lives") or self.place) in scopes] or cands
        if named and any(self.kinds.word_shape(self.state.things[e]) for e in cands):
            levels = {g: i for i, g in enumerate(self.up(group or self.place))}
            ranked = []
            for e in cands:
                for t in named:
                    if self.kinds.word_shape(self.state.things[e]):
                        hit = self.kinds.reaches(actor, self.state.things[e], t)
                    else:
                        # a word with no shape made for this thing's own kind (window.close for a window) competes
                        # as its own kind's word, rather than losing silently to any word with a shape (trials 28 Oct)
                        hit = ((0, 0), None) if self._family_fits(e, self.state.get(t, "kind"), exact=True) else None
                    if hit:
                        ranked.append((hit[0], levels.get(self.state.get(e, "lives"), 99), e, t))
            if ranked:
                ranked.sort(key=lambda x: (x[0], x[1]))
                best = [r for r in ranked if (r[0], r[1]) == (ranked[0][0], ranked[0][1])]
                if len({r[2] for r in best}) == 1 and len({r[3] for r in ranked}) == 1:
                    return best[0][2]
                said = ", ".join(dict.fromkeys(self.state.get(r[2], "word") for r in best))
                if len({r[3] for r in ranked}) > 1:
                    which = list(dict.fromkeys(r[3] for r in ranked))
                    raise Refused(f"{len(which)} things called {st.words or st.target} could take {word} ({said}): "
                                  f"{self.choices(actor, which)}. Say {word} with one of those ids",
                                  kept=f"{len(which)} things sharing the name said could take {word}; asked which")
                raise Refused(f"{word} could mean {said} for {st.words or st.target}; say which")
            cands = [e for e in cands if not self.kinds.word_shape(self.state.things[e])]
            if not cands:
                family = self._family(word, actor)
                if len(family) == 1 and len(named) == 1:      # one word it could be: its own reason, what is missing
                    self.kinds.check_word(actor, self.state.things[family[0]], named[0])
                kinds_ = ", ".join(dict.fromkeys(f"a {self.state.get(t, 'kind')}" for t in named))
                said = ", ".join(self.state.get(e, "word") for e in self._family(word, actor))
                raise Refused(f"nothing called {word} acts on {kinds_}; {word} means {said} for other things "
                              f"(actions {named[0]} lists what does)")
        kinds = list(dict.fromkeys(self.state.get(t, "kind") for t in named))

        def fits(e, kind):
            ns = str(self.state.get(e, "word")).rsplit(".", 1)[0]
            usage = (str(self.state.get(e, "help") or "").splitlines() or [""])[0]
            return ns == kind or ns in str(kind).split("-") or f"<{kind}" in usage or f"<{kind}" in str(
                self.state.get(e, "takes") or "")
        # close Help, where Help names a window and a button: the family word that fits one of them (window.close)
        fit = [e for e in cands if any(fits(e, kd) for kd in kinds)] if kinds else cands
        if len(fit) == 1:
            return fit[0]
        said = ", ".join(self.state.get(e, "word") for e in (fit or cands))
        named_as = " or ".join(f"a {kd}" for kd in kinds[:3])
        if kinds and fit:
            raise Refused(f"{word} could mean {said} for {named_as}; say which")
        if kinds:
            raise Refused(f"nothing called {word} acts on {named_as}; {word} means {said} for other things")
        if st.words or st.target:
            raise Refused(f"nothing you can see is called {st.words or st.target}; {word} means {said} (help {word})")
        raise Refused(f"{word} could mean {said}; say which, or name the thing (help {word})")

    def _may_answer_plainly(self, e, actor):
        """Whether a family word may answer a plain word for this actor: the kernel's, a module's, one a steward or its
        group's leader made, or the actor's own. A member's verb answers only its maker plainly; anyone may still say
        it by its full name (trials 28 Oct: a member's tidy.done took over done for everyone)."""
        a = self.state.things.get(e, {})
        if a.get("from") != "verb":
            return True
        maker = a.get("made_by")
        person = self.state.get(maker, "for") if self.state.get(maker, "kind") == "agent" else maker
        scope = a.get("lives") or self.place
        return person == actor.person or self.is_steward(person) or (scope != self.place and self.is_leader(person, scope))

    def _family_fits(self, e, kind, exact=False):
        ns = str(self.state.get(e, "word")).rsplit(".", 1)[0]
        if ns == kind or (not exact and ns in str(kind).split("-")):
            return True
        usage = (str(self.state.get(e, "help") or "").splitlines() or [""])[0]
        return f"<{kind}>" in usage or f"<{kind}>" in str(self.state.get(e, "takes") or "") if exact else (
            f"<{kind}" in usage or f"<{kind}" in str(self.state.get(e, "takes") or ""))

    def _family(self, word, actor):
        return [e for e in self.entries() if str(self.state.get(e, "word") or "").rsplit(".", 1)[-1] == word
                and "." in str(self.state.get(e, "word")) and self.shown(actor.person, e) is not None]

    def name_target(self, actor, st, entry, group):
        """A word that takes a thing, given a name: its dictionary entry's name (word.set window.open), or a thing so
        called (window.close Help; the kind its usage names first). Sets st.target; refuses when two things share it."""
        takes = self.takes_id(entry.get("takes"))
        first_takes = (str(entry.get("takes") or "").split() or [""])[0]
        names_a_thing = (takes and first_takes in ("<id>", "[<id>]")) or (
            entry.get("from") == "verb" and (self.usage_kind(entry) or self.kinds.word_shape(entry)))  # task.done <task>
        if not (names_a_thing and not st.target and st.words):
            return
        first = st.words.split()[0]
        plain = not L.ID.match(first) and not L.RECORD.match(first)
        if plain and (self.usage_kind(entry) or self.kinds.word_shape(entry)) and self.resolve_name(actor, st, entry):
            return
        try:
            named = self.find_entry(first, group) if plain else None
        except Refused:
            named = None
        if named and self.shown(actor.person, named) is not None:
            st.target, st.words = named, st.words[len(first):].strip()
        elif plain:
            self.resolve_name(actor, st, entry)        # set Lines at=…: Lines is dk74

    def needs_a_thing(self, actor, st, entry, text):
        """The refusal for a word given a name (or nothing) where it takes a thing's id: say which id, as a line."""
        usage = (entry.get('help', '').splitlines() or [''])[0]
        first = (st.words.split() or [''])[0].strip('"\'')
        if not first:
            return f"{st.word} needs a thing, by its id: {usage}"
        hits = []
        for t, a in list(self.state.things.items()):
            if a.get('kind') in ('topic', 'word'):
                continue                                   # help pages and words are not what a line acts on
            if first.casefold() in {str(a.get(f, '')).casefold() for f in ('name', 'title', 'label')} \
                    and self.shown(actor.person, t) is not None and not a.get('forgotten'):
                hits.append((t, a.get('kind')))
        hinted = [h for h in hits if f"<{h[1]}" in usage]  # window.move <window> …: a window first
        hits = hinted or hits
        if len(hits) == 1:
            line = text.replace(first if first in text else st.words.split()[0], hits[0][0], 1)
            return f"{st.word} takes an id, not a name: {first} is {hits[0][0]} (a {hits[0][1]}). Say: {line}"
        if hits:
            return (f"{st.word} takes an id; {len(hits)} things are called {first}: "
                    + ", ".join(f"{t} (a {kd})" for t, kd in hits[:4]) + ". Say it again with one of those ids")
        return (f"{st.word} takes a thing's id (like dk74), and nothing here is called {first}. "
                f"rows <kind> lists ids; find kind=<kind> name=<name> finds one by name. {usage}")

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
        if entry.get('from') == 'kernel' and entry.get('bound') in FLOOR and self.is_steward(person):
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
            if tok == "maker" and target and (self.state.get(target, 'for') == person or self.state.get(target, "made_by") in (person,) + tuple(
                    a for a in self.things("agent") if self.state.get(a, "for") == person)):
                return True
            if tok == "lead" and target and self.is_lead(person, target):
                return True
        return self._granted(person, word, group, depth)

    def _granted(self, who, word, group, depth=0):
        """A live grant to `who` for `word` reaching `group`, whose grantor still may use the word (SHAPE section 6)."""
        if depth > 4:
            return False
        e0 = self.find_entry(word, group)
        names = {word} | ({self.state.get(e0, "word"), self.state.get(e0, "bound")} |
                          set(str(self.state.get(e0, "aliases") or "").split()) if e0 else set())
        for g in self._grants_to(who):
            # a grant reaches a word by any name it answers to: its word, an alias, or its bound name
            if not any(self._matches(self.state.get(g, "words"), n) for n in names if n):
                continue
            if self.state.get(g, "where") not in self.up(group):
                continue
            grantor = self.state.get(g, "by")
            e = self.find_entry(word, group)
            if grantor and e and self._may_person(grantor, self.entry(e), None, group, depth + 1):
                return True
        return False

    def may(self, actor, entry, target, group):
        if actor.kind == "module" and actor.caller is None:
            # a module on its own (SHAPE section 6, last row): its grants, and its person's rights if it has one
            on, p = self.state.get(actor.module, "on"), self.state.get(actor.module, "for")
            return bool(on) and self._granted(actor.module, entry["word"], group) and (
                not p or self._may_person(p, entry, target, group))
        if actor.kind == "module":
            # a module answering a call: the caller's rights, narrowed to the module's grants. Both must allow it.
            on = self.state.get(actor.module, "on")
            return bool(on) and self._granted(actor.module, entry["word"], group) and \
                self._may_person(actor.person, entry, target, group)
        return self._may_person(actor.person, entry, target, group)

    def refusal_for(self, entry, group):
        may = entry.get("may") or "nobody"
        who = {"leaders": f"leaders of {self.name(group)}", "stewards": "stewards", "members": f"members of {self.name(group)}",
               "maker": "whoever made it", "lead": "its lead", "nobody": "no one", "anyone": "anyone here"}
        said = " or ".join(who.get(t.strip(), t) for t in may.split(" or "))
        return Refused(f"{entry['word']} is for {said}; help {entry['word']} says more")

    # ------------------------------------------------------------------ the fence
    def mark(self, actor, t, shown):
        m = self.seen.setdefault(actor.seen_key, {}).setdefault(t, {})
        for a in shown:
            m[a] = self.state.last_seq(t, a)
        m["*"] = self.state.rev.get(t, 0)

    def fence(self, actor, t, aspects, saw=None):
        """Refuse an act on `t` whose author has not looked, or whose look is older than a change to what it writes.
        A module or a page says what it saw (`saw`: thing -> the rev it read); a typed line has its seen marks."""
        if saw is not None:
            if t not in saw:
                raise Refused(f"{t} was not among what was read before acting on it; nothing was done")
            s = saw[t]
            if isinstance(s, dict):
                # a painted gesture: stale only if what it read, or what it writes, changed since it was painted
                rev = int(s.get("rev", 0))
                for a in set(aspects) | set(s.get("aspects") or []):
                    # a painted row read under a kind shows `start` for a thing that says `starts` (kinds.filled), so
                    # an aspect also counts its other spellings: wider, never narrower (kernel review H2, 28 Oct)
                    names = [x for thing, x in self.state.history if thing == t and x.startswith(a[:-1])] if a.endswith("*") \
                        else sorted(self.kinds.spellings_of(a))
                    last = max([self.state.last_seq(t, x) for x in names] + [0])
                    if last > rev:
                        raise Refused(f"stale: {t} changed since it was painted ({a.rstrip(':*')}, r{last}); "
                                      f"nothing was done. The view will repaint.")
                return
            if self.state.rev.get(t, 0) > int(s):
                raise Refused(f"stale: {t} changed since it was read (now at r{self.state.rev.get(t)}); nothing was done")
            return
        m = self.seen.get(actor.seen_key, {}).get(t)
        if m is None:
            raise Refused(f"you have not looked at {t} yet; look {t} first")
        for a in aspects:
            last = self.state.last_seq(t, a)
            if last > m.get(a, m.get("*", 0)):
                rec = self.log.records[last - 1]
                who = "someone" if rec.get("by") == "sealed" else self.name(rec.get("for") or rec.get("by"))
                raise Refused(f"stale: {t} changed since you looked (r{last} by {who}); look {t} again")

    # ------------------------------------------------------------------ commit
    def check_participants(self, actor, saw):
        for t, s in (saw or {}).items():
            if isinstance(s, dict) and s.get('participant'):
                if self.shown(actor.person, t) is None:
                    raise self.no_such(t)
                self.fence(actor, t, s.get('aspects') or ['*'], saw)

    def _commit(self, tx, by, words, **extra):
        rec = {"at": self.now().strftime("%Y-%m-%dT%H:%M:%SZ"), "by": by, "words": words,
               "parts": tx.parts}
        rec.update({k: v for k, v in extra.items() if v is not None})
        if tx.extra.get("passive"):
            rec["passive"] = True
        rec = self.log.append(rec)
        for p in rec["parts"]:
            self.state.apply(p["facts"], rec["seq"])
        # In-page modules have no child process to reap their leases.
        for mid in {h['by'] for h in self.leases.values()}:
            if self.state.get(mid, 'kind') == 'widget' and (not self.state.get(mid, 'on') or
                                                          self.state.get(mid, 'forgotten')):
                self.release(mid=mid)
        for p in rec["parts"]:
            if rec.get("entry") or rec.get("via") in ("offer", "sign-in"):
                # a part that made things (make, post) is about what it made, so who-sees applies to its hearing: with
                # no target, a private note's words reached everyone who hears `make` (found 23 Oct)
                made = [f[0] for f in p["facts"] if f[1] == "kind" and f[2] == "0"]
                self._happen({"word": p["word"], "target": p.get("target") or (made[0] if made else None),
                              "entry": p.get('entry') or self.find_entry(p['word']),
                              "made": made, "by": rec["by"], "for": rec.get("for"),
                              "passive": rec.get("passive", False),
                              "text": p.get("words", ""), "record": rec["seq"]})
        eid = rec.get('entry')
        if self.state.get(eid, 'from') == 'verb' and not any(p.get('entry') == eid for p in rec['parts']):
            made = [f[0] for p in rec['parts'] for f in p['facts'] if f[1] == 'kind' and f[2] == '0']
            self._happen({'word': self.state.get(eid, 'word'), 'entry': eid,
                          'target': L.parse(words).target or (made[0] if made else None),
                          'made': made, 'by': rec['by'], 'for': rec.get('for'),
                          'passive': rec.get('passive', False),
                          'text': words, 'record': rec['seq']})
        with self.changed:
            self.changed.notify_all()                    # pages' streams wake on every record
        return rec

    # ------------------------------------------------------------------ hear (SHAPE section 5)
    def _happen(self, h):
        h["n"] = len(self.happenings) + 1
        self.happenings.append(h)
        del self.happenings[:-2000]                      # momentary: the last 2000 are kept for streams catching up
        if self.modules and not h.get("passive"):
            self.modules.deliver(h)
        if not h.get("passive") and self._rule_wants(h):
            if self._rules_q is None:
                import queue as _q
                self._rules_q = _q.Queue()
                threading.Thread(target=self._rule_loop, daemon=True, name="rules").start()
            self._rules_q.put((dict(h), getattr(self._local, "rule_depth", 0)))
        with self.changed:
            self.changed.notify_all()

    def announce(self, mid, word, target=None, text=""):
        """A module says something happened outside the world (`window.opened`). Delivered, not recorded."""
        with self.lock:
            if not self.state.get(mid, "on") or not self._grant_names(mid, word):
                return f"refused: {self.name(mid)} holds no grant to say {word}"
            if target is not None and target not in self.state.things:
                target = None
            self._happen({"word": word, 'entry': self.find_entry(word), "target": target, "by": mid,
                          "text": str(text)[:500], "announced": True})
        return "ok"

    def scope_grants(self, actor, word, group):
        """Only grants whose location and issuer still authorize this use."""
        eid = self.find_entry(word, group)
        entry = self.entry(eid) if eid else {}
        names = {word, entry.get("word"), entry.get("bound")} | set(str(entry.get("aliases") or "").split())
        return [g for g in self._grants_to(actor.module)
                if any(self._matches(self.state.get(g, "words"), n) for n in names if n)
                and self.state.get(g, "where") in self.up(group)
                and self.state.get(g, "by") and eid
                and self._may_person(self.state.get(g, "by"), entry, None, group, 1)]

    def reaches(self, actor, word, kind, target=None, fields=(), group=None):
        """Conjunctive grant limits: kind:, thing:, fields:, library:.
        Each matching grant must independently admit the whole write; never
        assemble a wider permission from pieces of separate grants.
        """
        if actor.kind != "module":
            return
        fits = self.scope_grants(actor, word, group or self.place)
        onlys = [str(self.state.get(g, "only") or "") for g in fits]
        def admits(only):
            if not only:
                return True
            clauses = only.split(';')
            for clause in clauses:
                if clause.startswith('kind:'):
                    if kind not in clause[5:].split(','):
                        return False
                elif clause.startswith('thing:'):
                    if target != clause[6:]:
                        return False
                elif clause.startswith('fields:'):
                    if word not in ('set', 'undo') or not fields or not set(fields) <= set(clause[7:].split(',')):
                        return False
                elif clause.startswith('library:'):
                    from .document_scope import admits
                    if not isinstance(fields, dict) or not admits(
                            self, actor, clause[8:], word, kind, target, fields, group):
                        return False
                else:
                    return False
            return True
        if fits and not any(admits(o) for o in onlys):
            if all(o.startswith('kind:') and ';' not in o for o in onlys):
                raise Refused(f"{self.name(actor.module)}'s grant for {word} reaches only "
                              f"{', '.join(o[5:] for o in onlys)} things, not a {kind}; nothing was done")
            raise Refused(f"{self.name(actor.module)}'s grant for {word} reaches only "
                          f"{', '.join(onlys)}; this {kind} write is outside that scope; nothing was done")

    def hello_for(self, mid):
        """What a module is told when it starts: who it is, what it may do, whose it is, and a folder of its own."""
        with self.lock:
            grants = [self.state.get(g, "words") for g in self._grants_to(mid)]
            owner = next((t for t in self.things("person") if self.is_steward(t)), None)
            home = self.dir / "modules" / str(self.state.get(mid, "name") or mid)
            home.mkdir(parents=True, exist_ok=True)
            return {"t": "hello", "module": self.state.get(mid, "name"), "id": mid, "grants": grants,
                    "owner": owner, "place": self.place, "for": self.state.get(mid, "for"), "home": str(home)}

    def module_own(self, mid, line, mode="do", saw=None):
        """A module acting or reading on its own, outside any call: its grants alone (and its person's rights)."""
        actor = Actor(mid, mid, "module", module=mid, caller=None)
        try:
            if saw is not None:
                saw = {t: (v if isinstance(v, dict) else int(v)) for t, v in dict(saw).items()}
            out = self.run(actor, line, saw=saw, mode=mode)
        except (Refused, ValueError, TypeError) as exc:
            return {"ok": False, "text": f"refused: {exc}", "rows": [], "records": [], "made": []}
        if mode == "see":
            with self.lock:
                self.outside_marks(self.state.get(mid, "for"), out.get("rows"))
        return out

    # ------------------------------------------------------------------ what may go to an outside service
    @staticmethod
    def _place_rule(rule):
        return any(tok.strip() in ("public", "place") for tok in str(rule).split("|"))

    def place_sees(self, t, aspect=None):
        """Whether everyone in the place sees this thing (and everything its visibility follows), and, given an aspect,
        that aspect of it: a module reading on its own sees as the place does (`_sees`)."""
        seen, cur = set(), t
        while cur:
            if cur in seen or len(seen) > 32:
                return False
            seen.add(cur)
            x = self.state.things.get(cur)
            if not x or x.get("forgotten") or not self._place_rule(x.get("sees", "place")) or x.get("sees_when"):
                return False
            cur = x.get("visibility_of")
        rule = (self.state.things.get(t) or {}).get(f"sees.{aspect}") if aspect else None
        return rule is None or self._place_rule(rule)

    def own(self, person, t):
        """Whether a thing is this person's own: made by them or their agent, or made for them (a module's work)."""
        a = self.state.things.get(t) or {}
        if a.get("for"):
            return bool(person) and person == a["for"]  # made for someone: theirs alone (review H2: a module installed
            #                                             for Alex made Pike's crew note, and it counted as Alex's)
        maker = a.get("made_by")
        mp = self.state.get(maker, "for") if self.state.get(maker, "kind") == "agent" else maker
        return bool(person) and person in (maker, mp)

    def outside_marks(self, person, rows):
        """On each row a module reads, what it may send to an outside service (Alex, 28 Oct: "Public, or my own"):
        `outside` is public (everyone in the place sees it), yours (the reader's own) or no; `outside_not` lists the
        aspects the reader sees that are narrower than the place. A module with network access isn't contained
        (SHAPE section 11): this is what an honest module asks, not a wall."""
        for row in rows or []:
            t = row.get("id") if isinstance(row, dict) else None
            if not t or t not in self.state.things:
                continue
            row["outside"] = "public" if self.place_sees(t) else ("yours" if self.own(person, t) else "no")
            narrow = sorted(a[5:] for a in self.state.things[t] if a.startswith("sees.") and a[5:] in row
                            and not self.place_sees(t, a[5:]))
            if narrow:
                row["outside_not"] = narrow
        return rows

    def _grant_names(self, who, word):
        return [g for g in self._grants_to(who) if self._matches(self.state.get(g, "words"), word)]

    def may_hear(self, person, h):
        """Who-sees for a happening: its thing must be one the reader may see. A happening addressed to one person
        (`only`, screen state such as a window's view) reaches that person alone."""
        if h.get("only") and h["only"] != person:
            return False
        return h.get("target") is None or self.shown(person, h["target"]) is not None

    def happening_for(self, person, h):
        by = "someone" if h.get("by") == "sealed" else self.name(h.get("for") or h.get("by")) if h.get("by") else None
        out = {"n": h["n"], "word": h["word"], "target": h.get("target"), "by": by, "text": h.get("text", ""),
               "record": h.get("record"), "announced": bool(h.get("announced"))}
        for m in h.get("made") or ():
            if self.state.get(m, "kind") == "said":         # a said line: whom it calls (chat.py), so a waker need
                out["said"] = m                              # not read it again
                # only people who may see the line, now: an older record (before chat.py kept `to` inside the chat)
                # or a chat that closed since must not wake an outsider with its text (card dk1245)
                out["to"] = [p for p in str(self.state.get(m, "to") or "").split() if self.shown(p, m) is not None]
                out["by_id"] = h.get("for") or h.get("by")
        return out

    def module_hears(self, mid, h):
        """A module hears a word its grants name as `hear:<word or pattern>`, about a thing it may see: what its
        person sees if it is installed for one, else what the whole place sees. Its own acts come back as `done`."""
        if h.get("by") == mid or not self.state.get(mid, "on"):
            return False
        if not any(self._matches(" ".join(w[5:] for w in (self.state.get(g, "words") or "").split()
                                          if w.startswith("hear:")), h["word"]) for g in self._grants_to(mid)):
            return False
        t = h.get("target")
        return t is None or self.shown(mid, t) is not None

    # ------------------------------------------------------------------ hold (SHAPE section 5)
    def hold(self, mid, word):
        with self.lock:
            if not self.state.get(mid, "on") or not self._grant_names(mid, word):
                return None, f"{self.name(mid)} holds no grant to hold {word}"
            lease = f"h{len(self.leases_made) + 1}"
            self.leases_made.append(lease)
            self.leases[lease] = {"lease": lease, "word": word, "by": mid, "since": time.strftime("%H:%M:%S")}
            self._happen({"word": "hold.began", "target": None, "by": mid, "text": f"{word} {lease}"})
            return lease, None

    def release(self, lease=None, mid=None):
        with self.lock:
            gone = [l for l, h in self.leases.items() if l == lease or (mid and h["by"] == mid)]
            for l in gone:
                h = self.leases.pop(l)
                self._happen({"word": "hold.ended", "target": None, "by": h["by"], "text": f"{h['word']} {l}"})
            return gone

    def undone(self):
        out = set()
        for r in self.log.records:
            if r.get("undoes"):
                out.add(r["undoes"])
                out.update(r.get("undoes_too") or ())        # rule acts that went back with the act that caused them
        return out

    # ------------------------------------------------------------------ the act loop
    def run(self, actor, line, press=None, saw=None, mode="do"):
        """A whole line: its steps in order, each its own record; a refused step refuses only itself, the rest still run.
        -> {ok, text, rows, records, made}. A refusal or a broken word is kept in `refusals` (refusals.py), once, by
        the outermost run on this thread: a press whose button's line refuses inside is one refusal."""
        depth = getattr(self._local, "runs", 0)
        self._local.runs = depth + 1
        try:
            out = self._run(actor, line, press, saw, mode)
        except Exception as exc:                         # noqa: BLE001  kept, then raised as before
            if depth == 0:
                self.refusals.error(exc, line, actor=actor, via="press" if press else "line")
            raise
        finally:
            self._local.runs = depth
        if depth == 0 and not out.get("ok"):
            kept = out.pop("kept", None)
            text = kept or out.get("text", "")
            self.refusals.keep(text[text.find("refused:"):] if "refused:" in text else text, line, actor=actor,
                               via="press" if press else "line", mode=mode if mode != "do" else None,
                               vouched=bool(kept))
        return out

    def _run(self, actor, line, press=None, saw=None, mode="do"):
        if press:
            with self.lock:
                for r in self.log.records:
                    if r.get("press") == press:
                        return {"ok": True, "text": f"already done, as r{r['seq']}", "rows": [], "records": [], "made": []}
        steps = L.split_batch(line)
        out = {"ok": True, "text": "", "rows": [], "records": [], "made": []}
        texts = []
        handles = {}
        kept = self.session_names(actor)
        last = kept.new if kept is not None else None
        for i, s in enumerate(steps):
            if L.parse(s).word not in ("help", "?"):         # help $today asks about the word, not today's date
                s = self.fill_handles(s, handles)
                # as= names from earlier lines of this sign-in, and $me $here $today $now $new; outside quotes (dk1368)
                s = self.fill_names(s, {**self.plain_fills(actor, last), **(kept or {})})
            pressed = pressed_id = None
            try:
                self.reserved_as(s)
                s, pressed, pressed_id = self.pressed_line(actor, s, mode=mode)
                r = self.step(actor, s, press=press if len(steps) == 1 else None, saw=saw, mode=mode)
                if pressed:
                    r = dict(r, text=f"pressed {pressed}: {r.get('text', '')}")
                self.keep_handle(s, r.get("made"), handles)
                if r.get("made"):
                    last = r["made"][-1]
                if kept is not None:
                    self.keep_handle(s, r.get("made"), kept)
                    kept.new = last
            except Refused as exc:
                unnamed = self.unfilled_names(s)
                if unnamed:
                    exc = Refused(f"{exc}; " + self.unnamed_why(unnamed, kept), kept=getattr(exc, "kept", None))
                # a pressed button's refusal names the line it ran, so a receipt or `refusals` says which line failed
                texts.append(f"refused: pressing {pressed} ran {s}: {exc}" if pressed else f"refused: {exc}")
                if getattr(exc, "kept", None):
                    # by id only: a member's label and does= line are their words (refusals session, 28 Oct)
                    out["kept"] = f"refused: pressing {pressed_id}: {exc.kept}" if pressed else f"refused: {exc.kept}"
                # Alex's rule (17 Oct, confirmed 5 Nov): a refused line refuses only itself; the lines after it still
                # run. What it would have made never existed, so $new refuses for the rest of this batch rather than
                # naming something older.
                out["ok"] = False
                last = None
                handles.pop("new", None)
                continue
            texts.append(r["text"])
            out["rows"] += r.get("rows", [])
            if r.get("record"):
                out["records"].append(f"r{r['record']}")
            out["made"] += r.get("made", [])
        out["text"] = "\n".join(t for t in texts if t)
        if self.modules:
            self.modules.reconcile()
        return out

    def pressed_line(self, actor, text, mode="do"):
        """press <button> -> (its does= line, its label, its id). The line runs as an ordinary typed line, outside any lock, so
        a module word in it answers as it would from a click. Anything else -> (text, None)."""
        st = L.parse(text)
        with self.lock:
            try:
                eid = self.find_entry(st.word)
            except Refused:
                return text, None, None
            if not eid or self.state.get(eid, "bound") != "press" or self.state.get(eid, "from") != "kernel":
                return text, None, None
            if mode == "see":
                raise Refused(f"{st.word} acts; /see runs only readings; send it through /do")
            if not st.target and st.words:
                self.name_target(actor, st, self.entry(eid), None)
            if not st.target:
                raise Refused("press <button>: say which, by its label or id (rows button lists them)")
            a = self.shown(actor.person, st.target)
            if a is None:
                raise self.no_such(st.target)
            line = str(a.get("does") or "").strip()
            if not line:
                raise Refused(f"{a.get('label') or st.target} has nothing to press: only a thing with does=\"<line>\" "
                              f"(a button) runs a line")
            return line, str(a.get("label") or st.target), st.target

    @staticmethod
    def fill_handles(text, handles):
        """`$name` -> the thing a step earlier in the same line or answer made with `as=name` (the desk's form)."""
        if not handles or "$" not in text:
            return text
        if "new" in handles:                           # $new fills only where a thing goes, as the plain fills do
            text = Kernel.fill_names(text, {"new": handles["new"]})
        return L.re.sub(r"\$([a-z][a-z0-9_]*)\b",
                        lambda m: m.group(0) if m.group(1) == "new" else handles.get(m.group(1), m.group(0)), text)

    @staticmethod
    def keep_handle(text, made, handles):
        name = L.parse(text).kv.get("as")
        if name and made:
            handles[name] = made[-1]
        if made:
            handles["new"] = made[-1]                  # $new: the last thing made by an earlier step

    # the names the kernel fills itself, never an as= name: in any line ($me $here $today $now $new), and where a
    # verb, a rule, the painter or a component lens runs ($target $this $by $item $carried $view $viewer). help $
    SUPPLIED = frozenset({"me", "here", "today", "now", "new", "target", "this", "by", "said", "item", "carried", "view",
                          "viewer"})
    SESSION_NAMES = 64                                 # a sign-in keeps its last 64 as= names; older ones are dropped

    def plain_fills(self, actor, last=None):
        """What `$me $here $today $now $new` say in a line: who is acting (an agent is itself), the place, the
        kernel's date and time (UTC), and the last thing made earlier in this line or sign-in (`$new`)."""
        now = self.now()
        out = {"me": actor.id, "here": self.place, "today": now.date().isoformat(),
               "now": now.strftime("%Y-%m-%dT%H:%M:%SZ")}
        if last:
            out["new"] = last
        return out

    def reserved_as(self, text):
        name = L.parse(text).kv.get("as")
        if name in self.SUPPLIED:
            raise Refused(f"as={name}: ${name} is a fill-in the kernel supplies, so it can't name a thing; "
                          f"choose another name (help $ lists them)")

    def session_names(self, actor):
        """-> the dict of as= names this actor's sign-in keeps, or None where none last (a rule's line, or a line run
        inside another line). In memory only: a kernel restart forgets them, and nobody else's sign-in sees them."""
        if getattr(self._local, "runs", 0) > 1 or getattr(self._local, "rule", None):
            return None
        return self.names.setdefault((actor.id, actor.session), _Names(self.SUPPLIED, self.SESSION_NAMES))

    QUOTED = L.re.compile(r"\"(?:\\.|[^\"\\])*\"?|'(?:\\.|[^'\\])*'?")
    NAME = L.re.compile(r"\$([a-z][a-z0-9_]*)\b")

    @classmethod
    def fill_text(cls, text, names, facts, read):
        """The same $ names in prose, plus $.fact and $[[thing|label]].fact.

        Unlike a command, quoted prose is still prose. Substitute once: values
        are data, never another template or a line to execute. `read` must use
        the caller's ordinary visibility fence. Missing fills fail explicitly.
        """
        field = r"[A-Za-z_][A-Za-z0-9_-]*"
        pattern = L.re.compile(
            r"\$\[\[([^\]\n]+)\]\]\.(" + field + r")|\$\.(" + field + r")|" + cls.NAME.pattern)

        def fill(match):
            target, prop, local, name = match.groups()
            values = read(target.split("|", 1)[0]) if target else facts if local else names
            key = prop or local or name
            if key not in values:
                raise ValueError("unfilled " + match.group(0))
            return str(values[key])

        return pattern.sub(fill, text)

    @classmethod
    def fill_names(cls, text, names):
        """`$name` -> what an earlier line of this sign-in made with as=name, or a plain fill ($me …). Only where a
        thing goes: never inside quoted text, so a verb's steps="... $card" or a note about $today keeps its words."""
        if not names or "$" not in text:
            return text
        out, at = [], 0
        for q in list(cls.QUOTED.finditer(text)) + [None]:
            end = q.start() if q else len(text)
            out.append(cls.NAME.sub(lambda m: names.get(m.group(1), m.group(0)), text[at:end]))
            if q:
                out.append(q.group(0))
                at = q.end()
        return "".join(out)

    def unfilled_names(self, text):
        """The `$name`s left in a line outside quotes, other than what a later part fills itself."""
        bare = self.QUOTED.sub(" ", text or "")
        return [n for n in dict.fromkeys(self.NAME.findall(bare)) if n == "new" or n not in self.SUPPLIED]

    def unnamed_why(self, unnamed, kept):
        if unnamed == ["new"]:
            return "$new is the last thing made, and nothing was made yet in this line or sign-in"
        unnamed = [n for n in unnamed if n != "new"]
        said = ", ".join("$" + n for n in unnamed)
        if kept is None:
            return f"{said} names nothing here: a line run by a rule or inside another line has only its own as= names"
        have = ", ".join("$" + n for n in kept) or "none yet"
        return (f"{said} names nothing: no earlier line of this sign-in said as={unnamed[0]} (yours: {have}). "
                f"as= names last for your sign-in until the kernel restarts; help $ lists every fill-in")

    def step(self, actor, text, press=None, saw=None, mode="do"):
        from .words import KERNEL
        st = L.parse(text)
        if st.word == "do" and text.strip()[2:].strip():
            text = text.strip()[2:].strip()            # the desk's `do <word> …`, which every lens gesture says
            st = L.parse(text)
        if not st.word:
            raise Refused("an empty line; help lists the words you may use")
        with self.lock:
            self.check_participants(actor, saw)
            group = st.kv.get("in") or None
            if group and self.state.get(group, "kind") not in ("place", "group"):
                raise self.no_such(group)
            eid = self.find_entry(st.word, group)
            if eid is None and st.word in FLOOR and self.is_steward(actor.person):
                eid = next((e for e in self.things('word') if self.state.get(e, 'from') == 'kernel'
                            and self.state.get(e, 'bound') == st.word), None)
            if eid is None:
                eid = self.plain_verb(actor, st, group)            # close Help: window.close, from Help's kind
            if eid is None:
                from .helping import suggest
                raise Refused(f"nothing answers to '{st.word}' here; " + suggest(self, actor, st.word, group))
            entry = self.entry(eid)
            st.word = entry['word']
            if mode == "see" and entry.get("word_kind") != "see":
                raise Refused(f"{st.word} is an act; /see runs only readings; send it through /do")
            text = L.re.sub(r'^\S+', st.word, text, count=1)
            takes = self.takes_id(entry.get("takes"))
            if st.target and takes is None:
                st.words = (st.target + " " + st.words).strip()       # a word that takes no thing: an id is words
                st.target = None
            self.name_target(actor, st, entry, group)          # a name where a thing goes (P1)
            if st.target and L.ID.match(st.target):
                if self.shown(actor.person, st.target) is None:
                    raise self.no_such(st.target)                     # the same words as for a thing that isn't there
                group = group or (st.target if self.state.get(st.target, "kind") in ("group", "place")
                                  else (self.groups_of(st.target) or [None])[0])
            elif takes == "required":
                raise Refused(self.needs_a_thing(actor, st, entry, text))
            group = group or self.place
            if not self.may(actor, entry, st.target, group):
                if actor.kind == "module" and self._may_person(actor.person, entry, st.target, group):
                    raise Refused(f"{self.name(actor.module)} holds no grant for {st.word}; nothing was done")
                raise self.refusal_for(entry, group)
            self.guard(actor, entry, st)
            if entry.get("word_kind") == "do":
                said = self.once(actor, entry, st.target)
                if said:
                    raise Refused(said)
            src, name = self.source(entry)
            if src == "kernel":
                fn = KERNEL.get(name)
                if fn is None:
                    raise Refused(f"{st.word} is unbound: the kernel has no word {name}")
                if entry.get("word_kind") == "see":
                    return fn(self, actor, st, entry, None, group)
                tx = Tx(self)
                tx.part(st.word, st.target, text)
                tx.parts[-1]["entry"] = eid
                res = fn(self, actor, st, entry, tx, group, saw=saw)
                if tx.empty:
                    return res
                rec = self._commit_use(tx, actor, text, entry, press, saw, st)
                res["record"] = rec["seq"]
                res["made"] = tx.made
                res["text"] = res["text"].replace("[r?]", f"[r{rec['seq']}]")
                return res
        if src == "verb":
            return self.verb_note(actor, st, entry, group, text, press, saw, mode)
        if src == "module":
            return self.module_word(actor, st, entry, group, text, press, saw)  # no lock held while the module works
        raise Refused(f"{st.word} is unbound: its entry says it comes from {src}, which this kernel does not run yet")

    def _commit_use(self, tx, actor, words, entry, press, saw, st):
        self.check_participants(actor, saw)
        rec = self._commit_use_record(tx, actor, words, entry, press, saw, st)
        # your own act marks what it wrote as seen (the desk's rule): a thing it made, whole; a thing you had looked
        # at, the aspects it changed. A thing you never looked at stays unlooked.
        marks = self.seen.setdefault(actor.seen_key, {})
        for p in tx.parts:
            for f in p["facts"]:
                if f[0] in tx.made or f[0] in marks:
                    m = marks.setdefault(f[0], {})
                    m[f[1]] = rec["seq"]
                    if f[0] in tx.made:
                        m["*"] = rec["seq"]
        return rec

    def _commit_use_record(self, tx, actor, words, entry, press, saw, st):
        if entry.get('undo') == 'external' or any(
                self.state.get(p.get('entry'), 'undo') == 'external' for p in tx.parts):
            tx.extra['external'] = True
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
        turn = self.turn_of(actor) if not getattr(self._local, "cause", None) else {}
        return self._commit(tx, by=by, words=words, entry=entry["id"], press=press, undoes=undoes,
                            rule=getattr(self._local, "rule", None),         # a rule ran it (never on a sealed act)
                            caused_by=getattr(self._local, "cause", None),   # the act whose happening fired that rule
                            because=turn.get("because"),                     # what the agent's turn is answering
                            work=turn.get("work"),                           # the card the turn is working on
                            external=tx.extra.get("external"),
                            **{"for": actor.person if by != actor.person else None,
                               "via": "module" if actor.kind == "module" else ("agent" if actor.kind == "agent" else None),
                               "saw": saw})

    def turn_of(self, actor):
        """The turn an agent is working (kernel `turn`, said by the house that woke it): what it answers and the card
        it works on. A module answering an agent's call carries the agent's turn. Kept in memory, never in the world."""
        a = actor
        for _ in range(8):
            if a is None:
                return {}
            if a.kind in ("agent", "person"):
                return self.turns.get(a.id) or {}
            a = a.caller
        return {}

    # ------------------------------------------------------------------ verb notes (SHAPE section 4)
    def verb_note(self, actor, st, entry, group, text, press=None, saw=None, mode="do"):
        """A word made of other words. Its steps run as whoever said it (it never adds power). A see verb's steps are
        readings; a do verb's steps are the kernel's own words and make ONE record, so one undo takes it all back."""
        from .words import KERNEL
        depth = getattr(self._local, "verb_depth", 0)
        if depth > 4:
            raise Refused(f"{entry['word']} calls words that call it, too deep; nothing was done")
        args = ([st.target] if st.target else []) + st.words.split()
        raw_steps = entry.get('steps_bound') or entry.get("steps") or ""
        # names a later part of the line fills itself: handles (as=card) and what the painter and rules supply
        later = set(L.re.findall(r"\bas=([a-z][a-z0-9_]*)", raw_steps)) | self.SUPPLIED
        unfilled = "\x00unfilled\x00"
        plain = {k_: v for k_, v in self.plain_fills(actor).items() if k_ != "new"}   # $me $here $today $now
        free = " ".join(args).strip()
        if free and not L.re.search(r"\$([1-9*]|target\b|this\b)", raw_steps):
            # task.add "buy milk": free words where a verb has no place for them fill its first setting nobody gave
            first = next((n for n in L.re.findall(r"=\$([a-z][a-z0-9_]*)\b", raw_steps)
                          if n not in st.kv and n not in later), None)
            if first:
                st.kv = dict(st.kv, **{first: free})

        def fill(x):
            # Named values are quoted and inserted in ONE substitution pass: a
            # supplied '$1', quote or semicolon stays data.
            import shlex
            def sub(m):
                key = m[1]
                if key in ("target", "this"):            # $this: the old desk's word for the thing a verb is on
                    return st.target or (args[0] if args else "")
                if key in plain and key not in st.kv:
                    return plain[key]
                if key == "*":
                    return " ".join(args)
                if key.isdecimal():
                    return args[int(key) - 1] if len(args) >= int(key) else ""
                if key in st.kv:
                    return shlex.quote(st.kv[key])
                return m[0] if key in later else unfilled
            out = L.re.sub(r"\$(target\b|this\b|[1-9]|\*|[a-z][a-z0-9_]*\b)", sub, x)
            # a key=$name nobody gave is left out, not stored as "$name" (and a set does not erase that fact)
            out = L.re.sub(r"\s*\b[a-z_][a-z0-9_.-]*=" + unfilled, "", out)
            return out.replace(unfilled, "")
        steps = [fill(x) for x in L.split_batch(raw_steps) if x.strip()]
        self._local.verb_depth = depth + 1
        try:
            if entry.get("word_kind") == "see":
                said, rows, values = [], [], []
                previous = getattr(self._local, "predicate", None)
                if previous is None and st.target:
                    self._local.predicate = (st.target, st.kv.get("answer", ""), False)
                try:
                    for x in steps:
                        if getattr(self._local, "predicate_depth", 0):
                            pe = self.find_entry(L.parse(x).word, group)
                            if not pe or self.source(self.entry(pe))[0] not in ("kernel", "verb"):
                                raise Refused("a condition cannot call a module")
                        r = self.step(actor, x, mode="see")
                        said.append(r.get("text", ""))
                        rows += r.get("rows", [])
                        values.append(r.get("value"))
                    return {"text": "\n".join(t for t in said if t), "rows": rows,
                            "value": values[0] if len(values) == 1 else None}
                finally:
                    self._local.predicate = previous
            with self.lock:
                firsts = [L.parse(x) for x in steps]
                kinds = [self.source(self.entry(e))[0] if e else None for e in
                         [self.find_entry(f.word if f.word != "do" else L.parse(x.strip()[2:]).word,
                                          f.kv.get("in") or group) for f, x in zip(firsts, steps)]]
            if "module" in kinds:
                return self._verb_with_modules(actor, st, entry, group, text, steps, press, saw)
            with self.lock:
                said = self.once(actor, entry, st.target)
                if said:
                    raise Refused(said)
                tx, notes, handles = Tx(self), [], {}
                for x in steps:
                    x = self.fill_handles(x, handles)
                    s2 = L.parse(x)
                    if s2.word == "do":
                        x = x.strip()[2:].strip()
                        s2 = L.parse(x)
                    g = s2.kv.get("in") or group
                    eid = self.find_entry(s2.word, g)
                    if eid is None:
                        raise Refused(f"{entry['word']} stopped at '{x}': nothing answers to {s2.word}; nothing was done")
                    e = self.entry(eid)
                    s2.word = e['word']
                    x = L.re.sub(r'^\S+', s2.word, x, count=1)
                    if self.source(e)[0] != "kernel":
                        raise Refused(f"{entry['word']} stopped at '{x}': {s2.word} comes from {e.get('from')}, "
                                      f"which a verb note's steps can't run yet; nothing was done")
                    if s2.target and self.takes_id(e.get("takes")) is None:
                        s2.words, s2.target = (s2.target + " " + s2.words).strip(), None
                    try:
                        self.name_target(actor, s2, e, g)            # a step given a name ($2 = "Appearance")
                    except Refused as exc:
                        raise Refused(f"{entry['word']} stopped at '{x}': {exc}; nothing was done",
                                      kept=f"{entry['word']} stopped at '{x}': {exc.kept}; nothing was done"
                                      if getattr(exc, "kept", None) else None)
                    if s2.target and L.ID.match(s2.target):
                        if self.shown(actor.person, s2.target) is None:
                            raise self.no_such(s2.target)
                        g = s2.kv.get("in") or (self.groups_of(s2.target) or [group])[0]
                    if not self.may(actor, e, s2.target, g):
                        raise Refused(f"{entry['word']} stopped at '{x}': {self.refusal_for(e, g)}; nothing was done")
                    self.guard(actor, e, s2)
                    if e.get("word_kind") == "see":
                        notes.append(KERNEL[self.source(e)[1]](self, actor, s2, e, None, g).get("text", ""))
                        continue                    # a reading inside an act: it marks what it read as seen
                    said = self.once(actor, e, s2.target, tx)
                    if said:
                        raise Refused(f"{entry['word']} stopped at '{x}': {said}; nothing was done")
                    made_before = len(tx.made)
                    tx.part(s2.word, s2.target, x)
                    tx.parts[-1]["entry"] = eid
                    res = KERNEL[self.source(e)[1]](self, actor, s2, e, tx, g, saw=saw)
                    notes.append(res["text"])
                    self.keep_handle(x, tx.made[made_before:], handles)
                if tx.empty:
                    return {"text": "\n".join(n for n in notes if n)}
                rec = self._commit_use(tx, actor, text, entry, press, saw, st)
                body = "\n".join(n.replace("[r?]", f"[r{rec['seq']}]") for n in notes if n)
                return {"text": f"{body}\n~ {entry['word']}, one act [r{rec['seq']}]", "record": rec["seq"],
                        "made": tx.made}
        finally:
            self._local.verb_depth = depth

    def _verb_with_modules(self, actor, st, entry, group, text, steps, press=None, saw=None):
        """A do verb with module words among its steps: each module is asked as the caller (no lock held while it
        works), and its answer's lines join the verb's one act, checked as the caller narrowed to that module. A module
        reads the world as it was before the verb began; it can't name what an earlier step made. A step that changed
        the outside world (an external answer) makes the whole act one that undo refuses."""
        from .words import KERNEL
        tx, notes, handles, asked, external = Tx(self), [], {}, [], []

        def stop(x, why, kept=None):
            for mid, use in asked:
                self.modules.done(mid, use, {"ok": False, "refused": why, "made": [], "text": why})
            if not asked:
                return Refused(f"{entry['word']} stopped at '{x}': {why}; nothing was done",
                               kept=f"{entry['word']} stopped at '{x}': {kept}; nothing was done" if kept else None)
            # an earlier step's module may already have acted on the screen; the world records none of it
            who = ", ".join(dict.fromkeys(self.state.get(m, "name") for m, _ in asked))
            return Refused(f"{entry['word']} stopped at '{x}': {why}. Nothing was recorded, but {who} answered an "
                           f"earlier step and may already have acted (the screen can differ from the world until it "
                           f"catches up)")
        for x in steps:
            x = self.fill_handles(x, handles)
            s2 = L.parse(x)
            if s2.word == "do":
                x = x.strip()[2:].strip()
                s2 = L.parse(x)
            g = s2.kv.get("in") or group
            with self.lock:
                eid = self.find_entry(s2.word, g)
                if eid is None:
                    raise stop(x, f"nothing answers to {s2.word}")
                e = self.entry(eid)
                s2.word = e['word']
                x = L.re.sub(r'^\S+', s2.word, x, count=1)
                if s2.target and self.takes_id(e.get("takes")) is None:
                    s2.words, s2.target = (s2.target + " " + s2.words).strip(), None
                try:
                    self.name_target(actor, s2, e, g)            # tidy Feed Appearance: $2 by name, as typed
                except Refused as exc:
                    raise stop(x, str(exc).removeprefix("refused: "), getattr(exc, "kept", None))
                if s2.target and L.ID.match(s2.target):
                    if s2.target in tx.made:
                        if self.source(e)[0] == "module":
                            raise stop(x, f"{s2.target} is made by this verb and is not in the world yet, so a "
                                          f"module can't be asked about it")
                    elif self.shown(actor.person, s2.target) is None:
                        raise stop(x, f"no thing called {s2.target} here")
                    else:
                        g = s2.kv.get("in") or (self.groups_of(s2.target) or [group])[0]
                if not self.may(actor, e, s2.target, g):
                    raise stop(x, str(self.refusal_for(e, g)))
                self.guard(actor, e, s2)
                src, name = self.source(e)
            if src == "module":
                if len(steps) == 1:
                    s2.kv.setdefault('in', g)  # a module alias retains the caller's group
                mid = self.module_named(name)
                if not mid or not self.state.get(mid, "on") or not self.modules or not self.modules.running(mid):
                    raise stop(x, f"{s2.word} is unbound: {name} is not running")
                ans = self.modules.call(mid, e.get("bound") or e["word"],
                                        {"target": s2.target, "words": s2.words, "kv": s2.kv}, caller=actor)
                if ans.get("refused"):
                    raise stop(x, f"{name}: {ans['refused']}")
                asked.append((mid, ans.get("use")))
                if e.get("word_kind") == "see" or not (ans.get("lines") or ans.get("external") or e.get('undo') == 'external'):
                    notes.append(ans.get("text", ""))
                    continue
                if ans.get("external") or e.get('undo') == 'external':
                    external.append(name)
                    notes.append(f"{s2.word}: {ans.get('text') or 'done outside the world'}")
                    continue
                with self.lock:
                    try:
                        notes += self._admit_lines(tx, mid, actor, e, ans)
                    except Refused as exc:
                        raise stop(x, str(exc).replace("; nothing was done", ""), getattr(exc, "kept", None))
                continue
            with self.lock:
                if e.get("word_kind") == "see":
                    notes.append(KERNEL[name](self, actor, s2, e, None, g).get("text", ""))
                    continue
                said = self.once(actor, e, s2.target, tx)
                if said:
                    raise stop(x, said)
                made_before = len(tx.made)
                tx.part(s2.word, s2.target, x)
                tx.parts[-1]["entry"] = eid
                try:
                    res = KERNEL[name](self, actor, s2, e, tx, g, saw=saw)
                except Refused as exc:
                    raise stop(x, str(exc), getattr(exc, "kept", None))
                notes.append(res["text"])
                self.keep_handle(x, tx.made[made_before:], handles)
        with self.lock:
            changed = self._changed_under(tx)
            if changed:
                raise stop(steps[-1], f"{changed} changed while the verb ran")
            if tx.empty and not external:
                return {"text": "\n".join(n for n in notes if n)}
            if external:
                tx.extra["external"] = True
            if tx.empty:
                tx.part(st.word, st.target, text)
                tx.parts[-1]['entry'] = entry['id']
            # A one-step module alias keeps the module's authorship, while its
            # own entry still holds undo/once/seal metadata and its happening.
            author = Actor(asked[0][0], actor.person, 'module', module=asked[0][0], caller=actor) \
                if len(steps) == 1 and asked else actor
            rec = self._commit_use(tx, author, text, entry, press, saw, st)
        for mid, use in asked:
            self.modules.done(mid, use, {"ok": True, "record": f"r{rec['seq']}", "made": tx.made, "text": ""})
        body = "\n".join(n.replace("[r?]", f"[r{rec['seq']}]") for n in notes if n)
        tail = f"\n~ {entry['word']}, one act [r{rec['seq']}]" + (
            f"; it touched the outside world through {', '.join(external)}, so undo cannot take it back"
            if external else "")
        return {"text": body + tail, "record": rec["seq"], "made": tx.made}

    def _changed_under(self, tx):
        """A thing whose fact moved since `tx` read it (the lock was let go while a module worked), or None."""
        from .store import h as _h
        first = {}
        for p in tx.parts:
            for f in p["facts"]:
                first.setdefault((f[0], f[1]), f[2])
        for (t, a), before in first.items():
            if _h(self.state.things.get(t, {}).get(a, GONE)) != before:
                return t
        return None

    # ------------------------------------------------------------------ rules (SHAPE section 5)
    RULE_DEPTH = 3

    def _rule_wants(self, h):
        if getattr(self._local, "rule_depth", 0) >= self.RULE_DEPTH:
            return False                    # a rule's act may wake rules, three deep at most
        return any(self._rule_matches(self.state.things[r], h) for r in self.things('rule'))

    def _rule_hears(self, rid, r, h, maker):
        """Whose acts a rule hears: `by=` (Alex, 28 Oct: "You, your agents, leaders"). A rule runs as its maker, so by
        default it hears only acts its maker would trust: the maker's own, their agents', and the leaders' of the
        rule's group (the place's stewards for a rule in the place). `by=anyone` hears everyone, as do rules made
        before by= existed. A sealed act is heard only by `by=anyone`: matching it on who acted would tell the rule's
        maker who did it (security review round 2; SHAPE section 8). A module acting on its own is no one's act."""
        by = str(r.get("by") or "anyone")
        if by == "anyone":
            return True
        first = h
        rec = h.get("record")
        if rec and rec <= len(self.log.records) and self.log.records[rec - 1].get("caused_by"):
            # a rule's own act is judged by the act that started the chain, so a member's act can't reach a
            # by=maker rule through a leader's by=anyone rule (approved-builds review M4)
            cause = self.log.records[self.log.records[rec - 1]["caused_by"] - 1]
            first = {"by": cause.get("by"), "for": cause.get("for")}
        if h.get("by") == "sealed" or first.get("by") == "sealed":
            return False
        who = first.get("for") or first.get("by")
        if who and self.state.get(who, "kind") in ("module", "widget"):
            # a module on its own acts for the person it is installed for (Alex's window module: a new window is his
            # screen's); a module installed for no one (a relay of outside text) is no one's act
            who = self.state.get(who, "for")
        if not who:
            return False
        if who in (maker.id, maker.person):
            return True
        if self.state.get(who, "kind") != "person":
            return False
        return any(self.is_leader(who, g) for g in (self.groups_of(rid) or [self.place]))

    def _rule_matches(self, r, h):
        word = r.get('on_entry') == h.get('entry') if r.get('on_entry') else r.get('on') == h.get('word')
        return word and (not r.get('of_kind') or self.state.get(h.get('target'), 'kind') == r['of_kind'])

    def _rule_loop(self):
        import queue as _q
        while True:
            try:
                h, depth = self._rules_q.get(timeout=60)
            except _q.Empty:
                continue
            try:
                self._fire_rules(h, depth)
            except Exception as exc:        # noqa: BLE001  a rule never stops the kernel
                self.notices.append(f"a rule failed on {h.get('word')}: {exc!r}")

    def actor_of(self, who):
        kind = self.state.get(who, "kind")
        if kind == "person":
            return Actor(who, who, "person")
        if kind == "agent":
            return Actor(who, self.state.get(who, "for"), "agent")
        if kind in ("module", "widget"):
            return Actor(who, who, "module", module=who, caller=None)
        return None

    def _fire_rules(self, h, depth):
        """`make kind=rule on=<word> do="<line>"`: after each happening of that word which the rule's maker may hear,
        the line runs as the maker ($target, $by filled), on the rules' own thread; its records say `rule`."""
        with self.lock:
            rules = [(r, dict(self.state.things[r])) for r in self.things("rule")
                     if self._rule_matches(self.state.things[r], h) and not self.state.get(r, "forgotten")
                     and str(self.state.get(r, "off") or "") not in ("yes", "True")
                     and (h.get("record") or 10 ** 12) > self.state.last_seq(r, "kind")]    # not its own making
        for rid, r in rules:
            actor = self.actor_of(r.get("made_by"))
            if actor is None:
                continue
            with self.lock:
                if not self.may_hear(actor.person, h) or not self._rule_hears(rid, r, h, actor):
                    continue
            by = "" if h.get("by") == "sealed" else str(h.get("for") or h.get("by") or "")
            line = L.re.sub(r"\$(target|item)\b", lambda m: h.get("target") or "",       # $item: the old desk's word
                            str(r.get('do_bound') or r.get("do") or "")).replace("$by", by)
            # The exact immutable message made by this happening, not the latest
            # message in its chat (which may already have another speaker).
            said = next((m for m in h.get("made") or [] if self.state.get(m, "kind") == "said"), "")
            line = L.re.sub(r"\$said\b", lambda m: said, line)
            resting = self._rule_rests(line)
            if resting:
                self.rules_fired = (self.rules_fired + [(rid, h.get("n"), f"resting: {resting} is off")])[-50:]
                continue
            self._local.rule, self._local.rule_depth = rid, depth + 1
            first = h.get("record")
            if first and first <= len(self.log.records):
                first = self.log.records[first - 1].get("caused_by") or first          # a chain keeps its first act
            self._local.cause = first
            try:
                out = self.run(actor, line)
            finally:
                self._local.rule, self._local.rule_depth, self._local.cause = None, 0, None
            self.rules_fired = (self.rules_fired + [(rid, h.get("n"), out["text"].split("\n")[0])])[-50:]

    def _rule_rests(self, line):
        """A rule whose line is a word of a module that is off rests with that module (`off guy` is the switch for
        the guy and for what asks him), so it is not run, and not a refusal each time its happening comes round
        (28 Oct: three guy rules were refused every few minutes while the guy was off). -> the module's name, or None."""
        word = (line.split() or [""])[0]
        with self.lock:
            try:
                eid = self.find_entry(word)
            except Refused:
                return None
            if eid is None:
                return None
            src, name = self.source(self.entry(eid))
            if src != "module":
                return None
            mid = self.module_named(name)
            return name if mid and not self.state.get(mid, "on") else None

    # ------------------------------------------------------------------ module words
    def module_word(self, actor, st, entry, group, text, press, saw=None):
        from . import document_scope as docs
        bound = entry.get("bound") or entry["word"]
        if bound in docs.WORDS:
            with self.lock:
                library = docs.selection(self, actor, bound, st.target, st.kv)
                if st.words or not library:
                    raise Refused("Documents request is outside a visible inherited library; nothing was done")
                # Every module in the caller chain must independently admit the
                # same selection; clauses from separate grants never combine.
                current = actor
                while current:
                    if current.kind == "module":
                        grants = self.scope_grants(current, bound, group)
                        if not any(str(self.state.get(g, "only") or "") in ("", "library:" + library)
                                   for g in grants):
                            raise Refused("Documents request is outside the caller's library grant; nothing was done")
                    current = current.caller
                # Per-call context, never mutate the widget's shared Actor.
                scoped = Actor(actor.id, actor.person, actor.kind, actor.module, actor.caller)
                scoped.seen_key, scoped.session = actor.seen_key, actor.session
                scoped.document_library, scoped.document_target = library, st.target
                actor = scoped
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
        if entry.get("word_kind") == "do" and (ans.get("external") or entry.get('undo') == 'external'):
            # it changed the outside world (a window opened), not the world: an act with its words and no facts,
            # which undo refuses (SHAPE section 11)
            with self.lock:
                tx = Tx(self)
                tx.part(st.word, st.target, text)
                rec = self._commit(tx, by=mid, words=text, entry=entry["id"], press=press, external=True,
                                   **{"for": actor.person, "via": "module"})
            return {"text": f"ok {st.word} [r{rec['seq']}] · {ans.get('text') or 'done outside the world'}"
                            f"\n~ by {self.name(mid)} for {self.name(actor.person)}; it touched the outside world, "
                            f"so undo cannot take it back", "record": rec["seq"], "rows": ans.get("rows", [])}
        if entry.get("word_kind") == "see" or not ans.get("lines"):
            return {"text": ans.get("text", ""), "rows": ans.get("rows", [])}
        try:
            out = self.admit(mid, actor, text, entry, ans, press, saw)
        except Refused as exc:
            self.modules.done(mid, ans.get("use"), {"ok": False, "refused": str(exc), "made": [], "text": str(exc)})
            raise
        self.modules.done(mid, ans.get("use"), {"ok": True, "made": out.get("made", []), "text": out.get("text", ""),
                                                **({"record": f"r{out['record']}"} if out.get("record") else {})})
        # A declarative module's receipt is meaningful only after admission, including
        # successful equality/no-op. Previously its detailed text/rows were discarded.
        if ans.get("text"):
            out["text"] += "\n" + ans["text"]
        if ans.get("rows"):
            out["rows"] = ans["rows"]
        return out

    def admit(self, mid, caller, text, entry, ans, press=None, press_saw=None):
        """A module's answer: its lines run as one use, one record, as the caller narrowed to the module, and only if
        what it read is unchanged (SHAPE section 11). Refused whole otherwise. A painted press says what its page
        showed (`press_saw`): an answer that writes a thing the page showed is fenced on that too, so two leaders
        pressing Next on one painted agenda move it once, though the module read it fresh both times."""
        author = Actor(mid, caller.person, "module", module=mid, caller=caller)
        saw = self._module_saw(mid, ans)
        with self.lock:
            tx = Tx(self)
            notes = self._admit_lines(tx, mid, caller, entry, ans, press_saw)
            if tx.empty:
                return {"text": "\n".join(notes)}
            rec = self._commit_use(tx, author, text, entry, press, saw, L.parse(text))
            body = "\n".join(n.replace("[r?]", f"[r{rec['seq']}]") for n in notes)
            return {"text": f"{body}\n~ by {self.name(mid)} for {self.name(caller.person)}", "record": rec["seq"],
                    "made": tx.made}

    def _module_saw(self, mid, ans):
        """What a module says it read: thing -> rev, or thing -> {rev, aspects} (the per-aspect form fence() reads, so an
        unrelated change to a thing doesn't refuse an answer). Anything else is a refusal, never a crash (found 28 Oct by
        the kernel-shape review: a dict saw raised TypeError at the door)."""
        out = {}
        for t, v in (ans.get("saw") or {}).items():
            try:
                if isinstance(v, dict):
                    aspects = v.get("aspects")
                    if aspects is not None and not (isinstance(aspects, list) and all(isinstance(a, str) for a in aspects)):
                        raise ValueError
                    # no aspects named: the whole thing, as a bare rev fences it (a {rev} alone would fence only what
                    # the answer writes, weaker than the int it stands for; kernel review round 2)
                    out[str(t)] = {"rev": int(v.get("rev", 0)), "aspects": aspects or ["*"],
                                   **({"participant": True} if v.get("participant") is True else {})} \
                        if aspects or v.get("participant") is True else int(v.get("rev", 0))
                else:
                    out[str(t)] = int(v)
            except (TypeError, ValueError):
                raise Refused(f"{self.name(mid)} said it read {t} as {str(v)[:60]}; saw takes a rev, or "
                              f"{{rev, aspects}}; nothing was done")
        return out

    def _admit_lines(self, tx, mid, caller, entry, ans, press_saw=None):
        """A module's answer lines into `tx`, each checked as the caller narrowed to the module. Lock held."""
        from .words import KERNEL
        author = Actor(mid, caller.person, "module", module=mid, caller=caller)
        saw = self._module_saw(mid, ans)
        self.check_participants(author, saw)  # includes equality/no-op, before any answer lines
        if True:
            notes, handles = [], {}
            for line in ans["lines"]:
                line = self.fill_handles(str(line), handles)
                st = L.parse(line)
                if st.word == "do":
                    line = line.strip()[2:].strip()
                    st = L.parse(line)
                made_before = len(tx.made)
                group = st.kv.get('in') or ((self.groups_of(st.target) or [self.place])[0] if st.target else self.place)
                eid = self.find_entry(st.word, group)
                if eid is None:
                    raise Refused(f"{self.name(mid)} answered with '{st.word}', which nothing answers to; nothing was done")
                e = self.entry(eid)
                if self.source(e)[0] != "kernel" or e.get("word_kind") != "do":
                    raise Refused(f"{self.name(mid)} answered with {st.word}; a module's answer may hold only acts the "
                                  f"kernel runs; nothing was done")
                if st.target and self.shown(caller.person, st.target) is None:
                    raise self.no_such(st.target)
                group = st.kv.get("in") or ((self.groups_of(st.target) or [self.place])[0] if st.target else self.place)
                if self.state.get(group, "kind") not in ("place", "group"):
                    raise self.no_such(group)
                if not self.may(author, e, st.target, group):
                    if not self._may_person(caller.person, e, st.target, group):
                        raise Refused(f"{entry['word']} would {st.word} {st.target or ''}, and {self.refusal_for(e, group)}; "
                                      f"nothing was done")
                    raise Refused(f"{self.name(mid)} holds no grant for {st.word}; nothing was done")
                library = getattr(caller, "document_library", None)
                if library:
                    from .document_scope import admits
                    kind = st.kv.get("kind") if st.word == "make" else self.state.get(st.target, "kind")
                    if st.words or not admits(self, author, library, st.word, kind, st.target, st.kv, group):
                        raise Refused("Documents answer is outside the selected library; nothing was done")
                self.guard(author, e, st)
                said = self.once(author, e, st.target, tx)
                if said:
                    raise Refused(f"{said}; nothing was done")
                if press_saw and st.target in press_saw:
                    self.fence(caller, st.target, [x for x in st.kv if x not in ("in", "as")], press_saw)
                tx.part(st.word, st.target, line)
                tx.parts[-1]["entry"] = eid
                res = KERNEL[self.source(e)[1]](self, author, st, e, tx, group, saw=saw)
                notes.append(res["text"])
                self.keep_handle(line, tx.made[made_before:], handles)
            return notes

    def module_see(self, mid, caller, line):
        """A module reading while it answers a call: a see word, run as the caller narrowed to the module."""
        author = Actor(mid, caller.person, "module", module=mid, caller=caller)
        try:
            library = getattr(caller, "document_library", None)
            if library:
                from .document_scope import read_rows
                st = L.parse(line)
                # This reviewed provider only needs unadorned rows readings.
                # Refuse aliases/extra projections rather than expose raw text.
                if (st.word != "rows" or st.target or st.kv
                        or st.words not in ("document-library", "document-folder", "document-entry", "file", "post")):
                    raise Refused("Documents provider read is outside the selected library")
                with self.lock:
                    r = self.step(author, line, mode="see")
                    r["rows"] = read_rows(self, author, library, caller.document_target, st.words, r.get("rows", []))
                    r["text"] = ""  # step's original text can contain unrelated rows
            else:
                r = self.step(author, line, mode="see")
        except Refused as exc:
            return {"refused": str(exc), "text": f"refused: {exc}", "rows": []}
        # the kernel read these for the caller, so they count as the caller's look: a taskbar button that lists
        # windows through a module and then sets one is not refused "you have not looked" (desktop, 23 Oct)
        marks = self.seen.get(author.id, {})
        for row in r.get("rows") or []:
            t = row.get("id") if isinstance(row, dict) else None
            if t in marks:
                self.seen.setdefault(caller.seen_key, {})[t] = dict(marks[t])
        with self.lock:
            self.outside_marks(caller.person, r.get("rows"))
        return r

    def on_offer(self, mid, words):
        """A module offers its words. Each becomes an entry only in its own namespace, only with help, and only if
        absent; after that the entry is the world's (SHAPE section 11). -> receipt text."""
        out = []
        with self.lock:
            pattern = self.state.get(mid, "publishes")
            # what this module offers now, kept in memory only: help hides and help check names the words it dropped
            self.offered = getattr(self, "offered", {})
            self.offered[mid] = {(w.get("word") or "").lower() for w in words}
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
                    out.append(self._refresh_offer(mid, eid, word, w))
                    continue
                kind = w.get("kind", "do")
                if kind not in ("do", "see", "hear", "hold"):
                    out.append(f"refused: {word} is a {kind} word; words are do, see, hear or hold")
                    continue
                may = w.get("may") or "anyone"
                if not all(t.strip() in MAY_WORDS for t in may.split(" or ")):
                    may = "anyone"
                try:
                    shape = self._offered_shape(w)
                except Refused as exc:
                    out.append(f"refused: {word}: {exc}")
                    continue
                tx = Tx(self)
                tx.part("offer", None, f"offer {word}")
                e = tx.mint()
                tx.set(e, "kind", "word")
                tx.set(e, "word", word)
                tx.set(e, "word_kind", kind)
                tx.set(e, "takes", w.get("takes") or "")
                tx.set(e, "help", w["help"].strip())
                tx.set(e, "may", may)
                tx.set(e, "undo", w.get("undo") if w.get("undo") in ("yes", "no", "external") else
                       ("yes" if kind == "do" else "no"))
                tx.set(e, "from", f"module:{self.state.get(mid, 'name')}")
                tx.set(e, "bound", word)            # what the module answers to, whatever the entry is called later
                tx.set(e, "lives", self.place)
                for a, v in shape.items():
                    if v:
                        tx.set(e, a, v)             # the shape its code reads (kinds.py)
                rec = self._commit(tx, by=mid, words=f"offer {word}", via="offer")
                out.append(f"published {word} as {e} [r{rec['seq']}]")
        return out

    def _offered_shape(self, w):
        """acts_on and needs a module offers with a word (kinds.py), tidied; refuses what the kernel can't read."""
        from .kinds import KIND_NAME
        acts_on = str(w.get("acts_on") or "").strip().casefold()
        if acts_on and not KIND_NAME.match(acts_on):
            raise Refused(f"acts_on={acts_on} is not a kind name")
        return {"acts_on": acts_on, "needs": self.kinds.check_shape_text(w.get("needs"))}

    def _refresh_offer(self, mid, eid, word, w):
        """A module offers a word it already has. A field the module itself wrote last follows the new offer; a field
        a steward changed (word-set, or an undo of one) stays the world's, with a notice when they now differ."""
        new = {"help": (w.get("help") or "").strip(), "takes": w.get("takes") or ""}
        try:
            new.update(self._offered_shape(w))
        except Refused:
            pass                                    # an unreadable shape leaves the one the world has
        if w.get("undo") in ("yes", "no", "external"):
            new["undo"] = w["undo"]
        if w.get("may") and all(t.strip() in MAY_WORDS for t in w["may"].split(" or ")):
            new["may"] = w["may"]
        changed, kept = {}, []
        for a, v in new.items():
            if (self.state.get(eid, a) or "") == v:
                continue
            seq = self.state.last_seq(eid, a)
            rec = self.log.records[seq - 1] if seq else {}
            if not seq or (rec.get("by") == mid and rec.get("via") == "offer"):
                changed[a] = v
            else:
                kept.append(a)
        if kept:
            self.notices.append(f"{self.name(mid)} now offers {word} with different {', '.join(kept)}, but a steward "
                                f"edited its entry {eid}; the steward's edit stays (word-set {word} … to take the new)")
        if not changed:
            return f"bound {word} to {eid}"
        tx = Tx(self)
        tx.part("offer", eid, f"offer {word}")
        for a, v in changed.items():
            tx.set(eid, a, v)
        rec = self._commit(tx, by=mid, words=f"offer {word}: {', '.join(changed)} refreshed", via="offer")
        return f"bound {word} to {eid}; refreshed {', '.join(changed)} [r{rec['seq']}]"

    def namespace_owner(self, word):
        """The module whose namespace a dotted word is in (window.* is the window module's), or None: a family no module
        publishes (task.*, word.*) is free for the world's own words (P4, Alex 27 Oct: one dotted spelling)."""
        if "." not in word:
            return None
        for m in self.things("module"):
            if self._matches(self.state.get(m, "publishes") or "", word):
                return self.state.get(m, "name")
        return None

    def dropped(self, e):
        """True when a module word's module runs and no longer offers it (known only since the module's last start)."""
        frm = str(self.state.get(e, "from") or "")
        if not frm.startswith("module:"):
            return False
        mid = self.module_named(frm[7:])
        offered = getattr(self, "offered", {}).get(mid)
        return offered is not None and (self.state.get(e, "bound") or self.state.get(e, "word")) not in offered

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
