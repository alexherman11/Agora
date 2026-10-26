"""Mixed failing/live board and general handles through real doors and DOM.

--native uses never-shown WebView2, including a trusted same-thread infinite
mount and parent-watchdog recovery. Default uses the existing hidden driver.
"""
import json
from pathlib import Path
import sys
import time

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from painter.fixture import Fixture
from painter.browser import Page
from painter.install import Q,upsert,activate


def run(factory=Page,native=False):
    f=Fixture();d=f.door;pages=[];checks=[]
    def check(name,ok):
        print(('PASS ' if ok else 'FAIL ')+name,flush=True);checks.append(dict(name=name,ok=bool(ok)));assert ok,name
    def component(name,code,settings='{}',review=True,**extra):
        tid=upsert(d,'component',name,code=code,settings=settings,parts='{"body":{}}',**extra)
        if review:d.say('look '+tid);d.say('component '+tid)
        return tid
    def set_(t,**values):
        d.say('look '+t);return d.say('set '+t+''.join(' '+k+'='+Q(v) for k,v in values.items()))
    def wait(test,timeout=15):
        until=time.monotonic()+timeout
        while time.monotonic()<until:
            for p in pages:p.c.js('0')
            if test():return
            time.sleep(.1)
        raise AssertionError('condition timed out')
    try:
        if native:
            broker=f.d.srv.RequestHandlerClass.widget_broker;original=broker.request
            def trace(actor,action,body):
                if action=='stall':print('NATIVE STALL',body.get('path'),body.get('stage'),flush=True)
                return original(actor,action,body)
            broker.request=trace
        bad=component('broken-mount',"export default {mount(){throw Error('Printer unavailable')}}")
        click=component('broken-click',"export default {mount(api){return api.part('body','button',{on:{click(){throw Error('Vote could not open')}}},'Open vote')}}")
        loop=component('broken-loop',"export default {mount(){while(true){}}}",review=False)
        timer=component('broken-timer',"export default {mount(api){api.setTimeout(()=>{throw Error('Timer stopped')},500);return api.part('body','div',{},'Waiting for timer')}}")
        raf=component('broken-animation',"export default {mount(api){api.requestAnimationFrame(()=>{throw Error('Animation stopped')});return api.part('body','div',{},'Waiting for animation')}}")
        good=component('isolated-control',"export default {mount(api,s){let n=0;return api.part('body','button',{on:{click(e){e.currentTarget.textContent='Worker presses '+(++n)}}},'Worker presses 0')}}",review=False)
        source=(HERE.parent/'apps/taskboard/component-board.lens').read_text(encoding='utf-8')
        source=source.replace('root : column, of tag:', 'root : column\n  faults : row\n    bad : broken-mount\n    click : broken-click\n    loop : broken-loop\n    data : flag, priority "not a number"\n    timer : broken-timer\n    animation : broken-animation\n    worker : isolated-control\n  board : column, of tag:',1)
        lid=upsert(d,'lens','isolation-board',painter='components',text=source)
        wid=activate(d,'isolation-board','Hidden isolation board')
        p=factory(f.url,f.token,wid);pages.append(p)
        try:p.until('document.querySelectorAll(".card").length===25',seconds=30)
        except Exception:
            print('NATIVE DIAGNOSTIC',[(a['name'],a['health']['health'],a['health']['quarantined'],a['health']['last_error']) for a in d.say('look-view isolation-board')['rows'][0]['parts']],flush=True)
            print('TARGETS',p.c.call('Target.getTargets'),flush=True)
            raise
        # Native first-pass loop is recovered by trusted parent. No further loop
        # executes on the painter thread; the isolated worker is terminable.
        loop_sel=Q('[data-path="root/faults/loop"]')
        p.until('document.querySelector('+loop_sel+')?.classList.contains("component-stopped")',seconds=30)
        check('Mount, bad settings and infinite loop stop only their parts',p.js('document.body.innerText.includes("Printer unavailable")&&document.body.innerText.includes("needs a number")&&document.querySelectorAll(".card").length===25'))
        check('A never-painted worker has no fictitious last-good loading snapshot',p.js('!document.querySelector('+Q('[data-path="root/faults/loop"] [data-stale]')+')'))
        if native:check('Actual WebView2 scratch window is never shown',p.hidden())
        p.until('document.body.innerText.includes("Worker presses 0")')
        p.js('document.querySelector('+Q('[data-path="root/faults/worker"] button')+').click()')
        p.until('document.body.innerText.includes("Worker presses 1")')
        check('A separate worker answers after its looping sibling is killed',True)
        p.js('document.querySelector('+Q('[data-path="root/faults/click"]')+').click()')
        p.until('document.body.innerText.includes("Vote could not open")')
        check('Click failure keeps last good rendering marked stale',p.js('!!document.querySelector('+Q('[data-path="root/faults/click"] [data-stale]')+')'))
        p.until('document.body.innerText.includes("Timer stopped")&&document.body.innerText.includes("Animation stopped")')
        check('Timers and animation callbacks are attributed to their owners',True)
        task=f.tasks[0];sel='[data-task="'+task+'"]'
        p.js('document.querySelector('+Q(sel+' .cardtop button')+').click()');p.until('!!document.querySelector(".menu")')
        p.js('[...document.querySelectorAll(".menu button")].find(b=>b.textContent==="Assign to JEFF").click()')
        wait(lambda:f.k.state.get(task,'who')=='JEFF')
        p.until('document.querySelector('+Q(sel)+')?.dataset.factWho==="JEFF"')
        check('Healthy board menu still writes actual facts',True)
        point=p.start_drag(sel,'[data-lane=Done]');p.release(point)
        wait(lambda:f.k.state.get(task,'lane')=='Done');check('Healthy board retains real pointer drag',True)
        from painter.install import taskboard
        neighbour=f.k.join('proof:isolation-neighbour','Neighbour',invite={'admitted':True})['person']
        f.d.entry.sessions['isolation-peer']={'account':'proof:isolation-neighbour','method':'proof'}
        d.say('role '+neighbour+' leader in='+f.k.place)
        peer=taskboard.Door(f.url,'isolation-peer');peer.say('look '+task);peer.say('task-priority '+task+' priority=1')
        p.until('document.querySelector('+Q(sel)+')?.dataset.factPriority==="1"')
        check('Another person updates the board while parts are stopped',True)
        set_(bad,code="export default {mount(api){return api.part('body','div',{},'Printer ready')}}");d.say('component '+bad)
        p.js('[...document.querySelectorAll('+Q('[data-path="root/faults/bad"] button')+')].find(b=>b.textContent==="Try again")?.click()')
        p.until('document.body.innerText.includes("Printer ready")')
        check('Try again recovers after a module fix',True)
        compact=d.say('look-view isolation-board')['rows'][0]
        full=d.say('look-view isolation-board plan=yes')['rows'][0]
        check('Default look-view is compact; full plan is explicit','tree' not in compact and 'components' not in compact and 'tree' in full and len(json.dumps(compact))<len(json.dumps(full))/2)
        wait(lambda:any(a.get('health',{}).get('painted') for a in d.say('look-view isolation-board')['rows'][0]['parts']))
        reading=d.say('look-view isolation-board')['rows'][0]
        check('Agent can read painted text, computed styles and health without pixels',any('Worker presses' in str(a['health']['painted']) for a in reading['parts']))
        wait(lambda:next(a for a in d.say('look-view isolation-board')['rows'][0]['parts'] if a['name']=='loop')['health']['quarantined'])
        check('Repeated crashes/hang are quarantined as private facts',True)
        if not native:
            p.js('scrollTo(0,0)');p.c.js('scrollTo(0,0)')
            p.shot(HERE/'evidence/isolation-hidden.png')
        # General handle checks, independent of ten frozen requests.
        for field,value in [('glow','#2356ab67'),('padding','3px 7px 5px')]:
            d.say('make kind=part-style lens=isolation-board target=card '+field+'='+Q(value))
        p.until('(()=>{const s=getComputedStyle(document.querySelector(".card"));return s.paddingTop==="3px"&&s.paddingLeft==="7px"&&s.paddingBottom==="5px"&&s.boxShadow!=="none"})()')
        check('Alpha colours and CSS padding shorthand accepted and painted',True)
        before=len(f.k.log.records)
        refused=d.request('/do',dict(line='make kind=part-style lens=isolation-board target=card padding="url(escape)"'))
        check('Unpaintable style refused atomically at write time',not refused['ok'] and len(f.k.log.records)==before and 'allowed' not in refused.get('exception',''))
        d.say('personal-view isolation-board lane-view.labels.name='+Q(json.dumps({'Done':'Finished in my language'})))
        d.say('personal-view isolation-board task-view.format.who=initials')
        p.until('document.querySelector("[data-lane=Done] .lanehead")?.textContent.includes("Finished in my language")')
        check('Display labels preserve domain value and drop identity',p.js('document.querySelector("[data-lane=Done]").dataset.lane==="Done"') and f.k.state.get(task,'lane')=='Done')
        check('Personal scope is discoverable and absent for another viewer','Just for me' in d.say('help personal-view')['text'] and 'Finished in my language' not in str(peer.say('look-view isolation-board')))
        p.until('[...document.querySelectorAll(".card .avatar")].some(a=>a.title==="JEFF"&&a.textContent==="J")')
        check('Initials formatting leaves underlying name unchanged',p.js('[...document.querySelectorAll(".card .avatar")].some(a=>a.title==="JEFF"&&a.textContent==="J")') and f.k.state.get(task,'who')=='JEFF')
        # Add a declarative fact-change motion to an existing template.
        set_(lid,text=source.replace('task-view : card,','task-view : card,',1).replace('  only when $view.filter','  when fact priority changes play pulse\n  only when $view.filter',1))
        p.until('document.querySelectorAll(".card").length===25');time.sleep(1)
        peer.say('look '+task);peer.say('task-priority '+task+' priority=2')
        p.until('document.querySelector('+Q(sel)+')?.dataset.lastMotion==="pulse"')
        check('A peer fact change plays its declared theme motion',True)
        if native:
            component('later-hang',"export default {mount(){while(true){}}}")
            current=next(a for a in d.rows('lens') if a['id']==lid)['text']
            recovery_started=time.monotonic()
            set_(lid,text=current.replace('    worker : isolated-control','    worker : isolated-control\n    later : later-hang'))
            # Query only the trusted parent during the in-page hang.
            p.c.until('document.querySelector("#widget-surface").dataset.recoveries==="1"',timeout=30)
            p.session=None
            p.until('document.querySelectorAll(".card").length===25',seconds=20)
            p.until('document.querySelector('+Q('[data-path="root/faults/later"]')+')?.classList.contains("component-stopped")',seconds=15)
            check('Trusted in-page infinite loop is quarantined by the native parent and board recovers',True)
            print(f'NATIVE RECOVERY {1000*(time.monotonic()-recovery_started):.1f} ms; hidden=True; 25 cards restored',flush=True)
        result=dict(native=native,checks=checks)
        (HERE/'evidence'/('isolation-native-proof.json' if native else 'isolation-proof.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(f'{len(checks)} of {len(checks)} isolation/handle checks passed'+(' in WebView2' if native else ''),flush=True)
    finally:
        for p in pages:p.close()
        f.close()


def native_main():
    import socket,threading,urllib.request
    sys.path.insert(0,str(HERE.parents[1]/'window-lab/kernel-desktop'))
    from gaming_gate import assert_clear
    assert_clear()
    import webview,widget_guard
    from widget_browser import CDP
    widget_guard.install()
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    webview.settings['REMOTE_DEBUGGING_PORT']=port
    anchor=webview.create_window('Hidden isolation anchor',html='<html></html>',hidden=True,width=200,height=100)
    class NativePage(Page):
        def __init__(self,url,token,widget,**kwargs):
            from urllib.parse import quote
            assert_clear()
            target=url+'/dev/signin?token='+token+'&next='+quote('/desk/widget.html?widget='+widget,safe='')
            self.win=webview.create_window('Never-shown isolation scratch board',target,hidden=True,width=1600,height=1040)
            self.win.events.loaded.wait(20)
            end=time.monotonic()+15;found=None
            while time.monotonic()<end:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/json/list') as r:targets=json.load(r)
                found=next((t for t in targets if t['type']=='page' and t['url'].startswith(url+'/desk/widget.html')),None)
                if found:break
                time.sleep(.1)
            assert found,'native debugging page not found'
            self.c=CDP(found['webSocketDebuggerUrl']);self.session=None;self.errors=[]
            self.c.call('Page.enable');self.c.call('Emulation.setFocusEmulationEnabled',enabled=True)
            self.c.until('!!document.querySelector("#widget-surface iframe")')
        def hidden(self):return not bool(self.win.native.Visible)
        def start_drag(self,selector,target):
            # A never-shown WebView2 intentionally stops compositor frames.
            # Deliver real pointer input without awaiting a hidden rAF.
            a=self.point(selector)
            b=self.js('(()=>{const r=document.querySelector('+json.dumps(target)+').getBoundingClientRect();return {x:r.x+r.width/2,y:Math.max(60,Math.min(innerHeight*.65,r.bottom-12))}})()')
            offset=self.c.js('(()=>{const r=document.querySelector("iframe").getBoundingClientRect();return {x:r.x,y:r.y}})()')
            b=dict(x=b['x']+offset['x'],y=b['y']+offset['y'])
            self.c.call('Input.dispatchMouseEvent',type='mouseMoved',**a)
            self.c.call('Input.dispatchMouseEvent',type='mousePressed',button='left',clickCount=1,**a)
            for i in range(1,13):
                self.c.call('Input.dispatchMouseEvent',type='mouseMoved',button='left',buttons=1,
                            x=a['x']+(b['x']-a['x'])*i/12,y=a['y']+(b['y']-a['y'])*i/12)
                time.sleep(.02)
            return b
        def close(self):self.c.s.close();self.win.destroy()
    status=[1]
    def execute():
        try:run(NativePage,True);status[0]=0
        except Exception:
            import traceback;traceback.print_exc()
        finally:anchor.destroy()
    webview.start(execute,gui='edgechromium',private_mode=True)
    return status[0]


if __name__=='__main__':
    if '--native' in sys.argv:raise SystemExit(native_main())
    run()
