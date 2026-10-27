r"""wallpaper: the theme's wallpaper as the real Windows wallpaper (Claude, 27 Oct 2026).

Alex, 27 Oct: "render the theme's wallpaper to an image, set it as my real Windows wallpaper, and drop the full-screen
wallpaper window. Keep an off switch that puts my old wallpaper back."

The desktop page (pages/shell/desktop.html, the same drawing the bars copy behind themselves) is rendered once in hidden
headless Edge at the monitor's real size and saved as a PNG; that file becomes the Windows wallpaper (Fill, 1:1). Nothing
of ours runs over the desktop afterwards: the desktop icons are back, and a click on the wallpaper is a click on Windows'
own desktop. A new theme is rendered again (the window module asks for the theme's hash every few seconds).

The off switch. Before the first change, the wallpaper as it was (its file, its style, and a copy of the picture, since a
Spotlight picture is a cache file Windows rotates away) is saved in state/wallpaper/before.json. restore() puts it back
and forgets the save. window.shell off does it, and so does this, with or without the desk running:

    .venv/Scripts/python.exe research/window-lab/kernel-desktop/wallpaper.py restore

Windows has no supported call that turns Windows Spotlight back on, so a Spotlight desktop comes back as the Spotlight
picture it showed; the command line restore then opens Settings > Background, where Spotlight is one pick. The command
line restore also leaves a mark (state/wallpaper/off) so the desk does not set the theme's wallpaper again on its next
start; `wallpaper.py on` takes the mark away.

Documented calls only: SystemParametersInfoW(SPI_SETDESKWALLPAPER) and the WallpaperStyle / TileWallpaper values under
HKCU\Control Panel\Desktop. AGORA_DESKTOP_LAYER=bottom (or workerw) brings the old wallpaper window back instead.
"""
import base64
import ctypes
import hashlib
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import winreg
from pathlib import Path
from urllib.parse import quote, urlsplit

HERE = Path(__file__).resolve().parent
STATE = HERE / "state" / "wallpaper"
BEFORE = STATE / "before.json"
OFF = STATE / "off"                   # made by `wallpaper.py restore`: the desk leaves the wallpaper alone until `on`
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
DESK_KEY = r"Control Panel\Desktop"
WALLPAPERS_KEY = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Wallpapers"
SPI_SETDESKWALLPAPER = 0x0014
SPIF_UPDATEINIFILE, SPIF_SENDCHANGE = 0x01, 0x02
SPOTLIGHT = 3                         # Explorer\Wallpapers BackgroundType: 0 picture, 1 colour, 2 slideshow, 3 Spotlight

user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.SystemParametersInfoW.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_wchar_p, ctypes.c_uint]
user32.SystemParametersInfoW.restype = ctypes.c_int


def enabled():
    """The theme's wallpaper as Windows' own is the default; AGORA_DESKTOP_LAYER=bottom|workerw keeps the old window."""
    return os.environ.get("AGORA_DESKTOP_LAYER", "system") == "system"


# ------------------------------------------------------------------------------------------------ Windows' wallpaper
def current():
    """-> what Windows shows now: {path, style, tile, background_type}."""
    out = {}
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, DESK_KEY) as k:
        for name, key in (("path", "WallPaper"), ("style", "WallpaperStyle"), ("tile", "TileWallpaper")):
            try:
                out[name] = str(winreg.QueryValueEx(k, key)[0])
            except OSError:
                out[name] = ""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, WALLPAPERS_KEY) as k:
            out["background_type"] = int(winreg.QueryValueEx(k, "BackgroundType")[0])
    except (OSError, ValueError):
        out["background_type"] = None
    return out


def ours(path):
    """A picture this file made (agora-*.png in state/wallpaper), not the saved copy of Alex's own."""
    try:
        p = Path(path)
        return p.parent.resolve() == STATE.resolve() and p.name.startswith("agora-")
    except (OSError, ValueError):
        return False


def _set(path, style="10", tile="0"):
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, DESK_KEY, 0, winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, "WallpaperStyle", 0, winreg.REG_SZ, str(style))
        winreg.SetValueEx(k, "TileWallpaper", 0, winreg.REG_SZ, str(tile))
    if not user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, str(path), SPIF_UPDATEINIFILE | SPIF_SENDCHANGE):
        raise OSError(ctypes.get_last_error(), "SystemParametersInfoW(SPI_SETDESKWALLPAPER) refused " + str(path))


def save_before():
    """Keep the wallpaper as it is now, once: a save that exists is never overwritten (so a second apply, a restart or
    a theme change cannot lose the original)."""
    if BEFORE.exists():
        return json.loads(BEFORE.read_text(encoding="utf-8"))
    now = current()
    if ours(now["path"]):
        return None                    # ours already and no save: there is nothing of Alex's to keep
    STATE.mkdir(parents=True, exist_ok=True)
    now["copy"] = ""
    src = Path(now["path"]) if now["path"] else None
    if src and src.is_file():
        dst = STATE / ("before" + (src.suffix.lower() or ".img"))
        shutil.copyfile(src, dst)
        now["copy"] = str(dst)
    now["saved"] = time.strftime("%Y-%m-%d %H:%M:%S")
    BEFORE.write_text(json.dumps(now, indent=1), encoding="utf-8")
    return now


def apply(png):
    """Make `png` the Windows wallpaper (saving the old one first). -> 'set' or 'already'."""
    save_before()
    if current()["path"].lower() == str(png).lower():
        return "already"
    _set(png)
    for old in STATE.glob("agora-*.png"):
        if old.resolve() != Path(png).resolve():
            try:
                old.unlink()
            except OSError:
                pass
    return "set"


def restore(open_settings=False):
    """Put the saved wallpaper back and forget the save. -> what happened, in words."""
    if not BEFORE.exists():
        return "nothing to put back: Agora has not changed the Windows wallpaper"
    b = json.loads(BEFORE.read_text(encoding="utf-8"))
    src = b.get("path") if b.get("path") and Path(b["path"]).is_file() else b.get("copy")
    if src and Path(src).is_file():
        _set(src, b.get("style") or "10", b.get("tile") or "0")
        said = "the old wallpaper is back"
    else:
        said = "the old wallpaper's picture is gone; nothing was changed"
    BEFORE.unlink()
    if b.get("background_type") == SPOTLIGHT:
        said += " (as the Spotlight picture it showed; Settings > Background turns Spotlight back on)"
        if open_settings:
            os.startfile("ms-settings:personalization-background")
    return said


# ------------------------------------------------------------------------------------------------ rendering
class CDP:
    """The few DevTools calls the render needs, over a plain websocket (as hidden_evidence.py)."""
    def __init__(self, url):
        p = urlsplit(url)
        self.s = socket.create_connection((p.hostname, p.port), timeout=30)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET {p.path} HTTP/1.1\r\nHost: {p.netloc}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        got = b""
        while not got.endswith(b"\r\n\r\n"):
            got += self.s.recv(1)
        if b"101" not in got.splitlines()[0]:
            raise OSError("DevTools refused the socket")
        self.seq = 0

    def _read(self, n):
        out = b""
        while len(out) < n:
            b = self.s.recv(n - len(out))
            if not b:
                raise EOFError("DevTools closed")
            out += b
        return out

    def _receive(self):
        first, second = self._read(2)
        size = second & 127
        if size == 126:
            size = struct.unpack("!H", self._read(2))[0]
        elif size == 127:
            size = struct.unpack("!Q", self._read(8))[0]
        mask = self._read(4) if second & 128 else None
        data = self._read(size)
        if mask:
            data = bytes(x ^ mask[i % 4] for i, x in enumerate(data))
        return json.loads(data)

    def call(self, method, **params):
        self.seq += 1
        data = json.dumps({"id": self.seq, "method": method, "params": params}).encode()
        mask, n = os.urandom(4), len(data)
        head = bytes((0x81, 0x80 | (n if n < 126 else 126 if n < 65536 else 127)))
        if n >= 126:
            head += struct.pack("!H" if n < 65536 else "!Q", n)
        self.s.sendall(head + mask + bytes(x ^ mask[i % 4] for i, x in enumerate(data)))
        while True:
            r = self._receive()
            if r.get("id") == self.seq:
                if "error" in r:
                    raise RuntimeError(r["error"])
                return r.get("result") or {}

    def js(self, expression):
        r = self.call("Runtime.evaluate", expression=expression, returnByValue=True, awaitPromise=True)
        return (r.get("result") or {}).get("value")


# The page is drawn when its theme is in, and a picture wallpaper has loaded (it is a CSS background, not an <img>).
DRAWN = """(() => {
  if (!window.__ready) return false;
  const w = document.querySelector('.wall');
  if (!w) return false;
  const bg = getComputedStyle(w).backgroundImage || '';
  if (!/url\\(/.test(bg)) return true;
  return performance.getEntriesByType('resource').some(e => /theme-wallpaper/.test(e.name) && e.responseEnd > 0);
})()"""


def render(port, token, out, size, scale):
    """Draw the desktop page at `size` real pixels (`scale` real pixels per CSS pixel) into the PNG `out`. Hidden:
    headless Edge with its own throwaway profile, no window."""
    w, h = size
    cw, ch = round(w / scale), round(h / scale)
    STATE.mkdir(parents=True, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="edge-", dir=STATE)
    proc = subprocess.Popen([EDGE, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
                             "--remote-debugging-port=0", "--remote-allow-origins=*", "--disable-background-networking",
                             "--hide-scrollbars", "--mute-audio", "--user-data-dir=" + tmp, "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=0x08000000)
    cdp = None
    try:
        active = Path(tmp) / "DevToolsActivePort"
        end = time.monotonic() + 30
        dport = None
        while dport is None and time.monotonic() < end:
            try:                       # Edge may still hold the file it is writing (a PermissionError, seen live 27 Oct)
                dport = active.read_text().splitlines()[0]
            except (OSError, IndexError):
                time.sleep(0.1)
        if dport is None:
            raise TimeoutError("headless Edge did not start in 30 s")
        pages = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{dport}/json/list", timeout=10).read())
        cdp = CDP(next(p["webSocketDebuggerUrl"] for p in pages if p["type"] == "page"))
        cdp.call("Page.enable")
        cdp.call("Emulation.setDeviceMetricsOverride", width=cw, height=ch, deviceScaleFactor=scale, mobile=False,
                 screenWidth=cw, screenHeight=ch)
        page = "/desk/shell/desktop.html?hide=1&sx=0&sy=0&sw=%d&sh=%d" % (cw, ch)
        cdp.call("Page.navigate", url=f"http://127.0.0.1:{port}/dev/signin?token={quote(token)}&next={quote(page)}")
        end = time.monotonic() + 30
        while not cdp.js(DRAWN):
            if time.monotonic() > end:
                raise TimeoutError("the desktop page did not draw in 30 s")
            time.sleep(0.2)
        time.sleep(0.5)                               # one more frame for the dim layer and a decoded picture
        shot = cdp.call("Page.captureScreenshot", format="png", fromSurface=True)
        data = base64.b64decode(shot["data"])
        tmp_out = Path(str(out) + ".part")
        tmp_out.write_bytes(data)
        os.replace(tmp_out, out)
        return out
    finally:
        try:
            if cdp:
                cdp.call("Browser.close")
        except Exception:
            pass
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.terminate()
        for _ in range(10):
            try:
                shutil.rmtree(tmp)
                break
            except OSError:
                time.sleep(0.5)


def theme_hash(port, token):
    """-> the hash of the theme the desktop's owner wears now (the door's theme.json)."""
    req = urllib.request.Request(f"http://127.0.0.1:{port}/desk/theme.json", headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())["hash"]


class Keeper:
    """While the shell's desktop layer is on, keeps the Windows wallpaper like the theme; when it goes, puts the old
    wallpaper back. The window module calls want() from each reconcile; the work runs on this thread."""
    def __init__(self, port, token, size, scale, log):
        self.port, self.token, self.size, self.scale, self.log = port, token, tuple(size), scale, log
        self.on = None                 # None until the first reconcile says
        self.shown = None              # the theme hash on the wallpaper now
        self.said = ""
        self.wake = threading.Event()
        threading.Thread(target=self.run, daemon=True, name="wallpaper").start()

    def want(self, on):
        if on != self.on:
            self.on = on
            self.wake.set()

    def status(self):
        return self.said

    def step(self):
        if self.on is None:
            return
        if OFF.exists():                              # wallpaper.py restore was run: stay off until wallpaper.py on
            self.said = "off (wallpaper.py restore); wallpaper.py on brings the theme's wallpaper back"
            return
        if not self.on:
            if BEFORE.exists():
                self.said = restore(open_settings=False)
                self.log("wallpaper: " + self.said)
            self.shown = None
            return
        h = theme_hash(self.port, self.token)
        if h == self.shown:
            return
        w, ht = self.size
        png = STATE / f"agora-{h}-{w}x{ht}.png"
        if not png.exists():
            t = time.monotonic()
            render(self.port, self.token, png, self.size, self.scale)
            self.log(f"wallpaper: drew theme {h} at {w}x{ht} in {time.monotonic() - t:.1f} s")
        got = apply(png)
        self.shown = h
        self.said = f"the theme's wallpaper is the Windows wallpaper ({got})"
        self.log("wallpaper: " + self.said)

    def run(self):
        while True:
            self.wake.wait(5)
            self.wake.clear()
            try:
                self.step()
            except Exception as exc:
                import traceback
                self.said = f"wallpaper: {exc!r}"
                self.log(self.said + "\n" + traceback.format_exc(limit=4))
                self.wake.wait(30)                    # a failing render is not retried every few seconds


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "status"
    if what == "restore":
        STATE.mkdir(parents=True, exist_ok=True)
        OFF.write_text("wallpaper.py restore " + time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")
        print(restore(open_settings=True))
        print("the desk leaves the wallpaper alone until: wallpaper.py on")
    elif what == "on":
        OFF.unlink(missing_ok=True)
        print("on: the desk sets the theme's wallpaper again within a few seconds (while the shell is on)")
    elif what == "status":
        now = current()
        print(f"Windows wallpaper: {now['path'] or '(none)'} (style {now['style']}, background type {now['background_type']})")
        print("Agora's picture" if ours(now["path"]) else "not Agora's picture")
        print("saved to put back: " + (json.loads(BEFORE.read_text(encoding='utf-8'))["path"] if BEFORE.exists() else "nothing"))
    else:
        print("wallpaper.py status | restore | on")
