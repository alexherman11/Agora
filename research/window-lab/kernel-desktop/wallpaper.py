r"""EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
(people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.

wallpaper: the Windows wallpaper, saved, set and put back. Only the seam; what the wallpaper shows is the world's.

The window module (kd_window.follow_wallpaper) calls apply() with the picture `Shell settings` names (wallpaper=<file>)
and restore() when the setting is emptied. What fills the setting is a rule in the world, e.g. the theme's wallpaper:

    rule on=theme.changed do="window.picture shell-desktop size=screen name=\"Agora wallpaper\" ; set <Shell settings> wallpaper=$new"

and a photo of Alex's own is `set <Shell settings> wallpaper=<file>`. (27 Oct this file also drew the theme and asked for
its hash every 5 s; 4 Nov that became window.picture plus the rule above. research/source-edits/SOURCE-EDITS-AUDIT.md.)

The off switch. Before the first change, the wallpaper as it was (its file, its style, and a copy of the picture, since a
Spotlight picture is a cache file Windows rotates away) is saved in state/wallpaper/before.json. restore() puts it back
and forgets the save. Emptying the setting does it (and undo brings Agora's back); so does this, with or without the desk:

    .venv/Scripts/python.exe research/window-lab/kernel-desktop/wallpaper.py restore

Windows has no supported call that turns Windows Spotlight back on, so a Spotlight desktop comes back as the Spotlight
picture it showed; the command line restore then opens Settings > Background, where Spotlight is one pick. It also
leaves a mark (state/wallpaper/off) so the desk leaves the wallpaper alone until `wallpaper.py on`.

Documented calls only: SystemParametersInfoW(SPI_SETDESKWALLPAPER) and the WallpaperStyle / TileWallpaper values under
HKCU\Control Panel\Desktop. AGORA_DESKTOP_LAYER=bottom (or workerw) brings the old wallpaper window back instead.
"""
import ctypes
import json
import os
import shutil
import sys
import time
import winreg
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE = HERE / "state" / "wallpaper"
BEFORE = STATE / "before.json"
OFF = STATE / "off"                   # made by `wallpaper.py restore`: the desk leaves the wallpaper alone until `on`
DESK_KEY = r"Control Panel\Desktop"
WALLPAPERS_KEY = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Wallpapers"
SPI_SETDESKWALLPAPER = 0x0014
SPIF_UPDATEINIFILE, SPIF_SENDCHANGE = 0x01, 0x02
SPOTLIGHT = 3                         # Explorer\Wallpapers BackgroundType: 0 picture, 1 colour, 2 slideshow, 3 Spotlight

user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.SystemParametersInfoW.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_wchar_p, ctypes.c_uint]
user32.SystemParametersInfoW.restype = ctypes.c_int


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
    """Make the picture `png` the Windows wallpaper (saving the old one first). -> 'set' or 'already'."""
    save_before()
    if current()["path"].lower() == str(png).lower():
        return "already"
    _set(png)
    for old in STATE.glob("agora-*.*"):
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


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "status"
    if what == "restore":
        STATE.mkdir(parents=True, exist_ok=True)
        OFF.write_text("wallpaper.py restore " + time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")
        print(restore(open_settings=True))
        print("the desk leaves the wallpaper alone until: wallpaper.py on")
    elif what == "on":
        OFF.unlink(missing_ok=True)
        print("on: within a few seconds the desk sets the wallpaper Shell settings names again")
    elif what == "status":
        now = current()
        print(f"Windows wallpaper: {now['path'] or '(none)'} (style {now['style']}, background type {now['background_type']})")
        print("Agora's picture" if ours(now["path"]) else "not Agora's picture")
        print("saved to put back: " + (json.loads(BEFORE.read_text(encoding='utf-8'))["path"] if BEFORE.exists() else "nothing"))
    else:
        print("wallpaper.py status | restore | on")
