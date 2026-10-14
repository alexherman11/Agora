"""probe (a5062, Codex m5110): does UI Automation see a painted part's DOM id ("part:<scene key>") as its AutomationId?

    python probe_ids.py <lens page url>

Opens the page in an Edge app window of its own (own profile under state/, at 100,200), asks UIA for the parts at a
grid of points, prints the AutomationIds it finds, and closes the window. Nothing is clicked or typed.
"""
import ctypes
import json
import subprocess
import sys
import time
from pathlib import Path

import capture as C

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PROFILE = Path(__file__).resolve().parent / "state" / "probe-edge-profile"

ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
url = sys.argv[1]
PROFILE.mkdir(parents=True, exist_ok=True)
p = subprocess.Popen([EDGE, f"--user-data-dir={PROFILE}", "--no-first-run", "--no-default-browser-check",
                      f"--app={url}", "--window-size=1200,1100", "--window-position=100,200"])
helper = C.Helper()
try:
    helper.ask(op="ping")
    hwnd = None
    for _ in range(80):                        # find the window by its place
        time.sleep(0.25)
        hw = C.user32.WindowFromPoint(C.wt.POINT(600, 700))
        root = C.user32.GetAncestor(hw, C.GA_ROOT) if hw else None
        if root and C.window_info(root)["class"].startswith("Chrome_WidgetWin"):
            info = C.window_info(root)
            if info["wrect"][0] >= 50 and info["wrect"][0] <= 200:
                hwnd = int(root)
                break
    print("window", hwnd and C.window_info(hwnd))
    time.sleep(4)                              # the page paints its scene
    for pt in ((400, 420), (400, 560), (400, 700)):
        for i in range(6):
            a = helper.ask(op="at", x=pt[0], y=pt[1])["chain"]
            if any(c.get("type", "").endswith("Document") for c in a):
                break
            time.sleep(0.5)
        print("at", pt, json.dumps([{k: c.get(k) for k in ("type", "name", "cls", "aid")} for c in a[:5]])[:600])
    for i in range(3):                         # Chromium builds its accessibility tree after the first ask
        t0 = time.perf_counter()
        t = helper.ask(op="tree", hwnd=hwnd, rect=[150, 300, 1800, 1650])
        print(f"  ask {i}: url {t.get('url')!r}, {len(t.get('parts') or [])} parts, {C.ms(t0)} ms")
        if t.get("parts"):
            break
        time.sleep(0.5)
    shot = Path(__file__).resolve().parent / "state" / "screen-probe.png"
    helper.ask(op="grab", rect=C.window_info(hwnd)["wrect"], path=str(shot), max=1200, ocr=False)
    print("the probe's own window, pictured:", shot)
    print("url", t.get("url"), "doc", t.get("doc"), "parts", len(t.get("parts") or []), "seen", t.get("seen"), "ms", t.get("ms"))
    ids = [x for x in (t.get("parts") or []) if x.get("aid")]
    print("parts with an AutomationId:", len(ids))
    for x in (t.get("parts") or [])[:25]:
        print(" ", json.dumps({k: x.get(k) for k in ("aid", "roles", "words", "rect")})[:200])
finally:
    helper.close()
    # only this probe's own Edge (its own profile, so its own browser process) and what it started; never by title,
    # which would also match Alex's own Lens windows
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
