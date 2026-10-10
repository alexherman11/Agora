"""names: the one resolver of a $name (8 Oct 2026, step 2 of the grammar unification).

A name is `$x` or `$x.part`. Before today two readers answered it: blanks.py for typed lines, verbs and rules, and
scene._fill for lenses, each with its own list of names and its own idea of a part. Now both build a Scope, a stack of
frames, and ask it. What differs between hosts is which frames are on the stack, never how a name is read.

The frames, innermost first (the first frame that claims a name answers):

    fixed      the words a host gives: in a verb $1 $2 ... $* $this; in a rule $item; in a lens $it $count $n $index
    lets       a lens's `let` names (values computed on the part)
    frames     a lens's `as` frames and host frames: $trip.title, $touched.by (only with a part)
    thing      the current thing: its fields ($title $text $kind $due $tags $id $item) then its props ($status)
    reply      $new, the thing made most recently earlier in this reply, and the handles `as=` named in this reply
    host       $me $today $session $here $house, each with parts ($me.corner, $here.talk, $house.<prop>)
    handles    $name set with `set name = ...` (sticky, outermost: anything nearer shadows it)

A part of a thing (`.title .maker .text .in .before .after .<prop>`) is read by `part_of`, the same for every host.
A host decides what a miss means: blanks refuses, naming the blanks it knows; a lens prints the word as written."""
import re

from world import Refusal

FIELDS = ("title", "text", "kind", "due", "tags", "id", "item")
PLACE = ("in", "before", "after", "text")
HOST = ("me", "today", "session", "here", "house")
PART = re.compile(r"^\.([A-Za-z_][A-Za-z0-9_-]*)$")


class Frame:
    """One frame of a scope. `kind` names it in receipts; `names` says what it claims (None: ask `has`)."""

    def __init__(self, kind, get, has=None, names=None, parts=None):
        self.kind, self._get, self._has, self.names, self._parts = kind, get, has, names, parts

    def claims(self, name):
        if self.names is not None:
            return name in self.names
        return bool(self._has and self._has(name))

    def get(self, name):
        return self._get(name)

    def part(self, name, attr):
        """A part of what `name` stands for in this frame, or None to fall back to part_of on its value."""
        return self._parts(name, attr) if self._parts else None


class Scope:
    def __init__(self, frames):
        self.frames = list(frames)      # innermost first

    def frame_for(self, name):
        for f in self.frames:
            if f.claims(name):
                return f
        return None

    def known(self):
        """Every fixed name the scope answers, for a refusal (frames with no list are left out)."""
        out = []
        for f in self.frames:
            for n in f.names or ():
                if n not in out:
                    out.append(n)
        return out


# ---------------------------------------------------------------------------------------------------------------------
# a thing's parts
# ---------------------------------------------------------------------------------------------------------------------
def thing_of(w, ident):
    """The node id and subject of a thing named by any id. -> (nid, sid or None, node or None)."""
    nid = ident
    if nid in w.subjects and nid not in w.nodes:
        apps = w.appearances_of(nid)
        if apps:
            nid = apps[0]
    n = w.nodes.get(nid)
    sid = n.get("subject") if n else (nid if nid in w.subjects else None)
    return nid, sid, n


def place_of(w, nid, p):
    """`.in` what holds a thing, `.before` and `.after` its neighbours there in reading order, `.text` its words.
    -> (value, why it has none)."""
    n = w.nodes.get(nid)
    if p == "text":
        s = w.subjects.get(n.get("subject")) if n else w.subjects.get(nid)
        if s is None or not isinstance(s.get("text"), str):
            return None, f"{nid} has no text (a note has; a chat's words are its lines)"
        return s["text"], None
    if n is None or not n.get("parent"):
        return None, f"{nid} is in nothing, so it has no {p}"
    if p == "in":
        return n["parent"], None
    ids = [k["id"] for k in w.children(n["parent"])]
    i = ids.index(nid) + (1 if p == "after" else -1)
    if not 0 <= i < len(ids):
        return None, f"{nid} is {'last' if p == 'after' else 'first'} in {n['parent']}, so nothing is {p} it"
    return ids[i], None


def part_of(w, ident, p, what="", resolve=None):
    """A part of the thing `ident` names: .title its title, .maker who made it (the actor of its create), .text its
    words, .in what holds it, .before and .after its neighbours, any other word one of its props (a person prop as the
    person's name). A part it doesn't have raises Refusal naming the thing; `what` is the written form for the message."""
    what = what or f"${ident}.{p}"
    try:
        nid = resolve(str(ident)) if resolve else str(ident)
    except Refusal:
        raise Refusal(f"{what}: {ident} names no thing, so it has no {p}")
    if nid not in w.nodes and nid not in w.subjects:
        raise Refusal(f"{what}: {ident} names no thing, so it has no {p}")
    nid, sid, n = thing_of(w, nid)
    if p == "title":
        return w.subjects[sid]["title"] if sid in w.subjects else w.title(n) if n else ""
    if p == "maker":
        import verbs
        who = verbs._author(w, sid or nid)
        if not who:
            raise Refusal(f"{what}: no one is recorded as making {nid} (it was made before this world's log began)")
        return who
    props = ((w.subjects[sid].get("props") if sid in w.subjects else (n or {}).get("props")) or {})
    if p in PLACE and not str(props.get(p) or "").strip():      # a prop of the same name is the author's, and wins
        v, why = place_of(w, nid, p)
        if why:
            raise Refusal(f"{what}: {why}")
        return v
    if p in props and str(props[p]).strip():
        import persons     # a1590: a person prop fills as the person's name: the words that, typed back, mean the same person
        return str(persons.shown(w, props[p]))
    raise Refusal(f"{what}: {nid} has no {p}= (a thing's parts are .title .maker .text, where it is .in .before .after, and its props)")


def fields_of(w, ident):
    """The fields a thing answers bare: title, text, kind, due, tags, id, item; and its props under their names."""
    nid, sid, n = thing_of(w, ident)
    s = w.subjects.get(sid) or {}
    import persons
    props = persons.shown_props(w, s.get("props") or ((n or {}).get("props") if (n or {}).get("type") == "surface" else None) or {})
    fields = {"item": nid if n else None, "id": sid or nid, "title": s.get("title", w.title(n) if n else ""), "text": s.get("text", ""),
              "kind": s.get("kind", (n or {}).get("type", "")), "due": s.get("due") or "", "tags": " ".join(s.get("tags") or [])}
    return fields, props


def thing_frame(w, ident, kind="thing"):
    """The frame of a current thing: its fields first, then its props. A part asked of a bare field name falls back
    to the thing itself (`$title` has no parts, but `$item.title` does, through the fixed frame)."""
    fields, props = fields_of(w, ident)

    def has(name):
        return name in fields or (name in props and str(props[name]).strip() != "")

    def get(name):
        return fields[name] if name in fields else props[name]
    return Frame(kind, get, has=has)


# ---------------------------------------------------------------------------------------------------------------------
# host names, the same in every host
# ---------------------------------------------------------------------------------------------------------------------
def house_of(w):
    """The house: the outermost surface of the world (its root), whose props are everyone's."""
    return getattr(w, "root", None) or next((n["id"] for n in w.nodes.values() if not n.get("parent")), None)


def host_frame(desk, ctx=None, here=None):
    """$me $today $session $here $house. `here` is a callable giving the room (blanks._here), since a rule's here is
    its home and a typed line's is where its typer stands; a lens passes its own host facts in `ctx`."""
    w = desk.world
    ctx = ctx or {}

    def get(name):
        if name == "me":
            return str(ctx.get("me") or (getattr(desk, "_ctx_me", None)) or w.me)
        if name == "today":
            today = ctx.get("today") or getattr(desk, "today", None)
            if not today:
                raise Refusal("$today is unset; clock YYYY-MM-DD sets it (clock follow keeps it on the wall date)")
            return today
        if name == "session":
            return ctx.get("session") or getattr(desk, "_session", None) or ""
        if name == "here":
            if here is None:
                raise Refusal("$here: a lens stands in no room; name the room, or read $item.in")
            return here()
        if name == "house":
            root = house_of(w)
            if not root:
                raise Refusal("$house: this world has no outermost surface")
            return root

    def parts(name, attr):
        p = attr[1:]
        what = f"${name}{attr}"
        if name in ("today", "session"):
            raise Refusal(f"{what}: ${name} has no parts")
        if name == "me":
            import persons
            import rooms
            who = get("me")
            if p == "corner":
                fid = rooms.corner_of(w, who)
                if not fid:
                    raise Refusal(f"{what}: {who} has no corner (a surface with role=resident actor={who})")
                return fid
            pid = persons.me(w, who) if persons.on(w) else None
            if pid and p == "title":
                return persons.name_now(w, pid)
            if pid:
                try:
                    return part_of(w, pid, p, what)
                except Refusal:
                    pass
            raise Refusal(f"{what}: {who} has no {p} (a person's parts are .corner, .title and the props on their person note)")
        if name == "here":
            fid = get("here")
            if p == "title":
                return w.nodes[fid]["title"]
            try:
                return part_of(w, fid, p, what)
            except Refusal:
                raise Refusal(f"{what}: {w.nodes[fid]['title']} ({fid}), the room you are in, has no {p}= "
                              f"(do prop {fid} {p}=<id> gives it one)")
        if name == "house":
            return part_of(w, get("house"), p, what)
    return Frame("host", get, names=HOST, parts=parts)


def handles_frame(vars_):
    v = vars_ or {}
    return Frame("handle", lambda n: v[n], has=lambda n: n in v)
