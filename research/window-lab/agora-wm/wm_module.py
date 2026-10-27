"""wm module: SHAPE §17 JSON-lines protocol. No live installation at import/run.
Run by a kernel from the supplied genesis snippet. Starts in shadow even if an
old world says live. Only a newly admitted wm.mode live request can arm it.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import queue
import sys
import threading
import time
import uuid
from engine import Rect,solve
from manager import Manager,DEFAULTS

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'kernel-desktop'))
from modproto import Module,log

HELP={
 'windows':('see','','Current windows: app, exe/icon reference, state, focus and geometry; never titles.'),
 'focus':('do','<key>','Ask Windows to focus a current manageable window; foreground lock may refuse.'),
 'minimise':('do','<key>','Really minimise a manageable unpinned window; never cloak.'),
 'restore':('do','<key>','Restore a manageable window and place it without overlap.'),
 'close':('do','<key>','Ask the window politely to close with WM_CLOSE; never kill a process.'),
 'pin':('do','<key>','Keep this window fixed. Undoable world intent; no geometry enters the log.'),
 'unpin':('do','<key>','Let this pinned window move again. Undoable.'),
 'arrange':('do','','Re-solve the current layout, preserving already legal windows.'),
 'mode':('do','live|shadow|off','Shadow computes only; live needs rollout arming; off releases every saved placement.'),
 'leave-alone':('do','<app>','Treat this app as fixed obstacles. Undoable world intent.'),
 'manage':('do','<app>','Remove an app exclusion; in adopted mode also adopts its current windows. Undoable.'),
 'changed':('hear','','Changed window keys in JSON text, at most ten announcements per second; no titles.')}


def offers():
    return [{'word':'wm.'+name,'kind':kind,'takes':takes,'help':'wm.'+name+': '+help,
        'may':'anyone','undo':'yes' if name in ('pin','unpin','mode','leave-alone','manage') else ('external' if kind=='do' else 'no')}
        for name,(kind,takes,help) in HELP.items()]


def quote(value):return json.dumps(value,ensure_ascii=False)


class MemNative:
    mutating=False
    def windows(self):return []


class WMModule:
    def __init__(self,headless=False,allow_live=False,theme_native=None):
        self.headless=headless;self.allow_live=allow_live;self.theme_native=theme_native
        self.owner=None;self.manager=None;self.lock=threading.RLock();self.stop=threading.Event()
        self.requests=queue.Queue();self.latest=None;self.last_mode_request=None;self.intent_seen=False
        self.m=Module(offers(),self.call,on_hello=self.hello,on_off=self.stop.set,
            on_status=lambda:f'{self.manager.mode if self.manager else "starting"}; {len(self.manager.rows) if self.manager else 0} windows')

    def hello(self,msg):
        self.owner=msg.get('for') or msg.get('owner');self.home=Path(msg['home'])
        if self.headless:self.manager=Manager(MemNative(),self.home,gate_fn=lambda:[])
        else:
            from win32_host import Native
            self.manager=Manager(Native(),self.home,allow_live=self.allow_live)
        self.manager.theme_path=self.theme_native or self.home.parent/'theme'/'theme-native.json'
        threading.Thread(target=self.intent_loop,daemon=True).start()

    def read_intent(self,use=None):
        result=self.m.see('rows wm-settings',use=use)
        if result.get('refused') or result.get('ok') is False:raise RuntimeError('cannot read wm-settings')
        rows=result.get('rows') or []
        if len(rows)!=1:raise RuntimeError('install exactly one wm-settings thing first')
        return rows[0]

    def intent_loop(self):
        self.m.ready.wait(3)
        while not self.stop.is_set():
            try:
                settings=self.read_intent();pins=self.m.see('rows wm-pin').get('rows',[])
                # Geometry is never a world fact, including for pins.
                with self.lock:self.latest=(settings,pins)
            except Exception as exc:log('wm intent:',str(exc))
            self.stop.wait(1)

    def _request(self,op,*args):
        answer=queue.Queue();self.requests.put((op,args,answer))
        try:return answer.get(timeout=4)
        except queue.Empty:return {'refused':'window manager did not answer'}

    def call(self,msg):
        caller=msg.get('caller') or {}
        if self.owner not in (caller.get('id'),caller.get('person')):return {'refused':'only this desktop owner and their agents may read or control its windows'}
        word=msg['word'].removeprefix('wm.');args=msg.get('args') or {};kv=args.get('kv') or {}
        words=str(args.get('words') or '').split();target=kv.get('key') or args.get('target') or (words[0] if words else None)
        if word=='windows':
            with self.lock:return {'rows':self.manager.reading(),'text':f'{len(self.manager.rows)} windows; {self.manager.mode}'}
        if word in ('focus','minimise','restore','close'):
            return self._request('action',word,target)
        if word=='arrange':return self._request('arrange')
        settings=self.read_intent(msg.get('use'));sid=settings['id'];saw={sid:settings['rev']}
        if word=='mode':
            mode=target
            if mode not in ('live','shadow','off'):return {'refused':'mode is live|shadow|off'}
            if mode=='live' and (self.headless or not self.allow_live):return {'refused':'live rollout disabled; coordinator must start with --allow-live'}
            return {'lines':[f'set {sid} mode={mode} mode_request={uuid.uuid4().hex}'],'saw':saw}
        if word in ('pin','unpin'):
            with self.lock:row=next((r for r in self.manager.reading() if r['key']==target),None)
            if not row or not row['managed']:return {'refused':'choose a current manageable window from wm.windows'}
            if word=='pin' and row['state']=='minimised':return {'refused':'restore the window before pinning it'}
            pins=self.m.see('rows wm-pin',use=msg.get('use')).get('rows',[])
            existing=next((r for r in pins if r.get('key')==target),None)
            if existing:
                return {'lines':[f'set {existing["id"]} active={"yes" if word=="pin" else "no"}'],
                    'saw':{existing['id']:existing['rev']}}
            if word=='unpin':return {'text':'already unpinned'}
            return {'lines':[f'make kind=wm-pin key={quote(target)} app={quote(row["app"])} active=yes'], 'saw':{}}
        if word in ('leave-alone','manage'):
            app=' '.join(words) if words else target
            if not app:return {'refused':'give the app name from wm.windows'}
            never=settings.get('never',[])
            if isinstance(never,str):
                try:never=json.loads(never)
                except ValueError:never=[x.strip() for x in never.split(',') if x.strip()]
            never=[n for n in never if n.lower()!=app.lower()]
            if word=='leave-alone':never.append(app)
            adopted=settings.get('adopted',[])
            if isinstance(adopted,str):adopted=json.loads(adopted)
            if word=='manage':
                with self.lock:adopted=sorted(set(adopted)|{r['key'] for r in self.manager.rows if r['app'].lower()==app.lower()})
            return {'lines':[f'set {sid} never={quote(json.dumps(never))} adopted={quote(json.dumps(adopted))}'],'saw':saw}
        return {'refused':'unknown wm word'}

    def tick(self,feed=None):
        with self.lock:
            manager=self.manager
            if not manager:return
            if self.latest:
                settings,pins=self.latest;self.latest=None
                try:
                    manager.configure(settings,[r['key'] for r in pins if r.get('active')=='yes'])
                    adopted=settings.get('adopted',[])
                    manager.adopted=set(json.loads(adopted) if isinstance(adopted,str) else adopted)
                    request=settings.get('mode_request')
                    if not self.intent_seen:
                        manager.switch('off' if settings.get('mode')=='off' else 'shadow');self.intent_seen=True
                    elif request!=self.last_mode_request:manager.switch(settings.get('mode','shadow'))
                    self.last_mode_request=request
                except Exception as exc:log('wm settings refused:',str(exc))
            if manager.lease:
                try:manager.lease.heartbeat()
                except Exception:
                    # Panic/guard death never rearms from the old world request.
                    manager.switch('off')
            while True:
                try:op,args,answer=self.requests.get_nowait()
                except queue.Empty:break
                try:
                    if op=='action':
                        value=manager.action(*args);answer.put({'external':True,'text':f'wm.{args[0]}: '+('Windows refused focus' if value is False else 'requested')})
                    else:
                        manager.state=solve(manager.state,{'type':'arrange'}).state
                        answer.put({'external':manager.mode=='live','text':'layout re-solved'})
                except Exception as exc:answer.put({'refused':str(exc)})
            if self.headless:work=Rect(0,0,3840,2160);rows=[];events=[]
            else:
                from win32_host import work_area
                work=work_area();rows=manager.native.windows();events=feed.drain() if feed else []
            manager.ingest(rows,work,events)
            now=time.monotonic()
            if manager.changed and now-manager.last_change>=.1:
                self.m.happen('wm.changed',text=json.dumps({'keys':sorted(manager.changed)}))
                manager.changed.clear();manager.last_change=now

    def run(self):
        if not self.headless:
            from win32_host import dpi_aware,EventFeed
            dpi_aware();feed=EventFeed().start()
        else:feed=None
        self.m.run_reader()
        try:
            while not self.stop.is_set():
                self.tick(feed);self.stop.wait(1/60 if self.manager and self.manager.gesture else .1)
        finally:
            if self.manager:self.manager.switch('off')
            if feed:feed.close()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--headless',action='store_true');p.add_argument('--allow-live',action='store_true');p.add_argument('--theme-native',type=Path)
    a=p.parse_args();WMModule(a.headless,a.allow_live,a.theme_native).run()
