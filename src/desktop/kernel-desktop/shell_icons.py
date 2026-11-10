"""EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
(people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.

shell_icons: real colour icons with alpha for the dock and the bars (shell builder, 26 Oct 2026).

Today's native_shell.executable_icon is 32 px on an opaque warm-white square (SHGetFileInfo + DrawIconEx). This is its
replacement: PNG with alpha at 64 px and up (the dock asks for 128 at 150%), cached on disk by exe, size and the exe's
modification time. A reference is a short string, so a row can carry it and a page can ask for it:

    exe:<path>        an executable, shortcut or any file the shell can draw: IShellItemImageFactory (SIIGBF_ICONONLY),
                      the same call Explorer makes; the fallback is ExtractIconEx.
    hwnd:<handle>     the window's own icon: WM_GETICON (big, then small2, then small), then the class icon.
    pkg:<full name>   a packaged (UWP / MSIX) app: AppxManifest.xml -> VisualElements -> Square44x44Logo (or
                      Square150x150Logo), the largest scale / targetsize file, drawn on the manifest's BackgroundColor
                      plate if the logo is a white glyph on nothing.
    aumid:<id>        the same through shell:AppsFolder\\<id> (the tile Start draws).
    agora:<name>      one of Agora's own apps: pages/shell/apps/<name>.svg (colour SVG, no pixels here).

    png_for(ref, size) -> bytes | None          None: the page draws a letter on the theme's plate instead
    window_ref(hwnd) -> str                      the best reference for a window (packaged app first, then its exe)
    svg_for(name) -> bytes | None

Alpha. HICON pixels are recovered by drawing the icon twice (on black and on white) and solving for alpha and colour,
which is right for 32-bit alpha icons and for old mask-only ones alike. The shell factory returns premultiplied BGRA,
which is un-premultiplied here. Nothing is installed; only documented shell/user/gdi/kernel APIs; no hooks.
"""
import ctypes as C
import hashlib
import io
import os
import re
import threading
import xml.etree.ElementTree as ET
from ctypes import wintypes as W
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = Path(os.environ.get("AGORA_ICON_CACHE") or HERE / "state" / "icon-cache")
APPS = HERE / "pages" / "shell" / "apps"
SIZES = (64, 96, 128, 192, 256)

u, k, sh, g, ole = (C.WinDLL(n, use_last_error=True) for n in ("user32", "kernel32", "shell32", "gdi32", "ole32"))


class GUID(C.Structure):
    _fields_ = [("a", C.c_ulong), ("b", C.c_ushort), ("c", C.c_ushort), ("d", C.c_ubyte * 8)]


class SIZE(C.Structure):
    _fields_ = [("cx", C.c_long), ("cy", C.c_long)]


class BIH(C.Structure):
    _fields_ = [("size", W.DWORD), ("width", W.LONG), ("height", W.LONG), ("planes", W.WORD), ("bits", W.WORD),
                ("compression", W.DWORD), ("image", W.DWORD), ("xppm", W.LONG), ("yppm", W.LONG),
                ("used", W.DWORD), ("important", W.DWORD)]


class ICONINFO(C.Structure):
    _fields_ = [("icon", W.BOOL), ("hx", W.DWORD), ("hy", W.DWORD), ("mask", W.HBITMAP), ("color", W.HBITMAP)]


def _guid(text):
    out = GUID()
    ole.CLSIDFromString(text, C.byref(out))
    return out


IID_FACTORY = "{BCC18B79-BA16-442F-80C4-8A59C30C463B}"
g.CreateCompatibleDC.argtypes, g.CreateCompatibleDC.restype = [W.HDC], W.HDC
g.CreateDIBSection.argtypes = [W.HDC, C.c_void_p, W.UINT, C.POINTER(C.c_void_p), W.HANDLE, W.DWORD]
g.CreateDIBSection.restype = W.HBITMAP
g.SelectObject.argtypes, g.SelectObject.restype = [W.HDC, W.HANDLE], W.HANDLE
g.DeleteObject.argtypes = [W.HANDLE]
g.DeleteDC.argtypes = [W.HDC]
g.GetDIBits.argtypes = [W.HDC, W.HBITMAP, W.UINT, W.UINT, C.c_void_p, C.c_void_p, W.UINT]
g.GetObjectW.argtypes = [W.HANDLE, C.c_int, C.c_void_p]
u.DrawIconEx.argtypes = [W.HDC, C.c_int, C.c_int, W.HICON, C.c_int, C.c_int, W.UINT, W.HBRUSH, W.UINT]
u.DestroyIcon.argtypes = [W.HICON]
u.GetIconInfo.argtypes = [W.HICON, C.POINTER(ICONINFO)]
u.SendMessageTimeoutW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM, W.UINT, W.UINT, C.POINTER(C.c_size_t)]
u.SendMessageTimeoutW.restype = C.c_ssize_t
u.GetClassLongPtrW.argtypes, u.GetClassLongPtrW.restype = [W.HWND, C.c_int], C.c_size_t
u.GetDC.argtypes, u.GetDC.restype = [W.HWND], W.HDC
u.ReleaseDC.argtypes = [W.HWND, W.HDC]
u.GetWindowThreadProcessId.argtypes = [W.HWND, C.POINTER(W.DWORD)]
u.IsWindow.argtypes = [W.HWND]
u.GetClassNameW.argtypes = [W.HWND, W.LPWSTR, C.c_int]
sh.SHCreateItemFromParsingName.argtypes = [W.LPCWSTR, C.c_void_p, C.POINTER(GUID), C.POINTER(C.c_void_p)]
sh.SHCreateItemFromParsingName.restype = C.c_long
sh.ExtractIconExW.argtypes = [W.LPCWSTR, C.c_int, C.POINTER(W.HICON), C.POINTER(W.HICON), W.UINT]
sh.ExtractIconExW.restype = W.UINT
k.OpenProcess.argtypes, k.OpenProcess.restype = [W.DWORD, W.BOOL, W.DWORD], W.HANDLE
k.CloseHandle.argtypes = [W.HANDLE]
k.GetPackageFullName.argtypes = [W.HANDLE, C.POINTER(W.UINT), W.LPWSTR]
k.GetPackageFullName.restype = C.c_long
k.GetPackagePathByFullName.argtypes = [W.LPCWSTR, C.POINTER(W.UINT), W.LPWSTR]
k.GetPackagePathByFullName.restype = C.c_long
k.GetApplicationUserModelId.argtypes = [W.HANDLE, C.POINTER(W.UINT), W.LPWSTR]
k.GetApplicationUserModelId.restype = C.c_long
k.QueryFullProcessImageNameW.argtypes = [W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD)]

_tls = threading.local()
_mem = {}                       # hwnd and pkg references: transient, not worth the disk
_lock = threading.Lock()


def _com():
    if not getattr(_tls, "com", False):
        ole.CoInitializeEx(None, 2)          # apartment threaded; a server thread owns its own
        _tls.com = True


# ---------------------------------------------------------------- pixels
def _hbitmap_rgba(hbm):
    """A GDI bitmap (32-bit, premultiplied BGRA from the shell factory) -> a straight-alpha PIL image."""
    from PIL import Image
    class BITMAP(C.Structure):
        _fields_ = [("type", W.LONG), ("w", W.LONG), ("h", W.LONG), ("stride", W.LONG), ("planes", W.WORD),
                    ("bits", W.WORD), ("data", C.c_void_p)]
    bm = BITMAP()
    g.GetObjectW(hbm, C.sizeof(bm), C.byref(bm))
    w, h = bm.w, bm.h
    bi = BIH(size=C.sizeof(BIH), width=w, height=-h, planes=1, bits=32)
    buf = C.create_string_buffer(w * h * 4)
    dc = g.CreateCompatibleDC(None)
    try:
        g.GetDIBits(dc, hbm, 0, h, buf, C.byref(bi), 0)
    finally:
        g.DeleteDC(dc)
    raw = bytearray(buf.raw)
    has_alpha = any(raw[i] for i in range(3, len(raw), 4))
    if not has_alpha:                                  # a 24-bit-ish source: opaque
        for i in range(3, len(raw), 4):
            raw[i] = 255
    else:
        for i in range(0, len(raw), 4):                # un-premultiply
            a = raw[i + 3]
            if 0 < a < 255:
                raw[i] = min(255, raw[i] * 255 // a)
                raw[i + 1] = min(255, raw[i + 1] * 255 // a)
                raw[i + 2] = min(255, raw[i + 2] * 255 // a)
    return Image.frombuffer("RGBA", (w, h), bytes(raw), "raw", "BGRA", 0, 1)


def _draw_on(hicon, n, fill):
    """DrawIconEx into an n x n 32-bit DIB filled with one grey level; -> bytes (BGRA)."""
    bi = BIH(size=C.sizeof(BIH), width=n, height=-n, planes=1, bits=32)
    pixels = C.c_void_p()
    dc = g.CreateCompatibleDC(None)
    bmp = g.CreateDIBSection(dc, C.byref(bi), 0, C.byref(pixels), None, 0)
    old = g.SelectObject(dc, bmp)
    try:
        C.memset(pixels, fill, n * n * 4)
        u.DrawIconEx(dc, 0, 0, hicon, n, n, 0, None, 3)         # DI_NORMAL
        return C.string_at(pixels, n * n * 4)
    finally:
        g.SelectObject(dc, old)
        g.DeleteObject(bmp)
        g.DeleteDC(dc)


def hicon_rgba(hicon, n):
    """An HICON at n x n with true alpha, by drawing on black and on white and solving for alpha and colour."""
    from PIL import Image
    black, white = _draw_on(hicon, n, 0), _draw_on(hicon, n, 255)
    out = bytearray(n * n * 4)
    for i in range(0, n * n * 4, 4):
        db = 255 - (white[i] - black[i])
        dg = 255 - (white[i + 1] - black[i + 1])
        dr = 255 - (white[i + 2] - black[i + 2])
        a = (db + dg + dr) // 3
        a = 0 if a < 0 else 255 if a > 255 else a
        if a:
            out[i] = min(255, black[i + 2] * 255 // a)          # R
            out[i + 1] = min(255, black[i + 1] * 255 // a)      # G
            out[i + 2] = min(255, black[i] * 255 // a)          # B
        out[i + 3] = a
    return Image.frombuffer("RGBA", (n, n), bytes(out), "raw", "RGBA", 0, 1)


def _icon_size_of(hicon):
    info = ICONINFO()
    if not u.GetIconInfo(hicon, C.byref(info)):
        return 0
    try:
        class BM(C.Structure):
            _fields_ = [("type", W.LONG), ("w", W.LONG), ("h", W.LONG), ("stride", W.LONG), ("planes", W.WORD),
                        ("bits", W.WORD), ("data", C.c_void_p)]
        bm = BM()
        g.GetObjectW(info.color or info.mask, C.sizeof(bm), C.byref(bm))
        return bm.w
    finally:
        if info.color:
            g.DeleteObject(info.color)
        if info.mask:
            g.DeleteObject(info.mask)


def _png(image, size):
    from PIL import Image
    if image.size != (size, size):
        image = image.resize((size, size), Image.LANCZOS)
    out = io.BytesIO()
    image.save(out, "PNG", optimize=True)
    return out.getvalue()


# ---------------------------------------------------------------- sources
def _factory_image(parsing_name, size):
    """IShellItemImageFactory::GetImage at size x size, icon only (no thumbnail), biggest-ok."""
    _com()
    iid, item = _guid(IID_FACTORY), C.c_void_p()
    if sh.SHCreateItemFromParsingName(parsing_name, None, C.byref(iid), C.byref(item)) != 0 or not item:
        return None
    vtbl = C.cast(item, C.POINTER(C.POINTER(C.c_void_p))).contents
    release = C.WINFUNCTYPE(C.c_ulong, C.c_void_p)(vtbl[2])
    get_image = C.WINFUNCTYPE(C.c_long, C.c_void_p, SIZE, W.UINT, C.POINTER(W.HBITMAP))(vtbl[3])
    hbm = W.HBITMAP()
    try:
        if get_image(item, SIZE(size, size), 0x1 | 0x4, C.byref(hbm)) != 0 or not hbm:     # BIGGERSIZEOK | ICONONLY
            return None
        try:
            return _hbitmap_rgba(hbm)
        finally:
            g.DeleteObject(hbm)
    finally:
        release(item)


def exe_icon(path, size):
    path = str(path)
    if not path or not os.path.exists(path):
        return None
    im = _factory_image(path, size)
    if im is not None and im.getbbox() is not None:
        return im
    big = W.HICON()
    if sh.ExtractIconExW(path, 0, C.byref(big), None, 1) and big:
        try:
            return hicon_rgba(big, max(size, 32))
        finally:
            u.DestroyIcon(big)
    return None


def hwnd_icon(hwnd, size):
    """The window's own icon: WM_GETICON (big, small2, small) then the class icon (GCL_HICON -14, GCL_HICONSM -34)."""
    hwnd = int(hwnd)
    if not u.IsWindow(hwnd):
        return None
    got = C.c_size_t()
    for which in (1, 2, 0):
        if u.SendMessageTimeoutW(hwnd, 0x7F, which, 0, 0x2, 120, C.byref(got)) and got.value:
            return hicon_rgba(got.value, 64 if _icon_size_of(got.value) < 64 else 128)    # owned by the window: never destroyed
    for idx in (-14, -34):
        h = u.GetClassLongPtrW(hwnd, idx)
        if h:
            return hicon_rgba(h, 64)
    return None


def _process_of(hwnd):
    pid = W.DWORD()
    u.GetWindowThreadProcessId(hwnd, C.byref(pid))
    return pid.value


def _package_of_pid(pid):
    h = k.OpenProcess(0x1000, False, pid)             # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return "", ""
    try:
        n = W.UINT(0)
        k.GetPackageFullName(h, C.byref(n), None)
        full = ""
        if n.value:
            buf = C.create_unicode_buffer(n.value)
            if k.GetPackageFullName(h, C.byref(n), buf) == 0:
                full = buf.value
        n = W.UINT(0)
        k.GetApplicationUserModelId(h, C.byref(n), None)
        aumid = ""
        if n.value:
            buf = C.create_unicode_buffer(n.value)
            if k.GetApplicationUserModelId(h, C.byref(n), buf) == 0:
                aumid = buf.value
        return full, aumid
    finally:
        k.CloseHandle(h)


def _exe_of_pid(pid):
    h = k.OpenProcess(0x1000, False, pid)
    if not h:
        return ""
    try:
        buf, n = C.create_unicode_buffer(32768), W.DWORD(32768)
        return buf.value if k.QueryFullProcessImageNameW(h, 0, buf, C.byref(n)) else ""
    finally:
        k.CloseHandle(h)


def _core_window_pid(hwnd):
    """A UWP window is hosted by ApplicationFrameHost; the app's own process owns the CoreWindow child."""
    found = []

    @C.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
    def each(c, _):
        cls = C.create_unicode_buffer(64)
        u.GetClassNameW(c, cls, 64)
        if cls.value == "Windows.UI.Core.CoreWindow":
            found.append(_process_of(c))
        return True
    u.EnumChildWindows.argtypes = [W.HWND, C.c_void_p, W.LPARAM]
    u.EnumChildWindows(hwnd, each, 0)
    return found[0] if found else 0


def window_ref(hwnd):
    """The best reference for one window. Packaged apps (their own process, or a CoreWindow behind
    ApplicationFrameHost) -> pkg:, otherwise exe:."""
    hwnd = int(hwnd)
    pid = _process_of(hwnd)
    exe = _exe_of_pid(pid)
    if exe.lower().endswith("applicationframehost.exe"):
        inner = _core_window_pid(hwnd)
        if inner:
            pid, exe = inner, _exe_of_pid(inner)
    full, _ = _package_of_pid(pid)
    if full:
        return "pkg:" + full
    return "exe:" + exe if exe else f"hwnd:{hwnd}"


def _hex(c):
    m = re.fullmatch(r"#([0-9a-fA-F]{6})", c or "")
    return tuple(int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4)) if m else None


def package_icon(full_name, size):
    """AppxManifest.xml -> VisualElements -> the logo file with the most pixels (targetsize or scale variants)."""
    from PIL import Image, ImageDraw
    n = W.UINT(0)
    k.GetPackagePathByFullName(full_name, C.byref(n), None)
    if not n.value:
        return None
    buf = C.create_unicode_buffer(n.value)
    if k.GetPackagePathByFullName(full_name, C.byref(n), buf) != 0:
        return None
    root = Path(buf.value)
    try:
        tree = ET.parse(root / "AppxManifest.xml")
    except (OSError, ET.ParseError):
        return None
    visual = next((e for e in tree.iter() if e.tag.endswith("}VisualElements") or e.tag == "VisualElements"), None)
    if visual is None:
        return None
    logo = visual.get("Square44x44Logo") or visual.get("Square150x150Logo") or visual.get("Logo")
    if not logo:
        return None
    rel = Path(logo.replace("\\", "/"))
    folder, stem = root / rel.parent, rel.stem
    candidates = [p for p in folder.glob(stem + "*.png")] if folder.is_dir() else []
    if not candidates:
        return None

    def score(p):
        name = p.name.lower()
        try:
            with Image.open(p) as im:
                px = im.size[0]
        except OSError:
            return (-1, 0)
        unplated = 1 if "altform-unplated" in name else 0
        light = 0 if "lightunplated" in name or "contrast" in name else 1
        return (px if px <= 512 else 0, unplated, light)
    best = max(candidates, key=lambda p: (score(p)[0], score(p)[1], score(p)[2]))
    im = Image.open(best).convert("RGBA")
    raw = im.tobytes()
    px = [(raw[i], raw[i + 1], raw[i + 2]) for i in range(0, len(raw), 4) if raw[i + 3] > 40]
    plate = _hex(visual.get("BackgroundColor"))
    if px:
        covered = len(px) / (im.size[0] * im.size[1])
        light = sum(1 for p in px if min(p) > 225) / len(px)
        dark = sum(1 for p in px if max(p) < 70) / len(px)
        fill = None
        if light > 0.6 and covered < 0.7:                   # a white glyph on nothing: it expects its plate
            fill = plate or (60, 64, 80)
        elif dark > 0.8 and covered < 0.7:                  # a black glyph on nothing: it expects a light page
            fill = (244, 244, 247)
        if fill:
            s = max(im.size)
            base = Image.new("RGBA", (s, s), (0, 0, 0, 0))
            ImageDraw.Draw(base).rounded_rectangle((0, 0, s - 1, s - 1), radius=s // 5, fill=fill + (255,))
            inner = im.resize((int(s * .66), int(s * .66)), Image.LANCZOS)
            base.alpha_composite(inner, ((s - inner.size[0]) // 2, (s - inner.size[1]) // 2))
            im = base
    return im


def aumid_icon(aumid, size):
    return _factory_image("shell:AppsFolder\\" + aumid, size)


# ---------------------------------------------------------------- the front door
def _stamp(ref):
    kind, _, rest = ref.partition(":")
    if kind == "exe":
        try:
            st = os.stat(rest)
            return f"{rest.lower()}|{st.st_mtime_ns}|{st.st_size}"
        except OSError:
            return rest.lower()
    return ref


def svg_for(name):
    name = re.sub(r"[^a-z0-9-]", "", str(name).lower())
    p = APPS / f"{name}.svg"
    return p.read_bytes() if p.is_file() else None


def png_for(ref, size=128):
    """-> PNG bytes with alpha at size (64..256), or None. exe, pkg and aumid references are cached on disk."""
    try:
        size = int(size or 128)
    except (TypeError, ValueError):
        size = 128
    if size not in SIZES:
        size = min(SIZES, key=lambda s: abs(s - size))
    kind, _, rest = (ref or "").partition(":")
    if kind not in ("exe", "hwnd", "pkg", "aumid"):
        return None
    disk = kind != "hwnd"
    name = hashlib.sha1(f"{_stamp(ref)}|{size}".encode("utf-8", "replace")).hexdigest()[:24] + f"-{size}.png"
    f = CACHE / name
    if disk and f.is_file():
        return f.read_bytes()
    if kind == "hwnd" and (ref, size) in _mem:
        return _mem[(ref, size)]
    try:
        if kind == "exe":
            im = exe_icon(rest, size)
        elif kind == "hwnd":
            im = hwnd_icon(rest, size)
        elif kind == "pkg":
            im = package_icon(rest, size)
        else:
            im = aumid_icon(rest, size)
    except Exception:                       # noqa: BLE001  an icon is never worth a failed request
        im = None
    if im is None or im.getbbox() is None:
        return None
    data = _png(im, size)
    if disk:
        CACHE.mkdir(parents=True, exist_ok=True)
        tmp = f.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_bytes(data)
        os.replace(tmp, f)
    else:
        with _lock:
            if len(_mem) > 200:
                _mem.clear()
            _mem[(ref, size)] = data
    return data


def serve(ref, size=128):
    """What the desktop's /desk/icon route sends: (status, content-type, bytes)."""
    kind, _, rest = (ref or "").partition(":")
    if kind == "agora":
        data = svg_for(rest)
        return (200, "image/svg+xml", data) if data else (404, "text/plain", b"no such Agora icon")
    data = png_for(ref, size)
    return (200, "image/png", data) if data else (404, "text/plain", b"no icon")
