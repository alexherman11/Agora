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
  look [id] [:1|:2|:3|:4] outline from id (default desk). :1 the line, :2 its children (default), :3 everything under it with first lines, :4 with full text
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


def unescape_value(v):
    """A k=v value after shlex: an unescaped \\n is a newline; \\\\ is one literal backslash (so \\\\n stays literal)."""
    return re.sub(r"(?<!\\)\\n", "\n", v).replace("\\\\", "\\").replace("\\$", "$")


def split_batch(line):
    """Split on ; or newlines outside quotes."""
    out, cur, q, esc = [], "", None, False
    for ch in line or "":
        if q:
            cur += ch
            if esc:
                esc = False
            elif ch == "\\":
                esc = True   # an escaped quote inside a value does not close it (export writes \" inside text=)
            elif ch == q:
                q = None
        elif ch in "\"'":
            q = ch
            cur += ch
        elif ch in ";\n":
            if cur.strip():
                out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out or [""]


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

    batch = False   # round 9: several commands per call, ; or newline separated; $new = last created surface
    read_cap = None # round 11 (lean): at most this many read/examine commands per call; the rest are folded, visibly

    def dispatch(self, name, args):
        if self.batch and name == "desk":
            parts = split_batch(args.get("line", ""))
            if parts and parts[0].lower().startswith("script "):
                parts = [args.get("line", "").strip()]   # a script definition keeps its ; for later
            if len(parts) > 1:
                outs, error = [], False
                reads = 0
                for i, part in enumerate(parts):
                    if self.read_cap and part.split()[0].lower() in ("read", "examine"):
                        reads += 1
                        if reads > self.read_cap:
                            rest = parts[i:]
                            outs.append(f"({len(rest)} later command(s) not run: at most {self.read_cap} reads per call. "
                                        f"Not run: {'; '.join(rest)}. Ask for them in another call, or narrow with find)")
                            break
                    r = self._one({"line": part})
                    body = r["text"] if "text" in r else "ERR " + r["error"]
                    outs.append(f"[{i + 1}] {part}\n{body}")
                    if "error" in r:
                        error = True
                        if i < len(parts) - 1:
                            rest = parts[i + 1:]
                            outs.append(f"(stopped; {len(rest)} later command(s) not run. Not run: {'; '.join(rest)}. "
                                        f"Fix [{i + 1}] and resubmit them in one call)")
                        break
                return {"text": "\n\n".join(outs), "batch": len(parts), "batch_error": error}
        return self._one(args, name)

    _cmd_no = 0

    def _one(self, args, name="desk"):
        header = self.delta_header()
        self._cmd_no += 1
        n0 = len(self.world.events)
        r = self._dispatch(name, args)
        for e in self.world.events[n0:]:
            e.setdefault("cmd", self._cmd_no)   # which command produced it: undo groups steps by this, not by verb
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
            if len(argv) > 1:
                raise Refusal(f"{cmd} takes only an id; examine {argv[0]} shows what is inside")
            return self.cmd_fold(argv[0], cmd == "open")
        if cmd == "read":
            section, full, tail = None, False, None
            for a in argv[1:]:
                if a.startswith("#"):
                    section = a[1:]
                elif a in (":3", ":full"):
                    full = True
                elif a.startswith("tail="):
                    if not (a[5:].isdigit() and int(a[5:]) > 0):
                        raise Refusal("tail=<n> wants a positive number of lines")
                    tail = int(a[5:])
                elif section is not None and "=" not in a and not a.startswith(":"):
                    section += " " + a    # read a07 #Session 2: a section name may have spaces
            return self.cmd_read(argv[0] if argv else None, section, full, tail)
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
                kv[k] = unescape_value(v)
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
        ident = ident.lstrip("@").strip().strip('"\'')   # any command may name a thing by its quoted title
        if ident.startswith("$") and ident[1:] in (getattr(self, "vars", None) or {}):
            ident = self.vars[ident[1:]]   # a handle you named: create ... as=draft, or set draft = a98
        if ident in ("$new", "$item"):
            want = (self.world.last_surface or self.world.last_created) if ident == "$new" else self.world.last_created
            if not want:
                raise Refusal(f"{ident}: nothing has been created yet in this session")
            ident = want
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

    def view_matches(self, nid):
        """Ids a view currently shows. Plain desks have no selections, so no views."""
        return None

    def view_lines(self, nid, depth):
        return []

    def child_extra(self, nid, depth):
        """Extra lines printed under an appearance in an outline. Plain desks print none; the bullets desk overrides."""
        return None

    def line(self, nid, level=1):
        w = self.world
        n = w.nodes[nid]
        self._mark_seen(nid)
        bits = []
        if n["type"] == "surface" and n["layout"] == "view":
            head = f"{nid} view \"{n['title']}\" of {n.get('query')}" + (f" as table {n['cols']}" if n.get("cols") else "")
            kids = []
            m = self.view_matches(nid)
            bits.append("query not evaluable" if m is None else f"{len(m)} match" + ("es" if len(m) != 1 else ""))
        elif n["type"] == "surface":
            kids = w.children(nid)
            head = f"{nid} surface \"{n['title']}\" {n['layout']}"
            geo = self._geom(nid) if n["parent"] else f"{n['w']}x{n['h']}"
            bits.append(geo)
            bits.append(f"{len(kids)} inside" if kids else "empty")
            if kids and n["layout"] != "free":
                axis = "h" if n["layout"] == "column" else "w"
                share = min(k[axis] for k in kids)
                if share < 80:
                    bits.append(f"cramped, {share}px each")   # fuller than it is tall: the fold that a screen would show
                lim = n["h"] if axis == "h" else n["w"]
                pos = "y" if axis == "h" else "x"
                spilled = sum(1 for k in kids if k[pos] + k[axis] > lim + 1)
                if spilled:
                    bits.append(f"{spilled} past the {'bottom' if axis == 'h' else 'right edge'} (offscreen)")
        else:
            s = w.subjects[n["subject"]]
            self._mark_seen(s["id"])
            head = f"{nid} {s['kind']} \"{s['title']}\""
            geo = self._geom(nid)
            if geo:
                bits.append(geo)
            if s.get("due"):
                bits.append(f"due {s['due']}")
            if s.get("props") and s["kind"] == "trial":
                p = s["props"]   # a trial's line reads as a result, not as a property dump
                bits.append(" ".join(x for x in [p.get("task", ""), str(p.get("model", "")).replace("gpt-5.6-", ""),
                                                 p.get("status", ""), p.get("score", ""),
                                                 f"{p['calls']} calls" if p.get("calls") else "",
                                                 f"{p['seconds']}s" if p.get("seconds") else ""] if x))
            elif s.get("props"):
                bits.append(" ".join(f"{k}={v}" for k, v in s["props"].items() if k not in ("label", "started")))
            if s["kind"] in ("note", "task", "chat", "doc", "trial"):
                bits.append(f"{len(s['text'].split())}w")
            if n["folded"]:
                bits.append("folded")
            others = len(w.appearances_of(s["id"])) - 1
            if others:
                bits.append(f"also x{others}")
            if s.get("comments"):
                open_ = sum(1 for c in s["comments"] if not c["resolved"])
                bits.append(f"{len(s['comments'])} comment" + ("s" if len(s["comments"]) != 1 else "") + (f", {open_} open" if open_ else ""))
            nl = len(w.links_of(s["id"]))
            if nl:
                bits.append(f"{nl} link" + ("s" if nl != 1 else ""))
            if s["kind"] == "doc":
                secs = [h for h, _ in w.sections(s["text"]) if h]
                if secs:
                    bits.append(f"{len(secs)} sections")
        hid = w.hidden_fraction(nid)
        if hid > 0.05:
            by = [r.split()[1] for r in w.relations(nid) if r.startswith("under")]
            bits.append(("hidden" if hid >= 0.95 else f"{int(hid * 100)}% hidden") + (" by " + ",".join(by) if by else ""))
        for r in w.relations(nid):
            if r.startswith(("offscreen", "spills")):
                bits.append(r)
        if n["type"] == "surface":
            covered = [r.split()[1] for r in w.relations(nid) if r.startswith("covers") and w.nodes[r.split()[1]]["type"] == "surface"]
            if covered:
                bits.append("covers " + ",".join(covered))
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

    def outline(self, root, level=2, deep=False, full=False):
        lines = []
        self._full = full   # :4 shows each thing's text, not only its first line

        def walk(nid, depth, force_open):
            n = self.world.nodes[nid]
            lvl = 2 if (depth == 0 and level >= 2) else 1
            lines.append(("  " * depth) + self.line(nid, lvl).replace("\n", "\n" + "  " * depth))
            if n["type"] == "surface" and n["layout"] == "view":
                if depth == 0 or force_open or deep or nid in self.open:
                    lines.extend(self.view_lines(nid, depth))
                elif self.view_matches(nid):
                    lines[-1] += f"  (open {nid} to see them)"
                return
            if n["type"] == "appearance":
                extra = self.child_extra(nid, depth)
                if extra:
                    lines.append(extra)
            if n["type"] == "surface":
                kids = self.world.children(nid)
                if kids and (force_open or deep or nid in self.open):
                    cap = 16 if deep else None   # a deep look folds a long panel; the fold says how to see the rest
                    for k in kids[:cap]:
                        walk(k["id"], depth + 1, False)
                    if cap and len(kids) > cap:
                        lines.append(("  " * (depth + 1)) + f"(… {len(kids) - cap} more in {nid}; look {nid} :2 lists one line each)")
                elif kids:
                    lines[-1] += f"  (open {nid} to see inside)"

        self._deep = deep   # :3 also shows each thing's first line (child_extra reads this)
        try:
            walk(root, 0, True)
        finally:
            self._deep = False
            self._full = False
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
            # look's suffix is containment depth: :3 on a surface walks everything under it, open or not.
            # An appearance has nothing under it, so :3 there is examine (the plain desk keeps its focus form).
            if self.world.nodes[nid]["type"] == "surface":
                return header + self.outline(nid, 2, deep=True, full=level >= 4)
            return header + (self.cmd_examine(nid) if hasattr(self, "cmd_examine") else self.focus(nid))
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
            # :3 on a surface: everything under it, whether or not it is open, then its verbs
            out = [self.outline(nid, 2, deep=True)]
            out.append("  verbs: " + " ".join(w.verbs_for(nid)) + f"   (verbs {nid} for argument forms)")
        return "\n".join(out)

    def cmd_fold(self, ident, opening):
        nid = self._resolve(ident, allow_subject=False)
        if self.world.nodes[nid]["type"] != "surface":
            raise Refusal(f"{nid} is not a surface; read {nid} for its content")
        if opening:
            self.open.add(nid)
            # a look walks from the root and only descends into open surfaces, so an open
            # surface inside a closed one would never be reached: open the ancestors too, and say so
            also = []
            p = self.world.nodes[nid]["parent"]
            while p and p != self.world.root:
                if p not in self.open:
                    self.open.add(p)
                    also.append(p)
                p = self.world.nodes[p]["parent"]
            note = ("\n(also opened " + ", ".join(also) + f" so that look reaches {nid})") if also else ""
            return self.outline(nid, 2) + note
        self.open.discard(nid)
        return self.outline(self.world.nodes[nid]["parent"] or nid, 2)

    def cmd_read(self, ident, section=None, full=False, tail=None):
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
        secs = w.sections(s["text"])
        named = [(h, b) for h, b in secs if h]
        body = s["text"]
        if named and section is None and not full and not tail:   # tail= wants the end of the text, not its outline
            # fold-as-budget for text: the outline of sections, each with its word count
            pre = next((b for h, b in secs if h is None), "")
            lines = ([pre] if pre else []) + [f"## {h}  ({len(b.split())}w)" for h, b in named]
            body = "\n".join(lines) + f"\n(read {nid} #<n> or #<name> for one section, read {nid} :3 for all)"
        elif named and section is not None:
            pick = None
            if section.isdigit() and 1 <= int(section) <= len(named):
                pick = named[int(section) - 1]
            else:
                pick = next(((h, b) for h, b in named if h.lower() == section.lower()), None)
            if not pick:
                raise Refusal(f"no section {section!r}; sections: " + ", ".join(f"#{i + 1} {h}" for i, (h, _) in enumerate(named)))
            body = f"## {pick[0]}\n{pick[1]}"
        if tail:
            bl = body.splitlines()
            if len(bl) > tail:
                cut = bl[:-tail]
                heading = next((l for l in reversed(cut) if l.startswith("## ")), None)   # the section the tail lines belong to
                keep = [heading] if heading else []
                body = "\n".join(keep + [f"(… {len(cut) - len(keep)} earlier line(s) folded; without tail= for all)"] + bl[-tail:])
        out = f"{head}\n---\n{body}\n---"
        if s.get("comments"):
            out += "\ncomments:"
            for c in s["comments"]:
                out += f"\n  {c['id']} {c['by']}: {c['text']}" + (" (resolved)" if c["resolved"] else " (open)")
                for r in c["replies"]:
                    out += f"\n      {r['by']}: {r['text']}"
        links = w.links_of(s["id"])
        if links:
            out += "\nlinks:"
            for l in links:
                other = l["to"] if l["from"] == s["id"] else l["from"]
                ot = w.subjects[other]["title"] if other in w.subjects else other
                arrow = f"{l['kind']} →" if l["from"] == s["id"] else f"← {l['kind']} from"
                out += f"\n  {l['id']} {arrow} {other} \"{ot}\""
        return out

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
        out.append(self.subject_verbs_line(sid))
        return "\n".join(out)

    def subject_verbs_line(self, sid):
        """The verbs a subject answers to. The plain desk uses the world's table; verb-registry desks override."""
        return "  verbs: " + "  ".join(f"{v} {sig}".strip() for v, sig in self.world.verbs_for(sid).items())

    def cmd_find(self, words):
        q = words.lower().strip()
        if not q:
            raise Refusal("find needs words")
        w = self.world
        hits = []
        scored = []
        for s in w.subjects.values():
            hay = (s["title"] + " " + s["text"] + " " + " ".join(s["tags"])).lower()
            if all(t in hay for t in q.split()):
                # things named by the words come before things that merely mention them (Terra's friction note)
                rank = 0 if all(t in s["title"].lower() for t in q.split()) else 1 if all(t in " ".join(s["tags"]).lower() for t in q.split()) else 2
                scored.append((rank, s))
        for _, s in sorted(scored, key=lambda x: x[0]):
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
            mine = [e for e in self.world.events if e["by"] == "jeff" and e["verb"] != "undo" and not e.get("undone")]
            if not mine:
                raise Refusal("nothing of yours to undo")
            eid = mine[-1]["id"]   # bare undo: your latest change
        ev = next((e for e in self.world.events if e["id"] == eid), None)
        if ev is None:
            raise Refusal(f"no event {eid}")
        if ev.get("cause"):
            # a rule's consequence: undo the command that caused it, and everything it caused
            eid = ev["cause"]
            ev = next(e for e in self.world.events if e["id"] == eid)
        group = [ev]
        if ev.get("via"):
            # a composed verb (sort, move <selection>, group ...) is undone as a whole: its contiguous steps,
            # on both sides of the named one
            evs = self.world.events
            at = evs.index(ev)
            same = lambda e: (e.get("via") == ev["via"] and e.get("cmd") == ev.get("cmd") and not e.get("undone")
                              and e["by"] == ev["by"] and not e.get("cause"))
            j = at - 1
            while j >= 0 and same(evs[j]):
                group.insert(0, evs[j])
                j -= 1
            j = at + 1
            while j < len(evs) and same(evs[j]):
                group.append(evs[j])
                j += 1
        caused = [e for e in self.world.events if e.get("cause") in {g["id"] for g in group} and not e.get("undone")]
        group = sorted(group + caused, key=lambda e: int(e["id"][1:]))
        done = []
        revs0 = {k: v["rev"] for k, v in list(self.world.nodes.items()) + list(self.world.subjects.items())}
        for e in reversed(group):
            r = self.world.undo(e["id"])
            done.append(e["id"])
        for k, v in list(self.world.nodes.items()) + list(self.world.subjects.items()):
            if revs0.get(k) != v["rev"]:
                self._mark_seen(k)   # an undo is your own change; what it touched stays seen
        self._after_mutation()
        if len(done) > 1:
            what = f"{len(done)} steps of {ev['via']}" if ev.get("via") else f"{eid} and {len(caused)} rule consequence(s)"
            return f"ok {r['event']}: reverted {done[-1]}..{done[0]} ({what})"
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
        kv = dict(kv)   # values were unescaped where they were parsed
        cur = w.nodes[nid]["rev"] if nid in w.nodes else w.subjects[nid]["rev"]
        seen = cur if getattr(self, "_in_rules", False) else self.seen.get(nid)   # a rule is the desk's own hands: no fence
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
        if r.get("created") in w.nodes:
            self._mark_seen(r["created"])
            out += "\n  now: " + self.line(r["created"], 1) + self.position_note(r["created"])
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
