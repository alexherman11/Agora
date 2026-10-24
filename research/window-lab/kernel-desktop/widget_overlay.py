"""JS draws the full desktop; the host presents its alpha pixels, never a box.

An offscreen Edge page provides reliable alpha, unlike WebView2 colour-key
transparency. A crop is a rendering optimization, not a limit on surface space.
No debugger endpoint or browser credential is passed to widget code.
"""
import base64
import ctypes
import io
import queue
import threading
import time
from urllib.parse import quote

from PIL import Image, ImageDraw

from gaming_gate import reasons
from sprite import Sprite
from widget_browser import Browser

# Window geometry from window.list is physical pixels. This process owns the
# alpha HWNDs too, so its browser viewport and native positions must agree.
ctypes.WinDLL('user32').SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))


def protected_boxes(kernel):
    """Reserve bars and every trusted desktop chrome/receipt. Trusted host
    windows (sign-in, Lines, Help, Thing) are protected in their entirety."""
    boxes=[]
    with kernel.lock:
        for w in kernel.things('window'):
            if kernel.state.get(w,'forgotten'):continue
            try:
                x,y=map(int,kernel.state.get(w,'at').split(','));width,height=map(int,kernel.state.get(w,'size').split(','))
            except (ValueError,AttributeError):continue
            if kernel.state.get(w,'edge') or not (kernel.state.get(w,'lens') or kernel.state.get(w,'widget')):
                boxes.append((x,y,x+width,y+height))
            else:
                boxes.extend(((x,y,x+width,y+56),(x,y+height-56,x+width,y+height)))
    return boxes


class Overlay:
    def __init__(self,kernel,base,entry,mid,stop):
        self.k,self.base,self.entry,self.mid,self.stop=kernel,base,entry,mid,stop
        self.hits=[];self.events=queue.Queue(maxsize=64)
        self.sprite=None
        self.hit_surfaces=[];self.hit_key=None

    def hit(self,x,y):
        return not any(a<=x<c and b<=y<d for a,b,c,d in protected_boxes(self.k)) and any(
            r['x']<=x<r['x']+r['width'] and r['y']<=y<r['y']+r['height'] for r in self.hits)

    def pointer(self,msg,x,y):
        try:self.events.put_nowait((msg,x,y))
        except queue.Full:pass

    def run(self):
        # The drawing HWND always has WS_EX_TRANSPARENT. Separate tiny HWNDs
        # receive only explicit hit rectangles, so click-through works across
        # other programs' threads too (HTTRANSPARENT alone does not promise it).
        self.sprite=Sprite('Agora widget overlay')
        self.sprite.start()
        try:
            with Browser(self.base) as c:
                import ctypes
                u=ctypes.WinDLL('user32');width,height=u.GetSystemMetrics(0),u.GetSystemMetrics(1)
                c.call('Emulation.setDeviceMetricsOverride',width=width,height=height,deviceScaleFactor=1,mobile=False)
                c.call('Emulation.setDefaultBackgroundColorOverride',color={'r':0,'g':0,'b':0,'a':0})
                path='/desk/widget.html?widget='+self.mid
                c.call('Page.navigate',url=self.base+'/dev/signin?token='+self.entry.token('alex')+'&next='+quote(path,safe=''))
                c.until('!!(window.widgetSurface && document.querySelector("#widget-surface iframe"))')
                # Chromium can replace its document background during navigation.
                # Apply alpha to the settled widget document, not just about:blank.
                c.call('Emulation.setDefaultBackgroundColorOverride',color={'r':0,'g':0,'b':0,'a':0})
                seq=0;gated=False;next_gate=0;next_boxes=0;boxes=[]
                while not self.stop.is_set():
                    now=time.monotonic()
                    if now>=next_gate:
                        gated=bool(reasons());next_gate=now+1
                    if gated:
                        self.sprite.hide()
                        for hit in self.hit_surfaces:hit.hide()
                        self.stop.wait(.5);continue
                    data=c.js('({ ...window.widgetSurface, stopped:document.querySelector("#widget-surface").dataset.stopped })')
                    if data.get('stopped'):break
                    self.hits=data.get('hits') or []
                    while not self.events.empty():
                        msg,x,y=self.events.get_nowait()
                        c.call('Input.dispatchMouseEvent',type={0x201:'mousePressed',0x202:'mouseReleased',0x200:'mouseMoved'}[msg],x=x,y=y,button='left' if msg!=0x200 else 'none',clickCount=1 if msg!=0x200 else 0)
                    r=data.get('paint') or dict(x=0,y=60,width=width,height=height-160)
                    r={k:float(r[k]) for k in ('x','y','width','height')}
                    if r['width']<1 or r['height']<1:self.stop.wait(.05);continue
                    raw=c.call('Page.captureScreenshot',format='png',captureBeyondViewport=False,clip={**r,'scale':1})['data']
                    image=Image.open(io.BytesIO(base64.b64decode(raw))).convert('RGBA')
                    if now>=next_boxes:boxes=protected_boxes(self.k);next_boxes=now+.3
                    key=(str(self.hits),str(boxes))
                    if key!=self.hit_key:
                        for hit in self.hit_surfaces:hit.close()
                        self.hit_surfaces=[];self.hit_key=key
                        for rect in self.hits:
                            hx,hy,hw,hh=(int(rect[v]) for v in ('x','y','width','height'))
                            hy=max(60,hy);hh=min(hh,height-100-hy)
                            if hw<1 or hh<1:continue
                            hit=Sprite('Agora widget hit area',hit_test=lambda x,y:True,on_pointer=self.pointer)
                            hit.start();pixels=Image.new('RGBA',(hw,hh),(0,0,0,1));draw=ImageDraw.Draw(pixels)
                            for a,b,d,e in boxes:draw.rectangle((a-hx,b-hy,d-hx,e-hy),fill=(0,0,0,0))
                            hit.show(key,pixels,hx,hy);self.hit_surfaces.append(hit)
                    for hit in self.hit_surfaces:hit.hide(False)
                    mask=ImageDraw.Draw(image)
                    # Exclude reserved screen edges even if a widget asks for them.
                    mask.rectangle((0,0,image.width,max(-1,60-r['y'])),fill=(0,0,0,0)) if r['y']<60 else None
                    if r['y']+image.height>height-100:mask.rectangle((0,max(0,height-100-r['y']),image.width,image.height),fill=(0,0,0,0))
                    for a,b,d,e in boxes:
                        mask.rectangle((a-r['x'],b-r['y'],d-r['x'],e-r['y']),fill=(0,0,0,0))
                    seq+=1;self.sprite.show(seq,image,int(r['x']),int(r['y']));self.sprite.hide(False)
                    self.stop.wait(1/30)
        finally:
            for hit in self.hit_surfaces:hit.close()
            self.sprite.close()


class Overlays:
    def __init__(self,kernel,base,entry):
        self.k,self.base,self.entry=kernel,base,entry;self.running={};self.closed=threading.Event()
        self.rest={}

    def loop(self):
        while not self.closed.wait(1):
            with self.k.lock:
                want={w for w in self.k.things('widget') if self.k.state.get(w,'on') and self.k.state.get(w,'code') and self.k.state.get(w,'surface')=='overlay' and not self.k.state.get(w,'forgotten')}
            for w,(ev,t) in list(self.running.items()):
                if w not in want or not t.is_alive():
                    ev.set();self.running.pop(w,None)
                    if w in want:self.rest[w]=time.monotonic()+30
            if reasons():continue
            for w in want-set(self.running):
                if time.monotonic()<self.rest.get(w,0):continue
                ev=threading.Event();overlay=Overlay(self.k,self.base,self.entry,w,ev)
                t=threading.Thread(target=overlay.run,daemon=True,name='widget-overlay');self.running[w]=(ev,t);t.start()

    def close(self):
        self.closed.set()
        for ev,t in self.running.values():ev.set();t.join(4)
