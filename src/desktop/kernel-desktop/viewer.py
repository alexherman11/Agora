"""EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
(people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.

Viewer's native content pane. No web server for files, and no native bridge in web content.

The existing pywebview window owns the form/lifetime. A plain WebView2 control
and a native address strip sit in that form, so sites need not permit framing.
Only navigation state lives here; opening a page/file creates no world thing.
"""
import base64
import html
import json
import mimetypes
import re
import threading
import urllib.request
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit
from uuid import uuid4

HERE = Path(__file__).resolve().parent
LOCAL = "https://agora-viewer.invalid/"
MARKDOWN = HERE.parents[1] / "text-desk/notation/desk-shell/markdown.js"
STYLE = """body{margin:0;background:#f6f3ec;color:#243c37;font:17px/1.6
Segoe UI,sans-serif}main{max-width:960px;margin:40px auto;padding:0 32px}
h1{font-size:30px}a{color:#176d66}li{margin:8px 0}pre{white-space:pre-wrap;
overflow-wrap:anywhere;font:15px/1.6 Consolas,monospace}img{display:block;
max-width:100%;max-height:82vh;margin:auto}.hint{color:#667771}"""


def document(title, body, script=""):
    nonce = uuid4().hex
    policy = ("default-src 'none'; img-src data:; style-src 'unsafe-inline'; "
              f"script-src 'nonce-{nonce}'; base-uri 'none'; form-action 'none'")
    return ("<!doctype html><meta charset=utf-8><meta http-equiv="
            f'"Content-Security-Policy" content="{policy}"><title>{html.escape(title)}</title>'
            f"<style>{STYLE}</style><main>{body}</main>"
            + (f'<script nonce="{nonce}">{script}</script>' if script else "")).encode("utf-8")


def file_path(value):
    if value.lower().startswith("file:"):
        url = urlsplit(value)
        value = unquote(url.path)
        if url.netloc:
            value = "//" + url.netloc + value
        elif re.match(r"^/[a-z]:", value, re.I):
            value = value[1:]
    return Path(value).expanduser()


class Locations:
    """Resolve user input, and serve only opaque URLs registered by this viewer."""
    def __init__(self, origin, token):
        self.origin, self.token = origin.rstrip("/"), token
        self.files, self.labels = {}, {}

    def register(self, path):
        path = Path(path).resolve()
        for url, old in self.files.items():
            if path == old:
                return url
        url = LOCAL + uuid4().hex
        self.files[url], self.labels[url] = path, str(path)
        return url

    def resolve(self, value):
        value = value.strip().strip('"')
        if not value:
            raise ValueError("Enter a web address, a lens or thing name, or a file path.")
        if value.lower().startswith(("http://", "https://")):
            if not urlsplit(value).hostname:
                raise ValueError("That web address needs a host name.")
            return value
        path = file_path(value)
        if (value.lower().startswith("file:") or path.is_absolute()
                or value.startswith((".", "~", "\\\\")) or path.exists()):
            if not path.exists():
                raise ValueError("That file or folder does not exist.")
            return self.register(path)
        if re.match(r"^(localhost|\w[\w.-]*\.[a-z]{2,})(:\d+)?([/?#]|$)", value, re.I):
            return "https://" + value
        if "://" in value or value.lower().startswith(("javascript:", "data:", "about:")):
            raise ValueError("Use a web address, a lens or thing name, or a file path.")
        request = urllib.request.Request(self.origin + "/see",
            json.dumps({"line": "look " + json.dumps(value, ensure_ascii=False)}).encode(),
            {"Authorization": "Bearer " + self.token, "Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=8) as response:
            out = json.load(response)
        rows = out.get("rows", [])
        if not out.get("ok") or not rows:
            raise ValueError("No lens or thing with that name was found.")
        thing = rows[0]
        if thing.get("kind") == "lens":
            # The shared scene compiler resolves the facade's title, not a
            # kernel id (nor necessarily the name entered in the address bar).
            title = thing.get("title") or thing.get("name") or thing.get("label") or (thing.get("text") or "").split("\n")[0][:80]
            dest = "/lens.html?inspect=0&lens=" + quote(title, safe="")
        else:
            dest = "/desk/thing.html?target=" + quote(thing["id"])
        self.labels[self.origin + dest] = thing.get("title") or thing.get("name") or value
        return self.origin + "/dev/signin?token=" + quote(self.token) + "&next=" + quote(dest, safe="")

    def read(self, url):
        path = self.files[url.split("#", 1)[0]]
        name = html.escape(path.name or str(path))
        if path.is_dir():
            entries = ([path.parent] if path.parent != path else []) + sorted(
                path.iterdir(), key=lambda p: (not p.is_dir(), p.name.casefold()))
            links = []
            for child in entries:
                label = "Parent folder" if child == path.parent else child.name + ("/" if child.is_dir() else "")
                links.append(f'<li><a href="{self.register(child)}">{html.escape(label)}</a></li>')
            return document(str(path), f"<h1>{name}</h1><p class=hint>Folder · read only</p><ul>{''.join(links)}</ul>"), "text/html"
        if path.stat().st_size > 64 * 1024 * 1024:
            raise ValueError("This file is larger than the Viewer's 64 MB preview limit.")
        data = path.read_bytes()
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return data, "application/pdf"
        if suffix in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico"):
            mime = mimetypes.guess_type(path.name)[0] or "image/png"
            image = base64.b64encode(data).decode()
            return document(path.name, f'<h1>{name}</h1><img alt="{name}" src="data:{mime};base64,{image}">'), "text/html"
        if b"\0" in data[:4096] and not data.startswith((b"\xff\xfe", b"\xfe\xff")):
            raise ValueError("No preview for this file type. Try text, Markdown, an image or PDF.")
        text = data.decode("utf-16" if data.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig", errors="replace")
        if suffix in (".md", ".markdown"):
            # Reuse Agora's DOM-only Markdown renderer: raw HTML stays text,
            # media have no admitted source and nothing becomes editable.
            script = MARKDOWN.read_text(encoding="utf-8")
            script += "\nMarkdown.draw(document.getElementById('words')," + json.dumps(text).replace("<", "\\u003c") + ",{},new Set(),false);"
            script += "\nfor(const a of document.querySelectorAll('[data-href]')){const u=a.dataset.href;if(/^https?:\\/\\//i.test(u))a.href=u;}"
            return document(path.name, f"<h1>{name}</h1><div id=words class=md-doc></div>", script), "text/html"
        return document(path.name, f"<h1>{name}</h1><p class=hint>Text · read only</p><pre>{html.escape(text)}</pre>"), "text/html"


class Viewer:
    """Construct on the form's UI thread, after pywebview's blank page loads."""
    def __init__(self, window, origin, token):
        from webview.platforms.edgechromium import WebView2, CoreWebView2CreationProperties
        from System.Windows.Forms import ToolStrip, ToolStripButton, ToolStripTextBox, ToolStripLabel, ToolStripGripStyle, Keys, DockStyle
        from System.Drawing import Color

        self.window, self.form = window, window.native
        self.init_error = None
        self.locations = Locations(origin, token)
        self.serial = 0
        self.form.browser.webview.Visible = False
        self.bar = ToolStrip()
        self.bar.Dock = DockStyle.Top
        self.bar.GripStyle = ToolStripGripStyle.Hidden
        self.bar.BackColor = Color.FromArgb(246, 243, 236)
        self.back, self.forward = ToolStripButton("←"), ToolStripButton("→")
        self.back.ToolTipText, self.forward.ToolTipText = "Back (Alt+Left)", "Forward (Alt+Right)"
        self.address = ToolStripTextBox()
        self.address.AutoSize = False
        self.address.AccessibleName = "Web address, lens or thing name, or file path"
        self.go = ToolStripButton("Go")
        self.status = ToolStripLabel("Ready")
        for item in (self.back, self.forward, self.address, self.go, self.status):
            self.bar.Items.Add(item)
        self.view = WebView2()
        props = CoreWebView2CreationProperties()
        host_props = self.form.browser.webview.CreationProperties
        props.UserDataFolder = host_props.UserDataFolder
        props.BrowserExecutableFolder = host_props.BrowserExecutableFolder
        props.AdditionalBrowserArguments = host_props.AdditionalBrowserArguments
        props.ProfileName = "viewer-" + uuid4().hex
        props.set_IsInPrivateModeEnabled(True)
        self.view.CreationProperties = props
        self.view.Dock = DockStyle.Fill
        self.form.Controls.Add(self.view)
        self.form.Controls.Add(self.bar)
        self.view.BringToFront()
        self.bar.BringToFront()
        self.form.Resize += self.resize
        self.resize(None, None)
        self.back.Click += lambda *_: self.view.GoBack() if self.view.CanGoBack else None
        self.forward.Click += lambda *_: self.view.GoForward() if self.view.CanGoForward else None
        self.go.Click += lambda *_: self.navigate(str(self.address.Text))

        def key(sender, event):
            if event.KeyCode == Keys.Enter:
                event.SuppressKeyPress = True
                self.navigate(str(self.address.Text))
        self.address.KeyDown += key
        self.form.KeyPreview = True
        def shortcut(sender, event):
            if event.Control and event.KeyCode == Keys.L:
                self.address.Focus()
                self.address.SelectAll()
                event.SuppressKeyPress = True
            elif event.Alt and event.KeyCode in (Keys.Left, Keys.Right):
                button = self.back if event.KeyCode == Keys.Left else self.forward
                button.PerformClick()
                event.SuppressKeyPress = True
        self.form.KeyDown += shortcut
        self.view.CoreWebView2InitializationCompleted += self.ready
        self.view.EnsureCoreWebView2Async(None)

    def resize(self, *_):
        self.address.Width = max(180, self.form.ClientSize.Width - 280)

    def ui(self, fn):
        from System import Action
        if not self.form.IsDisposed:
            self.form.BeginInvoke(Action(fn))

    def navigate(self, value):
        self.serial += 1
        serial = self.serial
        self.status.Text = "Opening…"
        def resolve():
            try:
                url = self.locations.resolve(value)
                def apply():
                    if serial == self.serial:
                        self.view.CoreWebView2.Navigate(url)
                self.ui(apply)
            except Exception as exc:
                message = str(exc)
                self.ui(lambda: self.error(message) if serial == self.serial else None)
        threading.Thread(target=resolve, daemon=True, name="viewer-location").start()

    def error(self, message):
        self.status.Text = "Could not open"
        self.status.ToolTipText = message
        if self.view.CoreWebView2 is not None:
            self.view.CoreWebView2.NavigateToString(document("Could not open", "<h1>Could not open</h1><p>" + html.escape(message) + "</p>").decode())

    def ready(self, sender, event):
        if not event.IsSuccess:
            self.init_error = str(event.InitializationException)
            return self.error("WebView2 could not start: " + self.init_error)
        from Microsoft.Web.WebView2.Core import CoreWebView2WebResourceContext
        core = self.view.CoreWebView2
        # This control has no pywebview injection, host objects or message handler.
        core.AddWebResourceRequestedFilter(LOCAL + "*", CoreWebView2WebResourceContext.All)
        core.WebResourceRequested += self.resource
        core.SourceChanged += self.changed
        core.HistoryChanged += self.changed
        core.NavigationCompleted += self.completed
        core.NavigationStarting += self.starting
        core.NewWindowRequested += self.popup
        core.NavigateToString(document("Viewer", "<h1>Viewer</h1><p>Enter a web address, a lens or thing name, or a file path above.</p><p class=hint>Pages, Agora and your files · Back and Forward · Ctrl+L to enter an address</p>").decode())

    def resource(self, sender, event):
        from System import Array, Byte
        from System.IO import MemoryStream
        try:
            data, mime = self.locations.read(str(event.Request.Uri))
            code = 200
        except Exception as exc:
            data, mime, code = document("Could not open", "<h1>Could not open</h1><p>" + html.escape(str(exc)) + "</p>"), "text/html", 404
        stream = MemoryStream(Array[Byte](data))
        event.Response = sender.Environment.CreateWebResourceResponse(stream, code, "OK" if code == 200 else "Not found",
            "Content-Type: " + mime + "\r\nCache-Control: no-store\r\n")

    def starting(self, sender, event):
        # File reads are only address-bar actions or registered local links.
        # Web pages cannot turn a file: navigation into an ambient local read.
        if urlsplit(str(event.Uri)).scheme not in ("http", "https", "about"):
            event.Cancel = True
            self.status.Text = "Use the address bar to open files"

    def changed(self, *_):
        url = str(self.view.Source or "")
        if "/dev/signin?" not in url and url != "about:blank":
            self.address.Text = self.locations.labels.get(url.split("#", 1)[0], url)
        self.back.Enabled, self.forward.Enabled = self.view.CanGoBack, self.view.CanGoForward

    def completed(self, sender, event):
        self.changed()
        self.status.Text = "Ready" if event.IsSuccess else "Page did not load"
        self.status.ToolTipText = "" if event.IsSuccess else str(event.WebErrorStatus)

    def popup(self, sender, event):
        event.Handled = True
        sender.Navigate(str(event.Uri))


def attach(window, origin, token):
    from System import Action
    def install():
        if not hasattr(window, "agora_viewer"):
            window.agora_viewer = Viewer(window, origin, token)
    window.native.Invoke(Action(install))
