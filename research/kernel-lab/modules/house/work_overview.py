"""Current Work cards, never a history of builder phases."""
import re

HIDDEN = {"done", "verified", "finished", "completed", "released", "cancelled",
          "trashed", "queued", "backlog", "later", "ready", "waiting", "paused"}


def rows(module, agents, builders, use):
    def read(line):
        reply = module.see(line, use=use)
        if reply.get("refused") or reply.get("ok") is False:
            raise RuntimeError(reply.get("refused") or reply.get("text") or "Current work could not be read")
        return reply.get("rows") or []

    cards = read("rows taskboard-task")
    names = {p["id"]: p.get("title") or "Untitled work" for p in cards}
    names.update({p["id"]: p.get("name") or "Someone" for p in read("rows person")})
    residents = {a.person: a.name for a in agents.values()}
    resident_names = {name.casefold(): pid for pid, name in residents.items()}
    workers = {r["task"]: r for r in builders.rows({"use": use})}

    def words(value, fallback=""):
        return re.sub(r"\bdk\d+\b", lambda m: names.get(m[0], "the linked item"),
                      " ".join(str(value or fallback).split()))

    result = []
    for card in cards:
        lane = str(card.get("lane", "")).strip().casefold()
        status = str(card.get("status", "")).strip().casefold()
        if lane in HIDDEN or status in HIDDEN or any(
            str(card.get(f, "")).casefold() in {"yes", "true", "1"}
            for f in ("released", "cancelled", "paused")
        ):
            continue
        worker = workers.get(card["id"])
        same_run = bool(worker and worker.get("build_run") and worker["build_run"] == card.get("build_run"))
        if same_run and worker["doing"] == "released":
            continue
        holder = card.get("owner") or card.get("who") or ""
        resident = holder if holder in residents else resident_names.get(str(holder).casefold())
        blocked = bool(card.get("blocked_on")) or "blocked" in {lane, status}
        running = bool(worker and worker["doing"] in {"working", "reviewing", "landing"}
                       and same_run
                       and (not card.get("builder") or card["builder"] == worker["name"])
                       and card.get("build") in {"building", "reviewing", "landing"})
        if not blocked and not running and not (lane == "now" and resident and not card.get("build_run")):
            continue
        result.append(dict(id=card["id"], title=words(card.get("title"), "Untitled work"),
                           owner=words(worker["name"] if running else holder, "Unassigned"),
                           state="Blocked" if blocked else "Working",
                           blocker=words(card.get("blocked_on"), "Blocker not recorded") if blocked else "",
                           resolver=words(card.get("blocker_owner"), "Resolver not recorded") if blocked else "",
                           next_action=words(card.get("next_action")), detail=words(card.get("text"))))
    return sorted(result, key=lambda r: (r["state"] != "Blocked", r["title"].casefold(), r["id"]))
