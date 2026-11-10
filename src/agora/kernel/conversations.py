"""General private conversation and draft words (dk2770).

No provider, tenant or UI. The authenticated host supplies Actor; model output
never supplies that identity. A module answers using caller rights AND grants.
"""
from .kernel import Refused
from .lines import Step


def require_person(k, actor):
    if (actor.kind != "person" or actor.id != actor.person or actor.caller is not None
            or getattr(k._local, "rule", None) or getattr(k._local, "cause", None)
            or getattr(k._local, "verb_depth", 0)):
        raise Refused("this action requires the person's direct act")


def _arguments(st, allowed):
    if st.words or set(st.kv) - set(allowed):
        raise Refused("unexpected conversation or draft arguments")


def conversation(k, actor, chat):
    a = k.shown(actor.person, chat)
    if (not a or a.get("kind") != "chat"
            or a.get("conversation_owner") != actor.person or not a.get("conversation_agent")):
        raise Refused("no private conversation for this caller")
    if actor.kind == "module":
        if (actor.module != a["conversation_agent"] or actor.id != actor.module
                or actor.caller is None or actor.caller.kind != "person"
                or actor.caller.id != actor.person or actor.caller.person != actor.person):
            raise Refused("this module cannot answer this conversation")
    else:
        require_person(k, actor)
    return a


def open_conversation(k, actor, st, entry, tx, group, saw=None):
    require_person(k, actor)
    tx.extra["passive"] = True
    _arguments(st, {"fresh"})
    if st.kv.get("fresh", "no") not in ("yes", "no"):
        raise Refused("fresh says yes or no")
    agent = k.shown(actor.person, st.target)
    if not agent or agent.get("kind") != "module" or not agent.get("on"):
        raise Refused("choose an enabled module")
    chats = [t for t in k.things("chat")
             if k.state.get(t, "conversation_agent") == st.target
             and k.state.get(t, "conversation_owner") == actor.person
             and k.shown(actor.person, t) is not None]
    if chats and st.kv.get("fresh") != "yes":
        chat = max(chats, key=lambda t: k.state.history[(t, "kind")][0][0])
    else:
        chat = tx.mint()
        for key, value in {
            "kind": "chat", "name": agent.get("name", "Conversation"),
            "conversation_agent": st.target, "conversation_owner": actor.person,
            "with": actor.person, "sees": "person:" + actor.person, "read_only": True,
            "made_by": actor.person, f"in:{group}": len(k.log.records) + 1,
        }.items():
            tx.set(chat, key, value)
    return {"text": "Your private conversation", "rows": [{"id": chat, "kind": "chat"}]}


def append_conversation(k, actor, st, entry, tx, group, saw=None):
    tx.extra["passive"] = True
    _arguments(st, {"text"})
    conversation(k, actor, st.target)
    k.reaches(actor, st.word, "said", fields=("text", "chat"), group=group)
    text = str(st.kv.get("text", ""))
    if not text.strip():
        raise Refused("a conversation message needs text")
    t = tx.mint()
    for key, value in {
        "kind": "said", "text": text, "chat": st.target, "visibility_of": st.target,
        "made_by": actor.id, "for": actor.person, f"in:{group}": len(k.log.records) + 1,
    }.items():
        tx.set(t, key, value)
    # No addressing, notifications or House wake, even when text contains @names.
    return {"text": "Saved in your conversation", "rows": [{"id": t, "kind": "said"}]}


def create_draft(k, actor, st, entry, tx, group, saw=None):
    tx.extra["passive"] = True
    _arguments(st, {"text", "destination"})
    conversation(k, actor, st.target)
    if actor.kind != "module":
        raise Refused("a conversation module creates the draft")
    k.reaches(actor, st.word, "draft", fields=("text", "destination"), group=group)
    text, destination = st.kv.get("text", ""), st.kv.get("destination")
    dest = k.shown(actor.person, destination)
    if not text.strip() or not dest or dest.get("kind") not in ("group", "place"):
        raise Refused("a draft needs text and a visible destination group")
    t = tx.mint()
    for key, value in {
        "kind": "draft", "text": text, "destination": destination, "chat": st.target,
        "made_by": actor.module, "for": actor.person, "author": actor.person,
        "sees": "person:" + actor.person, "status": "draft",
        f"in:{group}": len(k.log.records) + 1,
    }.items():
        tx.set(t, key, value)
    return {"text": "Private draft saved; review it before Post", "rows": [{"id": t, "kind": "draft"}]}


def post_draft(k, actor, st, entry, tx, group, saw=None):
    from .words import post
    require_person(k, actor)
    _arguments(st, {"rev"})
    a = k.shown(actor.person, st.target)
    if not a or a.get("kind") != "draft" or a.get("author") != actor.person:
        raise Refused("only the draft's person can Post it")
    if a.get("posted"):
        return {"text": "Already posted", "rows": [{"id": a["posted"], "kind": "post"}]}
    if str(k.state.rev.get(st.target)) != st.kv.get("rev"):
        raise Refused("review the current draft before Post")
    destination = a["destination"]
    dest = k.shown(actor.person, destination)
    if not dest or dest.get("kind") not in ("group", "place"):
        raise Refused("the destination is no longer available")
    eid = k.find_entry("post", destination)
    e = k.entry(eid) if eid else None
    if not e or k.source(e) != ("kernel", "post") or not k.may(actor, e, None, destination):
        raise Refused("you cannot post at this destination")
    step = Step("", e["word"], None, {"text": a["text"], "in": destination}, "")
    k.guard(actor, e, step)
    once = k.once(actor, e, None, tx)
    if once:
        raise Refused(once)
    tx.part(e["word"], None, "Post reviewed draft")
    tx.parts[-1]["entry"] = eid
    post(k, actor, step, e, tx, destination, saw=saw)
    published = tx.made[-1]
    tx.set(st.target, "posted", published)
    tx.set(st.target, "status", "posted")
    return {"text": "Posted as you [r?]", "rows": [{"id": published, "kind": "post"}]}
