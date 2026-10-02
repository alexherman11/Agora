"""Persons, phase 1 (a1568, design a1016): a person is a thing with one id for a life, and names are labels on it.

A person is a subject of kind person with its own id kind (p1895), placed on no surface, so it has one id and never a
second one for an appearance (a760). Its name is a prop (name=pike), a label and never the identity, and its title is
that name as people read it. The names a person has borne are kept in the person (subject["person"]["names"], a list of
[name, from event number]), so a rename's undo, which restores the whole subject, takes the name back too.

Every event names its person in who= (by= keeps the name it was signed with, never rewritten). Printing shows the
person's name, with a mark only where two persons have borne it: 'pike, first' is the earlier of two Pikes. Today's
bearer is never marked.

Forgiving to people, strict to stored text (a990): a typed name means today's bearer and names the door to an earlier
one (pike,first); a person id always means that person. Stored names in props, queries and chat signatures are not
read through persons yet: that is phase 2 (a1590), so nothing migrates twice.

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
    w.subjects[pid] = _subject(w, pid, n, kind_guess(w, n), f"e{k + 1}", [(n, k)])
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


HELP = """person: the people who act here, each a thing with one id for a life (a1568, a1016). A name is a label on a
person, never the identity: two persons may bear one name in turn, and each keeps their own acts.
  person                      lists every person: id, name, kind, how many acts
  person <name or id>         one person (as examine does): names borne, acts, corner, doors to another bearer
  person new <name> [kind=resident|human|agent|worker]
                              a new person who bears <name> from now on; an earlier bearer keeps every act before
  person <name or id> name=<new>
                              renames that person; their acts, made_by and corner follow them (undo takes it back)
  person begin [again=<name>:<event>,...] [paused=<name>,...]
                              makes the persons of this world, once, from who has acted here. again= says a new person
                              bore a name from that event on. One event; undo takes it back
  A typed name means today's bearer, and names the door to an earlier one: examine pike, history pike,first. A person
  id (p1895) always means that person. Every event records its person (who=); by= keeps the name it was signed with.
  Printed, a person is their name, marked only where two persons have borne it: 'pike, first'.
  Stored names (owner=, asked_by=, a view's query, a chat line's signature) are still names: phase 2 (a1590)."""
