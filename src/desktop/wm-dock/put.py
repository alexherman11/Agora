"""put.py: the dock's Window Manager icon starts and stops the window manager (a6113). 16 Oct 2026.

    python put.py lines                                 print the desk lines, built from the live world (read only)
    python put.py door <url> <world> [--as who]         send them through a door: a copy's, for a test
    python put.py check <url> <world> [--as who]        say whether a world has them already

What it puts: in the lens home-dock (a5564) an icon with switch=wm has two faces. While the home base lists the host
verb wm.start (witnessed:host) and the window manager is off (no witnessed:wm row) a click asks `host wm.start`; while
it is on, the icon is lit, says "Put back", and a click asks `host wm.stop`. While the running home base does not know
wm.start yet (an older hud.py, until it is restarted) the icon does what it did: opens what its opens= names. Then
switch=wm on Alex's Window Manager icon (a5575). Run again: what is there already is left.
"""
import json
import sys
import urllib.request

LENS, ICON = "a5564", "a5575"
GUARD = 'only when ($d.opens or "") != "" and $d.opens != "chat"\n    role appicon\n'
GUARD_NEW = ('only when ($d.opens or "") != "" and $d.opens != "chat" and (($d.switch or "") != "wm" or '
             'count(witnessed:host name=wm.start) = 0)\n    role appicon\n')
HEAD = "# Right-click an icon"
HEAD_NEW = ("# switch=wm (a6113): the icon starts the window manager (host wm.start) and, lit while it runs (witnessed:wm),\n"
            "# a second click puts every window back (host wm.stop); opens= is used only by a home base that lacks wm.start.\n"
            "# Right-click an icon")
AT = "adder : column\n"
PARTS = """  wm : column
    only when ($d.switch or "") = "wm" and count(witnessed:host name=wm.start) > 0 and count(witnessed:wm) = 0
    role appicon
    on click host wm.start
    glyph : text "$d.glyph"
      role appglyph
    label : text "$d.title"
      role applabel
      clamp 1
  wmon : column
    only when ($d.switch or "") = "wm" and count(witnessed:wm) > 0
    role appicon.on
    on click host wm.stop
    glyph : text "$d.glyph"
      role appglyph
    label : text "Put back"
      role applabel
      clamp 1
"""


def q(text):
    """A desk value in double quotes: backslash, quote and dollar escaped, newlines as \\n."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def lines(ask):
    lens = ask(f"read {LENS}")
    out = []
    if GUARD in lens:
        out.append(f"do replace {LENS} old={q(GUARD)} new={q(GUARD_NEW)}")
    if "switch=wm (a6113)" not in lens:
        out.append(f"do replace {LENS} old={q(HEAD)} new={q(HEAD_NEW)}")
    if "  wmon : column" not in lens:
        out.append(f"do replace {LENS} old={q(AT)} new={q(PARTS + AT)}")
    if "switch=wm" not in ask(f"read {ICON}"):
        out.append(f"do prop {ICON} switch=wm")
    return out


def door(url, world, who):
    def ask(line):
        body = json.dumps({"session": world, "as": who, "line": line, "whole": True}).encode("utf-8")
        req = urllib.request.Request(url.rstrip("/") + "/api/do", data=body, method="POST")
        return json.loads(urllib.request.urlopen(req, timeout=30).read()).get("text") or ""
    return ask


def main():
    a = sys.argv[1:]
    who = a[a.index("--as") + 1] if "--as" in a else "worker-a6113"
    mode = a[0] if a else "lines"
    ask = door("http://127.0.0.1:8794", "frontier", who) if mode == "lines" else door(a[1], a[2], who)
    todo = lines(ask)
    if mode == "lines":
        print("\n".join(todo))
        return 0
    if mode == "check":
        print("has it" if not todo else f"lacks {len(todo)} line(s)")
        return 0 if not todo else 1
    for line in todo:
        target = line.split()[2]                     # what is changed must have been looked at: read it just before
        ask(f"read {target}")
        said = ask(line)
        print(said.strip().splitlines()[-1][:300] if said.strip() else "(no answer)")
        if said.startswith("ERR") or "\nERR" in said or "refused" in said.lower():
            print(said[:1500])
            return 1
    print(ask("scene home-base ok").strip().splitlines()[-1][:300])
    return 0


if __name__ == "__main__":
    sys.exit(main())
