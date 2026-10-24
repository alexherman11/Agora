"""A hidden browser for scenarios: headless Edge or Chrome over the DevTools protocol.

Nothing appears on screen: the browser runs headless with no console window,
in a throwaway profile that is deleted afterwards. Each person gets a private
browser context of their own (their own cookies, as their own phone would),
their own screen size, and their own client address, sent as a header the
entry service is told to trust, the way it trusts Cloudflare's in production.
Clicks and typing are real input events at the element's place on the page.
"""

from __future__ import annotations

import asyncio
import base64
import json
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

import websockets

BROWSERS = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe"]
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Browser:
    async def start(self) -> Browser:
        exe = next((b for b in BROWSERS if Path(b).exists()), None)
        if exe is None:
            raise RuntimeError("no Edge or Chrome found")
        self.exe = exe
        self.profile = tempfile.mkdtemp(prefix="entry-evening-browser-")
        port = free_port()
        self.proc = subprocess.Popen(
            [exe, "--headless=new", f"--remote-debugging-port={port}", f"--user-data-dir={self.profile}",
             "--no-first-run", "--no-default-browser-check", "--disable-extensions", "--hide-scrollbars",
             "--disable-features=Translate,MediaRouter", "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=NO_WINDOW)
        deadline = time.time() + 30
        while True:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2) as r:
                    ws_url = json.loads(r.read())["webSocketDebuggerUrl"]
                break
            except OSError:
                if time.time() > deadline:
                    raise
                await asyncio.sleep(0.2)
        self.ws = await websockets.connect(ws_url, max_size=64 * 1024 * 1024)
        self.n, self.waiting = 0, {}
        self.reader = asyncio.create_task(self._read())
        return self

    async def _read(self) -> None:
        async for raw in self.ws:
            msg = json.loads(raw)
            fut = self.waiting.pop(msg.get("id"), None)
            if fut and not fut.done():
                fut.set_result(msg)

    async def call(self, method: str, session: str | None = None, **params) -> dict:
        self.n += 1
        fut = asyncio.get_running_loop().create_future()
        self.waiting[self.n] = fut
        msg = {"id": self.n, "method": method, "params": params}
        if session:
            msg["sessionId"] = session
        await self.ws.send(json.dumps(msg))
        reply = await asyncio.wait_for(fut, 60)
        if "error" in reply:
            raise RuntimeError(f"{method}: {reply['error'].get('message')}")
        return reply.get("result", {})

    async def person(self, name: str, ip: str, size=(390, 844), mobile=True) -> Tab:
        ctx = (await self.call("Target.createBrowserContext", disposeOnDetach=True))["browserContextId"]
        target = (await self.call("Target.createTarget", url="about:blank", browserContextId=ctx))["targetId"]
        session = (await self.call("Target.attachToTarget", targetId=target, flatten=True))["sessionId"]
        tab = Tab(self, name, ctx, target, session)
        await tab.call("Page.enable")
        await tab.call("Network.enable")
        await tab.call("Network.setExtraHTTPHeaders", headers={"X-Test-Client-IP": ip})
        await tab.call("Emulation.setDeviceMetricsOverride", width=size[0], height=size[1],
                       deviceScaleFactor=1, mobile=mobile)
        return tab

    async def close(self) -> None:
        try:
            await self.call("Browser.close")
        except Exception:  # noqa: BLE001 - it is going away either way
            pass
        self.reader.cancel()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        shutil.rmtree(self.profile, ignore_errors=True)


class Tab:
    def __init__(self, browser: Browser, name: str, ctx: str, target: str, session: str):
        self.b, self.name, self.ctx, self.target, self.session = browser, name, ctx, target, session

    async def call(self, method: str, **params) -> dict:
        return await self.b.call(method, self.session, **params)

    async def js(self, expr: str):
        r = await self.call("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
        if r.get("exceptionDetails"):
            raise RuntimeError(f"{self.name}: {r['exceptionDetails'].get('text')} in {expr[:80]}")
        return r.get("result", {}).get("value")

    async def _settled(self, timeout=15) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                if await self.js("window.__stay === undefined && document.readyState === 'complete'"):
                    return
            except RuntimeError:
                pass  # mid-navigation: the old page is gone, the new one not yet there
            await asyncio.sleep(0.05)
        raise TimeoutError(f"{self.name}: the page did not finish loading")

    async def goto(self, url: str) -> None:
        await self.js("window.__stay = 1")
        await self.call("Page.navigate", url=url)
        await self._settled()

    async def _centre(self, selector: str) -> tuple[float, float]:
        r = await self.js(f"""(() => {{ const e = document.querySelector({json.dumps(selector)});
            if (!e) return null; e.scrollIntoView({{block: 'center'}}); const r = e.getBoundingClientRect();
            return [r.left + r.width / 2, r.top + r.height / 2, r.width, r.height]; }})()""")
        if not r or (r[2] == 0 and r[3] == 0):
            raise LookupError(f"{self.name}: nothing visible matches {selector!r} on {await self.url()}")
        return r[0], r[1]

    async def click(self, selector: str, navigates: bool = True) -> None:
        x, y = await self._centre(selector)
        if navigates:
            await self.js("window.__stay = 1")
        for kind in ("mouseMoved", "mousePressed", "mouseReleased"):
            await self.call("Input.dispatchMouseEvent", type=kind, x=x, y=y, button="left",
                            buttons=1 if kind == "mousePressed" else 0, clickCount=1)
        if navigates:
            await self._settled()

    async def click_text(self, tag: str, text: str, navigates: bool = True) -> None:
        """Click the `tag` whose visible text is `text` (a button or a chip's label)."""
        found = await self.js(f"""(() => {{ const all = [...document.querySelectorAll({json.dumps(tag)})];
            const e = all.find(x => x.innerText.trim() === {json.dumps(text)}); if (!e) return false;
            e.setAttribute('data-scenario-target', '1'); return true; }})()""")
        if not found:
            raise LookupError(f"{self.name}: no {tag} saying {text!r} on {await self.url()}")
        await self.click("[data-scenario-target]", navigates)
        if not navigates:
            await self.js("document.querySelector('[data-scenario-target]').removeAttribute('data-scenario-target')")

    async def type(self, selector: str, text: str) -> None:
        await self.click(selector, navigates=False)
        await self.js(f"document.querySelector({json.dumps(selector)}).select()")
        await self.call("Input.insertText", text=text)

    async def text(self) -> str:
        return await self.js("document.body.innerText")

    async def url(self) -> str:
        return await self.js("location.href")

    async def value(self, selector: str) -> str:
        return await self.js(f"document.querySelector({json.dumps(selector)}).value")

    async def shot(self, path: Path, selector: str | None = None) -> Path:
        params = {"format": "png"} if path.suffix == ".png" else {"format": "jpeg", "quality": 72}
        if selector:
            r = await self.js(f"""(() => {{ const e = document.querySelector({json.dumps(selector)});
                e.scrollIntoView({{block: 'center'}}); const r = e.getBoundingClientRect();
                return [r.left + scrollX, r.top + scrollY, r.width, r.height]; }})()""")
            params["clip"] = {"x": r[0], "y": r[1], "width": r[2], "height": r[3], "scale": 2}
            params["captureBeyondViewport"] = True
        else:
            await self.js("scrollTo(0, 0)")
        data = (await self.call("Page.captureScreenshot", **params))["data"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(data))
        return path

    async def cookies(self) -> dict[str, str]:
        got = await self.b.call("Storage.getCookies", browserContextId=self.ctx)
        return {c["name"]: c["value"] for c in got.get("cookies", [])}

    async def close(self) -> None:
        await self.b.call("Target.disposeBrowserContext", browserContextId=self.ctx)
