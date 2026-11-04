"""EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
(people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.

sprite: a see-through, click-through window that shows one small picture with real alpha (a layered window,
UpdateLayeredWindow), for the little guy's overlay.

Why not WebView2: pywebview's transparent windows use a colour key, and on this machine the key failed after the
window was moved or restarted, leaving a grey box around the guy (ran 23 Oct, twice). A layered window with per-pixel
alpha is the shell's own way to draw a shape over the desktop, needs no browser engine, and cannot take a click.

    s = Sprite(w, h); s.start()       a thread of its own owns the window and pumps its messages
    s.show(image, x, y)               an RGBA PIL image, placed with its top-left at x, y (real pixels)
    s.hide(); s.close()
"""
import ctypes
import threading
import time
from ctypes import wintypes as wt

from PIL import Image, ImageChops

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32")
kernel32 = ctypes.WinDLL("kernel32")

WS_POPUP = 0x80000000
WS_EX = 0x80000 | 0x20 | 0x80 | 0x8 | 0x08000000     # layered, transparent (click-through), tool, topmost, no activate
ULW_ALPHA = 2


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [("BlendOp", ctypes.c_ubyte), ("BlendFlags", ctypes.c_ubyte), ("SourceConstantAlpha", ctypes.c_ubyte),
                ("AlphaFormat", ctypes.c_ubyte)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wt.DWORD), ("biWidth", ctypes.c_long), ("biHeight", ctypes.c_long), ("biPlanes", wt.WORD),
                ("biBitCount", wt.WORD), ("biCompression", wt.DWORD), ("biSizeImage", wt.DWORD),
                ("biXPelsPerMeter", ctypes.c_long), ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wt.DWORD),
                ("biClrImportant", wt.DWORD)]


WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)
user32.DefWindowProcW.restype = ctypes.c_ssize_t
user32.DefWindowProcW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
user32.CreateWindowExW.restype = wt.HWND
user32.CreateWindowExW.argtypes = [wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, wt.HWND, wt.HMENU, wt.HINSTANCE, wt.LPVOID]
user32.UpdateLayeredWindow.argtypes = [wt.HWND, wt.HDC, ctypes.POINTER(wt.POINT), ctypes.POINTER(wt.SIZE), wt.HDC,
                                       ctypes.POINTER(wt.POINT), wt.DWORD, ctypes.POINTER(BLENDFUNCTION), wt.DWORD]
user32.GetDC.restype = wt.HDC
user32.GetDC.argtypes = [wt.HWND]
user32.ReleaseDC.argtypes = [wt.HWND, wt.HDC]
user32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
user32.DestroyWindow.argtypes = [wt.HWND]
user32.UnregisterClassW.argtypes = [wt.LPCWSTR, wt.HINSTANCE]
gdi32.CreateCompatibleDC.restype = wt.HDC
gdi32.CreateCompatibleDC.argtypes = [wt.HDC]
gdi32.CreateDIBSection.restype = wt.HBITMAP
gdi32.CreateDIBSection.argtypes = [wt.HDC, ctypes.c_void_p, wt.UINT, ctypes.POINTER(ctypes.c_void_p), wt.HANDLE, wt.DWORD]
gdi32.SelectObject.restype = wt.HGDIOBJ
gdi32.SelectObject.argtypes = [wt.HDC, wt.HGDIOBJ]
gdi32.DeleteObject.argtypes = [wt.HGDIOBJ]
gdi32.DeleteDC.argtypes = [wt.HDC]
kernel32.GetModuleHandleW.restype = wt.HMODULE


class WNDCLASS(ctypes.Structure):
    _fields_ = [("style", wt.UINT), ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int),
                ("hInstance", wt.HINSTANCE), ("hIcon", wt.HICON), ("hCursor", wt.HANDLE), ("hbrBackground", wt.HBRUSH),
                ("lpszMenuName", wt.LPCWSTR), ("lpszClassName", wt.LPCWSTR)]


def premultiplied_bgra(img):
    """RGBA -> the premultiplied BGRA bytes a layered window wants."""
    img = img.convert("RGBA")
    r, g, b, a = img.split()
    r, g, b = (ImageChops.multiply(c, a) for c in (r, g, b))
    return Image.merge("RGBA", (b, g, r, a)).tobytes()


class Sprite:
    def __init__(self, title="Agora guy", hit_test=None, on_pointer=None):
        self.title = title
        self.hwnd = None
        self.want = None                  # (image key, image, x, y) asked for
        self.shown_key = None
        self.cache = {}                   # image key -> (hbitmap, w, h)
        self.visible = True
        self.ready = threading.Event()
        self.stop_ev = threading.Event()
        self.lock = threading.Lock()
        self.hit_test, self.on_pointer = hit_test, on_pointer

    def start(self):
        threading.Thread(target=self._loop, daemon=True, name="sprite").start()
        self.ready.wait(5)

    def show(self, key, img, x, y):
        with self.lock:
            self.want = (key, img, int(x), int(y))

    def hide(self, hidden=True):
        self.visible = not hidden

    def close(self):
        self.stop_ev.set()

    def _bitmap(self, key, img):
        hit = self.cache.get(key)
        if hit:
            return hit
        w, h = img.size
        bi = BITMAPINFOHEADER()
        bi.biSize, bi.biWidth, bi.biHeight, bi.biPlanes, bi.biBitCount = ctypes.sizeof(BITMAPINFOHEADER), w, -h, 1, 32
        bits = ctypes.c_void_p()
        hbm = gdi32.CreateDIBSection(None, ctypes.byref(bi), 0, ctypes.byref(bits), None, 0)
        data = premultiplied_bgra(img)
        ctypes.memmove(bits, data, len(data))
        if len(self.cache) > 64:                       # bubbles come and go: keep the cache small
            for k in list(self.cache)[:32]:
                gdi32.DeleteObject(self.cache.pop(k)[0])
        self.cache[key] = (hbm, w, h)
        return self.cache[key]

    def _put(self, key, img, x, y):
        hbm, w, h = self._bitmap(key, img)
        screen = user32.GetDC(None)
        mem = gdi32.CreateCompatibleDC(screen)
        old = gdi32.SelectObject(mem, hbm)
        blend = BLENDFUNCTION(0, 0, 255, 1)
        user32.UpdateLayeredWindow(self.hwnd, screen, ctypes.byref(wt.POINT(x, y)), ctypes.byref(wt.SIZE(w, h)), mem,
                                   ctypes.byref(wt.POINT(0, 0)), 0, ctypes.byref(blend), ULW_ALPHA)
        gdi32.SelectObject(mem, old)
        gdi32.DeleteDC(mem)
        user32.ReleaseDC(None, screen)

    def _loop(self):
        def dispatch(h, m, w, l):
            if m == 0x84 and self.hit_test:  # WM_NCHITTEST, screen coordinates
                x,y=ctypes.c_short(l & 65535).value,ctypes.c_short((l >> 16) & 65535).value
                return 1 if self.hit_test(x,y) else -1  # HTCLIENT / HTTRANSPARENT
            if m in (0x201,0x202,0x200) and self.on_pointer:
                p=wt.POINT();user32.GetCursorPos(ctypes.byref(p))
                self.on_pointer(m,p.x,p.y)
                return 0
            return user32.DefWindowProcW(h,m,w,l)
        self._proc = WNDPROC(dispatch)
        wc = WNDCLASS()
        class_name = f'AgoraSprite{id(self)}'
        wc.lpfnWndProc, wc.lpszClassName = self._proc, class_name
        wc.hInstance = kernel32.GetModuleHandleW(None)
        user32.RegisterClassW(ctypes.byref(wc))
        self.hwnd = user32.CreateWindowExW(WS_EX & ~0x20 if self.hit_test else WS_EX, class_name, self.title, WS_POPUP, 0, 0, 1, 1, None, None,
                                           wc.hInstance, None)
        self.ready.set()
        msg = wt.MSG()
        was_visible = None
        last = None
        while not self.stop_ev.is_set():
            while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            with self.lock:
                want = self.want
            if want and want[:1] + want[2:] != last:
                last = want[:1] + want[2:]
                self._put(*want)
            if self.visible != was_visible and want:
                user32.ShowWindow(self.hwnd, 4 if self.visible else 0)       # SW_SHOWNOACTIVATE / SW_HIDE
                was_visible = self.visible
            time.sleep(0.012)
        user32.DestroyWindow(self.hwnd)
        user32.UnregisterClassW(class_name,wc.hInstance)
        for hbm, _, _ in self.cache.values():
            gdi32.DeleteObject(hbm)
