"""Steward lines: let signed-out visitors say the board's see-words its lens watches (may=anyone). Each reading still
filters by who-sees, so a visitor gets only what is seen-by everyone. Run through steward_session.sh. Prints what
changed; `--may members` puts them back. Claude, 5 Nov 2026 (src/community/board/PUBLIC-HOST.md).
"""
import argparse
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parents[2] / "agora"
sys.path.insert(0, str(LAB))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--door", required=True)
    ap.add_argument("--token-file", required=True)
    ap.add_argument("--words", default="board.badges board.feed board.events board.catch-up board.queue board.search "
                                       "board.asks forgotten map.layers")
    ap.add_argument("--may", default="anyone")
    a = ap.parse_args()
    from painter.install import taskboard
    door = taskboard.Door(a.door, Path(a.token_file).read_text(encoding="utf-8").strip())
    want = set(a.words.split())
    for e in door.rows("word"):
        name = e.get("bound") or e.get("word") or e.get("name")
        if name in want and not e.get("in"):
            if e.get("may") == a.may:
                print("already", name, e["id"])
                continue
            door.say("look " + e["id"])
            try:
                print("word-set", name, e["id"], door.say(f"word-set {e['id']} may={a.may}")["text"][:100])
            except RuntimeError as exc:
                print("refused", name, e["id"], str(exc)[:200])


if __name__ == "__main__":
    main()
