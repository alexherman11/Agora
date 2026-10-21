"""The sandbox's start and its cleanup, with stand-ins for Edge, the desktop and DevTools (a7413): no browser, no
desktop, nothing on anyone's screen. What it proves: a start that fails after Edge was launched (the page websocket
reset at document.readyState, WinError 10054; no DevTools page) closes its own sandbox once, is not retried, says the
stage; a good start fits the page to --size by the window's own frame; screen.py's guard over a failed start is ended
and says it is not an acceptance verdict. What it does not prove: anything about a real Edge (sandbox_window.py test
and screen.py --visible do that)."""
import asyncio
import io
import json
import shutil
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "text-desk-lab" / "notation"))
import agora_tmp  # noqa: E402
import sandbox_window as SB  # noqa: E402


class FakeCdp:
    """A page that answers as told: inner/outer sizes that follow setWindowBounds, or a reset at readyState."""
    calls = []

    def __init__(self, port, reset_at_ready=False, inner=(2546, 1403), frame=(14, 37), dpr=1.5, screen=(2560, 1440)):
        self.reset, self.inner, self.frame, self.dpr, self.screen = reset_at_ready, list(inner), frame, dpr, screen

    def js(self, expr):
        if "readyState" in expr:
            if self.reset:
                raise ConnectionResetError(10054, "An existing connection was forcibly closed by the remote host")
            return "complete"
        if "outerWidth" in expr:
            return [*self.inner, self.inner[0] + self.frame[0], self.inner[1] + self.frame[1], *self.screen]
        if "devicePixelRatio" in expr:
            return [*self.inner, self.dpr]
        return list(self.inner)

    def call(self, method, **params):
        FakeCdp.calls.append((method, params))
        if method == "Browser.getWindowForTarget":
            return {"windowId": 7}
        if method == "Browser.setWindowBounds":
            b = params["bounds"]
            if b.get("windowState") == "fullscreen":
                self.inner = list(self.screen)
            else:                                  # Windows caps a framed window near the screen (ran: 1458 outer)
                self.inner = [min(b["width"], self.screen[0] + self.frame[0]) - self.frame[0],
                              min(b["height"], self.screen[1] + 18) - self.frame[1]]
        return {}

    def close(self):
        FakeCdp.calls.append(("close", {}))


def stage(cdp_factory, cdp_page=True):
    """Stand-ins for every outside effect of open_edge; -> the record of what it did."""
    rec = {"starts": 0, "closes": []}
    SB.STATE = Path(agora_tmp.directory("sandbox-start-test-"))

    def start(name, argv, env=None):
        rec["starts"] += 1
        rec["argv"] = argv
        SB.state_file(name).write_text(json.dumps({"pid": 4242, "pids": [4242]}), encoding="utf-8")
        return 4242

    def close(name, quiet=False):
        rec["closes"].append(name)
        SB.state_file(name).unlink(missing_ok=True)
        return {"ok": True}

    SB.start, SB.close, SB.free_port = start, close, lambda: 5555
    SB.wait_cdp = lambda port, secs=30: cdp_page
    SB.top_windows = lambda name: [(1, 4242, "Chrome_WidgetWin_1", "Lens", True, (0, 0, 2560, 1440))]
    SB.Cdp = cdp_factory
    SB.exe = lambda pid: "?"                   # Edge is gone by the time the failure is described
    def offline_status(*args, **kwargs):
        raise ConnectionError("fixture: no status endpoint")
    SB.urllib.request.urlopen = offline_status
    SB.time.sleep = lambda s: None
    return rec


def expect_exit(fn):
    try:
        fn()
    except SystemExit as e:
        return str(e)
    raise AssertionError("expected the start to exit")


def main():
    real = {k: getattr(SB, k) for k in ("STATE", "start", "close", "free_port", "wait_cdp", "top_windows", "Cdp", "exe")}
    sleep = SB.time.sleep
    urlopen = SB.urllib.request.urlopen
    made = []
    try:
        # 1. the page websocket resets at readyState: closed once, not retried, the stage named, no state left
        rec = stage(lambda port: FakeCdp(port, reset_at_ready=True))
        made.append(SB.STATE)
        why = expect_exit(lambda: SB.open_edge("t1", "http://x/", "2560x1440"))
        assert rec["starts"] == 1, rec
        assert rec["closes"] == ["t1"], rec
        assert "document.readyState" in why and "ConnectionResetError" in why and "pid 4242 presence unknown" in why, why
        assert "not a tested page" in why, why
        assert not SB.state_file("t1").exists()
        print("reset at readyState: one start, its own sandbox closed once, stage and error named: ok")

        # 2. DevTools lists no page / the websocket cannot open: the same cleanup
        def no_page(port):
            raise StopIteration("no page target")
        rec = stage(no_page)
        made.append(SB.STATE)
        why = expect_exit(lambda: SB.open_edge("t2", "http://x/", "1280x800"))
        assert rec["closes"] == ["t2"] and "DevTools websocket" in why, (rec, why)
        print("no DevTools page: its own sandbox closed, stage named: ok")

        # 3. no DevTools port at all: the existing bounded retry (tries=2), each closed, then an exit
        rec = stage(lambda port: FakeCdp(port), cdp_page=False)
        made.append(SB.STATE)
        why = expect_exit(lambda: SB.open_edge("t3", "http://x/", "1280x800"))
        assert rec["starts"] == 2 and rec["closes"] == ["t3", "t3"], rec
        print("no DevTools port: two bounded starts, each closed: ok")

        rec = stage(lambda port: FakeCdp(port), cdp_page=False)
        made.append(SB.STATE)
        SB.close = lambda *a, **kw: {"ok": False}
        why = expect_exit(lambda: SB.open_edge("t3-unknown", "http://x/", "1280x800"))
        assert rec["starts"] == 1 and SB.state_file("t3-unknown").exists()
        assert "no retry" in why and "ownership state retained" in why
        print("unknown cleanup: receipt/state kept, no second launch: ok")

        # 4. a good start at Alex's size (the whole screen): fullscreen on its desktop, the page 2560x1440 at 1.5
        FakeCdp.calls = []
        rec = stage(lambda port: FakeCdp(port))
        made.append(SB.STATE)
        st = SB.open_edge("t4", "http://x/", "2560x1440")
        bounds = [p for m, p in FakeCdp.calls if m == "Browser.setWindowBounds"]
        assert bounds == [{"windowId": 7, "bounds": {"windowState": "fullscreen"}}], bounds
        assert st["viewport"] == [2560, 1440, 1.5] and rec["closes"] == [], (st, rec)
        assert json.loads(SB.state_file("t4").read_text(encoding="utf-8"))["viewport"] == [2560, 1440, 1.5]
        assert ("close", {}) in FakeCdp.calls
        print("good start at the screen's size: fullscreen, page 2560x1440 measured and kept, not closed: ok")
        # a7466: the hidden window must not stop painting when Alex's display sleeps (Edge's occlusion tracking)
        assert "--disable-features=CalculateNativeWinOcclusion" in rec["argv"], rec["argv"]
        assert "--disable-backgrounding-occluded-windows" in rec["argv"] and "--disable-renderer-backgrounding" in rec["argv"]
        print("edge is started with occlusion tracking and backgrounding off: ok")

        # 4b. smaller than the screen: the framed window grows by its own frame
        FakeCdp.calls = []
        stage(lambda port: FakeCdp(port, inner=(1266, 763)))
        made.append(SB.STATE)
        st = SB.open_edge("t4b", "http://x/", "1280x800")
        bounds = [p for m, p in FakeCdp.calls if m == "Browser.setWindowBounds"]
        assert bounds and bounds[0]["bounds"]["width"] == 1294 and bounds[0]["bounds"]["height"] == 837, bounds
        assert st["viewport"] == [1280, 800, 1.5], st
        print("good start at 1280x800: window grown by its frame, page 1280x800 measured: ok")

        # 4c. a page Windows cannot hold (taller than the screen, not the screen): measured and kept as it is
        stage(lambda port: FakeCdp(port, inner=(1266, 1403)))
        made.append(SB.STATE)
        st = SB.open_edge("t4c", "http://x/", "1280x1500")
        assert st["viewport"] == [1280, 1421, 1.5], st
        print("a page Windows caps: the measured size is reported, not the one asked: ok")

        # 5. already the right size: no resize; viewport=False keeps the old outer-window meaning
        FakeCdp.calls = []
        stage(lambda port: FakeCdp(port, inner=(1280, 800)))
        made.append(SB.STATE)
        st = SB.open_edge("t5", "http://x/", "1280x800")
        assert not [m for m, _ in FakeCdp.calls if m == "Browser.setWindowBounds"] and st["viewport"] == [1280, 800, 1.5]
        FakeCdp.calls = []
        stage(lambda port: FakeCdp(port))
        made.append(SB.STATE)
        st = SB.open_edge("t6", "http://x/", "1280x800", viewport=False)
        assert "viewport" not in st and not [m for m, _ in FakeCdp.calls if m.startswith("Browser.")]
        print("right size: no resize; viewport=False: no fitting: ok")
    finally:
        for k, v in real.items():
            setattr(SB, k, v)
        SB.time.sleep = sleep
        SB.urllib.request.urlopen = urlopen
        for d in made:
            shutil.rmtree(d, ignore_errors=True)

    # 6. screen.py: a start that fails still ends the guard, closes, and says the verdict is not an acceptance
    import screen
    events = []

    class Guard:
        def __init__(self, name, words):
            pass

        def __enter__(self):
            events.append("guard on")
            return self

        def __exit__(self, *a):
            events.append("guard off")

        def verdict(self):
            return 0, "alex: untouched by the sandbox"

    class FakeSB:
        pass
    fake = FakeSB()
    fake.Guard = Guard
    fake.open_edge = lambda name, url, size: (_ for _ in ()).throw(SystemExit("edge started but failed at document.readyState"))
    fake.close = lambda name, quiet=False: events.append("closed")
    old = screen.SB, screen.VISIBLE
    screen.SB, screen.VISIBLE = fake, "sandbox"
    out = io.StringIO()
    try:
        with redirect_stdout(out):
            why = expect_exit(lambda: asyncio.run(screen.run("http://x/", [], (2560, 1440), [0])))
    finally:
        screen.SB, screen.VISIBLE = old
    assert "document.readyState" in why, why
    assert events == ["guard on", "closed", "guard off"], events
    assert "not an acceptance verdict" in out.getvalue(), out.getvalue()
    print("screen.py failed start: guard ended, sandbox closed, verdict marked not an acceptance: ok")


if __name__ == "__main__":
    main()
