"""Window manager policy host. Shadow has no write-capable Native, lease or overlay.
All Win32 operations run on its single owner thread; module calls queue requests.
"""
from copy import deepcopy
import json
from pathlib import Path
import time
from engine import State,Window,Rect,solve,valid
from feel import Feel,Gesture,from_settings


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
    fields=('key','app','exe','icon','agora','state','focused','rect','space','managed','why')
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
        self.settings=candidate;self.feel=feel;self.state.pin_min=feel.pin_min
        self.changed.update(self.pins^set(pins))
        new_pins=set(pins)
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
        reasons,at=self.gate_cache;now=time.monotonic()
        if reasons is None or now-at>=GATE_TTL:
            reasons=list(self.gate_fn());self.gate_cache=(reasons,now)
        return reasons

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
        if mode=='off':self.gesture=None;self.preview=None

    def ingest(self,rows,work,events=()):
        """Polling reconciles missing hooks, size refusals and work-area changes."""
        now=time.monotonic();self.rows=rows;self.refs={r['key']:r['ref'] for r in rows}
        if self.mode=='off':
            current={r['key']:r for r in rows}
            self.changed.update(set(current)^set(self.actual))
            self.changed.update(k for k,r in current.items() if self.actual.get(k)!=r)
            self.actual=deepcopy(current)
            return None
        gates=self.gated_now()
        if gates:
            self.gated=True
            if self.ghost:self.ghost.clear()
            self.gesture=None;self.preview=None;self.gesture_ref=None
            return {'at':time.time(),'gated':gates,'observed_apps':sorted(set(r['app'] for r in rows)),
                'plan':[],'minimise':[]}
        resumed=self.gated;self.gated=False
        self.read_theme()
        everything={r['key'] for r in rows}
        current={r['key']:r for r in rows if not floating(r)}
        self.state.work=work
        if self.boot or resumed:
            # Starting/resuming uses actual geometry, never replays stale drag debt.
            self.state.windows={}
            for i,row in enumerate(current.values()):
                r=Rect(*row['rect']);pinned=row['key'] in self.pins
                self.state.windows[row['key']]=Window(row['key'],tuple(row.get('_preferred',(r.w,r.h))),
                    rect=r,last_used=i if not row['focused'] else len(rows)+1,
                    managed=self._managed(row),pinned=pinned,home=r if pinned else None,minimised=row['state']=='minimised')
            self.state.clock=len(rows)+1;self.boot=False
            self.state=solve(self.state,{'type':'arrange'}).state
        for key in sorted(set(self.state.windows)-set(current)):
            self.changed.add(key);self.pending.pop(key,None)
            if self.gesture and self.gesture.key==key:self._drop_gesture()
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
                self.gesture=Gesture(self.state,key,Rect(*current[key]['rect']),now*1000,self.feel)
                self.gesture_ref=current[key]['ref']
            elif kind=='drag-end' and self.gesture and self.gesture.key==key:
                self._release(Rect(*current[key]['rect']),now*1000)
        if self.gesture and self.gesture.idle(now*1000) and self.gesture.key in current:
            self._release(Rect(*current[self.gesture.key]['rect']),now*1000)   # a lost drag-end
        for key,row in current.items():
            old=self.actual.get(key);r=Rect(*row['rect']);w=self.state.windows.get(key)
            if w is None:
                size=row.get('_preferred',(r.w,r.h));pref=(min(size[0],self.state.bounds.w),min(size[1],self.state.bounds.h))
                if row['state']=='minimised':
                    self.state.windows[key]=Window(key,pref,rect=r,managed=self._managed(row),pinned=key in self.pins,
                        home=r if key in self.pins else None,minimised=True)
                else:
                    self.state=solve(self.state,{'type':'open','key':key,'window':{'preferred':pref,
                        'rect':r.values(),'managed':self._managed(row),'pinned':key in self.pins,
                        'home':r if key in self.pins else None}}).state
                w=self.state.windows[key]
                if row['state']=='minimised':w.minimised=True
            w.managed=self._managed(row) and not self.failures.get(key,0)>=3
            if not w.managed:
                w.rect=r;w.minimised=row['state']=='minimised';continue
            if key in self.pins and not w.pinned:w.rect=r;w.pinned=True;w.home=r
            elif key not in self.pins:w.pinned=False;w.home=None
            pending=self.pending.get(key)
            dragging=self.gesture is not None and self.gesture.key==key
            if w.pinned and old and old['rect']!=row['rect'] and not pending and not dragging and key!=self.released \
                    and row['state']!='minimised' and old['state']!='minimised':
                w.rect=r;w.home=r   # you moved your pin: that is its new place (the WM only narrows or regrows it)
            if pending and self.mode=='live' and now-pending['at']>=.35:
                if pending.get('kind')=='minimise':
                    if row['state']!='minimised':
                        self.failures[key]=3;w.managed=False;w.minimised=False;w.rect=r
                elif pending.get('kind')=='restore':
                    if self.native.needs_restore(row['ref']):
                        self.failures[key]=3;w.managed=False;w.rect=r;w.minimised=row['state']=='minimised'
                elif r!=pending['rect'] and row['state']!='minimised':
                    expected=pending['rect'];self.failures[key]=self.failures.get(key,0)+1
                    # Only excess dimensions establish a minimum; position refusal is an obstacle.
                    w.minimum=(max(w.minimum[0],r.w if r.w>expected.w else 0),
                        max(w.minimum[1],r.h if r.h>expected.h else 0))
                    w.rect=r
                    if w.pinned:w.home=r if not w.home else Rect(w.home.x,w.home.y,max(w.home.w,r.w),max(w.home.h,r.h))
                    if self.failures[key]>=3:w.managed=False
                    self.state=solve(self.state,{'type':'arrange'}).state
                self.pending.pop(key,None)
            if old and row['focused'] and not old['focused']:
                self.state=solve(self.state,{'type':'focus','key':key}).state
            if old and old['state']!=row['state'] and key not in self.pending:
                # Manager-requested minimise is already reflected in the plan.
                if row['state']=='minimised' and not w.minimised:
                    if dragging:self._drop_gesture();dragging=False
                    self.state=solve(self.state,{'type':'minimise','key':key}).state
                elif row['state']!='minimised' and w.minimised and old['state']=='minimised':
                    self.state=solve(self.state,{'type':'restore','key':key}).state
            if dragging and self.gesture:
                self._show(self.gesture.step(r,now*1000),r)
            elif old and old['rect']!=row['rect'] and not pending and not w.pinned and key!=self.released \
                    and row['state']!='minimised':
                # A self-resizer or move without native modal hooks still gets reconciled.
                self.state=solve(self.state,{'type':'drag-end','key':key,'rect':r.values()}).state
        # Unmanaged windows are fixed within windows; no duplicate obstacles.
        if not self.gesture:self.state=solve(self.state,{'type':'arrange'}).state
        plan=solve(self.state,{'type':'noop'})
        rows_out=[]
        for key,row in current.items():
            target=plan.placements.get(key);w=self.state.windows[key]
            rows_out.append({'key':key,'app':row['app'],'actual':row['rect'],'planned':target.values() if target else None,
                'minimise':key in plan.minimise,'managed':w.managed,'pinned':w.pinned})
        for row in rows:
            if self.actual.get(row['key'])!=row:self.changed.add(row['key'])
        result={'at':time.time(),'mode':self.mode,'gated':[],'work':work.values(),'plan':rows_out,
            'minimise':[r['app'] for r in rows_out if r['minimise']], 'notes':plan.notes,'valid':valid(plan.state)}
        if self.mode=='shadow':self._log(result)
        elif self.mode=='live' and not self.gesture:
            self.apply(plan,current)
        self.actual=deepcopy({r['key']:r for r in rows})
        return result

    def drag_tick(self,rect,now=None):
        """The 60 Hz path while a drag is on: only the dragged window's rectangle; no enumeration, no gate."""
        if not self.gesture or self.mode=='off':return None
        now=time.monotonic() if now is None else now
        frame=self.gesture.step(rect,now*1000);self._show(frame,rect);return frame

    def _show(self,frame,actual):
        """Ghosts for neighbours that gave way, and a fainter outline where the dragged window will land."""
        if self.mode!='live':return
        if not self.ghost:
            if self.ghost_factory:self.ghost=self.ghost_factory()
            else:
                from ghost import Ghost
                self.ghost=Ghost()
        landing=frame.landing if max(abs(a-b) for a,b in zip(frame.landing.values(),actual.values()))>2 else None
        self.ghost.update(list(frame.ghosts.values()),landing)

    def _release(self,rect,now_ms):
        result=self.gesture.release(rect,now_ms);self.released=self.gesture.key
        self.state=result.state;self._drop_gesture()

    def _drop_gesture(self):
        self.gesture=None;self.gesture_ref=None;self.preview=None
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

    def _managed(self,row):
        return row['managed'] and self.failures.get(row['key'],0)<3 and row['app'].lower() not in {x.lower() for x in self.settings['never']} and (
            self.settings['manage']=='all' or row['key'] in self.adopted)

    def apply(self,plan,current):
        if not valid(plan.state):return  # impossible fixed geometry fails closed
        if self.gated_now():return
        self.lease.heartbeat()
        # Minimise before placement; never transiently move over another managed window.
        for key in plan.minimise:
            row=current.get(key)
            if row and self._managed(row) and row['state']!='minimised' and not self.state.windows[key].pinned:
                if key in self.pending:continue
                self.lease.save(row['ref']);self.native.minimise(row['ref'])
                self.pending[key]={'kind':'minimise','rect':None,'at':time.monotonic()}
        for key,target in plan.placements.items():
            row=current.get(key)
            if not row or not self._managed(row):continue
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

    def action(self,verb,key):
        if self.mode!='live':raise PermissionError('native window actions require live mode')
        if self.gate_fn():raise PermissionError('game/fullscreen gate is active')
        row=next((r for r in self.rows if r['key']==key),None)
        if not row or not self._managed(row):raise PermissionError('window is no longer manageable')
        if verb in ('minimise','restore') and key in self.pins:raise PermissionError('unpin before minimising/restoring')
        self.lease.heartbeat();self.lease.save(row['ref'])
        return getattr(self.native,verb)(row['ref'])

    def reading(self):
        rows=public_rows(self.rows,self.pins)
        for row in rows:
            if row['key'] in self.failures and self.failures[row['key']]>=3:
                row['managed']=False;row['why']='unmovable or repeatedly self-resizing'
            elif not self._managed(row):row['managed']=False;row['why']=row['why'] or 'app excluded or not adopted'
        return rows
