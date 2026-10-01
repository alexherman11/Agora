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
a wake line, a verb's own lines, a lens act) is bound when it is saved (a1156): each word means the verb it meant
where the line lives, and at run time it never looks again. A word nothing answers there is refused at save (a rule
is saved broken, a1027). A verb never takes a built-in's word, nor a word another verb answers where it would live
unless it says overrides=<that verb> (Juniper c1337). Where a line stands (`standing`): a typed line where its typer
is; a verb's lines and a rule where THEY live, never where their author or caller stands; a lens gesture in the room
its lens lives in; a wake in its corner.

`help <word>` explains a verb you can use; `examine <thing>` lists the verbs on a thing, and the verbs of the room
you are in; `help` with a word it doesn't know lists every verb at hand where you are (a1308, Pike's a1299); nothing
lists every verb in the house. You find verbs by trying them, by examining things, or by
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
    standing(desk). a1156: a stored line that was bound when saved never looks: its word means the verb it was bound
    to (bound_find); only a typed line, or a stored line saved before bindings, looks here."""
    w, word, me = desk.world, word.lower(), (me or "").lower()
    if at is None:
        entry = bound(desk)
        if entry is not None:
            return bound_find(desk, word, words, me, entry)
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
              "plan", "apply", "examine", "x", "ex", "rest", "wake", "go", "rules", "rule", "export", "why", "compare", "table",
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


def builtin_words(desk):
    """a1156 (4): the words the desk itself answers (its commands, its verbs and their synonyms). A world verb never
    takes one. The retired built-ins (tidy, reply, stack ...) are not among them: this desk only refuses those, and a
    world verb may answer them (a990)."""
    import knife
    return (set(desk._builtin_verbs()) | DESK_WORDS) - set(knife.SPECIALIZED)


def _desc(w, s):
    kind, val = where(w, s)
    return {"actor": f"carried by {val}", "house": "on the house", "thing": f"on {val}",
            "room": f"in {_room_name(w, val)}"}[kind]


def _aid(w, s):
    apps = w.appearances_of(s["id"])
    return apps[0] if apps else s["id"]


def _verb_named(w, ident):
    """The verb subject an id names (its appearance or its subject), placed and tagged verb, or None."""
    ident = str(ident or "").strip().lstrip("@")
    sid = (w.nodes.get(ident) or {}).get("subject") or ident
    s = w.subjects.get(sid)
    return s if s and "verb" in (s.get("tags") or []) and w.appearances_of(sid) else None


def answering(w, word, s):
    """a1156 (4): the other verbs that answer `word` at hand where verb `s` would live, so that `s` would take the word
    over there: the house, the rooms around its room (its own included), its thing, and for a carried verb what its
    maker carries and what is at hand where the maker stands. A verb farther out (a house verb, when `s` is on a room)
    is what `s` would stand over; one nearer still wins, and is not taken over."""
    import rooms
    kind, val = where(w, s)
    if kind == "room":
        fid = val
    elif kind == "thing":
        fid = room_holding(w, val)
    elif kind == "actor":
        fid = rooms.room_of(w, val) if rooms.all_rooms(w) else None
    else:
        fid = None
    places = {("room", r) for r in (rooms_up(w, fid) if fid in w.nodes else [])} | {("house", None)}
    if kind in ("actor", "thing"):
        places.add((kind, val))
    return [o for o in all_verbs(w) if o["id"] != s["id"] and word in _names(o["title"]) and where(w, o) in places]


def state(w):
    """Each verb note's words, where it lives, its lines and what it overrides: what a change to a verb is judged
    against."""
    return {s["id"]: (tuple(_names(s["title"])), where(w, s), s["text"], str((s.get("props") or {}).get("overrides", "")))
            for s in all_verbs(w)}


def check_change(desk, before):
    """After an act: each verb made, renamed or moved is judged for its words (a1156 (4)): a built-in's word is refused,
    and so is a word another verb already answers where it would live, unless it says overrides=<that verb>. Its lines
    are judged as stored text when they are bound (after_act). -> None, or why it is refused."""
    w = desk.world
    builtin = builtin_words(desk)
    for sid, st in state(w).items():
        old = before.get(sid)
        if old == st or (old is not None and old[:2] == st[:2] and old[3] == st[3]):
            continue                            # only its lines changed: they are bound in after_act
        s, me = w.subjects[sid], _aid(w, w.subjects[sid])
        for word in st[0]:
            if word in builtin:
                return (f"{me} would answer to {word}, a word the desk itself answers (do {word} ...): a verb made in the "
                        f"world never takes a built-in's word, so {word} means one thing everywhere (a1156). Give it "
                        f"another word")
        ov_said = st[3].strip()
        ov = _verb_named(w, ov_said) if ov_said else None
        if ov_said and ov is None:
            return f"{me} says overrides={ov_said}, which is no verb (a placed note tagged verb): name the verb it stands over by its id"
        stood = False
        for word in st[0]:
            for o in answering(w, word, s):
                kind, val = where(w, s)
                if kind == "room" and where(w, o) == (kind, val):
                    return (f"{me} would be a second {word} in {_room_name(w, val)}: {_aid(w, o)} already answers to "
                            f"{word} there, and a bare {word} there must mean one verb. Give it another word, or put it "
                            f"on another room")
                if ov is not None and o["id"] == ov["id"]:
                    stood = True
                    continue
                return (f"{me} would answer to {word} {_desc(w, s)}, where {_aid(w, o)} ({_desc(w, o)}, made by "
                        f"{_author(w, o['id']) or '?'}) already answers to {word}: a word is never quietly taken over "
                        f"(a1156). To stand over it there on purpose, say so: overrides={_aid(w, o)} on {me} (a typed "
                        f"{word} there then names both); or give it another word")
        if ov is not None and not stood:
            return (f"{me} says overrides={ov_said}, but {_aid(w, ov)} does not answer to "
                    f"{' or '.join(st[0])} where {me} would live ({_desc(w, s)}): there is nothing to stand over")
    return None


def rollback(desk, n0):
    """Take back the events of a refused act, newest first, and drop them: a refusal changes nothing."""
    w = desk.world
    for e in reversed(w.events[n0:]):
        if e["verb"] != "undo" and not e.get("undone"):
            w.undo(e["id"])
    del w.events[n0:]


# ---- a1156: a stored line's words are bound when it is saved ------------------------------------------------------
# A stored line (a verb's lines, a rule, a lens's acts, a corner's wake) is judged when it is saved, while its author is
# there: each bare word that reaches for a verb made in the world is bound to the verb it means right then, and the
# binding is kept with the line's holder (the note, or the corner for a wake). At run time a bound line never looks
# again: a verb made later with the same word changes nothing, and a bound verb that is gone fails loudly. A word
# nothing answers is refused at save (a rule is saved broken, as a990's rules always were). Changing a verb's lines
# leaves a note on the sill of every other author whose lines are bound to it (Unison's lesson, a1142). Typed lines
# are untouched: a person's bare word is looked up when they type it, as always.

KEEP_WAKES = 8          # a corner keeps the bindings of its last few wake lines, so an undo of a wake finds its own


def holder_kind(s):
    tags = s.get("tags") or []
    return next((k for k in ("verb", "rule", "lens") if k in tags), None)


def stored_texts(w):
    """-> {key: (kind, text)} for every placed holder of stored lines: ('s', subject id) for a verb, rule or lens note,
    ('n', node id) for a node with a wake line."""
    out = {}
    for s in w.subjects.values():
        kind = holder_kind(s)
        if kind and w.appearances_of(s["id"]):
            out[("s", s["id"])] = (kind, s["text"])
    for n in w.nodes.values():
        wake = (n.get("props") or {}).get("wake")
        if wake:
            out[("n", n["id"])] = ("wake", str(wake))
    return out


def holder_home(w, key, kind):
    """Where a holder's lines stand (a990 (3)): a verb's where it lives, a rule's or a lens's in the room holding its
    note, a wake in its corner."""
    if key[0] == "n":
        import rooms
        return key[1] if rooms.is_room(w, key[1]) else room_holding(w, key[1])
    s = w.subjects[key[1]]
    return home(w, s) if kind == "verb" else room_holding(w, s["id"])


def holder_label(w, key, kind):
    if key[0] == "n":
        return f"the wake on {key[1]}"
    s = w.subjects.get(key[1])
    return f"{kind} {_aid(w, s) if s else key[1]}" + (f' "{s["title"]}"' if s and kind != "verb" else "")


def _rule_steps(text):
    """The action of a rule (`when ... do X` / `on ... do X`), as one `do X ...` step; `use <id>` names its verb."""
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            argv = shlex.split(line)
        except ValueError:
            argv = line.split()
        if "do" in argv[1:]:
            act = argv[argv.index("do", 1) + 1:]
            if act and act[0].lower() != "use":
                out.append("do " + " ".join(shlex.quote(a) for a in act))
    return out


def _lens_steps(text):
    """Each desk command a lens's gestures send (`on click do ...`), read as the lens compiler reads them."""
    import desk as desk_mod
    import scene
    out = []
    for raw in text.splitlines():
        line = scene._outside_quotes(raw, " # ")[0]
        _name, colon, rest = line.strip().partition(" : ")
        if not colon:
            continue
        for p in scene._outside_quotes(rest, ", "):
            p = p.strip()
            if p.startswith("on ") and " do " in p:
                cmd = p.partition(" do ")[2].strip()
                if cmd.split(" ")[0] not in scene.ACT_COMMANDS:
                    cmd = "do " + cmd
                out += desk_mod.split_batch(cmd)
    return out


def line_words(desk, kind, text):
    """-> [(word, its words, the step)] for each step of stored text whose word reaches for a verb made in the world."""
    import desk as desk_mod
    if kind == "rule":
        steps = _rule_steps(text)
    elif kind == "lens":
        steps = _lens_steps(text)
    else:
        steps = [st for line in text.splitlines() if line.strip() and not line.strip().startswith("#")
                 for st in desk_mod.split_batch(line)]
    out = []
    for st in steps:
        hit = _world_word(desk, st)
        if hit:
            out.append((hit[0], hit[1], st.strip()))
    return out


def bind_text(desk, kind, text, here, me):
    """-> the binding of stored `text` standing in `here`, saved by `me`: {text, words: {word: {id, at} | {thing}},
    missing: {word: why}, by}. A word is bound to what a stored line standing there means by it now (a990's strict
    lookup); a word that only a verb on the thing it is used on can answer ($1, $item) is bound as such."""
    w = desk.world
    entry = {"text": text, "words": {}, "missing": {}, "by": me, "lines": {}}
    builtin = builtin_words(desk)
    for word, args, step in line_words(desk, kind, text):
        entry["lines"].setdefault(word, []).append(step)
        if word in entry["words"] or word in entry["missing"]:
            continue
        if word.startswith("$"):
            entry["missing"][word] = (f"{step!r}: a stored line's verb word can't be a blank, or it would mean whatever "
                                      f"it is filled with; name the verb (its word, or use <id>)")
            continue
        if word in builtin:
            entry["missing"][word] = f"{step!r}: {word} is the desk's own verb; a stored line says do {word} ..."
            continue
        try:
            hit = find(desk, word, [a for a in args if "=" not in a], me, at=(here, True))
        except Refusal as e:
            entry["missing"][word] = str(e)
            continue
        if hit:
            entry["words"][word] = {"id": hit[0]["id"], "at": _aid(w, hit[0])}
        elif any(where(w, s)[0] == "thing" and word in _names(s["title"]) for s in all_verbs(w)) \
                and any(a.startswith("$") for a in args):
            entry["words"][word] = {"thing": True}      # a verb that lives on a thing: the thing it is used on answers
        else:
            import knife
            entry["missing"][word] = (f"{word} is not a verb here: nothing answers to it where this line lives "
                                      f"({_room_name(w, here) if here else 'no room: it lives on the house or is carried'}), "
                                      f"neither a general verb ({' '.join(knife.GENERAL)}) nor one made in the world. "
                                      f"A stored line's words are bound when it is saved, so a verb made later never takes "
                                      f"one over: make the verb first (help verbs), then save the line; or name one: use <id>")
    return entry


def binding_of(w, key, text):
    """The binding kept for this holder's current `text`, or None (saved before bindings, a1156)."""
    if key[0] == "s":
        b = (w.subjects.get(key[1]) or {}).get("binds")
        return b if b and b.get("text") == text else None
    for b in reversed((w.nodes.get(key[1]) or {}).get("binds") or []):
        if b.get("text") == text:
            return b
    return None


def keep_binding(w, key, entry):
    """Kept with the holder, outside its props: a subject's binding is restored with it by undo (restore_subject);
    a corner keeps its last few wake bindings by text, since undo restores only its props."""
    if key[0] == "s":
        s = w.subjects[key[1]]
        if entry["words"] or entry["missing"]:
            s["binds"] = entry
        else:
            s.pop("binds", None)
        return
    n = w.nodes[key[1]]
    kept = [b for b in (n.get("binds") or []) if b.get("text") != entry["text"]]
    n["binds"] = (kept + ([entry] if entry["words"] or entry["missing"] else []))[-KEEP_WAKES:]


def writer(w, key):
    """Who last wrote this holder's lines: its maker, or the last to change its text (a wake: to set it)."""
    if key[0] == "s":
        sid = key[1]
        ids, who = {sid} | set(w.appearances_of(sid)), None
        for e in w.events:
            if e.get("undone") or e["verb"] == "undo":
                continue
            a = e.get("args") or {}
            if e["verb"] == "create" and isinstance(e.get("undo"), dict):
                made = e["undo"].get("delete")
                if made in ids or (made in w.nodes and w.nodes[made].get("subject") == sid):
                    who = e["by"]
            elif e["target"] in ids and e["verb"] == "edit" and ("text" in a or "append" in a):
                who = e["by"]
        return who
    return next((e["by"] for e in reversed(w.events) if e["target"] == key[1] and e["verb"] == "prop"
                 and "wake" in (e.get("args") or {}) and not e.get("undone")), None)


def bind_unbound(desk):
    """Once per world (a1156): every stored line saved before bindings is bound to what it means now, as its writer,
    so nothing made from now on can take it over. A word nothing answers now stays unbound and fails when it runs,
    saying why; it is never left to be found later. Meaning is unchanged: a990 already looked strictly at run time.
    Juniper c1421: it is not done quietly: one event by the house, `bind`, names every holder it bound, so history and
    the !! line show it, and undo takes the bindings back (the lines then look strictly at run time, as before)."""
    w = desk.world
    if getattr(w, "_binds_version", 0) >= 1:
        return
    w._binds_version = 1
    me, done = w.me, []          # [(key, label, what it kept before)]
    try:
        for key, (kind, text) in stored_texts(w).items():
            if binding_of(w, key, text) is None and line_words(desk, kind, text):
                obj = w.subjects[key[1]] if key[0] == "s" else w.nodes[key[1]]
                prev = __import__("copy").deepcopy(obj.get("binds"))
                w.me = writer(w, key) or me
                entry = bind_text(desk, kind, text, holder_home(w, key, kind), w.me)
                keep_binding(w, key, entry)
                done.append((key, holder_label(w, key, kind), prev, w.me, entry))
    finally:
        w.me = me
    if not done:
        return
    ids = [(_aid(w, w.subjects[k[1]]) if k[0] == "s" else k[1]) for k, *_ in done]
    said = "; ".join(f"{label} as {who}: " + (", ".join(f"{wd} → {r.get('at', 'the thing it is used on')}"
                                                       for wd, r in e["words"].items()) or "nothing")
                     + ("".join(f", {wd} unbound" for wd in e["missing"]))
                     for _k, label, _p, who, e in done)
    ev = w._event("bind", ids[0], {"holders": ids}, {"restore_binds": [(k[0], k[1], p) for k, _l, p, _w, _e in done]},
                  actor="house", note=f"a1156: bound {len(done)} stored line holder(s) saved before bindings, each as "
                                      f"its writer, to what it meant then: {said}")
    ev["changed"] = ids


def lens_binds(w, sids):
    """A lens act's binding: the painted lens's, then the lenses it was built from (the first to bind a word wins).
    None when none of them was bound (saved before bindings: a990's strict lookup)."""
    merged, any_ = {"text": None, "words": {}, "missing": {}, "by": None, "lines": {}}, False
    for sid in sids:
        s = w.subjects.get(sid)
        b = binding_of(w, ("s", sid), s["text"]) if s else None
        if b:
            any_ = True
            for k in ("words", "missing"):
                for wd, v in b[k].items():
                    if wd not in merged["words"] and wd not in merged["missing"]:
                        merged[k][wd] = v
    return merged if any_ else None


def stored_at(w, nid):
    """-> (_act_home, _act_binds) for running a node's wake line as the stored text it is (house.py sends stored=)."""
    import rooms
    here = nid if rooms.is_room(w, nid) else room_holding(w, nid)
    wake = str(((w.nodes.get(nid) or {}).get("props") or {}).get("wake") or "")
    return (here,), binding_of(w, ("n", nid), wake)


def bound(desk):
    """The binding of the stored line being run now, or None: a typed line, or one saved before bindings (then a990's
    strict lookup, as before). The innermost template's (a verb's lines, a rule), else a lens act's or a wake's."""
    for c in reversed(getattr(desk, "_ctxs", None) or []):
        if c.template:
            return getattr(c, "binds", None)
    if getattr(desk, "_act_home", None):
        return getattr(desk, "_act_binds", None)
    return None


def bound_find(desk, word, words, me, entry):
    """A bound line's word: the verb it was bound to, or a loud refusal. It never finds another verb with the word."""
    w = desk.world
    rec = entry["words"].get(word)
    if rec is None:
        why = entry["missing"].get(word)
        raise Refusal(f"this line was saved with no verb for {word}" + (f" ({why})" if why else "")
                      + f": a stored line never looks again, so nothing made later answers it. Make the verb, then save "
                        f"the line again (or name one: use <id>)")
    if rec.get("thing"):
        named = _thing_names(desk, words)
        hits = [(s, where(w, s)[1]) for s in all_verbs(w) if word in _names(s["title"]) and where(w, s)[0] == "thing"
                and (where(w, s)[1] in named or (w.nodes.get(where(w, s)[1]) or {}).get("subject") in named)]
        if len(hits) != 1:
            raise Refusal(f"{word} was bound to the verb on the thing it is used on, and "
                          + ("no thing named here carries one" if not hits else f"{len(hits)} things named here do"))
        return hits[0][0], "bound", hits[0][1]
    s = _verb_named(w, rec["id"])
    if s is None:
        raise Refusal(f"{word} {rec['at']} is gone; this line was bound to it. A stored line never finds another {word} "
                      f"on its own: save the line again to bind it to one that is here, or name one: use <id>")
    kind, val = where(w, s)
    if kind == "actor" and val != me:
        raise Refusal(f"{word} {rec['at']} is carried by {val}; only they can use it (this line was bound to it)")
    return s, "bound", (val if kind in ("thing", "room") else None)


def _bound_to(w, vsid):
    """Every holder whose kept binding uses verb `vsid` -> [(key, kind, entry, words)]."""
    out = []
    for key, (kind, text) in stored_texts(w).items():
        b = binding_of(w, key, text)
        used = [wd for wd, rec in ((b or {}).get("words") or {}).items() if rec.get("id") == vsid]
        if used and key != ("s", vsid):
            out.append((key, kind, b, used))
    return out


def tell_users(desk, vsid):
    """a1156 (3): a verb's lines changed. Each other author whose stored lines are bound to it gets a note on their
    sill naming those lines; the editor's own are named on the receipt. -> receipt lines."""
    import rooms
    w = desk.world
    s, me = w.subjects[vsid], w.me
    word, aid = _names(s["title"])[0], _aid(w, s)
    by = {}
    for key, kind, b, used in _bound_to(w, vsid):
        lines = [l for wd in used for l in (b.get("lines") or {}).get(wd, [])]
        by.setdefault(b.get("by") or "?", []).append(f"{holder_label(w, key, kind)}: " + " | ".join(lines))
    out, made = [], w.last_created
    for who, items in sorted(by.items()):
        if who == me:
            out.append(f"~ {word} {aid} changed; these of yours use it: " + "; ".join(items))
            continue
        fid = rooms.corner_of(w, who)
        if not fid:
            out.append(f"~ {word} {aid} changed; {who} has lines that use it and no sill to tell: " + "; ".join(items))
            continue
        text = (f"{me} changed the lines of {word} ({aid}). These of yours are bound to it, so they now do what it does "
                f"now:\n" + "\n".join(f"- {i}" for i in items)
                + f"\nread {aid} shows it; nothing of yours was changed")
        w.apply("create", fid, None, {"kind": "note", "title": f"{word} changed; these of yours use it", "text": text}, me)
        out.append(f"~ {word} {aid} changed: a note on {who}'s sill ({w.last_created}) names their {len(items)} line(s) that use it")
    w.last_created = made
    return out


def after_act(desk, before):
    """a1156: after an act, each holder whose lines were saved (made, changed, or newly tagged) is bound where its lines
    stand. -> (why it is refused, or None; receipt lines). A verb's, a lens's or a wake's line with a word nothing
    answers is refused (nothing changes); a rule is kept, and saved broken by the rules (a1027)."""
    w = desk.world
    notes, changed_verbs = [], []
    for key, (kind, text) in stored_texts(w).items():
        if before.get(key) == (kind, text):
            continue
        entry = bind_text(desk, kind, text, holder_home(w, key, kind), w.me)
        if entry["missing"] and kind != "rule":
            why = next(iter(entry["missing"].values()))
            aid = key[1] if key[0] == "n" else _aid(w, w.subjects[key[1]])
            what = {"verb": f"the verb {aid}'s lines are stored text, judged where it lives",
                    "lens": f"the lens {aid}'s acts are stored text, judged in the room holding it",
                    "wake": "a wake line is stored text, judged in the corner it is set on"}[kind]
            return f"{what}: {why}", []
        keep_binding(w, key, entry)
        if entry["words"]:
            notes.append(f"~ {holder_label(w, key, kind)}: its words are bound (a1156): " + ", ".join(
                f"{wd} → {rec['at']}" if not rec.get("thing") else f"{wd} → the verb on the thing it is used on"
                for wd, rec in entry["words"].items()))
        old = before.get(key)
        if kind == "verb" and old is not None and old[0] == "verb" and _steps(old[1]) != _steps(text):
            changed_verbs.append(key[1])
    for vsid in changed_verbs:
        notes += tell_users(desk, vsid)
    return None, notes


def binding_lines(w, key, text, indent="  "):
    """What examine and help say of a holder's binding."""
    b = binding_of(w, key, text)
    if not b:
        return []
    out = []
    if b["words"]:
        parts = []
        for wd, rec in b["words"].items():
            if rec.get("thing"):
                parts.append(f"{wd} → the verb on the thing it is used on")
                continue
            s = _verb_named(w, rec["id"])
            parts.append(f"{wd} → {rec['at']}" + ("" if s else " (gone: these lines fail until saved again)"))
        out.append(f"{indent}its words are bound (saved by {b.get('by') or '?'}): " + ", ".join(parts))
    for wd in b["missing"]:
        out.append(f"{indent}{wd} is bound to nothing: nothing answered it when these lines were saved")
    return out


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
            + "".join(l + "\n" for l in binding_lines(w, ("s", s["id"]), s["text"]))
            + (f"  stands over {(s.get('props') or {})['overrides']} where it lives (overrides=)\n"
               if (s.get("props") or {}).get("overrides") else "")
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
    ctx.binds = binding_of(w, ("s", s["id"]), s["text"])       # a1156: its own lines mean what they meant when saved
    tag = f"{name} {w.appearances_of(s['id'])[0]}"
    ov_said = str((s.get("props") or {}).get("overrides", "")).strip()
    if ov_said:
        # Juniper c1337: a verb standing over another says so on every receipt; if that one is gone or renamed, the
        # override fails loudly, like a bound line (a1156 (2))
        o = _verb_named(w, ov_said)
        if o is None or not set(_names(o["title"])) & set(_names(s["title"])):
            raise Refusal(f"{tag} overrides {ov_said}, which is " + ("gone" if o is None else f"now {o['title']!r}")
                          + f"; the override fails until it is said again: do prop {_aid(w, s)} overrides=<the verb it "
                            f"stands over>, or remove=overrides")
        tag += f" {_desc(w, s)}, over {name} {_aid(w, o)} {_desc(w, o)}"
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


# a1595: help blanks / help verbs live in the world now, as notes in the Help binder (helpnotes.py)
