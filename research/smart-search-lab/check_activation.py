"""Hidden check of the Search switch-on: a headless scratch desk only, no visible window, no live world.

    python check_activation.py
"""
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
DESK = ROOT / "research/window-lab/kernel-desktop"
sys.path[:0] = [str(DESK), str(ROOT / "research/kernel-lab")]
from test_kdesk import Desk  # noqa: E402

spec = importlib.util.spec_from_file_location("smart_search_install", ROOT / "research/kernel-lab/apps/smart-search/install.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

failed = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f" :: {detail}"))
    if not ok:
        failed.append(name)


desk = Desk()
try:
    door = app.painter.taskboard.Door(desk.url, desk.entry.token("alex"))
    ids = app.activate(door)
    widget = door.rows("widget", name="smart-search")[0]
    component = door.rows("component", name="smart-search")[0]
    grants = [g for g in door.rows("grant", to=ids["widget"]) if not g.get("revoked")]
    buttons = door.rows("button", name="smart-search-button")
    check("widget is on", widget.get("on") is True, widget)
    check("component bytes reviewed", component.get("reviewed_code") == ids["review_sha256"], component.get("reviewed_code"))
    check("only the required grants", [g.get("words") for g in grants] == [app.REQUIRED_GRANTS], grants)
    check("one Search button on the taskbar", [(b["label"], b["bar"], b["does"]) for b in buttons]
          == [("Search", "taskbar", "window.open smart-search")], buttons)
    check("switch-on opens no window", desk.window("smart-search") is None)
    again = app.activate(door)
    check("re-running is a no-op", again == ids and len(door.rows("grant", to=ids["widget"])) == len(grants)
          and len(door.rows("button", name="smart-search-button")) == 1, again)
    hits = door.say("search " + app.painter.Q("Search") + " limit=50")["rows"]
    check("kernel search finds the Search button as an App", any(r["id"] == ids["button"] for r in hits),
          [(r["kind"], r.get("name")) for r in hits])
    # A worker's own session cannot do the steward half; it must refuse, not half-switch.
    worker = Desk.say(desk, "widget " + ids["widget"] + " surface=window grants=search", "claude")
    check("a non-steward cannot re-grant the widget", not worker.get("ok"), worker)
    opened = door.say("window.open smart-search")
    check("Search opens in its own window (hidden desk)", opened.get("ok") and desk.wait(lambda: desk.window("smart-search"), 15), opened)
finally:
    desk.close()
print(f"{'FAILED ' + str(len(failed)) if failed else 'all passed'}")
sys.exit(1 if failed else 0)
