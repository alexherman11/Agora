"""dump.py: print a note's text from this worktree's frontier-try (no server), to keep as an 'expected before'.

    python research/window-lab/hud-equal/dump.py <id> [out-file]
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "home-search"))
import apply as hs  # noqa: E402  (text_of)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "home-layout"))
import put  # noqa: E402

w = put.Try("worker-a5994")
t = hs.text_of(w.do(f"read {sys.argv[1]} :3"))
if len(sys.argv) > 2:
    pathlib.Path(sys.argv[2]).write_text(t + "\n", encoding="utf-8")
else:
    print(t)
