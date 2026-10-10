"""blanks: the one filler (a806, rooms step 2a; a598 3.2's 'filled once, in one place').

A blank is a word beginning with $ that stands for a value the desk knows when the line runs. Typed desk lines,
world verbs, scripts and rules all fill their blanks here, the same way:

    $here          the room you are in (rooms.room_of); $here.<prop> a prop of it: $here.talk, $here.describe.
                   In a rule, the rule's own home (a990): the room its author saved it in
    $new           the thing made most recently earlier in this reply (any kind; of several made by one line, the
                   last); refused, saying why, if nothing in this reply made anything. The receipt says what it was
    $today         the clock's date                     $me   whoever is acting
    $<handle>      a handle you named (set draft = a98, or create ... as=draft)
    in a verb:     $1 $2 ... its words, $* the rest of the line exactly as said, $this the thing a verb lives on
    in a rule:     $item   the thing it fired on (the target, as in a lens act)
    the current thing's own words (8 Oct, names.py): in a rule, $title $text $kind $due $tags and any prop ($status)
                   are $item's; in a verb that lives on a thing they are $this's
    $house         the outermost surface, whose props are everyone's: $house.<prop>
    $me.corner, $me.<prop>   a person's corner and the props on their person note
    a part of the thing a blank names (a1027): .title its title, .maker who made it, .<prop> one of its props
                   ($item.asked_by, $1.status); .text its words, .in what holds it, .before and .after its neighbours
                   there (7 Oct); a part it doesn't have refuses, naming the thing
    $( <expr> )    a value computed where it stands (8 Oct): the lens's expressions (expr.py), over the same names,
                   with count(<selection>) and sum/min/max($field of <selection>); a value that cannot be computed
                   refuses with the reason, never fills as none
    a handle named with as= (create ... as=draft) lives for the reply it was named in; set draft = <id> keeps it

Where they are filled: after the line is parsed, in the values themselves (a target, a selection, a k=v value), so a
filled value is never read again as desk words or filled a second time ($* may carry '$here' or 'a; b "hi"' through
untouched). Text is words by default (a965): in a typed line an argument the verb declares as text (help append:
line=<str>) is never filled, and a prop value (untyped) fills only when the whole value is one blank; targets,
selections and ids are filled. Only inside a verb body, a script or a rule, which its author wrote as a template, are
text values filled too. A literal
dollar sign is written \\$ anywhere. A blank that can't be filled refuses; it is never stored as its own name.

$new is kept per reader and per reply: each line that makes something records it, and the later lines of the same
reply (same `reply` token from the caller, or the same call) read the most recent (Juniper, a806 (10)). A line in a
new reply finds nothing there, so a $new can never reach back to a thing made an hour ago. A verb body is a reply of
its own: its steps see each other's $new, and the caller's next line sees the last thing the whole use made.
"""
import re

import names
from world import Refusal

LIT = ""          # a \$ in the line, kept out of shlex's way until it lands in a value as a plain $
BLANK = re.compile(re.escape(LIT) + r"|\$(\*|\d+|[A-Za-z_][A-Za-z0-9_]*)((?:\.[A-Za-z_][A-Za-z0-9_-]*)?)")
WORD = re.compile(r"^\$(\d+|[A-Za-z_][A-Za-z0-9_]*)(\.[A-Za-z_][A-Za-z0-9_-]*)?$")
READS = ("look", "read", "examine", "x", "ex", "find", "table", "why", "compare", "history", "go", "where", "pivot",
         "verbs", "open", "close", "set")       # typed commands whose words name things: filled as values

KNOWN = ("$here $here.<prop> $new $today $me $me.corner $me.<prop> $house $house.<prop>, a handle ($name: set, or as= in this "
         "reply); in a verb $1 $2 $* $this; in a rule $item; the current thing's own words ($title, $status); a thing's parts "
         ".title .maker .text .in .before .after .<prop>; a value $( <expr> )")


class Ctx:
    """Where a line is being filled. kind: typed | verb | script | rule."""
    binds = None            # a1156: a template's binding (verbs.bind_text), kept with its lines when they were saved

    def __init__(self, kind, args=None, rest="", me=None, this=None, item=None, name="", prev=None, home=None, handles=None):
        self.kind, self.args, self.rest, self.me, self.this, self.item, self.name = kind, args, rest, me, this, item, name
        self.prev = prev        # what was made most recently earlier at this level of this reply (None: nothing yet)
        self.home = home        # a990: the room a template lives in (its bare words are looked up there), or None
        self.handles = handles if handles is not None else {}     # 8 Oct: the things `as=` named in this reply

    @property
    def template(self):
        return self.kind != "typed"


SP = "\u2423"       # a space inside $( ... ), kept out of the line's word split until the value is computed or stored


def protect(line):
    """Before a line is split into words: every \\$ becomes LIT, so no parser eats the backslash; and every space
    inside a `$( ... )` becomes SP, so `n=$(2 + 3)` is one word for the parser and reads back as written."""
    line = (line or "").replace("\\$", LIT)
    out, i = "", 0
    while True:
        j = line.find("$(", i)
        k = _close(line, j + 1) if j >= 0 else -1
        if k < 0:
            return out + line[i:]
        out += line[i:j] + line[j:k + 1].replace(" ", SP)
        i = k + 1


def literal(text):
    return str(text).replace(LIT, "$").replace(SP, " ")


def ctx_of(desk):
    stack = getattr(desk, "_ctxs", None)
    return stack[-1] if stack else Ctx("typed")


def _title(desk, ident):
    return desk._title_of(ident)


def _here(desk, ctx, name):
    if ctx.kind == "rule":
        # a990: a rule stands in its own home, the room its author saved it in, wherever anyone is now
        if ctx.home:
            return ctx.home
        raise Refusal(f"${name}: this rule has no room (it was saved before rules had homes, or where there are no "
                      f"rooms); name the thing itself, or save the rule again from the room it belongs to")
    import rooms
    w = desk.world
    if not rooms.all_rooms(w):
        raise Refusal(f"${name}: this world has no rooms, so there is no here (a room is a surface with prop role=room)")
    fid = rooms.room_of(w, w.me)
    if fid is None:
        raise Refusal(f"${name}: {w.display_name(w.me)} is not placed in a room (a focus, not a location), so there is no here")
    return fid


def _word_frame(desk, ctx):
    """The words a template gives: $1 $2 ... $* $this in a verb, $item in a rule. Each is claimed in every host, so a
    word used where it has no value refuses with what it means (never falls through to a handle of that name)."""
    def has(name):
        return name.isdigit() or name in ("this", "item")

    def get(name):
        if name.isdigit():
            k = int(name)
            if ctx.args is None or k < 1:
                raise Refusal(f"${name} stands for a word after a verb or script; there are none here")
            if k > len(ctx.args):
                raise Refusal(f"{ctx.name or 'this'} needs {k} word(s) after it; got {len(ctx.args)}"
                              + (f". help {ctx.name}" if ctx.name else ""))
            val = ctx.args[k - 1]
            if isinstance(val, Refusal):
                raise val
            return val
        if name == "item":
            if ctx.kind != "rule" or not ctx.item:
                raise Refusal("$item stands for the target: the thing a rule fired on, or the thing a lens gesture acts on. "
                              "Did you mean $new, the thing made most recently in this reply?")
            return ctx.item
        if name == "this":
            if ctx.kind != "verb":
                raise Refusal("$this is the thing a verb lives on; it has a value only inside a verb")
            if not ctx.this:
                raise Refusal(f"{ctx.name} says $this but lives on no thing")
            return ctx.this
    return names.Frame("word", get, has=has)


def _reply_frame(desk, ctx):
    """$new, and the handles `as=` named earlier in this reply."""
    def has(name):
        return name == "new" or name in ctx.handles

    def get(name):
        if name == "new":
            if ctx.kind == "rule":
                raise Refusal("$new: a rule has no earlier line; it acts on $item, the thing it fired on")
            if not ctx.prev:
                where = "this verb's earlier steps" if ctx.kind == "verb" else "this reply"
                raise Refusal(f"$new names the thing made most recently earlier in this reply, and nothing earlier in "
                              f"{where} made anything (a new reply starts fresh). Use the id a receipt printed")
            val = ctx.prev[-1]              # a line that made several: the last (Juniper, a806 (10))
            desk._filled_new = val
            return val
        return ctx.handles[name]
    return names.Frame("reply", get, has=has)


def scope_of(desk, ctx):
    """The frames a typed line, a verb or a rule reads names through (names.py says the order)."""
    frames = [_word_frame(desk, ctx)]
    cur = ctx.item if ctx.kind == "rule" else (ctx.this if ctx.kind == "verb" else None)
    if cur and (cur in desk.world.nodes or cur in desk.world.subjects):
        frames.append(names.thing_frame(desk.world, cur))
    frames.append(_reply_frame(desk, ctx))
    frames.append(names.host_frame(desk, {"me": ctx.me}, here=lambda: _here(desk, ctx, "here")))
    frames.append(names.handles_frame(getattr(desk, "vars", None)))
    return names.Scope(frames)


def _one(desk, ctx, name, attr):
    """The value of one blank, or a Refusal. attr is '' or '.<word>'."""
    what = "$" + name + attr
    f = scope_of(desk, ctx).frame_for(name)
    if f is None:
        raise Refusal(f"${name} is no blank here. Blanks: {KNOWN}. A literal dollar sign is written \\$")
    if attr:
        v = f.part(name, attr)
        if v is not None:
            return v
    val = f.get(name)
    if not attr:
        return str(val) if name == "me" else val
    return _part(desk, val, attr, what)


def _part(desk, val, attr, what):
    """A part of the thing a blank names (a1027; names.part_of): .title its title, .maker who made it, .text, .in,
    .before, .after, any other word one of its props. A part it doesn't have refuses, naming the thing."""
    if attr == ".title" and str(val) in desk.world.nodes:
        return _title(desk, val)
    return names.part_of(desk.world, val, attr[1:], what, resolve=desk._resolve)


def name_made(desk, alias, ident):
    """`create ... as=draft` (and group): the handle lives for this reply, in the innermost template (a verb's own
    steps see it; the caller's later lines in the same reply see it too, through the typed ctx). `set` keeps one."""
    ctx_of(desk).handles[alias] = ident


# ---- $( <expr> ): a value computed where it stands (8 Oct) ------------------------------------------------------------
def _close(text, i):
    """The index of the `)` closing the `(` at text[i], or -1."""
    depth, q = 0, False
    for k in range(i, len(text)):
        c = text[k]
        if c == '"' and text[k - 1:k] != "\\":
            q = not q
        if q:
            continue
        depth += (c == "(") - (c == ")")
        if depth == 0:
            return k
    return -1


def whole_blank(value):
    """Is this whole value one blank ($new, $here.talk, $draft) or one computed value ($( ... ))?"""
    v = str(value).replace(SP, " ")
    return bool(WORD.match(v)) or (v.startswith("$(") and _close(v, 1) == len(v) - 1)


def expr_env(desk, ctx):
    """The expression evaluator's door to a command's names: $x and $x.part through the one resolver; a selection
    through the desk's own reader; a member's field through part_of."""
    def get(name):
        if not name.startswith("$"):
            return None                     # a bare word in a command's expression names no let; it is none, and says so
        m = WORD.match(name)
        if not m:
            return None
        try:
            return str(_one(desk, ctx, m.group(1), m.group(2) or ""))
        except Refusal:
            return None

    def select(q):
        sel = desk._parse_selection(fill(desk, q, ctx=ctx))
        return list(sel[0]) if sel else []

    def field(i, f):
        try:
            return _part(desk, i, "." + f, f"${i}.{f}")
        except Refusal:
            return None
    return {"get": get, "select": select, "field": field, "reads": []}


def compute(desk, value, ctx=None, soft=False):
    """Every `$( <expr> )` in `value` becomes its printed value. A value that cannot be computed refuses with the
    reason (soft: stays as written, for an echo)."""
    import expr as X
    ctx = ctx or ctx_of(desk)
    out, i = "", 0
    while True:
        j = value.find("$(", i)
        if j < 0:
            return out + value[i:]
        k = _close(value, j + 1)
        if k < 0:
            return out + value[i:]
        inner = value[j + 2:k].replace(SP, " ").strip()
        val, inputs = X.run(inner, expr_env(desk, ctx))
        if val.is_none() and not soft:
            raise Refusal(f"$( {inner} ): {val.why}" + (f" ({inputs})" if inputs else ""))
        out += value[i:j] + (value[j:k + 1].replace(SP, " ") if val.is_none() else X.fmt(val, reach=False))
        i = k + 1


def fill(desk, value, text=False, ctx=None, quote=False, soft=False):
    """Fill every blank in one value, in one pass: what a blank becomes is never read again. text=True: the value is
    words a person wrote (line=, text=, title=), filled only inside a template. quote=True: the value is still desk
    words (a read command's arguments), so a filled value with a space is quoted, and one inside quotes is escaped.
    soft=True (a receipt's echo): a blank that can't be filled stays as written instead of refusing."""
    ctx = ctx or ctx_of(desk)
    value = str(value)
    if text and not ctx.template:
        return literal(value)
    if "$(" in value:
        value = compute(desk, value, ctx, soft=soft)

    def one(m):
        if m.group(0) == LIT:
            return "\\$" if soft else "$"
        name, attr = m.group(1), m.group(2) or ""
        if name == "*":
            if ctx.args is None:
                return m.group(0)               # typed: $* is two characters
            val = literal(ctx.rest)
        elif name.isdigit() and ctx.args is None:
            return m.group(0)                   # typed: $5 is a price, not a blank
        else:
            try:
                val = str(_one(desk, ctx, name, attr))
            except Refusal:
                if soft:
                    return m.group(0)
                raise
        if not quote:
            return val
        if value[:m.start()].count('"') % 2 == 1:
            return val.replace("\\", "\\\\").replace('"', '\\"')
        return '"' + val.replace("\\", "\\\\").replace('"', '\\"') + '"' if (" " in val or not val) else val

    keep = getattr(desk, "_filled_new", None)
    out = BLANK.sub(one, value)
    if soft:
        desk._filled_new = keep          # an echo names nothing: only a line that ran says what its $new was
    return out


ARG = re.compile(r"([A-Za-z_][A-Za-z0-9_-]*)=(<[^>]*>|[^\s\]|]+)")
PROSE = ("<str>", "<text>")


def arg_kinds(verb):
    """{key: 'prose' | 'value'} from the verb's own argument list, the one help <verb> prints (append: line=<str>).
    A key it doesn't declare, and every key of prop, is a prop: untyped."""
    import moo
    v = moo.REGISTRY.get(verb if verb in moo.REGISTRY else moo.SYNONYMS.get(verb, verb))    # create is a verb, not group
    if v is None or v.name == "prop":
        return {}
    return {k: "prose" if spec in PROSE else "value" for k, spec in ARG.findall(v.args or "")}


def fill_arg(desk, verb, key, value):
    """One k=v value of a do line (a965, inverting a806's list of text keys). Typed: an argument the verb declares as
    text (<str>) is prose, never filled; one it declares as a target, selection, id or date is filled; any other (a
    prop) fills only when the whole value is one blank (describe=$new), never a blank inside other words. In a
    template (a verb body, script or rule, written as one) every value is filled."""
    if ctx_of(desk).template:
        return fill(desk, value)
    kind = _kind(verb, key)
    if kind == "prose" or (kind == "prop" and not whole_blank(value)):
        return literal(value)
    return fill(desk, value)


def _kind(verb, key):
    if verb == "prop" and key == "query":
        return "value"          # a1322: a view's query is a selection, filled as every selection is
    return arg_kinds(verb).get(key, "prop")


def kept(desk, verb, key, value):
    """a1322: the blanks a typed prop value keeps as its own words (wake="look $new"), so the receipt can say so: an
    ok must not hide a blank that will never fill. [] in a template, for text, or for a whole-value blank."""
    if ctx_of(desk).template or _kind(verb, key) != "prop" or whole_blank(value):
        return []
    return [m.group(0) for m in BLANK.finditer(str(value))
            if m.group(1) and m.group(1) != "*" and not m.group(1).isdigit()]


def kept_note(words):
    return (f"{', '.join(dict.fromkeys(words))} kept as typed: a blank fills only when the whole value is one blank "
            f"(help blanks)") if words else ""


def show(desk, line, ctx=None):
    """A template line as it will run, for a receipt: each blank that can be filled now shows its value; one that
    can't shows as written (the step that uses it says why)."""
    return fill(desk, line, ctx=ctx, quote=True, soft=True)


def word(desk, raw, ctx=None):
    """A verb's word as the caller said it: a whole-word blank ($new, $here.talk, $draft) is filled in the caller's
    place now, so `polish $new` means what $new means on that line. -> the value, or the Refusal to raise if the verb
    uses it. Any other word is kept as said."""
    raw = str(raw)
    if not WORD.match(raw):
        return literal(raw)
    try:
        return fill(desk, raw, ctx=ctx)
    except Refusal as e:
        return e


def made_by(events):
    """The things a line made: each create, group or link it did itself, not what a rule did after it."""
    out = []
    for e in events:
        if e["verb"] == "link" and isinstance(e.get("undo"), dict) and e["undo"].get("drop_link") \
                and not str(e.get("via") or "").startswith("rule ") and not e.get("undone"):
            out.append(e["undo"]["drop_link"])      # a3295: a link is made too; $new is its id (examine, unlink id=)
            continue
        if e["verb"] in ("create", "group") and isinstance(e.get("undo"), dict) and e["undo"].get("delete") \
                and not str(e.get("via") or "").startswith("rule ") and not e.get("undone"):
            out.append(e["undo"]["delete"])
    return out


# a1595: help blanks / help verbs live in the world now, as notes in the Help binder (helpnotes.py)
