"""The home base's widgets (a5530) as desk lines: the world half of the commission, kept here as files so it can be read,
tried on a copy and applied to the live world after the code it needs (`live`, `on end`, `$now`, `by -at`) has landed.

    python research/window-lab/widgets/apply.py lines <out.desk> [--into base|tiling]   the lines (explore.py ... < out.desk)
    python research/window-lab/widgets/apply.py update <out.desk>         lines that rewrite the lenses and rules
    python research/window-lab/widgets/apply.py place <out.desk> --into base|tiling   only the edit that places them
    python research/window-lab/widgets/apply.py door [--as <name>] [--cleared e<n>]   all of it, to the live door, line by
                                                                          line, stopping at a refusal
    python research/window-lab/widgets/apply.py door-place [--into ...]   only the placing edit, live (after a5496's layout
                                                                          replaces home-base with home-tiling, run this)
--into: base edits home-base's bar (the frame before a5496's layout), tiling edits home-tiling's top row and drops its
clock (a5496, c5612); door finds which the live world has. --cleared: calls older than this event are not shown (use
the newest event id at the time, so the bar starts calm).

What the lines make, all in the Home base room (f5204), all world data anyone may change afterwards:
  - five lenses: home-widgets (the one reader of slot=bar widgets) and the widgets home-clock, home-now, home-pomodoro,
    home-notices (notes tagged lens and widget, slot=bar, order=1..4), with their roles appended to home-style;
  - Alex's notices surface (role=notices actor=alex, skip= the chat the home base shows, cleared= the newest call seen),
    his timer note (role=pomodoro) and his now note (role=now);
  - four rules that make a notice (role=notice to=alex topic= about= came=$now) when a commission lands, a worker asks
    (commission=waiting), a thing is tagged ready-for-review, or a design waits on his word;
  - one edit that places them, top left: home-base's bar begins with the widgets and its date text goes, or, with
    a5496's layout, home-tiling's top row begins with them and its clock goes.
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
# a5496's layout (research/window-lab/home-layout): once home-base is home-tiling, the widgets lead its top row and take
# over its clock (worker-a5496, c5612: 'the clock is yours from then on')
TOP_OLD = """  top : row
    role top
    clock : row
      role clock
      of witnessed:clock as k
      each clockface
    day : text "$today"
      role clocktime
      only when count(witnessed:clock) = 0
"""
TOP_NEW = """  top : row
    role top
    widgets : row
      lens home-widgets
"""


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


def place(into):
    """The one edit that puts the widgets on screen: into a5496's home-tiling top row, or the older home-base bar."""
    if into == "tiling":
        return ['read "home-tiling"', f'do replace "home-tiling" old={q(TOP_OLD)} new={q(TOP_NEW)}']
    return ['read "home-base"', f'do replace "home-base" old={q(BAR_OLD)} new={q(BAR_NEW)}']


def lines(cleared="e10780", into="base"):
    out = [f"do create {ROOM} kind=surface title=\"Alex's notices\" layout=column as=nb; set notices = $nb; "
           f"do prop $notices role=notices actor=alex skip=a5080 cleared={cleared}",
           f"do create {ROOM} kind=note title=\"Alex's timer\" role=pomodoro actor=alex mode=focus focus=25 rest=5 state=idle",
           f"do create {ROOM} kind=note title=\"Alex's now\" role=now actor=alex"]
    for sel, topic in RULES:
        out.append(f"do create {ROOM} kind=note tags=rule title=\"Notice Alex: {topic}\" text={q(rule(sel, topic))}")
    style = (HERE / "widgets.style").read_text(encoding="utf-8").rstrip("\n")
    out += ['read "home-style"', f'do append "home-style" line={q(style)}']
    out.append(f"do create {ROOM} kind=note title=home-widgets tags=lens style=home-style text={q(lens('home-widgets'))}")
    for name, order, size in WIDGETS:
        out.append(f"do create {ROOM} kind=note title={name} tags=lens,widget style=home-style slot=bar order={order} size={size} "
                   f"text={q(lens(name))}")
    return out + place(into)


def door(line, who):
    body = json.dumps({"session": "frontier", "as": who, "line": line, "whole": True}).encode()
    r = urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8794/api/do", data=body, method="POST"), timeout=60)
    return json.loads(r.read()).get("text", "")


def main(argv):
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d       # noqa: E731
    who, into = opt("--as", "worker-a5530"), opt("--into")
    if argv[:1] == ["door"] and not into:          # the live world says which frame it has
        into = "tiling" if "nothing matches" not in door("find title:home-tiling,tag:lens", who) else "base"
    kw = {"into": into or "base", **({"cleared": opt("--cleared")} if opt("--cleared") else {})}
    out = {"lines": lambda: lines(**kw), "update": update, "place": lambda: place(kw["into"]),
           "door": lambda: lines(**kw), "door-place": lambda: place(kw["into"])}.get(argv[0] if argv else "", lambda: None)()
    if out is None:
        print(__doc__)
    elif not argv[0].startswith("door"):
        pathlib.Path(argv[1]).write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"wrote {len(out)} lines to {argv[1]}")
    else:
        for line in out:
            said = door(line, who)
            print(said[:400])
            if said.startswith("ERR") or "refused" in said[:200]:
                print("stopped: the line above was refused")
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
