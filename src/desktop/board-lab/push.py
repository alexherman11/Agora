"""push (a6010): put the board directions into a world, as notes in the Home base room (f5204).

    python src/desktop/board-lab/push.py try [lens files ...]      into frontier-try, through explore.py

The style direction-board is the world's home-style followed by this folder's nb.style-roles (a placed lens paints in
its placer's style, so round 3 adds the roles to home-style itself; until then a direction is looked at as the root
lens, in its own style). Each <name>.lens becomes the note titled <name>, tagged lens, style=direction-board; an
existing note of that title in the room is rewritten. The try world is recopied at every landing: push again.
(After directions/push.py, a5534.)
"""
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
LAB = HERE.parents[1] / "text-desk" / "notation"
ROOM = "f5204"


def quote(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def explore(lines, world="frontier-try"):
    r = subprocess.run([sys.executable, str(LAB / "explore.py"), world, "--as", "worker-a6010", "--whole"],
                       input="\n".join(lines) + "\n", capture_output=True, text=True, encoding="utf-8", cwd=LAB)
    return r.stdout + r.stderr


def in_room(text):
    return {m.group(2): m.group(1) for m in re.finditer(r'^\s+(a\d+) note "([^"]+)"', text, re.M)}


def body_of(text):
    """The words of a `read` between its two --- lines."""
    m = re.search(r"^---\n(.*?)\n---$", text, re.M | re.S)
    return m.group(1) if m else None


def put(title, tags, text, extra=""):
    have = in_room(explore([f"look {ROOM} :2"]))
    if title in have:
        lines = [f"look {have[title]}", f"do rewrite {have[title]} text={quote(text)}"]
    else:
        lines = [f"look {ROOM}", f"do create {ROOM} kind=note title={quote(title)} tags={tags}{extra} text={quote(text)}"]
    out = explore(lines)
    print(title + ": " + " | ".join(l for l in out.splitlines() if re.match(r"^(ok |ERR|.*refus)", l))[:600])


def main():
    how, files = sys.argv[1], sys.argv[2:] or sorted(str(p) for p in HERE.glob("direction-board-*.lens"))
    assert how == "try", "only the try world, for round 1"
    home = body_of(explore(["read home-style"]))
    if not home:
        sys.exit("home-style not read")
    home = "\n".join(l for l in home.splitlines() if not l.startswith("# a6010"))
    put("direction-board", "style", home.rstrip() + "\n" + (HERE / "nb.style-roles").read_text(encoding="utf-8").rstrip())
    for f in files:
        p = pathlib.Path(f)
        put(p.stem, "lens", p.read_text(encoding="utf-8").rstrip("\n"), " style=direction-board")
        out = explore([f"scene {p.stem} ok"]).splitlines()
        print("  " + next((l for l in out if "compile" in l or l.startswith("ok")), out[-1] if out else "?")[:900])


if __name__ == "__main__":
    main()
