"""Read-only ownership/cloaking evidence for the named board rectangles."""
import json
from ctypes import wintypes as W
import ctypes
from capture_live import u,ENUM
from painter.install import taskboard

u.GetWindowThreadProcessId.argtypes=[W.HWND,ctypes.POINTER(W.DWORD)]
u.GetClassNameW.argtypes=[W.HWND,W.LPWSTR,ctypes.c_int]
dwm=ctypes.WinDLL('dwmapi');dwm.DwmGetWindowAttribute.argtypes=[W.HWND,W.DWORD,ctypes.c_void_p,W.DWORD]
def info(h):
    pid=W.DWORD();u.GetWindowThreadProcessId(h,ctypes.byref(pid));name=ctypes.create_unicode_buffer(200);u.GetClassNameW(h,name,200)
    cloaked=W.DWORD();hr=dwm.DwmGetWindowAttribute(h,14,ctypes.byref(cloaked),ctypes.sizeof(cloaked))
    return dict(hwnd=h,pid=pid.value,cls=name.value,cloaked=cloaked.value if hr==0 else None)
d=taskboard.live_door();rows=d.request('/see',dict(line='window.list'))['rows'];wanted={tuple(r['box']):r['shows'] for r in rows if r.get('shows') in ('taskboard','taskboard-js','taskboard-components') and r.get('box')}
out=[]
def each(h,_):
    if not u.IsWindowVisible(h):return True
    r=W.RECT();u.GetWindowRect(h,ctypes.byref(r));box=(r.left,r.top,r.right-r.left,r.bottom-r.top)
    if box in wanted:
        x,y,w,hi=box;points=[]
        for rx,ry in ((.1,.1),(.5,.5),(.9,.9)):
            root=u.GetAncestor(u.WindowFromPoint(W.POINT(x+int(w*rx),y+int(hi*ry))),2)
            points.append(info(root))
        out.append(dict(board=wanted[box],window=info(h),hits=points))
    return True
u.EnumWindows(ENUM(each),0)
print(json.dumps(out),flush=True)
