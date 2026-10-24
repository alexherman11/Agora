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
import time  # noqa: F401  (holds keep their start time)
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
        self.changed = threading.Condition()
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
        self.happenings = []                           # delivered, not recorded (SHAPE section 5); in memory
        self.leases, self.leases_made = {}, []         # holds: momentary, in memory (SHAPE section 5)
        self.dev_sessions = None                       # start_kernel.py --dev-entry: a callable -> {token: session}
        self.clock = None                              # a callable -> aware datetime, for a run with its own time
        if not self.log.records:
            if genesis is None:
                raise ValueError("an empty world needs a genesis")
            self._genesis(genesis)
        self.tag = self.state.get("world", "tag")
        self.place = self.state.get("world", "place")

    def now(self):
        """The kernel's time (UTC). A run may give it a clock of its own; records are stamped with it."""
        from datetime import datetime, timezone
        return self.clock() if self.clock else datetime.now(timezone.utc)

    def once(self, actor, entry, target):
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
            if r.get("entry") != entry["id"] or r["seq"] in undone or r.get("undoes"):
                return False
            if r.get("by") == "sealed":
                t = r["parts"][0].get("target") if r.get("parts") else None
                return r.get("seal") == self.seal(actor.person, entry["id"], t)
            return actor.person in (r.get("by"), r.get("for"))

        def target_of(r):
            return r["parts"][0].get("target") if r.get("parts") else None
        acts = [r for r in self.log.records if mine(r)]
        for clause in [c.strip() for c in rule.split(";") if c.strip()]:
            if clause == "per person per target":
                if target and any(target_of(r) == target for r in acts):
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
        if group == self.place or self.state.get(group, "open"):
            return True                                     # every person who joined is a member of the place, and of
            #                                                 an open group in it (a public channel); its leaders are
            #                                                 still appointed
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
        a = self.state.things.get(t)
        if a is None or t == "world" or a.get("forgotten"):
            return None                 # a forgotten thing is out of every view; undo of the forget brings it back
        if not self._sees(reader, a.get("sees", "place"), t):
            return None
        out = {}
        likes, votes, claims, contacts = 0, {}, [], []
        for k, v in a.items():
            if k.startswith("like:"):
                likes += 1
                continue
            if k.startswith("vote:"):                    # sealed: only the count of each option is shown
                votes[v] = votes.get(v, 0) + 1
                continue
            if k.startswith("sees.") or k == "sees":     # a rule about who sees, not something to see
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
        if a.get("kind") == "poll":
            for o in str(a.get("options") or "").split():
                out[f"votes_{o}"] = votes.get(o, 0)
            out["votes"] = sum(votes.values())
        if claims:
            out["claimed_by"] = ", ".join(self.name(p) for p in claims)       # in the order they were claimed
            out["claims"] = len(claims)
        if str(a.get("seats", "")).isdigit():
            out["seats_left"] = max(0, int(a["seats"]) - len(claims))
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
            s = saw[t]
            if isinstance(s, dict):
                # a painted gesture: stale only if what it read, or what it writes, changed since it was painted
                rev = int(s.get("rev", 0))
                for a in set(aspects) | set(s.get("aspects") or []):
                    names = [x for x in self.state.things.get(t, {}) if x.startswith(a[:-1])] if a.endswith("*") \
                        else [a]
                    last = max([self.state.last_seq(t, x) for x in names] + [0])
                    if last > rev:
                        raise Refused(f"stale: {t} changed since it was painted ({a.rstrip(':*')}, r{last}); "
                                      f"nothing was done. The view will repaint.")
                return
            if self.state.rev.get(t, 0) > int(s):
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
        rec = {"at": self.now().strftime("%Y-%m-%dT%H:%M:%SZ"), "by": by, "words": words,
               "parts": tx.parts}
        rec.update({k: v for k, v in extra.items() if v is not None})
        rec = self.log.append(rec)
        for p in rec["parts"]:
            self.state.apply(p["facts"], rec["seq"])
        for p in rec["parts"]:
            if rec.get("entry") or rec.get("via") in ("offer", "sign-in"):
                self._happen({"word": p["word"], "target": p.get("target"), "by": rec["by"], "for": rec.get("for"),
                              "text": p.get("words", ""), "record": rec["seq"]})
        with self.changed:
            self.changed.notify_all()                    # pages' streams wake on every record
        return rec

    # ------------------------------------------------------------------ hear (SHAPE section 5)
    def _happen(self, h):
        h["n"] = len(self.happenings) + 1
        self.happenings.append(h)
        del self.happenings[:-2000]                      # momentary: the last 2000 are kept for streams catching up
        if self.modules:
            self.modules.deliver(h)
        with self.changed:
            self.changed.notify_all()

    def announce(self, mid, word, target=None, text=""):
        """A module says something happened outside the world (`window.opened`). Delivered, not recorded."""
        with self.lock:
            if not self.state.get(mid, "on") or not self._grant_names(mid, word):
                return f"refused: {self.name(mid)} holds no grant to say {word}"
            if target is not None and target not in self.state.things:
                target = None
            self._happen({"word": word, "target": target, "by": mid, "text": str(text)[:500], "announced": True})
        return "ok"

    def _grant_names(self, who, word):
        return [g for g in self._grants_to(who) if self._matches(self.state.get(g, "words"), word)]

    def may_hear(self, person, h):
        """Who-sees for a happening: its thing must be one the reader may see."""
        return h.get("target") is None or self.shown(person, h["target"]) is not None

    def happening_for(self, person, h):
        by = "someone" if h.get("by") == "sealed" else self.name(h.get("for") or h.get("by")) if h.get("by") else None
        return {"n": h["n"], "word": h["word"], "target": h.get("target"), "by": by, "text": h.get("text", ""),
                "record": h.get("record"), "announced": bool(h.get("announced"))}

    def module_hears(self, mid, h):
        """A module hears a word its grants name as `hear:<word or pattern>`, about a thing everyone in the place may
        see (a module has no person of its own to see more as)."""
        if h.get("by") == mid or not self.state.get(mid, "on"):
            return False
        if not any(self._matches(" ".join(w[5:] for w in (self.state.get(g, "words") or "").split()
                                          if w.startswith("hear:")), h["word"]) for g in self._grants_to(mid)):
            return False
        t = h.get("target")
        return t is None or (self.state.things.get(t) is not None and
                             str(self.state.get(t, "sees", "place")) in ("place", "public"))

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
        handles = {}
        for i, s in enumerate(steps):
            s = self.fill_handles(s, handles)
            try:
                r = self.step(actor, s, press=press if len(steps) == 1 else None, saw=saw, mode=mode)
                self.keep_handle(s, r.get("made"), handles)
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

    @staticmethod
    def fill_handles(text, handles):
        """`$name` -> the thing a step earlier in the same line or answer made with `as=name` (the desk's form)."""
        if not handles or "$" not in text:
            return text
        return L.re.sub(r"\$([a-z][a-z0-9_]*)\b", lambda m: handles.get(m.group(1), m.group(0)), text)

    @staticmethod
    def keep_handle(text, made, handles):
        name = L.parse(text).kv.get("as")
        if name and made:
            handles[name] = made[-1]

    def step(self, actor, text, press=None, saw=None, mode="do"):
        from .words import KERNEL
        st = L.parse(text)
        if st.word == "do" and text.strip()[2:].strip():
            text = text.strip()[2:].strip()            # the desk's `do <word> …`, which every lens gesture says
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
            if entry.get("word_kind") == "do":
                said = self.once(actor, entry, st.target)
                if said:
                    raise Refused(said)
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
                res = fn(self, actor, st, entry, tx, group, saw=saw)
                if tx.empty:
                    return res
                rec = self._commit_use(tx, actor, text, entry, press, saw, st)
                res["record"] = rec["seq"]
                res["made"] = tx.made
                res["text"] = res["text"].replace("[r?]", f"[r{rec['seq']}]")
                return res
        if src == "module":
            return self.module_word(actor, st, entry, group, text, press, saw)  # no lock held while the module works
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
    def module_word(self, actor, st, entry, group, text, press, saw=None):
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
        if entry.get("word_kind") == "do" and ans.get("external"):
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
        return self.admit(mid, actor, text, entry, ans, press, saw)

    def admit(self, mid, caller, text, entry, ans, press=None, press_saw=None):
        """A module's answer: its lines run as one use, one record, as the caller narrowed to the module, and only if
        what it read is unchanged (SHAPE section 11). Refused whole otherwise. A painted press says what its page
        showed (`press_saw`): an answer that writes a thing the page showed is fenced on that too, so two leaders
        pressing Next on one painted agenda move it once, though the module read it fresh both times."""
        from .words import KERNEL
        author = Actor(mid, caller.person, "module", module=mid, caller=caller)
        saw = {k: int(v) for k, v in (ans.get("saw") or {}).items()}
        with self.lock:
            tx = Tx(self)
            notes = []
            handles = {}
            for line in ans["lines"]:
                line = self.fill_handles(str(line), handles)
                st = L.parse(line)
                if st.word == "do":
                    line = line.strip()[2:].strip()
                    st = L.parse(line)
                made_before = len(tx.made)
                eid = self.find_entry(st.word)
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
                said = self.once(author, e, st.target)
                if said:
                    raise Refused(f"{said}; nothing was done")
                if press_saw and st.target in press_saw:
                    self.fence(caller, st.target, [x for x in st.kv if x not in ("in", "as")], press_saw)
                tx.part(st.word, st.target, line)
                res = KERNEL[self.source(e)[1]](self, author, st, e, tx, group, saw=saw)
                notes.append(res["text"])
                self.keep_handle(line, tx.made[made_before:], handles)
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
                if kind not in ("do", "see", "hear", "hold"):
                    out.append(f"refused: {word} is a {kind} word; words are do, see, hear or hold")
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
                tx.set(e, "undo", w.get("undo") if w.get("undo") in ("yes", "no", "external") else
                       ("yes" if kind == "do" else "no"))
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
