"""Pure staged world recipe. Prints commands; never connects or applies.

JEFF reads all targets first, checks passages, saves their current text in a
restore note, then uses these exact replacements through the Desk tool.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
STYLE_ANCHOR = "role appgrip : on spbg, spbg, height gap, pad gap x0"
VIEWER_OLD = '    title : text "$title"\n      role heading\n      clamp 2\n      share 1'
VIEWER_NEW = VIEWER_OLD + '\n      carry\n      tip "$title" "Drag to the dock to pin this."'
THING_OLD = '  name : text "$item"\n    role hitname\n    clamp 1\n    share 1'
THING_NEW = THING_OLD + '\n    carry\n    tip "$title" "Drag to the dock to pin this."'


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def passages():
    return [
        ("a5206", STYLE_ANCHOR, STYLE_ANCHOR + "\n" + (HERE / "style.style").read_text(encoding="utf-8").rstrip()),
        ("a5486", VIEWER_OLD, VIEWER_NEW),
        ("a6784", THING_OLD, THING_NEW),
        ("a5564", (HERE / "before-home-dock.lens").read_text(encoding="utf-8").rstrip(),
         (HERE / "home-dock.lens").read_text(encoding="utf-8").rstrip()),
    ]


def preflight(texts):
    """All passages checked before making any commands; no partial plan."""
    for ident, old, new in passages():
        text = texts[ident]
        if old not in text and text.count(new) == 1:
            continue
        if text.count(old) != 1 or (ident == "a5206" and "# a7223 slim dock begin" in text):
            raise ValueError("staged dock passage moved or already partly applied: " + ident)


def commands(reverse=False):
    out = []
    if not reverse:
        for path in sorted(HERE.glob("*.verb")):
            out += ["look f5189", "do create f5189 kind=note title=" + q(path.stem)
                    + " tags=verb on=f5189 text=" + q(path.read_text(encoding="utf-8").rstrip())]
    for ident, old, new in (reversed(passages()) if reverse else passages()):
        if reverse:
            old, new = new, old
        out += ["read " + ident, "do replace " + ident + " old=" + q(old) + " new=" + q(new)]
    return out


if __name__ == "__main__":
    import sys
    print("\n".join(commands("--reverse" in sys.argv)))
