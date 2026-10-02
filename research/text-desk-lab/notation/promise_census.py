"""promise_census: what a1587's migration would make of a world's owe=, awaiting= and due_for= props, and what reads
them. Read-only: loads a copy of the pickle and never saves.

    python promise_census.py <world>
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


def main():
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
