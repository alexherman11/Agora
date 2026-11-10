"""General pending delegation receipts and guarded, addressed refusal notices.

No scheduler or execution permission. Matching vocabulary, chat and wording are
world policy. Source messages are immutable; a rule cannot supply their speaker.
"""
import hashlib
import re

from .chat import people_named
from .kernel import Refused
from .store import GONE


def person(k, actor, value):
    return people_named(k, actor, value)[0] if value else None


def write(k, actor, tx, group, kind, facts):
    t = tx.mint()
    tx.part("make", t, kind)
    for key, value in dict(kind=kind, made_by=actor.id, **facts).items():
        tx.set(t, key, value)
    if actor.id != actor.person:
        tx.set(t, "for", actor.person)
    tx.set(t, "in:" + group, len(k.log.records) + 1)
    return t


def open_(k, actor, st, entry, tx, group, saw=None):
    owner = person(k, actor, st.kv.get("owner")) or actor.person
    if owner != actor.person:
        return {"text": "handoff belongs to another delegator"}
    target = st.target
    row = k.shown(owner, target)
    if not row:
        raise k.no_such(target)
    cause = getattr(k._local, "cause", None)
    if cause and cause in k.undone():
        return {"text": "handoff source was undone"}
    field = st.kv.get("to_field")
    if field and field not in row:
        return {"text": "recipient field is not visible"}
    value = row.get(field) if field else st.kv.get("to")
    if field and cause:
        value = k.state.before(target, field, cause + 1)
        if value is GONE:
            value = None
    recipient = person(k, actor, value)
    if not recipient or recipient == owner or k.shown(recipient, target) is None:
        return {"text": "no receiving person"}
    key = f"{target}:{owner}:{recipient}:{cause or len(k.log.records) + 1}"
    for h in k.things("handoff"):
        if k.state.get(h, "key") == key:
            return {"text": "handoff already recorded", "rows": [{"id": h}]}
    k.reaches(actor, entry["word"], "handoff", target=target)
    for h in k.things("handoff"):
        if k.state.get(h, "about") == target and k.state.get(h, "owner") == owner:
            tx.set(h, "status", "superseded")
    h = write(k, actor, tx, group, "handoff", {
        "about": target, "owner": owner, "recipient": recipient,
        "status": "pending", "key": key, "source_record": cause or len(k.log.records) + 1,
        "recipient_field": field or "", "visibility_of": target,
        "sees": f"person:{owner}|person:{recipient}",
    })
    return {"text": f"pending handoff {h}", "rows": [{"id": h}]}


def close(k, actor, st, entry, tx, group, saw=None):
    recipient = person(k, actor, st.kv.get("recipient")) or actor.person
    count = 0
    for h in k.things("handoff"):
        row = k.shown(actor.person, h)
        if (row and row.get("about") == st.target and row.get("status") == "pending"
                and row.get("recipient") == recipient
                and actor.person in (row.get("owner"), recipient)):
            k.reaches(actor, entry["word"], "handoff", target=h)
            tx.set(h, "status", "accepted")
            count += 1
    return {"text": f"accepted {count} handoff(s)"}


def pattern(policy, field, text):
    expression = policy.get(field)
    if not expression:
        return False
    if len(str(expression)) > 2000:
        raise Refused("handoff policy pattern is too long")
    try:
        return bool(re.search(expression, text, re.I))
    except re.error as exc:
        raise Refused(f"invalid handoff policy {field}: {exc}") from exc


def linked(k, reader, source, target):
    """Explicit about, task link/name, or reply chain; never another chat."""
    row = source
    visited = set()
    for _ in range(12):
        if row.get("about") == target:
            return True
        text = str(row.get("text") or "")
        if re.search(r"(?<!\w)" + re.escape(target) + r"(?!\w)", text):
            return True
        target_row = k.shown(reader, target) or {}
        name = str(target_row.get("title") or target_row.get("name") or "")
        if len(name) >= 5 and name.casefold() in text.casefold():
            return True
        reply = row.get("reply_to")
        if not reply or reply in visited:
            break
        visited.add(reply)
        row = k.shown(reader, reply) or {}
        if row.get("chat") != source.get("chat"):
            break
    return False


def record_refusal(k, actor, tx, group, h, row, source, reason, category):
    key = h + ":" + hashlib.sha256(" ".join(reason.casefold().split()).encode()).hexdigest()
    if any(k.state.get(e, "key") == key for e in k.things("handoff-refusal")):
        return 0
    write(k, actor, tx, group, "handoff-refusal", {
        "handoff": h, "about": row["about"], "owner": row["owner"],
        "recipient": row["recipient"], "reason": reason, "category": category,
        "source": source, "visibility_of": source, "key": key,
        "sees": f"person:{row['owner']}|person:{row['recipient']}",
    })
    return 1


def refuse(k, actor, st, entry, tx, group, saw=None):
    """Explicit recipient evidence for refusals outside the world's vocabulary."""
    row = k.shown(actor.person, st.target)
    source_id = st.kv.get("source")
    source = k.shown(actor.person, source_id)
    category = st.kv.get("category")
    if (not row or row.get("kind") != "handoff" or row.get("status") != "pending"
            or row.get("recipient") != actor.person or not source or source.get("kind") != "said"
            or (source.get("for") or source.get("made_by")) != actor.person
            or category not in ("scope", "provider", "cannot")
            or k.shown(row["owner"], source_id) is None
            or k.state.history[(source_id, "kind")][0][0] <= int(row["source_record"])):
        raise Refused("handoff.refuse needs your pending handoff, your later visible source reply, "
                      "and category=scope|provider|cannot")
    k.reaches(actor, entry["word"], "handoff-refusal", target=st.target)
    count = record_refusal(k, actor, tx, group, st.target, row, source_id, source["text"], category)
    return {"text": f"recorded {count} handoff refusal(s)"}


def observe(k, actor, st, entry, tx, group, saw=None):
    """A plain reply becomes structured evidence only for a pending recipient."""
    source = k.shown(actor.person, st.target)
    policy = k.shown(actor.person, st.kv.get("policy"))
    if not source or source.get("kind") != "said":
        return {"text": "no recipient reply"}
    if not policy or policy.get("kind") != "handoff-policy" or not k.own(actor.person, st.kv.get("policy")):
        raise Refused("handoff.observe needs your own handoff-policy")
    if source.get("chat") != policy.get("chat"):
        return {"text": "reply is outside the handoff chat"}
    speaker = source.get("for") or source.get("made_by")
    if speaker == actor.person:
        return {"text": "delegator reply"}
    # Strip quotations/code, so discussing a refusal is not making one.
    reason = str(source.get("text") or "")
    bare = re.sub(r'```[\s\S]*?```|`[^`]*`|"[^"]*"|“[^”]*”|(?m:^\s*>.*$)', " ", reason)
    if pattern(policy, "resolved", bare):
        return {"text": "recipient reports the restriction resolved"}
    category = next((c for c in ("scope", "provider", "cannot")
                     if pattern(policy, c, bare)), None)
    if not category:
        return {"text": "ordinary reply"}
    seq = k.state.history[(st.target, "kind")][0][0]
    cause = getattr(k._local, "cause", None)
    if cause and cause in k.undone():
        return {"text": "reply was undone"}
    candidates = []
    for h in k.things("handoff"):
        row = k.shown(actor.person, h)
        if (not row or row.get("status") != "pending" or row.get("owner") != actor.person
                or row.get("recipient") != speaker or seq <= int(row.get("source_record", 0))):
            continue
        target = row["about"]
        field = row.get("recipient_field")
        current = k.shown(actor.person, target)
        if not current or (field and person(k, actor, current.get(field)) != speaker):
            continue
        if k.shown(speaker, target) is None:
            continue
        if linked(k, actor.person, source, target) or pattern(policy, "session", bare):
            candidates.append((h, row))
    count = 0
    for h, row in candidates:
        k.reaches(actor, entry["word"], "handoff-refusal", target=h)
        count += record_refusal(k, actor, tx, group, h, row, st.target, reason, category)
    return {"text": f"recorded {count} handoff refusal(s)"}


def notify(k, actor, st, entry, tx, group, saw=None):
    event = k.shown(actor.person, st.target)
    if not event or event.get("kind") != "handoff-refusal" or event.get("notice"):
        return {"text": "no undelivered refusal"}
    h = event.get("handoff")
    hand = k.shown(actor.person, h)
    source = k.shown(actor.person, event.get("source"))
    if (not hand or hand.get("status") != "pending" or hand.get("owner") != actor.person
            or not source or source.get("kind") != "said"
            or (source.get("for") or source.get("made_by")) != hand.get("recipient")
            or event.get("about") != hand.get("about")
            or event.get("reason") != source.get("text")
            or k.state.history[(event["source"], "kind")][0][0] <= int(hand["source_record"])):
        return {"text": "refusal no longer belongs to a pending handoff"}
    # All evidence is projected as the destination, including private fields.
    target = hand["about"]
    chat = source["chat"]
    target_row = k.shown(actor.person, target)
    field = hand.get("recipient_field")
    if (not target_row or k.shown(actor.person, chat) is None
            or (field and person(k, actor, target_row.get(field)) != hand["recipient"])):
        return {"text": "refusal evidence is not visible"}
    template = st.kv.get("text")
    if not template:
        raise Refused("handoff.notify needs text= with {task}, {recipient}, {reason}, {source}")
    title = target_row.get("title") or target_row.get("name") or target
    values = {"task": f"[{title}]({target})",
              "recipient": k.name(hand["recipient"]), "reason": source["text"],
              "source": f"[source]({event['source']})"}
    text = re.sub(r"\{(task|recipient|reason|source)\}", lambda m: values[m[1]], template)
    from .notifications import create
    cc = person(k, actor, st.kv.get("cc"))
    notice, _ = create(k, actor, tx, group, entry["word"], source=event["source"],
                       about=target, recipient=actor.person, text=text, key="handoff:" + h, cc=cc)
    tx.set(h, "status", "refused")
    tx.set(h, "refusal", st.target)
    tx.set(st.target, "notice", notice)
    return {"text": "one addressed handoff notice", "rows": [{"id": notice}]}
