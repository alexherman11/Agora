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
    on=house    everyone, everywhere

`help <word>` explains a verb you can use; `examine <thing>` lists the verbs on a thing; nothing lists every verb
in the house. You find verbs by trying them, by examining things, or by watching someone use one.

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
    """-> ('actor', name) | ('thing', id) | ('house', None) for a verb subject."""
    on = str((s.get("props") or {}).get("on", "")).strip()
    if not on:
        return "actor", (_author(w, s["id"]) or "").lower()
    if on.lower() == "house":
        return "house", None
    if on in w.nodes or on in w.subjects:
        return "thing", on
    return "actor", on.lower()


def all_verbs(w):
    return [s for s in w.subjects.values() if s["kind"] == "note" and "verb" in (s.get("tags") or [])
            and w.appearances_of(s["id"])]


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


def find(desk, word, words, me):
    """-> (verb subject, level, thing id or None), or None. Order: what you carry, the things you named, the house.
    Two verbs answering at the same level refuse with both named: the desk never picks one."""
    w, word, me = desk.world, word.lower(), (me or "").lower()
    named = _thing_names(desk, words)
    levels = {"carried": [], "thing": [], "house": []}
    for s in all_verbs(w):
        if word not in _names(s["title"]):
            continue
        kind, val = where(w, s)
        if kind == "actor" and val == me:
            levels["carried"].append((s, None))
        elif kind == "thing" and (val in named or (w.nodes.get(val) or {}).get("subject") in named):
            levels["thing"].append((s, val))
        elif kind == "house":
            levels["house"].append((s, None))
    for level in ("carried", "thing", "house"):
        hits = levels[level]
        if len(hits) > 1:
            raise Refusal(f"{len(hits)} verbs answer to {word!r} here ({level}): "
                          + ", ".join(f"{w.appearances_of(s['id'])[0]} by {_author(w, s['id']) or '?'}" for s, _ in hits)
                          + ". Say which by its id: use <id> [words]")
        if hits:
            return hits[0][0], level, hits[0][1]
    return None


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
    return [s for s in all_verbs(w) if where(w, s)[0] == "thing" and where(w, s)[1] in ids]


def describe(desk, s):
    w = desk.world
    kind, val = where(w, s)
    home = {"actor": f"carried by {val}", "thing": f"on {val}", "house": "on the house, for everyone"}[kind]
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
                     rest=" ".join(words) if rest is None else rest)
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
            return run(desk, s, words[1:], me, val if kind == "thing" else None, _rest(line, 2))
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
  Where it lives (prop on):  none = carried by its maker only (a draft)   on=<id> = on that thing   on=house = everyone
  Using one: just say it (sweep porch), or do sweep porch. use <verb id> [words] names exactly which.
  help <word> explains a verb you can use; examine <thing> lists the verbs on it. Nothing lists them all.
  e.g. do create Home kind=note title=wave tags=verb text="# wave to someone in Porch talk\\ndo append a570 line=\\"*waves at $1*\\""
       wave thimble          (only you can, until: do prop <its id> on=house)"""
