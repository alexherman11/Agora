"""Independent review proof: fresh headless desktop and guarded headless browser only.

Not run by the sandboxed worker. All fixtures live in --scratch (default: this
worktree's .work-proof). No real models or coding workers are started.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
DESK = LAB.parent / "desktop/kernel-desktop"
PY = Path("C:/Projects/Agora4/.venv/Scripts/python.exe")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scratch", type=Path, default=HERE.parents[3] / ".work-proof")
    ap.add_argument("--fake-port", type=int, default=8848)
    args = ap.parse_args()
    scratch = args.scratch.resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    for key in ("TMP", "TEMP", "TMPDIR"):
        os.environ[key] = str(scratch)
    tempfile.tempdir = str(scratch)
    os.environ["HOUSE_FAKE_MODEL"] = f"http://127.0.0.1:{args.fake_port}"
    sys.path[:0] = [str(LAB), str(DESK)]
    model = subprocess.Popen([str(PY), str(LAB / "modules/house/fake_model.py"), str(args.fake_port),
                              str(scratch / "fake-model.jsonl")], stdout=subprocess.DEVNULL,
                             creationflags=0x08000000 if sys.platform == "win32" else 0)
    desk = page = None
    checks = []
    def check(name, condition):
        checks.append(dict(check=name, ok=bool(condition)))
        if not condition:
            raise AssertionError(name)
        print("ok " + name, flush=True)
    try:
        from test_kdesk import Desk
        from painter.browser import Page
        desk = Desk()
        spec = importlib.util.spec_from_file_location("work_install_proof", HERE / "install.py")
        app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app)
        door = app.board.Door(desk.url, desk.entry.token("alex"))
        desk.wait(lambda: "house.active" in door.say("help all")["text"], 30)
        app.painter.install(door)
        ids = app.install(door)
        def task(title, **facts):
            tid = door.say('make kind=taskboard-task title=' + app.Q(title) + ''.join(
                ' ' + k + '=' + app.Q(v) for k, v in facts.items()))["made"][0]
            return tid
        live = task("Repair dock", lane="Now", who="JEFF")
        task("Owner approval", lane="Blocked", who="JEFF", blocked_on="Needs a decision", blocker_owner="Alex")
        for title, lane in (("Hidden finished", "Done"), ("Hidden queue", "Queued"), ("Hidden released", "Released")):
            task(title, lane=lane, who="JEFF", build="building", build_phase="working")
        task("Hidden old build", lane="Now", who="JEFF", build="landed", build_run="stale")
        page = Page(desk.url, door.token, ids["widget"], width=1440, height=900)
        page.c.call("Page.bringToFront")
        page.until('document.querySelectorAll(".work-line").length === 2', 45)
        text = page.js('document.body.textContent')
        check("current cards occur once and historical cards hide", text.count("Repair dock") == 1 and "Hidden" not in text)
        check("blocker and resolver are visible with names", "Needs a decision" in text and "Alex" in text)
        check("no opaque ids", not __import__('re').search(r'\bdk\d+\b', text))
        page.js('document.querySelector(".work-title").click()')
        page.until('!!document.querySelector("[role=dialog]")')
        check("clickable names open details", page.js('document.querySelector("[role=dialog]").textContent.includes("Close")'))
        page.js('[...document.querySelectorAll("[role=dialog] button")].find(b=>b.textContent==="Close").click()')
        door.say("look " + live)
        door.say(f"set {live} lane=Done")
        page.until('document.querySelectorAll(".work-line").length === 1', 20)
        check("finishing disappears without clearing", not page.js('document.body.textContent.includes("Repair dock")'))
        for n in range(20):
            task(f"Resident work {n:02}", lane="Now", who="JEFF")
        page.until('document.querySelector(".work-caption").textContent.includes("21")', 30)
        check("overflow uses pages", page.js('!document.querySelector(".work-pagination button:last-child").disabled'))
        before = page.js('document.querySelector(".work-line").textContent')
        page.js('document.querySelector(".work-pagination button:last-child").click()')
        page.until('document.querySelector(".work-line").textContent !== ' + json.dumps(before))
        check("next page reveals other work", True)
        page.shot(scratch / "work-overview.png")
        for width, height in ((1440,900), (700,600), (420,700)):
            page.c.call("Emulation.setDeviceMetricsOverride", width=width, height=height, deviceScaleFactor=1, mobile=False)
            page.js('window.dispatchEvent(new Event("resize"))')
            page.until('document.querySelector(".work-overview").getBoundingClientRect().bottom <= innerHeight')
            check(f"no page scroll at {width}px", page.js('document.scrollingElement.scrollHeight <= innerHeight && document.scrollingElement.scrollWidth <= innerWidth'))
            page.until('[...document.querySelectorAll(".work-line")].every(n=>n.getBoundingClientRect().bottom <= document.querySelector(".work-rows").getBoundingClientRect().bottom)')
        page.shot(scratch / "work-phone.png")
        before = page.js('getComputedStyle(document.querySelector(".work-overview")).getPropertyValue("--work-ink")')
        dark = next(r for r in door.say("theme.list")["rows"] if any(
            word in r.get("name", "").lower() for word in ("dusk", "mocha", "night", "dark")))
        door.say("theme.use " + dark["id"])
        page.until('getComputedStyle(document.querySelector(".work-overview")).getPropertyValue("--work-ink") !== ' + json.dumps(before), 20)
        check("Work responds to the viewer theme", True)
        page.shot(scratch / "work-themed.png")
        check("no stopped components", not page.js('!!document.querySelector(".component-stopped")'))
    finally:
        if page:
            page.close()
        if desk:
            desk.close()
        model.terminate()
        model.wait(timeout=15)
        (scratch / "work-proof.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
