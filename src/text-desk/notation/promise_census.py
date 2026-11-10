"""promise_census: what a1587's migration would make of a world's owe=, awaiting= and due_for= props, and what reads
them. Read-only: loads a copy of the pickle and never saves.

    python promise_census.py <world>
    python promise_census.py --commissions <world>    each commission's promise, and who a2798's rule says made it
"""
import pickle
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
KEYS = ("owe", "awaiting", "due_for")
WORD = re.compile(r"\b(owe|awaiting|due_for)\b")


def writer(w, sid, key):
    """The latest live event that set this subject's prop `key`: (event, its value)."""
    nodes = {nid for nid, n in w.nodes.items() if n.get("subject") == sid} | {sid}
    for e in reversed(w.events):
        if e.get("undone") or e["verb"] == "undo" or e["target"] not in nodes:
            continue
        a = e.get("args") or {}
        if key in a:
            return e, a[key]
    return None, None


def dry_run(path):
    """--migrate: run a1587's migration on the world in memory (never saved) and print what it made and changed."""
    import promises
    desk = pickle.loads(Path(path).read_bytes())
    w = desk.world
    w.me = "house"
    n0 = len(w.events)
    promises.migrate(desk)
    for e in w.events[n0:]:
        print(f"{e['id']} {e['verb']} by {e['by']}: {e.get('args')}")
        for part in (e.get("note") or "").split("; "):
            print("  " + part)
    print("== every promise, as a third person reads it")
    for sid in promises.all_sids(w):
        st = promises.state(w, sid)
        print(f"{st['aid']}\t{st['state']}\t{promises.phrase(w, st, {'pid': None, 'name': ''})}\t{st['what'][:60]!r}\tabout={st['about']}")
    for who in ("sable", "pike", "juniper", "alex"):
        w.me = who
        print(f"== as {who}: held-by {len(promises.matching(w, 'held-by:' + who))}, asked-of "
              f"{len(promises.matching(w, 'asked-of:' + who))}, owed-to {len(promises.matching(w, 'owed-to:' + who))}")


def commissions(world):
    """--commissions: every promise about a commission card, and what a2798's rule makes of it (made by asked_by's own
    act of setting commission=asked, the earliest; or by no one when someone else set it for them). Never saves."""
    import promises
    w = pickle.loads((HERE / "sessions" / f"{world}.pickle").read_bytes()).world
    for sid in promises.all_sids(w):
        st = promises.state(w, sid)
        c = promises.about_sid(w, st)
        p = (w.subjects.get(c) or {}).get("props") or {}
        if not c or st["form"] != "promise" or w.subjects[c].get("kind") != "task" or "commission" not in p:
            continue
        ab = p.get("asked_by")
        made = promises.events(w).get(st["made"]) if st["made"] else None
        own = promises.asker_act(w, c, ab) if ab else None
        rule = ("no asked_by: the setter's, as before" if not ab else
                f"{ab}'s own ({own['id']})" if own else f"no one's: {ab} never set commission=asked here")
        print(f"{st['aid']}\tabout {st['about']}\tasked_by={ab or '-'}\tnow: {promises.phrase(w, st, {'pid': None, 'name': ''})}"
              f"\tmade by {made['by'] if made else '?'} ({st['made']})\trule: {rule}")


def main():
    if "--migrate" in sys.argv:
        return dry_run(sys.argv[sys.argv.index("--migrate") + 1])
    if "--commissions" in sys.argv:
        return commissions(sys.argv[sys.argv.index("--commissions") + 1])
    w = pickle.loads((HERE / "sessions" / f"{sys.argv[1]}.pickle").read_bytes()).world
    trash = {nid for nid, n in w.nodes.items() if (n.get("props") or {}).get("trash") == "yes"}

    def place(sid):
        for nid, n in w.nodes.items():
            if n.get("subject") == sid:
                p, seen = n.get("parent"), set()
                while p and p not in seen:
                    if p in trash:
                        return nid, "trash"
                    seen.add(p)
                    p = (w.nodes.get(p) or {}).get("parent")
                return nid, ""
        return "-", "nowhere"
    for key in KEYS:
        print(f"== {key}=")
        for sid, s in w.subjects.items():
            v = (s.get("props") or {}).get(key)
            if v is None:
                continue
            e, _ = writer(w, sid, key)
            nid, where = place(sid)
            p = s.get("props") or {}
            by = (e["by"] + (f" (rule, tripped by {e['tripped_by']})" if e.get("tripped_by") else "")) if e else "?"
            print(f"{nid}\t{e['id'] if e else '-'}\tby={by}\towner={p.get('owner', '')}\tasked_by={p.get('asked_by', '')}"
                  f"\tstatus={p.get('status', '')}\t{where}\t{s['kind']}\t{s['title'][:50]!r}\t{key}={v[:90]!r}")
    print("== readers (words owe / awaiting / due_for in a query, a note's text or a surface prop)")
    for nid, n in w.nodes.items():
        if n.get("type") == "surface":
            q = " ".join(str(x) for x in (n.get("query") or "", n.get("cols") or "", *(n.get("props") or {}).values()))
            if WORD.search(q):
                print(f"{nid}\tsurface\t{n.get('title', '')[:40]!r}\t{q[:160]!r}")
    for sid, s in w.subjects.items():
        hits = [l.strip() for l in (s.get("text") or "").splitlines() if WORD.search(l)]
        if hits and (set(s.get("tags") or []) & {"rule", "verb", "lens", "style"} or s["kind"] in ("note",)):
            nid, where = place(sid)
            tags = ",".join(s.get("tags") or [])
            if tags and set(s.get("tags") or []) & {"rule", "verb", "lens", "style"}:
                for h in hits[:4]:
                    print(f"{nid}\t{tags}\t{where}\t{s['title'][:40]!r}\t{h[:160]!r}")
    print("== the commission behind each due note: who set commission=asked, owner, asked_by")
    for sid, s in w.subjects.items():
        d = (s.get("props") or {}).get("due_for")
        if not d:
            continue
        c = w.subjects.get((w.nodes.get(d) or {}).get("subject")) or {}
        e, _ = writer(w, c.get("id"), "commission") if c else (None, None)
        asked = next((x for x in w.events if x["target"] == d and (x.get("args") or {}).get("commission") == "asked"
                      and not x.get("undone")), None)
        cp = c.get("props") or {}
        print(f"{place(sid)[0]}\tfor {d}\tfirst asked by {asked['by'] if asked else '?'} ({asked['id'] if asked else '-'})"
              f"\towner={cp.get('owner', '')}\tasked_by={cp.get('asked_by', '')}\tlived={cp.get('lived', '')[:30]!r}"
              f"\tnote status={(s.get('props') or {}).get('status', '')}")
    print("== owe= and awaiting= values written before and since overwritten or removed (history only)")
    for e in w.events:
        a = e.get("args") or {}
        for k in ("owe", "awaiting"):
            if k in a and not e.get("undone") and e["verb"] != "undo":
                sid = (w.nodes.get(e["target"]) or {}).get("subject", e["target"])
                now = ((w.subjects.get(sid) or {}).get("props") or {}).get(k)
                if now != a[k]:
                    print(f"{e['target']}\t{e['id']}\tby={e['by']}\t{k}={str(a[k])[:70]!r}\tnow={str(now)[:30]!r}")
        if a.get("remove") in KEYS:
            print(f"{e['target']}\t{e['id']}\tby={e['by']}\tremove={a['remove']}")
    print("== world verbs and things whose word or prop collides with phase 1's words")
    words = {"promise", "ask", "accept", "decline", "withdraw", "report", "confirm", "release", "carry", "promises"}
    for sid, s in w.subjects.items():
        tags = set(s.get("tags") or [])
        ws = {x.strip().lower() for x in s["title"].split("|")}
        if "verb" in tags and ws & words:
            print(f"{place(sid)[0]}\tverb {s['title']!r} on={(s.get('props') or {}).get('on', '')}")
        for k in (s.get("props") or {}):
            if k in words | {"released", "kept", "carried"}:
                print(f"{place(sid)[0]}\tprop {k}={s['props'][k][:60]!r}\t{s['title'][:40]!r}")
        if s["kind"] not in ("note", "task", "chat", "image", "doc", "trial", "person"):
            print(f"{place(sid)[0]}\tkind {s['kind']}")


main()
