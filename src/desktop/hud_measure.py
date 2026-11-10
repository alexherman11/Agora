"""hud_measure.py: measure the REAL home base page through its DevTools port (a5736). Reads and scrolls the page only.

    python hud_measure.py <port> fit          the page's size and scale, whether it scrolls, every part that scrolls
    python hud_measure.py <port> scroll       frame times while the chat feed scrolls for 6 s (scroll_cost.js)
    python hud_measure.py <port> idle         frame times and long tasks over 6 s of doing nothing
    python hud_measure.py <port> layer        the frost moved from a fixed page background to a fixed layer of its own
                                              (to compare `scroll` before and after; gone at the next show)

The port exists only when hud.py was started with WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=<port>;
any program on this PC can drive the page through it, so start the home base again without it afterwards.
"""
import asyncio
import json
import sys
import urllib.request
from pathlib import Path

import websockets

HERE = Path(__file__).resolve().parent

FIT = """(() => { const out = []; for (const el of document.querySelectorAll('*')) { const cs = getComputedStyle(el);
  if (/auto|scroll/.test(cs.overflowY + cs.overflowX) && (el.scrollHeight > el.clientHeight + 1 || el.scrollWidth > el.clientWidth + 1))
    out.push((el.dataset.key || el.tagName).split('/').slice(-2).join('/') + ' ' + el.clientHeight + '/' + el.scrollHeight); }
  const d = document.documentElement;
  return {window: innerWidth + 'x' + innerHeight, dpr: devicePixelRatio, page: d.scrollWidth + 'x' + d.scrollHeight,
          page_scrolled: scrollY, scrollers: out}; })()"""
IDLE = """new Promise(r => { const lt = []; new PerformanceObserver(l => l.getEntries().forEach(e => lt.push(Math.round(e.duration)))).observe({type: 'longtask'});
  const fr = []; const t0 = performance.now(); let last = t0;
  const f = () => { const now = performance.now(); fr.push(now - last); last = now;
    if (now - t0 < 6000) return requestAnimationFrame(f); fr.sort((a, b) => a - b);
    r({frames: fr.length, p50: +fr[fr.length >> 1].toFixed(1), p95: +fr[Math.floor(fr.length * .95)].toFixed(1),
       max: Math.round(fr[fr.length - 1]), over33: fr.filter(x => x > 33).length, longtasks: lt}); };
  requestAnimationFrame(f); })"""
LAYER = """(() => { const s = document.getElementById('hud-frost'); if (!s) return 'no frost';
  const m = /url\\(([^)]*)\\)/.exec(s.textContent); if (!m) return 'no picture';
  s.textContent = 'html{background:#0d100f!important}body,#paint{background:transparent!important}'
    + 'html::before{content:"";position:fixed;inset:0;z-index:-1;background:url(' + m[1] + ') center/cover no-repeat;will-change:transform}';
  return 'layer'; })()"""


async def main():
    port, what = sys.argv[1], sys.argv[2]
    tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=5).read())
    page = next(t for t in tabs if t.get("type") == "page" and "lens.html" in t.get("url", ""))
    expr = {"fit": FIT, "idle": IDLE, "layer": LAYER,
            "scroll": (HERE / "scroll_cost.js").read_text(encoding="utf-8")}[what]
    async with websockets.connect(page["webSocketDebuggerUrl"], max_size=16 * 1024 * 1024) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate",
                                  "params": {"expression": expr, "awaitPromise": True, "returnByValue": True}}))
        while True:
            m = json.loads(await ws.recv())
            if m.get("id") == 1:
                r = m.get("result", {})
                print(json.dumps(r.get("result", {}).get("value", r.get("exceptionDetails")), ensure_ascii=False))
                return


if __name__ == "__main__":
    asyncio.run(main())
