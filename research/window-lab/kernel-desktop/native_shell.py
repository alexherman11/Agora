"""Windows task buttons and executable icons. Momentary readings, never world facts.

Only documented shell/user APIs; no hooks or injection. Private DLL prototypes.
"""
import base64
import ctypes as C
from ctypes import wintypes as W
from functools import lru_cache
import os
from pathlib import Path
import struct
import zlib

import sysread as s

u, k, sh, g = (C.WinDLL(n) for n in ('user32', 'kernel32', 'shell32', 'gdi32'))
u.GetForegroundWindow.restype = W.HWND
u.ShowWindow.argtypes = [W.HWND, C.c_int]
u.SetForegroundWindow.argtypes = [W.HWND]
u.GetClassNameW.argtypes = [W.HWND, W.LPWSTR, C.c_int]


def program_path(hwnd):
    pid = W.DWORD()
    s._pid(hwnd, C.byref(pid))
    handle = s._open_process(0x1000, False, pid.value)
    if not handle:
        return ''
    try:
        buf, size = C.create_unicode_buffer(32768), W.DWORD(32768)
        return buf.value if s._image(handle, 0, buf, C.byref(size)) else ''
    finally:
        s._close(handle)


@lru_cache(maxsize=256)
def executable_icon(path):
    """SHGetFileInfo's executable icon, rendered into a 32-bit DIB; every GDI handle released."""
    if not path:
        return ''
    class INFO(C.Structure):
        _fields_ = [('icon', W.HICON), ('index', C.c_int), ('attributes', W.DWORD),
                    ('display', W.WCHAR * 260), ('type', W.WCHAR * 80)]
    class BITMAP(C.Structure):
        _fields_ = [('size', W.DWORD), ('width', W.LONG), ('height', W.LONG),
                    ('planes', W.WORD), ('bits', W.WORD), ('compression', W.DWORD),
                    ('image_size', W.DWORD), ('x', W.LONG), ('y', W.LONG),
                    ('used', W.DWORD), ('important', W.DWORD), ('colors', W.DWORD * 3)]
    sh.SHGetFileInfoW.argtypes = [W.LPCWSTR, W.DWORD, C.POINTER(INFO), W.UINT, W.UINT]
    sh.SHGetFileInfoW.restype = C.c_size_t
    g.CreateCompatibleDC.argtypes, g.CreateCompatibleDC.restype = [W.HDC], W.HDC
    g.CreateDIBSection.argtypes = [W.HDC, C.c_void_p, W.UINT, C.POINTER(C.c_void_p), W.HANDLE, W.DWORD]
    g.CreateDIBSection.restype = W.HBITMAP
    g.SelectObject.argtypes, g.SelectObject.restype = [W.HDC, W.HANDLE], W.HANDLE
    g.DeleteObject.argtypes = [W.HANDLE]
    g.DeleteDC.argtypes = [W.HDC]
    u.DestroyIcon.argtypes = [W.HICON]
    u.DrawIconEx.argtypes = [W.HDC, C.c_int, C.c_int, W.HICON, C.c_int, C.c_int, W.UINT, W.HBRUSH, W.UINT]
    info = INFO()
    if not sh.SHGetFileInfoW(path, 0, C.byref(info), C.sizeof(info), 0x100):
        return ''
    dc = bitmap = old = None
    try:
        dc = g.CreateCompatibleDC(None)
        b = BITMAP()
        b.size, b.width, b.height, b.planes, b.bits = 40, 32, -32, 1, 32
        pixels = C.c_void_p()
        bitmap = g.CreateDIBSection(dc, C.byref(b), 0, C.byref(pixels), None, 0)
        if not bitmap:
            return ''
        old = g.SelectObject(dc, bitmap)
        # Opaque warm white also handles legacy mask-only icons without lost black strokes.
        C.memset(pixels, 255, 32 * 32 * 4)
        u.DrawIconEx(dc, 0, 0, info.icon, 32, 32, 0, None, 3)
        raw = C.string_at(pixels, 4096)
        scanlines = bytearray()
        for y in range(32):
            scanlines.append(0)  # PNG filter: none
            for x in range(32):
                b, green, r, _ = raw[(y*32+x)*4:(y*32+x+1)*4]
                scanlines.extend((r, green, b, 255))
        def chunk(tag, value):
            return struct.pack('!I', len(value)) + tag + value + struct.pack('!I', zlib.crc32(tag+value))
        png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B',32,32,8,6,0,0,0))
        png += chunk(b'IDAT', zlib.compress(scanlines)) + chunk(b'IEND', b'')
        return 'data:image/png;base64,' + base64.b64encode(png).decode()
    finally:
        if old:
            g.SelectObject(dc, old)
        if bitmap:
            g.DeleteObject(bitmap)
        if dc:
            g.DeleteDC(dc)
        u.DestroyIcon(info.icon)


def windows(exclude=()):
    out = []
    foreground = u.GetForegroundWindow()
    @s._EnumProc
    def each(hwnd, _):
        if hwnd in exclude or not s._visible(hwnd) or s._owner(hwnd, 4) or s._style(hwnd, -20) & 0x80:
            return True
        cls = C.create_unicode_buffer(128)
        u.GetClassNameW(hwnd, cls, len(cls))
        if cls.value in ('Shell_TrayWnd', 'Shell_SecondaryTrayWnd', 'Progman', 'WorkerW'):
            return True
        title = s._title(hwnd).strip()
        cloak = W.DWORD()
        s._cloaked(hwnd, 14, C.byref(cloak), 4)
        if not title or cloak.value:
            return True
        path = program_path(hwnd)
        out.append(dict(handle=str(hwnd), name=title, program=Path(path).stem, path=path,
                        icon=executable_icon(path), front=hwnd == foreground,
                        shown=not bool(u.IsIconic(W.HWND(hwnd)))))
        return True
    s._enum(each, 0)
    return sorted(out, key=lambda r: int(r['handle']))


def activate(handle, exclude=()):
    row = next((r for r in windows(exclude) if r['handle'] == str(handle)), None)
    if not row:
        return False
    hwnd = int(handle)
    if row['front']:
        u.ShowWindow(hwnd, 6)
    else:
        u.ShowWindow(hwnd, 9)
        u.SetForegroundWindow(hwnd)
    return True


def start_menu():
    # Ctrl+Esc is the documented Start shortcut. SendInput, no system-wide hook.
    class KEY(C.Structure):
        _fields_ = [('vk', W.WORD), ('scan', W.WORD), ('flags', W.DWORD),
                    ('time', W.DWORD), ('extra', C.c_size_t)]
    class PAYLOAD(C.Union):
        _fields_ = [('key', KEY), ('padding', C.c_byte * (32 if C.sizeof(C.c_void_p) == 8 else 24))]
    class INPUT(C.Structure):
        _fields_ = [('type', W.DWORD), ('data', PAYLOAD)]
    seq = (INPUT * 4)()
    for item, (vk, flags) in zip(seq, ((0x11, 0), (0x1B, 0), (0x1B, 2), (0x11, 2))):
        item.type, item.data.key = 1, KEY(vk, 0, flags, 0, 0)
    return u.SendInput(4, seq, C.sizeof(INPUT)) == 4


def settings(which):
    uri = {'network': 'ms-settings:network-status', 'volume': 'ms-settings:sound',
           'battery': 'ms-settings:batterysaver', 'time': 'ms-settings:dateandtime'}.get(which)
    if not uri:
        return False
    os.startfile(uri)
    return True
