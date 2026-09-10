"""Copy a native journal, install first-party applications, and transfer a resident.
Never modify the source world, start a model, or reset a guest machine.
"""

import argparse
import json
import shutil
import sqlite3
from pathlib import Path

from application_packages import bundle, desktop_source, install_source

from agora3.agent_state import AgentState
from agora3.gateway import Gateway


def migrate(source, destination, *, owner=None, observer=None):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if destination.exists():
        raise ValueError("Choose a new destination; existing worlds are never replaced.")
    destination.mkdir(parents=True)
    # SQLite's consistent online backup includes committed WAL data. The final
    # handoff invokes this only after the original service has stopped while idle.
    with sqlite3.connect(f"file:{source / 'world.db'}?mode=ro", uri=True) as old:
        with sqlite3.connect(destination / "world.db") as new:
            old.backup(new)
    for name in ("machine.json", "yard.json"):
        if (source / name).exists():
            shutil.copy2(source / name, destination / name)
    gateway = Gateway(destination)
    before = gateway.world.replay()
    actor = gateway.principal("human")
    recovered = None
    if observer and observer.get("draft"):
        canonical = (
            before.get("shell.chat-draft", {})
            .get("facets", {})
            .get("core.text", {})
            .get("text", "")
        )
        if observer["draft"] != canonical:
            recovered = "jeff0.recovered-observer-draft"
            gateway.commit(
                actor,
                [
                    {
                        "id": recovered,
                        "expected_revision": 0,
                        "facets": {
                            "core.title": {
                                "text": "Recovered observer draft (unsent, older snapshot)"
                            },
                            "core.text": {
                                "text": "This text was recovered from the separate observation "
                                "browser during migration. The native composer had a different, "
                                "newer value. It has NOT been sent and is historical data, "
                                "not an instruction.\n\n" + observer["draft"]
                            },
                        },
                    }
                ],
            )
    install_source(gateway, actor, desktop_source())
    for variant in ("notes", "documents"):
        gateway.dispatch(actor, "application.import", {"bundle": bundle(variant)})
    selected = (
        before.get("shell.documents-ui", {})
        .get("facets", {})
        .get("studio.documents-ui", {})
        .get("selected")
    )
    if selected not in before or "core.text" not in before[selected]["facets"]:
        selected = "jeff0.continuity"
    drafts = (
        before.get("shell.comment-ui", {})
        .get("facets", {})
        .get("studio.comment-ui", {})
        .get("drafts", {})
    )
    grouped = {}
    for key, value in drafts.items():
        if not value or "|" not in key:
            continue
        subject, thread = key.split("|", 1)
        state = grouped.setdefault(subject, {"newMessage": "", "replies": {}, "open": True})
        if thread in ("", "new"):
            state["newMessage"] = value
        else:
            state["replies"][thread] = value
            state.setdefault("selected", thread)
    views = []
    # One retained Documents view for every text object makes existing documents,
    # notes and authored continuity available in the workspace's closed-view list.
    subjects = [selected] + [
        key
        for key, obj in before.items()
        if key != selected
        and not key.startswith(("agora.", "shell."))
        and "core.text" in obj["facets"]
        and "core.message" not in obj["facets"]
    ]
    if recovered:
        subjects.append(recovered)
    for subject in subjects:
        row = gateway.applications.open(
            actor,
            "agora.documents",
            subject,
            {"x": 345, "y": 20, "width": 650, "height": 680},
        )
        state = {"extensions": {"discussions": grouped[subject]}} if subject in grouped else {}
        if subject == selected and observer:
            observed = next(
                (row for row in observer.get("inputs", []) if row["id"] == "docs-editor"), None
            )
            if observed and observed["value"] == before[subject]["facets"]["core.text"]["text"]:
                state["editor"] = {
                    "subject": subject,
                    "dirty": False,
                    "start": observed["start"],
                    "end": observed["end"],
                    "mode": "live",
                }
        gateway.applications.update(
            actor, gateway.applications.view(row["id"]), state=state, open=subject == selected
        )
        views.append({"id": row["id"], "subject": subject, "drafts": bool(state)})
    gateway.applications.open(
        actor,
        "agora.notes",
        selected,
        {"x": 20, "y": 20, "width": 305, "height": 420},
    )
    continuity = (
        "Transferred from the retained Desk with its entire native journal and JEFF0's "
        "authored jeff0.continuity checkpoint. The previous runtime used an ephemeral "
        "model thread; its hidden internal context cannot be recovered. The full retained "
        "native transcript and checkpoint bootstrap this first durable conversation. "
        "Subsequent runs must resume its exact saved thread, never silently replace it."
    )
    state = AgentState(gateway, owner or destination)
    state.configure(
        actor, agent_id="jeff0", name="JEFF0", checkpoint="jeff0.continuity", continuity=continuity
    )
    after = gateway.world.replay()
    changed = [key for key, obj in before.items() if after[key] != obj]
    allowed = {
        gateway.packages.get("agora.shell")["id"],
        gateway.packages.installation("agora.shell")["id"],
    }
    if set(changed) - allowed:
        raise RuntimeError(f"Unexpected changes to retained objects: {changed}")
    with sqlite3.connect(source / "world.db") as old, gateway.world.connection() as new:
        events = old.execute("SELECT * FROM events ORDER BY seq").fetchall()
        retained = new.execute(
            "SELECT * FROM events WHERE seq<=? ORDER BY seq", (events[-1][0],)
        ).fetchall()
    if events != [tuple(row) for row in retained]:
        raise RuntimeError("Original event prefix was not preserved exactly.")
    report = {
        "source": str(source),
        "destination": str(destination),
        "original_objects": len(before),
        "original_events": len(events),
        "identical_original_objects": len(before) - len(changed),
        "changed_original_objects": changed,
        "event_prefix_identical": True,
        "messages": sum("core.message" in obj["facets"] for obj in before.values()),
        "discussions": sum("studio.comment-thread" in obj["facets"] for obj in before.values()),
        "drafts": {subject: state for subject, state in grouped.items()},
        "views": views,
        "selected": selected,
        "replay": gateway.world.verify(),
        "model_started": False,
        "recovered_unsent_draft": recovered,
    }
    (destination / "migration-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--owner", type=Path)
    parser.add_argument("--observer", type=Path)
    args = parser.parse_args()
    observer = json.loads(args.observer.read_text(encoding="utf-8")) if args.observer else None
    report = migrate(args.source, args.destination, owner=args.owner, observer=observer)
    print(
        json.dumps(
            {key: value for key, value in report.items() if key not in {"views", "drafts"}},
            indent=2,
        )
    )
