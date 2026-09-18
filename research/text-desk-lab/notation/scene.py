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
    text <template>              words, with $title $text $kind $due $tags $id $item $it $n
    clamp <N>                    at most N lines of that text
    of <selection>               repeat over the things a desk selection finds (kind:note,in:Canvas)
    over $tags                   repeat over a list field of the current thing; $it is each value
    each <part>                  what to instantiate for each repeated thing
    at item                      take x,y,w,h from the thing's own appearance in the world
    on <gesture> do <command>    click | edit | drag | drop. The command is a desk command line; the painter
                                 fills $x $y (drag), $value (edit), $other (drop) at the moment of the gesture.

Anything else is refused with the line number. There is no escape to raw HTML, CSS or script in v0, on purpose:
the pressure that builds against that wall is the research result.
"""

import pathlib
import re

LAYOUTS = ("column", "row", "free")
GESTURES = ("click", "edit", "drag")      # `drop` was admitted and never painted (Astra). A gesture exists when the painter can do it.
NAMES = ("title", "text", "kind", "due", "tags", "id", "item", "it", "n")


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
}
NAMES = NAMES + tuple(f for _, fs in SOURCES.values() for f in fs)


def rows(desk, source, session=None):
    """-> list of dicts, or None when `source` is not a row source (then it is an ordinary selection)."""
    w = desk.world
    head, _, arg = source.strip().partition(":")
    if head not in SOURCES or (head in ("sections", "comments")) != bool(arg):
        return None
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


def parse(src):
    """-> (root_name, parts) where parts[name] = node {name, props, kids}"""
    parts, stack, root = {}, [], None
    known_roles = _roles()
    for n, raw in enumerate(src.splitlines(), 1):
        line = _outside_quotes(raw, " # ")[0].rstrip()
        if not line.strip() or line.strip().startswith("#") or line.strip().startswith("lens "):
            continue
        indent = len(line) - len(line.lstrip())
        name, colon, rest = line.strip().partition(" : ")
        if not colon or not re.fullmatch(r"[\w-]+", name):
            raise LensRefusal(f"line {n}: a part is `name : prop, prop`; got {line.strip()!r}")
        node = {"name": name, "kids": [], "line": n, "layout": None, "role": None, "text": None, "clamp": None,
                "of": None, "over": None, "each": None, "at": None, "on": [], "lens": None}
        for p in [p.strip() for p in _outside_quotes(rest, ", ") if p.strip()]:
            word, _, val = p.partition(" ")
            if p in LAYOUTS:
                node["layout"] = p
            elif word in ("role", "each") and re.fullmatch(r"[\w.-]+", val):
                if word == "role" and known_roles is not None and val not in known_roles:
                    raise LensRefusal(f"line {n}: no role {val!r} in calm.style. Roles: {' '.join(sorted(known_roles))}")
                node[word] = val
            elif word == "text" and val:
                node["text"] = val.strip('"')
                for v in re.findall(r"\$(\w+)", node["text"]):
                    if v not in NAMES:      # Lark: $me printed as its own name, identically in both printers. Agreement is not truth.
                        raise LensRefusal(f"line {n}: no value ${v}. A lens can name: {' '.join('$' + x for x in NAMES)}")
            elif word == "clamp" and val.isdigit():
                node["clamp"] = int(val)
            elif word == "of" and val:
                node["of"] = val
            elif word == "over" and re.fullmatch(r"\$\w+", val):
                node["over"] = val[1:]
            elif p == "at item":
                node["at"] = "item"
            elif word == "lens" and re.fullmatch(r"[\w$.-]+", val):
                node["lens"] = val
            elif word == "on":
                g, do, cmd = val.partition(" do ")
                if g not in GESTURES or not do or not cmd.strip():
                    raise LensRefusal(f"line {n}: `on <{'|'.join(GESTURES)}> do <desk command>`; got {p!r}")
                cmd = cmd.strip()
                # `on drag do move $item ...` reads as English; the desk wants `do move ...`. A gesture names a verb
                # unless it begins with one of the desk's own reading or session commands.
                if cmd.split(" ")[0] not in ("do", "look", "read", "examine", "find", "undo", "run", "scene", "rows", "worktree", "open", "fold"):
                    cmd = "do " + cmd
                node["on"].append({"on": g, "line": cmd})
            else:
                raise LensRefusal(f"line {n}: a lens cannot say {p!r}. It can say: {', '.join(LAYOUTS)}, role, text, clamp, "
                                  f"of <selection>, over $field, each <part>, at item, on <gesture> do <command>")
        if (node["of"] or node["over"]) and not node["each"]:
            raise LensRefusal(f"line {n}: `of`/`over` repeats something; say what with `each <part>`")
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
    for p in parts.values():
        for k in _walk(p):
            if k["each"] and k["each"] not in parts:
                raise LensRefusal(f"line {k['line']}: each {k['each']}: no part of that name is defined (unindented) in this lens")

    def reach(name, trail):
        if name in trail:
            raise LensRefusal(f"part {name!r} repeats itself ({' -> '.join(trail + [name])}); a lens may not recurse")
        for k in _walk(parts[name]):
            if k["each"]:
                reach(k["each"], trail + [name])
    for name in parts:
        reach(name, [])
    return root, parts


def _walk(node):
    yield node
    for k in node["kids"]:
        yield from _walk(k)


def _fill(tpl, ctx):
    return re.sub(r"\$(\w+)", lambda m: str(ctx[m.group(1)]) if m.group(1) in ctx else m.group(0), tpl)


def _ctx_for(w, nid):
    n = w.nodes[nid]
    s = w.subjects.get(n.get("subject")) or {}
    return {"item": nid, "id": n.get("subject") or nid, "title": s.get("title", n.get("title", "")), "text": s.get("text", ""),
            "kind": s.get("kind", n["type"]), "due": s.get("due") or "", "tags": " ".join(s.get("tags") or []),
            "_tags": list(s.get("tags") or [])}


def build(desk, src, stack=(), count=None):
    root, parts = parse(src)
    w = desk.world
    count = count if count is not None else [0]

    def make(node, ctx, key, parent_layout="free"):
        if node["at"] == "item" and parent_layout != "free":
            raise LensRefusal(f"line {node['line']}: `at item` places a part by its world position, which only a `free` parent can honour; "
                              f"its parent is {parent_layout or 'unlaid'}. Make the parent free, or drop `at item`")
        out = {"part": node["name"], "key": key, "role": node["role"], "layout": node["layout"], "item": ctx.get("item"),
               "box": None, "text": None, "clamp": node["clamp"], "acts": [], "kids": []}
        if node["at"] == "item" and ctx.get("item") in w.nodes:
            n = w.nodes[ctx["item"]]
            out["box"] = [n["x"], n["y"], n["w"], n["h"]]
            # Lark: "can he see this?" The world already knows (offscreen-part, spills-parent, 43% hidden by f52); the scene threw it away.
            out["facts"] = [f for f in w.relations(ctx["item"]) if f != "clear"]
        if node["text"] is not None:
            out["text"] = _fill(node["text"], {k: v for k, v in ctx.items() if k != "n"} if node["each"] else ctx)   # a repeat words its own count
        safe = {k: (_cmd_value(v) if isinstance(v, str) else v) for k, v in ctx.items()}
        out["acts"] = [{"on": a["on"], "line": _fill(a["line"], safe)} for a in node["on"]]
        if ctx.get("item") in w.nodes and out["acts"]:
            out["rev"] = w.nodes[ctx["item"]]["rev"]      # Astra: a gesture acts on the generation that was observed, not on a fresh look
        count[0] += 1
        if count[0] > BUDGET:
            raise LensRefusal(f"this lens makes more than {BUDGET} scene nodes. Put `clamp N` on the repeat (line {node['line']}); the text will say how many are left")
        if node["each"]:
            each = parts[node["each"]]
            if node["of"]:
                out["of"] = node["of"]
                rs = rows(desk, _fill(node["of"], ctx))
                keep = node["clamp"] or 10 ** 9       # Flint: clamp N on a repeat; 305 things put 305 nodes in both printers
                total = len(rs) if rs is not None else None
                for k, r in enumerate((rs or [])[:keep]):
                    out["kids"].append(make(each, dict(ctx, **r), f"{key}/{r.get('cid') or r.get('eid') or r.get('name') or k}", node["layout"]))
                sel = desk._parse_selection(_fill(node["of"], ctx)) if rs is None else None
                ids = sel[0] if sel else []
                total = len(ids) if total is None else total
                for i in ids[:keep]:
                    out["kids"].append(make(each, _ctx_for(w, i), f"{key}/{i}", node["layout"]))
                if total > keep:
                    out["cut"] = total - keep
                    out["kids"].append({"part": "cut", "key": f"{key}/cut", "role": "cut", "layout": None, "item": None, "box": None,
                                        "text": f"{total - keep} more not shown (clamp {keep}); find {_fill(node['of'], ctx)} lists all {total}",
                                        "clamp": None, "acts": [], "kids": []})
            else:
                for k, v in enumerate(ctx.get("_" + node["over"], [])):
                    out["kids"].append(make(each, dict(ctx, it=v), f"{key}/{k}", node["layout"]))
            out["n"] = len(out["kids"]) - (1 if out.get("cut") else 0)
            if out["text"] is not None:                         # Flint bug 4: the count existed and could not be put into words
                out["text"] = out["text"].replace("$n", str(out["n"]))
        if node["lens"]:
            inner = _fill(node["lens"], ctx)
            if inner.lower() in stack:
                raise LensRefusal(f"line {node['line']}: lens {inner} contains itself ({' -> '.join(stack + (inner.lower(),))})")
            sub = build(desk, find_lens(desk, inner)["text"], stack + (inner.lower(),), count)
            sub["key"] = f"{key}/lens:{inner}"
            _rekey(sub, sub["key"])
            out["kids"].append(sub)
            out["lens"] = inner
        for kid in node["kids"]:
            out["kids"].append(make(kid, dict(ctx, n=out.get("n", ctx.get("n", ""))), f"{key}/{kid['name']}", node["layout"]))
        return out

    return make(parts[root], {}, root)


def _rekey(n, prefix):
    for k in n["kids"]:
        k["key"] = prefix + "/" + k["key"]
        _rekey(k, prefix)


def to_text(scene, name, who, at):
    lines = [f"scene {name} · for {who} · world @{at}"]

    def pr(n, d):
        bits = [n["part"]]
        if n.get("item"):
            bits.append(n["item"])
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
            bits.append(n["layout"])
        if n.get("lens"):
            bits.append(f"· lens {n['lens']}")
        if n["box"]:
            bits.append(f"at {n['box'][0]},{n['box'][1]} {n['box'][2]}x{n['box'][3]}")
        if n.get("facts"):
            bits.append("= " + ", ".join(n["facts"]))
        if "n" in n:
            bits.append(f"· {n['n']} of {n['of']}" if n.get("of") else f"· {n['n']}")
        for a in n["acts"]:
            bits.append(f"· {a['on']}: {a['line']}")
        lines.append("  " * d + " ".join(bits))
        for k in n["kids"]:
            pr(k, d + 1)

    pr(scene, 1)
    return "\n".join(lines)


def find_lens(desk, name):
    w = desk.world
    for s in w.subjects.values():
        if "lens" in (s.get("tags") or []) and s["title"].lower() == name.lower():
            return s
    have = [s["title"] for s in w.subjects.values() if "lens" in (s.get("tags") or [])]
    raise LensRefusal(f"no lens {name!r}. A lens is a note tagged lens whose text is the description. Lenses here: {', '.join(have) or 'none'}")


def scene_for(desk, name):
    """Astra: an invalid lens was stored before it was validated, and the view went blank. A lens that stops compiling
    now keeps showing its last version that did, and says so first, in both printers."""
    s = find_lens(desk, name)
    good = getattr(desk, "_lens_good", None)
    if good is None:
        good = desk._lens_good = {}
    try:
        sc = build(desk, s["text"], (s["title"].lower(),))
        good[s["id"]] = s["text"]
        return sc, to_text(sc, s["title"], desk.world.me, len(desk.world.events))
    except LensRefusal as e:
        if s["id"] not in good:
            raise
        sc = build(desk, good[s["id"]])
        sc["broken"] = str(e)
        text = to_text(sc, s["title"], desk.world.me, len(desk.world.events))
        return sc, f"! lens {s['title']} no longer compiles: {e}\n! showing the last version that did. Fix it with rewrite, or undo.\n" + text
