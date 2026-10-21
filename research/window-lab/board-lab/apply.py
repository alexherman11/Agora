"""The board's world half (a6010, HUD sprint lane 1, round 3): the inbox as the home base's board panel. Only this lane's
part; the desk lane (a5994) assembles the three lanes and applies them in one pass.

    python research/window-lab/board-lab/apply.py lines <out.desk>     the lines, for explore.py or hud_playtest --apply
    python research/window-lab/board-lab/apply.py backup [--world frontier] [--port 8794] [--as <name>]
                                        first: each note it changes, as it stands, into before-a6010/ (to put back by hand)
    python research/window-lab/board-lab/apply.py check                on frontier-try (a copy the house makes): apply
                                        the lines with explore.py, then every lens it touches must compile, and the home base
    python research/window-lab/board-lab/apply.py door [--world frontier] [--port 8794] [--as <name>]
                                        all of it through a door, line by line, stopping at the first refusal

What the lines do, all world data anyone may change afterwards:
  - home-style (a5206) gains the nb* roles the board paints with (nb.style-roles), as one block between two marker
    lines; a later run replaces that block, so it is applied once however often it runs. First, so the lens never stands
    uncompiled.
  - home-board (a5548) becomes the inbox (home-board.lens): NEEDS YOU, IN MOTION, LANDED, one-press answers.
  - home-board-small (a5682) becomes its one line (home-board-small.lens): '6 need you · 5 moving · 2 wait on JEFF'.
  - Alex's board panel (a5674) is tagged glance-you and glance-board, so lane 3's glance opens it for both numbers.
It does not shelve Waiting on you (a5668): which panels stand out is the layout's, the desk lane's to set.
"""
import json
import pathlib
import re
import subprocess
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
LAB = HERE.parents[1] / "text-desk-lab" / "notation"
STYLE, BOARD, SMALL, PANEL = "a5206", "a5548", "a5682", "a5674"
TITLES = {STYLE: "home-style", BOARD: "home-board", SMALL: "home-board-small", PANEL: "The board"}
BEGIN, END = "# a6010 board roles: begin (board-lab/apply.py replaces this block)", "# a6010 board roles: end"
BEFORE = HERE / "before-a6010"


def q(s):
    """A value as the desk reads it: double quotes, backslash, quote and dollar escaped, newlines as \\n."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def text(name):
    return (HERE / name).read_text(encoding="utf-8").rstrip("\n")


def block():
    return BEGIN + "\n" + text("nb.style-roles") + "\n" + END


def lines(style_now=None):
    """The desk lines. style_now: home-style's text as it stands (None: assume the block is not there yet)."""
    out = [f"read {STYLE}"]
    if style_now and BEGIN in style_now and END in style_now:
        old = style_now[style_now.index(BEGIN):style_now.index(END) + len(END)]
        out.append(f"do replace {STYLE} old={q(old)} new={q(block())}")
    else:
        out.append(f"do append {STYLE} line={q(block())}")
    out += [f"read {BOARD}", f"do rewrite {BOARD} text={q(text('home-board.lens'))}",
            f"read {SMALL}", f"do rewrite {SMALL} text={q(text('home-board-small.lens'))}",
            f"read {PANEL}", f"do tag {PANEL} add=glance-you,glance-board"]
    return out


def door(line, who, port, world):
    body = json.dumps({"session": world, "as": who, "line": line, "whole": True}).encode()
    r = urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/api/do", data=body, method="POST"), timeout=60)
    return json.loads(r.read()).get("text", "")


def body_of(said):
    """The words of a `read <id> :3` between its two --- lines, and the head line naming the note."""
    ls = said.splitlines()
    i = ls.index("---")
    j = ls.index("---", i + 1)
    return "\n".join(ls[i + 1:j]), next((x for x in ls[:i] if "appears at" in x), "")


def explore(cmds, world="frontier-try", who="worker-a6010"):
    r = subprocess.run([sys.executable, str(LAB / "explore.py"), world, "--as", who, "--whole"], input="\n".join(cmds) + "\n",
                       capture_output=True, text=True, encoding="utf-8", cwd=LAB)
    return r.stdout + r.stderr


def refused(said):
    return [x for x in said.splitlines() if x.startswith(("ERR", "MISS")) or x.startswith("~ ! lens") or "does not compile" in x]


def check():
    """Apply on frontier-try with explore.py, then every lens it touches, and the home base, must compile."""
    style_now, head = body_of(explore([f"read {STYLE} :3"]))
    if TITLES[STYLE] not in head:
        print(f"{STYLE} is not home-style here: {head}")
        return 1
    bad, ls = 0, lines(style_now)
    for first, act in zip(ls[0::2], ls[1::2]):          # each act with its read, in one run (explore forgets looks)
        r = refused(explore([first, act]))
        print(("REFUSED " if r else "ok      ") + act[:110] + (f"  -> {r[:2]}" if r else ""))
        bad += bool(r)
    for lens in ("home-board", "home-board-small", "home-base"):
        said = [x for x in explore([f"scene {lens} ok"], who="alex").splitlines() if "compile" in x]
        print(f"{lens}: {said[0] if said else '(no answer)'}"[:200])
        bad += not said or "does not compile" in said[0]
    return 1 if bad else 0


def backup(who, port, world):
    BEFORE.mkdir(exist_ok=True)
    for i, title in TITLES.items():
        said = door(f"read {i} :3", who, port, world)
        if i == PANEL:
            (BEFORE / f"{i}.txt").write_text(said + "\n", encoding="utf-8")     # a panel's facts are its props and tags
            print(f"kept {i} ({title}) as read")
            continue
        words, head = body_of(said)
        if title not in head:
            print(f"refusing: {i} is not {title} in {world}: {head}")
            return 1
        (BEFORE / f"{i}.txt").write_text(words + "\n", encoding="utf-8")
        print(f"kept {i} ({title}): {len(words)} characters")
    return 0


def main(argv):
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d       # noqa: E731
    if not argv or argv[0] not in ("lines", "backup", "check", "door"):
        print(__doc__)
        return 0
    if argv[0] == "lines":
        pathlib.Path(argv[1]).write_text("\n".join(lines()) + "\n", encoding="utf-8")
        print(f"wrote {len(lines())} lines to {argv[1]}")
        return 0
    if argv[0] == "check":
        return check()
    who, port, world = opt("--as", "worker-a6010"), opt("--port", "8794"), opt("--world", "frontier")
    if argv[0] == "backup":
        return backup(who, port, world)
    if not (BEFORE / f"{BOARD}.txt").exists():
        print("run backup first: the live texts this replaces must be kept before it runs")
        return 1
    style_now, _ = body_of(door(f"read {STYLE} :3", who, port, world))
    for line in lines(style_now):
        said = door(line, who, port, world)
        print(said[:300])
        if refused(said):
            print("stopped: the line above was refused or left a lens not compiling:", refused(said)[:2])
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
