"""EDITING A MODULE (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
A module is a seam to something outside the kernel (a model provider, git, Twitch, the media session, a map server) and
turns it into world facts and words. What the world does with them (who is told, when, in what words, how it looks)
belongs in rules, lenses and this module's settings thing, read at each use. Names (JEFF, Alex), ids (dk...), models,
counts, timeouts and message text in this file are debt: move them to settings when you touch them, and never add more.

Current Work cards, never a history of builder phases.

What is the world's (4 Nov): which lanes hide, the order of the three states and every word Work shows are facts on
the `work-settings` thing (made by the Work installer from DEFAULTS, then Alex's to change), read at each call. A fact
missing there falls back to DEFAULTS. What stays here is the join the world can't say yet: cards with the House's own
worker runs, which live only in the House."""
import re

DEFAULTS = {
    "hide_lanes": "done,verified,finished,completed,released,cancelled,trashed,queued,backlog,later,ready,waiting,paused",
    "order": "blocked,waiting,working",
    "word_blocked": "Blocked", "word_waiting": "Waiting", "word_working": "Working",
    # Alex, 3 Nov: finished results sat for days because nothing listed them; a stopped worker's result is current work
    "word_received": "Finished, waiting on its review", "word_reviewed": "Checks passed, waiting to land",
    "word_since": "since", "word_untitled": "Untitled work", "word_someone": "Someone",
    "word_linked": "the linked item", "word_unassigned": "Unassigned",
    "word_no_blocker": "Blocker not recorded", "word_no_resolver": "Resolver not recorded",
}
HIDDEN = set(DEFAULTS["hide_lanes"].split(","))
RUNNING = {"working", "reviewing", "landing"}          # a builder's phase (house.who doing=) that is work in progress
STUCK = {"blocked", "recovery-needed"}                 # a builder's phase that waits on someone
WAITING = ("received", "reviewed")                     # a stopped worker's result, waiting on the one in charge


def settings(module, read):
    """DEFAULTS, then the facts of the work-settings thing made by the House's own person (not anyone's)."""
    whose = {(getattr(module, "hello", None) or {}).get(k) for k in ("for", "owner")} - {None, ""}
    out = dict(DEFAULTS)
    for row in read("rows work-settings"):
        if row.get("kind") == "work-settings" and (row.get("made_by") in whose or row.get("for") in whose):
            out.update({k: str(v) for k, v in row.items() if k in DEFAULTS and str(v).strip()})
            break
    return out


def rows(module, agents, builders, use):
    def read(line):
        reply = module.see(line, use=use)
        if reply.get("refused") or reply.get("ok") is False:
            raise RuntimeError(reply.get("refused") or reply.get("text") or "Current work could not be read")
        return reply.get("rows") or []

    cards = read("rows taskboard-task")
    S = settings(module, read)
    hidden = {x.strip().casefold() for x in S["hide_lanes"].split(",") if x.strip()}
    order = {x.strip().casefold(): n for n, x in enumerate(S["order"].split(","))}
    names = {p["id"]: p.get("title") or S["word_untitled"] for p in cards}
    names.update({p["id"]: p.get("name") or S["word_someone"] for p in read("rows person")})
    residents = {a.person: a.name for a in agents.values()}
    resident_names = {name.casefold(): pid for pid, name in residents.items()}
    names.update(residents)
    workers = {r["task"]: r for r in builders.rows({"use": use}) if r.get("task")}

    def words(value, fallback=""):
        return re.sub(r"\bdk\d+\b", lambda m: names.get(m[0], S["word_linked"]),
                      " ".join(str(value or fallback).split())) or fallback

    def title(card):
        # a builder's card is titled "Card dk1368 (Bring over …" or "Card dk1332: the reworked …": the card it serves
        # says what the work is, by its own name
        text = " ".join(str(card.get("title") or "").split())
        m = re.match(r"(?i)card\s+(dk\d+)\b", text)
        parent = m[1] if m else card.get("parent_task")
        if parent and parent in names and parent != card["id"]:
            text = names[parent]
        return words(text, S["word_untitled"]).rstrip(" .…(") or S["word_untitled"]

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
        if lane in hidden or status in hidden or any(
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
        waiting = doing in WAITING and not blocked
        if not blocked and not running and not waiting and not (lane == "now" and resident and not card.get("build_run")):
            continue
        if waiting:
            since = str(worker.get("awaiting") or worker.get("last_turn") or "")[:10]
            reason = S["word_" + doing] + (f" {S['word_since']} {since}" if since else "")
        if stuck and not reason:
            reason = worker.get("error") or worker.get("now") or card.get("build_detail")
        resolver = card.get("blocker_owner") or card.get("resolver") or (
            (card.get("lead") or holder) if stuck else "")
        if waiting:
            resolver = worker.get("owner_name") or card.get("lead") or holder
        state = "blocked" if blocked else "waiting" if waiting else "working"
        result.append(dict(id=card["id"], title=title(card),
                           owner=person(worker["name"] if same_run else holder, S["word_unassigned"]),
                           state=S["word_" + state], rank=order.get(state, len(order)),
                           blocker=first(words(reason, S["word_no_blocker"])) if blocked or waiting else "",
                           resolver=person(resolver, S["word_no_resolver"]) if blocked or waiting else "",
                           next_action=words(card.get("next_action")), detail=words(card.get("text"))))
    result.sort(key=lambda r: (r.pop("rank"), r["title"].casefold(), r["id"]))
    return result
