"""Hidden end-to-end Music proof; fake Windows session, real module and guarded painter.

Run with the pinned Python. Fixtures and screenshots stay in .music-proof.
"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import types
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
DESK = LAB.parent / "desktop/kernel-desktop"
ROOT = LAB.parents[1]
sys.path[:0] = [str(LAB), str(DESK)]


def load_app():
    spec = importlib.util.spec_from_file_location("music_install", HERE / "install.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    return app


def fake_session(state_file):
    """Run the actual adapter, substituting only its Windows session dependency."""
    import kd_media
    kd_media.HEADLESS = False
    path = Path(state_file)
    def state():
        return json.loads(path.read_text(encoding="utf-8"))
    class Session:
        def start(self):
            return True
        def state(self):
            return {"ok": True, "s": state()}
        def stop(self):
            pass
    def press(action):
        s = state()
        with path.with_suffix(".actions").open("a", encoding="utf-8") as f:
            f.write(action + "\n")
        if action == "play":
            s["status"] = "Paused" if s["status"] == "Playing" else "Playing"
        elif action in ("next", "prev"):
            s["title"] = "Next song" if action == "next" else "Previous song"
            s["position"] = 0
        elif action == "shuffle":
            s["shuffle"] = not s["shuffle"]
        elif action == "repeat":
            s["repeat"] = {"None": "List", "List": "Track", "Track": "None"}[s["repeat"]]
        path.write_text(json.dumps(s), encoding="utf-8")
        return "fake session"
    sys.modules["media"] = types.SimpleNamespace(
        SESSION=Session(), ART=path.parent, player_of=lambda app: "Fixture player", press=press)
    kd_media.Media().run()


def main():
    scratch = ROOT / ".music-proof"
    scratch.mkdir(exist_ok=True)
    temp = ROOT / ".tmp"
    temp.mkdir(exist_ok=True)
    for key in ("TMP", "TEMP", "TMPDIR"):
        os.environ[key] = str(temp)
    tempfile.tempdir = str(temp)
    from PIL import Image
    art = scratch / "album.png"
    Image.new("RGB", (480, 480), "#c3dfcc").save(art)
    state_file = scratch / "session.json"
    state = dict(app="fixture", title="Morning light", artist="Test artist", album="A quiet album",
                 status="Playing", position=30, end=180, updated=1, art=str(art), shuffle=False, repeat="None",
                 can={key: True for key in ("play", "pause", "next", "prev", "shuffle", "repeat")})
    def update(**values):
        state.update(values)
        state_file.write_text(json.dumps(state), encoding="utf-8")
    update()
    actions = state_file.with_suffix(".actions")
    actions.write_text("", encoding="utf-8")
    import kdesk
    original = kdesk.module_specs
    def specs(headless=False):
        rows = original(headless)
        for row in rows:
            if row["name"] == "media":
                row["run"] = [sys.executable, str(Path(__file__).resolve()), "--session", str(state_file)]
        return rows
    kdesk.module_specs = specs
    from test_kdesk import Desk
    from painter.browser import Page
    from test_shell_components import ShellPage
    from test_kdesk import scratch_dir
    class BrowserScratch:
        """Browser fixture profile with inherited access, matching the world fixture."""
        def __init__(self, prefix="", **_):
            self.name = scratch_dir(prefix)
        def cleanup(self):
            target = Path(self.name).resolve()
            if temp.resolve() not in target.parents:
                raise AssertionError("browser profile outside fixture temp")
            shutil.rmtree(target, ignore_errors=True)
    def hidden_page(*args, factory=Page, **kwargs):
        # Only the browser constructor uses this replacement. No production temp
        # behavior or filesystem permissions change.
        import widget_browser
        popen = widget_browser.subprocess.Popen
        with (scratch / "browser-stderr.log").open("a", encoding="utf-8") as log:
            def captured_popen(*args, **kwargs):
                kwargs["stderr"] = log
                return popen(*args, **kwargs)
            with patch("widget_browser.tempfile.TemporaryDirectory", BrowserScratch), patch(
                    "widget_browser.subprocess.Popen", captured_popen):
                return factory(*args, **kwargs)
    desk = page = dock = None
    checks = []
    def check(name, ok):
        checks.append({"check": name, "ok": bool(ok)})
        if not ok:
            raise AssertionError(name)
        print("PASS " + name, flush=True)
    try:
        desk = Desk()
        app = load_app()
        door = app.board.Door(desk.url, desk.entry.token("alex"))
        import shell_install
        shell_install.install(door)
        ids = app.install(door)
        check("installer is idempotent", ids == app.install(door))
        check("Music is in the dock settings",
              "music" in door.rows("shell-settings")[0]["dock_apps"].split(","))
        now = door.say("media.now")["rows"][0]
        check("actual adapter reads status, artwork and reported position",
              now["playing"] and now["position"] == 30 and now["art"].startswith("data:image/jpeg"))
        # The real dock opens the headless window through its guarded gesture.
        shell = door.rows("widget", name="shell-dock")[0]
        if shell:
            # Match test_dock_launch's actual shell host. A generic widget page
            # has no AGORA_SHELL context for the bar's native layout/icon calls.
            key = desk.srv.RequestHandlerClass.widget_broker.guard_key
            dock = hidden_page(desk.url, door.token, "dock", key, 1440, 180, factory=ShellPage)
            # Fact attributes can also occur on noninteractive painter wrappers.
            # Target the launch button, as the dock's own launch proof does.
            dock.until("""document.querySelector('button[data-id="app:music"]')?.getAttribute("aria-label") === "Music, not running" """, 30)
            # Observe, without substituting, the same Data.act path used by the
            # existing dock launch regression. A refusal must identify itself.
            dock.js("""(() => {
              const D=ShellKit.Data, act=D.act.bind(D);
              globalThis.musicDockCalls=[]; globalThis.musicDockReplies=[];
              D.act=async line=>{
                musicDockCalls.push(line);
                const reply=await act(line);
                musicDockReplies.push({ok:reply.ok,text:reply.text});
                return reply;
              };
            })()""")
            dock.js("""document.querySelector('button[data-id="app:music"]').click()""")
            dock.until("musicDockReplies.length > 0", 15)
            launch = dock.js("({calls:musicDockCalls,replies:musicDockReplies})")
            (scratch / "dock-launch.json").write_text(json.dumps(launch, indent=2), encoding="utf-8")
            check("dock dispatches window.open music", launch["calls"][0] == "window.open music")
            check("dock accepts Music launch: " + str(launch["replies"][0]), launch["replies"][0]["ok"])
        else:
            # Some desktop generations call the shell widget taskbar.
            raise AssertionError("Expected shell-dock widget for actual dock proof")
        desk.wait(lambda: desk.window("music"), 15)
        check("Music opens from the dock", True)
        page = hidden_page(desk.url, door.token, ids["widget"], width=900, height=650)
        page.until('!!document.querySelector(".music-song")', 30)
        check("song, artist and album render", all(x in page.js("document.body.innerText") for x in
              ("Morning light", "Test artist", "A quiet album")))
        page.until('document.querySelector(".music-art").naturalWidth > 0')
        check("album artwork decodes", True)
        check("reported progress is 30 seconds", page.js('document.querySelector("progress").value') == 30)
        time.sleep(3.5)
        check("playing does not animate progress", page.js('document.querySelector("progress").value') == 30)
        update(position=44, updated=2)
        page.until('document.querySelector("progress").value === 44', 15)
        check("new reported position updates progress", True)
        for action, condition in [
            ("pause", '!!document.querySelector("[data-action=resume]")'),
            ("resume", '!!document.querySelector("[data-action=pause]")'),
            ("next", 'document.querySelector(".music-title").textContent==="Next song"'),
            ("prev", 'document.querySelector(".music-title").textContent==="Previous song"'),
            ("shuffle", 'document.querySelector("[data-action=shuffle]").getAttribute("aria-pressed")==="true"'),
            ("repeat", 'document.querySelector("[data-action=repeat]").title==="Repeat: List"'),
            ("repeat", 'document.querySelector("[data-action=repeat]").title==="Repeat: Track"'),
            ("repeat", 'document.querySelector("[data-action=repeat]").title==="Repeat: None"'),
        ]:
            # Capabilities arrive with the reading; wait for the actual control
            # and keep its button selector aligned with music-components.js.
            selector = f'button[data-action="{action}"]'
            page.until("!!document.querySelector(" + json.dumps(selector) + ")", 15)
            page.js("document.querySelector(" + json.dumps(selector) + ").click()")
            page.until(condition, 20)
            check(action + " works through guarded media word", True)
        check("controls reached the fake Windows session",
              actions.read_text().splitlines() == ["play", "play", "next", "prev", "shuffle", "repeat", "repeat", "repeat"])
        # Check the most crowded state before removing optional controls.
        for width, height in ((900, 650), (420, 740)):
            page.c.call("Emulation.setDeviceMetricsOverride", width=width, height=height, deviceScaleFactor=1, mobile=False)
            page.c.until(f"innerWidth === {width}")
            # The widget's outer border takes space from its child viewport.
            frame_width = page.c.js('document.querySelector("#widget-surface iframe").clientWidth')
            page.until(f"innerWidth === {frame_width}")
            page.js("new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))")
            layout = page.js("""(() => {
              const bounds=n=>{
                const r=n.getBoundingClientRect();
                return {left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height};
              };
              return {width:innerWidth,height:innerHeight,
                scrollWidth:document.scrollingElement.scrollWidth,
                scrollHeight:document.scrollingElement.scrollHeight,
                bodyPadding:getComputedStyle(document.body).padding,
                panel:bounds(document.querySelector('.music-panel')),
                art:bounds(document.querySelector('.music-art')),
                controls:[...document.querySelectorAll('.music-controls button')].map(bounds)};
            })()""")
            (scratch / f"layout-{width}.json").write_text(json.dumps(layout, indent=2), encoding="utf-8")
            check(f"fits {width}px without page scrolling",
                  layout["scrollHeight"] <= layout["height"] and layout["scrollWidth"] <= layout["width"])
            check(f"all five controls fit {width}px", len(layout["controls"]) == 5 and all(
                b["left"] >= 0 and b["top"] >= 0 and b["right"] <= layout["width"]
                and b["bottom"] <= layout["height"] for b in layout["controls"]))
            if width == 420:
                check("narrow Music owns its padding", layout["bodyPadding"] == "0px"
                      and layout["panel"]["top"] == 0)
                check("narrow CSS keeps artwork compact", layout["art"]["width"] <= 180
                      and layout["art"]["height"] <= 180)
                page.shot(scratch / "music-narrow.png")
        # Preserve state changed by controls, then simulate support disappearing.
        state.update(json.loads(state_file.read_text()))
        update(can={key: key not in ("shuffle", "repeat") for key in state["can"]})
        page.until('!document.querySelector("[data-action=shuffle]") && !document.querySelector("[data-action=repeat]")', 15)
        check("unsupported shuffle and repeat disappear", True)
        check("Spotify account controls omitted", not page.js('!!document.querySelector("[data-action=like],[data-action=connect]")'))
        page.shot(scratch / "music-light.png")
        rgb = page.js('getComputedStyle(document.querySelector(".music-panel")).backgroundColor')
        check("light theme", sum(int(n) for n in __import__("re").findall(r"\d+", rgb)[:3]) > 600)
        update(title="", can={})
        page.until('!document.querySelector(".music-song")', 15)
        check("empty session explains what to do", page.js(
            'getComputedStyle(document.querySelector(".music-empty")).display!=="none"'))
        check("no component failures", not page.js('!!document.querySelector(".component-stopped")'))
    finally:
        if dock:
            dock.close()
        if page:
            page.close()
        if desk:
            desk.close()
        (scratch / "results.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
    print(f"{len(checks)} checks passed", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--session":
        fake_session(sys.argv[2])
    else:
        main()
