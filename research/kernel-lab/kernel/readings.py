"""Readings for the obvious questions, and press (Alex approved P5 and P7 on 27 Oct 2026; research/kernel-lab/terminal).

who            the people, agents and modules here
recent         the latest acts you may see, newest first: recent by=me, by=Alex, kind=window, since=r1200, limit=30
kinds          every kind of thing you can see, with counts
on <module>    the other half of off
press <button> run a button's does= line exactly as a click would
history alone  your own latest acts (history <thing> is that thing's trail)

Recent shows who did which word to which visible thing and when: never facts, never a sealed act's author, never a
thing the reader cannot see now (an act that touched only hidden things is left out).
"""
from .kernel import Refused


def who(k, actor, st, entry, tx, group, saw=None):
    rows, people, agents, modules = [], [], [], []
    for t in k.things("person"):
        if k.shown(actor.person, t) is None:
            continue
        role = "steward" if k.is_steward(t) else ("leader" if any(
            k.state.get(g, f"member:{t}") == "leader" for g in k.things("group")) else "")
        people.append(k.name(t) + (f" ({role})" if role else ""))
        rows.append({"id": t, "kind": "person", "name": k.name(t), "role": role})
    for t in k.things("agent"):
        if k.shown(actor.person, t) is None:
            continue
        agents.append(k.name(t))
        rows.append({"id": t, "kind": "agent", "name": k.name(t), "for": k.state.get(t, "for")})
    for t in k.things("module"):
        if k.shown(actor.person, t) is None:
            continue
        on = bool(k.state.get(t, "on"))
        modules.append(k.state.get(t, "name") + ("" if on else " (off)"))
        rows.append({"id": t, "kind": "module", "name": k.state.get(t, "name"), "on": on})
    me = k.name(actor.id) if actor.id in k.state.things else k.name(actor.person)
    text = [f"you: {me}", "people: " + (", ".join(people) or "none you can see"),
            "agents: " + (", ".join(agents) or "none"), "modules: " + (", ".join(modules) or "none")]
    return {"text": "\n".join(text), "rows": rows}


def _touched(rec):
    out = []
    for p in rec.get("parts", []):
        for t in [p.get("target")] + [f[0] for f in p.get("facts", [])]:
            if t and t not in out:
                out.append(t)
    return out


def _own(k, actor, rec):
    return rec.get("by") in (actor.id, actor.person) or rec.get("for") == actor.person


def acts(k, actor, by=None, kind=None, since=0, limit=15):
    """The latest acts the reader may see, newest first, as rows."""
    undone = k.undone()
    rows = []
    for rec in reversed(k.log.records):
        if rec["seq"] <= since or len(rows) >= limit:
            break
        if not rec.get("entry") and not rec.get("undoes"):
            continue                                     # kernel bookkeeping (installs, offers), not anyone's act
        sealed = rec.get("by") == "sealed"
        if by == "me" and (sealed or not _own(k, actor, rec)):
            continue
        name = "someone" if sealed else k.name(rec.get("for") or rec.get("by"))
        if by not in (None, "me") and (sealed or by.casefold() not in (name.casefold(), str(rec.get("by")).casefold())):
            continue
        things = [t for t in _touched(rec) if k.state.get(t, "kind") not in ("word", "grant", "taskboard-event")
                  and k.shown(actor.person, t) is not None]
        if not things and _touched(rec):
            continue                                     # it touched only what this reader cannot see
        if kind and not any(k.state.get(t, "kind") == kind for t in things):
            continue
        word = k.state.get(rec.get("entry"), "word") or (rec.get("parts") or [{}])[0].get("word") or "undo"
        label = lambda t: k.state.get(t, "title") or k.state.get(t, "name") or k.state.get(t, "label") or t
        via = f" (by {k.name(rec['by'])})" if not sealed and rec.get("for") and rec.get("by") != rec.get("for") else ""
        rule = " (a rule)" if rec.get("rule") else ""
        rows.append({"record": f"r{rec['seq']}", "at": rec.get("at", ""), "by": name + via + rule, "word": word,
                     "things": things, "undone": rec["seq"] in undone,
                     "text": f"r{rec['seq']} {str(rec.get('at', ''))[11:16]} {name}{via}{rule} {word} "
                             + ", ".join(f"{label(t)}" for t in things[:3])
                             + (" (undone)" if rec["seq"] in undone else "")})
    return rows


def recent(k, actor, st, entry, tx, group, saw=None):
    kv = st.kv
    since = kv.get("since", "0").lstrip("r")
    if not since.isdecimal():
        raise Refused("since= takes a record, like since=r1200")
    limit = min(int(kv.get("limit", "15")) if str(kv.get("limit", "15")).isdecimal() else 15, 100)
    by = kv.get("by") or (st.words.split()[0] if st.words else None)
    rows = acts(k, actor, by=by, kind=kv.get("kind"), since=int(since), limit=limit)
    head = f"{len(rows)} latest act{'' if len(rows) == 1 else 's'} you can see" + (f" by {by}" if by else "")
    return {"text": head + ("\n" + "\n".join("  " + r["text"] for r in rows) if rows else
                            "; recent by=<name> kind=<kind> since=r<n> narrows it"), "rows": rows}


def kinds(k, actor, st, entry, tx, group, saw=None):
    if st.words.strip() or st.target:
        from .kinds import kinds_reading
        if st.target:
            st.words = (st.target + " " + st.words).strip()
        return kinds_reading(k, actor, st)
    count = {}
    for t, a in list(k.state.things.items()):
        if t == "world" or a.get("forgotten") or k.shown(actor.person, t) is None:
            continue
        count[a.get("kind")] = count.get(a.get("kind"), 0) + 1
    order = sorted(count.items(), key=lambda kc: (-kc[1], str(kc[0])))
    return {"text": f"{len(order)} kinds you can see (rows <kind> lists one, help <kind> says what acts on it):\n  "
                    + " · ".join(f"{kd} {n}" for kd, n in order),
            "rows": [{"kind": kd, "count": n} for kd, n in order]}


def on(k, actor, st, entry, tx, group, saw=None):
    from .words import _module_of
    m = _module_of(k, st)
    if k.state.get(m, "on"):
        return {"text": f"{k.name(m)} is already on"}
    tx.set(m, "on", True)
    # the grants its last off took back come back with it
    seq = k.state.last_seq(m, "on")
    rec = k.log.records[seq - 1] if seq else {}
    back = [f[0] for p in rec.get("parts", []) for f in p.get("facts", []) if f[1] == "revoked"]
    for g in back:
        tx.set(g, "revoked")
    return {"text": f"ok on {k.state.get(m, 'name')} [r?] · {len(back)} grant{'' if len(back) == 1 else 's'} back; "
                    f"it starts in a moment; off stops it again"}


def press(k, actor, st, entry, tx, group, saw=None):
    t = st.target
    a = k.shown(actor.person, t) or {}
    line = str(a.get("does") or "").strip()
    if not line:
        raise Refused(f"{k.name(t)} has nothing to press: only a thing with does=\"<line>\" (a button) runs a line")
    out = k.run(actor, line)
    if not out.get("ok"):
        raise Refused(f"pressing {a.get('label') or t} ran {line}: {out.get('text', '').removeprefix('refused: ')}")
    return {"text": f"pressed {a.get('label') or t}: {out.get('text', '')}", "rows": out.get("rows", [])}


def own_history(k, actor):
    rows = acts(k, actor, by="me", limit=15)
    return {"text": ("your latest acts (history <thing> shows one thing's trail):\n" if rows else
                     "you have no acts here yet") + "\n".join("  " + r["text"] for r in rows), "rows": rows}
