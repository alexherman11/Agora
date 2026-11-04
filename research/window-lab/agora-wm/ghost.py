"""EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
(people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.

Agora-owned translucent previews. Click-through, tool, no activation.
All calls must occur on one UI thread. No target application is touched.

During a drag: faint available spaces and a stronger box where the dragged
window will land. Real neighbours move through the manager's eased positions.
"""
import ctypes as C
from ctypes import wintypes as W
from win32_host import u,k,sig

sig(u,'CreateWindowExW',W.HWND,W.DWORD,W.LPCWSTR,W.LPCWSTR,W.DWORD,C.c_int,C.c_int,C.c_int,C.c_int,
    W.HWND,W.HMENU,W.HINSTANCE,C.c_void_p)
sig(u,'DestroyWindow',W.BOOL,W.HWND)
sig(u,'SetLayeredWindowAttributes',W.BOOL,W.HWND,W.COLORREF,W.BYTE,W.DWORD)

NEIGHBOUR_ALPHA=40     # of 255: available spaces (which can overlap)
LANDING_ALPHA=70       # selected landing stays legible over available spaces


def _make(alpha,selected=False):
    # STATIC class owns its paint; translucent solid preview, no hooks/input.
    # Available areas use system gray, selected glass lights up white.
    # WS_EX_LAYERED|WS_EX_TRANSPARENT|WS_EX_TOOLWINDOW|WS_EX_NOACTIVATE; WS_POPUP.
    hwnd=u.CreateWindowExW(0x80000|0x20|0x80|0x08000000,'STATIC','',0x80000000|(6 if selected else 5),
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
            if not self.landing:self.landing=_make(LANDING_ALPHA,selected=True)
            self._place(self.landing,landing)
        elif self.landing:self._hide(self.landing)

    def clear(self):
        for hwnd in self.handles+([self.landing] if self.landing else []):self._hide(hwnd)

    def close(self):
        for hwnd in self.handles+([self.landing] if self.landing else []):u.DestroyWindow(hwnd)
        self.handles=[];self.landing=None;self.shown={}
