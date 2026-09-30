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
    a part of the thing a blank names (a1027): .title its title, .maker who made it, .<prop> one of its props
                   ($item.asked_by, $1.status); a part it doesn't have refuses, naming the thing

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

from world import Refusal

LIT = ""          # a \$ in the line, kept out of shlex's way until it lands in a value as a plain $
BLANK = re.compile(re.escape(LIT) + r"|\$(\*|\d+|[A-Za-z_][A-Za-z0-9_]*)((?:\.[A-Za-z_][A-Za-z0-9_-]*)?)")
WORD = re.compile(r"^\$(\d+|[A-Za-z_][A-Za-z0-9_]*)(\.[A-Za-z_][A-Za-z0-9_-]*)?$")
READS = ("look", "read", "examine", "x", "ex", "find", "table", "why", "compare", "history", "go", "where", "pivot",
         "verbs", "open", "close", "set")       # typed commands whose words name things: filled as values

KNOWN = ("$here $here.<prop> $new $today $me, a handle you set ($name); in a verb $1 $2 $* $this; in a rule $item; "
         "a thing's parts .title .maker .<prop>")


class Ctx:
    """Where a line is being filled. kind: typed | verb | script | rule."""

    def __init__(self, kind, args=None, rest="", me=None, this=None, item=None, name="", prev=None, home=None):
        self.kind, self.args, self.rest, self.me, self.this, self.item, self.name = kind, args, rest, me, this, item, name
        self.prev = prev        # what was made most recently earlier at this level of this reply (None: nothing yet)
        self.home = home        # a990: the room a template lives in (its bare words are looked up there), or None

    @property
    def template(self):
        return self.kind != "typed"


def protect(line):
    """Before a line is split into words: every \\$ becomes LIT, so no parser eats the backslash."""
    return (line or "").replace("\\$", LIT)


def literal(text):
    return str(text).replace(LIT, "$")


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


def _one(desk, ctx, name, attr):
    """The value of one blank, or a Refusal. attr is '' or '.<word>'."""
    w = desk.world
    what = "$" + name + attr
    if name.isdigit():
        k = int(name)
        if ctx.args is None or k < 1:
            raise Refusal(f"{what} stands for a word after a verb or script; there are none here")
        if k > len(ctx.args):
            raise Refusal(f"{ctx.name or 'this'} needs {k} word(s) after it; got {len(ctx.args)}"
                          + (f". help {ctx.name}" if ctx.name else ""))
        val = ctx.args[k - 1]
        if isinstance(val, Refusal):
            raise val
        return _part(desk, val, attr, what) if attr else val
    if name == "here":
        fid = _here(desk, ctx, name)
        if not attr:
            return fid
        p = attr[1:]
        props = w.nodes[fid].get("props") or {}
        if p in props and str(props[p]).strip():
            return str(props[p])
        if p == "title":
            return w.nodes[fid]["title"]
        raise Refusal(f"{what}: {w.nodes[fid]['title']} ({fid}), the room you are in, has no {p}= "
                      f"(do prop {fid} {p}=<id> gives it one)")
    if name == "new":
        if ctx.kind == "rule":
            raise Refusal("$new: a rule has no earlier line; it acts on $item, the thing it fired on")
        if not ctx.prev:
            where = "this verb's earlier steps" if ctx.kind == "verb" else "this reply"
            raise Refusal(f"$new names the thing made most recently earlier in this reply, and nothing earlier in "
                          f"{where} made anything (a new reply starts fresh). Use the id a receipt printed")
        val = ctx.prev[-1]              # a line that made several: the last (Juniper, a806 (10))
        desk._filled_new = val
    elif name == "item":
        if ctx.kind != "rule" or not ctx.item:
            raise Refusal("$item stands for the target: the thing a rule fired on, or the thing a lens gesture acts on. "
                          "Did you mean $new, the thing made most recently in this reply?")
        val = ctx.item
    elif name == "this":
        if ctx.kind != "verb":
            raise Refusal("$this is the thing a verb lives on; it has a value only inside a verb")
        if not ctx.this:
            raise Refusal(f"{ctx.name} says $this but lives on no thing")
        val = ctx.this
    elif name == "today":
        today = getattr(desk, "today", None)
        if not today:
            raise Refusal("$today is unset; clock YYYY-MM-DD sets it (clock follow keeps it on the wall date)")
        if attr:
            raise Refusal(f"{what}: $today has no parts")
        return today
    elif name == "me":
        val = ctx.me or w.me
        if attr:
            raise Refusal(f"{what}: $me has no parts")
        return str(val)
    elif name in (getattr(desk, "vars", None) or {}):
        val = desk.vars[name]
    else:
        raise Refusal(f"${name} is no blank here. Blanks: {KNOWN}. A literal dollar sign is written \\$")
    return _part(desk, val, attr, what) if attr else val


def _part(desk, val, attr, what):
    """A part of the thing a blank names (a1027): .title its title, .maker who made it (the actor of its create), any
    other word one of its props, as $here.<prop> is of a room. A part it doesn't have refuses, naming the thing."""
    if attr == ".title":
        return _title(desk, val)
    w, p = desk.world, attr[1:]
    try:
        nid = desk._resolve(str(val))
    except Refusal:
        raise Refusal(f"{what}: {val} names no thing, so it has no {p}")
    sid = w.nodes[nid].get("subject") if nid in w.nodes else nid
    if p == "maker":
        import verbs
        who = verbs._author(w, sid or nid)
        if not who:
            raise Refusal(f"{what}: no one is recorded as making {nid} (it was made before this world's log began)")
        return who
    props = ((w.subjects[sid].get("props") if sid in w.subjects else w.nodes[nid].get("props")) or {})
    if p in props and str(props[p]).strip():
        return str(props[p])
    raise Refusal(f"{what}: {nid} has no {p}= (a thing's parts are .title, .maker and its props)")


def fill(desk, value, text=False, ctx=None, quote=False, soft=False):
    """Fill every blank in one value, in one pass: what a blank becomes is never read again. text=True: the value is
    words a person wrote (line=, text=, title=), filled only inside a template. quote=True: the value is still desk
    words (a read command's arguments), so a filled value with a space is quoted, and one inside quotes is escaped.
    soft=True (a receipt's echo): a blank that can't be filled stays as written instead of refusing."""
    ctx = ctx or ctx_of(desk)
    value = str(value)
    if text and not ctx.template:
        return literal(value)

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
    kind = arg_kinds(verb).get(key, "prop")
    if kind == "prose" or (kind == "prop" and not WORD.match(str(value))):
        return literal(value)
    return fill(desk, value)


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
    """The things a line made: each create or group it did itself, not what a rule did after it."""
    out = []
    for e in events:
        if e["verb"] in ("create", "group") and isinstance(e.get("undo"), dict) and e["undo"].get("delete") \
                and not str(e.get("via") or "").startswith("rule ") and not e.get("undone"):
            out.append(e["undo"]["delete"])
    return out


HELP = """blanks: words beginning with $ that the desk fills with a value when the line runs.
  $here          the room you are in; $here.<prop> a prop of it: $here.talk its chat, $here.describe its note
                 (in a rule: the room the rule lives in, where its author saved it)
  $new           the thing made most recently earlier in this reply (a note, task, surface, view ...; if one line
                 made several, the last). Only this reply: in a reply where nothing was made yet it refuses and
                 says why. The receipt ends ($new = <id>), so you see which thing it was
  $today         the clock's date          $me   who you are          $<name>   a handle (help handles)
  in a verb: $1 $2 .. its words, $* the rest of the line exactly as said, $this the thing a verb lives on
  in a rule: $item the thing it fired on
  parts of a thing a blank names ($1 $item $new $this or a handle): .title its title, .maker who made it, .<prop>
                 one of its props ($item.asked_by); a part it doesn't have refuses
  Text is words by default: an argument a verb declares as text (help append: line=<str>; old= new= title= text=)
  is never filled in a typed line, so a chat line about $here keeps its words. Targets, selections and ids are
  filled: do move a12 into=$here. A prop value fills only when the whole value is one blank (do prop f581
  describe=$new); a blank inside other words (next="check $today") stays as typed. Inside a verb, a script or a rule (templates their author wrote), text values are filled
  too, once: what a blank becomes is never filled again. A literal dollar sign is \\$, in both.
  A blank that can't be filled refuses; nothing stores a blank's own name. A receipt shows the value, not the blank.
  e.g. do create $here kind=note title=Plan   then   do link $new $here.describe"""
