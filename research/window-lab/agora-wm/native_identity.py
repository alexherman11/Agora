"""Discover the host's Agora.Window.<thing> property, never a title.
This is a UI identity hint, not an authority credential. Only the window host
publishes it; destruction removes it. No remote pointer or process memory read.
"""
import ctypes as C
from ctypes import wintypes as W
import re
from win32_host import u,sig

ENUMPROP=C.WINFUNCTYPE(W.BOOL,W.HWND,C.c_void_p,W.HANDLE,C.c_size_t)
sig(u,'EnumPropsExW',C.c_int,W.HWND,ENUMPROP,C.c_size_t)


def agora_id(hwnd):
    found=[]
    def each(handle,name,value,param):
        if name and name>65535 and value==1:
            label=C.wstring_at(name)
            if label.startswith('Agora.Window.') and re.fullmatch(r'[a-z]+[0-9]+',label[13:]):found.append(label[13:])
        return True
    callback=ENUMPROP(each);u.EnumPropsExW(hwnd,callback,0)
    return found[0] if len(found)==1 else None
