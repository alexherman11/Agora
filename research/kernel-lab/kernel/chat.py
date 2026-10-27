"""Chats: a kind of thing people talk in, and the `say` word (MOVING-IN D4, Alex 27 Oct: "A kind, chat is a great idea").

    make kind=chat name="Shop talk"                       an open chat: the place sees it, anyone in it may say
    make kind=chat name=Conversation with="Alex, JEFF"    a closed chat: only those people see it and say in it
    say <chat> <words> [reply_to=<said>] [about=<thing>]  a line in it, a `said` thing; undo takes it back
    chat <chat> [limit=<n>] [since=<said>]                its latest lines, oldest first

A said line is addressed (its `to`): to each @name in it outside quotes, or, with none, in a closed chat to everyone else
in it (a conversation between two people speaks to the other). The line's happening carries `to`, so whatever wakes
people (the house) knows whom it calls without reading the line again. A said line is seen by whoever sees its chat
(`visibility_of`), never wider.
"""
import re

from .kernel import Refused

AT = re.compile(r"(?<![\w@])@([A-Za-z][\w.-]*)")
QUOTED = re.compile(r"`[^`]*`|\"[^\"]*\"|“[^”]*”")


def people_named(k, actor, names):
    """'Alex, JEFF' -> [person ids], refusing a name no person here has."""
    out = []
    for name in [n.strip().lstrip("@") for n in re.split(r"[,\s]+", str(names or "")) if n.strip()]:
        hits = [p for p in k.things("person") if str(k.state.get(p, "name", "")).casefold() == name.casefold()
                or p == name]
        if not hits:
            raise Refused(f"no person here is called {name}; rows person lists them")
        out.append(hits[0])
    return list(dict.fromkeys(out))


def closed_sees(k, actor, kv):
    """make kind=chat with=<names>: who sees it, as a sees rule (the maker is always in it). Narrows, never widens."""
    people = people_named(k, actor, kv.pop("with"))
    if actor.person not in people:
        people.insert(0, actor.person)
    kv["with"] = " ".join(people)
    return "|".join(f"person:{p}" for p in people)


def addressed(k, chat, text, speaker):
    """-> (person ids the line calls, @names that call no one here)."""
    bare = QUOTED.sub(" ", text)
    to, unknown = [], []
    for name in AT.findall(bare):
        hit = [p for p in k.things("person") if str(k.state.get(p, "name", "")).casefold() == name.casefold()]
        if hit:
            if hit[0] != speaker:                    # naming yourself calls no one
                to.append(hit[0])
        else:
            unknown.append("@" + name)
    if not to and not unknown and k.state.get(chat, "with"):
        to = [p for p in str(k.state.get(chat, "with")).split() if p != speaker]
    return list(dict.fromkeys(t for t in to if t != speaker)), unknown


def say(k, actor, st, entry, tx, group, saw=None):
    chat = st.target
    if not chat or k.state.get(chat, "kind") != "chat":
        raise Refused("say <chat> <words>: say which chat (rows chat lists them), then your words")
    text = str(st.kv.get("text") or st.words).strip()
    if not text:
        raise Refused(f"say {k.name(chat)} <words>: there were no words")
    people = str(k.state.get(chat, "with") or "").split()
    if people and actor.person not in people:
        raise Refused(f"{k.name(chat)} is between {', '.join(k.name(p) for p in people)}; you are not in it")
    reply = st.kv.get("reply_to")
    if reply and (k.state.get(reply, "kind") != "said" or k.shown(actor.person, reply) is None):
        raise Refused(f"reply_to={reply}: no said line you can see is called that")
    to, unknown = addressed(k, chat, st.text or text, actor.person)     # st.text keeps its quotes
    outside = [p for p in to if people and p not in people]
    t = tx.mint()
    tx.set(t, "kind", "said")
    tx.set(t, "text", text)
    tx.set(t, "chat", chat)
    tx.set(t, "visibility_of", chat)
    if to:
        tx.set(t, "to", " ".join(to))
    if reply:
        tx.set(t, "reply_to", reply)
    a = st.kv.get("about")
    if a:
        if k.shown(actor.person, a) is None:
            raise k.no_such(a)
        tx.set(t, "about", a)
    tx.set(t, "made_by", actor.id)
    if actor.id != actor.person:
        tx.set(t, "for", actor.person)
    tx.set(t, f"in:{group}", len(k.log.records) + 1)
    notes = []
    if to:
        notes.append("to " + ", ".join(k.name(p) for p in to))
    if outside:
        notes.append(", ".join(k.name(p) for p in outside) + " cannot see this chat, so the line does not reach them")
    if unknown:
        notes.append("no one here is called " + ", ".join(unknown))
    return {"text": f"ok say {t} [r?] in {k.name(chat)}" + (" · " + "; ".join(notes) if notes else ""),
            "rows": [{"id": t, "kind": "said", "chat": chat, "to": to}]}


def said_row(k, t, a):
    by = a.get("made_by")
    return {"id": t, "kind": "said", "chat": a.get("chat"), "by": k.name(a.get("for") or by) if by else "",
            "via": k.name(by) if a.get("for") else "", "text": a.get("text", ""), "at": a.get("made", ""),
            "to": [k.name(p) for p in str(a.get("to") or "").split()], "reply_to": a.get("reply_to", ""),
            "about": a.get("about", ""), "rev": k.state.rev.get(t, 0)}


def lines_of(k, reader, chat):
    out = []
    for t in k.things("said"):
        if k.state.get(t, "chat") != chat:
            continue
        a = k.shown(reader, t)
        if a is not None:
            out.append((k.state.history[(t, "kind")][0][0], t, a))
    return [(t, a) for _, t, a in sorted(out)]


def chat(k, actor, st, entry, tx, group, saw=None):
    c = st.target
    if not c or k.state.get(c, "kind") != "chat":
        raise Refused("chat <chat> [limit=<n>]: say which chat; rows chat lists them")
    limit = st.kv.get("limit", "20")
    limit = min(int(limit), 200) if str(limit).isdigit() else 20
    got = lines_of(k, actor.person, c)
    since = st.kv.get("since")
    if since:
        seen = [i for i, (t, _) in enumerate(got) if t == since]
        got = got[seen[0] + 1:] if seen else got
    got = got[-limit:]
    rows = [said_row(k, t, a) for t, a in got]
    for t, a in got:
        k.mark(actor, t, a)
    people = str(k.state.get(c, "with") or "").split()
    head = (f"{k.name(c)} ({c}), a chat" + (f" between {', '.join(k.name(p) for p in people)}" if people else ", open")
            + f": {len(rows)} latest line{'' if len(rows) == 1 else 's'}")
    body = [f"  {r['id']} {str(r['at'])[11:16]} {r['by']}: {r['text']}" for r in rows]
    return {"text": head + ("\n" + "\n".join(body) if body else "; say <chat> <words> starts it"), "rows": rows}
