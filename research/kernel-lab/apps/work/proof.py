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
        door.say(f'say {convo} text="hello from the proof"')
        task = door.say('task-add title="Dock: battery reads wrong" who=JEFF')["made"][0]
        door.say("look " + task)
        door.say(f"set {task} build=building builder=builder-a")
        dock = door.rows("shell-settings")[0].get("dock_apps", "")
        check("Work is in the dock's apps", "work" in dock.split(","), dock)

        from painter.browser import Page
        page = Page(url, token, ids["widget"], width=1500, height=1000)
        page.c.call("Page.bringToFront")            # the painter paints only a page that is seen (27 Oct)
        try:
            page.until('document.querySelectorAll("[data-component]").length > 0', 60)
            page.until('document.body.textContent.includes("JEFF") && document.body.textContent.includes("AT WORK")', 30)
        except AssertionError:
            page.shot(ev / "work-failed.png")
            raise
        text = page.js("document.body.textContent")
        check("the page paints JEFF from house.who", "JEFF" in text, text[:200].replace("\n", " · "))
        check("a card with build= is under BUILDS, with its builder", "Dock: battery reads wrong" in text
              and "builder-a" in text, "building · Dock: battery reads wrong · builder-a")
        page.shot(ev / "work-overview.png")
        page.js('[...document.querySelectorAll("button")].find(b => b.innerText.trim() === "Open").click()')
        page.until('document.body.textContent.includes("IN THEIR CHAT")', 20)
        page.until('document.body.textContent.includes("hello from the proof")', 20)
        text = page.js("document.body.textContent")
        check("Open shows him up close: his chat and his record outside it",
              "IN THEIR CHAT" in text and "OUTSIDE ANY CHAT" in text and "Heard you." in text, "")
        page.shot(ev / "work-jeff-open.png")
        page.js('(() => { const i = [...document.querySelectorAll("input")].find(x => (x.placeholder || "").startsWith("Write to JEFF"));'
                ' i.value = "from the Work page"; i.dispatchEvent(new Event("change", {bubbles: true})); return true })()')
        page.until('document.body.textContent.includes("from the Work page")', 40)
        lines = []
        end = time.time() + 30
        while time.time() < end:
            lines = door.say(f"chat {convo} limit=10")["rows"]
            if any(r["text"] == "from the Work page" for r in lines) and lines[-1]["by"] == "JEFF":
                break
            time.sleep(0.3)
        check("the box says into his chat, as Alex, and he answers there",
              any(r["text"] == "from the Work page" and r["by"] == "Alex" for r in lines) and lines[-1]["by"] == "JEFF",
              " | ".join(f"{r['by']}: {r['text']}" for r in lines[-3:]))
        grants = door.rows("grant", to=ids["widget"])[0].get("words", "")
        check("the page hears house.doing (what an agent is doing, never recorded)", "hear:house.doing" in grants)
        page.until('document.body.textContent.includes("Heard you.")', 20)
        page.shot(ev / "work-jeff-talked.png")
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
