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


class LensRefusal(Exception):
    pass


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
                node["on"].append({"on": g, "line": cmd.strip()})
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

    def make(node, ctx, key):
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
                sel = desk._parse_selection(_fill(node["of"], ctx))
                ids = sel[0] if sel else []
                out["of"] = node["of"]
                for i in ids:
                    out["kids"].append(make(each, _ctx_for(w, i), f"{key}/{i}"))
            else:
                for k, v in enumerate(ctx.get("_" + node["over"], [])):
                    out["kids"].append(make(each, dict(ctx, it=v), f"{key}/{k}"))
            out["n"] = len(out["kids"])
        for kid in node["kids"]:
            out["kids"].append(make(kid, ctx, f"{key}/{kid['name']}"))
        return out

    return make(parts[root], {}, root)


def to_text(scene, name, who, at):
    lines = [f"scene {name} · for {who} · world @{at}"]

    def pr(n, d):
        bits = [n["part"]]
        if n.get("item"):
            bits.append(n["item"])
        if n["text"] is not None:
            t = n["text"].split("\n")
            shown = t[: n["clamp"]] if n["clamp"] else t
            bits.append('"' + " / ".join(shown)[:100] + '"' + (f" (+{len(t) - len(shown)} line(s) clamped)" if len(shown) < len(t) else ""))
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
