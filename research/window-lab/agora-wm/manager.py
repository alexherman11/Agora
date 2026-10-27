"""Window manager policy host. Shadow has no write-capable Native, lease or overlay.
All Win32 operations run on its single owner thread; module calls queue requests.
"""
from copy import deepcopy
import json
from pathlib import Path
import time
from engine import State,Window,Rect,solve,valid


DEFAULTS={'when_full':'minimise-oldest','manage':'all','drag':'ghost','never':[], 'reflow':'gentle','mode':'shadow'}


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
        self.styled={}
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
        self.settings=candidate;new_pins=set(pins);self.changed.update(self.pins^new_pins);self.pins=new_pins
        self.state.when_full=self.settings['when_full'];self.state.reflow=self.settings['reflow']
        # Live drag stays disabled until an explicit evidence file establishes smoothness.

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
        gates=self.gate_fn()
        if gates:
            self.gated=True
            if self.ghost:self.ghost.clear()
            self.gesture=None;self.preview=None
            return {'at':time.time(),'gated':gates,'observed_apps':sorted(set(r['app'] for r in rows)),
                'plan':[],'minimise':[]}
        resumed=self.gated;self.gated=False
        self.read_theme()
        current={r['key']:r for r in rows}
        self.state.work=work
        if self.boot or resumed:
            # Starting/resuming uses actual geometry, never replays stale drag debt.
            self.state.windows={}
            for i,row in enumerate(rows):
                r=Rect(*row['rect']);self.state.windows[row['key']]=Window(row['key'],tuple(row.get('_preferred',(r.w,r.h))),
                    rect=r,last_used=i if not row['focused'] else len(rows)+1,
                    managed=self._managed(row),pinned=row['key'] in self.pins,minimised=row['state']=='minimised')
            self.state.clock=len(rows)+1;self.boot=False
            self.state=solve(self.state,{'type':'arrange'}).state
        for key in set(self.state.windows)-set(current):
            self.changed.add(key)
            self.state=solve(self.state,{'type':'close','key':key}).state
            self.pending.pop(key,None);self.failures.pop(key,None)
        by_hwnd={r['ref'].hwnd:r['key'] for r in rows}
        for e in events:
            key=by_hwnd.get(e['hwnd']);w=self.state.windows.get(key)
            if not w or not self._managed(current[key]):continue
            kind=e['type']
            if kind=='focus':self.state=solve(self.state,{'type':'focus','key':key}).state
            if kind=='drag-start':
                self.gesture={'key':key,'base':deepcopy(self.state),'rect':Rect(*current[key]['rect'])}
            elif kind=='drag-end' and self.gesture and self.gesture['key']==key:
                self.preview=solve(self.gesture['base'],{'type':'drag-end','key':key,'rect':current[key]['rect']})
                self.state=self.preview.state;self.gesture=None;self.preview=None
                if self.ghost:self.ghost.clear()
        for key,row in current.items():
            old=self.actual.get(key);r=Rect(*row['rect']);w=self.state.windows.get(key)
            if w is None:
                size=row.get('_preferred',(r.w,r.h));pref=(min(size[0],self.state.bounds.w),min(size[1],self.state.bounds.h))
                if row['state']=='minimised':
                    self.state.windows[key]=Window(key,pref,rect=r,managed=self._managed(row),pinned=key in self.pins,minimised=True)
                else:
                    self.state=solve(self.state,{'type':'open','key':key,'window':{'preferred':pref,
                        'rect':r.values(),'managed':self._managed(row),'pinned':key in self.pins}}).state
                w=self.state.windows[key]
                if row['state']=='minimised':w.minimised=True
            w.managed=self._managed(row) and not self.failures.get(key,0)>=3
            if not w.managed:
                w.rect=r;w.minimised=row['state']=='minimised';continue
            if key in self.pins and not w.pinned:w.rect=r;w.pinned=True
            elif key not in self.pins:w.pinned=False
            if w.pinned:w.rect=r  # user's placement is the fixed obstacle; manager never drags a pin
            pending=self.pending.get(key)
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
                    if self.failures[key]>=3:w.managed=False
                    self.state=solve(self.state,{'type':'arrange'}).state
                self.pending.pop(key,None)
            if old and row['focused'] and not old['focused']:
                self.state=solve(self.state,{'type':'focus','key':key}).state
            if old and old['state']!=row['state'] and key not in self.pending:
                # Manager-requested minimise is already reflected in the plan.
                if row['state']=='minimised' and not w.minimised:
                    self.state=solve(self.state,{'type':'minimise','key':key}).state
                elif row['state']!='minimised' and w.minimised and old['state']=='minimised':
                    self.state=solve(self.state,{'type':'restore','key':key}).state
            if self.gesture and self.gesture['key']==key:
                self.preview=solve(self.gesture['base'],{'type':'drag-move','key':key,'rect':r.values()})
                if self.mode=='live':
                    if not self.ghost:
                        if self.ghost_factory:self.ghost=self.ghost_factory()
                        else:
                            from ghost import Ghost
                            self.ghost=Ghost()
                    self.ghost.update([box for k,box in self.preview.placements.items() if k!=key and box!=self.gesture['base'].windows[k].rect])
            elif old and old['rect']!=row['rect'] and not pending:
                # A self-resizer or move without native modal hooks still gets reconciled.
                self.state=solve(self.state,{'type':'drag-end','key':key,'rect':r.values()}).state
        # Unmanaged windows are fixed within windows; no duplicate obstacles.
        if not self.gesture:self.state=solve(self.state,{'type':'arrange'}).state
        plan=self.preview if self.gesture and self.preview else solve(self.state,{'type':'noop'})
        rows_out=[]
        for key,row in current.items():
            target=plan.placements.get(key);w=self.state.windows[key]
            rows_out.append({'key':key,'app':row['app'],'actual':row['rect'],'planned':target.values() if target else None,
                'minimise':key in plan.minimise,'managed':w.managed,'pinned':w.pinned})
            if old:=self.actual.get(key):
                if old!=row:self.changed.add(key)
            else:self.changed.add(key)
        result={'at':time.time(),'mode':self.mode,'gated':[],'work':work.values(),'plan':rows_out,
            'minimise':[r['app'] for r in rows_out if r['minimise']], 'notes':plan.notes,'valid':valid(plan.state)}
        if self.mode=='shadow':
            with self.log_path.open('a',encoding='utf-8') as f:f.write(json.dumps(result)+'\n')
        elif self.mode=='live' and not self.gesture:
            self.apply(plan,current)
        self.actual=deepcopy(current)
        return result

    def _managed(self,row):
        return row['managed'] and self.failures.get(row['key'],0)<3 and row['app'].lower() not in {x.lower() for x in self.settings['never']} and (
            self.settings['manage']=='all' or row['key'] in self.adopted)

    def apply(self,plan,current):
        if not valid(plan.state):return  # impossible fixed geometry fails closed
        if self.gate_fn():return
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
            if self.state.windows[key].pinned:continue
            if key in self.pending:continue
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
