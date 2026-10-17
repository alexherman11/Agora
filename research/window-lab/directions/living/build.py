"""build: LAMPLIT, lane 3's direction (a6057), into a world. worker-a6057, 16 Oct.

    python research/window-lab/directions/living/build.py style            write direction-living.style here
    python research/window-lab/directions/living/build.py try [--wear]     put the style and lenses into frontier-try
    python research/window-lab/directions/living/build.py lines <out>      the same as desk lines, for a world that
                                                                           has none of them yet (no ids assumed)

direction-living.style is home-style (read from frontier-try, the live world's copy) followed by lamplit.overrides: a
style's later role or token of one name wins, so the direction wears every role the HUD has, and lanes 1 and 2's
lenses (the board, the tiling) are worn, not copied. The lenses are notes in the Home base room (f5204), titled by
their file names, style=direction-living.

--wear also changes the try world's DATA so the home base shows the direction (all undoable, all in the copy):
  home-base's style -> direction-living; the widgets home-clock, home-now and home-notices lose their widget tag (the
  glance takes the clock's place, The house takes Now, the living notices take the bar); the At work panel shows
  direction-living-house and is called The house. Never run --wear against the live world without Alex's word.
"""
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
LAB = HERE.parents[3] / "research" / "text-desk-lab" / "notation"
ROOM = "f5204"
ME = "worker-a6057"
LENSES = [("direction-living-glance", "widget", "slot=bar order=1 size=m"),
          ("direction-living-notices", "widget", "slot=bar order=4 size=m"),
          ("direction-living-house", "", ""),
          ("direction-living-house-small", "", "")]


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def explore(lines, world="frontier-try"):
    r = subprocess.run([sys.executable, str(LAB / "explore.py"), world, "--as", ME, "--whole"],
                       input="\n".join(lines) + "\n", capture_output=True, text=True, encoding="utf-8", cwd=LAB)
    return r.stdout + r.stderr


def style():
    out = explore(["read a5206"])
    base = out.split("---", 1)[1].rsplit("---", 1)[0].strip("\n")
    text = base + "\n" + (HERE / "lamplit.overrides").read_text(encoding="utf-8").rstrip("\n")
    (HERE / "direction-living.style").write_text(text + "\n", encoding="utf-8")
    print(f"direction-living.style: {len(text.splitlines())} lines (home-style {len(base.splitlines())})")
    return text


def notes():
    """(title, tags, props, text) for the style and each lens."""
    yield "direction-living", "style", "", (HERE / "direction-living.style").read_text(encoding="utf-8").rstrip("\n")
    for name, tag, props in LENSES:
        yield name, "lens" + ("," + tag if tag else ""), ("style=direction-living " + props).strip(), \
            (HERE / f"{name}.lens").read_text(encoding="utf-8").rstrip("\n")


def in_room(text):
    return {m.group(2): m.group(1) for m in re.finditer(r'^\s+(a\d+) note "([^"]+)"', text, re.M)}


def lines(have=None):
    have = have or {}
    out = [f"look {ROOM}"]
    for title, tags, props, text in notes():
        if title in have:
            out += [f"read {have[title]}", f"do rewrite {have[title]} text={q(text)}"]
        else:
            out.append(f"do create {ROOM} kind=note title={q(title)} tags={tags} {props} text={q(text)}".replace("  ", " "))
    return out


def wear():
    return ["read a5208", "do prop a5208 style=direction-living",
            'read "home-clock"', 'do tag "home-clock" remove=widget',
            'read "home-now"', 'do tag "home-now" remove=widget',
            'read "home-notices"', 'do tag "home-notices" remove=widget',
            'read "home-pomodoro"', 'do tag "home-pomodoro" remove=widget',
            "find prop:role=home-panel,prop:lens=home-work",
            "do prop prop:role=home-panel,prop:lens=home-work lesser=direction-living-house-small lens=direction-living-house",
            "find prop:role=home-panel,prop:lens=direction-living-house",
            'do retitle prop:role=home-panel,prop:lens=direction-living-house title="The house"']


def main(a):
    if not a:
        print(__doc__)
        return
    if a[0] == "style":
        style()
    elif a[0] == "lines":
        style()
        pathlib.Path(a[1]).write_text("\n".join(lines()) + "\n", encoding="utf-8")
    elif a[0] == "try":
        style()
        have = in_room(explore([f"look {ROOM} :2"]))
        ls = lines(have) + (wear() if "--wear" in a else [])
        out = explore(ls)
        for l in out.splitlines():
            if re.match(r"^(ok |ERR|.*refus|.*MISS|.*unread|.*not compile|.*error)", l, re.I):
                print(l[:300])


if __name__ == "__main__":
    main(sys.argv[1:])
