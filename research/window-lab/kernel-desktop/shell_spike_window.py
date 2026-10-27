"""Spike 1 (shell builder, 26 Oct 2026): can a WebView2 window have truly transparent corners?

Runs ON A HIDDEN DESKTOP, started by shell_proof.py through research/window-lab/sandbox_window.py (never on Alex's
screen). It makes the same rounded "pill" page in four windows and looks at the corner pixels:

    A  pywebview transparent=True                      (what the library offers)
    B  opaque key colour as the page/background + WS_EX_LAYERED colour key   (our own Win32, no library help)
    C  B with a different key (the pill's own edge colour), to see the anti-aliased fringe
    D  SetWindowRgn rounded region, page opaque                              (region clipping)

For each it prints, as measured: the pixel at the very corner, the pixels along the curve, hit-test through the
corner, and, if this desktop is composed, the pixel a red backing window shows through the corner.
Results go to the JSON file named by argv[1] and PNGs beside it.
"""
import ctypes
import json
import sys
import threading
import time
from ctypes import wintypes as wt
from pathlib import Path

OUT = Path(sys.argv[1])
VENV = Path(__file__).resolve().parents[3] / ".venv" / "Lib" / "site-packages"
if VENV.exists():
    sys.path.append(str(VENV))
import webview  # noqa: E402
from PIL import Image  # noqa: E402

u32, g32, k32 = ctypes.WinDLL("user32", use_last_error=True), ctypes.WinDLL("gdi32"), ctypes.WinDLL("kernel32")
u32.GetWindowDC.restype = wt.HDC
u32.GetWindowDC.argtypes = [wt.HWND]
u32.GetDC.restype = wt.HDC
u32.GetDC.argtypes = [wt.HWND]
u32.ReleaseDC.argtypes = [wt.HWND, wt.HDC]
u32.PrintWindow.argtypes = [wt.HWND, wt.HDC, wt.UINT]
u32.WindowFromPoint.restype = wt.HWND
u32.WindowFromPoint.argtypes = [wt.POINT]
u32.GetAncestor.restype = wt.HWND
u32.GetAncestor.argtypes = [wt.HWND, wt.UINT]
u32.SetWindowPos.argtypes = [wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wt.UINT]
u32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
u32.SetWindowLongPtrW.argtypes = [wt.HWND, ctypes.c_int, ctypes.c_ssize_t]
u32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
u32.GetWindowLongPtrW.argtypes = [wt.HWND, ctypes.c_int]
u32.SetLayeredWindowAttributes.argtypes = [wt.HWND, wt.COLORREF, ctypes.c_ubyte, wt.DWORD]
u32.GetLayeredWindowAttributes.argtypes = [wt.HWND, ctypes.POINTER(wt.COLORREF), ctypes.POINTER(ctypes.c_ubyte),
                                          ctypes.POINTER(wt.DWORD)]
u32.SetWindowRgn.argtypes = [wt.HWND, wt.HRGN, wt.BOOL]
g32.CreateRoundRectRgn.restype = wt.HRGN
g32.CreateRoundRectRgn.argtypes = [ctypes.c_int] * 6
g32.CreateCompatibleDC.restype = wt.HDC
g32.CreateCompatibleDC.argtypes = [wt.HDC]
g32.CreateCompatibleBitmap.restype = wt.HBITMAP
g32.CreateCompatibleBitmap.argtypes = [wt.HDC, ctypes.c_int, ctypes.c_int]
g32.SelectObject.restype = wt.HGDIOBJ
g32.SelectObject.argtypes = [wt.HDC, wt.HGDIOBJ]
g32.BitBlt.argtypes = [wt.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wt.HDC, ctypes.c_int,
                       ctypes.c_int, wt.DWORD]
g32.GetDIBits.argtypes = [wt.HDC, wt.HBITMAP, wt.UINT, wt.UINT, ctypes.c_void_p, ctypes.c_void_p, wt.UINT]
g32.DeleteObject.argtypes = [wt.HGDIOBJ]
g32.DeleteDC.argtypes = [wt.HDC]
g32.CreateSolidBrush.restype = wt.HBRUSH
g32.CreateSolidBrush.argtypes = [wt.COLORREF]

GWL_EXSTYLE, WS_EX_LAYERED, LWA_COLORKEY = -20, 0x80000, 1
SWP_NOACTIVATE, SWP_SHOWWINDOW = 0x10, 0x40
PILL = "#6d3fb5"          # the pill
EDGE = "#cdb4ff"          # its 2px edge
W, H, R = 520, 160, 36     # real pixels asked for; pill corner radius in css px


class BIH(ctypes.Structure):
    _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG), ("biPlanes", wt.WORD),
                ("biBitCount", wt.WORD), ("biCompression", wt.DWORD), ("biSizeImage", wt.DWORD),
                ("biXPelsPerMeter", wt.LONG), ("biYPelsPerMeter", wt.LONG), ("biClrUsed", wt.DWORD),
                ("biClrImportant", wt.DWORD)]


def to_image(dc, bmp, w, h):
    bi = BIH(biSize=ctypes.sizeof(BIH), biWidth=w, biHeight=-h, biPlanes=1, biBitCount=32)
    buf = ctypes.create_string_buffer(w * h * 4)
    g32.GetDIBits(dc, bmp, 0, h, buf, ctypes.byref(bi), 0)
    return Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1)


def rect_of(hwnd):
    r = wt.RECT()
    u32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right - r.left, r.bottom - r.top


def print_window(hwnd):
    x, y, w, h = rect_of(hwnd)
    wdc = u32.GetWindowDC(hwnd)
    dc = g32.CreateCompatibleDC(wdc)
    bmp = g32.CreateCompatibleBitmap(wdc, w, h)
    old = g32.SelectObject(dc, bmp)
    ok = u32.PrintWindow(hwnd, dc, 2)
    im = to_image(dc, bmp, w, h)
    g32.SelectObject(dc, old)
    g32.DeleteObject(bmp)
    g32.DeleteDC(dc)
    u32.ReleaseDC(hwnd, wdc)
    return im, bool(ok)


def screen_copy(x, y, w, h):
    sdc = u32.GetDC(None)
    dc = g32.CreateCompatibleDC(sdc)
    bmp = g32.CreateCompatibleBitmap(sdc, w, h)
    old = g32.SelectObject(dc, bmp)
    g32.BitBlt(dc, 0, 0, w, h, sdc, x, y, 0x00CC0020 | 0x40000000)
    im = to_image(dc, bmp, w, h)
    g32.SelectObject(dc, old)
    g32.DeleteObject(bmp)
    g32.DeleteDC(dc)
    u32.ReleaseDC(None, sdc)
    return im


def page(bg, pill, edge):
    return (f'<!doctype html><html><body style="margin:0;background:{bg};overflow:hidden">'
            f'<div style="position:absolute;inset:14px;border-radius:{R}px;background:{pill};box-shadow:inset 0 0 0 2px {edge}">'
            f'</div></body></html>')


def backing(x, y, w, h):
    """A plain red top-level window (own thread and message loop) behind the test window."""
    ready = threading.Event()
    box = {}

    def run():
      try:
        WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)
        u32.DefWindowProcW.restype = ctypes.c_ssize_t
        u32.DefWindowProcW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
        proc = WNDPROC(lambda h, m, w_, l: u32.DefWindowProcW(h, m, w_, l))

        class WC(ctypes.Structure):
            _fields_ = [("style", wt.UINT), ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int),
                        ("cbWndExtra", ctypes.c_int), ("hInstance", wt.HINSTANCE), ("hIcon", wt.HICON),
                        ("hCursor", wt.HANDLE), ("hbrBackground", wt.HBRUSH), ("lpszMenuName", wt.LPCWSTR),
                        ("lpszClassName", wt.LPCWSTR)]
        wc = WC()
        wc.lpfnWndProc, wc.lpszClassName = proc, "ShellSpikeBacking"
        wc.hbrBackground = g32.CreateSolidBrush(0x0000FF)          # COLORREF 0x00BBGGRR: red
        wc.hInstance = k32.GetModuleHandleW(None)
        u32.RegisterClassW(ctypes.byref(wc))
        u32.CreateWindowExW.restype = wt.HWND
        u32.CreateWindowExW.argtypes = [wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD, ctypes.c_int, ctypes.c_int,
                                        ctypes.c_int, ctypes.c_int, wt.HWND, wt.HMENU, wt.HINSTANCE, wt.LPVOID]
        hw = u32.CreateWindowExW(0x80, "ShellSpikeBacking", "backing", 0x90000000, x, y, w, h, None, None,
                                 wc.hInstance, None)              # WS_POPUP | WS_VISIBLE, tool window
        box["h"] = hw
        ready.set()
        msg = wt.MSG()
        end = time.time() + 120
        while time.time() < end:
            while u32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                u32.TranslateMessage(ctypes.byref(msg))
                u32.DispatchMessageW(ctypes.byref(msg))
            time.sleep(0.02)
      except Exception as exc:
        box["err"] = repr(exc)
        ready.set()
    threading.Thread(target=run, daemon=True).start()
    ready.wait(5)
    if "h" not in box:
        raise RuntimeError("backing window: " + box.get("err", "timeout"))
    return box["h"]


def corner_report(im, name):
    """What the corner pixels hold. im is RGBA from the window's own paint."""
    w, h = im.size
    px = im.load()
    ring = [px[x, y] for x, y in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (5, 5), (w // 2, 2))]
    # the anti-aliased fringe along the top-left curve: pixels inside the 14..14+R box that are neither the
    # background, the pill nor the edge colour
    def near(a, b, t=6):
        return all(abs(a[i] - b[i]) <= t for i in range(3))
    out = {"corner": px[0, 0][:3], "alpha_corner": px[0, 0][3], "sample": [p[:3] for p in ring[:4]]}
    bg = px[0, 0]
    pill = tuple(int(PILL[i:i + 2], 16) for i in (1, 3, 5))
    edge = tuple(int(EDGE[i:i + 2], 16) for i in (1, 3, 5))
    fr = 0
    for y in range(14, 14 + R + 2):
        for x in range(14, 14 + R + 2):
            p = px[x, y]
            if not (near(p, bg) or near(p, pill) or near(p, edge)):
                fr += 1
    out["blended_pixels_in_one_corner"] = fr
    return out


def main():
    results = {}
    shared = {}
    x0, y0 = 300, 300

    def variant(name, create_kwargs, html, after=None):
        win = webview.create_window(name, html=html, x=x0, y=y0, width=W, height=H, frameless=True, easy_drag=False,
                                    min_size=(100, 50), hidden=False, **create_kwargs)
        ready = threading.Event()
        win.events.loaded += lambda: ready.set()
        ready.wait(30)
        time.sleep(1.2)
        hwnd = int(win.native.Handle.ToInt64())
        u32.SetWindowPos(hwnd, None, x0, y0, W, H, 4 | SWP_NOACTIVATE)
        r = {}
        if after:
            r.update(after(hwnd) or {})
        time.sleep(0.6)
        back = shared.setdefault("back", None) or shared.update(back=backing(x0, y0, W, H)) or shared["back"]
        u32.SetWindowPos(back, wt.HWND(1), x0, y0, W, H, SWP_NOACTIVATE | SWP_SHOWWINDOW)      # HWND_BOTTOM
        r["raise_ok"] = bool(u32.SetWindowPos(hwnd, wt.HWND(-1), x0, y0, W, H, SWP_NOACTIVATE | SWP_SHOWWINDOW))  # topmost
        time.sleep(0.8)
        im, ok = print_window(hwnd)
        im.save(OUT.with_name(f"spike-window-{name}.png"))
        r["print_window_ok"] = ok
        r["size"] = im.size
        r["paint"] = corner_report(im, name)
        ex = u32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        key, alpha, flags = wt.COLORREF(), ctypes.c_ubyte(), wt.DWORD()
        got = u32.GetLayeredWindowAttributes(hwnd, ctypes.byref(key), ctypes.byref(alpha), ctypes.byref(flags))
        r["layered"] = {"ex_layered": bool(ex & WS_EX_LAYERED), "attrs_ok": bool(got), "colorkey_bgr": hex(key.value),
                        "flags": flags.value}
        sc = screen_copy(x0, y0, W, H)
        sc.save(OUT.with_name(f"spike-window-{name}-screen.png"))
        r["screen_copy_corner"] = sc.getpixel((1, 1))[:3]
        r["screen_copy_centre"] = sc.getpixel((W // 2, H // 2))[:3]
        pt = wt.POINT(x0 + 2, y0 + 2)
        top = u32.GetAncestor(u32.WindowFromPoint(pt), 2)
        r["hit_test_corner_is_this_window"] = int(top or 0) == hwnd
        r["hit_test_corner_is_backing"] = int(top or 0) == int(back)
        pt = wt.POINT(x0 + W // 2, y0 + H // 2)
        top = u32.GetAncestor(u32.WindowFromPoint(pt), 2)
        r["hit_test_centre_is_this_window"] = int(top or 0) == hwnd
        order = []

        @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
        def each(h_, _):
            cls = ctypes.create_unicode_buffer(80)
            u32.GetClassNameW(h_, cls, 80)
            if u32.IsWindowVisible(h_):
                order.append((int(h_), cls.value, rect_of(h_)))
            return True
        u32.EnumWindows(each, 0)
        r["z_order_front_first"] = [f"{c} {rc}" + (" <- test" if h_ == hwnd else " <- backing" if h_ == int(back) else "")
                                    for h_, c, rc in order][:8]
        hit = u32.WindowFromPoint(wt.POINT(x0 + W // 2, y0 + H // 2))
        cls = ctypes.create_unicode_buffer(80)
        u32.GetClassNameW(hit, cls, 80)
        r["hit_centre_class"] = cls.value
        r["visible"] = bool(u32.IsWindowVisible(hwnd))
        r["style_hex"] = hex(u32.GetWindowLongPtrW(hwnd, -16) & 0xffffffff)
        r["exstyle_hex"] = hex(u32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE) & 0xffffffff)
        r["children"] = []

        @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
        def kid(c, _):
            cls = ctypes.create_unicode_buffer(80)
            u32.GetClassNameW(c, cls, 80)
            r["children"].append(f"{cls.value} vis={bool(u32.IsWindowVisible(c))} {rect_of(c)}")
            return True
        u32.EnumChildWindows(hwnd, kid, 0)
        results[name] = r
        win.destroy()
        time.sleep(0.8)

    def key_it(color_bgr):
        def f(hwnd):
            ex = u32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
            u32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, ex | WS_EX_LAYERED)
            ok = u32.SetLayeredWindowAttributes(hwnd, color_bgr, 0, LWA_COLORKEY)
            return {"set_layered_ok": bool(ok)}
        return f

    def region(hwnd):
        x, y, w, h = rect_of(hwnd)
        rgn = g32.CreateRoundRectRgn(14, 14, w - 14, h - 14, 2 * R, 2 * R)
        return {"region_ok": bool(u32.SetWindowRgn(hwnd, rgn, True))}

    def run():
        try:
            variant("A-pywebview-transparent", {"transparent": True}, page("transparent", PILL, EDGE))
            variant("B-colorkey-black", {"background_color": "#010203"}, page("#010203", PILL, EDGE),
                    key_it(0x030201))
            # key picked near the edge colour so the blended pixels look like the edge, not like a halo
            kc = "#cdb4fe"
            variant("C-colorkey-edge-tone", {"background_color": kc}, page(kc, PILL, EDGE),
                    key_it(int(kc[5:7], 16) << 16 | int(kc[3:5], 16) << 8 | int(kc[1:3], 16)))
            variant("D-region", {"background_color": "#ff00ff"}, page("#ff00ff", PILL, EDGE), region)
            results["screen_is_composed"] = None
        except Exception as exc:
            results["error"] = repr(exc)
        OUT.write_text(json.dumps(results, indent=1, default=str), encoding="utf-8")
        for w in list(webview.windows):
            try:
                w.destroy()
            except Exception:
                pass

    anchor = webview.create_window("anchor", html="<html></html>", hidden=True, width=200, height=100)
    webview.start(run, gui="edgechromium", private_mode=True)


if __name__ == "__main__":
    main()
