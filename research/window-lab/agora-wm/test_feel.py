"""The feel of drags and resizes, from scenes on Alex's real screen: 3840x2160 at 150 %, bars taking the top
57 px, theme gaps 12 inner / 14 outer (theme-native.json, 26 Oct). Time advances 16 ms per tick (60 Hz)."""
import statistics
import time
import unittest
from engine import State, Window, Rect, solve, valid
from feel import Feel, Gesture, from_settings, ease, snap

WORK = Rect(0, 57, 3840, 1977)          # ran: SPI_GETWORKAREA on Alex's desktop, 26 Oct
FEEL = Feel(scale=1.5)                   # ran: 144 dpi
SEEDS = int(__import__("os").environ.get("FEEL_SEEDS", 300))
GAP = 12


def desk(**boxes):
    s = State(work=WORK, gap_inner=GAP, gap_outer=14)
    for i, (k, b) in enumerate(boxes.items()):
        pinned = k.endswith('_pin')
        s.windows[k] = Window(k, preferred=b[2:], rect=Rect(*b), last_used=i, pinned=pinned,
                              home=Rect(*b) if pinned else None)
    assert valid(s), 'scene must start legal'
    return s


def glide(g, frm, to, t, ms, size=None):
    """Move the dragged rect from frm to to over ms, one tick per 16 ms; returns (t, frames)."""
    frm, to = (r if isinstance(r, Rect) else Rect(*r) for r in (frm, to))
    steps = max(1, ms // 16)
    frames = []
    for i in range(1, steps + 1):
        e = i / steps
        r = Rect(*(round(a + (b - a) * e) for a, b in zip(frm.values(), to.values())))
        t += 16
        frames.append(g.step(r, t))
    return t, frames


def hold(g, at, t, ms):
    frames = []
    for _ in range(max(1, ms // 16)):
        t += 16
        frames.append(g.step(at if isinstance(at, Rect) else Rect(*at), t))
    return t, frames


# Browser and chat snapped side by side across the top; notes below the browser. Bounds: x 14..3826, y 71..2020.
BROWSER = (14, 71, 2200, 1300)
CHAT = (2226, 71, 1600, 1300)
NOTES = (14, 1383, 1000, 637)


class DragFeel(unittest.TestCase):
    def test_hover_then_back_away_moves_nothing(self):
        s = desk(browser=BROWSER, chat=CHAT, notes=NOTES)
        g = Gesture(s, 'notes', NOTES, 0, FEEL)
        over = (300, 900, 1000, 637)                       # well inside the browser
        t, frames = glide(g, NOTES, over, 0, 400)
        t, more = hold(g, over, t, 200)                    # rests 200 ms: less than the 350 ms dwell
        t, back = glide(g, over, NOTES, t, 300)
        for f in frames + more + back:
            self.assertEqual(f.ghosts, {}, 'nothing may shuffle before the dwell')
        r = g.release(NOTES, t)
        self.assertEqual(r.placements['browser'], Rect(*BROWSER))
        self.assertEqual(r.placements['chat'], Rect(*CHAT))
        self.assertEqual(r.placements['notes'], Rect(*NOTES))

    def test_dwell_then_yield_eases_and_settles_back(self):
        s = desk(browser=BROWSER, chat=CHAT, notes=NOTES)
        g = Gesture(s, 'notes', NOTES, 0, FEEL)
        edge = (14, 1200, 1000, 637)                       # 183 px into the browser's bottom
        t, approach = glide(g, NOTES, edge, 0, 300)
        t, frames = hold(g, edge, t, 800)
        timeline = approach + frames
        touched = next(i for i, f in enumerate(timeline) if 'browser' in f.held)
        gave = next(i for i, f in enumerate(timeline) if 'browser' in f.ghosts)
        self.assertGreaterEqual((gave - touched) * 16, FEEL.dwell_ms, 'rests a full dwell before giving way')
        self.assertLessEqual((gave - touched) * 16, FEEL.dwell_ms + 32)
        moved = [i for i, f in enumerate(frames) if 'browser' in f.ghosts]
        # eased: distance to the final ghost shrinks every frame and is reached within motion_ms
        final = frames[-1].ghosts['browser']
        gaps = [sum(abs(a - b) for a, b in zip(f.ghosts['browser'].values(), final.values())) for f in frames[moved[0]:]]
        self.assertEqual(gaps, sorted(gaps, reverse=True))
        arrive = next(i for i, d in enumerate(gaps) if d == 0)
        self.assertLessEqual(arrive * 16, FEEL.motion_ms + 16)
        self.assertGreater(gaps[0], 0, 'first yielded frame is mid-flight, not a jump')
        # leave: the browser waits return_ms, then eases home
        t, away = glide(g, edge, NOTES, t, 64)
        t, after = hold(g, NOTES, t, 700)
        timeline = away + after
        still_away = [i for i, f in enumerate(timeline) if 'browser' in f.ghosts]
        self.assertTrue(still_away and still_away[0] == 0)
        self.assertEqual(timeline[-1].ghosts, {})
        r = g.release(NOTES, t)
        self.assertEqual(r.placements['browser'], Rect(*BROWSER))

    def test_fast_sweep_across_two_windows_moves_neither(self):
        s = desk(browser=BROWSER, chat=CHAT, notes=NOTES)
        g = Gesture(s, 'notes', NOTES, 0, FEEL)
        t, a = glide(g, NOTES, (600, 400, 1000, 637), 0, 250)          # up through the browser...
        t, b = glide(g, (600, 400, 1000, 637), (2700, 400, 1000, 637), t, 500)   # ...across into the chat...
        t, c = glide(g, (2700, 400, 1000, 637), (2700, 1383, 1000, 637), t, 250)  # ...down into free space
        self.assertTrue(all(f.ghosts == {} for f in a + b + c), 'a sweep in transit never shuffles windows')
        r = g.release((2700, 1383, 1000, 637), t)
        self.assertEqual(r.placements['browser'], Rect(*BROWSER))
        self.assertEqual(r.placements['chat'], Rect(*CHAT))
        self.assertTrue(valid(r.state))

    def test_slow_drag_across_both_shuffles_and_ends_legal(self):
        s = desk(browser=BROWSER, chat=CHAT, notes=NOTES)
        g = Gesture(s, 'notes', NOTES, 0, FEEL)
        t, a = glide(g, NOTES, (600, 700, 1000, 637), 0, 1500)
        t, b = glide(g, (600, 700, 1000, 637), (2600, 700, 1000, 637), t, 4000)
        self.assertTrue(any(f.ghosts for f in a + b), 'a slow drag that rests gets room')
        r = g.release((2600, 700, 1000, 637), t)
        self.assertTrue(valid(r.state), r.notes)

    def test_a_neighbour_that_cannot_slide_shrinks_its_own_side_not_a_third_window(self):
        # Found in the hidden-desktop proof: the browser slid right and squeezed the chat from 1992 px to 776 px.
        s = desk(browser=BROWSER, chat=CHAT, notes=NOTES)
        g = Gesture(s, 'notes', NOTES, 0, FEEL)
        into = (300, 1100, 1000, 637)
        t, _ = glide(g, NOTES, into, 0, 300)
        t, _ = hold(g, into, t, 700)
        r = g.release(into, t)
        self.assertEqual(r.placements['chat'], Rect(*CHAT), 'the chat is not part of this')
        b = r.placements['browser']
        self.assertEqual((b.x, b.y, b.w), BROWSER[:3])
        self.assertEqual(b.bottom, 1100 - GAP, 'the browser\'s bottom edge gave way')
        self.assertTrue(valid(r.state))

    def test_shallow_drop_pushes_the_dragged_window_back_and_snaps(self):
        s = desk(browser=BROWSER, chat=CHAT, notes=(1500, 1500, 1000, 500))
        g = Gesture(s, 'notes', (1500, 1500, 1000, 500), 0, FEEL)
        drop = (1180, 1340, 1000, 500)                     # 43 px into the browser's bottom, quickly
        t, _ = glide(g, (1500, 1500, 1000, 500), drop, 0, 150)
        r = g.release(drop, t + 16)
        self.assertEqual(r.placements['browser'], Rect(*BROWSER), 'a nudge does not move the neighbour')
        n = r.placements['notes']
        self.assertEqual(n.y, BROWSER[1] + BROWSER[3] + GAP, 'pushed back to exactly the gap')
        self.assertTrue(valid(r.state))

    def test_quick_drop_onto_a_window_lands_on_its_outline_not_on_the_window(self):
        # What you see is what you get: no time to dwell, so the chat never gave way and the outline showed the
        # notes pushed back out of it. The release does exactly that.
        s = desk(browser=BROWSER, chat=CHAT, notes=NOTES)
        g = Gesture(s, 'notes', NOTES, 0, FEEL)
        drop = (2500, 300, 1000, 637)                      # centre inside the chat
        t, frames = glide(g, NOTES, drop, 0, 160)
        r = g.release(drop, t + 16)
        self.assertTrue(valid(r.state), r.notes)
        self.assertEqual(r.placements['chat'], Rect(*CHAT))
        self.assertEqual(r.placements['notes'], frames[-1].landing)

    def test_swap_two_equal_tiles(self):
        a, b = (14, 71, 1200, 900), (1226, 71, 1200, 900)
        s = desk(a=a, b=b)
        g = Gesture(s, 'a', a, 0, FEEL)
        over = (1236, 80, 1200, 900)                       # A over B, 10 px off B's place
        t, _ = glide(g, a, over, 0, 300)
        t, frames = hold(g, over, t, 700)
        self.assertEqual(frames[-1].ghosts.get('b'), Rect(*a), 'B shows it will take A\'s place')
        r = g.release(over, t)
        self.assertEqual(r.placements['b'], Rect(*a))
        self.assertEqual(r.placements['a'], Rect(*b), 'A lands snapped into B\'s old place')

    def test_dead_zone_puts_it_back(self):
        s = desk(browser=BROWSER, chat=CHAT, notes=NOTES)
        g = Gesture(s, 'notes', NOTES, 0, FEEL)
        wobble = (NOTES[0] + 9, NOTES[1] - 5, NOTES[2], NOTES[3])      # 9 px < 15 px dead zone at 150 %
        t, frames = glide(g, NOTES, wobble, 0, 100)
        self.assertTrue(all(f.landing == Rect(*NOTES) for f in frames))
        self.assertEqual(g.release(wobble, t).placements['notes'], Rect(*NOTES))

    def test_snap_together_at_the_gap_and_escape_past_the_radius(self):
        s = desk(browser=(14, 71, 1800, 1300), spotify=(2400, 400, 900, 700))
        start = (2400, 400, 900, 700)
        near = (14 + 1800 + GAP + 20, 380, 900, 700)        # 20 px from snapping (radius 24 at 150 %)
        g = Gesture(s, 'spotify', start, 0, FEEL)
        t, _ = glide(g, start, near, 0, 300)
        r = g.release(near, t)
        self.assertEqual(r.placements['spotify'].x, 14 + 1800 + GAP)
        far = (14 + 1800 + GAP + 40, 380, 900, 700)
        g = Gesture(s, 'spotify', start, 0, FEEL)
        t, _ = glide(g, start, far, 0, 300)
        self.assertEqual(g.release(far, t).placements['spotify'].x, far[0], 'past the radius: free placement')

    def test_screen_edge_snap_and_rubber_band(self):
        s = desk(spotify=(2400, 400, 900, 700))
        g = Gesture(s, 'spotify', (2400, 400, 900, 700), 0, FEEL)
        out = (3100, 60, 900, 700)                          # partly off the right and top
        t, frames = glide(g, (2400, 400, 900, 700), out, 0, 300)
        self.assertEqual(frames[-1].landing, Rect(3826 - 900, 71, 900, 700), 'held at the outer gap')
        self.assertEqual(g.release(out, t).placements['spotify'], Rect(3826 - 900, 71, 900, 700))

    def test_pin_is_a_wall(self):
        s = desk(browser=(14, 71, 1800, 1300), spotify_pin=(2600, 71, 1226, 1300))
        g = Gesture(s, 'browser', (14, 71, 1800, 1300), 0, FEEL)
        into = (1200, 71, 1800, 1300)
        t, _ = glide(g, (14, 71, 1800, 1300), into, 0, 300)
        t, frames = hold(g, into, t, 800)
        self.assertNotIn('spotify_pin', frames[-1].ghosts)
        r = g.release(into, t)
        self.assertEqual(r.placements['spotify_pin'], Rect(2600, 71, 1226, 1300))
        self.assertEqual(r.placements['browser'].right, 2600 - GAP)

    def test_drag_your_own_pin_moves_its_home(self):
        s = desk(note_pin=(14, 71, 800, 600))
        g = Gesture(s, 'note_pin', (14, 71, 800, 600), 0, FEEL)
        t, _ = glide(g, (14, 71, 800, 600), (1000, 500, 800, 600), 0, 300)
        r = g.release((1000, 500, 800, 600), t)
        w = r.state.windows['note_pin']
        self.assertTrue(w.pinned)
        self.assertEqual(w.home, Rect(1000, 500, 800, 600))


class ResizeFeel(unittest.TestCase):
    def test_shared_edge_moves_both(self):
        s = desk(browser=BROWSER, chat=CHAT)
        g = Gesture(s, 'browser', BROWSER, 0, FEEL)
        wider = (14, 71, 2500, 1300)
        t, frames = glide(g, BROWSER, wider, 0, 300)
        self.assertEqual(frames[-1].ghosts['chat'].x, 14 + 2500 + GAP, 'the chat recedes with the edge, no dwell')
        r = g.release(wider, t)
        self.assertEqual(r.placements['chat'], Rect(14 + 2500 + GAP, 71, 3826 - (14 + 2500 + GAP), 1300))
        g = Gesture(r.state, 'browser', r.placements['browser'], 0, FEEL)
        narrower = (14, 71, 1700, 1300)
        t, _ = glide(g, r.placements['browser'], narrower, 0, 300)
        r = g.release(narrower, t)
        self.assertEqual(r.placements['chat'].x, 14 + 1700 + GAP, 'shrinking away: the chat follows')
        self.assertEqual(r.placements['chat'].right, 3826)

    def test_free_edges_do_not_follow(self):
        s = desk(browser=BROWSER, chat=CHAT)
        g = Gesture(s, 'browser', BROWSER, 0, Feel(scale=1.5, edges='free'))
        narrower = (14, 71, 1700, 1300)
        t, _ = glide(g, BROWSER, narrower, 0, 300)
        self.assertEqual(g.release(narrower, t).placements['chat'], Rect(*CHAT))

    def test_resize_into_a_loose_neighbour_resists_then_it_shrinks_to_its_floor(self):
        chat = (2400, 71, 1426, 1300)                       # 174 px of free space between them: not bonded
        s = desk(browser=BROWSER, chat=chat)
        g = Gesture(s, 'browser', BROWSER, 0, FEEL)
        into = (14, 71, 2600, 1300)                          # 212 px into the chat
        t, _ = glide(g, BROWSER, into, 0, 150)
        quick = g.frame.landing
        self.assertEqual(quick.right, 2400 - GAP, 'before the dwell the edge stops at the gap')
        t, frames = hold(g, into, t, 900)
        chat_ghost = frames[-1].ghosts['chat']
        self.assertEqual(chat_ghost.x, 14 + 2600 + GAP, 'after the dwell the chat gives way by shrinking')
        self.assertEqual(chat_ghost.right, chat[0] + chat[2], 'shrinks, not shoved')
        deep = (14, 71, 3500, 1300)                          # past the chat's 60 % floor
        t, frames = glide(g, into, deep, t, 200)
        floor = int(1426 * 0.6)
        self.assertEqual(frames[-1].ghosts['chat'].w, floor)
        self.assertEqual(frames[-1].landing.right, 3826 - floor - GAP, 'the edge stops at the floor')
        r = g.release(frames[-1].landing.values(), t + 16)
        self.assertTrue(valid(r.state))
        self.assertEqual(r.placements['chat'].w, floor)

    def test_all_eight_handles(self):
        mid = (1000, 600, 1200, 800)
        for name, box in {'left': (900, 600, 1300, 800), 'right': (1000, 600, 1300, 800),
                          'top': (1000, 500, 1200, 900), 'bottom': (1000, 600, 1200, 900),
                          'top-left': (900, 500, 1300, 900), 'top-right': (1000, 500, 1300, 900),
                          'bottom-left': (900, 600, 1300, 900), 'bottom-right': (1000, 600, 1300, 900)}.items():
            s = desk(w=mid)
            g = Gesture(s, 'w', mid, 0, FEEL)
            t, _ = glide(g, mid, box, 0, 200)
            self.assertEqual(g.kind, 'resize', name)
            r = g.release(box, t)
            self.assertEqual(r.placements['w'], Rect(*box), name)

    def test_rubber_band_at_minimum(self):
        s = desk(w=(1000, 600, 1200, 800))
        s.windows['w'].minimum = (700, 500)
        g = Gesture(s, 'w', (1000, 600, 1200, 800), 0, FEEL)
        tiny = (1800, 600, 400, 800)                        # left edge dragged far right
        t, frames = glide(g, (1000, 600, 1200, 800), tiny, 0, 200)
        self.assertEqual(frames[-1].landing, Rect(2200 - 700, 600, 700, 800))
        self.assertEqual(g.release(tiny, t).placements['w'], Rect(1500, 600, 700, 800))


class PinFeel(unittest.TestCase):
    def test_a_pin_is_not_narrowed_while_the_new_window_fits_at_sixty_percent(self):
        # Order (WM.md "Opening: fill first"): free space at 60 %+, then minimise the oldest, then narrow pins.
        s = desk(browser=(14, 71, 2500, 1949), spotify_pin=(2826, 71, 1000, 1949))
        r = solve(s, {'type': 'open', 'key': 'editor', 'window': {'preferred': (3100, 1800)}})
        self.assertTrue(valid(r.state))
        self.assertEqual(r.minimise, ['browser'], 'the oldest goes first')
        self.assertEqual(r.placements['spotify_pin'], Rect(2826, 71, 1000, 1949), 'the pin keeps its width')
        self.assertGreaterEqual(r.placements['editor'].w, int(3100 * 0.6))

    def test_a_wide_pin_is_narrowed_when_something_big_opens_then_grows_back(self):
        # Spotify pinned 2100 wide: with the browser minimised, 1700 px are left, under 60 % of the editor's 3100.
        s = desk(browser=(14, 71, 1700, 1949), spotify_pin=(1726, 71, 2100, 1949))
        r = solve(s, {'type': 'open', 'key': 'editor', 'window': {'preferred': (3100, 1800)}})
        self.assertTrue(valid(r.state))
        self.assertIn('browser', r.minimise, 'the oldest goes first')
        self.assertNotIn('spotify_pin', r.minimise)
        pin = r.placements['spotify_pin']
        self.assertEqual(pin.right, 3826, 'keeps its screen-side edge')
        self.assertLess(pin.w, 2100)
        self.assertGreaterEqual(pin.w, 1050, 'never under pin_min of its pinned width')
        self.assertGreater(pin.w, 1050, 'narrowed only as far as needed')
        self.assertGreaterEqual(r.placements['editor'].w, int(3100 * 0.6))
        back = solve(r.state, {'type': 'close', 'key': 'editor'})
        self.assertEqual(back.placements['spotify_pin'], Rect(1726, 71, 2100, 1949), 'grows back to its pinned width')

    def test_pin_stays_on_screen_when_the_work_area_shrinks(self):
        s = desk(spotify_pin=(2826, 71, 1000, 1949))
        r = solve(s, {'type': 'work-area', 'rect': [0, 57, 3400, 1977]})
        self.assertNotIn('spotify_pin', r.minimise)
        self.assertTrue(r.state.bounds.contains(r.placements['spotify_pin']))


class Mechanics(unittest.TestCase):
    def test_settings_validate(self):
        f = from_settings({'dwell_ms': '200', 'snap_px': 20, 'pin_min': '0.4', 'edges': 'free'}, 1.5)
        self.assertEqual((f.dwell_ms, f.snap_px, f.pin_min, f.edges, f.px(f.snap_px)), (200, 20, 0.4, 'free', 30))
        for bad in ({'dwell_ms': 5000}, {'snap_px': 'lots'}, {'pin_min': 0.05}, {'edges': 'glue'}, {'motion_ms': True}):
            with self.assertRaises(ValueError):
                from_settings(bad)

    def test_easing_is_material_standard_and_monotone(self):
        values = [ease(i / 20) for i in range(21)]
        self.assertEqual(values, sorted(values))
        self.assertEqual((values[0], values[-1]), (0.0, 1.0))
        self.assertGreater(values[5], 0.5, 'decelerating: most of the travel early')

    def test_snap_never_into_an_overlap(self):
        r = snap(Rect(100, 100, 400, 300), [Rect(512, 120, 300, 300), Rect(0, 405, 800, 300)],
                 Rect(0, 0, 2000, 2000), 12, 24)
        self.assertFalse(r.near(Rect(0, 405, 800, 300), 12))

    def test_release_is_what_the_ghosts_showed(self):
        """Seeded scenes of 3-8 windows; drags and resizes with random rests. At release every neighbour ends where
        its ghost was aiming, the dragged window on its outline, and the layout is legal."""
        import random
        mismatches = []
        for seed in range(SEEDS):
            rng = random.Random(seed)
            s = State(work=WORK, gap_inner=GAP, gap_outer=14)
            for i in range(rng.randint(3, 8)):
                s = solve(s, {'type': 'open', 'key': f'w{i}',
                              'window': {'preferred': (rng.randint(500, 1800), rng.randint(400, 1300))}}).state
            keys = [k for k, w in s.windows.items() if not w.minimised]
            key = rng.choice(keys); start = s.windows[key].rect
            g = Gesture(s, key, start, 0, FEEL); t = 0; r = start
            # Windows' modal loop is either a move or a size from one handle, never both: so is this.
            handle = rng.choice([None, None, ('right',), ('left',), ('bottom',), ('top',), ('right', 'bottom'),
                                 ('left', 'top'), ('right', 'top'), ('left', 'bottom')])
            for _ in range(rng.randint(1, 4)):
                if handle:
                    e = {'left': r.x, 'right': r.right, 'top': r.y, 'bottom': r.bottom}
                    for side in handle:
                        e[side] += rng.randint(-700, 900) * (1 if side in ('right', 'bottom') else -1)
                    # Windows' sizing loop never inverts a window or takes it under its minimum track size.
                    if 'left' in handle:e['left'] = min(e['left'], e['right'] - 160)
                    if 'right' in handle:e['right'] = max(e['right'], e['left'] + 160)
                    if 'top' in handle:e['top'] = min(e['top'], e['bottom'] - 100)
                    if 'bottom' in handle:e['bottom'] = max(e['bottom'], e['top'] + 100)
                    to = Rect(e['left'], e['top'], e['right'] - e['left'], e['bottom'] - e['top'])
                else:
                    to = Rect(r.x + rng.randint(-1500, 1500), r.y + rng.randint(-800, 800), r.w, r.h)
                t, _ = glide(g, r, to, t, rng.choice([96, 300, 900]))
                t, _ = hold(g, to, t, rng.choice([0, 100, 500]))
                r = to
            t, _ = hold(g, r, t, 300)                         # let every animation finish
            result = g.release(r, t + 16)
            # What the ghosts were aiming at in the release tick itself (a dwell may complete in that very tick).
            # A neighbour in its 250 ms settle-back delay goes home at release (nothing needs it moved): excluded.
            shown = {k: g.shown.get(k, g.home(k)) for k in g.neighbours() if g.tr(k)['away'] is None}
            landing = g.frame.landing
            self.assertTrue(valid(result.state), (seed, result.notes))
            got = {k: result.placements.get(k) for k in shown}
            if got != shown or result.placements.get(key) != landing:
                mismatches.append(seed)
        print(f'feel WYSIWYG: {SEEDS - len(mismatches)}/{SEEDS} releases matched the ghosts; differing seeds {mismatches[:12]}')
        self.assertEqual(mismatches, [])

    def test_deterministic_replay(self):
        def run():
            s = desk(browser=BROWSER, chat=CHAT, notes=NOTES)
            g = Gesture(s, 'notes', NOTES, 0, FEEL)
            t, a = glide(g, NOTES, (300, 1000, 1000, 637), 0, 300)
            t, b = hold(g, (300, 1000, 1000, 637), t, 600)
            r = g.release((300, 1000, 1000, 637), t)
            return [(f.ghosts, f.landing) for f in a + b], r.placements
        self.assertEqual(run(), run())

    def test_frame_cost_twenty_windows(self):
        s = State(work=WORK, gap_inner=GAP, gap_outer=14)
        for i in range(20):                                 # 5 x 4 grid of 740x470 tiles
            x, y = 14 + (i % 5) * 764, 71 + (i // 5) * 488
            s.windows[f'w{i}'] = Window(f'w{i}', preferred=(740, 470), rect=Rect(x, y, 740, 470), last_used=i)
        self.assertTrue(valid(s))
        g = Gesture(s, 'w0', s.windows['w0'].rect, 0, FEEL)
        costs = []
        t = 0
        path = [(14 + i * 9, 71 + i * 4) for i in range(300)]     # slow diagonal across the grid: many yields
        for x, y in path:
            t += 16
            start = time.perf_counter()
            g.step(Rect(x, y, 740, 470), t)
            costs.append((time.perf_counter() - start) * 1000)
        start = time.perf_counter()
        r = g.release(Rect(*path[-1], 740, 470), t + 16)
        release_ms = (time.perf_counter() - start) * 1000
        self.assertTrue(valid(r.state), r.notes)
        p95 = sorted(costs)[int(len(costs) * .95)]
        print(f'feel frame cost, 20 windows, {len(costs)} ticks: median {statistics.median(costs):.3f} ms, '
              f'p95 {p95:.3f} ms, max {max(costs):.3f} ms; release {release_ms:.3f} ms')
        self.assertLess(p95, 8.0)


if __name__ == '__main__':
    unittest.main()
