"""persons_census (a1590): every stored name that names a person in a world, and who bore it when it was written.
Read-only: loads a copy of the pickle and never saves.

    python persons_census.py <world>
"""
import pickle
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import persons  # noqa: E402

TERM = re.compile(r"(?:prop:([\w-]+)=|(held-by|asked-of|owed-to|asked-by|awaits|offered-to|unanswered):)([\w-]+)")
SET = re.compile(r"\b(owner|asked_by|worker|person|actor)=([\w,-]+)")


def setter(w, ids, key):
    """The latest live event that set prop `key` on any of `ids`: its number, or 0."""
    for e in reversed(w.events):
        if e.get("undone") or e["verb"] == "undo" or e["target"] not in ids:
            if e["verb"] == "create" and isinstance(e.get("undo"), dict) and e["undo"].get("delete") in ids \
                    and key in (e.get("args") or {}) and not e.get("undone"):
                return persons._num(e["id"])
            continue
        if key in (e.get("args") or {}):
            return persons._num(e["id"])
    return 0


def main(world):
    w = pickle.loads((HERE / "sessions" / f"{world}.pickle").read_bytes()).world
    ix = persons.index(w)
    names = set(ix.spans)
    keys, earlier, rows = Counter(), Counter(), []
    for sid, s in w.subjects.items():
        if s.get("kind") == "person":
            continue
        ids = {sid} | set(w.appearances_of(sid))
        for k, v in (s.get("props") or {}).items():
            if persons.norm(v) in names and k != "name":
                keys[k] += 1
                n = setter(w, ids, k)
                if not n:
                    keys["no event: " + k] += 1
                then, now = persons.at(w, v, n), persons.today(w, v)
                if then != now:
                    earlier[k] += 1
                    rows.append(f"  {sid} {w.appearances_of(sid)[:1]} {k}={v} set e{n}: then {then} ({persons.label(w, then)}), today {now}  {s['title'][:50]!r}")
    for nid, nd in w.nodes.items():
        if nd["type"] != "surface":
            continue
        for k, v in (nd.get("props") or {}).items():
            vs = [x for x in str(v).split(",") if persons.norm(x) in names]
            if vs and k not in ("query",):
                keys["surface " + k] += 1
                n = setter(w, {nid}, k)
                for x in vs:
                    if persons.at(w, x, n) != persons.today(w, x):
                        earlier["surface " + k] += 1
                        rows.append(f"  {nid} surface {k}={v} set e{n}: {x} then {persons.at(w, x, n)} today {persons.today(w, x)}")
    print("person-naming props:", dict(keys))
    print("of them, bound to an earlier person:", dict(earlier))
    print("\n".join(rows))
    print("== stored selections and lines that name a person")
    for nid, nd in w.nodes.items():
        q = nd.get("query") or (nd.get("props") or {}).get("query")
        if q:
            for m in TERM.finditer(str(q)):
                if persons.norm(m.group(3)) in names:
                    ev = next((e for e in reversed(w.events) if not e.get("undone") and "query" in (e.get("args") or {})
                               and (e["target"] == nid or (e.get("undo") or {}).get("delete") == nid)), None)
                    k = persons._num(ev["id"]) if ev else None
                    then = persons.at(w, m.group(3), k) if k is not None else None
                    print(f"  view {nid} {nd['title'][:40]!r} query={q!r} written {ev['id'] if ev else '(no event)'} "
                          f"by {ev['by'] if ev else '?'}: {m.group(3)} then {then} today {persons.today(w, m.group(3))}")
                    break
        wake = (nd.get("props") or {}).get("wake")
        if wake and (TERM.search(str(wake)) or SET.search(str(wake))):
            print(f"  wake {nid}: {wake!r}")
    for sid, s in w.subjects.items():
        tags = s.get("tags") or []
        kind = next((k for k in ("verb", "rule", "lens") if k in tags), None)
        if not kind or not w.appearances_of(sid):
            continue
        hits = [m.group(0) for m in TERM.finditer(s["text"]) if persons.norm(m.group(3)) in names]
        hits += [m.group(0) for m in SET.finditer(s["text"]) if any(persons.norm(x) in names for x in m.group(2).split(","))]
        if hits:
            print(f"  {kind} {w.appearances_of(sid)[0]} {s['title'][:40]!r}: {hits}")


def dry_run(world):
    """--migrate: run a1590's migration on the world in memory (never saved): its note, and every person-naming view
    before and after."""
    import verbs
    desk = pickle.loads((HERE / "sessions" / f"{world}.pickle").read_bytes())
    w = desk.world
    w.me = "house"
    views = [nid for (k, nid), (kind, q) in verbs.stored_texts(w).items() if k == "q" and persons.stored_words(q)]
    before = {v: desk.view_matches(v) for v in views}
    ev = persons.migrate(desk)
    if ev is None:
        print("nothing to migrate")
        return
    print(f"{ev['id']} {ev['verb']} by {ev['by']}: {ev['args']}")
    for part in ev["note"].split("; "):
        print("  " + part)
    for v in views:
        after = desk.view_matches(v)
        print(f"  view {v} {w.nodes[v]['title']!r}: {len(before[v])} -> {len(after)}"
              + ("" if before[v] == after else f"  (left: {sorted(set(before[v]) - set(after))})"))


if __name__ == "__main__":
    if sys.argv[1] == "--migrate":
        dry_run(sys.argv[2])
    else:
        main(sys.argv[1])
