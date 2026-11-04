"""Install the Appearance app through ordinary door words (research/kernel-lab/theme/THEMES.md).

install(door) is scratch-safe: it makes the component, its arrangement, the widget and the taskbar button with `make`, `set`,
`look`, `component` and `widget`, the words every builder has. Nothing here restarts anything or opens a window.
A coordinator rolls it out live with `python -m theme.install --live` after adopting the theme module.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
sys.path.insert(0, str(LAB))
spec = importlib.util.spec_from_file_location("painter_install", LAB / "painter/install.py")
painter_install = importlib.util.module_from_spec(spec)
spec.loader.exec_module(painter_install)
upsert, widget_source, Q = painter_install.upsert, painter_install.widget_source, painter_install.Q

GRANTS = ("window.surface rows look look-view history components help component-health component-action "
          "theme.* clock make set undo upload files.convert attach board.post "
          "hear:make hear:set hear:forget hear:undo hear:component hear:component-action hear:theme.changed hear:upload hear:attach")


def card():
    """The component's card: what a neighbour reads before arranging it elsewhere."""
    return dict(
        name="appearance", category="content",
        purpose="Choose, make, import, export and share themes: live preview cards of the whole desktop, Try for 30 seconds, "
                "Use just for me, an editor with a live preview, and a post to the board with the theme attached.",
        settings=json.dumps({}),
        parts=json.dumps({p: dict(facts="none") for p in "gallery card editor exchange".split()}),
        slots=json.dumps([]),
        gestures="try keep revert use useme follow make edit import post attach",
        example="root : appearance\n  watch reading:\"theme.list\"\n  on try do theme.try $theme",
        uses="Appearance window; any place that lets people choose how it looks",
        limitations="Reads theme.list, theme.current, theme.options and board-channel; says theme.* and board words only. "
                    "Pictures in an imported file stay inside it; a file over 60 KB is shared as a post attachment, not pasted.")


def install(door):
    ids = {}
    code = (HERE / "components/appearance.js").read_text(encoding="utf-8")
    c = card()
    name = c.pop("name")
    t = upsert(door, "component", name, **c, code=code)
    current = door.rows("component", name=name)[0]
    if current.get("reviewed_code") != hashlib.sha256(code.encode()).hexdigest():
        door.say("look " + t)
        door.say("component " + t)
    ids["component"] = t
    upsert(door, "lens", "appearance", title="Appearance", painter="components",
           text=(HERE / "appearance.lens").read_text(encoding="utf-8"), view=json.dumps({"tab": "gallery"}))
    mid = upsert(door, "widget", "appearance", title="Appearance", style="bars", component_lens="appearance", code=widget_source())
    current = door.rows("widget", name="appearance")[0]
    matching = any(g.get("words") == GRANTS and not g.get("revoked") for g in door.rows("grant", to=mid))
    if not current.get("on") or not matching:
        door.say("look " + mid)
        door.say("widget " + mid + " surface=window grants=" + Q(GRANTS))
    ids["widget"] = mid
    ids["button"] = upsert(door, "button", "appearance-button", label="Appearance", bar="taskbar", icon="palette",
                           does="window.open appearance")
    painter_install.app(door, "appearance", "Appearance", "appearance")
    return ids


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--live", action="store_true")
    args = ap.parse_args()
    if not args.live:
        ap.error("use install(door) for a scratch world, or explicitly --live")
    desktop = LAB.parents[0] / "window-lab/kernel-desktop"
    sys.path.insert(0, str(desktop))
    from gaming_gate import assert_clear
    spec2 = importlib.util.spec_from_file_location("taskboard_install", LAB / "apps/taskboard/install.py")
    tb = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(tb)
    assert_clear()
    door = tb.live_door()
    if not door.request("/see", {"line": "help theme.use"}).get("ok"):
        raise RuntimeError("The coordinator must adopt the theme module before a live install; no restart attempted.")
    print(json.dumps(install(door)))


if __name__ == "__main__":
    main()
