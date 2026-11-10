"""Read the current engine's pending behavior on an entirely in-memory fake feed.

This is a diagnosis probe, NOT an acceptance test for a repaired Send contract.
No captures, persisted world, Conversation, network or host actions are used.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "text-desk" / "notation"))
import moo
import roomworld


def main():
    desk, _ = roomworld.build()
    desk._session = "capture-pending-fixture"
    w = desk.world
    w.me = "alex"  # fixture identity only; no live world is loaded
    chat = w.add_subject("chat", "Isolated capture fixture feed")
    w.subjects[chat]["lines"] = []
    w.place(chat, w.root, 0, 0, 100, 100)
    sid = w.add_subject("note", "Isolated pending draft")
    w.subjects[sid]["props"].update(actor="alex", context="", pending="wait-1-1")
    draft = w.place(sid, w.root, 0, 0, 100, 100)
    before = len(w.events)
    desk.cmd_do_knife("append", [chat], {
        "line": "Fixture words", "to": "pike", "captures": "", "context_from": draft,
    })
    lines = w.subjects[chat]["lines"]
    pending = moo.props_of(w, draft)["pending"]
    print(f"CURRENT GAP: pending={pending}; appended_lines={len(lines)}; new_events={len(w.events)-before}")
    assert len(lines) == 1 and pending == "wait-1-1"
    print("Diagnosis reproduced: pending alone does not enforce refusal in the engine. NOT repaired acceptance.")


if __name__ == "__main__":
    main()
