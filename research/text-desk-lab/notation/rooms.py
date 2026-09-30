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
    for fid, n in w.nodes.items():
        p = n.get("props") or {}
        if n["type"] == "surface" and p.get("role") == "resident" and str(p.get("actor", "")).lower() == a and a:
            return fid
    return None


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
    for n in w.nodes.values():
        if n["type"] == "surface" and a in {x.strip().lower() for x in str((n.get("props") or {}).get("person", "")).split(",")}:
            return "person"
    return "agent"


CALLED = r"@({names}|everyone|all)\b"


def called_by_line(w, sid, text, speaker):
    """a1062: the residents a chat line in subject `sid` would call, as the house hears it (house.news): the owner of a
    corner the chat sits in (a visitors' book, a talk with Alex), and, in a chat they are a member of, anyone it names
    @name, @everyone or @all outside quotes (a916). Never the speaker. -> [actor, ...]"""
    from world import unquoted
    s = w.subjects.get(sid)
    if not s or s["kind"] != "chat":
        return []
    members = {m.strip().lower() for m in str((s.get("props") or {}).get("members", "")).split(",")}
    heard = unquoted(text)
    me = str(speaker or "").split("/")[0].lower()
    out = []
    for fid, n in w.nodes.items():
        p = n.get("props") or {}
        who = str(p.get("actor", "")).lower()
        if n["type"] != "surface" or p.get("role") != "resident" or not who or who == me:
            continue
        inside = any(a["type"] == "appearance" and a.get("subject") == sid and _within(w, a, fid) for a in w.nodes.values())
        if inside or (("all" in members or who in members) and re.search(CALLED.format(names=re.escape(who)), heard, re.I)):
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
    """a1062: what a chat line's receipt says about the residents it calls who are resting or asleep, or "". A
    resident's line waits for their next wake, and is shown first there, marked for them; a person's line calls them
    at once (a resting one; one asleep is not run by the house until someone wakes them). Said every time, so the
    old '(no need to wake)' habit has nothing left to do."""
    import scene
    w = desk.world
    n = w.nodes.get(nid)
    sid = n.get("subject") if n else nid
    who = called_by_line(w, sid, text, w.me)
    if not who:
        return ""
    how = presences(desk)
    rows = {r["corner"]: r for r in scene.house_rows(desk)}
    resting = []
    for a in who:
        word = how(a)
        if word == "asleep":
            resting.append((a, "asleep", "is asleep (the house doesn't run them)"))
        elif word.startswith("resting"):
            wakes = (rows.get(corner_of(w, a)) or {}).get("wakes", "")
            said = word if word != "resting" else ("resting, until " + wakes + " at the latest" if wakes else "resting")
            resting.append((a, "resting", "is " + said))
    if not resting:
        return ""
    person = kind_of(w, w.me) == "person"
    out = []
    for a, how_, said in resting:
        name = w.display_name(a)
        if person and how_ == "resting":
            out.append(f"{name} was resting; your line calls them now")
        elif person:
            out.append(f"{name} {said}; they'll see this first when they're woken (wake {a}, or want=awake)")
        else:
            out.append(f"{name} {said}; they'll see this when they wake, first and marked for them, so there's no need "
                       f"to say so (wake {a} to call them now)")
    return "\n  ".join(out)


def cmd_wake(desk, arg):
    """a1062: wake <name>: end that resident's rest now. It sets call=<you> on their corner, signed by you (the
    Desktop's wake button sets the same prop); the house delivers it at once, clears it, and their wake says who
    called and, if you left a line that was held for them, which one. A mention never wakes a resting resident when
    a resident or agent says it; waking is this act."""
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
    w = desk.world

    def word(actor):
        if asleep(w, actor):
            return "asleep"
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
    bits = [x for x in (p.get("status"), f"owner {p['owner']}" if p.get("owner") else "", f"due {s['due']}" if s.get("due") else "") if x]
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
    others = [a for a in here(w, fid) if a != me]
    how = presences(desk)
    awake = [a for a in others if how(a) != "asleep"]
    sleeping = [a for a in others if how(a) == "asleep"]
    # a806 (6): a sleeping actor is never 'here with you'; one asleep is said so, wherever they sleep. a948 (4): one
    # between turns is here, and resting; only someone in a turn right now is named plain
    names = ", ".join(w.display_name(a) + (f" ({how(a)})" if how(a) else "") for a in awake)
    if at == fid:
        out.append(f"Here with you: {names}." if awake else "No one else is here." if not sleeping else "No one else here is awake.")
    else:
        out.append(f"Here: {names}." if awake else "No one is here." if not sleeping else "No one here is awake.")
    for a in sleeping:
        out.append(f"{w.display_name(a)} is asleep here" + (" (their own corner)." if corner_of(w, a) == fid else "."))
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
    # `rules` lists every one
    ids = [i for i in ids if "rule" not in (w.subjects.get(w.nodes[i].get("subject") or "", {}).get("tags") or [])]
    if ids:
        out.append("At hand:")
        out += ["  " + item_line(desk, i) for i in ids[:AT_HAND_MAX]]
        if len(ids) > AT_HAND_MAX:
            out.append(f"  (+{len(ids) - AT_HAND_MAX} more; look {fid} :2 lists them all)")
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
