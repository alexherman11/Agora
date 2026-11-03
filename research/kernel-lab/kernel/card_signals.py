"""Card-rule vocabulary, not a scheduler. Notes and their deduplication undo together."""
from .kernel import Refused
from .next_steps import KINDS, person


def signal(k, actor, st, entry, tx, group, saw=None):
    source = st.target
    card = k.shown(actor.person, source)
    mode = st.kv.get("mode")
    event = st.kv.get("event")
    if mode not in ("waiting", "notify", "reporter") or event not in ("landed", "done"):
        raise Refused("task.signal <card> mode=waiting|notify|reporter event=landed|done")
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
                recipient = "JEFF" if row.get("alex_ask") else next(
                    (p for field in ("owner", "lead", "who") if (p := person(k, row.get(field)))), None)
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
        recipient = person(k, "JEFF" if row.get("alex_ask") else ref)
        if not recipient or k.shown(recipient, target) is None or k.shown(recipient, source) is None:
            continue
        # Use the recipient's projection, including field privacy, for every word
        # delivered. The rule maker can have wider sight than the recipient.
        visible_source = k.shown(recipient, source)
        title = next((card[field] for field in ("title", "name")
                      if card.get(field) and card.get(field) == visible_source.get(field)), "the dependency")
        key = f"{mode}:{source}:{target}:{recipient}"
        if key in keys:
            continue
        keys.add(key)
        k.reaches(actor, entry["word"], "taskboard-event", target=target)
        text = (f"Unblocked: {title} has landed" if event == "landed" else f"Unblocked: {title} is done")
        if mode == "notify":
            text = f"{title} has landed; your next step is due."
        elif mode == "reporter":
            text = f"A fix for what you found has landed: {title}. Please check it."
        note = tx.mint()
        readers = {recipient, actor.person}
        house = k.module_named("house")
        sponsor = k.state.get(house, "for") if house else None
        if sponsor and k.shown(sponsor, target) is not None and k.shown(sponsor, source) is not None:
            readers.add(sponsor)
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
