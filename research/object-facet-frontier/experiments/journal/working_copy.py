"""Is "run the verb on a working copy, commit its per-(thing, aspect) diff as rows" a mechanism or a snapshot in disguise?

Sable, 25 Sep 2026. Jeff's framing: it is a mechanism if (1) the rows alone rebuild what the working copy became,
(2) each batch carries what the verb read, so fence and merge can judge it without the verb, and (3) the cascade's
rows are attributed to the rule that wrote them. Measured too: the cost against a pickle, and whether text as hunks
makes the diff per hunk.

    python working_copy.py            prints the findings; nothing outside a temp directory is written

Runs the desk's own verbs (moo.REGISTRY) and rules (DeskKnife._run_rules) on in-memory desks. Reads no session.
"""

import copy
import difflib
import json
import pickle
import statistics
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
NOTATION = Path(__file__).resolve().parents[3] / "text-desk-lab" / "notation"
sys.path.insert(0, str(NOTATION))

import explore  # noqa: E402
import moo      # noqa: E402

ABSENT = "<absent>"

# ---- the projection: the desk as rows keyed (referent, aspect) ------------------------------------------------------
NODE_GROUPS = {"x": "geom:pos", "y": "geom:pos", "w": "geom:size", "h": "geom:size", "parent": "place", "z": "place", "order": "place"}
UNKNOWN = set()
SUBJECT_KNOWN = {"id", "rev", "kind", "title", "text", "tags", "due", "comments", "props"}
NODE_KNOWN = {"id", "rev", "type", "subject", "parent", "x", "y", "w", "h", "z", "folded", "layout", "title", "props", "order", "share"}
DERIVED_IN_FLOW = ("x", "y", "w", "h", "z")      # sable-9 switch on: a flow child's box is the reflow cache, not a row


def aspect_of_field(kind, key):
    """The aspect a field belongs to (also used to name reads)."""
    if key == "tags":
        return "tag:*"
    if key == "props":
        return "prop:*"
    if key == "comments":
        return "comment:*"
    if kind == "node" and key in NODE_GROUPS:
        return NODE_GROUPS[key]
    return key


def project(d):
    TRACK[0] = False
    try:
        w, rows = d.world, {}
        for sid, s in w.subjects.items():
            for k, v in s.items():
                if k in ("id", "rev"):
                    continue
                if k not in SUBJECT_KNOWN:
                    UNKNOWN.add(f"subject.{k}")
                if k == "tags":
                    for t in v:
                        rows[(sid, f"tag:{t}")] = True
                elif k == "props":
                    for pk, pv in v.items():
                        rows[(sid, f"prop:{pk}")] = pv
                elif k == "comments":
                    for c in v:
                        rows[(sid, f"comment:{c['id']}")] = json.loads(json.dumps(c))
                else:
                    rows[(sid, k)] = v
        choices = getattr(w, "choices", False)
        for nid, n in w.nodes.items():
            grouped = {}
            in_flow = choices and (w.nodes.get(n.get("parent") or "") or {}).get("layout") in ("column", "row")
            for k, v in n.items():
                if k in ("id", "rev") or (in_flow and k in DERIVED_IN_FLOW):
                    continue
                if k not in NODE_KNOWN:
                    UNKNOWN.add(f"node.{k}")
                if k == "props":
                    for pk, pv in v.items():
                        rows[(nid, f"prop:{pk}")] = pv
                elif k in NODE_GROUPS:
                    grouped.setdefault(NODE_GROUPS[k], {})[k] = v
                else:
                    rows[(nid, k)] = v
            for a, v in grouped.items():
                rows[(nid, a)] = v
        for link in w.links:
            for k, v in link.items():
                if k != "id":
                    rows[(link["id"], k)] = v
        for r in d.rules or []:
            rows[(r["id"], "code")] = {k: v for k, v in r.items() if k not in ("id", "done", "cursor", "fired")}
            rows[(r["id"], "memory")] = {k: (sorted(r[k]) if k == "done" else r[k]) for k in ("done", "cursor", "fired") if k in r}
        for name, body in (d.scripts or {}).items():
            rows[(f"script:{name}", "code")] = body
        rows[("clock", "today")] = d.today
        rows[("clock", "follow")] = bool(d.follow)
        return json.loads(json.dumps({f"{g}\x1f{a}": v for (g, a), v in rows.items()}, default=list))
    finally:
        TRACK[0] = True


def diff(before, after):
    out = {}
    for k in before.keys() | after.keys():
        b, a = before.get(k, ABSENT), after.get(k, ABSENT)
        if b != a:
            out[k] = a
    return out


def apply_rows(d, delta):
    """Assign rows into a desk: no verb, rule or script runs. Entities appear when their first aspect does and go
    when their last aspect goes."""
    w = d.world
    by = {}
    for key, v in delta.items():
        g, a = key.split("\x1f")
        by.setdefault(g, {})[a] = v
    for g, aspects in by.items():
        if g.startswith("s") and g[1:].isdigit():
            s = w.subjects.setdefault(g, {"id": g, "rev": 0, "tags": [], "comments": [], "props": {}})
            for a, v in aspects.items():
                if a.startswith("tag:"):
                    t = a[4:]
                    if v == ABSENT:
                        s["tags"] = [x for x in s["tags"] if x != t]
                    elif t not in s["tags"]:
                        s["tags"].append(t)
                elif a.startswith("prop:"):
                    if v == ABSENT:
                        s["props"].pop(a[5:], None)
                    else:
                        s["props"][a[5:]] = v
                elif a.startswith("comment:"):
                    cs = [c for c in s["comments"] if c["id"] != a[8:]]
                    if v != ABSENT:
                        cs.append(v)
                    s["comments"] = sorted(cs, key=lambda c: int(c["id"][1:]))
                elif v == ABSENT:
                    s.pop(a, None)
                else:
                    s[a] = v
            if set(s) <= {"id", "rev", "tags", "comments", "props"} and not (s["tags"] or s["comments"] or s["props"]):
                del w.subjects[g]
        elif g[:1] in "af" and g[1:].isdigit():
            n = w.nodes.setdefault(g, {"id": g, "rev": 0})
            for a, v in aspects.items():
                if a.startswith("prop:"):
                    if v == ABSENT:
                        n.setdefault("props", {}).pop(a[5:], None)
                    else:
                        n.setdefault("props", {})[a[5:]] = v
                elif a in ("geom:pos", "geom:size", "place"):
                    for k in [k for k, grp in NODE_GROUPS.items() if grp == a]:
                        if v == ABSENT or k not in v:
                            n.pop(k, None)
                        else:
                            n[k] = v[k]
                elif v == ABSENT:
                    n.pop(a, None)
                else:
                    n[a] = v
            if not (set(n) - {"id", "rev"} - (set(DERIVED_IN_FLOW) if getattr(w, "choices", False) else set())):
                del w.nodes[g]
        elif g.startswith("l") and g[1:].isdigit():
            link = next((x for x in w.links if x["id"] == g), None)
            if link is None:
                link = {"id": g}
                w.links.append(link)
            for a, v in aspects.items():
                if v == ABSENT:
                    link.pop(a, None)
                else:
                    link[a] = v
            if set(link) == {"id"}:
                w.links.remove(link)
        elif g.startswith("r") and g[1:].isdigit():
            r = next((x for x in d.rules if x["id"] == g), None)
            if r is None:
                r = {"id": g}
                d.rules.append(r)
            if aspects.get("code", None) == ABSENT:
                d.rules.remove(r)
                continue
            if "code" in aspects:
                r.update(aspects["code"])
            if "memory" in aspects:
                m = aspects["memory"]
                for k in ("done", "cursor", "fired"):
                    r.pop(k, None)
                    if k in m:
                        r[k] = set(m[k]) if k == "done" else m[k]
        elif g.startswith("script:"):
            if aspects["code"] == ABSENT:
                d.scripts.pop(g[7:], None)
            else:
                d.scripts[g[7:]] = aspects["code"]
        elif g == "clock":
            if "today" in aspects:
                d.today = None if aspects["today"] == ABSENT else aspects["today"]
                w.today = d.today
            if "follow" in aspects:
                d.follow = aspects["follow"]
        else:
            UNKNOWN.add(f"referent {g}")
    if getattr(w, "choices", False):
        # sable-9: assigning rows is followed by deriving layout; flow children's boxes are recomputed, never assigned
        for fid, n in list(w.nodes.items()):
            if n["type"] == "surface" and (n.get("parent") is None or (w.nodes.get(n["parent"]) or {}).get("layout") == "free"):
                w.reflow(fid)


def canonical(d):
    w = d.world
    strip = lambda x: {k: v for k, v in x.items() if k != "rev"}   # noqa: E731
    return json.loads(json.dumps({
        "subjects": {k: strip(v) for k, v in sorted(w.subjects.items())},
        "nodes": {k: strip(v) for k, v in sorted(w.nodes.items())},
        "links": sorted((dict(x) for x in w.links), key=lambda x: x["id"]),
        "rules": sorted(({**r, "done": sorted(r.get("done") or [])} for r in d.rules or []), key=lambda r: r["id"]),
        "scripts": dict(d.scripts or {}), "clock": [d.today, bool(d.follow)]}, default=list))


# ---- read tracking: the working copy's entities log which fields were read, and in which phase -------------------------
TRACK, PHASE, LOG = [True], ["act"], []


class TD(dict):
    def __init__(self, *a, owner=None, **k):
        super().__init__(*a, **k)
        self._owner = owner

    def _log(self, key):
        if TRACK[0]:
            LOG.append((PHASE[0], self._owner, key))

    def __getitem__(self, k):
        self._log(k)
        return super().__getitem__(k)

    def get(self, k, default=None):
        self._log(k)
        return super().get(k, default)

    def __contains__(self, k):
        self._log(k)
        return super().__contains__(k)

    def __iter__(self):
        self._log("*")
        return super().__iter__()

    def items(self):
        self._log("*")
        return super().items()

    def values(self):
        self._log("*")
        return super().values()

    def keys(self):
        self._log("*")
        return super().keys()

    def __deepcopy__(self, memo):            # an undo snapshot: bookkeeping, not a semantic read
        was, TRACK[0] = TRACK[0], False
        try:
            return copy.deepcopy(dict(super().items()), memo)
        finally:
            TRACK[0] = was

    def __reduce_ex__(self, proto):
        return (dict, (dict(super().items()),))


class TL(list):
    def __init__(self, *a, owner=None):
        super().__init__(*a)
        self._owner = owner

    def __iter__(self):
        if TRACK[0]:
            LOG.append((PHASE[0], self._owner, "*"))
        return super().__iter__()

    def __reduce_ex__(self, proto):
        return (list, (list(super().__iter__()),))


def instrument(d):
    w = d.world
    w.subjects = TD({k: TD(v, owner=k) for k, v in dict.items(w.subjects)}, owner="subjects")
    w.nodes = TD({k: TD(v, owner=k) for k, v in dict.items(w.nodes)}, owner="nodes")
    w.links = TL([TD(x, owner=x["id"]) for x in list.__iter__(w.links)], owner="links")


def reads_named(entries, d):
    """(phase, owner, field) -> readable aspects, grouped by phase."""
    out = {}
    for phase, owner, key in entries:
        if owner in ("subjects", "nodes", "links"):
            name = (f"all {owner}", "members") if key == "*" else (key, "exists")
        else:
            kind = "subject" if owner.startswith("s") else "node" if owner[:1] in "af" else "link"
            name = (owner, "*" if key == "*" else aspect_of_field(kind, key))
        out.setdefault(phase, set()).add(name)
    return out


# ---- a working desk with ordinary things ---------------------------------------------------------------------------------
def home(n_extra=0, words=40):
    d = explore.fresh()
    run = lambda line: d.dispatch("desk", {"line": line})   # noqa: E731
    run("look")
    run("clock 2026-09-25")
    run("do create f01 kind=surface title=Today layout=column")
    run("do create f01 kind=surface title=Later layout=column")
    lorem = " ".join(["word"] * words)
    run(f'do create f01 kind=note title=Essay text="## Intro\\nold intro\\n## Notes\\n- first"')
    run('do create f01 kind=task title="Call dentist"')
    run('do create f01 kind=task title="Book flights"')
    run('do create f01 kind=note title=Groceries text="milk\\neggs"')
    for i in range(n_extra):
        run(f'do create {"f01" if i % 3 else "Later"} kind=note title="Note {i}" text="{lorem}\\n{lorem}"')
    run("rule when prop:status=done do tag add=done")
    run("rule when tag:urgent do move into=Today")
    run("script morning = look Today")
    return d


def ids(d):
    w = d.world
    by_title = {}
    for nid, n in w.nodes.items():
        by_title.setdefault(w.title(n), nid)
    return by_title


def run_act(d, verb, target, kv, actor="alex"):
    """One act on a working copy: the verb, then the rules; rows, reads and attribution come back."""
    base = project(d)
    wc = copy.deepcopy(d)
    instrument(wc)
    wc.world.me = actor
    LOG.clear()
    PHASE[0] = "act"
    err = None
    try:
        moo.REGISTRY[verb].run(wc.world, target, dict(kv))
    except Exception as e:                      # a refusal: nothing to commit
        err = f"{type(e).__name__}: {e}"
    act_rows = diff(base, project(wc))
    by_rule = {}
    orig = wc._fire

    def fire(r, i):
        before = project(wc)
        PHASE[0] = r["id"]
        try:
            return orig(r, i)
        finally:
            by_rule.setdefault(r["id"], {}).update(diff(before, project(wc)))
            PHASE[0] = "rule selection"
    wc._fire = fire
    PHASE[0] = "rule selection"
    if not err:
        wc._run_rules(cause=wc.world.events[-1]["id"] if wc.world.events else None)
    TRACK[0] = False
    rows = diff(base, project(wc))
    reads = reads_named(LOG, wc)
    TRACK[0] = True
    return wc, rows, act_rows, by_rule, reads, err


ACTS = [
    ("create", "f01", {"kind": "note", "title": "New", "text": "a\nb"}),
    ("retitle", "Groceries", {"title": "Shopping"}),
    ("append", "Groceries", {"line": "bread"}),
    ("rewrite", "Essay", {"text": "## Intro\nA new intro\n## Notes\n- first"}),
    ("prop", "Call dentist", {"status": "done"}),
    ("tag", "Book flights", {"add": "urgent"}),
    ("due", "Book flights", {"on": "2026-10-01"}),
    ("move", "Groceries", {"into": "Later"}),
    ("resize", "Essay", {"to": "300x160"}),
    ("raise", "Essay", {}),
    ("fold", "Groceries", {}),
    ("comment", "Essay", {"line": "Which intro?"}),
    ("link", "Essay", {"to": "Groceries", "as": "refers"}),
    ("remove", "Groceries", {}),
    ("sort", "Later", {"by": "title"}),
    ("done", "Book flights", {}),
    ("tidy", "f01", {}),
]


def hidden(base, wc):
    """Attributes of the desk and world that changed but are not in the projection."""
    skip_w = {"subjects", "nodes", "links"}
    skip_d = {"world", "rules", "scripts", "today", "follow"}
    out = []
    for k, v in vars(wc.world).items():
        if k not in skip_w and pickle.dumps(v) != pickle.dumps(vars(base.world).get(k)):
            out.append(f"world.{k}")
    for k, v in vars(wc).items():
        if k not in skip_d and not callable(v) and pickle.dumps(v) != pickle.dumps(vars(base).get(k)):
            out.append(k)
    return out


def check_acts():
    d = home(n_extra=6)
    t = ids(d)
    results = []
    for verb, target, kv in ACTS:
        tgt = t.get(target, target)
        kv = {k: (t.get(v, v) if k in ("into", "to") and v in t else v) for k, v in kv.items()}
        wc, rows, act_rows, by_rule, reads, err = run_act(d, verb, tgt, kv)
        # (1) the rows alone, assigned onto the base, rebuild what the working copy became
        rebuilt = copy.deepcopy(d)
        apply_rows(rebuilt, rows)
        same = canonical(rebuilt) == canonical(wc)
        where = []
        if not same:
            a, b = canonical(rebuilt), canonical(wc)
            for part in a:
                if a[part] != b[part]:
                    where.append(part)
        # (1b) a world built from nothing but the full projection
        fresh = explore.fresh()
        fresh.world.nodes.clear()
        fresh.rules, fresh.scripts = [], {}
        apply_rows(fresh, {k: v for k, v in project(wc).items()})
        from_nothing = canonical(fresh) == canonical(wc)
        results.append({"act": f"{verb} {target}", "err": err, "rows": len(rows), "act_rows": len(act_rows),
                        "rule_rows": {r: len(x) for r, x in by_rule.items() if x},
                        "rebuilds": same, "differs_in": where, "from_nothing": from_nothing,
                        "reads": {p: sorted(f"{a}.{b}" for a, b in s) for p, s in reads.items()},
                        "aspects": sorted({k.split(chr(31))[1] for k in rows}),
                        "hidden": hidden(d, wc)})
    return results


def costs():
    out = []
    for n in (200, 1000, 3000):
        d = home(n_extra=n, words=40)
        t = ids(d)
        tgt = t["Groceries"]
        timing = {"copy": [], "pickle": [], "project2+diff": [], "act+rules": []}
        for _ in range(5):
            t0 = time.perf_counter()
            wc = copy.deepcopy(d)
            t1 = time.perf_counter()
            pickle.dumps(d)
            t2 = time.perf_counter()
            b = project(d)
            moo.REGISTRY["append"].run(wc.world, tgt, {"line": "x"})
            wc._run_rules(cause=None)
            t3 = time.perf_counter()
            diff(b, project(wc))
            t4 = time.perf_counter()
            timing["copy"].append(t1 - t0)
            timing["pickle"].append(t2 - t1)
            timing["act+rules"].append(t3 - t2)
            timing["project2+diff"].append(t4 - t3)
        out.append({"subjects": len(d.world.subjects), "pickle_kb": len(pickle.dumps(d)) // 1024,
                    **{k: round(statistics.median(v) * 1000, 1) for k, v in timing.items()}})
    return out


def hunk_rows():
    """Whole-value text against line hunks: how big is the diff for three ordinary edits of a 60-line document?"""
    doc = [f"line {i}: " + " ".join(["word"] * 12) for i in range(60)]
    edits = {"append one line": doc + ["a new line"],
             "rewrite one section (3 lines)": doc[:20] + ["new a", "new b", "new c"] + doc[23:],
             "rewrite everything": [f"other {i}" for i in range(60)]}
    out = []
    for name, new in edits.items():
        whole = len("\n".join(new).encode())
        rows, size = 0, 0
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, doc, new, autojunk=False).get_opcodes():
            if tag != "equal":
                changed = max(i2 - i1, j2 - j1)
                rows += changed
                size += sum(len(x.encode()) for x in new[j1:j2])
        out.append({"edit": name, "whole_rows": 1, "whole_bytes": whole, "hunk_rows": rows, "hunk_bytes": size})
    return out


def main():
    res = check_acts()
    print("ACTS: rows, rebuild from rows, reads, attribution")
    for r in res:
        print(f"- {r['act']}: {'REFUSED ' + r['err'] if r['err'] else ''}{r['rows']} row(s) [{', '.join(r['aspects'])}]; "
              f"act {r['act_rows']}, rules {r['rule_rows'] or '-'}; rows rebuild the copy: {r['rebuilds']}"
              + (f" (differs in {r['differs_in']})" if r["differs_in"] else "") + f"; from nothing: {r['from_nothing']}")
        for phase, rs in r["reads"].items():
            print(f"    reads[{phase}]: {', '.join(rs[:14])}{' ...+' + str(len(rs) - 14) if len(rs) > 14 else ''}")
        if r["hidden"]:
            print(f"    changed outside the projection: {', '.join(r['hidden'])}")
    print("unknown fields met:", sorted(UNKNOWN) or "none")
    print()
    print("COST (ms, median of 5): working copy vs today's pickle")
    for c in costs():
        print("-", c)
    print()
    print("TEXT: whole value vs line hunks, 60-line document")
    for h in hunk_rows():
        print("-", h)
    Path(__file__).with_name("working_copy.json").write_text(json.dumps({"acts": res}, indent=1, default=list), encoding="utf-8")


if __name__ == "__main__":
    main()
