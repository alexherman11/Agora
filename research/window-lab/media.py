"""media.py: the home base's music controller (a5245; the system media session since a6443). 15 Oct 2026.

    python media.py now                          what is playing, as the row the home base says
    python media.py shape                        the same row by shape only (field: type and length), never the words
    python media.py play | next | prev           press that button, as the home base does

No sign-in and nothing new installed. What it reads, first that can answer:
  - the system media session (a6443, 17 Oct): what Windows tells every program about the media playing now, read by
    smtc.ps1 (Windows PowerShell's WinRT, nothing installed) run as this process's child: title, artist, album, the
    album art (a file in media/now-playing/, which the desk may show: media_links.py), play state, where in the song
    and how long it is, shuffle and repeat. Spotify's session when there is one, else the one Windows calls current.
  - else Spotify's own window title, which is "Artist - Song" while a song plays and "Spotify", "Spotify Free" or
    "Spotify Premium" while paused (a5245): no album, no art, no time, and a paused Spotify shows no song.
How it presses: through the session's own controls (TryTogglePlayPause and so on: no key is pressed, no window takes
focus); with no session, an app command (WM_APPCOMMAND, what a keyboard's media keys mean) posted to Spotify's window;
with no Spotify window, the media key itself (SendInput), which Windows gives to whatever holds the media session.

rows() is what the home base keeps as `witnessed:media`: one row or none.
    name media · player (Spotify, Edge ...) · playing yes|no · title · artist · album · line ("song · artist")
    art     the album art's path (media/now-playing/<hash>.jpg), or empty
    at      the song's progress as `live until` words: "<the moment it ends> of <its length in s>" while it plays, or
            "<seconds left> of <length>" while paused (standing still); empty when the app says no length
    length  its length as m:ss · shuffle on|off|"" (the app does not say) · repeat off|track|list|""
    can     the controls the app offers now: the words of play pause next prev shuffle repeat, joined by spaces
    liked   yes|no|unknown, and like_why: why unknown (spotify_like.py: Liked Songs, through Spotify's Web API)
    source  session | window (which of the two above answered)
The moment is fixed while the song plays on, so the row (and every page built from it) changes only on a new song, a
pause, a seek or a new like: the painter moves the bar and the time from its own clock (scene.py `live`).

The panel is the lens home-music (Home base f5204; its source and put script in home-music/ here). Its parts ask the
home base with host verbs (host_verbs.py): media.play, media.next, media.prev, media.shuffle, media.repeat,
media.like, media.unlike. hud.py writes witnessed:media in Hud.say_desktop, and stop() ends the session reader (Hud.closed
and --stop clear the row). Off switch: stop(), or the home base ending (the reader's stdin closes and it ends).
"""
import ctypes
import json
import os
import subprocess
import sys
import threading
import time
from ctypes import wintypes as wt
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ART = REPO / "media" / "now-playing"                                   # media_links.FOLDERS["media"]: the desk shows it
ART_KEEP = 40                                                          # the newest arts kept; older ones it made go

user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
WNDENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
WM_APPCOMMAND = 0x0319
APPCOMMAND = {"play": 14, "next": 11, "prev": 12}                      # MEDIA_PLAY_PAUSE, NEXTTRACK, PREVIOUSTRACK
VK = {"play": 0xB3, "next": 0xB0, "prev": 0xB1}                        # VK_MEDIA_PLAY_PAUSE, _NEXT_TRACK, _PREV_TRACK
IDLE = {"spotify", "spotify free", "spotify premium"}
PLAYERS = {"spotify": "Spotify", "msedge": "Edge", "chrome": "Chrome", "firefox": "Firefox", "zune": "Media Player",
           "microsoft.zunemusic": "Media Player", "vlc": "VLC", "applemusic": "Apple Music", "itunes": "iTunes"}

user32.EnumWindows.argtypes = [WNDENUMPROC, wt.LPARAM]
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


# -- the system media session, through smtc.ps1
class Session:
    """smtc.ps1 as a child: start() once, then state() is its last word (a dict, or None before it spoke or when it
    could not start), and send(line) presses (-> True/False, or None when it did not answer within `wait`)."""

    def __init__(self, art_dir=ART, dry=False):
        self.art_dir, self.dry = Path(art_dir), dry
        self.p, self.last, self.why, self.answers = None, None, "", []
        self.lock, self.cond = threading.Lock(), threading.Condition()

    def start(self):
        if self.p and self.p.poll() is None:
            return True
        env = {**os.environ, "AGORA_ART_DIR": str(self.art_dir), "AGORA_SMTC_PARENT": str(os.getpid()),
               "AGORA_SMTC_DRY": "1" if self.dry else "0"}
        try:
            self.p = subprocess.Popen(["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                                       "-File", str(HERE / "smtc.ps1")], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, env=env, text=True, encoding="utf-8", errors="replace",
                                      creationflags=0x08000000)                       # CREATE_NO_WINDOW
        except OSError as e:
            self.why = f"Windows PowerShell did not start: {e}"
            return False
        threading.Thread(target=self._read, daemon=True).start()
        return True

    def _read(self):
        p = self.p
        try:
            self._lines(p)
        except (OSError, ValueError):                            # the pipe closed under it: stop() was called
            pass
        try:
            err = (p.stderr.read() or "").strip().splitlines()
        except (OSError, ValueError):
            err = []
        with self.cond:
            self.last, self.why = None, "the session reader ended" + (f": {err[-1][:200]}" if err else "")
            self.cond.notify_all()

    def _lines(self, p):
        for line in p.stdout:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            with self.cond:
                if "did" in o:
                    self.answers.append(o)
                else:
                    self.last = o
                    self.why = "" if o.get("ok") else (o.get("why") or "the session did not read")
                self.cond.notify_all()

    def state(self, wait=0.0):
        """The last state; with wait, up to that many seconds for a first one."""
        end = time.time() + wait
        with self.cond:
            while self.last is None and self.p and self.p.poll() is None and time.time() < end:
                self.cond.wait(max(0.01, end - time.time()))
            return self.last

    def send(self, line, wait=5.0):
        if not (self.p and self.p.poll() is None):
            return None
        with self.cond:
            self.answers.clear()
            try:
                self.p.stdin.write(line + "\n")
                self.p.stdin.flush()
            except OSError:
                return None
            end = time.time() + wait
            while not self.answers and time.time() < end:
                self.cond.wait(max(0.01, end - time.time()))
            return bool(self.answers[0].get("ok")) if self.answers else None

    def stop(self):
        p, self.p = self.p, None
        if p and p.poll() is None:
            try:
                p.stdin.write("stop\n")
                p.stdin.close()
                p.wait(3)
            except (OSError, subprocess.TimeoutExpired):
                p.kill()


SESSION = Session()
LIKES = None            # spotify_like.Library(), set by likes(); None until the first row


def likes():
    global LIKES
    if LIKES is None:
        import spotify_like
        LIKES = spotify_like.Library()
    return LIKES


def stop():
    """The off switch: the session reader ends (the home base calls this as it closes)."""
    SESSION.stop()
    if LIKES is not None:
        LIKES.stop()


def player_of(app):
    a = (app or "").lower().split("!")[0]
    a = a.rsplit("\\", 1)[-1].removesuffix(".exe")
    for k, v in PLAYERS.items():
        if k in a:
            return v
    return a.split(".")[0].capitalize() or "Media"


def clock(s):
    s = max(0, int(round(s)))
    return f"{s // 3600}:{s // 60 % 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


_KEPT = {}               # the moment last written for a track, so the row stands still while it plays on


def progress(s, now=None):
    """-> the `live until` words for a session state, or "" when the app gives no length. The moment is the song's
    end: updated + (end - position). While it plays on, a new estimate within 2 s of the kept one keeps the old."""
    end, pos = float(s.get("end") or 0), float(s.get("position") or 0)
    if end <= 0:
        return ""
    key = (s.get("title"), s.get("artist"), s.get("album"))
    if s.get("status") != "Playing":
        _KEPT.pop("moment", None)
        return f"{max(0, round(end - pos))} of {round(end)}"
    at = float(s.get("updated") or (now or time.time())) + (end - pos)
    kept = _KEPT.get("moment")
    if kept and kept[0] == key and abs(kept[1] - at) < 2:
        at = kept[1]
    _KEPT["moment"] = (key, at)
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(at)) + f" of {round(end)}"


def _rel(path):
    """The art's path as the desk names it: relative to the checkout (media/now-playing/x.jpg), forward slashes."""
    if not path:
        return ""
    try:
        return Path(path).resolve().relative_to(REPO.resolve()).as_posix()
    except ValueError:
        return ""


def _prune(keep):
    try:
        arts = sorted((f for f in ART.glob("*") if f.suffix in (".jpg", ".png") and len(f.stem) == 16),
                      key=lambda f: f.stat().st_mtime, reverse=True)
    except OSError:
        return
    for f in arts[ART_KEEP:]:
        if not keep or f.resolve() != Path(keep).resolve():
            try:
                f.unlink()
            except OSError:
                pass


def session_row(s, liked=("unknown", "")):
    """A session state (smtc.ps1's "s") -> the witnessed:media row."""
    title, artist = (s.get("title") or "").strip(), (s.get("artist") or "").strip()
    end = float(s.get("end") or 0)
    can = s.get("can") or {}
    rep = {"None": "off", "Track": "track", "List": "list"}.get(s.get("repeat") or "", "")
    shuf = "" if s.get("shuffle") is None else ("on" if s.get("shuffle") else "off")
    return {"name": "media", "source": "session", "player": player_of(s.get("app")),
            "playing": "yes" if s.get("status") == "Playing" else "no", "title": title, "artist": artist,
            "album": (s.get("album") or "").strip(), "line": f"{title} · {artist}" if artist else title,
            "art": _rel(s.get("art")), "at": progress(s), "length": clock(end) if end > 0 else "",
            "shuffle": shuf, "repeat": rep, "can": " ".join(k for k in ("play", "pause", "next", "prev", "shuffle", "repeat") if can.get(k)),
            "liked": liked[0], "like_why": liked[1]}


# -- Spotify's window title (a5245), when there is no session
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


def window_rows():
    h, t = spotify()
    if not h:
        return []
    base = {"name": "media", "source": "window", "player": "Spotify", "album": "", "art": "", "at": "", "length": "",
            "shuffle": "", "repeat": "", "can": "play next prev", "liked": "unknown",
            "like_why": "Windows' media session did not answer, so the song is known only by Spotify's window title"}
    if t.strip().lower() in IDLE:
        return [{**base, "playing": "no", "title": "", "artist": "", "line": "Paused"}]
    artist, _, song = t.partition(" - ")
    if not song:
        artist, song = "", t
    return [{**base, "playing": "yes", "title": song, "artist": artist, "line": f"{song} · {artist}" if artist else song}]


def rows(session=None, library=None):
    """The witnessed:media row: from the session when it answers (starting its reader the first time), else from
    Spotify's window title. `session` and `library` are stand-ins for tests and stages."""
    ses = session or SESSION
    ses.start()
    st = ses.state(wait=4.0)
    s = (st or {}).get("s") if (st or {}).get("ok") else None
    if not s or not ((s.get("title") or "").strip()):
        return window_rows()
    lib = library if library is not None else likes()
    liked = lib.state_of(s.get("title") or "", s.get("artist") or "", player_of(s.get("app")))
    row = session_row(s, liked)
    if session is None and s.get("art"):
        _prune(s["art"])
    return [row]


# -- pressing
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


SESSION_WORDS = {"play": "toggle", "next": "next", "prev": "prev"}


def press(action, words="", session=None):
    """play (play or pause), next, prev, shuffle, repeat. -> what took it ("session", "spotify", "key"), or "".
    shuffle and repeat go only to the session: they flip what it says now (shuffle on <-> off; repeat off -> list ->
    track -> off, as Spotify's button goes)."""
    ses = session or SESSION
    st = ses.state() if ses.start() else None
    s = (st or {}).get("s") if st else None
    if action in ("shuffle", "repeat"):
        if not s:
            return ""
        if action == "shuffle":
            line = "shuffle " + ("off" if s.get("shuffle") else "on")
        else:
            line = "repeat " + {"None": "list", "List": "track", "Track": "none"}.get(s.get("repeat") or "None", "list")
        return "session" if ses.send(line) else ""
    if action not in APPCOMMAND:
        return ""
    if s and ses.send(SESSION_WORDS[action]):
        return "session"
    h, _ = spotify()
    if h and user32.PostMessageW(h, WM_APPCOMMAND, h, APPCOMMAND[action] << 16):
        return "spotify"
    return "key" if _key(VK[action]) else ""


def shape(row):
    """A row by shape only: each field's type and length, never its words (a look at the real PC that keeps what
    Alex is listening to off the record)."""
    return {k: (v if k in ("name", "source", "playing", "shuffle", "repeat", "can", "liked") else
                f"{type(v).__name__}[{len(v)}]" if isinstance(v, str) else type(v).__name__) for k, v in row.items()}


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "now"
    try:
        if what in ("now", "shape"):
            rs = rows()
            print([shape(r) for r in rs] if what == "shape" else rs)
            s = (SESSION.state() or {}).get("s") or {}
            print("art:", "a file" if s.get("art") else f"none ({s.get('artwhy') or SESSION.why or 'no session'})")
        else:
            print(press(what) or f"not done: {what} (now, shape, play, next, prev, shuffle or repeat)")
    finally:
        stop()
