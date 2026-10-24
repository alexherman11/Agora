"""Read only named board window pixels, without focus/input or whole-screen capture."""
import ctypes
from ctypes import wintypes as W
import json
from pathlib import Path
import sys
from PIL import Image

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from painter.process_gate import check
from painter.install import taskboard

u=ctypes.WinDLL('user32',use_last_error=True);g=ctypes.WinDLL('gdi32',use_last_error=True)
u.SetProcessDpiAwarenessContext.argtypes=[ctypes.c_void_p];u.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
ENUM=ctypes.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
u.EnumWindows.argtypes=[ENUM,W.LPARAM];u.GetWindowRect.argtypes=[W.HWND,ctypes.POINTER(W.RECT)]
u.GetWindowTextW.argtypes=[W.HWND,W.LPWSTR,ctypes.c_int];u.IsWindowVisible.argtypes=[W.HWND]
u.WindowFromPoint.argtypes=[W.POINT];u.WindowFromPoint.restype=W.HWND
u.GetAncestor.argtypes=[W.HWND,W.UINT];u.GetAncestor.restype=W.HWND
u.GetDC.argtypes=[W.HWND];u.GetDC.restype=W.HDC;u.ReleaseDC.argtypes=[W.HWND,W.HDC]
g.CreateCompatibleDC.argtypes=[W.HDC];g.CreateCompatibleDC.restype=W.HDC
g.CreateCompatibleBitmap.argtypes=[W.HDC,ctypes.c_int,ctypes.c_int];g.CreateCompatibleBitmap.restype=W.HBITMAP
g.SelectObject.argtypes=[W.HDC,W.HGDIOBJ];g.SelectObject.restype=W.HGDIOBJ
g.BitBlt.argtypes=[W.HDC,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,W.HDC,ctypes.c_int,ctypes.c_int,W.DWORD]
g.GetDIBits.argtypes=[W.HDC,W.HBITMAP,W.UINT,W.UINT,ctypes.c_void_p,ctypes.c_void_p,W.UINT]
g.DeleteObject.argtypes=[W.HGDIOBJ];g.DeleteDC.argtypes=[W.HDC]


class Header(ctypes.Structure):
    _fields_=[('size',W.DWORD),('width',W.LONG),('height',W.LONG),('planes',W.WORD),('bits',W.WORD),
              ('compression',W.DWORD),('imageSize',W.DWORD),('xppm',W.LONG),('yppm',W.LONG),('used',W.DWORD),('important',W.DWORD)]


def main():
    check();d=taskboard.live_door();rows=d.request('/see',dict(line='window.list'))['rows'];wanted={tuple(r['box']):r['shows'] for r in rows if r.get('shows') in ('taskboard','taskboard-js','taskboard-components') and r.get('shown')}
    found=[]
    def each(h,_):
        if not u.IsWindowVisible(h):return True
        r=W.RECT();u.GetWindowRect(h,ctypes.byref(r));box=(r.left,r.top,r.right-r.left,r.bottom-r.top)
        if box in wanted:found.append((h,box,wanted[box]))
        return True
    u.EnumWindows(ENUM(each),0)
    evidence=[];images=[]
    for hwnd,(x,y,w,h),name in found:
        visible=all(u.GetAncestor(u.WindowFromPoint(W.POINT(x+int(w*rx),y+int(h*ry))),2)==hwnd for rx,ry in ((.1,.1),(.5,.1),(.5,.5),(.1,.9),(.9,.9)))
        if not visible:
            evidence.append(dict(name=name,unoccluded=False));continue
        source=u.GetDC(None);dc=g.CreateCompatibleDC(source);bitmap=g.CreateCompatibleBitmap(source,w,h);previous=g.SelectObject(dc,bitmap)
        try:
            assert g.BitBlt(dc,0,0,w,h,source,x,y,0x00CC0020|0x40000000)
            header=Header(ctypes.sizeof(Header),w,-h,1,32,0,w*h*4,0,0,0,0);data=ctypes.create_string_buffer(w*h*4)
            assert g.GetDIBits(dc,bitmap,0,h,data,ctypes.byref(header),0)
            image=Image.frombuffer('RGB',(w,h),data.raw,'raw','BGRX',0,1)
            image.save(HERE/'evidence'/f'live-native-{name}.png');images.append((name,image.copy()))
            evidence.append(dict(name=name,unoccluded=True,width=w,height=h))
        finally:
            g.SelectObject(dc,previous);g.DeleteObject(bitmap);g.DeleteDC(dc);u.ReleaseDC(None,source)
    if len(images)==3:
        images.sort(key=lambda p:('taskboard','taskboard-js','taskboard-components').index(p[0]))
        combined=Image.new('RGB',(sum(im.width for _,im in images),max(im.height for _,im in images)),'white');offset=0
        for _,im in images:combined.paste(im,(offset,0));offset+=im.width
        combined.save(HERE/'evidence/live-native-three-boards.png')
    (HERE/'evidence/native-capture.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    print(json.dumps(evidence),flush=True)


if __name__=='__main__':main()
