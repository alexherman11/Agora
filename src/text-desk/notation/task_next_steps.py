"""Task-grounded attention, not a second task store or an execution authority.

World tasks/promises own intent and evidence. The host only projects them and
queues bounded, deduplicated review requests through the existing durable inbox.
Importing, rendering or replaying this module has no external effects.
"""

import hashlib
import json
from datetime import UTC, datetime

import persons
import promises
import task_flow

KINDS = {"task", "story", "epic"}
HELD = {"paused", "cancelled", "trashed", "permission", "permission-held", "unknown"}
CLOSED = {"done", "cancelled", "trashed"}
RESULTS = {"completed", "failed"}
PRIORITY = {"low": 0, "normal": 1, "high": 2, "urgent": 3, "0": 3, "1": 2, "2": 1, "3": 0}
MATERIAL = (
    "owner",
    "lead",
    "asked_by",
    "goal",
    "acceptance",
    "request_ref",
    "parent_task",
    "worker_milestone",
    "worker_summary",
    "worker_evidence",
    "result_ref",
)
FIELDS = (
    "target",
    "title",
    "project",
    "priority",
    "state",
    "next_action",
    "acceptance",
    "waiting_on",
    "blocker",
    "resolver",
    "resume_when",
    "review_at",
    "basis",
    "reviewed",
    "verified",
    "promises",
)


def canonical(w, ref):
    return w.subject_of(ref) or ref


def props(w, sid):
    return w.subjects.get(canonical(w, sid), {}).get("props") or {}


def responsible(w, p, actor):
    return any(persons.holds(w, p.get(k, ""), actor) for k in ("owner", "lead", "asked_by"))


def held(p):
    return (
        p.get("status") in HELD
        or p.get("commission") in HELD
        or p.get("authority") in {"held", "permission"}
        or p.get("approval_required") in (True, "true", "yes")
        or p.get("effect_state") == "unknown"
    )


def enabled(w, rid):
    return (w.nodes.get(rid, {}).get("props") or {}).get("next_steps") == "on"


def _hash(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()[:16]


def _target(w, e):
    return canonical(w, (e.get("undo") or {}).get("delete_subject") or e.get("target", ""))


def _revisions(w):
    revisions = {}
    for e in w.events:
        if not e.get("undone") and e.get("verb") in {"create", "prop", "put"}:
            args = e.get("args") or {}
            if (
                any(k in args or k in str(args.get("remove", "")).split(",") for k in MATERIAL)
                or args.get("status") in HELD | {"doing", "failed"}
                or args.get("commission") in HELD | {"failed", "working"}
            ):
                revisions[_target(w, e)] = e["id"]
    return revisions


def basis(w, sid, revisions=None):
    """Current intent/result version, including children; cosmetic noise is irrelevant.

    Material event ids prevent a correction followed by a revert from resurrecting
    an old attestation. Undone attestations do not count; undone changes restore
    the prior material basis.
    """
    sid = canonical(w, sid)
    children = sorted(
        s
        for s, t in w.subjects.items()
        if t.get("kind") in KINDS and canonical(w, props(w, s).get("parent_task", "")) == sid
    )
    revisions = _revisions(w) if revisions is None else revisions
    return _hash(
        [
            (
                s,
                {k: props(w, s).get(k, "") for k in MATERIAL},
                revisions.get(s),
                [
                    w.subjects.get(canonical(w, props(w, s).get(k, "")), {}).get("rev")
                    for k in ("worker_evidence", "result_ref")
                ],
            )
            for s in [sid, *children]
        ]
    )


def attested(w, sid, key, token, evidence=None):
    """An owner's authored review/verification, never a delivery receipt.

    The existing world identity/authority system remains the trust boundary. A
    verification is an attributed claim with inspectable evidence, not proof that
    the host evaluated arbitrary acceptance prose.
    """
    p = props(w, sid)
    if p.get(key) != token:
        return False
    for e in reversed(w.events):
        if e.get("undone") or _target(w, e) != sid or key not in (e.get("args") or {}):
            continue
        author = e.get("by", "")
        # A lead owns review of a delegated result; otherwise its owner does.
        reviewer = p.get("lead") or p.get("asked_by") or p.get("owner", "")
        # Token and evidence must be bound by the SAME authorized event. A later
        # evidence-only property edit cannot borrow the earlier owner's claim.
        if evidence and canonical(w, e["args"].get("verified_evidence", "")) != evidence:
            return False
        if evidence and any(
            not later.get("undone")
            and _target(w, later) == evidence
            and later.get("verb") not in {"comment", "markread"}
            for later in w.events[w.events.index(e) + 1 :]
        ):
            return False
        return e["args"][key] == token and persons.holds(w, reviewer, author)
    return False


def _deadline(value):
    try:
        date = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return date.timestamp() if date.tzinfo else None  # no invented local timezone
    except (ValueError, TypeError, OverflowError):
        return None


def _promise_rows(w, actor):
    reader = promises._person(w, actor)
    for sid in promises.all_sids(w):
        st = promises.state(w, sid)
        if st["state"] not in {promises.OPEN, promises.ASKED, promises.REPORTED}:
            continue
        if any(promises.same(st.get(k), reader) for k in ("holder", "owed", "asker", "asked")):
            yield st, promises.phrase(w, st, reader=reader, hints=False)


def rows(w, actor, now=None):
    """Unbounded inspectable source; only the model packet is bounded."""
    now = now if now is not None else datetime.now(UTC).timestamp()
    linked, unlinked = {}, []
    for st, phrase in _promise_rows(w, actor):
        about = canonical(w, st["about"])
        if w.subjects.get(about, {}).get("kind") in KINDS:
            linked.setdefault(about, []).append(phrase)
        else:
            unlinked.append((st, phrase))
    result = []
    revisions = _revisions(w)
    for sid, s in w.subjects.items():
        p = s.get("props") or {}
        if s.get("kind") not in KINDS or not (responsible(w, p, actor) or sid in linked):
            continue
        status = p.get("status", "open")
        # Legacy closed cards stay closed; a tracked done card needs verification.
        tracked = bool(p.get("next_action") or p.get("acceptance"))
        has_result = p.get("worker_milestone") in RESULTS
        if (
            p.get("commission") == "landed"
            and not tracked
            and not has_result
            and not linked.get(sid)
        ):
            continue
        if (status in CLOSED or p.get("commission") in {"cancelled", "trashed"}) and not linked.get(
            sid
        ):
            if status != "done" or not (tracked or has_result):
                continue
        token = basis(w, sid, revisions)
        reviewed = attested(w, sid, "reviewed_basis", token)
        if (
            status == "done"
            and reviewed
            and p.get("parent_task")
            and not p.get("acceptance")
            and not linked.get(sid)
        ):
            continue  # reviewed child result; its parent's acceptance remains separate
        evidence = canonical(w, p.get("verified_evidence", ""))
        verified = bool(
            p.get("acceptance")
            and evidence in w.subjects
            and attested(w, sid, "verified_basis", token, evidence=evidence)
        )
        if status == "done" and verified and not held(p) and not linked.get(sid):
            continue
        state = status
        if held(p):
            state = "held: " + ("unknown effect" if p.get("effect_state") == "unknown" else status)
        elif p.get("worker_milestone") in RESULTS and not reviewed:
            state = "result awaiting owner review"
        elif status == "done" and not verified:
            state = "done claimed; acceptance unverified"
        elif status == "blocked" or p.get("blocked_on"):
            state = "blocked"
        elif (due := _deadline(p.get("review_at"))) is not None and due <= now:
            state = "review due"
        elif p.get("review_at") and due is None:
            state = "invalid review deadline: use ISO datetime with timezone"
        result.append(
            dict(
                target=(w.appearances_of(sid) or [sid])[0],
                title=s.get("title", sid),
                project=p.get("project", ""),
                priority=p.get("priority", "normal"),
                state=state,
                next_action=p.get("next_action", "Record next action"),
                acceptance=p.get("acceptance", ""),
                waiting_on=p.get("waiting_on", ""),
                blocker=p.get("blocked_on", ""),
                resolver=p.get("blocker_owner", ""),
                resume_when=p.get("resume_when", ""),
                review_at=p.get("review_at", ""),
                basis=token,
                reviewed="yes" if reviewed else "no",
                verified="yes" if verified else "no",
                promises="; ".join(linked.get(sid, [])),
            )
        )
    for st, phrase in unlinked:
        result.append(
            dict.fromkeys(FIELDS, "")
            | dict(
                target=st["aid"],
                title=st["what"],
                priority="normal",
                state="promise: " + phrase,
                next_action="Review commitment; retain, confirm or release explicitly",
            )
        )
    return sorted(
        result,
        key=lambda r: (
            -PRIORITY.get(r["priority"], 1),
            r["state"].startswith("held:"),
            r["state"] not in {"result awaiting owner review", "review due"},
            r["target"],
        ),
    )


def packet(w, actor, now=None, limit=8):
    items = rows(w, actor, now)
    lines = [
        "Next steps (canonical tasks and promises; "
        "priority is authored, not inferred from activity).",
        "Receipt is not review; worker completion is not parent verification. "
        "Wake is not permission.",
        "Reconcile new instructions with goal/acceptance/next_action. "
        "Review evidence before claiming done.",
        "Held/unknown work requires its stated resolver; do not retry unknown effects. "
        "No automatic project start.",
    ]
    shown = 0
    for r in items[:limit]:
        start = len(lines)

        def short(k, n=150, row=r):
            text = str(row[k]).replace("\n", " ")
            return text if len(text) <= n else text[:n] + "… [read task]"

        lines.append(
            f"- {short('title', 90)} ({r['target']}) [{r['priority']}; {short('state', 90)}] "
            f"next: {short('next_action')}; acceptance: {short('acceptance') or 'missing'}; "
            f"basis={r['basis']}; reviewed={r['reviewed']}; verified={r['verified']}"
        )
        if r["blocker"] or r["resume_when"]:
            lines.append(
                f"  blocker: {short('blocker')}; resolver: {short('resolver', 70)}; "
                f"resume: {short('resume_when')}"
            )
        if r["waiting_on"]:
            lines.append("  waiting on: " + short("waiting_on", 90))
        if r["promises"]:
            lines.append("  " + short("promises", 180))
        if len("\n".join(lines)) > 5800:
            del lines[start:]
            break
        shown += 1
    lines.append(
        f"{len(items)} open attention items; {len(items) - shown} more. "
        f"Inspect rows nextsteps:{actor}."
    )
    return "\n".join(lines)


def context(w, rid, state, force=False):
    if not enabled(w, rid):
        return ""
    actor = w.nodes[rid]["props"].get("actor", "")
    text = packet(w, actor)
    signature = _hash(text)
    if not force and state.get("next_steps_context") == signature:
        return ""
    state["next_steps_context"] = signature
    return text


def collect(w, rid, state, start, now):
    """Called by news(), saved WITH its inbox/cursor; no independent retry loop.

    Deadlines are one-shot review requests, not stale-activity guesses. Paused,
    cancelled and unknown-effect tasks never wake. Re-arming requires a new
    deadline. Existing relay/quota/connection gates own delivery and retry.
    """
    if not enabled(w, rid):
        return ""
    actor = w.nodes[rid]["props"].get("actor", "")
    seen = state.setdefault("next_steps_due", {})
    events_seen = state.setdefault("next_steps_events", {})
    reasons = []
    for sid, s in w.subjects.items():
        p = s.get("props") or {}
        if (
            s.get("kind") not in KINDS
            or not responsible(w, p, actor)
            or held(p)
            or p.get("status") in CLOSED
        ):
            continue
        date = p.get("review_at", "")
        due = _deadline(date)
        if due is not None and due <= now and seen.get(sid) != date:
            seen[sid] = date
            reasons.append("task review due")
    for e in w.events[start:]:
        if e.get("undone") or e.get("verb") != "prop":
            continue
        card, before, after = task_flow._card(w, e)
        if not card or not responsible(w, after, actor):
            continue
        # Current cancellation/hold takes precedence over old queued results.
        current = props(w, card["id"])
        if held(current):
            continue
        event_number = int(e["id"][1:])
        if event_number <= events_seen.get(card["id"], 0):
            continue
        event_reasons = []
        if before.get("priority") != after.get("priority"):
            event_reasons.append("task priority changed")
        if any(
            before.get(k) != after.get(k) and after.get(k) in values
            for k, values in (
                ("status", {"done", "failed"}),
                ("commission", {"landed", "failed"}),
                ("worker_milestone", RESULTS),
            )
        ):
            event_reasons.append(
                "task ended or result arrived; owner review and unfinished siblings remain"
            )
        if event_reasons:
            events_seen[card["id"]] = event_number
            reasons.extend(event_reasons)
    if not reasons:
        return ""
    # Cursor plus per-task high water marks deduplicate event replay. Deadlines are separate
    # because a clock tick has no native world event. No full task dump is queued.
    return (
        "Next-steps review: "
        + "; ".join(dict.fromkeys(reasons))
        + ". Inspect current tasks before choosing authorized next work."
    )
