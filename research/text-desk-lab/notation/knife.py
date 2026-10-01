"""Round 7: knives, not avocado slicers.

General verbs over general targets. A target is one id, a selection, or (for pair verbs) two ids.

Selections (one token; quote it if it has spaces, or join terms with commas):
  ?tide+parser      subjects whose title/text/tags contain all the words
  kind:image        kind (several: kind:note|task)
  tag:harbor        tag
  in:f04            inside surface f04 (recursively)
  hidden            more than 5% covered
  also:a18          the other appearances of a18's subject
  due<2026-09-20    due before (or due>)
  a20,a22           an explicit list
  terms combine with AND:  kind:image,in:f04   or  "kind:image in:f04"

Verbs (all take an id or a selection unless noted):
  move   into= | before= | after= | to= | by=    [one=1 keeps one appearance per subject]
  remove, raise, lower, fold, unfold, resize to=, retitle title=, append line=
  group  as=column|row|free title=  [in=fXX]   a new surface around the selection (pair/many verb)
  swap A B          exchange positions (or order, if tiled)
  beside A B        put A right after B, in B's surface
  match A to=B      give A B's size
  sort, tile, untile, rename, create   (surfaces, unchanged)
"""

import re

import moo
from world import Refusal

SPECIALIZED = {"split", "gather", "dedupe", "reveal", "reply", "tidy", "stack", "done"}   # due and tag are property setters: general
GENERAL = [n for n in moo.REGISTRY if n not in SPECIALIZED]


def _leaves(w, fid):
    out = []
    for k in w.children(fid):
        if k["type"] == "surface":
            out += [k["id"]] + _leaves(w, k["id"])
        else:
            out.append(k["id"])
    return out


def parse_selection(w, token, trash=False):
    """Return (ids, description) or None if token is a plain id. What is inside a Trash (moo.trash_surfaces) is left out
    unless an in: term names the Trash or a surface inside it, or trash=True (a1327)."""
    token = token.strip().strip('"')
    if token in w.nodes or token in w.subjects or token in ("desk", "root") or token.lower().startswith("corner:"):
        return None     # corner:<name> is one thing, a resident's corner (a1027), not a selection
    terms = [t for t in re.split(r"[,\s]+", token) if t]
    if all(t in w.nodes for t in terms) and len(terms) > 1:
        return terms, "list " + ",".join(terms)
    KNOWN = ("kind:", "tag:", "in:", "also:", "prop:", "title:", "comments:", "links:", "parts:", "part-of:", "answers:",
             "answered-by:", "unanswered:")
    for t in terms:
        # Moss: an unknown term fell back to a text search in find and to nothing in scene: two wrong answers, no refusal
        if re.match(r"^-?[a-z]+:\S", t) and not t.lstrip("-").startswith(KNOWN):
            raise Refusal(f"no selection term {t.split(':')[0].lstrip('-')}: (terms: ?words {' '.join(KNOWN)} due< due> age< age> hidden; help selections)")
    neg = [t[1:] for t in terms if t.startswith("-") and len(t) > 1]   # -tag:fixed: everything the term would select is left out
    terms = [t for t in terms if not t.startswith("-")]
    if not (terms or neg) or not any(t.startswith(("?", "kind:", "tag:", "in:", "also:", "due<", "due>", "age<", "age>", "prop:", "title:", "comments:", "links:", "parts:", "part-of:", "answers:", "answered-by:", "unanswered:")) or t == "hidden" for t in terms + neg):
        return None
    cands = [n["id"] for n in w.nodes.values() if n["parent"]]
    for t in terms:
        if t.startswith("?"):
            words = [x for x in t[1:].lower().split("+") if x]
            def ok(nid, words=words):
                n = w.nodes[nid]
                if n["type"] == "surface":
                    return all(x in n["title"].lower() for x in words)
                s = w.subjects[n["subject"]]
                hay = (s["title"] + " " + s["text"] + " " + " ".join(s["tags"])).lower()
                return all(x in hay for x in words)
            cands = [c for c in cands if ok(c)]
            apps = [c for c in cands if w.nodes[c]["type"] == "appearance"]
            if apps:
                cands = apps   # words prefer content; a surface only matches when nothing else does
        elif t.startswith("kind:"):
            kinds = set(t[5:].split("|"))
            cands = [c for c in cands if moo.kind_of(w, c) in kinds]
        elif t.startswith("tag:"):
            tag = t[4:]
            cands = [c for c in cands if w.nodes[c]["type"] == "appearance" and tag in w.subjects[w.nodes[c]["subject"]]["tags"]]
        elif t.startswith("in:"):
            fid = t[3:]
            if fid not in w.nodes or w.nodes[fid]["type"] != "surface":
                raise Refusal(f"in: needs a surface id, not {fid}")
            inside = set(_leaves(w, fid))
            cands = [c for c in cands if c in inside]
        elif t == "hidden":
            cands = [c for c in cands if w.hidden_fraction(c) > 0.05]
        elif t.startswith("also:"):
            a = t[5:]
            if a not in w.nodes or w.nodes[a]["type"] != "appearance":
                raise Refusal(f"also: needs an appearance id, not {a}")
            others = set(w.appearances_of(w.nodes[a]["subject"])) - {a}
            cands = [c for c in cands if c in others]
        elif t.startswith("prop:"):
            k, eq, v = t[5:].partition("=")
            if not k:
                raise Refusal("prop:k=v, or prop:k alone for things that have k")
            if eq and not v:      # Juniper, Pike: prop:year= matched everything that has a year, silently
                raise Refusal(f"prop:{k}= has no value; say prop:{k}=<value>, or prop:{k} alone for things that have {k}")

            def okp(nid, k=k, v=v, eq=eq):
                n = w.nodes[nid]
                props = (n.get("props") if n["type"] == "surface" else w.subjects[n["subject"]].get("props")) or {}
                return (props.get(k) == v) if v else (k in props)
            cands = [c for c in cands if okp(c)]
        elif t.startswith("age<") or t.startswith("age>"):
            # days since the last event that touched the thing, by the clock; things never touched under a clock have no age
            if not w.today:
                raise Refusal("age needs a clock: clock YYYY-MM-DD")
            op, n_days = t[3], t[4:]
            if not n_days.isdigit():
                raise Refusal("age<N or age>N, N in days")

            def oka(nid, op=op, n_days=int(n_days)):
                d = w.last_day(nid)
                if not d:
                    return op == ">"   # untouched since the clock began: older than any N, never "recent"
                age = w.days_between(d, w.today)
                return age < n_days if op == "<" else age > n_days
            cands = [c for c in cands if oka(c)]
        elif t.startswith("due<") or t.startswith("due>"):
            op, date = t[3], t[4:]
            def okd(nid, op=op, date=date):
                n = w.nodes[nid]
                if n["type"] != "appearance":
                    return False
                d = w.subjects[n["subject"]]["due"]
                return bool(d) and ((d < date) if op == "<" else (d > date))
            cands = [c for c in cands if okd(c)]
        elif t.startswith("title:"):
            word = t[6:].lower()
            cands = [c for c in cands if word in w.title(w.nodes[c]).lower()]
        elif t.startswith("comments:"):
            want = t[9:]
            def okc(nid, want=want):
                n = w.nodes[nid]
                if n["type"] != "appearance":
                    return False
                cs = w.subjects[n["subject"]]["comments"]
                return any(not c["resolved"] for c in cs) if want == "open" else bool(cs)
            cands = [c for c in cands if okc(c)]
        elif t.startswith("unanswered:"):
            # a chat whose latest lines were said by someone else: waiting on this reader (the command center's inbox)
            who = t[11:].lower()
            if not who:
                raise Refusal("unanswered:<name>, e.g. unanswered:alex")

            def oku(nid, who=who):
                n = w.nodes[nid]
                return n["type"] == "appearance" and w.subjects[n["subject"]]["kind"] == "chat" and bool(moo.unanswered(w, n["subject"], who))
            cands = [c for c in cands if oku(c)]
        elif t.startswith("links:"):
            src = w.subject_of(t[6:])
            if not src:
                raise Refusal("links: needs an appearance or subject id")
            linked = {l["to"] if l["from"] == src else l["from"] for l in w.links_of(src)}
            cands = [c for c in cands if w.nodes[c]["type"] == "appearance" and w.nodes[c]["subject"] in linked]
        elif t.startswith(("parts:", "part-of:")):
            # Pike: links: is untyped and undirected. `do link a20 to=a30 as=part-of` says a20 is part of a30:
            # parts:a30 finds a20; part-of:a20 finds a30. One kind, one direction, usable in find and in a lens.
            key = "parts:" if t.startswith("parts:") else "part-of:"
            src = w.subject_of(t[len(key):])
            if not src:
                raise Refusal(f"{key} needs an appearance or subject id")
            if key == "parts:":
                linked = {l["from"] for l in w.links_of(src) if l["kind"] == "part-of" and l["to"] == src}
            else:
                linked = {l["to"] for l in w.links_of(src) if l["kind"] == "part-of" and l["from"] == src}
            cands = [c for c in cands if w.nodes[c]["type"] == "appearance" and w.nodes[c]["subject"] in linked]
        elif t.startswith(("answers:", "answered-by:")):
            # a1027, as parts:/part-of: are for part-of: `do link a1008 to=a1006 as=answers` says a1008 answers a1006;
            # answers:a1006 finds a1008 (what answers it), answered-by:a1008 finds a1006 (what it answers)
            key = "answers:" if t.startswith("answers:") else "answered-by:"
            src = w.subject_of(t[len(key):])
            if not src:
                raise Refusal(f"{key} needs an appearance or subject id")
            if key == "answers:":
                linked = {l["from"] for l in w.links_of(src) if l["kind"] == "answers" and l["to"] == src}
            else:
                linked = {l["to"] for l in w.links_of(src) if l["kind"] == "answers" and l["from"] == src}
            cands = [c for c in cands if w.nodes[c]["type"] == "appearance" and w.nodes[c]["subject"] in linked]
        else:
            raise Refusal(f"unknown selection term {t!r}; terms: ?words kind: tag: in: hidden also: due< due> age< age> title: comments:open links:<id> parts:<id> part-of:<id> answers:<id> answered-by:<id> unanswered:<name>; -term leaves out")
    for n in neg:
        r = parse_selection(w, n, trash=True)
        if r is None:
            raise Refusal(f"-{n}: {n!r} is not a selection term")
        out = set(r[0])
        cands = [c for c in cands if c not in out]
    bins = [] if trash else moo.trash_surfaces(w)
    if bins and not any(t.startswith("in:") and (t[3:] in bins or any(w._is_inside(t[3:], b) for b in bins)) for t in terms):
        gone = {i for b in bins for i in _leaves(w, b)}
        cands = [c for c in cands if c not in gone]
    return cands, token


def trash_left_out(w, token):
    """a1327: how many things a selection left out because they are in a Trash, and the Trash ids. -> (n, bins)"""
    bins = moo.trash_surfaces(w)
    if not bins:
        return 0, []
    every, kept = parse_selection(w, token, trash=True), parse_selection(w, token)
    return (len(every[0]) - len(kept[0]) if every and kept else 0), bins


def general_verbs_by_origin(w, nid):
    out = {}
    for origin, names in moo.verbs_by_origin(w, nid).items():
        keep = [n for n in names if n not in SPECIALIZED]
        if keep:
            out[origin] = keep
    return out


PAIR_DOC = {
    "swap": ("A B", "Exchange the positions of two things (their order, if the surface is tiled)."),
    "beside": ("A B", "Put A right after B, in B's surface."),
    "match": ("A to=B", "Give A the size of B."),
    "link": ("A B as=blocks|refers|answers|part-of", "Connect A to B. examine shows a thing's links; links:A selects what A is linked to."),
}


def pair_verb(w, verb, a, b, args):
    if verb == "link":
        r = w.apply("link", a, None, {"to": b, "as": args.get("as", "refers")})
        r["events"] = [r["event"]]
        return r
    if a not in w.nodes or b not in w.nodes:
        raise Refusal(f"{verb} needs two ids on the desk")
    na, nb = w.nodes[a], w.nodes[b]
    if verb == "swap":
        if na["parent"] == nb["parent"] and w.nodes[na["parent"]]["layout"] != "free":
            kids = [k["id"] for k in w.children(na["parent"])]
            before = list(kids)
            i, j = kids.index(a), kids.index(b)
            kids[i], kids[j] = kids[j], kids[i]
            w._order(na["parent"], kids)
            for k in (a, b, na["parent"]):
                w._bump(k)
            ev = w._event("swap", a, {"with": b}, {"reorder": [na["parent"], before]})
            ev["changed"] = [a, b, na["parent"]]
            return {"ok": True, "event": ev["id"], "events": [ev["id"]], "changed": [a, b, na["parent"]]}
        steps = [("move", a, {"to": f"{nb['x']},{nb['y']}"}), ("move", b, {"to": f"{na['x']},{na['y']}"})]
        if na["parent"] != nb["parent"]:
            steps = [("move", a, {"into": nb["parent"]}), ("move", b, {"into": na["parent"]})]
        return moo._compose(w, steps)
    if verb == "beside":
        return moo._compose(w, [("move", a, {"after": b})])
    if verb == "match":
        return moo._compose(w, [("resize", a, {"to": f"{nb['w']}x{nb['h']}"})])
    raise Refusal(f"no pair verb {verb}")


def group_around(w, ids, args):
    """A new surface around a selection: created in the common parent (or in=), selection moved in."""
    if not ids:
        raise Refusal("group needs at least one thing (or an empty surface: use group on the surface itself)")
    parents = {w.nodes[i]["parent"] for i in ids}
    parent = args.get("in") or (parents.pop() if len(parents) == 1 else None)
    if not parent:
        raise Refusal("the selection spans several surfaces; say in=<surface> for the new group")
    lay = args.get("as", "column")
    spatial = lay == "free" and w.nodes[parent]["layout"] == "free"
    if spatial:
        # naming an arrangement must not destroy it: the group forms around its members, where they already are
        pad, head = 16, 28
        box = {i: w.box(i) for i in ids}     # where each is drawn (held here: a free surface's children)
        x0 = min(b[0] for b in box.values()) - pad
        y0 = min(b[1] for b in box.values()) - pad - head
        x1 = max(b[0] + b[2] for b in box.values()) + pad
        y1 = max(b[1] + b[3] for b in box.values()) + pad
        x0, y0 = max(0, x0), max(0, y0)
        rel = {i: (box[i][0] - x0, box[i][1] - y0) for i in ids}
    r0 = w.apply("group", parent, None, {"title": args.get("title", "group"), "as": lay})
    gid = r0["created"]
    if spatial:
        g = w.nodes[gid]
        g["x"], g["y"], g["w"], g["h"] = x0, y0, x1 - x0, y1 - y0
        steps = [s for i in ids for s in (("move", i, {"into": gid}), ("move", i, {"to": f"{rel[i][0]},{rel[i][1]}"}))]
    else:
        steps = [("move", i, {"into": gid}) for i in ids]
    r = moo._compose(w, steps)
    r["events"] = [r0["event"]] + r["events"]
    r["created"] = gid
    return r
