"""EDITING THE KERNEL (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
The kernel changes only to give every world a general capability: a word, a check, a kind of fact any app, module or
person can use. It never names its tenants: no app, module, person, kind or field name appears in this code except the
kernel's own (word, rule, kind, grant, person, ...). If your change needs `if kind == "..."`, a person's name or one app's
field, stop: the missing piece is a general word (a kind's policy, a rule step, a reading). Build that, or put it on the
Board. Names already here are debt (docs/design/source-edits/SOURCE-AUDIT-KERNEL.md lists them); take them out when you can.

Chats: a kind of thing people talk in, and the `say` word (MOVING-IN D4, Alex 27 Oct: "A kind, chat is a great idea").

    make kind=chat name="Shop talk"                       an open chat: the place sees it, anyone in it may say
    make kind=chat name=Conversation with="Alex, JEFF"    a closed chat: only those people see it and say in it
    say <chat> <words> [reply_to=<said>] [about=<thing>] [acts=<receipts>]   a line in it, a `said` thing
    set <said> acts=<receipts>                            only its speaker, and only its acts (what it did after it)
    set <said> text=<words>                               only its speaker: an edit, kept as `edited` (its time)
    forget <said>                                         its speaker or the chat's leaders remove it; undo brings it back
    react <said> emoji=<e>                                the caller's reaction, toggled; not sealed (names are shown)
    pin <said> [off=yes]                                  the chat's leaders pin a line (chat <chat> pinned=yes)
    chat <chat> [limit=<n>] [since=<said>] [before=<said>] [pinned=yes]   its latest lines, oldest first

A chat row (said_row) carries what a chat view needs in one reading: by_id, name, guest, badge, text, at (ISO UTC) and
ts (epoch seconds), reply_to with a short reply excerpt, edited (epoch seconds or None), removed, pinned, reactions
[{emoji, count, mine, names}], mentions (person ids @named in the text now) and files attached to the line. A removed
(forgotten) line is shown, emptied, only while a line the reader sees replies to it. The contract the board's chat view
is written against: src/community/board/CHAT-CONTRACT.md.

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
        hits = [p for p in k.things("person") if not k.is_visitor(p)
                and (str(k.state.get(p, "name", "")).casefold() == name.casefold() or p == name)]
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
    for name in (n.rstrip(".-") for n in AT.findall(bare)):     # "thanks @JEFF." calls JEFF, not "JEFF."
        hit = [p for p in k.things("person") if str(k.state.get(p, "name", "")).casefold() == name.casefold()
               and not k.is_visitor(p)]
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


def _epoch(iso):
    """'2026-11-05T02:14:09Z' -> 1762308849 (int seconds), or None."""
    if not iso:
        return None
    from datetime import datetime, timezone
    try:
        return int(datetime.strptime(str(iso)[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp())
    except ValueError:
        return None


def speaker_of(k, a):
    """The person a said line is by (its agent's person for an agent's line), or '' for a line from outside."""
    if a.get("speaker"):
        return ""
    by = a.get("for") or a.get("made_by") or ""
    if k.state.get(by, "kind") == "agent":
        by = k.state.get(by, "for") or by
    return by


def mentioned(k, text):
    """Person ids @named in the words (outside quotes), in order, once each."""
    out = []
    for name in (n.rstrip(".-") for n in AT.findall(QUOTED.sub(" ", str(text or "")))):
        hit = [p for p in k.things("person") if str(k.state.get(p, "name", "")).casefold() == name.casefold()
               and not k.is_visitor(p)]
        if hit:
            out.append(hit[0])
    return list(dict.fromkeys(out))


def badge(k, person, chat):
    if not person or k.state.get(person, "kind") != "person":
        return ""
    if k.is_steward(person):
        return "steward"
    return "leader" if k.is_leader(person, (k.groups_of(chat) or [k.place])[0]) else ""


def reactions(k, reader, t, a):
    """react:<person>:<emoji> facts -> [{emoji, count, mine, names}], in the order each emoji first came."""
    seen = {}
    for key, v in a.items():
        if not key.startswith("react:"):
            continue
        who, _, emoji = key[6:].partition(":")
        if not emoji:
            continue
        seen.setdefault(emoji, []).append((k.state.last_seq(t, key), who))      # in the order they came
    out = []
    for emoji, who in sorted(seen.items(), key=lambda kv: min(w[0] for w in kv[1])):
        people = [p for _, p in sorted(who)]
        out.append({"emoji": emoji, "count": len(people), "mine": reader in people,
                    "names": [k.name(p) for p in people]})
    return out


def said_row(k, t, a, reader=None, files=None):
    by = a.get("made_by")
    person = speaker_of(k, a)
    text = a.get("text", "")
    name = a.get("speaker") or (k.name(a.get("for") or by) if by else "")
    reply_to = a.get("reply_to") or None
    reply = None
    if reply_to:
        ra = k.shown(reader, reply_to) if reader is not None else None
        if ra is not None:
            reply = {"id": reply_to, "name": ra.get("speaker") or k.name(speaker_of(k, ra) or ra.get("made_by")),
                     "text": str(ra.get("text", ""))[:120], "removed": False}
        elif k.state.get(reply_to, "forgotten") and k.state.get(reply_to, "chat") == a.get("chat"):
            reply = {"id": reply_to, "name": "", "text": "", "removed": True}
    return {"id": t, "kind": "said", "chat": a.get("chat"), "by": name, "by_id": person, "name": name,
            "guest": k.is_guest(person), "badge": badge(k, person, a.get("chat")),
            "mine": bool(reader) and person == reader,
            "from": a.get("from", ""),
            "acts": a.get("acts", ""),
            "via": k.name(by) if a.get("for") else "", "text": text, "at": a.get("made", ""),
            "ts": _epoch(a.get("made")),
            "to": [k.name(p) for p in str(a.get("to") or "").split()], "reply_to": reply_to, "reply": reply,
            "edited": _epoch(a.get("edited")), "removed": False, "pinned": bool(a.get("pinned")),
            "reactions": reactions(k, reader, t, a), "mentions": mentioned(k, text),
            "files": list(files or []),
            "about": a.get("about", ""), "rev": k.state.rev.get(t, 0)}


def removed_row(k, t, chat):
    """A removed line still answered by a reply: its place in the chat, without its words or speaker."""
    return {"id": t, "kind": "said", "chat": chat, "by": "", "by_id": "", "name": "", "guest": False, "badge": "",
            "mine": False, "from": "", "acts": "", "via": "", "text": "",
            "at": k.log.records[k.state.history[(t, "kind")][0][0] - 1]["at"],
            "ts": _epoch(k.log.records[k.state.history[(t, "kind")][0][0] - 1]["at"]),
            "to": [], "reply_to": None, "reply": None, "edited": None, "removed": True, "pinned": False,
            "reactions": [], "mentions": [], "files": [], "about": "", "rev": k.state.rev.get(t, 0)}


def lines_of(k, reader, chat, removed=False):
    """(id, shown facts) of the chat's lines the reader sees, oldest first. removed=True also gives (id, None) for a
    forgotten line that a seen line replies to (the reader sees the chat: the caller has checked)."""
    out, gone = [], []
    for t in k.things("said"):
        if k.state.get(t, "chat") != chat:
            continue
        a = k.shown(reader, t)
        if a is not None:
            out.append((k.state.history[(t, "kind")][0][0], t, a))
        elif removed and k.state.get(t, "forgotten"):
            gone.append(t)
    if gone:
        answered = {a.get("reply_to") for _, _, a in out}
        out += [(k.state.history[(t, "kind")][0][0], t, None) for t in gone if t in answered]
    return [(t, a) for _, t, a in sorted(out, key=lambda x: x[0])]


def files_on(k, reader, ids):
    """{said id: [{id, name, mime, size}]}: files attached to these lines that the reader sees."""
    ids, out = set(ids), {}
    for f in k.things("file"):
        parent = k.state.get(f, "attached_to")
        if parent in ids:
            fa = k.shown(reader, f)
            if fa is not None:
                out.setdefault(parent, []).append({"id": f, "name": fa.get("name", ""), "mime": fa.get("mime_type", ""),
                                                   "size": fa.get("byte_size")})
    return out


EMOJI_MAX, EMOJI_KINDS = 16, 20


def react(k, actor, st, entry, tx, group, saw=None):
    """react <said> emoji=<e>: the caller's reaction on a chat line, toggled."""
    t = st.target
    if k.state.get(t, "kind") != "said":
        raise Refused("react <chat line> emoji=<emoji>: chat <chat> lists its lines")
    emoji = str(st.kv.get("emoji") or st.words or "").strip()
    if not emoji or len(emoji) > EMOJI_MAX or any(c.isspace() for c in emoji) or ":" in emoji:
        raise Refused(f"react {t} emoji=<emoji>: one emoji or short word, at most {EMOJI_MAX} characters, no spaces")
    people = str(k.state.get(k.state.get(t, "chat"), "with") or "").split()
    if people and actor.person not in people:
        raise Refused(f"{k.name(k.state.get(t, 'chat'))} is between {', '.join(k.name(p) for p in people)}")
    key = f"react:{actor.person}:{emoji}"
    if tx.get(t, key):
        tx.set(t, key)
        return {"text": f"ok react {t} [r?] · took back your {emoji}"}
    kinds = {a.split(":", 2)[2] for a in k.state.things.get(t, {}) if a.startswith("react:") and a.count(":") >= 2}
    if emoji not in kinds and len(kinds) >= EMOJI_KINDS:
        raise Refused(f"{t} already has {EMOJI_KINDS} different reactions; add to one of those")
    tx.set(t, key, k.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
    return {"text": f"ok react {t} [r?] · {emoji}"}


def chat(k, actor, st, entry, tx, group, saw=None):
    c = st.target
    if not c or k.state.get(c, "kind") != "chat":
        raise Refused("chat <chat> [limit=<n>]: say which chat; rows chat lists them")
    limit = st.kv.get("limit", "20")
    limit = min(int(limit), 200) if str(limit).isdecimal() else 20
    pinned = str(st.kv.get("pinned", "")).lower() in ("yes", "true")
    got = lines_of(k, actor.person, c, removed=not pinned)
    if pinned:
        got = [(t, a) for t, a in got if a is not None and a.get("pinned")]
    since, before = st.kv.get("since"), st.kv.get("before")
    if since:
        seen = [i for i, (t, _) in enumerate(got) if t == since]
        got = got[seen[0] + 1:] if seen else got
    if before:
        seen = [i for i, (t, _) in enumerate(got) if t == before]
        if not seen:
            raise Refused(f"before={before}: no line of {k.name(c)} you can see is called that")
        got = got[:seen[0]]
    got = got[-limit:]
    files = files_on(k, actor.person, [t for t, a in got if a is not None])
    rows = [said_row(k, t, a, actor.person, files.get(t)) if a is not None else removed_row(k, t, c) for t, a in got]
    for t, a in got:
        if a is not None:
            k.mark(actor, t, a)
    people = str(k.state.get(c, "with") or "").split()
    head = (f"{k.name(c)} ({c}), a chat" + (f" between {', '.join(k.name(p) for p in people)}" if people else ", open")
            + f": {len(rows)} latest line{'' if len(rows) == 1 else 's'}")
    body = [f"  {r['id']} {str(r['at'])[11:16]} " + ("(removed)" if r["removed"] else
            f"{r['by']}{' (guest)' if r['guest'] else ''}: {r['text']}" + (" (edited)" if r["edited"] else "")
            + "".join(f" [{x['emoji']} {x['count']}]" for x in r["reactions"]))
            + (f"\n      ~ {r['acts']}" if r["acts"] else "")
            for r in rows]
    return {"text": head + ("\n" + "\n".join(body) if body else "; say <chat> <words> starts it"), "rows": rows}


def said_set(k, actor, t, kv):
    """set on a said line: its speaker may change its words (an edit, kept as `edited`, its time) and its acts
    (receipts of what they did after saying it), nothing else."""
    if set(kv) - {"acts", "text"}:
        raise Refused("a said line keeps everything but its words and acts; set changes only text= and acts= "
                      "(forget removes the line, undo takes it back)")
    if k.state.get(t, "made_by") != actor.id:
        raise Refused("only whoever said the line edits it or sets its acts")
    if k.state.get(t, "speaker") or k.state.get(t, "read_only") or k.state.get(k.state.get(t, "chat"), "read_only"):
        raise Refused(f"{k.name(k.state.get(t, 'chat'))} is read-only")
    if "text" in kv:
        text = str(kv["text"]).strip()
        if not text:
            raise Refused("an edit needs words; forget removes the line")
        if len(text) > 4000:
            raise Refused("a chat line holds at most 4000 characters")
        if text != k.state.get(t, "text"):
            kv["text"] = text
            kv["edited"] = k.now().strftime("%Y-%m-%dT%H:%M:%SZ")
