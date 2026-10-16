"""put.py: put the home base's music panel (a5592) into a world. 15 Oct 2026.

    python put.py try [world] [--as who]      into a copy (default frontier-try), through explore.py
    python put.py live [--as who]             into the live world, through the door (127.0.0.1:8794)
    python put.py lines                       print the desk lines only

What it puts: the lens home-music (home-music.lens here) as a note in Home base f5204, its three style roles
(home-music.style) appended to home-style a5206, and two lines in home-base a5208 that place it at the top of the right
column. A world that already has home-music gets its text rewritten instead, and the style and placement are left
when they are already there, so it can be run again after editing the .lens file.
"""
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTATION = HERE.parents[1] / "text-desk-lab" / "notation"
ROOM, STYLE, FRAME = "f5204", "a5206", "a5208"
AFTER = "    right : column\n      role side\n      scroll scroll\n"
PLACE = "      music : column\n        lens home-music\n"


def q(text):
    """A desk value in double quotes: backslash, quote and dollar escaped, newlines as \\n."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def lines(ask):
    """ask(line) -> the desk's text. The desk lines, built from what the world has now."""
    lens = (HERE / "home-music.lens").read_text(encoding="utf-8").rstrip("\n")
    roles = [l for l in (HERE / "home-music.style").read_text(encoding="utf-8").splitlines() if l.strip()]
    out = []
    style = ask(f"read {STYLE}")                     # the roles first: a lens naming a missing role does not compile
    for r in roles:
        if r not in style:
            out.append(f"do append {STYLE} line={q(r)}")
    found = ask("find title:home-music,tag:lens")
    if "nothing" in found or "home-music" not in found:
        out.append(f"do create {ROOM} kind=note title=home-music tags=lens style=home-style text={q(lens)}")
    else:
        lid = found.split('note "home-music"')[0].split()[-1]
        out.append(f"do rewrite {lid} text={q(lens)}")
    frame = ask(f"read {FRAME}")
    if "lens home-music" not in frame:
        out.append(f"do replace {FRAME} old={q(AFTER)} new={q(AFTER + PLACE)}")
    return out


def door(world, who):
    def one(line):
        body = json.dumps({"session": world, "as": who, "line": line, "whole": True}).encode("utf-8")
        req = urllib.request.Request("http://127.0.0.1:8794/api/do", data=body, method="POST")
        return json.loads(urllib.request.urlopen(req, timeout=20).read()).get("text") or ""

    def ask(lines):                                  # one request per line: a value may hold a ; or a newline escape
        return "\n".join(one(l) for l in lines.split("\n"))
    return ask


def explore(world, who):
    def ask(line):
        p = subprocess.run([sys.executable, str(NOTATION / "explore.py"), world, "--as", who, "--whole"],
                           input=line + "\n", capture_output=True, text=True, encoding="utf-8", errors="replace")
        return p.stdout
    return ask


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "lines"
    who = sys.argv[sys.argv.index("--as") + 1] if "--as" in sys.argv else "worker-a5592"
    world = sys.argv[2] if mode == "try" and len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "frontier-try"
    ask = door("frontier", who) if mode == "live" else explore(world, who)
    todo = lines(ask)
    if mode == "lines":
        print("\n".join(todo))
        return
    for line in todo:
        # each act is read just before it, as the desk asks: what is changed must have been looked at
        target = line.split()[2]                     # do <verb> <target> ...
        said = ask(f"look {target}\n{line}")
        print(said[-1500:])
        if "\nERR " in said or said.startswith("ERR ") or "refused" in said:
            sys.exit("stopped: the desk refused that line, so the ones after it were not sent")
    lens = ask("scene home-base ok")
    print(lens.strip().splitlines()[-1] if lens.strip() else "(no answer to scene home-base ok)")


if __name__ == "__main__":
    main()
