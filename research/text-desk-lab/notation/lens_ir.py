"""The staged lens compiler, stages 4 and 5: lower to the six kinds, evaluate through the read accessor.

    parse (scene.parse) -> resolve (scene.resolve) -> lower -> evaluate(IR, accessor, host) -> scene -> print / emit

Built to Sable's statement (sable-8): evaluation is a function of the IR, the accessor's answers and the host facts,
and nothing else; the accessor is the only door to the world and records every read in R; within one part the order
is bind, lets, guard, emit, acts, instances, placed lens, fixed kids; ABSENT is a value; count is the true size.
The scene it produces has the same shape as scene.build's, so scene.to_text and scene.emit print and paint it, and
Juniper's golden prints judge the switch. Jeff owns this file (desk-shell/OWNERS.md)."""
import re

import scene as S

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
        s = S.find_lens(self.desk, name)
        self.R.append(("define", name, s["id"], s["rev"]))
        return s

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
    while these hold). -> (subject aspects, appearance aspects). `kind` and `age` are not aspects any verb declares;
    a kind change would go unfenced here, and age moves only with the clock."""
    subj, app = set(), set()
    for t in [x for x in re.split(r"[,\s]+", q.strip()) if x]:
        t = t[1:] if t.startswith("-") else t
        if t.startswith("tag:"):
            subj.add("tags")
        elif t.startswith("prop:"):
            subj.add("prop:" + t[5:].split("=")[0])
        elif t.startswith("title:"):
            subj.add("title")
        elif t.startswith("?"):
            subj |= {"title", "text", "tags"}
        elif t.startswith(("due<", "due>")):
            subj.add("due")
        elif t.startswith(("in:", "also:")) or t == "hidden":
            app.add("place")
        elif t.startswith(("comments:", "links:", "parts:", "part-of:")):
            subj.add(t.split(":")[0])
    return subj, app


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
            bind = {"kind": "many", "of": node["of"], "over": node["over"], "each": node["each"], "as": node["as"], "clamp": node["clamp"]}
        else:
            bind = None
        guard = None
        if node["only"]:
            m = S._VALUE_TEST.fullmatch(node["only"].strip())
            guard = {"kind": "value", "ref": m.group(1), "op": m.group(2), "rhs": m.group(3).strip('"'), "src": node["only"]} if m \
                else {"kind": "selection", "q": node["only"], "src": node["only"]}
        ir = {"part": node["name"], "line": node["line"], "src": node["src"], "ast": node,
              "bind": bind,
              "lets": [{"name": d, "interp": i, "inputs": ins} for d, i, ins in node["derive"]],
              "guard": guard,
              "emit": {"layout": node["layout"], "role": node["role"], "text": node["text"], "clamp": node["clamp"],
                       "at": node["at"], "spread": node.get("spread"), "props": node["props"]},
              "acts": [dict(a) for a in node["on"]],
              "place": node["lens"], "carry": node["carry"],
              "kids": [one(k) for k in node["kids"]],
              "deps": {"emit": _deps(node["text"]), "guard": _deps(node["only"]),
                       "acts": [_deps(a["line"]) for a in node["on"]],
                       "lets": [_deps(*[x for x in ins if x.startswith("$")]) for _, _, ins in node["derive"]]}}
        return ir
    return {name: one(node) for name, node in parts.items()}, root


# ---------------------------------------------------------------------------------------------------------------------
# Stage 5, evaluate. A transcription of scene.build's make(), with the world reached only through the accessor, the
# fixed order within a part, host facts in Gamma, count as the true size, and one rule for guards.
# ---------------------------------------------------------------------------------------------------------------------
def evaluate(desk, src, stack=(), count=None, props=None, closure=None, acc=None, cb=()):
    root, parts = S.parse(src)
    S.resolve(root, parts)
    irs, root = lower(root, parts)
    acc = acc or Accessor(desk)
    w = desk.world
    props = props or {}
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
        if b and b["kind"] == "one":
            out["the"] = (S._fill(b["q"], ctx), the_state)
        if b and b.get("as"):
            out["as"] = b["as"]
        if ctx.get("_captured") and b and b["kind"] == "one":
            out["captured"] = [{"field": k, "value": v, "now": live, "same": (str(live) == str(v))} for k, v, live in ctx["_captured"]]
        if the_state not in ("live",) and not the_state.startswith("->"):
            return out
        # --- lets
        for let in node["lets"]:
            dctx = dict(ctx.get("_props") or {})
            dctx.update(ctx)
            vals = [S._fill(x, dctx, track) if x.startswith("$") else x for x in let["inputs"]]
            res, err = S.INTERPS[let["interp"]][1](vals)
            out.setdefault("derived", []).append({"name": let["name"], "interp": let["interp"], "inputs": vals,
                                                  "result": (f"{len(res)} rows" if isinstance(res, list) else res), "error": err})
            if isinstance(res, list):
                ctx["_" + let["name"]] = res
            else:
                ctx[let["name"]] = res or ""
        # --- guard: one rule, judged against the part's own frame after its bind and lets (sable-8 section 2)
        g = node["guard"]
        if g and g["kind"] == "value":
            vctx = dict(ctx.get("_props") or {})
            vctx.update(ctx)
            left = S._fill(g["ref"], vctx, track)
            right = S._fill(g["rhs"], vctx, track) if g["rhs"].startswith("$") else g["rhs"]
            gone = [x for x, v in ((g["ref"], left), (g["rhs"], right)) if x.startswith("$") and (v == x or v == "")]
            if gone or not S._compare(left, g["op"], right):
                out.update(text=None, acts=[], kids=[], absent=g["src"],
                           why=(f"no {gone[0].lstrip('$')}" if gone else f"{g['ref']} is {left}, not {g['op']} {right}"))
                return out
            out["test"] = f"{g['ref']} is {left} {g['op']} {right}"
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
        if em["at"] == "item" and ctx.get("item") in w.nodes:
            n = w.nodes[ctx["item"]]
            out["box"] = [n["x"], n["y"], n["w"], n["h"]]
            out["facts"] = [f for f in w.relations(ctx["item"]) if f != "clear"]
        if em["text"] is not None:
            pv = dict(ctx.get("_props") or {})
            missing = [p for p in em["props"] if p not in pv and p not in ctx]
            fill_ctx = {p: "" for p in missing}
            fill_ctx.update(pv)
            fill_ctx.update({k: v for k, v in ctx.items() if k != "n"} if (b and b["kind"] == "many") else ctx)
            out["text"] = S._fill(em["text"], fill_ctx, track)
            if em["props"]:
                out["read"] = {p: pv.get(p) for p in em["props"] if p in pv}
            if missing:
                out["missing"] = missing
        if ctx.get("_state") and ctx["_state"] != "live":
            out["state"] = ctx["_state"]
        # --- acts
        safe = {k: (S._cmd_value(v) if isinstance(v, str) else v) for k, v in ctx.items()}
        out["id"] = ctx.get("id")
        safe["_frames"] = {k: {kk: (S._cmd_value(vv) if isinstance(vv, str) else vv) for kk, vv in f.items()} for k, f in frames.items()}
        acts = [] if (node["acts"] and ctx.get("_state") in ("gone", "unplaced")) else [
            {"on": a["on"], "line": S._fill(a["line"], safe, track), **({"part": a["part"]} if a.get("part") else {})} for a in node["acts"]]
        if node["carry"]:
            if not ctx.get("item"):
                raise S.LensRefusal(f"line {node['line']}: `carry` needs a world thing behind this part, and here there is none (a derived row or the root)")
            acts.append({"on": "carry"})
        out["acts"] = acts
        if track["bad"]:
            raise S.LensRefusal(f"line {node['line']}: ${sorted(track['bad'])[0]}.field: no part above this one is named `as {sorted(track['bad'])[0]}`")
        if track["reads"]:
            out["freads"] = {k: v for k, v in track["reads"].items()}
            out["frames"] = {f: frames[f].get("id") for f in track["frames"] if f in frames}
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
                fid = frames.get(fr, {}).get("id")
                a = S._aspect_of_field(fld)
                if fid and a:
                    fields.setdefault(fid, set()).add(a)
            for i in [sj] + [frames[f].get("id") for f in track["frames"] if f in frames]:
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
            if b["of"]:
                sel_text = S._fill(b["of"], ctx)
                out["of"] = sel_text
                rs = acc.rows(sel_text) if sel_text.partition(":")[0] in S.SOURCES else None
                total = len(rs) if rs is not None else None
                if rs is not None:
                    for k, r in enumerate(rs[:keep]):
                        okey = r.get("cid") or r.get("eid") or r.get("name") or (S._slug(r["heading"]) if "heading" in r else k)
                        out["kids"].append(make(each, S._inst(ctx, node["ast"], {**ctx, "count": total, **r}), f"{key}/{okey}", em["layout"], chain, cb))
                else:
                    named, ids = acc.select(sel_text)
                    shown = [["select", sel_text, [list(x) for x in named[:keep]] if named is not None else list(ids[:keep])]] if b["clamp"] else []
                    if named is not None:
                        total = len(named)
                        for i, st in named[:keep]:
                            mcb = cb + shown + ([[i, S._rev_of(w, i), []]] if st != "live" else _member_reads(w, i, sel_text))
                            out["kids"].append(make(each, S._inst(ctx, node["ast"], dict(acc.thing(i, st), count=total)), f"{key}/{i}", em["layout"], chain, mcb))
                        out["states"] = [f"{i} {st}" for i, st in named if st != "live"]
                    else:
                        total = len(ids)
                        for i in ids[:keep]:
                            out["kids"].append(make(each, S._inst(ctx, node["ast"], dict(acc.thing(i), count=total)), f"{key}/{i}", em["layout"], chain, cb + shown + _member_reads(w, i, sel_text)))
                got = [k["item"] or k["key"] for k in out["kids"]]
                out["members"] = {"of": sel_text, "n": total, "ids": got, "at": len(w.events)}
                if total > keep:
                    out["cut"] = total - keep
                    out["kids"].append({"part": "cut", "key": f"{key}/cut", "role": "cut", "layout": None, "item": None, "box": None,
                                        "text": f"{total - keep} more not shown (clamp {keep}); find {sel_text} lists all {total}",
                                        "clamp": None, "acts": [], "kids": []})
            else:
                rows_over = ctx.get("_" + b["over"], [])
                for k, v in enumerate(rows_over):
                    if isinstance(v, dict):
                        ictx = S._inst(ctx, node["ast"], dict(ctx, it=str(v.get("date", v.get("n", ""))), count=len(rows_over)))
                        ictx["_frames"] = dict(ictx["_frames"], it=v)
                        out["kids"].append(make(each, ictx, f"{key}/{S._slug(str(v.get('n', k)))}", em["layout"], chain, cb))
                    else:
                        out["kids"].append(make(each, S._inst(ctx, node["ast"], dict(ctx, it=v, count=len(rows_over))), f"{key}/{S._slug(str(v))}", em["layout"], chain, cb))
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
            if out["text"] is not None:
                out["text"] = out["text"].replace("$n", str(out["n"]))
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
            out["kids"].append(make(kid, dict(ctx, n=out.get("n", ctx.get("n", "")), count=out.get("n", ctx.get("count", ""))), f"{key}/{kid['part']}", em["layout"], chain, cb))
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
    try:
        sc = evaluate(desk, s["text"], stack, count, props=s.get("props") or {}, closure=closure, acc=acc, cb=cb)
        stamp(sc)
        good[s["id"]] = {"text": s["text"], "rev": s["rev"]}
        return sc
    except S.LensRefusal as e:
        g = good.get(s["id"])
        g = {"text": g, "rev": None} if isinstance(g, str) else g
        if not g:
            raise
        del closure[mark:]
        entry.update(status="fallback", shown_rev=g["rev"], refusal=str(e))
        sc = evaluate(desk, g["text"], stack, count, props=s.get("props") or {}, closure=closure, acc=acc)
        stamp(sc)
        sc["broken"] = f"lens {s['title']}: {e}"
        return sc


def scene_for(desk, name):
    """-> (scene, text), as scene.scene_for, through the staged pipeline."""
    s = S.find_lens(desk, name)
    closure = []
    acc = Accessor(desk)
    sc = compile_lens(desk, s, (s["title"].lower(),), [0], closure, acc)
    S.emit(sc)
    at = len(desk.world.events)
    fallen = [c for c in closure if c["status"] == "fallback"]
    sc["def"] = dict(lens=s["title"], id=s["id"], rev=s["rev"], status="fallback" if fallen else "current", closure=closure,
                     frame=".".join(f"{c['id']}r{c['rev']}" for c in closure), **S._identity())
    sc["views"] = {a: v for a, v in (getattr(desk, "_views", None) or {}).items() if v.get("lens") == s["title"].lower()}
    text = S.to_text(sc, s["title"], desk.world.me, at)
    if fallen:
        head = "".join(f"! lens {c['lens']} no longer compiles: {c['refusal']}\n" for c in fallen)
        text = head + "! showing the last version that did; gestures are off until it compiles. Fix it with rewrite, or undo.\n" + text
    return sc, text
