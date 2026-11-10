"""Big white blocks (dk1136): the see-through bars on a guarded hidden desktop, real WebView2, no shell reservation.

Two children, the same steps. `unpatched` is the negative control (pinned pywebview as it ships); `patched` installs
window_transparency as GuiScreen.start does and also drives GuiScreen.open for a bar (its AppBar replaced by a stub, so
nothing reserves an edge of Alex's screen). What is measured, in the hidden window's own process:

  * shown_unasked: a transparent window made hidden=True became visible before the host showed it (navigation start);
  * reshown_by_reload: hidden by the host (as for a full-screen game), then location.reload(): visible again;
  * light fraction of the window (PrintWindow) on the page itself vs on WebView2's error page (a door that is down);
  * GuiScreen bar: on glass before it was first visible; on a door that is down never visible, then shown once the
    door answers (its page tried again).
"""
import json
import socket
import sys
import threading
import time
import unittest
from pathlib import Path
from uuid import uuid4

HERE = Path(__file__).resolve().parent
PYTHON = r"C:\Projects\Agora4\.venv\Scripts\python.exe"
TITLE = "Agora bar paint fixture"
PAGE = (b"<!doctype html><html><head><meta charset='utf-8'><style>html,body{margin:0;background:transparent}"
        b"div{width:240px;height:48px;border-radius:24px;background:#2f6f5a}</style></head><body><div></div></body></html>")


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def serve(port):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class Page(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(PAGE)))
            self.end_headers()
            self.wfile.write(PAGE)

        def log_message(self, *a):
            pass
    srv = ThreadingHTTPServer(("127.0.0.1", port), Page)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def child(result_path, patched):
    def progress(stage):
        Path(result_path).with_suffix(".progress").write_text(stage, encoding="utf-8")

    progress("imports")
    sys.stderr = open(Path(result_path).with_suffix(".log"), "w", encoding="utf-8", buffering=1)
    from types import SimpleNamespace
    import webview
    import kd_window
    import shell_native
    import window_transparency
    from kd_window import GuiScreen, user32, SW_HIDE, SW_SHOWNOACTIVATE
    sys.path.insert(0, str(HERE.parent))
    from sandbox_window import print_window

    if not patched:
        window_transparency.install = lambda: None
    up, down = free_port(), free_port()
    servers = [serve(up)]
    screen = GuiScreen(None)
    result = {"patched": patched, "ok": False}
    opened = []

    def hwnd_of(title, secs=20):
        end = time.monotonic() + secs
        while time.monotonic() < end:
            h = user32.FindWindowW(None, title)
            if h:
                return h
            time.sleep(0.002)
        return 0

    class Watch:
        """IsWindowVisible every 2 ms: when it was first seen visible."""
        def __init__(self, title):
            self.first, self.stop = None, False
            self.h = hwnd_of(title)
            threading.Thread(target=self.run, daemon=True).start()

        def run(self):
            while not self.stop:
                if self.first is None and self.h and user32.IsWindowVisible(self.h):
                    self.first = time.monotonic()
                time.sleep(0.002)

    def light(h):
        img = print_window(h).convert("RGB")
        px = list(zip(*[iter(img.tobytes())] * 3))
        return round(sum(1 for p in px if min(p) >= 220) / max(1, len(px)), 3)

    def inspect():
        try:
            # 1. a plain transparent hidden window, as the bars are made
            progress("plain transparent window")
            title = f"{TITLE} plain"
            win = webview.create_window(title, f"http://127.0.0.1:{up}/", hidden=True, transparent=True,
                                        frameless=True, width=1200, height=400)
            opened.append(win)
            watch = Watch(title)
            assert win.events.loaded.wait(30), "page did not load"
            time.sleep(1.0)
            result["shown_unasked"] = watch.first is not None
            win.show()
            time.sleep(1.0)
            result["light_on_page"] = light(watch.h)
            user32.ShowWindow(watch.h, SW_HIDE)                 # the host steps the bar back (a full-screen game)
            time.sleep(0.3)
            win.events.loaded.clear()
            threading.Thread(target=lambda: win.run_js("location.reload()"), daemon=True).start()
            win.events.loaded.wait(15)
            time.sleep(1.0)
            result["reshown_by_reload"] = bool(user32.IsWindowVisible(watch.h))
            user32.ShowWindow(watch.h, SW_SHOWNOACTIVATE)
            win.events.loaded.clear()
            win.load_url(f"http://127.0.0.1:{down}/")           # the door is down
            win.events.loaded.wait(15)
            time.sleep(2.0)
            result["light_on_error_page"] = light(watch.h)
            watch.stop = True
            win.destroy()

            if patched:
                # 2. GuiScreen's own bar path; the AppBar (a real edge reservation) is a stub
                glassed = {}
                real_glass = shell_native.glass
                shell_native.glass = lambda h: glassed.setdefault(h, time.monotonic()) and real_glass(h)

                def make_bar(wid, hwnd, edge):
                    screen.bars[wid] = SimpleNamespace(remove=lambda: None, resize=lambda h: None)
                    screen.bar_hidden[wid] = False
                    user32.ShowWindow(hwnd, SW_HIDE)
                    shell_native.glass(hwnd)
                    if screen._bar_may_show(wid):
                        user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
                screen._make_bar = make_bar

                def bar(wid, port):
                    shown = threading.Event()
                    t = f"{TITLE} {wid}"
                    screen.open(wid, "shell-top", t, f"http://127.0.0.1:{port}/", (0, 0, 1200, 400),
                                lambda: None, shown.set, bar="top")
                    opened.append(screen.wins[wid]["w"])
                    return shown, Watch(t)

                progress("GuiScreen bar, door up")
                shown, watch = bar("up", up)
                assert shown.wait(30), "bar never shown"
                time.sleep(0.5)
                first, h = watch.first, watch.h
                result["bar_visible"] = bool(user32.IsWindowVisible(h))
                result["bar_glass_before_visible"] = bool(first and h in glassed and glassed[h] <= first)
                watch.stop = True

                progress("GuiScreen bar, door down")
                shown, watch = bar("down", down)
                time.sleep(8)
                result["down_bar_ever_visible"] = watch.first is not None
                result["down_bar_page_failed"] = bool(screen.wins["down"].get("page_failed"))
                servers.append(serve(down))                     # the door comes back
                result["down_bar_shown_after_door"] = shown.wait(20)
                time.sleep(0.5)
                result["down_bar_visible_after_door"] = bool(watch.h and user32.IsWindowVisible(watch.h))
                result["down_bar_glass_before_visible"] = bool(watch.first and watch.h in glassed
                                                               and glassed[watch.h] <= watch.first)
                watch.stop = True
            result["ok"] = True
        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            progress("closing")
            for w in opened:
                try:
                    w.destroy()
                except Exception:
                    pass
            Path(result_path).write_text(json.dumps(result, indent=2), encoding="utf-8")
            screen.anchor.destroy()

    try:
        screen.start(inspect)
    finally:
        for s in servers:
            s.shutdown()
        if not Path(result_path).exists():
            Path(result_path).write_text(json.dumps(result, indent=2), encoding="utf-8")


def run_child(mode):
    sys.path.insert(0, str(HERE.parent))
    import sandbox_window as sb
    name = "barpaint-" + uuid4().hex[:10]
    result_path = sb.STATE / (name + "-result.json")
    with sb.Guard(name, TITLE) as guard:
        sb.run_hidden(name, [PYTHON, str(Path(__file__).resolve()), "--child", str(result_path), mode])
        end = time.monotonic() + 150
        while not result_path.exists() and time.monotonic() < end:
            time.sleep(.2)
    assert result_path.exists(), "hidden fixture timed out; retained ownership receipt"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    print(f"Hidden bar paint ({mode}): " + json.dumps(result), flush=True)
    return result, guard


class TransparencyContractTest(unittest.TestCase):
    """window_transparency on a stand-in EdgeChrome: no native windows."""

    def test_transparent_windows_are_not_shown_by_navigation_and_the_host_hears_the_outcome(self):
        from types import ModuleType, SimpleNamespace
        from unittest.mock import patch
        import window_transparency

        class Chrome:
            def __init__(self, window):
                self.pywebview_window, self.shown = window, 0

            def on_navigation_start(self, sender, args):
                self.shown += 1

            def on_navigation_completed(self, sender, args):
                pass
        platform = ModuleType("webview.platforms")
        platform.edgechromium = SimpleNamespace(EdgeChrome=Chrome)
        with patch.dict(sys.modules, {"webview.platforms": platform}):
            window_transparency.install()
            patched = Chrome.on_navigation_start
            window_transparency.install()
            self.assertIs(patched, Chrome.on_navigation_start)        # idempotent
        heard = []
        bar = Chrome(SimpleNamespace(transparent=True, agora_navigated=heard.append))
        page = Chrome(SimpleNamespace(transparent=False))
        bar.on_navigation_start(None, None)
        page.on_navigation_start(None, None)
        self.assertEqual((0, 1), (bar.shown, page.shown))
        for args in (SimpleNamespace(IsSuccess=False, HttpStatusCode=0), SimpleNamespace(IsSuccess=True, HttpStatusCode=403),
                     SimpleNamespace(IsSuccess=True, HttpStatusCode=200), SimpleNamespace(IsSuccess=True)):
            bar.on_navigation_completed(None, args)
        page.on_navigation_completed(None, SimpleNamespace(IsSuccess=False))
        self.assertEqual([False, False, True, True], heard)


class BarPaintTest(unittest.TestCase):
    def test_unpatched_pywebview_shows_hidden_bars_itself(self):
        r, guard = run_child("unpatched")
        self.assertFalse(any(n[2] for n in guard.notes), str(guard.notes))
        self.assertTrue(r["ok"], r)
        self.assertTrue(r["shown_unasked"], r)                # the cause: shown on navigation, before glass
        self.assertTrue(r["reshown_by_reload"], r)
        self.assertGreater(r["light_on_error_page"], 0.5, r)  # an error page fills the window, light

    def test_bars_show_only_on_glass_and_never_on_an_error_page(self):
        r, guard = run_child("patched")
        self.assertFalse(any(n[2] for n in guard.notes), str(guard.notes))
        self.assertTrue(r["ok"], r)
        self.assertFalse(r["shown_unasked"], r)
        self.assertFalse(r["reshown_by_reload"], r)
        self.assertTrue(r["bar_visible"] and r["bar_glass_before_visible"], r)
        self.assertFalse(r["down_bar_ever_visible"], r)
        self.assertTrue(r["down_bar_page_failed"], r)
        self.assertTrue(r["down_bar_shown_after_door"] and r["down_bar_visible_after_door"], r)
        self.assertTrue(r["down_bar_glass_before_visible"], r)


if __name__ == "__main__":
    if "--child" in sys.argv:
        i = sys.argv.index("--child")
        child(sys.argv[i + 1], sys.argv[i + 2] == "patched")
    else:
        unittest.main()
