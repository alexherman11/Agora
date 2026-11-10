"""EDITING THE KERNEL (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
The kernel changes only to give every world a general capability: a word, a check, a kind of fact any app, module or
person can use. It never names its tenants: no app, module, person, kind or field name appears in this code except the
kernel's own (word, rule, kind, grant, person, ...). If your change needs `if kind == "..."`, a person's name or one app's
field, stop: the missing piece is a general word (a kind's policy, a rule step, a reading). Build that, or put it on the
Board. Names already here are debt (docs/design/source-edits/SOURCE-AUDIT-KERNEL.md lists them); take them out when you can.

Card-rule vocabulary, not a scheduler. Notes and their deduplication undo together.

Who a note reaches is the card's (owner, lead, who; notify_on_land; reporter), unless the rule says otherwise:
route=<field>:<person> sends a card that carries <field> to that person instead; cc=<person> may also read every note
(only where they see the card and its source); text="... {title} ..." is the note's wording, {title} the source card's
title as its recipient sees it (unseen="..." when they may not see it). All three are the world's, in its card rules (4 Nov; before, a person's name, a field,
one module's person and English sentences were written here). The kernel names no one and says nothing."""
from .kernel import Refused
from .next_steps import KINDS, person


def signal(k, actor, st, entry, tx, group, saw=None):
    source = st.target
    card = k.shown(actor.person, source)
    mode = st.kv.get("mode")
    event = st.kv.get("event")
    if mode not in ("waiting", "notify", "reporter") or event not in ("landed", "done"):
        raise Refused("task.signal <card> mode=waiting|notify|reporter event=landed|done [route=<field>:<person>] "
                      "[cc=<person>] [text=\"... {title} ...\"] [unseen=<words>]")
    template = " ".join(str(st.kv.get("text") or "{title}").split())[:500]
    unseen = " ".join(str(st.kv.get("unseen") or "…").split())[:80]     # {title} when the recipient may not see it
    cc = person(k, st.kv.get("cc")) if st.kv.get("cc") else None
    if st.kv.get("cc") and not cc:
        raise Refused(f"cc={st.kv.get('cc')}: no such person here")
    route_field, _, route_to = str(st.kv.get("route") or "").partition(":")
    if st.kv.get("route") and not (route_field and route_to):
        raise Refused("route=<field>:<person>: a card that carries <field> reaches that person instead")

    def routed(row, ref):
        return route_to if route_field and row.get(route_field) else ref
    if mode == "reporter" and card and card.get("status") == "curing" and card.get("curing_via"):
        source = card["curing_via"]
        card = k.shown(actor.person, source)
    if not card or card.get("kind") not in KINDS:
        return {"text": "no card to signal"}
    cause = getattr(k._local, "cause", None)
    if cause and cause in k.undone():
        return {"text": "the triggering act was undone"}
    # A successful word happening is not proof of publication (House may hold it).
    if event == "landed" and card.get("build") != "landed":
        return {"text": "card has not landed"}
    if event == "done" and not (
        str(card.get("lane", "")).casefold() == "done"
        or str(card.get("status", "")).casefold() == "done"
    ):
        return {"text": "card is not done"}

    destinations = []
    if mode == "waiting":
        for target in list(k.state.things):
            row = k.shown(actor.person, target)
            if row and row.get("kind") in KINDS and row.get("waiting_on") == source:
                recipient = next((p for field in ("owner", "lead", "who") if (p := person(k, row.get(field)))), None)
                destinations.append((target, row, recipient))
    elif mode == "notify":
        destinations.append((source, card, card.get("notify_on_land")))
    else:
        if card.get("reporter"):
            destinations.append((source, card, card["reporter"]))
        # The old reporter rule refers to a rough spot's maker through curing_via.
        for target in list(k.state.things):
            row = k.shown(actor.person, target)
            if row and row.get("curing_via") == source and row.get("status") == "curing":
                destinations.append((target, row, row.get("reporter") or row.get("for") or row.get("made_by")))

    count = 0
    keys = {k.state.get(t, "card_signal") for t in k.things("taskboard-event")}
    for target, row, ref in destinations:
        recipient = person(k, routed(row, ref))
        if not recipient or k.shown(recipient, target) is None or k.shown(recipient, source) is None:
            continue
        # Use the recipient's projection, including field privacy, for every word
        # delivered. The rule maker can have wider sight than the recipient.
        visible_source = k.shown(recipient, source)
        title = next((card[field] for field in ("title", "name")
                      if card.get(field) and card.get(field) == visible_source.get(field)), unseen)
        key = f"{mode}:{source}:{target}:{recipient}"
        if key in keys:
            continue
        keys.add(key)
        k.reaches(actor, entry["word"], "taskboard-event", target=target)
        text = template.replace("{title}", str(title))
        note = tx.mint()
        readers = {recipient, actor.person}
        if cc and k.shown(cc, target) is not None and k.shown(cc, source) is not None:
            readers.add(cc)
        # One happening per note; existing hear:make admission and the House
        # inbox deliver it. No new module grants or execution authority.
        tx.part("make", note, "card rule note")
        for field, value in {
            "kind": "taskboard-event", "about": target, "source": source,
            "visibility_of": target, "text": text, "to": recipient,
            "sees": "|".join("person:" + p for p in sorted(readers) if p),
            "sees.text": "|".join("person:" + p for p in sorted({recipient, actor.person}) if p),
            "card_signal": key, "made_by": actor.id, "in:" + group: len(k.log.records) + 1,
        }.items():
            tx.set(note, field, value)
        count += 1
    return {"text": f"card rules: {count} addressed note(s)"}
