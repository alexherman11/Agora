"""bridge_page.py <url> <log> (a7950): one pywebview (WebView2) window with a js_api bridge, as hud.py makes the home
base (gui edgechromium, js_api), for seam_browser.py on the sandbox desktop only: no hotkey, no hooks, no Esc.

The bridge has one method, touched(*words), which appends its words to <log>: a call that reaches Python leaves a line.
"""
import json
import sys

import webview


class Bridge:
    def touched(self, *words):
        with open(sys.argv[2], "a", encoding="utf-8") as f:
            f.write(json.dumps(list(words)) + "\n")
        return "recorded"


webview.create_window("Agora map bridge check", sys.argv[1], js_api=Bridge(), width=1200, height=800)
webview.start(gui="edgechromium", private_mode=True)
