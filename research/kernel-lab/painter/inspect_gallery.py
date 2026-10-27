"""Hidden gallery capture and runtime diagnostics; scratch only."""
from pathlib import Path
import sys,time,json
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from painter.fixture import Fixture
from painter.browser import Page
f=Fixture();p=None
try:
    out=f.door.request('/see',dict(line='look-view component-gallery'))
    print('PLAN',out.get('ok'),out.get('text'),flush=True)
    p=Page(f.url,f.token,f.ids['component-gallery'],1200,1000)
    events=[];prev=p.c.on_event
    def event(e):
        prev(e)
        if 'exception' in e.get('method','').lower() or e.get('method')=='Runtime.consoleAPICalled':events.append(e)
    p.c.on_event=event
    for _ in range(100):
        p.c.js('0')
        try:p.c.call('Runtime.enable',**p.context())
        except Exception:pass
        time.sleep(.1)
    print('OUTER',p.c.js('document.body.innerText'),flush=True)
    print('INNER',p.js('document.body.innerText.slice(0,1000)'),flush=True)
    print('ERRORS',json.dumps(events,ensure_ascii=False),flush=True)
    p.shot(Path(__file__).resolve().parent/'evidence/component-gallery.png')
finally:
    if p:p.close()
    f.close()
