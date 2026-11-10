"""The kernel door for a public host: the kernel's own door, plus the widget host's trusted page and broker, so a plain
phone browser can open a component-painter widget (the Seabright board) the way a desktop widget window does.

Claude, 5 Nov 2026, for the Seabright meeting (src/community/board/PUBLIC-HOST.md). Source: seam (a host).

    python src/community/deploy/public_door.py --world <dir> [--genesis <genesis.json>] --port 8810 \
        --entry http://127.0.0.1:8817 --origin https://seabright.example.org --home-widget seabright-board

What it adds to kernel/door.py, and why it is safe without the desktop's X-Agora-Widget-Host guard:
- GET /desk/<page> serves only the widget host's trusted parent (widget.html and the scripts it loads) from
  src/desktop/kernel-desktop/pages, unchanged. The parent runs the widget's code in a sandboxed srcdoc frame
  (opaque origin, its own CSP with connect-src 'none'); only the parent talks to the broker.
- POST /desk/widget/<action> is the same broker (widgets.py), signed in, same-origin only. A sandboxed frame's request
  carries Origin: null and is refused here before any line runs. Every act still runs as the viewer narrowed to the
  widget's grants (kernel/inpage.py Principal), exactly as on the desktop.
- What the desktop guard adds that a browser cannot: the native WebView2 guard also stops a frame navigating itself
  away (an exfiltration path CSP does not cover). Here only reviewed components a steward installed should run.
- GET <--board-path> (default /) sends a signed-in member to the home widget, a signed-in account that has not joined to /welcome, and anyone
  else to the public site (--public, default /about).
- POST from the public https origin is same-site: the kernel's own _cross_site compares with http:// only.
The name of the home widget and the public origin are settings (arguments), not source.
"""
import argparse
import json
import mimetypes
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
LAB = REPO / "src" / "agora"
DESK = REPO / "src" / "desktop" / "kernel-desktop"
PAGES = DESK / "pages"
sys.path[:0] = [str(LAB), str(DESK)]

from kernel import door as KD           # noqa: E402
from kernel.kernel import Kernel        # noqa: E402
from widgets import Widgets             # noqa: E402

# the trusted parent and what it loads (widget.html), nothing else of the desktop's pages
HOST_PAGES = {"widget.html", "kd.js", "kd.css", "menu.js", "theme-live.js", "widget-host.js", "widget-slots.js"}
THEME = ("theme.css", "theme.json", "theme-native.json", "theme-wallpaper")


def make_handler(kernel, entry, secret, origin, home_widget, public, board_path="/"):
    Base = KD.make_handler(kernel, entry, secret)
    widgets = Widgets(kernel)

    class Handler(Base):
        widget_broker = widgets

        def _cross_site(self):
            o = self.headers.get("Origin")
            return o is not None and o not in (origin, f"http://{self.headers.get('Host')}")

        def _home(self):
            for w in kernel.things("widget"):
                if kernel.state.get(w, "name") == home_widget and not kernel.state.get(w, "forgotten"):
                    return w
            return None

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == board_path:
                actor, why = self._actor()
                if actor is None:
                    where = "/welcome" if why and "not joined" in why else public
                    return self._raw(302, b"", "text/plain", [("Location", where)])
                w = self._home()
                if w is None:
                    return self._raw(503, b"The board is being set up. Try again in a minute.", "text/plain; charset=utf-8")
                return self._raw(302, b"", "text/plain", [("Location", f"/desk/widget.html?slot=1&widget={w}")])   # slot: no desktop window strip
            if path.startswith("/desk/") and path[6:] in THEME:
                from urllib.parse import parse_qs
                q = {k: v[0] for k, v in parse_qs(urlsplit(self.path).query).items()}
                return self._theme(path[6:], q, "/desk/")
            if path.startswith("/desk/"):
                rel = path[6:]
                if rel not in HOST_PAGES:
                    return self._send(404, {"error": "no such page"})
                p = PAGES / rel
                ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
                if ctype.startswith("text/") or ctype.endswith("javascript"):
                    ctype += "; charset=utf-8"
                data = p.read_bytes()
                if rel == "widget.html":
                    # a phone lays the page out at its own width, not a 980 px desktop page shrunk down
                    data = data.replace(b'<meta charset="utf-8">', b'<meta charset="utf-8"><meta name="viewport" '
                                        b'content="width=device-width, initial-scale=1">', 1)
                return self._raw(200, data, ctype)
            return super().do_GET()

        def do_POST(self):
            path = urlsplit(self.path).path
            if not path.startswith("/desk/widget/"):
                return super().do_POST()
            if self._cross_site() or self.headers.get("Origin") is None:
                return self._send(403, {"ok": False, "text": "foreign origin"})
            actor, why = self._actor()
            if actor is None:
                return self._send(401, {"ok": False, "text": why})
            from kernel.blobs import cap
            size = int(self.headers.get("Content-Length") or 0)
            if size > max(100000, 4 * ((cap(kernel) + 2) // 3) + 16384):
                return self._send(413, {"ok": False, "text": "bridge message too large"})
            body = {}
            try:
                body = self._body() or {}
                if size > 100000 and body.get("op") != "upload":
                    return self._send(413, {"ok": False, "text": "bridge message too large"})
                out = widgets.request(actor, path.rsplit("/", 1)[-1], body)
            except (KD.Refused, ValueError, KeyError, TypeError) as e:
                out = {"ok": False, "text": "refused: " + str(e)}
                if not getattr(e, "agora_kept", False):
                    kernel.refusals.keep(e, str(body.get("line") or ""), actor=actor, via="widget",
                                         where=f"widget {path.rsplit('/', 1)[-1]}",
                                         kind="refused" if isinstance(e, KD.Refused) else "error")
            return self._send(200, out)

    return Handler


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--world", required=True)
    ap.add_argument("--genesis")
    ap.add_argument("--port", type=int, default=8810)
    ap.add_argument("--entry", default="http://127.0.0.1:8817")
    ap.add_argument("--origin", required=True, help="the public origin, e.g. https://seabright.example.org")
    ap.add_argument("--home-widget", required=True, help="the widget's name that / opens for a signed-in member")
    ap.add_argument("--public", default="/about", help="where the board path sends someone not signed in")
    ap.add_argument("--board-path", default="/", help="the path that opens the home widget, e.g. /board")
    a = ap.parse_args()
    genesis = None
    if a.genesis:
        sys.path.insert(0, str(LAB))
        from start_kernel import load_genesis
        genesis = load_genesis(a.genesis)
    k = Kernel(a.world, genesis)
    secret = os.environ.get("KERNEL_SHARED_SECRET", "")
    entry = KD.EntryClient(a.entry, secret)
    srv = KD.Server(("127.0.0.1", a.port), make_handler(k, entry, secret, a.origin.rstrip("/"), a.home_widget, a.public, a.board_path))
    host = KD.Host(k, LAB)
    host.reconcile()
    print(f"public kernel door on http://127.0.0.1:{a.port} · world {a.world} · {len(k.log.records)} records", flush=True)
    try:
        srv.serve_forever()
    finally:
        host.stop_all()


if __name__ == "__main__":
    main()
