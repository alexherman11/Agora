"""test_winkey.py: a bare Win tap shows or hides the home base; every Win chord stays Windows' (a5980). 16 Oct 2026.

    python test_winkey.py

No key is sent to the machine. The decision (winkey.Tap) is driven with scripted key events; the hook's callback is
called by hand with made-up key records and a stand-in for SendInput; the real hook is put in and taken out (about a
second, with a stand-in sender and a guard that always says no, so a key Alex presses meanwhile passes untouched); the
hook's guard in hud.py is run with stand-ins for the door, the screen and the hook. What only a real press can show:
that Windows keeps Start shut after the mask keys, and that the home base opens.
"""
import ctypes
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import winkey as W  # noqa: E402

bad = []


def check(what, ok, got=None):
    print(("ok   " if ok else "FAIL ") + what + ("" if ok else f"  (got {got!r})"))
    if not ok:
        bad.append(what)


LWIN, RWIN, SHIFT, CTRL, ALT, TAB, ESC = 0x5B, 0x5C, 0xA0, 0xA2, 0xA4, 0x09, 0x1B
LEFT, UP = 0x25, 0x26


def k(c):
    return ord(c)


def run(events, tap=None):
    """events: (vk, 'd'|'u', t[, held]) ... -> the answers, in order."""
    tap = tap or W.Tap()
    out = []
    for e in events:
        vk, du, t = e[:3]
        out.append(tap.feed(vk, du == "d", t, *(e[3:] or [None])))
    return out


def taps(events, tap=None):
    return run(events, tap).count(W.TAP)


def only_last_taps(events):
    got = run(events)
    return got[-1] == W.TAP and got[:-1].count(W.TAP) == 0


def chord(*keys, t=0.0):
    """Win down, each key down then up in turn, Win up: a chord the way it is usually typed."""
    ev, t = [(LWIN, "d", t)], t + 0.05
    for vk in keys:
        ev += [(vk, "d", t), (vk, "u", t + 0.03)]
        t += 0.06
    return ev + [(LWIN, "u", t)]


# -- the bare tap
check("a bare tap of the left Win key toggles, on its up", only_last_taps([(LWIN, "d", 0), (LWIN, "u", 0.12)]))
check("so does the right Win key", only_last_taps([(RWIN, "d", 0), (RWIN, "u", 0.12)]))
check("the Win down itself always passes", run([(LWIN, "d", 0)]) == [W.PASS])
check("two taps, two toggles", taps([(LWIN, "d", 0), (LWIN, "u", 0.1), (LWIN, "d", 0.5), (LWIN, "u", 0.6)]) == 2)

# -- every chord passes
for name, keys in [("Win+D", [k("D")]), ("Win+E", [k("E")]), ("Win+L", [k("L")]), ("Win+V", [k("V")]),
                   ("Win+1", [k("1")]), ("Win+Left", [LEFT]), ("Win+Up Win+Left", [UP, LEFT]), ("Win+Tab", [TAB]),
                   ("Win+.", [0xBE]), ("Win+X", [k("X")]), ("Win+Space", [0x20]), ("Win+PrintScreen", [0x2C])]:
    check(f"{name} passes untouched, every event", taps(chord(*keys)) == 0)
ev = [(LWIN, "d", 0), (SHIFT, "d", 0.05), (k("S"), "d", 0.1), (k("S"), "u", 0.15), (SHIFT, "u", 0.2), (LWIN, "u", 0.25)]
check("Win+Shift+S passes", taps(ev) == 0)
ev = [(LWIN, "d", 0), (SHIFT, "d", 0.05), (k("S"), "d", 0.1), (LWIN, "u", 0.15), (k("S"), "u", 0.2), (SHIFT, "u", 0.25)]
check("Win+Shift+S with Win let go first passes", taps(ev) == 0)
ev = [(SHIFT, "d", 0), (LWIN, "d", 0.05), (k("S"), "d", 0.1), (k("S"), "u", 0.15), (LWIN, "u", 0.2), (SHIFT, "u", 0.25)]
check("Shift first, then Win, then S passes", taps(ev) == 0)
ev = [(SHIFT, "d", 0), (LWIN, "d", 0.05), (LWIN, "u", 0.15), (SHIFT, "u", 0.2)]
check("Shift held across a Win press (Shift+Win) is a chord", taps(ev) == 0)
ev = [(CTRL, "d", 0), (LWIN, "d", 0.05), (LEFT, "d", 0.1), (LEFT, "u", 0.12), (LWIN, "u", 0.15), (CTRL, "u", 0.2)]
check("Ctrl+Win+Left (the next virtual desktop) passes", taps(ev) == 0)
ev = [(LWIN, "d", 0), (k("D"), "u", 0.05), (LWIN, "u", 0.1)]
check("a key's release alone during the press (its down came before) makes a chord", taps(ev) == 0)
every = [vk for vk in range(1, 255) if vk not in W.WIN]
check("every other key, in every order, makes a chord: no toggle for any of 252 keys x 3 orders",
      all(taps(chord(vk)) == 0
          and taps([(LWIN, "d", 0), (vk, "d", 0.05), (LWIN, "u", 0.1), (vk, "u", 0.15)]) == 0
          and taps([(vk, "d", 0), (LWIN, "d", 0.05), (vk, "u", 0.1), (LWIN, "u", 0.15)]) == 0 for vk in every))
check("both Win keys in one press are not a bare tap",
      taps([(LWIN, "d", 0), (RWIN, "d", 0.05), (RWIN, "u", 0.1), (LWIN, "u", 0.15)]) == 0)
check("and the press after a chord taps again", taps(chord(k("D")) + [(LWIN, "d", 1), (LWIN, "u", 1.1)]) == 1)

# -- held, repeating
rep = [(LWIN, "d", 0)] + [(LWIN, "d", 0.5 + i * 0.033) for i in range(30)] + [(LWIN, "u", 1.6)]
check("Win held (1.6 s, repeating) and let go with nothing between passes", taps(rep) == 0)
rep = [(LWIN, "d", 0)] + [(LWIN, "d", 0.25 + i * 0.033) for i in range(10)] + [(LWIN, "u", 0.6)]
check("key repeat inside a short press does not break the tap", only_last_taps(rep))
check("held past HOLD without repeats passes too", taps([(LWIN, "d", 0), (LWIN, "u", W.HOLD + 0.05)]) == 0)

# -- Alt+Tab, Ctrl+Esc and keys the hook never saw go up
alt_tab = [(ALT, "d", 0), (TAB, "d", 0.05), (TAB, "u", 0.1), (TAB, "d", 0.3), (TAB, "u", 0.35), (ALT, "u", 0.6)]
check("Alt+Tab passes, every event", run(alt_tab) == [W.PASS] * 6)
check("a Win tap after Alt+Tab is let go toggles", taps(alt_tab + [(LWIN, "d", 1), (LWIN, "u", 1.1)]) == 1)
check("a Win tap while Alt is still held (the switcher open) is a chord",
      taps([(ALT, "d", 0), (TAB, "d", 0.05), (TAB, "u", 0.1), (LWIN, "d", 2.5), (LWIN, "u", 2.6), (ALT, "u", 3)]) == 0)
check("Ctrl+Esc (Start, Windows' own) never touches the Win key", run([(CTRL, "d", 0), (ESC, "d", 0.05), (ESC, "u", 0.1),
                                                                       (CTRL, "u", 0.15)]) == [W.PASS] * 4)
check("Windows' count of held keys wins: a key whose up was missed does not spoil a tap",
      taps([(CTRL, "d", 0), (LWIN, "d", 5, set()), (LWIN, "u", 5.1, set())]) == 1)
check("and a key Windows counts as held (Alt, in the switcher) makes a chord though no event said so",
      taps([(LWIN, "d", 0, {ALT}), (LWIN, "u", 0.1, {ALT})]) == 0)
check("a mouse button held when Win is let go (Win+click) is a chord", taps([(LWIN, "d", 0, set()), (LWIN, "u", 0.2, {0x01})]) == 0)
t = W.Tap()
t.feed(LWIN, True, 0)
t.mouse(0.1)
check("a quick click or wheel during the press (Sable's point 3) is a chord", t.feed(LWIN, False, 0.2) == W.PASS)
t.mouse(5)
check("a click outside a press changes nothing", taps([(LWIN, "d", 6), (LWIN, "u", 6.1)], t) == 1)
check("the held count leaves out the Win keys themselves", taps([(LWIN, "d", 0, {LWIN}), (LWIN, "u", 0.1, {LWIN})]) == 1)
check("a Win up whose down was never seen passes and does not toggle", run([(LWIN, "u", 0)]) == [W.PASS])
# Win+L: the screen locks, the secure desktop takes the keys, the hook never sees L's up or Win's up
t = W.Tap()
run([(LWIN, "d", 0), (k("L"), "d", 0.05)], t)
check("after Win+L (ups never seen) the next tap, seconds later, toggles", taps([(LWIN, "d", 30, set()), (LWIN, "u", 30.1, set())], t) == 1)
t = W.Tap()
run([(LWIN, "d", 0), (k("L"), "d", 0.05)], t)
check("even counting from events alone (L still counted down) it is a chord, not a stuck tap",
      run([(LWIN, "d", 30), (LWIN, "u", 30.1)], t) == [W.PASS, W.PASS] and t.since is None)

# -- the callback, by hand: a stand-in for SendInput, nothing reaches the machine
sent, toggled, logs = [], [], []
ev_tap = threading.Event()


def fake_send(vk, scan):
    sent.append((vk, scan))
    return 3


def on_tap():
    toggled.append(1)
    ev_tap.set()


def nxt(*a):           # CallNextHookEx stood in: made-up key records never reach another program's hook
    return 0


h = W.Hook(on_tap, may=lambda: "", send=fake_send, held=lambda: set(), log=logs.append, nxt=nxt)


def key(vk, down, extra=0, hook=h, scan=0x5B):
    rec = W.KBDLLHOOKSTRUCT(vk, scan, 0, 0, extra)
    return hook._call(0, W.WM_KEYDOWN if down else W.WM_KEYUP, ctypes.addressof(rec))


check("the callback passes a Win down", key(LWIN, True) == 0)
r = key(LWIN, False)
ev_tap.wait(2)
check("a bare tap's Win up is held back (1), the mask and Win up sent, the toggle handed on",
      r == 1 and sent == [(LWIN, 0x5B)] and toggled == [1] and h.taps == 1, (r, sent, toggled))
check("a chord's Win up passes and sends nothing",
      [key(LWIN, True), key(k("D"), True), key(k("D"), False), key(LWIN, False)] == [0, 0, 0, 0] and len(sent) == 1, sent)
check("our own keys (marked) pass and are not counted: a marked key in a press keeps it bare",
      [key(LWIN, True), key(W.MASK_VK, True, W.MARK), key(LWIN, False)][-1] == 1 and len(sent) == 2, sent)
h2 = W.Hook(on_tap, may=lambda: "a full-screen program is in front", send=fake_send, held=lambda: set(), log=logs.append, nxt=nxt)
check("a tap the guard refuses passes to Windows, sends nothing and says why",
      [key(LWIN, True, hook=h2), key(LWIN, False, hook=h2)] == [0, 0] and len(sent) == 2
      and logs[-1] == "winkey: a bare tap passed to Windows: a full-screen program is in front", logs)
h3 = W.Hook(on_tap, may=lambda: "", send=lambda vk, sc: 0, held=lambda: set(), log=logs.append, nxt=nxt)
check("when Windows refuses the mask keys the real Win up passes (never left down), no toggle",
      [key(LWIN, True, hook=h3), key(LWIN, False, hook=h3)] == [0, 0] and h3.taps == 0 and "refused the mask" in logs[-1], logs)


def boom():
    raise OSError("no")


h4 = W.Hook(on_tap, may=lambda: "", send=fake_send, held=boom, log=logs.append, nxt=nxt)
check("a fault inside the callback passes the key on and is said",
      key(LWIN, True, hook=h4) == 0 and logs[-1].startswith("winkey: hook fault OSError"), logs[-1:])

# what each key costs: the callback by hand (stood-in next hook), an ordinary key and a Win press with Windows' real
# count of held keys (254 GetAsyncKeyState calls)
hm = W.Hook(on_tap, may=lambda: "measuring", send=fake_send, log=logs.append, nxt=nxt)
t0 = time.perf_counter()
for _ in range(2000):
    key(k("A"), True, hook=hm)
    key(k("A"), False, hook=hm)
per_key = (time.perf_counter() - t0) / 4000
t0 = time.perf_counter()
for i in range(200):
    key(LWIN, True, hook=hm)
    key(LWIN, False, hook=hm)
per_win = (time.perf_counter() - t0) / 400
print(f"     (callback: {per_key * 1e6:.0f} us per ordinary key, {per_win * 1e6:.0f} us per Win event; Windows allows up to 1 s)")
check("a key costs well under a millisecond in the callback", per_key < 0.001 and per_win < 0.005, (per_key, per_win))

# the mask itself, built but not sent: what send_mask would hand SendInput
built = []
real_send = W.user32.SendInput
W.user32.SendInput = lambda n, arr, size: built.extend((arr[i].u.ki.wVk, arr[i].u.ki.dwFlags, arr[i].u.ki.dwExtraInfo)
                                                       for i in range(n)) or n
try:
    n = W.send_mask(RWIN, 0x5C)
finally:
    W.user32.SendInput = real_send
check("send_mask: 0xFF down, 0xFF up, then that Win key's up (extended), all marked as ours",
      n == 3 and built == [(0xFF, 0, W.MARK), (0xFF, 2, W.MARK), (RWIN, 3, W.MARK)], built)
check("an INPUT is the size Windows expects (40 bytes on 64-bit)", ctypes.sizeof(W.INPUT) == (40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28),
      ctypes.sizeof(W.INPUT))

# -- the real hook, in and out (it never acts: the guard always says no, the sender is a stand-in)
real = W.Hook(lambda: None, may=lambda: "a test hook never acts", send=lambda vk, sc: 0, log=logs.append)
t0 = time.perf_counter()
went = real.start()
check("the hook goes in, on a thread of its own", went and real.on and real.thread.name == "winkey" and real.hhook,
      (went, real.hhook))
check("starting it again does not put in a second", real.start() and real.on)
old = real.hhook
real.reseat()
time.sleep(0.2)
check("reseat puts a new hook in and takes the old out (Windows had not dropped it)",
      real.on and real.hhook and real.hhook != old and real.dropped == 0, (old, real.hhook, real.dropped))
# the mouse hook rides on a Win press: a made-up press, fed by hand (CallNextHookEx stood in), never reaches Windows
real.nxt = nxt
real.held = lambda: set()
check("no mouse hook outside a press", real.mhook is None)
key(LWIN, True, hook=real)
time.sleep(0.2)
check("a Win press puts the mouse hook in", bool(real.mhook), real.mhook)
key(k("D"), True, hook=real)
key(k("D"), False, hook=real)
key(LWIN, False, hook=real)
time.sleep(0.2)
check("and its end takes it out", real.mhook is None, real.mhook)
key(LWIN, True, hook=real)
time.sleep(0.2)
had = bool(real.mhook)
gone = real.stop()
check("stopping during a press takes the mouse hook out too", had and real.mhook is None and real.hhook is None)
real.thread = None
real.nxt, real.held = W.user32.CallNextHookEx, W.held_now
real.start()
check("slow callbacks are counted (none so far)", real.slow == 0 and real.slowest < W.SLOW, (real.slow, real.slowest))
gone = real.stop()
check("and comes out: its thread ends (Windows removes a hook whose thread is gone)", gone and not real.on and real.thread is None)
check("in again, out again", real.start() and real.stop() and not real.on)
print(f"     (in and out twice in {time.perf_counter() - t0:.2f} s)")
check("stopping a hook that is not in is harmless", W.Hook(lambda: None).stop())

# a process holding the hook, killed: the kill takes the hook with it (Windows' rule; we see the process end)
child = subprocess.Popen([sys.executable, "-c",
                          "import sys, time; sys.path.insert(0, r'%s'); import winkey as W;"
                          "h = W.Hook(lambda: None, may=lambda: 'test', send=lambda v, s: 0);"
                          "print('in' if h.start() else 'not in', flush=True); time.sleep(60)" % HERE],
                         stdout=subprocess.PIPE, text=True, creationflags=0x08000000)
said = child.stdout.readline().strip()
subprocess.run(["taskkill", "/PID", str(child.pid), "/T", "/F"], capture_output=True)
child.wait(10)
check("a process with the hook in, killed, ends at once", said == "in" and child.returncode not in (None, 0),
      (said, child.returncode))

# -- the guard's eyes (read only)
import os  # noqa: E402
w = W.why_not(os.getpid())
check("why_not answers words or nothing", isinstance(w, str), w)
check("full screen is a yes or no", W.fullscreen_in_front(os.getpid()) in (True, False))
check("this process is not elevated", W.elevated(os.getpid()) is False)
check("a process whose token is closed to us (System, pid 4) counts as elevated", W.elevated(4) is True)

# -- hud.py's guard with stand-ins: the hook goes in and out with winkey=, --winkey off and a full-screen program
import hud as HUD  # noqa: E402


class FakeHook:
    made = []

    def __init__(self, on_tap, may=None, log=None):
        self.on = False
        self.slow, self.slowest, self.dropped, self.reseats = 0, 0.0, 0, 0
        FakeHook.made.append(self)

    def reseat(self):
        self.reseats += 1

    def start(self):
        self.on = True
        return True

    def stop(self):
        self.on = False
        return True


class Stop(Exception):
    pass


def guard(ticks, winkey_arg="on", note=lambda n: "on", door_up=lambda n: True, full=lambda n: False):
    """Run Hud.guard_winkey for `ticks` seconds of stand-in time; -> (is the hook in after each tick, what it printed)."""
    a = type("A", (), {"winkey": winkey_arg, "world": "w", "lens": "home-base", "door": "http://x"})()
    hud = HUD.Hud(a)
    hud.settings = dict(HUD.host_verbs.DEFAULTS)
    n = [0]
    states, printed = [], []
    saved = (HUD.winkey.Hook, HUD.winkey.fullscreen_in_front, HUD.host_verbs.settings, HUD.time.sleep)
    HUD.winkey.Hook = FakeHook
    HUD.winkey.fullscreen_in_front = lambda me: full(n[0])
    HUD.host_verbs.settings = lambda *x: {**HUD.host_verbs.DEFAULTS, "winkey": note(n[0]), "read": door_up(n[0])}

    def tick(_):
        states.append(bool(hud.winkey and hud.winkey.on))
        n[0] += 1
        if n[0] >= ticks:
            raise Stop

    HUD.time.sleep = tick
    HUD.print = lambda *x, **kw: printed.append(" ".join(map(str, x)))
    try:
        hud.guard_winkey()
    except Stop:
        pass
    finally:
        HUD.winkey.Hook, HUD.winkey.fullscreen_in_front, HUD.host_verbs.settings, HUD.time.sleep = saved
        del HUD.print
    return states, printed


s, p = guard(3)
check("hud: the hook goes in at once and stays", s == [True, True, True] and p == ["hud: the Win key shows and hides the home base"], (s, p))
s, p = guard(3, winkey_arg="off")
check("hud --winkey off: never in", s == [False] * 3 and p == ["hud: the Win key is Windows' own: --winkey off"], (s, p))
s, p = guard(40, note=lambda n: "off" if n >= 14 else "on")
check("winkey=off on the note takes it out at the next read (15 s), and keeps it out", s[:14] == [True] * 14 and s[14:] == [False] * 26
      and p[-1] == "hud: the Win key is Windows' own: winkey=off on the lens note", (s, p))
s, p = guard(40, note=lambda n: "off" if n < 20 else "on")
check("winkey=on again puts it back at the next read", s[14] is False and s[-1] is True, s)
s, p = guard(40, note=lambda n: "off" if n < 20 else "on", door_up=lambda n: n < 20)
check("a door that does not answer keeps what was read (off stays off)", s[14] is False and s[-1] is False, s)
s, p = guard(125)
check("hud reseats the hook once a minute", FakeHook.made[-1].reseats == 2, FakeHook.made[-1].reseats)
s, p = guard(6, full=lambda n: 2 <= n < 4)
check("a full-screen program in front takes the hook out (no Python in a game's keys), and it comes back after",
      s == [True, True, False, False, True, True] and "a full-screen program is in front" in p[1], (s, p))

print("winkey:", "all passed" if not bad else f"{len(bad)} failed")
sys.exit(1 if bad else 0)
