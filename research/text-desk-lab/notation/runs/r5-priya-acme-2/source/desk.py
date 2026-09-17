"""Text notations over the World, plus a one-line REPL grammar.

Experiments carried by this module:
  * fold-as-budget: level 1 = one folded line, level 2 = opened (children folded), level 3 = focus.
  * seen-fencing: `do` is refused unless the caller has seen the target at its current rev.
    Lines carry no revision numbers; the desk remembers what it showed you.
  * delta header: every look begins with what changed since your last look.
  * relations variant: geometry printed as spatial relations, coordinates on request.
  * apply variant: edit the outline text, the desk diffs it into operations.
"""

import re
import shlex
from copy import deepcopy

from world import Refusal, SCREEN, World

HELP = """commands (one per call):
  look [id] [:1|:2|:3]   outline from id (default desk). :1 folded line, :2 open (default), :3 focus
  open id | close id     expand / collapse id in later looks (view only; nothing moves)
  read id                full text of a note/task/etc (via an appearance or subject id)
  where id               exact geometry and spatial relations
  verbs id               what you can do to id, with argument forms
  pivot id               appearance -> its subject and every place it appears; subject -> appearances
  find words             search titles and text
  history [id]           recent events (with undo ids)
  do verb id k=v ...     change something. e.g. do move a04 into=f02   do append a03 line="new item"
  undo eN                revert an event
  plan / apply           (apply variant only) paste an edited outline; the desk diffs it into ops
ids: f.. surface, a.. appearance, s.. subject, e.. event. quote values with spaces."""


class Desk:
    def __init__(self, world: World, variant="outline"):
        self.world = world
        self.variant = variant
        self.open = {world.root}
        self.seen = {}          # id -> rev last shown to the caller
        self.last_event_seen = 0
        self.injections = world.injections
        self.hooks = []         # callables run after each successful mutation (for scenarios)
        self.world.coords = variant != "tree"
        self.hide_coords = variant in ("relations", "tree")

    # ---- public harness surface -------------------------------------
    @property
    def events(self):
        return self.world.events

    def snapshot(self):
        return self.world.snapshot()

    def dispatch(self, name, args):
        header = self.delta_header()
        r = self._dispatch(name, args)
        if header:
            if "text" in r:
                r["text"] = header + r["text"]
            else:
                r["error"] = header + r["error"]
        return r

    def _dispatch(self, name, args):
        try:
            if name == "desk":
                line = args.get("line", "")
                return {"text": self.repl(line)}
            if name == "look":
                return {"text": self.repl(f"look {args.get('target', '')} :{args.get('level', 2)}".strip())}
            if name == "open":
                return {"text": self.repl(f"open {args.get('target', '')}")}
            if name == "read":
                return {"text": self.repl(f"read {args.get('target', '')}")}
            if name == "where":
                return {"text": self.repl(f"where {args.get('target', '')}")}
            if name == "verbs":
                return {"text": self.repl(f"verbs {args.get('target', '')}")}
            if name == "pivot":
                return {"text": self.repl(f"pivot {args.get('target', '')}")}
            if name == "find":
                return {"text": self.repl(f"find {args.get('words', '')}")}
            if name == "history":
                return {"text": self.repl(f"history {args.get('target', '')}".strip())}
            if name == "undo":
                return {"text": self.repl(f"undo {args.get('event', '')}")}
            if name == "do":
                return {"text": self.cmd_do(args.get("verb"), args.get("target"), dict(args.get("args") or {}))}
            return {"error": f"unknown tool {name}"}
        except Refusal as r:
            return {"error": str(r)}

    # ---- repl -------------------------------------------------------
    def repl(self, line):
        line = (line or "").strip()
        if not line:
            return HELP
        first = line.split(None, 1)[0].lower()
        if first in ("plan", "apply"):
            head, _, rest = line.partition("\n")
        else:
            head, rest = line, ""
        try:
            words = shlex.split(head)
        except ValueError as e:
            raise Refusal(f"could not parse: {e}")
        cmd, argv = words[0].lower(), words[1:]
        argv = [a.lstrip("@") for a in argv]
        if cmd in ("help", "?"):
            return HELP
        if cmd == "look":
            level = 2
            target = None
            for a in argv:
                if a.startswith(":") and a[1:].isdigit():
                    level = int(a[1:])
                else:
                    target = a
            return self.cmd_look(target, level)
        if cmd in ("open", "close"):
            if not argv:
                raise Refusal(f"{cmd} needs an id")
            return self.cmd_fold(argv[0], cmd == "open")
        if cmd == "read":
            return self.cmd_read(argv[0] if argv else None)
        if cmd == "where":
            return self.cmd_where(argv[0] if argv else None)
        if cmd == "verbs":
            return self.cmd_verbs(argv[0] if argv else None)
        if cmd == "pivot":
            return self.cmd_pivot(argv[0] if argv else None)
        if cmd == "find":
            return self.cmd_find(" ".join(argv))
        if cmd == "history":
            return self.cmd_history(argv[0] if argv else None)
        if cmd == "undo":
            return self.cmd_undo(argv[0] if argv else None)
        if cmd == "do":
            if len(argv) < 2:
                raise Refusal("do needs: do <verb> <id> [k=v ...]")
            kv = {}
            for a in argv[2:]:
                k, eq, v = a.partition("=")
                if not eq:
                    raise Refusal(f"argument {a!r} must be key=value")
                kv[k] = v
            if argv[1].lower() in self._verb_names() and argv[0].lower() not in self._verb_names():
                return self.cmd_do(argv[1], argv[0], kv)
            return self.cmd_do(argv[0], argv[1], kv)
        if cmd in ("plan", "apply"):
            if self.variant != "apply":
                raise Refusal("plan/apply are not available in this desk; use do")
            return self.cmd_apply(rest, dry=(cmd == "plan"))
        raise Refusal(f"unknown command {cmd!r}; try help")

    def _verb_names(self):
        return {"move", "resize", "raise", "lower", "remove", "tile", "untile", "rename", "group", "fold", "unfold",
                "edit", "append", "retitle", "rewrite", "place"}

    # ---- rendering --------------------------------------------------
    def _resolve(self, ident, allow_subject=True):
        if not ident:
            raise Refusal("which id?")
        ident = ident.lstrip("@")
        if ident in ("desk", "root"):
            return self.world.root
        if ident in self.world.nodes:
            return ident
        if allow_subject and ident in self.world.subjects:
            return ident
        hits = [n["id"] for n in self.world.nodes.values() if self.world.title(n).lower() == ident.lower()]
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            raise Refusal(f"{ident!r} names {len(hits)} things: {', '.join(hits)}; use an id")
        raise Refusal(f"no such id {ident!r} (ids look like f02, a05, s03; use look or find)")

    def _mark_seen(self, nid):
        if nid in self.world.nodes:
            self.seen[nid] = self.world.nodes[nid]["rev"]
        elif nid in self.world.subjects:
            self.seen[nid] = self.world.subjects[nid]["rev"]

    def _place_words(self, nid):
        x, y, w, h = self.world.abs_rect(nid)
        cx, cy = x + w / 2, y + h / 2
        col = "left" if cx < SCREEN[0] / 3 else "right" if cx > 2 * SCREEN[0] / 3 else "mid"
        row = "top" if cy < SCREEN[1] / 3 else "bottom" if cy > 2 * SCREEN[1] / 3 else "mid"
        if col == "mid" and row == "mid":
            return "center"
        return f"{row}-{col}" if row != "mid" else col if col != "mid" else row

    def _geom(self, nid):
        n = self.world.nodes[nid]
        if self.hide_coords:
            if n["parent"] and self.world.nodes[n["parent"]]["layout"] != "free":
                return ""
            return self._place_words(nid)
        if n["parent"] and self.world.nodes[n["parent"]]["layout"] != "free":
            return f"{n['w']}x{n['h']}"
        return f"{n['w']}x{n['h']} at {n['x']},{n['y']}"

    def verb_hints(self, nid):
        """Verbs worth showing on this line right now. Plain desks show none; the acme desk overrides."""
        return None

    def line(self, nid, level=1):
        w = self.world
        n = w.nodes[nid]
        self._mark_seen(nid)
        bits = []
        if n["type"] == "surface":
            kids = w.children(nid)
            head = f"{nid} surface \"{n['title']}\" {n['layout']}"
            geo = self._geom(nid) if n["parent"] else f"{n['w']}x{n['h']}"
            bits.append(geo)
            bits.append(f"{len(kids)} inside" if kids else "empty")
        else:
            s = w.subjects[n["subject"]]
            self._mark_seen(s["id"])
            head = f"{nid} {s['kind']} \"{s['title']}\""
            geo = self._geom(nid)
            if geo:
                bits.append(geo)
            if s.get("due"):
                bits.append(f"due {s['due']}")
            if s["kind"] in ("note", "task", "chat", "doc"):
                bits.append(f"{len(s['text'].split())}w")
            if n["folded"]:
                bits.append("folded")
            others = len(w.appearances_of(s["id"])) - 1
            if others:
                bits.append(f"also x{others}")
        hid = w.hidden_fraction(nid)
        if hid > 0.05:
            by = [r.split()[1] for r in w.relations(nid) if r.startswith("under")]
            bits.append(("hidden" if hid >= 0.95 else f"{int(hid * 100)}% hidden") + (" by " + ",".join(by) if by else ""))
        for r in w.relations(nid):
            if r.startswith(("offscreen", "spills")):
                bits.append(r)
        hints = self.verb_hints(nid)
        if hints:
            bits.append("try: " + " ".join(hints))
        out = head + (" · " + " · ".join(b for b in bits if b) if bits else "")
        if level >= 2 and n["type"] == "appearance":
            s = w.subjects[n["subject"]]
            first = s["text"].strip().splitlines()[0] if s["text"].strip() else ""
            if first:
                out += f'\n{"":4}> {first[:90]}'
        if level >= 3:
            out += "\n    verbs: " + " ".join(w.verbs_for(nid))
        return out

    def outline(self, root, level=2):
        lines = []

        def walk(nid, depth, force_open):
            n = self.world.nodes[nid]
            lvl = 2 if (depth == 0 and level >= 2) else 1
            lines.append(("  " * depth) + self.line(nid, lvl).replace("\n", "\n" + "  " * depth))
            if n["type"] == "surface":
                kids = self.world.children(nid)
                if kids and (force_open or nid in self.open):
                    for k in kids:
                        walk(k["id"], depth + 1, False)
                elif kids:
                    lines[-1] += f"  (open {nid} to see inside)"

        walk(root, 0, True)
        return "\n".join(lines)

    def delta_header(self):
        evs = [e for e in self.world.events[self.last_event_seen:] if e["by"] != "jeff"]
        self.last_event_seen = len(self.world.events)
        if not evs:
            return ""
        parts = [f"{e['id']} {e['verb']} {e['target']} by {e['by']}" for e in evs]
        return "!! since your last look: " + "; ".join(parts) + "\n"

    # ---- commands ---------------------------------------------------
    def cmd_look(self, target, level):
        nid = self._resolve(target or "desk")
        header = ""
        if nid in self.world.subjects:
            return header + self.cmd_pivot(nid)
        if level >= 3:
            return header + self.focus(nid)
        if level <= 1:
            return header + self.line(nid, 1)
        return header + self.outline(nid, 2)

    def focus(self, nid):
        w = self.world
        n = w.nodes[nid]
        out = [self.line(nid, 1)]
        if n["type"] == "appearance":
            s = w.subjects[n["subject"]]
            text = s["text"].strip()
            words = text.split()
            if len(words) > 250:
                text = " ".join(words[:250]) + " …(read {} for all)".format(nid)
            out.append("  subject " + s["id"] + (f" tags {','.join(s['tags'])}" if s["tags"] else ""))
            if text:
                out.append("  ---\n  " + text.replace("\n", "\n  ") + "\n  ---")
            out.append("  where: " + self._where_line(nid))
            out.append("  verbs: " + "  ".join(f"{v} {sig}".strip() for v, sig in w.verbs_for(nid).items()))
        else:
            for k in w.children(nid):
                out.append("  " + self.line(k["id"], 1))
            out.append("  verbs: " + " ".join(w.verbs_for(nid)) + f"   (verbs {nid} for argument forms)")
        return "\n".join(out)

    def cmd_fold(self, ident, opening):
        nid = self._resolve(ident, allow_subject=False)
        if self.world.nodes[nid]["type"] != "surface":
            raise Refusal(f"{nid} is not a surface; read {nid} for its content")
        if opening:
            self.open.add(nid)
        else:
            self.open.discard(nid)
        return self.outline(nid if opening else self.world.nodes[nid]["parent"] or nid, 2)

    def cmd_read(self, ident):
        nid = self._resolve(ident)
        w = self.world
        if nid in w.subjects:
            s = w.subjects[nid]
        elif w.nodes[nid]["type"] == "appearance":
            s = w.subjects[w.nodes[nid]["subject"]]
        else:
            raise Refusal(f"{nid} is a surface; look {nid} shows what is inside")
        self._mark_seen(nid)
        self._mark_seen(s["id"])
        apps = w.appearances_of(s["id"])
        head = f"{s['id']} {s['kind']} \"{s['title']}\" · appears at {', '.join(apps)}"
        if s["tags"]:
            head += f" · tags {','.join(s['tags'])}"
        if s.get("due"):
            head += f" · due {s['due']}"
        return f"{head}\n---\n{s['text']}\n---"

    def _where_line(self, nid):
        w = self.world
        n = w.nodes[nid]
        x, y, wd, h = w.abs_rect(nid)
        parent = n["parent"]
        pl = w.nodes[parent]["layout"] if parent else "-"
        rel = w.relations(nid)
        s = f"screen {x},{y} {wd}x{h} · in {parent or '-'} ({pl})"
        if parent:
            s += f" local {n['x']},{n['y']} z{n['z']}"
        if rel:
            s += " · " + ", ".join(rel)
        hid = w.hidden_fraction(nid)
        if hid:
            s += f" · {int(hid * 100)}% hidden"
        if not rel and not hid:
            s += " · clear"
        return s

    def cmd_where(self, ident):
        nid = self._resolve(ident, allow_subject=False)
        self._mark_seen(nid)
        return f"{nid}: " + self._where_line(nid)

    def cmd_verbs(self, ident):
        nid = self._resolve(ident)
        self._mark_seen(nid)
        v = self.world.verbs_for(nid)
        return f"{nid} verbs:\n" + "\n".join(f"  {k} {sig}".rstrip() for k, sig in v.items())

    def cmd_pivot(self, ident):
        nid = self._resolve(ident)
        w = self.world
        if nid in w.subjects:
            sid = nid
        elif w.nodes[nid]["type"] == "appearance":
            sid = w.nodes[nid]["subject"]
        else:
            n = w.nodes[nid]
            return f"{nid} is a surface in {n['parent'] or '-'}; surfaces have no subject"
        s = w.subjects[sid]
        self._mark_seen(sid)
        out = [f"{sid} {s['kind']} \"{s['title']}\" · {len(s['text'].split())}w" + (f" · tags {','.join(s['tags'])}" if s["tags"] else "")]
        for a in w.appearances_of(sid):
            n = w.nodes[a]
            out.append(f"  {self.line(a, 1)}  in {n['parent']} \"{w.title(w.nodes[n['parent']])}\"")
        out.append("  verbs: " + "  ".join(f"{v} {sig}".strip() for v, sig in w.verbs_for(sid).items()))
        return "\n".join(out)

    def cmd_find(self, words):
        q = words.lower().strip()
        if not q:
            raise Refusal("find needs words")
        w = self.world
        hits = []
        for s in w.subjects.values():
            hay = (s["title"] + " " + s["text"] + " " + " ".join(s["tags"])).lower()
            if all(t in hay for t in q.split()):
                apps = w.appearances_of(s["id"])
                for a in apps:
                    hits.append(f"  {self.line(a, 1)}  in {w.nodes[a]['parent']}")
                if not apps:
                    hits.append(f"  {s['id']} {s['kind']} \"{s['title']}\" (not on the desk)")
        for n in w.nodes.values():
            if n["type"] == "surface" and q in n["title"].lower():
                hits.append(f"  {self.line(n['id'], 1)}")
        return f"find {words!r}: {len(hits)} hit(s)\n" + "\n".join(hits) if hits else f"find {words!r}: nothing"

    def cmd_history(self, ident):
        evs = self.world.events
        if ident:
            nid = self._resolve(ident)
            evs = [e for e in evs if e["target"] == nid or nid in (e.get("args") or {}).values()]
        evs = evs[-12:]
        if not evs:
            return "no events yet"
        return "\n".join(
            f"{e['id']} {e['verb']} {e['target']} {self._fmt_args(e['args'])} by {e['by']}"
            + (f" via {e['via']}" if e.get("via") and e["via"] != e["verb"] else "") + (" (undone)" if e.get("undone") else "")
            for e in evs)

    def _fmt_args(self, args):
        return " ".join(f"{k}={v!r}" if " " in str(v) else f"{k}={v}" for k, v in (args or {}).items())

    def cmd_undo(self, eid):
        if not eid:
            raise Refusal("undo needs an event id like e3")
        r = self.world.undo(eid)
        self._after_mutation()
        return f"ok {r['event']}: reverted {eid}"

    def cmd_do(self, verb, target, kv):
        if not verb or not target:
            raise Refusal("do needs a verb and an id")
        verb = verb.lower()
        w = self.world
        if verb not in self._verb_names():
            try:
                hint = self._resolve(target)
                raise Refusal(f"{verb} is not a verb; {hint} has: " + "  ".join(
                    f"{v} {sig}".strip() for v, sig in w.verbs_for(hint).items()))
            except Refusal as r:
                if "is not a verb" in str(r):
                    raise
                raise Refusal(f"{verb} is not a verb (form: do <verb> <id> key=value); try verbs <id>")
        nid = self._resolve(target)
        kv = {k: v.replace("\\n", "\n") for k, v in kv.items()}
        cur = w.nodes[nid]["rev"] if nid in w.nodes else w.subjects[nid]["rev"]
        seen = self.seen.get(nid)
        if seen is None:
            raise Refusal(f"you have not looked at {nid} yet; look, read or where it first")
        if seen != cur:
            recent = [e for e in w.events if e["target"] == nid or nid in (e.get("changed") or [])]
            why = f"; last change {recent[-1]['id']} {recent[-1]['verb']} by {recent[-1]['by']}" if recent else ""
            raise Refusal(f"stale: {nid} changed since you last saw it{why}; look at it again before acting")
        kv = {k: self._resolve(v, allow_subject=False) if k in ("into", "before", "after") else v for k, v in kv.items()}
        r = w.apply(verb, nid, None, kv)
        for c in r.get("changed", []):
            if c in w.events[-1].setdefault("changed", []):
                pass
            w.events[-1].setdefault("changed", []).append(c)
        self._after_mutation()
        out = f"ok {r['event']}: {verb} {nid} {self._fmt_args(kv)}".rstrip()
        if r.get("created"):
            out += f" → created {r['created']}"
        if r.get("note"):
            out += f"\n  {r['note']}"
        for c in r.get("changed", []):
            if c in w.nodes and c != nid:
                self._mark_seen(c)   # your own change; the receipt is the look
        if nid in w.nodes:
            self._mark_seen(nid)
            out += "\n  now: " + self.line(nid, 1) + self.position_note(nid)
        return out

    def position_note(self, nid):
        n = self.world.nodes.get(nid)
        if not n or not n["parent"] or self.world.nodes[n["parent"]]["layout"] == "free":
            return ""
        kids = [k["id"] for k in self.world.children(n["parent"])]
        i = kids.index(nid) + 1
        suffix = 'th' if 10 <= i % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(i % 10, 'th')
        return f"  ({i}{suffix} of {len(kids)} in {n['parent']})"

    def _after_mutation(self):
        for h in list(self.hooks):
            h(self)

    # ---- apply variant: edit the outline ----------------------------
    LINE = re.compile(r"^(\s*)([fa]\d\d)\b(?:\s+\w+)?(?:\s+\"([^\"]*)\")?")

    def cmd_apply(self, body, dry):
        w = self.world
        body = body.strip("\n")
        if not body:
            raise Refusal("apply needs the edited outline on the following lines (first line must be a surface)")
        rows = []
        for raw in body.splitlines():
            if not raw.strip() or raw.strip().startswith(">") or raw.strip().startswith("verbs"):
                continue
            m = self.LINE.match(raw.replace("├", " ").replace("└", " ").replace("│", " "))
            if not m:
                raise Refusal(f"could not read line: {raw!r} (each line must start with an id)")
            rows.append((len(m.group(1)), m.group(2), m.group(3)))
        if not rows:
            raise Refusal("nothing to apply")
        root = rows[0][1]
        if root not in w.nodes or w.nodes[root]["type"] != "surface":
            raise Refusal("first line must be the surface you are editing")
        # infer parent by indentation
        stack = [(rows[0][0], root)]
        parent_of, order_in, titles = {}, {}, {}
        for ind, nid, title in rows[1:]:
            while stack and ind <= stack[-1][0]:
                stack.pop()
            if not stack:
                raise Refusal(f"{nid} is indented less than the root")
            p = stack[-1][1]
            parent_of[nid] = p
            order_in.setdefault(p, []).append(nid)
            if title is not None:
                titles[nid] = title
            if nid in w.nodes and w.nodes[nid]["type"] == "surface":
                stack.append((ind, nid))
        # which nodes are in scope: everything under root that the caller has seen
        def subtree(nid):
            out = [nid]
            if w.nodes[nid]["type"] == "surface":
                for k in w.children(nid):
                    out += subtree(k["id"])
            return out
        scope = set(subtree(root)) - {root}
        listed = set(parent_of)
        ops = []
        for nid in listed:
            if nid not in w.nodes:
                raise Refusal(f"{nid} does not exist")
            if nid not in scope and self.seen.get(nid) is None:
                raise Refusal(f"{nid} is outside {root} and you have not looked at it")
        for nid in sorted(scope - listed):
            if self.seen.get(nid) is None:
                raise Refusal(f"{nid} is inside {root} but not in your outline; you have not seen it (open its surface first)")
            ops.append(("remove", nid, {}))
        for nid, p in parent_of.items():
            if w.nodes[nid]["parent"] != p:
                ops.append(("move", nid, {"into": p}))
        for p, ids in order_in.items():
            if w.nodes[p]["layout"] != "free":
                current = [k["id"] for k in w.children(p) if k["id"] in ids]
                if [i for i in ids if i in w.nodes] != current:
                    for i, nid in enumerate(ids):
                        ops.append(("move", nid, {"into": p, "at": i}))
        for nid, t in titles.items():
            if w.title(w.nodes[nid]) != t:
                ops.append(("rename" if w.nodes[nid]["type"] == "surface" else "edit", nid, {"title": t}))
        for _, nid, _ in ops:
            if nid in w.nodes and self.seen.get(nid) not in (None, w.nodes[nid]["rev"]):
                raise Refusal(f"stale: {nid} changed since you last saw it; look again")
        if not ops:
            return "nothing to change: the outline already matches the desk"
        desc = "\n".join(f"  {v} {nid} {self._fmt_args(a)}".rstrip() for v, nid, a in ops)
        if dry:
            return f"plan ({len(ops)} op(s)):\n{desc}\nsend the same outline with apply to do it"
        snap = deepcopy((w.nodes, w.subjects, w.events))
        done = []
        try:
            for v, nid, a in ops:
                r = w.apply(v, nid, None, a)
                done.append(r["event"])
        except Refusal as e:
            w.nodes, w.subjects, w.events = snap
            raise Refusal(f"apply aborted, nothing changed: {e}")
        self._after_mutation()
        for nid in listed:
            self.seen.pop(nid, None)
        return f"applied {len(ops)} op(s) (events {done[0]}..{done[-1]}):\n{desc}\n" + self.outline(root, 2)
