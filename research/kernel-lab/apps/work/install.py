"""Install Work (work.lens) through the door: its components, lens, widget and Work in the dock. No kernel imports, no
source changes to the world; re-running updates what changed and leaves the rest. Opens no window.

    python install.py [--world <dir>] [--port 8810]

house.active joins visible card state with current holders; old build phases do not keep finished work visible.
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
          "house.active house.who house.activity house.log chat say set hear:say hear:house.doing hear:task-*")


# The two general components Work arranges, beside the catalogue's (components/*.js), with their cards.
COMPONENTS = {
    "work-overview": dict(category="collections", purpose="Current work with bounded pages; nothing scrolls.",
        settings="{}", parts='{"body": {"facts": "bound visible row"}}', slots='["rows"]',
        gestures="", example="root : work-overview", uses="Work", limitations="Pages fit the available height."),
    "work-line": dict(category="content", purpose="One current card, holder and blocker; names open details.",
        settings=json.dumps({key: {"type": "text", "default": ""} for key in
                             ("title", "owner", "state", "blocker", "resolver", "detail", "next")}),
        parts='{"body": {"facts": "bound visible row"}}', slots="[]", gestures="",
        example='root : work-line, title "Current work"', uses="Work",
        limitations="Long lines are ellipsized; activate a name for details."),
}


def components(door):
    import hashlib
    for name, card in COMPONENTS.items():
        code = (LAB / "components" / f"{name}.js").read_text(encoding="utf-8")
        t = painter.upsert(door, "component", name, **card, code=code)
        if door.rows("component", name=name)[0].get("reviewed_code") != hashlib.sha256(code.encode()).hexdigest():
            door.say("look " + t)
            door.say("component " + t)                 # the steward reviews these exact bytes (ARRANGEMENT.md)


def install(door):
    out = {}
    components(door)
    text = (HERE / "work.lens").read_text(encoding="utf-8")
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
    if not door.rows("work-view"):
        out["view"] = door.say('make kind=work-view name="Alex\'s work view" sees=me')["made"][0]
    painter.app(door, "work", "Work", "work")
    # What Work hides and says is the world's (4 Nov): seeded once from the House's defaults, then Alex's to change.
    if not door.rows("work-settings"):
        overview = _load("work_overview_defaults", LAB / "modules/house/work_overview.py")
        door.say("make kind=work-settings name=\"Work settings\" "
                 + " ".join(f"{k}={Q(v)}" for k, v in overview.DEFAULTS.items()))
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
