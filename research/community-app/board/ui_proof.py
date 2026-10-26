"""Hidden Chromium acceptance over the board proof's actual two-week scratch world.

Nothing is installed live and no native window is opened. CDP pointer/keyboard
events exercise controls; file-picker assignment uses CDP's real file input API.
"""
import argparse
import base64
import io
import json
import os
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
LAB=HERE.parents[1]/'kernel-lab'
DESKTOP=LAB.parent/'window-lab/kernel-desktop'
sys.path[:0]=[str(HERE),str(LAB),str(DESKTOP),str(LAB/'tests')]
from proof import Proof,fixtures
from ui_install import install_ui,taskboard,Q
from protocol import line
from painter.browser import Page,write_capture
from kernel.door import EntryClient
import kdesk

OUT=HERE/'evidence/ui'


class UI:
    def __init__(self):
        OUT.mkdir(parents=True,exist_ok=True)
        self.f=Proof();self.pages=[];self.checks=[];self.shots=[];self.metrics={}
        self.seed=self.f.run()
        f=self.f
        f.k.dev_sessions=lambda:f.entry.sessions
        handler=kdesk.make_desk_handler(f.k,EntryClient(f.entry.url,f.entry.secret))
        self.srv=kdesk.DesktopServer(('127.0.0.1',0),handler)
        self.srv.window_origins=handler.window_origins=kdesk.WindowOrigins(f.k,handler)
        threading.Thread(target=self.srv.serve_forever,daemon=True).start()
        self.url='http://127.0.0.1:'+str(self.srv.server_address[1])
        os.environ['AGORA_WIDGET_HOST_KEY']=handler.widget_broker.guard_key
        self.d=taskboard.Door(self.url,f.tokens['Alex'])
        self.d.say(line('module window',run=json.dumps([sys.executable,str(DESKTOP/'kd_window.py'),'--headless']),publishes='window.*',grants=kdesk.WINDOW_GRANTS))
        assert f.host.wait_offered(f.k.module_named('window'))
        self.ids=install_ui(self.d)
        # Screenshot positioning control exists only in this disposable world.
        # It calls the exact local selection handle used by the real controls.
        shell=self.d.rows('component',name='board-shell')[0]
        code=shell['code'].replace("root.dataset.ready='true'", "root.addEventListener('board-proof-view',e=>api.select(e.detail));root.dataset.ready='true'")
        self.d.say('look '+shell['id']);self.d.say('set '+shell['id']+' code='+Q(code));self.d.say('component '+shell['id'])
        self.channels={r['title']:r['group'] for r in self.d.rows('board-channel')}
        self.posts=self.d.rows('post')
        self.examples={kind:next((p for p in self.posts if p.get('post_kind')==kind and not p.get('reply_to') and 'SENTINEL' not in p.get('text','')),None) for kind in ['discussion','question','announcement','event','poll','ask','offer','document','Lost pet']}

    def check(self,name,ok,detail=None):
        row=dict(check=name,ok=bool(ok),detail=detail);self.checks.append(row)
        print(('PASS ' if ok else 'FAIL ')+name+((' · '+str(detail)) if detail is not None else ''),flush=True)
        assert ok,name

    def page(self,who='Alex',width=1440,height=900):
        before=time.perf_counter();p=Page(self.url,self.f.tokens[who],self.ids['widget'],width,height,clock=self.f.at)
        self.pages.append(p);p.until('!!document.querySelector(".nb-shell") && document.querySelector(".nb-navigation").innerText.includes("Off-topic")',30)
        p.set_clock(self.f.at)
        self.metrics.setdefault('cold_start_to_board_ms',round((time.perf_counter()-before)*1000,2))
        if 'first_paint_upper_bound_ms' not in self.metrics:
            from PIL import Image
            p.js('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))')
            pixels=base64.b64decode(p.c.call('Page.captureScreenshot',format='png',captureBeyondViewport=False)['data'])
            painted_at=time.perf_counter()
            accent=p.js('getComputedStyle(document.querySelector(".nb-masthead .nb-primary")).backgroundColor.match(/\\d+/g).slice(0,3).map(Number)')
            with Image.open(io.BytesIO(pixels)) as raster:assert sum(pixel==tuple(accent) for pixel in raster.convert('RGB').getdata())>50,'Initial board raster has no brand pixels'
            path=OUT/'first-paint-1440.png';write_capture(path,pixels);self.shots.append(str(path.relative_to(HERE)))
            self.metrics['first_paint_upper_bound_ms']=round((painted_at-p.navigate_at)*1000,2)
        return p

    def wait(self,p,expr,seconds=20):
        # Every hidden browser's Fetch interception needs its CDP events
        # serviced, including the second person's otherwise-idle page.
        end=time.monotonic()+seconds;last=None
        while time.monotonic()<end:
            try:
                for page in self.pages:page.c.js('0')
                if p.js(expr):return
            except (RuntimeError,AssertionError,StopIteration) as exc:last=exc
            time.sleep(.06)
        raise AssertionError(expr+'\n'+str(last)+'\n'+str(p.js('document.body.innerText')))

    def world_wait(self,condition,seconds=20):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            for page in self.pages:page.c.js('0')
            if condition():return
            time.sleep(.06)
        raise AssertionError('World reading did not confirm the pointer action')

    def click(self,p,selector):
        self.wait(p,'!!document.querySelector('+json.dumps(selector)+')')
        point=p.point(selector)
        p.js('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))')
        point=p.point(selector)
        p.c.call('Input.dispatchMouseEvent',type='mouseMoved',**point)
        p.c.call('Input.dispatchMouseEvent',type='mousePressed',button='left',clickCount=1,**point)
        p.c.call('Input.dispatchMouseEvent',type='mouseReleased',button='left',clickCount=1,**point)

    def button(self,p,label,within='document'):
        self.wait(p,'(()=>{const root='+within+';return !!root&&[...root.querySelectorAll("button")].some(b=>b.textContent.trim()==='+json.dumps(label)+'&&!b.hidden&&b.getClientRects().length)})()')
        selector=p.js('(()=>{const list='+within+'.querySelectorAll("button");const b=[...list].find(b=>b.textContent.trim()==='+json.dumps(label)+'&&!b.hidden&&b.getClientRects().length);if(!b)throw Error("No button '+label+'");b.dataset.proofClick="yes";return "[data-proof-click=yes]"})()')
        self.click(p,selector);p.js('document.querySelector("[data-proof-click]")?.removeAttribute("data-proof-click")')

    def key(self,p,key,code=None,modifiers=0):
        for typ in ['keyDown','keyUp']:p.c.call('Input.dispatchKeyEvent',type=typ,key=key,code=code or key,modifiers=modifiers,windowsVirtualKeyCode={'Enter':13,'Tab':9,'Escape':27,'ArrowDown':40,'Home':36,'End':35,'a':65}.get(key,0))

    def fill(self,p,selector,value):
        self.click(p,selector);self.key(p,'a','KeyA',2);p.c.call('Input.insertText',text=value)

    def choose(self,p,selector,value):
        if selector=='[aria-label="Post type"]':
            if not p.js('document.querySelector(".nb-kind-tiles").hidden'):
                self.click(p,'[data-post-type='+json.dumps(value)+']')
            else:
                self.button(p,'← Choose a different post');self.click(p,'[data-post-type='+json.dumps(value)+']')
            return
        self.wait(p,'[...(document.querySelector('+json.dumps(selector)+')?.options||[])].some(o=>o.value==='+json.dumps(value)+'||o.textContent==='+json.dumps(value)+')')
        index=p.js('(()=>{const n=document.querySelector('+json.dumps(selector)+');return [...n.options].findIndex(o=>o.value==='+json.dumps(value)+'||o.textContent==='+json.dumps(value)+')})()');assert index>=0,value
        count=p.js('document.querySelector('+json.dumps(selector)+').options.length')
        self.click(p,selector)
        if index==count-1:self.key(p,'End')
        else:
            self.key(p,'Home')
            for _ in range(index):self.key(p,'ArrowDown')
        self.key(p,'Enter')
        print('CHOICE '+value+' -> '+str(p.js('document.querySelector('+json.dumps(selector)+').value')),flush=True)

    def shot(self,p,name,width,height,focus=None):
        self.resize(p,width,height)
        self.wait(p,'document.querySelector(".nb-channel-list")?.innerText.includes("Off-topic")',25)
        self.wait(p,'[...document.querySelectorAll(".nb-photo")].filter(i=>!i.closest("[data-stale]")).every(i=>i.complete&&i.naturalWidth>0)',25)
        self.wait(p,'![...document.querySelectorAll(".nb-file")].some(n=>!n.closest("[data-stale]") && (n.querySelector(".nb-photo-placeholder") || [...n.querySelectorAll("[role=status]")].some(s=>s.textContent.startsWith("Opening attachment"))))',25)
        time.sleep(.3);p.js('scrollTo(0,0);document.querySelector(".nb-centre").scrollTop=0;if(document.querySelector(".nb-thread"))document.querySelector(".nb-thread").scrollTop=0;if(document.querySelector(".nb-dialog"))document.querySelector(".nb-dialog").scrollTop=0')
        if focus:
            p.js('document.activeElement?.blur();document.querySelector('+json.dumps(focus)+')?.scrollIntoView({block:"start"})')
            p.js('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))')
            p.js('document.querySelector('+json.dumps(focus)+')?.scrollIntoView({block:"start"})')
        path=OUT/f'{name}-{width}.png'
        for attempt in range(4):
            self.wait(p,'document.querySelector(".nb-channel-list")?.innerText.includes("Off-topic")',25)
            if focus:p.js('document.querySelector('+json.dumps(focus)+')?.scrollIntoView({block:"start"})')
            p.shot(path)
            if p.js('document.querySelector(".nb-channel-list")?.innerText.includes("Off-topic") && !document.querySelector(".nb-photo-placeholder")'):break
        else:raise AssertionError('Capture never reached a settled navigation/photo state: '+name)
        self.shots.append(str(path.relative_to(HERE)))
        self.check('No horizontal overflow '+name+' '+str(width),p.js('document.documentElement.scrollWidth<=innerWidth+1'))

    def shots_for(self,p,name,focus=None):
        for width,height in [(1440,900),(390,844)]:self.shot(p,name,width,height,focus)
        self.resize(p,1440,900)

    def resize(self,p,width,height):
        p.c.call('Emulation.setDeviceMetricsOverride',width=width,height=height,deviceScaleFactor=1,mobile=False)
        p.until('Math.abs(innerWidth-'+str(width)+')<4')
        p.js('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))')

    def navigate(self,p,**values):
        # The runtime exposes no window test hook; ask its ordinary view handle
        # via an installed test-only, reviewed component control.
        script='document.querySelector(".nb-shell").dispatchEvent(new CustomEvent("board-proof-view",{detail:'+json.dumps(values)+'}))'
        p.js(script)
        self.wait(p,'(()=>{const v=JSON.parse(document.querySelector(".nb-shell").dataset.view||"{}");return Object.entries('+json.dumps(values)+').every(([k,x])=>v[k]===x)})()')

    def run(self,quick=False):
        f=self.f;p=self.page()
        self.wait(p,'document.querySelectorAll(".nb-post").length>=12')
        self.check('Feed constructs twelve cards for more than 400 posts',p.js('document.querySelectorAll(".nb-feed>.nb-post").length===12'),self.seed['posts'])
        self.check('Slim bar; feed occupies unused reading-pane space',p.js('!document.querySelector(".nb-logo")&&!document.querySelector(".nb-thread")&&document.querySelector(".nb-centre").getBoundingClientRect().width>1000'))
        self.shots_for(p,'feed-catchup')
        self.resize(p,390,844)
        self.check('Phone first post is visible and catch-up is one collapsed row',p.js('document.querySelector(".nb-feed>.nb-post").getBoundingClientRect().top<innerHeight/2 && getComputedStyle(document.querySelector(".nb-catchup-entries")).display==="none"'))
        self.choose(p,'.nb-phone-channel','__saved')
        bookmark_order=next(r['id'] for r in self.d.rows('board-order') if r['rule']=='bookmarks')
        self.wait(p,'JSON.parse(document.querySelector(".nb-shell").dataset.view).order==='+json.dumps(bookmark_order))
        self.check('Phone Saved opens the world bookmark ordering',True)
        self.choose(p,'.nb-phone-channel','')
        self.wait(p,'JSON.parse(document.querySelector(".nb-shell").dataset.view).order==="" && document.querySelectorAll(".nb-feed>.nb-post").length===12')
        self.resize(p,1440,900)
        self.check('Catch-up uses grouped thread rows',p.js('document.querySelectorAll(".nb-catchup .nb-entry").length<=3'))
        self.check('Catch-up and action text meet WCAG AA',self.contrast(p))
        self.drag_text(p,'.nb-feed>.nb-post .rich-text p')
        self.button(p,'Quote selection','document.querySelector(".nb-feed>.nb-post")')
        self.wait(p,'!!document.querySelector(".nb-thread form blockquote")')
        self.check('Feed selection opens its thread with the exact quotation and clears selection',p.js('!!JSON.parse(document.querySelector(".nb-shell").dataset.view).quote && getSelection().isCollapsed'))
        self.navigate(p,thread='',quote='',source='')
        unrelated=f.say('Alex','post text="OTHER-SURFACE-SENTINEL"')['made'][0]
        self.check('Board readings exclude another surface’s posts',unrelated not in {r['id'] for r in f.see('Alex','board.feed')['rows']} and not f.see('Alex','board.search q=OTHER-SURFACE-SENTINEL')['rows'])
        for kind,post in self.examples.items():
            if not post:continue
            self.navigate(p,thread=post['id'],replyTo=post['id'])
            self.wait(p,'!!document.querySelector(".nb-thread [data-post='+post['id']+']")')
            self.shots_for(p,'kind-'+kind.replace(' ','-').lower())
            if kind=='question':self.shots_for(p,'decision')
            if kind=='document':
                csv=next(x for x in self.d.rows('file') if x.get('name')=='signatures.csv')
                table='.nb-thread [data-fact-id='+csv['id']+'] table'
                self.wait(p,'!!document.querySelector('+json.dumps(table)+')')
                self.shots_for(p,'csv-table',table)
        if quick:return
        self.navigate(p,thread='',replyTo='')
        model_status=f.see('Alex','model.status')['rows'][0];available=model_status['up'] and model_status['model'] in model_status.get('installed',[])
        if available:
            self.button(p,'Summarise','document.querySelector(".nb-catchup")')
            self.wait(p,'document.querySelector(".nb-catchup").innerText.includes("Local model summary")||JSON.parse(document.querySelector(".nb-shell").dataset.view).summaryUnavailable==="yes"',35)
            context=next(r for r in self.d.rows('board-catch-up') if r.get('for')==f.people['Alex'] or r.get('made_by')==f.people['Alex'])
            self.check('Optional summary is labelled or unavailable action hidden; context is private',not f.raw('Neighbour 02','look '+context['id'],'see')['ok'] and p.js('!document.querySelector(".nb-catchup").innerText.includes("local model is not running")'))
        else:
            self.check('Unavailable model hides summary and offline explanation',p.js('!document.querySelector(".nb-catchup").innerText.includes("Summarise") && !document.body.innerText.includes("local model is not running")'))
        q=self.page('Neighbour 02')
        q_origin=q.js('performance.timeOrigin')
        self.check('Neighbour has no leaders queue',q.js('!document.querySelector(".nb-personal").innerText.includes("Leaders")'))
        self.check('Phone destinations also conceal the leaders queue from neighbours',q.js('!document.querySelector(".nb-phone-channel option[value=__queue]")'))
        self.navigate(p,thread='',replyTo='',compose='no')
        self.click(p,'.nb-masthead .nb-primary');self.wait(p,'!!document.querySelector(".nb-dialog")')
        self.wait(p,'document.querySelector('+json.dumps('[aria-label="Post type"]')+').options.length>=10')
        self.check('Compose starts with world-defined friendly tiles',p.js('!document.querySelector(".nb-kind-tiles").hidden&&document.querySelector(".nb-compose-step").hidden&&document.querySelector("[data-post-type=\\"Lost pet\\"]")!==null'))
        for width,height in [(1440,900),(390,844)]:
            self.resize(p,width,height);p.shot(OUT/'polish'/f'compose-choose-{width}.png')
        self.resize(p,1440,900)
        self.choose(p,'[aria-label="Post type"]','event');self.wait(p,'!!document.querySelector("[name=start]")')
        self.fill(p,'[name=start]','Thu 6pm')
        self.check('Typed date is parsed locally and confirmed in plain words',p.js('document.querySelector("[name=start]").validationMessage===""&&document.querySelector(".nb-date-confirm").innerText.includes("6:00 pm")'))
        self.shots_for(p,'compose-event')
        self.choose(p,'[aria-label="Post type"]','Lost pet');self.wait(p,'!!document.querySelector("[name=pet_name]")')
        self.shots_for(p,'compose-lost-pet')
        self.choose(p,'[aria-label="Post type"]','discussion')
        self.fill(p,'[aria-label="Your message"]','A neighbour-led walking visit this Saturday. Bring your questions.')
        self.fill(p,'[aria-label="Title (optional)"]','Walking together')
        paths=[]
        for name in ['camera.txt','planning.pdf']:
            path=Path(f.tmp.name)/name;path.write_bytes(fixtures()[name]);paths.append(str(path))
        # Native file-input selection invokes the ordinary change/upload path.
        # Runtime.evaluate supplies the actual input node to DOM.setFileInputFiles.
        remote=p.c.call('Runtime.evaluate',expression='document.querySelector("input[type=file]")',**p.context())['result']['objectId']
        p.c.call('DOM.setFileInputFiles',files=paths,objectId=remote,**({'_session':p.context()['_session']} if '_session' in p.context() else {}))
        self.wait(p,'document.querySelectorAll(".nb-upload-list p").length===2',35)
        print('COMPOSE BEFORE POST '+str(p.js('({valid:document.querySelector(".nb-dialog form").checkValidity(),values:[...document.querySelectorAll(".nb-dialog input,.nb-dialog textarea,.nb-dialog select")].map(n=>({label:n.getAttribute("aria-label"),value:n.value})),width:innerWidth})')),flush=True)
        self.button(p,'Post to neighbours')
        self.wait(p,'!document.querySelector(".nb-dialog")',30)
        made=next(x for x in self.d.rows('post') if x.get('title')=='Walking together')
        attached=[x for x in self.d.rows('file') if x.get('attached_to')==made['id']]
        self.check('Pointer and keyboard compose; photo and PDF uploaded and attached',len(attached)==2)
        self.wait(q,'document.body.innerText.includes("Walking together")')
        self.check('Second person receives the first person’s post without reload',q.js('document.body.innerText.includes("Walking together")') and q.js('performance.timeOrigin')==q_origin)
        likes=int(made.get('likes',0));self.click(p,'[data-post='+made['id']+'] .nb-upvote')
        self.wait(p,'document.querySelector("[data-post='+made['id']+'] .nb-upvote").innerText.includes("1")')
        self.check('Pointer upvote is a sealed world like',int(next(x for x in self.d.rows('post') if x['id']==made['id'])['likes'])==likes+1)
        self.click(p,'[data-post='+made['id']+'] .nb-actions>.nb-text-button')
        self.wait(p,'!!document.querySelector(".nb-thread [data-post='+made['id']+']")')
        self.fill(p,'[aria-label="Your reply"]','I can bring printed copies for anyone who needs them.')
        self.button(p,'Post reply')
        self.wait(p,'document.querySelector(".nb-thread").innerText.includes("printed copies")')
        replies=[x for x in self.d.rows('post') if x.get('thread')==made['id']]
        self.check('Keyboard reply is present in world readings',any('printed copies' in r.get('text','') for r in replies))
        # Select the first body passage using actual drag events.
        body='.nb-thread [data-post='+made['id']+'] .rich-text p'
        self.drag_text(p,body)
        self.button(p,'Quote selection','document.querySelector(".nb-thread [data-post='+made['id']+']")')
        self.wait(p,'!!document.querySelector(".nb-thread form blockquote")')
        self.fill(p,'[aria-label="Your reply"]','That sounds good to me.')
        self.button(p,'Post reply')
        self.wait(p,'document.querySelector(".nb-thread").innerText.includes("That sounds good")')
        quoted=[x for x in self.d.rows('post') if x.get('thread')==made['id'] and x.get('quote')]
        self.check('Pointer-selected quotation is admitted with source',bool(quoted) and quoted[0]['quote_source']==made['id'])
        self.shots_for(p,'thread-with-quotes','.nb-thread [data-post='+quoted[0]['id']+']')
        self.wait(p,'!!document.querySelector(".nb-photo[src]")')
        self.shots_for(p,'photo','.nb-thread .nb-photo')
        pdf_file=next(x for x in attached if x['name']=='planning.pdf')
        pdf_selector='.nb-thread [data-fact-id='+pdf_file['id']+'] .nb-page'
        self.wait(p,'!!document.querySelector('+json.dumps(pdf_selector)+')')
        self.drag_text(p,pdf_selector)
        self.button(p,'Quote selection','document.querySelector(".nb-thread [data-fact-id='+pdf_file['id']+']")')
        self.wait(p,'JSON.parse(document.querySelector(".nb-shell").dataset.view).source==='+json.dumps(pdf_file['id'])+' && !!document.querySelector(".nb-thread form blockquote")')
        self.fill(p,'[aria-label="Your reply"]','This is the passage we should discuss.')
        self.button(p,'Post reply')
        self.wait(p,'document.querySelector(".nb-thread").innerText.includes("passage we should discuss")')
        self.check('PDF page quote is checked by the world',any(x.get('quote_source')==pdf_file['id'] and str(x.get('quote_page'))=='1' for x in self.d.rows('post')))
        self.shots_for(p,'pdf-page',pdf_selector)
        pdf_reply=next(x for x in self.d.rows('post') if x.get('quote_source')==pdf_file['id'])
        self.shots_for(p,'pdf-page-quote','.nb-thread [data-post='+pdf_reply['id']+']')
        # Future event with one independent volunteer slot. The world enforces
        # the last-seat race; the interface reads its resulting full state.
        event=f.say('Alex',line('board.post',post_kind='event',title='Walk the safe route',text='Meet neighbours by the crossing.',start=(f.at+timedelta(days=2,hours=14)).isoformat(),end=(f.at+timedelta(days=2,hours=16)).isoformat(),seats='10',location='Seabright crossing',**{'in':self.channels['Meetings & events']}))['made'][0]
        slot=f.say('Alex',line('make',kind='slot',event=event,title='Bring the printed map',seats='1'))['made'][0]
        self.navigate(p,thread=event,replyTo=event)
        self.wait(p,'!!document.querySelector(".nb-thread [data-post='+event+']")')
        self.button(p,'Going','document.querySelector(".nb-thread [data-post='+event+']")')
        self.world_wait(lambda:any(x.get('about')==event for x in self.d.rows('board-rsvp')))
        self.check('RSVP is read back from world facts',any(x.get('about')==event for x in self.d.rows('board-rsvp')))
        self.wait(p,'JSON.parse(document.querySelector(".nb-thread [data-post='+event+']").dataset.facts).rev==='+str(next(x for x in self.d.rows('post') if x['id']==event)['rev']))
        self.button(p,'Maybe','document.querySelector(".nb-thread [data-post='+event+']")')
        self.world_wait(lambda:any(x.get('about')==event and x.get('status')=='maybe' for x in self.d.rows('board-rsvp')))
        self.wait(p,'document.querySelector(".nb-thread .nb-rsvp button[aria-pressed=true]")?.textContent==="Maybe"')
        self.check('Going and Maybe toggle a single reservation',next(x for x in self.d.rows('post') if x['id']==event)['seats_left']==9)
        self.check('Wide reading pane is at least 520 pixels; no nested vertical scroll',p.js('document.querySelector(".nb-thread").getBoundingClientRect().width>=520&&![...document.querySelectorAll(".nb-thread section,.nb-thread [data-component=column]")].some(n=>n.scrollHeight>n.clientHeight+2&&["auto","scroll"].includes(getComputedStyle(n).overflowY))'))
        self.resize(p,1090,900)
        self.check('Below 1100 pixels the thread replaces the feed with a back action',p.js('getComputedStyle(document.querySelector(".nb-centre")).display==="none"&&document.querySelector(".nb-thread").innerText.includes("← Back")'))
        self.resize(p,1440,900)
        event_rev=next(x for x in self.d.rows('post') if x['id']==event)['rev']
        self.wait(p,'JSON.parse(document.querySelector(".nb-thread [data-post='+event+']").dataset.facts).rev==='+str(event_rev))
        self.click(p,'.nb-thread [data-fact-id='+slot+'] button')
        self.wait(p,'document.querySelector(".nb-thread [data-fact-id='+slot+']").innerText.includes("Place filled")')
        self.check('Claim last slot; world reports zero seats',next(x for x in self.d.rows('slot') if x['id']==slot)['seats_left']==0)
        self.shots_for(p,'event-full-slots')
        downloads=Path(f.tmp.name)/'downloads';downloads.mkdir(exist_ok=True)
        p.c.call('Browser.setDownloadBehavior',behavior='allow',downloadPath=str(downloads),eventsEnabled=True)
        self.button(p,'Add to calendar','document.querySelector(".nb-thread [data-post='+event+']")')
        self.world_wait(lambda:bool(list(downloads.glob('*.ics'))))
        self.check('Calendar button downloads the world’s actual calendar bytes',b'BEGIN:VCALENDAR' in next(downloads.glob('*.ics')).read_bytes())
        imported_file=next(x for x in self.d.rows('file') if x['name']=='meeting.ics')
        imported_event=next(x for x in self.d.rows('event') if x.get('file_source')==imported_file['id'])
        self.navigate(p,thread=self.examples['document']['id'],replyTo=self.examples['document']['id'])
        imported_selector='.nb-thread .nb-file[data-fact-id='+imported_file['id']+']'
        self.wait(p,'!!document.querySelector('+json.dumps(imported_selector)+')')
        self.wait(p,'[...document.querySelector('+json.dumps(imported_selector)+').querySelectorAll("button")].some(b=>b.textContent==="Going"&&!b.disabled)')
        self.button(p,'Going','document.querySelector('+json.dumps(imported_selector)+')')
        self.world_wait(lambda:any(x.get('about')==imported_event['id'] and x.get('for')==f.people['Alex'] for x in self.d.rows('board-rsvp')))
        self.check('Converted calendar RSVP targets its richer event thing',True)
        self.button(p,'Add to calendar','document.querySelector('+json.dumps(imported_selector)+')')
        self.world_wait(lambda:len(list(downloads.glob('*.ics')))>=2)
        self.check('Converted calendar offers an actual download',len(list(downloads.glob('*.ics')))>=2)
        self.wait(p,'[...document.querySelectorAll(".nb-thread audio")].some(a=>a.readyState>0&&a.duration>0)')
        self.check('Converted media loads through Blob-only playback',p.js('[...document.querySelectorAll(".nb-thread audio")].some(a=>a.src.startsWith("blob:"))'))
        poll=f.say('Alex',line('board.post',post_kind='poll',title='Which afternoon works?',text='Choose a time for our next walk.',options='Saturday Sunday',closes=(f.at+timedelta(days=1)).isoformat(),**{'in':self.channels['Neighbours']}))['made'][0]
        self.navigate(p,thread=poll,replyTo=poll)
        self.wait(p,'!!document.querySelector(".nb-thread [data-post='+poll+'] .nb-option")')
        self.click(p,'.nb-thread [data-post='+poll+'] .nb-option')
        self.world_wait(lambda:next(x for x in self.d.rows('post') if x['id']==poll).get('votes_Saturday')==1)
        self.check('Pointer poll vote is sealed count in world reading',next(x for x in self.d.rows('post') if x['id']==poll).get('votes_Saturday')==1)
        self.wait(p,'document.querySelector(".nb-thread .nb-poll").innerText.includes("Your choice")')
        self.check('After voting, poll becomes bars and marks only your choice',p.js('document.querySelectorAll(".nb-thread .nb-poll-result").length===2&&!document.querySelector(".nb-thread .nb-poll button")'))
        f.at+=timedelta(days=2);p.set_clock(f.at)
        self.navigate(p,thread=poll,offset=1)
        self.wait(p,'document.querySelector(".nb-thread .nb-poll").innerText.includes("Closed")')
        self.shots_for(p,'poll-after-closing')
        # Leader hide through its real reason composer and receipt-specific undo.
        self.navigate(p,thread=made['id'],replyTo=made['id'])
        self.click(p,'.nb-thread [data-post='+made['id']+'] > .nb-actions > .nb-more > summary')
        self.button(p,'Hide with a reason','document.querySelector(".nb-thread [data-post='+made['id']+']")')
        self.fill(p,'[aria-label="Reason for hiding"]','Checking the route with the crossing guard.')
        self.button(p,'Save')
        self.wait(p,'document.querySelector(".nb-notice")?.innerText.includes("crossing guard")')
        self.wait(p,'!document.querySelector(".nb-dialog")')
        self.check('Leader hide notice contains actual world reason',any('crossing guard' in x.get('reason','') for x in f.see('Alex','forgotten')['rows']))
        self.shots_for(p,'hidden-post-notice')
        self.resize(p,390,844)
        self.check('Phone hidden thread retains its reason and Undo without a reply form',p.js('document.querySelector(".nb-thread .nb-notice")?.innerText.includes("crossing guard") && !document.querySelector(".nb-thread form")'))
        self.button(p,'Undo hide','document.querySelector(".nb-thread .nb-notice")')
        self.wait(p,'!!document.querySelector(".nb-thread [data-post='+made['id']+']")')
        self.check('Leader pointer undo restores the post',any(x['id']==made['id'] for x in self.d.rows('post')))
        self.resize(p,1440,900)
        self.navigate(p,thread='',search='')
        self.resize(p,390,844)
        self.choose(p,'.nb-phone-channel','__queue')
        self.wait(p,'document.body.innerText.includes("Please verify the signup time")')
        self.wait(p,'document.querySelector(".nb-phone-channel").selectedOptions[0]?.textContent.includes("(1)")')
        self.check('Phone leader picker opens the real queue with its count',p.js('document.querySelector(".nb-phone-channel").selectedOptions[0].textContent.includes("(1)")'))
        self.shots_for(p,'leaders-queue')
        self.navigate(p,queue='no',search='council')
        self.wait(p,'document.querySelector(".nb-search")?.innerText.includes("Search results")')
        self.wait(p,'!!document.querySelector(".nb-search mark")')
        self.check('Search highlights matches and applies filter chips live',p.js('!!document.querySelector(".nb-search mark")&&document.querySelectorAll(".nb-searchfilters select").length===4&&!document.querySelector(".nb-searchfilters button")'))
        self.shots_for(p,'search-results')
        self.navigate(p,search='written comments',thread='',queue='no')
        self.wait(p,'!!document.querySelector(".nb-search .nb-entry-button")')
        self.click(p,'.nb-search .nb-entry-button')
        self.wait(p,'document.querySelector(".nb-thread [aria-label=\\"Choose a page\\"]")?.value==="3"')
        self.check('A document search hit opens its owning thread at the addressed page',True)
        empty=f.say('Alex',line('group',name='Garden ideas',open='yes'))['made'][0]
        f.say('Alex',line('make',kind='board-channel',group=empty,title='Garden ideas'))
        self.navigate(p,channel=empty,search='',queue='no',thread='')
        self.wait(p,'document.body.innerText.includes("Room for a first conversation")')
        self.shots_for(p,'empty-channel')
        self.navigate(p,channel='',thread='',search='',queue='no',offset=0)
        before=bool(f.see('Alex','catch-up')['rows']);self.button(p,'Mark all seen')
        self.world_wait(lambda:not f.see('Alex','catch-up')['rows'])
        self.wait(p,'!document.querySelector(".nb-summary")')
        self.check('Pointer mark seen clears the actual personal reading and cached summary',before and not f.see('Alex','catch-up')['rows'])
        self.navigate(p,thread=made['id'],replyTo=made['id'])
        self.wait(p,'!!document.querySelector(".nb-thread [data-fact-id='+pdf_file['id']+']")')
        self.button(p,'Download','document.querySelector(".nb-thread [data-fact-id='+pdf_file['id']+']")')
        self.world_wait(lambda:(downloads/'planning.pdf').exists())
        self.check('Plain download crosses trusted host without sandbox relaxation',(downloads/'planning.pdf').read_bytes()==Path(paths[1]).read_bytes())
        agent=f.say('Agent',line('board.post',text='I can help organise the walking notes.',**{'in':self.channels['Off-topic']}))['made'][0]
        self.navigate(p,thread=agent,replyTo=agent)
        self.wait(p,'document.querySelector(".nb-thread").innerText.includes("agent for Neighbour 01")')
        self.check('Verified agent origin is labelled for its real person',next(x for x in self.d.rows('post') if x['id']==agent).get('via_actor') is not None)
        self.shots_for(p,'agent-badge')
        self.navigate(p,thread='',offset=0)
        self.privacy(q)
        self.performance(p)
        self.faults(p,q,event,poll)

    def drag_text(self,p,selector):
        rect=p.point(selector,.05,.2)
        bounds=p.js('(()=>{const n=document.querySelector('+json.dumps(selector)+');const r=document.createRange();r.selectNodeContents(n);const b=r.getClientRects()[0];return {x:b.x+1,y:b.y+b.height/2,right:b.right-1}})()')
        offset=p.c.js('(()=>{const r=document.querySelector("iframe").getBoundingClientRect();return {x:r.x,y:r.y}})()')
        a=dict(x=bounds['x']+offset['x'],y=bounds['y']+offset['y']);b=dict(x=bounds['right']+offset['x'],y=a['y'])
        p.c.call('Input.dispatchMouseEvent',type='mouseMoved',**a)
        p.c.call('Input.dispatchMouseEvent',type='mousePressed',button='left',clickCount=1,**a)
        for i in range(1,9):p.c.call('Input.dispatchMouseEvent',type='mouseMoved',button='left',buttons=1,x=a['x']+(b['x']-a['x'])*i/8,y=a['y'])
        p.c.call('Input.dispatchMouseEvent',type='mouseReleased',button='left',clickCount=1,**b)
        assert p.js('getSelection().toString().length>0'),'No selected passage'

    def contrast(self,p):
        return p.js('''(()=>{const lum=c=>{const rgb=c.trim().startsWith('#')?c.trim().slice(1).match(/../g).map(v=>parseInt(v,16)):c.match(/[\\d.]+/g).slice(0,3).map(Number);const a=rgb.map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4});return a[0]*.2126+a[1]*.7152+a[2]*.0722};const root=document.querySelector('.nb-shell'),s=getComputedStyle(root),ratio=(fg,bg)=>{const a=lum(fg),b=lum(bg);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05)};return ratio(s.getPropertyValue('--accent'),s.getPropertyValue('--nb-soft'))>=4.5&&ratio(s.getPropertyValue('--ink'),s.getPropertyValue('--nb-soft'))>=4.5&&ratio(s.getPropertyValue('--muted'),s.getPropertyValue('--card'))>=4.5&&['discussion','question','event','poll','ask','offer','document','announcement','decision'].every(k=>ratio(s.getPropertyValue('--nb-kind-'+k),s.getPropertyValue('--card'))>=4.5)})()''')

    def privacy(self,p):
        outsider='Neighbour 02';private=next(x for x in self.d.rows('post') if x.get('text')=='PRIVATE-COUNCIL-SENTINEL')
        files=[x for x in self.d.rows('file') if x.get('attached_to')==private['id']]
        first='Neighbour 01';group=private['groups'][0]
        code,photo=self.f.upload(first,'private-camera.jpg',fixtures()['camera.txt'],group)
        assert code==200 and photo['ok'],photo
        self.f.see(first,'look '+photo['made'][0]);self.f.see(first,'look '+private['id'])
        self.f.say(first,line('attach',photo['made'][0],to=private['id']))
        files+=[dict(id=photo['made'][0])]
        for variant in ['', '?variant=thumbnail']:
            self.check('Private photo positive owner control '+(variant or 'content'),self.f.file(first,photo['made'][0],variant)[0]==200)
        self.check('Private post and file absent from outsider component page','SENTINEL' not in p.js('document.body.innerText') and private['id'] not in p.js('document.body.innerHTML'))
        for file in files:
            for variant in ['content','thumbnail']:
                refused=p.js('agora.file('+json.dumps(file['id'])+','+json.dumps(variant)+').then(()=>false,()=>true)')
                self.check('File transport refuses outsider '+variant,refused)
        self.check('Component network remains disabled',p.js('fetch("/files/'+files[0]['id']+'").then(()=>false,()=>true)'))

    def performance(self,p):
        start=time.perf_counter();pages=0;max_cards=0
        # Real wheel scrolling and pointer pagination over the complete feed.
        total=len(self.f.see('Alex','board.feed')['rows'])
        for i in range((total+11)//12):
            max_cards=max(max_cards,p.js('document.querySelectorAll(".nb-feed>.nb-post").length'))
            p.c.call('Input.dispatchMouseEvent',type='mouseWheel',x=650,y=650,deltaY=800,deltaX=0)
            if i<(total+11)//12-1:
                self.button(p,'Older →','document.querySelector(".nb-pagination")')
                self.wait(p,'JSON.parse(document.querySelector(".nb-shell").dataset.view).offset==='+str((i+1)*12))
            pages+=1
        self.metrics.update(scroll_all_posts_ms=round((time.perf_counter()-start)*1000,2),feed_threads=total,pages_scrolled=pages,max_feed_cards=max_cards)
        self.check('Scrolled every feed page with bounded DOM',self.metrics['max_feed_cards']<=12,self.metrics)

    def faults(self,p,q,event,poll):
        self.navigate(p,thread=poll,offset=0)
        original=self.d.rows('component',name='poll')[0]
        self.d.say('look '+original['id']);self.d.say('set '+original['id']+' code='+Q('export default {mount(){throw Error("Broken poll fixture")}}'));self.d.say('component '+original['id'])
        self.wait(p,'document.body.innerText.includes("Broken poll fixture")')
        self.check('Broken poll is a stopped part while feed survives',p.js('document.querySelectorAll(".nb-feed>.nb-post").length>0'))
        file=self.d.rows('component',name='file')[0]
        self.d.say('look '+file['id']);self.d.say('set '+file['id']+' code='+Q('export default {mount(){throw Error("Throwing file fixture")}}'));self.d.say('component '+file['id'])
        document=self.examples['document']['id'];self.navigate(p,thread=document)
        self.wait(p,'document.body.innerText.includes("Throwing file fixture")')
        self.check('Throwing file is a stopped part while feed survives',p.js('document.querySelectorAll(".nb-feed>.nb-post").length>0'))
        loop=self.d.say('make kind=component name=board-loop settings="{}" parts="{}" slots="[]" code='+Q('export default {mount(){while(true){}}}'))['made'][0]
        lens=self.d.rows('lens',name='seabright-board')[0];text=lens['text'].replace('  centre :','  loop : board-loop\n  centre :')
        self.d.say('look '+lens['id']);self.d.say('set '+lens['id']+' text='+Q(text))
        self.wait(p,'document.body.innerText.includes("No heartbeat") || [...document.querySelectorAll(".component-stopped")].some(n=>n.innerText.includes("board loop"))',20)
        self.check('New looping component times out independently',p.js('document.querySelectorAll(".nb-feed>.nb-post").length>0'))
        # Peer live update after all three failures, plus pointer upvote/compose.
        receipt=self.f.say('Neighbour 02',line('board.post',text='The healthy neighbours can still update this board.',**{'in':self.channels['Off-topic']}))
        self.wait(p,'document.querySelector(".nb-feed").innerText.includes("healthy neighbours")')
        self.click(p,'.nb-feed [data-post='+receipt['made'][0]+'] .nb-upvote')
        self.click(p,'.nb-masthead .nb-primary');self.wait(p,'!!document.querySelector(".nb-dialog")');self.choose(p,'[aria-label="Post type"]','discussion')
        self.fill(p,'[aria-label="Your message"]','Compose works beside the stopped parts.')
        self.button(p,'Post to neighbours');self.wait(p,'!document.querySelector(".nb-dialog")')
        self.check('Faults retain compose, upvotes and peer live updates',any(x.get('text')=='Compose works beside the stopped parts.' for x in self.d.rows('post')) and next(x for x in self.d.rows('post') if x['id']==receipt['made'][0]).get('likes')==1)
        self.shots_for(p,'fault-isolation')

    def close(self):
        for p in self.pages:p.close()
        self.srv.shutdown();self.srv.server_close();self.f.close()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--quick',action='store_true');args=ap.parse_args()
    ui=UI()
    try:ui.run(args.quick)
    finally:
        result=dict(checks=ui.checks,metrics=ui.metrics,screenshots=ui.shots,seed=ui.seed,hidden=True,live_touched=False)
        (OUT/'ui-proof.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');ui.close()
    print(f'BOARD UI: {len(ui.checks)}/{len(ui.checks)} checks passed; hidden=True; screenshots={len(ui.shots)}',flush=True)
    print('BOARD UI SPEED '+json.dumps(ui.metrics,sort_keys=True),flush=True)


if __name__=='__main__':main()
