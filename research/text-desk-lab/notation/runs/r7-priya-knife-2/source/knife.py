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

SPECIALIZED = {"split", "gather", "dedupe", "reveal", "reply", "tidy", "stack", "done", "due"}
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
    if not terms or not any(t.startswith(("?", "kind:", "tag:", "in:", "also:", "due<", "due>", "title:")) or t == "hidden" for t in terms):
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
        else:
            raise Refusal(f"unknown selection term {t!r}; terms: ?words kind: tag: in: hidden also: due< due> title:")
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
}


def pair_verb(w, verb, a, b, args):
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
    r0 = w.apply("group", parent, None, {"title": args.get("title", "group"), "as": args.get("as", "column")})
    gid = r0["created"]
    r = moo._compose(w, [("move", i, {"into": gid}) for i in ids])
    r["events"] = [r0["event"]] + r["events"]
    r["created"] = gid
    return r
