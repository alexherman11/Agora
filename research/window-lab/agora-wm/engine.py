"""Deterministic, integer-pixel free placement. No OS imports or side effects.

solve returns a Result (placements, minimise, notes) with .state for the next event.
Events are JSON-shaped dictionaries; rectangles are [x,y,width,height].
"""
from dataclasses import dataclass, field, replace
from copy import deepcopy


@dataclass(frozen=True, order=True)
class Rect:
    x: int
    y: int
    w: int
    h: int

    @property
    def right(self): return self.x + self.w
    @property
    def bottom(self): return self.y + self.h
    def contains(self, r):
        return self.x <= r.x and self.y <= r.y and self.right >= r.right and self.bottom >= r.bottom
    def near(self, r, gap=0):
        return (self.x < r.right + gap and r.x < self.right + gap
                and self.y < r.bottom + gap and r.y < self.bottom + gap)
    def values(self): return [self.x, self.y, self.w, self.h]


SQUASH = 0.6      # an arrange never shrinks a window below this share of its usual width or height
PIN_MIN = 0.5     # a pin may be narrowed to this share of its pinned width when something big opens (wm-settings pin_min)


@dataclass
class Window:
    key: str
    preferred: tuple = (900, 700)
    minimum: tuple = (240, 160)
    rect: Rect | None = None
    pinned: bool = False
    last_used: int = 0
    managed: bool = True
    minimised: bool = False
    home: Rect | None = None   # a pin's chosen rectangle; it may be narrowed from it, and grows back to it


@dataclass
class State:
    work: Rect = Rect(0, 60, 3840, 2034)
    gap_inner: int = 16
    gap_outer: int = 16
    windows: dict = field(default_factory=dict)
    obstacles: list = field(default_factory=list)
    when_full: str = 'minimise-oldest'
    reflow: str = 'gentle'
    clock: int = 0
    gesture: dict | None = None
    displacement: dict = field(default_factory=dict)  # victim -> causal stack, newest last
    pin_min: float = PIN_MIN

    @property
    def bounds(self):
        g = self.gap_outer
        return Rect(self.work.x+g, self.work.y+g, max(0,self.work.w-2*g), max(0,self.work.h-2*g))


@dataclass
class Result:
    placements: dict
    minimise: list
    notes: list
    state: State
    def __iter__(self): return iter((self.placements, self.minimise, self.notes))


def copy_state(s):
    """Cheap structural copy: Rects are frozen, Windows are copied one level. Same result as deepcopy, ~20x faster."""
    return replace(s,windows={k:replace(w) for k,w in s.windows.items()},obstacles=list(s.obstacles),
        gesture=deepcopy(s.gesture), displacement=deepcopy(s.displacement))


def occupied(s, exclude=()):
    return list(s.obstacles) + [w.rect for k,w in sorted(s.windows.items())
        if k not in exclude and w.rect and not w.minimised]


def free_rectangles(bounds, blocks, gap):
    """Maximal empty rectangles by splitting; overlapping candidates are intentional."""
    free = [bounds]
    for b in blocks:
        b = Rect(b.x-gap,b.y-gap,b.w+2*gap,b.h+2*gap)
        nxt = []
        for r in free:
            if not r.near(b):
                nxt.append(r); continue
            if b.x > r.x: nxt.append(Rect(r.x,r.y,b.x-r.x,r.h))
            if b.right < r.right: nxt.append(Rect(b.right,r.y,r.right-b.right,r.h))
            if b.y > r.y: nxt.append(Rect(r.x,r.y,r.w,b.y-r.y))
            if b.bottom < r.bottom: nxt.append(Rect(r.x,b.bottom,r.w,r.bottom-b.bottom))
        unique = sorted(set(r for r in nxt if r.w>0 and r.h>0))
        free = [r for r in unique if not any(q != r and q.contains(r) for q in unique)]
    return free


def fit(s, w, fill=False, least=None):
    """Best free spot. least=(w,h): accept a smaller spot, down to that size (a big window opening onto a full screen)."""
    candidates = []
    for r in free_rectangles(s.bounds, occupied(s,(w.key,)),s.gap_inner):
        width,height = (r.w,r.h) if fill else tuple(max(p,m) for p,m in zip(w.preferred,w.minimum))
        reduced=bool(least) and not fill and r.w>=least[0] and r.h>=least[1]
        if reduced:width,height=min(width,r.w),min(height,r.h)
        if width < w.minimum[0] or height < w.minimum[1] or width>r.w or height>r.h: continue
        x = min(max(w.rect.x if w.rect else r.x,r.x),r.right-width)
        y = min(max(w.rect.y if w.rect else r.y,r.y),r.bottom-height)
        box = Rect(x,y,width,height)
        distance = abs(x-w.rect.x)+abs(y-w.rect.y) if w.rect else 0
        # fill, or a window that cannot have its preferred size: the biggest spot first, then the nearest
        score = (-width*height,distance,y,x) if fill or least else (distance,r.w*r.h-width*height,y,x)
        candidates.append((score,box))
    return min(candidates)[1] if candidates else None


def clamp(r,b,minimum):
    width,height = min(b.w,max(minimum[0],r.w)),min(b.h,max(minimum[1],r.h))
    return Rect(min(max(r.x,b.x),b.right-width),min(max(r.y,b.y),b.bottom-height),width,height)


def valid(s):
    boxes = [(k,w.rect) for k,w in s.windows.items() if w.rect and not w.minimised]
    for k,r in boxes:
        w=s.windows[k]
        if w.managed and not s.bounds.contains(r): return False
        if w.managed and not w.pinned and (r.w<w.minimum[0] or r.h<w.minimum[1]): return False
        if w.managed and any(r.near(b,s.gap_inner) for b in s.obstacles): return False
    return not any(a.near(b,s.gap_inner) for i,(ka,a) in enumerate(boxes) for kb,b in boxes[i+1:]
        if s.windows[ka].managed or s.windows[kb].managed)


def push(s, key, target, shrink=False, held=frozenset(), budget=None):
    """Only the collision-connected component can move; bounded backtracking.
    held: neighbours the dragged window may cover for now (a drag that has not rested on them long enough). The
    dragged window passes over them; anything else cascading into them treats them as walls."""
    budget=[budget or max(80,len(s.windows)*12)]
    g=s.gap_inner;bounds=s.bounds;obstacles=s.obstacles;meta=s.windows
    # The search moves rectangles in a plain dict (one shallow copy per node), not whole States: same search, same
    # answers, about twenty times cheaper; a drag tick with twenty windows has to fit in a 16 ms frame.
    order=[k for k in sorted(meta) if not meta[k].minimised and meta[k].rect]
    def move(layout,k,r,path):
        budget[0]-=1
        if budget[0]<0 or k in path or not bounds.contains(r): return None
        if any(r.near(b,g) for b in obstacles): return None
        trial=dict(layout);trial[k]=r
        for other in order:
            if other==k: continue
            b=trial[other]
            if not r.near(b,g): continue
            if k==key and other in held: continue
            w=meta[other]
            if w.pinned or not w.managed or other in path or other in held: return None
            dx=min(r.right+g-b.x,b.right+g-r.x)
            dy=min(r.bottom+g-b.y,b.bottom+g-r.y)
            horizontal=[Rect(r.right+g,b.y,b.w,b.h),Rect(r.x-g-b.w,b.y,b.w,b.h)]
            vertical=[Rect(b.x,r.bottom+g,b.w,b.h),Rect(b.x,r.y-g-b.h,b.w,b.h)]
            for group in (horizontal,vertical):
                group.sort(key=lambda q:abs(q.x-b.x)+abs(q.y-b.y))
            options=(horizontal+vertical) if dx<=dy else (vertical+horizontal)
            if shrink:
                # Shrink only down to SQUASH of its usual size (never a strip); past that it gets minimised instead.
                mw=max(w.minimum[0],int(min(w.preferred[0],bounds.w)*SQUASH));mh=max(w.minimum[1],int(min(w.preferred[1],bounds.h)*SQUASH))
                if b.w<mw or b.h<mh:mw,mh=min(mw,b.w),min(mh,b.h)
                options += [Rect(b.x,b.y,min(b.w,max(mw,r.x-g-b.x)),b.h),
                    Rect(r.right+g,b.y,max(mw,b.right-r.right-g),b.h),
                    Rect(b.x,b.y,b.w,min(b.h,max(mh,r.y-g-b.y))),
                    Rect(b.x,r.bottom+g,b.w,max(mh,b.bottom-r.bottom-g))]
            resolved=None
            for q in options:
                if q.near(r,g): continue
                resolved=move(trial,other,q,path|{k})
                if resolved is not None: break
            if resolved is None:return None
            trial=resolved
        return trial
    found=move({k:meta[k].rect for k in order},key,target,set())
    if found is None:return None
    out=copy_state(s)
    for k,r in found.items():out.windows[k].rect=r
    return out


def anchor(r, width, bounds):
    """r at a new width, keeping the edge nearest the screen edge (a pin on the right keeps its right edge)."""
    if r.x+r.w/2 > bounds.x+bounds.w/2:return Rect(r.right-width,r.y,width,r.h)
    return Rect(r.x,r.y,width,r.h)


def narrow_pins(s, w, least=None):
    """Make room for w by narrowing pins toward pin_min of their pinned width, in eighths, all together, stopping
    at the first eighth where w fits (preferred, else at least `least`). Returns the spot for w, or None with every
    pin restored. Never moves a pin off its anchored edge."""
    pins=[v for _,v in sorted(s.windows.items()) if v.pinned and v.rect and not v.minimised and v.key!=w.key]
    if not pins:return None
    original={v.key:v.rect for v in pins}
    for step in range(1,9):
        for v in pins:
            r=original[v.key];home=v.home or r
            floor=min(r.w,max(v.minimum[0],int(home.w*s.pin_min)))
            v.rect=anchor(r,r.w-(r.w-floor)*step//8,s.bounds)
        found=fit(s,w) or (fit(s,w,least=least) if least else None)
        if found:return found
    for v in pins:v.rect=original[v.key]
    return None


def regrow_pins(s):
    """A narrowed pin takes back its pinned width first, as far as free space allows."""
    for k,v in sorted(s.windows.items()):
        if not (v.pinned and v.home and v.rect and not v.minimised and v.rect.w<v.home.w):continue
        others=occupied(s,(k,));low,high=v.rect.w,v.home.w
        while low<high:
            mid=(low+high+1)//2;q=anchor(v.rect,mid,s.bounds)
            if s.bounds.contains(q) and not any(q.near(b,s.gap_inner) for b in others):low=mid
            else:high=mid-1
        v.rect=anchor(v.rect,low,s.bounds)


def gentle(s):
    for k,w in sorted(s.windows.items()):
        if not w.rect or w.minimised or w.pinned or not w.managed or k in s.displacement: continue
        r=w.rect
        # One bounded growth step, never a relocation. Only on close/minimise.
        goal=Rect(r.x,r.y,max(r.w,min(w.preferred[0],r.w+max(1,w.preferred[0]//8))),
            max(r.h,min(w.preferred[1],r.h+max(1,w.preferred[1]//8))))
        for q in (goal,replace(goal,h=r.h),replace(goal,w=r.w)):
            if s.bounds.contains(q) and not any(q.near(b,s.gap_inner) for b in occupied(s,(k,))):
                w.rect=q;break



def adaptive(s, incoming):
    """Bounded repacking before eviction. Pins and unmanaged geometry remain fixed.
    Prefer large useful tiles, then their learned minima. Never wakes hidden apps.
    """
    movable=[w for w in s.windows.values() if not w.minimised and w.managed and not w.pinned]
    fixed=list(s.obstacles)+[w.rect for w in s.windows.values()
        if not w.minimised and w.rect and (w.pinned or not w.managed)]
    if not movable or len(movable)>16:return False
    for scale in (1, .85, .7, .6, .45, 0):
        budget=[300]
        sizes={w.key:tuple(max(m,round(p*scale)) for p,m in zip(w.preferred,w.minimum)) for w in movable}
        orders=[sorted(movable,key=lambda w:(-sizes[w.key][0]*sizes[w.key][1],w.key)),
                sorted(movable,key=lambda w:(w.key!=incoming,-w.last_used,w.key))]
        def pack(todo,blocks,result):
            if not todo:return result
            if budget[0]<=0:return None
            budget[0]-=1
            w=todo[0];width,height=sizes[w.key];candidates=[]
            for r in free_rectangles(s.bounds,blocks,s.gap_inner):
                if width>r.w or height>r.h:continue
                for x,y in ((r.x,r.y),(r.right-width,r.y),(r.x,r.bottom-height)):
                    q=Rect(x,y,width,height)
                    distance=abs(x-w.rect.x)+abs(y-w.rect.y) if w.rect else 0
                    candidates.append((r.w*r.h-width*height,distance,q))
            for _,_,q in sorted(set(candidates))[:8]:
                found=pack(todo[1:],blocks+[q],{**result,w.key:q})
                if found is not None:return found
            return None
        for order in orders:
            found=pack(order,fixed,{})
            if found is not None:
                for key,rect in found.items():s.windows[key].rect=rect
                return True
    return False


def placement(w):return (w.rect,w.minimised)


def remember_displacement(s,before,cause):
    for key,old in before.windows.items():
        w=s.windows.get(key)
        if key==cause or not w or old.minimised or not w.managed:continue
        if placement(w)!=placement(old):
            s.displacement.setdefault(key,[]).append({'cause':cause,'before':placement(old),
                'after':placement(w),'released':False})


def restore_displacement(s,cause):
    """Release only this opener's debt; buried debt waits for newer opens to close.
    A changed victim invalidates its debt. Batch exact restoration handles swaps;
    a blocked restore stays pending, never pushes other windows out of the way.
    """
    for key in list(s.displacement):
        if key not in s.windows:del s.displacement[key];continue
        for entry in s.displacement[key]:
            if entry['cause']==cause:entry['released']=True
    proposals={}
    for key,stack in list(s.displacement.items()):
        w=s.windows[key]
        if not stack or not w.managed or placement(w)!=stack[-1]['after']:
            del s.displacement[key];continue
        count=0;target=placement(w)
        for entry in reversed(stack):
            if not entry['released']:break
            target=entry['before'];count+=1
        if count:proposals[key]=(target,count)
    trial=copy_state(s)
    for key,(target,_) in proposals.items():trial.windows[key].rect,trial.windows[key].minimised=target
    if valid(trial):
        for key,(target,count) in proposals.items():
            s.windows[key].rect,s.windows[key].minimised=target
            del s.displacement[key][-count:]
    else:
        for key,(target,count) in proposals.items():
            w=s.windows[key];rect,hidden=target
            if hidden:continue
            if rect and s.bounds.contains(rect) and rect.w>=w.minimum[0] and rect.h>=w.minimum[1] and not any(
                    rect.near(b,s.gap_inner) for b in occupied(s,(key,))):
                w.rect=rect;w.minimised=False;del s.displacement[key][-count:]
            elif w.minimised and rect:
                found=fit(s,replace(w,preferred=(rect.w,rect.h),rect=rect),least=w.minimum)
                if found:
                    w.rect=found;w.minimised=False
                    s.displacement[key][-1]['after']=placement(w)
    s.displacement={k:v for k,v in s.displacement.items() if v}


def solve(state,event=None):
    s=copy_state(state);e=event or {'type':'arrange'};kind=e['type'];notes=[]
    key=e.get('key');w=s.windows.get(key)
    if kind=='open' and w is not None:kind='restore'
    if kind in ('minimise','restore','pin','unpin','drag-start','resize-start','drag-move','drag-end','resize-move','resize-end','manual'):
        s.displacement.pop(key,None)
    if kind=='open':
        data=dict(e.get('window',{}));key=data.pop('key',key)
        if 'rect' in data and not isinstance(data['rect'],Rect):data['rect']=Rect(*data['rect'])
        w=Window(key,**data);s.windows[key]=w
    if kind in ('focus','open','restore') and w:
        s.clock+=1;w.last_used=s.clock
    if kind=='close':s.windows.pop(key,None)
    elif kind=='minimise' and w and not w.pinned:w.minimised=True
    elif kind=='pin' and w and not w.minimised and w.rect:w.pinned=True;w.home=w.rect
    elif kind=='unpin' and w:w.pinned=False;w.home=None
    elif kind=='work-area':s.work=Rect(*e['rect'])
    elif kind in ('drag-start','resize-start') and w:s.gesture={'key':key,'rect':w.rect.values()}
    elif kind in ('drag-move','drag-end','resize-move','resize-end') and w and not w.pinned and w.managed:
        target=clamp(Rect(*e['rect']),s.bounds,w.minimum)
        original=deepcopy(s);solved=push(s,key,target) or push(s,key,target,True)
        if solved is None:
            reduced=deepcopy(s)
            for victim in sorted((v for v in reduced.windows.values() if v.key!=key and not v.pinned
                    and v.managed and not v.minimised),key=lambda v:(v.last_used,v.key)):
                victim.minimised=True
                solved=push(reduced,key,target,True)
                if solved is not None:break
        if solved is not None:s=solved
        else:
            # Clamp by a monotone search along the gesture from the last legal position.
            start=original.windows[key].rect
            if start:
                low,high=0,1024;best=original
                for _ in range(10):
                    mid=(low+high+1)//2
                    q=Rect(*(a+(b-a)*mid//1024 for a,b in zip(start.values(),target.values())))
                    attempt=push(original,key,q,True)
                    if attempt:low=mid;best=attempt
                    else:high=mid-1
                s=best
            notes.append('gesture clamped by fixed geometry')
        if kind.endswith('end'):s.gesture=None
    if kind in ('open','restore') and w:
        w=s.windows[key];w.minimised=False
        if w.pinned and w.rect:
            conflicts=[v for v in s.windows.values() if v.key!=key and not v.minimised and v.rect and w.rect.near(v.rect,s.gap_inner)]
            if not s.bounds.contains(w.rect) or any(v.pinned or not v.managed for v in conflicts) or any(w.rect.near(b,s.gap_inner) for b in s.obstacles):
                w.minimised=True;notes.append('pin restore blocked by fixed geometry')
            else:
                for v in conflicts:v.minimised=True
        if not w.pinned and w.managed:
            # Preserve a free open, then repack visible tiles within usable minima.
            # Only if bounded repacking fails do LRU victims give way. No process closes.
            previous_minimised={k:v.minimised for k,v in s.windows.items() if k!=key}
            want=tuple(max(p,m) for p,m in zip(w.preferred,w.minimum))
            least=(max(w.minimum[0],int(want[0]*SQUASH)),max(w.minimum[1],int(want[1]*SQUASH)))
            def place():return fit(s,w) or fit(s,w,least=least)
            found=fit(s,w)
            if found is None:found=fit(s,w,least=least)
            if found is None and adaptive(s,key):found=s.windows[key].rect
            if found is None:
                victims=[]
                for v in sorted((v for v in s.windows.values() if v.key!=key and not v.pinned and v.managed
                        and not v.minimised),key=lambda v:(v.last_used,v.key)):
                    v.minimised=True;victims.append(v);found=place()
                    if found is None and adaptive(s,key):found=s.windows[key].rect
                    if found:break
                if found:
                    for v in reversed(victims[:-1]):
                        if v.rect and not v.rect.near(found,s.gap_inner) and not any(v.rect.near(b,s.gap_inner) for b in occupied(s,(v.key,key))):
                            v.minimised=False
            if found is None:found=narrow_pins(s,w,least)
            if found is None:
                for k,was in previous_minimised.items():s.windows[k].minimised=was
                w.minimised=True;notes.append('new window cannot fit around fixed geometry')
            else:w.rect=found
    if kind in ('open','restore') and key in s.windows and not s.windows[key].minimised:
        remember_displacement(s,state,key)
    if kind=='work-area':
        # A pin stays on screen: moved and narrowed only as far as the new work area needs.
        for k,v in sorted(s.windows.items()):
            if v.pinned and v.rect and not v.minimised and not s.bounds.contains(v.rect):
                v.rect=clamp(v.rect,s.bounds,(min(v.minimum[0],s.bounds.w),min(v.minimum[1],s.bounds.h)))
    if kind in ('arrange','work-area','unpin'):
        # Preserve every already legal rectangle; repair only conflicts/out-of-bounds.
        accepted=list(s.obstacles)+[v.rect for v in s.windows.values() if v.rect and not v.minimised and (v.pinned or not v.managed)]
        for k,v in sorted(s.windows.items(),key=lambda kv:(-kv[1].last_used,kv[0])):
            if v.minimised or v.pinned or not v.managed:continue
            if v.rect and s.bounds.contains(v.rect) and v.rect.w>=v.minimum[0] and v.rect.h>=v.minimum[1] and not any(v.rect.near(b,s.gap_inner) for b in accepted):
                accepted.append(v.rect);continue
            free=free_rectangles(s.bounds,accepted,s.gap_inner)
            # A gap much smaller than the window is not a place for it: minimise it instead of squashing it into a
            # strip (live, 26 Oct: two Agora windows came out 161 px tall). Usual size = its own size, else preferred.
            want=(v.rect.w,v.rect.h) if v.rect else v.preferred
            least=(max(v.minimum[0],int(min(want[0],s.bounds.w)*SQUASH)),max(v.minimum[1],int(min(want[1],s.bounds.h)*SQUASH)))
            options=[Rect(r.x,r.y,min(max(v.preferred[0],least[0]),r.w),min(max(v.preferred[1],least[1]),r.h)) for r in free
                if r.w>=least[0] and r.h>=least[1]]
            if options:
                v.rect=min(options,key=lambda r:(abs(r.x-(v.rect.x if v.rect else 0))+abs(r.y-(v.rect.y if v.rect else 0)),-r.w*r.h,r))
                accepted.append(v.rect)
            else:v.minimised=True
    if kind in ('close','minimise'):
        restore_displacement(s,key)
        regrow_pins(s)
        if s.reflow=='gentle':gentle(s)
    if not valid(s):notes.append('infeasible fixed geometry: pins/obstacles retained; no safe global solution')
    return Result({k:v.rect for k,v in sorted(s.windows.items()) if v.rect and not v.minimised},
        sorted(k for k,v in s.windows.items() if v.minimised),notes,s)
