"""webview_page.py <url> [WxH]: one pywebview (WebView2) window on a page, as hud.py makes its home base, with none of
hud.py's keys (no hotkey, no Win hook, no Esc, no control screen): for webview_drag.py on the sandbox desktop only."""
import sys

import webview

w, h = (int(v) for v in (sys.argv[2] if len(sys.argv) > 2 else "1700x1000").split("x"))
webview.create_window("Agora webview check", sys.argv[1], width=w, height=h, frameless=True, easy_drag=False)
webview.start()
