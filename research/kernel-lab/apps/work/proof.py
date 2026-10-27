"""proof: Work in a fresh hidden desktop (test_kdesk.Desk, headless modules and browser, a scripted model). Never a live model,
never a window on Alex's screen.

    python proof.py [--port 8836]

Ran checks: the page paints JEFF from house.who and the task cards; Open shows him up close (his chat, his record
outside any chat); typing in the box says into his chat and he answers there; a card with build= appears under
BUILDS; what he is doing changing is a happening the page hears. Pictures in evidence/.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
DESK = LAB.parent / "window-lab" / "kernel-desktop"
PY = LAB.parents[1] / ".venv" / "Scripts" / "python.exe"
NAME = "work-proof"
NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(HERE))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8836)
    ap.add_argument("--fake-port", type=int, default=8848)
    a = ap.parse_args(argv)
    ev = HERE / "evidence"
    ev.mkdir(exist_ok=True)
    checks, procs, page = [], [], None

    def check(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": str(detail)[:300]})
        print(("ok   " if ok else "FAIL ") + name + (f" · {detail}" if detail else ""), flush=True)

    try:
        procs.append(subprocess.Popen([str(PY), str(LAB / "modules/house/fake_model.py"), str(a.fake_port),
                                       str(ev / "fake-model-log.jsonl")], stdout=subprocess.DEVNULL,
                                      creationflags=NO_WINDOW))
        # a fresh hidden desktop in this process (test_kdesk.Desk, as the painter's own proofs use), so the headless
        # page can be given the widget host's key; its house runs JEFF against the scripted model
        os.environ["HOUSE_FAKE_MODEL"] = f"http://127.0.0.1:{a.fake_port}"
        sys.path.insert(0, str(DESK))
        from test_kdesk import Desk
        desk = Desk()
        procs.append(type("Closer", (), {"kill": lambda self: desk.close()})())
        url, token = desk.url, desk.entry.token("alex")
        import importlib.util
        spec = importlib.util.spec_from_file_location("work_painter_install2", LAB / "painter/install.py")
        painter_install = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(painter_install)
        import install
        door = install.board.Door(url, token)
        painter_install.install(door)               # the reviewed components and the Task board, as live has them
        door.say('make kind=shell-settings name="Shell settings"')        # as the live desktop has (shell_install.py)
        ids = install.install(door)
        check("installed through the door (lens, widget, Alex's work-view, dock)", ids.get("widget"), ids)
        agent = door.rows("house-agent", name="JEFF")[0]
        convo = door.rows("chat", name="Conversation")[0]["id"]
        door.say("look " + agent["id"])
        door.say(f"set {agent['id']} want=awake")
        door.say(f'say {convo} text="hello from the proof RUN: rows chat | frobnicate"')
        task = door.say('task-add title="Dock: battery reads wrong" who=JEFF')["made"][0]
        door.say("look " + task)
        door.say(f"set {task} build=building builder=builder-a")
        dock = door.rows("shell-settings")[0].get("dock_apps", "")
        check("Work is in the dock's apps", "work" in dock.split(","), dock)
        view = door.rows("work-view")[0]
        check("JEFF is open at first, so the right side is never empty", view.get("agent") == agent["person"])

        from painter.browser import Page
        page = Page(url, token, ids["widget"], width=1500, height=1000)
        page.c.call("Page.bringToFront")            # the painter paints only a page that is seen (27 Oct)
        try:
            page.until('document.querySelectorAll(".band").length >= 5', 60)
            page.until('document.querySelectorAll(".console-line").length > 0 && '
                       'document.body.textContent.includes("Done:")', 40)
        except AssertionError:
            page.shot(ev / "work-failed.png")
            raise
        bands = page.js('[...document.querySelectorAll(".band")].map(b => b.querySelector(".band-head").textContent)')
        check("bands with a count, an empty band one quiet line",
              any(b.startswith("Builds1") for b in bands) and any("Needs you· nothing waits on you" == b for b in bands),
              " | ".join(bands))
        text = page.js("document.body.textContent")
        check("a card with build= is a line under Builds, with its builder", "Dock: battery reads wrong" in text
              and "builder-a" in text)
        log = page.js('[...document.querySelectorAll(".console-line")].map(l => l.className.split(" ")[1] + " " + l.textContent)')
        at = lambda test: next((i for i, x in enumerate(log) if test(x)), -1)  # noqa: E731
        heard = at(lambda x: x.startswith("heard") and "hello from the proof" in x)
        act = at(lambda x: x.startswith("act") and "rows chat" in x and "(1 refused)" in x)
        done = at(lambda x: x.startswith("said") and "Done:" in x)
        check("his log is a terminal: Alex's line, his receipts under his line, his answer after them, in time order",
              0 <= heard < act < done and sum(1 for x in log if x.startswith("act") and "rows chat" in x) == 1,
              f"lines {heard}, {act}, {done} of {len(log)}")
        font = page.js('getComputedStyle(document.querySelector(".console-log")).fontFamily')
        check("the log is monospaced", any(f in font for f in ("mono", "Mono", "Cascadia", "Consolas")), font)
        fill = page.js('[document.querySelector(".console").getBoundingClientRect().height, innerHeight, '
                       'document.querySelector(".console").getBoundingClientRect().width, innerWidth]')
        check("the log fills the right side", fill[0] > 0.75 * fill[1] and fill[2] > 0.5 * fill[3],
              f"{fill[0]:.0f} of {fill[1]} px high, {fill[2]:.0f} of {fill[3]} px wide")
        page.shot(ev / "work-overview.png")
        at_input = page.point(".console-prompt input")            # typed as Alex would: click, type, Enter
        page.c.call("Input.dispatchMouseEvent", type="mousePressed", button="left", clickCount=1, **at_input)
        page.c.call("Input.dispatchMouseEvent", type="mouseReleased", button="left", clickCount=1, **at_input)
        page.c.call("Input.insertText", text="from the Work page")
        for kind in ("keyDown", "keyUp"):
            page.c.call("Input.dispatchKeyEvent", type=kind, key="Enter", code="Enter", windowsVirtualKeyCode=13,
                        **({"text": chr(13)} if kind == "keyDown" else {}))
        lines = []
        end = time.time() + 40
        while time.time() < end:
            lines = door.say(f"chat {convo} limit=10")["rows"]
            if any(r["text"] == "from the Work page" for r in lines) and lines[-1]["by"] == "JEFF":
                break
            page.c.js("0")          # the test browser's firewall lets a request through only while we read its events
            time.sleep(0.3)
        check("the prompt says into his chat, as Alex, and he answers there",
              any(r["text"] == "from the Work page" and r["by"] == "Alex" for r in lines) and lines[-1]["by"] == "JEFF",
              " | ".join(f"{r['by']}: {r['text']}" for r in lines[-3:]))
        page.until('[...document.querySelectorAll(".console-line.said")].some(l => l.textContent.includes("Heard you."))', 20)
        try:
            page.until('document.querySelector(".console-prompt input").value === ""', 10)
        except AssertionError:
            pass
        box = page.js('document.querySelector(".console-prompt input").value')
        check("the box is empty again once the line is said", box == "", repr(box))
        own = page.js('[...document.querySelectorAll(".console-line.own")].map(l => l.textContent)')
        check("what he said outside any chat is marked so, by what woke him, with no ids",
              own and all("[outside any chat · Alex gave you a task: Dock: battery reads wrong]" in x and "dk" not in x
                          for x in own), " | ".join(own))
        size = page.js("[document.scrollingElement.scrollHeight, innerHeight]")
        check("the page itself never scrolls (only the log does)", size[0] <= size[1], f"{size[0]} of {size[1]} px")
        grants = door.rows("grant", to=ids["widget"])[0].get("words", "")
        check("the page hears house.doing (what an agent is doing, never recorded)", "hear:house.doing" in grants)
        stream = [e["params"]["entry"] for e in page.errors if e.get("method") == "Log.entryAdded"
                  and "/door/stream" in e["params"]["entry"].get("url", "")]
        check("'the kernel is away' here is the test browser's firewall refusing /door/stream, not a disconnect",
              stream and all("BLOCKED_BY_CLIENT" in x.get("text", "") for x in stream),
              f"{len(stream)} stream requests, each {stream[0].get('text') if stream else ''}")
        page.shot(ev / "work-jeff-talked.png")
        themes = door.say("theme.list")                  # the system theme: wear a dark one and look again
        dark = next((r for r in themes.get("rows") or [] if any(w in str(r.get("name", "")).lower()
                                                                  for w in ("night", "mocha", "dark", "dusk"))), None)
        if not dark:
            check("a dark theme to wear", False, themes.get("text", "")[:200])
        else:
            door.say(f"theme.use {dark['id']}")
            try:
                page.until(r'(() => { const c = getComputedStyle(document.querySelector(".console")).backgroundColor.match(/\d+/g).map(Number); '
                           'return c[0] + c[1] + c[2] < 200 })()', 20)
            except AssertionError:
                pass
            look = page.js('[getComputedStyle(document.querySelector(".console")).backgroundColor, '
                           'getComputedStyle(document.querySelector(".console-line.said")).color, '
                           'getComputedStyle(document.body).backgroundColor]')
            dim = lambda c: sum(map(int, __import__("re").findall(r"\d+", c)[:3]))  # noqa: E731
            check(f"Work wears the system theme ({dark.get('name')}): a dark log with light words",
                  dim(look[0]) < 200 and dim(look[1]) > 350, " · ".join(look))
            page.shot(ev / "work-dark.png")
            door.say("theme.use place")
    finally:
        if page:
            page.close()
        for p in reversed(procs):
            p.kill()
    ok = bool(checks) and all(c["ok"] for c in checks)
    (ev / "work-proof.json").write_text(json.dumps({"at": time.strftime("%Y-%m-%d %H:%M"), "complete": ok,
                                                    "checks": checks}, indent=1), encoding="utf-8")
    print("all checks ok" if ok else "SOME CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
