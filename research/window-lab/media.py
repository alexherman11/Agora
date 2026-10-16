"""media.py: the home base's small music controller (a5245). 15 Oct 2026.

    python media.py now                          what is playing, as the row the home base says
    python media.py play | next | prev           press that button, as the home base does

No sign-in and nothing new installed. What it reads and how it presses:
  - the track: Spotify's own window title, which is "Artist - Song" while a song plays and "Spotify", "Spotify Free"
    or "Spotify Premium" while paused. So the title is Spotify's only, and only while it plays; a paused Spotify says
    paused with no title (the window does not keep the last song's name).
  - the buttons: an app command (WM_APPCOMMAND, what a keyboard's media keys mean) posted to Spotify's window, so they
    reach Spotify even when a browser holds the system's media session. With no Spotify window, the media key itself
    is pressed (SendInput), and Windows gives it to whatever program holds the media session now.

rows() is what the home base keeps as `witnessed:media`: one row, {name: "media", player, playing (yes|no), title,
artist, line}, or no row when no player is found. press(action) is what a click on a part keyed media-play,
media-next or media-prev does.

The panel is the lens home-music (a5592, in Home base f5204, placed at the top of home-base's right column; its source
and a put script in home-music/ here): parts prev, play and next (role mediakey) that ask `on click host media.prev`
and so on (host_verbs.py, a5300), and a repeat over witnessed:media (each nowplaying: title, artist, "Paused").
hud.py writes witnessed:media in Hud.say_desktop and clears it in Hud.closed and --stop. CLICKS below is how the
buttons asked before host verbs (a5245); hud.py no longer injects it (a5592), and Hud.media / Api.media stay only for
a home base still running older code.
"""
import ctypes
import sys
from ctypes import wintypes as wt
from pathlib import Path

user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
WNDENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
WM_APPCOMMAND = 0x0319
APPCOMMAND = {"play": 14, "next": 11, "prev": 12}                      # MEDIA_PLAY_PAUSE, NEXTTRACK, PREVIOUSTRACK
VK = {"play": 0xB3, "next": 0xB0, "prev": 0xB1}                        # VK_MEDIA_PLAY_PAUSE, _NEXT_TRACK, _PREV_TRACK
IDLE = {"spotify", "spotify free", "spotify premium"}

user32.EnumWindows.argtypes = [WNDENUMPROC, wt.LPARAM]
user32.IsWindowVisible.argtypes = [wt.HWND]
user32.GetWindowTextLengthW.argtypes = [wt.HWND]
user32.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
user32.GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
user32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
user32.PostMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
user32.PostMessageW.restype = wt.BOOL
kernel32.OpenProcess.restype = wt.HANDLE
kernel32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
kernel32.QueryFullProcessImageNameW.argtypes = [wt.HANDLE, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD)]
kernel32.CloseHandle.argtypes = [wt.HANDLE]


# what the home base runs in its page: a click on a part with role mediakey whose part is named play, next or prev asks
# the host (pywebview's js_api) to press that button, and the painter does not also take the click
CLICKS = """(() => { if (window.__hudMedia) return; window.__hudMedia = 1;
  const cls = window.Style ? Style.roleClass('mediakey') : 'r-mediakey';
  document.addEventListener('click', e => {
    const b = e.target.closest && e.target.closest('.' + CSS.escape(cls) + '[data-key]'); if (!b) return;
    const a = b.dataset.key.split('/').pop(); if (!['play', 'next', 'prev'].includes(a)) return;
    e.preventDefault(); e.stopPropagation(); window.pywebview.api.media(a);
  }, true); })()"""


def _program(h):
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
    hp = kernel32.OpenProcess(0x1000, False, pid.value)
    if not hp:
        return ""
    try:
        buf, size = ctypes.create_unicode_buffer(520), wt.DWORD(520)
        return Path(buf.value).stem.lower() if kernel32.QueryFullProcessImageNameW(hp, 0, buf, ctypes.byref(size)) else ""
    finally:
        kernel32.CloseHandle(hp)


def spotify():
    """-> (window, title) of Spotify's titled top-level window, or (None, "")."""
    found = []

    def each(h, _):
        n = user32.GetWindowTextLengthW(h)
        cls = ctypes.create_unicode_buffer(64)
        user32.GetClassNameW(h, cls, 64)
        # its main window is Chromium's (Chrome_WidgetWin_*); it keeps helper windows titled "GDI+ Window" and the like
        if n and cls.value.startswith("Chrome_WidgetWin") and _program(h) == "spotify":
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(h, buf, n + 1)
            found.append((h, buf.value))
            return False
        return True

    user32.EnumWindows(WNDENUMPROC(each), 0)
    return found[0] if found else (None, "")


def rows():
    h, t = spotify()
    if not h:
        return []
    if t.strip().lower() in IDLE:
        return [{"name": "media", "player": "Spotify", "playing": "no", "title": "", "artist": "", "line": "Paused"}]
    artist, _, song = t.partition(" - ")
    if not song:
        artist, song = "", t
    return [{"name": "media", "player": "Spotify", "playing": "yes", "title": song, "artist": artist,
             "line": f"{song} · {artist}" if artist else song}]


class _KI(ctypes.Structure):
    _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD), ("time", wt.DWORD),
                ("dwExtraInfo", ctypes.c_size_t)]


class _IN(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [("ki", _KI), ("pad", ctypes.c_byte * 32)]
    _anonymous_ = ("u",)
    _fields_ = [("type", wt.DWORD), ("u", _U)]


def _key(vk):
    down, up = _IN(type=1), _IN(type=1)
    down.ki = _KI(vk, 0, 0x1, 0, 0)                                    # KEYEVENTF_EXTENDEDKEY
    up.ki = _KI(vk, 0, 0x1 | 0x2, 0, 0)                                # | KEYUP
    arr = (_IN * 2)(down, up)
    return user32.SendInput(2, arr, ctypes.sizeof(_IN)) == 2


def press(action):
    """play (play or pause), next or prev: to Spotify's window if there is one, else the media key. -> what it did."""
    if action not in APPCOMMAND:
        return ""
    h, _ = spotify()
    if h and user32.PostMessageW(h, WM_APPCOMMAND, h, APPCOMMAND[action] << 16):
        return "spotify"
    return "key" if _key(VK[action]) else ""


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "now"
    print(rows() if what == "now" else (press(what) or f"not done: {what} (now, play, next or prev)"))
