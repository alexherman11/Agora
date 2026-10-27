"""Agora-owned translucent previews. Click-through, tool, no activation.
All calls must occur on one UI thread. No target application is touched.
"""
import ctypes as C
from ctypes import wintypes as W
from win32_host import u,k,sig

sig(u,'CreateWindowExW',W.HWND,W.DWORD,W.LPCWSTR,W.LPCWSTR,W.DWORD,C.c_int,C.c_int,C.c_int,C.c_int,
    W.HWND,W.HMENU,W.HINSTANCE,C.c_void_p)
sig(u,'DestroyWindow',W.BOOL,W.HWND)
sig(u,'SetLayeredWindowAttributes',W.BOOL,W.HWND,W.COLORREF,W.BYTE,W.DWORD)


class Ghost:
    def __init__(self):self.handles=[]
    def update(self,rects):
        while len(self.handles)<len(rects):
            # STATIC class owns its paint; translucent solid preview, no hooks/input.
            hwnd=u.CreateWindowExW(0x80000|0x20|0x80|0x08000000,'STATIC','',0x80000000|0x00000004,
                0,0,1,1,None,None,None,None)
            if not hwnd:raise OSError('ghost CreateWindowExW')
            u.SetLayeredWindowAttributes(hwnd,0,65,2);self.handles.append(hwnd)
        for i,hwnd in enumerate(self.handles):
            if i<len(rects):
                r=rects[i]
                u.SetWindowPos(hwnd,W.HWND(-1),r.x,r.y,r.w,r.h,0x10|0x40|0x4000)
            else:u.ShowWindowAsync(hwnd,0)
    def clear(self):
        for hwnd in self.handles:u.ShowWindowAsync(hwnd,0)
    def close(self):
        for hwnd in self.handles:u.DestroyWindow(hwnd)
        self.handles=[]
