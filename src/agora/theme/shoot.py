"""Hidden screenshots of a page or a snippet of HTML in headless Edge (nothing appears on the screen)."""
import base64
import sys
import tempfile
import time
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
DESKTOP = LAB.parent / "desktop" / "kernel-desktop"
for p in (str(LAB), str(DESKTOP)):
    if p not in sys.path:
        sys.path.insert(0, p)
from widget_browser import Browser  # noqa: E402


def shot(c, path, width=None, height=None):
    c.call("Page.captureScreenshot", format="png", captureBeyondViewport=False, fromSurface=True)
    c.call("Runtime.evaluate", expression="new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))",
           awaitPromise=True)
    time.sleep(0.2)
    data = c.call("Page.captureScreenshot", format="png", captureBeyondViewport=False, fromSurface=True)["data"]
    Path(path).write_bytes(base64.b64decode(data))


def render_html(html, path, width=1280, height=720):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        name = f.name
    try:
        with Browser() as c:
            c.call("Emulation.setDeviceMetricsOverride", width=width, height=height, deviceScaleFactor=1, mobile=False)
            c.call("Page.navigate", url=Path(name).as_uri())
            c.until("document.readyState==='complete'")
            time.sleep(0.4)
            shot(c, path)
    finally:
        Path(name).unlink(missing_ok=True)
