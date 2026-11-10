"""Headless Chromium content/dock proof using Viewer's actual resolver and file renderer.

No native windows, live-world writes, uploads or temporary ACL changes. --native
in test_viewer.py separately tests the native host on a guarded hidden desktop.
"""
import base64
import hashlib
import http.server
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
import urllib.request

from PIL import Image, ImageDraw
from test_kdesk import Desk, scratch_dir, quoted
from viewer import Locations, LOCAL
from widget_browser import CDP

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[2] / ".viewer-test"


def main():
    OUT.mkdir(exist_ok=True)
    files = OUT / "proof-files"
    files.mkdir(exist_ok=True)
    text = files / "hello & café.txt"
    text.write_text("Hello from a local text file.\n<script>window.bad=true</script>\nCafé", encoding="utf-8")
    markdown = files / "read me.md"
    markdown.write_text("# Markdown fixture\n\n**Bold words** and `code`.\n\n- one\n- two\n\n<script>window.bad=true</script>", encoding="utf-8")
    im = Image.new("RGB", (560, 240), "#b3ded3")
    ImageDraw.Draw(im).text((40, 100), "A local image in Viewer", fill="#243c37")
    image, pdf = files / "picture.png", files / "paper.pdf"
    im.save(image)
    im.save(pdf, "PDF")
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files.iterdir()}
    class Web(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            data = (b"<!doctype html><title>Viewer web fixture</title><body style='background:#eef8ff;color:#243c37;font:22px Segoe UI;padding:48px'>"
                    b"<h1>Web page in Viewer</h1><p>This page refuses iframe embedding.</p><a href='/next'>Next page</a></body>")
            if self.path == "/next":
                data = b"<!doctype html><h1>Next web page</h1>"
            self.send_response(200)
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(data)
        def log_message(self, *_):
            pass
    web = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Web)
    threading.Thread(target=web.serve_forever, daemon=True).start()
    d = Desk()
    profile = Path(scratch_dir("viewer-edge-"))
    result = {"ok": False, "checks": [], "transport": "headless Chromium; CDP fulfills the same in-memory file responses as native WebView2"}
    process, c = None, None
    browser_log = open(OUT / "proof-browser.log", "w", encoding="utf-8")
    try:
        chrome = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        executable = str(chrome) if chrome.is_file() else r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        result["browser"] = Path(executable).name
        process = subprocess.Popen([executable, "--headless=new", "--disable-gpu", "--no-first-run", "--incognito",
            "--no-default-browser-check", "--remote-debugging-port=0", "--remote-allow-origins=*",
            "--user-data-dir=" + str(profile), "about:blank"],
            stdout=subprocess.DEVNULL, stderr=browser_log, creationflags=0x08000000)
        active = profile / "DevToolsActivePort"
        end = time.monotonic() + 20
        while not active.exists() and process.poll() is None and time.monotonic() < end:
            time.sleep(.1)
        port = active.read_text().splitlines()[0]
        targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list"))
        c = CDP(next(t["webSocketDebuggerUrl"] for t in targets if t["type"] == "page"))
        c.call("Page.enable")
        c.call("Emulation.setDeviceMetricsOverride", width=1100, height=780, deviceScaleFactor=1, mobile=False)
        locations = Locations(d.url, d.entry.token("alex"))
        file_requests = []
        def event(message):
            if message.get("method") != "Fetch.requestPaused":
                return
            params = message["params"]
            url = params["request"]["url"]
            try:
                body, mime = locations.read(url)
                code = 200
            except Exception as exc:
                body, mime, code = str(exc).encode(), "text/plain", 404
            file_requests.append({"url": url, "method": params["request"]["method"]})
            c.send("Fetch.fulfillRequest", requestId=params["requestId"], responseCode=code,
                   responseHeaders=[{"name": "Content-Type", "value": mime}, {"name": "Cache-Control", "value": "no-store"}],
                   body=base64.b64encode(body).decode())
        c.on_event = event
        c.call("Fetch.enable", patterns=[{"urlPattern": LOCAL + "*"}])
        def shot(name):
            c.call("Page.captureScreenshot", format="png")
            time.sleep(.2)
            (OUT / ("proof-" + name + ".png")).write_bytes(base64.b64decode(c.call("Page.captureScreenshot", format="png")["data"]))
        def visit(value, ready, name):
            url = locations.resolve(value)
            c.call("Page.navigate", url=url)
            c.until(ready)
            shot(name)
            result["checks"].append(name)
            print("PASS " + name, flush=True)
            return url
        def history(delta, ready):
            h = c.call("Page.getNavigationHistory")
            c.call("Page.navigateToHistoryEntry", entryId=h["entries"][h["currentIndex"] + delta]["id"])
            c.until(ready)
        page = f"http://127.0.0.1:{web.server_address[1]}/"
        visit(page, "document.body.innerText.includes('Web page in Viewer')", "web")
        c.js("document.querySelector('a').click()")
        c.until("document.body.innerText.includes('Next web page')")
        history(-1, "document.body.innerText.includes('Web page in Viewer')")
        history(1, "document.body.innerText.includes('Next web page')")
        result["checks"].append("web-link-back-forward")
        assert d.say('make kind=lens name=viewer-fixture title="Viewer fixture lens" text=' +
                     quoted('root : column\n  title : text "Agora lens inside Viewer"\n  body : text "Painted by the existing lens painter."'))["ok"]
        visit("viewer-fixture", "document.body.innerText.includes('Agora lens inside Viewer')", "lens")
        assert d.say('make kind=note name="Viewer fixture note" text="A thing read inside Viewer."')["ok"]
        visit("Viewer fixture note", "document.body.innerText.includes('A thing read inside Viewer.')", "thing")
        visit(str(text), "document.body.innerText.includes('Hello from a local text file.')", "text")
        assert c.js("window.bad === undefined")
        visit(str(image), "document.images.length===1 && document.images[0].naturalWidth===560", "image")
        visit(str(files), "document.querySelectorAll('li a').length===5", "folder")
        c.js("[...document.querySelectorAll('a')].find(a=>a.textContent.includes('hello')).click()")
        c.until("document.body.innerText.includes('Hello from a local text file.')")
        history(-1, "document.querySelectorAll('li a').length===5")
        history(1, "document.body.innerText.includes('Hello from a local text file.')")
        result["checks"].append("folder-click-back-forward")
        history(-1, "document.querySelectorAll('li a').length===5")
        visit(str(markdown), "!!document.querySelector('.md-h1') && !!document.querySelector('strong')", "markdown")
        assert c.js("window.bad === undefined")
        result["checks"].append("local-scripts-inert")
        # A headless PDF is also an actual browser render, captured for inspection.
        pdf_url = locations.resolve(str(pdf))
        c.call("Page.navigate", url=pdf_url)
        c.until("location.href===" + json.dumps(pdf_url) + " && document.readyState==='complete'")
        assert any(r["url"] == pdf_url for r in file_requests)
        time.sleep(2)
        shot("pdf")
        result["checks"].append("pdf")
        # The fallback dock must offer a real launch.
        from urllib.parse import quote
        dock = "/desk/shell/dock.html"
        c.call("Page.navigate", url=d.url + "/dev/signin?token=" + d.entry.token("alex") + "&next=" + quote(dock, safe=""))
        pin = next(p for p in d.say("rows button")["rows"] if p.get("does") == "window.open viewer")
        selector = '[data-id="pin:' + pin["id"] + '"]'
        c.until("!!document.querySelector(" + json.dumps(selector) + ")")
        shot("dock")
        c.js("document.querySelector(" + json.dumps(selector) + ").click()")
        d.wait(lambda: d.window("viewer"))
        result["checks"].append("dock-click-opens-viewer")
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files.iterdir()}
        assert before == after
        assert all(r["method"] == "GET" for r in file_requests)
        result["checks"].extend(["file-bytes-unchanged", "file-requests-are-read-only"])
        result["ok"] = True
    except Exception:
        import traceback
        result["error"] = traceback.format_exc()
    finally:
        if c:
            try:
                c.call("Browser.close")
            except (OSError, EOFError):
                pass
            c.s.close()
        if process:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=5)
        d.close()
        web.shutdown()
        web.server_close()
        browser_log.close()
        (OUT / "proof-result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"Viewer proof: {len(result['checks'])} checks; {'PASS' if result['ok'] else 'FAIL'}")
    assert result["ok"], result.get("error")


if __name__ == "__main__":
    main()
