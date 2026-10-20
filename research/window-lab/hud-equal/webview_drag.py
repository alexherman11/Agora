"""webview_drag.py: does a panel drag work in WebView2, the engine Alex's home base runs in? (a5994, c6725: Alex 20 Oct
12:48, 'window dragging no longer seems to be working'.) The playtest drags in Edge; this drags in a pywebview window.

    python research/window-lab/hud-equal/webview_drag.py [--world frontier-try]

It serves the worker's own -try world (its drags land there) through a door of this checkout's painter, opens
webview_page.py on a desktop Alex never sees (sandbox_window.run_hidden, with a DevTools port), posts a mouse drag of
The board's title onto another panel's middle (a swap) as Windows messages to that window only, and reads the copy's
last events: a drop-panel there means the drag reached the world. Off: it closes the sandbox and the door itself.
"""
import json
import pathlib
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
LAB = HERE.parent
NOTATION = LAB.parent / "text-desk-lab" / "notation"
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(NOTATION))
import sandbox_window as SB  # noqa: E402
import screen  # noqa: E402
import agora_tmp  # noqa: E402

FIND = """(() => { const t = [...document.querySelectorAll('#paint [data-key$="/grip/title"]')].filter(e => e.getClientRects().length);
  const r = e => { const b = e.getBoundingClientRect(); return [b.left + b.width / 2, b.top + b.height / 2]; };
  const board = t.find(e => e.textContent.trim() === 'The board'), other = t.find(e => e.textContent.trim() !== 'The board');
  const pane = other && other.parentElement.parentElement;
  return board && pane ? { from: r(board), to: r(pane), onto: other.textContent.trim(), titles: t.map(e => e.textContent.trim()) } : { titles: t.map(e => e.textContent.trim()) };
})()"""


def do(port, world, line):
    body = json.dumps({"session": world, "as": "alex", "line": line, "whole": True}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{port}/api/do", data=body, headers={"Content-Type": "application/json"})
    out = json.loads(urllib.request.urlopen(req, timeout=60).read())
    return out.get("text") or str(out.get("error"))


def main():
    world = sys.argv[sys.argv.index("--world") + 1] if "--world" in sys.argv else "frontier-try"
    copy = world          # served as it is: a worker's own -try world (never a copy made under sessions/, which is the worlds')
    state = agora_tmp.directory("wv-door-")
    shell = pathlib.Path(state) / "desk-shell"
    shutil.copytree(NOTATION / "desk-shell", shell)
    port = screen.free_port()
    door = subprocess.Popen([sys.executable, "door.py", str(port), "--no-git", "--state", state, "--static", str(shell)],
                            cwd=NOTATION, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    name = f"wv-{__import__('os').getpid()}"
    guard = SB.Guard(name, f"agora-sandbox-{name}")
    guard.__enter__()
    try:
        screen.wait_http(f"http://127.0.0.1:{port}/lens.html", 60)
        print("layout:", do(port, copy, "look f5664").splitlines()[0][:160])
        url = f"http://127.0.0.1:{port}/lens.html?" + urllib.parse.urlencode({"session": copy, "as": "alex", "lens": "home-base", "inspect": "0"})
        st = SB.run_hidden(name, ["python", str(HERE / "webview_page.py"), url, "1700x1000"], cdp=True)
        SB.join(name)
        hw = SB.main_window(name)
        c = SB.Cdp(st["port"])
        for _ in range(100):
            if c.js("document.querySelectorAll('#paint [data-key$=\"/grip/title\"]').length") > 0:
                break
            time.sleep(0.3)
        time.sleep(1.5)
        print("engine:", c.js("navigator.userAgent")[-60:])
        f = c.js(FIND)
        print("panels:", f["titles"])
        if "from" not in f:
            print("no board panel and another to drop it on (filled? then nothing is draggable: the filled header has no carry)")
            return
        ox, oy, dpr = SB.page_origin(hw, c)
        a = (ox + f["from"][0] * dpr, oy + f["from"][1] * dpr)
        b = (ox + f["to"][0] * dpr, oy + f["to"][1] * dpr)
        target, pt = hw, SB.wt.POINT(int(a[0]), int(a[1]))
        while True:                                   # the child window under the point, as the playtest finds it
            ch = SB.u32.ChildWindowFromPointEx(target, pt, 1)
            if not ch or ch == target or SB.cls_of(ch) in ("Intermediate D3D Window", "Chrome_RenderWidgetHostHWND"):
                break
            SB.u32.MapWindowPoints(target, ch, __import__("ctypes").byref(pt), 1)
            target = ch
        dx, dy = pt.x - int(a[0]), pt.y - int(a[1])
        SB.post(target, SB.WM_MOUSEMOVE, 0, SB.xy(a[0] + dx, a[1] + dy))
        time.sleep(0.05)
        SB.post(target, SB.WM_LBUTTONDOWN, 1, SB.xy(a[0] + dx, a[1] + dy))
        for k in range(1, 16):
            time.sleep(0.04)
            SB.post(target, SB.WM_MOUSEMOVE, 1, SB.xy(a[0] + (b[0] - a[0]) * k / 15 + dx, a[1] + (b[1] - a[1]) * k / 15 + dy))
        time.sleep(0.3)
        SB.shot_page(c, LAB / "demos" / "a5994" / "webview-mid-drag.png") if hasattr(SB, "shot_page") else None
        SB.post(target, SB.WM_LBUTTONUP, 0, SB.xy(b[0] + dx, b[1] + dy))
        time.sleep(2.5)
        hist = do(port, copy, "history f5664")
        moved = [l for l in hist.splitlines() if "drop-panel" in l or "swap" in l]
        print(f"dragged The board onto {f['onto']}: " + ("the world recorded it: " + moved[-1] if moved else "NOTHING reached the world"))
        print(do(port, copy, "history a5674").splitlines()[-1])
        c.close()
    finally:
        SB.close(name, quiet=True)
        guard.__exit__(None, None, None)
        print("guard:", guard.verdict())
        door.terminate()
        try:
            door.wait(timeout=10)
        except Exception:
            door.kill()


if __name__ == "__main__":
    main()
