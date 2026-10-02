"""Promises as things, phase 1 (a1587; design a1576 with Revisions 2 and 3): once-promises and requests, with honest ends.

A promise is a thing (a subject of kind promise, placed in the house's Promises surface, role=promises) that stores only
its words: its title is what is promised, to= is whom it is addressed to (owed to, or for a request, asked of), and
about= the thing it is about (optional). Who made it, who accepted, reported, confirmed, released or carried it are
never stored: the subject keeps the list of events that acted on it (subject["promise"]["acts"], each [event id, act,
words]) and every person is read from those events (by= and who=), as a chat line reads its author from its event
(a1581, Pike e3840). So persons (a1568) sit under it with nothing migrated, and an act that is undone counts for
nothing: its event is undone, and the state is read without it.

    promise to=<name> <words> [about=<id>]   a promise by you, owed to <name>
    ask to=<name> <words> [about=<id>]       a request of <name>, held by you; it is not a promise until they accept
    accept <id> / decline <id>               the one asked: accept makes it their promise, owed to the asker
    withdraw <id>                            the asker takes a request back
    report <id> [how=<words>]                its holder says it is done: 'reported, not confirmed' until the one owed
                                             confirms; owed to yourself, it is kept on your own word
    confirm <id>                             the one owed says it was kept
    release <id> [why=<words>]               its holder lets it go; a reason is welcome, never required
    carry <id> to=<name>                     its holder hands it on: 'carried to you from X' / 'you carried it to Y'

A commission is its asker's own once-promise (Juniper c1585): setting commission=asked makes one, owed to asked_by (or
the card's maker), and lived= on the card is the asker's report. A card that leaves the living (done, trashed,
cancelled, in a Trash) with an open promise about it that the same act did not end asks its holder, once, on their
sill: kept, released or carried?
"""

import re
import shlex
import weakref
from copy import deepcopy

import persons
from world import Refusal

VERBS = ("promise", "ask", "accept", "decline", "withdraw", "report", "confirm", "release", "carry")
ENDS_CARD = ("done", "trashed", "cancelled")
OPEN, ASKED, REPORTED = "open", "requested", "reported"
TERMS = ("held-by:", "asked-of:", "owed-to:", "asked-by:", "awaits:")

_ev = weakref.WeakKeyDictionary()


# ---- reading -------------------------------------------------------------------------------------------------------

def events(w):
    key = (getattr(w, "_eseq", 0), len(w.events))
    hit = _ev.get(w)
    if hit is None or hit[0] != key:
        hit = (key, {e["id"]: e for e in w.events})
        _ev[w] = hit
    return hit[1]


def surface(w):
    for fid, n in w.nodes.items():
        if n["type"] == "surface" and (n.get("props") or {}).get("role") == "promises":
            return fid
    return None


def on(w):
    """Has this world promises (a Promises surface)? Before, owe=/awaiting= are props like any other."""
    return surface(w) is not None


def is_promise(w, ident):
    sid = w.subject_of(ident) if ident in w.nodes else ident
    return bool(sid) and (w.subjects.get(sid) or {}).get("kind") == "promise"


def all_sids(w):
    return [sid for sid, s in w.subjects.items() if s.get("kind") == "promise"]


def aid_of(w, sid):
    apps = w.appearances_of(sid)
    return apps[0] if apps else sid


def _person(w, name=None, e=None):
    """A person as {pid, name}: from an event (its who=, else its by=), or from a stored name (today's bearer)."""
    if e is not None:
        n = persons.norm(e.get("by"))
        return {"pid": persons.of_event(w, e), "name": n}
    n = persons.norm(name)
    return {"pid": persons.today(w, n) if n and persons.on(w) else None, "name": n}


def same(a, b):
    if not a or not b:
        return False
    if a.get("pid") and b.get("pid"):
        return a["pid"] == b["pid"]
    return bool(a.get("name")) and a.get("name") == b.get("name")


def label(w, p):
    if not p:
        return "no one"
    if p.get("pid"):
        return persons.label(w, p["pid"])
    return p.get("name") or "unknown"


def me(w):
    return _person(w, w.me)


def state(w, sid):
    """Everything a promise is now, read from the events that acted on it. Undone events count for nothing."""
    s = w.subjects[sid]
    p = s.get("props") or {}
    evs = events(w)
    st = {"sid": sid, "aid": aid_of(w, sid), "what": s["title"], "form": None, "state": None, "asker": None,
          "asked": None, "maker": None, "holder": None, "owed": None, "about": p.get("about", ""), "trail": [],
          "asked_end": False, "carried_from": None, "carried_to": [], "made": None, "ended": None, "self": False}
    to = _person(w, p.get("to")) if p.get("to") else None
    for a in (s.get("promise") or {}).get("acts") or []:
        eid, act, words = a[0], a[1], (a[2] if len(a) > 2 else "")
        e = evs.get(eid)
        if e is not None and (e.get("undone") or e["verb"] == "undo"):
            continue
        who = _person(w, e=e) if e is not None else {"pid": None, "name": "unknown"}
        if act == "asked-end":
            st["asked_end"] = True
            continue
        st["trail"].append((act, who, eid if e is not None else None, words))
        if act == "promise":
            st.update(form="promise", state=OPEN, maker=who, holder=who, owed=to, made=eid)
        elif act == "ask":
            st.update(form="request", state=ASKED, asker=who, asked=to, made=eid)
        elif act == "accept":
            st.update(form="promise", state=OPEN, maker=who, holder=who, owed=st["asker"])
        elif act in ("decline", "withdraw", "release"):
            st.update(state={"decline": "declined", "withdraw": "withdrawn", "release": "released"}[act], ended=(act, who, eid, words))
        elif act == "report":
            if same(st["holder"], st["owed"]):
                st.update(state="kept", self=True, ended=(act, who, eid, words))
            else:
                st.update(state=REPORTED, ended=(act, who, eid, words))
        elif act == "confirm":
            st.update(state="kept", ended=(act, who, eid, words))
        elif act == "carry":
            new = _person(w, words)
            st["carried_to"].append((st["holder"], new, eid))
            st["carried_from"] = st["holder"]
            st["holder"] = new
    return st


def is_open(st):
    return st["state"] in (OPEN, ASKED)


def phrase(w, st, reader=None):
    """How a promise reads to this reader: 'asked of you by sable', 'you promised pike', 'reported by pike, not
    confirmed', 'carried to you from pike'."""
    r = reader or me(w)
    L = lambda p: "you" if same(p, r) else label(w, p)     # noqa: E731
    k = st["state"]
    if k == ASKED:
        if same(st["asked"], r):
            return f"asked of you by {label(w, st['asker'])} (accept or decline {st['aid']})"
        return f"{L(st['asker'])} asked {label(w, st['asked'])}" + (", waiting for an answer" if same(st["asker"], r) else "")
    if k in ("declined", "withdrawn"):
        a, who, eid, _ = st["ended"]
        return f"a request of {L(st['asked'])} by {L(st['asker'])}, {k} by {L(who)}" + (f" ({eid})" if eid else "")
    owed = L(st["owed"])
    if same(st["holder"], st["owed"]):
        base = "your own promise" if same(st["holder"], r) else f"{label(w, st['holder'])}'s own promise"
    elif st["carried_from"]:
        base = f"{L(st['holder'])} {'hold' if same(st['holder'], r) else 'holds'} it, owed to {owed}"
    else:
        base = f"{L(st['holder'])} promised {owed}"
    if k == OPEN:
        out = base
        for old, new, eid in st["carried_to"]:
            if same(new, r) and same(st["holder"], r):
                out += f" · carried to you from {label(w, old)}"
            elif same(old, r):
                out += f" · you carried it to {label(w, new)}"
            else:
                out += f" · carried to {label(w, new)} from {label(w, old)}"
        return out
    a, who, eid, words = st["ended"]
    if k == REPORTED:
        if same(st["owed"], r):
            return f"reported by {label(w, who)}, not confirmed (confirm {st['aid']} if it was kept)"
        return f"reported by {L(who)}, not confirmed by {label(w, st['owed'])}" + (f": {words}" if words else "")
    if k == "kept":
        if st["self"]:
            return f"kept ({'your' if same(who, r) else label(w, who) + chr(39) + 's'} own word)" + (f": {words}" if words else "")
        return f"kept, confirmed by {L(who)}"
    if k == "released":
        return f"released by {L(who)}" + (f": {words}" if words else "")
    return k or "?"


def short(w, st, reader=None):
    """The one word of its state, for a column: open, asked of you, reported, kept, released ..."""
    return phrase(w, st, reader)


def about_sid(w, st):
    a = st.get("about") or ""
    return w.subject_of(a) if a and (a in w.nodes or a in w.subjects) else None


def open_about(w, card_sid):
    return [st for st in (state(w, x) for x in all_sids(w)) if is_open(st) and about_sid(w, st) == card_sid]


def asked_of(w, card_sid):
    """Who is asked, in open requests about this thing, as printed: 'alex' or 'alex, pike' ('' when no one)."""
    names = []
    for st in open_about(w, card_sid):
        if st["state"] == ASKED and label(w, st["asked"]) not in names:
            names.append(label(w, st["asked"]))
    return ", ".join(names)


def matching(w, term):
    """A selection term over promises -> the set of subject ids it selects (cards, for awaits:)."""
    key, _, val = term.partition(":")
    val = val.strip().lower()
    if not val:
        raise Refusal(f"{key}:<name>, e.g. {key}:sable" + (" (awaits:any for anyone)" if key == "awaits" else ""))
    who = {"pid": None, "name": persons.norm(val)} if val == "any" else _person(w, val)
    hit = set()
    for sid in all_sids(w):
        st = state(w, sid)
        if key == "held-by" and st["state"] == OPEN and same(st["holder"], who):
            hit.add(sid)
        elif key == "asked-of" and st["state"] == ASKED and same(st["asked"], who):
            hit.add(sid)
        elif key == "asked-by" and st["state"] == ASKED and same(st["asker"], who):
            hit.add(sid)
        elif key == "owed-to" and st["state"] in (OPEN, REPORTED) and same(st["owed"], who):
            hit.add(sid)
        elif key == "awaits" and st["state"] == ASKED and (val == "any" or same(st["asked"], who)):
            c = about_sid(w, st)
            if c:
                hit.add(c)
    return hit


# ---- acting --------------------------------------------------------------------------------------------------------

def ensure_surface(w):
    """The Promises surface, made once in Home (the outermost room) by the house; -> (fid, event id or None)."""
    fid = surface(w)
    if fid:
        return fid, None
    import rooms
    rs = rooms.all_rooms(w)
    home = rs[0] if rs else w.root
    r = w.apply("create", home, None, {"kind": "surface", "title": "Promises", "layout": "column"}, "house")
    fid = r["created"]
    w.nodes[fid].setdefault("props", {})["role"] = "promises"
    return fid, r["event"]


def make(w, form, what, to, about=None, actor=None, cause=None, acts=None, quiet=False):
    """A new promise or request in the Promises surface. -> (aid, event). `acts`: the acts it is made with when they
    come from older events (the migration); otherwise the event made here is its making act."""
    fid, _ = ensure_surface(w)
    sid = w.add_subject("promise", str(what).strip())
    w.subjects[sid]["props"] = {"to": persons.norm(to)} if to else {}
    if about:
        w.subjects[sid]["props"]["about"] = about
    aid = w.place(sid, fid, 8, 8, 400, 40)
    w._bump(fid)
    ev = None
    if not quiet:
        args = {"to": persons.norm(to), "what": str(what).strip()}
        if about:
            args["about"] = about
        ev = w._event(form, aid, args, {"delete": aid, "delete_subject": sid}, actor)
        if cause:
            ev["cause"] = cause
    w.subjects[sid]["promise"] = {"acts": acts if acts is not None else [[ev["id"], form]]}
    return aid, ev


def _sill_notes(w, sid):
    aid = aid_of(w, sid)
    return [x for x, s in w.subjects.items() if (s.get("props") or {}).get("promise") in (aid, sid)
            and (s.get("props") or {}).get("status") != "done"]


def add_act(w, sid, act, words="", actor=None, cause=None, args=None):
    """One act on a promise: an event by the actor, the act kept with the event's id, and any sill question about it
    answered in the same event. Undo restores the promise and the questions."""
    notes = _sill_notes(w, sid) if act in ("report", "confirm", "release", "carry", "decline", "withdraw") else []
    before = [deepcopy(w.subjects[x]) for x in [sid] + notes]
    aid = aid_of(w, sid)
    ev = w._event(act, aid, dict(args or {}, **({"words": words} if words and not args else {})),
                  {"restore_subjects": before}, actor)
    ev["changed"] = [sid] + notes
    if cause:
        ev["cause"] = cause
    s = w.subjects[sid]
    s.setdefault("promise", {}).setdefault("acts", []).append([ev["id"], act] + ([words] if words else []))
    s["rev"] += 1
    for x in notes:
        n = w.subjects[x]
        n["props"]["status"] = "done"
        n["props"]["next"] = f"answered: {act} ({ev['id']})"
        n["rev"] += 1
    for a in w.appearances_of(sid):
        w._bump(a)
    return ev


def _who_may(w, st, act, actor):
    """None when this actor may do this act now, or the refusal saying who may and what the promise is."""
    a = _person(w, actor)
    k = st["state"]
    if k not in (OPEN, ASKED, REPORTED):
        return f"{st['aid']} has ended: {phrase(w, st)}. Nothing more ends it"
    if act in ("accept", "decline"):
        if k != ASKED:
            return f"{st['aid']} is not a request waiting for an answer: {phrase(w, st)}"
        if not same(st["asked"], a):
            return f"only {label(w, st['asked'])}, who was asked, can {act} {st['aid']}"
    elif act == "withdraw":
        if k != ASKED:
            return f"{st['aid']} is not a request (it is {phrase(w, st)}); its holder can release it"
        if not same(st["asker"], a):
            return f"only {label(w, st['asker'])}, who asked, can withdraw {st['aid']}"
    elif act in ("report", "release", "carry"):
        if k == ASKED:
            return (f"{st['aid']} is a request, not a promise yet: {phrase(w, st)}. "
                    + ("accept it first, or decline it" if same(st["asked"], a) else "the one asked accepts or declines it"))
        if k == REPORTED:
            return f"{st['aid']} is reported already, waiting for {label(w, st['owed'])} to confirm it"
        if not same(st["holder"], a):
            return f"only {label(w, st['holder'])}, who holds it, can {act} {st['aid']}"
    elif act == "confirm":
        if k == ASKED and same(st["asker"], a):
            return None          # what was asked was done: the asker says so, and it ends kept
        if k not in (OPEN, REPORTED):
            return f"{st['aid']} is {phrase(w, st)}"
        if not same(st["owed"], a):
            return f"only {label(w, st['owed'])}, to whom it is owed, can confirm {st['aid']}"
    return None


USAGE = {
    "promise": "promise to=<name> <words> [about=<id>]",
    "ask": "ask to=<name> <words> [about=<id>]",
    "accept": "accept <id>", "decline": "decline <id>", "withdraw": "withdraw <id>",
    "report": "report <id> [how=<words>]", "confirm": "confirm <id>",
    "release": "release <id> [why=<words>]", "carry": "carry <id> to=<name>",
}


def _parse(arg):
    try:
        argv = shlex.split(arg)
    except ValueError as e:
        raise Refusal(f"could not parse: {e}")
    words, kv = [], {}
    for x in argv:
        k, eq, v = x.partition("=")
        if eq and re.fullmatch(r"[a-z_]+", k):
            kv[k] = v
        else:
            words.append(x)
    return words, kv


def command(desk, verb, arg):
    """The nine verbs, typed (`accept a2001`) or through do (`do accept a2001`). -> receipt text."""
    w = desk.world
    words, kv = _parse(arg)
    if verb in ("promise", "ask"):
        to = kv.get("to") or ""
        what = " ".join(words) or kv.get("what", "")
        if not to or not what:
            raise Refusal(f"{USAGE[verb]}, e.g. {verb} to=pike \"review a1193 before it lands\" about=a1193")
        if persons.on(w) and persons.typed(w, to) is None and not _known_name(w, to):
            raise Refusal(f"no one called {to} acts here (person lists everyone)")
        if verb == "ask" and same(_person(w, to), me(w)):
            raise Refusal("a request is of someone else; to promise yourself something, promise to=<you>")
        about = None
        if kv.get("about"):
            about = desk._resolve(kv["about"], allow_subject=False)
        aid, ev = make(w, verb, what, persons.norm(to), about)
        desk._mark_seen(aid)
        desk._mark_seen(w.nodes[aid]["subject"])
        st = state(w, w.nodes[aid]["subject"])
        where = (f"it shows on {label(w, st['asked'])}'s list as 'asked of you' until they accept or decline; "
                 f"withdraw {aid} takes it back") if verb == "ask" else \
                (f"it is yours to keep: report {aid} when it's done, release {aid} if you can't, carry {aid} to=<name>")
        return f"ok {ev['id']}: {aid} {verb} \"{st['what']}\": {phrase(w, st)}" + (f" · about {about}" if about else "") + f"\n  {where}"
    if not words:
        raise Refusal(USAGE[verb])
    target = desk._resolve(words[0], allow_subject=False)
    sid = w.subject_of(target)
    if not is_promise(w, target):
        raise Refusal(f"{target} is not a promise or request; promises are in the Promises surface "
                      f"({surface(w) or 'none yet'}). promises lists yours")
    if desk.seen.get(target) is None and desk.seen.get(sid) is None:
        raise Refusal(f"you have not looked at {target} yet; look, examine or read it first")
    st = state(w, sid)
    why = _who_may(w, st, verb, w.me)
    if why:
        raise Refusal(why)
    text = ""
    if verb == "carry":
        to = kv.get("to") or (words[1] if len(words) > 1 else "")
        if not to:
            raise Refusal(USAGE["carry"])
        if same(_person(w, to), st["holder"]):
            raise Refusal(f"{label(w, st['holder'])} holds it already")
        text = persons.norm(to)
        ev = add_act(w, sid, "carry", text, args={"to": text})
    elif verb in ("report", "release"):
        text = kv.get("how" if verb == "report" else "why") or " ".join(words[1:])
        ev = add_act(w, sid, verb, text, args=({"how" if verb == "report" else "why": text} if text else {}))
    else:
        ev = add_act(w, sid, verb)
    desk._mark_seen(target)
    desk._mark_seen(sid)
    st = state(w, sid)
    out = f"ok {ev['id']}: {target} {verb}: {phrase(w, st)} · \"{st['what']}\""
    if verb == "carry":
        out += f"\n  {label(w, st['holder'])} sees it as 'carried to you from {label(w, st['carried_from'])}'"
    if verb == "report" and st["state"] == REPORTED:
        out += f"\n  it leaves your list; {label(w, st['owed'])} sees 'reported, not confirmed' until they confirm it"
    return out


def _known_name(w, name):
    n = persons.norm(name)
    return any(persons.norm(e.get("by")) == n for e in w.events[-2000:])


def listing(desk):
    """`promises`: yours, by what is waiting on whom."""
    w = desk.world
    r = me(w)
    groups = {"asked of you (accept or decline)": [], "you hold (report, release or carry)": [],
              "reported to you, not confirmed (confirm)": [], "owed to you": [], "you asked, waiting": [],
              "you reported, not confirmed yet": []}
    for sid in all_sids(w):
        st = state(w, sid)
        k = st["state"]
        if k == ASKED and same(st["asked"], r):
            groups["asked of you (accept or decline)"].append(st)
        elif k == ASKED and same(st["asker"], r):
            groups["you asked, waiting"].append(st)
        elif k == OPEN and same(st["holder"], r):
            groups["you hold (report, release or carry)"].append(st)
        elif k == OPEN and same(st["owed"], r):
            groups["owed to you"].append(st)
        elif k == REPORTED and same(st["owed"], r):
            groups["reported to you, not confirmed (confirm)"].append(st)
        elif k == REPORTED and same(st["holder"], r):
            groups["you reported, not confirmed yet"].append(st)
    out = []
    for title, sts in groups.items():
        if sts:
            out.append(f"{title}:")
            for st in sts:
                desk._mark_seen(st["aid"])
                out.append(f"  {st['aid']} \"{st['what']}\" · {phrase(w, st)}" + (f" · about {st['about']}" if st["about"] else ""))
    if not out:
        return "no open promises or requests of yours (help promises)"
    return "\n".join(out)


def card_lines(desk, nid):
    """What examine adds for a promise: its story, act by act, and the verbs open to you now."""
    w = desk.world
    st = state(w, w.subject_of(nid))
    out = [f"  a {st['form'] or 'promise'}: {phrase(w, st)}" + (f" · about {st['about']}" if st["about"] else "")]
    for act, who, eid, words in st["trail"]:
        out.append(f"    {act} by {label(w, who)}" + (f" ({eid})" if eid else " (no event says who)")
                   + (f": {words}" if words else ""))
    may = [v for v in ("accept", "decline", "withdraw", "report", "confirm", "release", "carry") if not _who_may(w, st, v, w.me)]
    out.append("  verbs: " + (" · ".join(USAGE[v].replace("<id>", st["aid"]) for v in may) if may else "none open to you now")
               + "   (help promises)")
    return out


# ---- what other acts mean for promises (after every act) -----------------------------------------------------------

def _owed_for(w, card_sid, writer):
    """Juniper c1585, Sable e4790 (a): owed to asked_by if set, else the card's maker, else its writer."""
    p = w.subjects[card_sid].get("props") or {}
    if p.get("asked_by"):
        return persons.norm(p["asked_by"])
    import blanks
    apps = set(w.appearances_of(card_sid))
    for e in w.events:
        if e["verb"] == "create" and not e.get("undone") and (e.get("undo") or {}).get("delete") in apps:
            return persons.norm(e["by"])
    return persons.norm(writer)


def living(w, card_sid):
    s = w.subjects.get(card_sid)
    if not s:
        return False
    if (s.get("props") or {}).get("status") in ENDS_CARD:
        return False
    import moo
    apps = w.appearances_of(card_sid)
    if not apps:
        return False
    bins = moo.trash_surfaces(w)
    return not all(moo.in_trash(w, a, bins) for a in apps)


def sill(w, name):
    import rooms
    fid = rooms.corner_of(w, name)
    if fid:
        return fid
    for f, n in w.nodes.items():
        if n["type"] == "surface" and persons.norm(name) in {x.strip().lower() for x in str((n.get("props") or {}).get("person", "")).split(",")}:
            return f
    return None


def after_act(desk, n0):
    """After a command: a commission asked makes its asker's promise; lived= on a card is its holder's report (or the
    owed one's confirmation); a card that left the living with an open promise about it asks the holder once. ->
    receipt lines."""
    w = desk.world
    if not on(w):
        return []
    new = [e for e in w.events[n0:] if not e.get("undone") and e["verb"] != "undo"]
    if not new:
        return []
    notes, cards = [], set()
    for e in new:
        sid = w.subject_of(e["target"]) if e["target"] in w.nodes or e["target"] in w.subjects else None
        for c in [sid] + [w.subject_of(x) for x in (e.get("changed") or []) if x in w.nodes]:
            if c and w.subjects.get(c, {}).get("kind") not in (None, "promise"):
                cards.add(c)
        a = e.get("args") or {}
        if e["verb"] != "prop" or not sid or persons.norm(e["by"]) in persons.NOT_PERSONS:
            continue
        s = w.subjects[sid]
        if a.get("commission") == "asked" and s.get("kind") == "task":
            mine_ = [st for st in open_about(w, sid) if st["state"] == OPEN and same(st["holder"], _person(w, e=e))]
            if not mine_:
                owed = _owed_for(w, sid, e["by"])
                aid, ev = make(w, "promise", f"live what this lands: {s['title']}", owed, aid_of(w, sid), e["by"], cause=e["id"])
                st = state(w, w.nodes[aid]["subject"])
                notes.append(f"~ a commission is its asker's promise: {aid} \"{st['what'][:60]}\" · {phrase(w, st)}"
                             f" (lived= on {aid_of(w, sid)} is your report)")
        if a.get("lived"):
            actor = _person(w, e=e)
            for st in open_about(w, sid):
                if st["state"] == OPEN and same(st["holder"], actor):
                    add_act(w, st["sid"], "report", str(a["lived"]), e["by"], cause=e["id"], args={"how": str(a["lived"])})
                    st2 = state(w, st["sid"])
                    notes.append(f"~ lived= reports {st['aid']}: {phrase(w, st2)}")
                elif st["state"] in (OPEN, REPORTED) and same(st["owed"], actor):
                    add_act(w, st["sid"], "confirm", "", e["by"], cause=e["id"])
                    notes.append(f"~ lived= by the one it's owed to confirms {st['aid']}: kept")
    for c in cards:
        if living(w, c):
            continue
        for st in open_about(w, c):
            if st["state"] != OPEN or st["asked_end"]:
                continue
            holder = label(w, st["holder"])
            fid = sill(w, holder)
            card = aid_of(w, c)
            if not fid:
                notes.append(f"~ {card} left the living with {st['aid']} still open (\"{st['what'][:60]}\", held by "
                             f"{holder}), and {holder} has no sill to be asked on: report, release or carry {st['aid']}")
                continue
            text = (f"{card} \"{w.subjects[c]['title']}\" left the living ({w.subjects[c].get('props', {}).get('status') or 'no longer placed'}), "
                    f"and your promise about it is still open:\n  {st['aid']} \"{st['what']}\" · {phrase(w, st, st['holder'])}\n"
                    f"Was it kept, released or carried? One of these ends it, and this note with it:\n"
                    f"  kept: report {st['aid']} how=\"...\"\n  released: release {st['aid']} [why=\"...\"]\n"
                    f"  carried: carry {st['aid']} to=<name>")
            made = w.last_created
            r = w.apply("create", fid, None, {"kind": "note", "title": f"Kept, released or carried? {st['aid']} about {card}",
                                              "text": text, "promise": st["aid"]}, "house")
            w.last_created = made
            evx = next(x for x in w.events if x["id"] == r["event"])
            evx["cause"] = new[0]["id"]
            w.subjects[st["sid"]]["promise"]["acts"].append([r["event"], "asked-end"])
            notes.append(f"~ {card} left the living with {st['aid']} still open: {holder} is asked once, on their sill "
                         f"({r['created']}): kept, released or carried?")
    return notes


def guard_props(w, verb, kv):
    """Once a world has promises, owe= and awaiting= are not props any more: one thing, never a prop saying otherwise."""
    if not on(w) or verb not in ("prop", "create"):
        return
    for k, door in (("owe", "promise to=<name> <words> about=<card>"), ("awaiting", "ask to=<name> <words> about=<card>"),
                    ("due_for", "a commission's promise (help promises)")):
        if k in kv and verb in ("prop", "create"):
            raise Refusal(f"{k}= is a promise now, held by the house as a thing with its maker and its end: {door}. "
                          f"(remove={k} still clears an old one)")


# ---- the migration, once per world (a1587 (5), (7); the table in c1992, Sable's answers in e4790) ------------------

IN_FLIGHT = ("asked", "working", "waiting", "ready", "landing", "landed")

# Sable's word on frontier's cards (e4790), each applied only while the card still says what it said when she gave it:
# a719's owe is a request of alex (deleting a card is his act); a1193's is her own promise owed to alex (the world half
# is hers, his seeing it confirms it), and it absorbs a1140's owe and a1971's due note; a1193's earlier owe (e2720) and
# awaiting=pike (e2798) were her request of Pike, ended when she rewrote them (e3291): migrated as a closed record.
# The Astra-era requests are closed records too: the team is paused and Jeff isn't here.
DECIDED = {
    "a719": {"owe": "Alex deletes a card", "as": "ask", "to": "alex"},
    "a1193": {"owe": "after landing: the world half", "to": "alex"},
    "a1140": {"owe": "after pulse lands: the world half", "into": "a1193"},
    "a397": {"awaiting": "astra-awareness", "closed": "withdrawn at migration: asker paused"},
    "a432": {"awaiting": "jeff", "closed": "withdrawn at migration: asker paused"},
    "a505": {"awaiting": "jeff", "closed": "withdrawn at migration: asker paused"},
}
SPOKE = {"sable"}      # writers who checked the table themselves (e4790): their owes are not flagged back to them
HISTORY = [   # (card, the owe event, its words, asked of, the awaiting event, the event that ended it, how)
    ("a1193", "e2720", "Pike's review before landing", "pike", "e2798", "e3291",
     "kept: Pike reviewed it (c1377, resolved Kept at e3328); Sable rewrote the owe and removed awaiting=pike at e3291"),
]


def writer(w, sid, key):
    """The latest live event that set this subject's prop `key` (a prop or a create), or None."""
    nodes = set(w.appearances_of(sid)) | {sid}
    for e in reversed(w.events):
        if e.get("undone") or e["verb"] == "undo" or e["target"] not in nodes and not (
                e["verb"] == "create" and (e.get("undo") or {}).get("delete") in nodes):
            continue
        if key in (e.get("args") or {}):
            return e
    return None


def _decided(w, sid, key, val):
    for aid in w.appearances_of(sid):
        d = DECIDED.get(aid)
        if d and key in d and str(val).startswith(d[key]):
            return aid, d
    return None, None


def plan(w):
    """What the migration would make, without making it. -> (items, steps): items are promises to make, each
    {form, what, to, about, acts, card, why}; steps are the other changes, each (kind, id, words)."""
    items, steps, cards = [], [], {}
    for sid, s in w.subjects.items():
        p = s.get("props") or {}
        if s.get("kind") == "promise":
            continue
        if any(k in p for k in ("owe", "awaiting")) or (s.get("kind") == "task" and p.get("commission") in IN_FLIGHT
                                                         and not p.get("lived") and p.get("status") not in ENDS_CARD):
            cards[sid] = p
    dues = {}
    for sid, s in w.subjects.items():
        d = (s.get("props") or {}).get("due_for")
        if d and (s.get("props") or {}).get("status") != "done":
            dues.setdefault(w.subject_of(d) if d in w.nodes else d, []).append(sid)
    folded = {}
    commission_done = set()

    def asker_of(card):
        e = next((x for x in reversed(w.events) if x["target"] in w.appearances_of(card) and x["verb"] == "prop"
                  and (x.get("args") or {}).get("commission") == "asked" and not x.get("undone")), None)
        return e

    for sid, p in cards.items():
        s, card = w.subjects[sid], aid_of(w, sid)
        owe, aw = p.get("owe"), p.get("awaiting")
        oe, ae = (writer(w, sid, "owe") if owe is not None else None), (writer(w, sid, "awaiting") if aw is not None else None)
        flight = s.get("kind") == "task" and p.get("commission") in IN_FLIGHT and not p.get("lived") and p.get("status") not in ENDS_CARD
        ce = asker_of(sid) if flight else None
        if aw is not None:
            _, d = _decided(w, sid, "awaiting", aw)
            if d and d.get("closed"):
                items.append({"form": "ask", "what": s["title"], "to": aw, "about": card, "card": sid,
                              "acts": [[ae["id"] if ae else None, "ask"], ["MIG", "withdraw", d["closed"]]],
                              "why": f"awaiting={aw} on {card}: a closed record ({d['closed']})"})
                steps.append(("remove", sid, "awaiting"))
                aw = None
        if owe is not None and str(owe).strip().lower() in ("none", ""):
            steps.append(("remove", sid, "owe"))
            owe = None
        if owe is not None:
            daid, d = _decided(w, sid, "owe", owe)
            steps.append(("remove", sid, "owe"))
            wname = oe["by"] if oe else None
            if d and d.get("into"):
                folded.setdefault(w.subject_of(d["into"]), []).append((card, owe))
                steps.append(("note", sid, f"owe on {card} folds into {d['into']}'s promise (Sable e4790)"))
            elif aw is not None and ae and oe and persons.norm(ae["by"]) == persons.norm(oe["by"]):
                items.append({"form": "ask", "what": owe, "to": aw, "about": card, "card": sid, "acts": [[oe["id"], "ask"]],
                              "why": f"owe= and awaiting={aw} on {card}, both by {oe['by']}: a request of {aw}",
                              "flag": None if persons.norm(oe["by"]) in SPOKE else persons.norm(oe["by"])})
                steps.append(("remove", sid, "awaiting"))
                aw = None
                if flight:
                    commission_done.add(sid)
            elif d and d.get("as") == "ask":
                items.append({"form": "ask", "what": owe, "to": d["to"], "about": card, "card": sid,
                              "acts": [[oe["id"] if oe else None, "ask"]], "why": f"owe on {card}: a request of {d['to']} (Sable e4790)"})
            elif flight and ce and oe and persons.norm(ce["by"]) == persons.norm(oe["by"]):
                cards[sid] = dict(p, _words=owe, _to=(d or {}).get("to"))      # the commission's promise takes its words
            else:
                to = (d or {}).get("to") or _owed_for(w, sid, wname or "")
                items.append({"form": "promise", "what": owe, "to": to, "about": card, "card": sid,
                              "acts": [[oe["id"] if oe else None, "promise"]],
                              "why": f"owe on {card} by {wname or 'unknown'}, owed to {to}"})
        if aw is not None:
            items.append({"form": "ask", "what": s["title"], "to": aw, "about": card, "card": sid,
                          "acts": [[ae["id"] if ae else None, "ask"]],
                          "why": f"awaiting={aw} on {card} by {ae['by'] if ae else 'unknown'}: a request of {aw}"})
            steps.append(("remove", sid, "awaiting"))
    for sid, p in cards.items():
        s = w.subjects[sid]
        flight = s.get("kind") == "task" and p.get("commission") in IN_FLIGHT and not p.get("lived") and p.get("status") not in ENDS_CARD
        if not flight or sid in commission_done:
            continue
        ce = asker_of(sid)
        who = ce["by"] if ce else None
        to = p.get("_to") or _owed_for(w, sid, who or "")
        words = p.get("_words") or f"live what this lands: {s['title']}"
        items.append({"form": "promise", "what": words, "to": to, "about": aid_of(w, sid), "card": sid,
                      "acts": [[ce["id"] if ce else None, "promise"]],
                      "why": f"commission {aid_of(w, sid)}: its asker's promise, owed to {to}"
                             + (", with its owe's words" if p.get("_words") else "")
                             + "".join(f"; folds in {c}'s owe" for c, _ in folded.get(sid, []))
                             + "".join(f"; retires due note {aid_of(w, n)}" for n in dues.get(sid, []))})
        for n in dues.pop(sid, []):
            steps.append(("retire-note", n, aid_of(w, sid)))
    for csid, notes in dues.items():         # due notes whose commission is no longer in flight (lived, or done)
        c = w.subjects.get(csid)
        if not c:
            continue
        ce = asker_of(csid)
        le = writer(w, csid, "lived")
        acts = [[ce["id"] if ce else None, "promise"]]
        if le and (c.get("props") or {}).get("lived"):
            acts.append([le["id"], "report", c["props"]["lived"]])
        items.append({"form": "promise", "what": f"live what this lands: {c['title']}", "about": aid_of(w, csid),
                      "to": _owed_for(w, csid, ce["by"] if ce else ""), "card": csid, "acts": acts,
                      "why": f"due note{'s' if len(notes) > 1 else ''} {', '.join(aid_of(w, n) for n in notes)} for "
                             f"{aid_of(w, csid)}: its asker's promise" + (", reported by its lived=" if len(acts) > 1 else "")})
        for n in notes:
            steps.append(("retire-note", n, aid_of(w, csid)))
    for card, eo, words, to, ea, eend, how in HISTORY:
        evs = events(w)
        if card in w.nodes and (evs.get(eo, {}).get("args") or {}).get("owe") == words and \
                (evs.get(ea, {}).get("args") or {}).get("awaiting") == to and eend in evs:
            items.append({"form": "ask", "what": words, "to": to, "about": card, "card": w.subject_of(card),
                          "acts": [[eo, "ask"], [eend, "confirm", how]],
                          "why": f"{card}'s earlier owe ({eo}) and awaiting={to} ({ea}): a request, closed as {how}"})
    for fid, n in w.nodes.items():           # the readers: views, lenses, rules, verbs that answer these words
        if n["type"] == "surface" and n.get("layout") == "view":
            q, cols = str(n.get("query") or ""), str(n.get("cols") or "")
            colset = [c.strip() for c in cols.split(",") if c.strip()]
            m = re.search(r"prop:awaiting=([\w-]+)", q)
            o = re.search(r"prop:owner=([\w-]+)", q)
            if m:
                steps.append(("view", fid, (f"kind:promise,asked-of:{m.group(1)}", "title,promise,about")))
            elif "owe" in colset and o:
                steps.append(("view", fid, (f"kind:promise,held-by:{o.group(1)}", "title,promise,about")))
            elif "awaiting" in colset or "owe" in colset:
                steps.append(("view", fid, (q, ",".join("asked_of" if c in ("awaiting", "owe") else c for c in colset))))
            if not m and ("prop:awaiting" in q or "prop:owe" in q):
                steps.append(("note", fid, f"view {fid} \"{n['title']}\": its selection {q} is left as it is, and "
                                           f"matches nothing once the props go; asked-of:<name> selects requests"))
    for sid, s in w.subjects.items():
        tags = s.get("tags") or []
        text = s.get("text") or ""
        if "lens" in tags and re.search(r"\$awaiting\b|prop:awaiting", text):
            new = re.sub(r"only when prop:awaiting(?![=\w])", "only when awaits:any", text)
            new = re.sub(r"prop:awaiting=([\w-]+)", r"awaits:\1", new).replace("$awaiting", "$asked_of")
            steps.append(("lens", sid, new))
        elif "rule" in tags and re.search(r"\bdue_for\b", text):
            steps.append(("retire-rule", sid, "a commission's promise does its job now (a1587)"))
        elif "verb" in tags and {x.strip().lower() for x in s["title"].split("|")} & set(VERBS):
            steps.append(("tell-verb", sid, s["title"]))
    return items, steps


def migrate(desk):
    """Once per world, at its first top-level line after landing: owe=, awaiting= and open due notes become
    promises and requests, the props go, and their readers read promises. One event by the house, said in history;
    undo takes all of it back (and it never runs again)."""
    w = desk.world
    if getattr(w, "_promises_version", 0) >= 1:
        return
    w._promises_version = 1
    items, steps = plan(w)
    if not items and not [s for s in steps if s[0] != "note"]:
        return
    import rooms
    rs = rooms.all_rooms(w)
    home = rs[0] if rs else w.root
    fid = surface(w)
    made_nodes, made_subjects, restore_s, restore_n = [], [], {}, {}
    if not fid:
        fid = w.add_surface("Promises", home, "column", 8, 8, 400, 300)
        w.nodes[fid]["props"] = {"role": "promises"}
        w.reflow(home)
        made_nodes.append(fid)
    ev = w._event("promises", fid, {}, {}, "house")
    mig = ev["id"]

    def keep_s(sid):
        if sid not in restore_s:
            restore_s[sid] = deepcopy(w.subjects[sid])

    said, per = [], {}
    for it in items:
        acts = [[mig if a[0] == "MIG" else a[0]] + a[1:] for a in it["acts"]]
        aid, _ = make(w, it["form"], it["what"], it["to"], it.get("about"), quiet=True, acts=acts)   # None: no event says who
        sid = w.nodes[aid]["subject"]
        made_nodes.append(aid)
        made_subjects.append(sid)
        st = state(w, sid)
        said.append(f"{aid} ({it['why']}): {phrase(w, st, {'pid': None, 'name': ''})}")
        for who in {label(w, st["maker"] or st["asker"]), label(w, st["asked"]) if st["asked"] else None, it.get("flag")}:
            if who and who != "unknown":
                per.setdefault(who, []).append((aid, st, it))
    for kind, ident, val in steps:
        if kind == "remove":
            if val in (w.subjects[ident].get("props") or {}):
                keep_s(ident)
                w.subjects[ident]["props"].pop(val)
                w.subjects[ident]["rev"] += 1
                said.append(f"{aid_of(w, ident)}: {val}= removed")
        elif kind == "retire-note":
            keep_s(ident)
            w.subjects[ident]["props"].update(status="done", next=f"now the asker's promise about {val} (a1587)")
            w.subjects[ident]["rev"] += 1
            said.append(f"{aid_of(w, ident)}: due note retired into the promise about {val}")
        elif kind == "view":
            restore_n.setdefault(ident, deepcopy(w.nodes[ident]))
            q, cols = val
            was = f"{w.nodes[ident].get('query')} as {w.nodes[ident].get('cols')}"
            w.nodes[ident]["query"], w.nodes[ident]["cols"] = q, cols
            w._bump(ident)
            said.append(f"view {ident} \"{w.nodes[ident]['title']}\": was {was}, now {q} as {cols}")
        elif kind == "lens":
            keep_s(ident)
            w.subjects[ident]["text"] = val
            w.subjects[ident]["rev"] += 1
            said.append(f"lens {aid_of(w, ident)} \"{w.subjects[ident]['title']}\": $awaiting reads $asked_of, prop:awaiting reads awaits:")
            per.setdefault(_maker(w, ident) or "", []).append((aid_of(w, ident), None, {"why": "your lens read awaiting=; it reads open requests now ($asked_of, awaits:any)"}))
        elif kind == "retire-rule":
            keep_s(ident)
            s = w.subjects[ident]
            s["tags"] = [t for t in s["tags"] if t != "rule"] + ["retired"]
            s["rev"] += 1
            said.append(f"rule {aid_of(w, ident)} \"{s['title']}\" retired (untagged rule, tagged retired): {val}")
        elif kind == "tell-verb":
            who = _maker(w, ident)
            said.append(f"world verb {aid_of(w, ident)} '{val}': the word is the house's now; use {aid_of(w, ident)} still runs it")
            per.setdefault(who or "", []).append((aid_of(w, ident), None, {"why": f"your verb '{val}' answers a word the house "
                                                  f"answers now ({', '.join(sorted(set(VERBS) & {x.strip().lower() for x in val.split('|')}))}); "
                                                  f"use {aid_of(w, ident)} still runs it, and it removed owe=, which nothing has now"}))
        elif kind == "note":
            said.append(val)
    asked = []
    for sid in made_subjects:            # (4): what the migration made about a card already gone asks its holder once
        st = state(w, sid)
        c = about_sid(w, st)
        if st["state"] == OPEN and c and not living(w, c):
            asked.append(st)
    for who, rows in per.items():
        f = sill(w, who)
        if not f or who in ("alex",):
            continue
        lines = [f"- {aid}: " + (f"\"{st['what'][:90]}\" · {phrase(w, st, _person(w, who))} · ({it['why']})" if st else it["why"])
                 + (f". You wrote this owe with awaiting= on the same card, so it is your request of them now; if it was "
                    f"your own promise instead, withdraw {aid} and promise to=<them> <words>" if it.get("flag") == who else "")
                 for aid, st, it in rows]
        sid = w.add_subject("note", "What the promises migration made of yours (a1587)",
                            "owe=, awaiting= and due notes are promises and requests now, things with their makers read "
                            f"from events ({mig}; help promises). Yours:\n" + "\n".join(lines))
        aid = w.place(sid, f, 8, 8, 300, 120)
        w._bump(f)
        made_nodes.append(aid)
        made_subjects.append(sid)
        said.append(f"told {who} on their sill ({aid})")
    for st in asked:
        holder = label(w, st["holder"])
        f = sill(w, holder)
        if not f:
            said.append(f"{st['aid']} is about {st['about']}, which has left the living; {holder} has no sill to be asked on")
            continue
        sid = w.add_subject("note", f"Kept, released or carried? {st['aid']} about {st['about']}",
                            f"{st['about']} has left the living, and your promise about it is still open (the migration "
                            f"{mig} found it):\n  {st['aid']} \"{st['what']}\"\nOne of these ends it, and this note with it:\n"
                            f"  kept: report {st['aid']} how=\"...\"\n  released: release {st['aid']} [why=\"...\"]\n"
                            f"  carried: carry {st['aid']} to=<name>")
        w.subjects[sid]["props"]["promise"] = st["aid"]
        aid = w.place(sid, f, 8, 8, 300, 120)
        w._bump(f)
        made_nodes.append(aid)
        made_subjects.append(sid)
        w.subjects[st["sid"]]["promise"]["acts"].append([mig, "asked-end"])
        said.append(f"{st['aid']}: its card {st['about']} has left the living; {holder} is asked once on their sill ({aid})")
    w.reflow(fid)
    n_p = sum(1 for i in items if i["form"] == "promise")
    ev["args"] = {"promises": n_p, "requests": len(items) - n_p, "steps": len(steps)}
    ev["undo"] = {"promises_migrate": {"nodes": made_nodes, "subjects": made_subjects,
                                       "restore_subjects": list(restore_s.values()), "restore_nodes": list(restore_n.values())}}
    ev["changed"] = [fid] + list(restore_s) + list(restore_n)
    ev["note"] = (f"a1587: owe=, awaiting= and open due notes became {n_p} promise(s) and {len(items) - n_p} request(s), "
                  f"each made by whoever wrote it (its event), and their readers read promises: " + "; ".join(said))


def _maker(w, sid):
    apps = set(w.appearances_of(sid))
    for e in w.events:
        if e["verb"] == "create" and not e.get("undone") and (e.get("undo") or {}).get("delete") in apps:
            return persons.norm(e["by"])
    return None


def unmigrate(w, u):
    """The undo of the migration: what it made goes, what it changed comes back. It does not run again."""
    for r in deepcopy(u.get("restore_subjects") or []):
        r["rev"] = w.subjects[r["id"]]["rev"] + 1 if r["id"] in w.subjects else r["rev"]
        w.subjects[r["id"]] = r
    for r in deepcopy(u.get("restore_nodes") or []):
        r["rev"] = w.nodes[r["id"]]["rev"] + 1 if r["id"] in w.nodes else r["rev"]
        w.nodes[r["id"]] = r
    parents = set()
    for nid in reversed(u.get("nodes") or []):
        n = w.nodes.pop(nid, None)
        if n and n.get("parent"):
            parents.add(n["parent"])
    for sid in u.get("subjects") or []:
        w.subjects.pop(sid, None)
    for p in parents:
        if p in w.nodes:
            w.reflow(p)
            w._bump(p)


# ---- printing helpers for the desk --------------------------------------------------------------------------------

COLS = ("promise", "asked_of", "holder", "owed")


def cell(w, sid, col):
    s = w.subjects.get(sid) or {}
    if col == "asked_of":
        if s.get("kind") == "promise":
            st = state(w, sid)
            return label(w, st["asked"]) if st["state"] == ASKED else ""
        return asked_of(w, sid)
    if s.get("kind") != "promise":
        return ""
    st = state(w, sid)
    if col == "promise":
        return phrase(w, st)
    if col == "holder":
        return label(w, st["holder"]) if st["holder"] else ""
    if col == "owed":
        return label(w, st["owed"] or st["asker"]) if (st["owed"] or st["asker"]) else ""
    return ""


HELP = """promises: a promise is a thing the house holds (a1587, design a1576): its words, whom it is owed to, and what it
is about. Who made it and who ended it are read from the events that did those things, never stored. It is open until
it ends one of three honest ways, each an act: kept (reported by its holder, confirmed by the one owed), released, or
carried to someone else. A request is not a promise: asking makes a request, held by the asker, and it becomes a
promise only when the one asked accepts it.
  promise to=<name> <words> [about=<id>]   a promise by you, owed to <name> (to=<you>: one you keep on your own word)
  ask to=<name> <words> [about=<id>]       a request of <name>; their lists say 'asked of you' until they answer
  accept <id> · decline <id>               the one asked answers (decline needs no reason)
  withdraw <id>                            the asker takes a request back
  report <id> [how=<words>]                its holder: done. 'reported, not confirmed' until the one owed confirms;
                                           owed to yourself, it is kept (your own word)
  confirm <id>                             the one owed: it was kept
  release <id> [why=<words>]               its holder lets it go; a reason is welcome, never required
  carry <id> to=<name>                     its holder hands it on; the new holder sees 'carried to you from X'
  promises                                 yours: asked of you, held, owed to you, reported to you, asked by you
Selections: held-by:<name> (open promises held), asked-of:<name> (open requests of), owed-to:<name> (open or reported,
owed to), asked-by:<name> (open requests made by), awaits:<name|any> (the things open requests are about). Columns
(table, a view's cols=): promise (how it reads to you), asked_of, holder, owed. A lens may print $asked_of of a card.
A commission is its asker's promise: commission=asked makes it (owed to asked_by, or the card's maker), and lived= on
the card is the asker's report. A card that leaves the living (done, trashed, cancelled, the Trash) with an open
promise about it asks the holder once, on their sill: kept, released or carried?
owe= and awaiting= are not props any more in a world with promises: their door is promise and ask."""
