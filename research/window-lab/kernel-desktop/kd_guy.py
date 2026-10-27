"""kd_guy: the little guy. A module (SHAPE 11) who walks along the Agora taskbar and hops onto the tops of windows.

Started by the kernel (the world's module thing `guy`), never by hand. What he does, in the design's own words: he
holds `window.overlay` (a hold word: the kernel lists his lease in `holds`, and `off guy` ends it) and sees `window.list all` (through
the kernel, which asks the window module) to know where the windows are. Where he is right now is momentary and stays
in this process; he keeps nothing lasting of his own.

    look guy           the kernel says what he is (a module, his grants, his words)
    status guy         he says what he is doing
    guy.say <words>    a speech bubble for a few seconds (the words are shown, never run)
    guy.hop [window]   hop onto that window now (an id or a name from window.list), or onto any
    guy.sit            sit down where he is for a while
    off guy | stop guy he goes: the hold ends, the overlay closes, the process stops. undo brings him back.

His window is click-through (it never takes a click or the focus), topmost, and hides while a program is full screen.
"""
import ctypes
import math
import os
import random
import sys
import threading
import time
from ctypes import wintypes as wt
from pathlib import Path

VENV_SITE = Path(__file__).resolve().parents[3] / ".venv" / "Lib" / "site-packages"
if VENV_SITE.exists() and str(VENV_SITE) not in sys.path:
    sys.path.append(str(VENV_SITE))
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from modproto import Module, log  # noqa: E402
import guy_looks  # noqa: E402

HEADLESS = "--headless" in sys.argv
PORT = int(os.environ.get("AGORA_KDESK_PORT", "8810"))
W, H = 300, 230                 # his picture, in real pixels: he stands at its bottom middle, the bubble above
FPS = 30
WALK = 95                       # pixels a second
SPRITE_HALF = 36

if sys.platform == "win32":
    user32 = ctypes.WinDLL("user32", use_last_error=True)      # private: shared argtypes break pywebview
    if not HEADLESS:
        user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    user32.SetWindowPos.argtypes = [wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wt.UINT]
    user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
    user32.GetWindowLongPtrW.argtypes = [wt.HWND, ctypes.c_int]
    user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
    user32.SetWindowLongPtrW.argtypes = [wt.HWND, ctypes.c_int, ctypes.c_ssize_t]
    user32.GetForegroundWindow.restype = wt.HWND
    user32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
    user32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
HWND_TOPMOST = wt.HWND(-1)
GWL_EXSTYLE = -20
WS_EX_LAYERED, WS_EX_TRANSPARENT, WS_EX_TOOLWINDOW, WS_EX_NOACTIVATE, WS_EX_APPWINDOW = 0x80000, 0x20, 0x80, 0x08000000, 0x40000


class Platform:
    def __init__(self, key, name, x1, x2, y, z):
        self.key, self.name, self.x1, self.x2, self.y, self.z = key, name, x1, x2, y, z

    def __repr__(self):
        return f"Platform({self.name} {self.x1}-{self.x2} @ {self.y})"


def visible_parts(x1, x2, y, front):
    """The parts of the edge x1..x2 at height y that no window in front covers (just above the edge, where he stands)."""
    parts = [(x1, x2)]
    for (fx, fy, fw, fh) in front:
        if not (fy <= y - 8 <= fy + fh):
            continue
        nxt = []
        for a, b in parts:
            if fx + fw <= a or fx >= b:
                nxt.append((a, b))
                continue
            if a < fx:
                nxt.append((a, fx))
            if fx + fw < b:
                nxt.append((fx + fw, b))
        parts = nxt
    return [(a, b) for a, b in parts if b - a >= 140]


class Guy:
    def __init__(self):
        self.x, self.y = 600.0, 2000.0
        self.facing = 1
        self.state = "stand"          # stand, walk, jump, fall, sit
        self.on = None                # the platform key he stands on
        self.platforms = {}
        self.jump = None              # (x0, y0, x1, y1, t0, dur, key)
        self.until = 0.0              # when the present stand or sit ends
        self.next_hop = time.time() + random.uniform(8, 14)
        self.bubble, self.bubble_until = "", 0.0
        self.holding = False
        self.hidden = False
        self.pose_sent = None
        self.sprite = None
        self.pictures = {}
        self.looks = guy_looks.clean({})
        self.look_revision = 0
        self.next_phrase = time.time() + 30
        self.lock = threading.Lock()
        self.m = Module(offer=self.offer(), on_call=self.call, on_happen=self.happen, on_status=self.status,
                        on_off=self.off)

    def offer(self):
        return [
            {"word": "guy.say", "kind": "do", "takes": "<words>", "may": "anyone",
             "help": "guy.say <words>: the little guy says it in a bubble for a few seconds. The words are shown, never run."},
            {"word": "guy.hop", "kind": "do", "takes": "[<id>] [<words>]", "may": "anyone",
             "help": "guy.hop [window]: the little guy hops onto that window (an id or name from window.list), or onto "
                     "whichever he likes."},
            {"word": "guy.sit", "kind": "do", "takes": "", "may": "anyone",
             "help": "guy.sit: the little guy sits down where he is for a while."},
        ]

    # -- the protocol
    def call(self, msg):
        word, args = msg["word"], msg.get("args") or {}
        who = (msg.get("caller") or {}).get("name", "someone")
        if not self.holding:
            return {"refused": "the guy holds no window.overlay right now, so there is nothing to show; holds says who holds what"}
        if word == "guy.say":
            words = (args.get("words") or "").strip()
            if not words:
                return {"refused": "guy.say needs words"}
            self.say(words[:120])
            self.m.happen('guy.say', text=words[:120])
            return {"text": f"the guy says “{words[:120]}” (for {who})"}
        if word == "guy.sit":
            with self.lock:
                if self.state in ("walk", "stand"):
                    self.state, self.until = "sit", time.time() + 12
            return {"text": "the guy sits down for a bit"}
        if word == "guy.hop":
            self.m.happen('guy.hop', target=args.get('target'))
            want = args.get("target") or (args.get("words") or "").strip()
            p = self.pick(want)
            if p is None and want:
                self.look_around()                    # a window opened a moment ago may not be on his map yet
                p = self.pick(want)
            if p is None:
                return {"refused": f"no window top he can reach{' called ' + want if want else ''}; window.list shows them"}
            self.hop_to(p)
            return {"text": f"the guy hops onto {p.name}"}
        return {"refused": f"guy has no word {word}"}

    def happen(self, h):
        if h.get("word") == "window.opened":
            if self.looks['chatty'] != 'quiet':
                phrases = self.looks['phrases'].splitlines()
                self.say((phrases[-1] if phrases else "ooh, a new window")[:120])

    def status(self):
        p = self.platforms.get(self.on)
        where = p.name if p else "the air"
        doing = {"walk": "walking", "stand": "standing", "jump": "hopping", "fall": "falling", "sit": "sitting"}[self.state]
        hold = "holds window.overlay" if self.holding else "waiting for the window.overlay hold"
        return (f"{doing} on {where} at {int(self.x)},{int(self.y)}; {hold}; knows {len(self.platforms)} window tops"
                + (f"; saying “{self.bubble}”" if time.time() < self.bubble_until else "")
                + f"; look r{self.look_revision} {self.looks}")

    def off(self):
        try:
            if self.sprite is not None:
                self.sprite.close()
                time.sleep(0.1)
        finally:
            os._exit(0)

    def say(self, words):
        self.bubble, self.bubble_until = words, time.time() + 6
        self.pose_sent = None

    # -- where the windows are
    def refresh_looks(self):
        """Read ordinary world facts; malformed neighbour edits fall back safely."""
        rows = self.m.see('rows pixel-guy').get('rows', [])
        row = next((r for r in rows if r.get('provider') == self.m.hello.get('id')), None)
        if row is not None:
            looks = guy_looks.clean(row)
            if looks != self.looks:
                self.looks = looks
                self.pictures.clear()
            self.look_revision = row.get('rev', 0)

    def watch_looks(self):
        while not self.m.closed.is_set():
            self.refresh_looks()
            self.m.closed.wait(0.4)

    def look_around(self):
        # Python remains the fallback and word provider. JS takes the drawing
        # only while its real overlay lease is alive, not merely installed.
        held = self.m.see('holds')
        self.js_active = any(r.get('by') == 'desktop-guy' and r.get('word') == 'window.overlay'
                             for r in held.get('rows', []))
        r = self.m.see("window.list all")
        rows = r.get("rows") or []
        if r.get("refused") or not rows:
            return
        work = next((x["box"] for x in rows if x.get("kind") == "work"), None)
        wins = [x for x in rows if x.get("kind") in ("window", "other") and x.get("box") and x.get("shown", True)]
        wins.sort(key=lambda x: x.get("z", 9999))
        bar = next((x for x in wins if x.get("shows") == "taskbar"), None)
        plats = {}
        if bar:
            self.bar_id = bar.get("id")
            bx, by, bw, bh = bar["box"]
            plats["bar"] = Platform("bar", "the taskbar", bx + 20, bx + bw - 20, by, -1)
        elif work:
            wx, wy, ww, wh = work
            plats["bar"] = Platform("bar", "the bottom of the screen", wx + 20, wx + ww - 20, wy + wh, -1)
        front = []
        for i, x in enumerate(wins):
            if x.get("shows") == "taskbar":
                continue
            bx, by, bw, bh = x["box"]
            if by > 100 and bw > 300:
                name = x.get("name") or "a window"
                for n, (a, b) in enumerate(visible_parts(bx + 10, bx + bw - 10, by, front)):
                    key = (x.get("id") or f"o{x.get('program')}:{bx // 40}") + f".{n}"
                    plats[key] = Platform(key, name, a, b, by, i)
            front.append((bx, by, bw, bh))
        with self.lock:
            old = self.platforms.get(self.on)
            self.platforms = plats
            if self.state in ("walk", "stand", "sit") and self.on is not None:
                p = self._same(old)
                if p is None or not (p.x1 - 10 <= self.x <= p.x2 + 10):
                    self.state, self.on, self.vy = "fall", None, 0.0          # the window went: down he goes
                else:
                    self.on, self.y = p.key, p.y

    def _same(self, old):
        if old is None:
            return None
        if old.key in self.platforms:
            return self.platforms[old.key]
        base = old.key.rsplit(".", 1)[0]
        near = [p for k, p in self.platforms.items() if k.rsplit(".", 1)[0] == base]
        return min(near, key=lambda p: abs((p.x1 + p.x2) / 2 - self.x), default=None)

    def pick(self, want=""):
        ps = [p for p in self.platforms.values() if p.key != self.on]
        if want and want == getattr(self, "bar_id", None):
            return self.platforms.get("bar") if self.on != "bar" else None
        if want:
            w = want.lower()
            ps = [p for p in ps if p.key.split(".")[0] == want or w in p.name.lower()]
        return random.choice(ps) if ps else None

    def hop_to(self, p):
        with self.lock:
            x1 = random.uniform(p.x1 + 30, max(p.x1 + 31, p.x2 - 30))
            dist = math.hypot(x1 - self.x, p.y - self.y)
            self.jump = (self.x, self.y, x1, p.y, time.time(), 0.55 + min(1.2, dist / 2600), p.key)
            self.state = "jump"
            self.facing = 1 if x1 >= self.x else -1

    # -- moving
    def tick(self, dt):
        now = time.time()
        with self.lock:
            p = self.platforms.get(self.on)
            if self.state == "jump":
                x0, y0, x1, y1, t0, dur, key = self.jump
                t = min(1.0, (now - t0) / dur)
                apex = min(y0, y1) - 160 - abs(x1 - x0) * 0.08
                # a parabola through start, apex and end
                self.x = x0 + (x1 - x0) * t
                self.y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * (2 * apex - (y0 + y1) / 2) + t ** 2 * y1
                if t >= 1.0:
                    self.on, self.state, self.until = key, "stand", now + random.uniform(0.6, 1.6)
                    if key not in self.platforms:
                        self.state, self.vy = "fall", 0.0
            elif self.state == "fall":
                self.vy = getattr(self, "vy", 0.0) + 2600 * dt
                ny = self.y + self.vy * dt
                below = [q for q in self.platforms.values() if q.x1 <= self.x <= q.x2 and self.y - 2 <= q.y <= ny + 2]
                if below:
                    q = min(below, key=lambda q: q.y)
                    self.y, self.on, self.state, self.until = q.y, q.key, "stand", now + 1.2
                    self.bubble, self.bubble_until = ("oof", now + 1.5) if self.vy > 1400 else (self.bubble, self.bubble_until)
                else:
                    self.y = ny
                    if self.y > 2300:                        # off the bottom: start again on the taskbar
                        bar = self.platforms.get("bar")
                        if bar:
                            self.x, self.y, self.on, self.state = (bar.x1 + bar.x2) / 2, bar.y, "bar", "stand"
            elif p is None:
                bar = self.platforms.get("bar")
                if bar:
                    self.x = min(max(self.x, bar.x1), bar.x2)
                    self.y, self.on, self.state = bar.y, "bar", "stand"
            elif self.state == "walk":
                self.x += self.facing * float(self.looks['speed']) * dt
                if self.x <= p.x1 + SPRITE_HALF or self.x >= p.x2 - SPRITE_HALF:
                    self.x = min(max(self.x, p.x1 + SPRITE_HALF), p.x2 - SPRITE_HALF)
                    self.facing *= -1
                if now > self.until:
                    self.state, self.until = "stand", now + random.uniform(1.0, 3.5)
            elif self.state in ("stand", "sit") and now > self.until:
                self.state, self.until = "walk", now + random.uniform(3, 9)
                if random.random() < 0.4:
                    self.facing *= -1
            if self.state in ("walk", "stand") and now > self.next_hop and len(self.platforms) > 1:
                self.next_hop = now + random.uniform(10, 22)
                choice = self.pick() if self.on == "bar" or random.random() < 0.6 else self.platforms.get("bar")
                if choice is not None and choice.key != self.on:
                    threading.Thread(target=self.hop_to, args=(choice,), daemon=True).start()

    def pose(self):
        if self.looks['chatty'] == 'chatty' and time.time() > self.next_phrase:
            self.next_phrase = time.time() + random.uniform(20, 40)
            phrases = [p for p in self.looks['phrases'].splitlines() if p.strip()]
            if phrases:
                self.say(random.choice(phrases)[:120])
        pose = {"jump": "jump", "fall": "jump", "walk": "walk", "sit": "sit"}.get(self.state, "stand")
        if pose == "walk":
            pose = "walk1" if int(time.time() / 0.17) % 2 else "walk2"
        blink = (time.time() % 3.7) < 0.14
        bubble = self.bubble if time.time() < self.bubble_until else ""
        return (pose, self.facing, bubble, blink)

    # -- his window
    def fullscreen_app(self):
        h = user32.GetForegroundWindow()
        if not h or (self.sprite and h == self.sprite.hwnd):
            return False
        r = wt.RECT()
        user32.GetWindowRect(h, ctypes.byref(r))
        import gaming_gate
        if gaming_gate.is_desktop(h):          # Explorer's desktop or Agora's wallpaper layer (a click puts it in front)
            return False
        return r.left <= 0 and r.top <= 0 and r.right >= user32.GetSystemMetrics(0) and r.bottom >= user32.GetSystemMetrics(1)

    def drive(self):
        """30 times a second: move, then draw him where he is. Only his pose and place change on the screen."""
        last = time.time()
        looked = 0.0
        while not self.m.closed.is_set():
            now = time.time()
            if now - looked > 1.2:
                looked = now
                threading.Thread(target=self.look_around, daemon=True).start()
            self.tick(min(0.1, now - last))
            last = now
            hide = self.fullscreen_app() or getattr(self, 'js_active', False)
            if hide != self.hidden:
                self.hidden = hide
                self.sprite.hide(hide)
            if not hide:
                pose = self.pose()
                looks = self.looks
                key = (pose, tuple(sorted(looks.items())))
                img = self.pictures.get(key)
                if img is None:
                    if len(self.pictures) > 40:
                        self.pictures.clear()
                    img = self.pictures[key] = art.picture(*pose, looks=looks)
                self.sprite.show(key, img, self.x - W / 2, self.y - H + 2)
            time.sleep(1 / FPS)

    def hold_overlay(self):
        """Ask the kernel for the window.overlay hold (a lease, on his own grants), until it says yes."""
        while not self.m.closed.is_set():
            out = self.m.hold("window.overlay")
            if out.get("lease"):
                self.holding, self.lease = True, out["lease"]
                log(f"hold: window.overlay, lease {out['lease']}")
                return True
            log(f"hold refused: {out.get('refused')}")
            time.sleep(5)

    def run(self):
        self.m.run_reader()
        self.m.ready.wait(30)
        self.hold_overlay()
        self.refresh_looks()
        threading.Thread(target=self.watch_looks, daemon=True, name='guy-looks').start()
        if HEADLESS:
            threading.Thread(target=self.drive_headless, daemon=True).start()
            self.m.closed.wait()
            return
        from sprite import Sprite
        self.sprite = Sprite("Agora guy")
        self.sprite.start()
        self.say("hello, Alex")
        self.look_around()
        bar = self.platforms.get("bar")
        if bar:
            self.x, self.y, self.on = bar.x1 + 300, bar.y, "bar"
        threading.Thread(target=self.drive, daemon=True, name="drive").start()
        self.m.closed.wait()
        self.off()

    def drive_headless(self):
        while not self.m.closed.is_set():
            self.look_around()
            for _ in range(12):
                self.tick(0.1)
                time.sleep(0.1)


class art:
    """The guy, 16 by 16 in the desk's colours (k ink, o face, b coat in the desk's accent, r cheeks, s shoes), drawn
    five real pixels to one of his, with a speech bubble above when he says something."""
    PAL = {"k": (20, 23, 26), "o": (242, 200, 148), "b": (63, 93, 115), "r": (232, 149, 107), "s": (122, 92, 46)}
    HEAD = ["................", ".....kkkkkk.....", "....koooooook...", "...koooooooook..", "...kookoookook..",
            "...koooooooook..", "...korooooorok..", "....kooookook...", ".....kkkkkkk...."]
    BODY = {
        "stand": ["....kbbbbbbk....", "...kbbbbbbbbk...", "...kbkbbbbkbk...", "....kbbbbbbk....", ".....kk..kk.....",
                  ".....ss..ss.....", "....sss..sss...."],
        "walk1": ["....kbbbbbbk....", "...kbbbbbbbbk...", "..kbbkbbbbkbbk..", "....kbbbbbbk....", "....kk....kk....",
                  "...ss......ss...", "..sss......sss.."],
        "walk2": ["....kbbbbbbk....", "...kbbbbbbbbk...", "...kbkbbbbkbk...", "....kbbbbbbk....", "......kkkk......",
                  "......ssss......", ".....ssssss....."],
        "jump": ["..k.kbbbbbbk.k..", "...kbbbbbbbbk...", "....kbbbbbbk....", "....kbbbbbbk....", "...kk......kk...",
                 "..ss........ss..", "................"],
        "sit": ["................", "....kbbbbbbk....", "...kbbbbbbbbk...", "..kbkbbbbbbkbk..", "...kbbbbbbbbk...",
                "..sssk....ksss..", "................"],
    }
    PX = 5
    _font = None

    @classmethod
    def font(cls):
        if cls._font is None:
            from PIL import ImageFont
            try:
                cls._font = ImageFont.truetype(r"C:\Windows\Fonts\seguisb.ttf", 19)
            except OSError:
                cls._font = ImageFont.load_default()
        return cls._font

    @classmethod
    def picture(cls, pose, facing, bubble, blink, looks=None):
        from PIL import Image, ImageDraw
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        pal = guy_looks.palette(cls.PAL, looks)
        px, ox, oy = cls.PX, W // 2 - 8 * cls.PX, H - 16 * cls.PX
        for x, y, c in guy_looks.pixels(cls.HEAD, cls.BODY, pose, blink, looks):
            xx = 15 - x if facing < 0 else x
            d.rectangle([ox + xx * px, oy + y * px, ox + xx * px + px - 1, oy + y * px + px - 1], fill=pal[c] + (255,))
        if bubble:
            f = cls.font()
            words, lines = bubble.split(), [""]
            for w_ in words:                          # wrap to about 240 pixels
                trial = (lines[-1] + " " + w_).strip()
                if d.textlength(trial, font=f) > 240 and lines[-1]:
                    lines.append(w_)
                else:
                    lines[-1] = trial
            lines = lines[:3]
            tw = max(d.textlength(l, font=f) for l in lines)
            bw, bh = int(tw) + 24, 26 * len(lines) + 12
            bx, by = (W - bw) // 2, oy - bh - 14
            d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=11, fill=(255, 255, 255, 255),
                                outline=cls.PAL["k"] + (255,), width=3)
            d.polygon([(W // 2 - 8, by + bh - 1), (W // 2 + 8, by + bh - 1), (W // 2, by + bh + 11)], fill=cls.PAL["k"] + (255,))
            for i, l in enumerate(lines):
                d.text((W // 2 - d.textlength(l, font=f) / 2, by + 7 + 26 * i), l, font=f, fill=cls.PAL["k"] + (255,))
        return img


if __name__ == "__main__":
    Guy().run()
