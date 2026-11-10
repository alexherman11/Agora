"""bridge_page.py <url> <log> [<allowed origin>] (a7950): one pywebview (WebView2) window with a js_api bridge, as hud.py
makes the home base (gui edgechromium, js_api), for seam_browser.py on the sandbox desktop only: no hotkey, no hooks,
no Esc.

The bridge has one method, touched(*words), which appends its words to <log>: a call that reaches Python leaves a line.

With an allowed origin (Pike c8089: can the Python side refuse a bridge message that is not the desk's own document?),
pywebview's message handler is wrapped, here and not in the package: a message whose source document is not on that
origin is refused before pywebview reads it, and the refusal is written to <log> as ["refused", <source>]. pywebview
puts its bridge into whatever top document loads (on_navigation_completed), so this is the check that matters if the
top page ever leaves the desk.
"""
import json
import sys

import webview

LOG = sys.argv[2]
ALLOWED = sys.argv[3] if len(sys.argv) > 3 else None


def write(words):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(list(words)) + "\n")


class Bridge:
    def touched(self, *words):
        write(words)
        return "recorded"


if ALLOWED:
    from webview.platforms import edgechromium

    heard = edgechromium.EdgeChrome.on_script_notify

    def guarded(self, sender, args):
        src = str(args.Source or "")
        if not src.startswith(ALLOWED.rstrip("/") + "/"):
            write(["refused", src[:120]])
            return None
        return heard(self, sender, args)

    edgechromium.EdgeChrome.on_script_notify = guarded      # before the window exists, so its handler is this one

webview.create_window("Agora map bridge check", sys.argv[1], js_api=Bridge(), width=1200, height=800)
webview.start(gui="edgechromium", private_mode=True)
