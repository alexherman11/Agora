"""Read-only bounded event-metadata audit. No event prose or model/house effects."""
import collections
import hashlib
import json
from pathlib import Path
import sys
import sqlite3
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/text-desk-lab/notation"))
import export_docs
import kept
import rooms
import task_flow
from replay import POLICY, modules


def digest(value):
    return hashlib.sha256(str(value or "").encode()).hexdigest()


def capture(w, low=26500, high=27216):
    rows = []
    for e in w.events:
        number = int(e["id"][1:])
        if not low <= number <= high:
            continue
        card, old, props = task_flow._card(w, e) if e.get("verb") in {
            "create", "prop", "put"} else (None, {}, {})
        notices = task_flow.notices(w, e)
        receipt = rooms.knock_of(w, e["id"])
        row = {
            "event": e["id"], "at": e.get("at"), "by": e.get("by"),
            "verb": e.get("verb"), "target": e.get("target"),
            "via": e.get("via"), "cause": e.get("cause"),
            "arg_keys": sorted((e.get("args") or {}).keys()),
            "transition_routes": [{"recipient": n["recipient"], "kinds": n["kinds"]}
                                  for n in notices],
            "knock_recipients": sorted((receipt or {}).get("args") or {}),
            "other_routes": rooms.reached(w, e) if not notices else {},
            "question": (e.get("args") or {}).get("mark") == "ask",
            "human": rooms.kind_of(w, str(e.get("by") or "").split("/")[0]) == "person",
        }
        if card:
            row["task"] = card.get("id") or e.get("target")
            row["snapshot_missing"] = bool((e.get("undo") or {}).get("kept")
                                          and kept.copy_of(e) is None)
            safe = {"commission", "status", "worker_milestone", "owner", "lead",
                    "asked_by", "blocker_owner", "accepted_by", "waiting_on"}
            # Arbitrary prose stays out of the captured fixture; stable hashes
            # still distinguish material blocker changes without interpreting it.
            opaque = {"blocked_on", "resume_when", "worker_summary", "worker_evidence"}
            row["old"] = {k: v for k, v in old.items() if k in safe}
            row["new"] = {k: v for k, v in props.items() if k in safe}
            row["old_hashes"] = {k: digest(old.get(k)) for k in opaque}
            row["new_hashes"] = {k: digest(props.get(k)) for k in opaque}
            row["present"] = sorted(k for k in opaque if props.get(k))
            row["creator"] = task_flow._creator(w, e, card)
            row["resident_bindings"] = {
                value: list(task_flow._residents(w, value))
                for p in (old, props) for k, value in p.items()
                if k in {"owner", "lead", "asked_by", "blocker_owner"} and value
            }
        rows.append(row)
    # Evaluate candidate routes against exactly the same loaded copy and archived
    # snapshots, never writing it. Explicit/comment/dependency routing is measured
    # independently rather than assumed unchanged from transition-only counts.
    candidate = modules()
    w.subjects["audit-only-policy"] = {"props": POLICY}
    try:
        with patch.dict(sys.modules, {"task_flow": candidate["task_flow"]}):
            events = [e for e in w.events if low <= int(e["id"][1:]) <= high]
            for row, event in zip(rows, events):
                notices = candidate["task_flow"].notices(w, event)
                row["candidate_routes"] = [
                    {"recipient": n["recipient"], "kinds": n["kinds"]} for n in notices]
                row["candidate_other_routes"] = (
                    candidate["rooms"].reached(w, event) if not notices else {})
    finally:
        del w.subjects["audit-only-policy"]
    return rows


def main():
    desk = export_docs.load("frontier-try")
    # The copied world keeps references to the source's archived event snapshots.
    # Reuse kept.copy_of, but make its SQLite connection explicitly read-only.
    main = ROOT.parent.parent if ROOT.parent.name == ".worktrees" else ROOT
    connect = sqlite3.connect
    def readonly(path, **kwargs):
        return connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True, **kwargs)
    with patch.object(kept, "SESSIONS", main / "research/text-desk-lab/notation/sessions"), \
         patch.object(kept.sqlite3, "connect", readonly):
        rows = capture(desk.world)
    out = Path(__file__).with_name("captured-metadata.json")
    out.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    routes = [r for r in rows if r["transition_routes"]]
    print(json.dumps({
        "interval": ["e26500", "e27216"], "events": len(rows),
        "copy_at": desk.world.events[-1]["id"],
        "transition_events": len(routes),
        "transition_recipient_notices": sum(len(r["transition_routes"]) for r in routes),
        "kinds": dict(collections.Counter(k for r in routes for n in r["transition_routes"]
                                           for k in n["kinds"])),
        "recipients": dict(collections.Counter(n["recipient"] for r in routes
                                                for n in r["transition_routes"])),
        "snapshot_missing_task_events": sum(r.get("snapshot_missing", False) for r in rows),
        "recorded_knock_events": sum(bool(r["knock_recipients"]) for r in rows),
        "fixture_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
    }, indent=2))


if __name__ == "__main__":
    main()
