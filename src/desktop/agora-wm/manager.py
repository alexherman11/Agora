"""EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
(people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.

Window manager policy host. Shadow has no write-capable Native, lease or overlay.
All Win32 operations run on its single owner thread; module calls queue requests.
"""
from copy import deepcopy
import json
from pathlib import Path
import time
from engine import State,Window,Rect,solve,valid,stacked_pair
from feel import Feel,Gesture,from_settings,ease,lerp
from size_policy import validate as size_rules, resolve as size_rule, dimensions


DEFAULTS={'when_full':'minimise-oldest','manage':'all','drag':'ghost','never':[], 'reflow':'gentle','mode':'shadow',
    # The feel (WM.md "Feel"): preferences Alex may tune, validated by feel.from_settings; px are at 100 % scale.
    'dwell_ms':350,'snap_px':16,'deadzone_px':10,'motion_ms':250,'pin_min':0.5,'edges':'shared'}
LOG_LIMIT=2_000_000     # shadow.jsonl rotates to shadow.1.jsonl past this many bytes
GATE_TTL=.5             # the game/full-screen gate costs ~26 ms (ran, 26 Oct): asked at most twice a second


def floating(row):
    """Owned dialogs/popups and maximised windows float outside the layout: a Save dialog must never make the
    oldest window minimise, and a window you maximised is not "restored" by the next tick."""
    return bool(row.get('owned') or row.get('maximised'))


def public_rows(rows,pins=()):
    fields=('key','app','exe','icon','agora','state','focused','rect','space','managed','why','display_mode')
    return [{**{k:row.get(k) for k in fields},
        'state':'pinned' if row['key'] in pins and row['state']!='minimised' else row['state']} for row in rows]


def colorref(value):
    if not isinstance(value,str) or len(value)!=7 or not value.startswith('#'):raise ValueError('native color must be #RRGGBB')
    r,g,b=(int(value[i:i+2],16) for i in (1,3,5));return r|(g<<8)|(b<<16)


class Manager:
    def __init__(self,native,home,allow_live=False,gate_fn=None,lease_factory=None,ghost_factory=None):
        self.native=native;self.home=Path(home);self.home.mkdir(parents=True,exist_ok=True)
        self.allow_live=allow_live;self.mode='shadow';self.settings=dict(DEFAULTS);self.state=State()
        self.rows=[];self.actual={};self.refs={};self.pins=set();self.adopted=set();self.pending={};self.failures={}
        self.gesture=None;self.preview=None;self.lease=None;self.ghost=None;self.last_change=0;self.changed=set()
        self.theme={};self.theme_path=None;self.theme_stamp=None;self.gated=False;self.boot=True
        self.styled={};self.feel=Feel(scale=self._scale());self.gesture_ref=None;self.released=None
        self.logged=None;self.gate_cache=(None,-1.0)
        self.gate_token=None
        self.share=None;self.borderless=set()
        self.share_floats={};self.share_note=''
        self.remembered={};self.recency={};self.use_clock=0;self.policy_minima={}
        self.motion={};self.drift={}  # native trajectories and last issued geometry
        self.sizes={};self.user_sized=set();self.size_signature={}
        if gate_fn is None:
            from win32_host import gate
            gate_fn=gate
        self.gate_fn=gate_fn;self.lease_factory=lease_factory;self.ghost_factory=ghost_factory
        self.log_path=self.home/'shadow.jsonl'

    def configure(self,settings,pins=()):
        for name,choices in {'when_full':('minimise-oldest','fill','focus'),'manage':('all','adopted'),
                'drag':('ghost','live'),'reflow':('none','gentle')}.items():
            if settings.get(name,DEFAULTS[name]) not in choices:raise ValueError(f'invalid {name}')
        never=settings.get('never',[])
        if isinstance(never,str):
            try:never=json.loads(never)
            except ValueError:never=[x.strip() for x in never.split(',') if x.strip()]
        if not isinstance(never,list) or not all(isinstance(x,str) for x in never):raise ValueError('never must be app names')
        candidate={**DEFAULTS,**settings,'never':never}
        if candidate['drag']=='live':raise ValueError('live drag has not passed the smoothness gate; use ghost')
        feel=from_settings(candidate,self._scale())     # dwell_ms, snap_px, deadzone_px, motion_ms, pin_min, edges
        sizes=size_rules(candidate.get('sizes',{}))
        self.sizes=sizes
        self.settings=candidate;self.feel=feel;self.state.pin_min=feel.pin_min
        self.changed.update(self.pins^set(pins))
        new_pins=set(pins)
        for key in self.pins^new_pins:self.state.displacement.pop(key,None)
        for key in new_pins-self.pins:
            w=self.state.windows.get(key)
            if w and w.rect and not w.minimised:w.pinned=True;w.home=w.rect
        for key in self.pins-new_pins:
            w=self.state.windows.get(key)
            if w:w.pinned=False;w.home=None
        self.pins=new_pins
        self.state.when_full=self.settings['when_full'];self.state.reflow=self.settings['reflow']
        # Live drag stays disabled until an explicit evidence file establishes smoothness.

    def _scale(self):
        try:
            value=self.native.scale()
            return float(value) if isinstance(value,(int,float)) and 0.5<=value<=4 else 1.0
        except Exception:return 1.0

    def gated_now(self):
        """The gate, asked at most every GATE_TTL seconds (it snapshots processes)."""
        read=getattr(self.native,'gate_token',None)
        token=read() if read else None
        if isinstance(token,tuple) and token!=self.gate_token:
            self.gate_cache=(None,-1.0);self.gate_token=token
        reasons,at=self.gate_cache;now=time.monotonic()
        if reasons is None or now-at>=GATE_TTL:
            reasons=list(self.gate_fn());self.gate_cache=(reasons,now)
        return reasons

    def layout_gates(self):
        reasons=self.gated_now()
        if not self.share:return reasons
        # Only an explicit, bounded arrangement may pass the ordinary gaming
        # gate. D3D/exclusive, presentation, lock and inspection failures stay
        # closed. Win32 geometry cannot prove that a game is composited.
        return [r for r in reasons if not (
            r=='full-screen foreground application' or r=='notification gate 2')]

    def _sizes(self,row,work):
        return dimensions(row,work,self.sizes,self.remembered.get(row['key'],row['rect'][2:]),
                          (self.state.gap_outer,self.state.gap_inner))

    def minimum_size(self,row,work):
        return self._sizes(row,work)[1]

    def game_protected(self,reasons):
        # Process names are produced by the shared game gate, not by a caller.
        return any(r.lower().endswith('.exe') or r=='notification gate 3' for r in reasons)

    def request_gates(self,reasons):
        """A user request may cross gaming protection, never desktop failures."""
        return [r for r in reasons if not (r.lower().endswith('.exe') or r in (
            'full-screen foreground application','notification gate 2','notification gate 3'))]

    def request_share(self,key=None,expect=None,requested=False):
        """One bar request; never a standing exemption from the gaming gate."""
        if self.mode!='live':raise PermissionError('shared layout requires live mode')
        previous=self.share
        self.share={'until':time.monotonic()+5,'keys':{r['key'] for r in self.rows},
            'target':key,'expect':expect,'new':{r['key'] for r in self.rows},'ready':False,
            'probed':set(),'probe_wait':{},'planned':False,'failed':set(),'requested':requested}
        self.gate_cache=(None,-1.0)
        reasons=self.gated_now()
        self.share['target_only']=requested and self.game_protected(reasons)
        if (self.request_gates(reasons) if self.share['target_only'] else self.layout_gates()):
            self.share=previous
            raise PermissionError('exclusive fullscreen or unavailable desktop; shared layout is unsupported')
        row=next((r for r in self.rows if r['key']==key),None)
        if key and (not row or not self._shareable(row) or key in self.pins):
            self.share=previous
            raise PermissionError('requested window is excluded, pinned or unavailable')
        if not key and not expect:
            self.share=previous
            raise ValueError('shared arrangement needs a window or expected executable')
        self._drop_gesture()
        if not self.share['target_only']:self.share_floats.clear()
        self.share_note=''
        # Failure counts are observations, not an app exclusion. A new explicit
        # bar request permits one fresh probe, never a background retry.
        if not self.share['target_only']:
            for candidate in self.rows:
                if self._shareable(candidate):self.failures.pop(candidate['key'],None)
        self.pending.clear()
        self.boot=True

    def _shareable(self,row):
        candidate=row.get('why')=='frameless; no app rule'
        return not row.get('owned') and self._managed({**row,'managed':row['managed'] or candidate},failures=False)

    def _hold_share(self,note):
        """End a failed/expired request without a native retry or reflow."""
        if self.share:
            self.share_floats.update({r['key']:list(r['rect']) for r in self.rows
                if r['key'] in self.share['keys'] and self._shareable(r) and r['key'] not in self.pins})
        self.pending.clear();self.share=None;self.share_note=note

    def _sharing(self):
        if self.share and time.monotonic()>=self.share['until']:
            # Stop at the deadline, including incomplete asynchronous work.
            # The following ordinary tick must not evict the requested app.
            self._hold_share('Sharing timed out; observed windows retained without further native actions')
        return self.share

    def read_theme(self):
        if not self.theme_path:return
        try:
            stamp=Path(self.theme_path).stat().st_mtime_ns
            if stamp==self.theme_stamp:return
            theme=json.loads(Path(self.theme_path).read_text(encoding='utf-8'))
            for g in ('gap_inner','gap_outer'):
                value=theme[g]
                if not isinstance(value,(int,float)) or not 0<=value<=128:raise ValueError('invalid gap')
            for value in theme.get('colors',{}).values():colorref(value)
            if theme.get('corner') not in ('square','round','small'):raise ValueError('invalid corner')
            self.theme=theme;self.theme_stamp=stamp
            self.state.gap_inner=round(theme['gap_inner']);self.state.gap_outer=round(theme['gap_outer'])
            self.state=solve(self.state,{'type':'arrange'}).state
            self.pending.clear()  # theme reapplication uses the existing lease
        except (OSError,ValueError,KeyError):return  # retain last validated sheet

    def switch(self,mode):
        if mode not in ('off','shadow','live'):raise ValueError('mode is live|shadow|off')
        if mode=='live':
            if not self.allow_live:raise PermissionError('live rollout is disabled; coordinator must start with --allow-live')
            if self.gate_fn():raise PermissionError('game/fullscreen gate is active')
            if self.settings['drag']!='ghost':raise PermissionError('only ghost drag is measured')
            if not self.lease:
                if self.lease_factory:self.lease=self.lease_factory(self.home/'lease.json')
                else:
                    from watchdog import Lease
                    self.lease=Lease(self.home/'lease.json')
                self.lease.acquire()
            self.native.mutating=True
        else:
            self.native.mutating=False;self.mode=mode  # fail closed even if release reports a failure
            if self.ghost:self.ghost.close();self.ghost=None
            if self.lease:
                try:self.lease.release()
                finally:self.lease=None
            self.native.mutating=False
        self.mode=mode;self.pending.clear()
        self.styled.clear()
        if mode!='live':self._drop_gesture()

    def ingest(self,rows,work,events=()):
        """Polling reconciles missing hooks, size refusals and work-area changes."""
        # A newly observed executable may be the game that just started. Do not
        # run its first layout using a pre-launch clear process-gate cache.
        if {r['exe'] for r in rows}-{r['exe'] for r in self.rows}:self.gate_cache=(None,-1.0)
        now=time.monotonic();self.rows=rows;self.refs={r['key']:r['ref'] for r in rows}
        self.state.work=work
        for row in rows:
            key=row['key'];old=self.actual.get(key)
            if key not in self.recency or row['focused'] and (not old or not old['focused']):
                self.use_clock+=1;self.recency[key]=self.use_clock
            if key not in self.remembered:
                normal=row.get('_normal')
                size=row.get('_preferred',row['rect'][2:])
                self.remembered[key]=tuple(normal[2:] if normal else size)
            rule=size_rule(row,self.sizes)
            signature=(rule,work.w,work.h,self.state.gap_outer,self.state.gap_inner)
            if self.size_signature.get(key)!=signature:
                if key not in self.user_sized:
                    self.remembered[key]=self._sizes(row,work)[0]
                self.size_signature[key]=signature
        present={r['key'] for r in rows}
        self.remembered={k:v for k,v in self.remembered.items() if k in present}
        self.recency={k:v for k,v in self.recency.items() if k in present}
        self.policy_minima={k:v for k,v in self.policy_minima.items() if k in present}
        self.user_sized.intersection_update(present)
        self.size_signature={k:v for k,v in self.size_signature.items() if k in present}
        if set(self.share_floats)-present:self.share_floats.clear()
        if self.mode=='off':
            current={r['key']:r for r in rows}
            self.changed.update(set(current)^set(self.actual))
            self.changed.update(k for k,r in current.items() if self.actual.get(k)!=r)
            self.actual=deepcopy(current)
            return None
        sharing=self._sharing()
        if sharing and sharing['expect'] and not sharing['ready']:
            matches=[r for r in rows if r['key'] not in sharing['new']
                and (str(r['exe']).lower()==sharing['expect'].lower()
                    or sharing['expect']=='agora' and r.get('agora')) and self._shareable(r)]
            target=matches[0] if len(matches)==1 else None
            if target:
                sharing['target']=target['key'];sharing['keys'].add(target['key'])
        if sharing:
            sharing['ready']=any(r['key']==sharing['target'] for r in rows)
        if sharing and sharing.get('requested') and self.game_protected(self.gated_now()):
            sharing['target_only']=True
        if sharing and sharing.get('target_only'):
            reasons=self.gated_now()
            if self.request_gates(reasons):
                self._hold_share('Requested launch cancelled: desktop gate is unavailable')
            elif sharing['ready']:
                row=next(r for r in rows if r['key']==sharing['target'])
                # Consume the request before touching native state. One exact
                # target, no follow-up layout or automatic retry on refusal.
                try:
                    result=self._requested_action('focus',row,reasons)
                    if result is False:self.share_note='Windows refused requested focus; no retry'
                except (OSError,PermissionError) as exc:
                    self._hold_share('Requested launch refused; no retry: '+str(exc))
            self.gated=True;self._drop_gesture()
            return {'gated':reasons,'plan':[],'minimise':[],'notes':[self.share_note]}
        gates=self.layout_gates()
        if sharing and not sharing['ready']:gates=gates or ['waiting for requested window']
        if gates:
            self.gated=True
            self._drop_gesture()
            return {'at':time.time(),'gated':gates,'observed_apps':sorted(set(r['app'] for r in rows)),
                'plan':[],'minimise':[]}
        if sharing and sharing['ready'] and self.mode=='live':
            # Ask state restoration before learning a fullscreen rectangle as
            # an app minimum. Only one probe per explicit request; no input.
            waiting=False
            for row in rows:
                key=row['key']
                if key not in sharing['keys'] or key in self.pins or not self._shareable(row):continue
                if key in sharing['probe_wait']:
                    if now-sharing['probe_wait'][key]<.35:waiting=True
                    elif self.native.needs_restore(row['ref']):self.failures[key]=3
                    continue
                if key not in sharing['probed'] and (row.get('maximised') or row.get('share_candidate')
                        or key==sharing['target'] and row['state']=='minimised'
                        or row.get('display_mode','').startswith('screen-sized')):
                    sharing['probed'].add(key)
                    try:
                        self.lease.heartbeat();self.lease.save(row['ref'])
                        self.native.restore_shared(row['ref'])
                    except (OSError,PermissionError):
                        self.failures[key]=3
                        self._hold_share('Window-state probe refused; sharing stopped without retry')
                        return {'gated':[],'plan':[],'minimise':[],'notes':[self.share_note]}
                    sharing['probe_wait'][key]=now;waiting=True
            if waiting:
                return {'gated':[],'plan':[],'minimise':[],'notes':['Waiting for requested window-state restore']}
        resumed=self.gated;self.gated=False
        self.read_theme()
        everything={r['key'] for r in rows}
        current={}
        for row in rows:
            key=row['key']
            if not sharing and key in self.share_floats:
                if row['rect']==self.share_floats[key]:continue
                del self.share_floats[key]  # external geometry change returns it to ordinary policy
            admitted=bool(sharing and key in sharing['keys'] and self._shareable(row) and key not in self.pins)
            if floating(row) and not admitted:continue
            if sharing and key not in sharing['keys']:continue
            if admitted and row.get('why')=='frameless; no app rule':self.borderless.add(key)
            current[key]={**row,'managed':True} if key in self.borderless and self._shareable(row) else row
        self.borderless.intersection_update(everything)
        self.share_floats={k:r for k,r in self.share_floats.items() if k in everything}
        self.state.work=work
        if self.boot or resumed:
            # Starting/resuming uses actual geometry, never replays stale drag debt.
            self.state.windows={};self.state.displacement={}
            for i,row in enumerate(current.values()):
                r=Rect(*row['rect']);pinned=row['key'] in self.pins
                if sharing and row.get('maximised') and not pinned:
                    normal=row.get('_normal')
                    size=row.get('_preferred',(r.w,r.h))
                    r=Rect(*normal) if normal else Rect(r.x,r.y,*size)
                self.state.windows[row['key']]=Window(row['key'],self.remembered[row['key']],
                    minimum=self.minimum_size(row,work),rect=r,last_used=self.recency[row['key']],
                    managed=self._managed(row),pinned=pinned,home=r if pinned else None,minimised=row['state']=='minimised',
                    no_evict=bool(sharing and row['key'] in sharing['probed']),
                    compact=size_rule(row,self.sizes).get('compact',False))
            self.state.clock=self.use_clock;self.boot=False
            if not sharing:
                if stacked_pair(self.state):
                    newest=max((w for w in self.state.windows.values() if not w.minimised),
                               key=lambda w:(w.last_used,w.key))
                    self.state=solve(self.state,{'type':'share','key':newest.key}).state
                else:self.state=solve(self.state,{'type':'arrange'}).state
        for key in sorted(set(self.state.windows)-set(current)):
            self.changed.add(key);self.pending.pop(key,None)
            if self.gesture and self.gesture.key==key:self._drop_gesture()
            self.state.displacement.pop(key,None)
            if key in everything:
                # Still open, but floating now (maximised, or an owned popup): it leaves the layout without a reflow,
                # so un-maximising finds its place free. It comes back like a newly opened window.
                del self.state.windows[key];continue
            self.failures.pop(key,None)
            self.state=solve(self.state,{'type':'close','key':key}).state
        by_hwnd={r['ref'].hwnd:r['key'] for r in current.values()}
        self.released=None
        for e in events:
            key=by_hwnd.get(e['hwnd']);w=self.state.windows.get(key)
            if not w or not self._managed(current[key]):continue
            kind=e['type']
            if kind=='focus':self.state=solve(self.state,{'type':'focus','key':key}).state
            if kind=='drag-start' and not w.minimised and current[key]['state']!='minimised':
                self.motion.clear();self.drift.clear()
                self.gesture=Gesture(self.state,key,Rect(*current[key]['rect']),now*1000,self.feel)
                self.gesture_ref=current[key]['ref']
            elif kind=='drag-end' and self.gesture and self.gesture.key==key:
                self._release(Rect(*current[key]['rect']),now*1000)
        if self.gesture and self.gesture.idle(now*1000) and self.gesture.key in current:
            self._release(Rect(*current[self.gesture.key]['rect']),now*1000)   # a lost drag-end
        for key,row in current.items():
            old=self.actual.get(key);r=Rect(*row['rect']);w=self.state.windows.get(key)
            if w is None:
                size=self.remembered[key];pref=(min(size[0],self.state.bounds.w),min(size[1],self.state.bounds.h))
                if row['state']=='minimised':
                    self.state.windows[key]=Window(key,pref,minimum=self.minimum_size(row,work),rect=r,managed=self._managed(row),pinned=key in self.pins,
                        home=r if key in self.pins else None,minimised=True,compact=size_rule(row,self.sizes).get('compact',False))
                else:
                    self.state=solve(self.state,{'type':'open','key':key,'window':{'preferred':pref,
                        'minimum':self.minimum_size(row,work),'rect':r.values(),'managed':self._managed(row),'pinned':key in self.pins,
                        'home':r if key in self.pins else None,'compact':size_rule(row,self.sizes).get('compact',False)}}).state
                w=self.state.windows[key]
                if row['state']=='minimised':w.minimised=True
            w.managed=self._managed(row) and not self.failures.get(key,0)>=3
            w.preferred=self.remembered[key]
            w.compact=size_rule(row,self.sizes).get('compact',False)
            floor=self.minimum_size(row,work)
            previous=self.policy_minima.get(key,(0,0))
            w.minimum=tuple(max(floor[i],w.minimum[i] if w.minimum[i]>previous[i] else 0) for i in (0,1))
            self.policy_minima[key]=floor
            w.last_used=self.recency[key];self.state.clock=max(self.state.clock,self.use_clock)
            if not w.managed:
                w.rect=r;w.minimised=row['state']=='minimised';continue
            if key in self.pins and not w.pinned:w.rect=r;w.pinned=True;w.home=r
            elif key not in self.pins:w.pinned=False;w.home=None
            pending=self.pending.get(key)
            moving_by_us=key in self.motion or (self.gesture and key in self.drift)
            if old and old['state']=='minimised' and row['state']!='minimised' and w.minimised:
                # A new external restore supersedes layout work, even inside
                # its acknowledgement interval. Do not lose this transition or
                # treat the successful restore as a refused minimise.
                self.pending.pop(key,None);pending=None
                self.state=solve(self.state,{'type':'restore','key':key}).state
                w=self.state.windows[key]
                if self.mode=='live':
                    # IsIconic can clear before native frame geometry settles.
                    # Use the same restore acknowledgement as apply().
                    pending={'kind':'restore','rect':w.rect,'at':now}
                    self.pending[key]=pending
            dragging=self.gesture is not None and self.gesture.key==key
            if w.pinned and old and old['rect']!=row['rect'] and not pending and not dragging and key!=self.released \
                    and row['state']!='minimised' and old['state']!='minimised':
                self.state.displacement.pop(key,None)
                w.rect=r;w.home=r   # you moved your pin: that is its new place (the WM only narrows or regrows it)
            if pending and not moving_by_us and self.mode=='live' and now-pending['at']>=.35:
                if pending.get('kind')=='minimise':
                    if row['state']!='minimised':
                        self.failures[key]=3;w.managed=False;w.minimised=False;w.rect=r
                elif pending.get('kind')=='restore':
                    if self.native.needs_restore(row['ref']):
                        self.failures[key]=3;w.managed=False;w.rect=r;w.minimised=row['state']=='minimised'
                elif r!=pending['rect'] and row['state']!='minimised':
                    expected=pending['rect'];self.failures[key]=self.failures.get(key,0)+1
                    if sharing:
                        # One fresh explicit probe, not a cycle of resize
                        # attempts that learns fullscreen as a minimum size.
                        self.failures[key]=3;w.managed=False;w.rect=r
                    # Only excess dimensions establish a minimum; position refusal is an obstacle.
                    else:w.minimum=(max(w.minimum[0],r.w if r.w>expected.w else 0),
                                    max(w.minimum[1],r.h if r.h>expected.h else 0))
                    w.rect=r
                    if w.pinned:w.home=r if not w.home else Rect(w.home.x,w.home.y,max(w.home.w,r.w),max(w.home.h,r.h))
                    if self.failures[key]>=3:w.managed=False
                    if not sharing:self.state=solve(self.state,{'type':'arrange'}).state
                self.pending.pop(key,None)
            if old and row['focused'] and not old['focused']:
                self.state=solve(self.state,{'type':'focus','key':key}).state
            if old and old['state']!=row['state'] and key not in self.pending:
                # Manager-requested minimise is already reflected in the plan.
                if row['state']=='minimised' and not w.minimised:
                    if dragging:self._drop_gesture();dragging=False
                    self.state=solve(self.state,{'type':'minimise','key':key}).state
            if dragging and self.gesture:
                self._show(self.gesture.step(r,now*1000,self._pointer()),r)
            elif old and old['rect']!=row['rect'] and not pending and not moving_by_us and not w.pinned and key!=self.released \
                    and row['state']!='minimised' and old['state']!='minimised':
                # A restore changes geometry too; it is not a manual drag.
                # A self-resizer or move without native modal hooks still gets reconciled.
                self.state=solve(self.state,{'type':'drag-end','key':key,'rect':r.values()}).state
        # Unmanaged windows are fixed within windows; no duplicate obstacles.
        if sharing and sharing['ready'] and not self.gesture:
            failed={k for k in current if self.failures.get(k,0)>=3}
            if not sharing['planned'] or failed!=sharing['failed']:
                # Intermediate open/restore reconciliation may have evicted a
                # neighbour. Begin the explicit share from observed visibility,
                # so repacking gets a chance before any real minimisation.
                for key,row in current.items():
                    self.state.windows[key].minimised=row['state']=='minimised'
                shared=solve(self.state,{'type':'share','key':sharing['target']})
                self.state=shared.state
                self.share_note='; '.join(shared.notes)
                evicted=[current[k]['app'] for k in shared.minimise
                    if k in current and current[k]['state']!='minimised']
                if evicted:self.share_note+='; least recently used stepped aside: '+', '.join(evicted)
                sharing['planned']=True;sharing['failed']=failed
                target=self.state.windows.get(sharing['target'])
                if target and not target.managed:
                    self.share_note='Requested window shown in front; fixed windows prevent sharing'
                    for key,row in current.items():
                        w=self.state.windows[key]
                        if key!=target.key:
                            w.rect=Rect(*row['rect']);w.minimised=row['state']=='minimised'
                            if w.rect.near(target.rect,self.state.gap_inner) and not w.minimised:w.managed=False
                    self.share_floats={k:list(r['rect']) for k,r in current.items()
                        if not self.state.windows[k].managed and k!=sharing['target']}
                    if target.rect:self.share_floats[target.key]=target.rect.values()
        elif not self.gesture:self.state=solve(self.state,{'type':'arrange'}).state
        if not sharing and self.state.fill_on_close and set(self.actual)-everything and not self.gesture:
            self.state=solve(self.state,{'type':'fill'}).state
        plan=solve(self.state,{'type':'noop'})
        rows_out=[]
        for key,row in current.items():
            target=plan.placements.get(key);w=self.state.windows[key]
            rows_out.append({'key':key,'app':row['app'],'actual':row['rect'],'planned':target.values() if target else None,
                'minimise':key in plan.minimise,'managed':w.managed,'pinned':w.pinned})
        for row in rows:
            if self.actual.get(row['key'])!=row:self.changed.add(row['key'])
        result={'at':time.time(),'mode':self.mode,'gated':[],'work':work.values(),'plan':rows_out,
            'minimise':[r['app'] for r in rows_out if r['minimise']],
            'notes':plan.notes+([self.share_note] if self.share_note else []),'valid':valid(plan.state)}
        if self.mode=='shadow':self._log(result)
        elif self.mode=='live' and not self.gesture:
            self.apply(plan,current)
        self.actual=deepcopy({r['key']:r for r in rows})
        if sharing and sharing['ready'] and not self.pending and all(
                k not in plan.placements or (not r.get('maximised') and Rect(*r['rect'])==plan.placements[k])
                for k,r in current.items()):
            self.share=None
        return result

    def drag_tick(self,rect,now=None):
        """The fast drag path reads geometry and pointer; no window enumeration."""
        if not self.gesture or self.mode=='off':return None
        if self.layout_gates():
            self.gated=True;self._drop_gesture();return None
        now=time.monotonic() if now is None else now
        frame=self.gesture.step(rect,now*1000,self._pointer());self._show(frame,rect);return frame

    def _pointer(self):
        read=getattr(self.native,'cursor',None)
        point=read() if read else None
        return point if isinstance(point,(tuple,list)) and len(point)==2 else None

    def _show(self,frame,actual):
        """The hand's landing glass, and real neighbours following eased geometry."""
        if self.mode!='live':return
        if self.layout_gates():
            self.gated=True;self._drop_gesture();return
        if not self.ghost:
            if self.ghost_factory:self.ghost=self.ghost_factory()
            else:
                from ghost import Ghost
                self.ghost=Ghost()
        self.ghost.update([q for q in frame.spaces if q!=frame.landing],frame.landing)
        rows={r['key']:r for r in self.rows}
        for key in set(frame.ghosts)|set(self.drift):
            if not self.gesture or key==self.gesture.key:continue
            row=rows.get(key)
            if not row or not self._managed(row) or key in self.pins:continue
            target=frame.ghosts.get(key,self.gesture.home(key))
            if target is None or target==self.drift.get(key,Rect(*row['rect'])):continue
            try:
                self.lease.heartbeat();self.lease.save(row['ref'])
                self.native.place(row['ref'],target);self.drift[key]=target
            except (OSError,PermissionError):
                self.failures[key]=3
                self._drop_gesture()
                break

    def _release(self,rect,now_ms):
        result=self.gesture.release(rect,now_ms,self._pointer());self.released=self.gesture.key
        chosen=result.placements.get(self.released)
        if chosen:
            self.remembered[self.released]=(chosen.w,chosen.h);self.user_sized.add(self.released)
        starts={r['key']:self.drift.get(r['key'],Rect(*r['rect'])) for r in self.rows}
        starts[self.released]=rect
        self.state=result.state;self._drop_gesture()
        if self.mode=='live':
            self.motion={k:(starts[k],q,now_ms) for k,q in result.placements.items()
                         if k in starts and starts[k]!=q}

    def motion_tick(self,now=None):
        """Complete a release without a one-frame SetWindowPos jump or focus call."""
        if not self.motion or self.mode!='live':return
        if self.layout_gates():
            self.gated=True;self.motion.clear();self.drift.clear();return
        now=time.monotonic() if now is None else now
        rows={r['key']:r for r in self.rows}
        self.lease.heartbeat()
        for key,(start,target,at) in list(self.motion.items()):
            row=rows.get(key)
            if not row or not self._managed(row) or row['state']=='minimised':
                self.motion.pop(key,None);continue
            progress=1 if self.feel.motion_ms<=0 else (now*1000-at)/self.feel.motion_ms
            q=lerp(start,target,ease(progress))
            try:
                if q!=self.drift.get(key,start):
                    self.lease.save(row['ref']);self.native.place(row['ref'],q);self.drift[key]=q
                if progress>=1:
                    self.motion.pop(key,None)
                    self.pending[key]={'rect':target,'at':now}
            except (OSError,PermissionError):
                self.motion.pop(key,None);self.failures[key]=3
        if not self.motion:self.drift.clear()

    def _drop_gesture(self):
        self.gesture=None;self.gesture_ref=None;self.preview=None
        self.motion.clear();self.drift.clear()
        if self.ghost:self.ghost.clear()

    def _log(self,result):
        """Shadow log: one line when the plan changes, never one per tick; rotates past LOG_LIMIT."""
        signature=json.dumps({k:v for k,v in result.items() if k!='at'},sort_keys=True)
        if signature==self.logged:return
        self.logged=signature
        try:
            if self.log_path.exists() and self.log_path.stat().st_size>LOG_LIMIT:
                self.log_path.replace(self.log_path.with_name(self.log_path.stem+'.1.jsonl'))
            with self.log_path.open('a',encoding='utf-8') as f:f.write(json.dumps(result)+'\n')
        except OSError:pass

    def _managed(self,row,failures=True):
        return row['managed'] and (not failures or self.failures.get(row['key'],0)<3) and row['app'].lower() not in {x.lower() for x in self.settings['never']} and (
            self.settings['manage']=='all' or row['key'] in self.adopted)

    def apply(self,plan,current):
        if not valid(plan.state):return  # impossible fixed geometry fails closed
        if self.layout_gates():return
        # The process/fullscreen gate cannot classify every windowed game.
        # Capacity pressure alone never authorises hiding an observed window.
        # Hold the whole plan, including neighbour moves, until an explicit
        # arrangement or enough space is available. Keep this at the native seam.
        if not (self.share and self.share.get('requested')) and any(
                k in current and current[k]['state']!='minimised' for k in plan.minimise):
            self._drop_gesture();self.boot=True
            return
        try:self._apply_plan(plan,current)
        except (OSError,PermissionError):
            if not self.share:raise
            self._hold_share('Native sharing operation refused; stopped without retry')

    def _apply_plan(self,plan,current):
        self.lease.heartbeat()
        # Minimise before placement; never transiently move over another managed window.
        for key in plan.minimise:
            if self.share and (key==self.share['target'] or self.state.windows[key].no_evict):continue
            row=current.get(key)
            if row and self._managed(row) and row['state']!='minimised' and not self.state.windows[key].pinned:
                if key in self.pending:continue
                try:
                    self.lease.save(row['ref']);self.native.minimise(row['ref'])
                except (OSError,PermissionError):
                    if not self.share:raise
                    self.failures[key]=3
                    self._hold_share('LRU minimisation refused; sharing stopped without retry')
                    return
                self.pending[key]={'kind':'minimise','rect':None,'at':time.monotonic()}
        for key,target in plan.placements.items():
            row=current.get(key)
            if not row or not self._managed(row):continue
            if key in self.motion:continue
            if self.share and key==self.share['target'] and self.share_note.startswith('Requested window shown in front') and not self.share.get('front'):
                self.lease.save(row['ref']);self.native.focus(row['ref']);self.share['front']=True
            role='pinned' if self.state.windows[key].pinned else ('focused' if row['focused'] else 'unfocused')
            color=self.theme.get('colors',{}).get(role);corner={'square':1,'round':2,'small':3}.get(self.theme.get('corner'))
            desired=(color,corner)
            if desired!=(None,None) and self.styled.get(key)!=desired:
                self.lease.save(row['ref'],geometry=False)
                self.native.style(row['ref'],colorref(color) if color else None,corner);self.styled[key]=desired
            if key in self.pending:continue   # pins are placed too: the engine only narrows or regrows them
            if Rect(*row['rect'])==target and row['state']!='minimised':continue
            try:
                self.lease.save(row['ref'])
                if self.native.needs_restore(row['ref']):
                    self.native.restore(row['ref'])
                    self.pending[key]={'kind':'restore','rect':target,'at':time.monotonic()}
                    continue  # asynchronous restore; measure fresh frame margins next tick
                self.native.place(row['ref'],target)
                self.pending[key]={'rect':target,'at':time.monotonic()}
            except (OSError,PermissionError):
                self.failures[key]=3;self.state.windows[key].managed=False
                if self.share:
                    self._hold_share('Native placement refused; sharing stopped without retry')
                    return

    def _requested_action(self,verb,row,reasons,geometry=None):
        """One named user action; never admit a background layout through a gate."""
        if self.mode!='live':raise PermissionError('native window actions require live mode')
        if self.request_gates(reasons):
            raise PermissionError('desktop gate is active; requested action is unavailable')
        if not self._shareable(row):
            raise PermissionError('window is no longer manageable')
        if row['key'] in self.pins and (verb in ('restore','move') or row['state']=='minimised'):
            raise PermissionError('unpin before restoring/moving')
        target=None
        if verb=='move':
            if row['state']=='minimised':raise PermissionError('restore the window before moving')
            def pair(value):
                try:parts=tuple(int(x) for x in value.split(','))
                except (ValueError,AttributeError):raise ValueError('at and size need two integer coordinates')
                if len(parts)!=2:raise ValueError('at and size need two integer coordinates')
                return parts
            geometry=geometry or {}
            if set(geometry)-{'at','size'} or 'at' not in geometry:
                raise ValueError('move needs at=x,y and optional size=w,h')
            target=Rect(*pair(geometry['at']),*(pair(geometry['size']) if 'size' in geometry else row['rect'][2:]))
            if target.w<=0 or target.h<=0 or not self.state.work.contains(target):
                raise ValueError('requested rectangle must fit the current work area')
        # Supersede stale share/drag debt, without creating an exemption or
        # scheduling retries. Subsequent ticks still use the full gaming gate.
        self._hold_share('Requested target only; background layout remains protected')
        self.pending.clear();self._drop_gesture();self.boot=True;self.gated=True
        self.lease.heartbeat();self.lease.save(row['ref'])
        if verb=='move':
            self.native.place(row['ref'],target)  # existing SWP_NOACTIVATE boundary
            self.remembered[row['key']]=(target.w,target.h);self.user_sized.add(row['key'])
            return
        if row['state']=='minimised':
            self.native.restore(row['ref'])
        return self.native.focus(row['ref'])

    def action(self,verb,key,share=False,requested=False,geometry=None):
        if self.mode!='live':raise PermissionError('native window actions require live mode')
        row=next((r for r in self.rows if r['key']==key),None)
        reasons=list(self.gate_fn())
        # The following tick must not reuse a pre-game clear cache after this
        # request has just observed the game. No transient reflow exemption.
        self.gate_cache=(reasons,time.monotonic())
        # Only the admitted world request path sets requested. Internal policy
        # calls, minimise/close and all layout paths retain their original gate.
        if requested and (verb=='move' or verb in ('focus','restore') and reasons
                          and (not share or self.game_protected(reasons))):
            if not row:raise PermissionError('window is no longer manageable')
            return self._requested_action(verb,row,reasons,geometry)
        if verb=='move':raise PermissionError('move requires an explicit request')
        if share and verb in ('focus','restore'):self.request_share(key=key,requested=requested)
        elif reasons:raise PermissionError('game/fullscreen gate is active')
        if not row or not (self._shareable(row) if share else self._managed(row)):
            raise PermissionError('window is no longer manageable')
        if verb in ('minimise','restore') and key in self.pins:raise PermissionError('unpin before minimising/restoring')
        if verb in ('minimise','restore') and not share:
            # The latest explicit intent supersedes layout work (or the
            # opposite action). The native call alone leaves stale policy.
            self.pending.pop(key,None)
            self.state=solve(self.state,{'type':verb,'key':key}).state
        try:
            self.lease.heartbeat();self.lease.save(row['ref'])
            result=self.native.focus(row['ref']) if share else getattr(self.native,verb)(row['ref'])
        except (OSError,PermissionError):
            if share:self._hold_share('Requested focus refused; sharing stopped without retry')
            raise
        if verb in ('minimise','restore') and not share and key in self.state.windows:
            self.pending[key]={'kind':verb,'rect':self.state.windows[key].rect,'at':time.monotonic()}
        return result

    def reading(self):
        rows=public_rows(self.rows,self.pins)
        for row in rows:
            if row['key'] in self.failures and self.failures[row['key']]>=3:
                row['managed']=False;row['why']='unmovable or repeatedly self-resizing'
            elif not self._managed(row):row['managed']=False;row['why']=row['why'] or 'app excluded or not adopted'
            if row['key'] in self.share_floats:
                row['managed']=False;row['why']='foreground fallback retained until geometry changes'
            if self.share_note:row['share_note']=self.share_note
        return rows
