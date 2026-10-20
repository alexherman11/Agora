"""Round 7: knives, not avocado slicers.

General verbs over general targets. A target is one id, a selection, or (for pair verbs) two ids.

Selections (one token; quote it if it has spaces, or join terms with commas):
  ?tide+parser      subjects whose title/text/tags contain all the words
  kind:image        kind (several: kind:note|task)
  tag:harbor        tag
  in:f04            inside surface f04 (recursively)
  hidden            more than 5% covered
  also:a18          the other appearances of a18's subject
  due<2026-09-20    due before (or due>); due:any, has a due date
  seats>3  status=done  due<=today  owner!=pike   (8 Oct, step 3 of the grammar unification) any aspect or prop compared
                    through the lens's expression kinds (expr.typed): numbers as numbers, dates as dates, words as words;
                    prop:k=v still reads, as k=v; a thing without the aspect never matches
  a20,a22          an explicit list
  terms combine with AND:  kind:image,in:f04   or  "kind:image in:f04"
  a row source may come first, then terms over its fields:  house doing=awake   messages:a12 who=alex   (scene.rows)

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
import persons
import promises
from world import Refusal

# 9 Oct 2026 (step 6): the specialized tier (split gather dedupe reveal reply tidy stack done, refused here with an alternative
# since a990) is gone; those words are verb notes of the house (houseverbs.py), looked up as any world verb is
GENERAL = list(moo.REGISTRY)


def _leaves(w, fid):
    out = []
    for k in w.children(fid):
        if k["type"] == "surface":
            out += [k["id"]] + _leaves(w, k["id"])
        else:
            out.append(k["id"])
    return out


def _in_order(w, fid, made):
    """Everything inside a surface, each surface before what it holds: a flow in its reading order, a free surface in
    the order its things were made (`made`: id -> place)."""
    kids = w.children(fid)
    if w.nodes[fid].get("layout") == "free":
        kids = sorted(kids, key=lambda k: made.get(k["id"], len(made)))
    out = []
    for k in kids:
        out.append(k["id"])
        if k["type"] == "surface":
            out += _in_order(w, k["id"], made)
    return out


# the selection terms parse_selection reads; the Help binder's selections note must name each (helpnotes.check, a1595)
TERMS = ("kind:", "tag:", "in:", "also:", "prop:", "title:", "comments:", "links:", "parts:", "part-of:", "answers:",
         "answered-by:", "unanswered:", "due:") + promises.TERMS      # a1587: held-by: asked-of: owed-to: asked-by: awaits:

# 8 Oct (step 3): what each term reads, so the fence's record of a member's reads (lens_ir.term_aspects, now aspects_of
# below) comes from the same table as the reader. Subject aspects, or "place" on the appearance; None: nothing any verb
# declares (kind, age, the promise terms). A compared aspect (k=v, k<v, prop:k=v) reads `prop:k`, or the field itself.
ASPECTS = {"tag": {"tags"}, "title": {"title"}, "?": {"title", "text", "tags"}, "due": {"due"}, "comments": {"comments"},
           "links": {"links"}, "parts": {"parts"}, "part-of": {"part-of"}, "answers": {"links"}, "answered-by": {"links"},
           "in": {"place"}, "also": {"place"}, "hidden": {"place"}, "kind": set(), "age": set(), "unanswered": set(),
           "settled": {"prop:status"}}
FIELDS = ("due", "title", "text", "kind", "tags")      # aspects compared by name, not through prop:
# 9 Oct (a3806): a thing is settled when its status says its work is over. One word for it, so a room can show what
# is live and say how many it left out, and no one has to remember which of five words a kind ends in. A promise is
# settled when it has ended (promises.state). -settled is what is live
SETTLED = ("done", "cured", "answered", "kept", "released", "landed", "closed", "retired")


def is_settled(w, nid):
    n = w.nodes.get(nid) or {}
    s = w.subjects.get(n.get("subject") or nid)
    if not s:
        return False
    if s.get("kind") == "promise":
        return bool(promises.state(w, s["id"]).get("ended"))
    return str((s.get("props") or {}).get("status", "")).lower() in SETTLED


GENERIC = re.compile(r"^([A-Za-z_][\w-]*)(!=|<=|>=|=|<|>)(.*)$")


def term_key(t):
    """-> (name, op, value) of one term: ('kind', ':', 'note'), ('seats', '>', '3'), ('hidden', '', ''), ('?', '', 'a+b')."""
    t = t[1:] if t.startswith("-") else t
    if t.startswith("?"):
        return "?", "", t[1:]
    if t in ("hidden", "settled"):
        return t, "", ""
    if ":" in t and (not GENERIC.match(t) or t.index(":") < min(i for i in (t.find(c) for c in "=<>!") if i >= 0)):
        name, _, val = t.partition(":")
        if name == "prop":
            k, eq, v = val.partition("=")
            return (k, "=", v) if eq else (k, "has", "")      # prop:k=v is k=v; prop:k alone is 'has k'
        return name, ":", val
    m = GENERIC.match(t)
    if m:
        return m.group(1), m.group(2), m.group(3)
    return t, "", ""


def aspects_of(q):
    """The aspects a member of selection `q` was read by: -> (subject aspects, appearance aspects). Every selection
    leaves out what is in a Trash, so a member's place always counts (a1327)."""
    subj, app = set(), {"place"}
    for t in [x for x in re.split(r"[,\s]+", (q or "").strip()) if x]:
        name, op, _v = term_key(t)
        if op in ("=", "!=", "<", ">", "<=", ">=", "has"):
            if name in ("kind", "age"):
                continue
            subj.add(name if name in FIELDS else f"prop:{name}")
            continue
        asp = ASPECTS.get(name)
        if asp is None:
            continue
        for a in asp:
            (app if a == "place" else subj).add(a)
    return subj, app


def value_of(w, nid, k):
    """A thing's value for an aspect or prop name, for a comparison; None when it has none."""
    n = w.nodes[nid]
    s = w.subjects.get(n.get("subject")) if n["type"] == "appearance" else None
    if k == "due":
        return (s or {}).get("due") or None
    if k == "title":
        return w.title(n)
    if k == "text":
        return (s or {}).get("text")
    if k == "kind":
        return moo.kind_of(w, nid)
    if k == "tags":
        return " ".join((s or {}).get("tags") or []) or None
    props = (n.get("props") if n["type"] == "surface" else (s or {}).get("props")) or {}
    v = props.get(k)
    return None if v is None or str(v).strip() == "" else v


def compares(w, raw, op, want, k=None, binds=None):
    """Does a stored value satisfy `op want`? Typed as the lens types values (expr.typed): a number against a number, a
    date against a date, words against words; kinds that cannot be compared never match. A person prop is the same
    person, not the same spelling (a1590)."""
    import expr as X
    if raw is None or str(raw).strip() == "":
        return False
    if op == "has":
        return True
    if k in persons.PERSON_KEYS and op in ("=", "!="):
        hit = persons.matches(w, raw, want, binds)
        return hit if op == "=" else not hit
    res = X._cmp(op, X.typed(raw), X.typed(want))
    return res.kind == "bool" and bool(res.v)


def filter_rows(w, rows, terms, binds=None, form="a row source"):
    """8 Oct: a row source's rows kept by comparison terms over their fields (`house doing=awake`, `messages:a12 who=alex`).
    Any other kind of term is refused: a row has fields, not a place or tags. `form` is the source as help prints it."""
    out = list(rows)
    for t in terms:
        neg = t.startswith("-")
        name, op, want = term_key(t)
        if op not in ("=", "!=", "<", ">", "<=", ">=", "has"):
            raise Refusal(f"unknown term {t!r}: {form} takes terms over its fields (k=v k!=v k<v k>v k<=v k>=v); kind:, tag:, in: and the like are for things")
        out = [r for r in out if compares(w, r.get(name), op, want, name, binds) != neg]
    return out

DUE_DOORS = "use due:any, due<DATE or due>DATE"


def misnamed(text):
    """a3359: a selection that asks for the due date as a prop, or by a due: word the desk doesn't read, is told the
    door. due is a field of its own (moo._field refuses `prop due=` the same way), so prop:due matched nothing and
    said so as if it had looked. -> the refusal's words, or None. Reads the text alone, so a lens is told when saved."""
    for t in re.split(r"[,\s]+", (text or "").strip().strip('"')):
        t = t.lstrip("-")
        if re.fullmatch(r"prop:due(=.*)?", t):
            return f"due is not a prop: {DUE_DOORS}"
        if re.match(r"due:\S", t) and t != "due:any":
            return f"{t}: due: takes only any (things with a due date); {DUE_DOORS}"
    return None


def parse_selection(w, token, trash=False, binds=None):
    """Return (ids, description) or None if token is a plain id. What is inside a Trash (moo.trash_surfaces) is left out
    unless an in: term names the Trash or a surface inside it, or trash=True (a1327). binds (a1590): the persons the
    stored line being read was bound to when saved; prop:owner= (and each person key) and the promise terms mean them,
    and a typed name means today's bearer. A door mark stays with its name: prop:owner=juniper,first is one term."""
    token = token.strip().strip('"')
    if token in w.nodes or token in w.subjects or token in ("desk", "root") or token.lower().startswith("corner:"):
        return None     # corner:<name> is one thing, a resident's corner (a1027), not a selection
    door = rf",[ \t]*({'|'.join(persons.ORDINALS + ('last',))})\b"
    terms = [t.replace("\x01", ",") for t in re.split(r"[,\s]+", re.sub(door, "\x01\\1", token)) if t]
    if all(t in w.nodes for t in terms) and len(terms) > 1:
        return terms, "list " + ",".join(terms)
    KNOWN = TERMS
    said = misnamed(",".join(terms))
    if said:
        raise Refusal(said)
    for t in terms:
        # Moss: an unknown term fell back to a text search in find and to nothing in scene: two wrong answers, no refusal
        if re.match(r"^-?[a-z]+:\S", t) and not t.lstrip("-").startswith(KNOWN):
            raise Refusal(f"no selection term {t.split(':')[0].lstrip('-')}: (terms: ?words {' '.join(KNOWN)} due< due> age< age> hidden settled; help selections)")
    neg = [t[1:] for t in terms if t.startswith("-") and len(t) > 1]   # -tag:fixed: everything the term would select is left out
    terms = [t for t in terms if not t.startswith("-")]
    if not (terms or neg) or not any(t.startswith(("?", "kind:", "tag:", "in:", "also:", "due<", "due>", "due:", "age<", "age>", "prop:", "title:", "comments:", "links:", "parts:", "part-of:", "answers:", "answered-by:", "unanswered:") + promises.TERMS) or t in ("hidden", "settled") or GENERIC.match(t) for t in terms + neg):
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
            # Pike, 7 Oct (a3482): `of in:<document>` listed its paragraphs in the order they were made, so one moved up
            # the page stayed last in the lens while look read it fourth. What is in a place is listed in that place's
            # reading order, where it has one: a free surface has none (its order is which card is on top), so there
            # the order things were made in stands.
            keep = set(cands)
            made = {c: k for k, c in enumerate(cands)}
            cands = [c for c in _in_order(w, fid, made) if c in keep]
        elif t == "settled":
            cands = [c for c in cands if is_settled(w, c)]
        elif t == "hidden":
            cands = [c for c in cands if w.hidden_fraction(c) > 0.05]
        elif t.startswith("also:"):
            a = t[5:]
            if a not in w.nodes or w.nodes[a]["type"] != "appearance":
                raise Refusal(f"also: needs an appearance id, not {a}")
            others = set(w.appearances_of(w.nodes[a]["subject"])) - {a}
            cands = [c for c in cands if c in others]
        elif t.startswith("prop:") or (GENERIC.match(t) and not t.startswith(("age<", "age>"))):
            # 8 Oct (step 3): one comparison for every aspect and prop, typed as the lens types values: prop:k=v is k=v,
            # due<DATE is the field due compared as a date, seats>3 a prop compared as a number
            if t.startswith("prop:"):
                k, eq, v = t[5:].partition("=")
                if not k:
                    raise Refusal("prop:k=v, or prop:k alone for things that have k")
                if eq and not v:      # Juniper, Pike: prop:year= matched everything that has a year, silently
                    raise Refusal(f"prop:{k}= has no value; say prop:{k}=<value>, or prop:{k} alone for things that have {k}")
                op = "=" if eq else "has"
            else:
                k, op, v = GENERIC.match(t).groups()
                if not v:
                    raise Refusal(f"{t} has no value; say {k}{op}<value>, or prop:{k} alone for things that have {k}")
            if k in ("kind", "age"):
                raise Refusal(f"{t}: {k} is not compared; say kind:<kind>, or age<N / age>N in days")
            cands = [c for c in cands if compares(w, value_of(w, c, k), op, v, k, binds)]
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
        elif t == "due:any":
            # a3359: has a due date, as comments:any and awaits:any ask; it could only be asked as due<2999-12-31
            cands = [c for c in cands if w.nodes[c]["type"] == "appearance" and w.subjects[w.nodes[c]["subject"]]["due"]]
        elif t.startswith("title:"):
            # a6642: `title:home+base`, the title holds every word, as ?home+base does over title, text and tags, so a
            # lens can put title hits first from the one words-of() it gives ?: `of title:$q`, then `of ?$q,-title:$q`
            words = [x for x in t[6:].lower().split("+") if x]
            cands = [c for c in cands if all(x in w.title(w.nodes[c]).lower() for x in words)]
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
        elif t.startswith(promises.TERMS):
            # a1587: open promises and requests, read from their events (held-by: asked-of: owed-to: asked-by:), and
            # the things open requests are about (awaits:<name|any>)
            hit = promises.matching(w, t, binds)
            cands = [c for c in cands if w.nodes[c]["type"] == "appearance" and w.nodes[c]["subject"] in hit]
        else:
            raise Refusal(f"unknown selection term {t!r}; terms: ?words kind: tag: in: hidden settled also: due< due> due:any age< age> title: comments:open links:<id> parts:<id> part-of:<id> answers:<id> answered-by:<id> unanswered:<name>, and any aspect or prop compared (k=v k!=v k<v k>v k<=v k>=v); -term leaves out")
    for n in neg:
        r = parse_selection(w, n, trash=True, binds=binds)
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
    return moo.verbs_by_origin(w, nid)


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
