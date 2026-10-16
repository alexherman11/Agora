"""The home base's widgets (a5530) as desk lines: the world half of the commission, kept here as files so it can be read,
tried on a copy and applied to the live world after the code it needs (`live`, `on end`, `$now`, `by -at`) has landed.

    python research/window-lab/widgets/apply.py lines <out.desk> [--as <name>]   write the lines (for explore.py < out.desk)
    python research/window-lab/widgets/apply.py update <out.desk>                lines that rewrite the lenses and rules
    python research/window-lab/widgets/apply.py door [--as <name>]               send them to the live door, one by one

What the lines make, all in the Home base room (f5204), all world data anyone may change afterwards:
  - five lenses: home-widgets (the one reader of slot=bar widgets) and the widgets home-clock, home-now, home-pomodoro,
    home-notices (notes tagged lens and widget, slot=bar, order=1..4), with their roles appended to home-style;
  - Alex's notices surface (role=notices actor=alex, skip= the chat the home base shows, cleared= the newest call seen),
    his timer note (role=pomodoro) and his now note (role=now);
  - four rules that make a notice (role=notice to=alex topic= about= came=$now) when a commission lands, a worker asks
    (commission=waiting), a thing is tagged ready-for-review, or a design waits on his word;
  - one edit to home-base: its bar begins with the widgets, top left, and the old date text goes.
Applying twice makes everything twice: it is for a world that has none of it yet."""
import json
import pathlib
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOM = "f5204"
WIDGETS = [("home-clock", 1, "s"), ("home-now", 2, "m"), ("home-pomodoro", 3, "s"), ("home-notices", 4, "m")]
RULES = [("prop:commission=landed", "landed"), ("prop:commission=waiting", "asking"),
         ("tag:ready-for-review", "review"), ("prop:design=waiting", "design")]
BAR_OLD = """  bar : row
    role bar
    mark : text "AGORA"
      role brand
    name : text "Home base"
      role place
      share 1
    when : text "$today"
      role meta
    keys : text "Ctrl+Alt+J or Esc closes"
      role meta"""
BAR_NEW = """  bar : row
    role bar
    widgets : row
      share 1
      lens home-widgets
    mark : text "AGORA"
      role brand
    keys : text "Ctrl+Alt+J or Esc closes"
      role meta"""


def q(s):
    """A value as the desk reads it: in double quotes, with backslash, quote and dollar escaped and newlines as \\n."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def lens(name):
    return (HERE / f"{name}.lens").read_text(encoding="utf-8").rstrip("\n")


def rule(sel, topic):
    # the target is the surface's unique title, so the rule needs no id known in advance (a selection target would make
    # create group what it matches into a new surface)
    return (f"when {sel} do create \"Alex's notices\" kind=note title={topic} role=notice "
            f"to=alex topic={topic} about=$item came=$now")


def update():
    """Lines that rewrite what `lines` made (each lens and rule by its title), for a world that already has them."""
    out = []
    for name in ["home-widgets"] + [w[0] for w in WIDGETS]:
        out += [f'read "{name}"', f'do rewrite "{name}" text={q(lens(name))}']
    for sel, topic in RULES:
        out += [f'read "Notice Alex: {topic}"', f'do rewrite "Notice Alex: {topic}" text={q(rule(sel, topic))}']
    return out


def lines(cleared="e10780"):
    out = [f"do create {ROOM} kind=surface title=\"Alex's notices\" layout=column as=nb; set notices = $nb; "
           f"do prop $notices role=notices actor=alex skip=a5080 cleared={cleared}",
           f"do create {ROOM} kind=note title=\"Alex's timer\" role=pomodoro actor=alex mode=focus focus=25 rest=5 state=idle",
           f"do create {ROOM} kind=note title=\"Alex's now\" role=now actor=alex"]
    for sel, topic in RULES:
        out.append(f"do create {ROOM} kind=note tags=rule title=\"Notice Alex: {topic}\" text={q(rule(sel, topic))}")
    style = (HERE / "widgets.style").read_text(encoding="utf-8").rstrip("\n")
    out.append(f'do append "home-style" line={q(style)}')
    out.append(f"do create {ROOM} kind=note title=home-widgets tags=lens style=home-style text={q(lens('home-widgets'))}")
    for name, order, size in WIDGETS:
        out.append(f"do create {ROOM} kind=note title={name} tags=lens,widget style=home-style slot=bar order={order} size={size} "
                   f"text={q(lens(name))}")
    out.append('read "home-base"')
    out.append(f'do replace "home-base" old={q(BAR_OLD)} new={q(BAR_NEW)}')
    return out


def main(argv):
    who = argv[argv.index("--as") + 1] if "--as" in argv else "worker-a5530"
    if argv[:1] in (["lines"], ["update"]) and len(argv) > 1:
        out = lines() if argv[0] == "lines" else update()
        pathlib.Path(argv[1]).write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"wrote {len(out)} lines to {argv[1]}")
    elif argv[:1] == ["door"]:
        for line in lines(**({"cleared": argv[argv.index("--cleared") + 1]} if "--cleared" in argv else {})):
            body = json.dumps({"session": "frontier", "as": who, "line": line, "whole": True}).encode()
            r = urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8794/api/do", data=body, method="POST"), timeout=60)
            said = json.loads(r.read()).get("text", "")
            print(said[:400])
            if said.startswith("ERR") or "refused" in said[:200]:
                print("stopped: the line above was refused")
                return 1
    else:
        print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
