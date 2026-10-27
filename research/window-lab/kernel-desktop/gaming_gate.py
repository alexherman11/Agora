"""Conservative desktop gate: game processes and full-screen foreground windows.
Read-only Win32 inspection; no titles, focus changes or input.
"""
import ctypes
from ctypes import wintypes as w

HELPERS = {'edgegameassist.exe','gamebarpresencewriter.exe','gameinputredistservice.exe','gameinputsvc.exe',
           'gameoverlayui.exe','gameoverlayui64.exe','gamebar.exe','gamebarftserver.exe'}
KNOWN = {'rocketleague.exe','fortniteclient-win64-shipping.exe','cs2.exe','dota2.exe','eldenring.exe',
         'helldivers2.exe','valorant-win64-shipping.exe','overwatch.exe','minecraft.exe'}
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
    try:
        more=k.Process32FirstW(h,ctypes.byref(p))
        while more:
            name=p.exe.lower()
            if name in KNOWN or ('game' in name and name not in HELPERS):
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
