"""Install Music through the door, opening no window. Source-only until House review."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


board = load("music_board_install", LAB / "apps/taskboard/install.py")
painter = load("music_painter_install", LAB / "painter/install.py")
Q = board.quote
GRANTS = ("window.surface rows look look-view history components help component-health component-action "
          "hear:make hear:set hear:forget hear:undo hear:component hear:component-action "
          "media.now media.pause media.resume media.next media.prev media.shuffle media.repeat")


def install(door):
    code = (HERE / "music-components.js").read_text(encoding="utf-8")
    settings = {key: {"type": "text", "default": ""} for key in
                ("title", "artist", "album", "player", "art", "repeat")}
    settings.update({key: {"type": "number", "default": 0} for key in ("position", "duration")})
    settings.update(playing={"type": "boolean", "default": False},
                    can={"type": "json", "default": {}}, shuffle={"type": "fact"})
    for name in ("music-panel", "music-song"):
        tid = painter.upsert(door, "component", name, category="content", code=code,
            purpose="Music from the Windows media session; reported progress only.",
            settings=json.dumps(settings if name == "music-song" else {}),
            parts=json.dumps({key: {} for key in
                             ("body", "art", "source", "title", "artist", "progress", "controls")}),
            slots='["default"]' if name == "music-panel" else "[]",
            gestures="pause resume next prev shuffle repeat" if name == "music-song" else "",
            example=f"root : {name}", limitations="No seek or Spotify account controls.")
        if door.rows("component", name=name)[0].get("reviewed_code") != hashlib.sha256(code.encode()).hexdigest():
            door.say("look " + tid)
            door.say("component " + tid)
    lens = painter.upsert(door, "lens", "music", title="Music", painter="components",
                          text=(HERE / "music.lens").read_text(encoding="utf-8"))
    widget = painter.upsert(door, "widget", "music", title="Music", style="bars",
                            component_lens="music", code=painter.widget_source(board_look=False))
    current = door.rows("widget", name="music")[0]
    grants = [g for g in door.rows("grant", to=widget) if not g.get("revoked")]
    if not current.get("on") or [g.get("words") for g in grants] != [GRANTS]:
        door.say("look " + widget)
        if current.get("on"):
            door.say("off " + widget)
            door.say("look " + widget)
        door.say("widget " + widget + " surface=window grants=" + Q(GRANTS))
    shells = door.rows("shell-settings")
    if not shells:
        # A new world has no settings until somebody customizes the shell.
        # The dock's fallback list does not include optional applications.
        door.say('make kind=shell-settings dock_apps="lines,help,board,taskboard,appearance,feed,music"')
    else:
        # ShellKit reads the first settings row; keep its app order and other facts.
        shell = shells[0]
        apps = (shell.get("dock_apps") or "lines,help,board,taskboard,appearance,feed").replace(" ", "")
        if "music" not in apps.split(","):
            door.say("look " + shell["id"])
            door.say("set " + shell["id"] + " dock_apps=" + Q(apps + ",music"))
    return {"lens": lens, "widget": widget}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if not args.live:
        parser.error("Use install(door) in a fixture, or --live after House review.")
    print(install(board.live_door()))
