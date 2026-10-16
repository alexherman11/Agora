"""winkey.py: a bare tap of the Windows key shows or hides the home base (a5980). 16 Oct 2026.

    python winkey.py            what the guard sees now (full screen in front? remote? elevated?); presses nothing

Alex, 16 Oct: 'let's bind the windows key to pull up this interface.' A bare tap is the Win key pressed and released
with no other key (and no mouse button) down in between, inside HOLD seconds. Every Win chord (Win+D, Win+E, Win+L,
Win+arrows, Win+number, Win+V, Win+Shift+S ...) reaches Windows exactly as before: the hook never holds back a Win
key down, nor any other key, and only acts on the Win-up that ends a bare tap.

How (hud.py runs it; nothing here runs on import):
  - Tap is the decision, pure logic: feed it key events, it answers PASS or TAP. test_winkey.py drives it with scripted
    events; nothing is sent to the machine.
  - Hook is a low-level keyboard hook (WH_KEYBOARD_LL) on a thread of its own that does nothing else, as Microsoft's
    page for the hook asks (a slow hook makes every key on the machine wait, and Windows silently drops a hook that
    is slow too often). On a TAP it hands the toggle to another thread and returns at once.
  - The Start menu opens when Windows sees Win down then Win up with nothing between. On a bare tap the hook holds
    back the real Win-up and sends three keys in its place: a key that means nothing (vk 0xFF, 'no mapping'), its
    release, then the Win-up. Windows sees a chord, so Start stays shut, and the Win key is released (never left
    down). The order matters: keys sent from inside the hook arrive after the event being hooked, so a mask sent
    while letting the real Win-up through would come too late. When Windows refuses the three keys, the real Win-up
    goes on untouched (Start opens; the home base does not toggle). AutoHotkey calls this its menu mask key.
  - A mouse click or wheel during the press makes it a chord too: a low-level mouse hook goes in when a Win press
    begins and comes out when it ends, so outside a Win press no code of ours is in the mouse's path.
  - It keeps no keys: only whether a Win press is going on, whether anything else happened in it, and which keys are
    down now. It writes, logs and sends no key anywhere (Sable's point on a5980: it is shaped like a keylogger).
  - Windows drops a hook that answers too slowly, without a word to it; hud.py puts it in again every minute
    (Hook.reseat) and says when a callback was slow.
  - RegisterHotKey cannot do this: it binds a key plus modifiers (MOD_WIN is a modifier, not a key), and Microsoft
    reserves Win shortcuts for the system. A bare Win needs the hook.

When it never acts (the Win key does what Windows does): winkey=off on the home-base lens note, or hud.py --winkey off;
a full-screen program in front (a game: the hook is then taken off entirely, so no Python runs in the game's input
path); this session is a remote one, or a remote desktop or virtual machine window is in front (the key is theirs);
the program in front runs elevated (our keys could not reach it, so the hook steps aside). The hook dies with its
process: Windows removes a low-level hook when the thread that set it ends, so --stop, a crash or taskkill leave the
keyboard as it was.

What it costs: Start no longer opens from the Win key. It opens from Ctrl+Esc (Windows' own; not caught here), from
the taskbar button whenever the home base is put away, and from the home base's host verb `start` (a dock icon can ask
for it).
"""
import ctypes
import threading
import time
from ctypes import wintypes as wt

VK_LWIN, VK_RWIN = 0x5B, 0x5C
WIN = (VK_LWIN, VK_RWIN)
MASK_VK = 0xFF                     # 'no mapping': a key that does nothing in any program
MARK = 0x41475241                  # dwExtraInfo on the keys we send ('AGRA'), so the hook lets its own keys by
HOLD = 0.8                         # seconds: a Win held longer than this is not a tap
GAP = 1.5                          # seconds: a Win down this long after the last Win event, while we think one is
                                   # down, is a new press (we missed its up: Win+L, the secure desktop)
PASS, TAP = "pass", "tap"


class Tap:
    """The tap/chord decision. feed(vk, down, t[, held]) -> PASS or TAP; TAP only on the Win-up that ends a bare tap.
    held, when given, is the set of keys and mouse buttons down right now by Windows' own count (the live hook gives
    it at each Win down and up, so a key whose release we never saw cannot spoil a tap, and a key held from before,
    Alt in an Alt+Tab switcher, Ctrl, a mouse button, makes it a chord). Without it the machine counts from events."""

    def __init__(self, hold=HOLD, gap=GAP):
        self.hold, self.gap = hold, gap
        self.win = set()           # the Win keys down now
        self.since = None          # when the press began
        self.last = None           # the last Win event in this press (repeats keep it fresh)
        self.chord = False         # something else happened during the press
        self.held = set()          # other keys down, by events

    def _others(self, held):
        return {k for k in (self.held if held is None else held) if k not in WIN}

    def feed(self, vk, down, t, held=None):
        if vk in WIN:
            if down:
                if self.since is not None and t - self.last <= self.gap:
                    if vk not in self.win:
                        self.chord = True              # the other Win key too: not a bare tap
                    self.win.add(vk)
                    self.last = t                      # key repeat while Win is held
                    return PASS
                if held is not None:
                    self.held = self._others(held)
                self.win, self.since, self.last = {vk}, t, t
                self.chord = bool(self._others(held))
                return PASS
            if vk not in self.win:
                return PASS                            # an up whose down we never saw
            self.win.discard(vk)
            self.last = t
            if self.win:
                return PASS
            bare = not self.chord and t - self.since <= self.hold and not self._others(held)
            self.since, self.chord = None, False
            return TAP if bare else PASS
        if down:
            self.held.add(vk)
        else:
            self.held.discard(vk)
        if self.since is not None:
            self.chord = True                          # any other key, down or up, while Win is down
        return PASS

    def mouse(self, t):
        """A mouse button or wheel moved: during a press, that is a chord (Win+click is not a tap)."""
        if self.since is not None and t - self.last <= self.gap:
            self.chord = True

    @property
    def pressing(self):
        return self.since is not None


# -- the machine
user32, kernel32, advapi32 = ctypes.windll.user32, ctypes.windll.kernel32, ctypes.windll.advapi32
WH_KEYBOARD_LL, WH_MOUSE_LL, HC_ACTION = 13, 14, 0
WM_KEYDOWN, WM_KEYUP, WM_SYSKEYDOWN, WM_SYSKEYUP, WM_QUIT = 0x100, 0x101, 0x104, 0x105, 0x12
WM_MOUSEMOVE, WM_APP = 0x200, 0x8000
MOUSE_IN, MOUSE_OUT, RESEAT = WM_APP + 10, WM_APP + 11, WM_APP + 12      # messages to the hook's own thread
SLOW = 0.1                         # seconds: a callback slower than this is said (Windows drops a hook at ~1 s)
KEYEVENTF_EXTENDEDKEY, KEYEVENTF_KEYUP = 0x1, 0x2
INPUT_KEYBOARD = 1
LRESULT = ctypes.c_ssize_t
HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wt.WPARAM, wt.LPARAM)


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", wt.DWORD), ("scanCode", wt.DWORD), ("flags", wt.DWORD), ("time", wt.DWORD),
                ("dwExtraInfo", ctypes.c_size_t)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD), ("time", wt.DWORD),
                ("dwExtraInfo", ctypes.c_size_t)]


class _MOUSEINPUT(ctypes.Structure):                 # only so the union has the size Windows expects
    _fields_ = [("dx", wt.LONG), ("dy", wt.LONG), ("mouseData", wt.DWORD), ("dwFlags", wt.DWORD), ("time", wt.DWORD),
                ("dwExtraInfo", ctypes.c_size_t)]


class _U(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", _MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wt.DWORD), ("u", _U)]


def _sig(fn, res, *args):
    fn.restype, fn.argtypes = res, list(args)


_sig(user32.SetWindowsHookExW, wt.HHOOK, ctypes.c_int, HOOKPROC, wt.HINSTANCE, wt.DWORD)
_sig(user32.UnhookWindowsHookEx, wt.BOOL, wt.HHOOK)
_sig(user32.CallNextHookEx, LRESULT, wt.HHOOK, ctypes.c_int, wt.WPARAM, wt.LPARAM)
_sig(user32.SendInput, wt.UINT, wt.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
_sig(user32.GetAsyncKeyState, ctypes.c_short, ctypes.c_int)
_sig(user32.GetMessageW, ctypes.c_int, ctypes.POINTER(wt.MSG), wt.HWND, wt.UINT, wt.UINT)
_sig(user32.PostThreadMessageW, wt.BOOL, wt.DWORD, wt.UINT, wt.WPARAM, wt.LPARAM)
_sig(user32.GetForegroundWindow, wt.HWND)
_sig(user32.GetWindowThreadProcessId, wt.DWORD, wt.HWND, ctypes.POINTER(wt.DWORD))
_sig(user32.GetClassNameW, ctypes.c_int, wt.HWND, wt.LPWSTR, ctypes.c_int)
_sig(user32.GetWindowRect, wt.BOOL, wt.HWND, ctypes.POINTER(wt.RECT))
_sig(user32.MonitorFromWindow, wt.HMONITOR, wt.HWND, wt.DWORD)
_sig(user32.GetMonitorInfoW, wt.BOOL, wt.HMONITOR, ctypes.c_void_p)
_sig(user32.GetSystemMetrics, ctypes.c_int, ctypes.c_int)
_sig(kernel32.GetModuleHandleW, wt.HMODULE, wt.LPCWSTR)
_sig(kernel32.GetCurrentThreadId, wt.DWORD)
_sig(kernel32.OpenProcess, wt.HANDLE, wt.DWORD, wt.BOOL, wt.DWORD)
_sig(kernel32.CloseHandle, wt.BOOL, wt.HANDLE)
_sig(kernel32.QueryFullProcessImageNameW, wt.BOOL, wt.HANDLE, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD))
_sig(advapi32.OpenProcessToken, wt.BOOL, wt.HANDLE, wt.DWORD, ctypes.POINTER(wt.HANDLE))
_sig(advapi32.GetTokenInformation, wt.BOOL, wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD, ctypes.POINTER(wt.DWORD))


def held_now():
    """The keys and mouse buttons Windows counts as down now. Inside the hook this is true of every key but the one
    being hooked (Windows updates that one after the hook returns), which is the Win key we are judging."""
    return {vk for vk in range(1, 255) if user32.GetAsyncKeyState(vk) & 0x8000}


def send_mask(win_vk, scan):
    """Mask, unmask, then the Win-up held back: -> how many of the three Windows took."""
    ks = [(MASK_VK, 0, 0), (MASK_VK, 0, KEYEVENTF_KEYUP), (win_vk, scan, KEYEVENTF_KEYUP | KEYEVENTF_EXTENDEDKEY)]
    arr = (INPUT * 3)()
    for i, (vk, sc, fl) in enumerate(ks):
        arr[i].type = INPUT_KEYBOARD
        arr[i].u.ki = KEYBDINPUT(vk, sc, fl, 0, MARK)
    return user32.SendInput(3, arr, ctypes.sizeof(INPUT))


# -- the guard: may the hook act now?
REMOTE_PROGRAMS = {"mstsc", "msrdc", "vmconnect", "virtualboxvm", "vmware-vmx", "vmware", "vmplayer", "windowssandbox",
                   "windowssandboxclient", "parsecd", "moonlight", "anydesk", "teamviewer", "rustdesk"}
SM_REMOTESESSION = 0x1000


class _MI(ctypes.Structure):
    _fields_ = [("cbSize", wt.DWORD), ("rcMonitor", wt.RECT), ("rcWork", wt.RECT), ("dwFlags", wt.DWORD)]


def _pid(h):
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
    return pid.value


def _program(pid):
    hp = kernel32.OpenProcess(0x1000, False, pid)            # PROCESS_QUERY_LIMITED_INFORMATION
    if not hp:
        return ""
    try:
        buf, size = ctypes.create_unicode_buffer(520), wt.DWORD(520)
        ok = kernel32.QueryFullProcessImageNameW(hp, 0, buf, ctypes.byref(size))
        return buf.value.replace("\\", "/").rsplit("/", 1)[-1].rsplit(".", 1)[0].lower() if ok else ""
    finally:
        kernel32.CloseHandle(hp)


def elevated(pid):
    """True when that process runs elevated, or when we cannot tell (its token is closed to us): either way, keys we
    send may not reach it, so the hook steps aside."""
    hp = kernel32.OpenProcess(0x1000, False, pid)
    if not hp:
        return True
    try:
        tok = wt.HANDLE()
        if not advapi32.OpenProcessToken(hp, 0x8, ctypes.byref(tok)):     # TOKEN_QUERY
            return True
        try:
            v, n = wt.DWORD(), wt.DWORD()
            if not advapi32.GetTokenInformation(tok, 20, ctypes.byref(v), 4, ctypes.byref(n)):   # TokenElevation
                return True
            return bool(v.value)
        finally:
            kernel32.CloseHandle(tok)
    finally:
        kernel32.CloseHandle(hp)


def fullscreen_in_front(own_pid=None):
    """Is a full-screen program in front (a game, a film)? The desktop and taskbar are not; nor is the home base
    itself (own_pid), which covers the whole monitor when shown. As capture.py's, with the window's rectangle."""
    fg = user32.GetForegroundWindow()
    if not fg:
        return False
    cls = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(fg, cls, 256)
    if cls.value in ("Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd") or (own_pid and _pid(fg) == own_pid):
        return False
    r = wt.RECT()
    user32.GetWindowRect(fg, ctypes.byref(r))
    mi = _MI()
    mi.cbSize = ctypes.sizeof(mi)
    user32.GetMonitorInfoW(user32.MonitorFromWindow(fg, 2), ctypes.byref(mi))
    m = mi.rcMonitor
    return r.left <= m.left and r.top <= m.top and r.right >= m.right and r.bottom >= m.bottom


def why_not(own_pid=None):
    """'' when a bare tap may act now, else the reason it may not (a few microseconds; the hook asks at each tap)."""
    if user32.GetSystemMetrics(SM_REMOTESESSION):
        return "this is a remote session"
    if fullscreen_in_front(own_pid):
        return "a full-screen program is in front"
    fg = user32.GetForegroundWindow()
    if fg:
        pid = _pid(fg)
        if pid != own_pid:
            if _program(pid) in REMOTE_PROGRAMS:
                return "a remote desktop or virtual machine is in front"
            if elevated(pid):
                return "the program in front runs elevated (or its token is closed to us)"
    return ""


class Hook:
    """The low-level keyboard hook on a thread of its own. on_tap() is called on another thread (it must not be
    slow either way: hud.py posts a message). may() -> '' or why not, asked at each tap. send() sends the mask and
    the Win-up; tests give their own so nothing reaches the machine, and their own nxt for CallNextHookEx.

    It is shaped like a keylogger, so, plainly: it keeps no key but in Tap (which Win keys are down, whether anything
    else happened during this press, and the codes of keys down right now, forgotten as they go up), and it never
    writes, logs or sends a key anywhere. Its log lines say only why a tap passed, or that the hook was slow.

    While a Win press is in progress (and only then), a low-level mouse hook is in too, so a click or wheel during
    the press makes it a chord; outside a press no code of ours sits in the mouse's path. reseat() puts the keyboard
    hook in again (new first, then the old out): Windows drops a hook that was too slow without a word, so hud.py
    reseats it every minute while no press is in progress. slow counts callbacks slower than SLOW."""

    def __init__(self, on_tap, may=lambda: "", send=send_mask, held=held_now, log=print, nxt=None):
        self.on_tap, self.may, self.send, self.held, self.log = on_tap, may, send, held, log
        self.nxt = nxt or user32.CallNextHookEx
        self.tap = Tap()
        self.hhook = None
        self.mhook = None
        self.tid = None
        self.thread = None
        self._proc = HOOKPROC(self._call)            # kept, or the callback is collected under Windows' feet
        self._mproc = HOOKPROC(self._mcall)
        self._ready = threading.Event()
        self.taps = 0
        self.slow, self.slowest = 0, 0.0
        self.dropped = 0                             # reseats that found the old hook already gone

    def _post(self, m):
        if self.tid:
            user32.PostThreadMessageW(self.tid, m, 0, 0)

    def _took(self, t0):
        d = time.perf_counter() - t0
        self.slowest = max(self.slowest, d)
        if d > SLOW:
            self.slow += 1

    # the callback: every key on the machine passes here while the hook is in, so it does as little as it can
    def _call(self, code, wparam, lparam):
        t0 = time.perf_counter()
        try:
            if code == HC_ACTION:
                k = KBDLLHOOKSTRUCT.from_address(lparam)
                if k.dwExtraInfo != MARK:
                    down = wparam in (WM_KEYDOWN, WM_SYSKEYDOWN)
                    is_win = k.vkCode in WIN
                    was = self.tap.pressing
                    got = self.tap.feed(k.vkCode, down, time.monotonic(), self.held() if is_win else None)
                    if self.tap.pressing != was:
                        self._post(MOUSE_IN if self.tap.pressing else MOUSE_OUT)
                    if got == TAP and self.decide(k):
                        self._took(t0)
                        return 1
        except Exception as e:                       # never let a fault keep a key from Windows
            self.log(f"winkey: hook fault {type(e).__name__}: {e}")
        self._took(t0)
        return self.nxt(None, code, wparam, lparam)

    def _mcall(self, code, wparam, lparam):
        try:
            if code == HC_ACTION:
                t = time.monotonic()
                if wparam != WM_MOUSEMOVE:
                    self.tap.mouse(t)
                if not self.tap.pressing or t - self.tap.last > self.tap.gap:
                    self._post(MOUSE_OUT)            # the press ended unseen (Win+L): the mouse hook goes
        except Exception:
            pass
        return self.nxt(None, code, wparam, lparam)

    def decide(self, k):
        """A bare tap ended: True when its Win-up is held back (the mask sent in its place, the toggle handed on)."""
        why = self.may()
        if why:
            self.log(f"winkey: a bare tap passed to Windows: {why}")
            return False
        if self.send(k.vkCode, k.scanCode) != 3:
            self.log("winkey: Windows refused the mask keys; the tap passed to Windows")
            return False
        self.taps += 1
        threading.Thread(target=self.on_tap, daemon=True).start()
        return True

    # install and remove
    def _run(self):
        self.tid = kernel32.GetCurrentThreadId()
        mod = kernel32.GetModuleHandleW(None)
        self.hhook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._proc, mod, 0)
        self._ready.set()
        if not self.hhook:
            self.log(f"winkey: the hook did not go in (error {ctypes.GetLastError()}); Ctrl+Alt+J still works")
            return
        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            m = msg.message
            if m == MOUSE_IN and not self.mhook:
                self.mhook = user32.SetWindowsHookExW(WH_MOUSE_LL, self._mproc, mod, 0)
            elif m == MOUSE_OUT and self.mhook:
                user32.UnhookWindowsHookEx(self.mhook)
                self.mhook = None
            elif m == RESEAT and not self.tap.pressing:
                new = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._proc, mod, 0)
                if new:
                    if not user32.UnhookWindowsHookEx(self.hhook):
                        self.dropped += 1            # Windows had already taken it out
                    self.hhook = new
        if self.mhook:
            user32.UnhookWindowsHookEx(self.mhook)
            self.mhook = None
        user32.UnhookWindowsHookEx(self.hhook)
        self.hhook = None

    def reseat(self):
        """Put the keyboard hook in again, at the hook thread's next message (not during a press)."""
        self._post(RESEAT)

    def start(self):
        """Put the hook in, on its own thread; -> True when it went in."""
        if self.thread and self.thread.is_alive():
            return bool(self.hhook)
        self._ready.clear()
        self.tap = Tap()
        self.thread = threading.Thread(target=self._run, name="winkey", daemon=True)
        self.thread.start()
        self._ready.wait(5)
        return bool(self.hhook)

    def stop(self, wait=5):
        """Take the hook out; -> True when its thread ended (so the hook is gone)."""
        if not self.thread:
            return True
        if self.tid:
            user32.PostThreadMessageW(self.tid, WM_QUIT, 0, 0)
        self.thread.join(wait)
        gone = not self.thread.is_alive()
        if gone:
            self.thread = None
        return gone

    @property
    def on(self):
        return bool(self.thread and self.thread.is_alive() and self.hhook)


if __name__ == "__main__":
    print("full screen in front:", fullscreen_in_front())
    print("remote session:", bool(user32.GetSystemMetrics(SM_REMOTESESSION)))
    print("a bare tap now would:", why_not() or "act")
