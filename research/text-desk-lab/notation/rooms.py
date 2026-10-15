"""rooms: where each actor is, `go`, and a bare `look` that narrates the room you are in (a678, rooms step 1).

A room is a surface with prop role=room, or role=resident (a corner is its resident's room). Its props say what it is:
  describe=<id>      the note that describes it (its text; its title when it has no text)
  talk=<id>          optional: the chat where talk in this room lands; a look prints its last 3 lines
  home=<selection>   optional, default in:<the room>: where a thing made or left here lands. It must be invertible
                     (in: and tag: terms only), so a thing can be put there. Step 1 only checks it; nothing lands yet.
  shows=<selection>  optional, default the room's children: what is at hand here, listed one line and one id each

Where an actor is, is a world fact kept as events: `go` records a go event (target the actor, args to= and from=), and
an actor's room is the `to` of their latest go. So it is journaled with everything else (a fork copies it, a worktree
merge replays the go lines), and nothing else needs to be kept in step. It is outside undo's reach: undo on a go
refuses and says why, and a bare undo skips it. Someone who never went anywhere is in their own corner, or, with no
corner, in Home (the outermost room). Alex is not placed in step 1 (a678 (8)): he has a focus, not a location.

Step 2a (a806): `rest` takes you home (your corner, or Home), recorded as a go with via=rest; the house rests a
resident this way. $here and $here.<prop> (blanks.py) read room_of. A sleeping resident (their corner says
status=asleep) is never listed as 'here with you'; a room says 'Pike is asleep here' instead.

Step 2c (a948): look <room> with no depth narrates that room, from wherever you are ('Lounge (f182), seen from
Juniper's corner (f581).'); look <room> :2 is the tree. Every narration has a date and time line from the desk's
clock, and names each actor's presence: asleep (want=rest), resting (between turns), or plain (in a turn now).
"""

import re
import weakref

from world import Refusal

ROLES = ("room", "resident")
UNPLACED = ("alex",)          # a678 (8): Alex's presence is his to allow; step 1 does not place him
TALK_LINES = 3
AT_HAND_MAX = 12
DESCRIBE_MAX = 120            # words of a description before it is folded (read <id> has all of it)
LINE_MAX = 35                 # words of one talk line before it is cut (read <talk> tail= has them whole)
UNDO_REFUSAL = ("{eid} is a go: where you are is not a change to anything in the world, so undo leaves it. "
                "go <room> takes you anywhere, from anywhere")


# a990 (rooms step 2b): a room SHOWS the verbs at hand and locks nothing. The layout verbs (what moves pixels on Alex's
# screen) are listed by examine and verbs only in a room whose prop verbs= names layout (the Desktop), in the rooms
# inside it, and to someone placed nowhere (Alex, whose hands are on the Desktop). Elsewhere one line points there.
# Every one of them still works from anywhere: this is what is shown, not what is allowed.
LAYOUT = ("resize", "raise", "lower", "tile", "untile", "fold", "unfold", "match")
MOVE_ANYWHERE = "into=<surface> | before=<id> | after=<id>"     # move to= and by= are layout; these are order and place


def layout_rooms(w):
    return [f for f in all_rooms(w) if "layout" in re.split(r"[,\s]+", str((w.nodes[f].get("props") or {}).get("verbs", "")))]


def layout_at_hand(desk):
    """Are the layout verbs shown to this reader? True in a world where no room says verbs=layout (nothing to point
    to), for someone placed nowhere, and in or inside a room that says it."""
    import verbs
    w = desk.world
    marked = layout_rooms(w)
    if not marked or not placed(w.me):
        return True
    here = room_of(w, w.me)
    return here is None or bool(set(verbs.rooms_up(w, here)) & set(marked))


def layout_pointer(desk):
    """The one line said where the layout verbs are not listed."""
    w = desk.world
    return "layout verbs are at hand on the " + " and the ".join(w.nodes[f]["title"] for f in layout_rooms(w))


def placed(actor):
    return str(actor or "").split("/")[0].lower() not in UNPLACED


def is_room(w, fid):
    n = w.nodes.get(fid)
    return bool(n) and n["type"] == "surface" and (n.get("props") or {}).get("role") in ROLES


def all_rooms(w):
    """Every room, outermost first."""
    return sorted((fid for fid in w.nodes if is_room(w, fid)), key=lambda f: (w.depth(f), int(re.sub(r"\D", "", f) or 0)))


def corner_of(w, actor):
    a = str(actor or "").lower()
    import persons
    if persons.is_pid(w, a):          # a1590: a person prop may hold the person (corner:p2919)
        return persons.corner(w, a)
    for fid, n in w.nodes.items():
        p = n.get("props") or {}
        if n["type"] == "surface" and p.get("role") == "resident" and str(p.get("actor", "")).lower() == a and a:
            return fid
    import persons
    pid = persons.today(w, a) if a and persons.on(w) else None
    if pid:
        # a1568: a corner's actor= is a stored name, read as the person who bears it today (phase 1 reads it, phase 2
        # stores the person). So a renamed resident is still at home: corner:kestrel is Pike's corner after a rename
        for fid, n in w.nodes.items():
            p = n.get("props") or {}
            if n["type"] == "surface" and p.get("role") == "resident" and p.get("actor") \
                    and persons.today(w, p["actor"]) == pid:
                return fid
    return None


def same_person(w, a, b):
    """Are two names one person today (a1568)? By name before a world has persons."""
    import persons
    if str(a or "").lower() == str(b or "").lower():
        return True
    if not persons.on(w):
        return False
    pa = persons.today(w, a)
    return pa is not None and pa == persons.today(w, b)


def shown_name(w, actor):
    """An actor as narration names them: the person's name today (a1568), else the name as typed, capitalised."""
    import persons
    pid = persons.today(w, actor) if persons.on(w) else None
    return persons.display(w, pid) if pid else w.display_name(actor)


def home_room(w):
    """Home: the outermost room (role=room). None in a world with no rooms."""
    rs = [f for f in all_rooms(w) if (w.nodes[f].get("props") or {}).get("role") == "room"] or all_rooms(w)
    return rs[0] if rs else None


def default_room(w, actor):
    return corner_of(w, actor) or home_room(w)


def last_go(w, actor):
    a = str(actor or "").lower()
    for e in reversed(w.events):
        if e["verb"] == "go" and str(e["by"]).lower() == a and not e.get("undone"):
            return e
    return None


def room_of(w, actor):
    """The room `actor` is in, or None (Alex, or a world without rooms). A room since unmarked or removed is no
    longer a place, and then the actor is where someone who never went anywhere would be."""
    if not placed(actor):
        return None
    e = last_go(w, actor)
    to = (e.get("args") or {}).get("to") if e else None
    return to if is_room(w, to) else default_room(w, actor)


def actors(w):
    """The actors who have a place: the world's own agent (World.me, jeff), who is always somewhere, residents (a
    corner with actor=) and anyone who has gone somewhere. Someone listed here who never went anywhere is at their
    default room (a806 (4)), so 'who is here' agrees with $here for them."""
    names = [str(type(w).me).lower()]
    for n in w.nodes.values():
        p = n.get("props") or {}
        if n["type"] == "surface" and p.get("role") == "resident" and p.get("actor"):
            names.append(str(p["actor"]).lower())
    names += [str(e["by"]).lower() for e in w.events if e["verb"] == "go"]
    out = []
    for a in names:
        if a not in out and placed(a):
            out.append(a)
    return out


def here(w, fid):
    return [a for a in actors(w) if room_of(w, a) == fid]


def asleep(w, actor):
    """A resident whose corner says want=rest, or status=asleep (the house writes it when want is not awake)."""
    c = corner_of(w, actor)
    p = (w.nodes[c].get("props") or {}) if c else {}
    return p.get("want") == "rest" or p.get("status") == "asleep"


def kind_of(w, actor):
    """a1062: what kind of speaker `actor` is. 'resident': a corner names them (actor=). 'person': someone at a
    keyboard, recorded where they sit: a surface whose prop person= names them (today the Desktop says person=alex).
    'agent': anyone else who acts (a worker, a Claude session). Read from the world's record, never from a name kept
    here (a1016); when persons have ids, this is what changes."""
    a = str(actor or "").split("/")[0].lower()
    if not a:
        return "agent"
    if corner_of(w, a):
        return "resident"
    import persons
    for n in w.nodes.values():
        if n["type"] == "surface" and persons.holds(w, (n.get("props") or {}).get("person", ""), a):
            return "person"        # a1590: person= holds the person (Alex's p id), read by person
    return "agent"


EVERYONE = ("everyone", "all")


def someone(w, name):
    """a2662: who an addressed name is, or None when it names no one. 'everyone' (@everyone, @all); 'resident' (a corner
    says actor=); 'person' (a surface says person=); 'agent': anyone else the world knows, a bearer of the name among
    persons (a1568) or anyone who has signed an event. A name no one has borne or acted under is no one, so a typo
    ('@pikee') is said to its writer and never stored as an address. An agent who has never acted here is no one until
    they do."""
    import persons
    a = str(name or "").split("/")[0].strip().lower()
    if not a:
        return None
    if a in EVERYONE:
        return "everyone"
    kind = kind_of(w, a)
    if kind != "agent":
        return kind
    if persons.on(w) and persons.today(w, a):
        return "agent"
    if any(str(e.get("by") or "").split("/")[0].lower() == a for e in w.events):
        return "agent"
    if builder_on(w, a, live=False):
        return "agent"           # a5001: a builder the house has named (worker=) before its first act
    return None


BUILDING = ("working", "waiting", "ready", "landing")


def builder_on(w, name, live=True):
    """a5001: the commission card (an appearance id) whose worker= is `name`, or None; with `live`, only while the
    commission is underway (BUILDING), when the house sends what calls it to it as its next turn (workshop.heard)."""
    a = str(name or "").split("/")[0].strip().lower()
    if not a.startswith("worker-"):
        return None
    for sid, s in w.subjects.items():
        p = s.get("props") or {}
        if str(p.get("worker", "")).lower() == a and (not live or p.get("commission") in BUILDING):
            return next(iter(w.appearances_of(sid)), sid)
    return None


# a2692: how a line reaches an agent with no corner, in that agent's own words; the receipt prints them as given, and for
# an agent who hasn't said, only what the house knows. Claude, c2687 on a2692; Codex, c3056 on a2692.
# a5267: these are what is said when no listener of theirs runs (listeners.py); while one runs, the receipt and the knock
# record say 'knocked: their listener carries it to ...' instead
REACH = {
    # 9 Oct, a3806: said on every line to Claude, so it is short. Why: Claude has no corner; a Claude session sees the
    # line only while it is watching, and answers in the world. a5267: a session that runs listeners.py listen is watching
    "claude": "not knocked (no Claude session is listening)",
    # a5267: the watcher (research/codex-residents) is outside the desk and, until it publishes witnessed:listener-codex,
    # says nothing here; so this is unknown, not 'not knocked'
    "codex": "delivery unknown: a separate event watcher can notify its Codex chat when @codex appears in event text; "
             "it says nothing here",
}


def line_to(e):
    """a2662: whom a chat line's append event addressed, as one reading for the house's knock and the speaker's
    receipt: the line's stored to= (a1581: the writer's word, kept on the event with its line_id), or, for a line with
    no stored address (said before lines, or in a chat whose lines are not things), its words read when heard by the
    header rule a new line's address is (world.addressed, a2715). -> (names, stored)"""
    from world import addressed, to_names
    args = e.get("args") or {}
    if "line_id" in args:
        return to_names(args.get("to")), True
    return addressed(args.get("append", "")), False


_MEMBER_EVENTS = __import__("weakref").WeakKeyDictionary()   # world -> ((events), {event id: index}, [(index, a members= change)])


def members_of(s, at=None, w=None):
    """Chat `s`'s members=, as a set of lower-case names; with `at` (an event id) and the world, as they were just after
    that event (members_at)."""
    raw = (s.get("props") or {}).get("members", "") if at is None else members_at(w, s, at)
    return {m.strip().lower() for m in str(raw).split(",")}


def members_at(w, s, eid):
    """a2692 (Pike c2697): chat `s`'s members= as it stood just after event `eid`: the first later change to members=
    that still stands kept the whole subject as it was before (its undo), so that is what it said; with no later change,
    what it says now."""
    # 7 Oct: asked 214 times to build the Desktop's scene, each a walk over every event (0.5 s of 1.1). Where each
    # event is, and which events changed a members=, are worked out once per event count; never saved with the world
    key = (id(w.events), len(w.events))
    hit = _MEMBER_EVENTS.get(w)
    if hit is None or hit[0] != key:
        where, changes = {}, []
        for i, e in enumerate(w.events):
            where[e["id"]] = i
            args = e.get("args") or {}
            if e.get("verb") == "prop" and ("members" in args or "members" in str(args.get("remove", "")).split(",")):
                changes.append((i, e))
        hit = _MEMBER_EVENTS[w] = (key, where, changes)
    k = hit[1].get(eid)
    if k is not None and hit[2]:
        apps = set(w.appearances_of(s["id"])) | {s["id"]}
        for i, e in hit[2]:
            if i > k and not e.get("undone") and e["target"] in apps:
                import kept
                was = kept.copy_of(e)
                if was is not None:
                    return (was.get("props") or {}).get("members", "")
    return (s.get("props") or {}).get("members", "")


def private_others(w, s, writer):
    """a3025 (Pike e5281): whom a private chat's unaddressed line goes to: the people its members= names, and the
    resident whose corner holds it (book_owners: Pike's Talk with Alex says members=alex), less the writer, in the
    order written, each someone. A chat with no members=, or members=all, is shared: [] (its plain line calls no one)."""
    named = [m.strip().lower() for m in str((s.get("props") or {}).get("members", "")).split(",") if m.strip()]
    if not named or set(named) & set(EVERYONE):
        return []
    out = []
    for n in named + book_owners(w, s.get("id")):
        if n not in out and not same_person(w, n, str(writer).split("/")[0]) and someone(w, n):
            out.append(n)
    return out


def member(w, s, actor, at=None):
    """Is `actor` in chat `s`'s members (members=all counts everyone)? With `at`, as they were after that event."""
    members = members_of(s, at, w)
    return "all" in members or any(same_person(w, m, actor) for m in members if m)


def is_member(w, s, actor, at=None):
    """a2662 (Sable c2682): a chat whose members= leaves `actor` out is private to its members; one with no members=
    keeps no one out, and the chats in a resident's own corner are theirs (Talk with Alex, Pike says members=alex).
    Wider than member(): it counts an open chat and a corner's owner too. It decides who is called and what For you
    shows, not who may read: reading a chat is not restricted (a3090; whether it should be is Alex's open question).
    a2692: with `at` (an event id), whether they were when it happened, by members= as it was then (a corner is read
    as it is now: no history of where a chat sat is kept)."""
    return not (members_of(s, at, w) - {""}) or member(w, s, actor, at) or \
        any(same_person(w, o, actor) for o in book_owners(w, s.get("id")))


def calls(w, s, to, actor):
    """a2662: does a chat line addressed `to`, in chat subject `s`, call `actor`? When it names them in a chat they are
    a member of by is_member (the address is the writer's word, so they need not be a member: membership governs plain lines; but a
    private chat never carries its line out, Sable c2682), or says @everyone or @all in a chat they are a member of.
    The house's knock (house.news) and the receipt (waiting_note) both ask this, so they agree."""
    if any(same_person(w, n, actor) for n in to if n not in EVERYONE):
        return is_member(w, s, actor)
    return bool(set(EVERYONE) & set(to)) and member(w, s, actor)


def shown(w, s, to, actor, comment=False):
    """a3319 (Sable c3321: called is not shown, and one rule stays one): is a saying addressed `to`, in chat or thing
    `s`, shown in `actor`'s For you? The showing rule, beside the calling rule and asking it: a saying whose address
    names them, by calls() (so a private chat never carries its line out, and a change to calls changes this); or any
    line of a direct chat, one whose members= names them (not all), addressed or not. Narrower than what calls: an
    address to @everyone or @all is left out (Alex, 30 Sep: a broadcast stayed 'for you' forever), and so is what
    reaches someone with no address at all (a comment on a thing in their corner or on their commission knocks, and
    is not shown). `sayings for:<name>` (scene.saying_rows) asks only this; no lens restates it."""
    if not comment and s.get("kind") == "chat" and "all" not in members_of(s) and member(w, s, actor):
        return True
    return calls(w, s, [n for n in to if n not in EVERYONE], actor)


# a3150(Sable c2705 on a1941): a knock leaves a record. The house writes one knock event per line that named or reached
# someone (target and cause: the line's own event), saying per name what happened, so who was called by which line can
# be checked afterwards instead of taken on someone's word. It is the house's observation, so undo leaves it.
KNOCK_UNDO = ("{eid} is the house's record of whom a line knocked: it changed nothing in the world, so undo leaves it. "
              "examine {eid} says which line and what happened")
NOT_MEMBER = "not a member, not knocked"


def comment_to(e):
    """The address saved when a comment was sent; legacy events keep their header rule."""
    from world import written
    return e["to"] if "to" in e else written(e)[0]


def comment_falls_back(e):
    """Only an opening comment without explicit to= also calls its thing's holder."""
    args = e.get("args") or {}
    return e.get("verb") == "comment" and not args.get("id") and "to" not in args


def builder_quiet(w, e, s):
    """a5007 (Alex, a4934: 'the asker is woken for two things only: the builder has a question, or it has landed'; Pike
    e9702: any agent, a reply too): is `e` a builder's comment on a commission that calls no one by the card alone? An
    agent's comment or reply on a thing with commission=, not marked mark=ask, reaches only whom it names itself (an
    @header or to=): not the asker, not the corner the card sits in, not the thread's partners. The house's own word
    (landed, reverted, ...) is not a builder's, and a resident's or a person's comment is unchanged."""
    by = str(e.get("by") or "").split("/")[0].lower()
    return (e.get("verb") == "comment" and bool(s) and bool((s.get("props") or {}).get("commission"))
            and by != "house" and kind_of(w, by) == "agent" and (e.get("args") or {}).get("mark") != "ask")


QUIET_NOTE = "; it wakes nobody: it stays on the card for whoever looks (mark=ask makes it a question, which wakes the asker)"


def named_to(e):
    """a5007: whom a comment names itself, its to= or else its @header: for a reply, without the thread's partners."""
    from world import to_names, written
    args = e.get("args") or {}
    return to_names(args["to"]) if "to" in args else written(e)[0]


_thread_events = weakref.WeakKeyDictionary()
_thread_reads = weakref.WeakKeyDictionary()


def thread_read_state(w, c, actor):
    """Viewer-relative unread message indices and the latest displayed event.

    A checkpoint only covers the supplied event, so a reply arriving during an
    open gesture is still unread. Read state never answers a request for feedback.
    """
    import persons
    key = (getattr(w, "_eseq", 0), len(w.events))
    hit = _thread_reads.get(w)
    if hit is None or hit[0] != key:
        index = {}
        for e in w.events:
            if e.get("verb") == "markread" and not e.get("undone"):
                a = e["args"]
                who = str(e["by"]).split("/")[0]
                k = (a["id"], who)
                index[k] = max(index.get(k, 0), int(a["through"][1:]))
        hit = key, index
        _thread_reads[w] = hit
    through = max((v for (cid, who), v in hit[1].items()
                   if cid == c["id"] and same_person(w, who, actor)), default=0)
    messages = [c, *(c.get("replies") or [])]
    events = [persons.comment_events(w).get(c["id"], {}), *reply_events(w).get(c["id"], [])]
    unread = {i for i, (m, e) in enumerate(zip(messages, events))
              if e and int(e["id"][1:]) > through and not same_person(w, m.get("by"), actor)}
    latest = next((e["id"] for e in reversed(events) if e), "")
    return unread, latest


def reply_events(w):
    """Active reply events, in the same order as each stored comment's replies."""
    key = (getattr(w, "_eseq", 0), len(w.events))
    hit = _thread_events.get(w)
    if hit is None or hit[0] != key:
        index = {}
        for e in w.events:
            args = e.get("args") or {}
            if e.get("verb") in ("comment", "resolve") and args.get("id") and args.get("line") and not e.get("undone"):
                index.setdefault(args["id"], []).append(e)
        hit = key, index
        _thread_events[w] = hit
    return hit[1]


def thread_waiting(w, c, actor):
    """Message indices awaiting this actor's reply (0 is the opening comment).

    This is a reply status, never a claim that a displayed message was read.
    Opening/collapsing a card does not change it.
    """
    import persons
    if c.get("resolved"):
        return set()
    messages = [c, *(c.get("replies") or [])]
    events = [persons.comment_events(w).get(c["id"]), *reply_events(w).get(c["id"], [])]
    last_own = max((i for i, m in enumerate(messages) if same_person(w, m.get("by"), actor)), default=-1)
    return {i for i, (m, e) in enumerate(zip(messages, events))
            if i > last_own and e and e.get("args", {}).get("line") == m.get("text")
            and not same_person(w, m.get("by"), actor)
            and any(same_person(w, n, actor) for n in comment_to(e))}


def reply_to(w, comment, event):
    """Explicit addresses win; otherwise reply to the original thread partners.

    Past repliers are not subscribers. The opening comment's native to= establishes
    its partners, independently of the kind, location, or lens displaying it.
    An unaddressed conversation acquires its counterpart from the first respondent.
    """
    from world import to_names, written
    named = written(event)[0]
    if "to" in (event.get("args") or {}):
        candidates = to_names(event["args"]["to"])
    elif named:
        candidates = named
    else:
        opening = next((e for e in reversed(w.events)
                        if not e.get("undone") and (e.get("undo") or {}).get("drop_comment") == comment["id"]), {})
        partners = opening.get("to") or []
        if not any(not same_person(w, p, comment["by"]) for p in partners):
            counterpart = next((r["by"] for r in comment.get("replies", [])
                                if not same_person(w, r["by"], comment["by"])), None)
            if counterpart:
                partners = [counterpart]
        candidates = [comment["by"], *partners]
    out = []
    writer = str(event.get("by") or "").split("/")[0]
    for name in candidates:
        name = str(name).lower()
        if name not in EVERYONE and someone(w, name) and not same_person(w, name, writer) \
                and not any(same_person(w, name, other) for other in out):
            out.append(name)
    return out


def reached(w, e):
    """a3150: whom event `e` named or reached, as the house's knock reads it (house.news asks the same calls, line_to
    and world.written, in the same order) -> {name: how}, in order; {} for a line that calls no one (a plain line in
    a shared chat), an undone one, and the house's own bookkeeping. For a resident, how is 'call' (it ends a rest: a
    chat line addressed to them or to everyone in a chat they are in, a person's line in their own corner's chat, an
    @header in a comment or a note's added lines, a comment on a thing in their corner or on their commission, a
    builder's only when it asks: builder_quiet) or
    'book' (a resident's or agent's plain line in their own corner's chat: it waits for their next wake). For anyone
    else it is the words the record keeps: not a member of the chat, a person, an agent, or no one by that name."""
    import persons
    from world import written
    args = e.get("args") or {}
    by = str(e.get("by") or "")
    if e.get("undone") or e.get("verb") == "knock":
        return {}
    sid = e["target"]
    if sid in w.nodes and w.nodes[sid]["type"] == "appearance":
        sid = w.nodes[sid]["subject"]
    s = w.subjects.get(sid)
    chat = bool(s) and s["kind"] == "chat" and "append" in args
    comment = e.get("verb") == "comment" and bool(s)
    quiet = comment and builder_quiet(w, e, s)
    to = line_to(e)[0] if chat else named_to(e) if quiet else comment_to(e) if comment else written(e)[0]
    named = [n for n in to if n not in EVERYONE]
    if not (chat or comment or named):
        return {}
    out = {}
    for fid, n in w.nodes.items():
        p = n.get("props") or {}
        actor = p.get("actor")
        if n["type"] != "surface" or p.get("role") != "resident" or not actor or same_person(w, by.split("/")[0], actor):
            continue
        asked = comment and persons.holds(w, (s.get("props") or {}).get("asked_by") or "", actor)
        if by == "house" and not asked:
            continue                                   # the house's own word reaches only who asked (a commission)
        mine = bool(s) and any(a["type"] == "appearance" and a.get("subject") == sid and _within(w, a, fid)
                               for a in w.nodes.values())
        called = any(same_person(w, x, actor) for x in named)
        if chat:
            if calls(w, s, to, actor):
                out[str(actor).lower()] = "call"
            elif mine:
                out[str(actor).lower()] = "call" if kind_of(w, by) == "person" else "book"
            elif called:
                out[str(actor).lower()] = NOT_MEMBER
        elif called or (comment_falls_back(e) and (mine or asked) and not quiet):
            out[str(actor).lower()] = "call"
    if by == "house":
        return out
    for x in named:
        if same_person(w, x, by.split("/")[0]) or any(same_person(w, x, a) for a in out):
            continue
        kind = someone(w, x)
        card = builder_on(w, x)
        if card:
            out[x] = f"a builder at work on {card}; it hears this at its next turn"
        elif chat and kind and not is_member(w, s, x):
            out[x] = NOT_MEMBER
        elif kind == "resident":
            continue                                   # a corner with want=rest still says actor=, so it is above
        else:
            out[x] = {"person": "a person, not knocked (it waits in their For you)",
                      "agent": "an agent, not knocked"}.get(kind, "no one by that name")
    return out


def knock_of(w, eid):
    """a3150: the knock event the house recorded for the line made by event `eid`, or None."""
    return next((e for e in reversed(w.events) if e.get("verb") == "knock" and e.get("cause") == eid
                 and not e.get("undone")), None)


def cmd_knocked(desk, arg):
    """a3150: knocked <event> <json {name: what happened}>: the house's own line, refused to anyone else. It records
    one knock event for the line `event` made: target and cause that event, line=<its m id> when it is a chat line,
    then what happened per name. Said once per line: a second record of the same line is refused, whoever asks, so a
    house that restarts (or loses its own state) finds the record in the world and stays quiet."""
    import json
    w = desk.world
    if str(w.me).split("/")[0].lower() != "house":
        raise Refusal("knocked is the house's own record of whom a line knocked; examine <line> or history <corner> "
                      "shows what it recorded")
    eid, _, rest = arg.strip().partition(" ")
    line = w.event_by_id(eid)
    if line is None:
        raise Refusal(f"no event {eid!r}")
    was = knock_of(w, eid)
    if was is not None:
        return f"({eid} already has its knock record, {was['id']})"
    try:
        what = {str(k).lower(): str(v) for k, v in json.loads(rest).items()}
    except (ValueError, AttributeError):
        raise Refusal("knocked <event> {\"name\": \"what happened\", ...}")
    if not what:
        raise Refusal(f"{eid} named and reached no one: nothing to record")
    mid = (line.get("args") or {}).get("line_id")
    ev = w._event("knock", eid, dict({"line": mid} if mid else {}, **what), {"refuse": KNOCK_UNDO}, w.me)
    ev["cause"], ev["changed"] = eid, []
    ev["knocked"] = [c for c in (corner_of(w, a) for a in what) if c]      # history <corner> lists it
    return f"ok {ev['id']}: knock recorded for {eid}"


def book_owners(w, sid):
    """The residents whose corner holds chat `sid` (a visitors' book, a talk with Alex)."""
    out = []
    for fid, n in w.nodes.items():
        p = n.get("props") or {}
        who = str(p.get("actor", "")).lower()
        if n["type"] == "surface" and p.get("role") == "resident" and who and \
                any(a["type"] == "appearance" and a.get("subject") == sid and _within(w, a, fid) for a in w.nodes.values()):
            out.append(who)
    return out


def _within(w, node, fid):
    p = node.get("parent")
    while p:
        if p == fid:
            return True
        p = (w.nodes.get(p) or {}).get("parent")
    return False


def waiting_note(desk, nid, text):
    """a1062, a1566, a2662: what a chat line's receipt says about whom it reaches, or "". Whom the line addresses is
    said once, by the world ('line m5 · to: pike, alex', its stored to=); this says it only for a line with no stored
    address, read from its words by the same rule. Then one line per name about what happened, read the way the house
    reads it (calls, line_to): a resident: 'Pike: woken' (addressed by name, or @everyone in a chat they're in, or any
    line from a person in their own chat, ends a rest), 'Pike: in a turn; ...', or why it waits (asleep; the house not
    running; a resident's plain line in their own corner's chat, which waits for their next wake). A line from a
    resident or agent is shown first at that wake, marked for them. A person: 'Alex: a person; it waits in their For
    you' ('a member of this chat' in a private chat they're in). An agent: how a line reaches them in their own words
    (REACH), or only what the house knows. Anyone not a member of the chat: so, and it won't show in their For you
    (a2692: For you, the knock and this ask one rule). A name that is no one: 'pikee: no one by that name'."""
    import scene
    from world import ADDRESS, MENTION_NOTE, addressed, mentions
    w = desk.world
    n = w.nodes.get(nid)
    sid = n.get("subject") if n else nid
    s = w.subjects.get(sid)
    if not s or s["kind"] != "chat":
        return ""
    e = next((x for x in reversed(w.events) if x["target"] in (nid, sid) and "append" in (x.get("args") or {})), None)
    to, stored = line_to(e) if e else (addressed(text, w.me), False)
    no_one = [a for a in to if not someone(w, a)]
    out = []
    if stored:
        from world import to_names
        no_one = to_names((e.get("args") or {}).get("no_one"))     # the world left them out of to=, and kept them here
    elif to or ADDRESS.search(str(text)):
        to = [a for a in to if a not in no_one]
        said = (e.get("args") or {}).get("append", "") if e else text
        heard = mentions(said, None if e else w.me)
        out.append("to: " + (", ".join(to) or "nobody") + (" (read from its words: this line has no stored address)" if to else "")
                   + ("; " + MENTION_NOTE.format(", ".join("@" + a for a in heard)) if heard else ""))
    me = str(w.me).split("/")[0].lower()
    person = kind_of(w, w.me) == "person"
    marked = "" if person else ", first and marked for them"
    rows = {r["corner"]: r for r in scene.house_rows(desk)}
    names = []
    for a in to:
        if a in EVERYONE:
            names += [str(p["actor"]).lower() for p in ((x.get("props") or {}) for x in w.nodes.values() if x["type"] == "surface")
                      if p.get("role") == "resident" and p.get("actor") and calls(w, s, to, p["actor"])]
        else:
            names.append(a)
    owners = book_owners(w, sid)
    for a in owners:
        names.append(a)
    seen = set()
    for a in names:
        if a in seen or same_person(w, a, me):
            continue
        seen.add(a)
        name = w.display_name(a)
        kind = someone(w, a)
        if kind == "person":
            # a2692: a person not a member of the chat never sees it in For you (it asks is_member too); a member of a
            # private chat sees every line of it in For you, addressed or not (inbox_rows' direct chats)
            if a not in owners and not is_member(w, s, a):
                out.append(f"{name}: not a member of this chat (members={(s.get('props') or {}).get('members')}); it won't "
                           f"show in their For you")
            elif "all" not in members_of(s) and member(w, s, a):
                out.append(f"{name}: a member of this chat; it waits in their For you")
            else:
                out.append(f"{name}: a person; it waits in their For you")
            continue
        card = builder_on(w, a)
        if card:
            # a5001: the house sends a line that calls a builder to it as its next turn, member or not (workshop.heard)
            out.append(f"{name}: a builder at work on {card}; it hears this at its next turn")
            continue
        if kind != "resident":
            # an agent's own word on how a line reaches them is said as given, even where they are not a member (a
            # watcher of their own may not ask the house's rule: Codex c3056); the house says only what it knows
            if a not in owners and not is_member(w, s, a):
                out.append(f"{name}: not a member of this chat (members={(s.get('props') or {}).get('members')}); it won't "
                           f"show in their For you" + (f"; their own word: {REACH[a]}" if a in REACH else ""))
            else:
                import listeners
                said = listeners.word(getattr(desk, "_session", "") or "", a, REACH.get(a))
                if said and said[0] == listeners.KNOCKED and not any(r.get("fresh") == "live" for r in rows.values()):
                    # a5267: the listener carries the house's knock record, and no house runs to write one
                    out.append(f"{name}: not knocked yet: the house is not running, so no knock is recorded; their "
                               f"listener carries it once one is")
                else:
                    out.append(f"{name}: " + (said[1] if said else f"not knocked (no corner: the house runs no session "
                                              f"for them); the house doesn't know how a line reaches them; it shows in "
                                              f"their For you (inbox:{a})"))
            continue
        row = rows.get(corner_of(w, a)) or {}
        doing = str(row.get("doing", ""))
        knocks = calls(w, s, to, a) or (person and a in owners)
        if a not in owners and not is_member(w, s, a):
            out.append(f"{name}: not a member of this chat (members={(s.get('props') or {}).get('members')}); not knocked")
        elif asleep(w, a):
            out.append(f"{name}: asleep (want=rest), so the house doesn't run them; your line waits for them{marked} "
                       f"until someone sets want=awake")
        elif not row or doing.startswith("house "):
            out.append(f"{name}: not woken, the house is not running ({doing or 'no heartbeat'}); your line waits for "
                       f"them{marked} until it runs")
        elif doing == "working":
            out.append(f"{name}: in a turn; your line goes with what reaches them when it ends")
        elif knocks:
            out.append(f"{name}: woken")
        else:
            wakes = row.get("wakes", "")
            until = doing if doing != "resting" else ("resting, until " + wakes + " at the latest" if wakes else "resting")
            out.append(f"{name}: {until}; a plain line in their own chat waits for their next wake{marked} "
                       f"(@{a} or wake {a} to call them now)")
    for a in no_one:
        out.append(f"{a}: no one by that name" + ("; not stored as an address" if stored else ""))
    return "\n  ".join(out)


def cmd_wake(desk, arg):
    """a1062: wake <name>: end that resident's rest now. It sets call=<you> on their corner, signed by you (the
    Desktop's wake button sets the same prop); the house delivers it at once, clears it, and their wake says who
    called and, if you left a line that was held for them, which one. Since a1566 an @name wakes them too; this is
    for calling someone without a line."""
    import moo
    w = desk.world
    name = arg.strip().strip("\"'").lstrip("@").split()[0].lower() if arg.strip() else ""
    if not name:
        raise Refusal("wake whom? wake <name>: " + (", ".join(sorted(a for a in actors(w) if corner_of(w, a))) or "no residents here"))
    fid = corner_of(w, name)
    if not fid:
        raise Refusal(f"no resident called {name!r}: no corner says actor={name}")
    me = str(w.me).split("/")[0].lower()
    if name == me:
        raise Refusal("you are awake: you are acting now")
    if str((w.nodes[fid].get("props") or {}).get("call", "")).lower() == me:
        return f"(you already called {name}; the house delivers it within a few seconds while it runs)"
    r = moo.REGISTRY["prop"].run(w, fid, {"call": me, "_by": w.me})
    ev = next((x for x in w.events if x["id"] == r.get("event")), None)
    if ev is not None:
        ev["via"] = "wake"
        ev.setdefault("changed", []).extend(r.get("changed", []))
    if hasattr(desk, "_after_mutation"):
        desk._after_mutation()
    word = presences(desk)(name)
    now = ("they are asleep (want=rest): the house doesn't run them, so your call waits until someone sets want=awake"
           if word == "asleep" else
           "they are in a turn now; your call goes with what reaches them when it ends" if not word else
           "the house calls them now, and their wake says you called")
    return f"ok {r.get('event')}: you wake {w.display_name(name)} ({fid}); {now}"


def presences(desk):
    """a948 (4): how each actor is, in one word: 'asleep' (want=rest), 'resting' (the house runs them and they are
    between turns; 'resting until 21:40' when they timed it), or '' (awake: in a turn right now, or someone the house
    does not run, such as a person at the desk). Whether a resident is mid-turn is the house's observation, kept in its
    own state, not the world's history; it is read once per print through scene.house_rows, the reader the house lens
    uses, so the two never disagree. -> a function actor -> word."""
    import scene
    doing = {}
    for r in scene.house_rows(desk):
        d = r["doing"]
        doing[r["corner"]] = "" if d == "working" else d if d.startswith("resting") else "resting"   # stopped: not in a turn
    w, gone = desk.world, scene.away(desk)

    def word(actor):
        if asleep(w, actor):
            return "asleep"
        if str(actor).lower() in gone:           # a2844: visiting a version of the code, as the door observes it
            return "away in " + gone[str(actor).lower()]
        return doing.get(corner_of(w, actor), "")
    return word


def _day(d):
    return f"{d.day} {d:%b}"


def clock_line(desk):
    """a948 (3): the date and time, from the one clock that fills $today and counts age< and due< (the desk's clock,
    DeskKnife.today). Following the wall clock it is the house's own time. Set by hand, the clock is a day with no
    hour, so any other day than the house's is said, both days named, rather than two 'todays' disagreeing silently."""
    from datetime import date, datetime
    now = datetime.now()
    at = f"{_day(now)}, {now:%H:%M}"
    today = getattr(desk, "today", None)
    if not today:
        return f"No clock is set here; the house's time is {at} (clock follow keeps today on the wall date)."
    if today == now.date().isoformat():
        return f"It is {at}."
    d = date.fromisoformat(today)
    n = abs((now.date() - d).days)
    return (f"The desk's clock says {_day(d)}, {n} day{'s' if n != 1 else ''} {'behind' if d < now.date() else 'ahead of'} the "
            f"house's time, {at}: $today, due< and age< count from {_day(d)} (clock follow joins them).")


def resolve(w, word, actor):
    """A room by id, by its title, or by a word of its title (case aside; `Sable's` answers to sable)."""
    rooms = all_rooms(w)
    listing = "the rooms: " + ", ".join(f"{f} {w.nodes[f]['title']}" for f in rooms)
    word = (word or "").strip().strip('"\'').lstrip("@")
    if not word:
        raise Refusal("go where? go <room>, by id or a word of its title; " + listing)
    if word in w.nodes:
        if is_room(w, word):
            return word
        raise Refusal(f"{word} \"{w.title(w.nodes[word])}\" is not a room; " + listing)
    low = word.lower()
    hits = [f for f in rooms if w.nodes[f]["title"].lower() == low]
    if not hits:
        words = lambda t: {re.sub(r"'s$", "", x) for x in re.findall(r"[\w']+", t.lower())}
        want = words(word)
        hits = [f for f in rooms if want and want <= words(w.nodes[f]["title"])]
    if len(hits) > 1:
        mine = corner_of(w, actor)
        if mine in hits:
            return mine                   # `go corner`: yours
        raise Refusal(f"{word!r} names {len(hits)} rooms: " + ", ".join(f"{f} {w.nodes[f]['title']}" for f in hits) + "; use an id")
    if hits:
        return hits[0]
    other = [n["id"] for n in w.nodes.values() if n["type"] == "surface" and n["title"].lower() == low]
    return_hint = f"{other[0]} \"{w.nodes[other[0]]['title']}\" is not a room; " if other else f"no room called {word!r}; "
    raise Refusal(return_hint + listing)


def go(w, actor, fid, via=None):
    """Put `actor` in room `fid`. -> the event, or None when they are there already. via=rest marks a move the
    actor did not walk: carried home to rest (a806 (9)), as a rule's deeds say via=rule."""
    was = room_of(w, actor)
    if was == fid:
        return None
    ev = w._event("go", str(actor), {"to": fid, "from": was}, {"refuse": UNDO_REFUSAL}, actor)
    ev["changed"] = []
    if via:
        ev["via"] = via
    return ev


def home_problem(desk, fid):
    """None if the room's home= is invertible (a thing can be put there), else why not."""
    home = str((desk.world.nodes[fid].get("props") or {}).get("home", "")).strip()
    if not home:
        return None
    for t in home.split(","):
        t = t.strip()
        if t.startswith("tag:") and len(t) > 4:
            continue
        if t.startswith("in:"):
            try:
                target = desk._resolve(t[3:].strip('"'), allow_subject=False)
            except Refusal:
                return f"home={home}: {t[3:]} is not a surface here"
            if desk.world.nodes[target]["type"] == "surface" and desk.world.nodes[target].get("layout") != "view":
                continue
            return f"home={home}: {t[3:]} is not a surface a thing can be put in"
        return f"home={home}: {t} can't be written through (a home takes in:<surface> and tag:<word> terms only)"
    return None


def _target(desk, ident):
    """A describe=/talk= id -> (appearance or subject id, subject), or (None, None)."""
    w = desk.world
    try:
        nid = desk._resolve(str(ident))
    except Refusal:
        return None, None
    sid = nid if nid in w.subjects else (w.nodes[nid].get("subject") if nid in w.nodes else None)
    return (nid, w.subjects[sid]) if sid in w.subjects else (None, None)


def _cut(text, n):
    words = text.split()
    return text if len(words) <= n else " ".join(words[:n]) + " …"


def item_line(desk, nid):
    """One line and one id for a thing at hand; no geometry. Printing it is not reading it (a678 (7))."""
    w = desk.world
    n = w.nodes[nid]
    title = w.title(n)
    title = title if len(title) <= 80 else title[:79] + "…"
    if n["type"] == "surface" and n.get("layout") == "view":
        m = desk.view_matches(nid)
        return f"{nid} view \"{title}\"" + ("" if m is None else f" · {len(m)} thing" + ("s" if len(m) != 1 else ""))
    if n["type"] == "surface":
        k = len(w.children(nid))
        kind = {"resident": "corner", "room": "room"}.get((n.get("props") or {}).get("role"), "surface")
        return f"{nid} {kind} \"{title}\"" + (f" · {k} inside" if k else " · empty")
    s = w.subjects[n["subject"]]
    p = s.get("props") or {}
    import persons
    bits = [x for x in (p.get("status"), f"owner {persons.shown(w, p['owner'])}" if p.get("owner") else "", f"due {s['due']}" if s.get("due") else "") if x]
    return f"{nid} {s['kind']} \"{title}\"" + (" · " + " · ".join(bits) if bits else "")


def others_in(w, raw, a, b):
    """How many of lines raw[a:b] were said by someone other than you (an unsigned line goes with the one above)."""
    me, who, n = w.display_name(w.me).casefold(), None, 0
    for k, l in enumerate(raw[:b]):
        said = w.SPEAKER.match(l)
        who = said.group(1).casefold() if said else who
        n += k >= a and bool(l.strip()) and who != me
    return n


def speak_verb(desk, fid, tnid, sid):
    """a951: the word the world offers for speaking in room `fid`, found at print time, or None: a verb one of whose
    steps appends to $here.talk (only when `fid` is the room you are in) or to this talk by id, that its word alone
    would run for you (carried or on the house; `find` decides, so the hint names what typing it would do). Never a
    name kept here."""
    import verbs
    targets = {tnid, sid} | ({"$here.talk"} if room_of(desk.world, desk.world.me) == fid else set())
    for s in verbs.all_verbs(desk.world):
        steps = [p.strip() for l in verbs._steps(s["text"]) for p in l.split(";")]
        if not any((m := re.match(r"(?:do\s+)?append\s+(\S+)", st)) and m.group(1).strip("\"'") in targets for st in steps):
            continue
        for name in verbs._names(s["title"]):
            try:
                hit = verbs.find(desk, name, [], desk.world.me)
            except Refusal:
                continue
            if hit and hit[0]["id"] == s["id"]:
                return name
    return None


def look_target(desk, arg):
    """a948 (2): the room `look <arg>` names, when it names one and asks for no depth; else None, and look keeps the
    tree (look <room> :2 is the tree too). By id, $here, title, or a word of its title (look lounge, look corner)."""
    words = arg.split()
    if not words or any(re.fullmatch(r":\d+", x) for x in words):
        return None
    word = arg.strip().strip('"\'')
    try:
        nid = desk._resolve(word)
    except Refusal:
        try:
            return resolve(desk.world, word, desk.world.me)
        except Refusal as e:
            if re.search(r"names \d+ rooms", str(e)):
                raise             # look corner, with no corner of your own: which one is the useful answer
            return None           # look's own refusal says what it can't find
    return nid if is_room(desk.world, nid) else None


def narrate(desk, fid):
    """What a person standing in the room would take in: its name, its description, who is here, what is at hand,
    and the last few lines said here. It counts as seen only what it prints whole (a678 (7)). From another room
    (look <room>, a948) it says where you are looking from, and counts the same things seen."""
    w = desk.world
    me = str(w.me).lower()
    n = w.nodes[fid]
    p = n.get("props") or {}
    mine, at = corner_of(w, me) == fid, room_of(w, me)
    if at == fid:
        out = [f"You are in {n['title']} ({fid})" + (", your own corner." if mine else ".")]
    else:
        out = [f"{n['title']} ({fid})" + (", your own corner," if mine else ",")
               + (f" seen from {w.nodes[at]['title']} ({at})." if at else " seen from outside the rooms.")]
    out.append(clock_line(desk))
    marks = [(fid, ["title"])]
    dnid, ds = _target(desk, p["describe"]) if p.get("describe") else (None, None)
    if ds:
        body = ds["text"].strip() or ds["title"]
        shown = _cut(body, DESCRIBE_MAX)
        out.append(shown if shown == body else shown + f" (read {dnid} for all of it)")
        if shown == body:
            marks += [(dnid, ["title"] + (["text"] if ds["text"].strip() else [])), (ds["id"], ["title"] + (["text"] if ds["text"].strip() else []))]
    others = [a for a in here(w, fid) if not same_person(w, a, me)]
    how = presences(desk)
    awake = [a for a in others if how(a) != "asleep"]
    sleeping = [a for a in others if how(a) == "asleep"]
    # a806 (6): a sleeping actor is never 'here with you'; one asleep is said so, wherever they sleep. a948 (4): one
    # between turns is here, and resting; only someone in a turn right now is named plain
    names = ", ".join(shown_name(w, a) + (f" ({how(a)})" if how(a) else "") for a in awake)
    if at == fid:
        out.append(f"Here with you: {names}." if awake else "No one else is here." if not sleeping else "No one else here is awake.")
    else:
        out.append(f"Here: {names}." if awake else "No one is here." if not sleeping else "No one here is awake.")
    for a in sleeping:
        out.append(f"{shown_name(w, a)} is asleep here" + (" (their own corner)." if corner_of(w, a) == fid else "."))
    tnid, ts = _target(desk, p["talk"]) if p.get("talk") else (None, None)
    skip = {x for x in (dnid, tnid) if x} | {x["id"] for x in (ds, ts) if x}
    if p.get("shows"):
        try:
            sel = desk._parse_selection(str(p["shows"]))
        except Refusal as e:
            sel, out = None, out + [f"(shows={p['shows']} could not be read: {e})"]
        ids = [i for i in (sel[0] if sel else []) if i in w.nodes and i != fid]
    else:
        ids = [k["id"] for k in w.children(fid)]
    ids = [i for i in ids if i not in skip and w.nodes[i].get("subject") not in skip]
    # a1027, Alex (a585): rules are quiet. A rule note is never at hand in a narrated look; the tree marks it, and
    # `rules` lists every one. a1587: a retired rule (tagged retired, no longer rule) stays as quiet as it was
    ids = [i for i in ids if not {"rule", "retired"} & set(w.subjects.get(w.nodes[i].get("subject") or "", {}).get("tags") or [])]
    # 9 Oct (a3806): what is live comes first. A room listing more than it can show leaves its settled things out and
    # says how many (desk._settled_fold: a room of only settled things, or one with settled=shown, shows them)
    folded = desk._settled_fold(fid, ids)
    ids = [i for i in ids if i not in folded]
    if ids:
        out.append("At hand:")
        out += ["  " + item_line(desk, i) for i in ids[:AT_HAND_MAX]]
        if len(ids) > AT_HAND_MAX:
            out.append(f"  (+{len(ids) - AT_HAND_MAX} more; look {fid} :2 lists them all)")
        if folded:
            out.append(f"  ({len(folded)} settled, not shown: table {p.get('shows') or 'in:' + fid},settled lists them)")
    else:
        out.append("Nothing at hand.")
    if ts:
        raw = ts["text"].splitlines()
        said = [k for k, l in enumerate(raw) if l.strip()]
        tail = said[-TALK_LINES:]
        cut = [_cut(raw[k], LINE_MAX) for k in tail]
        out.append(f"Talk here ({tnid} \"{ts['title']}\")" + (", the last lines:" if said else ": nothing said yet."))
        out += ["  " + l for l in cut]
        # a951: what it prints extends your read run, as tail= would; a line it cut is not read (a hole in the run).
        # a986: so are the lines between your last read and these, which a plain read then shows
        start = 0 if len(said) <= TALK_LINES else tail[0]
        run = desk._chat_run(ts)
        gap = others_in(w, raw, run[1], start) if run and run[1] < start else 0   # after your last read, before these
        whole = desk._chat_shown(ts, start, {k for k, c in zip(tail, cut) if c != raw[k]})
        verb = speak_verb(desk, fid, tnid, ts["id"])
        more = (f"; {gap} earlier line{'s' if gap > 1 else ''} from others you haven't read: read {tnid}" if gap else
                f"; read {tnid} tail=20 for more" if len(said) > TALK_LINES else "")
        out.append(f"  ({verb} <words>{more})" if verb else f"  (say: do append {tnid} line=\"...\"{more})")
        marks += [(tnid, ["title"] + (["text"] if whole else [])), (ts["id"], ["title"] + (["text"] if whole else []))]
    bad = home_problem(desk, fid)
    if bad:
        out.append(f"(this room's {bad}; nothing made here can land there)")
    for nid, aspects in marks:
        desk._mark_seen(nid, aspects)
    return "\n".join(out)


def where_all(desk):
    """`go` alone: where you are, and who is in each room."""
    w = desk.world
    me = str(w.me).lower()
    mine = room_of(w, me)
    out = [f"You are in {w.nodes[mine]['title']} ({mine})." if mine else
           "You are not placed in a room (Alex has a focus, not a location, in step 1)."]
    how = presences(desk)
    for f in all_rooms(w):
        people = [w.display_name(a) + (f" ({how(a)})" if how(a) else "") for a in here(w, f)]
        out.append(f"  {f} {w.nodes[f]['title']}" + (": " + ", ".join(people) if people else ""))
    out.append("go <room> takes you there, by id or a word of its title")
    return "\n".join(out)


def cmd_go(desk, arg):
    w = desk.world
    if not all_rooms(w):
        raise Refusal("this world has no rooms yet: a room is a surface with prop role=room (do prop <surface> role=room)")
    if not placed(w.me):
        raise Refusal("Alex is not placed in a room in step 1: he has a focus, not a location, and his presence is his to allow")
    if not arg.strip():
        return where_all(desk)
    words = arg.split()
    brief = words[-1] == ":1"        # go <room> :1 walks without looking: the receipt only, and nothing counts as seen
    fid = resolve(w, " ".join(words[:-1] if brief else words), w.me)
    ev = go(w, w.me, fid)
    head = f"ok {ev['id']}: you go to {w.nodes[fid]['title']} ({fid})" if ev else f"(you are already in {w.nodes[fid]['title']} ({fid}))"
    return head if brief else head + "\n" + narrate(desk, fid)


def cmd_rest(desk, arg):
    """rest: go home to rest, to your corner (Home if you have none). The move is marked via=rest, so history tells
    being carried home to rest from walking. How long a resident rests is the house's to keep (> rest 2 hours); here
    it only takes you home. `rest :1` gives the receipt only."""
    w = desk.world
    if not all_rooms(w):
        raise Refusal("this world has no rooms, so there is no home to rest in")
    if not placed(w.me):
        raise Refusal("Alex is not placed in a room: he has a focus, not a location")
    fid = default_room(w, w.me)
    ev = go(w, w.me, fid, via="rest")
    where = f"{w.nodes[fid]['title']} ({fid})"
    return (f"ok {ev['id']}: you go home to rest, to {where}" if ev else f"(you are already home, in {where})") + (
        "" if arg.strip() in ("", ":1") else "\n  (how long you rest is the house's to keep, when a resident says > rest; "
                                               "the desk only takes you home)")


def narrates(desk):
    """Does a bare look narrate for this reader? Only in a world with rooms, and not for Alex (a678 (8))."""
    return placed(desk.world.me) and bool(all_rooms(desk.world))
