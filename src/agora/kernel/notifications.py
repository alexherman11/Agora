"""Durable addressed world notifications; no delivery process or scheduler."""
from .chat import people_named
from .kernel import Refused


def create(k, actor, tx, group, word, *, source, about, recipient, text, key="", cc=None):
    if not text or not recipient:
        raise Refused("a notification needs a recipient and text")
    for reader in (actor.person, recipient):
        if any(k.shown(reader, target) is None for target in (source, about)):
            raise Refused("notification source and subject must be visible to sender and recipient")
    identity = f"{actor.person}:{recipient}:{key or source}"
    for n in k.things("notification"):
        if k.state.get(n, "key") == identity:
            return n, False
    readers = {actor.person, recipient}
    if cc and all(k.shown(cc, t) is not None for t in (source, about)):
        readers.add(cc)
    k.reaches(actor, word, "notification", target=about)
    n = tx.mint()
    tx.part("make", n, "addressed notification")
    facts = {
        "kind": "notification", "recipient": recipient, "to": recipient,
        "source": source, "about": about, "text": text, "state": "unread",
        "key": identity, "visibility_of": source, "made_by": actor.id,
        "sees": "|".join("person:" + p for p in sorted(readers)),
        "sees.text": "|".join("person:" + p for p in sorted({actor.person, recipient})),
        "in:" + group: len(k.log.records) + 1,
    }
    if actor.id != actor.person:
        facts["for"] = actor.person
    for field, value in facts.items():
        tx.set(n, field, value)
    return n, True


def send(k, actor, st, entry, tx, group, saw=None):
    people = people_named(k, actor, st.kv.get("to"))
    if len(people) != 1:
        raise Refused("notification.send needs exactly one to=<person>")
    cc = people_named(k, actor, st.kv.get("cc"))
    if len(cc) > 1:
        raise Refused("notification.send takes one envelope cc=<person>")
    notice, made = create(k, actor, tx, group, entry["word"], source=st.target,
                          about=st.kv.get("about") or st.target, recipient=people[0],
                          text=st.kv.get("text"), key=st.kv.get("key", ""), cc=cc[0] if cc else None)
    return {"text": f"{'created' if made else 'existing'} notification {notice}",
            "rows": [{"id": notice}]}


def state(k, actor, st, entry, tx, group, saw=None):
    row = k.shown(actor.person, st.target)
    if not row or row.get("kind") != "notification" or row.get("recipient") != actor.person:
        raise Refused("only the notification recipient may read or dismiss it")
    value = "dismissed" if entry["bound"] == "notification.dismiss" else "read"
    if row.get("state") in (value, "dismissed"):
        return {"text": "notification already " + row["state"]}
    k.reaches(actor, entry["word"], "notification", target=st.target)
    tx.part("set", st.target, "notification " + value)
    tx.set(st.target, "state", value)
    return {"text": "notification " + value, "rows": [{"id": st.target, "state": value}]}
