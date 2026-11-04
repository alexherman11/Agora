"""EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
(people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.

Conservative desktop gate: game processes and full-screen foreground windows.
Read-only Win32 inspection; no titles, focus changes or input.
"""
import ctypes
import json
import os
from ctypes import wintypes as w
from pathlib import Path

# Which programs are Alex's games, and which programs of his never count as one, are the world's: a `game-settings`
# thing (games=<exe,...> not_games=<exe,...>), which the window host mirrors to games.json on this machine so every
# reader of this file has it, with or without the door (4 Nov; before, a new game was an edit here). What stays here is
# a fact about Windows, not a choice: Game Bar's helpers have "game" in their names and are not games, and Windows'
# own shell windows can fill the screen with no game running (26 Oct: TextInputHost.exe at 3840x2160).
HELPERS = {'edgegameassist.exe','gamebarpresencewriter.exe','gameinputredistservice.exe','gameinputsvc.exe',
           'gameoverlayui.exe','gameoverlayui64.exe','gamebar.exe','gamebarftserver.exe'}
WINDOWS_OVERLAYS = {'textinputhost.exe','explorer.exe','shellexperiencehost.exe','startmenuexperiencehost.exe',
                    'searchhost.exe','lockapp.exe'}


def mirror_path():
    """Where the world's game lists are mirrored: one file per machine, read by any checkout (AGORA_GAMES_FILE for tests)."""
    if os.environ.get('AGORA_GAMES_FILE'):
        return Path(os.environ['AGORA_GAMES_FILE'])
    return Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'Agora' / 'games.json'


def write_mirror(games, not_games, source, path=None):
    """The window host's half: the lists as the world says them now, written whole (a reader never sees half)."""
    p = Path(path or mirror_path())
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + '.part')
    tmp.write_text(json.dumps({'games': sorted(games), 'not_games': sorted(not_games), 'from': source}, indent=1),
                   encoding='utf-8')
    os.replace(tmp, p)


_seen = {'mtime': None, 'games': frozenset(), 'not_games': frozenset()}


def world_lists():
    """-> (games, not_games) as the world last said them; both empty if it never has (then only the name test below)."""
    p = mirror_path()
    try:
        mtime = p.stat().st_mtime
        if mtime != _seen['mtime']:
            d = json.loads(p.read_text(encoding='utf-8'))
            _seen.update(mtime=mtime, games=frozenset(str(x).lower() for x in d.get('games') or ()),
                         not_games=frozenset(str(x).lower() for x in d.get('not_games') or ()))
    except (OSError, ValueError, TypeError, AttributeError):
        _seen.update(mtime=None, games=frozenset(), not_games=frozenset())
    return _seen['games'], _seen['not_games']


def is_game(exe, lists=None):
    """A game: one the world names, or any program with "game" in its name that is not a helper or a not_game.
    Named in both lists, it is a game (the careful answer)."""
    n = (exe or '').lower()
    games, not_games = lists or world_lists()
    return n in games or ('game' in n and n not in HELPERS and n not in not_games)


def never_game(exe):
    """Never a game, even filling the screen: Windows' own shell windows and helpers, and the world's not_games."""
    n = (exe or '').lower()
    return n in WINDOWS_OVERLAYS or n in HELPERS or n in world_lists()[1]


# What counts as the desktop, not a full-screen program: Explorer's own windows, and Agora's desktop layer (a
# screen-sized window under every app that draws the theme's wallpaper; shell_native.make_layer marks it with this
# window property). Clicking the wallpaper puts it in front, and before 27 Oct that read as a game and hid the bars.
DESKTOP_CLASSES = ('Progman', 'WorkerW', 'Shell_TrayWnd', 'Shell_SecondaryTrayWnd')
DESKTOP_PROP = 'Agora.Desktop'
_u = ctypes.WinDLL('user32', use_last_error=True)
_u.GetPropW.restype = w.HANDLE
_u.GetPropW.argtypes = [w.HWND, w.LPCWSTR]
_u.GetClassNameW.argtypes = [w.HWND, w.LPWSTR, ctypes.c_int]


def is_desktop(hwnd):
    """Is this window the desktop itself (Explorer's, or Agora's wallpaper layer)?"""
    if not hwnd:
        return False
    if _u.GetPropW(hwnd, DESKTOP_PROP):
        return True
    cls = ctypes.create_unicode_buffer(128)
    _u.GetClassNameW(hwnd, cls, 128)
    return cls.value in DESKTOP_CLASSES


class Process(ctypes.Structure):
    _fields_ = [('size',w.DWORD),('usage',w.DWORD),('pid',w.DWORD),('heap',ctypes.c_size_t),
                ('module',w.DWORD),('threads',w.DWORD),('parent',w.DWORD),('priority',w.LONG),
                ('flags',w.DWORD),('exe',w.WCHAR*260)]


def reasons():
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.CreateToolhelp32Snapshot.restype=w.HANDLE
    k.CloseHandle.argtypes=[w.HANDLE]
    k.Process32FirstW.argtypes=[w.HANDLE,ctypes.POINTER(Process)]
    k.Process32NextW.argtypes=k.Process32FirstW.argtypes
    h=k.CreateToolhelp32Snapshot(2,0)
    p=Process();p.size=ctypes.sizeof(p);out=[]
    if h == ctypes.c_void_p(-1).value:
        return ['process inspection failed']
    lists=world_lists()
    try:
        more=k.Process32FirstW(h,ctypes.byref(p))
        while more:
            if is_game(p.exe,lists):
                out.append(p.exe)
            more=k.Process32NextW(h,ctypes.byref(p))
    finally:k.CloseHandle(h)
    u=ctypes.WinDLL('user32',use_last_error=True);u.GetForegroundWindow.restype=w.HWND
    u.GetWindowRect.argtypes=[w.HWND,ctypes.POINTER(w.RECT)]
    u.GetClassNameW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int]
    fg=u.GetForegroundWindow();r=w.RECT()
    if fg and not is_desktop(fg):
        u.GetWindowRect(fg,ctypes.byref(r))
        if r.left<=0 and r.top<=0 and r.right>=u.GetSystemMetrics(0) and r.bottom>=u.GetSystemMetrics(1):
            out.append('full-screen foreground application')
    return out


def assert_clear():
    found=reasons()
    if found:
        raise RuntimeError('Gaming gate: '+', '.join(found))


if __name__=='__main__':
    found=reasons()
    print('Gaming gate: '+(', '.join(found) if found else 'clear'))
