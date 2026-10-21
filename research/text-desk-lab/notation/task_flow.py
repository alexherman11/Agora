"""Event-driven task handoffs. Reading/replaying the journal never sends anything.

The house consumes notices with its durable inbox/cursor and records ordinary knock
receipts. A knock means queued for the resident, never proof of model receipt or
acceptance. Only an owner's own accepted_by/status event counts as acceptance.
"""

import persons

BLOCK_FIELDS = ("blocked_on", "blocker_owner", "resume_when")
MILESTONES = {"checkpoint", "completed", "failed", "blocked"}
STATES = {"blocked", "done", "failed", "waiting", "paused", "yielded", "reported", "ready"}


def _bounded(value, limit):
    text = str(value or "")
    return text if len(text) <= limit else text[:limit] + " [truncated; read task]"


def _creator(w, event, card):
    if event.get("verb") == "create":
        return event.get("by", "")
    sid = card.get("id")
    for candidate in w.events:
        if (
            candidate.get("verb") == "create"
            and (candidate.get("undo") or {}).get("delete_subject") == sid
        ):
            return candidate.get("by", "")
    return ""


def _card(w, event):
    if event.get("verb") == "create":
        args = event.get("args") or {}
        if args.get("kind") not in {"task", "story", "epic"}:
            return None, {}, {}
        return args, {}, dict(args)
    target = event.get("target")
    node = w.nodes.get(target, {})
    sid = node.get("subject", target)
    undo = event.get("undo") or {}
    before = undo.get("restore_subject")
    if before is None:
        before = next((s for s in undo.get("restore_subjects", []) if s.get("id") == sid), None)
    # Existing event snapshots protect attribution from a later reassignment.
    card = before or w.subjects.get(sid)
    if not card or card.get("kind") not in {"task", "story", "epic"}:
        return None, {}, {}
    old = dict((before or {}).get("props") or {})
    props = dict(old)
    props.update({k: str(v) for k, v in (event.get("args") or {}).items() if k != "remove"})
    for key in str((event.get("args") or {}).get("remove", "")).split(","):
        props.pop(key, None)
    return card, old, props


def _residents(w, value):
    for node in w.nodes.values():
        props = node.get("props") or {}
        actor = props.get("actor")
        if (
            node.get("type") == "surface"
            and props.get("role") == "resident"
            and actor
            and persons.holds(w, value, actor)
        ):
            yield str(actor).lower()


def notices(w, event):
    """Return bounded, structured notices for one durable native mutation.

    No mutation, timer, model call, inference from presence, or automatic acceptance.
    Sleeping residents remain recipients (a held receipt); House.step controls waking.
    """
    if event.get("undone") or event.get("verb") not in {"create", "prop", "put"}:
        return []
    card, old, props = _card(w, event)
    if card is None:
        return []
    by = str(event.get("by") or "").split("/")[0]
    changed = {k for k in set(old) | set(props) if old.get(k) != props.get(k)}
    recipients = {}
    lead = props.get("lead") or props.get("asked_by") or _creator(w, event, card)

    def add(value, kind):
        for actor in _residents(w, value):
            if not persons.holds(w, actor, by):
                recipients.setdefault(actor, []).append(kind)

    if "owner" in changed and props.get("owner"):
        add(props["owner"], "assignment: awaiting your explicit acceptance")
    accepted = persons.holds(w, props.get("owner", ""), by) and (
        ("accepted_by" in changed and persons.holds(w, props.get("accepted_by", ""), by))
        or ("status" in changed and props.get("status") in {"accepted", "doing", "working"})
    )
    if accepted:
        add(lead, "accepted by " + by)
    state = (
        props.get("commission")
        if "commission" in changed
        else props.get("status")
        if "status" in changed
        else None
    )
    if state in STATES:
        add(lead, "state: " + state)
    if changed.intersection(BLOCK_FIELDS):
        add(lead, "blocker changed")
        if props.get("blocked_on"):
            add(props.get("blocker_owner", ""), "blocker needs resolution")
    if (
        "worker_milestone" in (event.get("args") or {})
        and changed.intersection({"worker_summary", "worker_milestone", "worker_evidence"})
        and props.get("worker_milestone") in MILESTONES
    ):
        add(lead, "worker " + props["worker_milestone"])
    missing = [k for k in BLOCK_FIELDS if not props.get(k)] if state == "blocked" else []
    return [
        {
            "id": f"{event['id']}:{actor}",
            "event": event["id"],
            "recipient": actor,
            "target": (event.get("undo") or {}).get("delete", event["target"]),
            "title": str(card.get("title") or "Task")[:160],
            "kinds": kinds,
            "summary": _bounded(props.get("worker_summary"), 600),
            "evidence": str(props.get("worker_evidence") or "")[:200],
            "blocker": str(props.get("blocked_on") or "")[:200],
            "resolver": str(props.get("blocker_owner") or "")[:80],
            "resume": str(props.get("resume_when") or "")[:200],
            "missing": missing,
        }
        for actor, kinds in recipients.items()
    ]


def delivery_text(notice):
    text = f'~ Task "{notice["title"]}" ({notice["target"]}, {notice["event"]}): ' + "; ".join(
        notice["kinds"]
    )
    if notice["summary"]:
        text += ". " + notice["summary"]
    if notice["blocker"]:
        text += (
            f". Blocked on {notice['blocker']}; resolver: {notice['resolver'] or 'missing'}; "
            f"resumes when: {notice['resume'] or 'missing'}"
        )
    if notice["missing"]:
        text += ". Complete blocked-task contract: " + ", ".join(notice["missing"])
    if notice["evidence"]:
        text += ". Evidence: " + notice["evidence"]
    return text + ". Read the task for full detail."
