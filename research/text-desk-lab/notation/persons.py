"""Persons, phase 1 (a1568, design a1016): a person is a thing with one id for a life, and names are labels on it.

A person is a subject of kind person with its own id kind (p1895), placed on no surface, so it has one id and never a
second one for an appearance (a760). Its name is a prop (name=pike), a label and never the identity, and its title is
that name as people read it. The names a person has borne are kept in the person (subject["person"]["names"], a list of
[name, from event number]), so a rename's undo, which restores the whole subject, takes the name back too.

Every event names its person in who= (by= keeps the name it was signed with, never rewritten). Printing shows the
person's name, with a mark only where two persons have borne it: 'pike, first' is the earlier of two Pikes. Today's
bearer is never marked.

Forgiving to people, strict to stored text (a990): a typed name means today's bearer and names the door to an earlier
one (pike,first); a person id always means that person.

Phase 2 (a1590): stored names become persons when saved. A prop that names a person (PERSON_KEYS: owner=, asked_by=,
person=) holds the person's id, and prints as their name (`shown`), so people type and read names as before and the
store holds who they meant. A stored line's names (a view's query, a rule, a lens, a wake, a verb's lines) are bound to
persons when the line is saved, in the binding a1156 keeps with it (its `persons`), and a selection read for that line
means those persons; $me is never bound. `migrate` binds everything saved before this, once, each name to the person
who bore it when it was written, found by its event's time. Chat signatures are a1581's; promises' to= are a1576's.

Nothing here runs until `person begin` has made the persons of a world (once, by one undoable event). Before that,
and in every world that never runs it, every function here answers as the names did: who= is absent, a label is by=.
"""

import re
import weakref

NOT_PERSONS = {"house", ""}          # the house acts as itself: its events carry no person
ORDINALS = ("first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth")
PID = re.compile(r"p\d+$")
KINDS = ("resident", "human", "agent", "worker")

_cache = weakref.WeakKeyDictionary()


def _num(eid):
    try:
        return int(str(eid)[1:])
    except ValueError:
        return 0


def norm(name):
    return str(name or "").split("/")[0].strip().lower()


class Index:
    """Who bears which name, read from the person subjects. Rebuilt when the world has a new event or subject."""

    def __init__(self, w):
        self.people = {}        # pid -> [(name, from event number)], oldest first
        self.spans = {}         # name -> [(from event number, pid)], oldest first
        for s in w.subjects.values():
            if s.get("kind") != "person":
                continue
            names = [(str(n), int(k)) for n, k in (s.get("person") or {}).get("names") or []]
            if not names:
                names = [(norm((s.get("props") or {}).get("name") or s["title"]), 0)]
            self.people[s["id"]] = names
            for n, k in names:
                self.spans.setdefault(n, []).append((k, s["id"]))
        for v in self.spans.values():
            v.sort()

    def bearers(self, name):
        """The persons who have borne `name`, in the order they began to bear it, each once."""
        out = []
        for _, pid in self.spans.get(norm(name), []):
            if pid not in out:
                out.append(pid)
        return out


def index(w):
    key = (getattr(w, "_eseq", 0), len(w.events), len(w.subjects))
    hit = _cache.get(w)
    if hit is None or hit[0] != key:
        hit = (key, Index(w))
        _cache[w] = hit
    return hit[1]


def on(w):
    """Have the persons of this world been made (person begin)?"""
    return bool(index(w).people)


def is_person(w, ident):
    s = w.subjects.get(ident)
    return bool(s) and s.get("kind") == "person"


def name_now(w, pid):
    return norm((w.subjects[pid].get("props") or {}).get("name")) if pid in w.subjects else ""


def at(w, name, k):
    """The person who bore `name` at event number k: of those who had begun to bear it by then, the latest. A name a
    person has since left still reaches them, unless someone else took it up after (so an act signed with an old name
    is never handed to an earlier bearer)."""
    best = None
    for start, pid in index(w).spans.get(norm(name), []):
        if start <= k:
            best = pid
    return best


def today(w, name):
    """Today's bearer of a name: the last person to take it up, even one who has since been renamed, until someone
    else takes it up. A name never falls back to an earlier bearer: after Pike is renamed kestrel, 'pike' (typed, or
    stored in a corner's actor=) still means Kestrel, never the first Pike."""
    b = index(w).bearers(name)
    return b[-1] if b else None


def corner(w, pid):
    """The corner whose actor= names this person today, or None."""
    for fid, n in w.nodes.items():
        p = n.get("props") or {}
        if n["type"] == "surface" and p.get("role") == "resident" and p.get("actor") and today(w, p["actor"]) == pid:
            return fid
    return None


def label(w, pid):
    """How a person is printed: their name now, and a mark only when someone else has borne that name too, for any
    but its latest bearer ('pike, first')."""
    if pid not in w.subjects:
        return pid
    n = name_now(w, pid)
    b = index(w).bearers(n)
    if len(b) > 1 and pid in b and pid != b[-1]:
        return f"{n}, {ORDINALS[b.index(pid)] if b.index(pid) < len(ORDINALS) else str(b.index(pid) + 1) + 'th'}"
    return n


def door(w, pid):
    """The words that reach this person back: the label with the comma closed up (pike,first), or the name."""
    return label(w, pid).replace(", ", ",")


def display(w, pid):
    lab = label(w, pid)
    return lab[:1].upper() + lab[1:]


def of_event(w, e):
    """The event's person id, or None (the house, or a world without persons)."""
    who = e.get("who")
    return who if who and who in w.subjects else None


def by(w, e):
    """Who did this event, as printed: the person's label, or the name it was signed with."""
    pid = of_event(w, e)
    return label(w, pid) if pid else str(e.get("by") or "")


def tripped(w, e):
    """Who set a rule's act off, as printed: tripped_who's label, else the name kept in tripped_by."""
    t = e.get("tripped_who")
    return label(w, t) if t and t in w.subjects else str(e.get("tripped_by") or "")


def named(w, name, k=None):
    """A name stored in an event (tripped_by, a comment's by=) as printed: the person who bore it at event k."""
    if not on(w) or norm(name) in NOT_PERSONS:
        return name
    pid = at(w, name, k if k is not None else 10 ** 12)
    return label(w, pid) if pid else name


def me(w, actor=None):
    """The person acting now: today's bearer of the actor's name, or None."""
    return today(w, actor if actor is not None else w.me) if on(w) else None


def mine(w, e, actor=None):
    """Is this event the acting person's own? By person once there are persons, so a renamed person keeps their acts
    and a new bearer of an old name does not inherit them; by name before."""
    actor = actor if actor is not None else w.me
    pid = of_event(w, e)
    if pid:
        return pid == me(w, actor)
    return e.get("by") == actor


def comment_by(w, c, made=None):
    """A comment's author as printed. The comment keeps the name it was signed with; its making event names the person.
    The person is used only when the event's name is the comment's own, so a comment signed 'alex' by an older rule
    (the owner's comments were signed alex) is never silently given to someone else."""
    if not on(w):
        return c.get("by")
    if made is None:
        made = comment_events(w).get(c.get("id"))
    if made and of_event(w, made) and norm(made.get("by")) == norm(c.get("by")):
        return label(w, made["who"])
    return named(w, c.get("by"), _num(made["id"]) if made else None)


def reply_by(w, c, i):
    """The i-th reply on comment c, its author as printed: the resolve event that wrote it names the person."""
    r = (c.get("replies") or [])[i]
    if not on(w):
        return r.get("by")
    evs = [e for e in w.events if e["verb"] == "resolve" and (e.get("args") or {}).get("id") == c.get("id")
           and (e.get("args") or {}).get("line") and not e.get("undone")]
    e = evs[i] if i < len(evs) else None
    if e and of_event(w, e) and norm(e.get("by")) == norm(r.get("by")):
        return label(w, e["who"])
    return named(w, r.get("by"), _num(e["id"]) if e else None)


_cmap = weakref.WeakKeyDictionary()


def comment_events(w):
    key = (getattr(w, "_eseq", 0), len(w.events))
    hit = _cmap.get(w)
    if hit is None or hit[0] != key:
        m = {}
        for e in w.events:
            u = e.get("undo")
            if isinstance(u, dict) and u.get("drop_comment"):
                m[u["drop_comment"]] = e
        hit = (key, m)
        _cmap[w] = hit
    return hit[1]


# ---- typed words: forgiving to people ------------------------------------------------------------------------------

def typed(w, word):
    """A word someone typed -> (person id, a note naming the door to another bearer, or "") or None when it names no
    person. A person id is that person; 'pike,first' (or 'pike, first') is the first Pike; a bare name is today's
    bearer."""
    if not on(w):
        return None
    raw = str(word or "").strip().lstrip("@").strip("\"'")
    if PID.match(raw) and is_person(w, raw):
        return raw, ""
    name, _, mark = raw.replace(", ", ",").partition(",")
    name, mark = norm(name), mark.strip().lower()
    ix = index(w)
    b = ix.bearers(name)
    if not b:
        return None
    if mark:
        if mark in ORDINALS and ORDINALS.index(mark) < len(b):
            return b[ORDINALS.index(mark)], ""
        if mark in ("last", "today", "now"):
            return b[-1], ""
        return None
    pid = today(w, name)
    others = [x for x in b if x != pid]
    if name_now(w, pid) != name:
        note = f"no one is called {name} now: showing its last bearer, now called {label(w, pid)} ({pid})"
    else:
        note = f"showing today's {name} ({pid})" if others else ""
    if others:
        note += "; " + "; ".join(f"an earlier {name} also bore this name: {door(w, x)} ({x})" for x in others)
    return pid, note


# ---- making persons ------------------------------------------------------------------------------------------------

def _subject(w, pid, name, kind, began, names, status=None):
    props = {"name": name, "kind": kind}
    if began:
        props["began"] = began
    if status:
        props["status"] = status
    return {"id": pid, "kind": "person", "title": name[:1].upper() + name[1:], "text": "", "tags": [], "due": None,
            "rev": 1, "comments": [], "props": props, "person": {"names": [list(x) for x in names]}}


def kind_guess(w, name):
    """resident: a corner names them; human: a surface says person=<them>; worker: worker-<commission>; else agent."""
    import rooms
    k = rooms.kind_of(w, name)
    if k == "resident":
        return "resident"
    if k == "person":
        return "human"
    return "worker" if name.startswith("worker-") else "agent"


def begin(w, again=(), paused=(), actor=None):
    """Make the persons of this world, once, in one event. `again`: [(name, event id)]: a new person bore this name
    from that event on (the first bearer keeps every act before it, and is paused). `paused`: names whose only bearer
    is paused. Every past event signed by a person gets who=. Undo of the event takes all of it back."""
    from world import Refusal
    if on(w):
        raise Refusal("the persons of this world were made already (person lists them)")
    again = [(norm(n), _num(e)) for n, e in again]
    paused = {norm(n) for n in paused}
    names = [norm(actor or w.me)] if norm(actor or w.me) not in NOT_PERSONS else []    # whoever runs it is one
    for e in w.events:
        for n in (e.get("by"), e.get("tripped_by")):
            n = norm(n)
            if n and n not in NOT_PERSONS and n not in names:
                names.append(n)
    for n in w.nodes.values():               # residents and people who have not acted yet
        p = n.get("props") or {}
        if n["type"] == "surface":
            for x in [p.get("actor")] + str(p.get("person", "")).split(","):
                x = norm(x)
                if x and x not in NOT_PERSONS and x not in names:
                    names.append(x)
    for n, k in again:
        if n not in names:
            raise Refusal(f"again={n}: no one has acted as {n} here")
    made, plan = [], []                      # plan: (pid, name, from)
    for n in names:
        splits = sorted(k for m, k in again if m == n)
        starts = [0] + splits
        for i, k in enumerate(starts):
            pid = w._id("p")
            began = next((e["id"] for e in w.events if norm(e.get("by")) == n and _num(e["id"]) >= k
                          and (i + 1 >= len(starts) or _num(e["id"]) < starts[i + 1])), None)
            superseded = i + 1 < len(starts)
            w.subjects[pid] = _subject(w, pid, n, kind_guess(w, n), began, [(n, k)],
                                       "paused" if superseded or n in paused else None)
            made.append(pid)
            plan.append((pid, n, k))
    _cache.pop(w, None)
    stamped = 0
    for e in w.events:
        k = _num(e["id"])
        t = norm(e.get("tripped_by"))
        if t and t not in NOT_PERSONS and at(w, t, k):
            e["tripped_who"] = at(w, t, k)          # who set a rule off, kept apart from whose rule it was (c1910)
        n = norm(e.get("by"))
        if n in NOT_PERSONS:
            continue
        pid = at(w, n, k)
        if pid:
            e["who"] = pid
            stamped += 1
    ev = w._event("person", "persons", {"begin": len(made), **({"again": ",".join(f"{n}:e{k}" for n, k in again)} if again else {}),
                                        **({"paused": ",".join(sorted(paused))} if paused else {})},
                  {"persons_begin": made}, actor)
    return {"ok": True, "event": ev["id"], "made": made, "stamped": stamped, "plan": plan}


def unbegin(w, made):
    """The undo of begin: the persons go, and every who= with them. Refused once a person has been made or renamed
    since, so nothing later is left naming a person who is gone."""
    from world import Refusal
    later = [e for e in w.events if e["verb"] == "person" and e["target"] != "persons" and not e.get("undone")]
    if later:
        raise Refusal(f"persons have changed since they were made ({later[-1]['id']}); undo that first")
    for pid in made:
        w.subjects.pop(pid, None)
    for e in w.events:
        e.pop("who", None)
        e.pop("tripped_who", None)
    _cache.pop(w, None)


def new(w, name, kind=None, actor=None):
    """A new person who bears `name` from now on. An earlier bearer keeps every act signed before this moment."""
    from world import Refusal
    n = norm(name)
    if not re.fullmatch(r"[a-z][\w-]*", n) or n in NOT_PERSONS:
        raise Refusal(f"{name!r} can't be a person's name: a word of letters, digits and dashes, beginning with a letter")
    if kind and kind not in KINDS:
        raise Refusal("kind= is one of " + ", ".join(KINDS))
    k = w.next_event_number()
    pid = w._id("p")
    w.subjects[pid] = _subject(w, pid, n, kind or kind_guess(w, n), None, [(n, k)])
    _cache.pop(w, None)
    before = [x for x in index(w).bearers(n) if x != pid]
    ev = w._event("person", pid, {"new": n, "kind": w.subjects[pid]["props"]["kind"]},
                  {"delete": None, "delete_subject": pid}, actor)
    return {"ok": True, "event": ev["id"], "created": pid, "earlier": before}


def rename(w, pid, name, actor=None):
    from world import Refusal
    from copy import deepcopy
    n = norm(name)
    if not re.fullmatch(r"[a-z][\w-]*", n) or n in NOT_PERSONS:
        raise Refusal(f"{name!r} can't be a person's name: a word of letters, digits and dashes, beginning with a letter")
    s = w.subjects[pid]
    was = name_now(w, pid)
    if n == was:
        raise Refusal(f"{pid} is already called {n}")
    holder = today(w, n)
    if holder and holder != pid and name_now(w, holder) == n:
        raise Refusal(f"{label(w, holder)} ({holder}) is called {n} now; a name is one person's at a time "
                      f"(person new {n} is how a new person takes up a name)")
    before = deepcopy(s)
    k = w.next_event_number()
    s["props"]["name"] = n
    s["title"] = n[:1].upper() + n[1:]
    s.setdefault("person", {}).setdefault("names", []).append([n, k])
    s["rev"] += 1
    ev = w._event("person", pid, {"name": n, "was": was}, {"restore_subject": before}, actor)
    return {"ok": True, "event": ev["id"], "was": was}


def who_for(w, actor):
    """World._event's hook, called before the event takes its number: the acting person, or None. An actor seen for
    the first time gets a person, made by an event of its own just before the act (so it can be undone)."""
    n = norm(actor)
    if n in NOT_PERSONS or not on(w):
        return None
    pid = today(w, n)
    return pid if pid is not None else _mint_quietly(w, n)


def _mint_quietly(w, n):
    pid = w._id("p")
    k = w.next_event_number()
    # a4164: someone who came through the gate is a human, said by the gate (deskd sets through_gate for that one
    # line); everyone else is guessed
    kind = "human" if n and norm(getattr(w, "through_gate", None)) == n else kind_guess(w, n)
    w.subjects[pid] = _subject(w, pid, n, kind, f"e{k + 1}", [(n, k)])
    _cache.pop(w, None)
    w._event("person", pid, {"new": n, "kind": w.subjects[pid]["props"]["kind"], "first_act": True},
             {"delete": None, "delete_subject": pid}, "house")
    return pid


# ---- what the desk prints about a person ---------------------------------------------------------------------------

def acts(w, pid):
    return [e for e in w.events if e.get("who") == pid or (e["target"] == pid)]


def card(w, pid, note=""):
    """examine <person>: who they are, the names they have borne, how much they did and when, and the doors."""
    s = w.subjects[pid]
    p = s.get("props") or {}
    mine_ = [e for e in w.events if e.get("who") == pid]
    out = [f"{pid} person \"{display(w, pid)}\" · " + " ".join(f"{k}={v}" for k, v in p.items())]
    if note:
        out.append("  " + note)
    names = (s.get("person") or {}).get("names") or []
    out.append("  a person: one id for a life; the name is a label (person " + pid + " name=<new> renames)")
    out.append("  names borne: " + ", ".join(f"{n} from " + (f"e{k}" if k else "the beginning") for n, k in names))
    for n, _ in names:
        others = [x for x in index(w).bearers(n) if x != pid]
        if others:
            out.append(f"  {n} was also borne by " + ", ".join(f"{label(w, x)} ({x})" for x in others))
    if mine_:
        a, b = mine_[0], mine_[-1]
        stamp_ = lambda e: str(e.get("at") or e.get("day") or "")[:16].replace("T", " ")   # noqa: E731
        out.append(f"  {len(mine_)} act(s): first {a['id']} {stamp_(a)}, latest {b['id']} {stamp_(b)}; "
                   f"history {door(w, pid) if ' ' not in door(w, pid) else pid} lists the latest")
    else:
        out.append("  no acts yet")
    c = corner(w, pid)
    if c:
        out.append(f"  corner: {c} \"{w.nodes[c]['title']}\"")
    return "\n".join(out)


def listing(w):
    if not on(w):
        return ("no persons in this world yet: person begin makes them, once, from who has acted here "
                "(help person)")
    rows = []
    for pid in index(w).people:
        p = w.subjects[pid].get("props") or {}
        n = sum(1 for e in w.events if e.get("who") == pid)
        rows.append(f"  {pid} {label(w, pid)} · {p.get('kind', '?')}" + (f" · {p['status']}" if p.get("status") else "")
                    + f" · {n} act(s)")
    return f"{len(rows)} person(s):\n" + "\n".join(rows)


# a1595: help person is a note in the Help binder (helpnotes.py); the arguments are DeskKnife.USAGE["person"]


# ---- phase 2 (a1590): stored names become persons when saved --------------------------------------------------------

PERSON_KEYS = ("owner", "asked_by", "person")          # props whose value names a person (person=: a1062's Desktop)
TERMS = ("held-by", "asked-of", "owed-to", "asked-by", "awaits", "offered-to")     # promise terms that name one (a1587)
_ORD = "|".join(ORDINALS + ("last",))
_DOOR = rf"[\w-]+(?:,[ \t]*(?:{_ORD})\b)?"            # a name, with its door mark when it has one (juniper,first)
STORED = re.compile(rf"(?<![\w])(?:prop:)?({'|'.join(PERSON_KEYS)})=\"?({_DOOR})|(?<![\w-])({'|'.join(TERMS)}):({_DOOR})")


def is_pid(w, v):
    v = str(v or "").strip()
    return bool(PID.match(v)) and is_person(w, v)


def words(v):
    """A prop value's names: split at commas, except the comma of a door mark (juniper,first is one name)."""
    return [x.strip() for x in re.split(rf",(?![ \t]*(?:{_ORD})\b)", str(v or "")) if x.strip()]


def key(word):
    """How a bound word is kept: lower case, its door mark closed up (juniper, first -> juniper,first)."""
    return re.sub(r",\s+", ",", str(word or "").strip().lstrip("@").strip("\"'").lower())


def shown(w, v):
    """A stored value as people read it: each person id in it is the person's name, with its door mark where two
    persons bore it (juniper,first, which typed back means the same person). Anything else prints as it is."""
    if v is None or not on(w):
        return v
    parts = words(v)
    if not any(is_pid(w, p) for p in parts):
        return v
    return ",".join(door(w, p) if is_pid(w, p) else p for p in parts)


def shown_props(w, props):
    return {k: shown(w, v) for k, v in (props or {}).items()} if on(w) else dict(props or {})


def resolve(w, word, binds=None):
    """A name in a prop value or a selection -> (person id, a note for the receipt) or (None, ""). A person id is that
    person; a word the stored line being read was bound to at save is that person ("bound"); else a typed name: today's
    bearer, naming the door to an earlier one."""
    raw = str(word or "").strip().lstrip("@").strip("\"'")
    if is_pid(w, raw):
        return raw, ""
    if binds and key(raw) in binds and is_pid(w, binds[key(raw)]):
        return binds[key(raw)], "bound"
    hit = typed(w, raw)
    return hit if hit else (None, "")


def store_args(w, kv, binds=None):
    """Before an act sets props (create, prop): each name in a person prop becomes the person's id, so the store holds
    who was meant. Typing doesn't change: owner=juniper is today's Juniper. -> receipt lines (a door to another bearer,
    or a name no one bears, kept as a word)."""
    if not on(w):
        return []
    notes = []
    for k in PERSON_KEYS:
        if k not in kv or not str(kv[k]).strip():
            continue
        out = []
        for x in words(kv[k]):
            if x.startswith("$") or norm(x) in NOT_PERSONS:
                out.append(x)
                continue
            pid, how = resolve(w, x, binds)
            if pid:
                out.append(pid)
                # 9 Oct (a3299, a3806): a typed name is today's bearer, always; that an earlier person bore it too is
                # a standing fact, said by `examine <name>`, not on every claim. A name no one bears now is still said
                if how and how != "bound" and not how.startswith("showing today's"):
                    notes.append(f"~ {k}={x}: {how}")
            else:
                out.append(x)
                notes.append(f"~ {k}={x}: no one here bears the name {x}, so it is kept as a word and names no person "
                             f"(a1590: a person prop holds a person; person lists them)")
        kv[k] = ",".join(out)
    return notes


def matches(w, have, want, binds=None):
    """prop:<person key>=<want> against a stored value: the same person (by id), or, for a value kept as a word (no
    one bore it when it was set), the same word."""
    pid = resolve(w, want, binds)[0] if on(w) else None
    for x in words(have):
        if x == want or (pid and x == pid):
            return True
    return False


def holds(w, value, who):
    """Does a person prop's value (person=alex,sable; owner=p2917) name `who` (a name, read as today's bearer, or a
    person id)? By words in a world without persons."""
    want = str(who or "").strip().lower()
    pid = want if is_pid(w, want) else (today(w, want) if want and on(w) else None)
    return any(x.lower() == want or (pid and x == pid) for x in words(value))


def stored_words(text):
    """The names a stored line names persons by: prop:owner=juniper, owner=juniper in a do line, held-by:pike ... ($me
    and awaits:any are never bound)."""
    out = []
    for m in STORED.finditer(str(text or "")):
        wd = key(m.group(2) or m.group(4))
        if wd and wd != "any" and wd not in out and norm(wd) not in NOT_PERSONS:
            out.append(wd)
    return out


def bind_words(w, text, k=None):
    """-> {word: person id} for the names in stored `text`: as its writer means them now (k None: today's bearer, when
    it is saved), or as they were meant at event number k (the migration). A name no one bears is left unbound."""
    out = {}
    if not on(w):
        return out
    for wd in stored_words(text):
        name, _, mark = wd.partition(",")
        if is_pid(w, wd):
            pid = wd
        elif k is None or mark:
            pid = resolve(w, wd)[0]
        else:
            pid = at(w, name, k)
        if pid:
            out[wd] = pid
    return out


def bound_note(w, binds):
    return ", ".join(f"{wd} → {label(w, pid)} ({pid})" for wd, pid in (binds or {}).items())


class reading:
    """`with persons.reading(desk, binds):` a selection read inside means these bound persons (a view's query, a lens)."""

    def __init__(self, desk, binds):
        self.desk, self.binds = desk, binds

    def __enter__(self):
        st = getattr(self.desk, "_pstack", None)
        if st is None:
            st = self.desk._pstack = []
        st.append(dict(self.binds or {}))

    def __exit__(self, *a):
        self.desk._pstack.pop()


def active(desk):
    """The persons of the stored line being read now, or None (a typed line: today's bearers)."""
    st = getattr(desk, "_pstack", None)
    if st:
        return st[-1]
    import verbs
    b = verbs.bound(desk) or getattr(desk, "_parse_binds", None)
    return (b or {}).get("persons") if b else None


# ---- the migration, once per world ----------------------------------------------------------------------------------

def _set_at(w, ids, k):
    """The number of the latest live event that set prop k on any of ids, or None."""
    for e in reversed(w.events):
        if e.get("undone") or e["verb"] == "undo":
            continue
        a = e.get("args") or {}
        if k not in a:
            continue
        made = (e.get("undo") or {}).get("delete") if isinstance(e.get("undo"), dict) else None
        if e["target"] in ids or made in ids:
            return _num(e["id"])
    return None


def _written_at(w, hkey):
    """The number of the event that wrote a stored line holder's current text (made it, or last changed it)."""
    kind, hid = hkey
    for e in reversed(w.events):
        if e.get("undone") or e["verb"] == "undo":
            continue
        a = e.get("args") or {}
        made = (e.get("undo") or {}).get("delete") if isinstance(e.get("undo"), dict) else None
        if kind == "s":
            ids = {hid} | set(w.appearances_of(hid))
            if (e["verb"] == "create" and (made in ids or (made in w.nodes and w.nodes[made].get("subject") == hid))) \
                    or (e["target"] in ids and e["verb"] in ("edit", "rewrite", "replace", "append")
                        and ("text" in a or "append" in a or "new" in a or "line" in a)):
                return _num(e["id"])
        elif kind == "q":
            if "query" in a and (e["target"] == hid or made == hid):
                return _num(e["id"])
        elif e["target"] == hid and "wake" in a:
            return _num(e["id"])
    return None


def migrate(desk):
    """a1590 (3): once per world, after its persons are made. Every person prop and every stored line saved before
    this binds each name to the person who bore it when it was written, found by its event's time: never guessed, and
    never today's bearer by default. A name with no event to time it is left as it is and named. One event by the house,
    undoable; its note counts what bound to an earlier person, and names each."""
    import verbs
    from copy import deepcopy
    w = desk.world
    if getattr(w, "_persons_version", 0) >= 2 or not on(w):
        return None
    w._persons_version = 2
    props_before, binds_before, earlier, untimed, changed = [], [], [], [], []
    nprops = nlines = 0
    for kind, obj in [("s", s) for s in w.subjects.values() if s.get("kind") != "person"] + \
                     [("n", n) for n in w.nodes.values() if n["type"] == "surface"]:
        props = obj.get("props") or {}
        todo = [k for k in PERSON_KEYS if props.get(k) and not all(is_pid(w, x) for x in words(props[k]))]
        if not todo:
            continue
        ids = {obj["id"]} | (set(w.appearances_of(obj["id"])) if kind == "s" else set())
        prev, did = dict(props), False
        for k in todo:
            n = _set_at(w, ids, k)
            out = []
            for x in words(props[k]):
                name, _, mark = key(x).partition(",")
                if is_pid(w, x) or norm(x) in NOT_PERSONS or not index(w).bearers(name):
                    out.append(x)
                    continue
                if n is None:
                    untimed.append(f"{obj['id']} {k}={x}")
                    out.append(x)
                    continue
                pid = resolve(w, x)[0] if mark else at(w, name, n)
                if not pid:
                    out.append(x)
                    continue
                out.append(pid)
                did = True
                nprops += 1
                if pid != today(w, name):
                    shown_id = (w.appearances_of(obj["id"]) or [obj["id"]])[0] if kind == "s" else obj["id"]
                    earlier.append(f"{shown_id} {k}={x} (set e{n}) → {label(w, pid)} ({pid})")
            if out != words(props[k]):
                props[k] = ",".join(out)
        if did:
            props_before.append((kind, obj["id"], prev))
            changed.append(obj["id"])
    for hkey, (hkind, text) in verbs.stored_texts(w).items():
        found = stored_words(text)
        if not found:
            continue
        b = verbs.binding_of(w, hkey, text)
        if b and b.get("persons") is not None:
            continue
        n = _written_at(w, hkey)
        if n is None:
            untimed.append(f"{verbs.holder_label(w, hkey, hkind)}: {', '.join(found)}")
            continue
        binds = bind_words(w, text, n)
        if not binds:
            continue
        holder = w.subjects[hkey[1]] if hkey[0] == "s" else w.nodes[hkey[1]]
        binds_before.append((hkey[0], hkey[1], deepcopy(holder.get("qbinds" if hkey[0] == "q" else "binds"))))
        entry = deepcopy(b) if b else {"text": text, "words": {}, "missing": {}, "by": None, "lines": {}}
        entry["persons"] = binds
        verbs.keep_binding(w, hkey, entry)
        nlines += 1
        changed.append(hkey[1])
        for wd, pid in binds.items():
            if pid != today(w, wd.partition(",")[0]):
                earlier.append(f"{verbs.holder_label(w, hkey, hkind)} (written e{n}): {wd} → {label(w, pid)} ({pid})")
    if not (props_before or binds_before or untimed):
        return None
    _cache.pop(w, None)
    note = (f"a1590: stored names became persons, each the person who bore the name when it was written: {nprops} "
            f"name(s) in props, {nlines} stored line(s). {len(earlier)} bound to an earlier person"
            + (": " + "; ".join(earlier) if earlier else "")
            + (f". {len(untimed)} left as they were, with no event to time them: " + "; ".join(untimed) if untimed else ""))
    ev = w._event("person", "persons", {"bound": nprops, "lines": nlines, "earlier": len(earlier)},
                  {"persons_migrate": {"props": props_before, "binds": binds_before}}, actor="house", note=note)
    ev["changed"] = sorted(set(changed))
    return ev


def unmigrate(w, data):
    """The undo of migrate: each prop and binding as it was. It never runs again (the world remembers it ran)."""
    for kind, oid, prev in data.get("props") or []:
        obj = (w.subjects if kind == "s" else w.nodes).get(oid)
        if obj is not None:
            obj["props"] = dict(prev)
    for kind, oid, prev in data.get("binds") or []:
        obj = (w.subjects if kind == "s" else w.nodes).get(oid)
        if obj is None:
            continue
        slot = "qbinds" if kind == "q" else "binds"
        if prev is None:
            obj.pop(slot, None)
        else:
            obj[slot] = prev
