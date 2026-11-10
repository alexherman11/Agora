"""Spike 2 (shell builder, 26 Oct 2026): can Agora's own desktop layer sit under every app, by the WorkerW method?

Runs ON A HIDDEN DESKTOP (started by shell_proof.py through sandbox_window.py); nothing here reaches Alex's screen.

What it measures, as printed to the JSON file named by argv[1]:
  1. whether the hidden desktop has a shell at all: GetShellWindow, Progman, SHELLDLL_DefView, WorkerW. (A desktop made
     by CreateDesktop has no Explorer on it, so the Progman message 0x052C has nothing to be sent to.)
  2. the fallback, shell_native.make_layer(): a bottom-most tool window. Two plain windows A (the layer) and B (an app)
     are made; B is shown after A. Checked: A carries WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE and not WS_EX_APPWINDOW;
     after B is raised and A is "raised" by hand, the layer's keep-at-bottom loop puts A below B again within 1.5 s;
     A never became the foreground window.
"""
import ctypes
import json
import sys
import threading
import time
from ctypes import wintypes as wt
from pathlib import Path

OUT = Path(sys.argv[1])
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import shell_native as SN  # noqa: E402

u32, g32, k32 = SN.user32, SN.gdi32, ctypes.WinDLL("kernel32")
u32.GetForegroundWindow.restype = wt.HWND
u32.GetShellWindow.restype = wt.HWND
u32.GetWindow.restype = wt.HWND
u32.GetWindow.argtypes = [wt.HWND, wt.UINT]
u32.CreateWindowExW.restype = wt.HWND
u32.CreateWindowExW.argtypes = [wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, wt.HWND, wt.HMENU, wt.HINSTANCE, wt.LPVOID]
k32.GetModuleHandleW.restype = wt.HMODULE
k32.GetModuleHandleW.argtypes = [wt.LPCWSTR]
u32.RegisterClassW.argtypes = [ctypes.c_void_p]
u32.PeekMessageW.argtypes = [ctypes.c_void_p, wt.HWND, wt.UINT, wt.UINT, wt.UINT]
u32.TranslateMessage.argtypes = [ctypes.c_void_p]
u32.DispatchMessageW.argtypes = [ctypes.c_void_p]
g32.CreateSolidBrush.restype = wt.HBRUSH
g32.CreateSolidBrush.argtypes = [wt.COLORREF]


def make_window(cls, title, colour, x, y, w, h, ex=0):
    done = threading.Event()
    box = {}

    def run():
        WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)
        u32.DefWindowProcW.restype = ctypes.c_ssize_t
        u32.DefWindowProcW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
        proc = WNDPROC(lambda hh, m, wp, lp: u32.DefWindowProcW(hh, m, wp, lp))

        class WC(ctypes.Structure):
            _fields_ = [("style", wt.UINT), ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int),
                        ("hInstance", wt.HINSTANCE), ("hIcon", wt.HICON), ("hCursor", wt.HANDLE), ("hbrBackground", wt.HBRUSH),
                        ("lpszMenuName", wt.LPCWSTR), ("lpszClassName", wt.LPCWSTR)]
        wc = WC()
        wc.lpfnWndProc, wc.lpszClassName, wc.hInstance = proc, cls, k32.GetModuleHandleW(None)
        wc.hbrBackground = g32.CreateSolidBrush(colour)
        u32.RegisterClassW(ctypes.byref(wc))
        box["h"] = u32.CreateWindowExW(ex, cls, title, 0x90000000 | 0x00C00000, x, y, w, h, None, None, wc.hInstance, None)
        done.set()
        msg = wt.MSG()
        end = time.time() + 60
        while time.time() < end:
            while u32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                u32.TranslateMessage(ctypes.byref(msg))
                u32.DispatchMessageW(ctypes.byref(msg))
            time.sleep(0.02)
    threading.Thread(target=run, daemon=True).start()
    done.wait(5)
    return box["h"]


def z_names():
    out = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def each(h, _):
        t = ctypes.create_unicode_buffer(64)
        u32.GetWindowTextW(h, t, 64)
        if t.value in ("layer-A", "app-B") and u32.IsWindowVisible(h):
            out.append(t.value)
        return True
    u32.EnumWindows(each, 0)
    return out


def main():
    r = {}
    shell = u32.GetShellWindow()
    cls = ctypes.create_unicode_buffer(64)
    r["shell_window"] = int(shell or 0)
    r["progman"] = int(u32.FindWindowW("Progman", None) or 0)
    r["workerw"] = int(u32.FindWindowW("WorkerW", None) or 0)
    r["defview_anywhere"] = False

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def look(h, _):
        u32.GetClassNameW(h, cls, 64)
        if cls.value in ("SHELLDLL_DefView", "Progman", "WorkerW"):
            r["defview_anywhere"] = True
        return True
    u32.EnumWindows(look, 0)
    r["attach_workerw_result"] = SN.attach_workerw(0, (0, 0, 100, 100)) if r["progman"] else "not tried: there is no Progman on this desktop to send 0x052C to"
    # the fallback layer
    a = make_window("ShellSpikeLayer", "layer-A", 0x00FF0000, 100, 100, 600, 400)
    time.sleep(0.2)
    mode = SN.make_layer(a, (100, 100, 600, 400))
    b = make_window("ShellSpikeApp", "app-B", 0x0000FF00, 200, 200, 400, 300)
    time.sleep(0.3)
    u32.SetWindowPos(b, wt.HWND(0), 200, 200, 400, 300, SN.SWP_NOACTIVATE | SN.SWP_SHOWWINDOW)
    time.sleep(0.2)
    ex = u32.GetWindowLongPtrW(a, SN.GWL_EXSTYLE)
    r["layer_mode"] = mode
    r["layer_exstyle_toolwindow"] = bool(ex & SN.WS_EX_TOOLWINDOW)
    r["layer_exstyle_noactivate"] = bool(ex & SN.WS_EX_NOACTIVATE)
    r["layer_exstyle_appwindow"] = bool(ex & SN.WS_EX_APPWINDOW)
    r["z_front_first_initial"] = z_names()
    u32.SetWindowPos(a, wt.HWND(-1), 0, 0, 0, 0, SN.SWP_NOMOVE | SN.SWP_NOSIZE | SN.SWP_NOACTIVATE)      # something raised it (topmost)
    r["z_after_a_raise"] = z_names()
    time.sleep(1.6)
    r["z_after_keep_loop"] = z_names()
    r["layer_below_app_after_loop"] = r["z_after_keep_loop"][:2] == ["app-B", "layer-A"]
    r["layer_became_foreground"] = int(u32.GetForegroundWindow() or 0) == int(a)
    OUT.write_text(json.dumps(r, indent=1), encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        OUT.write_text(json.dumps({"error": repr(exc)}), encoding="utf-8")
