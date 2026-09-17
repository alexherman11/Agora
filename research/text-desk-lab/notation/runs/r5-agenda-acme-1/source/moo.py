"""Round 3: verbs as objects' property, MOO style.

Three ideas in one module:
  1. A verb registry with inheritance by kind: thing <- appearance <- note/task/image/chat, thing <- surface.
     `examine id` prints the object like a MOO room: description, then a tag line of verbs by origin.
     `help verb` prints the verb's doc, arguments and one example.
  2. Verbs of increasing complexity, all expressed as compositions of world primitives:
     tidy, split, gather, sort, reveal, dedupe, done, due, stack.  Each returns a receipt listing the primitive
     events it produced, so undo stays per primitive and the audit trail stays honest.
  3. An adapter between what the model says and what exists: synonyms, "did you mean", and a stopword-tolerant
     match. Every adapter correction is recorded so we can count how often the vocabulary gap fires.
"""

import difflib
import re

from world import Refusal

# ---------------------------------------------------------------- registry


class Verb:
    def __init__(self, name, kinds, doc, args="", example="", run=None, level=1):
        self.name, self.kinds, self.doc, self.args, self.example, self.run, self.level = name, kinds, doc, args, example, run, level


REGISTRY = {}


def verb(name, kinds, doc, args="", example="", level=1):
    def deco(fn):
        REGISTRY[name] = Verb(name, tuple(kinds), doc, args, example, fn, level)
        return fn
    return deco


KIND_CHAIN = {
    "surface": ["surface", "thing"],
    "note": ["note", "text", "appearance", "thing"],
    "task": ["task", "text", "appearance", "thing"],
    "chat": ["chat", "text", "appearance", "thing"],
    "doc": ["doc", "text", "appearance", "thing"],
    "image": ["image", "appearance", "thing"],
}


def kind_of(w, nid):
    n = w.nodes[nid]
    return "surface" if n["type"] == "surface" else w.subjects[n["subject"]]["kind"]


def verbs_by_origin(w, nid):
    """{origin kind: [verb names]} walking the chain from most specific to most general."""
    out = {}
    chain = KIND_CHAIN[kind_of(w, nid)]
    for k in chain:
        names = [v.name for v in REGISTRY.values() if k in v.kinds and _applies(w, nid, v)]
        if names:
            out[k] = names
    return out


def _applies(w, nid, v):
    n = w.nodes[nid]
    if not n["parent"] and v.name in ("move", "resize", "raise", "lower", "remove"):
        return False
    if v.name in ("untile",) and n.get("layout") == "free":
        return False
    if v.name in ("tile", "tidy", "split", "sort", "stack") and n["type"] == "surface" and not w.children(nid):
        return False
    if v.name == "unfold" and not n.get("folded"):
        return False
    if v.name == "fold" and n.get("folded"):
        return False
    return True


# ---------------------------------------------------------------- primitives (thin wrappers over World.apply)


def _prim(w, verb, nid, args):
    return w.apply(verb, nid, None, args)


@verb("move", ["thing"], "Put this somewhere else.", "into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>", "do move a04 into=f02")
def v_move(w, nid, a):
    return _prim(w, "move", nid, a)


@verb("resize", ["thing"], "Change width and height.", "to=<w>x<h>", "do resize a04 to=300x160")
def v_resize(w, nid, a):
    return _prim(w, "resize", nid, a)


@verb("raise", ["thing"], "Bring to the front of its surface.", "", "do raise a04")
def v_raise(w, nid, a):
    return _prim(w, "raise", nid, a)


@verb("lower", ["thing"], "Send to the back of its surface.", "", "do lower a04")
def v_lower(w, nid, a):
    return _prim(w, "lower", nid, a)


@verb("remove", ["thing"], "Take this appearance off the desk. The subject survives and any other appearance stays.", "", "do remove a24")
def v_remove(w, nid, a):
    return _prim(w, "remove", nid, a)


@verb("tile", ["surface"], "Lay the children out as a column or row, sharing the space, nothing overlapping.", "as=column|row", "do tile f04 as=row")
def v_tile(w, nid, a):
    return _prim(w, "tile", nid, a)


@verb("untile", ["surface"], "Back to free placement.", "", "do untile f04")
def v_untile(w, nid, a):
    return _prim(w, "untile", nid, a)


@verb("rename", ["surface"], "Change the surface's title.", "title=<str>", 'do rename f05 title="Harbor"')
def v_rename(w, nid, a):
    return _prim(w, "rename", nid, a)


@verb("group", ["surface"], "Make a new empty surface inside this one.", "title=<str> as=free|column|row", 'do group f04 title="Pictures" as=column')
def v_group(w, nid, a):
    return _prim(w, "group", nid, a)


@verb("create", ["surface"], "Make a new note, task or chat and place it on this surface.", "kind=note|task|chat title=<str> [text=<str>] [due=YYYY-MM-DD] [tags=a,b]", 'do create f03 kind=task title="Send parser" due=2026-09-19')
def v_create(w, nid, a):
    return _prim(w, "create", nid, a)


@verb("fold", ["appearance"], "Show only the title on screen.", "", "do fold a04")
def v_fold(w, nid, a):
    return _prim(w, "fold", nid, a)


@verb("unfold", ["appearance"], "Show the content on screen again.", "", "do unfold a04")
def v_unfold(w, nid, a):
    return _prim(w, "unfold", nid, a)


@verb("append", ["text"], "Add a line at the end of the text. Edits the subject: every appearance changes.", "line=<str>", 'do append a18 line="4. Review"')
def v_append(w, nid, a):
    return _prim(w, "append", nid, a)


@verb("retitle", ["text", "image"], "Change the subject's title everywhere it appears.", "title=<str>", 'do retitle a18 title="Agenda"')
def v_retitle(w, nid, a):
    return _prim(w, "retitle", nid, a)


@verb("rewrite", ["text"], "Replace all the text. Write \\n between lines. Read first; the desk refuses if it changed since.", "text=<str>", 'do rewrite a18 text="one\\ntwo"')
def v_rewrite(w, nid, a):
    return _prim(w, "rewrite", nid, a)


# ---------------------------------------------------------------- level 2: task-shaped verbs, composed


def _compose(w, steps):
    """Run (verb, nid, args) steps; return one receipt naming all events. Abort and undo on refusal."""
    events, changed = [], []
    for verb, nid, args in steps:
        try:
            r = w.apply(verb, nid, None, args)
        except Refusal as e:
            for ev in reversed(events):
                try:
                    w.undo(ev)
                except Refusal:
                    pass
            raise Refusal(f"stopped at {verb} {nid}: {e}; earlier steps undone")
        events.append(r["event"])
        changed += r.get("changed", [])
    return {"ok": True, "event": events[-1] if events else None, "events": events, "changed": sorted(set(changed))}


def _leaves(w, fid):
    out = []
    for k in w.children(fid):
        if k["type"] == "surface":
            out += _leaves(w, k["id"])
        else:
            out.append(k["id"])
    return out


def _due_key(w, aid):
    return w.subjects[w.nodes[aid]["subject"]]["due"] or "9999"


@verb("sort", ["surface"], "Reorder the children of a tiled surface.", "by=due|title|kind [desc=1]", "do sort f02 by=due", level=2)
def v_sort(w, nid, a):
    n = w.nodes[nid]
    if n["layout"] == "free":
        raise Refusal("sort needs a tiled surface; tile it first (do tile f02 as=column)")
    by = a.get("by", "due")
    kids = [k["id"] for k in w.children(nid)]
    keyf = {
        "due": lambda k: _due_key(w, k),
        "title": lambda k: w.title(w.nodes[k]).lower(),
        "kind": lambda k: kind_of(w, k),
    }.get(by)
    if not keyf:
        raise Refusal("by= must be due, title or kind")
    order = sorted(kids, key=keyf, reverse=bool(a.get("desc")))
    if order == kids:
        return {"ok": True, "event": None, "events": [], "changed": [], "note": "already in that order"}
    steps = [("move", k, {"into": nid, "at": i}) for i, k in enumerate(order)]
    r = _compose(w, steps)
    r["note"] = "order now: " + ", ".join(order)
    return r


@verb("tidy", ["surface"], "Make nothing overlap: tile the surface as a column (or row) with the current order.", "[as=column|row]", "do tidy f04", level=2)
def v_tidy(w, nid, a):
    return _compose(w, [("tile", nid, {"as": a.get("as", "column")})])


@verb("split", ["surface"], "Divide the children into two tiled groups side by side (left/right) or stacked (top/bottom) by a rule.",
      "by=kind|title|tag left=<value> [right=<value>] [as=row|column]", 'do split f04 by=kind left=image', level=3)
def v_split(w, nid, a):
    by, left = a.get("by", "kind"), a.get("left")
    if not left:
        raise Refusal("split needs left=<value> (e.g. left=image); everything else goes right")
    leaves = _leaves(w, nid)

    def matches(aid):
        s = w.subjects[w.nodes[aid]["subject"]]
        if by == "kind":
            return s["kind"] == left
        if by == "title":
            return left.lower() in s["title"].lower()
        if by == "tag":
            return left in s["tags"]
        raise Refusal("by= must be kind, title or tag")

    L = [x for x in leaves if matches(x)]
    R = [x for x in leaves if not matches(x)]
    if not L or not R:
        raise Refusal(f"split would put everything on one side ({len(L)} left, {len(R)} right)")
    steps = [("tile", nid, {"as": a.get("as", "row")})]
    r0 = _compose(w, steps)
    g1 = w.apply("group", nid, None, {"title": a.get("left_title", left.capitalize() + "s"), "as": "column"})
    g2 = w.apply("group", nid, None, {"title": a.get("right_title", "Rest"), "as": "column"})
    steps = [("move", x, {"into": g1["created"]}) for x in L] + [("move", x, {"into": g2["created"]}) for x in R]
    r = _compose(w, steps)
    w._order(nid, [g1["created"], g2["created"]])
    r["events"] = r0["events"] + [g1["event"], g2["event"]] + r["events"]
    r["created"] = f"{g1['created']} (left), {g2['created']} (right)"
    return r


@verb("gather", ["surface"], "Bring every appearance matching words into this surface (one per subject), then sort if tiled.",
      "words=<text> [by=due|title]", 'do gather f02 words=harbor by=due', level=3)
def v_gather(w, nid, a):
    words = (a.get("words") or "").lower().split()
    if not words:
        raise Refusal("gather needs words=")
    steps = []
    seen_subjects = set()
    for s in w.subjects.values():
        hay = (s["title"] + " " + s["text"] + " " + " ".join(s["tags"])).lower()
        if not all(t in hay for t in words):
            continue
        apps = w.appearances_of(s["id"])
        if not apps:
            continue
        seen_subjects.add(s["id"])
        keep = next((x for x in apps if w.nodes[x]["parent"] == nid), apps[0])
        if w.nodes[keep]["parent"] != nid:
            steps.append(("move", keep, {"into": nid}))
        for x in apps:
            if x != keep:
                steps.append(("remove", x, {}))
    if not steps and not seen_subjects:
        raise Refusal(f"nothing matches {' '.join(words)!r}")
    r = _compose(w, steps) if steps else {"ok": True, "events": [], "changed": [], "event": None}
    if a.get("by") and w.nodes[nid]["layout"] != "free":
        r2 = v_sort(w, nid, {"by": a["by"]})
        r["events"] += r2.get("events", [])
    r["note"] = f"{len(seen_subjects)} subject(s) matched; {len(steps)} step(s)"
    return r


@verb("reveal", ["appearance"], "Make this fully visible: bring it to the front (free surface) and nudge it inside its parent.", "", "do reveal a22", level=2)
def v_reveal(w, nid, a):
    n = w.nodes[nid]
    p = w.nodes[n["parent"]]
    steps = []
    if p["layout"] == "free":
        steps.append(("raise", nid, {}))
        x, y = n["x"], n["y"]
        nx = min(max(0, x), max(0, p["w"] - n["w"]))
        ny = min(max(0, y), max(0, p["h"] - n["h"]))
        if (nx, ny) != (x, y) and w.coords:
            steps.append(("move", nid, {"to": f"{nx},{ny}"}))
    if not steps:
        return {"ok": True, "event": None, "events": [], "changed": [], "note": "already visible (tiled surfaces never overlap)"}
    return _compose(w, steps)


@verb("dedupe", ["appearance"], "Keep this appearance and remove every other appearance of the same subject.", "", "do dedupe a18", level=2)
def v_dedupe(w, nid, a):
    sid = w.nodes[nid]["subject"]
    others = [x for x in w.appearances_of(sid) if x != nid]
    if not others:
        return {"ok": True, "event": None, "events": [], "changed": [], "note": "already unique"}
    r = _compose(w, [("remove", x, {}) for x in others])
    r["note"] = f"removed {', '.join(others)}; {nid} is now the only appearance"
    return r


@verb("done", ["task"], "Mark the task done (prefixes the title with a check).", "", "do done a22", level=2)
def v_done(w, nid, a):
    t = w.title(w.nodes[nid])
    if t.startswith("✓ "):
        raise Refusal("already done")
    return _prim(w, "retitle", nid, {"title": "✓ " + t})


@verb("due", ["task", "note"], "Set or clear the due date.", "on=YYYY-MM-DD | clear=1", "do due a22 on=2026-09-19", level=2)
def v_due(w, nid, a):
    s = w.subjects[w.nodes[nid]["subject"]]
    if a.get("clear"):
        new = None
    else:
        new = a.get("on")
        if not new or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", new):
            raise Refusal("due needs on=YYYY-MM-DD or clear=1")
    before = dict(s)
    s["due"] = new
    s["rev"] += 1
    for x in w.appearances_of(s["id"]):
        w._bump(x)
    ev = w._event("due", nid, a, {"restore_subject": before})
    return {"ok": True, "event": ev["id"], "events": [ev["id"]], "changed": [s["id"]] + w.appearances_of(s["id"])}


@verb("stack", ["surface"], "Pile the children neatly at the top-left, each offset a little, front to back in the current z order.", "", "do stack f04", level=2)
def v_stack(w, nid, a):
    n = w.nodes[nid]
    if n["layout"] != "free" or not w.coords:
        raise Refusal("stack needs a free surface with placement")
    steps = [("move", k["id"], {"to": f"{8 + 24 * i},{8 + 24 * i}"}) for i, k in enumerate(w.children(nid))]
    return _compose(w, steps)


# ---------------------------------------------------------------- adapter

SYNONYMS = {
    "put": "move", "place": "move", "drag": "move", "send": "move", "relocate": "move", "insert": "move", "reorder": "sort",
    "arrange": "tidy", "organize": "tidy", "organise": "tidy", "layout": "tile", "align": "tile", "clean": "tidy", "cleanup": "tidy",
    "delete": "remove", "close": "remove", "dismiss": "remove", "hide": "fold", "collapse": "fold", "expand": "unfold", "show": "unfold",
    "add": "append", "edit": "rewrite", "set": "rewrite", "title": "retitle", "name": "rename", "label": "rename",
    "create": "group", "new": "group", "make": "group", "front": "raise", "top": "raise", "back": "lower", "bottom": "lower",
    "collect": "gather", "pull": "gather", "merge": "dedupe", "unique": "dedupe", "uncover": "reveal", "expose": "reveal",
    "complete": "done", "finish": "done", "check": "done", "order": "sort", "divide": "split", "separate": "split", "partition": "split",
    "scale": "resize", "shrink": "resize", "grow": "resize", "enlarge": "resize",
}


class Adapter:
    """Map what the model said to a verb that exists on that object. Records every correction."""

    def __init__(self):
        self.log = []

    def resolve(self, w, said, nid):
        said = said.lower().strip("@")
        avail = [v for vs in verbs_by_origin(w, nid).values() for v in vs]
        if said in avail:
            return said, None
        cand = SYNONYMS.get(said)
        note = None
        if cand and cand in avail:
            note = f"(you said {said}; that is {cand} here)"
        else:
            close = difflib.get_close_matches(said, avail, n=1, cutoff=0.75)
            if close:
                cand, note = close[0], f"(you said {said}; taking it as {close[0]})"
            elif cand:
                raise Refusal(f"{said} would mean {cand}, but {nid} has no {cand}. Its verbs: {' '.join(avail)}. help <verb> explains one.")
            else:
                sugg = difflib.get_close_matches(said, list(REGISTRY) + list(SYNONYMS), n=3, cutoff=0.5)
                hint = f" did you mean {', '.join(sugg)}?" if sugg else ""
                raise Refusal(f"{nid} has no verb {said}.{hint} Its verbs: {' '.join(avail)}. examine {nid} or help <verb>.")
        self.log.append({"said": said, "used": cand, "target": nid})
        return cand, note
