"""scene: the piece between the text world and the picture (v0, meant to be argued with).

A LENS is a short text that says how some part of the world is shown and what each gesture means. It lives in
the world as an ordinary note tagged `lens`, so it is edited with desk commands, undone, forked in a worktree,
and read by anyone. A lens is not code. The host that interprets it is small, fixed, and knows no app.

    world + lens  ->  SCENE  ->  text   (scene <lens>, what an agent reads)
                             ->  pixels (desk-shell/lens.html, a generic painter)

Both projections are printed from the same scene tree, so the screen and the text cannot disagree about what
is there, what it says, where it is, or what a gesture will do. That is the whole point.

Lens grammar. A part line is a name, ` : `, and what the part is and how it looks: `card : column, role card`,
`t : text "$title"`. Every other word is its own line, indented under its part, among the part's child parts
(Alex, 5 Oct: out of the comma lists). An unindented part is defined; the first one is the root.

    card : column, role card
      let size = "big" when $beds > 5
      let size = "small" otherwise
      of kind:note
      each t
    t : text "$title: $size"
      only when $beds > 2

The older `name : word, word, ...` is still read (the worlds hold lenses written so); `scene <lens> lines` prints
the one form. The words:

    column | row | free          how children are laid out (the same three words surfaces use)
    role <name>                  the look, by a role from the style file. A lens never names a colour or a size.
    text <template>              words, with $title $text $kind $due $tags $id $item $it $n, any field of a row
                                 source, and any prop of the thing ($place): the scene prints what it read and
                                 marks a missing prop (no place). Quote it to keep commas and hashes: text "a, b # c"
    marks                        on words: the text may carry marks, written in it: **strong**, *stressed*, ***both***,
                                 [label](address). Read, they are drawn; edited, they are their source, and Ctrl+B,
                                 Ctrl+I, Ctrl+K put one around what is selected or take it off. Not inside code runs;
                                 marks do not nest. The printer says `marks strong 2, link 1`
    clamp <N>                    on words: at most N lines (printed as ~, the painter clamps wrapped lines).
                                 on a repeat: at most N instances; both printers say how many are left
    of <selection>               repeat over the things a desk selection finds (kind:note,in:Canvas), over ids named
                                 one by one (of a04,s09: an appearance, or a subject wherever it appears; the scene
                                 prints each one's state: unplaced, gone), or over a row source: sections:<id>
                                 comments:<id> actors events worktrees (`rows <source>` prints them). An empty
                                 repeat prints (empty); it never looks like a full one
    over $tags                   repeat over a list field of the current thing; $it is each value
    each <part>                  what to instantiate for each repeated thing. $count is the repeat's true size (before
                                 any clamp), on the repeat, in each instance and in its fixed kids; $n on the repeat
                                 itself is how many it shows; $index in an instance is its place, from 1 (7 Oct)
    count <selection>            $count is how many things a selection (or a row source) finds, without drawing them:
                                 rested : text "$count paused", count kind:task,prop:status=paused. Printed `· count 7 of ...`
    at item                      take x,y,w,h from the thing's own appearance in the world (parent must be free)
    spread x <a> step <n|$prop> to <max>   place repeated parts along an axis (also y). $prop is a numeric prop of the
                                 lens note itself: do prop <lens> spacing=210. Computed presentation, never written back
    lens <name>                  place another lens here. A lens may not contain itself
    only when <selection>        the part exists only if the current thing (or anything) matches; the text prints the absence
    only when <expr>             the part exists only when the expression holds (= != < > <= >= has !has, and, or, not,
                                 arithmetic; see let). It prints its inputs; none (a missing value) is absence with
                                 the reason, not false. One way to test since 5 Oct: `$x = done` is read as
                                 `$x = "done"`, the one spelling
    the <selection>              exactly one thing becomes the current thing here; the text prints which (-> s31 (a32)),
                                 or (empty), or (ambiguous: a32, a50) with nothing built under it and gestures off
    as <name>                    name this part's thing as a frame; parts below read it as $name.title $name.start
                                 (a prop) and the scene prints `read name s31 start=...`. On a repeat, each instance
    derive <name> = <interpretation> <inputs>   a named calculation from a closed list (day-n <date> <n>,
                                 days-from <start> <end> (rows with $it.n $it.date, for over $name), weekday <date>,
                                 week-of <date>); it prints its inputs and result
    let <name> = <expr>          a named value (Alex, 5 Oct: if and arithmetic). An expression has + - * / and ( ),
      [when <expr> | otherwise]  comparisons (= != < > <= >= has !has), and, or, not; numbers, "text", dates
                                 (2026-10-05), durations (3d 2h), $names, $frame.field, a let named above; and
                                 count(<selection>), sum($field of <selection>), min(...), max(...), which carry
                                 their reach ('41 of 43; 2 have none'). Kinds are never coerced: '7' is a number,
                                 '2,550 USD' is text and says so. A missing value is none, printed none, never 0.
                                 Several lets of one name with `when` are an if: the first that holds is taken, an
                                 overlap is said, and `otherwise` holds when none of the others do. The scene
                                 prints every let with its expression, inputs and result
    text "... $(<expr>) ..."     an expression computed inside words; the scene prints each one with its inputs
    capture <field>=<value>      use this value instead of following the frame's; prints (now X: differs) when the
                                 world has moved on. Following is the default and is never written down
    carry                        this part's thing can be picked up (pointer or keys) and put down on a part that says `on drop`
    on drop <part> do <command>  the receiver of a carried thing; `$carried` fills with the carried thing at the drop; one command
    on <gesture> do <command>    click | edit | drag. The command is a desk verb line (`do` is implied); the painter
                                 fills $x $y (drag, click) and $value (edit) at the moment of the gesture. A gesture
                                 carries the item revision and the lens revision it was painted under; stale is refused.

Every placed part carries the world's visibility facts (= offscreen-part, 43% hidden by f52). Painters report what
only they know back through POST /api/observe; the scene prints it per viewer as ~ (viewport, cut by the clamp,
out of view). A lens that stops compiling keeps showing its last version that did, and says so first.

Anything else is refused with the line number. There is no escape to raw HTML, CSS or script in v0, on purpose:
the pressure that builds against that wall is the research result.
"""

import pathlib
import re
from desk import split_batch
import expr as X

LAYOUTS = ("column", "row", "free", "grid", "cells")      # pike-7 section 9: grid with tracks; cells is a grid row drawn as display: contents
PAINT_WORDS = ("tracks", "gap", "scroll", "fold", "fold_open", "fold_float", "fold_handle", "fold_group", "measure", "wrap", "lines", "share", "hint", "plain", "peek", "marks")   # pike-7 sections 6 and 9, lowered here; fold_open and fold_float are fold's modifiers
GESTURES = ("click", "edit", "drag", "menu")      # `drop` was admitted and never painted (Astra). A gesture exists when the painter can do it.
# Alex, 29 Sep ("native right click behavior"): `on menu "<label>" do ...` puts an entry in the part's own menu, which the
# painter opens on a right-click (or the menu key) anywhere on the part; a part with no entries keeps the browser's menu.
NAMES = ("title", "text", "kind", "due", "tags", "id", "item", "it", "n", "count", "index")


class LensRefusal(Exception):
    pass


# ---- admission: what Astra's foundations audit (research/shared-visual-desk/round5-bridge) reproduced ----------
BUDGET = 5000          # scene nodes. A lens that needs more must say `clamp N` on its repeat and let the text say the rest.
# 30 Sep: it was 1500, a round guard Astra's audit asked for against runaway repeats (18 Sep: 'no explicit negotiated
# resource bound'), never a measured limit; the Desktop kept reaching it. It stays a guard, not a working size: deskd
# now rebuilds a scene only when what it shows changed, and the painter keeps its last good paint when one is refused.


def _outside_quotes(line, sep):
    """Split `line` at `sep` wherever it is not inside double quotes."""
    out, cur, q, i = [], "", False, 0
    while i < len(line):
        if line[i] == '"' and (i == 0 or line[i - 1] != "\\"):
            q = not q
        if not q and line.startswith(sep, i):
            out.append(cur)
            cur, i = "", i + len(sep)
            continue
        cur += line[i]
        i += 1
    out.append(cur)
    return out


def _roles():
    try:
        src = (pathlib.Path(__file__).resolve().parent / "desk-shell" / "style" / "calm.style").read_text(encoding="utf-8")
        return {l.split()[1] for l in src.splitlines() if l.startswith("role ") and len(l.split()) > 1}
    except OSError:
        return None


# F7 (research/command-center): a style is world data. A note tagged `style` whose title is the style's name holds its
# source, so it is edited, undone, forked and merged like anything else; a lens names its style with prop style=<name>.
# The file desk-shell/style/<name>.style is only the seed for a world that has no such note.
def find_style(desk, name):
    w = desk.world
    hits = [s for s in w.subjects.values() if "style" in (s.get("tags") or []) and s["title"].lower() == name.lower()]
    placed = [s for s in hits if w.appearances_of(s["id"])]
    return (placed or hits or [None])[0]


def style_source(desk, name):
    """-> {name, text, origin, rev} for a style by name, from the world, else from the seed file; None if neither."""
    s = find_style(desk, name)
    if s is not None:
        return {"name": name, "text": s["text"], "origin": s["id"], "rev": f"{s['id']}r{s['rev']}"}
    f = pathlib.Path(__file__).resolve().parent / "desk-shell" / "style" / f"{pathlib.Path(name).name}.style"
    if f.exists():
        import hashlib
        text = f.read_text(encoding="utf-8")
        return {"name": name, "text": text, "origin": "file", "rev": "file-" + hashlib.sha256(text.encode()).hexdigest()[:10]}
    return None


def style_roles(desk, name):
    """The role names a lens may use under style `name`; None keeps the old behavior (calm.style, the file)."""
    if not name:
        return None
    st = style_source(desk, name)
    if st is None:
        raise LensRefusal(f"no style {name!r}: a style is a note tagged style titled {name!r} (or desk-shell/style/{name}.style)")
    return {l.split()[1] for l in st["text"].splitlines() if l.startswith("role ") and len(l.split()) > 1}


def pulsing_roles(desk, name):
    """a1140: the roles whose words include `pulse` in the style the painter installs for a lens (its style=, else calm).
    The painter moves them, so the print says so: a reader of the text must learn what the eye sees moving. Read with
    the painter's own parse (style_parse, below); a style the painter refuses paints nothing, so nothing pulses."""
    st = style_source(desk, name or "calm") or {}
    try:
        roles = style_parse(st.get("text") or "")["roles"]
    except LensRefusal:
        return set()
    return {n for n, r in roles.items() if "pulse" in r["props"]}


def mark_pulse(node, roles):
    """Set `pulse` on every node whose role pulses. Printer-side only: emit() never sends it to the painter."""
    if roles and node.get("role") in roles:
        node["pulse"] = True
    for k in node.get("kids") or []:
        mark_pulse(k, roles)


# a1101 (Pike e2213: "appending style roles says ok but never says the style still parses"): the painter's own parse
# and property reader (desk-shell/style/style.js: parse, check, resolveTokens, prop), mirrored line for line so an edit's
# receipt can say what the painter will do with it. test_scene checks this mirror against node running style.js.
_HEX = re.compile(r"^#[0-9a-fA-F]{3,8}$")


def style_parse(src):
    """-> {tokens, roles: {name: {props, line}}, clauses, fonts, themes} or raises LensRefusal('line N: ...') as
    Style.parse throws a Refusal."""
    out = {"tokens": {}, "roles": {}, "clauses": [], "fonts": {}, "themes": {}}
    theme = None
    for n, raw in enumerate(re.split(r"\r?\n", src), 1):
        indented = bool(re.match(r"^\s+\S", raw))
        s = re.sub(r"\s+#\s.*$", "", raw.strip()).strip()
        if not s or (s.startswith("#") and not re.match(r"^#[0-9a-fA-F]{3,8}\b", s)):
            continue
        m = re.match(r"^theme\s+(\S+)\s+of\s+(\S+)$", s)
        if m:
            theme = m.group(1)
            out["themes"][theme] = {"of": m.group(2), "tokens": {}, "line": n}
            continue
        m = re.match(r"^font\s+([\w-]+)\s*=\s*(.+)$", s)
        if m:
            theme = None
            out["fonts"][m.group(1)] = n
            continue
        m = re.match(r"^token\s+([\w.]+)\s*=\s*(.+)$", s)
        if m:
            if theme and indented:
                out["themes"][theme]["tokens"][m.group(1)] = m.group(2).strip()
            else:
                theme = None
                out["tokens"][m.group(1)] = m.group(2).strip()
            continue
        if theme and indented and re.match(r"^(role|when|present)\s", s):
            raise LensRefusal(f"line {n}: a theme may redefine tokens, not roles ({s.split()[1]!r})")
        if re.match(r"^present\s", s):
            raise LensRefusal(f"line {n}: `present` was removed. A lens says which parts are drawn")
        if re.match(r"^(role|when)\s", s):
            at, kw = s.rfind(" : "), s.split()[0]
            if at < 0:
                raise LensRefusal(f'line {n}: a {kw} line needs " : " with spaces before its properties: {kw} <name> : <property>, <property>')
            head, body = re.sub(r"^\w+\s+", "", s[:at], count=1).strip(), s[at + 3:].strip()
            theme = None
            hx = re.search(r"#[0-9a-fA-F]{3,8}\b", body)
            if hx:
                raise LensRefusal(f"line {n}: colours are named here; {hx.group(0)!r} may only appear on a token line")
            px = re.search(r"\b(\d+(?:\.\d+)?)px\b", body)
            if px:
                raise LensRefusal(f"line {n}: {px.group(0)} is not on the scale; lengths are gap, gap xN, gap /N, or an em")
            props = [x.strip() for x in body.split(",") if x.strip()]
            if kw == "role":
                out["roles"][head] = {"props": props, "line": n}
            else:
                out["clauses"].append({"sel": head, "props": props, "line": n})
            continue
        raise LensRefusal(f'line {n}: not a token, role, clause, font or theme line: "{s}"')
    return out


def _style_tokens(st):
    """Style.js resolveTokens, as types only: name -> 'colour' | 'length' | 'text' | 'word' | None."""
    raw, done = dict(st["tokens"]), {}

    def get(name, seen):
        if name in done:
            return done[name]
        if name not in raw or name in seen:
            return None
        seen.add(name)
        v = raw[name].strip()
        if _HEX.match(v):
            done[name] = "colour"
            return "colour"
        m = re.match(r"^([\w.]+)\s+at\s+([\d.]+)%?$", v)
        if m:
            base = get(m.group(1), seen)
            paper = bool(_HEX.match(raw.get("paper", ""))) or get("paper", {"__"})
            if base == "colour" and paper:
                done[name] = "colour"
                return "colour"
        if re.match(r"^\d+(\.\d+)?$", v):
            done[name] = "length"
        elif re.match(r"^([\w-]+)\s+([\d.]+)/([\d.]+)$", v):
            done[name] = "text"
        else:
            done[name] = "word"
        return done[name]
    return {k: get(k, set()) for k in raw}


def _style_prop_ok(p, T):
    """Whether style.js prop() can read property `p` (it returns css or a part), under token types T. -> (ok, why)."""
    def ln(e):
        m = re.match(r"^([\w.]+)\s*x\s*([\d.]+)$", e) or re.match(r"^([\w.]+)\s*/\s*([\d.]+)$", e) or re.match(r"^([\w.]+)$", e)
        if m and T.get(m.group(1)) == "length":
            return "n"
        return "em" if re.match(r"^([\d.]+)em$", e) else None

    def col(e):
        m = re.match(r"^([\w.]+)\s+at\s+([\d.]+)%?$", e)
        if m and T.get(m.group(1)) == "colour" and T.get("paper"):
            return True
        return T.get(e) == "colour"
    for pat, fn in ((r"^(show|hide)\s+\w+$", lambda m: True), (r"^on\s+(.+)$", lambda m: col(m.group(1))),
                    (r"^([\w.]+)\s*->\s*(.+)$", lambda m: col(m.group(2))), (r"^edge\s+(.+)$", lambda m: col(m.group(1))),
                    (r"^border\s+(top|right|bottom|left)\s+(.+)$", lambda m: col(m.group(2))),
                    (r"^corner\s+(.+)$", lambda m: ln(m.group(1)) == "n"), (r"^pad\s+(top|right|bottom|left)\s+(.+)$", lambda m: ln(m.group(2)) == "n"), (r"^pad\s+(.+)$", lambda m: ln(m.group(1)) == "n"),
                    (r"^space\s+(above|below)\s+(.+)$", lambda m: ln(m.group(2)) == "n"), (r"^between\s+(.+)$", lambda m: ln(m.group(1)) == "n"),
                    (r"^width\s+(.+)$", lambda m: ln(m.group(1)) is not None), (r"^lift\s+(.+)$", lambda m: ln(m.group(1)) == "n" and T.get("ink") == "colour")):
        m = re.match(pat, p)
        if m:
            if fn(m):
                return True, ""
            if re.search(r"\s\d+(\.\d+)?$", p) and not re.search(r"[x/]\s*\d+(\.\d+)?$", p):
                return False, "a bare number is not on the scale: say gap, gap xN or gap /N"
            return False, "names no token of the right kind"
    if p == "pulse":                               # a1140: the one motion
        return True, ""
    if re.match(r"^text\b", p):
        if T.get(p.split()[0] if p.startswith("text.") else "text") != "text":
            return False, "names no text token"
        m = re.search(r"\bat\s+([\d.]+)\b", p)
        return (False, f'"text at {m.group(1)}" is not a step of the ramp') if m else (True, "")
    return (True, "") if col(p) else (False, "is no property and no colour token")


def style_check(src):
    """-> {"refusal": str or None, "roles": n, "tokens": n, "unread": [(role, prop, line, why)]}: what the painter
    will make of this style text."""
    try:
        st = style_parse(src)
    except LensRefusal as e:
        return {"refusal": str(e), "roles": 0, "tokens": 0, "unread": []}
    T = _style_tokens(st)
    unread = [(name, p, r["line"], why) for name, r in st["roles"].items() for p in r["props"]
              for ok, why in [_style_prop_ok(p, T)] if not ok]
    return {"refusal": None, "roles": len(st["roles"]), "tokens": len(st["tokens"]), "unread": unread}


def _cmd_value(v):
    """A value going inside a quoted desk command keeps its quotes and backslashes (Astra: `She said "yes"` lost them)."""
    return str(v).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


# ---- rows: parts of the world that are not appearances, made repeatable ------------------------------------
# Moss, Lark and Wren hit one wall from three sides: a lens repeats over a selection, and sections, comments,
# actors, events and worktrees were not selectable. Each source below is a fact the desk already printed
# somewhere; here it gets named fields. `rows <source>` prints the same rows in the desk, so a lens never sees
# anything the terminal cannot.
SOURCES = {
    "sections": ("sections:<id>", ("item", "heading", "words", "text", "index")),
    "comments": ("comments:<id>", ("item", "cid", "by", "text", "state")),
    "actors": ("actors", ("name", "acts", "last", "verb", "target", "read", "behind")),
    "events": ("events", ("eid", "verb", "target", "by", "at", "merged")),
    "worktrees": ("worktrees", ("name", "by", "commands", "merged", "behind")),
    # the command center (research/command-center): a chat's lines, and what the house observes of its residents
    # a1581: line is the chat line (a thing, m<n>) the text line belongs to, to who it addresses, edited 'edited' or ''
    "messages": ("messages:<id>", ("item", "who", "said", "index", "at", "line", "to", "edited")),
    # Alex, 30 Sep: what's for me, one list, oldest first like a chat (newest at the bottom), each line saying which
    # chat it came from and when
    # (a3319: these rows are `sayings for:<name>` under their first name, kept so nothing printed goes false)
    "inbox": ("inbox:<name>", ("item", "chat", "who", "said", "at", "open", "index", "eid", "line", "before")),
    # a3319 (lines phase 2): chat lines and comments as they are stored, two kinds read through one showing. `what` is
    # line or comment, `saying` its own id (m<n> or c<n>), `name` its writer as a word an @ can call; answered and
    # before are filled when for:<name> says whose For you it is
    "sayings": ("sayings [for:<name>] [in:<id>]", ("item", "what", "saying", "by", "name", "at", "in", "to", "said",
                                                    "answered", "edited", "before", "state", "eid")),
    # a1581 (Juniper c1695: lines out of every default find, but reachable when asked): every chat line as a thing,
    # oldest first, in one chat or all; by and at read from the event that made it ('unknown' when none can be found)
    "lines": ("lines[:<chat>]", ("item", "chat", "line", "who", "by", "at", "to", "said", "edited", "reply_to", "eid")),
    "house": ("house[:<corner>]", ("resident", "corner", "doing", "turns", "since", "beat", "fresh", "room", "item")),   # item: the corner, so a gesture on a row acts on it (30 Sep, wake/rest)
    # what each resident wrote, its last turns, oldest first like a chat (Alex, 29 Sep: to see their turns and text;
    # 30 Sep: newest at the bottom on every chat-like list, so a lens shows the newest with `clamp last N, scroll end`)
    "turns": ("turns[:<corner>]", ("resident", "corner", "turn", "at", "said", "acts")),
}
NAMES = NAMES + tuple(f for _, fs in SOURCES.values() for f in fs)
HOUSE_STATE = pathlib.Path(__file__).resolve().parent / "house-state"   # <world>/house.json, written by house.py


def turn_rows(desk, corner=None):
    """The replies the house kept for each resident (house.json `said`), oldest first. `acts` counts the lines that
    reached the desk (those beginning with >); the rest is the resident's own thinking, shown as written."""
    import json
    import time
    try:
        world = (getattr(desk, "_session", "") or "").split("@")[0]
        st = json.loads((HOUSE_STATE / world / "house.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if st.get("world") != world:
        return []
    out = []
    for cid, r in sorted((st.get("residents") or {}).items()):
        if corner and cid != corner:
            continue
        for t in r.get("said") or []:
            at = t.get("at")
            out.append({"resident": r.get("actor") or "(no name yet)", "corner": cid, "turn": t.get("n", 0),
                        "at": time.strftime("%H:%M", time.localtime(at)) if at else "", "said": t.get("text") or "(nothing)",
                        "acts": sum(1 for l in (t.get("text") or "").splitlines() if l.lstrip().startswith(">")), "_t": at or 0})
    out.sort(key=lambda r: r.pop("_t"))
    return out


def _clock(at, now=None):
    """'08:15' today, '29 Sep 22:38' another day: small enough to sit beside every line."""
    import datetime
    try:
        t = datetime.datetime.fromisoformat(str(at))
    except ValueError:
        return ""
    today = (now or datetime.datetime.now()).date()
    return t.strftime("%H:%M") if t.date() == today else f"{t.day} {t.strftime('%b %H:%M')}"


def line_times(w, sid):
    """When each line of chat `sid` was added: its append event's time and id, matched by the signed line itself (the
    event keeps it whole). -> [(iso, eid)] per non-blank line, in order; a line no append event made has ('', '')."""
    key = (id(w), len(w.events))
    cache = line_times.__dict__.setdefault("cache", {})
    if cache.get("key") != key:
        by = {}
        for e in w.events:
            args = e.get("args") or {}
            if e.get("verb") != "edit" or e.get("undone") or not isinstance(args, dict) or "append" not in args:
                continue
            for s in e.get("changed") or ():
                if s in w.subjects and w.subjects[s]["kind"] == "chat":
                    for l in str(args["append"]).splitlines():
                        if l.strip():
                            by.setdefault(s, {}).setdefault(l.strip(), []).append((e.get("at", ""), e["id"]))
        cache.clear()
        cache.update(key=key, by=by)
    pending = {k: list(v) for k, v in cache["by"].get(sid, {}).items()}
    return [pending[l.strip()].pop(0) if pending.get(l.strip()) else ("", "")
            for l in w.subjects[sid]["text"].splitlines() if l.strip()]


def text_lines(w, sid):
    """a1581: chat `sid`'s non-blank text lines, each with the chat line (the thing) it belongs to and when that was
    said, read from the event that made it -> [(text, line or None, (iso, eid))]. A chat with no lines (one from
    before a1581) is matched by its words, as line_times always did."""
    s = w.subjects[sid]
    if s.get("lines") is None:
        return [(l, None, t) for l, t in zip([l for l in s["text"].splitlines() if l.strip()], line_times(w, sid))]
    out = []
    for line in s["lines"]:
        e = w.event_by_id(line.get("ev"))
        parts = [l for l in line["text"].split("\n") if l.strip()]
        for k, l in enumerate(parts):
            if line.get("edited") and k == len(parts) - 1:
                l += f"  (edited, {line['id']})"        # as read prints it: a change to what was said is never silent
            out.append((l, line, (e.get("at", ""), e["id"]) if e else ("", "")))
    return out


def source_head(source):
    """The row source a repeat's `of` names, or its first word when it names none: the word before the first colon
    ('messages:a12'), or `sayings`, whose terms follow it after a space ('sayings for:alex in:a12')."""
    src = str(source).strip()
    return "sayings" if src.split(" ")[0] == "sayings" else src.partition(":")[0]


def saying_rows(desk, terms=""):
    """a3319 (lines phase 2; Pike c3323: unify the reading first): the SAYINGS of the desk, chat lines and comments
    as they are stored, two kinds read through one showing, oldest first like a chat. Nothing is migrated and no id
    is new: `saying` is a line's m<n> or a comment's c<n>, `what` says which. `by`, `at`, `in` (the chat, or the thing
    commented on) and `to` are read as each kind keeps them: a line's signature, its event's time and its stored
    to=; a comment's author (persons.comment_by), its event's time, and the address stored on that event (world's
    comment; a comment from before a3319 has none, and addresses no one here).

    Terms, in any order: `in:<id>` keeps one chat's lines or one thing's comments; `for:<name>` keeps what is shown
    in that person's For you, by the house's one showing rule (rooms.shown, which asks rooms.calls: nothing here
    restates it), leaves out what they wrote themselves, and fills `answered` and `before`, which are facts about a
    saying and a person:
      answered  a line: 'yes' when a line of theirs follows it in that chat, else 'no' (today's rule: who wrote last).
                a comment: 'yes' when they replied to it or commented later on that thing; 'withdrawn' when its
                writer resolved it; else 'no'. Someone else's resolve doesn't end it for them (Pike c3323): `state`
                then says 'resolved by <name>', and their answer is a new comment on the thing.
      before    a2692: 'addressed to you before you were a member of this chat', for a line that never knocked them
                (Pike c2697: the knock is a happening, read as membership was; For you is a showing, read as it is).
    A row also answers to the names For you's rows had (chat, who, open, index, line), so `inbox:<name>` is this
    source under its first name."""
    import persons
    import rooms
    from world import addressed_before
    w = desk.world
    me, only = "", None
    for t in str(terms).replace(",", " ").split():
        k, _, v = t.partition(":")
        if k == "for" and v:
            me = v.lower()
        elif k == "in" and v:
            nid = desk._resolve(v)
            only = (w.nodes.get(nid) or {}).get("subject") or (nid if nid in w.subjects else None)
            if only is None:
                raise LensRefusal(f"sayings in:{v}: {v} has no lines or comments to list")
        else:
            raise LensRefusal(f"sayings: unknown term {t!r}; sayings [for:<name>] [in:<id>], e.g. sayings for:$me")
    where = {}
    for nid, n in w.nodes.items():
        if n["type"] == "appearance" and n["subject"] not in where:
            where[n["subject"]] = nid
    made, closed = persons.comment_events(w), None
    flip = {"yes": "no", "no": "yes", "withdrawn": "no"}
    out = []
    for sid, s in w.subjects.items():
        if sid not in where or (only and sid != only):
            continue
        if s["kind"] == "chat" and not (me and not rooms.is_member(w, s, me)):
            tl = text_lines(w, sid)
            mine_after = False              # walking back from the end: has a line of mine come after this one?
            for k in range(len(tl) - 1, -1, -1):
                text, line, (at, eid) = tl[k]
                m = w.SPEAKER.match(text)
                who = m.group(1).lower() if m else ""
                if me and who == me:
                    mine_after = True
                    continue
                if me and not who:
                    continue
                said = text[m.end():] if m else text
                # a1581: a line's address is its writer's stored word, never its words searched again; a chat from
                # before lines is read by the rule it was written under (every @name outside quotes)
                to = line["to"] if line is not None else addressed_before(said)
                before = ""
                if me:
                    if not rooms.shown(w, s, to, me):
                        continue
                    if eid and rooms.calls(w, s, [n for n in to if n not in rooms.EVERYONE], me) \
                            and not rooms.is_member(w, s, me, at=eid):
                        before = "addressed to you before you were a member of this chat"
                by = m.group(0).rstrip(" \t:") if m else ""
                answered = ("yes" if mine_after else "no") if me else ""
                # eid keys the row (the line's own event), so a line keeps its place in the painter as newer ones arrive
                out.append({"item": where[sid], "what": "line", "saying": line["id"] if line else "", "by": by,
                            "name": who, "at": _clock(at), "in": s["title"], "to": ", ".join(to), "said": said,
                            "answered": answered, "edited": "edited" if line and line.get("edited") else "",
                            "before": before, "state": "", "eid": eid or f"{where[sid]}-{k + 1}",
                            "chat": s["title"], "who": by, "open": flip.get(answered, ""), "index": k + 1,
                            "line": line["id"] if line else "", "_t": (at or "", _enum(eid))})
        cs = s.get("comments") or []
        for i, c in enumerate(cs):
            e = made.get(c["id"])
            writer = str(c.get("by") or "").split("/")[0].lower()
            to = (e or {}).get("to")
            if me and (rooms.same_person(w, writer, me) or to is None or not rooms.shown(w, s, to, me, comment=True)):
                continue
            state = "open"
            if c.get("resolved"):
                if closed is None:
                    closed = {(x.get("args") or {}).get("id"): x for x in w.events
                              if x.get("verb") == "resolve" and not x.get("undone")}
                r = closed.get(c["id"])
                rby = str((r or {}).get("by") or "").split("/")[0].lower()
                state = "withdrawn" if r and rooms.same_person(w, rby, writer) else \
                    "resolved by " + (rooms.shown_name(w, rby) if r else "someone")
            answered = ""
            if me:
                mine = any(rooms.same_person(w, str(x.get("by") or "").split("/")[0], me)
                           for x in list(c.get("replies") or []) + cs[i + 1:])
                answered = "yes" if mine else "withdrawn" if state == "withdrawn" else "no"
            by = str(persons.comment_by(w, c, e) or "")
            by = by[:1].upper() + by[1:]
            at = (e or {}).get("at", "")
            out.append({"item": where[sid], "what": "comment", "saying": c["id"], "by": by, "name": writer,
                        "at": _clock(at), "in": s["title"], "to": ", ".join(to or []), "said": c["text"],
                        "answered": answered, "edited": "", "before": "", "state": state,
                        "eid": e["id"] if e else c["id"], "chat": s["title"], "who": by, "open": flip.get(answered, ""),
                        "index": i + 1, "line": "", "_t": (at or "", _enum(e["id"] if e else ""))})
    out.sort(key=lambda r: r.pop("_t"))
    return out


def _enum(eid):
    """An event id's number ('e5967' -> 5967), 0 when it has none: sayings of one second stay in the order said."""
    d = "".join(ch for ch in str(eid or "") if ch.isdigit())
    return int(d) if d else 0


def line_rows(desk, chat=None):
    """a1581: the chat lines (things, m<n>) of one chat or of every chat on the desk, oldest first. A line spoken over
    several text lines is one row; `said` is its words after the signature, `to` who its writer addressed."""
    import persons
    w = desk.world
    sid = w.subject_of(chat) if chat else None
    if chat and (sid is None or w.subjects[sid]["kind"] != "chat"):
        raise LensRefusal(f"lines:{chat}: {chat} is not a chat")
    out = []
    for s in ([w.subjects[sid]] if sid else w.subjects.values()):
        apps = w.appearances_of(s["id"])
        if s["kind"] != "chat" or not apps or s.get("lines") is None:
            continue
        for l in s["lines"]:
            e = w.event_by_id(l.get("ev"))
            m = w.SPEAKER.match(l["text"])
            out.append({"item": apps[0], "chat": s["title"], "line": l["id"], "who": m.group(0).rstrip(" \t:") if m else "",
                        "by": persons.by(w, e) if e else "unknown",      # a1568: the event's person, as printed
                        "at": _clock(e.get("at", "")) if e else "", "to": ", ".join(l["to"]),
                        "said": l["text"][m.end():] if m else l["text"], "edited": "edited" if l.get("edited") else "",
                        "reply_to": l.get("reply_to", ""), "eid": l.get("ev") or l["id"], "_t": (e or {}).get("at", "")})
    out.sort(key=lambda r: r.pop("_t") or "")
    return out


def away(desk):
    """a2844: who is away in a version of the code, as the door observes it (its visits.json, beside the house's state):
    actor -> '<commission>@<commit>'. Like the house's rows, an outside observation, never an event of this world."""
    import json
    try:
        world = (getattr(desk, "_session", "") or "").split("@")[0]
        st = json.loads((HOUSE_STATE / "visits.json").read_text(encoding="utf-8"))
        if st.get("world") != world:
            return {}
        return {str(a).lower(): str(v.get("label") or v.get("in")) for a, v in (st.get("away") or {}).items()}
    except (OSError, ValueError, AttributeError):
        return {}


def house_rows(desk, corner=None):
    """What the house observes, read from its own state (not the world's history: an outside resource with observed
    status). `fresh` says whether the house itself is alive: its heartbeat is written every two seconds, and a beat
    older than 30 s is printed as `stale`, and then `doing` says the house stopped rather than repeating its last
    observation as if it were current. Reading the clock here is a host read, like $today."""
    import json
    import time
    import rooms
    try:
        world = (getattr(desk, "_session", "") or "").split("@")[0]
        st = json.loads((HOUSE_STATE / world / "house.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if st.get("world") != world:
        return []
    age = time.time() - float(st.get("beat") or 0)
    fresh = "live" if age < 30 else f"stale {int(age // 60)}m" if age < 3600 else f"stale {int(age // 3600)}h"
    out, gone = [], away(desk)
    for cid, r in sorted((st.get("residents") or {}).items()):
        if corner and cid != corner:
            continue
        last = r.get("last_turn")
        doing = (r.get("doing") or "?") if fresh == "live" else "house " + fresh.replace("stale", "stopped") + " ago"
        if fresh == "live" and doing == "resting" and r.get("rest_until"):     # a rest the resident timed itself
            until = float(r["rest_until"])
            fmt = "%H:%M" if until - time.time() < 86400 else "%a %H:%M"
            doing = "resting until " + time.strftime(fmt, time.localtime(until))
        # a1062: when the house will next wake a resting resident on its own (a timed rest's end, an open objective's
        # breather, wake_every): the latest a line held for them waits
        wakes = r.get("wakes_at") if fresh == "live" and doing.startswith("resting") else None
        wakes = time.strftime("%H:%M" if float(wakes) - time.time() < 86400 else "%a %H:%M", time.localtime(float(wakes))) if wakes else ""
        room = rooms.room_of(desk.world, r.get("actor")) if r.get("actor") else None    # a678: where they are, a world fact
        out.append({"item": cid, "resident": r.get("actor") or "(no name yet)", "corner": cid, "doing": doing,
                    "turns": r.get("turns", 0), "since": time.strftime("%H:%M", time.localtime(last)) if last else "",
                    "beat": time.strftime("%H:%M:%S", time.localtime(st.get("beat") or 0)), "fresh": fresh,
                    # a2844: someone visiting a version is not in a room of this world: the door says where they are
                    "room": "away in " + gone[str(r.get("actor")).lower()] if str(r.get("actor")).lower() in gone else
                            desk.world.nodes[room]["title"] if room else "", "wakes": wakes})
    return out


def rows(desk, source, session=None):
    """-> list of dicts, or None when `source` is not a row source (then it is an ordinary selection)."""
    w = desk.world
    if source_head(source) == "sayings":
        return saying_rows(desk, source.strip()[len("sayings"):])
    head, _, arg = source.strip().partition(":")
    if head not in SOURCES or (head not in ("house", "turns", "lines") and (head in ("sections", "comments", "messages", "inbox")) != bool(arg)):
        return None      # sections, comments and messages need an id, inbox a name; house, turns and lines one or none; the rest none
    if head == "inbox":
        return saying_rows(desk, "for:" + arg)
    if head == "lines":
        return line_rows(desk, desk._resolve(arg) if arg else None)
    if head == "house":
        return house_rows(desk, desk._resolve(arg) if arg else None)
    if head == "turns":
        return turn_rows(desk, desk._resolve(arg) if arg else None)
    if arg:
        nid = desk._resolve(arg)
        s = w.subjects.get((w.nodes.get(nid) or {}).get("subject")) or w.subjects.get(nid)
        if s is None:
            raise LensRefusal(f"{source}: {arg} has no content to take {head} from")
    if head == "sections":
        return [{"item": nid, "heading": h or "(before the first heading)", "words": len(b.split()), "text": b, "index": k}
                for k, (h, b) in enumerate(w.sections(s["text"]), 1)]
    if head == "comments":
        return [{"item": nid, "cid": c["id"], "by": c["by"], "text": c["text"], "state": "resolved" if c["resolved"] else "open"}
                for c in s.get("comments", [])]
    if head == "messages":
        # a chat's lines: each is signed by its speaker (world.apply signs a chat line with its actor); a line a rule
        # added keeps its whole signature in who ('Alex, via rule r3'), so it never reads as Alex speaking
        out = []
        tl = text_lines(w, s["id"]) if s["kind"] == "chat" else [(l, None, ("", "")) for l in s["text"].splitlines() if l.strip()]
        for k, (text, line, (at, _eid)) in enumerate(tl, 1):
            m = w.SPEAKER.match(text)
            out.append({"item": nid, "who": m.group(0).rstrip(" \t:") if m else "", "said": text[m.end():] if m else text, "index": k,
                        "at": _clock(at), "line": line["id"] if line else "", "to": ", ".join(line["to"]) if line else "",
                        "edited": "edited" if line and line.get("edited") else ""})
        return out
    if head == "events":
        return [{"eid": e["id"], "verb": e["verb"], "target": e["target"], "by": e["by"], "at": e.get("at", e.get("day", "")),
                 "merged": e.get("merged", "")} for e in w.events[-20:]][::-1]
    if head == "actors":
        out, total = {}, len(w.events)
        for e in w.events:
            r = out.setdefault(e["by"], {"name": e["by"], "acts": 0, "read": "", "behind": ""})
            r.update(acts=r["acts"] + 1, last=e.get("at", e.get("day", "")), verb=e["verb"], target=e["target"])
        for a, v in (getattr(desk, "_per", None) or {}).items():
            r = out.setdefault(a, {"name": a, "acts": 0, "last": "", "verb": "", "target": ""})
            r.update(read=v[2], behind=total - v[2])
        return sorted(out.values(), key=lambda r: r.get("last") or "", reverse=True)
    if head == "worktrees":
        import pickle
        import worktree
        base = (session or getattr(desk, "_session", "") or "").split("@")[0]
        out = []
        for p in sorted(worktree.SESSIONS.glob(f"{base}@*.pickle")) if base else []:
            wt = getattr(pickle.loads(p.read_bytes()), "_wt", None) or {}
            out.append({"name": p.stem.split("@", 1)[1], "by": wt.get("by", ""), "commands": len(wt.get("journal", [])),
                        "merged": wt.get("merged_n", 0), "behind": len(w.events) - wt.get("base_events", 0)})
        return out


def rows_text(desk, source):
    rs = rows(desk, source)
    if rs is None:
        raise LensRefusal("rows <source>. Sources: " + ", ".join(v[0] for v in SOURCES.values()))
    fields = SOURCES[source_head(source)][1]
    lines = [f"rows {source}: {len(rs)}  (fields: {' '.join('$' + f for f in fields)})"]
    for r in rs:
        lines.append("  " + " · ".join(f"{f}={str(r.get(f, ''))[:60]!r}" if " " in str(r.get(f, "")) else f"{f}={str(r.get(f, ''))[:60]}" for f in fields if f != "text" or len(fields) < 6))
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------------------------------------
# Stage 1, parse. The surface words are a table: each row is the word, the shape a reader sees in a refusal, and the
# setter that puts it on the part. The refusal vocabulary is printed from this table, so it cannot drift from the grammar
# (Sable's probe 7: `if` was refused with a list of eleven words that omitted seven the grammar had). Pike, round six.
# ---------------------------------------------------------------------------------------------------------------------

def _w_layout(node, p, val, n, env):
    node["layout"] = p


def _w_grid(node, p, val, n, env):
    """`grid 1 3 3 1`, `grid 1fr fit 2fr`: tracks in fr (a bare number is fr) or fit (as wide as the widest cell)."""
    toks = val.split()
    tracks = []
    for t in toks:
        if t == "fit" or re.fullmatch(r"\d+gap", t):
            tracks.append(t)
        elif re.fullmatch(r"\d+(\.\d+)?(fr)?", t) and float(t.rstrip("fr")) > 0:
            tracks.append(t if t.endswith("fr") else t + "fr")
        else:
            raise LensRefusal(f"line {n}: `grid <tracks>`: each track is a positive number of fr (1, 3fr), fit, or a gap (12gap); got {t!r}")
    if not tracks:
        raise LensRefusal(f"line {n}: `grid <tracks>`, for example `grid 1 3 3 1`; got {p!r}")
    node["layout"], node["tracks"] = "grid", tracks


def _w_gap(node, p, val, n, env):
    # F10 (research/command-center): a lens names no size. `gap` is one step of the style's spacing scale, `gap x2` two,
    # `gap /2` half, as tracks already say `12gap`. A bare number is the older pixel form, kept for the lenses using it.
    v = val.strip()
    if v.isdigit():
        node["gap"] = int(v)
        return
    m = re.fullmatch(r"(?:([x/])\s*(\d+(?:\.\d+)?))?", v)
    if not m:
        raise LensRefusal(f"line {n}: `gap`, `gap x2` or `gap /2` (steps of the style's gap); got {p!r}")
    node["gap"] = (m.group(1) or "x") + (m.group(2) or "1")


def _w_scroll(node, p, val, n, env):
    if val not in ("none", "scroll", "end"):
        raise LensRefusal(f"line {n}: `scroll none|scroll|end` (end keeps the newest in view); got {p!r}")
    node["scroll"] = val


def _w_fold(node, p, val, n, env):
    """`fold` or `fold "Projects"`: folded by default, until a viewer unfolds it (a choice that makes no event); the
    label is the lens's words for the handle, else the part's text or name. Alex, 29 Sep ("a collapsing system", and the
    world log "in a menu like the terminal"): `open` shows it unfolded until the viewer folds it, and `float` draws its
    open contents over the page, below the handle, instead of pushing the page down (a menu). A folded part gives up
    its `share`, so its siblings take the room."""
    # Alex, 29 Sep ("click on tasks to expand them"): the label is a template filled like text (`fold "$title"`), and
    # `handle <role>` gives the handle a look of the lens's choosing (a card's title rather than a tool).
    # Alex, 30 Sep ("when viewing the turns of an agent it collapses their to me text"): `group <name>` makes an
    # accordion: opening a fold folds its open siblings in the same group (the viewer's folds, no event).
    m = re.fullmatch(r'("[^"]+")?\s*(.*)', val.strip())
    mods = m.group(2).split() if m else ["?"]
    handle = group = None
    if "group" in mods:
        k = mods.index("group")
        group = mods[k + 1] if k + 1 < len(mods) else None
        del mods[k:k + 2]
        if not group or not re.fullmatch(r"[\w.-]+", group):
            raise LensRefusal(f'line {n}: `fold ... group <name>`: siblings in one group fold when another opens; got {p!r}')
    if "handle" in mods:
        k = mods.index("handle")
        handle = mods[k + 1] if k + 1 < len(mods) else None
        del mods[k:k + 2]
        if not handle or not re.fullmatch(r"[\w.-]+", handle):
            raise LensRefusal(f'line {n}: `fold ... handle <role>`: the role the handle wears; got {p!r}')
        if env["roles"] is not None and handle not in env["roles"]:
            raise LensRefusal(f"line {n}: no role {handle!r} for the fold's handle in {'style ' + env['style'] if env.get('style') else 'calm.style'}. Roles: {' '.join(sorted(env['roles']))}")
    if any(x not in ("open", "float") for x in mods) or len(set(mods)) != len(mods):
        raise LensRefusal(f'line {n}: `fold ["<label for the handle>"] [open] [float] [handle <role>] [group <name>]`; got {p!r}')
    node["fold"] = m.group(1).strip('"') if m.group(1) else True
    node["fold_open"], node["fold_float"], node["fold_handle"], node["fold_group"] = "open" in mods, "float" in mods, handle, group


def _w_measure(node, p, val, n, env):
    if not re.fullmatch(r"\d+ch", val):
        raise LensRefusal(f"line {n}: `measure <n>ch` (at most that wide, centred); got {p!r}")
    node["measure"] = val


def _w_verbatim(node, p, val, n, env):
    node["wrap"] = "verbatim"     # as wide as its longest line, scrolling sideways: code, tables of text


def _w_lines(node, p, val, n, env):
    m = re.fullmatch(r"(\d+)\.\.(\d*)", val)
    if not m or int(m.group(1)) < 1 or (m.group(2) and int(m.group(2)) < int(m.group(1))):
        raise LensRefusal(f"line {n}: `lines <min>..<max>` (grows, then scrolls; `lines 3..` for no top); got {p!r}")
    node["lines"] = [int(m.group(1)), int(m.group(2)) if m.group(2) else None]


def _w_hint(node, p, val, n, env):
    m = re.fullmatch(r'"([^"]*)"', val)
    if not m or not m.group(1):
        raise LensRefusal(f'line {n}: `hint "<words shown while the text is empty>"`; got {p!r}')
    node["hint"] = m.group(1)


def _w_plain(node, p, val, n, env):
    node["plain"] = True          # Juniper a559: no runs; backticks print as the characters they are


def _w_marks(node, p, val, n, env):
    # Editor board a3486 (7 Oct): the words may carry marks, written in the text itself: **strong**, *stressed*,
    # [label](address). Read, they are drawn as marks; edited, they are their source (as code runs are, a559)
    node["marks"] = True


def _w_peek(node, p, val, n, env):
    node["peek"] = True           # a1032 (Alex: 'see what they are working on at a glance'): shown while its parent is folded


_RUNS = re.compile(r"```[^\n]*\n(.*?)```|`([^`\n]+)`", re.S)


_MARKS = re.compile(r"BS*BS*BS*(?=BSS)(?P<both>[^*BSn]+?)(?<=BSS)BS*BS*BS*|BS*BS*(?=BSS)(.+?)(?<=BSS)BS*BS*|BS*(?=BSS)([^*BSn]+?)(?<=BSS)BS*|BS[([^BS]BSn]+)BS]BS(([^)BSsBSn]+)BS)".replace("BS", chr(92)))


def marks_of(text):
    """One stretch of plain words -> runs, the marked ones carrying mark=strong|stress|both|link (a link its href). The
    grammar is closed: two stars, one star, three for both, [label](address); a star beside a space is a star."""
    out, at = [], 0
    for m in _MARKS.finditer(text):
        if m.start() > at:
            out.append({"text": text[at:m.start()]})
        if m.group("both") is not None:
            out.append({"text": m.group("both"), "mark": "both"})
        elif m.group(2) is not None:
            out.append({"text": m.group(2), "mark": "strong"})
        elif m.group(3) is not None:
            out.append({"text": m.group(3), "mark": "stress"})
        else:
            out.append({"text": m.group(4), "mark": "link", "href": m.group(5)})
        at = m.end()
    if at < len(text):
        out.append({"text": text[at:]})
    return out


def runs_of(text, marks=False):
    """Juniper a559: code spans and fences become runs at print, from this closed grammar, with no world effect; the
    words stay the part's source, so the printer's text and the fence are unchanged. -> [{text, role?, block?}] or None."""
    out, at = [], 0
    for m in _RUNS.finditer(text or ""):
        if m.start() > at:
            out.append({"text": text[at:m.start()]})
        out.append({"text": m.group(1), "role": "code", "block": True} if m.group(1) is not None else {"text": m.group(2), "role": "code"})
        at = m.end()
    if at < len(text or ""):
        out.append({"text": text[at:]})
    if marks:                              # marks are looked for in the plain stretches only: code keeps its stars
        out = [r2 for r in out for r2 in ([r] if r.get("role") else marks_of(r["text"]))]
    if not any(r.get("role") or r.get("mark") for r in out):
        return None
    return out


def _w_share(node, p, val, n, env):
    if not re.fullmatch(r"\d+(\.\d+)?", val) or float(val) <= 0:
        raise LensRefusal(f"line {n}: `share <weight>` (this child's share of its column or row); got {p!r}")
    node["share"] = float(val) if "." in val else int(val)


def _w_carry(node, p, val, n, env):
    node["carry"] = True          # Pike a361/c368: carry on the thing, `on drop <part>` on the receiver


def _w_role(node, p, val, n, env):
    # a1105 (Alex: 'objectives should have a light highlight on the whole card'): `role <name> when <selection>` lets a
    # part's look follow its thing's state. Several may follow the plain role; the first that holds wins, the scene
    # prints which and why, and a part none holds for keeps its plain role. The test is `only when`'s, either kind.
    val, _, cond = val.partition(" when ")
    if not re.fullmatch(r"[\w.-]+", val) or (_ and not cond.strip()):
        raise LensRefusal(f"line {n}: `role <name>` or `role <name> when <selection | expr>`; got {p!r}")
    cond = _one_test(cond.strip(), n)
    if env["roles"] is not None and val not in env["roles"]:
        raise LensRefusal(f"line {n}: no role {val!r} in {'style ' + env['style'] if env.get('style') else 'calm.style'}. Roles: {' '.join(sorted(env['roles']))}")
    if _:
        node["role_when"].append((val, cond.strip()))
    else:
        node["role"] = val


def _w_each(node, p, val, n, env):
    if not re.fullmatch(r"[\w.-]+", val):
        raise LensRefusal(f"line {n}: `each <part>`; got {p!r}")
    node["each"] = val


def _w_text(node, p, val, n, env):
    if not val:
        raise LensRefusal(f"line {n}: `text \"...\"`; got {p!r}")
    node["text"] = val.strip('"')
    # Juniper, Pike: a lens could not read a thing's own prop ($place). Any name outside NAMES is a prop; the
    # scene prints what it read and marks (no place) when the thing lacks it. Lark's $me now prints (no me): honest.
    node["props"] = [v for v, dot in re.findall(r"\$(\w+)(\.\w+)?", node["text"]) if not dot and v not in NAMES]


def _w_clamp(node, p, val, n, env):
    # 29 Sep (a repeat couldn't show the newest N; the Desktop's chats passed the scene budget): `clamp last N` keeps
    # the last N of a repeat, the newest lines of a chat, keyed as they would be without the clamp
    last = val.startswith("last ")
    num = val[5:].strip() if last else val
    if not num.isdigit():
        raise LensRefusal(f"line {n}: `clamp <number>` or, on a repeat, `clamp last <number>`; got {p!r}")
    node["clamp"] = int(num)
    if last:
        node["clamp_last"] = True


def _w_of(node, p, val, n, env):
    if not val:
        raise LensRefusal(f"line {n}: `of <selection | row source> [as <frame>]`; got {p!r}")
    node["of"], _, asname = val.partition(" as ")          # `of parts:$trip.item as stop`
    if asname:
        node["as"] = asname.strip()


def _w_by(node, p, val, n, env):
    # a1069/a1078: a repeat in the order of props, numbers ascending, a missing value last, ties in the order the things
    # were made. `by priority, rank`: the parts after the comma are more props (parse joins them), not words
    if not re.fullmatch(r"[\w.-]+( [\w.-]+)*", val or ""):
        raise LensRefusal(f"line {n}: `by <prop>[, <prop>]` on a repeat; got {p!r}")
    node["by"] = (node["by"] or []) + val.split()


def _w_count(node, p, val, n, env):
    if not val.strip():
        raise LensRefusal(f"line {n}: `count <selection or row source>`; got {p!r}")
    node["count"] = val.strip()       # a1101: '7 paused', without drawing the seven


def _w_over(node, p, val, n, env):
    val, _, asname = val.partition(" as ")       # Sable, 7 Oct: `over $comments as c` was refused by printing its own form
    val = val.strip()
    if not re.fullmatch(r"\$\w+", val):
        raise LensRefusal(f"line {n}: `over $<list> [as <frame>]` repeats over a list the current thing holds ($tags) or "
                          f"rows a derive named; got {p!r}. Rows from a source (comments:<id>, sections:<id>; the command "
                          f"`rows` lists them) go under `of`: `of comments:$item`")
    node["over"] = val[1:]
    if asname:
        node["as"] = asname.strip()


def _w_at(node, p, val, n, env):
    if val != "item":
        raise LensRefusal(f"line {n}: `at item`; got {p!r}")
    node["at"] = "item"


def _w_lens(node, p, val, n, env):
    if not re.fullmatch(r"[\w$.-]+", val):
        raise LensRefusal(f"line {n}: `lens <name>`; got {p!r}")
    node["lens"] = val


def _w_spread(node, p, val, n, env):
    # Astra's challenge: x = clamp(20 + order * spacing, 0, 440). Not arithmetic in the lens: a layout word. The
    # relationship is `spread`; the coefficient is a number or a $prop of the lens note, which is world data:
    # `do prop <lens> spacing=210` changes every present and future placement, is an event, and can be undone.
    m = re.fullmatch(r"(x|y) (-?\d+) step (\$?[\w.-]+) to (\d+)", val)
    if not m:
        raise LensRefusal(f"line {n}: `spread x <start> step <number or $prop of this lens> to <max>` (and the same for y); got {p!r}")
    node.setdefault("spread", {})[m.group(1)] = (int(m.group(2)), m.group(3), int(m.group(4)))


def _w_the(node, p, val, n, env):
    if not val:
        raise LensRefusal(f"line {n}: `the <selection> [as <frame>]`; got {p!r}")
    node["the"], _, asname = val.partition(" as ")        # `the tag:trip as trip` reads as one phrase
    if asname:
        node["as"] = asname.strip()


def _w_as(node, p, val, n, env):
    if not re.fullmatch(r"\w+", val):
        raise LensRefusal(f"line {n}: `as <frame>`; got {p!r}")
    if val in NAMES or val in ("value", "x", "y") or node["as"]:
        raise LensRefusal(f"line {n}: `as {val}` would shadow a built-in name; choose another frame name")
    node["as"] = val


def _w_derive(node, p, val, n, env):
    m = re.fullmatch(r"(\w+) = ([\w-]+)((?: \S+)*)", val)
    if not m:
        raise LensRefusal(f"line {n}: `derive <name> = <interpretation> <inputs>`; got {p!r}")
    dname, interp, ins = m.group(1), m.group(2), m.group(3).split()
    if interp not in INTERPS:
        raise LensRefusal(f"line {n}: no interpretation {interp!r}. The list is closed: " + ", ".join(f"{k} <{'> <'.join(v[0])}>" for k, v in INTERPS.items()))
    if len(ins) != len(INTERPS[interp][0]):
        raise LensRefusal(f"line {n}: {interp} takes {len(INTERPS[interp][0])} input(s): {' '.join(INTERPS[interp][0])}; got {len(ins)}")
    if dname in NAMES or any(dname == d[0] for d in node["derive"]):
        raise LensRefusal(f"line {n}: derive {dname}: that name is taken")
    node["derive"].append((dname, interp, ins))


def _w_capture(node, p, val, n, env):
    m = re.fullmatch(r"(\w+)=(\S+)", val)
    if not m:
        raise LensRefusal(f"line {n}: `capture <field>=<value>`; got {p!r}")
    node["capture"][m.group(1)] = m.group(2)


def _w_let(node, p, val, n, env):
    """`let <name> = <expr> [when <expr> | otherwise]` (Alex, 5 Oct: if and arithmetic; Pike a1397, Juniper a1399).
    Several lets of one name, each with `when`, are an if; one may say `otherwise`; two unguarded answers are refused."""
    m = re.fullmatch(r"(\w+)\s*=\s*(.+)", val.strip())
    if not m:
        raise LensRefusal(f"line {n}: `let <name> = <expr> [when <expr> | otherwise]`; got {p!r}")
    lname, rest = m.group(1), m.group(2).strip()
    if lname in NAMES or lname in X.KEYWORDS or any(lname == d[0] for d in node["derive"]):
        raise LensRefusal(f"line {n}: let {lname}: that name is taken")
    cond = None
    if rest.endswith(" otherwise"):
        rest, cond = rest[:-len(" otherwise")].strip(), "otherwise"
    elif " when " in rest:
        rest, _, cond = rest.rpartition(" when ")
        rest, cond = rest.strip(), cond.strip()
    for text in (rest, cond if cond and cond != "otherwise" else None):
        if text:
            try:
                X.parse(text)
            except X.ExprError as e:
                raise LensRefusal(f"line {n}: let {lname}: {e}")
    others = [c for l, _, c in node["let"] if l == lname]
    if cond is None and others:
        raise LensRefusal(f"line {n}: let {lname} has two answers on this part; give each a `when`, or one `otherwise`")
    if others and None in others:
        raise LensRefusal(f"line {n}: let {lname} already has an unguarded answer on this part; give it a `when`")
    if cond == "otherwise" and "otherwise" in others:
        raise LensRefusal(f"line {n}: let {lname} has two `otherwise` answers")
    node["let"].append((lname, rest, cond))


def _w_only(node, p, val, n, env):
    if not (val.startswith("when ") and val[5:].strip()):
        raise LensRefusal(f"line {n}: `only when <selection>` or `only when <expr>`; got {p!r}")
    node["only"] = _one_test(val[5:].strip(), n)      # Wren, Flint: the desk's own selection decides; an expression is judged after lets


# Alex, 5 Oct ("make our three ways to say the one new one"): a test is a selection (membership) or an expression; the
# older `$x <op> value` form, with a bare word on the right, is the expression `$x <op> "value"` and is read as that.
_LEGACY_TEST = re.compile(r"(\$[\w.-]+)\s*(=|!=|<=|>=|<|>|!?has(?=\s))\s*(\S+)")


def _one_test(text, n):
    m = _LEGACY_TEST.fullmatch(text)
    if not m:
        return text
    ref, op, rhs = m.groups()
    if not (rhs[0] in "$\"@(-" or rhs[0].isdigit() or rhs in ("none", "true", "false")):
        rhs = f'"{rhs}"'
    text = f"{ref} {op} {rhs}"
    try:
        X.parse(text)
    except X.ExprError as e:
        raise LensRefusal(f"line {n}: {e}")
    return text


# the desk's own commands a gesture may begin with; any other first word is a verb, and gets `do ` (verbs.py binds the
# words of these lines when a lens is saved, a1156, and reads them by this same list)
ACT_COMMANDS = ("do", "look", "read", "examine", "find", "undo", "run", "scene", "rows", "worktree", "open", "fold", "go")


def _w_on(node, p, val, n, env):
    g, do, cmd = val.partition(" do ")
    drop_part = label = None
    if g.startswith("drop "):
        drop_part, g = g[5:].strip(), "drop"
    if g.startswith("menu "):
        label, g = g[5:].strip(), "menu"
        if not re.fullmatch(r'"[^"]+"', label):
            raise LensRefusal(f'line {n}: `on menu "<label>" do <desk command>`: the entry\'s words, quoted; got {p!r}')
        label = label.strip('"')
    if (g not in GESTURES and g != "drop") or not do or not cmd.strip() or (g == "drop" and not drop_part) or (g == "menu" and not label):
        raise LensRefusal(f"line {n}: `on <click|edit|drag> do <desk command>`, `on menu \"<label>\" do <desk command>` or `on drop <part> do <desk command>`; got {p!r}")
    cmd = cmd.strip()
    if g == "drop" and len(split_batch(cmd)) > 1:
        raise LensRefusal(f"line {n}: a drop is one proposal: one desk command, not {len(split_batch(cmd))}")
    # `on drag do move $item ...` reads as English; the desk wants `do move ...`. A gesture names a verb
    # unless it begins with one of the desk's own reading or session commands.
    if cmd.split(" ")[0] not in ACT_COMMANDS:
        cmd = "do " + cmd
    node["on"].append({"on": g, "line": cmd, **({"part": drop_part} if drop_part else {}), **({"label": label} if label else {})})


# word -> (shape as a reader sees it, setter). A layout word is its own name.
WORDS = {
    **{lay: (lay, _w_layout) for lay in LAYOUTS},
    "grid": ("grid <tracks: 1 3 3 1 | 1fr fit 2fr>", _w_grid),
    "gap": ("gap | gap x2 | gap /2", _w_gap),
    "scroll": ("scroll none|scroll|end", _w_scroll),
    "fold": ('fold ["<handle label>"] [open] [float] [handle <role>] [group <name>]', _w_fold),
    "measure": ("measure <n>ch", _w_measure),
    "verbatim": ("verbatim", _w_verbatim),
    "lines": ("lines <min>..<max>", _w_lines),
    "share": ("share <weight>", _w_share),
    "hint": ('hint "..."', _w_hint),
    "plain": ("plain", _w_plain),
    "marks": ("marks", _w_marks),
    "peek": ("peek", _w_peek),
    "carry": ("carry", _w_carry),
    "role": ("role <name> [when <selection | expr>]", _w_role),
    "text": ('text "..."', _w_text),
    "clamp": ("clamp [last] <n>", _w_clamp),
    "the": ("the <selection> [as <frame>]", _w_the),
    "of": ("of <selection | row source> [as <frame>]", _w_of),
    "over": ("over $<list> [as <frame>]", _w_over),
    "by": ("by <prop>[, <prop>]", _w_by),
    "count": ("count <selection>", _w_count),
    "as": ("as <frame>", _w_as),
    "each": ("each <part>", _w_each),
    "at": ("at item", _w_at),
    "only": ("only when <selection | expr>", _w_only),
    "derive": ("derive <name> = <interpretation> <inputs>", _w_derive),
    "let": ("let <name> = <expr> [when <expr> | otherwise]", _w_let),
    "capture": ("capture <field>=<value>", _w_capture),
    "spread": ("spread x|y <start> step <n | $prop> to <max>", _w_spread),
    "lens": ("lens <name>", _w_lens),
    "on": ("on <gesture> do <command>", _w_on),
}


def vocabulary():
    """What a lens can say, printed from the table. Every refusal that lists the words uses this."""
    return ", ".join(shape for _, (shape, _f) in WORDS.items())


def _check_part(node, n):
    """Static checks on one part, after its words are read (stage 3 in miniature; the cross-part checks follow the loop)."""
    if (node["of"] or node["over"]) and not node["each"]:
        raise LensRefusal(f"line {n}: `of`/`over` repeats something; say what with `each <part>`")
    if node["the"] and (node["each"] or node["of"] or node["over"]):
        raise LensRefusal(f"line {n}: `the` names exactly one thing; it cannot repeat (drop `each`, `of` or `over`)")
    if node["count"] and (node["of"] or node["over"]):
        raise LensRefusal(f"line {n}: a repeat already has $count, its true size; `count` is for a part that repeats nothing")
    if node["as"] and (node["as"] in NAMES or node["as"] in ("value", "x", "y")):
        raise LensRefusal(f"line {n}: `as {node['as']}` would shadow a built-in name; choose another frame name")
    if node["as"] and not (node["the"] or node["of"] or node["over"]):
        raise LensRefusal(f"line {n}: `as {node['as']}` names the thing chosen here, so this part needs `the`, `of` or `over`")
    if node["by"] and not node["of"]:
        raise LensRefusal(f"line {n}: `by` orders a repeat; this part has no `of`")
    if node["capture"] and not node["the"]:
        raise LensRefusal(f"line {n}: `capture` holds a field of the thing chosen by `the`; this part has no `the`")
    import knife      # a3359: a selection that names due as a prop is refused here, when the lens is saved, not at a look
    only = None if X.looks_like(node["only"]) else node["only"]
    for sel in [node["of"], node["the"], only, node["count"]] + [c for _, c in node["role_when"] if not X.looks_like(c)]:
        said = knife.misnamed(sel)
        if said:
            raise LensRefusal(f"line {n}: {said}")


def indent_of(line):
    return len(line) - len(line.lstrip())


def parse(src, roles=None, style=None):
    """-> (root_name, parts) where parts[name] = node {name, props, kids}. `roles`: the lens's style's roles (F7).
    Alex, 5 Oct (out of the comma lists): a line whose head is a name before ` : ` opens a part and says what it is and
    how it looks (`card : column, role card`, `t : text "$title"`); every other word is its own line, indented under
    the part it belongs to, among that part's child parts. The older comma list on the part line is still read, since
    the worlds hold lenses written that way; to_lines prints the one form, and both parse to the same tree."""
    parts, stack, root = {}, [], None
    env = {"roles": roles if roles is not None else _roles(), "style": style}

    def say(node, p, n):
        word, _, val = p.partition(" ")
        row = WORDS.get(word)
        if row is None:
            raise LensRefusal(f"line {n}: a lens cannot say {p!r}. It can say: {vocabulary()}")
        row[1](node, p, val, n, env)
        node["words"].append(p)

    for n, raw in enumerate(src.splitlines(), 1):
        line = _outside_quotes(raw, " # ")[0].rstrip()
        if not line.strip() or line.strip().startswith("#") or (indent_of(line) == 0 and re.fullmatch(r"lens \S+", line.strip())):   # a header line, `lens <name>`, as the first lenses began; an indented `lens x` is the word
            continue
        indent = len(line) - len(line.lstrip())
        text = line.strip()
        pieces = _outside_quotes(text, " : ")
        head = pieces[0] if len(pieces) > 1 else (text[:-2] if text.endswith(" :") else None)
        if head is None or not re.fullmatch(r"[\w-]+", head):
            # a word line: it belongs to the nearest part above it with a smaller indent
            while stack and stack[-1][0] >= indent:
                stack.pop()
            if not stack:
                raise LensRefusal(f"line {n}: {text!r} is a word with no part above it. A part is `name : <what it is>`; "
                                  f"its words are indented under it, one per line")
            say(stack[-1][1], text, n)
            continue
        name, rest = head, (" : ".join(pieces[1:]) if len(pieces) > 1 else "")
        node = {"name": name, "kids": [], "line": n, "layout": None, "role": None, "role_when": [], "text": None, "clamp": None,
                "of": None, "over": None, "each": None, "at": None, "on": [], "lens": None, "only": None, "props": [],
                "the": None, "as": None, "derive": [], "let": [], "capture": {}, "src": "", "words": [], "carry": False, "by": None,
                "tracks": None, "gap": None, "scroll": None, "fold": False, "measure": None, "wrap": None, "lines": None, "share": None, "hint": None, "plain": False, "peek": False, "marks": False, "count": None}
        last = None
        for p in [p.strip() for p in _outside_quotes(rest, ", ") if p.strip()]:
            word, _, val = p.partition(" ")
            if last == "by" and not val and word not in WORDS and re.fullmatch(r"[\w.-]+", word):
                node["by"].append(word)          # the older `by priority, rank`: a bare name after `by` is its next prop
                node["words"][-1] += " " + word  # said once, as `by priority rank`
                continue
            last = word
            say(node, p, n)
        if indent == 0:
            if name in parts:
                raise LensRefusal(f"line {n}: part {name!r} is already defined on line {parts[name]['line']}; one name, one part")
            parts[name] = node
            root = root or name
            stack = [(0, node)]
        else:
            while stack and stack[-1][0] >= indent:
                stack.pop()
            if not stack:
                raise LensRefusal(f"line {n}: indented part with no parent")
            if any(k["name"] == name for k in stack[-1][1]["kids"]):
                raise LensRefusal(f"line {n}: {stack[-1][1]['name']} already has a child named {name!r}; siblings need different names (they are its address)")
            stack[-1][1]["kids"].append(node)
            stack.append((indent, node))
    if not root:
        raise LensRefusal("an empty lens shows nothing; start with  window : column")
    every = [k for p in parts.values() for k in _walk(p)]
    for k in every:
        k["src"] = f"{k['name']} : " + ", ".join(k["words"])     # one spelling of the part's own words, whichever form it was written in
        _check_part(k, k["line"])          # after every line, since a part's words may follow its children
        for wd in ("gap", "scroll", "fold", "measure"):
            if k[wd] not in (None, False) and not k["layout"]:
                raise LensRefusal(f"line {k['line']}: `{wd}` is a frame word; this part has no layout (column, row, free, grid)")
        for wd in ("wrap", "lines", "hint"):
            if k[wd] is not None and k["text"] is None:
                raise LensRefusal(f"line {k['line']}: `{'verbatim' if wd == 'wrap' else wd}` is a text word; this part prints no text")
        if k["layout"] == "grid" and not k["tracks"]:
            raise LensRefusal(f"line {k['line']}: `grid` names its tracks: grid 1 3 3 1")
        if k["clamp"] is not None and k["text"] is not None and any(a["on"] == "edit" for a in k["on"]):
            raise LensRefusal(f"line {k['line']}: `on edit` on a clamped text: the person would replace words the clamp hides; drop the clamp, or edit through a part that shows the whole value")
        if k["each"] and k["each"] not in parts:
            raise LensRefusal(f"line {k['line']}: each {k['each']}: no part of that name is defined (unindented) in this lens")
        if k["carry"] and any(a["on"] == "drag" for a in k["on"]):
            raise LensRefusal(f"line {k['line']}: a part cannot both `carry` and `on drag`; a carried thing is put down by a drop")
        for a in k["on"]:
            if a["on"] == "drop" and not any(x["name"] == a["part"] and x["carry"] for x in every):
                raise LensRefusal(f"line {k['line']}: `on drop {a['part']}`: no part named {a['part']!r} says `carry`")

    def reach(name, trail):
        if name in trail:
            raise LensRefusal(f"part {name!r} repeats itself ({' -> '.join(trail + [name])}); a lens may not recurse")
        for k in _walk(parts[name]):
            if k["each"]:
                reach(k["each"], trail + [name])
    for name in parts:
        reach(name, [])
    return root, parts


HEAD_WORDS = LAYOUTS + ("grid", "text")


def to_lines(src, roles=None, style=None):
    """The one form of a lens (Alex, 5 Oct): a part line says what the part is and how it looks, `card : column, role
    card` or `t : text "$title"`; every other word is its own line under it, in the order written, then its child
    parts. A lens that does not parse is refused as parse refuses it. Comments do not survive (parse drops them)."""
    root, parts = parse(src, roles, style)
    out = []

    def split(node):
        head, rest = [], []
        for p in node["words"]:
            w = p.partition(" ")[0]
            if w in HEAD_WORDS and not any(x.partition(" ")[0] in HEAD_WORDS for x in head):
                head.append(p)
            elif w == "role" and " when " not in p and not any(x.startswith("role ") for x in head):
                head.append(p)
            else:
                rest.append(p)
        head.sort(key=lambda x: x.startswith("role "))      # what it is, then how it looks
        return head, rest

    def emit(node, depth):
        head, rest = split(node)
        out.append("  " * depth + node["name"] + (" : " + ", ".join(head) if head else " :"))
        for p in rest:
            out.append("  " * (depth + 1) + p)
        for k in node["kids"]:
            emit(k, depth + 1)

    for name in parts:
        emit(parts[name], 0)
    return "\n".join(out)


# ---------------------------------------------------------------------------------------------------------------------
# Stage 2, resolve. Every $name in a lens is classified before anything is evaluated: a thing's field, a host fact, a
# gesture fact, a let (derive) named above, a frame named above with `as`, or a prop read (which resolves at evaluation
# and prints its absence). A `$frame.field` whose frame is not in scope is refused here, for every part reachable from
# the root, so an untaken branch is not an unexercised program (Sable R6; Pike's rules N1 to N6, round six).
# ---------------------------------------------------------------------------------------------------------------------
HOST = ("me", "today", "session", "touched")
HOST_FRAMES = ("touched", "changed")      # Juniper: $touched (last event on the thing), $touched.by, $changed.<field>; host reads, never in a fence
GESTURE_FACTS = ("value", "x", "y", "carried")


def _refs_of(node):
    """Every $name and $frame.field this part's own words use, with the word they sit in."""
    out = []
    srcs = [("text", node["text"] or ""), ("only", node["only"] or ""), ("of", node["of"] or ""), ("the", node["the"] or ""),
            ("lens", node["lens"] or ""), ("count", node["count"] or "")]
    srcs += [("derive", x) for _, _, ins in node["derive"] for x in ins]
    srcs += [("let", e) for _, e, _c in node["let"]] + [("let", c) for _, _e, c in node["let"] if c and c != "otherwise"]
    if node["only"] and X.looks_like(node["only"]):
        srcs.append(("only", node["only"]))
    srcs += [("on", a["line"]) for a in node["on"]]
    srcs += [("role", c) for _, c in node["role_when"]]          # a1105: a role's test reads names like `only when`
    for word, text in srcs:
        for a, b in _VAR.findall(text):
            out.append((word, a, b))
    return out


def _exprs_of(node):
    """The expressions this part's own words hold, with the word they sit in."""
    out = [("let", e) for _, e, _c in node["let"]] + [("let", c) for _, _e, c in node["let"] if c and c != "otherwise"]
    if node["only"] and X.looks_like(node["only"]):
        out.append(("only when", node["only"]))
    out += [("role", c) for _, c in node["role_when"] if X.looks_like(c)]
    return out


def resolve(root, parts):
    """-> {id(node): {"frames": set, "lets": set}} for every part reachable from the root, walking kids and `each`.
    Refuses a `$frame.field` whose frame no part above names, and a bare `$frame` used as a value."""
    scopes = {}

    def visit(node, frames, lets, trail):
        frames, lets = set(frames), set(lets)
        if node["as"]:
            frames.add(node["as"])
        if node["of"] or node["over"]:
            frames.add("it")
        for dname, _i, _ins in node["derive"]:
            lets.add(dname)
        for lname, _e, _c in node["let"]:
            lets.add(lname)
        scopes[id(node)] = {"frames": frames, "lets": lets}
        for word, text in _exprs_of(node):      # a bare word in an expression is a let named above, or it is refused
            for bare in X.bare_words(text):
                if bare not in lets:
                    raise LensRefusal(f"line {node['line']}: `{bare}` in `{word} {text}` is no let named above; quote words: \"{bare}\"")
        for word, a, b in _refs_of(node):
            if b:
                if a not in frames and a != "it" and a not in HOST_FRAMES:
                    raise LensRefusal(f"line {node['line']}: ${a}.{b}: no part above this one is named `as {a}`"
                                      + (f" (frames in scope: {', '.join(sorted(frames))})" if frames else " (no frames in scope)"))
        for kid in node["kids"]:
            visit(kid, frames, lets, trail)
        if node["each"] and node["each"] not in trail:
            visit(parts[node["each"]], frames, lets, trail + [node["each"]])

    visit(parts[root], set(), set(), [root])
    return scopes


def classify(name, scope):
    """What a bare $name means in a scope: field | host | gesture | let | frame | prop."""
    if name in ("title", "text", "kind", "due", "tags", "id", "item", "n", "count", "index"):
        return "field"
    if name in HOST:
        return "host"
    if name in GESTURE_FACTS:
        return "gesture"
    if name in scope["lets"]:
        return "let"
    if name in scope["frames"]:
        return "frame"
    return "prop"


def role_of(role, role_when, ctx, track, select, run=None):
    """a1105: the role a part takes here and why. `role_when` is [(name, condition)] in the lens's order; the first that
    holds for this part's thing wins, else the plain role. A condition is a selection (judged as `only when` judges one:
    the thing is among what it finds, or, with no thing, it finds anything) or an expression run by `run(text) ->
    (Value, inputs)`, where none does not hold. `select(q)` -> ids. -> (role, why or None)."""
    for name, cond in role_when:
        if run and X.looks_like(cond, ctx.get("_lets") or ()):
            val, ins = run(cond)
            if X.holds(val):
                return name, cond + (f" ({ins})" if ins else "")
            continue
        q = _fill(cond, ctx)
        ids = select(q)
        t = ctx.get("item") or ctx.get("id")
        if ((t in ids or ctx.get("id") in ids) if t else bool(ids)):
            return name, q
    return role, None


def _walk(node):
    yield node
    for k in node["kids"]:
        yield from _walk(k)


def _date(s):
    import datetime
    try:
        return datetime.date.fromisoformat(str(s).strip())
    except ValueError:
        return None


def _day_n(vals):
    d, n = _date(vals[0]), str(vals[1]).strip()
    if d is None or not n.lstrip("-").isdigit():
        return None, f"day-n wants <date> <n>; got {vals[0]!r} {vals[1]!r}"
    import datetime
    return (d + datetime.timedelta(days=int(n) - 1)).isoformat(), None


def _days_from(vals):
    a, b = _date(vals[0]), _date(vals[1])
    if a is None or b is None:
        return None, f"days-from wants <start> <end> as dates; got {vals[0]!r} {vals[1]!r}"
    import datetime
    if (b - a).days > 366 or b < a:
        return None, f"days-from: {vals[0]} to {vals[1]} is not a span of at most a year"
    return [{"n": k + 1, "date": (a + datetime.timedelta(days=k)).isoformat()} for k in range((b - a).days + 1)], None


def _weekday(vals):
    d = _date(vals[0])
    return (d.strftime("%a"), None) if d else (None, f"weekday wants a date; got {vals[0]!r}")


def _week_of(vals):
    import datetime
    d = _date(vals[0])
    return ((d - datetime.timedelta(days=d.weekday())).isoformat(), None) if d else (None, f"week-of wants a date; got {vals[0]!r}")


# Pike W6: named interpretations, a closed and budgeted list like the roles in calm.style. Each is pure over printed
# inputs and total. There is no +, no if and no nesting; a new one is argued for and added by whoever owns the host.
def _when(vals, part):
    """Juniper: a freshness value (`e412 prop · 2026-09-25 21:40`, or a plain date or date-time) shown as its time or
    its date alone, so a person's screen need not carry the event id and verb; provenance keeps the whole value."""
    import re as _re
    m = _re.search(r"(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}:\d{2}))?", str(vals[0]))
    if not m:
        return None, f"{part} wants a date, a date-time or a freshness value; got {vals[0]!r}"
    if part == "time" and not m.group(2):
        return None, f"time wants a date-time or a freshness value; got {vals[0]!r}"
    return (m.group(2) if part == "time" else m.group(1)), None


def _day_or_time(vals):
    """Juniper (day lens a496): `day-or-time <when> <today>`: the time alone when the day is today, `Mon 28` within a
    week either way, else the date. Today is an input, so the read is visible; goldens freeze it per world."""
    import re as _re
    m = _re.search(r"(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}:\d{2}))?", str(vals[0]))
    d, today = (_date(m.group(1)) if m else None), _date(vals[1])
    if not d or not today:
        return None, f"day-or-time wants a date-time or a freshness value and today; got {vals[0]!r}, {vals[1]!r}"
    if d == today:
        return (m.group(2) or d.isoformat()), None
    return (d.strftime("%a %d").replace(" 0", " ") if abs((d - today).days) <= 7 else d.isoformat()), None


INTERPS = {"day-n": (("date", "n"), _day_n), "days-from": (("start", "end"), _days_from),
           "day-or-time": (("when", "today"), _day_or_time),
           "weekday": (("date",), _weekday), "week-of": (("date",), _week_of),
           "time": (("when",), lambda v: _when(v, "time")), "date": (("when",), lambda v: _when(v, "date"))}
_VAR = re.compile(r"\$(\w+)(?:\.(\w+))?")


def _fill(tpl, ctx, track=None):
    """$name from the current thing; $frame.field from a frame named above with `as` (Pike W3). `track` collects
    what was read, what was missing, and which frames fed the words, so the scene can print it and the fence can carry it."""
    frames = ctx.get("_frames") or {}

    def rep(m):
        a, b = m.group(1), m.group(2)
        if b:
            f = frames.get(a)
            if f is None:
                if track is not None:
                    track["bad"].add(a)
                return m.group(0)
            v = f.get(b) if (b in f and not b.startswith("_")) else (f.get("_props") or {}).get(b)
            if track is not None:
                cap = b in (f.get("_captured_fields") or ())
                if not cap:
                    track["frames"].add(a)          # a captured value is not a read of the world: it stays out of the fence
                if v is None:
                    track["missing"].add(f"{a}.{b}")
                else:
                    track["reads"][f"{a}.{b}"] = f"{v} (captured)" if cap else v
            return "" if v is None else str(v)
        if a in ctx and track is not None:
            track.setdefault("own", set()).add(a)
        return str(ctx[a]) if a in ctx else m.group(0)

    return _VAR.sub(rep, tpl)


def _fill_text(tpl, ctx, track, run):
    """Words with `$( <expr> )` inside: each expression is computed by `run(text) -> (Value, inputs)` and printed in its
    place, with its reach; then the plain $names are filled. -> (text, [(expr, printed, inputs)])."""
    out, computed, i = "", [], 0
    while True:
        j = tpl.find("$(", i)
        if j < 0:
            out += tpl[i:]
            break
        depth, k = 0, j + 1
        while k < len(tpl):
            depth += (tpl[k] == "(") - (tpl[k] == ")")
            if depth == 0:
                break
            k += 1
        if k >= len(tpl):
            out += tpl[i:]
            break
        inner = tpl[j + 2:k].strip()
        val, inputs = run(inner)
        shown = X.fmt(val)
        computed.append((inner, shown, inputs))
        # in the words themselves: the bare value, with a short reach only when it is partial ('6 (1 of 2)'); the scene
        # print beside the part says the whole reach (a1448: reach is part of the value, and the eye must see partiality)
        out += tpl[i:j] + X.fmt(val, reach=False) + (f" ({val.reach.split(';')[0]})" if val.partial and val.reach else "")
        i = k + 1
    return _fill(out, ctx, track), computed


def _binds(node):
    return bool(node["the"] or node["of"] or node["over"] or node["as"] or node["derive"] or node.get("let") or node["capture"] or node["only"] or node["each"])


def _chain_hash(chain):
    """Pike a308: the identity of one part is its own line plus the lines above it that bind its frame (the, of, over,
    as, derive, capture, only, each). An edit anywhere else in the lens does not change it, so a gesture painted
    under this part is still meaningful and need not be refused."""
    import hashlib
    lines = [n["src"] for n in chain[:-1] if _binds(n)] + [chain[-1]["src"]]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:12]


def defpart_hash(src, path, roles=None, style=None):
    """Recompute a gesture node's part hash from a lens text and the node's part path (root/repeat/card). The path
    steps into a kid by name, or through `each` into the named part. None when the path no longer exists. `roles` and
    `style` are the lens's own (F7): parsed under the default roles, a lens with its own style refuses, and every
    part-identity check failed (F18)."""
    root, parts = parse(src, roles=roles, style=style)
    names = path.split("/")
    if names[0] not in parts:
        return None
    node, chain = parts[names[0]], [parts[names[0]]]
    for name in names[1:]:
        kid = next((k for k in node["kids"] if k["name"] == name), None)
        if kid is None and node["each"] == name:
            kid = parts[name]
        if kid is None:
            return None
        node = kid
        chain.append(node)
    return _chain_hash(chain)


_ASPECT_NAMES = ("title", "text", "due", "tags")


def _aspect_of_field(f):
    if f in _ASPECT_NAMES:
        return f
    if f in NAMES or f in ("value", "x", "y", "n", "count"):
        return None
    return f"prop:{f}"


def _rev_of(w, i):
    x = w.subjects.get(i) or w.nodes.get(i)
    return x["rev"] if x else None


def _inst(ctx, node, ictx):
    """The context for one instance of a repeat: the thing's own values, plus every frame named above, plus this
    part's own frame when it says `as`. Pike: a nested `of` used to lose the outer thing's fields."""
    ictx = dict(ictx)
    frames = dict(ctx.get("_frames") or {})
    if node["as"]:
        if node["as"] in frames:
            # Juniper A1 (Pike's rule N1): an inner `as a` silently replaced the outer one, and "Alpha under Alpha" printed
            # under both rows. A frame may not shadow a frame named above it.
            raise LensRefusal(f"line {node['line']}: `as {node['as']}` would shadow the frame `as {node['as']}` named above this part; choose another frame name")
        frames[node["as"]] = ictx
    ictx["_frames"] = frames
    return ictx


def _ctx_for(w, nid, state=None):
    """The values a lens may print for one thing. An appearance id, or a subject id (then item is its first appearance,
    or None when unplaced: Pike found a lens could not name the durable thing at all)."""
    if nid not in w.nodes and nid not in w.subjects:          # named in a lens, gone from the world: the scene says so
        return {"item": None, "id": nid, "title": "", "text": "", "kind": "", "due": "", "tags": "", "_tags": [], "_props": {},
                "_state": state or "gone"}
    if nid in w.subjects and nid not in w.nodes:
        s, apps = w.subjects[nid], w.appearances_of(nid)
        n = w.nodes[apps[0]] if apps else {"type": s.get("kind", "note")}
        item = apps[0] if apps else None
    else:
        n = w.nodes[nid]
        s = w.subjects.get(n.get("subject")) or {}
        item = nid
    ctx = {"item": item, "id": n.get("subject") or nid, "title": s.get("title", n.get("title", "")), "text": s.get("text", ""),
           "kind": s.get("kind", n["type"]), "due": s.get("due") or "", "tags": " ".join(s.get("tags") or []),
           "_tags": list(s.get("tags") or []),
           # F11: a surface's props live on the surface itself (a resident's corner carries status, want)
           # a1590: a person prop holds the person; a lens reads the name ($owner = $me holds for today's bearer)
           "_props": __import__("persons").shown_props(w, s.get("props") or (n.get("props") if n.get("type") == "surface" else None) or {})}
    if s.get("id"):
        import promises      # a1587: who open requests about it ask, read from their events ($asked_of; '' for none)
        ctx["asked_of"] = promises.cell(w, s["id"], "asked_of") if promises.on(w) else ""
    if state:
        ctx["_state"] = state
    return ctx


_ID = re.compile(r"^[afs]\d+$")


def _named(w, sel):
    """`of a04,s09`: ids named one by one. -> list of (id, state) or None when `sel` is not a list of ids.
    An appearance id is itself; a subject id is each of its appearances (occurrences), or the subject unplaced;
    a missing id is gone. Pike: `of a04,a06` emptied entirely when a04 was removed; each id now answers alone."""
    terms = [t for t in re.split(r"[,\s]+", sel.strip()) if t]
    if not terms or not all(_ID.match(t) for t in terms):
        return None
    out = []
    for t in terms:
        if t in w.nodes:
            out.append((t, "live"))
        elif t in w.subjects:
            apps = w.appearances_of(t)
            out += [(a, "live") for a in apps] or [(t, "unplaced")]
        else:
            out.append((t, "gone"))
    return out


def _rekey(n, prefix):
    for k in n["kids"]:
        k["key"] = prefix + "/" + k["key"]
        _rekey(k, prefix)


def _reprefix(n, old, new):
    for k in n["kids"]:
        if k["key"].startswith(old + "/"):
            k["key"] = new + k["key"][len(old):]
        _reprefix(k, old, new)


def _slug(s):
    return re.sub(r"[^\w-]+", "-", str(s).strip().lower()).strip("-")[:40] or "-"


def _ago(iso):
    import datetime
    try:
        s = int((datetime.datetime.now() - datetime.datetime.fromisoformat(iso)).total_seconds())
    except (TypeError, ValueError):
        return "at an unknown time"
    return (f"{max(s, 0)} s" if s < 90 else f"{s // 60} min" if s < 5400 else f"{s // 3600} h" if s < 172800 else f"{s // 86400} days") + " ago"


def judge_views(desk, views, closure, style_rev):
    """a1473: whether each viewer's sizes are of the lens as it stands. A painter reports the frame (each lens in the
    closure at its revision) and the style revision it painted; anything else now means its boxes are of an older lens.
    The edit is named: the first event after the paint's world that touched a lens in the closure or its style.
    -> {viewer: copy of the view with "paint": {"state": current|stale|unknown, "edit": words or None, "age": words}}"""
    w = desk.world
    frame = ".".join(f"{c['id']}r{c['rev']}" for c in closure)
    ids = set()
    for sid in [c["id"] for c in closure] + ([style_rev.rsplit("r", 1)[0]] if style_rev and style_rev[:1] == "s" else []):
        ids.add(sid)
        ids.update(w.appearances_of(sid))
    out = {}
    for a, v in views.items():
        v = dict(v)
        if "boxes" in v:
            p = v.get("painted") or {}
            state = "unknown" if not p else "current" if (p.get("frame"), p.get("style")) == (frame, style_rev or "seed") else "stale"
            edit = None
            if state == "stale":
                evs = [e for e in w.events[v.get("at", 0):] if e.get("target") in ids] or \
                      [e for e in reversed(w.events) if e.get("target") in ids][:1]
                if evs:
                    e = evs[0]
                    edit = ("your" if e.get("by") == w.me else f"{e.get('by')}'s") + f" edit at {e['id']}" + (f" (and {len(evs) - 1} more)" if len(evs) > 1 else "")
                else:
                    edit = f"a change to the lens (painted {p.get('frame')}, now {frame})"
            v["paint"] = {"state": state, "edit": edit, "age": _ago(v.get("time"))}
        out[a] = v
    return out


def box_words(b):
    """A painter's box ("320x840 scroll sh=2400", "hidden") as words for a part's line."""
    if b == "hidden":
        return "not drawn (folded or hidden)"
    m = re.match(r"(\d+)x(\d+)", b or "")
    if not m:
        return f"box {b!r} (unreadable)"
    wd, ht = int(m.group(1)), int(m.group(2))
    kv = dict(re.findall(r"(\w+)=([\d/]+)", b))
    out = f"{wd}x{ht}px"
    if ht == 0 or wd == 0:
        out += f" ({'0 high' if ht == 0 else '0 wide'}: nothing visible)"
    over = " and ".join(x for x in (f"{kv['sh']} high" if "sh" in kv else "", f"{kv['sw']} wide" if "sw" in kv else "") if x)
    if over:
        mode = next((x for x in ("scroll", "clip", "spill") if f" {x}" in b), "spill")
        out += {"scroll": f", scrolls: contents {over}", "clip": f", clipped: contents {over}",
                "spill": f", contents spill out of it: {over}"}[mode]
    if "cut" in kv:
        n, of = kv["cut"].split("/")
        out += f", {n} of {of} parts cut off"
    if "out" in kv:
        n, of = kv["out"].split("/")
        out += f", {n} of {of} parts scrolled out of view"
    return out


def to_text(scene, name, who, at, roots=None, part=None):
    """The scene as text. `roots` (a1101): print only these nodes and what is inside them, each under its full key."""
    lines = [f"scene {name}" + (f" · part {part}: {len(roots)} match" + ("es" if len(roots) != 1 else "") if roots is not None else "")
             + f" · for {who} · world @{at}"]
    views = scene.get("views") or {}
    for a, v in views.items():
        vp = v.get("viewport") or {}
        # Pike a561: since 0477e78 a viewer publishes attention (viewport, scroll) only when they allow it; say so
        where = (f"is looking: {vp.get('w')}x{vp.get('h')} at scroll {vp.get('sx')},{vp.get('sy')}" if vp.get("w") is not None
                 else "has this open; attention not shared")
        pa = v.get("paint")
        lines.append(f"  ~ {a} {where} · painted world @{v.get('at')}"
                     + (" (behind)" if v.get("at", at) < at else "") + f" · reported {str(v.get('time', ''))[11:19]}"
                     + (f" ({pa['age']}) · " + {"current": "sizes are of the lens as it stands",
                                                "stale": f"painted before {pa['edit']}: sizes are of the old lens",
                                                "unknown": "its painter did not say which revision it painted"}[pa["state"]] if pa else ""))
    sized = [v for v in views.values() if v.get("paint")]
    if sized and all(v["paint"]["state"] == "stale" for v in sized):
        lines.append(f"  ! no viewer has painted this lens since {sized[0]['paint']['edit']}; the sizes below are of the old lens")
    elif not sized and part is not None:
        lines.append("  ~ no painted sizes: no viewer has this lens open with a painter that reports them (screen.py paints a copy)")

    def rv(v, top=120):
        """A read value on one line: newlines become ` / ` as in a body, and a long one is cut and says so (Juniper,
        juniper-7: a chat's text in a read put lines at column zero and every indentation reader mis-parsed the print)."""
        t = " / ".join(str(v).splitlines()) if isinstance(v, str) else v
        return (t[:top] + f" (={top} of {len(t)} chars)") if isinstance(t, str) and len(t) > top else t

    def pr(n, d, pkey=None):
        bits = [n["part"]]
        if n.get("absent"):
            why = rv(n.get("why") or f"not {n['absent']}", 80)      # a1101: a value test quoted a whole message
            lines.append("  " * d + f"{n['part']} {n.get('item') or ''} (absent: {why})".replace("  (", " ("))
            return
        if n.get("item"):
            bits.append(n["item"])
        elif n.get("id"):
            bits.append(n["id"])
        if n["text"] is not None:
            # Lark: fidelity is a property of a printer, not of a tree. This printer says every cut it makes.
            t = n["text"].split("\n")
            shown = t[: n["clamp"]] if n["clamp"] and "n" not in n else t
            body, cut = " / ".join(shown), ""
            if len(body) > 240:
                body, cut = body[:240], f" (=240 of {len(n['text'])} chars printed here; read {n.get('item') or 'it'} for all)"
            if len(shown) < len(t):
                cut += f" (={len(shown)} of {len(t)} lines, clamp {n['clamp']})"
            if n["clamp"]:
                cut += f" (~clamp {n['clamp']}: the painter clamps wrapped lines and may show less)"
            bits.append('"' + body + '"' + cut)
        if n["role"]:
            r = n["role"] + (" pulse" if n.get("pulse") else "")          # a1140: the print says what the eye sees move
            bits.append(f"[{r}, since {n['since']}]" if n.get("since") else f"[{r}]")
        if n["layout"]:
            bits.append(n["layout"] + (" " + " ".join(n["tracks"]) if n.get("tracks") else ""))
        for wd in ("gap", "scroll", "measure", "share"):
            if n.get(wd) is not None:
                bits.append(f"{wd} {n[wd]}")
        if n.get("fold"):
            bits.append(("unfolded" if n.get("fold_open") else "folded") + (f' "{n["fold"]}"' if isinstance(n["fold"], str) else "")
                        + (" float" if n.get("fold_float") else "") + (f" handle {n['fold_handle']}" if n.get("fold_handle") else "")
                        + (f" group {n['fold_group']}" if n.get("fold_group") else ""))
        if n.get("wrap") == "verbatim":
            bits.append("verbatim")
        if n.get("lines"):
            bits.append(f"lines {n['lines'][0]}..{n['lines'][1] if n['lines'][1] is not None else ''}")
        if n.get("hint"):
            bits.append(f'hint "{n["hint"]}"')
        if n.get("peek"):
            bits.append("peek")
        if n.get("plain"):
            bits.append("plain")
        elif n.get("text") and runs_of(n["text"], n.get("marks")):
            rs = runs_of(n["text"], n.get("marks"))
            if any(r.get("role") for r in rs) or not n.get("marks"):
                bits.append(f"runs {sum(1 for r in rs if r.get('role'))} code")
            if n.get("marks"):
                bits.append("marks " + (", ".join(f"{k} {c}" for k in ("strong", "stress", "both", "link") for c in [sum(1 for r in rs if r.get("mark") == k)] if c) or "none"))
        elif n.get("marks"):
            bits.append("marks none")
        if n.get("lens"):
            bits.append(f"· lens {n['lens']}")
        if n["box"]:
            bits.append(f"at {n['box'][0]},{n['box'][1]} {n['box'][2]}x{n['box'][3]}" + (f" ({n['placed']}, not its place in the world)" if n.get("placed") else ""))
        if n.get("facts"):
            bits.append("= " + ", ".join(n["facts"]))
        if n.get("the"):
            bits.append(f"· the {n['the'][0]} " + (n["the"][1] if n["the"][1].startswith("->") else f"({n['the'][1]})"))
        if n.get("as"):
            bits.append(f"as {n['as']}")
        for c in n.get("captured") or []:
            bits.append(f"· captured {c['field']}={c['value']} (now {c['now']}: {'same' if c['same'] else 'differs'})")
        for dv in n.get("derived") or []:
            if dv.get("interp") == "let":
                bits.append(f"· {dv['name']} = {dv['result']} ({dv['expr']}" + (f"; {dv['inputs_s']}" if dv.get("inputs_s") else "") + ")"
                            + (f" (overlap: {dv['overlap']} answers held; the first was taken)" if dv.get("overlap") else ""))
            else:
                bits.append(f"· {dv['name']} = {dv['interp']}({', '.join(dv['inputs'])}) = {dv['result']}" if not dv["error"] else f"· {dv['name']}: (uninterpretable: {dv['error']})")
        for ex, shown, inputs in n.get("computed") or []:
            bits.append(f"· $({ex}) = {shown}" + (f" ({inputs})" if inputs else ""))
        if n.get("read"):
            bits.append("· read " + " ".join(f"{k}={rv(v)}" for k, v in n["read"].items()))
        if n.get("freads"):
            byf = {}
            for k, v in n["freads"].items():
                f, fld = k.split(".", 1)
                byf.setdefault(f, []).append(f"{fld}={v}")
            bits.append("· read " + "; ".join(f"{f} " + (f"{n.get('frames', {}).get(f)} " if n.get('frames', {}).get(f) else "") + " ".join(rv(x) for x in fs) for f, fs in byf.items()))
        if n.get("missing"):
            bits.append("(" + ", ".join(f"no {m}" for m in n["missing"]) + ")")
        if n.get("state"):
            bits.append(f"({n['state']})")
        if "n" in n:
            bits.append((f"· {n['n']} of {n['of']}" if n.get("of") else f"· {n['n']}") + (f" by {', '.join(n['by'])}" if n.get("by") else ""))
            if n["n"] == 0:
                bits.append("(empty)")         # Pike: every miss printed like an honest empty; now an empty says so
            if n.get("states"):
                bits.append("(" + ", ".join(n["states"]) + ")")
        if n.get("counted"):
            bits.append(f"· count {n['counted'][1]} of {n['counted'][0]}")
        if n.get("test"):
            bits.append(f"· only when {n['test']}")
        for a in n["acts"]:
            if a["on"] == "fold":
                continue                    # the line already says folded; the fold act is the viewer's, with no line
            bits.append(f"· {a['on']}" + (f" {a['part']}" if a.get("part") else "") + (f' "{a["label"]}"' if a.get("label") else "")
                        + (f": {a['line']}" if a.get("line") else ""))
        for a, v in views.items():
            if n["key"] in (v.get("facts") or {}):
                bits.append(f"~ {a}: {v['facts'][n['key']]}")
            if v.get("paint"):           # a1473: the box this part was painted at, from that viewer's last report
                b = (v.get("boxes") or {}).get(n["key"])
                old = " before the edit" if v["paint"]["state"] == "stale" else ""
                if not (b == "hidden" and pkey and v["boxes"].get(pkey) == "hidden"):     # said once, at the top one
                    bits.append(f"~ {a}{old}: " + (box_words(b) if b else "not in the paint"))
        # Juniper (key form, 25 Sep), Pike's C4 gap: the occurrence key was painted as data-key and never printed. The
        # segment is the key below the parent's; a fixed part's segment is its own name and prints nothing.
        seg = n["key"][len(pkey) + 1:] if pkey and n["key"].startswith(pkey + "/") else n["key"]
        if seg != n["part"]:
            bits.append(f"· key {seg}")
        lines.append("  " * d + " ".join(bits))
        for k in n["kids"]:
            pr(k, d + 1, n["key"])

    if roots is None:
        pr(scene, 1)
    for r in roots or []:
        lines.append(f"  = {r['key']}")
        pr(r, 2, r["key"].rsplit("/", 1)[0] if "/" in r["key"] else None)
    return "\n".join(lines)


def find_lens(desk, name):
    import kinds
    w = desk.world
    hits = [s for s in w.subjects.values() if kinds.is_lens(s) and s["title"].lower() == name.lower()]
    if len(hits) > 1:        # a removed lens leaves its subject behind, unplaced; the placed one is the one meant
        placed = [s for s in hits if w.appearances_of(s["id"])]
        hits = placed if len(placed) == 1 else hits
    if len(hits) > 1:        # Pike: two lenses with one title, the first silently won
        raise LensRefusal(f"{len(hits)} lenses are titled {name!r} ({', '.join(s['id'] for s in hits)}); retitle one so the name means one thing")
    if hits:
        return hits[0]
    have = [s["title"] for s in w.subjects.values() if kinds.is_lens(s)]
    raise LensRefusal(f"no lens {name!r}. A lens is a thing of kind lens (or a note tagged lens) whose text is the description. Lenses here: {', '.join(have) or 'none'}")


PROVENANCE = ("the", "derived", "test", "read", "freads", "frames", "captured", "members", "states", "missing", "of", "cut", "n", "as", "facts", "views", "counted", "size", "computed")


def emit(node):
    """Add `paint` and `fence` to a scene node and its kids, from the fields the evaluator produced. Idempotent."""
    if node.get("absent"):
        paint = {"kind": "text", "absent": True, "why": node.get("why") or f"not {node['absent']}", "text": None}
    elif node.get("state") and node["state"] != "live" and not node.get("kids"):
        paint = {"kind": "text", "state": node["state"], "text": node.get("text")}
    elif node.get("layout"):
        paint = {"kind": "frame", "flow": node["layout"]}
    else:
        paint = {"kind": "text", "text": node.get("text"), "wrap": "prose"}
    if node.get("text") is not None and paint["kind"] == "frame":
        paint["text"] = node["text"]           # a frame with words: kept until the frame/leaf split (pike-7 section 4)
    if node.get("clamp") is not None:
        paint["clamp"] = node["clamp"]
    if node.get("role"):
        paint["role"] = node["role"]
    if node.get("box"):
        paint["box"] = node["box"]
        if node.get("placed"):
            paint["placed_by"] = node["placed"]
    if node.get("lens"):
        paint["placed"] = {"lens": node["lens"]}
    if node.get("role") == "cut":
        paint["cut"] = True
    # pike-7 sections 6 and 9: tracks, gap, scroll, fold and measure on a frame; wrap and lines on text; share on any child
    if paint["kind"] == "frame":
        for k in ("tracks", "gap", "scroll", "measure"):
            if node.get(k) is not None:
                paint[k] = node[k]
        if node.get("fold"):
            paint["fold"] = {"folded": not node.get("fold_open"), "label": node["fold"] if isinstance(node["fold"], str) else (node.get("text") or node.get("part") or "")}
            if node.get("fold_float"):
                paint["fold"]["float"] = True
            if node.get("fold_handle"):
                paint["fold"]["handle"] = node["fold_handle"]
            if node.get("fold_group"):
                paint["fold"]["group"] = node["fold_group"]
            paint["semantic"] = {"role": "group", "expanded": bool(node.get("fold_open"))}
    elif paint["kind"] == "text" and not paint.get("absent"):
        if node.get("wrap"):
            paint["wrap"] = node["wrap"]
        if node.get("lines"):
            paint["lines"] = node["lines"]
        if node.get("hint"):
            paint["hint"] = node["hint"]
        if not node.get("plain") and node.get("text"):
            rs = runs_of(node["text"], node.get("marks"))
            if node.get("marks"):
                paint["marks"] = True
            if rs:
                paint["runs"] = rs            # the text stays the joined words; the fence and the printer do not change
        ons = {a.get("on") for a in (node.get("acts") or [])}
        if "edit" in ons:
            mx = (node.get("lines") or [1, 1])[1]
            paint["commit"] = "enter" if (not node.get("lines") or mx == 1) else "ctrl-enter"    # emitted, so the print can say which
        if "click" in ons:
            paint["semantic"] = {"role": "button", "label": node.get("text") or ""}
    if node.get("share") is not None:
        paint["share"] = node["share"]
    if node.get("peek") and not paint.get("absent"):
        paint["peek"] = True
    node["paint"] = paint
    acts = list(node.get("acts") or [])
    if node.get("fold") and not any(a.get("on") == "fold" for a in acts):
        acts.append({"on": "fold"})            # no line, no fence: the viewer's own choice
        node["acts"] = acts
    if [a for a in acts if a.get("on") != "fold"]:
        fence = {k: node[k] for k in ("item", "rev", "reads", "defpart", "bind") if k in node}
        if any(a.get("on") == "drop" for a in node["acts"]):
            fence["key"] = node["key"]           # c368: a drop receiver's occurrence is part of what the drop means
        node["fence"] = fence
    for k in node.get("kids") or []:
        emit(k)
    return node


# a1505: the shape of what painter_view sends. A page keeps the painter it loaded until its person asks for the new one
# (the door's quiet line), so a change here that an older lens.js can't read must raise this number; a page whose
# lens.js (const SHAPE) reads another shape then reloads on its own, carrying its view, and says why.
PAINTER_SHAPE = 1


def painter_view(node):
    """The node as the painter should see it: key, paint, acts, fence, kids, and nothing else."""
    out = {"key": node["key"], "paint": node.get("paint"), "acts": node.get("acts") or [], "kids": [painter_view(k) for k in node.get("kids") or []]}
    if node.get("fence"):
        out["fence"] = node["fence"]
    if node.get("part"):
        out["part"] = node["part"]
    return out


def _identity():
    import hashlib
    here = pathlib.Path(__file__).resolve().parent
    h = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()[:12] if f.exists() else None
    return {"compiler": h(here / "scene.py"), "style": h(here / "desk-shell" / "style" / "calm.style")}


def split_scene_arg(desk, arg):
    """a1101: `scene <lens> [<part path> | ok]` -> (lens name, rest or None). The name may be quoted, or bare with
    spaces; a bare line that names a lens whole is the lens (a lens titled `scratch lens` is not lens `scratch`)."""
    import shlex
    arg = arg.strip()
    if arg[:1] in "\"'":
        try:
            words = shlex.split(arg)
        except ValueError as e:
            raise LensRefusal(f"scene: could not read the lens name: {e}")
        if len(words) > 2:
            raise LensRefusal(f"scene <lens> [<part path> | ok]; got {len(words) - 1} words after the name")
        return words[0], (words[1] if len(words) > 1 else None)
    try:
        find_lens(desk, arg)
        return arg, None
    except LensRefusal:
        if " " not in arg:
            raise
    name, _, rest = arg.rpartition(" ")
    find_lens(desk, name.strip())           # refuses as `scene <that name>` would
    return name.strip(), rest


def scene_for(desk, name, part=None):
    """-> (scene, text), through the staged pipeline in lens_ir (parse table, resolve, lower, evaluate through the read
    accessor, emit, print). scene["def"] is the requested definition, the effective transitive closure with each member's
    status (current | fallback), compiler and style identity, and a frame id. Gestures are honoured only on a frame
    whose whole closure is current; a fallback frame is for reading. The old single-pass evaluator (build, _compile,
    scene_for_old) was retired on 5 Oct, after the goldens were printed from this pipeline and frozen as plain worlds."""
    import lens_ir
    return lens_ir.scene_for(desk, name, part)
