"""The staged lens compiler, stages 4 and 5: lower to the six kinds, evaluate through the read accessor.

    parse (scene.parse) -> resolve (scene.resolve) -> lower -> evaluate(IR, accessor, host) -> scene -> print / emit

Built to Sable's statement (sable-8): evaluation is a function of the IR, the accessor's answers and the host facts,
and nothing else; the accessor is the only door to the world and records every read in R; within one part the order
is bind, lets, guard, emit, acts, instances, placed lens, fixed kids; ABSENT is a value; count is the true size.
The scene it produces has the same shape as scene.build's, so scene.to_text and scene.emit print and paint it, and
Juniper's golden prints judge the switch. Jeff owns this file (desk-shell/OWNERS.md)."""
import re

import moo
import scene as S
import expr as X
from desk import aspects_of, aspects_meet, event_aspects
from world import Refusal

ABSENT = None          # printed (no x); a third value, distinct from "" and from false


import weakref as _weakref
_TOUCH = _weakref.WeakKeyDictionary()


def _touch_index(w):
    """name -> the indices of the events whose target or `changed` names it (a6010: a board of 60 cards asked
    `$changed.commission` of each, and each ask walked back through all ~11k events, ~2 ms each). Events are only
    appended (an undo is an event of its own and marks the one it undoes, which the reader still checks), so the
    index is extended with the new ones; it is made again if the list was replaced or shrank."""
    ev = w.events
    hit = _TOUCH.get(w)
    if hit is None or hit[0] is not ev or hit[1] > len(ev) or (hit[1] and ev[hit[1] - 1] is not hit[2]):
        hit = [ev, 0, None, {}]
        _TOUCH[w] = hit
    idx = hit[3]
    for i in range(hit[1], len(ev)):
        e = ev[i]
        for nm in {e["target"], *(e.get("changed") or [])}:
            idx.setdefault(nm, []).append(i)
    if len(ev) != hit[1]:
        hit[1], hit[2] = len(ev), ev[-1]
    return idx


class Accessor:
    """The seam: six questions, each recorded in R (sable-8 section 1)."""

    def __init__(self, desk):
        self.desk, self.w, self.R = desk, desk.world, []
        # Snappy Desk stage 2 (14 Oct): while a repeat's instance is built, every question asked here is kept with its
        # answer (one list per instance being built, outer ones too), so the next build can ask them again and keep
        # the instance when every answer is the same. `nodes` keeps the parts whose fence must be read again then.
        self.rec, self.nodes, self.entries = [], [], []
        self._sel = {}

    def _said(self, name, args, ans):
        for r in self.rec:
            r.append((name, args, ans))

    def value(self, r, a):
        c = S._ctx_for(self.w, r)
        v = c.get(a) if (a in c and not a.startswith("_")) else (c.get("_props") or {}).get(a)
        self.R.append(("value", r, a, S._rev_of(self.w, r)))
        if self.rec:
            self._said("value", (r, a), v)
        return v

    def thing(self, r, state=None):
        """Every printable value of one thing, as one read of the thing (the printer says which fields were used)."""
        self.R.append(("thing", r, S._rev_of(self.w, r)))
        c = S._ctx_for(self.w, r, state)
        if self.rec:
            self._said("thing", (r, state), dict(c))
        return c

    def select(self, q):
        """Referents matching a selection, in the desk's order, as a membership read. Answered once per build: the
        world holds still while a lens is built."""
        hit = self._sel.get(q)
        if hit is None:
            named = S._named(self.w, q)
            if named is not None:
                hit = (tuple(named), None)
            else:
                try:
                    sel = self.desk._parse_selection(q)
                except Refusal as exc:
                    # 15 Oct (a5398), as rows above: `count(kind:task,in:$item)` on a note asks in: of a note, and the
                    # native refusal escaped the compiler, so the write that triggered the lens check crashed.
                    raise S.LensRefusal(f"selection {q!r}: {exc}") from exc
                hit = (None, tuple(sel[0]) if sel else ())
            self._sel[q] = hit
        named, ids = hit
        self.R.append(("select", q, [i for i, _ in named] if named is not None else list(ids)))
        if self.rec:
            self._said("select", (q,), hit)
        return (list(named), None) if named is not None else (None, list(ids))

    def rows(self, src):
        # a6010: answered once per build, as select is (the world holds still while a lens is built): the home base asked
        # one chat's lines four times, ~70 ms each. Each asker gets its own copies of the rows
        if ("rows", src) not in self._sel:
            try:
                self._sel[("rows", src)] = S.rows(self.desk, src, memo=self._sel)
            except Refusal as exc:
                # Authored row queries use the native selector's refusal type. At the
                # compiler boundary they belong to lens diagnostics and fallback,
                # including checks run after an otherwise successful native write.
                raise S.LensRefusal(f"row source {src!r}: {exc}") from exc
        rs = self._sel[("rows", src)]
        rs = None if rs is None else [dict(r) for r in rs]
        self.R.append(("rows", src, len(rs) if rs is not None else None))
        if self.rec:
            self._said("rows", (src,), None if rs is None else [dict(r) for r in rs])
        return rs

    def define(self, name):
        s = S.find_lens(self.desk, name, getattr(self, "home", None))     # 9 Oct: nearest to the placing lens's room
        self.R.append(("define", name, s["id"], s["rev"]))
        if self.rec:
            self._said("define", (name,), (s["id"], s["rev"]))
        return s

    def touched(self, r, aspect=None):
        """The last event on thing `r` (its appearance or subject), or the last one that changed `aspect`; undone events
        and undos are skipped (an undo is not a touch, as `age<` already says). -> {id, at, by} or None."""
        w = self.w
        n = w.nodes.get(r)
        names = {r} | ({n["subject"]} if n and n.get("subject") else set()) | set(w.appearances_of(r) if r in w.subjects else [])
        hit = None
        idx = _touch_index(w)        # a6010: the events on these names only, not every event of the world each time
        for i in sorted({i for nm in names for i in idx.get(nm, ())}, reverse=True):
            e = w.events[i]
            if e.get("undone") or e["verb"] == "undo":
                continue
            if aspect and not aspects_meet({aspect}, event_aspects(e)):
                continue
            hit = e
            break
        self.R.append(("touched", r, aspect, hit["id"] if hit else None))
        if self.rec:
            self._said("touched", (r, aspect), hit["id"] if hit else None)
        if not hit:
            return None
        wall = (hit.get("at") or "")[:16].replace("T", " ")
        # Juniper: the date is the event's desk-clock day, as `today` and `due` are; the time is the wall clock's
        at = (f"{hit['day']} {wall[11:]}".strip() if hit.get("day") else wall)
        return {"id": hit["id"], "verb": hit.get("via") or hit["verb"], "at": at, "by": hit["by"]}

    def host(self, f):
        v = {"me": self.w.me, "today": getattr(self.desk, "today", None) or getattr(self.w, "today", None),
             "session": getattr(self.desk, "_session", None)}.get(f)
        self.R.append(("host", f, v))
        if self.rec:
            self._said("host", (f,), v)
        return v

    def same(self, name, args, was):
        """Ask again what was asked when an instance was built: -> whether the answer is the one it was built from."""
        if name == "touched":
            self.touched(*args)
            return self.R[-1][3] == was
        now = getattr(self, name)(*args)
        if name == "thing":
            return dict(now) == was
        if name == "select":
            return self._sel[args[0]] == was
        if name == "rows":
            return (None if now is None else [dict(r) for r in now]) == was
        if name == "define":
            return (now["id"], now["rev"]) == was
        return now == was


# ---------------------------------------------------------------------------------------------------------------------
# Snappy Desk stage 2 (Alex approved the plan, 14 Oct): views by change. An Enter in one paragraph of a 70-paragraph
# design rebuilt all 70 (1367 parts, 6268 expressions, ~240 ms). Now each instance of a repeat is kept from the last
# build of the same lens for the same viewer, and used again when (1) the values it reads from the parts above it are
# the same (its fingerprint: every $name, $frame.field and bare name its parts mention, its frames, its thing), and (2)
# every question it asked the world, asked again, has the same answer (Accessor.same). What moves without changing what
# it shows is read again: each gesture's fence (its reads, with the revisions of now and the reads of the parts above
# it), its bind, and a repeat's event count. A part that places another lens, stands at its world position, or spreads
# is never kept, nor what holds one. LENS_REUSE=off turns it off; LENS_REUSE_VERIFY=1 builds every scene twice and says
# any difference (in house-state/lens-reuse.err); every 25th build is checked so anyway, and a difference is served as
# the whole build, with what was kept forgotten.
# ---------------------------------------------------------------------------------------------------------------------
import os
import time as _time

_REUSE = {}                 # (session, viewer, lens text, style, props) -> {instance key: entry}, the last build's
_IR = {}                    # (lens text, style, roles) -> (IR parts, root, what each part reads)
_OFF = [False]
_STATS = {"kept": 0, "made": 0, "builds": 0, "differed": 0}
VERIFY_EVERY = 25
_IDENT = re.compile(r"(?<![\w$.])([A-Za-z]\w*)")


def _fence_reads(w, fields0, ids0, cb):
    """A gesture's reads (its fence): the things it was built from, with their revisions now, and the selections on
    its chain. fields0: id -> aspects it showed; ids0: [(id, always)]; cb: the reads of the binds above it."""
    reads, fields = {}, {k: set(v) for k, v in fields0.items()}
    for i, always in ids0:
        r = S._rev_of(w, i)
        if always or r is not None:
            reads[i] = r
    selects = []
    for e in cb:
        if e[0] == "select":
            if e not in selects:
                selects.append(e)
        elif S._rev_of(w, e[0]) is not None:
            reads[e[0]] = S._rev_of(w, e[0])
            fields.setdefault(e[0], set()).update(e[2])
    return [[i, r, sorted(fields.get(i) or [])] for i, r in sorted(reads.items())] + selects


def _bind(w, out):
    if out.get("item") in w.nodes and out["acts"]:
        out["rev"] = w.nodes[out["item"]]["rev"]
        nd = w.nodes[out["item"]]
        sj2 = w.subjects.get(nd.get("subject") or "")
        out["bind"] = {"subject": nd.get("subject"), "subject_rev": sj2["rev"] if sj2 else None, "parent": nd["parent"],
                       "parent_rev": w.nodes[nd["parent"]]["rev"] if nd["parent"] in w.nodes else None, "units": "px in parent"}


def _static(node, irs, memo):
    """-> (names, frame fields, idents, keepable) of a part and everything inside it, read from its IR alone."""
    got = memo.get(id(node))
    if got is not None:
        return got
    em, b = node["emit"], node["bind"]
    words = [em.get("text"), em.get("light"), em.get("fold") if isinstance(em.get("fold"), str) else None, node["place"]]
    exprs = [c for _, c in em["role_when"]]
    if node["guard"]:
        exprs.append(node["guard"]["src"])
    for let in node["lets"]:
        exprs += [let["expr"], let["when"]]
    for a in node["acts"]:
        words.append(a.get("line"))
        exprs.append(a.get("when"))
    if b:
        words += [b.get("q"), b.get("of"), b.get("over")]
    words = [t for t in words if isinstance(t, str)]
    exprs = [t for t in exprs if isinstance(t, str)] + [t for t in words if "$(" in t]
    names, ffields, idents = set(), set(), set()
    for t in words + exprs:
        for a, f in S._VAR.findall(t):
            (ffields.add((a, f)) if f else names.add(a))
    for t in exprs:
        idents.update(_IDENT.findall(t))
    keep = not node["place"] and em.get("at") != "item" and not em.get("spread") and not (
        b and b["kind"] == "many" and (b.get("by") or b.get("run") or b.get("over")))
    inner = list(node["kids"]) + ([irs[b["each"]]] if b and b["kind"] == "many" and b.get("each") in irs else [])
    for k in inner:
        n2, f2, i2, k2 = _static(k, irs, memo)
        names |= n2
        ffields |= f2
        idents |= i2
        keep = keep and k2
    got = memo[id(node)] = (frozenset(names), frozenset(ffields), frozenset(idents), keep)
    return got


def _fingerprint(node, irs, memo, ctx, layout):
    """What an instance reads from the parts above it, as a value: kept instances are used again only when it is equal."""
    names, ffields, idents, _ = _static(node, irs, memo)
    props = ctx.get("_props") or {}
    frames = ctx.get("_frames") or {}
    vals = ctx.get("_values") or {}
    fp = [ctx.get("item"), ctx.get("id"), ctx.get("_state"), layout, repr(ctx.get("_captured")),
          tuple(sorted(frames)), tuple(sorted(ctx.get("_lets") or ()))]
    for n in sorted(names):
        fp.append((n, n in ctx, n in props, repr(ctx[n] if n in ctx else props.get(n)), (frames.get(n) or {}).get("id")))
    for a, f in sorted(ffields):
        fr = frames.get(a)
        if fr is None:
            fp.append((a, f, None))
            continue
        v = fr.get(f) if (f in fr and not f.startswith("_")) else (fr.get("_props") or {}).get(f)
        fp.append((a, f, fr.get("id"), repr(v), f in (fr.get("_captured_fields") or ())))
    for i in sorted(idents):
        v = vals.get(i)
        fp.append((i, repr(ctx.get(i)), (getattr(v, "kind", None), X.fmt(v)) if i in vals else None))
    return tuple(fp)


def _first_diff(a, b, path=""):
    """-> where two scenes first differ (their reads list R aside), or None."""
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k == "R" and not path:
                continue
            d = _first_diff(a.get(k), b.get(k), f"{path}.{k}" if k != "kids" else path)
            if d:
                return d
        return None
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return f"{path}: {len(a)} kept, {len(b)} made"
        for x, y in zip(a, b):
            d = _first_diff(x, y, f"{path}/{x.get('key') if isinstance(x, dict) else ''}")
            if d:
                return d
        return None
    return None if a == b else f"{path}: kept {str(a)[:120]!r}, made {str(b)[:120]!r}"


# ---------------------------------------------------------------------------------------------------------------------
# Stage 4, lower. A part becomes one IR node holding its operations in the fixed order, with dependency edges: the
# $names each operation uses (Sable: R_g is derived from these, not from what a tracker happened to see).
# ---------------------------------------------------------------------------------------------------------------------
def term_aspects(q):
    """The aspects of a member that selection `q`'s terms read (sable-8 amended R_g: a `bind many` instance is a member
    while these hold). -> (subject aspects, appearance aspects). 8 Oct: read from the term table (knife.aspects_of), so
    the fence and the reader cannot drift."""
    import knife
    return knife.aspects_of(q)


def _member_reads(w, i, q):
    """The [id, rev, aspects] entries that say `i` is a member of select(q)."""
    if S._named(w, q) is not None:
        # Naming an identity does not read its placement or its children. Its
        # live/unplaced/gone state is carried by the named selection instead.
        return []
    subj, app = term_aspects(q)
    n = w.nodes.get(i)
    sid = n.get("subject") if n else (i if i in w.subjects else None)
    out = []
    if subj and sid and sid in w.subjects:
        out.append([sid, w.subjects[sid]["rev"], sorted(subj)])
    if subj and not sid and n:
        out.append([i, n["rev"], sorted(subj)])
    if app and n:
        out.append([i, n["rev"], sorted(app)])
    return out


def _deps(*texts):
    out = set()
    for t in texts:
        for a, b in S._VAR.findall(t or ""):
            out.add(f"{a}.{b}" if b else a)
    return sorted(out)


def lower(root, parts):
    """-> IR root. Each IR node: part, line, src, bind, lets, guard, emit, acts, place, kids, carry, capture, deps."""
    def one(node):
        if node["the"]:
            bind = {"kind": "one", "q": node["the"], "as": node["as"], "capture": dict(node["capture"])}
        elif node["of"] or node["over"]:
            bind = {"kind": "many", "of": node["of"], "over": node["over"], "each": node["each"], "as": node["as"], "clamp": node["clamp"],
                    "last": bool(node.get("clamp_last")), "by": node.get("by"), "run": node.get("run")}
        else:
            bind = None
        guard = None
        if node["only"]:        # a selection, or an expression (expr.looks_like), told apart at evaluation, when the lets in scope are known
            guard = {"q": node["only"], "src": node["only"]}
        ir = {"part": node["name"], "line": node["line"], "src": node["src"], "ast": node,
              "bind": bind,
              "lets": [{"name": l, "expr": e, "when": c} for l, e, c in node.get("let", [])],
              "guard": guard,
              "emit": {"layout": node["layout"], "role": node["role"], "role_when": list(node["role_when"]), "text": node["text"], "clamp": node["clamp"],
                       "at": node["at"], "spread": node.get("spread"), "props": node["props"],
                       **{k: node[k] for k in S.PAINT_WORDS if node.get(k) not in (None, False)}},
              "acts": [dict(a) for a in node["on"]],
              "place": node["lens"], "carry": node["carry"],
              "kids": [one(k) for k in node["kids"]],
              "deps": {"emit": _deps(node["text"]), "guard": _deps(node["only"]), "role": _deps(*[c for _, c in node["role_when"]]),
                       "acts": [_deps(a["line"]) for a in node["on"]],
                       "lets": [_deps(e, c if c and c != "otherwise" else "") for _, e, c in node.get("let", [])]}}
        return ir
    return {name: one(node) for name, node in parts.items()}, root


# ---------------------------------------------------------------------------------------------------------------------
# Stage 5, evaluate. A transcription of scene.build's make(), with the world reached only through the accessor, the
# fixed order within a part, host facts in Gamma, count as the true size, and one rule for guards.
# ---------------------------------------------------------------------------------------------------------------------
def evaluate(desk, src, stack=(), count=None, props=None, closure=None, acc=None, cb=(), on=None, prefix=None):
    """prefix (a6010): a placed lens is built under its placer's key (`<part key>/lens:<name>`) from the start, so its
    parts have their final keys and what is kept of them can be used again at the next build."""
    props = props or {}
    acc = acc or Accessor(desk)
    # F7: the lens's own style; 9 Oct (step 7): found from the lens's own room (acc.home, set by compile_lens)
    roles = S.style_roles(desk, props.get("style"), getattr(acc, "home", None))
    ik = (src, props.get("style"), repr(roles))
    if ik in _IR:          # 14 Oct (stage 2): a lens is read once per text and style, not at every build
        irs, root, smemo = _IR[ik]
    else:
        root, parts = S.parse(src, roles=roles, style=props.get("style"))
        S.resolve(root, parts)
        irs, root = lower(root, parts)
        smemo = {}             # what each part reads (_static), worked out once per lens read
        _IR[ik] = (irs, root, smemo)
        while len(_IR) > 64:
            _IR.pop(next(iter(_IR)))
    w = desk.world
    count = count if count is not None else [0]
    host = {f: acc.host(f) for f in ("me", "today", "session")}
    # a6010: a placed lens was keyed again under its placer after it was built (S._rekey, in place), so nothing of it
    # could be kept, and the home base (every panel a placed lens) was built whole at every change, ~500 ms. Built
    # under its final keys now (prefix), it is kept as a root lens is, one store per place it stands (and thing it
    # stands on, a5949)
    off = _OFF[0] or os.environ.get("LENS_REUSE") == "off" or (len(stack) > 1 and prefix is None)
    ck = (getattr(desk, "_session", None), w.me, ik, repr(sorted(props.items(), key=str)), on, prefix)
    prev = {} if off else _REUSE.get(ck, {})
    nxt, used = {}, set()

    def instance(each, ictx, key, layout, chain, cb):
        """One instance of a repeat: the one kept from the last build when nothing it read has changed, else made."""
        if off or not _static(each, irs, smemo)[3] or key in used:
            if key in used:
                nxt.pop(key, None)        # two instances with one key: neither is kept (the second is renamed)
            used.add(key)
            return make(each, ictx, key, layout, chain, cb)
        used.add(key)
        fp = _fingerprint(each, irs, smemo, ictx, layout)
        old = prev.get(key)
        if old is not None and old["fp"] == fp:
            marks, mark = [len(r) for r in acc.rec], len(acc.R)
            if all(acc.same(*q) for q in old["asks"]):
                count[0] += old["count"]
                if count[0] > S.BUDGET:
                    raise S.LensRefusal(f"this lens makes more than {S.BUDGET} scene nodes. Put `clamp N` on the repeat (line {each['line']}); the text will say how many are left")
                delta = len(cb) - old["cb0"]
                for g in old["nodes"]:
                    n = g["node"]
                    if g.get("members"):
                        n["members"]["at"] = len(w.events)
                        continue
                    g["cb"] = list(cb) + g["cb"][old["cb0"]:]
                    n["reads"] = _fence_reads(w, g["fields0"], g["ids0"], g["cb"])
                    _bind(w, n)
                old["cb0"] = len(cb)
                for k2, e2 in old["inner"]:
                    e2["cb0"] += delta
                    nxt[k2] = e2
                    used.add(k2)
                for r in acc.nodes:
                    r.extend(old["nodes"])
                for r in acc.entries:
                    r.append((key, old))
                    r.extend(old["inner"])
                nxt[key] = old
                _STATS["kept"] += 1
                return old["out"]
            del acc.R[mark:]
            for r, m in zip(acc.rec, marks):
                del r[m:]
        asks, nodes, inner = [], [], []
        acc.rec.append(asks)
        acc.nodes.append(nodes)
        acc.entries.append(inner)
        c0 = count[0]
        try:
            out = make(each, ictx, key, layout, chain, cb)
        finally:
            acc.rec.pop()
            acc.nodes.pop()
            acc.entries.pop()
        e = {"fp": fp, "asks": asks, "nodes": nodes, "inner": inner, "count": count[0] - c0, "out": out, "cb0": len(cb)}
        nxt[key] = e
        for r in acc.entries:
            r.append((key, e))
        _STATS["made"] += 1
        return out

    def spread_of(node, index, kid):
        sp, item = node["emit"].get("spread"), w.nodes.get(kid.get("item") or "")
        if not sp:
            return
        if node["emit"]["layout"] != "free":
            raise S.LensRefusal(f"line {node['line']}: spread places parts by position, which only a `free` part can honour")
        xy = {}
        for axis, (start, step, top) in sp.items():
            if step.startswith("$"):
                if step[1:] not in props or not str(props[step[1:]]).lstrip("-").isdigit():
                    raise S.LensRefusal(f"line {node['line']}: spread step {step}: this lens has no numeric prop {step[1:]!r}. Set it: do prop <this lens> {step[1:]}=150")
                step = props[step[1:]]
            xy[axis] = max(0, min(top, start + index * int(step)))
        kid["box"] = [xy.get("x", 0), xy.get("y", 0), item["w"] if item else 200, item["h"] if item else 80]
        kid["placed"] = "spread"

    def absent(node, key, ctx, why=None):
        return {"part": node["part"], "key": key, "role": None, "layout": None, "item": ctx.get("item"), "box": None,
                "text": None, "clamp": None, "acts": [], "kids": [], "absent": node["guard"]["src"], **({"why": why} if why else {})}

    def make(node, ctx, key, parent_layout="free", chain=(), cb=()):
        chain = chain + (node["ast"],)
        cb = list(cb)                      # sable-8 amended: R_g includes the binds on the gesture's chain
        em = node["emit"]
        if em["at"] == "item" and parent_layout != "free":
            raise S.LensRefusal(f"line {node['line']}: `at item` places a part by its world position, which only a `free` parent can honour; "
                                f"its parent is {parent_layout or 'unlaid'}. Make the parent free, or drop `at item`")
        ctx = dict(ctx)
        ctx.update({k: v for k, v in host.items() if v is not None})
        frames = dict(ctx.get("_frames") or {})
        ctx["_frames"] = frames
        track = {"frames": set(), "reads": {}, "missing": set(), "bad": set()}
        # Juniper's freshness words: $touched, $touched.by, $changed.<field>, as host reads of the last event
        asked = {d for group in node["deps"].values() for d in (group if isinstance(group, list) and group and isinstance(group[0], str) else sum(group, []) if isinstance(group, list) else [])}
        rid = ctx.get("id") or ctx.get("item")
        if rid and any(d == "touched" or d.startswith("touched.") or d.startswith("changed.") for d in asked):
            t = acc.touched(rid)
            ctx["touched"] = f"{t['id']} {t['verb']} · {t['at']}" if t else ""
            frames["touched"] = dict(t or {}, id=(t or {}).get("id"))
            ch = {}
            for d in asked:
                if d.startswith("changed."):
                    f = d.split(".", 1)[1]
                    c = acc.touched(rid, S._aspect_of_field(f) or f)
                    ch[f] = f"{c['id']} {c['verb']} · {c['at']}" if c else None
            frames["changed"] = ch

        def frame_reads():
            """This part's reads of frame fields so far, as fence entries: what its lets and bind were built from."""
            fl = {}
            for k in track["reads"]:
                fr, _, fld = k.partition(".")
                if fr in S.HOST_FRAMES:
                    continue
                fid, a = frames.get(fr, {}).get("id"), S._aspect_of_field(fld)
                if fid and a and S._rev_of(w, fid) is not None:
                    fl.setdefault(fid, set()).add(a)
            return [[i, S._rev_of(w, i), sorted(a)] for i, a in fl.items()]
        # --- bind one
        the_state = "live"
        b = node["bind"]
        if b and b["kind"] == "one":
            sel_text = S._fill(b["q"], ctx, track)
            named, ids = acc.select(sel_text)
            # the membership read (q, S): the whole answer, since a new match anywhere turns live into ambiguous
            cb.append(["select", sel_text, [list(x) for x in named] if named is not None else list(ids)])
            if named is not None:
                ids = [i for i, st in named if st == "live"] or [i for i, st in named if st == "unplaced"]
            if len(ids) == 1:
                tc = acc.thing(ids[0])
                for k, v in b["capture"].items():
                    live = tc.get(k) if (k in tc and not k.startswith("_")) else (tc.get("_props") or {}).get(k)
                    tc.setdefault("_captured", []).append((k, v, live))
                    tc.setdefault("_captured_fields", set()).add(k)
                    if k in tc and not k.startswith("_"):
                        tc[k] = v
                    else:
                        tc["_props"] = dict(tc.get("_props") or {}, **{k: v})
                ctx.update({k: v for k, v in tc.items() if k != "_frames"})
                if b["as"]:
                    frames[b["as"]] = tc
                the_state = f"-> {tc['id']}" + (f" ({ids[0]})" if ids[0] != tc["id"] else "")
            else:
                the_state = "empty" if not ids else "ambiguous: " + ", ".join(ids)
        out = {"part": node["part"], "key": key, "role": em["role"], "layout": em["layout"], "item": ctx.get("item"),
               "box": None, "text": None, "clamp": em["clamp"], "acts": [], "kids": []}
        out.update({k: em[k] for k in S.PAINT_WORDS if k in em})
        if isinstance(out.get("share"), str):
            del out["share"]                    # a5496: filled below, once the lets are known; never sent unfilled
        if isinstance(out.get("fold"), str) and "$" in out["fold"]:
            out["fold"] = S._fill(out["fold"], {**(ctx.get("_props") or {}), **ctx}, track)      # a fold's label is words, like text
        if b and b["kind"] == "one":
            out["the"] = (S._fill(b["q"], ctx), the_state)
        if b and b.get("as"):
            out["as"] = b["as"]
        if ctx.get("_captured") and b and b["kind"] == "one":
            out["captured"] = [{"field": k, "value": v, "now": live, "same": (str(live) == str(v))} for k, v, live in ctx["_captured"]]
        if the_state not in ("live",) and not the_state.startswith("->"):
            return out
        # --- lets (`count <selection>` is one of them since 9 Oct: `let count = count(<selection>)`, a1101)
        def xenv():
            """The expression evaluator's door to this part: $names and lets from the frame, selections through the
            accessor (a membership read on the gesture's chain), a member's field through the accessor's thing read."""
            vals = ctx.get("_values") or {}
            rowbag = []
            def get(name):
                bare = name[1:] if name.startswith("$") else name
                if "." not in bare and bare in vals:
                    return vals[bare]
                if not name.startswith("$"):
                    return ctx.get(name)
                v = S._fill(name, dict(ctx.get("_props") or {}, **ctx), track)
                return None if v in (name, "") else v
            def select(q):
                q = S._fill(q, ctx, track)
                if S.source_head(q) in S.SOURCES:          # 8 Oct: count(house doing=awake) counts a source's rows
                    rs = acc.rows(q) or []
                    # 13 Oct: each row is its own member, so join($quote of lines:f3 about=a9) reads the row's own field
                    keys = [f"\x00row{len(rowbag) + k}" for k in range(len(rs))]
                    rowbag.extend(rs)
                    return keys
                named, ids = acc.select(q)
                ids = [i for i, _ in named] if named is not None else ids
                cb.append(["select", q, [list(x) for x in named] if named is not None else list(ids)])
                return ids
            def field(i, f):
                if isinstance(i, str) and i.startswith("\x00row"):
                    return rowbag[int(i[4:])].get(f)
                tc = acc.thing(i)
                # An aggregate's member fields are real reads too. Recording only
                # membership let a computed command carry old text without its
                # revision, and left its target unseen at dispatch.
                aspect = S._aspect_of_field(f)
                nd = w.nodes.get(i)
                if nd:
                    cb.append([i, nd["rev"], ["place"]])
                owner = (nd.get("subject") or i) if nd else i
                if aspect and owner and S._rev_of(w, owner) is not None:
                    cb.append([owner, S._rev_of(w, owner), [aspect]])
                return tc.get(f) if (f in tc and not f.startswith("_")) else (tc.get("_props") or {}).get(f)
            return {"get": get, "select": select, "field": field, "reads": []}
        groups = {}
        for let in node["lets"]:
            groups.setdefault(let["name"], []).append(let)
        for lname, defs in groups.items():      # an if: the first `when` that holds, else `otherwise`; an overlap is said
            held, otherwise = [], None
            for d in defs:
                if d["when"] == "otherwise":
                    otherwise = d
                elif d["when"] is None:
                    held.append((d, ""))
                else:
                    cv, cins = X.run(d["when"], xenv())
                    if X.holds(cv):
                        held.append((d, cins))
            chosen, cins = held[0] if held else ((otherwise, "") if otherwise else (None, ""))
            if chosen is None:
                val, ins, said = X.none(f"no answer for {lname} holds here"), "", "; ".join(d["expr"] + " when " + str(d["when"]) for d in defs)
            else:
                val, ins = X.run(chosen["expr"], xenv())
                said = chosen["expr"] + (f" when {chosen['when']}" if chosen["when"] and chosen["when"] != "otherwise" else " otherwise" if chosen["when"] else "")
            ins = "; ".join(x for x in (cins, ins) if x)
            out.setdefault("derived", []).append({"name": lname, "interp": "let", "inputs": [], "result": X.fmt(val), "error": None,
                                                  "expr": said, "inputs_s": ins, "overlap": len(held) if len(held) > 1 else 0})
            ctx["_values"] = dict(ctx.get("_values") or {}, **{lname: val})
            ctx["_lets"] = set(ctx.get("_lets") or ()) | {lname}
            ctx[lname] = X.fmt(val, reach=False)          # $name in words and selections prints it; none prints none
        # --- guard: one rule, judged against the part's own frame after its bind and lets (sable-8 section 2)
        g = node["guard"]
        if g and X.looks_like(g["src"], ctx.get("_lets") or ()):
            val, ins = X.run(g["src"], xenv())
            h = X.holds(val)
            if h is None:
                out.update(text=None, acts=[], kids=[], absent=g["src"], why=f"can't tell: {val.why}" + (f" ({ins})" if ins else ""))
                return out
            if not h:
                out.update(text=None, acts=[], kids=[], absent=g["src"], why=f"{g['src']} is false" + (f" ({ins})" if ins else ""))
                return out
            out["test"] = g["src"] + (f" ({ins})" if ins else "")
        elif g:
            q = S._fill(g["q"], ctx)
            named, ids = acc.select(q)
            ids = [i for i, _ in named] if named is not None else ids
            t = ctx.get("item") or ctx.get("id")
            ok = (t in ids or ctx.get("id") in ids) if t else bool(ids)
            if not ok:
                a = absent(node, key, ctx)
                a["why"] = f"not {q}"
                return a
        # --- emit
        if em["role_when"]:             # a1105: the look follows the thing's state; each selection is a read in R
            def sel(q):
                named, ids = acc.select(q)
                return [i for i, _ in named] if named is not None else ids
            out["role"], why = S.role_of(em["role"], em["role_when"], ctx, track, sel, run=lambda t: X.run(t, xenv()))
            if why:
                out["since"] = why
        if em["at"] == "item" and ctx.get("item") in w.nodes:
            n = w.nodes[ctx["item"]]
            out["box"] = [n["x"], n["y"], n["w"], n["h"]]
            out["facts"] = [f for f in w.relations(ctx["item"]) if f != "clear"]
        if em["text"] is not None:
            pv = dict(ctx.get("_props") or {})
            missing = [p for p in em["props"] if p not in pv and p not in ctx]
            fill_ctx = {p: "" for p in missing}
            fill_ctx.update(pv)
            fill_ctx.update({k: v for k, v in ctx.items() if k not in ("n", "count")} if (b and b["kind"] == "many") else ctx)
            if "$(" in em["text"]:
                out["text"], computed = S._fill_text(em["text"], fill_ctx, track, lambda e: X.run(e, xenv()))
                if computed:
                    out["computed"] = computed
            else:
                out["text"] = S._fill(em["text"], fill_ctx, track)
            if em.get("light"):              # 13 Oct: the passages to light, filled as the words are
                lt = em["light"]
                out["light"] = (S._fill_text(lt, fill_ctx, track, lambda e: X.run(e, xenv()))[0] if "$(" in lt
                                else S._fill(lt, fill_ctx, track))
            if em.get("markdown") and "[[" in (out["text"] or ""):     # a5820: what each [[wikilink]] names, read now
                out["wikilinks"] = S.wikilinks_of(w, out["text"], acc.thing)
            # a6109: an id in words that are only read is drawn as the name of what it names. Not recorded as a read:
            # a name is how the words look, never what a press on this part was fenced on
            if out["text"] and not em.get("ids") and not em.get("plain") and not em.get("picture") and not em.get("live") \
                    and (em.get("markdown") or not any(a["on"] == "edit" for a in node["acts"])):   # a document's drawn lines name too
                # a person's name only in a text that is no button and no document (c6186: the To chips stay chips)
                named = S.things_of(w, out["text"], people=not node["acts"] and not em.get("markdown"))
                if named:
                    out["things"] = named
            if isinstance(em.get("markdown"), str) and any(a["on"] == "edit" for a in node["acts"]):
                # `markdown links <selection>`: what typing [[ offers, read as one membership read (at most 500)
                named, ids = acc.select(S._fill(em["markdown"], fill_ctx, track))
                ids = [i for i, _ in named] if named is not None else ids
                out["titles"] = [{"id": i, "title": c.get("title") or "", "kind": c.get("kind") or ""}
                                 for i in ids[:500] for c in [S._ctx_for(w, i)] if c.get("title")]
            if em["props"]:
                out["read"] = {p: pv.get(p) for p in em["props"] if p in pv}
            if missing:
                out["missing"] = missing
        if isinstance(em.get("share"), str):          # a5496: `share $(expr)`, a weight that follows data
            sc_ctx = {**(ctx.get("_props") or {}), **ctx}
            s = em["share"]
            s = S._fill_text(s, sc_ctx, track, lambda e: X.run(e, xenv()))[0] if "$(" in s else S._fill(s, sc_ctx, track)
            try:
                weight = float(s)
            except (TypeError, ValueError):
                weight = 0
            if weight > 0:
                out["share"] = int(weight) if weight == int(weight) else weight
            else:
                out.pop("share", None)
        if ctx.get("_state") and ctx["_state"] != "live":
            out["state"] = ctx["_state"]
        if isinstance(out.get("fold"), str) and "$(" in out["fold"]:      # a5530: a label computes as words do: fold "$(total)"
            out["fold"] = S._fill_text(out["fold"], {**(ctx.get("_props") or {}), **ctx}, track, lambda e: X.run(e, xenv()))[0]
        if em.get("picture") and ctx.get("item"):
            original = acc.thing(ctx["item"])
            if out.get("text") == original.get("text"):
                out["image_regions"] = original.get("_image_regions", [])
        # --- acts
        safe = {k: (S._cmd_value(v) if isinstance(v, str) else v) for k, v in ctx.items()}
        out["id"] = ctx.get("id")
        safe["_frames"] = {k: {kk: (S._cmd_value(vv) if isinstance(vv, str) else vv) for kk, vv in f.items()} for k, f in frames.items()}
        def act_line(line):
            # Juniper and Pike, 7 Oct: `do split $item $(next) ...` reached the desk as the words '$(next)', and a
            # paragraph was made with block=$(next). A command computes $( ) as words do, when the part is built
            if "$(" not in line:
                return S._fill(line, safe, track)
            return S._fill_text(line, safe, track, lambda e: X.run(e, xenv()), esc=S._cmd_value)[0]
        def offered(a):                  # 14 Oct: `on menu "<label>" when <test>`: the entry is there only where it holds
            return not a.get("when") or X.holds(X.run(a["when"], xenv())[0]) is True
        acts = [] if (node["acts"] and ctx.get("_state") in ("gone", "unplaced")) else [
            {"on": a["on"], "line": act_line(a["line"]), **{k: a[k] for k in ("part", "side", "label") if a.get(k)}}
            for a in node["acts"] if offered(a)]
        if node["carry"]:
            if not ctx.get("item"):
                raise S.LensRefusal(f"line {node['line']}: `carry` needs a world thing behind this part, and here there is none (a derived row or the root)")
            acts.append({"on": "carry"})
        out["acts"] = acts
        if track["bad"]:
            raise S.LensRefusal(f"line {node['line']}: ${sorted(track['bad'])[0]}.field: no part above this one is named `as {sorted(track['bad'])[0]}`")
        # what this node printed whole, for the command line's seen index (jeff-2): its own fields and the frame fields
        own = sorted({a for f in track.get("own", ()) if (a := S._aspect_of_field(f))})
        if own:
            out["shown"] = own
        fsh = {}
        for k in track["reads"]:
            fr, _, fld = k.partition(".")
            if fr in S.HOST_FRAMES:
                continue
            fid, a = frames.get(fr, {}).get("id"), S._aspect_of_field(fld)
            if fid and a:
                fsh.setdefault(fid, set()).add(a)
        if fsh:
            out["fshown"] = {i: sorted(a) for i, a in fsh.items()}
        if track["reads"]:
            out["freads"] = {k: v for k, v in track["reads"].items()}
            out["frames"] = {f: frames[f].get("id") for f in track["frames"] if f in frames and f not in S.HOST_FRAMES}
        if track["missing"]:
            out["missing"] = sorted(set(out.get("missing") or []) | {f"{m} on {frames[m.split('.')[0]].get('id')}" for m in track["missing"]})
        if out["acts"]:
            fields, ids0 = {}, []
            current_node = w.nodes.get(ctx.get("item") or "") or {}
            sj = current_node.get("subject") or current_node.get("id")
            for f in track.get("own", ()):
                a = S._aspect_of_field(f)
                if a and sj:
                    fields.setdefault(sj, set()).add(a)
                if f in ("before", "after") and current_node.get("parent"):
                    parent = current_node["parent"]
                    ids0.append((parent, True))
                    fields.setdefault(parent, set()).add("place")
            for k in track["reads"]:
                fr, _, fld = k.partition(".")
                if fr in S.HOST_FRAMES:
                    continue                    # a freshness read is not fenced: a comment must not stale a card's gestures
                fid = frames.get(fr, {}).get("id")
                a = S._aspect_of_field(fld)
                if fid and a:
                    fields.setdefault(fid, set()).add(a)
            ids0 += [(i, False) for i in [sj] + [frames[f].get("id") for f in track["frames"] if f in frames and f not in S.HOST_FRAMES] if i]
            g = {"node": out, "fields0": fields, "ids0": ids0, "cb": list(cb)}
            out["reads"] = _fence_reads(w, fields, ids0, g["cb"])
            out["defpart"] = {"path": "/".join(n["name"] for n in chain), "hash": S._chain_hash(chain)}
            for r in acc.nodes:
                r.append(g)
        _bind(w, out)
        count[0] += 1
        if count[0] > S.BUDGET:
            raise S.LensRefusal(f"this lens makes more than {S.BUDGET} scene nodes. Put `clamp N` on the repeat (line {node['line']}); the text will say how many are left")
        # --- instances
        if b and b["kind"] == "many":
            each = irs[b["each"]]
            keep = b["clamp"] or 10 ** 9
            pick = (lambda xs: xs[-keep:]) if b.get("last") else (lambda xs: xs[:keep])      # noqa: E731  clamp last N: the newest
            if b["of"]:
                sel_text = S._fill(b["of"], ctx)
                out["of"] = sel_text
                rs = acc.rows(sel_text) if S.source_head(sel_text) in S.SOURCES else None
                total = len(rs) if rs is not None else None
                if b.get("by"):
                    out["by"] = b["by"]             # a1069: ordered here, in the scene, so both printers show one order
                if rs is not None and b.get("by"):
                    rs = moo.sort_by(rs, b["by"], lambda r, k: r.get(k))
                if b.get("run"):
                    out["run"] = b["run"]
                if rs is not None:
                    first = max(0, len(rs) - keep) if b.get("last") else 0
                    place = S.run_places([r.get(b["run"]) for r in rs]) if b.get("run") else None
                    for k, r in enumerate(rs[first:first + keep], first):
                        if place:
                            r = dict(r, run=place[k])
                        okey = r.get("rid") or r.get("cid") or r.get("eid") or r.get("name") or (S._slug(r["heading"]) if "heading" in r else k)
                        out["kids"].append(instance(each, S._inst(ctx, node["ast"], {**ctx, "count": total, "index": k + 1, **r}), f"{key}/{okey}", em["layout"], chain, cb))
                else:
                    named, ids = acc.select(sel_text)
                    if b.get("by"):
                        if named is not None:
                            named = moo.sort_by(named, b["by"], lambda x, k: moo.props_of(w, x[0]).get(k))
                        else:
                            ids = moo.order_by(w, list(ids), b["by"])
                    # a clamped repeat's fence compares the shown prefix, so it says the order it was shown in
                    shown = [["select", sel_text, [list(x) for x in pick(named)] if named is not None else list(pick(list(ids))), keep]
                             + ([list(b["by"])] if b.get("by") else [])] if b["clamp"] else []
                    if named is not None and not shown:
                        shown = [["select", sel_text, [list(x) for x in named]]]
                    order = [x[0] for x in named] if named is not None else list(ids)
                    place = dict(zip(order, S.run_places([moo.props_of(w, i).get(b["run"]) for i in order]))) if b.get("run") else {}
                    if named is not None:
                        total = len(named)
                        base = max(0, total - keep) if b.get("last") else 0      # $index: the place in the whole repeat
                        for k, (i, st) in enumerate(pick(named), base + 1):
                            mcb = cb + shown + ([[i, S._rev_of(w, i), []]] if st != "live" else _member_reads(w, i, sel_text))
                            out["kids"].append(instance(each, S._inst(ctx, node["ast"], dict(acc.thing(i, st), count=total, index=k, **({"run": place[i]} if place else {}))), f"{key}/{i}", em["layout"], chain, mcb))
                        out["states"] = [f"{i} {st}" for i, st in named if st != "live"]
                    else:
                        total = len(ids)
                        base = max(0, total - keep) if b.get("last") else 0
                        for k, i in enumerate(pick(list(ids)), base + 1):
                            out["kids"].append(instance(each, S._inst(ctx, node["ast"], dict(acc.thing(i), count=total, index=k, **({"run": place[i]} if place else {}))), f"{key}/{i}", em["layout"], chain, cb + shown + _member_reads(w, i, sel_text)))
                got = [k["item"] or k["key"] for k in out["kids"]]
                out["members"] = {"of": sel_text, "n": total, "ids": got, "at": len(w.events)}
                for r in acc.nodes:
                    r.append({"node": out, "members": True})
                if total > keep:
                    out["cut"] = total - keep
                    cut = {"part": "cut", "key": f"{key}/cut", "role": "cut", "layout": None, "item": None, "box": None,
                           "text": (f"{total - keep} earlier not shown (clamp last {keep}); " if b.get("last") else f"{total - keep} more not shown (clamp {keep}); ")
                           + f"find {sel_text} lists all {total}", "clamp": None, "acts": [], "kids": []}
                    if S.things_of(w, sel_text):                  # a6109: in:f155 is drawn as the board's name
                        cut["things"] = S.things_of(w, sel_text)
                    if b.get("last"):
                        out["kids"].insert(0, cut)
                    else:
                        out["kids"].append(cut)
            else:
                held = (ctx.get("_values") or {}).get(b["over"])         # 9 Oct: a let of kind rows (days-from(a, b))
                rows_over = held.v if (held is not None and getattr(held, "kind", "") == "rows") else ctx.get("_" + b["over"], [])
                total = len(rows_over)
                dcb = cb + frame_reads()
                for k, v in enumerate(rows_over):
                    if isinstance(v, dict):
                        ictx = S._inst(ctx, node["ast"], dict(ctx, it=str(v.get("date", v.get("n", ""))), count=len(rows_over), index=k + 1))
                        ictx["_frames"] = dict(ictx["_frames"], it=v)
                        out["kids"].append(make(each, ictx, f"{key}/{S._slug(str(v.get('n', k)))}", em["layout"], chain, dcb))
                    else:
                        out["kids"].append(make(each, S._inst(ctx, node["ast"], dict(ctx, it=v, count=len(rows_over), index=k + 1)), f"{key}/{S._slug(str(v))}", em["layout"], chain, dcb))
            seen_keys = {}
            for kid in out["kids"]:
                c = seen_keys.get(kid["key"], 0) + 1
                seen_keys[kid["key"]] = c
                if c > 1:
                    old = kid["key"]
                    nxt.pop(old, None)           # a kept instance must not carry a name given for this build's twin
                    kid["key"] = f"{old}#{c}"
                    S._reprefix(kid, old, kid["key"])
            out["n"] = len(out["kids"]) - (1 if out.get("cut") else 0)
            for k, kid in enumerate(out["kids"][:out["n"]]):
                spread_of(node, k, kid)
            out["size"] = total
            if out["text"] is not None:
                out["text"] = re.sub(r"\$count\b", str(total), out["text"].replace("$n", str(out["n"])))    # a1101: the true size
        # --- placed lens
        if node["place"]:
            inner = S._fill(node["place"], ctx)
            # a5949 (Sable's a4270): the placed lens starts on the thing this part stands on, when it stands on one
            on = ctx.get("item") if is_thing(w, ctx.get("item")) else None
            named = "$" in node["place"]       # a name from data: what it names is not this lens's fault
            held = len(closure) if closure is not None else 0
            try:
                if inner.lower() in stack:
                    raise S.LensRefusal(f"line {node['line']}: lens {inner} contains itself ({' -> '.join(stack + (inner.lower(),))})")
                sub = compile_lens(desk, acc.define(inner), stack + (inner.lower(),), count, closure if closure is not None else [], acc, cb,
                                   on=on, prefix=f"{key}/lens:{inner}")
            except S.LensRefusal as e:
                # a5949: a lens named from data (`lens $v.with`) that is missing, contains itself or does not compile is
                # said in one line in its place, and its placer (the home base) is still drawn; a name written in the
                # lens refuses the lens, as before
                if not named:
                    raise
                if closure is not None:
                    del closure[held:]
                sub = cut_node("lens", f"lens {inner or '(no name)'} cannot be drawn here: {str(e).split('. ')[0]}")
            sub["key"] = f"{key}/lens:{inner}"      # a6010: its parts were built under this key already (prefix)
            out["kids"].append(sub)
            out["lens"] = inner
        # --- fixed kids
        for kid in node["kids"]:
            out["kids"].append(make(kid, dict(ctx, n=out.get("n", ctx.get("n", "")), count=out.get("size", ctx.get("count", ""))), f"{key}/{kid['part']}", em["layout"], chain, cb))
        return out

    # a5949 (Sable's a4270): a lens stood on a thing starts on it, its fields and $item, as an instance of a repeat does
    root_ctx = {k: v for k, v in acc.thing(on).items() if k != "_frames"} if on else {}
    sc = make(irs[root], root_ctx, f"{prefix}/{root}" if prefix else root, cb=cb)
    if prefix:
        sc["key"] = prefix              # the placed lens's root stands at its placer's key; its parts under <prefix>/<root>
    sc["R"] = list(acc.R)
    if not off:
        _REUSE.pop(ck, None)
        _REUSE[ck] = nxt
        while len(_REUSE) > 24:
            _REUSE.pop(next(iter(_REUSE)))
    return sc


def is_thing(w, i):
    """a5949: whether an id names a thing (an appearance or a subject) a lens can be stood on."""
    return isinstance(i, str) and (i in w.nodes or i in w.subjects)


def may_read(desk, on):
    """a5949 (Sable, on a5949; Juniper in f4358: an address is not believed): THE one place that asks whether this
    viewer may have a lens stood on this thing, for all three doors (a typed `scene <lens> on`, an address's on=, a lens
    placed on a thing), since every one of them comes through compile_lens. Today everyone here may read everything, so
    it only asks that the id names a thing; strangers (Juniper's room) will add their refusal here. -> None or why not."""
    if not is_thing(desk.world, on):
        return f"on={on}: no thing has that id"
    return None


def stood_refusal(desk, acc, s, on):
    """a5949 (Sable's a4270, 'each lens must say what it can stand on and refuse the rest in words'): may_read, then a
    lens note's stands_on=<selection>, what it can be stood on. -> the words of a refusal, or None when it may stand."""
    if not on:
        return None
    no = may_read(desk, on)
    if no:
        return f"{no}, so lens {s['title']} cannot be stood on it"
    sel = (s.get("props") or {}).get("stands_on")
    if not sel:
        return None
    w = desk.world
    mine = {on} | ({w.nodes[on].get("subject")} if on in w.nodes else set(w.appearances_of(on) if on in w.subjects else []))
    named, ids = acc.select(sel)
    hits = {i for i, _ in named} if named is not None else set(ids)
    hits |= {w.nodes[i].get("subject") for i in hits if i in w.nodes}
    if mine & hits:
        return None
    subj = w.subjects.get(w.nodes[on].get("subject")) if on in w.nodes else w.subjects.get(on)
    return f"lens {s['title']} stands on {sel}; {(subj or {}).get('title', on)} ({on}) is not one"


def cut_node(part, text):
    """a5949: one line said in place of a lens that cannot be drawn here (stood on what it does not stand on, or placed
    by a name from data that is missing, contains itself or does not compile), so its placer is still drawn."""
    return {"part": part, "key": part, "role": "cut", "layout": None, "item": None, "box": None, "text": text,
            "clamp": None, "acts": [], "kids": []}


def compile_lens(desk, s, stack, count, closure, acc=None, cb=(), on=None, prefix=None):
    """One lens to a scene through the staged pipeline, recording the definition used; fallback as scene._compile does.
    `on` (a5949): the thing the lens is stood on, where its root starts; a lens note's stands_on= may refuse it.
    `prefix` (a6010): the key a placed lens stands at, under which its parts are built (evaluate)."""
    good = getattr(desk, "_lens_good", None)
    if good is None:
        good = desk._lens_good = {}
    entry = {"lens": s["title"], "id": s["id"], "rev": s["rev"], "status": "current"}
    closure.append(entry)
    mark = len(closure)

    def stamp(node):
        dp = node.get("defpart")
        if dp is not None and "lens" not in dp:
            dp["lens"], dp["id"] = s["title"], s["id"]
        for k in node.get("kids") or []:
            stamp(k)
    acc = acc or Accessor(desk)
    prev_home = getattr(acc, "home", None)
    acc.home = S.room_of_thing(desk.world, s)      # 9 Oct (step 7): this lens's own lookups (its style, the lenses it places) stand in its room
    try:
        no = stood_refusal(desk, acc, s, on)
        if no:
            return cut_node(stack[-1] if stack else s["title"], no)
        try:
            import persons
            import verbs
            b = verbs.binding_of(desk.world, ("s", s["id"]), s["text"])     # a1590: its names mean whom they meant when saved
            with persons.reading(desk, (b or {}).get("persons")):
                sc = evaluate(desk, s["text"], stack, count, props=s.get("props") or {}, closure=closure, acc=acc, cb=cb, on=on, prefix=prefix)
            stamp(sc)
            good[s["id"]] = {"text": s["text"], "rev": s["rev"]}
            return sc
        except S.LensRefusal as e:
            if getattr(e, "lens", None) is None:
                e.lens = s            # the innermost lens that refused, so a check can quote its line
            g = good.get(s["id"])
            g = {"text": g, "rev": None} if isinstance(g, str) else g
            if not g:
                raise
            del closure[mark:]
            entry.update(status="fallback", shown_rev=g["rev"], refusal=str(e), refused_in=e.lens)
            sc = evaluate(desk, g["text"], stack, count, props=s.get("props") or {}, closure=closure, acc=acc, on=on, prefix=prefix)
            stamp(sc)
            sc["broken"] = f"lens {s['title']}: {e}"
            return sc
    finally:
        acc.home = prev_home


def _quote_line(s, msg):
    """a1101: a refusal that names a line quotes it, from the lens it came from."""
    import re as _re
    m = _re.match(r"line (\d+):", msg or "")
    lines = (s or {}).get("text", "").splitlines()
    if not m or not 0 < int(m.group(1)) <= len(lines):
        return ""
    return f" | {s['title']} line {m.group(1)}: {lines[int(m.group(1)) - 1].strip()[:160]}"


def style_note(desk, s):
    """What paints lens `s`: '· style pixel', or the default said out loud (a1101: a missing style= was silent)."""
    name = (s.get("props") or {}).get("style")
    if not name:
        return "no style=; using the default (calm)"
    st = S.style_source(desk, name, S.room_of_thing(desk.world, s))
    if st is None:
        return f"style {name}: no such style"
    c = S.style_check(st["text"])
    return f"style {name}" + (f" (does not parse: {c['refusal']})" if c["refusal"] else "")


def check(desk, s, ages=False):
    """-> (compiles, one line): whether lens `s` (a subject) compiles as its text stands now, its node count against the
    budget, what paints it, and a refusal with its line. The fallback to the last good version is reported, not shown."""
    closure, count = [], [0]
    try:
        compile_lens(desk, s, (s["title"].lower(),), count, closure, Accessor(desk))
    except S.LensRefusal as e:
        return False, f"lens {s['title']} does not compile: {e}{_quote_line(getattr(e, 'lens', None) or s, str(e))}"
    fallen = [c for c in closure if c["status"] == "fallback"]
    if fallen:
        c = fallen[0]
        return False, (f"lens {s['title']} does not compile" + (f" (inner lens {c['lens']})" if c["id"] != s["id"] else "")
                       + f": {c['refusal']}{_quote_line(c.get('refused_in'), c['refusal'])}; its painter shows the last version that did, gestures off")
    return True, f"lens {s['title']} compiles: {count[0]} of {S.BUDGET} nodes · {style_note(desk, s)}" + (paint_ages(desk, s, closure) if ages else "")


def paint_ages(desk, s, closure):
    """a1473, for `scene <lens> ok`: how old each viewer's report of sizes is, the oldest first, and whether it is of the
    lens as it stands."""
    name = (s.get("props") or {}).get("style")
    rev = (S.style_source(desk, name, S.room_of_thing(desk.world, s)) or {}).get("rev", "") if name else ""
    views, since = S.reported_views(desk, s["title"])
    vs = S.judge_views(desk, views, closure, rev)
    vs = sorted(((a, v) for a, v in vs.items() if v.get("paint")), key=lambda av: str(av[1].get("time")))
    if not vs:
        return (" · painted sizes: none reported" + (f" since the house started ({S._clock(since)})" if since else "")
                + " (no viewer has it open with a painter that reports them)")
    say = {"current": "current", "stale": None, "unknown": "revision unknown"}
    return " · painted sizes, oldest first: " + "; ".join(
        f"{a} {v['paint']['age']} ({say[v['paint']['state']] or 'before ' + v['paint']['edit']})" for a, v in vs)


def find_parts(sc, path):
    """a1101: the nodes a part path names, topmost first. Each segment matches a part's name or its key segment, along a
    chain that ends at the node (people, people/list, list/f571, porch/main/people)."""
    segs = [x for x in path.strip("/").split("/") if x]
    hits = []

    def walk(n, chain, pkey):
        seg = n["key"][len(pkey) + 1:] if pkey and n["key"].startswith(pkey + "/") else n["key"]
        chain = chain + [(n.get("part"), seg)]
        tail = chain[-len(segs):]
        if len(tail) == len(segs) and all(sg in (p, k) for sg, (p, k) in zip(segs, tail)):
            hits.append(n)
            return
        for k in n.get("kids") or []:
            walk(k, chain, n["key"])
    walk(sc, [], None)
    return hits


def part_names(sc):
    out, stack = set(), [sc]
    while stack:
        n = stack.pop()
        out.add(n.get("part"))
        stack += n.get("kids") or []
    return sorted(x for x in out if x)


def scene_for(desk, name, part=None, words=None, on=None):
    """-> (scene, text), as scene.scene_for, through the staged pipeline. With `part`, the text is only the parts that
    path names (find_parts) and what is inside them; scene["printed"] lists those nodes. With `words` (a4179:
    {"start": n, "whole": bool}) the text is the scene's words alone (scene.to_words), and scene["said"] lists the
    nodes it showed whole, each for itself. With `on` (a5949) the lens is stood on that thing: an address is not
    believed (Juniper, a4270), so an id that names no thing is refused here, where the scene is built."""
    s = S.find_lens(desk, name)
    closure = []
    acc = Accessor(desk)
    import promises
    with promises.held(desk.world), S.still(desk.world):     # a4838: the world holds still while a lens is built
        sc = compile_lens(desk, s, (s["title"].lower(),), [0], closure, acc, on=on)
        _STATS["builds"] += 1
        if os.environ.get("LENS_REUSE") != "off" and (os.environ.get("LENS_REUSE_VERIFY") == "1" or _STATS["builds"] % VERIFY_EVERY == 0):
            closure2 = []
            _OFF[0] = True
            try:
                sc2 = compile_lens(desk, s, (s["title"].lower(),), [0], closure2, Accessor(desk), on=on)
            finally:
                _OFF[0] = False
            S.emit(sc)
            S.emit(sc2)
            d = _first_diff(sc, sc2)
            if d:
                _STATS["differed"] += 1
                _REUSE.clear()
                try:
                    with open(S.HOUSE_STATE / "lens-reuse.err", "a", encoding="utf-8") as f:
                        f.write(f"{_time.strftime('%Y-%m-%dT%H:%M:%S')} {getattr(desk, '_session', '')} {s['title']} as {desk.world.me}: {d}\n")
                except OSError:
                    pass
                sc, closure = sc2, closure2
    S.emit(sc)
    at = len(desk.world.events)
    fallen = [c for c in closure if c["status"] == "fallback"]
    sc["def"] = dict(lens=s["title"], id=s["id"], rev=s["rev"], status="fallback" if fallen else "current", closure=closure,
                     frame=".".join(f"{c['id']}r{c['rev']}" for c in closure), **S._identity(), **({"on": on} if on else {}))
    name = (s.get("props") or {}).get("style")
    home = S.room_of_thing(desk.world, s)          # 9 Oct (step 7): the style nearest the lens's own room
    if name:                                  # F7: which style paints this lens, and which revision of it
        st = S.style_source(desk, name, home) or {}
        sc["def"].update(style_name=name, style_rev=st.get("rev", ""))
    S.mark_pulse(sc, S.pulsing_roles(desk, name, home))   # a1140: the painter installs this one style for the whole scene
    views, since = S.reported_views(desk, s["title"])
    sc["views"] = S.judge_views(desk, views, closure, sc["def"].get("style_rev"))
    if since:
        sc["reports_since"] = since
    roots = None
    if part:
        roots = find_parts(sc, part)
        if not roots:
            raise S.LensRefusal(f"no part {part!r} in the scene of {s['title']}. Its parts: {' '.join(part_names(sc))}")
        sc["printed"] = roots
    if words is not None:
        text, sc["said"] = S.to_words(sc, s["title"], desk.world.me, at, roots=roots, part=part,
                                      start=words.get("start", 1), whole=words.get("whole", False))
    else:
        text = S.to_text(sc, s["title"], desk.world.me, at, roots=roots, part=part)
    if words is None and not (s.get("props") or {}).get("style"):
        head, _, rest = text.partition("\n")
        text = head + " · " + style_note(desk, s) + ("\n" + rest if rest else "")
    if fallen:
        head = "".join(f"! lens {c['lens']} no longer compiles: {c['refusal']}\n" for c in fallen)
        text = head + "! showing the last version that did; gestures are off until it compiles. Fix it with rewrite, or undo.\n" + text
    return sc, text
