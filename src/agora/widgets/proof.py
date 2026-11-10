"""Short hidden Chromium proof, scratch world only. No live writes or GPU soak."""
import base64
import importlib.util
import json
from pathlib import Path
import sys
import time
from urllib.parse import quote

HERE=Path(__file__).resolve().parent
DESKTOP=HERE.parents[1]/'desktop/kernel-desktop'
sys.path.insert(0,str(DESKTOP))
sys.path.insert(0,str(HERE))
from test_kdesk import Desk
from widget_browser import Browser
from install import install, taskboard, quote as Q

EVIDENCE=HERE/'evidence'


def frame_context(c):
    targets=[t for t in c.call('Target.getTargets')['targetInfos'] if t['type']=='iframe' and t['url']=='about:srcdoc']
    if targets:
        target=targets[0]
        sessions=getattr(c,'widget_sessions',{})
        if target['targetId'] not in sessions:
            sessions[target['targetId']]=c.call('Target.attachToTarget',targetId=target['targetId'],flatten=True)['sessionId']
            c.widget_sessions=sessions
        return {'_session':sessions[target['targetId']]}
    tree=c.call('Page.getFrameTree')['frameTree']
    child=next((f for f in tree.get('childFrames',[]) if f['frame'].get('name')=='agora-widget'),None)
    if child:
        # Same-process iframe: obtain its main execution context via Runtime events.
        contexts=[]
        previous=c.on_event
        def event(e):
            previous(e)
            if e.get('method')=='Runtime.executionContextCreated':contexts.append(e['params']['context'])
        c.on_event=event;c.call('Runtime.disable');c.call('Runtime.enable');c.on_event=previous
        ctx=next(x['id'] for x in contexts if x.get('auxData',{}).get('frameId')==child['frame']['id'] and x.get('auxData',{}).get('isDefault'))
        return {'contextId':ctx}
    raise RuntimeError('sandbox execution context is not ready')


def inside(c,expression):
    r=c.call('Runtime.evaluate',expression=expression,returnByValue=True,awaitPromise=True,**frame_context(c))
    if r.get('exceptionDetails'):raise AssertionError(r['exceptionDetails'])
    return r.get('result',{}).get('value')


def main():
    EVIDENCE.mkdir(exist_ok=True)
    d=Desk();checks=[]
    def check(name,condition):
        assert condition,name
        checks.append(name);print('PASS '+name,flush=True)
    try:
        door=taskboard.Door(d.url,d.entry.token('alex'))
        taskboard.install(door)
        settings=door.rows('taskboard-settings')[0]
        door.say('set '+settings['id']+' model=widget-proof-unavailable')
        for rule in door.rows('rule'):
            if 'summarize' in str(rule.get('do','')):
                door.say('look '+rule['id']);door.say('set '+rule['id']+' off=yes')
        examples=[('Invite the neighbours to Sunday lunch','Backlog','2','paper','Alex','Bring something to share.\nLeave room for new faces.'),
                  ('Find a quieter rhythm for the feed','Backlog','3','sage','JEFF','A slower lane for things that matter.'),
                  ('Sketch the garden gathering','Backlog','4','paper','Alex',''),
                  ('Give the community a beautiful front door','Now','1','paper','Alex','Warm paper, a little colour, a place to belong.'),
                  ('Make every small change understandable','Now','2','peach','JEFF','Every press is a line.\nEvery change has a history.'),
                  ('Try the same board through two views','Now','3','paper','Alex',''),
                  ('Choose our first shared tools','Done','3','sage','Alex','A small beginning.'),
                  ('Leave a little room for play','Done','4','paper','JEFF','')]
        for title,lane,p,colour,who,note in examples:
            out=door.say(f'task-add title={Q(title)} to={lane} who={who} text={Q(title)} source=widget-proof status=open when=2026-10-24')
            t=out['made'][0];door.say('look '+t)
            door.say(f'set {t} priority={p} colour={colour} short={Q(title)} note={Q(note)} note_colour={colour}')
        ids=install(door)
        seq=len(d.k.log.records);check('idempotent widget installation',install(door)==ids and len(d.k.log.records)==seq)
        with Browser(d.url) as c:
            def visit(mid,width,height):
                c.call('Emulation.setDeviceMetricsOverride',width=width,height=height,deviceScaleFactor=1,mobile=False)
                extra='&slot=1' if d.k.state.get(mid,'surface') in ('top','bottom') else ''
                c.call('Page.navigate',url=d.url+'/dev/signin?token='+d.entry.token('alex')+'&next='+quote('/desk/widget.html?widget='+mid+extra,safe=''))
                c.until('!!document.querySelector("#widget-surface iframe")')
                time.sleep(.3)
            def screenshot(name):
                c.call('Page.captureScreenshot',format='png',captureBeyondViewport=False)
                time.sleep(.15)
                (EVIDENCE/name).write_bytes(base64.b64decode(c.call('Page.captureScreenshot',format='png',captureBeyondViewport=False)['data']))
            visit(ids['taskboard-js'],1500,1000)
            c.until('document.querySelector("#widget-surface iframe")?.getAttribute("sandbox")==="allow-scripts"')
            for _ in range(50):
                if inside(c,'document.querySelectorAll(".card").length')==8:break
                time.sleep(.1)
            check('same eight world tasks rendered',inside(c,'document.querySelectorAll(".card").length')==8)
            check('opaque sandbox has no host DOM',c.js('(()=>{try{return !!document.querySelector("#widget-surface iframe").contentDocument.body}catch{return false}})()') is False)
            check('theme delivered as data',inside(c,'agora.theme().then(t=>t.paper)')=='#FAF9F6')
            screenshot('taskboard-js.png')
            # Real pointer drag through the opaque frame, using its real DOM boxes.
            boxes=inside(c,'(()=>{const a=document.querySelector(".card"),b=document.querySelector("[data-lane=Done]");const r=a.getBoundingClientRect(),s=b.getBoundingClientRect();return {id:a.dataset.task,x:r.x+r.width/2,y:r.y+r.height/2,tx:s.x+s.width/2,ty:s.y+s.height*.65}})()')
            offset=c.js('(()=>{const r=document.querySelector("#widget-surface iframe").getBoundingClientRect();return {x:r.x,y:r.y}})()')
            x,y=boxes['x']+offset['x'],boxes['y']+offset['y'];tx,ty=boxes['tx']+offset['x'],boxes['ty']+offset['y']
            c.call('Input.dispatchMouseEvent',type='mouseMoved',x=x,y=y)
            c.call('Input.dispatchMouseEvent',type='mousePressed',x=x,y=y,button='left',clickCount=1)
            for n in range(1,13):
                c.call('Input.dispatchMouseEvent',type='mouseMoved',x=x+(tx-x)*n/12,y=y+(ty-y)*n/12,button='left',buttons=1)
                time.sleep(.015)
            c.call('Input.dispatchMouseEvent',type='mouseReleased',x=tx,y=ty,button='left',clickCount=1)
            d.wait(lambda:(c.js('0'),d.k.state.get(boxes['id'],'lane')=='Done')[1])
            check('real pointer drag says task-move',d.k.state.get(boxes['id'],'lane')=='Done')
            # An old observed revision must not move the card again.
            old=door.rows('taskboard-task')[0];door.say('set '+old['id']+' note="A newer note"')
            stale=inside(c,'agora.do('+json.dumps('task-move '+old['id']+' to=Now')+','+json.dumps({old['id']:old['rev']})+').then(()=>false,e=>e.message.includes("stale"))')
            check('stale competing edit refused through bridge',stale)
            inside(c,'document.querySelector(".cardtop button").click();true')
            screenshot('taskboard-menu.png')
            inside(c,'document.querySelector(".card").dispatchEvent(new MouseEvent("dblclick",{bubbles:true}));true');time.sleep(.3);screenshot('taskboard-editor.png')
            # Guy editor and actual shared-fact update.
            visit(ids['guy-editor'],600,990)
            for _ in range(30):
                if inside(c,'!!document.querySelector("[aria-label=Name]")'):break
                time.sleep(.1)
            screenshot('guy-editor.png')
            inside(c,'(()=>{const n=document.querySelector("[aria-label=Name]");n.value="Moss Junior";n.dispatchEvent(new Event("change"));return true})()')
            d.wait(lambda:(c.js('0'),door.rows('guy-profile')[0]['name']=='Moss Junior')[1])
            check('editor stores real guy facts',door.rows('guy-profile')[0]['name']=='Moss Junior')
            original=d.host.call
            def overlay_call(mid,word,args,caller):
                if word=='window.list':return {'rows':[dict(kind='work',box=[0,60,1400,800])], 'text':'scratch overlay viewport'}
                return original(mid,word,args,caller)
            d.host.call=overlay_call
            visit(ids['desktop-guy'],1400,950)
            c.call('Emulation.setDefaultBackgroundColorOverride',color={'r':0,'g':0,'b':0,'a':0})
            c.until('widgetSurface.paint!==null');screenshot('guy-overlay.png')
            from PIL import Image
            with Image.open(EVIDENCE/'guy-overlay.png') as captured:
                check('overlay background is truly transparent',captured.mode=='RGBA' and captured.getpixel((0,0))[3]==0)
            check('overlay paints in full desktop coordinates',c.js('widgetSurface.paint!==null'))
            check('overlay defaults to click through',c.js('widgetSurface.hits.length===0'))
            # Empty media is honest; controlled fixture through the real media word
            # answer supplies album art for visual QA only, never the live world.
            d.host.call=original
            import io
            from PIL import Image,ImageDraw
            art=Image.new('RGB',(72,72),'#91aaa0');paint=ImageDraw.Draw(art);paint.ellipse((12,6,78,90),fill='#e3d5b2');paint.ellipse((-12,27,45,98),fill='#718d83');out=io.BytesIO();art.save(out,'PNG')
            def call(mid,word,args,caller):
                if word=='media.now':return {'text':'fixture','rows':[dict(kind='media',title='A walk through the trees',artist='Soft Sunday · visual fixture',playing=True,position=83,duration=240,art='data:image/png;base64,'+base64.b64encode(out.getvalue()).decode())]}
                return original(mid,word,args,caller)
            d.host.call=call
            visit(ids['now-playing'],340,40)
            for _ in range(40):
                if inside(c,'document.querySelector(".title")?.textContent')=='A walk through the trees':break
                time.sleep(.1)
            screenshot('now-playing.png')
            check('bar widget holds a real lease',any(h['by']==ids['now-playing'] and h['word']=='window.bar' for h in d.k.leases.values()))
            d.host.call=original
            hostile='''await agora.ready;
const result={};
try{await fetch('http://127.0.0.1:9/leak');result.fetch=false}catch{result.fetch=true}
try{result.cookie=document.cookie;result.cookieBlocked=false}catch{result.cookieBlocked=true}
try{localStorage.setItem('x','y');result.storage=false}catch{result.storage=true}
try{top.location='https://example.invalid/widget-escape';result.top=false}catch{result.top=true}
try{await agora.do('pin TARGET');result.pin=false}catch(e){result.pin=e.message.includes('grant')}
result.pywebview=typeof window.pywebview==='undefined';result.native=typeof window.chrome?.webview==='undefined';
await agora.describe(JSON.stringify(result));'''
            target=door.say('post Widget sandbox target')['made'][0]
            hostile=hostile.replace('TARGET',target)
            h=door.say('make kind=widget name=hostile-proof code='+Q(hostile))['made'][0]
            door.say('look '+h);door.say(f'widget {h} grants="window.surface describe"')
            visit(h,700,450)
            data=d.wait(lambda:(c.js('0'),d.k.state.get(h,'description'))[1])
            result=json.loads(data)
            for name in ('fetch','cookieBlocked','storage','top','pin','pywebview','native'):
                check('hostile '+name+' blocked',result.get(name) is True)
            check('top location unchanged',c.js('location.pathname')=='/desk/widget.html')
            check('ungranted pin wrote no fact',not d.k.state.get(target,'pinned'))
            check('look returns widget description',door.say('look '+h)['rows'][0]['description']==data)
            door.say('off '+h)
            check('off immediately releases widget holds',not any(x['by']==h for x in d.k.leases.values()))
            c.until('document.querySelector("#widget-surface").dataset.stopped==="true"')
            check('off destroys sandbox frame',not c.js('!!document.querySelector("#widget-surface iframe")'))
        print(f'{len(checks)} of {len(checks)} widget checks passed',flush=True)
        (EVIDENCE/'proof.json').write_text(json.dumps({'checks':checks,'count':len(checks)},indent=2),encoding='utf-8')
    finally:d.close()


if __name__=='__main__':main()
