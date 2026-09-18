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

import re

LAYOUTS = ("column", "row", "free")
GESTURES = ("click", "edit", "drag", "drop")
NAMES = ("title", "text", "kind", "due", "tags", "id", "item", "it", "n")


class LensRefusal(Exception):
    pass


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
    for n, raw in enumerate(src.replace("\\n", "\n").splitlines(), 1):
        line = raw.split(" # ")[0].rstrip()
        if not line.strip() or line.strip().startswith("#") or line.strip().startswith("lens "):
            continue
        indent = len(line) - len(line.lstrip())
        name, colon, rest = line.strip().partition(" : ")
        if not colon or not re.fullmatch(r"[\w-]+", name):
            raise LensRefusal(f"line {n}: a part is `name : prop, prop`; got {line.strip()!r}")
        node = {"name": name, "kids": [], "line": n, "layout": None, "role": None, "text": None, "clamp": None,
                "of": None, "over": None, "each": None, "at": None, "on": []}
        for p in [p.strip() for p in rest.split(", ") if p.strip()]:
            word, _, val = p.partition(" ")
            if p in LAYOUTS:
                node["layout"] = p
            elif word in ("role", "each") and re.fullmatch(r"[\w.-]+", val):
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
            parts[name] = node
            root = root or name
            stack = [(0, node)]
        else:
            while stack and stack[-1][0] >= indent:
                stack.pop()
            if not stack:
                raise LensRefusal(f"line {n}: indented part with no parent")
            stack[-1][1]["kids"].append(node)
            stack.append((indent, node))
    if not root:
        raise LensRefusal("an empty lens shows nothing; start with  window : column")
    for p in parts.values():
        for k in _walk(p):
            if k["each"] and k["each"] not in parts:
                raise LensRefusal(f"line {k['line']}: each {k['each']}: no part of that name is defined (unindented) in this lens")
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


def build(desk, src, depth=0):
    root, parts = parse(src)
    w = desk.world

    def make(node, ctx, key, parent_layout="free"):
        if node["at"] == "item" and parent_layout != "free":
            raise LensRefusal(f"line {node['line']}: `at item` places a part by its world position, which only a `free` parent can honour; "
                              f"its parent is {parent_layout or 'unlaid'}. Make the parent free, or drop `at item`")
        out = {"part": node["name"], "key": key, "role": node["role"], "layout": node["layout"], "item": ctx.get("item"),
               "box": None, "text": None, "clamp": node["clamp"], "acts": [], "kids": []}
        if node["at"] == "item" and ctx.get("item") in w.nodes:
            n = w.nodes[ctx["item"]]
            out["box"] = [n["x"], n["y"], n["w"], n["h"]]
        if node["text"] is not None:
            out["text"] = _fill(node["text"], ctx)
        out["acts"] = [{"on": a["on"], "line": _fill(a["line"], ctx)} for a in node["on"]]
        if node["each"]:
            each = parts[node["each"]]
            if node["of"]:
                out["of"] = node["of"]
                rs = rows(desk, _fill(node["of"], ctx))
                for k, r in enumerate(rs or []):
                    out["kids"].append(make(each, dict(ctx, **r), f"{key}/{r.get('cid') or r.get('eid') or r.get('name') or k}", node["layout"]))
                sel = desk._parse_selection(_fill(node["of"], ctx)) if rs is None else None
                ids = sel[0] if sel else []
                for i in ids:
                    out["kids"].append(make(each, _ctx_for(w, i), f"{key}/{i}", node["layout"]))
            else:
                for k, v in enumerate(ctx.get("_" + node["over"], [])):
                    out["kids"].append(make(each, dict(ctx, it=v), f"{key}/{k}", node["layout"]))
            out["n"] = len(out["kids"])
            if out["text"] is not None:                         # Flint bug 4: the count existed and could not be put into words
                out["text"] = out["text"].replace("$n", str(out["n"]))
        for kid in node["kids"]:
            out["kids"].append(make(kid, dict(ctx, n=out.get("n", ctx.get("n", ""))), f"{key}/{kid['name']}", node["layout"]))
        return out

    return make(parts[root], {}, root)


def to_text(scene, name, who, at):
    lines = [f"scene {name} · for {who} · world @{at}"]

    def pr(n, d):
        bits = [n["part"]]
        if n.get("item"):
            bits.append(n["item"])
        if n["text"] is not None:
            # Lark: fidelity is a property of a printer, not of a tree. This printer says every cut it makes.
            t = n["text"].split("\n")
            shown = t[: n["clamp"]] if n["clamp"] else t
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
        if n["box"]:
            bits.append(f"at {n['box'][0]},{n['box'][1]} {n['box'][2]}x{n['box'][3]}")
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
    s = find_lens(desk, name)
    sc = build(desk, s["text"])
    return sc, to_text(sc, s["title"], desk.world.me, len(desk.world.events))
