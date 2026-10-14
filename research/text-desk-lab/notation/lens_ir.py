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

ABSENT = None          # printed (no x); a third value, distinct from "" and from false


class Accessor:
    """The seam: six questions, each recorded in R (sable-8 section 1)."""

    def __init__(self, desk):
        self.desk, self.w, self.R = desk, desk.world, []

    def value(self, r, a):
        c = S._ctx_for(self.w, r)
        v = c.get(a) if (a in c and not a.startswith("_")) else (c.get("_props") or {}).get(a)
        self.R.append(("value", r, a, S._rev_of(self.w, r)))
        return v

    def thing(self, r, state=None):
        """Every printable value of one thing, as one read of the thing (the printer says which fields were used)."""
        self.R.append(("thing", r, S._rev_of(self.w, r)))
        return S._ctx_for(self.w, r, state)

    def select(self, q):
        """Referents matching a selection, in the desk's order, as a membership read."""
        named = S._named(self.w, q)
        if named is not None:
            self.R.append(("select", q, [i for i, _ in named]))
            return named, None
        sel = self.desk._parse_selection(q)
        ids = list(sel[0]) if sel else []
        self.R.append(("select", q, ids))
        return None, ids

    def rows(self, src):
        rs = S.rows(self.desk, src)
        self.R.append(("rows", src, len(rs) if rs is not None else None))
        return rs

    def define(self, name):
        s = S.find_lens(self.desk, name, getattr(self, "home", None))     # 9 Oct: nearest to the placing lens's room
        self.R.append(("define", name, s["id"], s["rev"]))
        return s

    def touched(self, r, aspect=None):
        """The last event on thing `r` (its appearance or subject), or the last one that changed `aspect`; undone events
        and undos are skipped (an undo is not a touch, as `age<` already says). -> {id, at, by} or None."""
        w = self.w
        n = w.nodes.get(r)
        names = {r} | ({n["subject"]} if n and n.get("subject") else set()) | set(w.appearances_of(r) if r in w.subjects else [])
        hit = None
        for e in reversed(w.events):
            if e.get("undone") or e["verb"] == "undo":
                continue
            if e["target"] not in names and not (names & set(e.get("changed") or [])):
                continue
            if aspect and not aspects_meet({aspect}, event_aspects(e)):
                continue
            hit = e
            break
        self.R.append(("touched", r, aspect, hit["id"] if hit else None))
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
        return v


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
def evaluate(desk, src, stack=(), count=None, props=None, closure=None, acc=None, cb=()):
    props = props or {}
    acc = acc or Accessor(desk)
    # F7: the lens's own style; 9 Oct (step 7): found from the lens's own room (acc.home, set by compile_lens)
    root, parts = S.parse(src, roles=S.style_roles(desk, props.get("style"), getattr(acc, "home", None)), style=props.get("style"))
    S.resolve(root, parts)
    irs, root = lower(root, parts)
    w = desk.world
    count = count if count is not None else [0]
    host = {f: acc.host(f) for f in ("me", "today", "session")}

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
                    rs = acc.rows(q)
                    return [r.get("item") or k for k, r in enumerate(rs or [])]
                named, ids = acc.select(q)
                ids = [i for i, _ in named] if named is not None else ids
                cb.append(["select", q, list(ids)])
                return ids
            def field(i, f):
                tc = acc.thing(i)
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
            if em["props"]:
                out["read"] = {p: pv.get(p) for p in em["props"] if p in pv}
            if missing:
                out["missing"] = missing
        if ctx.get("_state") and ctx["_state"] != "live":
            out["state"] = ctx["_state"]
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
            return S._fill_text(line, safe, track, lambda e: X.run(e, xenv()))[0]
        acts = [] if (node["acts"] and ctx.get("_state") in ("gone", "unplaced")) else [
            {"on": a["on"], "line": act_line(a["line"]), **{k: a[k] for k in ("part", "label") if a.get(k)}} for a in node["acts"]]
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
            reads, fields = {}, {}
            sj = (w.nodes.get(ctx.get("item") or "") or {}).get("subject")
            for f in track.get("own", ()):
                a = S._aspect_of_field(f)
                if a and sj:
                    fields.setdefault(sj, set()).add(a)
            for k in track["reads"]:
                fr, _, fld = k.partition(".")
                if fr in S.HOST_FRAMES:
                    continue                    # a freshness read is not fenced: a comment must not stale a card's gestures
                fid = frames.get(fr, {}).get("id")
                a = S._aspect_of_field(fld)
                if fid and a:
                    fields.setdefault(fid, set()).add(a)
            for i in [sj] + [frames[f].get("id") for f in track["frames"] if f in frames and f not in S.HOST_FRAMES]:
                if i and S._rev_of(w, i) is not None:
                    reads[i] = S._rev_of(w, i)
            selects = []
            for e in cb:
                if e[0] == "select":
                    if e not in selects:
                        selects.append(e)
                elif S._rev_of(w, e[0]) is not None:
                    reads[e[0]] = S._rev_of(w, e[0])
                    fields.setdefault(e[0], set()).update(e[2])
            out["reads"] = [[i, r, sorted(fields.get(i) or [])] for i, r in sorted(reads.items())] + selects
            out["defpart"] = {"path": "/".join(n["name"] for n in chain), "hash": S._chain_hash(chain)}
        if ctx.get("item") in w.nodes and out["acts"]:
            out["rev"] = w.nodes[ctx["item"]]["rev"]
            nd = w.nodes[ctx["item"]]
            sj2 = w.subjects.get(nd.get("subject") or "")
            out["bind"] = {"subject": nd.get("subject"), "subject_rev": sj2["rev"] if sj2 else None, "parent": nd["parent"],
                           "parent_rev": w.nodes[nd["parent"]]["rev"] if nd["parent"] in w.nodes else None, "units": "px in parent"}
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
                    rs = sorted(rs, key=lambda r: tuple(moo.order_value(r.get(k)) for k in b["by"]))
                if b.get("run"):
                    out["run"] = b["run"]
                if rs is not None:
                    first = max(0, len(rs) - keep) if b.get("last") else 0
                    place = S.run_places([r.get(b["run"]) for r in rs]) if b.get("run") else None
                    for k, r in enumerate(rs[first:first + keep], first):
                        if place:
                            r = dict(r, run=place[k])
                        okey = r.get("rid") or r.get("cid") or r.get("eid") or r.get("name") or (S._slug(r["heading"]) if "heading" in r else k)
                        out["kids"].append(make(each, S._inst(ctx, node["ast"], {**ctx, "count": total, "index": k + 1, **r}), f"{key}/{okey}", em["layout"], chain, cb))
                else:
                    named, ids = acc.select(sel_text)
                    if b.get("by"):
                        if named is not None:
                            at = {i: k for k, (i, _st) in enumerate(named)}
                            named = sorted(named, key=lambda x: (tuple(moo.order_value(moo.props_of(w, x[0]).get(k)) for k in b["by"]), at[x[0]]))
                        else:
                            ids = moo.order_by(w, list(ids), b["by"])
                    # a clamped repeat's fence compares the shown prefix, so it says the order it was shown in
                    shown = [["select", sel_text, [list(x) for x in pick(named)] if named is not None else list(pick(list(ids))), keep]
                             + ([list(b["by"])] if b.get("by") else [])] if b["clamp"] else []
                    order = [x[0] for x in named] if named is not None else list(ids)
                    place = dict(zip(order, S.run_places([moo.props_of(w, i).get(b["run"]) for i in order]))) if b.get("run") else {}
                    if named is not None:
                        total = len(named)
                        base = max(0, total - keep) if b.get("last") else 0      # $index: the place in the whole repeat
                        for k, (i, st) in enumerate(pick(named), base + 1):
                            mcb = cb + shown + ([[i, S._rev_of(w, i), []]] if st != "live" else _member_reads(w, i, sel_text))
                            out["kids"].append(make(each, S._inst(ctx, node["ast"], dict(acc.thing(i, st), count=total, index=k, **({"run": place[i]} if place else {}))), f"{key}/{i}", em["layout"], chain, mcb))
                        out["states"] = [f"{i} {st}" for i, st in named if st != "live"]
                    else:
                        total = len(ids)
                        base = max(0, total - keep) if b.get("last") else 0
                        for k, i in enumerate(pick(list(ids)), base + 1):
                            out["kids"].append(make(each, S._inst(ctx, node["ast"], dict(acc.thing(i), count=total, index=k, **({"run": place[i]} if place else {}))), f"{key}/{i}", em["layout"], chain, cb + shown + _member_reads(w, i, sel_text)))
                got = [k["item"] or k["key"] for k in out["kids"]]
                out["members"] = {"of": sel_text, "n": total, "ids": got, "at": len(w.events)}
                if total > keep:
                    out["cut"] = total - keep
                    cut = {"part": "cut", "key": f"{key}/cut", "role": "cut", "layout": None, "item": None, "box": None,
                           "text": (f"{total - keep} earlier not shown (clamp last {keep}); " if b.get("last") else f"{total - keep} more not shown (clamp {keep}); ")
                           + f"find {sel_text} lists all {total}", "clamp": None, "acts": [], "kids": []}
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
            if inner.lower() in stack:
                raise S.LensRefusal(f"line {node['line']}: lens {inner} contains itself ({' -> '.join(stack + (inner.lower(),))})")
            sub = compile_lens(desk, acc.define(inner), stack + (inner.lower(),), count, closure if closure is not None else [], acc, cb)
            sub["key"] = f"{key}/lens:{inner}"
            S._rekey(sub, sub["key"])
            out["kids"].append(sub)
            out["lens"] = inner
        # --- fixed kids
        for kid in node["kids"]:
            out["kids"].append(make(kid, dict(ctx, n=out.get("n", ctx.get("n", "")), count=out.get("size", ctx.get("count", ""))), f"{key}/{kid['part']}", em["layout"], chain, cb))
        return out

    sc = make(irs[root], {}, root, cb=cb)
    sc["R"] = list(acc.R)
    return sc


def compile_lens(desk, s, stack, count, closure, acc=None, cb=()):
    """One lens to a scene through the staged pipeline, recording the definition used; fallback as scene._compile does."""
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
        try:
            import persons
            import verbs
            b = verbs.binding_of(desk.world, ("s", s["id"]), s["text"])     # a1590: its names mean whom they meant when saved
            with persons.reading(desk, (b or {}).get("persons")):
                sc = evaluate(desk, s["text"], stack, count, props=s.get("props") or {}, closure=closure, acc=acc, cb=cb)
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
            sc = evaluate(desk, g["text"], stack, count, props=s.get("props") or {}, closure=closure, acc=acc)
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
    vs = S.judge_views(desk, {a: v for a, v in (getattr(desk, "_views", None) or {}).items() if v.get("lens") == s["title"].lower()}, closure, rev)
    vs = sorted(((a, v) for a, v in vs.items() if v.get("paint")), key=lambda av: str(av[1].get("time")))
    if not vs:
        return " · painted sizes: none reported (no viewer has it open with a painter that reports them)"
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


def scene_for(desk, name, part=None, words=None):
    """-> (scene, text), as scene.scene_for, through the staged pipeline. With `part`, the text is only the parts that
    path names (find_parts) and what is inside them; scene["printed"] lists those nodes. With `words` (a4179:
    {"start": n, "whole": bool}) the text is the scene's words alone (scene.to_words), and scene["said"] lists the
    nodes it showed whole, each for itself."""
    s = S.find_lens(desk, name)
    closure = []
    acc = Accessor(desk)
    sc = compile_lens(desk, s, (s["title"].lower(),), [0], closure, acc)
    S.emit(sc)
    at = len(desk.world.events)
    fallen = [c for c in closure if c["status"] == "fallback"]
    sc["def"] = dict(lens=s["title"], id=s["id"], rev=s["rev"], status="fallback" if fallen else "current", closure=closure,
                     frame=".".join(f"{c['id']}r{c['rev']}" for c in closure), **S._identity())
    name = (s.get("props") or {}).get("style")
    home = S.room_of_thing(desk.world, s)          # 9 Oct (step 7): the style nearest the lens's own room
    if name:                                  # F7: which style paints this lens, and which revision of it
        st = S.style_source(desk, name, home) or {}
        sc["def"].update(style_name=name, style_rev=st.get("rev", ""))
    S.mark_pulse(sc, S.pulsing_roles(desk, name, home))   # a1140: the painter installs this one style for the whole scene
    sc["views"] = S.judge_views(desk, {a: v for a, v in (getattr(desk, "_views", None) or {}).items() if v.get("lens") == s["title"].lower()},
                                closure, sc["def"].get("style_rev"))
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
