"""Disposable-world checks; --native runs the real host on a guarded hidden desktop."""
import hashlib
import http.server
import json
from pathlib import Path
import sys
import threading
import time
import unittest
import urllib.request
import base64
from html.parser import HTMLParser
from http.cookiejar import CookieJar
from urllib.parse import parse_qs, urlencode, urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCRATCH = ROOT / ".viewer-test"
PY = r"C:\Projects\Agora4\.venv\Scripts\python.exe"
sys.path.insert(0, str(HERE))
from viewer import Locations, LOCAL
from test_kdesk import Desk, quoted, scratch_dir


class ViewerTest(unittest.TestCase):
    def test_file_previews_and_folder_links_preserve_bytes(self):
        from PIL import Image
        class Elements(HTMLParser):
            def __init__(self, body):
                super().__init__()
                self.tags = []
                self.feed(body.decode("utf-8"))
            def handle_starttag(self, tag, attrs):
                self.tags.append((tag, dict(attrs)))
        files = Path(scratch_dir("viewer-files-"))
        text = files / "hello & café.txt"
        text.write_text("Hello café\n<script>window.bad=true</script>", encoding="utf-8")
        markdown = files / "read me.md"
        markdown.write_text("# Heading\n\n**Bold**\n</script><script>window.bad=true</script>", encoding="utf-8")
        image, pdf = files / "picture.png", files / "paper.pdf"
        im = Image.new("RGB", (32, 16), "#b3ded3")
        im.save(image)
        im.save(pdf, "PDF")
        before = {p: p.read_bytes() for p in files.iterdir()}
        locations = Locations("http://127.0.0.1:1", "")
        folder, mime = locations.read(locations.resolve(str(files)))
        self.assertEqual("text/html", mime)
        links = [attrs["href"] for tag, attrs in Elements(folder).tags if tag == "a"]
        self.assertEqual(5, len(links))
        self.assertEqual(set(before), {locations.files[url] for url in links} - {files.parent})
        for url in links:
            if locations.files[url] == text:
                body, _ = locations.read(url)
                self.assertIn("Hello café".encode(), body)
                self.assertIn(b"&lt;script&gt;", body)
        body, _ = locations.read(locations.resolve(str(image)))
        src = next(attrs["src"] for tag, attrs in Elements(body).tags if tag == "img")
        self.assertEqual(before[image], base64.b64decode(src.split(",", 1)[1]))
        self.assertEqual((before[pdf], "application/pdf"), locations.read(locations.resolve(str(pdf))))
        body, _ = locations.read(locations.resolve(str(markdown)))
        scripts = [attrs for tag, attrs in Elements(body).tags if tag == "script"]
        self.assertEqual(1, len(scripts))
        self.assertIn("nonce", scripts[0])
        self.assertIn(b"Markdown.draw(", body)
        self.assertIn(b"\\u003c/script>", body)
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        print("Viewer files: text, image bytes, PDF bytes, Markdown script escaping and 5 folder links pass.")

    def test_named_lens_signin_and_scene_use_its_title(self):
        d = Desk()
        try:
            title = "Viewer lens & café"
            text = 'root : column\n  title : text "Agora lens inside Viewer"'
            self.assertTrue(d.say('make kind=lens name=viewer-fixture title=' +
                                  quoted(title) + ' text=' + quoted(text))["ok"])
            locations = Locations(d.url, d.entry.token("alex"))
            browser = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
            with browser.open(locations.resolve("viewer-fixture")) as response:
                query = parse_qs(urlsplit(response.url).query)
                self.assertIn(b'id="paint"', response.read())
            self.assertEqual([title], query["lens"])
            with browser.open(d.url + "/api/scene?" + urlencode(
                    {"lens": query["lens"][0], "view": "painter"})) as response:
                scene = json.load(response)
            self.assertNotIn("refused", scene, scene)
            self.assertIn("Agora lens inside Viewer", json.dumps(scene))
            print("Viewer lens: sign-in cookie, title lookup and painter scene pass.")
        finally:
            d.close()

    def test_dock_pin_opens_one_viewer_and_migration_is_idempotent(self):
        import kdesk
        d = Desk()
        try:
            pins = [r for r in d.say("rows button")["rows"] if r.get("does") == "window.open viewer"]
            self.assertEqual(1, len(pins))
            for _ in range(2):
                self.assertTrue(d.say(pins[0]["does"])["ok"])
            d.wait(lambda: d.window("viewer"))
            self.assertEqual(1, len([w for w in d.windows() if w["shows"] == "viewer"]))
            kdesk.after_genesis(d.k, headless=True)
            self.assertEqual(1, len([r for r in d.say("rows button")["rows"] if r.get("does") == "window.open viewer"]))
            print("Viewer dock pin opens one window; repeated migration keeps one pin.")
        finally:
            d.close()

    def test_local_routes_are_opaque_and_text_is_inert(self):
        SCRATCH.mkdir(exist_ok=True)
        p = SCRATCH / "escaping & spaces.txt"
        p.write_text("<script>fetch('https://example.invalid')</script>\nCafé", encoding="utf-8")
        locations = Locations("http://127.0.0.1:1", "")
        url = locations.resolve(str(p))
        self.assertTrue(url.startswith(LOCAL))
        self.assertNotIn(p.name, url)
        body, mime = locations.read(url)
        self.assertEqual("text/html", mime)
        self.assertIn(b"&lt;script&gt;", body)
        self.assertIn(b"default-src 'none'", body)
        self.assertEqual(url, locations.resolve(p.as_uri()))
        with self.assertRaises(KeyError):
            locations.read(LOCAL + "not-registered")
        with self.assertRaises(ValueError):
            locations.resolve("javascript:alert(1)")


def fixture():
    """Runs wholly on the hidden desktop; exercises actual GuiScreen.open."""
    SCRATCH.mkdir(exist_ok=True)
    sys.stderr = open(SCRATCH / "native-stderr.txt", "w", encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr
    import logging
    from types import SimpleNamespace
    from PIL import Image, ImageDraw
    import webview
    from kd_window import GuiScreen
    sys.path.insert(0, str(HERE.parent))
    import sandbox_window as sw
    SCRATCH.mkdir(exist_ok=True)
    logging.basicConfig(filename=str(SCRATCH / "native.log"), level=logging.DEBUG, force=True)
    logging.getLogger("pywebview").addHandler(logging.FileHandler(SCRATCH / "native-webview.log", mode="w", encoding="utf-8"))
    # Avoid pywebview's TemporaryDirectory too; this is fixture-only storage.
    from test_kdesk import scratch_dir
    profile = scratch_dir("viewer-profile-")
    original_start = webview.start
    webview.start = lambda *args, **kwargs: original_start(*args, storage_path=profile, **kwargs)
    files = SCRATCH / "files"
    files.mkdir(exist_ok=True)
    text = files / "hello & café.txt"
    text.write_text("Hello from a local text file.\n<script>window.bad=true</script>\nCafé", encoding="utf-8")
    markdown = files / "read me.md"
    markdown.write_text("# Markdown fixture\n\n**Bold words** and `code`.\n\n- one\n- two\n\n<script>window.bad=true</script>", encoding="utf-8")
    image = files / "picture.png"
    im = Image.new("RGB", (560, 240), "#b3ded3")
    ImageDraw.Draw(im).text((40, 100), "A local image in Viewer", fill="#243c37")
    im.save(image)
    pdf = files / "paper.pdf"
    im.save(pdf, "PDF")
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files.iterdir()}
    d = Desk()
    import kd_window
    kd_window.PORT = d.srv.server_address[1]
    class Web(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            body = (b"<!doctype html><title>Fixture web</title><body style='background:#eef8ff;font:24px Segoe UI;padding:48px'>"
                    b"<h1>Web page in Viewer</h1><p>This page refuses iframe embedding.</p>"
                    b"<a href='/next'>Next page</a> <a target='_blank' href='/popup'>Same-window popup</a></body>")
            if self.path == "/next":
                body = b"<h1>Next web page</h1>"
            if self.path == "/popup":
                body = b"<h1>Popup in the same Viewer</h1>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("X-Frame-Options", "DENY")
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *_):
            pass
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Web)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    page = f"http://127.0.0.1:{server.server_address[1]}/"
    made = d.say('make kind=lens name=viewer-fixture title="Viewer fixture lens" text=' +
                 quoted('root : column\n  title : text "Agora lens inside Viewer"\n  body : text "Painted by the existing lens painter."'))
    assert made["ok"], made
    note = d.say('make kind=note name="Viewer fixture note" text="A thing read inside Viewer."')
    assert note["ok"], note
    module = SimpleNamespace(token=d.entry.token("alex"))
    screen = GuiScreen(module)
    shown = threading.Event()
    result = {"ok": False, "checks": []}

    def wait(cond, timeout=20):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            value = cond()
            if value:
                return value
            time.sleep(.1)
        raise AssertionError("Native Viewer wait timed out")

    def run():
        try:
            from System import Action
            screen.open("fixture", "viewer", "Viewer fixture", d.url + "/desk/viewer.html",
                        (50, 50, 1100, 780), lambda: None, shown.set)
            print("Screen.open returned", flush=True)
            win = screen.wins["fixture"]["w"]

            def ui(fn):
                done, value = threading.Event(), {}
                def call():
                    try:
                        value["result"] = fn()
                    except Exception as exc:
                        value["error"] = exc
                    finally:
                        done.set()
                win.native.BeginInvoke(Action(call))
                assert done.wait(10), "UI thread stalled"
                if "error" in value:
                    raise value["error"]
                return value.get("result")

            if not shown.wait(20):
                initialization = ui(lambda: win.native.browser.webview.EnsureCoreWebView2Async(None))
                diagnostic = ui(lambda: {
                    "source": str(win.native.browser.webview.Source),
                    "core": str(win.native.browser.webview.CoreWebView2),
                    "visible": win.native.Visible,
                    "loaded": win.events.loaded.is_set(),
                    "attached": hasattr(win, "agora_viewer"),
                    "handle": str(win.native.browser.webview.Handle),
                    "init_done": initialization.IsCompleted,
                    "init_error": str(initialization.Exception),
                })
                raise AssertionError("Viewer did not show: " + repr(diagnostic))
            controller = wait(lambda: getattr(win, "agora_viewer", None))
            core = wait(lambda: ui(lambda: controller.view.CoreWebView2 or controller.init_error), 60)
            assert not isinstance(core, str), core
            def js(expression):
                task = ui(lambda: core.ExecuteScriptAsync(expression))
                wait(lambda: task.IsCompleted)
                return json.loads(str(task.Result))
            def ready(expression):
                wait(lambda: js(expression))
            def shot(name):
                # CapturePreview flushes WebView2's compositor before PrintWindow.
                from System.IO import MemoryStream
                from Microsoft.Web.WebView2.Core import CoreWebView2CapturePreviewImageFormat as Format
                stream = MemoryStream()
                task = ui(lambda: core.CapturePreviewAsync(Format.Png, stream))
                wait(lambda: task.IsCompleted)
                (SCRATCH / (name + "-content.png")).write_bytes(bytes(stream.ToArray()))
                stream.Dispose()
                hwnd = int(win.native.Handle.ToInt64())
                sw.print_window(hwnd).save(SCRATCH / (name + ".png"))
            def visit(value, expression, name):
                ui(lambda: (setattr(controller.address, "Text", value), controller.go.PerformClick()))
                ready(expression)
                assert ui(lambda: str(controller.status.Text)) == "Ready"
                shot(name)
                result["checks"].append(name)

            ready("document.body.innerText.includes('Enter a web address')")
            visit(page, "document.body.innerText.includes('Web page in Viewer')", "web")
            assert js("typeof window.pywebview") == "undefined", "Remote content has a native bridge"
            js("document.querySelector('a').click()")
            ready("document.body.innerText.includes('Next web page')")
            ui(lambda: controller.back.PerformClick())
            ready("document.body.innerText.includes('Web page in Viewer')")
            ui(lambda: controller.forward.PerformClick())
            ready("document.body.innerText.includes('Next web page')")
            ui(lambda: controller.back.PerformClick())
            ready("document.body.innerText.includes('Web page in Viewer')")
            js("document.querySelector('[target]').click()")
            ready("document.body.innerText.includes('Popup in the same Viewer')")
            result["checks"].append("web-links-back-forward-popup")
            visit("viewer-fixture", "document.body.innerText.includes('Agora lens inside Viewer')", "lens")
            assert ui(lambda: str(controller.address.Text)) == "Viewer fixture lens"
            visit("Viewer fixture note", "document.body.innerText.includes('A thing read inside Viewer.')", "thing")
            visit(str(text), "document.body.innerText.includes('Hello from a local text file.')", "text")
            assert js("window.bad === undefined")
            visit(str(image), "document.images.length===1 && document.images[0].naturalWidth===560", "image")
            visit(str(files), "document.querySelectorAll('li a').length===5", "folder")
            link = js("[...document.querySelectorAll('a')].find(a=>a.textContent.includes('hello')).href")
            js("location.href=" + json.dumps(link))
            ready("document.body.innerText.includes('Hello from a local text file.')")
            ui(lambda: controller.back.PerformClick())
            ready("document.querySelectorAll('li a').length===5")
            ui(lambda: controller.forward.PerformClick())
            ready("document.body.innerText.includes('Hello from a local text file.')")
            result["checks"].append("folder-click-back-forward")
            visit(str(markdown), "!!document.querySelector('.md-h1') && !!document.querySelector('strong')", "markdown")
            assert js("window.bad === undefined")
            # PDF viewer lives in Chromium's PDF extension, not the top-page DOM.
            ui(lambda: controller.navigate(str(pdf)))
            wait(lambda: ui(lambda: str(controller.view.Source).startswith(LOCAL) and str(controller.address.Text) == str(pdf)))
            wait(lambda: ui(lambda: str(controller.status.Text)) == "Ready")
            time.sleep(2)
            shot("pdf")
            result["checks"].append("pdf")
            ui(lambda: controller.navigate(str(files / "missing.txt")))
            ready("document.body.innerText.includes('does not exist')")
            result["checks"].append("missing-file-error")
            after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files.iterdir()}
            assert before == after, "A viewed file changed"
            result["checks"].append("file-bytes-unchanged")
            result["ok"] = True
        except Exception:
            import traceback
            result["error"] = traceback.format_exc()
        finally:
            (SCRATCH / "native-result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
            for rec in list(screen.wins.values()):
                rec["w"].destroy()
            screen.anchor.destroy()
            d.close()
            server.shutdown()
            server.server_close()
    screen.start(lambda: threading.Thread(target=run, daemon=True).start())


def native():
    sys.path.insert(0, str(HERE.parent))
    import sandbox_window as sw
    SCRATCH.mkdir(exist_ok=True)
    sw.STATE = SCRATCH / "sandbox"
    sw.STATE.mkdir(exist_ok=True)
    name = "viewer-dk1656"
    result_file = SCRATCH / "native-result.json"
    if result_file.exists():
        result_file.unlink()
    with sw.Guard(name, "Viewer fixture") as guard:
        sw.run_hidden(name, [PY, str(Path(__file__).resolve()), "--fixture"],
                      env={"WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS": "--disable-gpu"})
        end = time.monotonic() + 100
        while not result_file.exists() and time.monotonic() < end:
            time.sleep(.2)
        assert result_file.exists(), "Native fixture did not finish"
        result = json.loads(result_file.read_text(encoding="utf-8"))
        print(json.dumps(result, indent=2))
    code, words = guard.verdict()
    print("Hidden desktop guard:", words)
    (SCRATCH / "guard-result.txt").write_text(words, encoding="utf-8")
    assert code == 0, words
    assert result["ok"], result.get("error")


if __name__ == "__main__":
    if "--fixture" in sys.argv:
        try:
            fixture()
        except Exception:
            import traceback
            (SCRATCH / "native-result.json").write_text(json.dumps({"ok": False, "error": traceback.format_exc()}), encoding="utf-8")
            raise
    elif "--native" in sys.argv:
        native()
    else:
        unittest.main()
