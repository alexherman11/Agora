"""Port of notation/task_next_steps.py onto kernel facts and attributed records.

No task store, polling, execution authority, or automatic completion. Reads use
the caller's visible facts; review claims use the current designated reviewer.
"""
import hashlib
import json
import shlex
from datetime import UTC, datetime

from .kernel import Refused
from .store import GONE

KINDS = {"taskboard-task", "task", "story", "epic"}
HELD = {"paused", "cancelled", "trashed", "permission", "permission-held", "unknown"}
MATERIAL = ("owner", "who", "lead", "asked_by", "goal", "title", "text",
            "acceptance", "request_ref", "parent_task", "worker_milestone",
            "worker_summary", "worker_evidence", "result_ref", "build_run", "build",
            "result_received", "reviewed_commit", "status", "lane")
PRIORITY = {"urgent": 3, "high": 2, "normal": 1, "low": 0,
            "0": 3, "1": 2, "2": 1, "3": 0, "4": 0}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def person(k, ref):
    if k.state.get(ref, "kind") == "agent":
        return k.state.get(ref, "for")
    if k.state.get(ref, "kind") == "person":
        return ref
    matches = [t for t in k.things("person") if k.name(t).casefold() == str(ref).casefold()]
    return matches[0] if len(matches) == 1 else None


def reviewer(k, p):
    return person(k, p.get("lead") or p.get("asked_by") or p.get("owner")
                  or p.get("who") or p.get("for") or p.get("made_by"))


def responsible(k, p, pid):
    return any(person(k, p.get(f)) == pid for f in ("owner", "who", "lead", "asked_by")) or (
        not any(p.get(f) for f in ("owner", "who", "lead", "asked_by"))
        and person(k, p.get("for") or p.get("made_by")) == pid)


def active_records(k):
    undone = k.undone()
    return [r for r in k.log.records if r["seq"] not in undone and not r.get("undoes")]


def basis(k, reader, target):
    """Intent and direct-child result versions; undo restores the previous basis."""
    subjects = [target] + sorted(t for t in k.state.things if
        (p := k.shown(reader, t)) and p.get("kind") in KINDS and p.get("parent_task") == target)
    records = active_records(k)
    values = []
    for t in subjects:
        p = k.shown(reader, t) or {}
        revision = max([r["seq"] for r in records if any(
            f[0] == t and f[1] in MATERIAL and
            k._sees(reader, k.state.get(t, "sees." + f[1], "place"), t)
            for part in r["parts"] for f in part["facts"])] + [0])
        evidence = [(ref, k.state.rev.get(ref)) for f in ("worker_evidence", "result_ref")
                    if (ref := p.get(f)) and k.shown(reader, ref) is not None]
        values.append((t, {f: p.get(f, "") for f in MATERIAL}, revision, evidence))
    return digest(values)


def attested(k, reader, target, p, key, token, evidence=None):
    if p.get(key) != token or not reviewer(k, p):
        return False
    records = active_records(k)
    for r in reversed(records):
        facts = {f[1]: f[3] if len(f) > 3 else None for part in r["parts"]
                 for f in part["facts"] if f[0] == target}
        if key not in facts:
            continue
        if facts[key] != token or person(k, r.get("by")) != reviewer(k, p):
            return False
        if evidence:
            if facts.get("verified_evidence") != evidence or k.shown(reader, evidence) is None:
                return False
            if any(later["seq"] > r["seq"] and any(f[0] == evidence for part in later["parts"]
                   for f in part["facts"]) for later in records):
                return False
        return True
    return False


def deadline(value):
    try:
        d = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return d.timestamp() if d.tzinfo else None
    except (ValueError, TypeError, OverflowError):
        return None


def rows(k, actor, ref, now=None):
    pid = person(k, ref)
    if not pid or k.shown(actor.person, pid) is None:
        raise Refused("nextsteps needs a visible person")
    now = datetime.now(UTC).timestamp() if now is None else now
    result = []
    for t in k.state.things:
        p = k.shown(actor.person, t)
        if not p or p.get("kind") not in KINDS or not responsible(k, p, pid):
            continue
        token = basis(k, actor.person, t)
        reviewed = attested(k, actor.person, t, p, "reviewed_basis", token)
        evidence = p.get("verified_evidence")
        verified = bool(p.get("acceptance") and evidence and
                        attested(k, actor.person, t, p, "verified_basis", token, evidence))
        lane = str(p.get("lane", "")).lower()
        status = lane if lane in HELD | {"done"} else str(p.get("status") or lane or "open").lower()
        held = (status in HELD or p.get("commission") in HELD or p.get("authority") in {"held", "permission"} or
                p.get("effect_state") == "unknown" or p.get("paused") in {"yes", "true", "1"} or
                p.get("approval_required") in {"yes", "true", "1"})
        tracked = bool(p.get("next_action") or p.get("acceptance") or p.get("build"))
        if status in {"cancelled", "trashed"} or (status == "done" and (not tracked or verified)):
            continue
        state = status
        if held:
            state = "held: " + ("unknown effect" if p.get("effect_state") == "unknown" else status)
        elif (p.get("build_phase") in {"received", "reviewed", "landed"} or
              p.get("build") in {"received", "reviewed", "landed"} or
              p.get("worker_milestone") in {"completed", "failed"}) and not reviewed:
            state = "result awaiting owner review"
        elif status == "done" and not verified:
            state = "done claimed; acceptance unverified"
        elif p.get("blocked_on"):
            state = "blocked"
        elif p.get("review_at"):
            due = deadline(p["review_at"])
            if due is None:
                state = "invalid review deadline: use ISO datetime with timezone"
            elif due <= now:
                state = "review due"
        row = {f: p.get(f, "") for f in ("next_action", "acceptance", "waiting_on", "resume_when", "review_at")}
        row.update(target=t, title=p.get("title") or p.get("goal") or t,
                   priority=p.get("priority", "normal"), state=state, basis=token,
                   reviewed="yes" if reviewed else "no", verified="yes" if verified else "no",
                   blocker=p.get("blocked_on", ""), resolver=p.get("blocker_owner", ""),
                   next_action=p.get("next_action") or "Record next action")
        result.append(row)
        k.mark(actor, t, p)
    return sorted(result, key=lambda r: (-PRIORITY.get(str(r["priority"]), 1),
                  r["state"].startswith("held:"), r["state"] not in {"result awaiting owner review", "review due"},
                  r["target"]))


def packet(items, ref):
    """The old bounded packet: whole rows, eight at most, under 6,000 chars."""
    lines = ["Next steps (canonical tasks; priority is authored, not inferred from activity).",
             "Receipt is not review; worker completion is not parent verification. Wake is not permission.",
             "Reconcile new instructions with goal/acceptance/next_action. Review evidence before claiming done.",
             "Held/unknown work requires its stated resolver; do not retry unknown effects. No automatic project start."]
    shown = 0
    for r in items[:8]:
        def short(f, n=150):
            text = str(r.get(f, "")).replace("\n", " ")
            return text if len(text) <= n else text[:n] + "… [read task]"
        line = (f"- {short('title', 90)} ({r['target']}) [{short('priority', 12)}; {short('state', 90)}] "
                f"next: {short('next_action')}; acceptance: {short('acceptance') or 'missing'}; "
                f"basis={r['basis']}; reviewed={r['reviewed']}; verified={r['verified']}")
        for label, field in (("blocker", "blocker"), ("resolver", "resolver"), ("resume", "resume_when"),
                             ("waiting on", "waiting_on"), ("review at", "review_at")):
            if r.get(field):
                line += f"; {label}: {short(field, 90)}"
        if len("\n".join(lines + [line])) > 5700:
            break
        lines.append(line)
        shown += 1
    lines.append(f"{len(items)} open attention items; {len(items) - shown} more. Inspect rows nextsteps:{ref}.")
    return "\n".join(lines)


def change(k, actor, st, entry, tx, group, saw=None):
    """Same five explicit acts as the old world; all changes remain undoable facts."""
    p = k.shown(actor.person, st.target) or {}
    if p.get("kind") not in KINDS:
        raise Refused("this word needs a task card")
    action = entry["bound"].rsplit("-", 1)[-1]
    # The designated lead owns review, even if the worker is a group leader.
    allowed = reviewer(k, p) == actor.person if action in {"review", "verify"} else (
        responsible(k, p, actor.person) or person(k, p.get("made_by")) == actor.person)
    if not allowed:
        raise Refused("only the designated reviewer may attest" if action in {"review", "verify"}
                      else "only the task's owner, lead or asker may maintain it")
    kv = dict(st.kv)
    required = {"next": ("next_action", "acceptance"),
                "revise": ("goal", "acceptance", "request_ref", "next_action"),
                "review": ("basis", "next_action"), "verify": ("basis", "evidence"),
                "followup": ("review_at",)}[action]
    # Retain the old world's positional spelling for ids/quoted task names,
    # as well as the kernel's named settings (which keep multiword values).
    try:
        raw = shlex.split(st.text)
    except ValueError:
        raise Refused("quote task values with matching quotes") from None
    if len(raw) > 2 and raw[1] in {st.target, p.get("title")}:
        positional = [v for v in raw[2:] if "=" not in v]
        for field, value in zip((f for f in required if f not in kv), positional):
            kv[field] = value
    if any(not kv.get(f) for f in required):
        raise Refused("supply " + " ".join(f + "=<value>" for f in required))
    if action in {"review", "verify"} and kv["basis"] != basis(k, actor.person, st.target):
        raise Refused("task changed; read its current nextsteps basis first")
    if action == "verify":
        if not p.get("acceptance") or k.shown(actor.person, kv["evidence"]) is None:
            raise Refused("verification needs acceptance and visible current evidence")
        values = {"verified_basis": kv["basis"], "verified_evidence": kv["evidence"]}
    elif action == "review":
        values = {"reviewed_basis": kv["basis"], "next_action": kv["next_action"], "review_at": GONE}
    else:
        if action == "followup" and deadline(kv["review_at"]) is None:
            raise Refused("review_at needs an ISO datetime with timezone")
        values = {f: kv[f] for f in required}
    k.reaches(actor, "set", p["kind"], target=st.target, fields=values)
    k.fence(actor, st.target, values, saw=saw)
    # Re-attestation must author the whole pair in one record, even where
    # Tx.set would otherwise suppress an unchanged token or evidence reference.
    if action in {"review", "verify"}:
        for f in values:
            if f.endswith("_basis") or f == "verified_evidence":
                tx.set(st.target, f, GONE)
    for f, value in values.items():
        tx.set(st.target, f, value)
    return {"text": f"ok {entry['word']} [r?]"}
