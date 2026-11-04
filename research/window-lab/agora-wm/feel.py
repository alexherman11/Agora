"""EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
(people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.

The feel of a drag or a resize: centre crossings for moves, dwell for resizes, swap or slide, eased motion,
settling back, snapping, shared edges and the landing. Pure and deterministic: time in ms is an input; nothing here
reads a clock, the screen or the world. The design and its numbers are in WM.md, "Feel".

    g = Gesture(state, key, start_rect, t_ms, Feel())
    frame = g.step(rect, t_ms)      # every tick while the person drags: ghosts + landing to show
    result = g.release(rect, t_ms)  # at mouse-up: an engine Result with the settled layout

Rectangles are engine Rects in physical pixels; Feel's pixel numbers are at 100 % and multiplied by `scale`.
"""
from dataclasses import dataclass, field
from engine import (Rect, SQUASH, MOTION_MS, copy_state, free_rectangles, push, solve, valid,
                    crossed_centre, drop_spaces, choose_space)


# ------------------------------------------------------------------ tunables
@dataclass(frozen=True)
class Feel:
    dwell_ms: int = 350        # rest on a window this long before it gives way (AOSP Launcher3 REORDER_TIMEOUT)
    snap_px: int = 16          # snap radius at 100 %
    deadzone_px: int = 10      # movement before a drag or resize breaks free
    motion_ms: int = MOTION_MS # animation; overridden by wm-settings
    pin_min: float = 0.5       # narrowest a pin may get, share of its pinned width (engine reads it via State)
    edges: str = 'shared'      # snapped windows share a resized edge ('free': they don't)
    return_ms: int = 250       # a yielded window waits this long after the drag leaves, then eases home
    fling_px_s: int = 600      # faster than this (100 %) is transit: dwell does not accumulate
    bond_px: int = 2           # two edges within this of exactly one gap apart are a shared (snapped) edge
    follow_px: int = 64        # a yielded edge-follower jumps (no easing) to targets this close
    idle_ms: int = 10000       # no movement and no drag-end for this long: the gesture is over
    scale: float = 1.0         # monitor DPI / 96

    def px(self, value):
        return int(round(value * self.scale))


SETTINGS = {'dwell_ms': (int, 0, 2000), 'snap_px': (int, 0, 64), 'deadzone_px': (int, 0, 64),
            'motion_ms': (int, 0, 1000), 'pin_min': (float, 0.2, 1.0)}


def from_settings(settings, scale=1.0):
    """Feel from wm-settings (values may arrive as text). Missing keys keep defaults; bad ones raise ValueError."""
    values = {}
    for name, (kind, low, high) in SETTINGS.items():
        raw = settings.get(name)
        if raw is None or raw == '':
            continue
        if isinstance(raw, bool):
            raise ValueError(f'{name} must be a number')
        try:
            number = float(raw)
        except (TypeError, ValueError):
            raise ValueError(f'{name} must be a number') from None
        if not low <= number <= high:
            raise ValueError(f'{name} must be between {low} and {high}')
        values[name] = int(round(number)) if kind is int else number
    edges = settings.get('edges') or 'shared'
    if edges not in ('shared', 'free'):
        raise ValueError('edges must be shared or free')
    if not isinstance(scale, (int, float)) or not 0.5 <= scale <= 4:
        scale = 1.0
    return Feel(**values, edges=edges, scale=float(scale))


# ------------------------------------------------------------------ easing
def _bezier(p1, p2, u):
    return 3 * (1 - u) ** 2 * u * p1 + 3 * (1 - u) * u * u * p2 + u ** 3


def ease(p, curve=(0.2, 0.0, 0.0, 1.0)):
    """cubic-bezier(curve) at progress p in [0,1] (Material 3 standard by default). Bisection: exact enough, pure."""
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    x1, y1, x2, y2 = curve
    low, high = 0.0, 1.0
    for _ in range(24):
        mid = (low + high) / 2
        if _bezier(x1, x2, mid) < p:
            low = mid
        else:
            high = mid
    return _bezier(y1, y2, (low + high) / 2)


def lerp(a, b, e):
    return Rect(*(round(x + (y - x) * e) for x, y in zip(a.values(), b.values())))


# ------------------------------------------------------------------ geometry
EDGES = ('left', 'right', 'top', 'bottom')


def edge(r, name):
    return {'left': r.x, 'right': r.right, 'top': r.y, 'bottom': r.bottom}[name]


def with_edges(r, left=None, right=None, top=None, bottom=None):
    x0 = r.x if left is None else left
    x1 = r.right if right is None else right
    y0 = r.y if top is None else top
    y1 = r.bottom if bottom is None else bottom
    return Rect(x0, y0, x1 - x0, y1 - y0)


def centre_in(a, b):
    cx, cy = a.x + a.w / 2, a.y + a.h / 2
    return b.x <= cx < b.right and b.y <= cy < b.bottom


def penetration(a, b, gap):
    """How far a reaches into b (closer than gap), as (axis, depth, share of b along that axis); None if clear."""
    if not a.near(b, gap):
        return None
    dx = min(a.right + gap - b.x, b.right + gap - a.x)
    dy = min(a.bottom + gap - b.y, b.bottom + gap - a.y)
    if dx <= dy:
        return 'x', dx, dx / max(1, b.w)
    return 'y', dy, dy / max(1, b.h)


def pull_out(r, wall, gap, bounds):
    """Translate r out of wall along its axis of least penetration, to exactly gap away; prefer staying on screen."""
    hit = penetration(r, wall, gap)
    if not hit:
        return r
    options = [Rect(wall.x - gap - r.w, r.y, r.w, r.h), Rect(wall.right + gap, r.y, r.w, r.h),
               Rect(r.x, wall.y - gap - r.h, r.w, r.h), Rect(r.x, wall.bottom + gap, r.w, r.h)]
    def cost(q):
        return (not bounds.contains(q), abs(q.x - r.x) + abs(q.y - r.y), q.values())
    return min(options, key=cost)


def clamp_into(r, bounds, minimum, moving=EDGES):
    """Keep r on screen and at least minimum. A move translates; a resize (moving is a subset of the edges)
    clips only its moving edges and grows them back out to the minimum, so a fixed edge never shifts."""
    mw, mh = min(minimum[0], bounds.w), min(minimum[1], bounds.h)
    if set(moving) != set(EDGES):
        left, top, right, bottom = r.x, r.y, r.right, r.bottom
        if 'left' in moving:
            left = max(left, bounds.x)
        if 'right' in moving:
            right = min(right, bounds.right)
        if 'top' in moving:
            top = max(top, bounds.y)
        if 'bottom' in moving:
            bottom = min(bottom, bounds.bottom)
        if right - left < mw:
            if 'left' in moving and 'right' not in moving:
                left = right - mw
            else:
                right = left + mw
        if bottom - top < mh:
            if 'top' in moving and 'bottom' not in moving:
                top = bottom - mh
            else:
                bottom = top + mh
        r = Rect(left, top, right - left, bottom - top)
        if bounds.contains(r):
            return r
    w, h = min(max(r.w, mw), bounds.w), min(max(r.h, mh), bounds.h)
    x = min(max(r.x, bounds.x), bounds.right - w)
    y = min(max(r.y, bounds.y), bounds.bottom - h)
    return Rect(x, y, w, h)


def snap(r, others, bounds, gap, radius, moving=EDGES, move=True, minimum=(0, 0)):
    """Magnetic edges: screen edge (outer gap), a neighbour's facing edge at exactly the inner gap, or a parallel
    edge (aligned). Closest within radius wins; an axis whose snap would overlap something is left unsnapped."""
    if radius <= 0:
        return r
    def legal(q):
        return (bounds.contains(q) and q.w >= min(minimum[0], r.w) and q.h >= min(minimum[1], r.h)
                and not any(q.near(o, gap) for o in others))
    def facing(o, axis):            # o overlaps r along the other axis: its near edge is a snap-together edge
        return (o.y < r.bottom and r.y < o.bottom) if axis == 'x' else (o.x < r.right and r.x < o.right)
    def close(o, axis):             # o is near along the other axis: its parallel edge is an alignment edge
        return (o.y < r.bottom + radius + gap and r.y < o.bottom + radius + gap) if axis == 'x' else \
            (o.x < r.right + radius + gap and r.x < o.right + radius + gap)
    out = r
    for axis, lo, hi in (('x', 'left', 'right'), ('y', 'top', 'bottom')):
        low_targets, high_targets = [edge(bounds, lo)], [edge(bounds, hi)]
        for o in others:
            if facing(o, axis):
                low_targets.append(edge(o, hi) + gap)
                high_targets.append(edge(o, lo) - gap)
            if close(o, axis):
                low_targets.append(edge(o, lo))
                high_targets.append(edge(o, hi))
        options = []
        if lo in moving:
            options += [(abs(t - edge(out, lo)), t - edge(out, lo), 'lo') for t in low_targets]
        if hi in moving:
            options += [(abs(t - edge(out, hi)), t - edge(out, hi), 'hi') for t in high_targets]
        options = sorted(o for o in options if 0 < o[0] <= radius)
        for _, delta, which in options:
            if move:
                q = Rect(out.x + delta, out.y, out.w, out.h) if axis == 'x' else Rect(out.x, out.y + delta, out.w, out.h)
            elif which == 'lo':
                q = with_edges(out, left=out.x + delta) if axis == 'x' else with_edges(out, top=out.y + delta)
            else:
                q = with_edges(out, right=out.right + delta) if axis == 'x' else with_edges(out, bottom=out.bottom + delta)
            if q.w > 0 and q.h > 0 and legal(q):
                out = q
                break
    return out


def nearest_free(r, blockers, bounds, gap):
    """r moved the least distance to a spot at least gap from every blocker and on screen, or None."""
    best = None
    for f in free_rectangles(bounds, blockers, gap):
        if f.w < r.w or f.h < r.h:
            continue
        x, y = min(max(r.x, f.x), f.right - r.w), min(max(r.y, f.y), f.bottom - r.h)
        score = (abs(x - r.x) + abs(y - r.y), y, x)
        if best is None or score < best[0]:
            best = (score, Rect(x, y, r.w, r.h))
    return best[1] if best else None


# ------------------------------------------------------------------ the gesture
@dataclass
class Frame:
    ghosts: dict              # neighbour key -> Rect where it is shown now (only neighbours away from home)
    landing: Rect             # where the dragged window will land if released now
    kind: str                 # still | move | resize
    held: list = field(default_factory=list)       # neighbours resisting (in contact, not yet given way)
    yielded: list = field(default_factory=list)    # neighbours that gave way
    minimise: list = field(default_factory=list)   # neighbours the preview would minimise
    spaces: list = field(default_factory=list)     # vacant areas and column slots


class Gesture:
    """One drag or resize of one window, from Windows' move/size start to its end."""

    def __init__(self, state, key, rect, t, feel=None):
        self.feel = feel or Feel()
        self.base = copy_state(state)
        self.key = key
        self.start = Rect(*rect) if not isinstance(rect, Rect) else rect
        self.base.windows[key].rect = self.start          # the real place at mouse-down is the truth
        self.base.windows[key].minimised = False
        self.t = self.t0 = self.last_move = t
        self.T = self.start
        self.samples = [(t, self.start)]
        self.kind = 'still'
        self.moving = set()
        self.broken = False
        self.track = {}       # key -> {'held': ms, 'yielded': bool, 'away': t|None, 'floor': ms, 'pushed': bool}
        self.shown = {}       # key -> target Rect (or None: minimised in the preview)
        self.anim = {}        # key -> (from Rect, to Rect, t0)
        self.swaps = {}       # key -> slot Rect it swaps into
        self.bonds = {}       # key -> its edge that shares the dragged window's moving edge
        self.cut_side = {}    # key -> the side it first gave way on (kept while it still works: no flicker)
        self.contacts = {}
        self.floored = set()
        self.landing = self.start
        self.frame = Frame({}, self.start, 'still')
        self.plan = (self.base, self.start)

    # -- small helpers
    @property
    def gap(self):
        return self.base.gap_inner

    def home(self, k):
        return self.base.windows[k].rect

    def neighbours(self):
        return [k for k, w in sorted(self.base.windows.items())
                if k != self.key and w.rect and not w.minimised]

    def movable(self, k):
        w = self.base.windows[k]
        return w.managed and not w.pinned

    def tr(self, k):
        return self.track.setdefault(k, {'held': 0, 'yielded': False, 'away': None, 'floor': 0, 'pushed': False})

    def minimum(self):
        return self.base.windows[self.key].minimum

    def walls(self):
        """What never gives way: pins, unmanaged windows, obstacles."""
        return [self.home(k) for k in self.neighbours() if not self.movable(k)] + list(self.base.obstacles)

    def idle(self, t):
        return t - self.last_move >= self.feel.idle_ms

    def current(self, k, t):
        if k not in self.anim:
            return self.shown.get(k, self.home(k))
        frm, to, t0 = self.anim[k]
        if to is None:
            return None
        if frm is None or self.feel.motion_ms <= 0:
            return to
        return lerp(frm, to, ease((t - t0) / self.feel.motion_ms))

    # -- classification
    def _classify(self, T):
        if (T.w, T.h) != (self.start.w, self.start.h):
            self.kind = 'resize'
        elif self.kind != 'resize':
            self.kind = 'move'
        if self.kind == 'resize':
            self.moving |= {e for e in EDGES if edge(T, e) != edge(self.start, e)}
            if not self.bonds and self.feel.edges == 'shared':
                self.bonds = self._bonds()
        travel = max(abs(edge(T, e) - edge(self.start, e)) for e in EDGES)
        if travel >= self.feel.px(self.feel.deadzone_px):
            self.broken = True

    def _bonds(self):
        """Neighbours snapped to a moving edge at gesture start (exactly one gap apart, overlapping alongside)."""
        s, tol, g = self.start, self.feel.px(self.feel.bond_px), self.gap
        out = {}
        for k in self.neighbours():
            if not self.movable(k):
                continue
            h = self.home(k)
            beside_y = h.y < s.bottom and s.y < h.bottom
            beside_x = h.x < s.right and s.x < h.right
            if 'right' in self.moving and beside_y and abs(h.x - (s.right + g)) <= tol:
                out[k] = 'left'
            elif 'left' in self.moving and beside_y and abs(s.x - (h.right + g)) <= tol:
                out[k] = 'right'
            elif 'bottom' in self.moving and beside_x and abs(h.y - (s.bottom + g)) <= tol:
                out[k] = 'top'
            elif 'top' in self.moving and beside_x and abs(s.y - (h.bottom + g)) <= tol:
                out[k] = 'bottom'
        return out

    def _speed(self):
        t, T = self.samples[-1]
        t0, T0 = self.samples[0]
        if t <= t0:
            return 0.0
        travel = max(abs(edge(T, e) - edge(T0, e)) for e in EDGES)
        return travel * 1000.0 / (t - t0)

    def _facing(self, k, T):
        """Which of k's edges faces the dragged window's moving edge, and where T asks it to be (resize only)."""
        s, h, g = self.start, self.home(k), self.gap
        options = []
        if 'right' in self.moving and h.x >= s.right:
            options.append((T.right + g - h.x, 'left', T.right + g))
        if 'left' in self.moving and h.right <= s.x:
            options.append((h.right - (T.x - g), 'right', T.x - g))
        if 'bottom' in self.moving and h.y >= s.bottom:
            options.append((T.bottom + g - h.y, 'top', T.bottom + g))
        if 'top' in self.moving and h.bottom <= s.y:
            options.append((h.bottom - (T.y - g), 'bottom', T.y - g))
        if not options:
            return None
        _, side, at = min(options)
        return side, at

    def _floor(self, k):
        w = self.base.windows[k]
        h = w.rect
        return max(w.minimum[0], int(h.w * SQUASH)), max(w.minimum[1], int(h.h * SQUASH))

    def _shrunk(self, k, T, grow=False):
        """k with its facing edge moved to meet T at the gap, never below its floor. Returns (rect, hit_floor)."""
        face = self._facing(k, T) if k not in self.bonds else (self.bonds[k], {
            'left': T.right + self.gap, 'right': T.x - self.gap, 'top': T.bottom + self.gap, 'bottom': T.y - self.gap}[self.bonds[k]])
        h = self.home(k)
        if not face:
            return h, False
        side, at = face
        fw, fh = self._floor(k)
        if not grow:
            at = max(at, h.x) if side == 'left' else min(at, h.right) if side == 'right' else \
                max(at, h.y) if side == 'top' else min(at, h.bottom)
        hit = False
        if side == 'left':
            if h.right - at < fw:
                at, hit = h.right - fw, True
            q = with_edges(h, left=at)
        elif side == 'right':
            if at - h.x < fw:
                at, hit = h.x + fw, True
            q = with_edges(h, right=at)
        elif side == 'top':
            if h.bottom - at < fh:
                at, hit = h.bottom - fh, True
            q = with_edges(h, top=at)
        else:
            if at - h.y < fh:
                at, hit = h.y + fh, True
            q = with_edges(h, bottom=at)
        if grow and (q.w > h.w or q.h > h.h):
            q = self._limit_growth(k, h, q)
        return q, hit

    def _limit_growth(self, k, h, q):
        """A bonded neighbour that follows a shrinking edge grows only into free space."""
        b, g = self.base.bounds, self.gap
        others = [self.home(o) for o in self.neighbours() if o != k] + list(self.base.obstacles)
        left, right, top, bottom = max(q.x, b.x), min(q.right, b.right), max(q.y, b.y), min(q.bottom, b.bottom)
        for o in others:
            if q.x < h.x and o.y < h.bottom + g and h.y < o.bottom + g and o.right <= h.x:
                left = max(left, o.right + g)
            if q.right > h.right and o.y < h.bottom + g and h.y < o.bottom + g and o.x >= h.right:
                right = min(right, o.x - g)
            if q.y < h.y and o.x < h.right + g and h.x < o.right + g and o.bottom <= h.y:
                top = max(top, o.bottom + g)
            if q.bottom > h.bottom and o.x < h.right + g and h.x < o.right + g and o.y >= h.bottom:
                bottom = min(bottom, o.y - g)
        return with_edges(h, left=min(left, h.x), right=max(right, h.right), top=min(top, h.y), bottom=max(bottom, h.bottom))

    def _cut(self, k, T):
        """k shrunk away from T on one side (the biggest piece left), if that keeps it at or above its floor.
        Preferred to shoving a third window when sliding k aside would need one squeezed."""
        h, g = self.home(k), self.gap
        fw, fh = self._floor(k)
        pieces = {'bottom': with_edges(h, bottom=T.y - g), 'top': with_edges(h, top=T.bottom + g),
                  'right': with_edges(h, right=T.x - g), 'left': with_edges(h, left=T.right + g)}
        pieces = {side: q for side, q in pieces.items() if q.w >= fw and q.h >= fh and not q.near(T, g)}
        if not pieces:
            return None
        side = self.cut_side.get(k)
        if side not in pieces:
            side = max(pieces, key=lambda n: (pieces[n].w * pieces[n].h, pieces[n].values()))
            self.cut_side[k] = side
        return pieces[side]

    def _slot(self, k, T, s):
        """Where k would sit if it swapped into the dragged window's starting place, or None."""
        h, st, g = self.home(k), self.start, self.gap
        candidates = [Rect(st.x, st.y, h.w, h.h), Rect(st.right - h.w, st.y, h.w, h.h),
                      Rect(st.x, st.bottom - h.h, h.w, h.h)]
        if st.w >= h.w * SQUASH and st.h >= h.h * SQUASH:
            candidates.append(Rect(st.x, st.y, min(st.w, h.w), min(st.h, h.h)))
        w = s.windows[k]
        others = [v.rect for o, v in s.windows.items() if o not in (k, self.key) and v.rect and not v.minimised]
        for q in candidates:
            if q.w < w.minimum[0] or q.h < w.minimum[1] or not s.bounds.contains(q) or q.near(T, g):
                continue
            if any(q.near(o, g) for o in others + list(s.obstacles)):
                continue
            return q
        return None

    # -- the layout the ghosts aim for
    def _target(self, T):
        """The dragged rect clamped on screen and pulled out of walls (they never give way)."""
        b = self.base.bounds
        q = clamp_into(T, b, self.minimum(), self.moving if self.kind == 'resize' else EDGES)
        if self.kind == 'resize':
            return self._clip(q, self.walls())
        for _ in range(4):
            for wall in self.walls():
                q = pull_out(q, wall, self.gap, b)
        return clamp_into(q, b, self.minimum())

    def _clip(self, q, blockers):
        """Resize: stop moving edges at blockers (the gap before them); never below minimum, never past start."""
        s, g, mw, mh = self.start, self.gap, *self.minimum()
        for b in blockers:
            if not q.near(b, g):
                continue
            options = []
            if 'right' in self.moving and b.x >= s.right:
                options.append((q.right - (b.x - g), with_edges(q, right=max(b.x - g, q.x + mw, s.right))))
            if 'left' in self.moving and b.right <= s.x:
                options.append((b.right + g - q.x, with_edges(q, left=min(b.right + g, q.right - mw, s.x))))
            if 'bottom' in self.moving and b.y >= s.bottom:
                options.append((q.bottom - (b.y - g), with_edges(q, bottom=max(b.y - g, q.y + mh, s.bottom))))
            if 'top' in self.moving and b.bottom <= s.y:
                options.append((b.bottom + g - q.y, with_edges(q, top=min(b.bottom + g, q.bottom - mh, s.y))))
            if options:
                q = min(options, key=lambda o: (o[0], o[1].values()))[1]
        return q

    def _layout(self, T, held):
        """State with the dragged window at T and neighbours where they go: swaps, slides, shrinks, pushes."""
        s = copy_state(self.base)
        key = self.key
        if self.kind == 'resize':
            self.floored = set()
            for k in self.neighbours():
                if not self.movable(k) or k in held:
                    continue
                t = self.tr(k)
                if k in self.bonds or (k in self.contacts and t['yielded'] and not t['pushed']):
                    q, hit = self._shrunk(k, T, grow=k in self.bonds)
                    s.windows[k].rect = q
                    if hit and q.near(T, self.gap):
                        self.floored.add(k)
            stuck = {k for k in self.floored if not self.tr(k)['pushed']}
            T = self._clip(T, [s.windows[k].rect for k in sorted(stuck)])
            held = set(held) | stuck
            for k in stuck:
                s.windows[k].rect = self._shrunk(k, T)[0]
        else:
            for k in sorted(self.contacts):
                t = self.tr(k)
                keep = k in self.swaps and centre_in(T, self.home(k)) and t['yielded']
                if not keep:
                    self.swaps.pop(k, None)
                if self.movable(k) and t['yielded'] and centre_in(T, self.home(k)) and k not in self.swaps:
                    slot = self._slot(k, T, s)
                    if slot:
                        self.swaps[k] = slot
            for k in list(self.swaps):
                if k not in self.contacts:
                    del self.swaps[k]
            for k, slot in self.swaps.items():
                s.windows[k].rect = slot
            held = set(held) - set(self.swaps)
        if not any(T.near(v.rect, self.gap) for o, v in s.windows.items()
                   if o != key and v.rect and not v.minimised and o not in held):
            s.windows[key].rect = T
            return s
        held = frozenset(held)
        # A bounded search (a frame is 16 ms). The release uses the very same search, so it lands exactly where the
        # ghosts showed: a bigger search at release found different layouts in 2 of 300 seeded drags.
        budget = max(40, 4 * len(s.windows))
        solved = push(s, key, T, held=held, budget=budget)     # 1. slide aside, keeping every size
        if solved is None and self.kind != 'resize':
            cut = copy_state(s)                                # 2. the covered neighbours shrink their facing side
            for k in sorted(self.contacts):
                if k in held or k in self.swaps or not cut.windows[k].rect.near(T, self.gap):
                    continue
                q = self._cut(k, T)
                if q is None:
                    cut = None
                    break
                cut.windows[k].rect = q
            if cut is not None:
                solved = push(cut, key, T, held=held, budget=budget)
        if solved is None:
            solved = push(s, key, T, True, held=held, budget=budget)   # 3. shrink, never under 60 % (SQUASH)
        if solved is None:
            # 4. Minimise what the hand is covering (least recently used first) rather than squash it into a strip.
            trial = copy_state(s)
            covered = sorted((k for k in self.neighbours() if self.movable(k) and k not in held
                              and trial.windows[k].rect.near(T, self.gap)),
                             key=lambda k: (trial.windows[k].last_used, k))
            for k in covered:
                trial.windows[k].minimised = True
                solved = push(trial, key, T, held=held, budget=budget)
                if solved is not None:
                    break
            if solved is None and covered:
                solved = push(trial, key, T, True, held=held, budget=budget)
        if solved is None:
            s.windows[key].rect = T
            return s
        return solved

    def _landing(self, T, held, layout):
        """Where the dragged window lands, given everything as the ghosts show it: a move goes to the nearest free
        spot (out of whatever is still resisting: that is the resistance), a resize to the furthest legal point
        along the path from where it started. Then it snaps, never into an overlap."""
        if not self.broken:
            return self.start
        b, g = self.base.bounds, self.gap
        q = self._target(T)
        blockers = [v.rect for o, v in sorted(layout.windows.items())
                    if o != self.key and v.rect and not v.minimised] + list(self.base.obstacles)
        def legal(r):
            return b.contains(r) and not any(r.near(o, g) for o in blockers)
        if self.kind == 'resize':
            q = self._clip(q, [self.home(k) for k in sorted(held)] +
                           [layout.windows[k].rect for k in sorted(self.floored)])
            if not legal(q):
                q = self._walk(q, legal)
        elif not legal(q):
            q = nearest_free(q, blockers, b, g) or (self.start if legal(self.start) else q)
        moving = self.moving if self.kind == 'resize' else EDGES
        return snap(q, blockers, b, g, self.feel.px(self.feel.snap_px), moving, move=self.kind != 'resize',
                    minimum=self.minimum())

    def _walk(self, q, legal):
        """The furthest rectangle on the straight path from start to q that is legal (start itself if none)."""
        low, high, best = 0, 1024, self.start
        for _ in range(11):
            mid = (low + high + 1) // 2
            r = Rect(*(a + (z - a) * mid // 1024 for a, z in zip(self.start.values(), q.values())))
            if legal(r):
                low, best = mid, r
            else:
                high = mid - 1
        return best

    # -- per tick
    def step(self, rect, t, pointer=None):
        T = Rect(*rect) if not isinstance(rect, Rect) else rect
        dt = max(0, t - self.t)
        self.t = t
        if T != self.T:
            self.last_move = t
        self.T = T
        self.samples = [(ts, r) for ts, r in self.samples if t - ts <= 120] + [(t, T)]
        self._classify(T)
        if self.kind == 'move':
            return self._move_step(T, t, pointer)
        if not self.broken:
            self.contacts = {}
            for k in list(self.shown):
                self._aim(k, self.home(k), t)
            self.landing = self.start
            self.frame = Frame(self._ghosts(t), self.start, 'still')
            return self.frame
        target = self._target(T)
        g = self.gap
        self.contacts = {k: hit for k in self.neighbours() if self.movable(k)
                         for hit in [penetration(target, self.home(k), g)] if hit}
        slow = self._speed() < self.feel.px(self.feel.fling_px_s)
        for k in self.neighbours():
            t_ = self.tr(k)
            if k in self.bonds:
                t_['yielded'] = True
            if k in self.contacts:
                if slow:
                    t_['held'] += dt
                if t_['held'] >= self.feel.dwell_ms:
                    t_['yielded'] = True
                if k in self.floored and slow:
                    t_['floor'] += dt
                    if t_['floor'] >= self.feel.dwell_ms:
                        t_['pushed'] = True
            elif k not in self.bonds:
                t_['held'] = 0
                t_['floor'] = 0
                t_['pushed'] = False
        held = {k for k in self.contacts if not self.tr(k)['yielded']}
        layout = self._layout(target, held)
        self.landing = self._landing(T, held, layout)
        if held and not self._fits(layout, self.landing):
            # Nowhere free for it at its size (live seed: a yielded neighbour had taken its starting slot): the windows
            # it covers give way now, in this tick, so the ghosts show it, rather than leaving it overlapping them.
            held = set()
            layout = self._layout(target, held)
            self.landing = self._landing(T, held, layout)
        self.plan = (layout, self.landing)       # release settles to exactly this
        for k in self.neighbours():
            w = layout.windows.get(k)
            want = None if (w is None or w.minimised) else w.rect
            self._aim(k, want, t)
        self.frame = Frame(self._ghosts(t), self.landing, self.kind, sorted(held),
                           sorted(k for k in self.contacts if self.tr(k)['yielded']),
                           sorted(k for k in self.neighbours() if self.shown.get(k, 1) is None))
        return self.frame

    def _move_step(self, T, t, pointer=None):
        # Every decision uses pickup geometry. Animated neighbours cannot
        # change their own threshold or cause an oscillating swap.
        eligible = {k for k in self.neighbours() if self.movable(k)
                    and crossed_centre(self.start, T, self.home(k))}
        self.contacts = {k: penetration(T, self.home(k), self.gap)
                         for k in eligible if T.near(self.home(k), self.gap)}
        held = set(self.neighbours()) - eligible
        for k in self.neighbours():
            self.tr(k)['yielded'] = k in eligible
        target = self._target(T)
        layout = self._layout(target, held) if self.broken else copy_state(self.base)
        blockers = [w.rect for k, w in layout.windows.items()
                    if k != self.key and w.rect and not w.minimised] + list(layout.obstacles)
        spaces = drop_spaces(layout.bounds, blockers, self.gap, self.minimum())
        landing = choose_space(T, spaces, layout.bounds, pointer) if self.broken else self.start
        if T == self.start:
            layout = copy_state(self.base)
            landing = self.start
        elif self.base.windows[self.key].pinned:
            landing = self._landing(T, held, layout)
        elif self.swaps:
            # Swapping occupies that tile, rather than unexpectedly growing
            # across unrelated vacant space beside it.
            slots = [self.home(k) for k in self.swaps
                     if not any(self.home(k).near(q, self.gap) for q in blockers)]
            landing = choose_space(T, slots, layout.bounds, pointer) or landing
        landing = landing or self._landing(T, held, layout)
        if not self._fits(layout, landing) or any(layout.windows[k].minimised for k in self.neighbours()):
            # Do not solve an impossible hover by moving an uncrossed neighbour.
            # Nor make a crossed window disappear instead of sliding.
            layout = copy_state(self.base)
            blockers = [self.home(k) for k in self.neighbours()] + list(layout.obstacles)
            spaces = drop_spaces(layout.bounds, blockers, self.gap, self.minimum())
            landing = choose_space(T, spaces, layout.bounds, pointer) or self.start
        self.plan = (layout, landing)
        self.landing = landing
        for k in self.neighbours():
            w = layout.windows[k]
            self._aim(k, None if w.minimised else w.rect, t)
        self.frame = Frame(self._ghosts(t), landing, self.kind,
                           sorted(held), sorted(eligible), [], spaces)
        return self.frame

    def _fits(self, layout, landing):
        trial = copy_state(layout)
        trial.windows[self.key].rect = landing
        return valid(trial)

    def _aim(self, k, want, t):
        """Point k's ghost at want, with the settle-back delay and easing."""
        home = self.home(k)
        shown = self.shown.get(k, home)
        t_ = self.tr(k)
        if want == home and shown != home and k not in self.contacts and self.broken:
            if t_['away'] is None:
                t_['away'] = t
            if t - t_['away'] < self.feel.return_ms:
                want = shown
            else:
                t_['away'] = None
                t_['yielded'] = k in self.bonds
        elif want != home:
            t_['away'] = None
        if want == shown:
            return
        now = self.current(k, t)
        settled = k in self.anim and (self.anim[k][0] is None or t - self.anim[k][2] >= self.feel.motion_ms)
        follow = (self.kind == 'resize' and now is not None and want is not None and settled
                  and max(abs(a - b) for a, b in zip(now.values(), want.values())) <= self.feel.px(self.feel.follow_px))
        if k in self.bonds and self.kind == 'resize':
            follow = True              # a shared edge moves with the hand, no easing
        self.anim[k] = (None if follow else now, want, t)
        self.shown[k] = want

    def _ghosts(self, t):
        out = {}
        for k in sorted(self.shown):
            r = self.current(k, t)
            if r is not None and r != self.home(k):
                out[k] = r
        return out

    # -- mouse-up
    def release(self, rect, t, pointer=None):
        """Settle to exactly what the ghosts were showing: neighbours that gave way go where their ghosts were,
        neighbours still resisting stay, and the dragged window lands on its outline (pushed back out of what
        resisted, snapped). Then the engine's full solver (shrink to 60 %, minimise least recently used, clamp)
        guarantees the no-overlap invariant."""
        frame = self.step(rect, t, pointer)
        key = self.key
        if not self.broken:
            result = solve(self.base, {'type': 'noop'})
            result.notes.append('inside the dead zone: put back')
            return result
        layout, landing = self.plan                # computed in the release tick itself: what the ghosts showed
        final = copy_state(layout)                 # the dragged window on its outline
        final.windows[key].rect = landing
        if not valid(final):                       # rare: the outline could not be made legal; settle around it
            final = self._layout(landing, set())
            final.windows[key].rect = landing
        pinned = final.windows[key].pinned
        final.windows[key].pinned = False
        kind = 'resize-end' if self.kind == 'resize' else 'drag-end'
        result = solve(final, {'type': kind, 'key': key, 'rect': landing.values()})
        w = result.state.windows[key]
        if pinned:
            w.pinned = True
            w.home = w.rect
        result.state.gesture = None
        if not valid(result.state):
            result.notes.append('released into infeasible fixed geometry')
        self.landing = w.rect if not w.minimised else landing
        self.frame = frame
        return result
