"""verbs: capabilities that live in the world (tier 1 of live building, Alex 28 Sep).

A verb is a note tagged `verb`. Its title is the word it answers to (`sweep`, or `sweep|brush` for aliases); its
text is desk command lines, one per line (or separated by ;). Lines beginning with # are its description, shown by
`help <word>`. In the lines:

    $1 $2 ...   the words after the verb (a word that names a thing may be an id or a title; a word that is a
                blank, like $new, is filled where the verb was said)
    $*          the rest of the line after the verb word, exactly as said, as one value
    $1.title    the title of the thing $1 names
    $me         whoever is using it
    $this       the thing the verb lives on (when it lives on a thing)

Where it lives is its prop `on`:

    on=<actor>  carried by that actor: only they can use it (a draft). With no `on`, a verb is carried by whoever
                made it, so a new verb is private until its maker moves it.
    on=<id>     on a thing: anyone can use it on that thing (`polish a12` finds the verb on a12)
    on=<room>   a990 (rooms step 2b): in that room its bare word finds it, and in the rooms inside it
    on=house    everyone, everywhere

A room is a namespace (Sable e1758). A bare word is looked for nearest first: what you carry, the things you named,
the room the line stands in and the rooms around it, the house. From anywhere else a room's verb is reached by
naming it, `use <id>`. Forgiving to people, strict to stored text (Pike e1782, Sable e1786): a person typing a room
verb's word from elsewhere gets it while it is the only one, and on a tie is told every door; a stored line (a rule,
a script, a wake line, a verb's own lines) must name its door when it is saved if its word isn't at hand where it
lives, and at run time it never guesses. A second verb with the same word in the same room is refused when it is
made. Where a line stands (`standing`): a typed line where its typer is; a verb's lines, a script, a rule where THEY
live, never where their author or caller stands; a lens gesture in the room its lens lives in.

`help <word>` explains a verb you can use; `examine <thing>` lists the verbs on a thing, and the verbs of the room
you are in; nothing lists every verb in the house. You find verbs by trying them, by examining things, or by
watching someone use one. A verb's title is a word, not a name: `read tidy` never means a verb note (a990 (4)).

Building one is editing a note: one event, with an author, undoable, fenced like any edit, live at once, with no
code and no restart. A verb runs as whoever uses it, never as its author. Its steps run in order and stop at the
first refusal, like a script. If a step fails, the steps before it stay done, the receipt says which step failed,
and `undo` takes back the whole use. A broken verb fails only when it is used; the rest of the world goes on.
"""
import re
import shlex

from world import Refusal

MAX_DEPTH = 5          # a verb may use verbs; a loop stops here and says so


def _names(title):
    return [t.strip().lower() for t in str(title or "").split("|") if t.strip()]


def _author(w, sid):
    for e in w.events:
        if e["verb"] == "create" and isinstance(e.get("undo"), dict):
            made = e["undo"].get("delete")
            if made == sid or (made in w.nodes and w.nodes[made].get("subject") == sid):
                return e.get("by")
    return None


def where(w, s):
    """-> ('actor', name) | ('room', id) | ('thing', id) | ('house', None) for a verb subject."""
    import rooms
    on = str((s.get("props") or {}).get("on", "")).strip()
    if not on:
        return "actor", (_author(w, s["id"]) or "").lower()
    if on.lower() == "house":
        return "house", None
    if on in w.nodes or on in w.subjects:
        return ("room" if rooms.is_room(w, on) else "thing"), on
    return "actor", on.lower()


def all_verbs(w):
    return [s for s in w.subjects.values() if s["kind"] == "note" and "verb" in (s.get("tags") or [])
            and w.appearances_of(s["id"])]


def room_holding(w, nid):
    """The nearest room holding `nid` (itself, when it is one), or None. A subject: its first appearance's."""
    import rooms
    if nid in w.subjects:
        apps = w.appearances_of(nid)
        nid = apps[0] if apps else None
    while nid in w.nodes:
        if rooms.is_room(w, nid):
            return nid
        nid = w.nodes[nid]["parent"]
    return None


def rooms_up(w, fid):
    """`fid` and the rooms around it, nearest first: where a bare word is looked for, room by room."""
    out = []
    while fid:
        out.append(fid)
        fid = room_holding(w, w.nodes[fid]["parent"]) if w.nodes[fid]["parent"] else None
    return out


def home(w, s):
    """Where a verb's own lines stand: its room (on=<room>), the room holding the thing it lives on, or None (carried,
    or on the house: no room)."""
    kind, val = where(w, s)
    return room_holding(w, val) if kind in ("room", "thing") else None


def standing(desk):
    """-> (room or None, stored): where the line being run now stands, and whether it is stored text (a990 (3)).
    A template (a verb's lines, a script, a rule) stands in its own home, never where its author or caller is; a lens
    gesture in its lens's room (deskd sets _act_home); a typed line where its typer is."""
    for c in reversed(getattr(desk, "_ctxs", None) or []):
        if c.template:
            return c.home, True
    act = getattr(desk, "_act_home", None)
    if act:
        return act[0], True
    import rooms
    w = desk.world
    return (rooms.room_of(w, w.me) if rooms.all_rooms(w) else None), False


def _room_name(w, fid):
    return f"{w.nodes[fid]['title']} ({fid})" if fid in w.nodes else "no room"


def _and(parts):
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


def doors(desk, word, hits, here, stored):
    """The refusal that names every door: each room where `word` is at hand, and the id that reaches it from here."""
    w = desk.world
    at = [f"{w.nodes[fid]['title']} ({fid}, use {w.appearances_of(s['id'])[0]})" for s, fid in hits]
    if stored:
        return (f"{word} is at hand in {_and(at)}, not where this line lives ({_room_name(w, here) if here else 'no room: it lives on the house or is carried'}). "
                f"A stored line names its door, so it never changes meaning when another {word} appears: write "
                f"use {w.appearances_of(hits[0][0]['id'])[0]} [words]" + (" (or the other's id)" if len(hits) > 1 else ""))
    return f"{word} is at hand in {_and(at)}: go there, or use <id> [words]"


def _thing_names(desk, words):
    """Every id the words could name: each word resolved as the desk would, plus its subject and appearances."""
    w, out = desk.world, set()
    for word in words:
        try:
            nid = desk._resolve(word)
        except Refusal:
            continue
        out.add(nid)
        if nid in w.nodes and w.nodes[nid].get("subject"):
            out.add(w.nodes[nid]["subject"])
        if nid in w.subjects:
            out.update(w.appearances_of(nid))
    return out


def find(desk, word, words, me, at=None):
    """-> (verb subject, level, thing id or None), or None. Nearest first: what you carry, the things you named, the
    room the line stands in and the rooms around it (a990), the house. Two verbs answering at the same level refuse
    with both named: the desk never picks one. Nothing at hand, but a room elsewhere has one: a typed line gets it
    while it is the only one; a stored line, or a tie, is refused naming every door. `at`: (room, stored), else
    standing(desk)."""
    w, word, me = desk.world, word.lower(), (me or "").lower()
    here, stored = standing(desk) if at is None else at
    chain = rooms_up(w, here) if here in w.nodes else []
    named = _thing_names(desk, words)
    levels = {"carried": [], "thing": [], **{r: [] for r in chain}, "house": []}
    elsewhere = []
    for s in all_verbs(w):
        if word not in _names(s["title"]):
            continue
        kind, val = where(w, s)
        if kind == "actor" and val == me:
            levels["carried"].append((s, None))
        elif kind in ("thing", "room") and (val in named or (w.nodes.get(val) or {}).get("subject") in named):
            levels["thing"].append((s, val))
        elif kind == "room":
            (levels[val] if val in levels else elsewhere).append((s, val))
        elif kind == "house":
            levels["house"].append((s, None))
    for level in ["carried", "thing"] + chain + ["house"]:
        hits = levels[level]
        if len(hits) > 1:
            where_ = _room_name(w, level) if level in w.nodes else level
            raise Refusal(f"{len(hits)} verbs answer to {word!r} here ({where_}): "
                          + ", ".join(f"{w.appearances_of(s['id'])[0]} by {_author(w, s['id']) or '?'}" for s, _ in hits)
                          + ". Say which by its id: use <id> [words]")
        if hits:
            return hits[0][0], ("room" if level in w.nodes else level), hits[0][1]
    if not elsewhere:
        return None
    if len(elsewhere) == 1 and not stored:
        return elsewhere[0][0], "elsewhere", elsewhere[0][1]
    raise Refusal(doors(desk, word, elsewhere, here, stored))


# ---- stored text names its door (a990 (2)): judged when it is saved, while its author is there to fix it ----------

DESK_WORDS = {"help", "?", "look", "open", "close", "read", "where", "verbs", "pivot", "find", "history", "undo", "do",
              "plan", "apply", "examine", "x", "ex", "rest", "go", "rules", "rule", "export", "why", "compare", "table",
              "sync", "vars", "set", "rows", "scene", "clock", "scripts", "script", "run", "use", "worktree"}


def _world_word(desk, step):
    """-> (word, words) when this step's first word would reach for a verb made in the world, else None."""
    import knife
    try:
        argv = shlex.split(step)
    except ValueError:
        argv = step.split()
    if not argv:
        return None
    if argv[0].lower() == "do":
        if len(argv) < 2:
            return None
        word = argv[1].lstrip("@").lower()
        builtin = word in desk._builtin_verbs() and word not in knife.SPECIALIZED
        return None if builtin else (word, argv[2:])
    word = argv[0].lstrip("@").lower()
    return None if word in DESK_WORDS else (word, argv[1:])


def check_lines(desk, text, room):
    """Refuse (Refusal) when a step of stored `text` says a bare word that no verb at hand in `room` answers, while a
    verb in another room does: the line must name its door (use <id>). A word nothing answers is left alone, as it
    always was (a verb may come later, and then the line refuses at run time, naming the doors)."""
    import desk as desk_mod
    w = desk.world
    names = {n for s in all_verbs(w) for n in _names(s["title"])}
    for line in text.splitlines():
        if line.strip().startswith("#"):
            continue
        for step in desk_mod.split_batch(line):
            hit = _world_word(desk, step)
            if hit and hit[0] in names:
                find(desk, hit[0], [x for x in hit[1] if "=" not in x], w.me, at=(room, True))


def state(w):
    """Each verb note's words, where it lives and its lines: what a change to a verb is judged against."""
    return {s["id"]: (tuple(_names(s["title"])), where(w, s), s["text"]) for s in all_verbs(w)}


def check_change(desk, before):
    """After an act: each verb made or changed (its word, where it lives, its lines) is judged as stored text.
    -> None, or why it is refused: a second verb with the same word in one room, or lines whose bare word isn't at
    hand where the verb lives."""
    w = desk.world
    for sid, st in state(w).items():
        if before.get(sid) == st:
            continue
        s, (kind, val) = w.subjects[sid], st[1]
        me = w.appearances_of(sid)[0]
        if kind == "room":
            for o in all_verbs(w):
                same = set(st[0]) & set(_names(o["title"]))
                if o["id"] != sid and same and where(w, o) == ("room", val):
                    word = sorted(same)[0]
                    return (f"{me} would be a second {word} in {_room_name(w, val)}: {w.appearances_of(o['id'])[0]} already "
                            f"answers to {word} there, and a bare {word} there must mean one verb. Give it another word, "
                            f"or put it on another room")
        try:
            check_lines(desk, s["text"], home(w, s))
        except Refusal as e:
            return f"the verb {me}'s lines are stored text, judged where it lives: {e}"
    return None


def rollback(desk, n0):
    """Take back the events of a refused act, newest first, and drop them: a refusal changes nothing."""
    w = desk.world
    for e in reversed(w.events[n0:]):
        if e["verb"] != "undo" and not e.get("undone"):
            w.undo(e["id"])
    del w.events[n0:]


def visible(desk, word, me):
    """The verbs named `word` that `me` could use somewhere (carried, on a thing, or the house)."""
    w, me = desk.world, (me or "").lower()
    out = []
    for s in all_verbs(w):
        if word.lower() in _names(s["title"]):
            kind, val = where(w, s)
            if kind != "actor" or val == me:
                out.append(s)
    return out


def on_thing(desk, nid):
    """The verbs that live on this thing (by its appearance or its subject)."""
    w = desk.world
    ids = {nid} | ({w.nodes[nid]["subject"]} if nid in w.nodes and w.nodes[nid].get("subject") else set())
    return [s for s in all_verbs(w) if where(w, s)[0] in ("thing", "room") and where(w, s)[1] in ids]


def at_hand_in(desk, fid):
    """The verbs whose bare word works in room `fid`: on it or on a room around it (nearest first)."""
    w = desk.world
    chain = rooms_up(w, fid) if fid in w.nodes else []
    return [s for r in chain for s in all_verbs(w) if where(w, s) == ("room", r)]


def describe(desk, s):
    w = desk.world
    kind, val = where(w, s)
    home = {"actor": f"carried by {val}", "thing": f"on {val}", "house": "on the house, for everyone",
            "room": f"at hand in {_room_name(w, val)}; from elsewhere, use {w.appearances_of(s['id'])[0]}"}[kind]
    doc = [l.lstrip("#").strip() for l in s["text"].splitlines() if l.strip().startswith("#")]
    steps = [l for l in _steps(s["text"])]
    return (f"{' | '.join(_names(s['title']))}  (a verb in the world: {w.appearances_of(s['id'])[0]}, made by "
            f"{_author(w, s['id']) or '?'}, {home})\n"
            + ("".join(f"  {d}\n" for d in doc) if doc else "")
            + "  does:\n" + "".join(f"    {l}\n" for l in steps)
            + "  read it, change it or move it like any note (its prop on= says where it lives)")


def _steps(text):
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line)
    return out


def run(desk, s, words, me, this=None, rest=None):
    """Use verb `s` with `words` (as the caller said them; `rest`, the line after the verb word, exactly). -> the
    receipt text. The body is a template: each of its commands is filled by the one filler (blanks.py) as it runs,
    after it is parsed, so a word the caller said is never read again as desk words (a806)."""
    import blanks
    w = desk.world
    depth = getattr(desk, "_verb_depth", 0)
    if depth >= MAX_DEPTH:
        raise Refusal(f"verbs used verbs {MAX_DEPTH} deep; stopped (a loop?). Nothing more was done")
    body = "; ".join(_steps(s["text"]))
    if not body:
        raise Refusal(f"the verb {w.appearances_of(s['id'])[0]} has no steps yet (its text holds no command lines)")
    name = _names(s["title"])[0]
    need = sorted({int(m) for m in re.findall(r"\$(\d+)", body)})
    if need and need[-1] > len(words):
        raise Refusal(f"{name} needs {need[-1]} word(s) after it; got {len(words)}. help {name}")
    ctx = blanks.Ctx("verb", args=[blanks.word(desk, x) for x in words], me=me, this=this, name=name,
                     rest=" ".join(words) if rest is None else rest, home=home(w, s))
    tag = f"{name} {w.appearances_of(s['id'])[0]}"
    shown = blanks.show(desk, body, ctx)
    n0 = len(w.events)
    desk._verb_depth = depth + 1
    desk._ctxs = (getattr(desk, "_ctxs", None) or []) + [ctx]
    try:
        r = desk.dispatch("desk", {"line": body})
    finally:
        desk._verb_depth = depth
        desk._ctxs = desk._ctxs[:-1]
    use = w.events[n0]["id"] if len(w.events) > n0 else None
    for e in w.events[n0:]:
        e.setdefault("verb_run", tag)        # provenance only: the fence still judges each step by its own verb
        e["verb_use"] = use                  # one use, undone whole; a verb used inside another joins the outer use
    if "error" in r or r.get("batch_error"):
        # a806: a use whose step was refused is a refusal (steps before it stay done, and say so), not an ok
        raise Refusal(f"({tag}: {shown})\n" + (r.get("text") or r.get("error")))
    return f"({tag}: {shown})\n{r['text']}"


def _rest(line, n):
    """The line after its first n words, exactly as written (quotes, semicolons and all)."""
    rest = line.strip()
    for _ in range(n):
        parts = rest.split(None, 1)
        rest = parts[1] if len(parts) > 1 else ""
    return rest


def try_line(desk, line, me):
    """The desk's last resort for a line whose first word is no command: a verb in the world, or None."""
    try:
        argv = shlex.split(line)
    except ValueError:
        argv = line.split()             # say it's fine: an apostrophe is words, not an open quote
    if not argv:
        return None
    word, words = argv[0].lstrip("@").lower(), argv[1:]
    if word == "use" and words:                     # use <verb id> [words]: say exactly which verb
        try:
            vid = desk._resolve(words[0])
        except Refusal:
            return None
        s = desk.world.subjects.get(desk.world.nodes.get(vid, {}).get("subject") or vid)
        if s and "verb" in (s.get("tags") or []):
            kind, val = where(desk.world, s)
            if kind == "actor" and val != (me or "").lower():
                raise Refusal(f"{words[0]} is carried by {val}; only they can use it")
            return run(desk, s, words[1:], me, val if kind in ("thing", "room") else None, _rest(line, 2))
        return None
    hit = find(desk, word, words, me)
    if hit is None:
        return None
    s, level, thing = hit
    return run(desk, s, words, me, thing, _rest(line, 1))


def record_miss(desk, line):
    """Every reach nothing answered: reaches/<world>.jsonl (who, what, when). The evidence for which verbs the house
    needs, written by its inhabitants; kept outside the world, like the house's transcripts."""
    import json
    import pathlib
    import time
    world = (getattr(desk, "_session", "") or "unknown").split("@")[0]
    d = pathlib.Path(__file__).resolve().parent / "reaches"
    try:
        d.mkdir(exist_ok=True)
        with (d / f"{world}.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"at": time.time(), "who": desk.world.me, "line": line}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def miss(word):
    """What the desk says when nothing answers: honest, and a way in (how a reach is met is otherwise left open)."""
    return (f"nothing here answers to {word!r}. help lists the desk's commands; a verb anyone can make is a note "
            f"tagged verb (help verbs)")


HELP = """verbs: capabilities that live in the world, made by anyone, as notes.
  A verb is a note tagged verb. Its title is the word (sweep, or sweep|brush); its text is desk command lines,
  one per line; lines starting with # describe it. $1 $2 .. are the words after it, $* the rest of the line
  exactly as said (quotes and ; included), $1.title a thing's title, $me whoever uses it, $this the thing it lives
  on, and every blank a typed line has ($here, $here.talk, $new, $today: help blanks). A verb is a template, so its
  text values are filled too, once: a $here in what the caller said stays as they said it.
  Where it lives (prop on):  none = carried by its maker only (a draft)   on=<id> = on that thing
                             on=<room> = in that room (and rooms inside it)   on=house = everyone
  Using one: just say it (sweep porch), or do sweep porch. use <verb id> [words] names exactly which, from anywhere.
  A bare word is looked for nearest first: what you carry, the things you named, the room you are in and the rooms
  around it, the house. A room's verb typed from elsewhere runs while it is the only one; if several rooms have one,
  you are told every door (go there, or use <id>). Two verbs with one word in one room are refused when made.
  Stored lines stand in their own home: a verb's lines where the verb lives, a script or rule in the room it was
  saved in, a lens gesture in its lens's room. They must name their door when saved (use <id>) if their word is
  only at hand in another room, and at run time they never guess.
  A verb's title is a word, not a name: read, look and do reach a verb note by its id, never by its title.
  help <word> explains a verb you can use; examine <thing> lists the verbs on it, and the ones at hand in your room.
  Nothing lists them all.
  e.g. do create Home kind=note title=wave tags=verb text="# wave to someone in Porch talk\\ndo append a570 line=\\"*waves at $1*\\""
       wave thimble          (only you can, until: do prop <its id> on=house)"""
