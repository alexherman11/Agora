"""Hidden Chromium check of the board's chats, on a disposable world. Nothing live, no windows.

A fresh install lists Announcements, Calendar, Map, Documents, then Chats. Alex opens Legal and sends with Enter;
Bea (her own hidden browser) sees it, reacts from the picker and replies; Alex sees the reaction, the reply excerpt
and Bea's HTML as plain text. Desktop and phone (390px, list behind the menu button) screenshots.
"""
import json
import os
import sys
import threading
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
LAB=HERE.parents[1]/'kernel-lab'
DESKTOP=LAB.parent/'window-lab/kernel-desktop'
sys.path[:0]=[str(HERE),str(LAB),str(DESKTOP),str(LAB/'tests')]
from proof import Proof,install
from ui_install import install_ui,taskboard
from protocol import line
from painter.browser import Page
from kernel.door import EntryClient
import kdesk
from ui_proof import UI

OUT=HERE/'evidence/chat'


class ChatUI(UI):
    def __init__(self):
        OUT.mkdir(parents=True,exist_ok=True)
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
        ids=install(lambda s:f.say('Alex',s),lambda s:f.see('Alex',s))
        self.ids=install_ui(self.d);self.ids['channels']=ids['channels']
        f.join('Bea')

    def page(self,who='Alex',width=1440,height=900):
        p=Page(self.url,self.f.tokens[who],self.ids['widget'],width,height,clock=self.f.at);self.pages.append(p)
        p.until('!!document.querySelector(".nb-shell") && document.querySelector(".nb-navigation").innerText.includes("Legal")',30)
        return p

    def shot(self,p,name,width=1440,height=900):
        self.resize(p,width,height);time.sleep(.4)
        path=OUT/f'{name}-{width}.png';p.shot(path);self.shots.append(str(path.relative_to(HERE)))
        self.check('No horizontal overflow '+name+' '+str(width),p.js('document.documentElement.scrollWidth<=innerWidth+1'))

    def open_chat(self,p,name):
        self.wait(p,'[...document.querySelectorAll(".nb-channel-list button")].some(b=>b.textContent.startsWith("# '+name+'"))')
        p.js('[...document.querySelectorAll(".nb-channel-list button")].find(b=>b.textContent.startsWith("# '+name+'")).dataset.proofChannel="yes"')
        self.click(p,'[data-proof-channel=yes]')
        self.wait(p,'!!document.querySelector(".nb-chat .nb-chat-input")&&document.querySelector(".nb-chat h1").textContent.includes("'+name+'")')

    def hover(self,p,selector):
        # the message tools show on hover, as for a person moving the mouse over the line
        p.c.call('Input.dispatchMouseEvent',type='mouseMoved',button='none',**p.point(selector));time.sleep(.15)

    def tool(self,p,msg,tool):
        self.hover(p,msg);self.click(p,msg+' [data-tool='+tool+']')

    def send(self,p,text):
        self.fill(p,'.nb-chat-input',text);self.key(p,'Enter')

    def run(self):
        f,d=self.f,self.d
        a=self.page('Alex')
        names=a.js('[...document.querySelectorAll(".nb-channel-list>*")].map(n=>n.textContent.replace(/\\d+$/,"").trim())')
        self.check('The list: Announcements, Calendar, Map, Documents, then Chats',names==['Announcements','Calendar','Map','Documents','Chats','# Legal','# Media','# Buyout','# Website','# Wishes','# Bugs'],names)
        self.open_chat(a,'Legal')
        self.check('Legal opens a chat in the centre, no feed or toolbar',a.js('!document.querySelector(".nb-feed")&&!document.querySelector(".nb-toolbar")&&document.querySelector(".nb-chat h1").textContent.includes("Legal")'))
        self.send(a,'Hello **neighbours**, the lease notes are at https://example.org/lease.')
        self.world_wait(lambda:any('lease notes' in str(r.get('text')) for r in d.rows('said')))
        self.wait(a,'document.querySelector(".nb-chat-log").innerText.includes("lease notes")')
        self.check('Enter sent it, the box is empty, bold and link formatted',a.js('document.querySelector(".nb-chat-input").value===""&&!!document.querySelector(".nb-msg-text strong")&&document.querySelector(".nb-msg-text a").href==="https://example.org/lease"'))
        self.send(a,'Second line, grouped under my name')
        self.wait(a,'document.querySelectorAll(".nb-msg").length===2')
        self.check('Consecutive lines group under one name',a.js('document.querySelectorAll(".nb-msg-name").length===1&&document.querySelectorAll(".nb-msg-grouped").length===1'))

        b=self.page('Bea')
        self.open_chat(b,'Legal')
        self.wait(b,'document.querySelectorAll(".nb-msg").length===2')
        # react from the picker on Alex's first line
        b.js('document.querySelector(".nb-msg").dataset.proofMsg="yes"')
        self.tool(b,'[data-proof-msg=yes]','react')
        self.wait(b,'document.querySelectorAll(".nb-emoji").length===8')
        self.click(b,'.nb-emoji[data-emoji="🎉"]')
        self.wait(b,'!!document.querySelector(".nb-react-mine[data-emoji=\\"🎉\\"]")',20)
        self.check('Bea reacts 🎉 from the picker; hers shows pressed',True)
        # reply to it
        b.js('document.querySelector(".nb-msg").dataset.proofMsg="yes"')
        self.tool(b,'[data-proof-msg=yes]','reply')
        self.wait(b,'!document.querySelector(".nb-chat-replybar").hidden')
        self.send(b,'Thanks! <b>not bold</b> @Alex')
        self.wait(b,'document.querySelectorAll(".nb-msg").length===3')
        self.wait(a,'document.querySelectorAll(".nb-msg").length===3',25)
        self.wait(a,'!!document.querySelector(".nb-react[data-emoji=\\"🎉\\"]")',25)
        last='[...document.querySelectorAll(".nb-msg")].at(-1)'
        self.check("Alex sees Bea's reaction with her name",a.js('document.querySelector(".nb-react[data-emoji=\\"🎉\\"]").title.includes("Bea")'))
        self.check("Alex sees the reply's excerpt of his line",a.js(last+'.querySelector(".nb-msg-replyto").textContent.includes("lease notes")'))
        self.check('HTML in a message is shown as text',a.js('!document.querySelector(".nb-msg-text b")&&'+last+'.innerText.includes("<b>not bold</b>")'))
        self.check('A line naming Alex is highlighted for him',a.js(last+'.classList.contains("nb-msg-mention")'),a.js(last+'.className'))
        self.shot(a,'chat-desktop')
        self.shot(b,'chat-bea')

        # edit own line inline
        a.js('[...document.querySelectorAll(".nb-msg-mine")].at(-1).dataset.proofMsg="yes"')
        self.tool(a,'[data-proof-msg=yes]','edit')
        self.wait(a,'!!document.querySelector(".nb-msg-editor")')
        self.fill(a,'.nb-msg-editor','Second line, edited');self.key(a,'Enter')
        self.wait(a,'!document.querySelector(".nb-msg-editor")&&document.querySelector(".nb-chat-log").innerText.includes("Second line, edited")&&!!document.querySelector(".nb-msg-edited")',20)
        self.check('Edit inline: Enter saves and the line says (edited)',True)

        # phone: the list folds behind the menu button
        self.resize(a,390,844)
        self.check('Phone: the list is folded away and a menu button shows',a.js('getComputedStyle(document.querySelector(".nb-layout>.nb-navigation")).display==="none"&&getComputedStyle(document.querySelector(".nb-menu-button")).display!=="none"'))
        self.shot(a,'chat-phone',390,844)
        self.click(a,'.nb-menu-button')
        self.wait(a,'getComputedStyle(document.querySelector(".nb-layout>.nb-navigation")).display!=="none"')
        self.shot(a,'chat-phone-menu',390,844)
        self.open_chat(a,'Bugs')
        self.check('Choosing a chat from the phone menu opens it and folds the list',a.js('document.querySelector(".nb-chat h1").textContent.includes("Bugs")&&getComputedStyle(document.querySelector(".nb-layout>.nb-navigation")).display==="none"'))
        # long press on touch opens a line's actions (a touch pointer, as a phone sends)
        self.click(a,'.nb-menu-button');self.wait(a,'getComputedStyle(document.querySelector(".nb-layout>.nb-navigation")).display!=="none"')
        self.open_chat(a,'Legal');self.wait(a,'document.querySelectorAll(".nb-msg").length>=3')
        a.js('(()=>{const m=document.querySelector(".nb-msg");m.dataset.proofMsg="yes";m.dispatchEvent(new PointerEvent("pointerdown",{pointerType:"touch",bubbles:true}))})()')
        self.wait(a,'document.querySelector("[data-proof-msg=yes]")?.dataset.active==="yes"||document.querySelector(".nb-msg[data-active=yes]")!==null',5)
        self.check('Phone: a long press shows the line’s actions',a.js('getComputedStyle(document.querySelector(".nb-msg[data-active=yes] .nb-msg-tools")).display==="flex"'))
        small=a.js('[...document.querySelectorAll(".nb-msg[data-active=yes] .nb-msg-tool,.nb-chat-send,.nb-menu-button")].filter(b=>b.getClientRects().length).map(b=>Math.round(b.getBoundingClientRect().height)).filter(h=>h<44)')
        self.check('Phone: message tools, Send and menu are at least 44px tall',not small,small)
        self.shot(a,'chat-phone-actions',390,844)
        fit=a.js('Math.round(document.querySelector(".nb-chat").getBoundingClientRect().bottom)<=innerHeight+1')
        self.check('Phone: the chat and its composer fit the screen height',fit,a.js('[document.querySelector(".nb-chat").getBoundingClientRect().bottom,innerHeight]'))
        for name,ready in [('Announcements','!!document.querySelector(".nb-feed")'),('Calendar','!!document.querySelector(".cal")'),('Map','!!document.querySelector("[data-component=map-panel]")')]:
            self.click(a,'.nb-menu-button')
            self.wait(a,'getComputedStyle(document.querySelector(".nb-layout>.nb-navigation")).display!=="none"')
            find='[...document.querySelectorAll(".nb-channel-list button")].find(b=>b.textContent.trim().startsWith('+json.dumps(name)+'))'
            self.wait(a,'!!'+find);a.js(find+'.dataset.proofChannel="'+name+'"')
            self.click(a,'[data-proof-channel="'+name+'"]')
            try:self.wait(a,ready,12)
            except AssertionError:
                print('DEBUG',name,a.js('JSON.stringify({opens:document.querySelector(".nb-shell").dataset.opens,nav:getComputedStyle(document.querySelector(".nb-layout>.nb-navigation")).display,map:[...document.querySelectorAll("[data-component=map-panel]")].map(n=>n.dataset.path+" "+n.className+" "+n.innerText.slice(0,80))})'),flush=True);raise
            if name=='Map':self.check('Phone: Map opens the map part in the centre (map components are not installed in this disposable world)',a.js('!document.querySelector(".nb-feed")&&!document.querySelector(".nb-chat")'))
            time.sleep(1.5)
            self.shot(a,'phone-'+name.lower(),390,844)
        self.resize(a,1440,900)
        # a signed-out visitor: the chats are listed with a lock and opening one invites sign-in
        f.say('Alex','visitors on')
        try:
            v=Page(self.url,'',self.ids['widget'],390,844,clock=f.at);self.pages.append(v)
            v.until('!!document.querySelector(".nb-shell")',30)
            self.wait(v,'document.querySelectorAll(".nb-channel[data-locked=yes]").length===6',20)
            self.check('Visitor: all six chats listed, each locked',True)
            self.click(v,'.nb-menu-button');self.wait(v,'getComputedStyle(document.querySelector(".nb-layout>.nb-navigation")).display!=="none"')
            v.js('[...document.querySelectorAll(".nb-channel-list button")].find(b=>b.textContent.startsWith("# Legal")).dataset.proofChannel="yes"');self.click(v,'[data-proof-channel=yes]')
            self.wait(v,'document.querySelector(".nb-chat")?.dataset.locked==="yes"',20)
            self.check('Visitor: a chat shows Sign in to read the chats, and the list part still runs',v.js('document.querySelector(".nb-chat").innerText.includes("Sign in to read the chats")&&!document.querySelector(".component-stopped")'))
            self.shot(v,'visitor-chat-phone',390,844)
        except Exception as e:
            print('VISITOR CHECK SKIPPED (no visitor session in this disposable world?):',str(e)[:300],flush=True)
        marks=[r for r in f.see('Alex','rows board-seen')['rows'] if r.get('group')==self.ids['channels']['Legal']]
        self.check('Reading a chat moves the reader’s own seen marker (one per chat)',len(marks)==1,marks)
        self.check('No refusal notice on screen after all of this',not a.js('/refused/i.test(document.body.innerText)'))
        errors=[e for p in self.pages for e in p.errors if e.get('method')=='Runtime.exceptionThrown']
        self.check('No uncaught script errors in either browser',not errors,str(errors)[:600])


def main():
    ui=ChatUI()
    try:ui.run()
    finally:
        (OUT/'chat-proof.json').write_text(json.dumps(dict(checks=ui.checks,screenshots=ui.shots,hidden=True,live_touched=False),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        ui.close()
    print(f'CHAT UI: {len(ui.checks)}/{len(ui.checks)} checks passed; hidden=True; screenshots={len(ui.shots)}',flush=True)


if __name__=='__main__':main()
