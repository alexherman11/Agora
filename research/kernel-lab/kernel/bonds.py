"""Bonds: what things share, read from the log and the world as the reader may see them (Alex approved 27 Oct 2026;
research/kinds-lab/fresh-kinds-and-bonds.md).

Nobody types a bond. Each record already says who acted, for whom, which things it touched, what it was answering
(caused_by for a rule, because for an agent's turn) and the card it worked on; each thing's facts point at other things
by id or by name. A bond is a reading over those, with a direction, a weight and a reason:

    origin       what it came from: who made it, what it was made with, what caused it
    consequence  what came from it: what it made, what followed from it, what points back at it as its maker
    company      what it sits with: what it is about, what mentions it, what was changed with it, the same task or lane
    alike        what is like it: the same kind, a kind it fits, the same aspects, the same maker
    control      what can act on it: words for its kinds, the people who may change it, modules whose grants reach it
    audience     who can see it
    shows        where it can appear: places it is in, lenses that draw its kinds, windows showing those lenses
    then         what else happened around the same time

A bond through something many things share counts less (a module that made 300 things says little about any two of
them). Every other thing and every record is checked against what the reader may see, so a bond never shows a hidden
thing, and a sealed act never says whose it was. The index is derived and lives only in memory.

Readings: around <thing>, nearby [<agent>], preview <line>. Word: turn <agent> r<n> [work=<card>].
"""
import math
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta

from .kernel import Refused
from . import lines as L

WHO = {"made_by", "for", "via_actor", "by", "person", "agent", "upload_owner"}
SKIP = {"kind", "forgotten", "lives", "bound", "from", "steps_bound", "do_bound", "on_entry", "rev", "made", "changed",
        "made_at", "changed_at", "id", "groups", "sees", "sees_when", "word_kind", "undo", "may", "takes", "once",
        "order", "colour", "color", "note_colour", "note_style", "priority", "seats", "status", "source",
        "source_status", "short_source", "reviewed_code", "painted", "observed_at", "elapsed_ms", "health"}
TEXTY = {"text", "title", "words", "help", "description", "short", "steps", "do", "shows", "name", "label"}
QUIET = {"word", "grant", "paint-report", "component", "part-style", "view-preference", "web-layout", "topic", "world",
         "kind", "aspect"}
WHOS = {"person", "agent", "module", "widget"}


def a_(kind):
    return f"a{'n' if str(kind)[:1] in 'aeiou' else ''} {kind}"


OUT = {"made_by": "made by {}", "for": "made for {}", "via_actor": "made through {}", "about": "about {}",
       "reply_to": "a reply to {}", "chat": "said in {}", "thread": "in the thread {}", "file_source": "read from {}",
       "visibility_of": "seen as {} is seen", "to": "to {}"}
IN = {"made_by": "made by this", "for": "made for this", "via_actor": "made through this", "about": "about this",
      "reply_to": "a reply to this", "chat": "said in this", "thread": "in this thread", "file_source": "read from this",
      "visibility_of": "seen as this is seen", "to": "to this"}


def label(k, x):
    """A thing as people read it: its title or name, an agent by its own name, a chat line by its words."""
    a = k.state.things.get(x, {})
    if a.get("kind") == "agent":
        return f"{a.get('label') or 'an agent'} (agent for {k.name(a.get('for'))})"
    v = a.get("title") or a.get("name") or a.get("label")
    if v:
        v = " ".join(str(v).split())
        return v[:80] + ("…" if len(v) > 80 else "")
    if a.get("text"):
        text = " ".join(str(a["text"]).split())
        return '"' + text[:40] + ("…" if len(text) > 40 else "") + '"'
    return x
NOT_NAMED = {"topic", "word", "grant", "taskboard-event", "paint-report"}
DIRECTIONS = ("origin", "consequence", "company", "alike", "control", "audience", "shows", "then")
RELATED = {"origin", "consequence", "company", "alike", "then"}
ID_IN_TEXT = re.compile(r"\b([a-z]{2,4}\d+)\b")
# a one-word name counts as a mention only for things that are someone or somewhere or something people name (a person,
# a program, a place); "window" or "open" in a sentence is not a mention of a module or a widget called that
ENTITY = {"person", "agent", "place", "group", "program", "app", "game", "spot", "map", "team", "project"}
SHAPE_SKIP = WHO | {"about", "text", "title", "name", "label", "short", "help"}


def mentionable(n, kind):
    return (" " in n and len(n) >= 5) or (len(n) >= 4 and kind in ENTITY)


def says(n, text):
    return n in text and re.search(r"(?<!\w)" + re.escape(n) + r"(?!\w)", text) is not None


def _epoch(at):
    try:
        return datetime.fromisoformat(str(at).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def _rare(n):
    """How much a bond through something shared by n things counts: 1 for two, less as n grows."""
    return 1.0 / math.log2(1 + max(n, 1))


class Bonds:
    def __init__(self, k):
        self.k = k
        self.recs = [None]                     # seq -> {things, made, who, at, cause, work, sealed}
        self.by_thing = defaultdict(list)      # thing -> [seq]
        self.children = defaultdict(list)      # seq -> [seq caused by it]
        self.by_work = defaultdict(list)       # card -> [seq worked on for it]

    # ------------------------------------------------------------------ the index
    def _index(self):
        records = self.k.log.records
        for rec in records[len(self.recs) - 1:]:
            things, made = [], []
            for p in rec.get("parts", []):
                for t in [p.get("target")] + [f[0] for f in p.get("facts", [])]:
                    if t and t != "world" and t not in things:
                        things.append(t)
                made += [f[0] for f in p.get("facts", []) if f[1] == "kind" and f[2] == "0"]
            cause = rec.get("caused_by") or (rec.get("because") if isinstance(rec.get("because"), int) else None)
            r = {"seq": rec["seq"], "things": things, "made": made, "who": rec.get("by"), "for": rec.get("for"),
                 "at": _epoch(rec.get("at")), "cause": cause, "work": rec.get("work"),
                 "sealed": rec.get("by") == "sealed", "entry": rec.get("entry")}
            self.recs.append(r)
            for t in things:
                self.by_thing[t].append(r["seq"])
            if cause:
                self.children[cause].append(r["seq"])
            if r["work"]:
                self.by_work[r["work"]].append(r["seq"])

    # ------------------------------------------------------------------ around
    def around(self, actor, t, toward=None, limit=3):
        k, reader = self.k, actor.person
        row = k.shown(reader, t)
        if row is None:
            raise k.no_such(t)
        self._index()
        state = k.state.things
        seen = {}

        def visible(x):
            if x not in seen:
                seen[x] = x in state and k.shown(reader, x) is not None
            return seen[x]

        bonds = {}

        def add(o, d, w, why):
            if not o or o == t or not isinstance(o, str) or not visible(o):
                return
            kd = state[o].get("kind")
            if kd in QUIET and not (d == "control" and kd in ("word", "grant")):
                return
            b = bonds.setdefault(o, {}).setdefault(d, [0.0, []])
            b[0] += w
            if why not in b[1]:
                b[1].append(why)

        name = lambda x: label(k, x)
        my_names = {str(row.get(f)).casefold() for f in ("name", "title", "label") if row.get(f)}
        my_names = {n for n in my_names if len(n) >= 3}

        # names of what the reader can see, for name-valued aspects and mentions
        names = defaultdict(list)
        for o, a in list(state.items()):
            if o == t or a.get("kind") in NOT_NAMED | QUIET or a.get("forgotten"):
                continue
            for f in ("name", "title", "label"):
                v = a.get(f)
                if isinstance(v, str) and 3 <= len(v) <= 60:
                    names[v.casefold()].append(o)
        sp = k.kinds.spellings(reader)

        def named(v, aspect):
            cands = [o for o in names.get(str(v).casefold(), []) if visible(o)]
            entry = sp.get(k.kinds.canonical(reader, aspect))
            if entry and entry.get("points_at"):
                cands = [o for o in cands if k.kinds.fits(reader, dict(k.shown(reader, o), id=o), entry["points_at"])]
                return cands, True
            return cands, False

        # 1. what it points at, by id or by name, and the places it is in
        same_value = defaultdict(list)
        for a, v in row.items():
            if a in SKIP or a.startswith(("like:", "vote:", "claim:", "contact:", "member:", "is:")):
                continue
            if a.startswith("in:"):
                add(a[3:], "shows", 1.0, f"it is in {name(a[3:])}")
                continue
            if isinstance(v, str) and L.ID.fullmatch(v) and v in state:
                add(v, "origin" if a in WHO else "company", 3.0, OUT.get(a, "its " + a + " is {}").format(name(v)))
                continue
            if isinstance(v, str) and 3 <= len(v) <= 60 and a not in TEXTY:
                hits, typed = named(v, a)
                if len(hits) == 1:
                    add(hits[0], "company", 2.5 if typed else 1.5, f"its {a} says {v}")
                same_value[(a, v)] = []

        # 2. what points at it, by id or by its name; what shares a value with it; who made what alongside
        maker = row.get("made_by")
        made_alike, kind_alike, shape_alike = [], [], []
        texts = {}
        keys = {x for x in row if x not in SKIP | SHAPE_SKIP and not x.startswith(("in:", "like:", "vote:", "claim:", "contact:",
                                                                     "member:", "is:", "sees."))}
        text = " ".join(str(row.get(f, "")) for f in TEXTY if row.get(f)).casefold()
        for o, a in list(state.items()):
            if o == t or a.get("forgotten") or not a.get("kind"):
                continue
            for x, v in a.items():
                if v == t and x not in ("lives",):
                    add(o, "consequence" if x in WHO else "company", 3.0, IN.get(x, "its " + x + " is this"))
                elif my_names and isinstance(v, str) and x not in TEXTY and v.casefold() in my_names \
                        and x not in SKIP:
                    _, typed = named(v, x)
                    add(o, "company", 2.5 if typed else 1.5, f"its {x} says {v}")
            if a.get("kind") not in QUIET:
                for (x, v) in same_value:
                    if a.get(x) == v:
                        same_value[(x, v)].append(o)
            other_text = " ".join(str(a.get(f, "")) for f in TEXTY if a.get(f)).casefold()
            if a.get("kind") not in QUIET:
                texts[o] = other_text
            if t in ID_IN_TEXT.findall(other_text):
                add(o, "company", 2.0, "mentions it")
            for n in my_names:
                if mentionable(n, row.get("kind")) and says(n, other_text):
                    add(o, "company", 1.5, f"mentions {n}")
            if maker and a.get("made_by") == maker:
                made_alike.append(o)
            if a.get("kind") == row.get("kind"):
                kind_alike.append(o)
            elif a.get("kind") not in QUIET and len(keys) >= 3:
                theirs = {x for x in a if x not in SKIP | SHAPE_SKIP and not x.startswith(("in:", "like:", "vote:", "claim:",
                                                                               "contact:", "member:", "is:", "sees."))}
                both = keys & theirs
                j = len(both) / max(1, len(keys | theirs))
                if j >= 0.6:
                    shape_alike.append((o, j, sorted(both)))
        for (x, v), others in same_value.items():
            vis = [o for o in others if visible(o)]
            if 1 <= len(vis) <= 60:
                for o in vis:
                    add(o, "company", _rare(len(vis) + 1), f"also {x}={v}")
        vis = [o for o in made_alike if visible(o)]
        for o in vis[:200]:
            add(o, "alike", _rare(len(vis) + 1), f"also made by {name(maker)}")
        vis = [o for o in kind_alike if visible(o)]
        for o in vis[:200]:
            add(o, "alike", 0.8 * _rare(len(vis) + 1), f"also {a_(row.get('kind'))}")
        for o, j, both in shape_alike:
            add(o, "alike", 1.5 * j, f"has the same aspects ({', '.join(both[:3])})")

        # 3. what its own text mentions, by id or by name
        for x in ID_IN_TEXT.findall(text):
            if x in state:
                add(x, "company", 2.0, f"it mentions {name(x)}")
        mentioned = set()
        for n, os_ in names.items():
            hits = [o for o in os_ if mentionable(n, state[o].get("kind"))]
            if hits and says(n, text):
                mentioned.add(n)
                for o in hits:
                    add(o, "company", 1.5, f"it mentions {n}")
        for n in mentioned:                            # both mention the same person, program or place
            others = [o for o, txt in texts.items() if o not in names.get(n, []) and says(n, txt) and visible(o)]
            for o in others[:60]:
                add(o, "company", 1.5 * _rare(len(others)), f"both mention {n}")

        # 4. from the log: made or changed in one act, causes and what followed, the card worked on, the same hands
        mine = self.by_thing.get(t, [])
        made_at = None
        for seq in mine:
            r = self.recs[seq]
            if r["sealed"]:
                continue                                # a sealed act says nothing about who, and little about what
            made_here = t in r["made"]
            if made_here:
                made_at = r
            n = len(r["things"])
            if n <= 40:
                for o in r["things"]:
                    if made_here and o in r["made"]:
                        add(o, "origin", 2.0 * _rare(n), f"made in the same act (r{seq})")
                    elif made_here:
                        add(o, "origin", 2.0 * _rare(n), f"made with it (r{seq})")
                    else:
                        add(o, "company", 1.2 * _rare(n), f"changed in the same act (r{seq})")
            who = r["for"] or r["who"]
            if who and who != "kernel":
                if made_here:
                    add(who, "origin", 0.5, "made it")
                else:
                    add(who, "company", 0.4, "changed it")
            c = r["cause"]
            if c and c < len(self.recs) and not self.recs[c]["sealed"]:
                for o in self.recs[c]["things"]:          # what caused its making, or a change to it
                    add(o, "origin" if made_here else "company", 2.5,
                        f"{'made' if made_here else 'changed'} because of it (r{c} → r{seq})")
            for ch in self.children.get(seq, []):
                for o in self.recs[ch]["things"]:
                    add(o, "consequence", 2.5, f"followed from it (r{seq} → r{ch})")
            if r["work"]:
                add(r["work"], "origin" if made_here else "company", 2.5, "worked on for this card")
        for seq in self.by_work.get(t, []):
            for o in self.recs[seq]["things"]:
                add(o, "consequence", 2.0, f"worked on for it (r{seq})")
        if made_at:
            who = made_at["for"] or made_at["who"]
            window = [r for r in self.recs[max(1, made_at["seq"] - 60):made_at["seq"] + 60]
                      if r is not None and r["seq"] != made_at["seq"] and not r["sealed"]]
            burst = [o for r in window if (r["for"] or r["who"]) == who and abs(r["at"] - made_at["at"]) <= 180
                     for o in r["made"]]
            for o in burst:                             # one person's burst: the bigger the burst, the less it says
                add(o, "company", _rare(len(burst) + 1), f"made by {name(who)} within 3 minutes")
            for r in window:
                if abs(r["at"] - made_at["at"]) <= 600:
                    for o in [x for x in r["things"] if state.get(x, {}).get("kind") not in WHOS | {"place", "group"}][:5]:
                        add(o, "then", 0.3, "happened within 10 minutes of its making")

        # 5. control: words for its kinds, the people who may change it, modules whose grants reach it
        kinds = [kd for kd, _ in k.kinds.kinds_of(reader, dict(row, id=t))]
        for e in k.entries():
            ea = state[e]
            w = str(ea.get("word") or "")
            ns = w.rsplit(".", 1)[0] if "." in w else None
            usage = (str(ea.get("help") or "").splitlines() or [""])[0]
            for kd in kinds:
                if ns == kd or (ns and ns in kd.split("-")) or f"<{kd}>" in usage or f"<{kd}>" in str(ea.get("takes")):
                    add(e, "control", 1.5, f"{w} acts on a {kd}")
                    break
        owner = state.get(maker, {}).get("for") if state.get(maker, {}).get("kind") == "agent" else maker
        if owner and state.get(owner, {}).get("kind") == "person":
            add(owner, "control", 1.5, "made it, so may change it")
        for g in k.groups_of(t):
            for x in state.get(g, {}):
                if x.startswith("member:") and state[g][x] == "leader":
                    add(x[7:], "control", 1.0, f"leads {name(g)}")
        for g in k.things("grant"):
            ga = state[g]
            only = str(ga.get("only") or "")
            if not ga.get("revoked") and any(f"kind:{kd}" in only.split(";")[0] or f"thing:{t}" in only
                                             for kd in kinds):
                add(ga.get("to"), "control", 1.5, f"its grant reaches {kinds[0]}s")
        for r in k.things("rule"):
            ra = state[r]
            if ra.get("of_kind") in kinds and not ra.get("off"):
                add(r, "control", 1.0, f"a rule hears {ra.get('of_kind')}s")

        # 6. audience: the people who can see it
        people = [p for p in k.things("person") if visible(p) and k.shown(p, t) is not None]
        for p in people:
            add(p, "audience", 1.0 if len(people) <= 12 else 0.2, "can see it")

        # 7. shows: lenses and readings that draw its kinds, and the windows showing those lenses
        lenses = []
        for o, a in list(state.items()):
            if a.get("forgotten") or a.get("kind") in ("word", "topic"):
                continue
            src = " ".join(str(a.get(f, "")) for f in ("text", "shows", "model_kind", "of_kind"))
            for kd in kinds:
                if re.search(r"(tag:|rows |rows\s+\"?|model_kind\b)" + re.escape(kd) + r"\b", src) \
                        or a.get("model_kind") == kd:
                    add(o, "shows", 2.0, f"draws {kd}s")
                    if a.get("kind") == "lens":
                        lenses.append(o)
                    break
        for o, a in list(state.items()):
            if a.get("kind") == "window" and (a.get("lens") in lenses or any(
                    a.get("lens") == state[x].get("name") for x in lenses)):
                add(o, "shows", 1.5, f"shows {name(a.get('lens')) if a.get('lens') in state else a.get('lens')}")

        # rank
        out = []
        for o, ds in bonds.items():
            # how bound up two things are: who can act on it, see it or show it are listed, but they don't add up
            total = sum(w for d, (w, _) in ds.items() if d in RELATED)
            for d, (w, why) in ds.items():
                out.append({"id": o, "name": name(o), "kind": state[o].get("kind"), "toward": d,
                            "strength": round(w, 2), "total": round(total, 2), "why": "; ".join(why[:3])})
        if toward == "strongest":
            best = {}
            for r in sorted(out, key=lambda r: -r["strength"]):
                best.setdefault(r["id"], r)
            rows = sorted([r for r in best.values() if r["total"] > 0], key=lambda r: -r["total"])[:limit]
        else:
            rows = []
            for d in ([toward] if toward else DIRECTIONS):
                rows += sorted([r for r in out if r["toward"] == d], key=lambda r: -r["strength"])[:limit]
        return row, rows

    # ------------------------------------------------------------------ nearby
    def working_set(self, actor_id, since, person=None):
        """What an actor touched (its acts) and read (its seen marks) since a time, as {thing: how}."""
        k = self.k
        self._index()
        ws = {}
        for r in reversed(self.recs[1:]):
            if r["at"] < since:
                break
            if r["sealed"]:
                continue
            if r["who"] == actor_id or (person and r["who"] == person):
                for t in r["things"]:
                    ws.setdefault(t, "changed")
        first = next((r["seq"] for r in self.recs[1:] if r["at"] >= since), len(self.recs))
        for t, marks in (k.seen.get(actor_id) or {}).items():
            if max(marks.values() or [0]) >= first - 1 or marks.get("*", 0) >= first - 1:
                ws.setdefault(t, "read")
        turn = k.turns.get(actor_id) or {}
        if isinstance(turn.get("because"), int) and turn["because"] < len(self.recs):
            for t in self.recs[turn["because"]]["things"]:
                ws.setdefault(t, "read")
        if turn.get("work"):
            ws.setdefault(turn["work"], "read")
        return ws

    def related(self, t):
        """Things one cheap step from t: what it points at by id, what points at it, what shared an act with it."""
        k, out = self.k, set()
        a = k.state.things.get(t, {})
        out.update(v for x, v in a.items() if isinstance(v, str) and v in k.state.things and x not in WHO)
        out.update(o for o, oa in list(k.state.things.items()) if not oa.get("forgotten")
                   and any(v == t for x, v in oa.items() if x not in WHO and x != "lives"))
        for seq in self.by_thing.get(t, [])[-20:]:
            r = self.recs[seq]
            if len(r["things"]) <= 12 and not r["sealed"]:
                out.update(r["things"])
        out.discard(t)
        return out

    def nearby(self, actor, who=None, minutes=30):
        k = self.k
        subject = who or actor.id
        person = k.state.get(subject, "for") if k.state.get(subject, "kind") == "agent" else subject
        since = k.now().timestamp() - minutes * 60
        mine = self.working_set(subject, since, person if k.state.get(subject, "kind") == "person" else None)
        if not mine:
            return []
        reader = actor.person
        visible = lambda x: x in k.state.things and k.shown(reader, x) is not None
        near = {}
        for x in list(mine):
            for y in self.related(x):
                near.setdefault(y, x)
        others = defaultdict(dict)
        for r in reversed(self.recs[1:]):
            if r["at"] < since:
                break
            who_ = r["who"]
            if r["sealed"] or who_ in (subject, "kernel") or (person and who_ == person and subject == person):
                continue
            for t in r["things"]:
                others[who_].setdefault(t, r)
        out = []
        for who_, touched in others.items():
            if not visible(who_):
                continue
            for t, r in touched.items():
                if not visible(t) or k.state.get(t, "kind") in QUIET:
                    continue
                how = None
                if mine.get(t) == "changed":
                    how = "is changing it too"
                elif mine.get(t) == "read":
                    how = "is changing what you read"
                elif t in near and visible(near[t]):
                    how = f"is working on it, bound up with {k.state.get(near[t], 'title') or k.name(near[t])}"
                if how:
                    ago = int((k.now().timestamp() - r["at"]) // 60)
                    out.append({"who": label(k, who_), "who_id": who_, "id": t,
                                "name": k.state.get(t, "title") or k.name(t), "how": how, "record": f"r{r['seq']}",
                                "minutes_ago": ago})
        order = {"is changing it too": 0, "is changing what you read": 1}
        return sorted(out, key=lambda r: (order.get(r["how"], 2), r["minutes_ago"]))

    # ------------------------------------------------------------------ impact (preview)
    def names_left(self, t, old, reader):
        """Things that still name `t` by an old name: [(thing, aspect)], and lenses whose text filters by it."""
        k = self.k
        if not isinstance(old, str) or len(old) < 2:
            return [], []
        kind = k.state.get(t, "kind")              # another lane still called Now keeps the name meaning a lane
        still = [o for o, a in k.state.things.items() if o != t and not a.get("forgotten") and a.get("kind") == kind
                 and old in (a.get("name"), a.get("title"), a.get("label"))]
        if still:
            return [], []                       # something else is still called that, so the name still means a thing
        said, lenses = [], []
        for o, a in list(k.state.things.items()):
            if o == t or a.get("forgotten") or k.shown(reader, o) is None:
                continue
            if a.get("kind") == "lens" and re.search(r"=" + re.escape(old) + r"\b", str(a.get("text", ""))):
                lenses.append(o)
                continue
            for x, v in a.items():
                if v == old and x not in TEXTY and x not in SKIP:
                    said.append((o, x))
        return said, lenses

    def impact(self, actor, tx, st, entry):
        """What an act's facts would change, and what else that reaches. Nothing is written."""
        from .store import GONE
        k, reader = self.k, actor.person
        state = k.state.things
        lines, rows = [], []
        name = lambda x: label(k, x)
        changed = defaultdict(dict)
        for p in tx.parts:
            for f in p["facts"]:
                changed[f[0]][f[1]] = f[3] if len(f) > 3 else None
        if not changed:
            return {"text": f"preview: {st.word} would change nothing", "rows": []}
        for t, facts in changed.items():
            if t in tx.made:
                kd = facts.get("kind")
                lines.append(f"makes a new {kd}" + (f" called {facts.get('title') or facts.get('name')}"
                                                    if facts.get("title") or facts.get("name") else ""))
                rows.append({"what": "makes", "kind": kd})
                continue
            before = dict(state.get(t, {}))
            after = dict(before)
            for a, v in facts.items():
                if v is None:
                    after.pop(a, None)
                else:
                    after[a] = v
            show = lambda v: "(none)" if v is None else (name(v) if isinstance(v, str) and v in state else str(v)[:30])
            said = ", ".join(f"{a} {show(before.get(a))} → {show(v) if v is not None else '(gone)'}"
                             for a, v in list(facts.items())[:6])
            lines.append(f"{name(t)} ({t}): {said}")
            rows.append({"what": "facts", "id": t, "facts": facts})
            # names other things use for it
            for a in ("name", "title", "label"):
                if a in facts and before.get(a) and before.get(a) != facts[a]:
                    users, lenses = self.names_left(t, before[a], reader)
                    if users:
                        by = defaultdict(list)
                        for o, x in users:
                            by[(state[o].get("kind"), x)].append(o)
                        for (kd, x), os_ in by.items():
                            lines.append(f"  {len(os_)} {kd}{'s' if len(os_) != 1 else ''} say {x}={before[a]}; "
                                         f"they would name something that is gone")
                            rows.append({"what": "names", "kind": kd, "aspect": x, "count": len(os_), "ids": os_})
                    for ln in lenses:
                        lines.append(f"  the lens {name(ln)} filters by ={before[a]}; it would stop finding them")
                        rows.append({"what": "lens-filter", "id": ln})
            # views that read what changes
            kinds_before = [kd for kd, _ in k.kinds.kinds_of(reader, dict(k.kinds.fill(reader, dict(before)), id=t))]
            kinds_after = [kd for kd, _ in k.kinds.kinds_of(reader, dict(k.kinds.fill(reader, dict(after)), id=t))]
            for o, a in list(state.items()):
                if a.get("kind") != "lens" or a.get("forgotten") or k.shown(reader, o) is None:
                    continue
                text = str(a.get("text", ""))
                if any(re.search(r"tag:" + re.escape(kd) + r"\b", text) for kd in kinds_before + kinds_after):
                    reads = [x for x in facts if re.search(r"(prop:|\$\w+\.)" + re.escape(x) + r"\b", text)]
                    if reads:
                        lines.append(f"  the lens {name(o)} reads {', '.join(reads)}; it will show the change")
                        rows.append({"what": "reader", "id": o, "aspects": reads})
            for kd in [x for x in kinds_before if x not in kinds_after]:
                lines.append(f"  it would stop being a {kd} (rows {kd} and views of {kd}s would drop it)")
                rows.append({"what": "leaves", "kind": kd})
            for kd in [x for x in kinds_after if x not in kinds_before]:
                lines.append(f"  it would become a {kd} too (rows {kd} would list it)")
                rows.append({"what": "joins", "kind": kd})
            if "forgotten" in facts and facts["forgotten"]:
                pointing = [o for o, a in state.items() if o != t and not a.get("forgotten")
                            and any(v == t for x, v in a.items() if x not in ("lives",)) and k.shown(reader, o)]
                if pointing:
                    lines.append(f"  {len(pointing)} thing{'s' if len(pointing) != 1 else ''} point at it; they "
                                 f"would point at something out of view")
                    rows.append({"what": "pointing", "ids": pointing})
            if "sees" in facts or "forgotten" in facts:
                n = sum(1 for p in k.things("person") if k.shown(p, t) is not None)
                lines.append(f"  {n} {'person sees' if n == 1 else 'people see'} it now")
                rows.append({"what": "audience", "now": n})
        # who hears it
        for r in k.things("rule"):
            ra = state[r]
            if ra.get("on_entry") == entry["id"] and not ra.get("forgotten") and k.shown(reader, r) is not None:
                kinds = {state.get(t, {}).get("kind") for t in changed}
                if not ra.get("of_kind") or ra["of_kind"] in kinds:
                    lines.append(f"  the rule {ra.get('name') or r} would run after it")
                    rows.append({"what": "rule", "id": r})
        hearing = [m for m in k.things("module") if k.state.get(m, "on") and k.shown(reader, m) is not None and any(
            k._matches(" ".join(w[5:] for w in str(state[g].get("words") or "").split() if w.startswith("hear:")),
                       entry["word"]) for g in k._grants_to(m))]
        if hearing:
            lines.append(f"  {len(hearing)} module{'s' if len(hearing) != 1 else ''} hear {entry['word']}: "
                         + ", ".join(str(state[m].get("name")) for m in hearing))
            rows += [{"what": "hears", "id": m} for m in hearing]
        try:
            k.kinds.check_promises(tx)
        except Refused as exc:
            lines.append(f"  it would be refused: {exc}")
            rows.append({"what": "refused", "why": str(exc)})
        if len(lines) == len(changed):
            lines.append("  nothing else reads or names what this changes")
        return {"text": f"preview of {st.text.strip()} (nothing was done):\n  " + "\n  ".join(lines), "rows": rows}


# ---------------------------------------------------------------------- the words
def _thing(k, actor, st):
    first = (st.target or (st.words.split() or [""])[0])
    if L.ID.fullmatch(first or ""):
        return first, (st.words if st.target else st.words[len(first):]).strip()
    hits = k.named(actor, st.words)
    if len(hits) == 1:
        return hits[0][0], ""
    if hits:
        raise Refused(f"{len(hits)} things are called {st.words}: " + ", ".join(f"{t} (a {kd})" for t, kd in hits[:4]))
    raise Refused(f"nothing you can see is called {st.words or '(nothing)'}; around <thing>")


def around(k, actor, st, entry, tx, group, saw=None):
    t, _ = _thing(k, actor, st)
    toward = st.kv.get("toward")
    if toward and toward not in DIRECTIONS + ("strongest",):
        raise Refused(f"toward= says {', '.join(DIRECTIONS)} or strongest")
    limit = int(st.kv.get("limit", "3")) if str(st.kv.get("limit", "3")).isdecimal() else 3
    row, rows = k.bonds.around(actor, t, toward, min(limit, 30))
    head = f"around {label(k, t)} ({t}), {a_(row.get('kind'))}"
    if not rows:
        return {"text": head + ": nothing you can see is bound up with it yet", "rows": []}
    lines = [head + ":"]
    for r in rows:
        lines.append(f"  {r['toward']} · {r['name']} ({r['id']}, {a_(r['kind'])}) · {r['why']}")
    return {"text": "\n".join(lines), "rows": rows}


def nearby(k, actor, st, entry, tx, group, saw=None):
    who = st.target
    if who and k.shown(actor.person, who) is None:
        raise k.no_such(who)
    rows = k.bonds.nearby(actor, who)
    whose = "you" if not who else label(k, who)
    if not rows:
        return {"text": f"no one else is working near what {whose} touched or read in the last half hour", "rows": []}
    lines = [f"working near what {whose} touched or read:"]
    for r in rows[:12]:
        lines.append(f"  {r['who']} {r['how']}: {r['name']} ({r['id']}), {r['minutes_ago']} min ago ({r['record']})")
    return {"text": "\n".join(lines), "rows": rows}


def preview(k, actor, st, entry, tx, group, saw=None):
    line = st.text.strip().split(None, 1)[1] if len(st.text.strip().split(None, 1)) > 1 else ""
    if not line.strip():
        raise Refused("preview <line>: what an act would change, without doing it (preview set dk80 name=Doing)")
    if len(L.split_batch(line)) > 1:
        raise Refused("preview takes one step at a time")
    return k.step(actor, line, mode="preview")


def turn(k, actor, st, entry, tx, group, saw=None):
    a = st.target
    kind = k.state.get(a, "kind")
    if kind not in ("agent", "person"):
        raise Refused("turn <agent> r<n> [work=<card>]: an agent (or a person an agent signs in as), and the line "
                      "its acts now answer")
    mine = (k.state.get(a, "for") if kind == "agent" else a) == actor.person
    if actor.kind != "module" and not k.is_steward(actor.person) and not mine:
        raise Refused(f"{label(k, a)} is not yours; a house, a steward or its person says what it is working on")
    words = st.words.split()
    if words and words[0] in ("done", "end", "off"):
        was = k.turns.pop(a, None)
        return {"text": f"{label(k, a)}'s turn is over" if was else f"{k.name(a)} had no turn"}
    because = None
    if words:
        w0 = words[0]
        if L.RECORD.fullmatch(w0) and 0 < int(w0[1:]) <= len(k.log.records):
            because = int(w0[1:])
        elif L.ID.fullmatch(w0) and k.shown(actor.person, w0) is not None:
            seqs = k.state.history.get((w0, "kind"))
            because = seqs[0][0] if seqs else None      # a thing: the act that made it (the line that woke the agent)
        else:
            raise Refused(f"turn <agent> r<n>: {w0} is not a record or a thing you can see")
    work = st.kv.get("work")
    if work and k.shown(actor.person, work) is None:
        raise k.no_such(work)
    k.turns[a] = {"because": because, "work": work, "since": time.time()}
    said = (f"answering r{because}" if because else "") + (f"{', ' if because else ''}on {k.state.get(work, 'title') or k.name(work)}"
                                                           if work else "")
    return {"text": f"{label(k, a)} is working now{': ' + said if said else ''}; its acts will say so in the log. "
                    f"turn {a} done ends it"}
