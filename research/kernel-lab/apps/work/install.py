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
          "house.who house.activity chat say set hear:say hear:house.doing hear:task-*")


# Colour says whose move it is (the old board's rule): mint someone at work now, amber Alex's, lilac a build on its
# way, rose stuck; the rest the theme's plain badge.
MINT, SKY, AMBER, LILAC, ROSE = ("#0B6E55", "#D9F2E8"), ("#2F5E86", "#E1ECF6"), ("#8A4B00", "#FCEBD3"),     ("#5B3FD0", "#ECE8FB"), ("#A32D2D", "#F8DEDE")
STYLES = {"badge[doing=working]": MINT, "badge[doing=idle]": SKY, "badge[doing=error]": ROSE,
          "badge[who=Alex]": AMBER, "badge[build=building]": MINT, "badge[build=asked]": LILAC,
          "badge[build=landing]": LILAC, "badge[build=blocked]": ROSE}


def styles(door):
    have = {r.get("target"): r for r in door.rows("part-style", lens="work")}
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
    text = (HERE / "work.lens").read_text(encoding="utf-8").replace("$SHOP", shop[0]["id"])
    out["lens"] = painter.upsert(door, "lens", "work", title="Work", painter="components", text=text)
    mid = painter.upsert(door, "widget", "work", title="Work", style="bars", component_lens="work",
                         code=painter.widget_source())
    current = door.rows("widget", name="work")[0]
    if not current.get("on") or not any(g.get("words") == GRANTS and not g.get("revoked")
                                        for g in door.rows("grant", to=mid)):
        door.say("look " + mid)
        door.say("widget " + mid + " surface=window grants=" + Q(GRANTS) + " only=kind:work-view")
    out["widget"] = mid
    styles(door)
    if not door.rows("work-view"):
        out["view"] = door.say('make kind=work-view name="Alex\'s work view" sees=me')["made"][0]
    jeff = door.rows("house-agent", name="JEFF")
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
