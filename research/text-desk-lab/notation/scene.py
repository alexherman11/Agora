"""scene: the piece between the text world and the picture (v0, meant to be argued with).

A LENS is a short text that says how some part of the world is shown and what each gesture means. It lives in
the world as an ordinary note tagged `lens`, so it is edited with desk commands, undone, forked in a worktree,
and read by anyone. A lens is not code. The host that interprets it is small, fixed, and knows no app.

    world + lens  ->  SCENE  ->  text   (scene <lens>, what an agent reads)
                             ->  pixels (desk-shell/lens.html, a generic painter)

Both projections are printed from the same scene tree, so the screen and the text cannot disagree about what
is there, what it says, where it is, or what a gesture will do. That is the whole point.

Lens grammar v0. One line per part:  name : prop, prop, ...   Children are indented under their parent.
An unindented name defines a part; the first one is the root.

    column | row | free          how children are laid out (the same three words surfaces use)
    role <name>                  the look, by a role from the style file. A lens never names a colour or a size.
    text <template>              words, with $title $text $kind $due $tags $id $item $it $n, any field of a row
                                 source, and any prop of the thing ($place): the scene prints what it read and
                                 marks a missing prop (no place). Quote it to keep commas and hashes: text "a, b # c"
    clamp <N>                    on words: at most N lines (printed as ~, the painter clamps wrapped lines).
                                 on a repeat: at most N instances; both printers say how many are left
    of <selection>               repeat over the things a desk selection finds (kind:note,in:Canvas), over ids named
                                 one by one (of a04,s09: an appearance, or a subject wherever it appears; the scene
                                 prints each one's state: unplaced, gone), or over a row source: sections:<id>
                                 comments:<id> actors events worktrees (`rows <source>` prints them). An empty
                                 repeat prints (empty); it never looks like a full one
    over $tags                   repeat over a list field of the current thing; $it is each value
    each <part>                  what to instantiate for each repeated thing; $count is the count, on and under the repeat ($n still works on the repeat itself)
    at item                      take x,y,w,h from the thing's own appearance in the world (parent must be free)
    spread x <a> step <n|$prop> to <max>   place repeated parts along an axis (also y). $prop is a numeric prop of the
                                 lens note itself: do prop <lens> spacing=210. Computed presentation, never written back
    lens <name>                  place another lens here. A lens may not contain itself
    only when <selection>        the part exists only if the current thing (or anything) matches; the text prints the absence
    only when $x <op> value      a value test (= != < > <= >= has !has) on a field, prop, frame field or derive of this part, judged
                                 after its derives; prints its inputs; a missing value is absence (no x), not false
    the <selection>              exactly one thing becomes the current thing here; the text prints which (-> s31 (a32)),
                                 or (empty), or (ambiguous: a32, a50) with nothing built under it and gestures off
    as <name>                    name this part's thing as a frame; parts below read it as $name.title $name.start
                                 (a prop) and the scene prints `read name s31 start=...`. On a repeat, each instance
    derive <name> = <interpretation> <inputs>   a named calculation from a closed list (day-n <date> <n>,
                                 days-from <start> <end> (rows with $it.n $it.date, for over $name), weekday <date>,
                                 week-of <date>); it prints its inputs and result; no + and no if
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

LAYOUTS = ("column", "row", "free", "grid", "cells")      # pike-7 section 9: grid with tracks; cells is a grid row drawn as display: contents
PAINT_WORDS = ("tracks", "gap", "scroll", "fold", "fold_open", "fold_float", "fold_handle", "measure", "wrap", "lines", "share", "hint", "plain")   # pike-7 sections 6 and 9, lowered here; fold_open and fold_float are fold's modifiers
GESTURES = ("click", "edit", "drag", "menu")      # `drop` was admitted and never painted (Astra). A gesture exists when the painter can do it.
# Alex, 29 Sep ("native right click behavior"): `on menu "<label>" do ...` puts an entry in the part's own menu, which the
# painter opens on a right-click (or the menu key) anywhere on the part; a part with no entries keeps the browser's menu.
NAMES = ("title", "text", "kind", "due", "tags", "id", "item", "it", "n", "count")


class LensRefusal(Exception):
    pass


# ---- admission: what Astra's foundations audit (research/shared-visual-desk/round5-bridge) reproduced ----------
BUDGET = 1500          # scene nodes. A lens that needs more must say `clamp N` on its repeat and let the text say the rest.


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
    "messages": ("messages:<id>", ("item", "who", "said", "index")),
    "house": ("house[:<corner>]", ("resident", "corner", "doing", "turns", "since", "beat", "fresh", "room")),
    # what each resident wrote, its last turns, newest first (Alex, 29 Sep: to see their turns and text)
    "turns": ("turns[:<corner>]", ("resident", "corner", "turn", "at", "said", "acts")),
}
NAMES = NAMES + tuple(f for _, fs in SOURCES.values() for f in fs)
HOUSE_STATE = pathlib.Path(__file__).resolve().parent / "house-state"   # <world>/house.json, written by house.py


def turn_rows(desk, corner=None):
    """The replies the house kept for each resident (house.json `said`), newest first. `acts` counts the lines that
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
    out.sort(key=lambda r: r.pop("_t"), reverse=True)
    return out


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
    out = []
    for cid, r in sorted((st.get("residents") or {}).items()):
        if corner and cid != corner:
            continue
        last = r.get("last_turn")
        doing = (r.get("doing") or "?") if fresh == "live" else "house " + fresh.replace("stale", "stopped") + " ago"
        if fresh == "live" and doing == "resting" and r.get("rest_until"):     # a rest the resident timed itself
            until = float(r["rest_until"])
            fmt = "%H:%M" if until - time.time() < 86400 else "%a %H:%M"
            doing = "resting until " + time.strftime(fmt, time.localtime(until))
        room = rooms.room_of(desk.world, r.get("actor")) if r.get("actor") else None    # a678: where they are, a world fact
        out.append({"resident": r.get("actor") or "(no name yet)", "corner": cid, "doing": doing,
                    "turns": r.get("turns", 0), "since": time.strftime("%H:%M", time.localtime(last)) if last else "",
                    "beat": time.strftime("%H:%M:%S", time.localtime(st.get("beat") or 0)), "fresh": fresh,
                    "room": desk.world.nodes[room]["title"] if room else ""})
    return out


def rows(desk, source, session=None):
    """-> list of dicts, or None when `source` is not a row source (then it is an ordinary selection)."""
    w = desk.world
    head, _, arg = source.strip().partition(":")
    if head not in SOURCES or (head not in ("house", "turns") and (head in ("sections", "comments", "messages")) != bool(arg)):
        return None      # sections, comments and messages need an id; house and turns take one or none; the rest none
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
        for k, line in enumerate((l for l in s["text"].splitlines() if l.strip()), 1):
            m = w.SPEAKER.match(line)
            out.append({"item": nid, "who": m.group(0).rstrip(" \t:") if m else "", "said": line[m.end():] if m else line, "index": k})
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
    fields = SOURCES[source.partition(":")[0]][1]
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
    m = re.fullmatch(r'("[^"]+")?\s*(.*)', val.strip())
    mods = m.group(2).split() if m else ["?"]
    handle = None
    if "handle" in mods:
        k = mods.index("handle")
        handle = mods[k + 1] if k + 1 < len(mods) else None
        del mods[k:k + 2]
        if not handle or not re.fullmatch(r"[\w.-]+", handle):
            raise LensRefusal(f'line {n}: `fold ... handle <role>`: the role the handle wears; got {p!r}')
        if env["roles"] is not None and handle not in env["roles"]:
            raise LensRefusal(f"line {n}: no role {handle!r} for the fold's handle in {'style ' + env['style'] if env.get('style') else 'calm.style'}. Roles: {' '.join(sorted(env['roles']))}")
    if any(x not in ("open", "float") for x in mods) or len(set(mods)) != len(mods):
        raise LensRefusal(f'line {n}: `fold ["<label for the handle>"] [open] [float] [handle <role>]`; got {p!r}')
    node["fold"] = m.group(1).strip('"') if m.group(1) else True
    node["fold_open"], node["fold_float"], node["fold_handle"] = "open" in mods, "float" in mods, handle


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


_RUNS = re.compile(r"```[^\n]*\n(.*?)```|`([^`\n]+)`", re.S)


def runs_of(text):
    """Juniper a559: code spans and fences become runs at print, from this closed grammar, with no world effect; the
    words stay the part's source, so the printer's text and the fence are unchanged. -> [{text, role?, block?}] or None."""
    out, at = [], 0
    for m in _RUNS.finditer(text or ""):
        if m.start() > at:
            out.append({"text": text[at:m.start()]})
        out.append({"text": m.group(1), "role": "code", "block": True} if m.group(1) is not None else {"text": m.group(2), "role": "code"})
        at = m.end()
    if not out:
        return None
    if at < len(text):
        out.append({"text": text[at:]})
    return out


def _w_share(node, p, val, n, env):
    if not re.fullmatch(r"\d+(\.\d+)?", val) or float(val) <= 0:
        raise LensRefusal(f"line {n}: `share <weight>` (this child's share of its column or row); got {p!r}")
    node["share"] = float(val) if "." in val else int(val)


def _w_carry(node, p, val, n, env):
    node["carry"] = True          # Pike a361/c368: carry on the thing, `on drop <part>` on the receiver


def _w_role(node, p, val, n, env):
    if not re.fullmatch(r"[\w.-]+", val):
        raise LensRefusal(f"line {n}: `role <name>`; got {p!r}")
    if env["roles"] is not None and val not in env["roles"]:
        raise LensRefusal(f"line {n}: no role {val!r} in {'style ' + env['style'] if env.get('style') else 'calm.style'}. Roles: {' '.join(sorted(env['roles']))}")
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
    if not val.isdigit():
        raise LensRefusal(f"line {n}: `clamp <number>`; got {p!r}")
    node["clamp"] = int(val)


def _w_of(node, p, val, n, env):
    if not val:
        raise LensRefusal(f"line {n}: `of <selection> [as <frame>]`; got {p!r}")
    node["of"], _, asname = val.partition(" as ")          # `of parts:$trip.item as stop`
    if asname:
        node["as"] = asname.strip()


def _w_over(node, p, val, n, env):
    if not re.fullmatch(r"\$\w+", val):
        raise LensRefusal(f"line {n}: `over $<rows> [as <frame>]`; got {p!r}")
    node["over"] = val[1:]


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


def _w_only(node, p, val, n, env):
    if not (val.startswith("when ") and val[5:].strip()):
        raise LensRefusal(f"line {n}: `only when <selection>` or `only when $x <op> <value>`; got {p!r}")
    node["only"] = val[5:].strip()      # Wren, Flint: the desk's own selection decides; a value test is judged after derives


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
    if cmd.split(" ")[0] not in ("do", "look", "read", "examine", "find", "undo", "run", "scene", "rows", "worktree", "open", "fold", "go"):
        cmd = "do " + cmd
    node["on"].append({"on": g, "line": cmd, **({"part": drop_part} if drop_part else {}), **({"label": label} if label else {})})


# word -> (shape as a reader sees it, setter). A layout word is its own name.
WORDS = {
    **{lay: (lay, _w_layout) for lay in LAYOUTS},
    "grid": ("grid <tracks: 1 3 3 1 | 1fr fit 2fr>", _w_grid),
    "gap": ("gap | gap x2 | gap /2", _w_gap),
    "scroll": ("scroll none|scroll|end", _w_scroll),
    "fold": ('fold ["<handle label>"] [open] [float] [handle <role>]', _w_fold),
    "measure": ("measure <n>ch", _w_measure),
    "verbatim": ("verbatim", _w_verbatim),
    "lines": ("lines <min>..<max>", _w_lines),
    "share": ("share <weight>", _w_share),
    "hint": ('hint "..."', _w_hint),
    "plain": ("plain", _w_plain),
    "carry": ("carry", _w_carry),
    "role": ("role <name>", _w_role),
    "text": ('text "..."', _w_text),
    "clamp": ("clamp <n>", _w_clamp),
    "the": ("the <selection> [as <frame>]", _w_the),
    "of": ("of <selection> [as <frame>]", _w_of),
    "over": ("over $<rows> [as <frame>]", _w_over),
    "as": ("as <frame>", _w_as),
    "each": ("each <part>", _w_each),
    "at": ("at item", _w_at),
    "only": ("only when <selection | $x <op> value>", _w_only),
    "derive": ("derive <name> = <interpretation> <inputs>", _w_derive),
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
    if node["as"] and (node["as"] in NAMES or node["as"] in ("value", "x", "y")):
        raise LensRefusal(f"line {n}: `as {node['as']}` would shadow a built-in name; choose another frame name")
    if node["as"] and not (node["the"] or node["of"] or node["over"]):
        raise LensRefusal(f"line {n}: `as {node['as']}` names the thing chosen here, so this part needs `the`, `of` or `over`")
    if node["capture"] and not node["the"]:
        raise LensRefusal(f"line {n}: `capture` holds a field of the thing chosen by `the`; this part has no `the`")


def parse(src, roles=None, style=None):
    """-> (root_name, parts) where parts[name] = node {name, props, kids}. `roles`: the lens's style's roles (F7)."""
    parts, stack, root = {}, [], None
    env = {"roles": roles if roles is not None else _roles(), "style": style}
    for n, raw in enumerate(src.splitlines(), 1):
        line = _outside_quotes(raw, " # ")[0].rstrip()
        if not line.strip() or line.strip().startswith("#") or line.strip().startswith("lens "):
            continue
        indent = len(line) - len(line.lstrip())
        name, colon, rest = line.strip().partition(" : ")
        if not colon or not re.fullmatch(r"[\w-]+", name):
            raise LensRefusal(f"line {n}: a part is `name : prop, prop`; got {line.strip()!r}")
        node = {"name": name, "kids": [], "line": n, "layout": None, "role": None, "text": None, "clamp": None,
                "of": None, "over": None, "each": None, "at": None, "on": [], "lens": None, "only": None, "props": [],
                "the": None, "as": None, "derive": [], "capture": {}, "src": line.strip(), "carry": False,
                "tracks": None, "gap": None, "scroll": None, "fold": False, "measure": None, "wrap": None, "lines": None, "share": None, "hint": None, "plain": False}
        for p in [p.strip() for p in _outside_quotes(rest, ", ") if p.strip()]:
            word, _, val = p.partition(" ")
            row = WORDS.get(word)
            if row is None:
                raise LensRefusal(f"line {n}: a lens cannot say {p!r}. It can say: {vocabulary()}")
            row[1](node, p, val, n, env)
        _check_part(node, n)
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
            ("lens", node["lens"] or "")]
    srcs += [("derive", x) for _, _, ins in node["derive"] for x in ins]
    srcs += [("on", a["line"]) for a in node["on"]]
    for word, text in srcs:
        for a, b in _VAR.findall(text):
            out.append((word, a, b))
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
        scopes[id(node)] = {"frames": frames, "lets": lets}
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
    if name in ("title", "text", "kind", "due", "tags", "id", "item", "n", "count"):
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
# Pike (round six, `if`): a structural test on a value. `only when $wd = Mon`, `only when $beds > 5`, `only when $a.due < $today`.
# Alex, 29 Sep ("messages to me should be pleasantly highlighted"): `has` and `!has` ask whether the words contain the
# value, ignoring case: `only when $said has @$me`. A value with a $name in it is filled, as a bare $name is.
_VALUE_TEST = re.compile(r"(\$[\w.-]+)\s*(=|!=|<=|>=|<|>|!?has(?=\s))\s*(\$[\w.-]+|\"[^\"]*\"|\S+)")


def _compare(left, op, right):
    try:
        a, b = float(left), float(right)
    except (TypeError, ValueError):
        a, b = str(left), str(right)
    if op in ("has", "!has"):
        return (str(right).lower() in str(left).lower()) == (op == "has")
    return {"=": a == b, "!=": a != b, "<": a < b, ">": a > b, "<=": a <= b, ">=": a >= b}[op]


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


def _binds(node):
    return bool(node["the"] or node["of"] or node["over"] or node["as"] or node["derive"] or node["capture"] or node["only"] or node["each"])


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
           "_props": dict(s.get("props") or (n.get("props") if n.get("type") == "surface" else None) or {})}
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


def build(desk, src, stack=(), count=None, props=None, closure=None):
    props = props or {}
    root, parts = parse(src, roles=style_roles(desk, props.get("style")), style=props.get("style"))   # F7, F18
    resolve(root, parts)          # stage 2: names are judged before any part is evaluated
    w = desk.world

    def spread_of(node, index, kid):
        sp, item = node.get("spread"), w.nodes.get(kid.get("item") or "")
        if not sp:
            return
        if node["layout"] != "free":
            raise LensRefusal(f"line {node['line']}: spread places parts by position, which only a `free` part can honour")
        xy = {}
        for axis, (start, step, top) in sp.items():
            if step.startswith("$"):
                if step[1:] not in props or not str(props[step[1:]]).lstrip("-").isdigit():
                    raise LensRefusal(f"line {node['line']}: spread step {step}: this lens has no numeric prop {step[1:]!r}. Set it: do prop <this lens> {step[1:]}=150")
                step = props[step[1:]]
            xy[axis] = max(0, min(top, start + index * int(step)))
        kid["box"] = [xy.get("x", 0), xy.get("y", 0), item["w"] if item else 200, item["h"] if item else 80]
        kid["placed"] = "spread"          # computed presentation, not the thing's durable position: no drag, nothing written back
    count = count if count is not None else [0]

    def make(node, ctx, key, parent_layout="free", chain=()):
        chain = chain + (node,)
        if node["at"] == "item" and parent_layout != "free":
            raise LensRefusal(f"line {node['line']}: `at item` places a part by its world position, which only a `free` parent can honour; "
                              f"its parent is {parent_layout or 'unlaid'}. Make the parent free, or drop `at item`")
        vtest = _VALUE_TEST.fullmatch(node["only"].strip()) if node["only"] else None
        if node["only"] and not vtest:
            sel = desk._parse_selection(_fill(node["only"], ctx))
            ids = sel[0] if sel else []
            if not ((ctx.get("item") in ids) if ctx.get("item") else bool(ids)):
                # the text prints the absence; it does not pretend the part was never written
                return {"part": node["name"], "key": key, "role": None, "layout": None, "item": ctx.get("item"), "box": None,
                        "text": None, "clamp": None, "acts": [], "kids": [], "absent": node["only"]}
        ctx = dict(ctx)
        frames = dict(ctx.get("_frames") or {})
        ctx["_frames"] = frames
        track = {"frames": set(), "reads": {}, "missing": set(), "bad": set()}
        the_state = "live"
        if node["the"]:
            # Pike W2: exactly one. Empty and ambiguous are states the scene prints; nothing is built under them.
            sel_text = _fill(node["the"], ctx, track)
            named = _named(w, sel_text)
            if named is not None:
                ids = [i for i, st in named if st == "live"] or [i for i, st in named if st == "unplaced"]
            else:
                sel = desk._parse_selection(sel_text)
                ids = list(sel[0]) if sel else []
            if len(ids) == 1:
                tc = _ctx_for(w, ids[0])
                for k, v in node["capture"].items():
                    # Pike W7: a captured value is used instead of the live one, and the scene says whether they still agree
                    live = tc.get(k) if (k in tc and not k.startswith("_")) else (tc.get("_props") or {}).get(k)
                    tc.setdefault("_captured", []).append((k, v, live))
                    tc.setdefault("_captured_fields", set()).add(k)      # Juniper: rows printed `read trip start=<captured>`, a false provenance
                    if k in tc and not k.startswith("_"):
                        tc[k] = v
                    else:
                        tc["_props"] = dict(tc.get("_props") or {}, **{k: v})
                ctx.update({k: v for k, v in tc.items() if k != "_frames"})
                if node["as"]:
                    frames[node["as"]] = tc
                the_state = f"-> {tc['id']}" + (f" ({ids[0]})" if ids[0] != tc["id"] else "")
            else:
                the_state = "empty" if not ids else "ambiguous: " + ", ".join(ids)
        out = {"part": node["name"], "key": key, "role": node["role"], "layout": node["layout"], "item": ctx.get("item"),
               "box": None, "text": None, "clamp": node["clamp"], "acts": [], "kids": []}
        out.update({k: node[k] for k in PAINT_WORDS if node.get(k) not in (None, False)})
        if isinstance(out.get("fold"), str) and "$" in out["fold"]:
            out["fold"] = _fill(out["fold"], {**(ctx.get("_props") or {}), **ctx}, track)      # a fold's label is words, like text
        if node["the"]:
            out["the"] = (_fill(node["the"], ctx), the_state)
        if node["as"]:
            out["as"] = node["as"]
        if ctx.get("_captured") and node["the"]:
            out["captured"] = [{"field": k, "value": v, "now": live, "same": (str(live) == str(v))} for k, v, live in ctx["_captured"]]
        if the_state not in ("live",) and not the_state.startswith("->"):
            return out          # empty or ambiguous: printed, gestures off, nothing under it
        for dname, interp, ins in node["derive"]:
            dctx = dict(ctx.get("_props") or {})
            dctx.update(ctx)                                     # Juniper: `day-n $trip.start $tripday` could not read the thing's own prop
            vals = [_fill(x, dctx, track) if x.startswith("$") else x for x in ins]
            res, err = INTERPS[interp][1](vals)
            out.setdefault("derived", []).append({"name": dname, "interp": interp, "inputs": vals,
                                                  "result": (f"{len(res)} rows" if isinstance(res, list) else res), "error": err})
            if isinstance(res, list):
                ctx["_" + dname] = res
            else:
                ctx[dname] = res or ""
        if vtest:
            # Sable probe 5, Juniper A5: `only when $wd=Mon` was accepted as a selection and printed a wrong reason on every
            # day. It is a value test, judged after this part's derives so its own `derive wd` is visible; it prints its
            # inputs, and a missing value is absence, not false (Sable's R6 condition).
            ref, op, rhs = vtest.group(1), vtest.group(2), vtest.group(3).strip('"')
            vctx = dict(ctx.get("_props") or {})
            vctx.update(ctx)
            left = _fill(ref, vctx, track)
            right = _fill(rhs, vctx, track) if "$" in rhs else rhs
            gone = [x for x, v in ((ref, left), (rhs, right)) if x.startswith("$") and (v == x or v == "")]
            if gone or not _compare(left, op, right):
                out.update(text=None, acts=[], kids=[], absent=node["only"],
                           why=(f"no {gone[0].lstrip('$')}" if gone else f"{ref} is {left}, not {op} {right}"))
                return out
            out["test"] = f"{ref} is {left} {op} {right}"
        if node["at"] == "item" and ctx.get("item") in w.nodes:
            n = w.nodes[ctx["item"]]
            out["box"] = [n["x"], n["y"], n["w"], n["h"]]
            # Lark: "can he see this?" The world already knows (offscreen-part, spills-parent, 43% hidden by f52); the scene threw it away.
            out["facts"] = [f for f in w.relations(ctx["item"]) if f != "clear"]
        if node["text"] is not None:
            pv = dict(ctx.get("_props") or {})
            missing = [p for p in node["props"] if p not in pv and p not in ctx]
            # Juniper: a prop named n (or any built-in name) crashed the compiler here. Built-ins win; the prop is still readable as $it or a frame.
            fill_ctx = {p: "" for p in missing}
            fill_ctx.update(pv)
            fill_ctx.update({k: v for k, v in ctx.items() if k != "n"} if node["each"] else ctx)
            out["text"] = _fill(node["text"], fill_ctx, track)   # a repeat words its own count
            if node["props"]:
                out["read"] = {p: pv.get(p) for p in node["props"] if p in pv}      # what the lens read from the thing
            if missing:
                out["missing"] = missing                                             # printed (no place); the painter shows nothing there
        if ctx.get("_state") and ctx["_state"] != "live":
            out["state"] = ctx["_state"]
        safe = {k: (_cmd_value(v) if isinstance(v, str) else v) for k, v in ctx.items()}
        out["id"] = ctx.get("id")
        # a thing that is gone or unplaced has no appearance to act on: no gesture is offered, and the text says why
        safe["_frames"] = {k: {kk: (_cmd_value(vv) if isinstance(vv, str) else vv) for kk, vv in f.items()} for k, f in frames.items()}
        acts = [] if (node["on"] and ctx.get("_state") in ("gone", "unplaced")) else [
            {"on": a["on"], "line": _fill(a["line"], safe, track), **{k: a[k] for k in ("part", "label") if a.get(k)}} for a in node["on"]]
        if node["carry"]:
            if not ctx.get("item"):
                raise LensRefusal(f"line {node['line']}: `carry` needs a world thing behind this part, and here there is none (a derived row or the root)")
            acts.append({"on": "carry"})          # no line: the drop's receiver says what happens
        out["acts"] = acts
        if track["bad"]:
            raise LensRefusal(f"line {node['line']}: ${sorted(track['bad'])[0]}.field: no part above this one is named `as {sorted(track['bad'])[0]}`")
        if track["reads"]:
            out["freads"] = {k: v for k, v in track["reads"].items()}
            out["frames"] = {f: frames[f].get("id") for f in track["frames"] if f in frames}
        if track["missing"]:
            out["missing"] = sorted(set(out.get("missing") or []) | {f"{m} on {frames[m.split('.')[0]].get('id')}" for m in track["missing"]})
        if out["acts"]:
            # Pike F1: what a gesture was built from. The item's subject and every frame its words or derives read.
            # Pike a308: at the grain of the aspect, so a retitle does not refuse a gesture that only read a prop.
            reads = {}
            sj = (w.nodes.get(ctx.get("item") or "") or {}).get("subject")
            fields = {}
            for f in track.get("own", ()):
                a = _aspect_of_field(f)
                if a and sj:
                    fields.setdefault(sj, set()).add(a)
            for k in track["reads"]:
                fr, _, fld = k.partition(".")
                fid = frames.get(fr, {}).get("id")
                a = _aspect_of_field(fld)
                if fid and a:
                    fields.setdefault(fid, set()).add(a)
            for i in [sj] + [frames[f].get("id") for f in track["frames"] if f in frames]:
                if i and _rev_of(w, i) is not None:
                    reads[i] = _rev_of(w, i)
            out["reads"] = [[i, r, sorted(fields.get(i) or [])] for i, r in sorted(reads.items())]
            out["defpart"] = {"path": "/".join(n["name"] for n in chain), "hash": _chain_hash(chain)}
        if ctx.get("item") in w.nodes and out["acts"]:
            out["rev"] = w.nodes[ctx["item"]]["rev"]
            # Astra (bridge c31, c42): fields they had to join server-side, now stated. Coordinates are px in the parent.
            nd = w.nodes[ctx["item"]]
            sj = w.subjects.get(nd.get("subject") or "")
            out["bind"] = {"subject": nd.get("subject"), "subject_rev": sj["rev"] if sj else None, "parent": nd["parent"],
                           "parent_rev": w.nodes[nd["parent"]]["rev"] if nd["parent"] in w.nodes else None, "units": "px in parent"}      # Astra: a gesture acts on the generation that was observed, not on a fresh look
        count[0] += 1
        if count[0] > BUDGET:
            raise LensRefusal(f"this lens makes more than {BUDGET} scene nodes. Put `clamp N` on the repeat (line {node['line']}); the text will say how many are left")
        if node["each"]:
            each = parts[node["each"]]
            if node["of"]:
                sel_text = _fill(node["of"], ctx)
                out["of"] = sel_text                  # Pike: the text printed the selection unfilled; print what was asked
                rs = rows(desk, sel_text)
                keep = node["clamp"] or 10 ** 9       # Flint: clamp N on a repeat; 305 things put 305 nodes in both printers
                total = len(rs) if rs is not None else None
                cnt = min(total, keep) if total is not None else None
                for k, r in enumerate((rs or [])[:keep]):
                    # Pike: sections and tags were keyed by position, so an insert retargeted every draft below it. Key by what it is.
                    okey = r.get("cid") or r.get("eid") or r.get("name") or (_slug(r["heading"]) if "heading" in r else k)
                    out["kids"].append(make(each, _inst(ctx, node, {**ctx, "count": cnt, **r}), f"{key}/{okey}", node["layout"], chain))
                named = _named(w, sel_text) if rs is None else None
                if named is not None:
                    total = len(named)
                    for i, st in named[:keep]:
                        out["kids"].append(make(each, _inst(ctx, node, dict(_ctx_for(w, i, st), count=min(total, keep))), f"{key}/{i}", node["layout"], chain))
                    out["states"] = [f"{i} {st}" for i, st in named if st != "live"]
                else:
                    sel = desk._parse_selection(sel_text) if rs is None else None
                    ids = sel[0] if sel else []
                    total = len(ids) if total is None else total
                    for i in ids[:keep]:
                        out["kids"].append(make(each, _inst(ctx, node, dict(_ctx_for(w, i), count=min(total, keep))), f"{key}/{i}", node["layout"], chain))
                # Juniper (round six, past Sable's probes): tagging a thing outside the printed reads moved the scene, because
                # the repeat had read "the set matching tag:day" and recorded nothing. A membership read is a read.
                got = [k["item"] or k["key"] for k in out["kids"]]
                out["members"] = {"of": sel_text, "n": total, "ids": got, "at": len(w.events)}
                if total > keep:
                    out["cut"] = total - keep
                    out["kids"].append({"part": "cut", "key": f"{key}/cut", "role": "cut", "layout": None, "item": None, "box": None,
                                        "text": f"{total - keep} more not shown (clamp {keep}); find {_fill(node['of'], ctx)} lists all {total}",
                                        "clamp": None, "acts": [], "kids": []})
            else:
                rows_over = ctx.get("_" + node["over"], [])
                for k, v in enumerate(rows_over):
                    if isinstance(v, dict):         # rows from a derive (days-from): $it.n $it.date, keyed by n
                        ictx = _inst(ctx, node, dict(ctx, it=str(v.get("date", v.get("n", ""))), count=len(rows_over)))
                        ictx["_frames"] = dict(ictx["_frames"], it=v)
                        out["kids"].append(make(each, ictx, f"{key}/{_slug(str(v.get('n', k)))}", node["layout"], chain))
                    else:
                        out["kids"].append(make(each, _inst(ctx, node, dict(ctx, it=v, count=len(rows_over))), f"{key}/{_slug(str(v))}", node["layout"], chain))
            # the same thing twice in one repeat gave two identical keys (Pike); an occurrence is (thing, ordinal here)
            seen_keys = {}
            for kid in out["kids"]:
                c = seen_keys.get(kid["key"], 0) + 1
                seen_keys[kid["key"]] = c
                if c > 1:
                    old = kid["key"]
                    kid["key"] = f"{old}#{c}"
                    _reprefix(kid, old, kid["key"])
            out["n"] = len(out["kids"]) - (1 if out.get("cut") else 0)
            for k, kid in enumerate(out["kids"][:out["n"]]):
                spread_of(node, k, kid)
            if out["text"] is not None:                         # Flint bug 4: the count existed and could not be put into words
                out["text"] = out["text"].replace("$n", str(out["n"]))
        if node["lens"]:
            inner = _fill(node["lens"], ctx)
            if inner.lower() in stack:
                raise LensRefusal(f"line {node['line']}: lens {inner} contains itself ({' -> '.join(stack + (inner.lower(),))})")
            sub = _compile(desk, find_lens(desk, inner), stack + (inner.lower(),), count, closure if closure is not None else [])
            sub["key"] = f"{key}/lens:{inner}"
            _rekey(sub, sub["key"])
            out["kids"].append(sub)
            out["lens"] = inner
        for kid in node["kids"]:
            out["kids"].append(make(kid, dict(ctx, n=out.get("n", ctx.get("n", "")), count=out.get("n", ctx.get("count", ""))), f"{key}/{kid['name']}", node["layout"], chain))
        return out

    return make(parts[root], {}, root)


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


def to_text(scene, name, who, at):
    lines = [f"scene {name} · for {who} · world @{at}"]
    views = scene.get("views") or {}
    for a, v in views.items():
        vp = v.get("viewport") or {}
        # Pike a561: since 0477e78 a viewer publishes attention (viewport, scroll) only when they allow it; say so
        where = (f"is looking: {vp.get('w')}x{vp.get('h')} at scroll {vp.get('sx')},{vp.get('sy')}" if vp.get("w") is not None
                 else "has this open; attention not shared")
        lines.append(f"  ~ {a} {where} · painted world @{v.get('at')}"
                     + (" (behind)" if v.get("at", at) < at else "") + f" · reported {str(v.get('time', ''))[11:19]}")

    def rv(v, top=120):
        """A read value on one line: newlines become ` / ` as in a body, and a long one is cut and says so (Juniper,
        juniper-7: a chat's text in a read put lines at column zero and every indentation reader mis-parsed the print)."""
        t = " / ".join(str(v).splitlines()) if isinstance(v, str) else v
        return (t[:top] + f" (={top} of {len(t)} chars)") if isinstance(t, str) and len(t) > top else t

    def pr(n, d, pkey=None):
        bits = [n["part"]]
        if n.get("absent"):
            why = n.get("why") or f"not {n['absent']}"
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
            bits.append(f"[{n['role']}]")
        if n["layout"]:
            bits.append(n["layout"] + (" " + " ".join(n["tracks"]) if n.get("tracks") else ""))
        for wd in ("gap", "scroll", "measure", "share"):
            if n.get(wd) is not None:
                bits.append(f"{wd} {n[wd]}")
        if n.get("fold"):
            bits.append(("unfolded" if n.get("fold_open") else "folded") + (f' "{n["fold"]}"' if isinstance(n["fold"], str) else "")
                        + (" float" if n.get("fold_float") else "") + (f" handle {n['fold_handle']}" if n.get("fold_handle") else ""))
        if n.get("wrap") == "verbatim":
            bits.append("verbatim")
        if n.get("lines"):
            bits.append(f"lines {n['lines'][0]}..{n['lines'][1] if n['lines'][1] is not None else ''}")
        if n.get("hint"):
            bits.append(f'hint "{n["hint"]}"')
        if n.get("plain"):
            bits.append("plain")
        elif n.get("text") and runs_of(n["text"]):
            bits.append(f"runs {sum(1 for r in runs_of(n['text']) if r.get('role'))} code")
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
            bits.append(f"· {dv['name']} = {dv['interp']}({', '.join(dv['inputs'])}) = {dv['result']}" if not dv["error"] else f"· {dv['name']}: (uninterpretable: {dv['error']})")
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
            bits.append(f"· {n['n']} of {n['of']}" if n.get("of") else f"· {n['n']}")
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
        # Juniper (key form, 25 Sep), Pike's C4 gap: the occurrence key was painted as data-key and never printed. The
        # segment is the key below the parent's; a fixed part's segment is its own name and prints nothing.
        seg = n["key"][len(pkey) + 1:] if pkey and n["key"].startswith(pkey + "/") else n["key"]
        if seg != n["part"]:
            bits.append(f"· key {seg}")
        lines.append("  " * d + " ".join(bits))
        for k in n["kids"]:
            pr(k, d + 1, n["key"])

    pr(scene, 1)
    return "\n".join(lines)


def find_lens(desk, name):
    w = desk.world
    hits = [s for s in w.subjects.values() if "lens" in (s.get("tags") or []) and s["title"].lower() == name.lower()]
    if len(hits) > 1:        # a removed lens leaves its subject behind, unplaced; the placed one is the one meant
        placed = [s for s in hits if w.appearances_of(s["id"])]
        hits = placed if len(placed) == 1 else hits
    if len(hits) > 1:        # Pike: two lenses with one title, the first silently won
        raise LensRefusal(f"{len(hits)} lenses are titled {name!r} ({', '.join(s['id'] for s in hits)}); retitle one so the name means one thing")
    if hits:
        return hits[0]
    have = [s["title"] for s in w.subjects.values() if "lens" in (s.get("tags") or [])]
    raise LensRefusal(f"no lens {name!r}. A lens is a note tagged lens whose text is the description. Lenses here: {', '.join(have) or 'none'}")


def _compile(desk, s, stack, count, closure):
    """One lens to a scene, recording in `closure` exactly which definition was used. A lens that does not compile is
    shown in its last version that did (Astra: also when it is an INNER lens), and the closure says so."""
    good = getattr(desk, "_lens_good", None)
    if good is None:
        good = desk._lens_good = {}
    entry = {"lens": s["title"], "id": s["id"], "rev": s["rev"], "status": "current"}
    closure.append(entry)
    mark = len(closure)

    def stamp(node):
        dp = node.get("defpart")
        if dp is not None and "lens" not in dp:
            dp["lens"], dp["id"] = s["title"], s["id"]
        for k in node.get("kids") or []:
            stamp(k)
    try:
        sc = build(desk, s["text"], stack, count, props=s.get("props") or {}, closure=closure)
        stamp(sc)
        good[s["id"]] = {"text": s["text"], "rev": s["rev"]}
        return sc
    except LensRefusal as e:
        g = good.get(s["id"])
        g = {"text": g, "rev": None} if isinstance(g, str) else g
        if not g:
            raise
        del closure[mark:]
        entry.update(status="fallback", shown_rev=g["rev"], refusal=str(e))
        sc = build(desk, g["text"], stack, count, props=s.get("props") or {}, closure=closure)
        stamp(sc)
        sc["broken"] = f"lens {s['title']}: {e}"
        return sc


# ---------------------------------------------------------------------------------------------------------------------
# Stage 6, emission. Pike's node contract (pike-7 section 6): every node the painter receives is {key, paint, acts, fence,
# kids}. `paint` is exactly what is drawn, and the painter's signature is paint plus the acts' shapes plus the kids' keys,
# so an unrelated event no longer remakes an element. `fence` is opaque to the painter: sent back with a gesture, never
# drawn, never compared. Provenance (the, derived, test, read, freads, frames, captured, members, states, missing, of,
# cut) stays on the node for the printer and need not travel to the painter.
# ---------------------------------------------------------------------------------------------------------------------
PROVENANCE = ("the", "derived", "test", "read", "freads", "frames", "captured", "members", "states", "missing", "of", "cut", "n", "as", "facts", "views")


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
            paint["semantic"] = {"role": "group", "expanded": bool(node.get("fold_open"))}
    elif paint["kind"] == "text" and not paint.get("absent"):
        if node.get("wrap"):
            paint["wrap"] = node["wrap"]
        if node.get("lines"):
            paint["lines"] = node["lines"]
        if node.get("hint"):
            paint["hint"] = node["hint"]
        if not node.get("plain") and node.get("text"):
            rs = runs_of(node["text"])
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


def scene_for(desk, name):
    """-> (scene, text), through the staged pipeline in lens_ir (parse table, resolve, lower, evaluate through the read
    accessor, emit, print). scene["def"] is the requested definition, the effective transitive closure with each member's
    status (current | fallback), compiler and style identity, and a frame id. Gestures are honoured only on a frame
    whose whole closure is current; a fallback frame is for reading. The old evaluator below (build) stays for one
    stage as the reference the goldens were made with; Juniper's check judged the switch at 82 same."""
    import lens_ir
    return lens_ir.scene_for(desk, name)


def scene_for_old(desk, name):
    s = find_lens(desk, name)
    closure = []
    sc = _compile(desk, s, (s["title"].lower(),), [0], closure)
    emit(sc)                      # stage 6: the painter's contract on every node
    at = len(desk.world.events)
    fallen = [c for c in closure if c["status"] == "fallback"]
    sc["def"] = dict(lens=s["title"], id=s["id"], rev=s["rev"], status="fallback" if fallen else "current", closure=closure,
                     frame=".".join(f"{c['id']}r{c['rev']}" for c in closure), **_identity())      # Pike report 1, item 4: the event count made every event remake the root; observed.at carries it
    # Iris, Lark: painters report back what only they know; per viewer, printed as ~, never world facts.
    sc["views"] = {a: v for a, v in (getattr(desk, "_views", None) or {}).items() if v.get("lens") == s["title"].lower()}
    text = to_text(sc, s["title"], desk.world.me, at)
    if fallen:
        head = "".join(f"! lens {c['lens']} no longer compiles: {c['refusal']}\n" for c in fallen)
        text = head + "! showing the last version that did; gestures are off until it compiles. Fix it with rewrite, or undo.\n" + text
    return sc, text
