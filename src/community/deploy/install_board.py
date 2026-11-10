"""Install the Seabright board into a fresh world through an authenticated door, in the order the desktop's installers
were run: board world (channels, kinds, orderings), the component gallery, the board's UI and widget, the map, Asks &
offers, Documents, then the activation (grants, nested views). Every step is the existing installer, unchanged, and each
checks what is there first, so running it again is safe.

    python src/community/deploy/install_board.py --door http://127.0.0.1:<port> --token-file <file>

The token file holds a session token for the steward (a loopback dev session while installing); it is read, not printed.
Claude, 5 Nov 2026, for the Seabright public host (src/community/board/PUBLIC-HOST.md).
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOARD = HERE.parent / "board"
LAB = HERE.parents[1] / "agora"
sys.path[:0] = [str(BOARD), str(LAB), str(LAB / "apps" / "map")]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--door", required=True)
    ap.add_argument("--token-file", required=True)
    ap.add_argument("--only", default="", help="comma-separated steps to run (default: all)")
    a = ap.parse_args()
    from painter.install import taskboard, install as install_gallery
    from install import install as install_world
    from ui_install import install_ui
    door = taskboard.Door(a.door, Path(a.token_file).read_text(encoding="utf-8").strip())
    see = lambda line: door.request("/see", dict(line=line))          # noqa: E731
    steps = []

    def world():
        if not door.rows("board-settings"):
            return install_world(door.say, see)
        return "already"
    steps.append(("world", world))
    steps.append(("gallery", lambda: list(install_gallery(door, board=False))))
    steps.append(("ui", lambda: install_ui(door)))

    def map_():
        import importlib.util
        spec = importlib.util.spec_from_file_location("map_install", LAB / "apps/map/install.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m.install(door)
    steps.append(("map", map_))

    def asks():
        from asks_install import install_asks
        return install_asks(door)
    steps.append(("asks", asks))

    def documents():
        from documents_install import install_documents
        return install_documents(door)
    steps.append(("documents", documents))

    def activate():
        from board_activate import activate as act
        return act(door)
    steps.append(("activate", activate))

    only = {s for s in a.only.split(",") if s}
    for name, fn in steps:
        if only and name not in only:
            continue
        print(f"== {name}", flush=True)
        out = fn()
        print(json.dumps(out, default=str)[:600], flush=True)
    print("INSTALLED", flush=True)


if __name__ == "__main__":
    main()
