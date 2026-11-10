"""Read the current offscreen overlay's diagnostic state, never its credentials."""
import json
from pathlib import Path
import sys
import urllib.request

DESKTOP=Path(__file__).resolve().parents[2]/'desktop/kernel-desktop'
sys.path.insert(0,str(DESKTOP))
from widget_browser import CDP

for root in sorted((DESKTOP/'state').glob('edge-kdesk-*'),key=lambda p:p.stat().st_mtime,reverse=True):
    try:
        port=(root/'DevToolsActivePort').read_text().splitlines()[0]
        pages=json.load(urllib.request.urlopen('http://127.0.0.1:'+port+'/json/list',timeout=1))
        target=next(x for x in pages if x['type']=='page' and '/desk/widget.html' in x.get('url',''))
        c=CDP(target['webSocketDebuggerUrl'])
        if '--repair-alpha' in sys.argv:
            from gaming_gate import assert_clear
            import ctypes
            assert_clear()
            u=ctypes.WinDLL('user32');u.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
            c.call('Emulation.setDeviceMetricsOverride',width=u.GetSystemMetrics(0),height=u.GetSystemMetrics(1),deviceScaleFactor=1,mobile=False)
            c.call('Emulation.setDefaultBackgroundColorOverride',color={'r':0,'g':0,'b':0,'a':0})
        print(c.js('({path:location.pathname,surface:window.widgetSurface,receipt:document.querySelector("#receipt")?.textContent,frame:!!document.querySelector("#widget-surface iframe")})'))
        c.s.close()
        break
    except Exception:
        continue
