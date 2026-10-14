"""The control screen's live test (a5062), on the real screen with a window of its own; it says what it will draw first.

    python test_live.py [--door http://localhost:8794]

Shows a plain window titled 'agora capture test' (an ordinary program, as far as the capture can tell) at 700,300 for
about ten seconds, always on top and never taking the keyboard, and checks:
  1. a rectangle inside it gives pixels and their words (Windows' text recognition), and no world objects;
  2. with --lens (design-review by default), an Edge window of its own beside it shows that lens from the live door as
     the test's own viewer: a drag over one painted part names its world object exactly (item, subject, rev, latest
     event) with no pixels when the page gives part ids, and never names one when it does not; a drag across both
     windows gives both, native=mixed;
  3. the selection drawn over it, photographed (state/screen-selection.png);
  4. Escape during a drag, and a click with no drag, make nothing (the overlay's own logic, keys stood in for).
Its captures are kept in this checkout's house-state and discarded at the end. Nothing is clicked or typed.
"""
import argparse
import ctypes
import subprocess
import sys
import threading
import time
from ctypes import wintypes as wt
from pathlib import Path

import capture as C

WORDS = "Agora capture test\nThe quick brown fox jumps\nover the lazy dog 12345"
X, Y, W, H = 700, 300, 660, 500


class PAINTSTRUCT(ctypes.Structure):
    _fields_ = [("hdc", wt.HDC), ("fErase", wt.BOOL), ("rcPaint", wt.RECT), ("fRestore", wt.BOOL),
                ("fIncUpdate", wt.BOOL), ("rgbReserved", ctypes.c_byte * 32)]


def test_window(ready, stop):
    u, g = C.user32, C.gdi32
    u.BeginPaint.restype, u.BeginPaint.argtypes = wt.HDC, [wt.HWND, ctypes.POINTER(PAINTSTRUCT)]
    u.EndPaint.argtypes = [wt.HWND, ctypes.POINTER(PAINTSTRUCT)]
    u.DrawTextW.argtypes = [wt.HDC, wt.LPCWSTR, ctypes.c_int, ctypes.POINTER(wt.RECT), wt.UINT]
    g.CreateFontW.restype = wt.HFONT
    g.CreateFontW.argtypes = [ctypes.c_int] * 5 + [wt.DWORD] * 8 + [wt.LPCWSTR]
    g.SetBkMode.argtypes = [wt.HDC, ctypes.c_int]
    g.SelectObject.restype, g.SelectObject.argtypes = wt.HGDIOBJ, [wt.HDC, wt.HGDIOBJ]
    g.SetTextColor.argtypes = [wt.HDC, wt.COLORREF]
    font = g.CreateFontW(-56, 0, 0, 0, 600, 0, 0, 0, 0, 0, 0, 5, 0, "Segoe UI")

    def proc(hwnd, msg, wp, lp):
        if msg == 0x000F:                                    # WM_PAINT
            ps = PAINTSTRUCT()
            hdc = u.BeginPaint(hwnd, ctypes.byref(ps))
            old = g.SelectObject(hdc, font)
            g.SetBkMode(hdc, 1)
            g.SetTextColor(hdc, 0)
            r = wt.RECT(40, 40, W - 20, H - 20)
            u.DrawTextW(hdc, WORDS, -1, ctypes.byref(r), 0)
            g.SelectObject(hdc, old)
            u.EndPaint(hwnd, ctypes.byref(ps))
            return 0
        if msg == C.WM_MOUSEACTIVATE:
            return C.MA_NOACTIVATE
        return u.DefWindowProcW(hwnd, msg, wp, lp)

    wp = C.WNDPROC(proc)
    c = C.WNDCLASS()
    c.lpfnWndProc, c.hInstance, c.lpszClassName = wp, C.kernel32.GetModuleHandleW(None), "AgoraCaptureTest"
    c.hbrBackground = g.CreateSolidBrush(0xFFFFFF)
    c.hCursor = u.LoadCursorW(None, ctypes.c_void_p(32512))
    u.RegisterClassW(ctypes.byref(c))
    hwnd = u.CreateWindowExW(C.WS_EX_TOPMOST | C.WS_EX_NOACTIVATE | C.WS_EX_TOOLWINDOW, "AgoraCaptureTest",
                             "agora capture test", C.WS_POPUP, X, Y, W, H, None, None, c.hInstance, None)
    u.ShowWindow(hwnd, 4)                                   # SW_SHOWNOACTIVATE
    u.UpdateWindow(hwnd)
    ready.append(int(hwnd))
    msg = wt.MSG()
    while not stop.is_set():
        while u.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
            u.TranslateMessage(ctypes.byref(msg))
            u.DispatchMessageW(ctypes.byref(msg))
        time.sleep(0.01)
    u.DestroyWindow(hwnd)


EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PAGE_AT = (1360, 300)          # physical pixels: just right of the test window


def open_page(door, lens, who):
    """An Edge window of the test's own (its own profile, so its own browser process) showing a lens as `who`."""
    prof = C.HERE / "state" / "test-edge-profile"
    prof.mkdir(parents=True, exist_ok=True)
    scale = C.monitor_of([PAGE_AT[0], PAGE_AT[1], 10, 10])["scale"]
    url = f"{door}/lens.html?" + C.urlencode({"session": "frontier", "as": who, "lens": lens, "inspect": "0"})
    print(f"   opening {url} in an Edge window of the test's own at {PAGE_AT}", flush=True)
    return subprocess.Popen([EDGE, f"--user-data-dir={prof}", "--no-first-run", "--no-default-browser-check", f"--app={url}",
                             f"--window-position={round(PAGE_AT[0] / scale)},{round(PAGE_AT[1] / scale)}",
                             f"--window-size={round(2200 / scale)},{round(1500 / scale)}"])


def find_part(helper, edge):
    """The page's window, and a small worded part on it level with the test window (so a drag can cross both)."""
    hwnd = None
    for _ in range(80):
        time.sleep(0.25)
        found = []

        def each(hw, lp):
            if C.user32.IsWindowVisible(hw) and C.window_info(hw)["pid"] == edge.pid and C.window_info(hw)["wrect"][2] > 400:
                found.append(int(hw))
            return True

        C.user32.EnumWindows(C.WNDENUMPROC(each), 0)
        if found:
            hwnd = found[0]
            break
    if not hwnd:
        return None, None
    for _ in range(40):                        # the page loads, paints its scene, and Chromium builds its tree
        time.sleep(0.5)
        t = helper.ask(op="tree", hwnd=hwnd, rect=[PAGE_AT[0], Y + 60, 700, H - 120])
        parts = [p for p in t.get("parts") or [] if p.get("words") and len(str(p["words"])) < 200
                 and p["rect"][0] < 1700 and Y + 60 <= p["rect"][1] and p["rect"][1] + p["rect"][3] <= Y + H - 60]
        if parts:
            parts.sort(key=lambda p: (not (p.get("aid") and C._item_of_key(p["aid"][5:])), p["rect"][2] * p["rect"][3]))
            return hwnd, parts[0]
    return hwnd, None


def main():
    ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    ap = argparse.ArgumentParser()
    ap.add_argument("--door", default="http://localhost:8794")
    ap.add_argument("--lens", default="design-review", help="the lens its own Agora window shows ('' for none)")
    ap.add_argument("--keep-as", default=None, help="keep the test's captures, owned by this person (for a receiving test)")
    a = ap.parse_args()
    args = argparse.Namespace(who=a.keep_as or "worker-a5062", world="frontier", draft=None, door=a.door)
    args.events = C.Events(a.door, args.who)
    threading.Thread(target=lambda: args.events.update(args.world), daemon=True).start()   # as capture.py does at start
    C.user32.PeekMessageW.argtypes = [ctypes.POINTER(wt.MSG), wt.HWND, wt.UINT, wt.UINT, wt.UINT]
    print(f"drawing a test window at {X},{Y} {W}x{H} for about ten seconds", flush=True)
    ready, stop, fails, made = [], threading.Event(), [], []
    th = threading.Thread(target=test_window, args=(ready, stop), daemon=True)
    th.start()
    helper = C.Helper()
    try:
        helper.ask(op="ping")
        while not ready:
            time.sleep(0.01)
        time.sleep(0.5)

        # 1. an ordinary program: pixels and words, no world objects
        cid, env, timing = C.capture([X + 20, Y + 20, W - 60, H - 120], helper, args)
        made.append(cid)
        C.report(cid, env, timing, args)
        words = (env["image_text"] or "").lower()
        if env["native"] != "none" or env["refs"] or not env["image_size"]:
            fails.append(f"1: expected pixels only, got native={env['native']} refs={len(env['refs'])}")
        if "quick brown fox" not in words:
            fails.append(f"1: the words were not recognised: {words!r}")

        # 2. an Agora page of the test's own beside it: a drag over one painted part, then across both windows
        if a.lens:
            edge = open_page(a.door, a.lens, args.who)
            try:
                hwnd, part = find_part(helper, edge)
                if part is None:
                    fails.append("2: the page showed no part with words")
                else:
                    px, py, pw, ph = part["rect"]
                    r = [px - 6, py - 6, min(pw, 900) + 12, ph + 12]
                    print(f"2. a drag over the {part['roles']} part at {r}: {' '.join(str(part['words']).split())[:60]!r}"
                          f" (its page id: {part.get('aid') or 'none'})", flush=True)
                    since = time.perf_counter()     # as the gesture does: the scene is begun when Ctrl+Alt arms
                    threading.Thread(target=C.prefetch, args=((r[0] + 3, r[1] + 3), helper, args.door, (), since, args.events), daemon=True).start()
                    time.sleep(1.0)                  # a one-second drag
                    cid, env, timing = C.capture(r, helper, args, since=since)
                    made.append(cid)
                    C.report(cid, env, timing, args)
                    named = [x for x in env["refs"] if x["resolved"] == "yes"]
                    if part.get("aid"):
                        if env["native"] != "full" or env["image_size"] or not named:
                            fails.append(f"2: expected a named object and no pixels, got native={env['native']} named={len(named)}")
                        elif not all(x["item"] and x["subject"] and x["seen_event"] for x in named):
                            fails.append(f"2: a named ref lacks its item, subject or event: {named}")
                        elif [x["item"] for x in named] != [C._item_of_key(part["aid"][5:])]:
                            fails.append(f"2: a drag over one part named {[x['item'] for x in named]}, not just its own")
                    elif named or any("item" in x for x in env["refs"]):
                        fails.append("2: a page with no part ids gave a named ref")
                    # across both: the test window's pixels and the page's parts
                    m = [X + W - 200, py - 6, 600, ph + 12]
                    cid, env, timing = C.capture(m, helper, args, since=since)
                    made.append(cid)
                    C.report(cid, env, timing, args)
                    if env["native"] != "mixed" or not env["image_size"]:
                        fails.append(f"2: expected native=mixed with pixels, got {env['native']}")
            finally:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(edge.pid)], capture_output=True)   # only its own Edge
                print("   the test's Edge window closed", flush=True)

        # 3. the selection, drawn and photographed
        ov = C.Overlay(lambda *x: None)
        sel = [X + 120, Y + 110, 380, 200]
        ov.draw(sel)
        time.sleep(0.4)
        shot = Path(C.HERE / "state" / "screen-selection.png")
        shot.parent.mkdir(parents=True, exist_ok=True)
        g = helper.ask(op="grab", rect=[X + 40, Y + 40, W - 80, H - 80], path=str(shot), max=4096, ocr=False, blt=True)
        time.sleep(1.6)
        ov.hide()
        print(f"3. the selection at {sel}, photographed {g['w']}x{g['h']}: {shot}", flush=True)

        # 4. Escape and a bare click make nothing (the overlay's logic; real keys are Alex's to press)
        before = C.captures.ids(args.world, args.who)
        done = []
        ov2 = ov                                             # one overlay per process (its window classes)
        ov2.on_done = lambda r, t0: done.append(r)
        keys = {C.VK_ESCAPE: True, C.VK_LBUTTON: True}
        real = C.held
        C.held = lambda vk: keys.get(vk, False)
        try:
            ov2.start = (X + 10, Y + 10)
            ov2.tick()                                       # Escape held during a drag
            esc_ok = ov2.start is None and not done
            keys[C.VK_ESCAPE] = False
            ov2.start = (0, 0)
            C.user32.GetCursorPos.argtypes = [ctypes.POINTER(wt.POINT)]
            ov2.rect = lambda: [5, 5, 2, 2]                  # a click, not a drag
            ov2.finish()
            click_ok = not done
            ov2.start, ov2.rect = (0, 0), (lambda: [5, 5, 200, 120])      # and a real drag is handed on
            ov2.finish()
            click_ok = click_ok and done == [[5, 5, 200, 120]]
        finally:
            C.held = real
            ov.hide()
        after = C.captures.ids(args.world, args.who)
        print(f"4. Escape cancels: {esc_ok}; a click makes nothing: {click_ok}; captures kept before {len(before)}, after {len(after)}", flush=True)
        if not (esc_ok and click_ok and before == after):
            fails.append("4: Escape or a click left something")
    finally:
        stop.set()
        th.join(2)
        helper.close()
        for cid in made if not a.keep_as else ():
            try:
                C.captures.discard(args.world, args.who, cid)
            except C.captures.CaptureError:
                pass
    print("test window closed; " + (f"its captures kept for {a.keep_as}: {', '.join(made)} in "
                                     f"{C.captures.ROOT / args.world / args.who}" if a.keep_as else "the test's captures discarded"), flush=True)
    print("FAIL\n  " + "\n  ".join(fails) if fails else "ok", flush=True)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
