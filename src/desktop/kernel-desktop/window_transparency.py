"""EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
(people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.

Transparent windows (the shell's top bar and dock) are shown by the host, never by pywebview (dk1136, 28 Oct 2026).

Pinned pywebview `EdgeChrome.on_navigation_start` does `form.Show(); form.Activate()` for every transparent window on
every navigation ("hack to make transparent window work"), even one made with hidden=True. For the bars that meant:

  * the first navigation showed the 3840x840 top bar and the 2340x690 dock before kd_window had put them on DWM glass,
    and a transparent WebView2 off glass draws its whole window rect white (shell_native.glass): a big white block
    until the page loaded;
  * every later navigation (the page's own location.reload() after a restart) showed the bar again, and activated it,
    even while it had stepped back for a full-screen game.

A failed navigation is the other half: WebView2's error page is opaque, and DWM does not clip a WebView2's drawing to
the window region, so a bar whose page reloads while the door is down shows the error page over its whole window.
`on_navigation_completed` tells the host (window.agora_navigated(ok)) so it can hide that bar and try the page again.
"""


def install():
    """Install before constructing any EdgeChrome: its handlers are bound to the instance at construction."""
    from webview.platforms import edgechromium

    chrome = edgechromium.EdgeChrome
    if getattr(chrome, "_agora_window_transparency", False):
        return
    started, completed = chrome.on_navigation_start, chrome.on_navigation_completed

    def on_navigation_start(self, sender, args):
        if self.pywebview_window.transparent:
            return                                      # the host shows it, on glass, when its page has loaded
        return started(self, sender, args)

    def on_navigation_completed(self, sender, args):
        try:
            return completed(self, sender, args)
        finally:
            told = getattr(self.pywebview_window, "agora_navigated", None)
            if told:
                told(navigation_ok(args))

    chrome.on_navigation_start, chrome.on_navigation_completed = on_navigation_start, on_navigation_completed
    chrome._agora_window_transparency = True


def navigation_ok(args):
    """Did the page itself arrive? False for a network error page and for an HTTP error (a refused sign-in)."""
    try:
        if not bool(args.IsSuccess):
            return False
    except Exception:                                   # noqa: BLE001  no answer is not a failure
        return True
    try:
        return not 400 <= int(args.HttpStatusCode)
    except Exception:                                   # noqa: BLE001  an older WebView2 SDK has no status code
        return True
