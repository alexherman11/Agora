"""Leave the NVIDIA performance strip inside Agora's top bar.

NVIDIA's CEF windows cover the entire monitor, including transparent pixels.
Never move/resize them or change their settings. Only lower our own top bar
behind these specific topmost surfaces and leave space for the compact strip.
"""
import ctypes as C
from ctypes import wintypes as W
from pathlib import Path

WIDTH_CSS, HEIGHT_CSS = 520, 52


def surfaces(bar_hwnd):
    """Visible, topmost NVIDIA CEF surfaces covering this bar, in Z order."""
    import native_shell
    u = C.WinDLL('user32', use_last_error=True)
    u.GetWindowRect.argtypes = [W.HWND, C.POINTER(W.RECT)]
    u.IsWindowVisible.argtypes = [W.HWND]
    u.GetClassNameW.argtypes = [W.HWND, W.LPWSTR, C.c_int]
    u.GetWindowLongPtrW.argtypes = [W.HWND, C.c_int]
    u.GetWindowLongPtrW.restype = C.c_ssize_t
    bar = W.RECT()
    if not u.GetWindowRect(bar_hwnd, C.byref(bar)):
        return []
    found = []
    proc = C.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)

    @proc
    def each(hwnd, _):
        if hwnd == bar_hwnd or not u.IsWindowVisible(hwnd):
            return True
        cls = C.create_unicode_buffer(128)
        u.GetClassNameW(hwnd, cls, len(cls))
        if cls.value != 'CEF-OSC-WIDGET' or not u.GetWindowLongPtrW(hwnd, -20) & 8:
            return True
        rect = W.RECT()
        if not u.GetWindowRect(hwnd, C.byref(rect)):
            return True
        if not (rect.left <= bar.left and rect.top <= bar.top
                and rect.right >= bar.right and rect.bottom >= bar.bottom):
            return True
        if Path(native_shell.program_path(hwnd)).name.lower() == 'nvidia overlay.exe':
            found.append(hwnd)
        return True

    u.EnumWindows.argtypes = [proc, W.LPARAM]
    u.EnumWindows(each, 0)
    return found


def accommodate(bar_hwnd):
    """Change only our bar's Z order. Return the CSS space its page must leave."""
    overlays = surfaces(bar_hwnd)
    if not overlays:
        return {}
    u = C.WinDLL('user32', use_last_error=True)
    u.SetWindowPos.argtypes = [W.HWND, W.HWND, C.c_int, C.c_int, C.c_int, C.c_int, W.UINT]
    # Last matching surface is the lowest in Z order: both NVIDIA surfaces stay
    # above us. No focus, visibility, size, position or other window is changed.
    if not u.SetWindowPos(bar_hwnd, overlays[-1], 0, 0, 0, 0, 0x1 | 0x2 | 0x10):
        return {}
    return dict(width=WIDTH_CSS, height=HEIGHT_CSS)
