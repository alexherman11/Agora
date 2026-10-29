"""Current Work cards, never a history of builder phases."""
import re

HIDDEN = {"done", "verified", "finished", "completed", "released", "cancelled",
          "trashed", "queued", "backlog", "later", "ready", "waiting", "paused"}
RUNNING = {"working", "reviewing", "landing"}          # a builder's phase (house.who doing=) that is work in progress
STUCK = {"blocked", "recovery-needed"}                 # a builder's phase that waits on someone


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
    names.update(residents)
    workers = {r["task"]: r for r in builders.rows({"use": use}) if r.get("task")}

    def words(value, fallback=""):
        return re.sub(r"\bdk\d+\b", lambda m: names.get(m[0], "the linked item"),
                      " ".join(str(value or fallback).split())) or fallback

    def title(card):
        # a builder's card is titled "Card dk1368 (Bring over …" or "Card dk1332: the reworked …": the card it serves
        # says what the work is, by its own name
        text = " ".join(str(card.get("title") or "").split())
        m = re.match(r"(?i)card\s+(dk\d+)\b", text)
        parent = m[1] if m else card.get("parent_task")
        if parent and parent in names and parent != card["id"]:
            text = names[parent]
        return words(text, "Untitled work").rstrip(" .…(") or "Untitled work"

    def person(value, fallback):
        # a builder is "Claude — Card dk1368 (…": the kind of worker is its calm name
        return words(str(value or "").split(" — ")[0].strip(), fallback)

    def first(text):
        # one calm line: the reason's first sentence (a blocker is often a paragraph)
        return re.split(r"(?<=\.)\s", text, maxsplit=1)[0].rstrip(".")

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
        same_run = bool(worker and worker.get("build_run") and worker["build_run"] == card.get("build_run")
                        and (not card.get("builder") or card["builder"] == worker["name"]))
        doing = str(worker.get("doing", "")).casefold() if same_run else ""
        if doing == "released":
            continue
        holder = card.get("owner") or card.get("who") or ""
        resident = holder if holder in residents else resident_names.get(str(holder).casefold())
        reason = card.get("blocked_on") or card.get("blocker")
        stuck = doing in STUCK
        blocked = bool(reason) or lane == "blocked" or status.startswith("blocked") or stuck
        running = doing in RUNNING
        if not blocked and not running and not (lane == "now" and resident and not card.get("build_run")):
            continue
        if stuck and not reason:
            reason = worker.get("error") or worker.get("now") or card.get("build_detail")
        resolver = card.get("blocker_owner") or card.get("resolver") or (
            (card.get("lead") or holder) if stuck else "")
        result.append(dict(id=card["id"], title=title(card),
                           owner=person(worker["name"] if same_run else holder, "Unassigned"),
                           state="Blocked" if blocked else "Working",
                           blocker=first(words(reason, "Blocker not recorded")) if blocked else "",
                           resolver=person(resolver, "Resolver not recorded") if blocked else "",
                           next_action=words(card.get("next_action")), detail=words(card.get("text"))))
    return sorted(result, key=lambda r: (r["state"] != "Blocked", r["title"].casefold(), r["id"]))
