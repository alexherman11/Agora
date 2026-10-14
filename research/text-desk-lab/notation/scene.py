"""scene: the piece between the text world and the picture (v0, meant to be argued with).

A LENS is a short text that says how some part of the world is shown and what each gesture means. It lives in
the world as an ordinary note tagged `lens`, so it is edited with desk commands, undone, forked in a worktree,
and read by anyone. A lens is not code. The host that interprets it is small, fixed, and knows no app.
Before adding a word here, read the guidance at the top of desk-shell/lens.js (14 Oct): name the missing capability,
not the case; shared state is world data; one rule beats a guess.

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
    run <prop>                   on a repeat: $run in each instance is its place in the unbroken stretch of neighbours
                                 that hold the same value of that prop (a numbered list: 1. 2., and 1. again after a
                                 break). A let named above a repeat is read inside it
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
    derive <name> = <function> <inputs>   the older spelling of a let that calls a function (9 Oct): `derive wd =
                                 weekday $d` reads as `let wd = weekday($d)`, and `scene <lens> lines` prints the let
    count <selection>            `let count = count(<selection>)` on a part that repeats nothing: $count without
                                 drawing the members (a1101)
    let <name> = <expr>          a named value (Alex, 5 Oct: if and arithmetic). An expression has + - * / and ( ),
      [when <expr> | otherwise]  comparisons (= != < > <= >= has !has), and, or, not; numbers, "text", dates
                                 (2026-10-05), durations (3d 2h), $names, $frame.field, a let named above; and
                                 count(<selection>), sum($field of <selection>), min(...), max(...), which carry
                                 their reach ('41 of 43; 2 have none'); and the functions (expr.FUNCS): weekday(d),
                                 week-of(d), day-n(d, n), day-or-time(when, today), time(when), date(when),
                                 days-from(a, b) (a value of kind rows, for `over $name`; `of days:<a>..<b>` is the
                                 newer way). Kinds are never coerced: '7' is a number,
                                 '2,550 USD' is text and says so. A missing value is none, printed none, never 0.
                                 Several lets of one name with `when` are an if: the first that holds is taken, an
                                 overlap is said, and `otherwise` holds when none of the others do. The scene
                                 prints every let with its expression, inputs and result
    text "... $(<expr>) ..."     an expression computed inside words; the scene prints each one with its inputs
    capture <field>=<value>      use this value instead of following the frame's; prints (now X: differs) when the
                                 world has moved on. Following is the default and is never written down
    carry                        this part's thing can be picked up (pointer or keys) and put down on a part that says `on drop`
    on key <key> do <command>    on a text with `on edit`: Enter, Tab, Shift+Tab or Backspace (only with the caret at the
                                 very start) runs the command instead of its usual work. $head and $tail are the words
                                 before and after the caret. After it the caret follows the text: into a paragraph
                                 the command made, or to the end of the one above when this one is gone
    on click do ... $focus       $focus is the thing whose text the caret is in; such a button does not take the caret
    $selected                    in an edit's or a button's command: the words last highlighted in a text (one with
                                 `marks`) of the same thing, in quotation marks with a space after; empty when none were. A comment box beside a paragraph
                                 can quote what was highlighted in it
    on click press <key>         the button presses Ctrl+B, Ctrl+I or Ctrl+K in the text the caret is in
    on drop <part> do <command>  the receiver of a carried thing; `$carried` fills with the carried thing at the drop; one command
    on <gesture> do <command>    click | edit | drag | select. The command is a desk verb line (`do` is implied); the painter
                                 fills $x $y (drag, click) and $value (edit; select: the words highlighted) at the moment
                                 of the gesture. A gesture carries the item revision and the lens revision it was painted
                                 under; stale is refused.
    on <gesture> when <test> do  the gesture is there only where the test holds (can't tell is not), as `only when` judges

Every placed part carries the world's visibility facts (= offscreen-part, 43% hidden by f52). Painters report what
only they know back through POST /api/observe; the scene prints it per viewer as ~ (viewport, cut by the clamp,
out of view). A lens that stops compiling keeps showing its last version that did, and says so first.

Anything else is refused with the line number. There is no escape to raw HTML, CSS or script in v0, on purpose:
the pressure that builds against that wall is the research result.
"""

import contextlib
import pathlib
import re
from desk import split_batch
from world import Refusal
import expr as X
import style as style_mod
import tree

LAYOUTS = ("column", "row", "free", "grid", "cells")      # pike-7 section 9: grid with tracks; cells is a grid row drawn as display: contents
PAINT_WORDS = ("tracks", "gap", "scroll", "fold", "fold_open", "fold_float", "fold_handle", "fold_group", "measure", "wrap", "lines", "share", "hint", "plain", "peek", "marks", "picture", "commit", "commit_only", "light")   # fold_open and fold_float are fold's modifiers; commit_only is commit's
GESTURES = ("click", "edit", "drag", "menu", "key", "open", "select")
# 14 Oct (Alex: the words highlighted should stay highlighted while he writes about them, and agents should highlight
# too): `on select do <command>` is sent when the viewer finishes highlighting words in the part's text, with $value
# the words, and again with $value empty when they click in such a text without highlighting. Where a highlight is
# kept is the lens's word (a prop on the viewer's own desk, a line, a thing), so it is world data anyone can read.
KEYS = ("Enter", "Tab", "Shift+Tab", "Backspace", "Delete")      # boundary deletion is authored in either direction
PRESSES = ("Ctrl+B", "Ctrl+I", "Ctrl+K")                # the keys a button may press in the text the caret is in      # `drop` was admitted and never painted (Astra). A gesture exists when the painter can do it.
# Alex, 29 Sep ("native right click behavior"): `on menu "<label>" do ...` puts an entry in the part's own menu, which the
# painter opens on a right-click (or the menu key) anywhere on the part; a part with no entries keeps the browser's menu.
NAMES = ("title", "text", "kind", "due", "tags", "id", "item", "it", "n", "count", "index", "run", "in", "before", "after")


class LensRefusal(Exception):
    pass


# ---- admission: what Astra's foundations audit (research/shared-visual-desk/round5-bridge) reproduced ----------
BUDGET = 5000          # scene nodes. A lens that needs more must say `clamp N` on its repeat and let the text say the rest.
# 30 Sep: it was 1500, a round guard Astra's audit asked for against runaway repeats (18 Sep: 'no explicit negotiated
# resource bound'), never a measured limit; the Desktop kept reaching it. It stays a guard, not a working size: deskd
# now rebuilds a scene only when what it shows changed, and the painter keeps its last good paint when one is refused.


def _outside_quotes(line, sep):
    """Split `line` at `sep` wherever it is not inside double quotes (tree.outside_quotes, the one rule since 9 Oct)."""
    return tree.outside_quotes(line, sep)


def _roles():
    """The roles of the seed style, for a lens that names no style= (checked against the file, as before)."""
    st = style_mod.seed("calm")
    return style_mod.role_names(st["text"]) if st else None


# F7 (research/command-center): a style is world data. A note tagged `style` whose title is the style's name holds its
# source, so it is edited, undone, forked and merged like anything else; a lens names its style with prop style=<name>.
# The file desk-shell/style/<name>.style is only the seed for a world that has no such note.
def room_of_thing(w, s):
    """The room holding a subject's first appearance (None when unplaced or outside every room): the scope a lens's own
    lookups stand in (9 Oct, step 7: the lens it places, the style that paints it)."""
    import verbs
    return verbs.room_holding(w, s["id"]) if s else None


def find_style(desk, name, at=None):
    """A style by name, nearest first (verbs.nearest; 9 Oct, step 7): the room `at` (the lens's), the rooms around it,
    the house, then unplaced; a tie is refused. None when no note is titled so (the seed file may answer)."""
    import verbs
    w = desk.world
    hits = [s for s in w.subjects.values() if "style" in (s.get("tags") or []) and s["title"].lower() == name.lower()]
    try:
        return verbs.nearest(desk, hits, name, "styles", at)
    except Refusal as e:
        raise LensRefusal(str(e))


def style_source(desk, name, at=None):
    """-> {name, text, origin, rev} for a style by name, from the world, else from the seed file; None if neither."""
    s = find_style(desk, name, at)
    if s is not None:
        return {"name": name, "text": s["text"], "origin": s["id"], "rev": f"{s['id']}r{s['rev']}"}
    return style_mod.seed(name)


def style_roles(desk, name, at=None):
    """The role names a lens may use under style `name`; None keeps the old behavior (calm.style, the file)."""
    if not name:
        return None
    st = style_source(desk, name, at)
    if st is None:
        raise LensRefusal(f"no style {name!r}: a style is a note tagged style titled {name!r} (or desk-shell/style/{name}.style)")
    return style_mod.role_names(st["text"])


def pulsing_roles(desk, name, at=None):
    """a1140: the roles whose words include `pulse` in the style the painter installs for a lens (its style=, else calm).
    The painter moves them, so the print says so: a reader of the text must learn what the eye sees moving. A style
    the painter refuses paints nothing, so nothing pulses."""
    st = style_source(desk, name or "calm", at) or {}
    try:
        roles = style_mod.parse(st.get("text") or "")["roles"]
    except style_mod.StyleRefusal:
        return set()
    return {n for n, r in roles.items() if "pulse" in r["props"]}


def mark_pulse(node, roles):
    """Set `pulse` on every node whose role pulses. Printer-side only: emit() never sends it to the painter."""
    if roles and node.get("role") in roles:
        node["pulse"] = True
    for k in node.get("kids") or []:
        mark_pulse(k, roles)


# 8 Oct (step 1 of the grammar unification): one reader of a style, style.py. Python reads it and the painter is handed
# the looks; the mirror that scene.py kept of style.js (a1101), and the node test that held them together, are gone.
def style_parse(src):
    """-> {tokens, roles: {name: {props, line}}, fonts, themes} or raises LensRefusal('line N: ...')."""
    try:
        return style_mod.parse(src)
    except style_mod.StyleRefusal as e:
        raise LensRefusal(str(e))


def style_check(src):
    """-> {"refusal": str or None, "roles": n, "tokens": n, "unread": [(role, prop, line, why)]}: what the painter
    will make of this style text."""
    return style_mod.check(src)


def _cmd_value(v):
    """A value going inside a quoted desk command keeps its quotes and backslashes (Astra: `She said "yes"` lost them)."""
    return str(v).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


# ---- rows: parts of the world that are not appearances, made repeatable ------------------------------------
# Moss, Lark and Wren hit one wall from three sides: a lens repeats over a selection, and sections, comments,
# actors, events and worktrees were not selectable. Each source below is a fact the desk already printed
# somewhere; here it gets named fields. `rows <source>` prints the same rows in the desk, so a lens never sees
# anything the terminal cannot.
SOURCES = {
    "captures": ("captures [cap-<id> ...]", ("cid", "label", "summary", "remaining")),
    "sections": ("sections:<id>", ("item", "heading", "words", "text", "index")),
    "comments": ("comments:<id>", ("item", "cid", "by", "text", "state", "replies", "image", "awaiting", "to", "eid", "unread", "unread_count", "reply_count", "latest", "opening_awaiting")),
    "replies": ("replies:<id>", ("item", "rid", "thread", "by", "text", "index", "awaiting", "to", "eid", "unread")),
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
    "sayings": ("sayings [for:<name>] [in:<id>] (or involving:<name>)",
                ("item", "what", "saying", "by", "name", "at", "in", "to", "said",
                 "answered", "edited", "before", "state", "eid", "thread",
                 "source", "line", "reply_to", "mark", "context", "context_summary")),
    # a1581 (Juniper c1695: lines out of every default find, but reachable when asked): every chat line as a thing,
    # oldest first, in one chat or all; by and at read from the event that made it ('unknown' when none can be found)
    "lines": ("lines[:<chat>]", ("item", "chat", "line", "who", "by", "at", "to", "said", "edited", "reply_to", "eid")),   # and each line's own fields
    "house": ("house[:<corner>]", ("resident", "corner", "doing", "turns", "since", "beat", "fresh", "room", "item")),   # item: the corner, so a gesture on a row acts on it (30 Sep, wake/rest)
    # what each resident wrote, its last turns, oldest first like a chat (Alex, 29 Sep: to see their turns and text;
    # 30 Sep: newest at the bottom on every chat-like list, so a lens shows the newest with `clamp last N, scroll end`)
    "turns": ("turns[:<corner>]", ("resident", "corner", "turn", "at", "said", "acts")),
    # 9 Oct (step 5): the days of a span as rows, what `derive days = days-from a b` + `over $days` built; terms over
    # its fields keep the Mondays (`of days:$term.start..$term.end weekday=Mon as d`)
    "days": ("days:<start>..<end>", ("n", "date", "weekday", "week")),
    # 8 Oct (step 4, table.py): the desk's own vocabulary as rows, so a lens can show it and `rows slots host=lens` lists
    # what a lens word takes; kinds with what their things carry and what their notes declare
    "words": ("words [host=verb|command|lens|term|kind]", ("host", "word", "form", "slots", "doc")),
    "slots": ("slots [host=... word=...]", ("host", "word", "slot", "type", "needed", "doc")),
    "kinds": ("kinds", ("kind", "is", "shape", "things", "props", "declared")),
    # 9 Oct (a3806): the lines the desk did not do, counted by shape, the most met first (verbs.record_reach): which
    # refusal or missing word is worth curing shows itself, without anyone deciding whose fault each one was
    "reaches": ("reaches", ("shape", "n", "who", "kind", "last", "line")),
    # a5052 (14 Oct): the windows a host keeps on the screen (research/window-lab/wm.py), as it last said them, in its
    # order: witnessed beside the house (witnessed.py), never in the world. name is the host's own for the window (a
    # repeat keys each by it), kind agora or adopted, pinned/collapsed/focused yes or no, age the seconds since it said so
    "windows": ("windows", ("name", "title", "lens", "kind", "pinned", "collapsed", "focused", "order", "age", "by")),
}
# a source's field names: read bare inside their own repeat ($who in `of messages:`); a text's $name that is one of them
# is no prop of the thing, and no aspect for the fence. 8 Oct: they no longer take a name away from `let` or `as` in
# every lens (`let shape` stopped compiling when a source gained a field shape): the nearer binding wins, as names.py says
SOURCE_FIELDS = tuple(dict.fromkeys(f for _, fs in SOURCES.values() for f in fs))
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
    first = src.split(" ")[0] if src else ""         # 8 Oct (step 3): terms may follow any source after a space
    return first.partition(":")[0]


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
    source under its first name.

    `involving:<name>` instead keeps their own outgoing sayings and explicitly
    addressed incoming sayings (subject to incoming chat membership). Broadcasts
    alone do not qualify. It does not infer read, answered or agreement state.
    Native lines remain one row even when their text spans several lines."""
    import persons
    import rooms
    from world import addressed_before
    w = desk.world
    me, involving, only = "", "", None
    for t in str(terms).replace(",", " ").split():
        k, _, v = t.partition(":")
        if k == "for" and v:
            me = v.lower()
        elif k == "involving" and v:
            involving = v.lower()
        elif k == "in" and v:
            nid = desk._resolve(v)
            only = (w.nodes.get(nid) or {}).get("subject") or (nid if nid in w.subjects else None)
            if only is None:
                raise LensRefusal(f"sayings in:{v}: {v} has no lines or comments to list")
        else:
            raise LensRefusal(f"sayings: unknown term {t!r}; " + SOURCES["sayings"][0])
    if me and involving:
        raise LensRefusal("sayings takes either for:<name> or involving:<name>, not both")
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
            listed = set()
            for k in range(len(tl) - 1, -1, -1):
                text, line, (at, eid) = tl[k]
                if involving and line is not None:
                    if line["id"] in listed:
                        continue
                    listed.add(line["id"])
                    text = line["text"]
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
                row = {"item": where[sid], "what": "line",
                            "saying": line["id"] if line else "", "by": by,
                            "name": who, "at": _clock(at), "in": s["title"], "to": ", ".join(to), "said": said,
                            "answered": answered, "edited": "edited" if line and line.get("edited") else "",
                            "before": before, "state": "", "eid": eid or f"{where[sid]}-{k + 1}",
                            "chat": s["title"], "who": by, "open": flip.get(answered, ""), "index": k + 1,
                            "line": line["id"] if line else "", "_t": (at or "", _enum(eid)),
                            "source": sid, "thread": "",
                            "reply_to": line.get("reply_to", "") if line else "",
                            "mark": "", "context": ""}
                # An authored field may describe a line, never forge its identity,
                # author, recipients, source or presentation bookkeeping.
                if line:
                    reserved = set(SOURCES["sayings"][1]) | set(row)
                    extra = {key: value for key, value in line_fields(line).items()
                             if key not in reserved and not key.startswith("_")
                             and isinstance(value, str)}
                    row.update(extra)
                    for key in ("mark", "context"):
                        value = line_fields(line).get(key, "")
                        row[key] = value if isinstance(value, str) else ""
                row["context_summary"] = ""
                if row["context"]:
                    from message_context import summary
                    row["context_summary"] = summary(row["context"])
                out.append(row)
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
                        "index": i + 1, "line": "", "_t": (at or "", _enum(e["id"] if e else "")),
                        "source": sid, "thread": c["id"], "reply_to": "",
                        "mark": "", "context": ""})
        # Replies are sayings in their own right: a return message to the opening
        # author must reach For you even though their own opening comment does not.
        for c in cs:
            replies = c.get("replies") or []
            events = rooms.reply_events(w).get(c["id"], [])
            for i, (reply, e) in enumerate(zip(replies, events), 1):
                writer = str(reply.get("by") or "").split("/")[0].lower()
                to = rooms.comment_to(e)
                if e.get("args", {}).get("line") != reply.get("text"):
                    continue
                if me and (rooms.same_person(w, writer, me) or not rooms.shown(w, s, to, me, comment=True)):
                    continue
                answered = ("yes" if any(rooms.same_person(w, r.get("by"), me) for r in replies[i:]) else "no") if me else ""
                by = str(persons.reply_by(w, c, i - 1) or "")
                at, eid = e.get("at", ""), e["id"]
                out.append({"item": where[sid], "what": "reply", "saying": f"{c['id']}/reply/{i}",
                            "by": by[:1].upper() + by[1:], "name": writer, "at": _clock(at), "in": s["title"],
                            "to": ", ".join(to), "said": reply["text"], "answered": answered, "edited": "",
                            "before": "", "state": "resolved" if c.get("resolved") else "open", "eid": eid,
                            "chat": s["title"], "who": by, "open": flip.get(answered, ""), "index": i, "thread": c["id"],
                            "line": "", "_t": (at or "", _enum(eid)),
                            "source": sid, "reply_to": "", "mark": "", "context": ""})
    out.sort(key=lambda r: r.pop("_t"))
    if involving:
        target = persons.resolve(w, involving)[0] if persons.on(w) else None
        viewer = persons.name_now(w, target) if target else involving

        def matches(name, event, author=False):
            if target:
                # Stored names belong to the person at the event, not whoever
                # might take up that same name later.
                pid = persons.of_event(w, event) if author and \
                    persons.norm(event.get("by")) == persons.norm(name) else None
                pid = pid or (name if persons.is_pid(w, name) else
                              persons.at(w, name, _enum(event["id"])) if event.get("id") else
                              persons.today(w, name))
                return pid == target
            return rooms.same_person(w, name, involving)

        def included(row):
            event = w.event_by_id(row["eid"]) or {}
            if matches(row["name"], event, author=True):
                return True
            named = [name.strip() for name in row["to"].split(",")
                     if name.strip() and name.strip() not in rooms.EVERYONE]
            if not any(matches(name, event) for name in named):
                return False
            return row["what"] != "line" or rooms.is_member(
                w, w.subjects[row["source"]], viewer)

        out = [row for row in out if included(row)]
    extra = {key for row in out for key in row} - set(SOURCES["sayings"][1])
    for row in out:
        for key in extra:
            row.setdefault(key, "")
    return out


def _enum(eid):
    """An event id's number ('e5967' -> 5967), 0 when it has none: sayings of one second stay in the order said."""
    d = "".join(ch for ch in str(eid or "") if ch.isdigit())
    return int(d) if d else 0


# 14 Oct (Snappy Desk stage 2): while a lens is built the world holds still, so what is read of the world alone is read
# once per build, not once per part that asks (a page of 70 paragraphs read its talk's 88 lines 70 times: 6160 person
# labels, half the build). A value kept here depends on the world and nothing else: no frame, viewer or lens.
_STILL = {}


@contextlib.contextmanager
def still(w):
    """While a lens is built from world `w`: answers that depend only on the world are kept until it is done."""
    if id(w) in _STILL:
        yield
        return
    _STILL[id(w)] = {}
    w.__dict__["_still_kids"] = {}       # world.py: children read from one index while it holds still
    try:
        yield
    finally:
        _STILL.pop(id(w), None)
        w.__dict__.pop("_still_kids", None)


def _once(w, key, make):
    m = _STILL.get(id(w))
    if m is None:
        return make()
    if key not in m:
        m[key] = make()
    return m[key]


def line_rows(desk, chat=None):
    """Each call has rows of its own to change; the rows are made once while the world holds still (still)."""
    return [dict(r) for r in _once(desk.world, ("line_rows", chat), lambda: _line_rows(desk, chat))]


def _line_rows(desk, chat=None):
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
                        "reply_to": l.get("reply_to", ""), "eid": l.get("ev") or l["id"], "_t": (e or {}).get("at", ""),
                        **line_fields(l)})
    out.sort(key=lambda r: r.pop("_t") or "")
    # 14 Oct: a line's own fields (about=, quote=, mark=, or any a writer gave) are row fields; a line without one
    # reads it as empty, as long as some line here has it
    extra = sorted({k for r in out for k in r} - set(SOURCES["lines"][1]))
    for r in out:
        for k in extra:
            r.setdefault(k, "")
    return out


def line_fields(l):
    """A chat line's own fields (world.py LINE_OWN says which words are not fields). Lines of 13 Oct kept about, quote
    and mark beside the text; since 14 Oct any field is kept under `fields`."""
    own = {k: l[k] for k in ("about", "quote", "mark") if l.get(k)}
    own.update({k: v for k, v in (l.get("fields") or {}).items() if k not in SOURCES["lines"][1]})
    return own


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
    """-> list of dicts, or None when `source` is not a row source (then it is an ordinary selection). 8 Oct (step 3):
    the source may be followed by terms over its fields, read by the one comparison (`house doing=awake`,
    `messages:a12 who=alex`, `sayings for:claude answered=no`; knife.filter_rows)."""
    import knife
    src = source.strip()
    first, _, rest = src.partition(" ")
    if source_head(src) == "captures":
        ids = list(dict.fromkeys(rest.split()))
        if len(ids) > 8 or any(not re.fullmatch(r"cap-\d+", cid) for cid in ids):
            raise LensRefusal("captures takes at most eight cap-<id> references")
        if not ids:
            return []
        try:
            import captures
        except ImportError:
            return [{"cid": cid, "label": "Attachment unavailable",
                     "summary": "Capture service unavailable; this attachment is kept.",
                     "remaining": " ".join(other for other in ids if other != cid)}
                    for cid in ids]
        rows = []
        capture_session = session or getattr(desk, "_session", "")
        actor = str(desk.world.me).split("/")[0]
        for cid in ids:
            try:
                value = captures.load_capture(capture_session, actor, cid)
                refs = value.get("refs") or []
                label = f"{len(refs)} native item(s)" if refs else "Image selection"
                summary = captures.preview(capture_session, actor, cid)
            except captures.CaptureError as exc:
                label, summary = "Attachment unavailable", str(exc)
            rows.append({"cid": cid, "label": label, "summary": summary,
                         "remaining": " ".join(other for other in ids if other != cid)})
        return rows
    if source_head(src) == "sayings":
        own = [t for t in rest.split() if t.startswith(("for:", "involving:", "in:"))]
        terms = [t for t in rest.split() if t not in own]
        rs = saying_rows(desk, " " + " ".join(own) if own else "")
    else:
        terms = [t for t in re.split(r"[,\s]+", rest) if t]
        rs = _rows_of(desk, first, session)
    if rs is None or not terms:
        return rs
    return knife.filter_rows(desk.world, rs, terms, __import__("persons").active(desk), SOURCES[source_head(src)][0])


def _rows_of(desk, source, session=None):
    w = desk.world
    head, _, arg = source.strip().partition(":")
    if head not in SOURCES or (head not in ("house", "turns", "lines") and (head in ("sections", "comments", "replies", "messages", "inbox", "days")) != bool(arg)):
        return None      # sections, comments and messages need an id, inbox a name, days a span; house, turns and lines one or none; the rest none
    if head == "days":
        a, _, b = arg.partition("..")
        da, _ = X._date_in(X.typed(a.strip()))
        db, _ = X._date_in(X.typed(b.strip()))
        if da is None or db is None:
            raise LensRefusal(f"{source}: days takes two dates, days:<start>..<end>; got {arg!r}")
        rows, why = X.day_rows(da, db)
        if rows is None:
            raise LensRefusal(f"{source}: {why}")
        return rows
    if head in ("words", "slots", "kinds"):
        import table
        return {"words": table.word_rows, "slots": table.slot_rows, "kinds": table.kind_rows}[head](desk)
    if head == "inbox":
        return saying_rows(desk, "for:" + arg)
    if head == "lines":
        return line_rows(desk, desk._resolve(arg) if arg else None)
    if head == "house":
        return house_rows(desk, desk._resolve(arg) if arg else None)
    if head == "turns":
        return turn_rows(desk, desk._resolve(arg) if arg else None)
    if head == "reaches":
        import verbs
        return verbs.reach_rows(desk)
    if head == "windows":
        import witnessed
        doc = witnessed.read(session or getattr(desk, "_session", "") or "", "windows")
        return [] if doc is None else [{**{f: "" for f in SOURCES["windows"][1]}, **{k: v for k, v in r.items() if k in SOURCES["windows"][1]},
                                        "order": k, "age": doc["age"], "by": doc.get("by") or ""}
                                       for k, r in enumerate(doc["rows"], 1) if isinstance(r, dict) and r.get("name")]
    if arg:
        nid = desk._resolve(arg)
        s = w.subjects.get((w.nodes.get(nid) or {}).get("subject")) or w.subjects.get(nid)
        if s is None:
            raise LensRefusal(f"{source}: {arg} has no content to take {head} from")
    if head == "sections":
        return [{"item": nid, "heading": h or "(before the first heading)", "words": len(b.split()), "text": b, "index": k}
                for k, (h, b) in enumerate(w.sections(s["text"]), 1)]
    if head == "replies":
        import rooms
        waiting = {c["id"]: rooms.thread_waiting(w, c, w.me) for c in s.get("comments", [])}
        unread = {c["id"]: rooms.thread_read_state(w, c, w.me)[0] for c in s.get("comments", [])}
        events = rooms.reply_events(w)
        return [{"item": nid, "rid": f"{c['id']}/reply/{i}", "thread": c["id"],
                 "by": r["by"], "text": r["text"], "index": i,
                 "to": ",".join(rooms.comment_to(e)) if e else "", "eid": e.get("id", ""),
                 "unread": "yes" if i in unread[c["id"]] else "no",
                 "awaiting": "yes" if i in waiting[c["id"]] else "no"}
                for c in s.get("comments", [])
                for i, r in enumerate(c.get("replies") or [], 1)
                for e in [events.get(c["id"], [])[i - 1] if i <= len(events.get(c["id"], [])) else {}]]
    if head == "comments":
        import persons
        import rooms
        events = persons.comment_events(w)
        # replies (13 Oct): the thread under the comment as one text, a line a reply, each signed
        return [{"item": nid, "cid": c["id"], "by": c["by"], "text": c["text"], "state": "resolved" if c["resolved"] else "open",
                 "replies": chr(10).join(f"{r['by']}: {r['text']}" for r in c.get("replies") or []),
                 "image": (c.get("image") or {}).get("data_url", ""),
                 "to": ",".join(rooms.comment_to(e)) if e else "", "eid": e.get("id", ""),
                 "unread": "yes" if 0 in unread else "no", "unread_count": len(unread),
                 "reply_count": len(c.get("replies") or []), "latest": latest,
                 "opening_awaiting": "yes" if 0 in waiting else "no",
                 "awaiting": "yes" if waiting else "no"}
                for c in s.get("comments", []) for e in [events.get(c["id"], {})]
                for unread, latest in [rooms.thread_read_state(w, c, w.me)]
                for waiting in [rooms.thread_waiting(w, c, w.me)]]
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
        raise LensRefusal("rows <source> [k=v k<v ...]. Sources: " + ", ".join(v[0] for v in SOURCES.values()))
    fields = SOURCES[source_head(source)][1]
    if source_head(source) == "lines":          # 14 Oct: and the fields the lines were given
        fields = fields + tuple(sorted({k for r in rs for k in r} - set(fields)))
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


def _w_light(node, p, val, n, env):
    # 13 Oct (Alex: comments live on the text): `light "<passages>"` lights each passage named, one a line, where it
    # stands in this part's words; a template filled as text is (`light "$(spots)"`). Paint only: the words are unchanged
    # 14 Oct: more than one template, each its passages (light "$(spots)" "$(mine)")
    parts = re.findall(r'"([^"]*)"', val)
    if not parts or not any(parts) or re.sub(r'"[^"]*"', "", val).strip():
        raise LensRefusal(f'line {n}: `light "<passages, one a line>" ["<more>" ...]` (a template: light "$(spots)"); got {p!r}')
    node["light"] = chr(10).join(x for x in parts if x)


def _w_commit(node, p, val, n, env):
    # 14 Oct: `commit enter only` (or ctrl-enter only): the key sends and nothing else does; leaving the text keeps the
    # draft. For a message, which is an act toward someone; an edit of words already there is saved on leaving too
    m = re.fullmatch(r"(explicit|enter|ctrl-enter)( only)?", val.strip())
    if not m or (m.group(2) and m.group(1) == "explicit"):
        raise LensRefusal(f"line {n}: `commit explicit|enter|ctrl-enter [only]`; got {p!r}")
    node["commit"] = m.group(1)
    if m.group(2):
        node["commit_only"] = True


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


def _w_picture(node, p, val, n, env):
    # 13 Oct (Alex: the design-review window needs diagrams): the words are a drawing, written as SVG, and the painter
    # draws it. The text stays the drawing's source, so a reader of the print can read and write one as any other text.
    node["picture"] = True


def _w_peek(node, p, val, n, env):
    if val and (not val.isdigit() or int(val) < 1):
        raise LensRefusal(f"line {n}: peek [positive line count]")
    node["peek"] = int(val) if val else True


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
    node["props"] = [v for v, dot in re.findall(r"\$(\w+)(\.\w+)?", node["text"]) if not dot and v not in NAMES and v not in SOURCE_FIELDS]


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


def _w_run(node, p, val, n, env):
    # Juniper, 7 Oct (a3470): a numbered item reads 1. 2. within its own list. `run <prop>` on a repeat gives each
    # instance $run: its place in the unbroken stretch of neighbours, in the order shown, that hold the same value of
    # that prop. A neighbour with another value (or none) ends the stretch, and the next begins again at 1.
    if not re.fullmatch(r"[BSw.-]+".replace("BS", chr(92)), val or ""):
        raise LensRefusal(f"line {n}: `run <prop>` on a repeat; got {p!r}")
    node["run"] = val


def run_places(values):
    """[value] in the order shown -> each one's place in its unbroken stretch of equal values, from 1."""
    out, prev, c = [], object(), 0
    for v in values:
        c = c + 1 if v == prev else 1
        prev = v
        out.append(c)
    return out


def _w_count(node, p, val, n, env):
    if not val.strip():
        raise LensRefusal(f"line {n}: `count <selection or row source>`; got {p!r}")
    node["count"] = val.strip()       # a1101: '7 paused', without drawing the seven
    # 9 Oct (step 5): the word is `let count = count(<selection>)`, read by the one evaluator; the fence takes the
    # membership from the let's select, as it took it from the word's
    if any(l == "count" for l, _, _ in node["let"]):
        raise LensRefusal(f"line {n}: count is already said on this part")
    node["let"].append(("count", f"count({val.strip()})", None))


def _w_over(node, p, val, n, env):
    val, _, asname = val.partition(" as ")       # Sable, 7 Oct: `over $comments as c` was refused by printing its own form
    val = val.strip()
    if not re.fullmatch(r"\$\w+", val):
        raise LensRefusal(f"line {n}: `over $<list> [as <frame>]` repeats over a list the current thing holds ($tags) or "
                          f"the rows a let holds (`let days = days-from($a, $b)`); got {p!r}. Rows from a source (comments:<id>, "
                          f"days:<a>..<b>; the command `rows` lists them) go under `of`: `of comments:$item`")
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
    """The older spelling (Pike W6, a closed list of interpretations) of a let that calls a function: `derive wd =
    weekday $d` is `let wd = weekday($d)` since 9 Oct (step 5), read by the one evaluator and printed as a let. The
    word records the let's spelling, so `scene <lens> lines` and `--convert` move a lens to it."""
    m = re.fullmatch(r"(\w+) = ([\w-]+)((?: \S+)*)", val)
    if not m:
        raise LensRefusal(f"line {n}: `derive <name> = <function> <inputs>` (the older spelling of `let <name> = <function>(<inputs>)`); got {p!r}")
    dname, interp, ins = m.group(1), m.group(2), m.group(3).split()
    if interp not in X.FUNCS:
        raise LensRefusal(f"line {n}: no interpretation {interp!r}. The list is closed: " + ", ".join(f"{k} <{'> <'.join(v[0])}>" for k, v in X.FUNCS.items()))
    if len(ins) != len(X.FUNCS[interp][0]):
        raise LensRefusal(f"line {n}: {interp} takes {len(X.FUNCS[interp][0])} input(s): {' '.join(X.FUNCS[interp][0])}; got {len(ins)}")
    if dname in NAMES or any(dname == l for l, _, _ in node["let"]):
        raise LensRefusal(f"line {n}: derive {dname}: that name is taken")
    spelled = f"let {dname} = {interp}({', '.join(ins)})"
    _w_let(node, spelled, spelled[4:], n, env)
    return spelled


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
    if (lname in NAMES and lname != "count") or lname in X.KEYWORDS:
        raise LensRefusal(f"line {n}: let {lname}: that name is taken")
    if lname == "count":        # 9 Oct: `let count = count(<sel>)` is what the word `count <sel>` says (a1101)
        node["count"] = node["count"] or rest
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
    # Alex, 7 Oct ('buttons on top'): a button presses a key in the text the caret is in. It is the painter's own act:
    # the line `press Ctrl+B` is never sent to the desk
    m = re.fullmatch(r"click press (.+)", val.strip())
    if m:
        if m.group(1) not in PRESSES:
            raise LensRefusal(f"line {n}: `on click press <{'|'.join(PRESSES)}>`; got {p!r}")
        node["on"].append({"on": "click", "line": "press " + m.group(1)})
        return
    g, do, cmd = val.partition(" do ")
    drop_part = label = when = None
    # 14 Oct (Alex: comments from the right-click box 'go to the ether' on a design, whose margin is not shown; then
    # 'make those changes more general purpose'): any gesture may say `when <test>`, and is there only where the test
    # holds (can't tell is not), so one part can act one way on a plain document and another on a design
    m = re.fullmatch(r'((?:menu\s+"[^"]+")|[^"]*?)\s+when\s+(.+)', g.strip())
    if m:
        g, when = m.group(1), m.group(2)
    if g.startswith("key "):
        label, g = g[4:].strip(), "key"
        if label not in KEYS:
            raise LensRefusal(f"line {n}: `on key <{'|'.join(KEYS)}> do <desk command>` on a text that has `on edit`; got {p!r}")
    if g.startswith("drop "):
        drop_part, g = g[5:].strip(), "drop"
    if g.startswith("menu "):
        m = re.fullmatch(r'"([^"]+)"', g[5:].strip())
        if not m:
            raise LensRefusal(f'line {n}: `on menu "<label>" [when <test>] do <desk command>`: the entry\'s words, quoted; got {p!r}')
        label, g = m.group(1), "menu"
    if (g not in GESTURES and g != "drop") or not do or not cmd.strip() or (g == "drop" and not drop_part) or (g == "menu" and not label):
        raise LensRefusal(f"line {n}: `on <click|edit|drag|select> [when <test>] do <desk command>`, `on menu \"<label>\" do <desk command>`, `on key <{'|'.join(KEYS)}> do <desk command>`, `on click press <key>` or `on drop <part> do <desk command>`; got {p!r}")
    if when:
        try:
            X.parse(when)
        except X.ExprError as e:
            raise LensRefusal(f"line {n}: `when {when}`: {e}")
    cmd = cmd.strip()
    if g == "drop" and len(split_batch(cmd)) > 1:
        raise LensRefusal(f"line {n}: a drop is one proposal: one desk command, not {len(split_batch(cmd))}")
    # `on drag do move $item ...` reads as English; the desk wants `do move ...`. A gesture names a verb
    # unless it begins with one of the desk's own reading or session commands.
    if cmd.split(" ")[0] not in ACT_COMMANDS:
        cmd = "do " + cmd
    node["on"].append({"on": g, "line": cmd, **({"part": drop_part} if drop_part else {}), **({"label": label} if label else {}),
                       **({"when": when.strip()} if when else {})})


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
    "commit": ("commit explicit|enter|ctrl-enter [only]", _w_commit),
    "share": ("share <weight>", _w_share),
    "hint": ('hint "..."', _w_hint),
    "plain": ("plain", _w_plain),
    "marks": ("marks", _w_marks),
    "picture": ("picture", _w_picture),
    "light": ('light "<passages>"', _w_light),
    "peek": ("peek [lines]", _w_peek),
    "carry": ("carry", _w_carry),
    "role": ("role <name> [when <selection | expr>]", _w_role),
    "text": ('text "..."', _w_text),
    "clamp": ("clamp [last] <n>", _w_clamp),
    "the": ("the <selection> [as <frame>]", _w_the),
    "of": ("of <selection | row source> [as <frame>]", _w_of),
    "over": ("over $<list> [as <frame>]", _w_over),
    "by": ("by <prop>[, <prop>]", _w_by),
    "run": ("run <prop>", _w_run),
    "count": ("count <selection>", _w_count),
    "as": ("as <frame>", _w_as),
    "each": ("each <part>", _w_each),
    "at": ("at item", _w_at),
    "only": ("only when <selection | expr>", _w_only),
    "derive": ("derive <name> = <function> <inputs>", _w_derive),
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
    if (node["count"] or any(l == "count" for l, _, _ in node["let"])) and (node["of"] or node["over"]):
        raise LensRefusal(f"line {n}: a repeat already has $count, its true size; `count` is for a part that repeats nothing")
    if node["as"] and (node["as"] in NAMES or node["as"] in ("value", "x", "y")):
        raise LensRefusal(f"line {n}: `as {node['as']}` would shadow a built-in name; choose another frame name")
    if node["as"] and not (node["the"] or node["of"] or node["over"]):
        raise LensRefusal(f"line {n}: `as {node['as']}` names the thing chosen here, so this part needs `the`, `of` or `over`")
    if node.get("run") and not (node["of"] or node["over"]):
        raise LensRefusal(f"line {n}: `run {node['run']}` counts along a repeat; this part repeats nothing (say `of` and `each`)")
    if node["by"] and not node["of"]:
        raise LensRefusal(f"line {n}: `by` orders a repeat; this part has no `of`")
    if node["capture"] and not node["the"]:
        raise LensRefusal(f"line {n}: `capture` holds a field of the thing chosen by `the`; this part has no `the`")
    import knife      # a3359: a selection that names due as a prop is refused here, when the lens is saved, not at a look
    only = None if X.looks_like(node["only"]) else node["only"]
    counted = None if X.looks_like(node["count"]) else node["count"]
    for sel in [node["of"], node["the"], only, counted] + [c for _, c in node["role_when"] if not X.looks_like(c)]:
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
        spelled = row[1](node, p, val, n, env)
        node["words"].append(spelled if isinstance(spelled, str) else p)     # an older spelling records the one form

    # 9 Oct (step 5): the lines are read by tree.read, the one indentation reader (a style and a kind note's slot
    # lines read through it too); what a line means here is a part (`name : ...`) or a word of the part above it.
    # A line indented under a word line belongs to that word's part, as it did when a word line held no place.
    def visit(tn, parent):
        n, text, indent = tn.line, tn.text, tn.indent
        pieces = _outside_quotes(text, " : ")
        head = pieces[0] if len(pieces) > 1 else (text[:-2] if text.endswith(" :") else None)
        if head is None or not re.fullmatch(r"[\w-]+", head):
            if parent is None:
                raise LensRefusal(f"line {n}: {text!r} is a word with no part above it. A part is `name : <what it is>`; "
                                  f"its words are indented under it, one per line")
            say(parent, text, n)
            for kid in tn.kids:
                visit(kid, parent)
            return
        node = _part(head, (" : ".join(pieces[1:]) if len(pieces) > 1 else ""), n, indent, parent)
        for kid in tn.kids:
            visit(kid, node)

    def _part(name, rest, n, indent, parent):
        nonlocal root
        node = {"name": name, "kids": [], "line": n, "layout": None, "role": None, "role_when": [], "text": None, "clamp": None,
                "of": None, "over": None, "each": None, "at": None, "on": [], "lens": None, "only": None, "props": [],
                "the": None, "as": None, "let": [], "capture": {}, "src": "", "words": [], "carry": False, "by": None, "run": None,
                "tracks": None, "gap": None, "scroll": None, "fold": False, "measure": None, "wrap": None, "lines": None, "share": None, "hint": None, "plain": False, "peek": False, "marks": False, "picture": False, "light": None, "count": None}
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
        else:
            if parent is None:
                raise LensRefusal(f"line {n}: indented part with no parent")
            if any(k["name"] == name for k in parent["kids"]):
                raise LensRefusal(f"line {n}: {parent['name']} already has a child named {name!r}; siblings need different names (they are its address)")
            parent["kids"].append(node)
        return node

    for top in tree.read(src, skip=lambda text, indent: indent == 0 and re.fullmatch(r"lens \S+", text) is not None):   # a header line, `lens <name>`, as the first lenses began; an indented `lens x` is the word
        visit(top, None)
    if not root:
        raise LensRefusal("an empty lens shows nothing; start with  window : column")
    every = [k for p in parts.values() for k in _walk(p)]
    for k in every:
        k["src"] = f"{k['name']} : " + ", ".join(k["words"])     # one spelling of the part's own words, whichever form it was written in
        _check_part(k, k["line"])          # after every line, since a part's words may follow its children
        for wd in ("gap", "scroll", "fold", "measure"):
            if k[wd] not in (None, False) and not k["layout"]:
                raise LensRefusal(f"line {k['line']}: `{wd}` is a frame word; this part has no layout (column, row, free, grid)")
        for wd in ("wrap", "lines", "hint", "commit", "light"):
            if k.get(wd) is not None and k["text"] is None:
                raise LensRefusal(f"line {k['line']}: `{'verbatim' if wd == 'wrap' else wd}` is a text word; this part prints no text")
        if k["picture"] and (k["text"] is None or any(a["on"] == "edit" for a in k["on"])):
            raise LensRefusal(f"line {k['line']}: `picture` draws a text that is a drawing (SVG): this part " + ("prints no text" if k["text"] is None else "is edited, and a drawing is edited as its source, in a part without `picture`"))
        if k["layout"] == "grid" and not k["tracks"]:
            raise LensRefusal(f"line {k['line']}: `grid` names its tracks: grid 1 3 3 1")
        if k["clamp"] is not None and k["text"] is not None and any(a["on"] == "edit" for a in k["on"]):
            raise LensRefusal(f"line {k['line']}: `on edit` on a clamped text: the person would replace words the clamp hides; drop the clamp, or edit through a part that shows the whole value")
        if any(a["on"] == "key" for a in k["on"]) and not any(a["on"] == "edit" for a in k["on"]):
            raise LensRefusal(f"line {k['line']}: `on key` is for a text being written: this part has no `on edit`")
        if any(a["on"] == "open" for a in k["on"]) and not k["fold"]:
            raise LensRefusal(f"line {k['line']}: `on open` needs a fold handle")
        if type(k["peek"]) is int and k["text"] is None:
            raise LensRefusal(f"line {k['line']}: `peek <lines>` needs text")
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
GESTURE_FACTS = ("value", "x", "y", "carried", "head", "tail", "focus", "selected", "quoted", "quoted_in")   # quoted, quoted_in: 13 Oct


def _refs_of(node):
    """Every $name and $frame.field this part's own words use, with the word they sit in."""
    out = []
    srcs = [("text", node["text"] or ""), ("only", node["only"] or ""), ("of", node["of"] or ""), ("the", node["the"] or ""),
            ("lens", node["lens"] or ""), ("count", node["count"] or "")]
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
    if name in ("title", "text", "kind", "due", "tags", "id", "item", "n", "count", "index", "run"):
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


# the interpretations (`_day_n`, `_days_from`, `_weekday`, `_week_of`, `_when`, `_day_or_time`, INTERPS) moved to expr.FUNCS on 9 Oct
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
        if a not in ctx and (frames.get(a) or {}).get("id"):
            # 14 Oct: a frame's bare name is its thing, as $item is the current one (`on select do prop $r ...`)
            if track is not None:
                track["frames"].add(a)
            return str(frames[a].get("item") or frames[a]["id"])
        return str(ctx[a]) if a in ctx else m.group(0)

    return _VAR.sub(rep, tpl)


def _fill_text(tpl, ctx, track, run, esc=None):
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
        put = X.fmt(val, reach=False) + (f" ({val.reach.split(';')[0]})" if val.partial and val.reach else "")
        # 14 Oct: in a command a computed value is escaped as a $name's is (_cmd_value), so words with a quote in them
        # stay one value and never end the command early
        out += tpl[i:j] + (esc(put) if esc else put)
        i = k + 1
    return _fill(out, ctx, track), computed


def _binds(node):
    return bool(node["the"] or node["of"] or node["over"] or node["as"] or node.get("let") or node["capture"] or node["only"] or node["each"])


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
    part-identity check failed (F18).
    14 Oct (a4838): every press asks this of the lens it was painted by; the answer is kept by what it is made of."""
    key = (src, path, frozenset(roles) if roles is not None else None, style)
    if key not in _DEFPART:
        if len(_DEFPART) >= 256:
            _DEFPART.clear()
        _DEFPART[key] = _defpart_hash(src, path, roles, style)
    return _DEFPART[key]


_DEFPART = {}


def _defpart_hash(src, path, roles, style):
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
    if f in ("in", "before", "after"):
        return "place"          # 8 Oct: where a thing is, read as a field, is a read of its place
    if f in NAMES or f in SOURCE_FIELDS or f in ("value", "x", "y", "n", "count"):
        return None
    return f"prop:{f}"


def _rev_of(w, i):
    x = w.subjects.get(i) or w.nodes.get(i)
    return x["rev"] if x else None


def _inst(ctx, node, ictx):
    """The context for one instance of a repeat: the thing's own values, plus every frame named above, plus this
    part's own frame when it says `as`. Pike: a nested `of` used to lose the outer thing's fields."""
    ictx = dict(ictx)
    # Juniper, 7 Oct (a3470): a let named above a repeat was in scope inside it (the lens compiled) and read none
    # there, since an instance began from its thing alone. A let crosses into the repeat as a frame does.
    if ctx.get("_lets"):
        ictx["_lets"] = set(ctx["_lets"]) | set(ictx.get("_lets") or ())
        ictx["_values"] = dict(ctx.get("_values") or {}, **(ictx.get("_values") or {}))
        for name in ctx["_lets"]:
            ictx[name] = ctx.get(name)
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
    """Each call has a context of its own to change; it is made once while the world holds still (still)."""
    return dict(_once(w, ("ctx", nid, state), lambda: _make_ctx(w, nid, state)))


def _make_ctx(w, nid, state=None):
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
    import names
    place = {p: names.place_of(w, item, p)[0] or "" for p in ("in", "before", "after")} if item else {"in": "", "before": "", "after": ""}
    ctx = {"item": item, "id": n.get("subject") or nid, "title": s.get("title", n.get("title", "")), "text": s.get("text", ""),
           "kind": s.get("kind", n["type"]), "due": s.get("due") or "", "tags": " ".join(s.get("tags") or []),
           **place,          # 8 Oct (names.py): where a thing is, as fields: $item.in, $trip.before, $after
           "_tags": list(s.get("tags") or []),
           # F11: a surface's props live on the surface itself (a resident's corner carries status, want)
           # a1590: a person prop holds the person; a lens reads the name ($owner = $me holds for today's bearer)
           "_props": __import__("persons").shown_props(w, s.get("props") or (n.get("props") if n.get("type") == "surface" else None) or {})}
    if s.get("id"):
        if any(c.get("image") for c in s.get("comments", [])):
            ctx["_image_regions"] = __import__("image_comments").regions(s)
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


def reported_views(desk, lens):
    """The last report of each viewer whose painter showed `lens` (a lens title), as the house keeps them (reports.py,
    a4869: beside the world, never in it). -> ({viewer: report}, when the house that keeps them started or None)"""
    import reports
    session = getattr(desk, "_session", None)
    return ({a: v for a, v in reports.views(session).items() if v.get("lens") == lens.lower()}, reports.since(session))


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
    """A painter's box ("320x840@0,48 scroll sh=2400", "hidden") as words for a part's line. a5047: "@x,y" is where the
    part lies on the page, its left and top in CSS pixels as laid out (no scroll); a report from before it has none."""
    if b == "hidden":
        return "not drawn (folded or hidden)"
    m = re.match(r"(\d+)x(\d+)(?:@(-?\d+),(-?\d+))?", b or "")
    if not m:
        return f"box {b!r} (unreadable)"
    wd, ht = int(m.group(1)), int(m.group(2))
    kv = dict(re.findall(r"(\w+)=([\d/]+)", b))
    out = f"{wd}x{ht}px" + (f" at {m.group(3)},{m.group(4)}" if m.group(3) is not None else "")
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
        pg = v.get("page") or {}
        if pg.get("w") is not None:     # a5047: the page's own size goes with every report
            where += f" · page {pg['w']}x{pg['h']} at {pg.get('dpr', 1):g}x"
        pa = v.get("paint")
        lines.append(f"  ~ {a} {where} · painted world @{v.get('at')}"
                     + (" (behind)" if v.get("at", at) < at else "") + f" · reported {str(v.get('time', ''))[11:19]}"
                     + (f" ({pa['age']}) · " + {"current": "sizes are of the lens as it stands",
                                                "stale": f"painted before {pa['edit']}: sizes are of the old lens",
                                                "unknown": "its painter did not say which revision it painted"}[pa["state"]] if pa else ""))
    sized = [v for v in views.values() if v.get("paint")]
    if sized and all(v["paint"]["state"] == "stale" for v in sized):
        lines.append(f"  ! no viewer has painted this lens since {sized[0]['paint']['edit']}; the sizes below are of the old lens")
    if not views and scene.get("reports_since"):
        # a4869: reports do not outlive the house that received them; one from before it is never shown
        lines.append(f"  ~ no viewer has reported painting this lens since the house started ({_clock(scene['reports_since'])})")
    if not sized and part is not None:
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
            bits.append("peek" + (f" {n['peek']}" if type(n["peek"]) is int else ""))
        if n.get("picture"):
            bits.append("picture")
        if n.get("light"):
            bits.append("light " + str(len([x for x in str(n["light"]).split(chr(10)) if x.strip()])))
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
            bits.append(f"· {dv['name']} = {dv['result']} ({dv['expr']}" + (f"; {dv['inputs_s']}" if dv.get("inputs_s") else "") + ")"
                        + (f" (overlap: {dv['overlap']} answers held; the first was taken)" if dv.get("overlap") else ""))
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
            bits.append((f"· {n['n']} of {n['of']}" if n.get("of") else f"· {n['n']}") + (f" by {', '.join(n['by'])}" if n.get("by") else "") + (f" run {n['run']}" if n.get("run") else ""))
            if n["n"] == 0:
                bits.append("(empty)")         # Pike: every miss printed like an honest empty; now an empty says so
            if n.get("states"):
                bits.append("(" + ", ".join(n["states"]) + ")")
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


WORDS_BUDGET = 120        # a4179: lines `scene <lens> words` prints before it says how to ask for the rest


def to_words(scene, name, who, at, roots=None, part=None, start=1, whole=False):
    """a4179: a scene's words as one text -> (text, the nodes it showed whole). Each text part's words on their own
    lines, in the scene's order, whole (no 240-character cut), and nothing else: no keys, roles, reads or gestures.
    An absent part says nothing, as it paints nothing. Over WORDS_BUDGET lines it prints that many from `start` and
    says how to ask for the rest; `whole` prints all. A node is shown whole when every line under it printed, so a
    text cut by its clamp, or lying outside the lines printed, has not been seen."""
    lines, spans = [], []

    def walk(n):
        if n.get("absent"):
            return
        lo, ok = len(lines), True
        if n.get("text") and n["text"].strip():
            t = n["text"].split("\n")
            keep = t[: n["clamp"]] if n["clamp"] and "n" not in n else t
            lines.extend(keep)
            if len(keep) < len(t):
                lines.append(f"(… {len(t) - len(keep)} more line(s) of {n.get('item') or 'this part'} not shown: clamp {n['clamp']})")
                ok = False
        for k in n["kids"]:
            walk(k)
        spans.append((n, lo, len(lines), ok))

    for r in ([scene] if roots is None else roots):
        walk(r)
    total = len(lines)
    if start > max(total, 1):
        raise LensRefusal(f"scene {name} words has {total} line(s); from={start} is past the end")
    lo = start - 1
    hi = total if whole else min(total, lo + WORDS_BUDGET)
    head = (f"scene {name} words" + (f" · part {part}: {len(roots)} match" + ("es" if len(roots) != 1 else "") if roots is not None else "")
            + f" · for {who} · world @{at} · {total} line" + ("" if total == 1 else "s"))
    out = [head] + lines[lo:hi]
    if lo or hi < total:
        ask = f"scene {name}" + (f" {part}" if part else "") + " words"
        out.append(f"(lines {lo + 1}-{hi} of {total}: " + (f"{ask} from={hi + 1} for the next, " if hi < total else "")
                   + f"{ask} :3 for all. Only what is printed here counts as seen)")
    return "\n".join(out), [n for n, a, b, ok in spans if ok and a >= lo and b <= hi]


def find_lens(desk, name, at=None):
    """A lens by title, regardless of case, nearest first (verbs.nearest; 9 Oct, step 7): the room `at` (a placing
    lens's own, else where the line stands), the rooms around it, the house, then unplaced (a removed lens leaves its
    subject behind). Two at one level, or two in rooms neither nearer, are refused naming each (Pike: the first silently won)."""
    import kinds
    import verbs
    w = desk.world
    hits = [s for s in w.subjects.values() if kinds.is_lens(s) and s["title"].lower() == name.lower()]
    try:
        s = verbs.nearest(desk, hits, name, "lenses", at)
    except Refusal as e:
        raise LensRefusal(str(e))
    if s is not None:
        return s
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
        if node.get("picture"):
            paint["picture"] = True
        if node.get("light") and str(node["light"]).strip():
            paint["light"] = [x.strip() for x in str(node["light"]).split(chr(10)) if x.strip()]
            if node.get("image_regions"):
                paint["regions"] = node["image_regions"]
        if not node.get("plain") and not node.get("picture") and node.get("text"):
            rs = runs_of(node["text"], node.get("marks"))
            if node.get("marks"):
                paint["marks"] = True
            if rs:
                paint["runs"] = rs            # the text stays the joined words; the fence and the printer do not change
        ons = {a.get("on") for a in (node.get("acts") or [])}
        if "edit" in ons:
            mx = (node.get("lines") or [1, 1])[1]
            paint["commit"] = node.get("commit") or ("enter" if (not node.get("lines") or mx == 1) else "ctrl-enter")
            if node.get("commit_only"):
                paint["commit_only"] = True
        if "click" in ons:
            paint["semantic"] = {"role": "button", "label": node.get("text") or ""}
    if node.get("share") is not None:
        paint["share"] = node["share"]
    if node.get("peek") and not paint.get("absent"):
        paint["peek"] = node["peek"]
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


def split_words_arg(desk, arg):
    """a4179: `scene <lens> [<part path>] words [:3 | from=<n>]` -> (the line without those words, {"start", "whole"}),
    or (the line, None) when it does not ask for the words. A line that names a lens whole is that lens, so a lens
    titled `two words` is still itself."""
    toks = arg.split()
    opts = {"start": 1, "whole": False}
    k = len(toks)
    while k and (toks[k - 1] in (":3", ":full") or toks[k - 1].startswith("from=")):
        k -= 1
    if k < 2 or toks[k - 1] != "words":
        return arg, None
    try:
        find_lens(desk, arg.strip())
        return arg, None
    except LensRefusal:
        pass
    for t in toks[k:]:
        if t.startswith("from="):
            if not (t[5:].isdigit() and int(t[5:]) > 0):
                raise LensRefusal("from=<n> wants the number of the first line to print, from 1")
            opts["start"] = int(t[5:])
        else:
            opts["whole"] = True
    return " ".join(toks[: k - 1]), opts


def scene_for(desk, name, part=None, words=None):
    """-> (scene, text), through the staged pipeline in lens_ir (parse table, resolve, lower, evaluate through the read
    accessor, emit, print). scene["def"] is the requested definition, the effective transitive closure with each member's
    status (current | fallback), compiler and style identity, and a frame id. Gestures are honoured only on a frame
    whose whole closure is current; a fallback frame is for reading. The old single-pass evaluator (build, _compile,
    scene_for_old) was retired on 5 Oct, after the goldens were printed from this pipeline and frozen as plain worlds."""
    import lens_ir
    return lens_ir.scene_for(desk, name, part, words)
