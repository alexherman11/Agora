"""A picture of a page, from headless Chrome, never on the screen: the evidence that lens.js paints from the kernel.

    C:/Projects/Agora4/.venv/Scripts/python.exe src/agora/shoot.py <url> <out.png> [--size 900x640] [--wait 4]

Chrome runs headless with a throwaway profile in a temporary folder (so nothing of Alex's browser is touched), the page
is given `--wait` seconds (lens.js holds a stream open, so "network idle" never comes), the picture is taken over the
DevTools protocol, and Chrome and its children are ended.
"""
import argparse
import asyncio
import base64
import contextlib
import json
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import websockets

from kernel import scratch

CHROME = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
          r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]
NO_WINDOW = 0x08000000             # CREATE_NO_WINDOW: no console flashes onto Alex's screen


async def _shoot(ws_url, url, out, w, h, wait):
    async with websockets.connect(ws_url, max_size=64 * 1024 * 1024) as ws:
        n = 0

        async def call(method, **params):
            nonlocal n
            n += 1
            await ws.send(json.dumps({"id": n, "method": method, "params": params}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("id") == n:
                    return msg.get("result", {})
        await call("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=1, mobile=False)
        await call("Page.enable")
        await call("Page.navigate", url=url)
        await asyncio.sleep(wait)
        shot = await call("Page.captureScreenshot", format="png")
        Path(out).write_bytes(base64.b64decode(shot["data"]))
        text = await call("Runtime.evaluate", expression="document.body ? document.body.innerText : ''",
                          returnByValue=True)
        return text.get("result", {}).get("value", "")


@contextlib.contextmanager
def browser():
    """Headless Chrome (or Edge) on a throwaway profile, never on the screen -> the DevTools websocket URL of its page.
    On leaving, the browser and its whole process tree end (taskkill /T on the pid started here, never by name) and the
    profile is deleted. modules/house/snap.py reuses this for its hidden shots."""
    exe = next((c for c in CHROME if Path(c).exists()), None)
    if not exe:
        raise RuntimeError("no Chrome or Edge found")
    prof = scratch.mkdtemp(prefix="kernel-shoot-")
    proc = subprocess.Popen([exe, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
                             "--hide-scrollbars", "--disable-background-networking", f"--user-data-dir={prof}",
                             "--remote-debugging-port=0", "--remote-allow-origins=*", "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=NO_WINDOW)
    try:
        port_file = Path(prof) / "DevToolsActivePort"
        for _ in range(200):
            if port_file.exists() and port_file.read_text().strip():
                break
            time.sleep(0.1)
        else:
            raise RuntimeError("the hidden browser did not start")
        port = port_file.read_text().split()[0]
        pages = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=10).read())
        yield next(p["webSocketDebuggerUrl"] for p in pages if p.get("type") == "page")
    finally:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, creationflags=NO_WINDOW)
        for _ in range(10):
            time.sleep(0.3)
            shutil.rmtree(prof, ignore_errors=True)
            if not Path(prof).exists():
                break


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("out")
    ap.add_argument("--size", default="900x640")
    ap.add_argument("--wait", type=float, default=4)
    a = ap.parse_args()
    w, h = (int(x) for x in a.size.split("x"))
    try:
        with browser() as ws_url:
            print(asyncio.run(_shoot(ws_url, a.url, a.out, w, h, a.wait)))
    except RuntimeError as exc:
        sys.exit(str(exc))


if __name__ == "__main__":
    main()
