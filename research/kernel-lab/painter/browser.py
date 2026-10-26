"""Hidden guarded-widget driver. Uses the existing widget proof's native wall."""
import base64
import json
from pathlib import Path
import sys
import time
from urllib.parse import quote

DESKTOP=Path(__file__).resolve().parents[2]/'window-lab/kernel-desktop'
sys.path.insert(0,str(DESKTOP))
from widget_browser import Browser


class Page:
    def __init__(self,url,token,widget,width=1600,height=1040,clock=None):
        self.browser=Browser(url,test_flags=['--disable-background-timer-throttling','--disable-renderer-backgrounding','--disable-backgrounding-occluded-windows']);self.c=self.browser.__enter__()
        self.errors=[];previous=self.c.on_event
        def capture(e):
            previous(e)
            if e.get('method') in ('Runtime.exceptionThrown','Log.entryAdded'):self.errors.append(e)
        self.c.on_event=capture;self.c.call('Runtime.enable');self.c.call('Log.enable')
        self.c.call('Emulation.setFocusEmulationEnabled',enabled=True)
        self.c.call('Emulation.setDeviceMetricsOverride',width=width,height=height,deviceScaleFactor=1,mobile=False)
        if clock:self.c.call('Page.addScriptToEvaluateOnNewDocument',source=self.clock_script(clock))
        self.navigate_at=time.perf_counter()
        self.c.call('Page.navigate',url=url+'/dev/signin?token='+token+'&next='+quote('/desk/widget.html?widget='+widget,safe=''))
        self.c.until('!!document.querySelector("#widget-surface iframe")')
        self.session=None

    @staticmethod
    def clock_script(clock):
        epoch=int(clock.timestamp()*1000)
        return '(()=>{const Original=globalThis.__originalDate||Date;globalThis.__originalDate=Original;globalThis.Date=class extends Original{constructor(...args){super(...(args.length?args:['+str(epoch)+']))}static now(){return '+str(epoch)+'}}})()'

    def set_clock(self,clock):self.js(self.clock_script(clock))

    def context(self):
        c=self.c
        if self.session:return self.session
        targets=[t for t in c.call('Target.getTargets')['targetInfos'] if t['type']=='iframe' and t['url']=='about:srcdoc']
        if targets:
            self.session={'_session':c.call('Target.attachToTarget',targetId=targets[-1]['targetId'],flatten=True)['sessionId']}
            return self.session
        tree=c.call('Page.getFrameTree')['frameTree'];child=next((f for f in tree.get('childFrames',[]) if f['frame'].get('name')=='agora-widget'),None)
        if not child:raise RuntimeError('widget frame not ready')
        contexts=[];previous=c.on_event
        def event(e):
            previous(e)
            if e.get('method')=='Runtime.executionContextCreated':contexts.append(e['params']['context'])
        c.on_event=event;c.call('Runtime.disable');c.call('Runtime.enable');c.on_event=previous
        ctx=next(x['id'] for x in contexts if x.get('auxData',{}).get('frameId')==child['frame']['id'] and x.get('auxData',{}).get('isDefault'))
        self.session={'contextId':ctx};return self.session

    def js(self,expression):
        try:r=self.c.call('Runtime.evaluate',expression=expression,returnByValue=True,awaitPromise=True,**self.context())
        except RuntimeError as exc:
            if not any(s in str(exc) for s in ('Cannot find context','No session with given id')):raise
            self.session=None
            r=self.c.call('Runtime.evaluate',expression=expression,returnByValue=True,awaitPromise=True,**self.context())
        if r.get('exceptionDetails'):raise AssertionError(r['exceptionDetails'])
        return r.get('result',{}).get('value')

    def until(self,expression,seconds=15):
        end=time.monotonic()+seconds;last=None
        while time.monotonic()<end:
            try:
                self.c.js('0')
                if self.js(expression):return
            except (RuntimeError,AssertionError,StopIteration) as e:last=e
            time.sleep(.08)
        raise AssertionError(expression+'\n'+str(last)+'\n'+str(self.js('document.body.innerText'))+'\n'+str(self.errors)[-8000:])

    def shot(self,path):
        self.c.call('Page.captureScreenshot',format='png',captureBeyondViewport=False);time.sleep(.1)
        Path(path).write_bytes(base64.b64decode(self.c.call('Page.captureScreenshot',format='png',captureBeyondViewport=False)['data']))

    def point(self,selector,rx=.5,ry=.5):
        b=self.js('(()=>{const n=document.querySelector('+json.dumps(selector)+');n.scrollIntoView({block:"center"});const r=n.getBoundingClientRect();return {x:r.x+r.width*'+str(rx)+',y:r.y+r.height*'+str(ry)+'}})()')
        offset=self.c.js('(()=>{const r=document.querySelector("iframe").getBoundingClientRect();return {x:r.x,y:r.y}})()')
        return dict(x=b['x']+offset['x'],y=b['y']+offset['y'])

    def start_drag(self,selector,target):
        a=self.point(selector,.5,.4)
        b=self.js('(()=>{const r=document.querySelector('+json.dumps(target)+').getBoundingClientRect();return {x:r.x+r.width/2,y:Math.max(60,Math.min(innerHeight*.65,r.bottom-12))}})()')
        offset=self.c.js('(()=>{const r=document.querySelector("iframe").getBoundingClientRect();return {x:r.x,y:r.y}})()')
        b=dict(x=b['x']+offset['x'],y=b['y']+offset['y'])
        self.c.call('Input.dispatchMouseEvent',type='mouseMoved',**a)
        self.c.call('Input.dispatchMouseEvent',type='mousePressed',button='left',clickCount=1,**a)
        for i in range(1,13):
            self.c.call('Input.dispatchMouseEvent',type='mouseMoved',button='left',buttons=1,
                        x=a['x']+(b['x']-a['x'])*i/12,y=a['y']+(b['y']-a['y'])*i/12)
            self.js('new Promise(resolve=>requestAnimationFrame(()=>resolve(true)))')
        return b

    def release(self,point):self.c.call('Input.dispatchMouseEvent',type='mouseReleased',button='left',clickCount=1,**point)
    def close(self):self.browser.__exit__(None,None,None)
