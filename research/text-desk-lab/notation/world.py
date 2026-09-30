"""A small synthetic desk, built to be read and written as text.

Ontology (same words as Agora, independent implementation):
  subject     content with identity (note, task, image, chat). Has text, tags, rev.
  appearance  a placement of a subject on a surface: x, y, w, h, z, rev.
  surface     a container with a layout: free (bag of rectangles), column, row.
The same subject may appear several times. Editing a subject edits every appearance.
Every mutation is an event with an undo; mutations are fenced on the observed rev.
"""

from copy import deepcopy
import re

SCREEN = (1280, 800)
ORDER_DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"


def between(a, b):
    """sable-9: an order key that sorts strictly between a and b (None = open end). Fractional indexing, base 36."""
    a, out, i, tight = a or "", "", 0, b is not None
    while True:
        ca = ORDER_DIGITS.index(a[i]) if i < len(a) else 0
        cb = ORDER_DIGITS.index(b[i]) if tight and i < len(b) else len(ORDER_DIGITS)
        if cb - ca > 1:
            return out + ORDER_DIGITS[(ca + cb) // 2]
        out += ORDER_DIGITS[ca]
        if tight and (i >= len(b) or ORDER_DIGITS[ca] != b[i]):
            tight = False
        i += 1


def _geometry_choices_default():
    import os
    return os.environ.get("DESK_GEOMETRY", "") == "choices"


class Refusal(Exception):
    pass


class World:
    def __init__(self):
        self.subjects = {}
        self.nodes = {}  # surfaces and appearances, keyed by id
        self.events = []
        self.injections = []
        self.links = []
        self.last_created = None
        self.last_surface = None
        self._ids = 0   # plain int: pickles on every Python (itertools.count stopped pickling in 3.14)
        self._eseq = 0  # the last event number ever issued; it never goes back, so an event id is never reused
        self.root = self.add_surface("desk", None, "free", 0, 0, *SCREEN)

    # ---- construction -------------------------------------------------
    def _id(self, prefix):
        if not isinstance(self._ids, int):          # a session pickled before the counter became an int
            self._ids = next(self._ids) - 1
        self._ids += 1
        return f"{prefix}{self._ids:02d}"

    def add_subject(self, kind, title, text="", tags=(), due=None):
        sid = self._id("s")
        self.subjects[sid] = {
            "id": sid, "kind": kind, "title": title, "text": text,
            "tags": list(tags), "due": due, "rev": 1, "comments": [], "props": {},
        }
        return sid

    # ---- comments, links, sections (round 9) ---------------------------
    def add_comment(self, sid, by, text, actor=None):
        cid = self._id("c")
        s = self.subjects[sid]
        s["comments"].append({"id": cid, "by": by, "text": text, "resolved": False, "replies": []})
        s["rev"] += 1
        for a in self.appearances_of(sid):
            self._bump(a)
        ev = self._event("comment", sid, {"line": text}, {"drop_comment": cid}, actor or by)
        ev["changed"] = [sid] + self.appearances_of(sid)
        return cid

    def find_comment(self, cid):
        for s in self.subjects.values():
            for c in s["comments"]:
                if c["id"] == cid:
                    return s, c
        return None, None

    def add_link(self, a, b, kind, actor=None):
        actor = actor or self.me
        sa, sb = self.subject_of(a), self.subject_of(b)
        if not sa or not sb:
            raise Refusal("link needs two things with content (appearances or subjects), not surfaces")
        if sa == sb:
            raise Refusal("cannot link a thing to itself")
        if kind not in ("blocks", "refers", "answers", "part-of"):
            raise Refusal("as= must be blocks, refers, answers or part-of")
        for l in self.links:
            if l["from"] == sa and l["to"] == sb and l["kind"] == kind:
                raise Refusal(f"already linked: {l['id']} {sa} {kind} {sb}")
        lid = self._id("l")
        self.links.append({"id": lid, "from": sa, "to": sb, "kind": kind})
        for s in (sa, sb):
            self.subjects[s]["rev"] += 1
            for x in self.appearances_of(s):
                self._bump(x)
        ev = self._event("link", a, {"to": b, "as": kind}, {"drop_link": lid}, actor)
        ev["changed"] = [sa, sb] + self.appearances_of(sa) + self.appearances_of(sb)
        return lid

    def subject_of(self, ident):
        if ident in self.subjects:
            return ident
        n = self.nodes.get(ident)
        return n["subject"] if n and n["type"] == "appearance" else None

    def links_of(self, sid):
        return [l for l in self.links if l["from"] == sid or l["to"] == sid]

    def sections(self, text):
        """Split doc text into [(heading, body)] on '## ' lines; the preamble has heading None."""
        out, head, buf = [], None, []
        for line in text.splitlines():
            if line.startswith("## "):
                if head is not None or buf:
                    out.append((head, "\n".join(buf).strip("\n")))
                head, buf = line[3:].strip(), []
            else:
                buf.append(line)
        if head is not None or buf:
            out.append((head, "\n".join(buf).strip("\n")))
        return out

    def checklist(self, text):
        return [(i, l) for i, l in enumerate(text.splitlines()) if l.lstrip().startswith(("- [ ]", "- [x]"))]

    def add_surface(self, title, parent, layout, x, y, w, h):
        fid = self._id("f")
        self.nodes[fid] = {
            "id": fid, "type": "surface", "title": title, "parent": parent,
            "layout": layout, "x": x, "y": y, "w": w, "h": h,
            "z": self._next_z(parent), "rev": 1,
        }
        return fid

    def place(self, subject, parent, x, y, w, h, folded=False):
        aid = self._id("a")
        self.nodes[aid] = {
            "id": aid, "type": "appearance", "subject": subject, "parent": parent,
            "x": x, "y": y, "w": w, "h": h, "z": self._next_z(parent),
            "folded": folded, "rev": 1,
        }
        if self.choices and self._flow(parent):
            self._join_flow(aid, parent)
        self.reflow(parent)
        return aid

    def _next_z(self, parent):
        sib = [n["z"] for n in self.nodes.values() if n["parent"] == parent]
        return (max(sib) + 1) if sib else 1

    # ---- sable-9: geometry as choices (behind the switch) ----------------
    # With `choices` on, a child of a column or row holds only choices: order (a fractional key: its place among its
    # siblings) and share (its weight in the flow). Its x, y, w, h are still written by reflow, but as a cache of a
    # derived layout, never as its own facts: children() orders by `order`, reflow() weighs by `share`, and a move or a
    # resize in a flow changes one child's order or share. Children of a free surface keep x, y, w, h as held choices.
    # Off (the default), nothing here runs and the world behaves exactly as before.
    choices = _geometry_choices_default()

    def _flow(self, fid):
        return fid in self.nodes and self.nodes[fid].get("layout") in ("column", "row")

    def _legacy_children(self, fid):
        kids = [n for n in self.nodes.values() if n["parent"] == fid]
        lay = self.nodes[fid]["layout"]
        if lay == "free":
            return sorted(kids, key=lambda n: n.get("z", 0))
        # a thing assigned from rows in a flow has no box until reflow derives one
        return sorted(kids, key=lambda n: (n.get("y", 0), n.get("x", 0)) if lay == "column" else (n.get("x", 0), n.get("y", 0)))

    def _axis(self, fid):
        return "h" if self.nodes[fid]["layout"] == "column" else "w"

    def _ensure_choices(self, fid):
        """Give every child of flow `fid` an order and a share, from today's order and sizes, only where missing."""
        last, axis = None, self._axis(fid)
        for k in self.children(fid):
            if k.get("order") is None or (last is not None and k["order"] <= last):
                k["order"] = between(last, None)
            last = k["order"]
            if not k.get("share"):
                k["share"] = max(1, k.get(axis, 1))

    def _join_flow(self, nid, fid):
        """A thing arriving in a flow goes after its last sibling, with the mean of its siblings' shares."""
        n = self.nodes[nid]
        n["order"], n["share"] = None, None
        sib = [k for k in self.children(fid) if k["id"] != nid]
        if sib:
            self._ensure_choices(fid)
            sib = [k for k in self.children(fid) if k["id"] != nid]
        n["order"] = between(sib[-1]["order"] if sib else None, None)
        shares = [k["share"] for k in sib if k.get("share")]
        n["share"] = int(sum(shares) / len(shares)) if shares else max(1, n.get(self._axis(fid), 1))

    def _reorder(self, fid, ids):
        """Put `ids` in this order, changing the fewest order keys: keep the longest run already in order, re-key the rest."""
        self._ensure_choices(fid)
        keys = [self.nodes[i].get("order") for i in ids]
        best, prev = [1] * len(ids), [-1] * len(ids)      # longest increasing subsequence of the existing keys
        for j in range(len(ids)):
            for i in range(j):
                if keys[i] is not None and keys[j] is not None and keys[i] < keys[j] and best[i] + 1 > best[j]:
                    best[j], prev[j] = best[i] + 1, i
        keep = set()
        j = max(range(len(ids)), key=lambda x: best[x]) if ids else -1
        while j >= 0 and keys[j] is not None:
            keep.add(j)
            j = prev[j]
        for j, i in enumerate(ids):
            if j in keep:
                continue
            lo = self.nodes[ids[j - 1]]["order"] if j else None
            hi = next((self.nodes[ids[x]]["order"] for x in range(j + 1, len(ids)) if x in keep), None)
            self.nodes[i]["order"] = between(lo, hi)

    def box(self, nid):
        """The box a thing is drawn in: held for a child of a free surface, derived (the reflow cache) in a flow."""
        n = self.nodes[nid]
        return n["x"], n["y"], n["w"], n["h"]

    # ---- queries ------------------------------------------------------
    def children(self, fid):
        if not (self.choices and self._flow(fid)):
            return self._legacy_children(fid)
        legacy = self._legacy_children(fid)
        keyed = sorted((n for n in legacy if n.get("order") is not None), key=lambda n: (n["order"], n["id"]))
        return keyed + [n for n in legacy if n.get("order") is None]

    def title(self, node):
        if node["type"] == "surface":
            return node["title"]
        return self.subjects[node["subject"]]["title"]

    def abs_rect(self, nid):
        n = self.nodes[nid]
        x, y = n["x"], n["y"]
        p = n["parent"]
        while p:
            pn = self.nodes[p]
            x += pn["x"]
            y += pn["y"]
            p = pn["parent"]
        return x, y, n["w"], n["h"]

    def depth(self, nid):
        d = 0
        while self.nodes[nid]["parent"]:
            nid = self.nodes[nid]["parent"]
            d += 1
        return d

    def appearances_of(self, sid):
        return [n["id"] for n in self.nodes.values() if n["type"] == "appearance" and n["subject"] == sid]

    def _overlap(self, a, b):
        ax, ay, aw, ah = self.abs_rect(a)
        bx, by, bw, bh = self.abs_rect(b)
        ox = min(ax + aw, bx + bw) - max(ax, bx)
        oy = min(ay + ah, by + bh) - max(ay, by)
        return (ox * oy) if (ox > 0 and oy > 0) else 0

    def relations(self, nid):
        """Spatial facts about nid relative to siblings and the screen."""
        n = self.nodes[nid]
        ax, ay, aw, ah = self.abs_rect(nid)
        out = []
        if ax + aw > SCREEN[0] or ay + ah > SCREEN[1] or ax < 0 or ay < 0:
            out.append("offscreen-part")
        if n["parent"]:
            px, py, pw, ph = self.abs_rect(n["parent"])
            ext = str((self.nodes[n["parent"]].get("props") or {}).get("extent", ""))
            if self.nodes[n["parent"]]["layout"] == "free" and "x" in ext and all(p.isdigit() for p in ext.split("x", 1)):
                pw, ph = (int(p) for p in ext.split("x", 1))
            if ax + aw > px + pw or ay + ah > py + ph:
                out.append("spills-parent")
            for s in self.children(n["parent"]):
                if s["id"] == nid:
                    continue
                area = self._overlap(nid, s["id"])
                if not area:
                    continue
                if s["z"] < n["z"]:
                    frac = area / float(s["w"] * s["h"])
                    out.append(f"covers {s['id']}" + (" fully" if frac > 0.95 else ""))
                else:
                    frac = area / float(aw * ah)
                    out.append(f"under {s['id']}" + (" fully" if frac > 0.95 else ""))
        return out

    def hidden_fraction(self, nid):
        n = self.nodes[nid]
        if not n["parent"]:
            return 0.0
        covered = 0.0
        for s in self.children(n["parent"]):
            if s["id"] != nid and s["z"] > n["z"]:
                covered += self._overlap(nid, s["id"])
        return min(1.0, covered / float(n["w"] * n["h"]))

    # ---- layout -------------------------------------------------------
    def reflow(self, fid):
        """Tiled surfaces share their space equally among children (like a tiling WM)."""
        f = self.nodes[fid]
        if f["layout"] == "free":
            return
        if self.choices:
            self._ensure_choices(fid)
        kids = self.children(fid)
        if not kids:
            return
        gap = 8
        n = len(kids)
        axis = "h" if f["layout"] == "column" else "w"
        total = f[axis] - gap * (n + 1)
        weights = [max(1, (k.get("share") if self.choices else None) or k[axis]) for k in kids]
        if self.equal_share:
            weights = [1] * n
        wsum = float(sum(weights))
        shares = [max(24, int(total * wt / wsum)) for wt in weights]
        if sum(shares) > total:
            shares = [max(24, total // n)] * n   # proportional shares clamped past the space: fall back to equal, never spill
        if f["layout"] == "column":
            y = gap
            for k, sh in zip(kids, shares):
                k["x"], k["y"], k["w"], k["h"] = gap, y, f["w"] - 2 * gap, sh
                y += sh + gap
        else:
            x = gap
            for k, sh in zip(kids, shares):
                k["x"], k["y"], k["w"], k["h"] = x, gap, sh, f["h"] - 2 * gap
                x += sh + gap
        if self.choices:
            for i, k in enumerate(kids):    # in a flow nothing overlaps: stacking is derived from order, like the box
                k["z"] = i + 1
        for k in kids:
            if k["type"] == "surface":
                self.reflow(k["id"])

    def _fair_share(self, nid):
        """A thing created at runtime inside a tiled parent takes the mean of its siblings' share, not a default size
        (otherwise proportional reflow squeezes every later arrival). Build-time placement is untouched."""
        n = self.nodes[nid]
        p = n["parent"]
        if not p or self.nodes[p]["layout"] == "free":
            return
        axis = "h" if self.nodes[p]["layout"] == "column" else "w"
        sib = [k[axis] for k in self.children(p) if k["id"] != nid]
        if sib:
            n[axis] = int(sum(sib) / len(sib))
        if self.choices:
            self._join_flow(nid, p)

    # ---- mutation -----------------------------------------------------
    def _bump(self, nid):
        if nid in self.nodes:
            self.nodes[nid]["rev"] += 1

    today = None   # the clock, when a desk sets one; events are stamped with it so things can have an age

    me = "jeff"   # who is at the desk: the owner by default; a visitor works under their own name

    def _event(self, verb, target, args, undo, actor=None, note=""):
        actor = actor or self.me
        self._eseq = self.next_event_number()
        ev = {"id": f"e{self._eseq}", "verb": verb, "target": target,
              "args": deepcopy(args), "undo": undo, "note": note, "by": actor,
              "at": __import__("datetime").datetime.now().isoformat(timespec="seconds")}   # wall time; `day` stays the desk's clock
        if self.today:
            ev["day"] = self.today
        self.events.append(ev)
        return ev

    def next_event_number(self):
        """Event ids are minted once and never reused (Sable, for Jeff's step 1b): a rolled-back or refused batch leaves
        a gap, never a second e2. A world pickled before the counter starts after the highest id it holds. A caller that
        restores an older copy of the world must carry _eseq across (keep_event_numbers)."""
        last = getattr(self, "_eseq", None)
        if last is None:
            last = max((int(e["id"][1:]) for e in self.events), default=0)
        return last + 1

    def keep_event_numbers(self, other):
        """After restoring a snapshot, never issue again a number the discarded world already issued."""
        self._eseq = max(getattr(self, "_eseq", 0) or 0, self.next_event_number() - 1, getattr(other, "_eseq", 0) or 0)

    def last_day(self, nid):
        """The clock day of the last event that touched this thing (or its subject), or None."""
        sid = self.nodes[nid].get("subject") if nid in self.nodes else nid
        for e in reversed(self.events):
            if e["verb"] == "undo" or e.get("undone"):
                continue   # undoing is not touching: it restores the past, including the thing's age
            if e.get("day") and (e["target"] in (nid, sid) or nid in (e.get("changed") or []) or sid in (e.get("changed") or [])):
                return e["day"]
        return None

    @staticmethod
    def days_between(a, b):
        from datetime import date
        ya, ma, da = map(int, a.split("-"))
        yb, mb, db = map(int, b.split("-"))
        return (date(yb, mb, db) - date(ya, ma, da)).days

    def fence(self, nid, rev):
        cur = self.nodes[nid]["rev"] if nid in self.nodes else self.subjects[nid]["rev"]
        if rev != cur:
            raise Refusal(f"stale: {nid} is at rev {cur}, you observed {rev}; look again")

    coords = True  # False = tree variant: no coordinate verbs on free surfaces
    equal_share = True  # tiled children share equally; False = proportional to their current size

    TEXT_VERBS = {
        "append": "line=<str>  (adds a line at the end; edits the subject, so every appearance changes)",
        "retitle": "title=<str>",
        "rewrite": "text=<str> [section=<heading>]  (replaces all the text, or only the body of one ## section; write \\n between lines)",
    }

    def verbs_for(self, nid):
        if nid in self.subjects:
            return dict(self.TEXT_VERBS, place="into=<surface>")
        n = self.nodes[nid]
        v = {}
        if n["parent"]:
            parent = self.nodes[n["parent"]]
            if parent["layout"] == "free" and self.coords:
                v["move"] = "to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>"
                v["resize"] = "to=<w>x<h>"
                v["raise"] = "(to front)"
                v["lower"] = "(to back)"
            elif parent["layout"] == "free":
                v["move"] = "into=<surface> | before=<node> | after=<node>"
                v["raise"] = "(to front)"
                v["lower"] = "(to back)"
            else:
                v["move"] = "into=<surface> | before=<node> | after=<node>"
                v["resize"] = "to=<w>x<h>"
            v["remove"] = "(removes this appearance only; the subject survives)"
        if n["type"] == "surface":
            v["tile"] = "as=column|row  (lay children out without overlap)"
            if n["layout"] != "free":
                v["untile"] = ""
            v["rename"] = "title=<str>"
            v["group"] = "title=<str> as=free|column|row  (new empty surface inside this one)"
            v["create"] = "kind=note|task|chat title=<str> [text=<str>] [due=YYYY-MM-DD] [tags=a,b]  (new subject, placed here)"
        else:
            v["unfold" if n["folded"] else "fold"] = "(show/hide content on screen)"
            v.update(self.TEXT_VERBS)
            v.update(self.content_verbs(n["subject"]))
        return v

    def content_verbs(self, sid):
        s = self.subjects[sid]
        v = {"comment": "line=<str>  (a comment on this thing, signed by you)",
             "link": "to=<id> as=blocks|refers|answers|part-of  (a connection to another thing)"}
        if any(not c["resolved"] for c in s["comments"]):
            v["resolve"] = "id=<cNN> [line=<str>]  (close a comment, optionally with a reply)"
        if s["kind"] == "doc" or "## " in s["text"]:
            v["append"] = "line=<str> [section=<name>]  (adds a line at the end, or at the end of a section)"
        if self.checklist(s["text"]):
            v["check"] = "item=<n>  (tick the n-th checklist line)"
        if self.links_of(sid):
            v["unlink"] = "id=<lNN>"
        return v

    @staticmethod
    def display_name(actor):
        """How an actor is named where people read: 'sable' -> 'Sable'."""
        a = str(actor or "")
        return a[:1].upper() + a[1:]

    # a chat line's signature: 'Sable: ...', or 'Alex, via rule r3: ...' when a rule added it (group 1 the speaker)
    SPEAKER = re.compile(r"^([\w-]+)(?:, via rule (\w+))?[ \t]*:[ \t]*")

    def sign_chat_line(self, line, actor):
        """A chat line as the world keeps it: 'Name: words', Name the actor's display name. Returns (line, dropped):
        a leading 'Name:' that is the actor's own (any case) is dropped, since the world signs now; a leading name that
        is anyone else's stays as plain words after the signature. A rule runs as whoever triggered it (Sable a656:
        whether it should run as its author is a643's question), so its line says so: 'Alex, via rule r3: ...' never
        reads as Alex speaking."""
        words = str(line).strip()
        said = re.match(r"^([\w-]+)[ \t]*:[ \t]*", words)
        dropped = bool(said and said.group(1).casefold() == str(actor).casefold())
        if dropped:
            words = words[said.end():]
        rule = getattr(self, "acting_rule", None)
        return self.display_name(actor) + (f", via rule {rule}" if rule else "") + ": " + words, dropped

    def apply(self, verb, target, rev, args, actor=None):
        actor = actor or self.me
        args = dict(args or {})
        if target in self.subjects:
            return self._apply_subject(verb, target, rev, args, actor)
        if target not in self.nodes:
            raise Refusal(f"no such node {target}")
        if rev is not None:
            self.fence(target, rev)
        allowed = self.verbs_for(target)
        if verb not in allowed:
            raise Refusal(f"{verb} is not a verb of {target}; its verbs: {', '.join(allowed)}")
        n = self.nodes[target]
        before = deepcopy(n)
        changed = [target]
        if verb in ("append", "retitle", "rewrite", "edit", "comment", "resolve", "check", "link", "unlink"):
            if n["type"] != "appearance":
                raise Refusal(f"{verb} needs an appearance or subject, not a surface")
            return self._apply_subject(verb, n["subject"], None, args, actor, via=target)
        if verb == "move":
            if "into" in args and not ("before" in args or "after" in args):
                dest = args["into"]
                if dest not in self.nodes or self.nodes[dest]["type"] != "surface":
                    raise Refusal(f"into= must name a surface, not {dest}")
                if self.nodes[dest].get("layout") == "view":
                    raise Refusal(f"{dest} is a view of {self.nodes[dest].get('query')}: things cannot be moved into it; change the thing so the query matches it")
                if dest == target or self._is_inside(dest, target):
                    raise Refusal("cannot move a surface into itself")
                if n["parent"] == dest and "at" not in args:
                    return {"ok": True, "event": None, "changed": [], "note": f"{target} is already in {dest}; nothing changed"}
                old = n["parent"]
                n["parent"] = dest
                n["z"] = self._next_z(dest)
                d = self.nodes[dest]
                if d["layout"] == "free":
                    n["x"], n["y"] = 16, 16
                    if self.choices:
                        n.pop("order", None), n.pop("share", None)   # a free surface holds boxes, not flow choices
                n["w"] = min(n["w"], d["w"] - 16)
                n["h"] = min(n["h"], d["h"] - 16)
                if self.choices and self._flow(dest):
                    self._join_flow(target, dest)
                if "at" in args:
                    self._set_index(target, int(args["at"]))
                self.reflow(old)
                self.reflow(dest)
                changed += [old, dest]
            elif "before" in args or "after" in args:
                anchor = args.get("before") or args.get("after")
                if anchor not in self.nodes:
                    raise Refusal(f"no such node {anchor}")
                a = self.nodes[anchor]
                if a["parent"] and self.nodes[a["parent"]]["layout"] == "free":
                    raise Refusal(f"{a['parent']} is a free surface, so before/after would only change stacking, not position. "
                                  f"tile {a['parent']} as=row|column first, then before/after orders it"
                                  + ("; or move to=<x>,<y>" if self.coords else ""))
                if a["id"] == target or self._is_inside(a["parent"], target) if a["parent"] else True:
                    raise Refusal("bad anchor")
                old = n["parent"]
                n["parent"] = a["parent"]
                kids = [k["id"] for k in self.children(a["parent"]) if k["id"] != target]
                i = kids.index(anchor) + (0 if "before" in args else 1)
                kids.insert(i, target)
                self._order(a["parent"], kids)
                d = self.nodes[a["parent"]]
                n["w"] = min(n["w"], d["w"] - 16)
                n["h"] = min(n["h"], d["h"] - 16)
                self.reflow(old)
                self.reflow(a["parent"])
                changed += [old, a["parent"]]
            elif ("to" in args or "by" in args) and not self.coords:
                raise Refusal("this desk has no free placement; use into=, before=, after=, or tile/group the surface")
            elif "to" in args:
                if str(args["to"]) in self.nodes:
                    raise Refusal(f"to= takes x,y coordinates; to put {target} inside {args['to']} say into={args['to']}")
                if self.nodes[n["parent"]]["layout"] != "free":
                    raise Refusal("parent is tiled; use before=/after=/into=, or untile the parent")
                n["x"], n["y"] = _pair(args["to"])
            elif "by" in args:
                if self.nodes[n["parent"]]["layout"] != "free":
                    raise Refusal("parent is tiled; use before=/after=/into=, or untile the parent")
                dx, dy = _pair(args["by"])
                n["x"] += dx
                n["y"] += dy
            else:
                raise Refusal("move needs to=, by=, into=, before= or after=")
        elif verb == "resize":
            w, h = _pair(args.get("to", ""), sep="x")
            if w < 40 or h < 24:
                raise Refusal("too small")
            n["w"], n["h"] = w, h
            if self.choices and self._flow(n["parent"]):
                self._ensure_choices(n["parent"])
                n["share"] = h if self.nodes[n["parent"]]["layout"] == "column" else w
            self.reflow(n["parent"])
            if n["type"] == "surface":
                self.reflow(target)
            changed.append(n["parent"])
        elif verb == "raise":
            n["z"] = self._next_z(n["parent"])
        elif verb == "lower":
            n["z"] = min(k["z"] for k in self.children(n["parent"])) - 1
        elif verb == "remove":
            if n["type"] == "surface" and self.children(target):
                raise Refusal("surface not empty; move or remove its children first")
            del self.nodes[target]
            self.reflow(before["parent"])
            self._bump(before["parent"])
            ev = self._event(verb, target, args, {"restore": before}, actor)
            what = ("view removed; what it listed stays where it is" if n.get("layout") == "view"
                    else "empty surface removed" if n["type"] == "surface"
                    else "appearance removed; the subject still exists")
            return {"ok": True, "event": ev["id"], "changed": [target, before["parent"]], "note": what}
        elif verb == "tile":
            lay = args.get("as", "column")
            if lay not in ("column", "row"):
                raise Refusal("as= must be column or row")
            if n["layout"] == lay:
                return {"ok": True, "event": None, "changed": [], "note": f"{target} is already a {lay}; nothing changed"}
            was_free = n["layout"] == "free"
            n["layout"] = lay
            if self.choices:
                # tiling is an arrangement a person chose: order from where things are now, share from their sizes
                if was_free:
                    for k in self.nodes.values():
                        if k["parent"] == target:
                            k["order"], k["share"] = None, None
                self._ensure_choices(target)
            self.reflow(target)
            changed += [k["id"] for k in self.children(target)]
        elif verb == "untile":
            n["layout"] = "free"
            if self.choices:
                # untiling keeps where things are drawn: the derived boxes become held, the flow choices go
                for k in self.nodes.values():
                    if k["parent"] == target:
                        k.pop("order", None), k.pop("share", None)
        elif verb == "rename":
            n["title"] = str(args.get("title", n["title"]))
        elif verb == "group":
            lay = args.get("as", "free")
            gw, gh = max(200, n["w"] // 2), max(120, n["h"] // 2)
            x, y, free = self.free_spot(target, gw, gh)
            gid = self.add_surface(str(args.get("title", "group")), target, lay, x, y, gw, gh)
            self.last_created = self.last_surface = gid
            self._fair_share(gid)
            self.reflow(target)
            self._bump(target)
            ev = self._event(verb, target, args, {"delete": gid}, actor)
            r = {"ok": True, "event": ev["id"], "changed": [target, gid], "created": gid}
            if n["layout"] == "free" and not free:
                r["note"] = (f"no free space in {target}: {gid} {', '.join(self.relations(gid)) or 'covers things'}; "
                             f"move it, resize it, or tile {target} so nothing overlaps")
            return r
        elif verb == "create":
            known = {"kind", "title", "text", "due", "tags", "layout", "query", "cols", "by", "desc", "as", "x", "y", "w", "h", "at"}
            stray = [k for k in args if k not in known]
            kind = args.get("kind", "note")
            if stray and kind in ("surface", "view"):
                raise Refusal(f"create does not take {', '.join(k + '=' for k in stray)} for a {kind}; it takes kind= title= "
                              f"(layout= for a surface; query= cols= for a view)")
            props = {k: str(args[k]) for k in stray}      # Juniper: an item with a date and a place is one command, not two
            if kind not in ("note", "task", "chat", "image", "doc", "trial", "surface", "view"):
                raise Refusal("kind= must be note, task, chat, image, doc, trial, surface or view")
            title = args.get("title")
            if not title:
                raise Refusal("create needs title=")
            if n.get("layout") == "view":
                raise Refusal(f"{target} is a view: it shows a selection and holds nothing itself; create inside a real surface")
            if kind == "view":
                # round 11d: a live collection. A view is a surface whose contents are a selection, evaluated at each look.
                query = str(args.get("query", "")).strip()
                if not query:
                    raise Refusal("a view needs query=<selection>, e.g. query=kind:task,due<today")
                x, y, free = self.free_spot(target, 400, 300)
                fid = self.add_surface(str(title), target, "view", x, y, 400, 300)
                self.nodes[fid]["query"] = query
                for k in ("cols", "by", "desc"):        # a view with cols= is a table at every look
                    if str(args.get(k, "")).strip():
                        self.nodes[fid][k] = str(args[k]).strip()
                self._fair_share(fid)
                self.reflow(target)
                self.last_created = self.last_surface = fid
                self._bump(target)
                ev = self._event(verb, target, args, {"delete": fid}, actor)
                return {"ok": True, "event": ev["id"], "changed": [target, fid], "created": fid,
                        "note": f"new view {fid} of {query} inside {target}; it lists whatever matches, wherever it is"}
            if kind == "surface":
                # round 11c: a new empty panel inside this one (group <surface> did this by accident of wording)
                layout = str(args.get("layout", "column"))
                if layout not in ("free", "column", "row"):
                    raise Refusal("layout= must be free, column or row")
                x, y, free = self.free_spot(target, 400, 300)
                fid = self.add_surface(str(title), target, layout, x, y, 400, 300)
                self._fair_share(fid)
                self.reflow(target)
                self.last_created = self.last_surface = fid
                self._bump(target)
                ev = self._event(verb, target, args, {"delete": fid}, actor)
                r = {"ok": True, "event": ev["id"], "changed": [target, fid], "created": fid,
                     "note": f"new {layout} surface {fid} inside {target}"}
                if n["layout"] == "free" and not free:
                    r["note"] += f"; no free space, it covers things: move it or tile {target}"
                return r
            due = args.get("due")
            if due and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(due)):
                raise Refusal("due= must be YYYY-MM-DD")
            sid = self.add_subject(kind, str(title), str(args.get("text", "")), [t for t in str(args.get("tags", "")).split(",") if t], due)
            self.subjects[sid]["props"].update(props)
            cw, ch = max(120, min(300, n["w"] - 16)), max(80, min(160, n["h"] - 16))   # never larger than the parent
            x, y, free = self.free_spot(target, cw, ch)
            aid = self.place(sid, target, x, y, cw, ch)
            self._fair_share(aid)
            self.reflow(target)
            self.last_created = aid
            self._bump(target)
            ev = self._event(verb, target, args, {"delete": aid, "delete_subject": sid}, actor)
            r = {"ok": True, "event": ev["id"], "changed": [target, aid], "created": aid,
                 "note": f"new {kind} {sid} placed as {aid}" + (" · " + " ".join(f"{k}={v}" for k, v in props.items()) if props else "")
                         + ("; x= y= w= h= place a thing, they are not props (do prop " + aid + " y=... for a prop)" if {"x", "y", "w", "h"} & set(args) else "")}
            if n["layout"] == "free" and not free:
                r["note"] += f"; no free space, it covers things: move it or tile {target}"
            return r
        elif verb == "fold":
            n["folded"] = True
        elif verb == "unfold":
            n["folded"] = False
        for c in set(changed):
            self._bump(c)
        ev = self._event(verb, target, args, {"restore": before}, actor)
        return {"ok": True, "event": ev["id"], "changed": sorted(set(changed))}

    def _apply_subject(self, verb, sid, rev, args, actor, via=None):
        s = self.subjects[sid]
        if rev is not None and rev != s["rev"]:
            raise Refusal(f"stale: {sid} is at rev {s['rev']}, you observed {rev}; look again")
        before = deepcopy(s)
        apps = self.appearances_of(sid)
        if verb == "comment":
            line = str(args.get("line", args.get("text", ""))).strip()
            if not line:
                raise Refusal("comment needs line=")
            cid = self.add_comment(sid, "alex" if actor in ("jeff", "alex") else actor, line, actor)
            return {"ok": True, "event": self.events[-1]["id"], "changed": [sid] + apps, "created": cid,
                    "note": f"comment {cid} added on {sid}"}
        if verb == "resolve":
            cid = str(args.get("id", args.get("comment", "")))
            owner, c = self.find_comment(cid)
            if owner is None or owner["id"] != sid:
                raise Refusal(f"{cid} is not a comment on {sid}; read {sid} to see its comments")
            if c["resolved"]:
                raise Refusal(f"{cid} is already resolved")
            reply = str(args.get("line", "")).strip()
            if reply:
                c["replies"].append({"by": "alex" if actor in ("jeff", "alex") else actor, "text": reply})
            c["resolved"] = True
            s["rev"] += 1
            for a in apps:
                self._bump(a)
            ev = self._event("resolve", via or sid, {"id": cid, "line": reply}, {"reopen": cid}, actor)
            ev["changed"] = [sid] + apps
            return {"ok": True, "event": ev["id"], "changed": [sid] + apps,
                    "note": f"{cid} by {c['by']} resolved" + (f' with reply "{reply}"' if reply else
                                                              " without a reply (line=\"...\" answers it as it closes)")}
        if verb == "check":
            items = self.checklist(s["text"])
            if not items:
                raise Refusal(f"{sid} has no checklist lines (- [ ] ...)")
            try:
                k = int(args.get("item", 0)) - 1
                i, l = items[k]
            except (ValueError, IndexError):
                raise Refusal(f"item= must be 1..{len(items)}")
            lines = s["text"].splitlines()
            lines[i] = l.replace("- [ ]", "- [x]", 1) if "- [ ]" in l else l.replace("- [x]", "- [ ]", 1)
            s["text"] = "\n".join(lines)
            s["rev"] += 1
            for a in apps:
                self._bump(a)
            ev = self._event("check", via or sid, args, {"restore_subject": before}, actor)
            ev["changed"] = [sid] + apps
            return {"ok": True, "event": ev["id"], "changed": [sid] + apps, "note": f"item {k + 1} is now: {lines[i].strip()}"}
        if verb == "link":
            lid = self.add_link(sid, args.get("to", ""), args.get("as", "refers"), actor)
            l = self.links[-1]
            return {"ok": True, "event": self.events[-1]["id"], "changed": self.events[-1]["changed"], "created": lid,
                    "note": f"{lid}: {l['from']} {l['kind']} {l['to']}"}
        if verb == "unlink":
            lid = str(args.get("id", ""))
            l = next((x for x in self.links if x["id"] == lid), None)
            if not l or sid not in (l["from"], l["to"]):
                raise Refusal(f"{lid} is not a link of {sid}")
            self.links.remove(l)
            s["rev"] += 1
            for a in apps:
                self._bump(a)
            ev = self._event("unlink", via or sid, args, {"restore_link": l}, actor)
            ev["changed"] = [sid] + apps
            return {"ok": True, "event": ev["id"], "changed": [sid] + apps, "note": f"{lid} removed"}
        if verb == "append" and args.get("section"):
            name = str(args["section"]).strip().lower()
            secs = self.sections(s["text"])
            if not any(h and h.lower() == name for h, _ in secs):
                raise Refusal(f"no section {args['section']!r} in {sid}; sections: " + ", ".join(h for h, _ in secs if h))
            out = []
            for h, body in secs:
                if h is not None:
                    out.append("## " + h)
                if body:
                    out.append(body)
                if h and h.lower() == name:
                    out.append(str(args.get("line", args.get("text", ""))))
            args = {"text": "\n".join(out)}
            verb = "edit"
        if verb == "append":
            args = {"append": args.get("line", args.get("text", args.get("append", "")))}
            verb = "edit"
        elif verb == "retitle":
            args = {"title": args.get("title", args.get("text", ""))}
            verb = "edit"
        elif verb == "rewrite":
            new = str(args.get("text", args.get("line", "")))
            if args.get("section"):
                # Moss: 1.2 KB to read a document, 49 KB to change one word in it. A change may be as small as a section.
                want = str(args["section"]).lstrip("# ").strip().lower()
                secs = self.sections(s["text"])
                hits = [k for k, (h, _) in enumerate(secs) if (h or "(before the first heading)").lower() == want]
                if len(hits) != 1:
                    heads = ", ".join(repr(h) for h, _ in secs if h) or "none"
                    raise Refusal(f"rewrite section={args['section']!r}: {'no such section' if not hits else 'more than one section has that heading'}. Sections here: {heads}")
                secs[hits[0]] = (secs[hits[0]][0], new.strip("\n"))
                new = "\n\n".join((f"## {h}\n" if h else "") + b for h, b in secs)
            args = {"text": new}
            verb = "edit"
        signed_note = ""
        if verb == "edit":
            if not any(k in args for k in ("title", "text", "append")):
                raise Refusal("edit needs title=, text= or append=")
            if "title" in args:
                s["title"] = str(args["title"])
            if "text" in args:
                s["text"] = str(args["text"])
            if "append" in args:
                line = str(args["append"])
                if s["kind"] == "chat":
                    # Juniper a484, Sable a656: the world signs every chat line with the event's actor, by display name.
                    # A typed "Name:" that is the actor's own is dropped (the world signs now, and the receipt says so);
                    # one naming anyone else stays as plain words after the real signature ("Juniper: Jeff: ...").
                    # A world verb runs as its caller and a rule as its author, so they sign as those.
                    line, dropped = self.sign_chat_line(line, actor)
                    args = dict(args, append=line, signed=self.display_name(actor))
                    if dropped:
                        signed_note = "the world signs for you; your typed name was dropped"
                s["text"] = (s["text"].rstrip("\n") + "\n" + line).strip("\n")
        elif verb == "place":
            dest = args.get("into")
            if dest not in self.nodes or self.nodes[dest]["type"] != "surface":
                raise Refusal("place needs into=<surface>")
            aid = self.place(sid, dest, 16, 16, 300, 160)
            self._bump(dest)
            ev = self._event(verb, sid, args, {"delete": aid}, actor)
            return {"ok": True, "event": ev["id"], "changed": [dest, aid], "created": aid}
        else:
            raise Refusal(f"{verb} is not a verb of subject {sid}")
        s["rev"] += 1
        apps = self.appearances_of(sid)
        for a in apps:
            self._bump(a)
        ev = self._event(verb, via or sid, args, {"restore_subject": before}, actor)
        note = f"subject {sid} changed; {len(apps)} appearance(s) now show the new content"
        if args.get("signed"):
            note += f"\n  said: {args['append']}" + (f"  ({signed_note})" if signed_note else "")
        if "text" in args:
            old_lines = [l for l in before["text"].splitlines() if l.strip()]
            new_lines = [l for l in s["text"].splitlines() if l.strip()]
            dropped = [l for l in old_lines if l not in new_lines]
            if dropped:
                who = {}
                for e in self.events:
                    if e["verb"] == "edit" and (e["target"] == sid or e["target"] in apps + [sid]) and e["args"].get("append"):
                        who[e["args"]["append"].strip()] = f"added by {e['by']}, {e['id']}"
                note += "\n  dropped " + str(len(dropped)) + " line(s): " + "; ".join(
                    f'"{l}"' + (f" ({who[l.strip()]})" if l.strip() in who else "") for l in dropped)
        return {"ok": True, "event": ev["id"], "changed": [sid] + apps, "note": note}

    def undo(self, event_id):
        ev = next((e for e in self.events if e["id"] == event_id), None)
        if not ev:
            raise Refusal(f"no event {event_id}")
        if ev.get("undone") or ev["verb"] == "undo":
            raise Refusal(f"{event_id} cannot be undone (already undone or is an undo)")
        later = [e for e in self.events if int(e["id"][1:]) > int(event_id[1:]) and not e.get("undone")
                 and e["verb"] != "undo" and (e["target"] == ev["target"] or ev["target"] in (e.get("changed") or []))]
        if later:
            raise Refusal(f"{event_id} is not the latest change to {ev['target']}; {later[-1]['id']} came after it. undo that first, or act on the current state")
        u = ev["undo"]
        if u.get("external"):
            raise Refusal(f"{event_id} had an effect outside the desk ({ev['verb']}); undo cannot take it back")
        if "restore" in u:
            r = deepcopy(u["restore"])
            r["rev"] = (self.nodes[r["id"]]["rev"] if r["id"] in self.nodes else r["rev"]) + 1
            self.nodes[r["id"]] = r
            if r["parent"]:
                self.reflow(r["parent"])
                self._bump(r["parent"])
        elif "restore_props" in u:
            nid, props = u["restore_props"]
            if nid in self.nodes:
                self.nodes[nid]["props"] = dict(props)
                self._bump(nid)
        elif "restore_subject" in u:
            r = deepcopy(u["restore_subject"])
            r["rev"] = self.subjects[r["id"]]["rev"] + 1
            self.subjects[r["id"]] = r
            for a in self.appearances_of(r["id"]):
                self._bump(a)
        elif "drop_comment" in u:
            owner, c = self.find_comment(u["drop_comment"])
            if owner:
                owner["comments"].remove(c)
                owner["rev"] += 1
        elif "reopen" in u:
            owner, c = self.find_comment(u["reopen"])
            if c:
                c["resolved"] = False
                c["replies"] = c["replies"][:-1] if c["replies"] else []
                owner["rev"] += 1
        elif "drop_link" in u:
            self.links = [l for l in self.links if l["id"] != u["drop_link"]]
        elif "restore_link" in u:
            self.links.append(u["restore_link"])
        elif "reorder" in u:           # a tiled swap: put the flow back in its old order
            fid, order = u["reorder"]
            if fid in self.nodes:
                kids = [k["id"] for k in self.children(fid)]
                order = [k for k in order if k in kids] + [k for k in kids if k not in order]
                self._order(fid, order)
                for k in [k for i, k in enumerate(order) if kids[i] != k] + [fid]:
                    self._bump(k)
        elif "delete" in u:
            gone = self.nodes.pop(u["delete"], None)
            if gone and gone["parent"]:
                self.reflow(gone["parent"])
                self._bump(gone["parent"])
            if u.get("delete_subject"):
                self.subjects.pop(u["delete_subject"], None)
        ev["undone"] = True
        ev2 = self._event("undo", event_id, {}, {}, note=f"reverted {event_id}")
        return {"ok": True, "event": ev2["id"], "reverted": event_id}

    def free_spot(self, fid, w, h):
        """A position inside fid where a w x h box overlaps nothing. Returns (x, y, found)."""
        f = self.nodes[fid]
        if f["layout"] != "free":
            return 10 ** 6, 10 ** 6, True   # tiled: land at the end; reflow sets the real position
        kids = [self.nodes[k["id"]] for k in self.children(fid)]
        w = min(w, max(40, f["w"] - 16))
        h = min(h, max(24, f["h"] - 16))
        step = 40
        for y in range(8, max(9, f["h"] - h - 7), step):
            for x in range(8, max(9, f["w"] - w - 7), step):
                if all(min(x + w, k["x"] + k["w"]) - max(x, k["x"]) <= 0 or min(y + h, k["y"] + k["h"]) - max(y, k["y"]) <= 0 for k in kids):
                    return x, y, True
        return 16, 16, False

    def _is_inside(self, nid, ancestor):
        p = self.nodes[nid]["parent"]
        while p:
            if p == ancestor:
                return True
            p = self.nodes[p]["parent"]
        return False

    def _order(self, fid, ids):
        if self.choices and self._flow(fid):
            self._reorder(fid, ids)
            self.reflow(fid)
            return
        f = self.nodes[fid]
        for i, k in enumerate(ids):
            if f["layout"] == "row":
                self.nodes[k]["x"] = i * 1000
            else:
                self.nodes[k]["y"] = i * 1000
            self.nodes[k]["z"] = i + 1
        self.reflow(fid)

    def _set_index(self, nid, index):
        fid = self.nodes[nid]["parent"]
        kids = [k["id"] for k in self.children(fid) if k["id"] != nid]
        kids.insert(max(0, min(index, len(kids))), nid)
        self._order(fid, kids)

    def snapshot(self):
        return {"subjects": deepcopy(self.subjects), "nodes": deepcopy(self.nodes), "links": deepcopy(self.links)}


def _pair(text, sep=","):
    try:
        a, b = str(text).lower().replace(" ", "").split(sep)
        return int(a), int(b)
    except Exception:
        raise Refusal(f"expected <a>{sep}<b>, got {text!r}")
