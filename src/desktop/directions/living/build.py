"""build: LAMPLIT, lane 3's direction (a6057), into a world. worker-a6057, 16 Oct.

    python src/desktop/directions/living/build.py style            write direction-living.style here
    python src/desktop/directions/living/build.py try [--wear] [--lanes]   put the style and lenses into frontier-try
                                                     (--lanes: also wear lane 1's inbox as The board; push it first)
    python src/desktop/directions/living/build.py lines <out>      the same as desk lines, for a world that
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
LAB = HERE.parents[3] / "src" / "text-desk" / "notation"
ROOM = "f5204"
ME = "worker-a6057"
LENSES = [("direction-living-glance", "widget", "slot=bar order=1 size=m"),
          ("direction-living-notices", "widget", "slot=bar order=4 size=m"),
          ("direction-living-timer", "", ""),
          ("direction-living-house", "", ""),
          ("direction-living-house-small", "", "")]
# round 2: the other lanes' roles go between home-style and the overrides, so this light is laid over them too, whether
# or not their round-3 roles have reached home-style yet: lane 1's inbox (a6010) and a5988's live feed
BORROWED = [HERE.parent.parent / "board-lab" / "nb.style-roles", HERE.parent.parent / "home-feed" / "feed.style"]


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def explore(lines, world="frontier-try"):
    r = subprocess.run([sys.executable, str(LAB / "explore.py"), world, "--as", ME, "--whole"],
                       input="\n".join(lines) + "\n", capture_output=True, text=True, encoding="utf-8", cwd=LAB)
    return r.stdout + r.stderr


def style():
    out = explore(["read a5206"])
    base = out.split("---", 1)[1].rsplit("---", 1)[0].strip("\n")
    lent = "".join("\n" + p.read_text(encoding="utf-8").rstrip("\n") for p in BORROWED if p.exists())
    text = base + lent + "\n" + (HERE / "lamplit.overrides").read_text(encoding="utf-8").rstrip("\n")
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
            'do retitle prop:role=home-panel,prop:lens=direction-living-house title="The house"',
            # round 2: which panel answers each number of the glance (a press on it fills the room with that panel)
            "find prop:role=home-panel,prop:actor=alex",
            "do tag prop:role=home-panel,prop:actor=alex,prop:lens=waiting-on-me add=glance-you",
            "do tag prop:role=home-panel,prop:actor=alex,prop:lens=direction-living-house add=glance-work",
            "do tag prop:role=home-panel,prop:actor=alex,prop:lens=home-board add=glance-board",
            # round 2: the chat's typing row says only whether the one you are writing to is at work (The house says
            # the rest); was every resident and worker the house had at work
            "read a5210",
            'do replace a5210 old="  working : row\\n    role working\\n    of house doing=working as h" '
            'new="  working : row\\n    role working\\n    of house doing=working resident=\\$draft.to as h"']


def lanes():
    """round 2: wear the other lanes' round-2 work in the same copy: lane 1's inbox as The board's lens, and NEEDS YOU
    is the glance's 'you' (lane 2's tiling is put by its own put.py try, before this)."""
    return ["find prop:role=home-panel,prop:actor=alex,prop:lens=home-board",
            "do prop prop:role=home-panel,prop:actor=alex,prop:lens=home-board lens=direction-board-inbox",
            "find prop:role=home-panel,prop:actor=alex,tag:glance-you",
            "do tag prop:role=home-panel,prop:actor=alex,tag:glance-you remove=glance-you",
            "find prop:role=home-panel,prop:actor=alex,prop:lens=direction-board-inbox",
            "do tag prop:role=home-panel,prop:actor=alex,prop:lens=direction-board-inbox add=glance-you"]


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
        ls = lines(have) + (wear() if "--wear" in a else []) + (lanes() if "--lanes" in a else [])
        out = explore(ls)
        for l in out.splitlines():
            if re.match(r"^(ok |ERR|.*refus|.*MISS|.*unread|.*not compile|.*error)", l, re.I):
                print(l[:300])


if __name__ == "__main__":
    main(sys.argv[1:])
