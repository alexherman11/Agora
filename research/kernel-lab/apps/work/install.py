"""Install Work (work.lens) through the door: the lens (painter=components), its widget and grants, Alex's work-view
(which person is open, his alone), JEFF's own chat on his house-agent, and Work in the dock. No kernel imports, no
source changes to the world; re-running updates what changed and leaves the rest. Opens no window.

    python install.py [--world <dir>] [--port 8810]

Builders appear by themselves: every house-agent is a row of house.who, and a card with build= (task.build will
write it: asked, building, landing, blocked, landed) shows under BUILDS with its builder=.
"""
import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
DESK = LAB.parent / "window-lab" / "kernel-desktop"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


board = _load("work_taskboard_install", LAB / "apps/taskboard/install.py")      # Door, quote
painter = _load("work_painter_install", LAB / "painter/install.py")               # upsert, widget_source
Q = board.quote

# the painter's own words first (as the Task board's widget holds them: painter/install.py activate), then Work's
GRANTS = ("window.surface rows look look-view history components help component-health component-action undo "
          "hear:make hear:set hear:forget hear:undo hear:component hear:component-action "
          "house.who house.activity house.log chat say set hear:say hear:house.doing hear:task-*")


# Colour says whose move it is (the old board's rule): amber Alex's, lilac a resident's (JEFF's), mint an agent at
# work this moment, rose stuck; the rest a plain grey pill. Hex here is the place's light look; the painter
# carries each colour across to the theme the viewer wears (painter/themed.js).
MINT, AMBER, LILAC, ROSE = ("#0B6E55", "#D9F2E8"), ("#8A4B00", "#FCEBD3"), ("#5B3FD0", "#ECE8FB"), ("#A32D2D", "#F8DEDE")
GREY = ("#5F6B66", "#ECEEEB")
STYLES = {"badge": GREY, "badge[doing=working]": MINT, "badge[doing=error]": ROSE, "badge[who=Alex]": AMBER, "badge[who=JEFF]": LILAC,
          "badge[build=building]": MINT, "badge[build=asked]": LILAC, "badge[build=landing]": LILAC,
          "badge[build=blocked]": ROSE}
TYPE = {"text.name": "emphasis=bold"}
GONE = ("badge[doing=idle]",)          # styles an earlier install made that the look no longer has

# The two general components Work arranges, beside the catalogue's (components/*.js), with their cards.
COMPONENTS = {
    "band": dict(category="collections", purpose="A titled band of rows with a count; one quiet line when it holds nothing.",
                 settings='{"name": {"type": "text", "default": ""}, "tone": {"type": "text", "default": "grey"}, '
                          '"empty": {"type": "text", "default": ""}, "folded": {"type": "text", "default": "no"}}',
                 parts='{"body": {"facts": "bound visible row"}, "heading": {"facts": "bound visible row"}, '
                       '"count": {"facts": "bound visible row"}, "quiet": {"facts": "bound visible row"}}',
                 slots='["rows"]', gestures="", example='root : band, name "Needs you", tone amber, empty "nothing waits"',
                 uses="Work; inbox; dashboard", limitations="The count is the rows its child collection paints."),
    "console": dict(category="content", purpose="A live monospaced log, newest at the bottom, with a prompt line under it.",
                    settings='{"value": {"type": "text", "default": ""}, "label": {"type": "text", "default": "Log"}, '
                             '"hint": {"type": "text", "default": ""}, "empty": {"type": "text", "default": ""}}',
                    parts='{"body": {"facts": "bound visible row"}, "log": {"facts": "bound visible row"}, '
                          '"prompt": {"facts": "bound visible row"}, "input": {"facts": "bound visible row"}}',
                    slots="[]", gestures="say", example='root : console, value "said	12:02	JEFF	On it."',
                    uses="Work; agent logs; build output", limitations="Lines are kind, time, who and text, tab-separated; "
                                                                      "display only, no terminal execution."),
}


def components(door):
    import hashlib
    for name, card in COMPONENTS.items():
        code = (LAB / "components" / f"{name}.js").read_text(encoding="utf-8")
        t = painter.upsert(door, "component", name, **card, code=code)
        if door.rows("component", name=name)[0].get("reviewed_code") != hashlib.sha256(code.encode()).hexdigest():
            door.say("look " + t)
            door.say("component " + t)                 # the steward reviews these exact bytes (ARRANGEMENT.md)


def styles(door):
    have = {r.get("target"): r for r in door.rows("part-style", lens="work")}
    for target in GONE:
        if have.get(target):
            door.say("look " + have[target]["id"])
            door.say("forget " + have[target]["id"])
    for target, paint in TYPE.items():             # the open person's name a little stronger than the line it heads
        if not have.get(target):
            door.say(f"make kind=part-style lens=work target={Q(target)} {paint}")
    for target, (fg, bg) in STYLES.items():
        old = have.get(target)
        if not old:
            door.say(f"make kind=part-style lens=work target={Q(target)} color={fg} background={bg} radius=soft")
        elif (old.get("color"), old.get("background")) != (fg, bg):
            door.say("look " + old["id"])
            door.say(f"set {old['id']} color={fg} background={bg}")


def install(door):
    out = {}
    shop = door.rows("chat", name="Shop talk")
    convo = door.rows("chat", name="Conversation")
    if not shop or not convo:
        raise RuntimeError("no Shop talk or Conversation yet: kdesk makes them when it starts (moving_in)")
    components(door)
    text = (HERE / "work.lens").read_text(encoding="utf-8").replace("$SHOP", shop[0]["id"])
    out["lens"] = painter.upsert(door, "lens", "work", title="Work", painter="components", text=text)
    mid = painter.upsert(door, "widget", "work", title="Work", style="bars", component_lens="work",
                         code=painter.widget_source())
    current = door.rows("widget", name="work")[0]
    grants = [g for g in door.rows("grant", to=mid) if not g.get("revoked")]
    if not current.get("on") or [g.get("words") for g in grants] != [GRANTS]:
        door.say("look " + mid)
        if current.get("on"):           # `widget` adds a grant beside the old one; off takes the old ones back first
            door.say("off " + mid)
            door.say("look " + mid)
        door.say("widget " + mid + " surface=window grants=" + Q(GRANTS) + " only=kind:work-view")
    out["widget"] = mid
    styles(door)
    if not door.rows("work-view"):
        out["view"] = door.say('make kind=work-view name="Alex\'s work view" sees=me')["made"][0]
    jeff = door.rows("house-agent", name="JEFF")
    view = door.rows("work-view")[0]
    if jeff and not view.get("agent"):
        door.say("look " + view["id"])
        door.say(f"set {view['id']} agent={jeff[0]['person']}")       # JEFF open at first: the right side is never empty
    if jeff and jeff[0].get("chat") != convo[0]["id"]:
        door.say("look " + jeff[0]["id"])
        door.say(f"set {jeff[0]['id']} chat={convo[0]['id']}")        # JEFF's own chat: the Conversation
    shell = door.rows("shell-settings")
    if shell:
        apps = (shell[0].get("dock_apps") or "lines,help,board,taskboard,appearance,feed").replace(" ", "")
        if "work" not in apps.split(","):
            door.say("look " + shell[0]["id"])
            door.say(f"set {shell[0]['id']} dock_apps={Q(apps + ',work')}")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--world", default=str(DESK / "state" / "world"))
    ap.add_argument("--port", type=int, default=8810)
    a = ap.parse_args()
    sessions = json.loads((Path(a.world) / "keep" / "sessions.json").read_text(encoding="utf-8"))
    token = next(t for t, v in sessions.items() if v.get("signer") == "alex")     # a widget is the steward's to turn on
    print(install(board.Door(f"http://127.0.0.1:{a.port}", token)))


if __name__ == "__main__":
    main()
