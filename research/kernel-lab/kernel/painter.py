"""The painter's routes on the kernel, through the desk's own lens compiler (SHAPE section 12: the facade).

lens.js and its pages (research/text-desk-lab/notation/desk-shell/) are served unchanged. A scene is built by the desk's
scene.py and lens_ir.py over a desk World made, for each reader, from the kernel things that reader may see. Nothing of
the desk is changed, and nothing is written into its folder: its modules are imported with bytecode caching off and
with its lens reuse cache (which can write a file) turned off.

The id map is fixed by the kernel's numbers, so it is the same for every build and every reader:
    kernel sb42  ->  desk subject s42, its appearances a(42*8 + k), and, for a group or the place, surface f42
A gesture comes back as a desk line (`do like a337`) with what it observed; both are translated back to kernel ids and
kernel revs (a desk rev here IS the kernel rev), and the line runs as an ordinary kernel line with that as its `saw`.

Not carried: a selection membership read in `observed` (the kernel fences things, not selections), the house's rows,
promises, persons' props, comments and links (kernel things have none yet), and events (the World has none, so
`by changed` and `age<` see nothing).
"""
import hashlib
import json
import os
import re
import sys
import threading
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
NOTATION = LAB.parent / "text-desk-lab" / "notation"
STATIC = NOTATION / "desk-shell"
SKIP = {"world", "word", "grant", "invite"}          # kernel things a view never needs
_IMPORT = threading.Lock()
_DESK = {}


def desk_modules():
    """The desk's World, DeskKnife, scene and style modules, imported once, read-only."""
    with _IMPORT:
        if not _DESK:
            was = sys.dont_write_bytecode
            sys.dont_write_bytecode = True               # never write __pycache__ into the desk's folder
            os.environ["LENS_REUSE"] = "off"             # its reuse check can append to house-state/lens-reuse.err
            if str(NOTATION) not in sys.path:
                sys.path.append(str(NOTATION))
            try:
                import world as W
                import desk_knife as DK
                import scene as S
                import style as ST
            finally:
                sys.dont_write_bytecode = was
            _DESK.update(World=W.World, DeskKnife=DK.DeskKnife, scene=S, style=ST)
    return _DESK


def painter_version():
    h = hashlib.sha1()
    for p in sorted(x for x in STATIC.rglob("*") if x.is_file()):
        h.update(str(p.relative_to(STATIC)).encode() + b"\0" + p.read_bytes() + b"\0")
    return h.hexdigest()[:12]


class Facade:
    def __init__(self, kernel):
        self.k = kernel
        self.lock = threading.Lock()                     # the desk compiler keeps module-level caches: one build at a time
        self.version = None

    # ------------------------------------------------------------------ ids
    def num(self, t):
        tag = self.k.tag
        return int(t[len(tag):]) if t.startswith(tag) and t[len(tag):].isdigit() else None

    def to_kernel(self, desk_id):
        m = re.fullmatch(r"([asf])(\d+)", str(desk_id or ""))
        if not m:
            return None
        n = int(m.group(2))
        t = f"{self.k.tag}{n // 8 if m.group(1) == 'a' else n}"
        return t if t in self.k.state.things else None

    def line_to_kernel(self, line):
        """A gesture's line, its desk ids put back as kernel ids (only ids the kernel has; other words stay)."""
        def swap(m):
            return self.to_kernel(m.group(0)) or m.group(0)
        return re.sub(r"(?<![\w$.])[asf]\d+(?![\w.])", swap, line)

    # what the desk calls an aspect of a painted thing -> the kernel aspects it was made from (see desk_for)
    ASPECTS = {"title": ["title", "name", "label", "text"], "text": ["text"], "tags": ["kind"], "place": ["in:*"],
               "prop:likes": ["like:*"], "prop:by": ["made_by"], "prop:pinned": ["pinned"], "prop:for": ["for"]}

    def saw_of(self, observed):
        """What a painted gesture read -> the kernel's `saw`: thing -> {rev it was painted at, kernel aspects read}."""
        saw = {}
        if not isinstance(observed, dict):
            return saw

        def note(desk_id, rev, aspects=()):
            t = self.to_kernel(str(desk_id))
            if t is None or not isinstance(rev, int):
                return
            s = saw.setdefault(t, {"rev": rev, "aspects": []})
            s["rev"] = min(rev, s["rev"])
            for a in aspects or ():
                # a fact's `<key>_title` (desk_for) was read from the fact `<key>`
                plain = [a[5:-6] if a.endswith("_title") else a[5:]] if a.startswith("prop:") else []
                for x in self.ASPECTS.get(a, plain):
                    if x not in s["aspects"]:
                        s["aspects"].append(x)
        note(observed.get("item"), observed.get("rev"))
        for r in observed.get("reads") or []:
            if isinstance(r, list) and len(r) >= 2 and r[0] != "select":
                note(r[0], r[1], r[2] if len(r) > 2 and isinstance(r[2], list) else ())
        return saw

    # ------------------------------------------------------------------ the World
    def desk_for(self, reader):
        """A desk over what `reader` (a person id) may see, built fresh. Called with self.lock held."""
        D = desk_modules()
        k = self.k
        with k.lock:
            w = D["World"]()
            w.nodes[w.root]["layout"] = "row"
            w.equal_share = False
            d = D["DeskKnife"](w, "lean")
            d.batch, d.lean, d.read_cap, d.ids = True, True, 4, {}
            w.me = (k.name(reader) or "someone")
            groups = sorted((t for t in k.state.things if k.state.get(t, "kind") in ("place", "group")
                             and k.shown(reader, t) is not None), key=self.num)
            for g in groups:
                parents = [p for p in k.groups_of(g) if p in groups]
                fid = f"f{self.num(g)}"
                w.nodes[fid] = {"id": fid, "type": "surface", "title": k.name(g),
                                "parent": f"f{self.num(parents[0])}" if parents else w.root,
                                "layout": "column", "x": 0, "y": 0, "w": 640, "h": 800, "z": 1,
                                "rev": k.state.rev.get(g, 0), "props": {"is": k.state.get(g, "kind")}}
            w.nodes["f0"] = {"id": "f0", "type": "surface", "title": "elsewhere", "parent": w.root, "layout": "column",
                             "x": 0, "y": 0, "w": 640, "h": 800, "z": 1, "rev": 0, "props": {}}
            for t in sorted(k.state.things, key=lambda t: self.num(t) or 0):
                n = self.num(t)
                kind = k.state.get(t, "kind")
                if n is None or kind in SKIP or kind in ("place", "group"):
                    continue
                a = k.shown(reader, t)
                if a is None:
                    continue
                sid = f"s{n}"
                tags = [kind] + (["lens"] if kind == "lens" else []) + (["style"] if kind == "style" else [])
                title = a.get("title") or a.get("name") or a.get("label") or (a.get("text") or "").split("\n")[0][:80]
                if kind == "person" or kind == "agent":
                    title = k.name(t)
                props = {}
                for key, v in a.items():
                    if key in ("text", "title", "kind") or key.startswith(("in:", "sees", "member:", "like:", "claim:",
                                                                           "contact:")):
                        continue
                    if isinstance(v, str) and self.num(v) is not None and k.shown(reader, v) is not None:
                        # a fact naming another thing (about=, meeting=, now=): the desk id of that thing, so a
                        # lens's `about=$i.id` compares, and its title beside it for printing
                        other = k.shown(reader, v)
                        props[key] = f"s{self.num(v)}"
                        props[f"{key}_title"] = str(other.get("title") or other.get("name") or
                                                    (other.get("text") or "").split("\n")[0][:80])
                        continue
                    props[key] = v if isinstance(v, str) else json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                for key in ("made_by", "pinned", "for"):
                    if a.get(key):
                        props[{"made_by": "by", "pinned": "pinned", "for": "for"}[key]] = k.name(a[key])
                if kind == "post":
                    props["likes"] = str(a.get("likes", 0))     # `pinned` only when it is: `by pinned` puts those first
                w.subjects[sid] = {"id": sid, "kind": "note", "title": title, "text": a.get("text", "") if kind != "post"
                                   else a.get("text", ""), "tags": tags, "due": None, "rev": k.state.rev.get(t, 0),
                                   "comments": [], "props": props}
                places = sorted(((g, a2) for g, a2 in [(g, k.state.get(t, f"in:{g}")) for g in k.groups_of(t)]
                                 if f"f{self.num(g)}" in w.nodes), key=lambda p: -(p[1] if isinstance(p[1], int) else 0))
                for i, (g, _) in enumerate(places[:8] or [(None, 0)]):
                    aid = f"a{n * 8 + i}"
                    w.nodes[aid] = {"id": aid, "type": "appearance", "subject": sid,
                                    "parent": f"f{self.num(g)}" if g else "f0", "x": 0, "y": 0, "w": 600, "h": 40,
                                    "z": 1, "folded": False, "rev": k.state.rev.get(t, 0)}
            w._ids = 10 ** 9                             # anything the desk mints stays clear of the map's ids
            for fid in [x for x, nd in w.nodes.items() if nd["type"] == "surface"]:
                w.reflow(fid)
        return d

    # ------------------------------------------------------------------ the routes
    def scene(self, reader, q):
        D = desk_modules()
        S = D["scene"]
        with self.lock:
            d = self.desk_for(reader)
            try:
                sc, text = S.scene_for(d, q.get("lens", ""), on=None, text=q.get("text") != "0")
                if q.get("view") == "painter":
                    sc = dict(S.painter_view(sc), **{"def": sc.get("def")})
                    keys = set(q.get("keys", "Enter,Tab,Shift+Tab,Backspace").split(","))
                    for node in S._walk(sc):
                        node["acts"] = [a for a in node["acts"] if a.get("on") != "key" or a.get("label") in keys]
                out = {"scene": sc, "text": text, "events_total": len(self.k.log.records)}
            except S.LensRefusal as e:
                out = {"refused": str(e), "events_total": len(self.k.log.records)}
            except Exception as e:                      # noqa: BLE001  a compiler fault arrives as a refusal
                out = {"refused": f"the lens compiler failed ({type(e).__name__}: {e})",
                       "events_total": len(self.k.log.records)}
        body = json.dumps(out, ensure_ascii=False)
        out["gen"] = "g" + hashlib.sha1(body.encode()).hexdigest()[:16]
        if q.get("have") == out["gen"]:
            return {"same": True, "gen": out["gen"]}
        return out

    def style(self, reader, q):
        D = desk_modules()
        with self.lock:
            d = self.desk_for(reader)
            st = D["scene"].style_source(d, q.get("name") or "calm")
        return D["style"].for_painter(st, q.get("theme")) if st else {"refused": f"no style {q.get('name')!r}"}

    def version_info(self):
        if self.version is None:
            self.version = painter_version()
        return {"code": "kernel", "painter": self.version, "shape": desk_modules()["scene"].PAINTER_SHAPE}

    def do(self, actor, body):
        """/api/do from a painted page: the gesture's line and what it observed, as a kernel line with its `saw`."""
        line = self.line_to_kernel(str(body.get("line") or ""))
        observed = body.get("observed")
        saw = self.saw_of(observed) if observed else None
        out = self.k.run(actor, line, press=body.get("gesture"), saw=saw)
        return {"text": out["text"], "error": None if out["ok"] else out["text"], "line": line,
                "events_total": len(self.k.log.records), "as": self.k.name(actor.id),
                "created": out.get("made", []), "code": "kernel"}


TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css",
         ".json": "application/json", ".png": "image/png", ".svg": "image/svg+xml", ".style": "text/plain; charset=utf-8",
         ".woff2": "font/woff2", ".ico": "image/x-icon"}


def static_file(path):
    """A painter file from desk-shell, read-only, never outside it. -> (bytes, content type) or None."""
    rel = path.lstrip("/") or "lens.html"
    p = (STATIC / rel).resolve()
    if STATIC.resolve() not in p.parents or not p.is_file():
        return None
    return p.read_bytes(), TYPES.get(p.suffix, "application/octet-stream")
