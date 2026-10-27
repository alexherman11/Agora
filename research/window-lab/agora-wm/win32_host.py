"""Official Win32 boundary. Construction is read-only unless explicitly armed.
Never reads window text. All mutations require an identity-bearing WindowRef.
"""
import ctypes as C
from ctypes import wintypes as W
from dataclasses import dataclass
from pathlib import Path
import queue
import threading
import time

from engine import Rect

u=C.WinDLL('user32',use_last_error=True);k=C.WinDLL('kernel32',use_last_error=True)
dwm=C.WinDLL('dwmapi',use_last_error=True);adv=C.WinDLL('advapi32',use_last_error=True)
shell=C.WinDLL('shell32',use_last_error=True)


def sig(lib,name,result,*args):
    f=getattr(lib,name);f.restype=result;f.argtypes=list(args);return f


ENUM=C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
HOOK=C.WINFUNCTYPE(None,W.HANDLE,W.DWORD,W.HWND,W.LONG,W.LONG,W.DWORD,W.DWORD)
sig(u,'EnumWindows',W.BOOL,ENUM,W.LPARAM)
sig(u,'GetWindowRect',W.BOOL,W.HWND,C.POINTER(W.RECT))
sig(u,'GetAncestor',W.HWND,W.HWND,W.UINT)
sig(u,'GetWindowThreadProcessId',W.DWORD,W.HWND,C.POINTER(W.DWORD))
sig(u,'GetClassNameW',C.c_int,W.HWND,W.LPWSTR,C.c_int)
sig(u,'GetWindowLongPtrW',C.c_ssize_t,W.HWND,C.c_int)
for name in ('IsWindow','IsWindowVisible','IsIconic','IsZoomed'):
    sig(u,name,W.BOOL,W.HWND)
sig(u,'GetForegroundWindow',W.HWND)
sig(u,'GetWindow',W.HWND,W.HWND,W.UINT)
sig(u,'MonitorFromPoint',W.HMONITOR,W.POINT,W.DWORD)
sig(u,'SetWindowPos',W.BOOL,W.HWND,W.HWND,C.c_int,C.c_int,C.c_int,C.c_int,W.UINT)
sig(u,'ShowWindowAsync',W.BOOL,W.HWND,C.c_int)
sig(u,'SetForegroundWindow',W.BOOL,W.HWND)
sig(u,'PostMessageW',W.BOOL,W.HWND,W.UINT,W.WPARAM,W.LPARAM)
sig(u,'SetWinEventHook',W.HANDLE,W.DWORD,W.DWORD,W.HMODULE,HOOK,W.DWORD,W.DWORD,W.DWORD)
sig(u,'UnhookWinEvent',W.BOOL,W.HANDLE)
sig(u,'PeekMessageW',W.BOOL,C.POINTER(W.MSG),W.HWND,W.UINT,W.UINT,W.UINT)
sig(u,'TranslateMessage',W.BOOL,C.POINTER(W.MSG))
sig(u,'DispatchMessageW',C.c_ssize_t,C.POINTER(W.MSG))
sig(u,'SystemParametersInfoW',W.BOOL,W.UINT,W.UINT,C.c_void_p,W.UINT)
sig(u,'RegisterHotKey',W.BOOL,W.HWND,C.c_int,W.UINT,W.UINT)
sig(u,'UnregisterHotKey',W.BOOL,W.HWND,C.c_int)
sig(u,'SetPropW',W.BOOL,W.HWND,W.LPCWSTR,W.HANDLE)
sig(u,'GetPropW',W.HANDLE,W.HWND,W.LPCWSTR)
sig(u,'RemovePropW',W.HANDLE,W.HWND,W.LPCWSTR)
sig(k,'OpenProcess',W.HANDLE,W.DWORD,W.BOOL,W.DWORD)
sig(k,'CloseHandle',W.BOOL,W.HANDLE)
sig(k,'QueryFullProcessImageNameW',W.BOOL,W.HANDLE,W.DWORD,W.LPWSTR,C.POINTER(W.DWORD))
sig(k,'GetProcessTimes',W.BOOL,W.HANDLE,C.POINTER(W.FILETIME),C.POINTER(W.FILETIME),C.POINTER(W.FILETIME),C.POINTER(W.FILETIME))
sig(adv,'OpenProcessToken',W.BOOL,W.HANDLE,W.DWORD,C.POINTER(W.HANDLE))
sig(adv,'GetTokenInformation',W.BOOL,W.HANDLE,C.c_int,C.c_void_p,W.DWORD,C.POINTER(W.DWORD))
sig(dwm,'DwmGetWindowAttribute',C.c_long,W.HWND,W.DWORD,C.c_void_p,W.DWORD)
sig(dwm,'DwmSetWindowAttribute',C.c_long,W.HWND,W.DWORD,C.c_void_p,W.DWORD)
sig(shell,'SHQueryUserNotificationState',C.c_long,C.POINTER(C.c_int))


class Placement(C.Structure):
    _fields_=[('length',W.UINT),('flags',W.UINT),('showCmd',W.UINT),('ptMinPosition',W.POINT),
        ('ptMaxPosition',W.POINT),('rcNormalPosition',W.RECT)]


sig(u,'GetWindowPlacement',W.BOOL,W.HWND,C.POINTER(Placement))
sig(u,'SetWindowPlacement',W.BOOL,W.HWND,C.POINTER(Placement))


def dpi_aware():
    sig(u,'SetProcessDpiAwarenessContext',W.BOOL,C.c_void_p)
    u.SetProcessDpiAwarenessContext(C.c_void_p(-4))


def identity(pid):
    h=k.OpenProcess(0x1000,False,pid)
    if not h:return None
    try:
        times=[W.FILETIME() for _ in range(4)];buf=C.create_unicode_buffer(32768);size=W.DWORD(len(buf))
        if not k.GetProcessTimes(h,*(C.byref(t) for t in times)):return None
        if not k.QueryFullProcessImageNameW(h,0,buf,C.byref(size)):return None
        return {'pid':int(pid),'created':(times[0].dwHighDateTime<<32)|times[0].dwLowDateTime,'exe':buf.value}
    finally:k.CloseHandle(h)


def elevated(pid):
    h=k.OpenProcess(0x1000,False,pid)
    if not h:return True
    token=W.HANDLE()
    try:
        if not adv.OpenProcessToken(h,8,C.byref(token)):return True
        value=W.DWORD();size=W.DWORD()
        if not adv.GetTokenInformation(token,20,C.byref(value),C.sizeof(value),C.byref(size)):return True
        return bool(value.value)
    finally:
        if token: k.CloseHandle(token)
        k.CloseHandle(h)


@dataclass(frozen=True)
class WindowRef:
    hwnd: int
    process: dict
    thread: int
    cls: str

    @property
    def key(self):return f'{self.process["pid"]}:{self.process["created"]}:{self.hwnd}'
    def record(self):return {'hwnd':self.hwnd,'process':self.process,'thread':self.thread,'cls':self.cls}


def reference(hwnd):
    pid=W.DWORD();thread=u.GetWindowThreadProcessId(hwnd,C.byref(pid))
    rec=identity(pid.value);cls=C.create_unicode_buffer(256)
    u.GetClassNameW(hwnd,cls,len(cls))
    return WindowRef(int(hwnd),rec,int(thread),cls.value) if rec else None


def same(ref):
    now=reference(ref.hwnd)
    return now==ref


def rect(hwnd,frame=True):
    r=W.RECT()
    if not u.GetWindowRect(hwnd,C.byref(r)):raise OSError(C.get_last_error(),'GetWindowRect')
    if frame:
        ext=W.RECT()
        if dwm.DwmGetWindowAttribute(hwnd,9,C.byref(ext),C.sizeof(ext))==0 and ext.right>ext.left:r=ext
    return Rect(r.left,r.top,r.right-r.left,r.bottom-r.top)


def attribute(hwnd,attr):
    val=W.DWORD()
    hr=dwm.DwmGetWindowAttribute(hwnd,attr,C.byref(val),C.sizeof(val))
    return val.value if hr==0 else None


def dpi_scale():
    """Primary monitor's effective DPI / 96 (ran 26 Oct: 144 dpi, 1.5). Feel's pixel numbers are at 100 %."""
    try:
        x=C.c_uint();y=C.c_uint()
        if C.WinDLL('shcore').GetDpiForMonitor(u.MonitorFromPoint(W.POINT(0,0),1),0,C.byref(x),C.byref(y))==0 and x.value:
            return x.value/96
    except (OSError,AttributeError):pass
    try:return u.GetDpiForSystem()/96 or 1.0
    except (OSError,AttributeError):return 1.0


def work_area():
    r=W.RECT()
    if not u.SystemParametersInfoW(0x30,0,C.byref(r),0):raise OSError('work area unavailable')
    return Rect(r.left,r.top,r.right-r.left,r.bottom-r.top)


def gate():
    import sys
    path=str(Path(__file__).resolve().parent.parent/'kernel-desktop')
    if path not in sys.path:sys.path.insert(0,path)
    import gaming_gate
    reasons=gaming_gate.reasons();state=C.c_int()
    hr=shell.SHQueryUserNotificationState(C.byref(state))
    if hr!=0:reasons.append('notification state unavailable')
    elif state.value in (1,3,4,7):reasons.append(f'notification gate {state.value}')
    elif state.value==2 and _foreground_exe().lower() not in SHELL_OVERLAYS and _foreground_covers_monitor():
        # "Busy" alone is not a game: on 26 Oct Windows reported it with Claude (an ordinary window) in front while
        # Agora's own desktop layer and the Claude app's screen overlay were screen-sized. Gate only when the window
        # in front really covers its monitor.
        reasons.append('notification gate 2')
    return reasons


class _MONITORINFO(C.Structure):
    _fields_=[('cbSize',W.DWORD),('rcMonitor',W.RECT),('rcWork',W.RECT),('dwFlags',W.DWORD)]


u.MonitorFromWindow.restype=W.HMONITOR;u.MonitorFromWindow.argtypes=[W.HWND,W.DWORD]


def _foreground_covers_monitor():
    h=u.GetForegroundWindow()
    if not h:return False
    r=W.RECT();u.GetWindowRect(h,C.byref(r))
    mi=_MONITORINFO();mi.cbSize=C.sizeof(_MONITORINFO)
    if not u.GetMonitorInfoW(u.MonitorFromWindow(h,2),C.byref(mi)):return True   # unknown: stay careful
    m=mi.rcMonitor
    return r.left<=m.left and r.top<=m.top and r.right>=m.right and r.bottom>=m.bottom


# Screen-sized shell windows that make Windows report "busy" (QUNS 2) with no full-screen program running.
# Seen 26 Oct 2026: TextInputHost.exe (touch keyboard / emoji panel) held the foreground at 3840x2160.
SHELL_OVERLAYS={'textinputhost.exe','nvidia overlay.exe','explorer.exe','shellexperiencehost.exe',
                'startmenuexperiencehost.exe','searchhost.exe','lockapp.exe'}


def _foreground_exe():
    import os
    h=u.GetForegroundWindow()
    if not h:return ''
    pid=W.DWORD();u.GetWindowThreadProcessId(h,C.byref(pid))
    hp=k.OpenProcess(0x1000,False,pid.value)
    if not hp:return ''
    try:
        buf=C.create_unicode_buffer(512);n=W.DWORD(512)
        return os.path.basename(buf.value) if k.QueryFullProcessImageNameW(hp,0,buf,C.byref(n)) else ''
    finally:k.CloseHandle(hp)


class Native:
    def __init__(self,mutating=False,allowed=None,rules=None):
        self.mutating=mutating;self.allowed=set(allowed) if allowed is not None else None
        self.rules=rules or {}

    def check(self,ref):
        if not self.mutating:raise PermissionError('read-only native boundary')
        if self.allowed is not None and ref.hwnd not in self.allowed:raise PermissionError('outside sandbox allowlist')
        if not same(ref) or elevated(ref.process['pid']):raise PermissionError('identity changed or elevated')

    def windows(self):
        rows=[];front=u.GetForegroundWindow()
        def each(hwnd,_):
            if not u.IsWindowVisible(hwnd) or u.GetAncestor(hwnd,2)!=hwnd:return True
            style=u.GetWindowLongPtrW(hwnd,-16);ex=u.GetWindowLongPtrW(hwnd,-20)
            if style&0x40000000 or ex&0x80 or ex&0x08000000:return True
            if attribute(hwnd,14):return True  # cloaked
            ref=reference(hwnd)
            if not ref or ref.cls in ('Progman','WorkerW','Shell_TrayWnd','Shell_SecondaryTrayWnd'):return True
            app=Path(ref.process['exe']).stem
            from native_identity import agora_id
            agora=agora_id(hwnd)
            if agora:app='Agora'
            rule=self.rules.get(app.lower(),{})
            try:r=rect(hwnd)
            except OSError:return True
            if r.w<=0 or r.h<=0:return True
            why=''
            if rule.get('ignore'):why='app rule: leave alone'
            elif elevated(ref.process['pid']):why='elevated or inaccessible'
            elif not style&0x00C00000 and not rule.get('manage') and not agora:why='frameless; no app rule'
            owned=bool(u.GetWindow(hwnd,4))   # GW_OWNER: a dialog or popup belongs to its owner, not the layout
            if not why and owned:why='owned dialog or popup'
            preferred=[r.w,r.h]
            if u.IsIconic(hwnd):
                try:
                    normal=self.placement(ref)['normal'];preferred=[normal[2]-normal[0],normal[3]-normal[1]]
                except OSError:pass
            rows.append({'key':ref.key,'app':app,'exe':ref.process['exe'],'icon':ref.process['exe'],
                'agora':agora,'state':'minimised' if u.IsIconic(hwnd) else 'normal','focused':hwnd==front,
                'rect':r.values(),'space':'primary','managed':not why,'why':why,'ref':ref,'_preferred':preferred,
                'owned':owned,'maximised':bool(u.IsZoomed(hwnd)) and not u.IsIconic(hwnd)})
            return True
        callback=ENUM(each);u.EnumWindows(callback,0)
        return rows

    def scale(self):return dpi_scale()

    def rect_of(self,ref):
        """One window's visible rectangle, for the 60 Hz drag path (no enumeration). Read-only."""
        return rect(ref.hwnd)

    def placement(self,ref):
        p=Placement();p.length=C.sizeof(p)
        if not u.GetWindowPlacement(ref.hwnd,C.byref(p)):raise OSError('GetWindowPlacement')
        return {'flags':p.flags,'show':p.showCmd,'min':[p.ptMinPosition.x,p.ptMinPosition.y],
            'max':[p.ptMaxPosition.x,p.ptMaxPosition.y],
            'normal':[p.rcNormalPosition.left,p.rcNormalPosition.top,p.rcNormalPosition.right,p.rcNormalPosition.bottom]}

    def restore_placement(self,ref,data):
        self.check(ref);p=Placement();p.length=C.sizeof(p)
        # Put back where it was, never whether it was minimised: the window keeps the state it has now. (Live, 26 Oct:
        # leases taken while windows were minimised by someone else re-minimised every window on a restart.)
        show=7 if u.IsIconic(ref.hwnd) else 3 if u.IsZoomed(ref.hwnd) else 4
        p.flags=data['flags']|4;p.showCmd=show;p.ptMinPosition=W.POINT(*data['min'])
        p.ptMaxPosition=W.POINT(*data['max']);p.rcNormalPosition=W.RECT(*data['normal'])
        if not u.SetWindowPlacement(ref.hwnd,C.byref(p)):raise OSError('SetWindowPlacement')

    def place(self,ref,target):
        self.check(ref);outer=rect(ref.hwnd,False);frame=rect(ref.hwnd)
        left,top=frame.x-outer.x,frame.y-outer.y
        right,bottom=outer.right-frame.right,outer.bottom-frame.bottom
        if not u.SetWindowPos(ref.hwnd,None,target.x-left,target.y-top,target.w+left+right,target.h+top+bottom,
                0x4000|0x4|0x10|0x200):raise OSError(C.get_last_error(),'SetWindowPos')

    def needs_restore(self,ref):return bool(u.IsIconic(ref.hwnd) or u.IsZoomed(ref.hwnd))

    def minimise(self,ref):self.check(ref);u.ShowWindowAsync(ref.hwnd,7)
    def restore(self,ref):self.check(ref);u.ShowWindowAsync(ref.hwnd,4)
    def focus(self,ref):self.check(ref);return bool(u.SetForegroundWindow(ref.hwnd))
    def close(self,ref):self.check(ref);return bool(u.PostMessageW(ref.hwnd,0x10,0,0))

    def style(self,ref,color=None,corner=None):
        self.check(ref);results={}
        for attr,value in ((34,color),(33,corner)):
            if value is None:continue
            val=W.DWORD(value);results[attr]=int(dwm.DwmSetWindowAttribute(ref.hwnd,attr,C.byref(val),C.sizeof(val)))
        return results


EVENTS={3:'focus',10:'drag-start',11:'drag-end',22:'minimise',23:'restore',
    0x8000:'open',0x8001:'close',0x8002:'show',0x8003:'hide',0x800B:'location'}


class EventFeed:
    def __init__(self,pid=0):
        self.events=queue.Queue(maxsize=4096);self.dropped=0;self.pid=pid;self.hooks=[]
        self.callback=HOOK(self._receive)

    def _receive(self,hook,event,hwnd,obj,child,thread,stamp):
        if not hwnd or event not in EVENTS or (event>=0x8000 and (obj!=0 or child!=0)):return
        try:self.events.put_nowait({'type':EVENTS[event],'hwnd':int(hwnd),'stamp':int(stamp)})
        except queue.Full:self.dropped+=1

    def start(self):
        # Called/pumped on the same thread, bound to its desktop. No injection.
        for lo,hi in ((3,3),(10,11),(22,23),(0x8000,0x8003),(0x800B,0x800B)):
            h=u.SetWinEventHook(lo,hi,None,self.callback,self.pid,0,0)
            if not h:self.close();raise OSError(C.get_last_error(),'SetWinEventHook')
            self.hooks.append(h)
        return self

    def drain(self):
        msg=W.MSG()
        while u.PeekMessageW(C.byref(msg),None,0,0,1):
            u.TranslateMessage(C.byref(msg));u.DispatchMessageW(C.byref(msg))
        events=[]
        while True:
            try:events.append(self.events.get_nowait())
            except queue.Empty:return events

    def close(self):
        for h in self.hooks:u.UnhookWinEvent(h)
        self.hooks=[]


def hotkey_probe():
    """Momentary registration only; never sends input. Releases on this thread."""
    ok=bool(u.RegisterHotKey(None,0x4A71,0x4003,8));error=0 if ok else C.get_last_error()
    if ok:u.UnregisterHotKey(None,0x4A71)
    return {'free':ok,'error':error}
