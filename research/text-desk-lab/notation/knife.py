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


def parse_selection(w, token):
    """Return (ids, description) or None if token is a plain id."""
    token = token.strip().strip('"')
    if token in w.nodes or token in w.subjects or token in ("desk", "root"):
        return None
    terms = [t for t in re.split(r"[,\s]+", token) if t]
    if all(t in w.nodes for t in terms) and len(terms) > 1:
        return terms, "list " + ",".join(terms)
    neg = [t[1:] for t in terms if t.startswith("-") and len(t) > 1]   # -tag:fixed: everything the term would select is left out
    terms = [t for t in terms if not t.startswith("-")]
    if not (terms or neg) or not any(t.startswith(("?", "kind:", "tag:", "in:", "also:", "due<", "due>", "age<", "age>", "prop:", "title:", "comments:", "links:")) or t == "hidden" for t in terms + neg):
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
        elif t.startswith("links:"):
            src = w.subject_of(t[6:])
            if not src:
                raise Refusal("links: needs an appearance or subject id")
            linked = {l["to"] if l["from"] == src else l["from"] for l in w.links_of(src)}
            cands = [c for c in cands if w.nodes[c]["type"] == "appearance" and w.nodes[c]["subject"] in linked]
        else:
            raise Refusal(f"unknown selection term {t!r}; terms: ?words kind: tag: in: hidden also: due< due> age< age> title: comments:open links:<id>; -term leaves out")
    for n in neg:
        r = parse_selection(w, n)
        if r is None:
            raise Refusal(f"-{n}: {n!r} is not a selection term")
        out = set(r[0])
        cands = [c for c in cands if c not in out]
    return cands, token


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
            i, j = kids.index(a), kids.index(b)
            kids[i], kids[j] = kids[j], kids[i]
            w._order(na["parent"], kids)
            for k in (a, b, na["parent"]):
                w._bump(k)
            ev = w._event("swap", a, {"with": b}, {"restore": None})
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
        x0 = min(w.nodes[i]["x"] for i in ids) - pad
        y0 = min(w.nodes[i]["y"] for i in ids) - pad - head
        x1 = max(w.nodes[i]["x"] + w.nodes[i]["w"] for i in ids) + pad
        y1 = max(w.nodes[i]["y"] + w.nodes[i]["h"] for i in ids) + pad
        x0, y0 = max(0, x0), max(0, y0)
        rel = {i: (w.nodes[i]["x"] - x0, w.nodes[i]["y"] - y0) for i in ids}
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
