"""Reviewable installer taking an already authenticated Door.

install(door) only authors the component, lens and widget. activate(door) is the
whole switch-on for a steward's door; `--live` runs it on the desktop (8810).
Neither opens a window, changes shell settings or restarts anything.
"""
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
spec = importlib.util.spec_from_file_location("search_painter_install", LAB / "painter/install.py")
painter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(painter)

# Requested activation manifest, not executed by install(). No writes or launch
# of native executables; ordinary window host still checks the viewer's rights.
REQUIRED_GRANTS = ("window.surface rows look look-view history components help component-health component-action "
                   "search window.open hear:make hear:set hear:forget hear:undo hear:component hear:component-action")


def install(door):
    source = (HERE / "lexical.js").read_text(encoding="utf-8")
    cid = painter.upsert(door, "component", "smart-search", category="collections",
        purpose="Apps and World text search: word matches and source evidence only.",
        settings="{}", parts='{"body":{"facts":"caller-visible search results"}}', slots="[]",
        gestures="evidence", example="root : smart-search", uses="Kernel search and caller-visible source evidence",
        limitations="Word matches only; up to 50 results before supported-kind/source filters. Capabilities unverified. Files, Email and Web disconnected. No inference.",
        code=source)
    # House must review exact code hash, then activate separately.
    lens = painter.upsert(door, "lens", "smart-search", title="Search",
        painter="components", text=(HERE / "search.lens").read_text(encoding="utf-8"))
    widget = painter.upsert(door, "widget", "smart-search", title="Search", style="bars",
        component_lens="smart-search", code=painter.widget_source(board_look=False))
    return dict(component=cid, lens=lens, widget=widget,
                review_sha256=hashlib.sha256(source.encode()).hexdigest(),
                requested_grants=REQUIRED_GRANTS)


def entry(door):
    """Explicit post-review one-click entry; creates no fixture apps or windows."""
    return painter.upsert(door, "button", "smart-search-button", label="Search",
                          bar="taskbar", icon="search", does="window.open smart-search")


def activate(door):
    """The whole switch-on, for a steward's door (component review and `widget` are steward words):
    install, review the exact component bytes, turn the widget on with only REQUIRED_GRANTS, then the
    one Search button. Re-running changes only what differs. Opens no window."""
    ids = install(door)
    if door.rows("component", name="smart-search")[0].get("reviewed_code") != ids["review_sha256"]:
        door.say("look " + ids["component"]); door.say("component " + ids["component"])
    current = door.rows("widget", name="smart-search")[0]
    granted = any(g.get("words") == REQUIRED_GRANTS and not g.get("revoked") for g in door.rows("grant", to=ids["widget"]))
    if not current.get("on") or not granted:
        door.say("look " + ids["widget"])
        door.say("widget " + ids["widget"] + " surface=window grants=" + painter.Q(REQUIRED_GRANTS))
    ids["button"] = entry(door)
    return ids


if __name__ == "__main__":
    # Alex's desktop. Run by a steward's session (the House cannot give a worker one); off switch:
    # `off <the smart-search widget>` and `forget <the smart-search-button>`.
    import argparse
    import sys
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--live", action="store_true")
    if not ap.parse_args().live:
        ap.error("use activate(door) in a hidden scratch world, or --live on the desktop after House review")
    sys.path.insert(0, str(LAB.parent / "window-lab/kernel-desktop"))
    from gaming_gate import assert_clear
    assert_clear()
    print(activate(painter.taskboard.live_door()))
