"""Opt-in conversational queuing; delivery and authority still belong to the house/desk.

Only reply_policy=queue changes the old stale-reply rule. Ordinary human follow-ups
are delivered on the next turn; leading stop/cancel/correction directives invalidate
the current turn's pending actions. This does not cancel a running provider request.
"""

import re


def queue_enabled(subject):
    return (subject.get("props") or {}).get("reply_policy") == "queue"


def human_event(w, event):
    import persons
    import rooms

    actor = str(event.get("by") or "").split("/")[0]
    pid = persons.today(w, actor) if persons.on(w) else None
    human = ((w.subjects.get(pid) or {}).get("props") or {}).get("kind") == "human"
    return human or rooms.kind_of(w, actor) == "person"


def message_body(event, text):
    """Remove only the recorded signature and address, never a content heading."""
    from world import header

    body = str(text).strip()
    signed = str((event.get("args") or {}).get("signed") or "")
    if signed and body.casefold().startswith((signed + ":").casefold()):
        body = body[len(signed) + 1:].lstrip()
    if body.startswith("@"):
        _, end = header(body)
        body = body[end:].lstrip(" :,")
    return body


def interrupts(text):
    """Explicit leading directives, not mentions or requests to correct a document."""
    return bool(re.match(
        r"^(?:/(?:interrupt|stop|cancel|correct)\b|"
        r"(?:please\s+)?(?:stop|cancel|wait|interrupt|correction)\b|"
        r"(?:please\s+)?(?:do not|don't|don’t)\b)", str(text).strip(), re.I
    ))


def is_interrupt(event, text):
    return ((event.get("args") or {}).get("mode") == "interrupt"
            or interrupts(message_body(event, text)))


def receives(w, subject, event, actor):
    import rooms

    to, _ = rooms.line_to(event)
    if to:
        return rooms.calls(w, subject, to, actor)
    corner = rooms.corner_of(w, actor)
    mine = corner is not None and any(
        n["type"] == "appearance" and n.get("subject") == subject["id"]
        and rooms._within(w, n, corner) for n in w.nodes.values()
    )
    return mine or rooms.member(w, subject, actor)


def queued_line(w, subject, event, text, actor):
    """Caller must establish that the event occurred after the resident turn began."""
    return (queue_enabled(subject) and human_event(w, event)
            and receives(w, subject, event, actor) and not is_interrupt(event, text))


def queued_interrupts(w, actor, cursor):
    """Stable records of post-cursor human directives; pure read, no cursor mutation."""
    if cursor is None:
        return []
    import rooms

    if rooms.kind_of(w, actor) != "resident":
        return []
    events = {e["id"]: e for e in w.events[max(0, int(cursor)):]}
    result = []
    for subject in w.subjects.values():
        if subject.get("kind") != "chat" or not queue_enabled(subject):
            continue
        for line in subject.get("lines") or []:
            event = events.get(line.get("ev"))
            if (event and human_event(w, event) and receives(w, subject, event, actor)
                    and is_interrupt(event, line["text"])):
                result.append({"event": event["id"], "message": line["id"],
                               "chat": next(iter(w.appearances_of(subject["id"])), subject["id"]),
                               "text": message_body(event, line["text"])})
    return sorted(result, key=lambda rec: int(rec["event"][1:]))
