"""EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
(people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.

wm module: SHAPE §17 JSON-lines protocol. No live installation at import/run.
Run by a kernel from the supplied genesis snippet. The world's wm-settings mode (set only by an admitted wm.mode
request) is the person's standing choice, and the module follows it: after a restart or a lost lease it arms live
again by itself once the game gate is clear (28 Oct, Alex: "the window manager keeps booting into non-live mode").
The panic chord holds it out of live until a new wm.mode request; wm.mode off is a standing off.
Earlier rule, superseded: "Starts in shadow even if an old world says live. Only a newly admitted wm.mode live
request can arm it."
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
from size_policy import validate as size_rules, FRACTIONS
from policy_reload import PolicyStatus,REFUSAL

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'kernel-desktop'))
from modproto import Module,log

HELP={
 'sizes':('see','','Editable window-kind defaults from wm-settings sizes; later matching kinds override earlier kinds.'),
 'size':('do','<kind> [match=<json>] [width=<fraction>] [height=<fraction>] [min_width=<fraction>] [min_height=<fraction>] [compact=yes|no] [remove=yes]',
         'Set a named window-kind size rule. Fractions use usable work area, half width includes its gutter share. Changes are undoable world facts.'),
 'windows':('see','','Current windows: app, exe/icon reference, state, focus and geometry; never titles.'),
 'policy':('see','','Startup imported policy code snapshot, scoped to Manager/Native and their local module functions; hot reload is unavailable.'),
 'focus':('do','<key>','Ask Windows to focus a current manageable window; foreground lock may refuse.'),
 'minimise':('do','<key>','Really minimise a manageable unpinned window; never cloak.'),
 'restore':('do','<key>','Restore a manageable window and place it without overlap.'),
 'close':('do','<key>','Ask the window politely to close with WM_CLOSE; never kill a process.'),
 'pin':('do','<key>','Keep this window fixed. Screen state, kept by this window manager, never in the world.'),
 'unpin':('do','<key>','Let this pinned window move again. Screen state, never in the world.'),
 'arrange':('do','[expect=<exe|agora>]','Re-solve the layout; expect arms one bar-requested shared layout for a new executable or Agora window, for at most five seconds. Browser windows keep half-screen width; LRU gives way before the request. Exclusive fullscreen is unsupported.'),
 'reload':('do','sha256=<reviewed digest>','Unavailable: refuses before source/native/lease operations. Existing watchdog cannot guarantee a bounded live handoff.'),
 'rollback':('do','sha256=<previous digest>','Unavailable: no retained code generation; requires a separately authorized WM lifecycle, with geometry/claim release.'),
 'mode':('do','live|shadow|off','Shadow computes only; live needs rollout arming; off releases every saved placement.'),
 'leave-alone':('do','<app>','Treat this app as fixed obstacles. Undoable world intent.'),
 'manage':('do','<app>','Remove an app exclusion (undoable); in adopted mode also adopts its current windows (screen state, kept locally).'),
}
# No wm.changed happening any more (Alex, 26 Oct: "visual state should not live in the world"): window keys and layout
# churn flooded the world's stream (Lines). The shell reads wm.windows on its own clock instead.


def offers():
    return [{'word':'wm.'+name,'kind':kind,'takes':takes,'help':'wm.'+name+': '+help,
        'may':'anyone','undo':'yes' if name in ('mode','leave-alone','manage','size') else ('external' if name=='close' else 'no')}
    # Focus, minimise, restore, pin and arrange change only this screen: not records (Alex, 26 Oct: "visual state should
    # not live in the world"; every dock click used to write one). close asks an app to close, so it stays recorded.
        for name,(kind,takes,help) in HELP.items()]


def quote(value):return json.dumps(value,ensure_ascii=False)


class MemNative:
    mutating=False
    def windows(self):return []


class WMModule:
    def __init__(self,headless=False,allow_live=False,theme_native=None):
        self.headless=headless;self.allow_live=allow_live;self.theme_native=theme_native
        self.owner=None;self.manager=None;self.lock=threading.RLock();self.stop=threading.Event()
        self.stewards=set()     # people who lead this place (Alex, 27 Oct: JEFF a steward too); refreshed by intent_loop
        self.requests=queue.Queue();self.latest=None;self.last_mode_request=None;self.intent_seen=False;self.held=False
        # Window pins and adopted windows are screen state (Alex, 26 Oct: "visual state should not live in the world"):
        # kept in <home>/screen.json, never as world things. The world keeps preferences only (wm-settings).
        self.screen={'pins':[],'adopted':[]};self.screen_path=None
        self.said={}            # topic -> last line said on stderr: a refusal is said once, not every second
        self.backlog=[]         # hook events drained during the 60 Hz drag path, handed to the next full tick
        self.full_at=0.0        # last full tick: during a drag one still runs each second (closes, the game gate)
        self.policy_reload=None
        self.m=Module(offers(),self.call,on_hello=self.hello,on_off=self.stop.set,
            on_status=lambda:f'{self.manager.mode if self.manager else "starting"}; {len(self.manager.rows) if self.manager else 0} windows')

    def hello(self,msg):
        self.owner=msg.get('for') or msg.get('owner');self.home=Path(msg['home'])
        self.screen_path=self.home/'screen.json'
        try:self.screen={'pins':[],'adopted':[],**json.loads(self.screen_path.read_text(encoding='utf-8'))}
        except (OSError,ValueError):pass
        if self.headless:self.manager=Manager(MemNative(),self.home,gate_fn=lambda:[])
        else:
            from win32_host import Native
            self.manager=Manager(Native(),self.home,allow_live=self.allow_live)
            import manager as manager_module
            import win32_host as native_module
            # Before intent_loop can arm live: no fingerprint work on the
            # lease-owning tick or request path.
            self.policy_reload=PolicyStatus(manager_module,native_module)
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
                settings=self.read_intent();pins=list(self.screen['pins'])
                # Geometry, pins and adoption are never world facts.
                with self.lock:self.latest=(settings,pins)
                self.say('intent',None)
            except Exception as exc:self.say('intent','wm intent: '+str(exc))
            try:
                seen=self.m.see('who')      # needs the grant `who` (grant wm words="who")
                if seen.get('refused') or seen.get('ok') is False:raise RuntimeError(seen.get('refused') or seen.get('text'))
                rows=seen.get('rows') or []
                self.stewards={r['id'] for r in rows if r.get('kind')=='person' and r.get('role')=='steward'}
                self.say('who',None)
            except Exception as exc:self.say('who','wm who: '+str(exc))
            self.stop.wait(1)

    def say(self,topic,line):
        """stderr (kept by the kernel in stderr.log) hears state changes only: a line when a topic's message
        changes, and one 'cleared' line when it goes away. Never once per tick."""
        if self.said.get(topic)==line:return
        before=self.said.get(topic);self.said[topic]=line
        if line:log(line)
        elif before:log(f'wm {topic}: clear')

    def _request(self,op,*args):
        answer=queue.Queue();self.requests.put((op,args,answer))
        try:return answer.get(timeout=4)
        except queue.Empty:return {'refused':'window manager did not answer'}

    def call(self,msg):
        caller=msg.get('caller') or {}
        if self.owner not in (caller.get('id'),caller.get('person')) and caller.get('person') not in self.stewards:
            return {'refused':'only this desktop owner, its stewards and their agents may read or control its windows'}
        word=msg['word'].removeprefix('wm.');args=msg.get('args') or {};kv=args.get('kv') or {}
        words=str(args.get('words') or '').split();target=kv.get('key') or args.get('target') or (words[0] if words else None)
        if word=='windows':
            with self.lock:return {'rows':self.manager.reading(),'text':f'{len(self.manager.rows)} windows; {self.manager.mode}'}
        if word=='policy':
            r=self.policy_reload
            return r.reading() if r else {'rows':[],'text':'imported policy snapshot unavailable'}
        if word in ('reload','rollback'):
            if caller.get('person') not in self.stewards:
                return {'refused':'WM policy handoff requires a desktop steward'}
            return {'refused':REFUSAL}
        if word in ('focus','minimise','restore','close'):
            return self._request('action',word,target,kv.get('share')=='yes')
        if word=='arrange':return self._request('arrange',kv.get('expect'))
        settings=self.read_intent(msg.get('use'));sid=settings['id'];saw={sid:settings['rev']}
        if word in ('size','sizes'):
            rules=size_rules(settings.get('sizes',{}))
            if word=='sizes':
                return {'rows':[{'name':name,**rule} for name,rule in rules.items()],
                        'text':json.dumps(rules,ensure_ascii=False)}
            if not target:return {'refused':'give a window-kind name'}
            try:
                if set(kv)-FRACTIONS-{'match','compact','remove','key'}:
                    raise ValueError('unknown size rule option')
                if kv.get('remove')=='yes':rules.pop(target,None)
                else:
                    rule=dict(rules.get(target,{}))
                    if 'match' in kv:rule['match']=json.loads(kv['match'])
                    for key in FRACTIONS & kv.keys():rule[key]=float(kv[key])
                    if 'compact' in kv:
                        if kv['compact'] not in ('yes','no'):raise ValueError('compact is yes|no')
                        rule['compact']=kv['compact']=='yes'
                    rules[target]=rule
                size_rules(rules)
            except (ValueError,TypeError) as exc:return {'refused':str(exc)}
            return {'lines':[f'set {sid} sizes={quote(json.dumps(rules))}'],'saw':saw}
        if word=='mode':
            mode=target
            if mode not in ('live','shadow','off'):return {'refused':'mode is live|shadow|off'}
            if mode=='live' and (self.headless or not self.allow_live):return {'refused':'live rollout disabled; coordinator must start with --allow-live'}
            return {'lines':[f'set {sid} mode={mode} mode_request={uuid.uuid4().hex}'],'saw':saw}
        if word in ('pin','unpin'):
            with self.lock:row=next((r for r in self.manager.reading() if r['key']==target),None)
            if not row or not row['managed']:return {'refused':'choose a current manageable window from wm.windows'}
            if word=='pin' and row['state']=='minimised':return {'refused':'restore the window before pinning it'}
            pins=set(self.screen['pins'])
            if (target in pins)==(word=='pin'):return {'text':f'already {word}ned'}
            pins=pins|{target} if word=='pin' else pins-{target}
            self._save_screen(pins=sorted(pins));self.latest=(settings,sorted(pins))
            return {'text':f'wm.{word}: {row["app"]}'}
        if word in ('leave-alone','manage'):
            app=' '.join(words) if words else target
            if not app:return {'refused':'give the app name from wm.windows'}
            never=settings.get('never',[])
            if isinstance(never,str):
                try:never=json.loads(never)
                except ValueError:never=[x.strip() for x in never.split(',') if x.strip()]
            never=[n for n in never if n.lower()!=app.lower()]
            if word=='leave-alone':never.append(app)
            if word=='manage':
                with self.lock:adopted=sorted(set(self.screen['adopted'])|{r['key'] for r in self.manager.rows if r['app'].lower()==app.lower()})
                self._save_screen(adopted=adopted)
            return {'lines':[f'set {sid} never={quote(json.dumps(never))}'],'saw':saw}
        return {'refused':'unknown wm word'}

    def lease_reason(self):
        """Why the last live lease ended ('panic', 'heartbeat expired', 'manager ended', 'off'), from its file."""
        try:return json.loads((self.home/'lease.json').read_text(encoding='utf-8')).get('reason')
        except (OSError,ValueError,AttributeError,TypeError):return None

    def _save_screen(self,**changes):
        self.screen.update(changes)
        if self.screen_path:
            tmp=self.screen_path.with_suffix('.tmp');tmp.write_text(json.dumps(self.screen),encoding='utf-8');tmp.replace(self.screen_path)

    def tick(self,feed=None):
        with self.lock:
            manager=self.manager
            if not manager:return
            if self.latest:
                settings,pins=self.latest;self.latest=None
                try:
                    # Pins are window keys from screen.json (26 Oct); older world wm-pin rows are not read any more.
                    manager.configure(settings,[r for r in pins if isinstance(r,str)])
                    manager.adopted=set(self.screen['adopted'])
                    request=settings.get('mode_request');want=settings.get('mode','shadow')
                    if not self.intent_seen:
                        self.held=self.lease_reason()=='panic';self.intent_seen=True   # the panic chord outlives a restart
                    elif request!=self.last_mode_request:self.held=False             # a new request lifts the hold
                    self.last_mode_request=request
                    target='off' if want=='off' else 'live' if want=='live' and not self.held else 'shadow'
                    # a refused live (game gate active) is tried again with the next second's settings
                    if manager.mode!=target:manager.switch(target)
                    self.say('settings',None)
                except Exception as exc:
                    # A refused live request (game gate active) is retried each second until it can apply; say so once.
                    self.say('settings','wm settings refused: '+str(exc))
            if manager.lease:
                try:manager.lease.heartbeat()
                except Exception:
                    # The lease ended. The panic chord holds live off until a new wm.mode request; any other end (a
                    # missed heartbeat, the guard gone) re-arms from the standing choice next second.
                    manager.switch('off');self.held=self.lease_reason()=='panic'
                    self.say('lease','wm lease ended: '+str(self.lease_reason()))
            while True:
                try:op,args,answer=self.requests.get_nowait()
                except queue.Empty:break
                try:
                    if op=='action':
                        value=manager.action(*args);answer.put({'external':args[0]=='close','text':f'wm.{args[0]}: '+('Windows refused focus' if value is False else 'requested')})
                    elif args and args[0]:
                        manager.request_share(expect=args[0])
                        answer.put({'text':'shared layout awaits requested executable window (five seconds)'})
                    else:
                        manager.state=solve(manager.state,{'type':'arrange'}).state
                        answer.put({'text':'layout re-solved'})
                except Exception as exc:answer.put({'refused':str(exc)})
            if self.headless:work=Rect(0,0,3840,2160);rows=[];events=[]
            else:
                events=self.backlog+(feed.drain() if feed else []);self.backlog=[]
                g=manager.gesture;ref=manager.gesture_ref
                now=time.monotonic()
                if manager.motion and not events and now-self.full_at<.1:
                    manager.motion_tick(now);return
                if g and ref and manager.mode!='off' and now-self.full_at<1 and not g.idle(now*1000) and not any(
                        e['hwnd']==ref.hwnd and e['type'] in ('drag-end','minimise','close','hide') for e in events):
                    # Drag path: just the dragged window's rectangle (~0.05 ms), not a full enumeration (~7-12 ms,
                    # ran 26 Oct with 17 windows) or the gate (~26 ms). Events wait for the next full tick.
                    try:
                        manager.drag_tick(manager.native.rect_of(ref));self.backlog=events[-512:];return
                    except OSError:pass       # the window went away mid-drag: a full tick sorts it out
                from win32_host import work_area
                work=work_area();rows=manager.native.windows();self.full_at=now
            manager.ingest(rows,work,events)
            manager.motion_tick()
            now=time.monotonic()
            if manager.changed and now-manager.last_change>=.1:
                manager.changed.clear();manager.last_change=now   # screen churn stays here, never in the world's stream

    def run(self):
        if not self.headless:
            from win32_host import dpi_aware,EventFeed
            dpi_aware();feed=EventFeed().start()
        else:feed=None
        self.m.run_reader()
        try:
            while not self.stop.is_set():
                self.tick(feed);self.stop.wait(1/60 if self.manager and (self.manager.gesture or self.manager.motion) else .1)
        finally:
            if self.manager:self.manager.switch('off')
            if feed:feed.close()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--headless',action='store_true');p.add_argument('--allow-live',action='store_true');p.add_argument('--theme-native',type=Path)
    a=p.parse_args();WMModule(a.headless,a.allow_live,a.theme_native).run()
