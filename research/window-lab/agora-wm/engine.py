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


def fit(s, w, fill=False):
    candidates = []
    for r in free_rectangles(s.bounds, occupied(s,(w.key,)),s.gap_inner):
        width,height = (r.w,r.h) if fill else tuple(max(p,m) for p,m in zip(w.preferred,w.minimum))
        if width < w.minimum[0] or height < w.minimum[1] or width>r.w or height>r.h: continue
        x = min(max(w.rect.x if w.rect else r.x,r.x),r.right-width)
        y = min(max(w.rect.y if w.rect else r.y,r.y),r.bottom-height)
        box = Rect(x,y,width,height)
        distance = abs(x-w.rect.x)+abs(y-w.rect.y) if w.rect else 0
        score = (-width*height,distance,y,x) if fill else (distance,r.w*r.h-width*height,y,x)
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


def push(s, key, target, shrink=False):
    """Only the collision-connected component can move; bounded backtracking."""
    budget=[max(80,len(s.windows)*12)]
    def move(layout,k,r,path):
        budget[0]-=1
        if budget[0]<0 or k in path or not layout.bounds.contains(r): return None
        if any(r.near(b,layout.gap_inner) for b in layout.obstacles): return None
        trial=deepcopy(layout);trial.windows[k].rect=r
        for other in sorted(trial.windows):
            w=trial.windows[other]
            if other==k or w.minimised or not w.rect or not r.near(w.rect,trial.gap_inner): continue
            if w.pinned or not w.managed or other in path: return None
            b=w.rect;g=trial.gap_inner
            dx=min(r.right+g-b.x,b.right+g-r.x)
            dy=min(r.bottom+g-b.y,b.bottom+g-r.y)
            horizontal=[Rect(r.right+g,b.y,b.w,b.h),Rect(r.x-g-b.w,b.y,b.w,b.h)]
            vertical=[Rect(b.x,r.bottom+g,b.w,b.h),Rect(b.x,r.y-g-b.h,b.w,b.h)]
            for group in (horizontal,vertical):
                group.sort(key=lambda q:abs(q.x-b.x)+abs(q.y-b.y))
            options=(horizontal+vertical) if dx<=dy else (vertical+horizontal)
            if shrink:
                mw,mh=w.minimum
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
    return move(s,key,target,set())


def gentle(s):
    for k,w in sorted(s.windows.items()):
        if not w.rect or w.minimised or w.pinned or not w.managed: continue
        r=w.rect
        # One bounded growth step, never a relocation. Only on close/minimise.
        goal=Rect(r.x,r.y,max(r.w,min(w.preferred[0],r.w+max(1,w.preferred[0]//8))),
            max(r.h,min(w.preferred[1],r.h+max(1,w.preferred[1]//8))))
        for q in (goal,replace(goal,h=r.h),replace(goal,w=r.w)):
            if s.bounds.contains(q) and not any(q.near(b,s.gap_inner) for b in occupied(s,(k,))):
                w.rect=q;break


def solve(state,event=None):
    s=deepcopy(state);e=event or {'type':'arrange'};kind=e['type'];notes=[]
    key=e.get('key');w=s.windows.get(key)
    if kind=='open':
        data=dict(e.get('window',{}));key=data.pop('key',key)
        if 'rect' in data and not isinstance(data['rect'],Rect):data['rect']=Rect(*data['rect'])
        w=Window(key,**data);s.windows[key]=w
    if kind in ('focus','open','restore') and w:
        s.clock+=1;w.last_used=s.clock
    if kind=='close':s.windows.pop(key,None)
    elif kind=='minimise' and w and not w.pinned:w.minimised=True
    elif kind=='pin' and w and not w.minimised and w.rect:w.pinned=True
    elif kind=='unpin' and w:w.pinned=False
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
            previous_minimised={k:v.minimised for k,v in s.windows.items() if k!=key}
            found=fit(s,w)
            if found is None and s.when_full=='focus':
                for other in s.windows.values():
                    if other.key!=key and other.managed and not other.pinned:other.minimised=True
                found=fit(s,w)
            if found is None and s.when_full=='fill':found=fit(s,w,True)
            if found is None and s.when_full!='fill':
                for v in sorted((v for v in s.windows.values() if v.key!=key and not v.pinned and v.managed
                        and not v.minimised),key=lambda v:(v.last_used,v.key)):
                    v.minimised=True;found=fit(s,w)
                    if found:break
            if found is None:
                for k,was in previous_minimised.items():s.windows[k].minimised=was
                w.minimised=True;notes.append('new window cannot fit around fixed geometry')
            else:w.rect=found
    if kind in ('arrange','work-area','unpin'):
        # Preserve every already legal rectangle; repair only conflicts/out-of-bounds.
        accepted=list(s.obstacles)+[v.rect for v in s.windows.values() if v.rect and not v.minimised and (v.pinned or not v.managed)]
        for k,v in sorted(s.windows.items(),key=lambda kv:(-kv[1].last_used,kv[0])):
            if v.minimised or v.pinned or not v.managed:continue
            if v.rect and s.bounds.contains(v.rect) and v.rect.w>=v.minimum[0] and v.rect.h>=v.minimum[1] and not any(v.rect.near(b,s.gap_inner) for b in accepted):
                accepted.append(v.rect);continue
            free=free_rectangles(s.bounds,accepted,s.gap_inner)
            options=[Rect(r.x,r.y,min(max(v.preferred[0],v.minimum[0]),r.w),min(max(v.preferred[1],v.minimum[1]),r.h)) for r in free
                if r.w>=v.minimum[0] and r.h>=v.minimum[1]]
            if options:
                v.rect=min(options,key=lambda r:(abs(r.x-(v.rect.x if v.rect else 0))+abs(r.y-(v.rect.y if v.rect else 0)),-r.w*r.h,r))
                accepted.append(v.rect)
            else:v.minimised=True
    if kind in ('close','minimise') and s.reflow=='gentle':gentle(s)
    if not valid(s):notes.append('infeasible fixed geometry: pins/obstacles retained; no safe global solution')
    return Result({k:v.rect for k,v in sorted(s.windows.items()) if v.rect and not v.minimised},
        sorted(k for k,v in s.windows.items() if v.minimised),notes,s)
