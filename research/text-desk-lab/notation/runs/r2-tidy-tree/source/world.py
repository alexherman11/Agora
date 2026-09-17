"""A small synthetic desk, built to be read and written as text.

Ontology (same words as Agora, independent implementation):
  subject     content with identity (note, task, image, chat). Has text, tags, rev.
  appearance  a placement of a subject on a surface: x, y, w, h, z, rev.
  surface     a container with a layout: free (bag of rectangles), column, row.
The same subject may appear several times. Editing a subject edits every appearance.
Every mutation is an event with an undo; mutations are fenced on the observed rev.
"""

from copy import deepcopy
import itertools

SCREEN = (1280, 800)


class Refusal(Exception):
    pass


class World:
    def __init__(self):
        self.subjects = {}
        self.nodes = {}  # surfaces and appearances, keyed by id
        self.events = []
        self.injections = []
        self._ids = itertools.count(1)
        self.root = self.add_surface("desk", None, "free", 0, 0, *SCREEN)

    # ---- construction -------------------------------------------------
    def _id(self, prefix):
        return f"{prefix}{next(self._ids):02d}"

    def add_subject(self, kind, title, text="", tags=(), due=None):
        sid = self._id("s")
        self.subjects[sid] = {
            "id": sid, "kind": kind, "title": title, "text": text,
            "tags": list(tags), "due": due, "rev": 1,
        }
        return sid

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
        self.reflow(parent)
        return aid

    def _next_z(self, parent):
        sib = [n["z"] for n in self.nodes.values() if n["parent"] == parent]
        return (max(sib) + 1) if sib else 1

    # ---- queries ------------------------------------------------------
    def children(self, fid):
        kids = [n for n in self.nodes.values() if n["parent"] == fid]
        lay = self.nodes[fid]["layout"]
        if lay == "free":
            return sorted(kids, key=lambda n: n["z"])
        return sorted(kids, key=lambda n: (n["y"], n["x"]) if lay == "column" else (n["x"], n["y"]))

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
        kids = self.children(fid)
        if not kids:
            return
        gap = 8
        n = len(kids)
        if f["layout"] == "column":
            share = max(24, (f["h"] - gap * (n + 1)) // n)
            y = gap
            for k in kids:
                k["x"], k["y"], k["w"], k["h"] = gap, y, f["w"] - 2 * gap, share
                y += share + gap
        else:
            share = max(40, (f["w"] - gap * (n + 1)) // n)
            x = gap
            for k in kids:
                k["x"], k["y"], k["w"], k["h"] = x, gap, share, f["h"] - 2 * gap
                x += share + gap
        for k in kids:
            if k["type"] == "surface":
                self.reflow(k["id"])

    # ---- mutation -----------------------------------------------------
    def _bump(self, nid):
        if nid in self.nodes:
            self.nodes[nid]["rev"] += 1

    def _event(self, verb, target, args, undo, actor="jeff", note=""):
        ev = {"id": f"e{len(self.events) + 1}", "verb": verb, "target": target,
              "args": deepcopy(args), "undo": undo, "note": note, "by": actor}
        self.events.append(ev)
        return ev

    def fence(self, nid, rev):
        cur = self.nodes[nid]["rev"] if nid in self.nodes else self.subjects[nid]["rev"]
        if rev != cur:
            raise Refusal(f"stale: {nid} is at rev {cur}, you observed {rev}; look again")

    coords = True  # False = tree variant: no coordinate verbs on free surfaces

    TEXT_VERBS = {
        "append": "line=<str>  (adds a line at the end; edits the subject, so every appearance changes)",
        "retitle": "title=<str>",
        "rewrite": "text=<str>  (replaces all the text; write \\n between lines)",
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
        else:
            v["unfold" if n["folded"] else "fold"] = "(show/hide content on screen)"
            v.update(self.TEXT_VERBS)
        return v

    def apply(self, verb, target, rev, args, actor="jeff"):
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
        if verb in ("append", "retitle", "rewrite", "edit"):
            if n["type"] != "appearance":
                raise Refusal(f"{verb} needs an appearance or subject, not a surface")
            return self._apply_subject(verb, n["subject"], None, args, actor, via=target)
        if verb == "move":
            if "into" in args and not ("before" in args or "after" in args):
                dest = args["into"]
                if dest not in self.nodes or self.nodes[dest]["type"] != "surface":
                    raise Refusal(f"into= must name a surface, not {dest}")
                if dest == target or self._is_inside(dest, target):
                    raise Refusal("cannot move a surface into itself")
                old = n["parent"]
                n["parent"] = dest
                n["z"] = self._next_z(dest)
                d = self.nodes[dest]
                if d["layout"] == "free":
                    n["x"], n["y"] = 16, 16
                n["w"] = min(n["w"], d["w"] - 16)
                n["h"] = min(n["h"], d["h"] - 16)
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
            return {"ok": True, "event": ev["id"], "changed": [target, before["parent"]],
                    "note": "appearance removed; the subject still exists"}
        elif verb == "tile":
            lay = args.get("as", "column")
            if lay not in ("column", "row"):
                raise Refusal("as= must be column or row")
            n["layout"] = lay
            self.reflow(target)
            changed += [k["id"] for k in self.children(target)]
        elif verb == "untile":
            n["layout"] = "free"
        elif verb == "rename":
            n["title"] = str(args.get("title", n["title"]))
        elif verb == "group":
            lay = args.get("as", "free")
            gid = self.add_surface(str(args.get("title", "group")), target, lay, 16, 16,
                                   max(200, n["w"] // 2), max(120, n["h"] // 2))
            self.reflow(target)
            self._bump(target)
            ev = self._event(verb, target, args, {"delete": gid}, actor)
            return {"ok": True, "event": ev["id"], "changed": [target, gid], "created": gid}
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
        if verb == "append":
            args = {"append": args.get("line", args.get("text", args.get("append", "")))}
            verb = "edit"
        elif verb == "retitle":
            args = {"title": args.get("title", args.get("text", ""))}
            verb = "edit"
        elif verb == "rewrite":
            args = {"text": args.get("text", args.get("line", ""))}
            verb = "edit"
        if verb == "edit":
            if not any(k in args for k in ("title", "text", "append")):
                raise Refusal("edit needs title=, text= or append=")
            if "title" in args:
                s["title"] = str(args["title"])
            if "text" in args:
                s["text"] = str(args["text"])
            if "append" in args:
                s["text"] = (s["text"].rstrip("\n") + "\n" + str(args["append"])).strip("\n")
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
        return {"ok": True, "event": ev["id"], "changed": [sid] + apps,
                "note": f"subject {sid} changed; {len(apps)} appearance(s) now show the new content"}

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
        if "restore" in u:
            r = deepcopy(u["restore"])
            r["rev"] = (self.nodes[r["id"]]["rev"] if r["id"] in self.nodes else r["rev"]) + 1
            self.nodes[r["id"]] = r
            if r["parent"]:
                self.reflow(r["parent"])
                self._bump(r["parent"])
        elif "restore_subject" in u:
            r = deepcopy(u["restore_subject"])
            r["rev"] = self.subjects[r["id"]]["rev"] + 1
            self.subjects[r["id"]] = r
            for a in self.appearances_of(r["id"]):
                self._bump(a)
        elif "delete" in u:
            gone = self.nodes.pop(u["delete"], None)
            if gone and gone["parent"]:
                self.reflow(gone["parent"])
        ev["undone"] = True
        ev2 = self._event("undo", event_id, {}, {}, note=f"reverted {event_id}")
        return {"ok": True, "event": ev2["id"], "reverted": event_id}

    def _is_inside(self, nid, ancestor):
        p = self.nodes[nid]["parent"]
        while p:
            if p == ancestor:
                return True
            p = self.nodes[p]["parent"]
        return False

    def _order(self, fid, ids):
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
        return {"subjects": deepcopy(self.subjects), "nodes": deepcopy(self.nodes)}


def _pair(text, sep=","):
    try:
        a, b = str(text).lower().replace(" ", "").split(sep)
        return int(a), int(b)
    except Exception:
        raise Refusal(f"expected <a>{sep}<b>, got {text!r}")
