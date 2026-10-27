"""Agora-owned translucent previews. Click-through, tool, no activation.
All calls must occur on one UI thread. No target application is touched.

During a drag: one box per neighbour that is giving way (where it will go), and a fainter box where the dragged
window will land (the snap and the resistance, shown before you let go). See WM.md, "Feel".
"""
import ctypes as C
from ctypes import wintypes as W
from win32_host import u,k,sig

sig(u,'CreateWindowExW',W.HWND,W.DWORD,W.LPCWSTR,W.LPCWSTR,W.DWORD,C.c_int,C.c_int,C.c_int,C.c_int,
    W.HWND,W.HMENU,W.HINSTANCE,C.c_void_p)
sig(u,'DestroyWindow',W.BOOL,W.HWND)
sig(u,'SetLayeredWindowAttributes',W.BOOL,W.HWND,W.COLORREF,W.BYTE,W.DWORD)

NEIGHBOUR_ALPHA=70     # of 255: a neighbour's destination
LANDING_ALPHA=40       # fainter: where the dragged window will land


def _make(alpha):
    # STATIC class owns its paint; translucent solid preview, no hooks/input.
    # WS_EX_LAYERED|WS_EX_TRANSPARENT|WS_EX_TOOLWINDOW|WS_EX_NOACTIVATE; WS_POPUP|SS_BLACKRECT (a solid dark box).
    hwnd=u.CreateWindowExW(0x80000|0x20|0x80|0x08000000,'STATIC','',0x80000000|0x00000004,
        0,0,1,1,None,None,None,None)
    if not hwnd:raise OSError('ghost CreateWindowExW')
    u.SetLayeredWindowAttributes(hwnd,0,alpha,2)
    return hwnd


class Ghost:
    def __init__(self):self.handles=[];self.landing=None;self.shown={}

    def _place(self,hwnd,r):
        if self.shown.get(hwnd)==r:return          # unchanged: no call, no compositor work
        # HWND_TOPMOST; SWP_NOACTIVATE|SWP_SHOWWINDOW|SWP_ASYNCWINDOWPOS
        u.SetWindowPos(hwnd,W.HWND(-1),r.x,r.y,r.w,r.h,0x10|0x40|0x4000);self.shown[hwnd]=r

    def _hide(self,hwnd):
        if self.shown.get(hwnd) is None:return
        u.ShowWindowAsync(hwnd,0);self.shown[hwnd]=None

    def update(self,rects,landing=None):
        while len(self.handles)<len(rects):self.handles.append(_make(NEIGHBOUR_ALPHA))
        for i,hwnd in enumerate(self.handles):
            if i<len(rects):self._place(hwnd,rects[i])
            else:self._hide(hwnd)
        if landing is not None:
            if not self.landing:self.landing=_make(LANDING_ALPHA)
            self._place(self.landing,landing)
        elif self.landing:self._hide(self.landing)

    def clear(self):
        for hwnd in self.handles+([self.landing] if self.landing else []):self._hide(hwnd)

    def close(self):
        for hwnd in self.handles+([self.landing] if self.landing else []):u.DestroyWindow(hwnd)
        self.handles=[];self.landing=None;self.shown={}
