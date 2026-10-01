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
from copy import deepcopy

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
    "trial": ["trial", "text", "appearance", "thing"],
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
    if n.get("layout") == "view" and v.name in ("tile", "untile", "group", "create", "sort", "tidy", "split", "stack"):
        return False   # a view holds nothing of its own
    if v.name in ("tile", "tidy", "split", "sort", "stack") and n["type"] == "surface" and not w.children(nid):
        return False
    if v.name == "unfold" and not n.get("folded"):
        return False
    if n["type"] == "appearance":
        s = w.subjects[n["subject"]]
        if v.name == "resolve" and not any(not c["resolved"] for c in s["comments"]):
            return False
        if v.name == "check" and not w.checklist(s["text"]):
            return False
        if v.name == "unlink" and not w.links_of(s["id"]):
            return False
    if v.name == "fold" and n.get("folded"):
        return False
    return True


# ---------------------------------------------------------------- primitives (thin wrappers over World.apply)


def _prim(w, verb, nid, args):
    return w.apply(verb, nid, None, args)


@verb("move", ["thing"], "Put this somewhere else.", "into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>", "do move a04 into=f02")
def v_move(w, nid, a):
    was = in_trash(w, nid)
    r = _prim(w, "move", nid, a)
    return with_untrash(w, nid, r, was)


# a1327 (Pike e2979, e3086; Sable e3080): a Trash is a surface with prop trash=yes; the house's trash verb (a1174) moves
# into it. What is inside one is left out of every selection that doesn't name it (knife.parse_selection), and a thing
# moved out of it is live again: status=trashed goes, and a task's status is open.
def trash_surfaces(w):
    return [n["id"] for n in w.nodes.values() if n["type"] == "surface" and (n.get("props") or {}).get("trash") == "yes"]


def in_trash(w, nid, bins=None):
    bins = trash_surfaces(w) if bins is None else bins
    return nid in w.nodes and any(w._is_inside(nid, t) for t in bins)


def with_untrash(w, nid, r, was):
    """After a move of `nid` that was in a Trash (`was`): if it (and every other appearance of its subject) is out now
    and still says status=trashed, one more step clears it, as the same command, so undo takes both back."""
    n = w.nodes.get(nid)
    if not was or not r.get("event") or not n or in_trash(w, nid):
        return r
    if n["type"] == "appearance" and any(in_trash(w, x) for x in w.appearances_of(n["subject"])):
        return r
    if props_of(w, nid).get("status") != "trashed":
        return r
    task = n["type"] == "appearance" and w.subjects[n["subject"]]["kind"] == "task"
    p = v_prop(w, nid, {"status": "open"} if task else {"remove": "status"})
    note = "out of the Trash: " + ("status=open (was trashed)" if task else "status=trashed removed")
    return dict(r, events=(r.get("events") or [r["event"]]) + [p["event"]],
                changed=sorted(set(r.get("changed", [])) | set(p.get("changed", []))),
                note="; ".join(x for x in (r.get("note"), note) if x))


@verb("place", ["subject"], "Put a subject on a surface as a new appearance; its other appearances stay where they are.",
      "into=<surface>", "do place s10 into=f02")
def v_place(w, sid, a):
    return w.apply("place", sid, None, a)


MOVE_ARGS = ("into", "before", "after", "to", "by")


@verb("put", ["task"], "Put a card in a lane's order: above=<card> gives it that card's status and priority and a rank just "
      "above it; status=<value> sends it to the bottom of its priority group among cards with that status. The ranks are "
      "the house's; one event, undone whole. With into=, before=, after=, to= or by= it is move, as put is everywhere else.",
      "above=<card> | status=<value>", "do put a12 above=a30")
def v_put(w, nid, a):
    # Pike c1202: its own word, so place keeps one meaning. `put` was already a synonym of move, and still is for
    # anything that isn't a card, and for a card given a move's arguments
    if any(k in a for k in MOVE_ARGS):
        return v_move(w, nid, a)
    return place_in_order(w, nid, a)


# a1069/a1078: a lane is a selection sorted `by priority, rank`. The lens word and the verb order a group with this one
# key, so the card the verb calls "above" is the card the person saw above.
RANK_STEP = 1000


def order_value(v):
    """Numbers ascending, then words, then a missing value last."""
    if v is None or v == "":
        return (2, 0, "")
    try:
        return (0, float(v), "")
    except (TypeError, ValueError):
        return (1, 0, str(v).lower())


def props_of(w, i):
    n = w.nodes.get(i)
    if n is not None:
        return (n.get("props") if n["type"] == "surface" else w.subjects[n["subject"]].get("props")) or {}
    return (w.subjects[i].get("props") or {}) if i in w.subjects else {}


def order_by(w, ids, keys):
    """`ids` in the order of `keys` (props); a stable sort, so ties keep the order they came in: for a selection, the
    order the appearances were made."""
    return sorted(ids, key=lambda i: tuple(order_value(props_of(w, i).get(k)) for k in keys))


def _lane_group(w, status, priority, leave_out):
    """The cards sharing a status and a priority, one per subject, in the order a lane sorted `by priority, rank` shows."""
    seen, out = set(leave_out), []
    for n in w.nodes.values():
        if n["type"] != "appearance" or not n["parent"] or n.get("subject") in seen:
            continue
        s = w.subjects[n["subject"]]
        p = s.get("props") or {}
        if s["kind"] == "task" and p.get("status") == status and p.get("priority") == priority:
            seen.add(s["id"])
            out.append(n["id"])
    return order_by(w, out, ["rank"])


def place_in_order(w, nid, a):
    actor = a.pop("_by", None) or w.me
    sid = w.nodes[nid]["subject"]
    s = w.subjects[sid]
    if s["kind"] != "task":
        raise Refusal(f"put above= orders cards; {nid} is a {s['kind']}")
    above = a.get("above")
    if above:
        if above not in w.nodes or w.nodes[above]["type"] != "appearance" or w.subjects[w.nodes[above]["subject"]]["kind"] != "task":
            raise Refusal(f"put {nid} above=<card>: {above} is not a card (a task's appearance)")
        if w.nodes[above]["subject"] == sid:
            raise Refusal(f"{above} is {nid} itself (the same task); nothing to do")
        tp = w.subjects[w.nodes[above]["subject"]].get("props") or {}
        status, priority = tp.get("status"), tp.get("priority")
    elif a.get("status"):
        status, priority = str(a["status"]), (s.get("props") or {}).get("priority")
    else:
        raise Refusal("put needs above=<card>, or status=<value> (the bottom of its priority group); into=, before= or after= moves it, as move does")
    group = _lane_group(w, status, priority, {sid})
    ranks = {i: props_of(w, i).get("rank") for i in group}
    new = {}                                           # subject -> rank, for the others the house renumbers

    def num(i):
        v = new.get(w.nodes[i]["subject"], ranks[i])
        return int(float(v))

    def renumber(upto):
        for k, i in enumerate(upto, 1):
            if order_value(ranks[i])[0] != 0 or int(float(ranks[i])) != k * RANK_STEP:
                new[w.nodes[i]["subject"]] = str(k * RANK_STEP)
    if above:
        at = group.index(next(i for i in group if w.nodes[i]["subject"] == w.nodes[above]["subject"]))
        prev = group[at - 1] if at else None
        ok = order_value(ranks[group[at]])[0] == 0 and (prev is None or (order_value(ranks[prev])[0] == 0 and num(group[at]) - num(prev) >= 2))
        if not ok:
            renumber(group[:at + 1])
        rank = (num(prev) + num(group[at])) // 2 if prev is not None else num(group[at]) - RANK_STEP
    else:
        if any(order_value(r)[0] != 0 for r in ranks.values()):
            renumber(group)
        rank = (num(group[-1]) + RANK_STEP) if group else RANK_STEP
    mine = s.get("props") or {}
    want = {"status": status, "priority": priority, "rank": str(rank)}
    was = {k: mine.get(k) for k in want}
    if not new and all(was[k] == want[k] for k in ("status", "priority")) and order_value(was["rank"])[0] == 0 \
            and (not group or (above and at == 0 and num(group[0]) > int(float(was["rank"])))
                 or (above and at and num(group[at - 1]) < int(float(was["rank"])) < num(group[at]))
                 or (not above and int(float(was["rank"])) > num(group[-1]))):
        # a825 (Pike c1202): a drop where the card already is harms nothing, so it is not refused; no event is made
        return {"ok": True, "event": None, "events": [], "changed": [],
                "note": f"already there, nothing moved (status={status or '(none)'}, priority={priority or '(none)'}, rank {was['rank']})"}
    before = [deepcopy(s)] + [deepcopy(w.subjects[x]) for x in new]
    props = s.setdefault("props", {})
    for k, v in want.items():
        if v is None:
            props.pop(k, None)
        else:
            props[k] = v
    for x, r in new.items():
        w.subjects[x].setdefault("props", {})["rank"] = r
    changed = []
    for x in [sid, *new]:
        w.subjects[x]["rev"] += 1
        for ap in w.appearances_of(x):
            w._bump(ap)
        changed += [x] + w.appearances_of(x)
    args = {"above": above} if above else {}
    args.update({k: (v if v is not None else "") for k, v in want.items()})
    ev = w._event("put", nid, args, {"restore_subjects": before}, actor)
    said = [f"{k} {was[k] or '(none)'} -> {want[k] or '(none)'}" for k in ("status", "priority") if was[k] != want[k]]
    where = f"just above {above}" if above else f"at the bottom of {'priority ' + priority if priority else 'the cards with no priority'}"
    note = f"put {nid} {where} with status={status or '(none)'}" + (f", priority={priority}" if priority else ", no priority")
    note += ("; " + ", ".join(said) if said else "") + f"; rank {was['rank'] or '(none)'} -> {rank}"
    if new:
        note += f"; renumbered {len(new)} other card(s) quietly, their order unchanged: " + " ".join(
            (w.appearances_of(x) or [x])[0] for x in sorted(new, key=lambda x: int(new[x])))
    return {"ok": True, "event": ev["id"], "changed": changed, "note": note}


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


@verb("create", ["surface"], "Make a new note, task, chat, doc, image or surface inside this surface.", "kind=note|task|chat|doc|image|surface title=<str> [text=<str>] [due=YYYY-MM-DD] [tags=a,b] [layout=column|row|free] [query=<selection> for kind=view] [any other key: a prop]", 'do create f03 kind=task title="Send parser" due=2026-09-19')
def v_create(w, nid, a):
    return _prim(w, "create", nid, a)


@verb("fold", ["appearance"], "Show only the title on screen.", "", "do fold a04")
def v_fold(w, nid, a):
    return _prim(w, "fold", nid, a)


@verb("unfold", ["appearance"], "Show the content on screen again.", "", "do unfold a04")
def v_unfold(w, nid, a):
    return _prim(w, "unfold", nid, a)


@verb("append", ["text"], "Add a line at the end of the text. Edits the subject: every appearance changes. "
      "On a chat the world signs the line with your name (type only your words; a 'Name:' of your own is dropped), "
      "and adding a line is never refused as stale, since it replaces nothing; rewriting a chat is still fenced.",
      "line=<str>", 'do append a18 line="4. Review"')
def v_append(w, nid, a):
    return _prim(w, "append", nid, a)


CHAT_RULES = ("the world signs each line with who added it (type only your words); adding a line is never refused "
              "as stale, rewriting the chat is")


def unanswered(w, sid, me="alex"):
    """Lines at the end of a chat that were not written by us."""
    lines = [l for l in w.subjects[sid]["text"].splitlines() if l.strip()]
    out = []
    for l in reversed(lines):
        said = w.SPEAKER.match(l)
        if not said or said.group(1).lower() == me:
            break   # ours: signed by us, or unsigned
        out.append(l)
    return list(reversed(out))


@verb("reply", ["chat"], "Answer the latest message(s) in this chat. The receipt names what you answered.", "line=<str>", 'do reply a27 line="On it. Found Tide data format and Parser notes."')
def v_reply(w, nid, a):
    line = str(a.get("line", a.get("text", ""))).strip()
    if not line:
        raise Refusal("reply needs line=")
    # F1: the chat signs a line with its actor (world.apply, Juniper a484); reply no longer signs it "Alex" for everyone,
    # and what it answers is judged for the one replying
    sid = w.nodes[nid]["subject"]
    pending = unanswered(w, sid, str(w.me or "alex").lower())
    r = _prim(w, "append", nid, {"line": line})
    r["note"] = ("answered: " + " | ".join(pending)) if pending else "no unanswered message; appended anyway"
    return r


@verb("comment", ["appearance"], "Leave a comment on this thing, signed by you. Comments show under read.", "line=<str>", 'do comment a20 line="Which timezone?"')
def v_comment(w, nid, a):
    return _prim(w, "comment", nid, a)


@verb("resolve", ["appearance"], "Close a comment on this thing, optionally with a reply.", "id=<cNN> [line=<str>]", 'do resolve a20 id=c03 line="UTC, per the parser notes."')
def v_resolve(w, nid, a):
    return _prim(w, "resolve", nid, a)


@verb("check", ["text"], "Tick (or untick) the n-th checklist line of this thing.", "item=<n>", "do check a22 item=2")
def v_check(w, nid, a):
    return _prim(w, "check", nid, a)


@verb("link", ["appearance"], "Connect this thing to another: blocks, refers, answers or part-of. Links show in examine.", "to=<id> as=blocks|refers|answers|part-of", "do link a20 to=a30 as=refers")
def v_link(w, nid, a):
    return _prim(w, "link", nid, a)


@verb("unlink", ["appearance"], "Remove a link by id.", "id=<lNN>", "do unlink a20 id=l02")
def v_unlink(w, nid, a):
    return _prim(w, "unlink", nid, a)


@verb("retitle", ["text", "image"], "Change the subject's title everywhere it appears.", "title=<str>", 'do retitle a18 title="Agenda"')
def v_retitle(w, nid, a):
    return _prim(w, "retitle", nid, a)


@verb("rewrite", ["text"], "Replace all the text. Write \\n between lines. Read first; the desk refuses if it changed since.", "text=<str>", 'do rewrite a18 text="one\\ntwo"')
def v_rewrite(w, nid, a):
    return _prim(w, "rewrite", nid, a)


@verb("replace", ["text"], "Change one exact passage of the text, leaving the rest. old must appear exactly once: include enough "
      "of the words around it. Write \\n between lines. Read first; the desk refuses if it changed since.",
      "old=<str> new=<str>", 'do replace a18 old="2. Draft" new="2. Draft, then review"')
def v_replace(w, nid, a):
    return _prim(w, "replace", nid, a)


# ---------------------------------------------------------------- level 2: task-shaped verbs, composed


def _compose(w, steps):
    """Run (verb, nid, args) steps; return one receipt naming all events. Abort and undo on refusal."""
    events, changed = [], []
    for verb, nid, args in steps:
        was = verb == "move" and in_trash(w, nid)
        try:
            try:
                r = w.apply(verb, nid, None, args)
                if was:
                    r = with_untrash(w, nid, r, was)
            except Refusal as e:
                if "is not a verb of" in str(e) and verb in REGISTRY:   # registry verbs (tag, prop, due ...) over a selection
                    r = REGISTRY[verb].run(w, nid, dict(args))
                else:
                    raise
        except Refusal as e:
            for ev in reversed(events):
                try:
                    w.undo(ev)
                except Refusal:
                    pass
            raise Refusal(f"stopped at {verb} {nid}: {e}; earlier steps undone")
        events += r["events"] if was and r.get("events") else [r["event"]]
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
        x, y, bw, bh = w.box(nid)
        _, _, pw, ph = w.box(n["parent"])
        nx = min(max(0, x), max(0, pw - bw))
        ny = min(max(0, y), max(0, ph - bh))
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


@verb("prop", ["appearance", "surface"], "Set or clear named properties on this thing (k=v ...; remove=k). prop:k=v selects by them. "
      "On a view, query=<selection> changes what it shows. A field kept elsewhere (title text kind due tags) is refused, naming its verb.",
      "k=v ... | remove=k","do prop a12 model=gpt-5.6-sol status=queued")
def v_prop(w, nid, a):
    actor = a.pop("_by", None) or w.me
    here = str(a.pop("at", "")) == "appearance"
    view = w.nodes[nid].get("layout") == "view"
    for k in a:
        why = _field(w, nid, k, view)
        if why:
            raise Refusal(why)
    if view and "query" in a:
        return _requery(w, nid, a, actor)
    if w.nodes[nid]["type"] == "surface" or here:
        # a surface has no subject: its properties (owner=alex ...) live on the surface itself.
        # at=appearance puts them on this one appearance instead of on the subject every appearance shares.
        node = w.nodes[nid]
        props = node.setdefault("props", {})
        rem = [k for k in str(a.pop("remove", "")).split(",") if k.strip()]
        if not a and not rem:
            raise Refusal("prop needs k=v and/or remove=k")
        if all(props.get(k) == str(v) for k, v in a.items()) and not [k for k in rem if k in props]:
            raise Refusal(f"{nid} already has that; props now: " + (" ".join(f"{k}={v}" for k, v in props.items()) or "(none)"))
        before = dict(props)
        for k in rem:
            props.pop(k, None)
        for k, v in a.items():
            props[k] = str(v)
        w._bump(nid)
        ev = w._event("prop", nid, dict(a, **({"remove": ",".join(rem)} if rem else {})), {"restore_props": (nid, before)}, actor)
        return {"ok": True, "event": ev["id"], "changed": [nid],
                "note": "props now: " + (" ".join(f"{k}={v}" for k, v in props.items()) or "(none)")}
    s = w.subjects[w.nodes[nid]["subject"]]
    props = s.setdefault("props", {})
    rem = [k for k in str(a.pop("remove", "")).split(",") if k.strip()]
    if not a and not rem:
        raise Refusal("prop needs k=v and/or remove=k")
    absent = [k for k in rem if k not in props]
    if absent and not a and len(absent) == len(rem):
        raise Refusal(f"no prop {', '.join(absent)} on {nid}; props now: " + (" ".join(f"{k}={v}" for k, v in props.items()) or "(none)"))
    if all(props.get(k) == str(v) for k, v in a.items()) and not [k for k in rem if k in props]:
        raise Refusal(f"{nid} already has " + " ".join(f"{k}={v}" for k, v in a.items()) + "; nothing to change")
    before = deepcopy(s)      # a whole copy: a shallow one shared tags and comments with later changes, and undo restored those
    for k in rem:
        props.pop(k, None)
    for k, v in a.items():
        props[k] = str(v)
    s["rev"] += 1
    for x in w.appearances_of(s["id"]):
        w._bump(x)
    ev = w._event("prop", nid, dict(a, **({"remove": ",".join(rem)} if rem else {})), {"restore_subject": before}, actor)
    return {"ok": True, "event": ev["id"], "changed": [s["id"]] + w.appearances_of(s["id"]),
            "note": "props now: " + (" ".join(f"{k}={v}" for k, v in props.items()) or "(none)")}


def _field(w, nid, k, view):
    """a1322 (Juniper c1393): a prop named like a field the house keeps elsewhere is refused, naming the verb that
    changes the field. An ok there stored a shadow prop that nothing reads. remove= still clears an old one."""
    n = w.nodes[nid]
    surface = n["type"] == "surface"
    what = "a view" if view else "a surface" if surface else f"a {w.subjects[n['subject']]['kind']}"
    if k == "title":
        return f"title is not a prop: do {'rename' if surface else 'retitle'} {nid} title=<str> changes the title"
    if k == "text":
        if surface:
            return f"text is not a prop, and {nid} is {what}: it has a title (do rename) but no text"
        return (f"text is not a prop: do rewrite {nid} text=<str> changes the text (or replace old= new=, "
                f"append line=)")
    if k == "kind":
        return f"kind is not a prop: {nid} is {what}, set when it was made; no verb changes it (make a new one)"
    if k == "due":
        return f"due is not a prop: do due {nid} on=YYYY-MM-DD (or clear=1) changes the date"
    if k == "tags":
        return f"tags is not a prop: do tag {nid} add=a,b (or remove=a,b) changes the tags"
    if k == "of":
        return (f"of is how a view reads aloud, not a prop: do prop {nid} query=<selection> changes what it shows"
                if view else f"of is not a prop: a view reads 'of <selection>'; {nid} is {what}, not a view")
    if k == "query" and not view:
        return (f"query is a view's selection, not a prop; {nid} is {what}, not a view "
                f"(do create <surface> kind=view title=<str> query=<selection>)")
    return None


def _requery(w, nid, a, actor):
    """a1322: prop query= on a view changes its selection; the next look evaluates the new one. Other k=v on the same
    line are props, as ever. The desk judged the selection first (desk_knife._check_view_query)."""
    n = w.nodes[nid]
    a = dict(a)             # the caller's k=v stay whole: its receipt echoes query=, and marks prop:query seen
    q = str(a.pop("query")).strip()
    if not q:
        raise Refusal("a view needs query=<selection>, e.g. query=kind:task,due<today")
    props = n.setdefault("props", {})
    rem = [k for k in str(a.pop("remove", "")).split(",") if k.strip()]
    if q == n.get("query") and all(props.get(k) == str(v) for k, v in a.items()) and not [k for k in rem if k in props]:
        raise Refusal(f"{nid} already shows {q}; nothing to change")
    before, was = deepcopy(n), n.get("query")
    n["query"] = q
    for k in rem:
        props.pop(k, None)
    for k, v in a.items():
        props[k] = str(v)
    w._bump(nid)
    ev = w._event("prop", nid, dict(a, query=q, **({"remove": ",".join(rem)} if rem else {})), {"restore": before}, actor)
    return {"ok": True, "event": ev["id"], "changed": [nid], "note": f"selection was {was}; now {q}"}


@verb("tag", ["appearance"], "Add or remove tags on this thing's subject. Tags are what tag: selects and rules watch.",
      "add=a,b | remove=a,b", "do tag a22 add=harbor,urgent")
def v_tag(w, nid, a):
    s = w.subjects[w.nodes[nid]["subject"]]
    add = [t for t in str(a.get("add", "")).split(",") if t.strip()]
    rem = [t for t in str(a.get("remove", "")).split(",") if t.strip()]
    if not add and not rem:
        raise Refusal("tag needs add=a,b and/or remove=a,b")
    before = deepcopy(s)      # (shared props: undoing a tag after a later prop brought the prop back)
    s["tags"] = [t for t in s["tags"] if t not in rem] + [t for t in add if t not in s["tags"]]
    s["rev"] += 1
    for x in w.appearances_of(s["id"]):
        w._bump(x)
    ev = w._event("tag", nid, a, {"restore_subject": before})
    return {"ok": True, "event": ev["id"], "changed": [s["id"]] + w.appearances_of(s["id"]),
            "note": "tags now: " + (",".join(s["tags"]) or "(none)")}


@verb("due", ["task", "note"], "Set or clear the due date.", "on=YYYY-MM-DD | clear=1", "do due a22 on=2026-09-19", level=1)
def v_due(w, nid, a):
    s = w.subjects[w.nodes[nid]["subject"]]
    if a.get("clear"):
        new = None
    else:
        new = a.get("on")
        if not new or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", new):
            raise Refusal("due needs on=YYYY-MM-DD or clear=1")
    before = deepcopy(s)
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
    "put": "move", "drag": "move", "send": "move", "relocate": "move", "insert": "move", "reorder": "sort",
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
        if said in REGISTRY and SYNONYMS.get(said) not in avail:     # a1081: put is a card's verb and, elsewhere, move
            raise Refusal(f"{said} does not apply to {nid} right now (its verbs: {' '.join(avail)}); "
                          + {"resolve": "it has no open comments", "check": "it has no checklist lines", "unlink": "it has no links",
                             "untile": "it is not tiled", "sort": "it is not a tiled surface with children"}.get(said, "see examine " + nid))
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
