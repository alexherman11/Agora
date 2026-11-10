"""Steward lines for the Seabright public world, said through an authenticated door (run by steward_session.sh while
the public kernel is stopped). Safe to run again: each step looks first.

1. reports modules whose run was resolved to the system python (load_genesis resolves symlinks; `set` cannot change a
   module's run, so seabright-kernel.service sets PYTHONPATH to the venv's site-packages for them);
2. visitors on, and `seen-by <thing> everyone` for the public channels' groups (--public-channels) and for every
   thing of the kinds a painter needs to paint the board (--paint-kinds). Chats stay members-only.

Claude, 5 Nov 2026 (research/community-app/board/PUBLIC-HOST.md).
"""
import argparse
import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parents[2] / "kernel-lab"
sys.path.insert(0, str(LAB))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--door", required=True)
    ap.add_argument("--token-file", required=True)
    ap.add_argument("--python", required=True)
    ap.add_argument("--public-channels", default="Announcements,Meetings & events")
    ap.add_argument("--paint-kinds", default="lens component part-style style widget button kind board-channel "
                                             "board-order board-settings theme")
    a = ap.parse_args()
    from painter.install import taskboard, Q
    door = taskboard.Door(a.door, Path(a.token_file).read_text(encoding="utf-8").strip())

    for m in door.rows("module"):
        run = m.get("run")
        try:
            words = json.loads(run) if isinstance(run, str) else list(run or [])
        except ValueError:
            continue
        if words and words[0] != a.python and Path(words[0]).name.startswith("python"):
            words[0] = a.python
            # a module's run cannot be changed by set (only made things can); the kernel unit's PYTHONPATH gives the
            # system python the venv's packages instead. Reported here so it is seen.
            print("module", m.get("name"), "runs", run[:80])

    print("visitors", door.say("visitors on")["text"][:160])
    targets = []
    for ch in door.rows("board-channel"):
        if ch.get("title") in a.public_channels.split(","):
            targets.append(ch["group"])
    for kind in a.paint_kinds.split():
        try:
            targets += [r["id"] for r in door.rows(kind)]
        except RuntimeError as exc:
            print("skip kind", kind, str(exc)[:100])
    done = 0
    for t in dict.fromkeys(targets):
        try:
            door.say("seen-by " + t + " everyone")
            done += 1
        except RuntimeError as exc:
            print("seen-by refused", t, str(exc)[:160])
    print("seen-by everyone:", done, "of", len(set(targets)))


if __name__ == "__main__":
    main()
