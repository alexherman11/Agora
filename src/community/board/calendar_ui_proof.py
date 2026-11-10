"""Hidden Chromium acceptance for Meetings & events' calendar, on a disposable world.

Alex opens Meetings & events, sees a month calendar, adds an event with the form;
Bea (another member, her own hidden browser) sees it and RSVPs in one click; Alex
sees her by name. Week view, opening the conversation, the shared right-click ask
menu, light colours and a phone width are checked too. Nothing live, no windows.
"""
import json
import os
import re
import sys
import threading
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
LAB=HERE.parents[1]/'agora'
DESKTOP=LAB.parent/'desktop/kernel-desktop'
sys.path[:0]=[str(HERE),str(LAB),str(DESKTOP),str(LAB/'tests')]
from proof import Proof,install
from ui_install import install_ui,taskboard,Q
from protocol import line
from painter.browser import Page
from kernel.door import EntryClient
import kdesk
from ui_proof import UI

OUT=HERE/'evidence/calendar'


class CalendarUI(UI):
    def __init__(self):
        OUT.mkdir(parents=True,exist_ok=True)
        # metrics pre-filled: the inherited page() then leaves the board's own first-paint evidence alone.
        self.f=f=Proof();self.pages=[];self.checks=[];self.shots=[];self.metrics={'first_paint_upper_bound_ms':None,'cold_start_to_board_ms':None}
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
        # An already-installed world without the new facts, like Alex's: install_ui must bring them.
        ids=install(lambda s:f.say('Alex',s),lambda s:f.see('Alex',s))
        for c in self.d.rows('board-channel'):
            if c.get('opens'):self.d.say('look '+c['id']);self.d.say('set '+c['id']+' opens="" opens_label=""')
        for k in self.d.rows('kind',name='event'):self.d.say('look '+k['id']);self.d.say('set '+k['id']+' defaults=""')
        self.ids=install_ui(self.d);self.ids['channels']=ids['channels']
        f.join('Bea')
        self.meetings=ids['channels']['Meetings & events']

    def shot(self,p,name,width=1440,height=900):
        self.resize(p,width,height);time.sleep(.3)
        path=OUT/f'{name}-{width}.png';p.shot(path);self.shots.append(str(path.relative_to(HERE)))
        self.check('No horizontal overflow '+name+' '+str(width),p.js('document.documentElement.scrollWidth<=innerWidth+1'))

    def right_click(self,p,selector):
        point=p.point(selector)
        for typ in ('mouseMoved','mousePressed','mouseReleased'):
            p.c.call('Input.dispatchMouseEvent',type=typ,button='right' if typ!='mouseMoved' else 'none',clickCount=1,**point)

    def press(self,p,label,until,within='document',tries=3):
        # A live repaint (another member's change arriving) can replace a button between
        # press and release; a person would press again, and so does the proof.
        for attempt in range(tries):
            try:
                self.button(p,label,within);self.wait(p,until,8);return attempt
            except AssertionError:
                if attempt==tries-1:raise

    def open_meetings(self,p):
        # The channel button may carry an unread count after its name.
        self.wait(p,'[...document.querySelectorAll(".nb-channel-list button")].some(b=>b.textContent.startsWith("Meetings & events"))')
        p.js('[...document.querySelectorAll(".nb-channel-list button")].find(b=>b.textContent.startsWith("Meetings & events")).dataset.proofChannel="yes"')
        self.click(p,'[data-proof-channel=yes]')
        self.wait(p,'!!document.querySelector(".cal .cal-grid")')

    def run(self):
        f,d=self.f,self.d
        channel=next(c for c in d.rows('board-channel') if c['group']==self.meetings)
        self.check('install_ui brings opens=calendar onto an installed channel',channel.get('opens')=='calendar')
        self.check('install_ui brings the event kind default seats',json.loads(d.rows('kind',name='event')[0].get('defaults') or '{}').get('seats')=='500')
        lens=d.rows('lens',name='seabright-board')[0]
        self.check('The board lens inherits the shared right-click ask menu',lens.get('right_click')=='ask')
        card=d.rows('component',name='calendar')[0]
        self.check('The calendar is a reviewed component card in the gallery',card.get('category')=='collections' and card.get('gestures')=='select add rsvp'
                   and card.get('reviewed_code') and 'calendar, month' in card.get('example',''))

        a=self.page('Alex')
        self.check('Before choosing, the board shows conversations',a.js('!document.querySelector(".cal") && !!document.querySelector(".nb-feed")'))
        self.open_meetings(a)
        self.check('Meetings & events opens a month calendar, not the feed',a.js('!document.querySelector(".nb-feed") && document.querySelectorAll(".cal-dow").length===7 && document.querySelectorAll(".cal-day").length>=28'))
        self.check('The month is the board clock\'s month, today marked',a.js('document.querySelector(".cal-head h2").textContent.includes("October 2026") && document.querySelector(".cal-day[data-today=yes]")?.dataset.date==="2026-10-22"'))
        self.check('The toolbar offers Calendar | Conversations, Calendar pressed',a.js('(()=>{const b=[...document.querySelectorAll(".nb-view")];return b.map(x=>x.textContent).join("|")==="Calendar|Conversations"&&b[0].getAttribute("aria-pressed")==="true"})()'))
        self.shot(a,'empty-month')

        # Add an event through the form, as Alex would.
        self.button(a,'＋ Add event')
        self.wait(a,'!!document.querySelector(".cal-form")')
        self.fill(a,'.cal-form input[name=title]','Garden workday')
        # Native date/time pickers: set their values as the picker does, then the input event.
        a.js('(()=>{for(const [n,v] of [["day","2026-10-24"],["from","10:00"],["to","12:30"]]){const i=document.querySelector(".cal-form input[name="+n+"]");i.value=v;i.dispatchEvent(new Event("input",{bubbles:true}))}})()')
        self.fill(a,'.cal-form input[name=where]','Corner garden, Murray St')
        self.fill(a,'.cal-form textarea[name=notes]','Bring gloves. Tea after.')
        self.shot(a,'add-form')
        self.button(a,'Add to calendar','document.querySelector(".cal-form")')
        self.world_wait(lambda:any(p.get('title')=='Garden workday' for p in d.rows('post')))
        event=next(p for p in d.rows('post') if p.get('title')=='Garden workday')
        expected=a.js('new Date(2026,9,24,10,0).toISOString().replace(/\\.\\d{3}Z$/,"Z")')
        self.check('The form made one event thing: title, when, where, notes, in the channel',event['post_kind']=='event' and event['start']==expected
                   and event.get('location')=='Corner garden, Murray St' and event['text']=='Bring gloves. Tea after.' and self.meetings in event.get('groups',[]),
                   dict(start=event['start'],expected=expected))
        self.wait(a,'!document.querySelector(".cal-form") && !!document.querySelector(".cal-day[data-date=\\"2026-10-24\\"] .cal-chip")')
        self.check('The event shows on its day and the day is selected',a.js('document.querySelector(".cal-day[aria-selected=true]").dataset.date==="2026-10-24" && document.querySelector(".cal-day[data-date=\\"2026-10-24\\"] .cal-chip").textContent.includes("Garden workday")'))
        self.check('The agenda shows when, where and notes',a.js('(()=>{const t=document.querySelector(".cal-side").innerText;return t.includes("Garden workday")&&t.includes("Corner garden")&&t.includes("Bring gloves")&&/10\\s?(am)?–12:30\\s?pm/i.test(t)})()'),
                   a.js('document.querySelector(".cal-side .cal-when")?.textContent'))

        # Another member sees it and RSVPs in one click.
        b=self.page('Bea')
        self.open_meetings(b)
        self.wait(b,'!!document.querySelector(".cal-day[data-date=\\"2026-10-24\\"] .cal-chip")')
        self.click(b,'.cal-day[data-date="2026-10-24"] .cal-chip')
        self.wait(b,'!!document.querySelector(".cal-side [data-rsvp=going]")')
        self.click(b,'.cal-side [data-rsvp=going]')
        self.world_wait(lambda:any(r.get('about')==event['id'] and r.get('status')=='going' for r in f.see('Bea','rows board-rsvp')['rows']))
        self.check('Bea RSVPs going in one click (a board-rsvp thing, one seat)',next(p for p in d.rows('post') if p['id']==event['id'])['seats_left']==499)
        self.wait(b,'document.querySelector(".cal-side [data-rsvp=going]")?.getAttribute("aria-pressed")==="true"')
        self.check('Bea\'s Going shows pressed and her chip is marked',b.js('document.querySelector(".cal-chip").dataset.yours==="going"'))
        self.shot(b,'bea-going')
        self.wait(a,'document.querySelector(".cal-side")?.innerText.includes("Going: Bea")',25)
        self.check('Alex sees who is coming by name',True)
        self.check('No ids in what the calendar shows',not re.search(r'\bbd\d+\b',a.js('document.querySelector(".cal").innerText')))

        # Week view.
        self.press(a,'Week','document.querySelectorAll(".cal-week .cal-col").length===7')
        self.check('Week view: seven days, the event on Saturday 24 with RSVP',a.js('(()=>{const c=document.querySelector(".cal-col[data-date=\\"2026-10-24\\"]");return !!c.querySelector(".cal-event [data-rsvp=going]")&&c.innerText.includes("Garden workday")})()'))
        self.shot(a,'week')
        self.press(a,'›','!!document.querySelector(".cal-col[data-date=\\"2026-10-31\\"]")')
        self.check('Next week steps seven days',a.js('!document.querySelector(".cal-event") && document.querySelector(".cal-head h2").textContent.replace(/\\s/g," ")==="Oct 25 – 31, 2026"'),a.js('document.querySelector(".cal-head h2").textContent'))
        self.press(a,'Today','!!document.querySelector(".cal-col[data-date=\\"2026-10-22\\"]")')
        self.press(a,'Month','!!document.querySelector(".cal-grid")')

        # Opening the conversation reuses the board's thread pane.
        self.click(a,'.cal-day[data-date="2026-10-24"] .cal-chip')
        self.press(a,'Open conversation','!!document.querySelector(".nb-thread [data-post=\\"'+event['id']+'\\"]")','document.querySelector(".cal-side")')
        self.check('Open conversation shows the event\'s thread beside the calendar',a.js('!!document.querySelector(".cal") && !!document.querySelector(".nb-thread textarea")'))
        self.shot(a,'conversation')
        self.press(a,'← Back','!document.querySelector(".nb-thread textarea")')

        # Shared right-click: the painter's ask menu, not a calendar-only menu.
        self.right_click(a,'.cal-day[data-date="2026-10-24"]')
        # Since dk1344 the one shared menu is drawn by the window host, outside the board's frame.
        a.c.until('!!document.querySelector(".ag-menu input[placeholder^=Ask]")')
        self.check('Right-click on the calendar opens the shared menu with Ask for a change',a.c.js('!!document.querySelector(".ag-menu")') and not a.js('!!document.querySelector(".ask-menu")'))
        self.key(a,'Escape')
        try:a.c.until('!document.querySelector(".ag-menu")',4)
        except AssertionError:a.c.js('document.querySelector(".ag-menu")?.remove();0')

        # Light theme.
        light=a.js('(()=>{const L=c=>{const [r,g,b]=c.match(/\\d+/g).map(Number);return (0.2126*r+0.7152*g+0.0722*b)/255};return ["cal-day","cal-event","cal-dow"].map(k=>L(getComputedStyle(document.querySelector("."+k)).backgroundColor))})()')
        self.check('Light theme: day, event and header backgrounds are light',min(light)>0.85,light)

        # Back to conversations, and a channel without a view stays a feed.
        self.press(a,'Conversations','!document.querySelector(".cal") && !!document.querySelector(".nb-feed")')
        self.check('Conversations shows the channel\'s posts, including the event',a.js('document.querySelector(".nb-feed").innerText.includes("Garden workday")'))
        self.button(a,'Neighbours','document.querySelector(".nb-channel-list")')
        self.wait(a,'JSON.parse(document.querySelector(".nb-shell").dataset.view||"{}").opens===""&&!document.querySelector(".nb-views button")')
        self.check('Neighbours has no opens fact, so no calendar and no switch',a.js('!document.querySelector(".cal")'))
        self.open_meetings(a)

        # Phone width.
        self.resize(a,390,844)
        self.wait(a,'!!document.querySelector(".cal-grid")')
        self.shot(a,'phone-month',390,844)
        self.resize(a,1440,900)

        # A refusal keeps the draft and says why (a past-due, impossible end).
        self.press(a,'＋ Add event','!!document.querySelector(".cal-form")')
        self.fill(a,'.cal-form input[name=title]','Backwards')
        a.js('(()=>{for(const [n,v] of [["from","18:00"],["to","17:00"]]){const i=document.querySelector(".cal-form input[name="+n+"]");i.value=v;i.dispatchEvent(new Event("input",{bubbles:true}))}})()')
        self.button(a,'Add to calendar','document.querySelector(".cal-form")')
        self.wait(a,'document.querySelector(".cal-status")?.textContent.includes("end after")')
        self.check('An end before the start is explained and nothing is posted',not any(p.get('title')=='Backwards' for p in d.rows('post'))
                   and a.js('document.querySelector(".cal-form input[name=title]").value==="Backwards"'))
        self.button(a,'Cancel','document.querySelector(".cal-form")')

        self.new_since(a,b)
        self.personal(a,b)

        errors=[e for p in self.pages for e in p.errors if e.get('method')=='Runtime.exceptionThrown']
        self.check('No uncaught script errors in either browser',not errors,str(errors)[:600])

        # The same component in the real component gallery: its example, no words, so no add or RSVP.
        from painter.install import install as install_gallery
        gallery=install_gallery(d,board=False)['component-gallery']
        g=Page(self.url,f.tokens['Alex'],gallery,1200,900,clock=f.at);self.pages.append(g)
        self.wait(g,'!!document.querySelector(".cal-grid")',40)
        self.check('Gallery shows the calendar card and its live example: November 2026, 4 Nov selected, no add or RSVP without gestures',
                   g.js('(()=>{const c=document.querySelector(".cal");c.scrollIntoView({block:"start"});return document.body.innerText.includes("calendar · A shared month and week calendar")&&c.querySelector(".cal-head h2").textContent.includes("November 2026")&&c.querySelector(".cal-day[aria-selected=true]").dataset.date==="2026-11-04"&&!c.querySelector(".cal-add")&&!c.querySelector("[data-rsvp]")})()'))
        path=OUT/'gallery-example-900.png';g.shot(path);self.shots.append(str(path.relative_to(HERE)))


    def later(self):
        # The proof clock stands still; each act that must be 'after' another gets its own minute.
        from datetime import timedelta
        self.f.at+=timedelta(minutes=1)

    def channel(self,p,title):
        self.wait(p,'[...document.querySelectorAll(".nb-channel-list button")].some(b=>b.textContent.startsWith('+json.dumps(title)+'))')
        p.js('(()=>{for(const b of document.querySelectorAll("[data-proof-channel]"))delete b.dataset.proofChannel;[...document.querySelectorAll(".nb-channel-list button")].find(b=>b.textContent.startsWith('+json.dumps(title)+')).dataset.proofChannel="yes"})()')
        self.click(p,'[data-proof-channel=yes]')
        group=self.ids['channels'][title]
        self.wait(p,'JSON.parse(document.querySelector(".nb-shell").dataset.view||"{}").channel==='+json.dumps(group))

    def new_since(self,a,b):
        f=self.f;neighbours=self.ids['channels']['Neighbours']
        shown='(()=>{const c=document.querySelector(".nb-catchup");return !!c&&!c.hidden&&c.getBoundingClientRect().height>0})()'
        self.later();f.say('Alex','board.seen')
        self.button(a,'All conversations','document.querySelector(".nb-navigation")')
        self.wait(a,'JSON.parse(document.querySelector(".nb-shell").dataset.view).channel===""&&!!document.querySelector(".nb-feed")')
        self.check('No \'new since\' header on All conversations',not a.js(shown))
        self.later();first=f.say('Bea',line('board.post',post_kind='discussion',title='Lost keys',text='Found a set of keys by the bench.',**{'in':neighbours}))['made'][0]
        self.later();f.say('Bea',line('board.post',post_kind='discussion',title='Tool library',text='Anyone want a tool library?',**{'in':neighbours}))
        self.channel(a,'Meetings & events')
        time.sleep(1)
        self.check('Nothing new in Meetings & events: no header there',not a.js(shown))
        self.channel(a,'Neighbours')
        self.wait(a,shown)
        self.check('Neighbours, with two new posts, shows the header',a.js('/^2 new since/.test(document.querySelector(".nb-catchup-jump").textContent)'),a.js('document.querySelector(".nb-catchup-jump")?.textContent'))
        self.shot(a,'new-since')
        self.click(a,'.nb-catchup-jump')
        self.wait(a,'JSON.parse(document.querySelector(".nb-shell").dataset.view).thread==='+json.dumps(first)+'&&!!document.querySelector(".nb-thread [data-post=\\"'+first+'\\"].nb-focus")')
        self.check('Clicking it lands on the oldest unseen post',a.js('(()=>{const r=document.querySelector(".nb-thread [data-post=\\"'+first+'\\"]").getBoundingClientRect();return r.bottom>0&&r.top<innerHeight})()'))
        self.shot(a,'new-since-jump')
        self.press(a,'← Back','!document.querySelector(".nb-thread textarea")')
        self.press(a,'Mark all seen','!'+shown,'document.querySelector(".nb-catchup")')
        self.world_wait(lambda:not f.see('Alex','board.catch-up in='+neighbours)['rows'])
        self.check('Mark all seen in a channel hides the header and clears that channel only',not a.js(shown))

    def personal(self,a,b):
        # Bea, who has never pressed Month or Week (an explicit press is view state and wins), makes the calendar hers.
        f=self.f;lens=self.ids['widget']  # personal words take the board's widget (or window)
        self.channel(a,'Meetings & events');self.channel(b,'Meetings & events')
        # Line keys are lowercase (kernel/lines.py KEY), so camelCase settings such as weekStart can't be named here yet.
        r=f.say('Bea',line('personal-view',lens,**{'calendar.view':'week'}))
        self.check('personal-view on the calendar part is accepted',r['ok'],r.get('text'))
        self.wait(b,'!!document.querySelector(".cal-week")',25)
        self.check("Bea's own calendar now opens on the week",True)
        self.check("Alex's calendar is unchanged (personal means just Bea)",a.js('!!document.querySelector(".cal-grid")&&!document.querySelector(".cal-week")'))
        bg='getComputedStyle(document.querySelector("[data-component=calendar][data-root]")).backgroundColor'
        before=(a.js(bg),b.js(bg))
        r=f.say('Bea','personal-style '+lens+' target=calendar background="#fff4d6"')
        self.check('personal-style on the calendar is accepted',r['ok'],r.get('text'))
        self.wait(b,bg+'!=='+json.dumps(before[1]),25)
        self.check("Bea's calendar takes her own colour; Alex's does not",a.js(bg)==before[0],dict(before=before,bea=b.js(bg),alex=a.js(bg)))
        r=f.say('Bea','personal-style '+lens+' target=board-catchup background="#eef6ff"')
        self.check('personal-style reaches the new-since header part too',r['ok'],r.get('text'))
        self.shot(b,'personal-week')

def main():
    ui=CalendarUI()
    try:ui.run()
    finally:
        (OUT/'calendar-proof.json').write_text(json.dumps(dict(checks=ui.checks,screenshots=ui.shots,hidden=True,live_touched=False),indent=2)+'\n',encoding='utf-8')
        ui.close()
    print(f'CALENDAR UI: {len(ui.checks)}/{len(ui.checks)} checks passed; hidden=True; screenshots={len(ui.shots)}',flush=True)


if __name__=='__main__':main()
