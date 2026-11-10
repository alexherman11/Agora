"""put.py: put the home base's music panel into a world (a5592; Spotify's look and Like since a6443). 17 Oct 2026.

    python put.py try [world] [--as who]      into a copy (default frontier-try), through explore.py
    python put.py live [--as who]             into the live world, through the door (127.0.0.1:8794): only AFTER the
                                              branch that taught the desk `media picture` has landed
                                              (before, the lenses do not compile)
    python put.py lines                       print the desk lines only

What it puts (each read from the world first, so it can run again after editing the files here):
  - home-music.style's lines into home-style (a5206): a line whose name is missing is appended; one whose name is
    there with other words is replaced in place (one definition of each name, as LAMPLIT asks);
  - the lenses home-music-keys, home-music-time (placed by the two below), home-music-full, home-music and
    home-music-small, as notes in Home base f5204 (created, or their text rewritten);
  - filled=home-music-full on the Music panel note (role=home-panel lens=home-music), and in home-tiling (a5692) the
    filled panel's body shows `lens $p.filled` when the panel says one, else `lens $p.lens` as before: a panel may
    have a form for when it fills the room (a world word for every panel, not only this one).
"""
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTATION = HERE.parents[1] / "text-desk" / "notation"
ROOM, STYLE, TILING = "f5204", "a5206", "a5692"
LENSES = ["home-music-keys", "home-music-time", "home-music-full", "home-music", "home-music-small"]
PANEL = "prop:role=home-panel,prop:lens=home-music"
HEADER = "# a6443: the music panel in Spotify's look (home-music*): its own dark palette; its green is a state only"
BODY_OLD = ("  body : column\n    role panebody\n    share 1\n    scroll scroll\n    lens $p.lens")   # fullpanel's last lines, read 20 Oct after the scrolling fix
BODY_NEW = ("  body : column\n    role panebody\n    share 1\n    scroll scroll\n    only when $item != ($lay.full or \"\") or ($p.filled or \"\") = \"\"\n"
            "    lens $p.lens\n"
            "  filledbody : column\n    role panebody\n    share 1\n    scroll scroll\n    only when $item = ($lay.full or \"\") and ($p.filled or \"\") != \"\"\n"
            "    lens $p.filled")


def q(text):
    """A desk value in double quotes: backslash, quote and dollar escaped, newlines as \\n."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def body_of(read):
    """The text of a `read` answer: between its two --- lines."""
    a = read.find("\n---\n")
    b = read.rfind("\n---")
    return read[a + 5:b + 1] if 0 <= a < b else ""


def head(line):
    m = re.match(r"^(role|token)\s+([\w.]+)", line)
    return m.group(0) if m else None


def lines(ask):
    """ask(line) -> the desk's text. The desk lines, built from what the world has now."""
    out = []
    style = body_of(ask(f"read {STYLE}"))            # the roles first: a lens naming a missing role does not compile
    mine = [r for r in (HERE / "home-music.style").read_text(encoding="utf-8").splitlines() if head(r)]
    block = "\n".join([HEADER] + mine)
    names = {head(r) for r in mine}
    lines_ = style.splitlines()
    at = [k for k, l in enumerate(lines_) if l.startswith("# a6443: the music panel")]
    if at:                                           # put before: its block is replaced whole, in one act
        i = at[0]
        j = i + 1
        while j < len(lines_) and head(lines_[j]) in names:
            j += 1
        old = "\n".join(lines_[i:j])
        if old != block:
            out.append(f"do replace {STYLE} old={q(old)} new={q(block)}")
    else:
        have = {head(l): l for l in lines_ if head(l)}
        clash = [h for h in names if h in have]
        if clash:
            raise SystemExit(f"home-style already names {', '.join(sorted(clash))} outside this panel's block; nothing sent")
        out.append(f"do append {STYLE} line={q(block)}")   # one append, its lines under one comment
    for name in LENSES:
        text = (HERE / f"{name}.lens").read_text(encoding="utf-8").rstrip("\n")
        found = ask(f"find title:{name},tag:lens")
        m = re.search(r'(a\d+) note "' + re.escape(name) + '"', found)
        if not m:
            out.append(f"do create {ROOM} kind=note title={name} tags=lens style=home-style text={q(text)}")
        elif body_of(ask(f"read {m.group(1)}")).rstrip("\n") != text:
            out.append(f"do rewrite {m.group(1)} text={q(text)}")
    tiling = body_of(ask(f"read {TILING}"))
    if "lens $p.filled" not in tiling:
        if not tiling.rstrip("\n").endswith(BODY_OLD):
            raise SystemExit("home-tiling's filled panel body is not as put.py knows it; nothing sent")
        out.append(f"do replace {TILING} old={q(BODY_OLD)} new={q(BODY_NEW)}")
    panel = ask(f"find {PANEL}")
    for pid in re.findall(r"(a\d+) note", panel):
        if "filled=home-music-full" not in panel.split(pid, 1)[1].splitlines()[0]:
            out.append(f"do prop {pid} filled=home-music-full")
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
    who = sys.argv[sys.argv.index("--as") + 1] if "--as" in sys.argv else "worker-a6443"
    world = sys.argv[2] if mode == "try" and len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "frontier-try"
    ask = door("frontier", who) if mode == "live" else explore(world, who)
    todo = lines(ask)
    if mode == "lines":
        print("\n".join(todo))
        return
    for line in todo:
        # each act is read just before it, as the desk asks: what is changed must have been looked at
        target = line.split()[2]                     # do <verb> <target> ...
        said = ask(f"{'look' if target.startswith('f') else 'read'} {target}\n{line}")
        print(said[-600:].strip() + "\n")
        if "\nERR " in said or said.startswith("ERR ") or "refused" in said:
            sys.exit("stopped: the desk refused that line, so the ones after it were not sent")
    for name in ("home-music", "home-music-full", "home-base"):
        lens = ask(f"scene {name} ok")
        print(name + ":", lens.strip().splitlines()[-1] if lens.strip() else "(no answer)")


if __name__ == "__main__":
    main()
