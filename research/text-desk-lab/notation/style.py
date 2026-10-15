"""style: the one reader of a style text (8 Oct 2026, step 1 of the grammar unification).

A style is a note tagged `style` (or the seed file desk-shell/style/<name>.style) whose lines are tokens, roles, fonts
and themes. Until today two readers read it: style.js in the browser, and a Python mirror in scene.py that receipts
used, kept in step by a node test. Now Python reads it once and hands every painter the result: `looks`, a dictionary
from role name to a medium-neutral look (colours as hex, lengths in pixels, a text face with size and leading). The
browser painter turns a look into CSS with a small table (style.js); a painter for another medium reads the same looks.

    parse(src)                 -> {tokens, roles, fonts, themes} or raises StyleRefusal(line, msg, escapes)
    looks(src | parsed, theme) -> {tokens, roles: {name: {look, line, unread}}, fonts, themes, ramp, unread}
    check(src)                 -> {refusal, roles, tokens, unread: [(role, prop, line, why)]}   (what a receipt says)

What the notation deliberately cannot say (each refusal prints two runnable escapes, as style.js did):
a colour or a length outside a token line; a type size off the ramp; a theme that redefines a role; a role line
without its spaced colon. `present` and `when <selection>` are gone: a lens says which parts are drawn and what role a
part wears (`role x when ...`); a removed word is refused, not ignored.

A look's keys (the painter's table maps each to its medium):
    on <colour>                  background           ink (a bare colour, or `x -> colour`)   foreground
    edge <colour>                a 1px border          border <side> <colour>                  one side
    corner <len>                 rounded corners       pad <len> | pad <side> <len>            padding
    space above|below <len>      margin                between <len>                           gap between children
    height <len|em>              least height          width <len|em>                          width (px) or widest (em)
    lift <len>                   a shadow, in the `shadow` token's colour when the style has one, else the ink's
    text [up|down [n]] [medium|strong] [slant] [tracked]  the face
    align start|center|end|stretch   where the part stands across its parent's flow (15 Oct)
    rail <colour>                a bar down the leading edge, as a lane's colour on a card (a5504)
    glow <colour>                a halo of the colour that slowly breathes: a part that is alive (a5504)
    afloat  shy  pulse  wave     flags: takes no room; unseen until near; the motions (pulse: the part breathes;
                                 wave, 14 Oct: each character rises in turn, as typing dots do)
    glide                        flag (a5504): when a repaint puts the same thing somewhere else (a card that changed
                                 lane), it travels there from where it was; a thing newly shown fades in
    touch                        flag (a5500, 15 Oct): the part answers the pointer: it rises and brightens under it,
                                 and sinks while pressed (a dock's icons). Brightens only, for reduced motion
"""
import hashlib
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
SEEDS = HERE / "desk-shell" / "style"
_HEX = re.compile(r"^#[0-9a-fA-F]{3,8}$")
SIDES = ("top", "right", "bottom", "left")
FAMILIES = {"mono": "ui-monospace, SFMono-Regular, Consolas, monospace", "serif": "Georgia, 'Iowan Old Style', serif"}
DEFAULT_FAMILY = "Inter, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif"
RAMP = 1.15
STEPS = (-3, -2, -1, 0, 1, 2, 3)


class StyleRefusal(Exception):
    """The style cannot be read. `line` is the line number (0 when the whole text is at fault); `escapes` are lines
    the writer can run instead."""

    def __init__(self, line, msg, escapes=()):
        super().__init__(f"line {line}: {msg}" if line else msg)
        self.line, self.msg, self.escapes = line, msg, list(escapes)


class Unread(Exception):
    """A property the painter will draw nothing for, and why."""


# ---------------------------------------------------------------------------------------------------------------------
# parse
# ---------------------------------------------------------------------------------------------------------------------
def _prop_ok(n, body):
    """A role's property names a token, never a raw colour or a pixel length."""
    hx = re.search(r"#[0-9a-fA-F]{3,8}\b", body)
    if hx:
        raise StyleRefusal(n, f"colours are named here; {hx.group(0)!r} may only appear on a token line",
                           [f"token <name> = {hx.group(0)}        (a new colour, named, for everyone)", "then say the name instead of the value"])
    px = re.search(r"\b(\d+(?:\.\d+)?)px\b", body)
    if px:
        k = max(1, round(float(px.group(1)) / 8))
        raise StyleRefusal(n, f"{px.group(0)} is not on the scale; lengths are gap, gap xN, gap /N, or an em",
                           [f"gap x{k}                       (= {k * 8}px at gap 8)", "token gap = <n>            (moves everything)"])


def parse(src):
    """A style's text as {tokens, token_line, roles: {name: {props, line}}, fonts, themes}. Read through tree.read, the
    one indentation reader (9 Oct, step 5): a theme's tokens are the lines under it, and a role's properties may be
    written on its line after ` : `, separated by commas, or one per line under `role <name> :` (the tree form, as a
    lens's words are written; both read to the same roles and `to_lines` prints the tree form)."""
    import tree
    out = {"tokens": {}, "token_line": {}, "roles": {}, "fonts": {}, "themes": {}}

    def refuse_in_theme(node):
        s = node.text
        what = s.split()[1] if len(s.split()) > 1 else "?"
        raise StyleRefusal(node.line, f"a theme may redefine tokens, not roles ({what!r}); both inhabitants must see one shape",
                           [f"role {what} : ...                 (change it for everyone, as a deed they will see)",
                            "do style <this appearance> ...     (change only this one, as an override)"])

    for node in tree.read(src):
        s, n = node.text, node.line
        m = re.match(r"^theme\s+(\S+)\s+of\s+(\S+)$", s)
        if m:
            theme = {"of": m.group(2), "tokens": {}, "line": n}
            out["themes"][m.group(1)] = theme
            for kid in tree.walk(node.kids):
                mt = re.match(r"^token\s+([\w.]+)\s*=\s*(.+)$", kid.text)
                if mt:
                    theme["tokens"][mt.group(1)] = mt.group(2).strip()
                elif re.match(r"^(role|when|present)\s", kid.text):
                    refuse_in_theme(kid)
                else:
                    raise StyleRefusal(kid.line, f'not a token line under theme {m.group(1)}: "{kid.text}"', ["token <name> = <value>"])
            continue
        m = re.match(r"^font\s+([\w-]+)\s*=\s*(.+)$", s)
        if m:
            names = [x.strip() for x in m.group(2).split(",") if x.strip()]
            out["fonts"][m.group(1)] = {"face": names[0] if names else "", "fallback": ", ".join(names[1:]) or "sans-serif", "line": n}
            continue
        m = re.match(r"^token\s+([\w.]+)\s*=\s*(.+)$", s)
        if m:
            out["tokens"][m.group(1)] = m.group(2).strip()
            out["token_line"][m.group(1)] = n
            continue
        if re.match(r"^present\s", s):
            raise StyleRefusal(n, "`present` was removed. A lens says which parts are drawn",
                               ["in the lens:   card : column, role card", "                 title : text $title, role title"])
        if re.match(r"^when\s", s):
            # 8 Oct: the clause reached only the old windowed shell; a look that depends on the thing is `role x when ...`
            raise StyleRefusal(n, "`when <selection>` was removed from styles. A look that depends on the thing is said in the lens",
                               ["in the lens:   card : column, role card, role card.due when $due != none"])
        if re.match(r"^role\s", s):
            at = s.rfind(" : ")
            if at < 0 and s.endswith(" :"):
                at = len(s) - 2
            if at < 0:
                raise StyleRefusal(n, 'a role line needs " : " with spaces before its properties',
                                   ["role <name> : <property>, <property>", "(an unspaced colon belongs to a selection, as in kind:note)"])
            head, body = re.sub(r"^\w+\s+", "", s[:at], count=1).strip(), s[at + 3:].strip()
            props = []
            _prop_ok(n, body)
            props += [x.strip() for x in body.split(",") if x.strip()]
            for kid in tree.walk(node.kids):            # the tree form: one property per line under the role
                _prop_ok(kid.line, kid.text)
                props += [x.strip() for x in kid.text.split(",") if x.strip()]
            out["roles"][head] = {"props": props, "line": n}
            continue
        raise StyleRefusal(n, f'not a token, role, font or theme line: "{s}"',
                           ["token <name> = <value>", "role <name> : <props>", "font <name> = <Family>, <fallback>", "theme <name> of <style>"])
    return out


def to_lines(src):
    """The style in the tree form: each role's properties one per line under `role <name> :`; tokens, fonts and themes
    as written. Comments and blank lines are kept where they stand. Raises StyleRefusal when the text does not parse."""
    import tree
    parse(src)
    out, roles = [], {}
    for node in tree.read(src):
        if re.match(r"^role\s", node.text):
            roles[node.line] = node
    skip = set()
    for n, raw in enumerate(re.split(r"\r?\n", src or ""), 1):
        if n in skip:
            continue
        node = roles.get(n)
        if node is None:
            out.append(raw.rstrip())
            continue
        at = node.text.rfind(" : ")
        if at < 0 and node.text.endswith(" :"):
            at = len(node.text) - 2
        head, body = node.text[:at].strip(), node.text[at + 3:].strip()
        props = [x.strip() for x in body.split(",") if x.strip()]
        for kid in tree.walk(node.kids):
            props += [x.strip() for x in kid.text.split(",") if x.strip()]
            skip.add(kid.line)
        out.append(f"{head} :")
        out += [f"  {p}" for p in props]
    return "\n".join(out).rstrip("\n") + ("\n" if (src or "").endswith("\n") else "")


# ---------------------------------------------------------------------------------------------------------------------
# tokens -> values
# ---------------------------------------------------------------------------------------------------------------------
def _rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c + c for c in h)
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def _hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(v))):02x}" for v in rgb)


def mix(a, b, t):
    """The colour t of the way from a to b, as style.js mixed `x at N%` over the paper."""
    A, B = _rgb(a), _rgb(b)
    return _hex([A[i] * (1 - t) + B[i] * t for i in range(3)]).upper()


def resolve_tokens(st, theme=None):
    """-> {name: {"type": colour|length|text|word, ...}}: a colour has `value` (hex); a length `value` (a number); a
    text `family`, `size`, `leading`; a word `value`. A token that names nothing readable is left out."""
    raw = dict(st["tokens"])
    if theme and theme in st["themes"]:
        raw.update(st["themes"][theme]["tokens"])
    done = {}

    def get(name, seen):
        if name in done:
            return done[name]
        if name not in raw or name in seen:
            return None
        seen = seen | {name}
        v = raw[name].strip()
        if _HEX.match(v):
            done[name] = {"type": "colour", "value": v.upper() if len(v) in (4, 7) else v}
            return done[name]
        m = re.match(r"^([\w.]+)\s+at\s+([\d.]+)%?$", v)
        if m:
            base = get(m.group(1), seen)
            paper = {"value": raw["paper"]} if _HEX.match(raw.get("paper", "")) else get("paper", seen | {"__"})
            if base and base["type"] == "colour" and paper:
                done[name] = {"type": "colour", "value": mix(paper["value"], base["value"], float(m.group(2)) / 100)}
                return done[name]
        if re.match(r"^\d+(\.\d+)?$", v):
            done[name] = {"type": "length", "value": float(v) if "." in v else int(v)}
        elif (m := re.match(r"^([\w-]+)\s+([\d.]+)/([\d.]+)$", v)):
            done[name] = {"type": "text", "family": m.group(1), "size": float(m.group(2)), "leading": float(m.group(3))}
        else:
            done[name] = {"type": "word", "value": v}
        return done[name]

    return {k: t for k in raw if (t := get(k, set())) is not None}


# ---------------------------------------------------------------------------------------------------------------------
# properties -> a look
# ---------------------------------------------------------------------------------------------------------------------
def _length(e, T):
    """-> a number of pixels, {"em": n}, or None."""
    m = re.match(r"^([\w.]+)\s*x\s*([\d.]+)$", e) or re.match(r"^([\w.]+)\s*/\s*([\d.]+)$", e)
    if m:
        b = T.get(m.group(1))
        if b and b["type"] == "length":
            return b["value"] * float(m.group(2)) if "x" in e else b["value"] / float(m.group(2))
        return None
    m = re.match(r"^([\w.]+)$", e)
    if m and (b := T.get(m.group(1))) and b["type"] == "length":
        return b["value"]
    m = re.match(r"^([\d.]+)em$", e)
    return {"em": float(m.group(1))} if m else None


def _colour(e, T):
    m = re.match(r"^([\w.]+)\s+at\s+([\d.]+)%?$", e)
    if m:
        b, p = T.get(m.group(1)), T.get("paper")
        if b and b["type"] == "colour" and p and p["type"] == "colour":
            return mix(p["value"], b["value"], float(m.group(2)) / 100)
        return None
    t = T.get(e)
    return t["value"] if t and t["type"] == "colour" else None


def _px(n):
    return int(n) if float(n).is_integer() else round(n, 2)


def family_of(name, fonts):
    """The face stack a text token's family names: a `font` line's face and fallback, else the built-in families."""
    f = fonts.get(name)
    if f:
        return f"'{f['face']}', {f['fallback']}"
    return FAMILIES.get(name, DEFAULT_FAMILY)


def read_prop(p, T, fonts):
    """One property as look fragments, {key: value}, or raises Unread(why)."""
    def need_len(e, key, em_ok=False):
        l = _length(e, T)
        if isinstance(l, dict) and em_ok:
            return {key + "_em": l["em"]}
        if isinstance(l, (int, float)):
            return {key: _px(l)}
        if re.search(r"\s\d+(\.\d+)?$", p) and not re.search(r"[x/]\s*\d+(\.\d+)?$", p):
            raise Unread("a bare number is not on the scale: say gap, gap xN or gap /N")
        raise Unread("names no token of the right kind")

    def need_col(e, key):
        c = _colour(e, T)
        if c is None:
            raise Unread("names no token of the right kind")
        return {key: c}

    if (m := re.match(r"^(show|hide)\s+\w+$", p)):
        raise Unread("`present` was removed: a lens says which parts are drawn")
    if (m := re.match(r"^on\s+(.+)$", p)):
        return need_col(m.group(1), "on")
    if (m := re.match(r"^([\w.]+)\s*->\s*(.+)$", p)):
        return need_col(m.group(2), "ink")
    if (m := re.match(r"^edge\s+(.+)$", p)):
        return need_col(m.group(1), "edge")
    if (m := re.match(r"^border\s+(top|right|bottom|left)\s+(.+)$", p)):
        return need_col(m.group(2), "border_" + m.group(1))
    if (m := re.match(r"^corner\s+(.+)$", p)):
        return need_len(m.group(1), "corner")
    if (m := re.match(r"^pad\s+(top|right|bottom|left)\s+(.+)$", p)):
        return need_len(m.group(2), "pad_" + m.group(1))
    if (m := re.match(r"^pad\s+(.+)$", p)):
        return need_len(m.group(1), "pad")
    if (m := re.match(r"^space\s+(above|below)\s+(.+)$", p)):
        return need_len(m.group(2), "space_" + m.group(1))
    if (m := re.match(r"^between\s+(.+)$", p)):
        return need_len(m.group(1), "between")
    if (m := re.match(r"^height\s+(.+)$", p)):
        return need_len(m.group(1), "height", em_ok=True)
    if (m := re.match(r"^width\s+(.+)$", p)):
        return need_len(m.group(1), "width", em_ok=True)
    if (m := re.match(r"^lift\s+(.+)$", p)):
        out = need_len(m.group(1), "lift")
        # a5504: a dark style's shadow is not its ink (a light ink drew a glow under every card); a `shadow` token wins
        sh = T.get("shadow")
        ink = sh if sh and sh["type"] == "colour" else T.get("ink")
        if not ink or ink["type"] != "colour":
            raise Unread("names no token of the right kind")
        out["lift_ink"] = ink["value"]
        if ink is sh:
            out["lift_shadow"] = True
        return out
    if (m := re.match(r"^rail\s+(.+)$", p)):
        return need_col(m.group(1), "rail")         # a5504: a lane's colour, a bar down the part's leading edge
    if (m := re.match(r"^glow\s+(.+)$", p)):
        return need_col(m.group(1), "glow")         # a5504: the part breathes a halo of this colour (alive, working)
    if p == "glide":
        return {"glide": True}                      # a5504: the part moves from where its thing was painted before
    if re.match(r"^text\b", p):
        tok = p.split()[0] if p.startswith("text.") else "text"
        t = T.get(tok)
        if not t or t["type"] != "text":
            raise Unread("names no text token")
        if (m := re.search(r"\bat\s+([\d.]+)\b", p)):
            raise Unread(f'"text at {m.group(1)}" is not a step of the ramp')
        ramp = T.get("ramp")
        ratio = ramp["value"] if ramp and ramp["type"] == "length" else RAMP
        size = t["size"]
        if (m := re.search(r"\bdown(?:\s+(\d+))?\b", p)):
            size = size / ratio ** int(m.group(1) or 1)
        if (m := re.search(r"\bup(?:\s+(\d+))?\b", p)):
            size = size * ratio ** int(m.group(1) or 1)
        face = {"family": family_of(t["family"], fonts), "size": round(size), "leading": t["leading"]}
        if re.search(r"\bstrong\b", p):
            face["weight"] = 600
        elif re.search(r"\bmedium\b", p):
            face["weight"] = 500
        if re.search(r"\bslant\b", p):
            face["slant"] = True
        if re.search(r"\btracked\b", p):
            face["tracked"] = True
        return {"text": face}
    if p in ("afloat", "shy", "pulse", "wave", "touch"):
        return {p: True}
    if (m := re.match(r"^align\s+(start|center|end|stretch)$", p)):
        return {"align": m.group(1)}      # 15 Oct: where the part stands across its parent's flow (a chat's own lines at the end)
    if re.match(r"^align\b", p):
        raise Unread("align takes start, center, end or stretch")
    c = _colour(p, T)
    if c is None:
        raise Unread("is no property and no colour token")
    return {"ink": c}


def ramp(T):
    t, r = T.get("text"), T.get("ramp")
    if not t or t["type"] != "text":
        return []
    ratio = r["value"] if r and r["type"] == "length" else RAMP
    return [{"step": s, "px": round(t["size"] * ratio ** s)} for s in STEPS]


def looks(src, theme=None):
    """The whole style, read once, for any painter. `src` is the text or a parsed style. Raises StyleRefusal."""
    st = parse(src) if isinstance(src, str) else src
    T = resolve_tokens(st, theme)
    roles, unread = {}, []
    for name, r in st["roles"].items():
        look, bad = {}, []
        for p in r["props"]:
            try:
                look.update(read_prop(p, T, st["fonts"]))
            except Unread as e:
                bad.append((p, str(e)))
                unread.append((name, p, r["line"], str(e)))
        roles[name] = {"look": look, "line": r["line"], "unread": bad}
    return {"tokens": T, "roles": roles, "fonts": {k: {"face": v["face"], "fallback": v["fallback"]} for k, v in st["fonts"].items()},
            "themes": list(st["themes"]), "theme": theme if theme in st["themes"] else "", "ramp": ramp(T), "unread": unread}


def check(src):
    """What a receipt says of a style text: {"refusal": str or None, "roles": n, "tokens": n, "unread": [(role, prop, line, why)]}."""
    try:
        lk = looks(src)
    except StyleRefusal as e:
        return {"refusal": str(e), "roles": 0, "tokens": 0, "unread": []}
    return {"refusal": None, "roles": len(lk["roles"]), "tokens": len(lk["tokens"]), "unread": lk["unread"]}


def role_names(src):
    """The roles a style text names, read from its `role` lines alone, so a lens under a style with one bad line still
    compiles (the painter keeps the last version of the style that read; the receipt says the style does not parse)."""
    return {l.split()[1] for l in (src or "").splitlines() if l.startswith("role ") and len(l.split()) > 1}


def seed(name):
    """The seed file's text for a style name, or None. -> {name, text, origin, rev}"""
    f = SEEDS / f"{pathlib.Path(name).name}.style"
    if not f.exists():
        return None
    text = f.read_text(encoding="utf-8")
    return {"name": name, "text": text, "origin": "file", "rev": "file-" + hashlib.sha256(text.encode()).hexdigest()[:10]}


def for_painter(source, theme=None):
    """The answer to /api/style: the source as before, plus `looks`, or `refusal` when the text cannot be read (the
    painter keeps the last style that could)."""
    out = dict(source)
    try:
        out["looks"] = looks(source["text"], theme)
    except StyleRefusal as e:
        out["looks"], out["refusal"], out["escapes"] = None, str(e), e.escapes
    return out
