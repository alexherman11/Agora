"""EDITING THE KERNEL (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
The kernel changes only to give every world a general capability: a word, a check, a kind of fact any app, module or
person can use. It never names its tenants: no app, module, person, kind or field name appears in this code except the
kernel's own (word, rule, kind, grant, person, ...). If your change needs `if kind == "..."`, a person's name or one app's
field, stop: the missing piece is a general word (a kind's policy, a rule step, a reading). Build that, or put it on the
Board. Names already here are debt (research/source-edits/SOURCE-AUDIT-KERNEL.md lists them); take them out when you can.

Chats: a kind of thing people talk in, and the `say` word (MOVING-IN D4, Alex 27 Oct: "A kind, chat is a great idea").

    make kind=chat name="Shop talk"                       an open chat: the place sees it, anyone in it may say
    make kind=chat name=Conversation with="Alex, JEFF"    a closed chat: only those people see it and say in it
    say <chat> <words> [reply_to=<said>] [about=<thing>] [acts=<receipts>]   a line in it, a `said` thing
    set <said> acts=<receipts>                            only its speaker, and only its acts (what it did after it)
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
        if len(hits) > 1 and name not in hits:
            # two people share the name: never pick one silently for a closed chat (security review M4, 28 Oct)
            raise Refused(f"{len(hits)} people are called {name} ({', '.join(hits[:5])}); say with= by id")
        out.append(hits[0] if name not in hits else name)
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
    if k.state.get(chat, "read_only"):
        raise Refused(f"{k.name(chat)} is read-only")
    text = str(st.kv.get("text") or st.words).strip()
    if not text:
        raise Refused(f"say {k.name(chat)} <words>: there were no words")
    people = str(k.state.get(chat, "with") or "").split()
    if people and actor.person not in people:
        raise Refused(f"{k.name(chat)} is between {', '.join(k.name(p) for p in people)}; you are not in it")
    reply = st.kv.get("reply_to")
    if reply and (k.state.get(reply, "kind") != "said" or k.shown(actor.person, reply) is None):
        raise Refused(f"reply_to={reply}: no said line you can see is called that")
    if reply and k.state.get(reply, "chat") != chat:
        # a reply quoting a closed chat's line into an open one would carry that line's id there (security review L4)
        raise Refused(f"reply_to={reply} is a line in another chat; a reply goes in the chat of the line it answers")
    # the words as said, with their own quotes: text=<value> is the whole of them (the lens sends that); else the
    # line, whose parse drops quotes around words
    to, unknown = addressed(k, chat, text if "text" in st.kv else (st.text or text), actor.person)
    # a line calls only people who can see its chat: `to` is what wakers (the house) read, and they read with their
    # own wider sight, so a name outside the chat must never reach the record (card dk1245, 28 Oct: the receipt said
    # "does not reach them" while `to` still held them)
    outside = [p for p in to if k.shown(p, chat) is None]
    to = [p for p in to if p not in outside]
    if outside and not to and people:
        to = [p for p in people if p != actor.person]     # it still speaks to the chat's own people, as an unnamed line does
    t = tx.mint()
    tx.set(t, "kind", "said")
    tx.set(t, "text", text)
    tx.set(t, "chat", chat)
    tx.set(t, "visibility_of", chat)
    if to:
        tx.set(t, "to", " ".join(to))
    if reply:
        tx.set(t, "reply_to", reply)
    if st.kv.get("acts"):
        tx.set(t, "acts", str(st.kv["acts"])[:2000])     # what the speaker did around this line: small receipts
    a = st.kv.get("about")
    if a:
        # a line may be about what an earlier step of the same act made (a verb's `as=` handle): not yet in the world,
        # but made by this speaker in this act (Ask, 3 Nov 2026: the request and Alex's line to JEFF are one act)
        if a not in tx.made and k.shown(actor.person, a) is None:
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


def receive(k, actor, st, entry, tx, group, saw=None):
    """Import from a chat's source module; outside speakers and mentions are data."""
    c = st.target
    if (actor.kind != "module" or not actor.module
            or k.state.get(c, "kind") != "chat"
            or k.state.get(c, "source") != actor.module
            or not k.state.get(c, "read_only")):
        raise Refused("chat.receive is only for this read-only chat's source module")
    k.reaches(actor, "chat.receive", "said", c)
    text, speaker, key = (str(st.kv.get(x) or "") for x in ("text", "speaker", "external_id"))
    if not text or not speaker or not key or len(text) > 4000 or len(speaker) > 100 or len(key) > 200:
        raise Refused("chat.receive needs text, speaker and external_id within chat limits")
    if any(k.state.get(t, "chat") == c and k.state.get(t, "external_id") == key
           for t in k.things("said")):
        return {"text": "already received", "rows": []}
    t = tx.mint()
    for a, v in (("kind", "said"), ("chat", c), ("visibility_of", c),
                 ("text", text), ("speaker", speaker), ("external_id", key),
                 ("from", k.state.get(actor.module, "name")),
                 ("made_by", actor.module), (f"in:{group}", len(k.log.records) + 1)):
        tx.set(t, a, v)
    return {"text": f"received a line in {k.name(c)}", "rows": [{"id": t, "kind": "said", "chat": c}]}


def said_row(k, t, a):
    by = a.get("made_by")
    return {"id": t, "kind": "said", "chat": a.get("chat"), "by": a.get("speaker") or (k.name(a.get("for") or by) if by else ""),
            "from": a.get("from", ""),
            "acts": a.get("acts", ""),
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
    limit = min(int(limit), 200) if str(limit).isdecimal() else 20
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
    body = [f"  {r['id']} {str(r['at'])[11:16]} {r['by']}: {r['text']}" + (f"\n      ~ {r['acts']}" if r["acts"] else "")
            for r in rows]
    return {"text": head + ("\n" + "\n".join(body) if body else "; say <chat> <words> starts it"), "rows": rows}


def said_set(k, actor, t, kv):
    """set on a said line: its speaker may change its acts (receipts of what they did after saying it), nothing else."""
    if set(kv) - {"acts"}:
        raise Refused("a said line keeps its words; set changes only its acts= (undo takes the line back)")
    if k.state.get(t, "made_by") != actor.id:
        raise Refused("only whoever said the line sets its acts")
