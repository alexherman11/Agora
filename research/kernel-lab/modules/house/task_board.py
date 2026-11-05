"""Read-only join for house.board: visible cards plus live House execution.

Missing word: house.board exposes the live process seam so a world lens can
combine tasks and work. No claims, scheduling, admission, or new authority.
"""
import re

DEFAULTS = {
    "board_order": "running,queued,blocked,review,activation,done,cancelled",
    "board_running": "Running", "board_queued": "Queued", "board_blocked": "Blocked",
    "board_review": "Waiting on review", "board_activation": "Waiting on switch-on",
    "board_done": "Done", "board_cancelled": "Cancelled",
    "board_coordinator": "Coordinator", "board_unassigned": "Unassigned",
    "board_no_cause": "Blocker not recorded",
    "board_resolve": "Resolver to record the authorized next step",
    "board_scope": "Assignment exceeds the governing scope",
    "board_scope_next": "Coordinator to retract the assignment or arrange an authorized handoff",
    "board_unknown": "Effect outcome unknown; inspect receipts before any retry",
    "board_hold": "Work is held",
    "board_review_next": "Review the received result",
    "board_activation_next": "Check the reviewed result and its switch-on evidence",
}
PRIORITY = {"urgent": 0, "high": 1, "normal": 2, "low": 3,
            "0": 0, "1": 1, "2": 2, "3": 3, "4": 4}
TRUE = {"yes", "true", "1"}
DONE = {"done", "completed", "verified", "finished"}


def rows(module, agents, builders, use):
    def read(line):
        reply = module.see(line, use=use)
        if reply.get("refused") or reply.get("ok") is False:
            raise RuntimeError(reply.get("refused") or reply.get("text") or "Task board unavailable")
        return reply.get("rows") or []

    cards, people = read("rows taskboard-task"), read("rows person")
    settings = dict(DEFAULTS)
    principals = {(getattr(module, "hello", None) or {}).get(k) for k in ("for", "owner")} - {None, ""}
    for setting in read("rows work-settings"):
        if setting.get("kind") == "work-settings" and (
                setting.get("made_by") in principals or setting.get("for") in principals):
            settings.update({k: str(v) for k, v in setting.items() if k in DEFAULTS and str(v).strip()})
            break
    order = {key.strip(): i for i, key in enumerate(settings["board_order"].split(","))}
    names = {p["id"]: p.get("name") or settings["board_unassigned"] for p in people}
    names.update({c["id"]: c.get("title") or c.get("goal") or "Untitled task" for c in cards})
    by_name = {p.get("name", "").casefold(): p["id"] for p in people}
    visible_people = {p["id"] for p in people}
    coordinator = next((a.person for a in agents.values()
                        if getattr(a, "cfg", {}).get("role") == "general-manager"),
                       settings["board_coordinator"])

    def text(value, fallback=""):
        return re.sub(r"\bdk\d+\b", lambda m: names.get(m[0], "the linked item"),
                      " ".join(str(value or fallback).split()))

    def person_id(value):
        return value if value in visible_people else by_name.get(str(value or "").casefold(), "")

    # rows() applies caller visibility before any process data is joined.
    workers = {w["task"]: w for w in builders.rows({"use": use}) if w.get("task")}
    result = []
    for card in cards:
        target = card["id"]
        worker = workers.get(target)
        same = bool(worker and worker.get("build_run") and worker["build_run"] == card.get("build_run")
                    and (not card.get("builder") or worker["name"] == card["builder"]))
        worker = worker if same else None
        phase = worker.get("doing", "") if worker else card.get("build_phase", "")
        lead = card.get("lead") or card.get("owner") or card.get("who")
        resolver = card.get("blocker_owner") or card.get("resolver") or lead or coordinator
        next_action = card.get("next_action") or ""
        lane, status = (str(card.get(f, "")).strip().casefold() for f in ("lane", "status"))
        scope = str(card.get("scope_blocked", "")).casefold() in TRUE
        assignment = person_id(card.get("current_executor") or card.get("owner") or card.get("who"))
        scope_cause = ""
        if any(a.person == assignment and getattr(a, "cfg", {}).get("role") == "manager"
               for a in agents.values()):
            import manager
            try:
                manager.permit(builders, assignment, target)
            except RuntimeError as exc:
                scope, scope_cause = True, str(exc)
        unknown = card.get("effect_state") == "unknown"
        held = unknown or any(str(card.get(k, "")).casefold() in TRUE for k in
                              ("paused", "held", "task_held", "approval_required")) or any(
            str(card.get(k, "")).casefold() in {"held", "permission", "permission-held", "unknown", "paused"}
            for k in ("authority", "commission", "status", "lane"))
        cause = card.get("blocked_on") or card.get("blocker")
        if scope:
            cause = card.get("scope_reason") or scope_cause or settings["board_scope"]
            resolver = card.get("scope_resolver") or coordinator
            next_action = settings["board_scope_next"]
        elif unknown:
            cause = settings["board_unknown"]
        elif held:
            cause = cause or settings["board_hold"]
        elif phase in {"blocked", "recovery-needed", "uncertain"}:
            cause = cause or (worker or {}).get("error") or (worker or {}).get("now") or card.get("build_detail")

        # A saved phase, owner or historical PID never proves execution.
        # Existing working phase is set only by authenticated adapter init/turn-start.
        execution, executor = {}, ""
        child = getattr(builders, "children", {}).get(target) if worker else None
        state = getattr(builders, "states", {}).get(target, {}) if worker else {}
        if (worker and phase == "working" and state.get("phase") == "working"
                and child and state.get("run") == card.get("build_run")
                and state.get("session") and state.get("turn_started") and child.alive()
                and (not state.get("result_received") or state["turn_started"] > state["result_received"])
                and state.get("pid") == getattr(getattr(child, "proc", None), "pid", None)
                and state.get("pid")):
            execution = dict(kind="authenticated-worker-turn", run=state["run"],
                             started=state["turn_started"])
            executor = worker["name"].split(" \u2014 ")[0]
        # Optional structured turn evidence is consumed, never manufactured from cfg.task.
        for agent in agents.values():
            turn = getattr(agent, "turn", {})
            claim = card.get("executor_claim")
            if (claim and card.get("current_executor") == agent.person
                    and turn.get("task") == target and turn.get("task_claim") == claim
                    and turn.get("execution_started") and getattr(agent, "busy", False)
                    and getattr(agent, "child", None) and agent.child.alive()):
                executor = agent.name
                execution = dict(kind="resident-turn", claim=claim, started=turn["execution_started"])
                break

        blocked = cause or held or scope or lane == "blocked" or status.startswith("blocked") or phase in {
            "blocked", "recovery-needed", "uncertain"}
        if blocked:
            key = "blocked"
            cause = cause or settings["board_no_cause"]
            next_action = next_action or settings["board_resolve"]
        elif status in {"cancelled", "trashed"} or lane in {"cancelled", "trashed"} or str(
                card.get("cancelled", "")).casefold() in TRUE:
            key = "cancelled"
        elif execution:
            key = "running"
        elif lane in DONE or status in DONE:
            key = "done"  # Authored board history; not an independent acceptance attestation.
        elif phase in {"received", "reviewed", "reviewing"}:
            key = "review"
            resolver = (worker or {}).get("owner_name") or lead or coordinator
            next_action = next_action or settings["board_review_next"]
        elif phase in {"landed", "landing"}:
            # Source landing alone says nothing about a live deployment.
            key = "activation"
            next_action = next_action or settings["board_activation_next"]
        else:
            key = "queued"
        title = card.get("title") or card.get("goal") or "Untitled task"
        parent = re.match(r"(?i)card\s+(dk\d+)\b", title)
        if parent and parent[1] in names and parent[1] != target:
            title = names[parent[1]]
        result.append(dict(
            id=target, rev=card.get("rev"), title=text(title), state=settings["board_" + key], state_key=key,
            priority=card.get("priority", "normal"), lead=text(lead, settings["board_unassigned"]),
            lead_id=person_id(lead), owner=text(executor or lead, settings["board_unassigned"]),
            executor=text(executor) if key == "running" else "",
            execution=execution if key == "running" else {},
            blocker=text(cause) if key == "blocked" else "",
            resolver=text(resolver) if key in {"blocked", "review", "activation"} else "",
            resolver_id=person_id(resolver), next_action=text(next_action),
            detail=text(card.get("text")), acceptance=text(card.get("acceptance")),
            delivery=phase if key in {"review", "activation"} else "",
        ))
    return sorted(result, key=lambda r: (order.get(r["state_key"], len(order)),
                  PRIORITY.get(str(r["priority"]).casefold(), 2), r["title"].casefold(), r["id"]))
