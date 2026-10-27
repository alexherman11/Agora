"""The drag feel with real Win32 windows, real ghosts, a real lease and real placement, on a never-shown desktop.

A drag is emulated the way Windows' move loop would look to the manager: a move/size start event, the dragged
window's rectangle changing at 60 Hz (we move our own fixture with SetWindowPos), then a move/size end event.
No input is sent anywhere; nothing is created on Alex's desktop. Run: python hidden_feel_proof.py
"""
import ctypes as C
from ctypes import wintypes as W
import json
from pathlib import Path
import statistics
import sys
import tempfile
import threading
import time
import uuid

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import sandbox_window as sb
from hidden_proof import PROC, WNDCLASS, wait_for
from win32_host import Native, Rect, reference, rect, u, k, dpi_aware
from engine import valid

WORK = Rect(0, 57, 3840, 1977)                  # Alex's work area (ran, 26 Oct); State's default gaps are 16
SCENE = {'browser': (16, 73, 1800, 1300), 'chat': (1832, 73, 1992, 1300), 'notes': (16, 1389, 1000, 629)}


class Scene:
    """Three ordinary captioned windows on the hidden desktop, pumped by their own thread."""
    def __init__(self, desktop):
        self.desktop = desktop; self.ready = threading.Event(); self.stop = threading.Event(); self.windows = {}
        self.error = None; self.thread = threading.Thread(target=self.run, daemon=True)

    def run(self):
        try:
            h = sb.join(self.desktop)
            self.proc = PROC(lambda hwnd, msg, wp, lp: u.DefWindowProcW(hwnd, msg, wp, lp))
            wc = WNDCLASS(); wc.proc = self.proc; wc.name = 'AgoraWMFeel' + uuid.uuid4().hex
            wc.instance = k.GetModuleHandleW(None)
            if not u.RegisterClassW(C.byref(wc)):
                raise OSError('RegisterClass')
            for i, name in enumerate(SCENE):
                hwnd = u.CreateWindowExW(0x40000, wc.name, 'WM feel fixture', 0x00CF0000, 200 + i * 60, 200 + i * 60,
                                         900, 700, None, None, wc.instance, None)
                if not hwnd:
                    raise OSError('CreateWindow')
                self.windows[name] = int(hwnd); u.ShowWindowAsync(hwnd, 4)
            self.ready.set(); msg = W.MSG()
            while not self.stop.is_set():
                while u.PeekMessageW(C.byref(msg), None, 0, 0, 1):
                    u.TranslateMessage(C.byref(msg)); u.DispatchMessageW(C.byref(msg))
                time.sleep(.002)
            for hwnd in self.windows.values():
                u.DestroyWindow(hwnd)
            u.CloseDesktop(h)
        except BaseException as exc:
            self.error = exc; self.ready.set()

    def __enter__(self):
        self.thread.start(); assert self.ready.wait(5)
        if self.error:
            raise self.error
        return self

    def __exit__(self, *_):
        self.stop.set(); self.thread.join(5)


def run(out):
    out = Path(out); dpi_aware(); name = 'wm-feel-' + uuid.uuid4().hex[:10]
    h, full = sb.desktop(name, create=True)
    report = {'desktop': full, 'tests': []}; before = sb.alex()
    try:
        with Scene(name) as scene:
            def worker():
                joined = sb.join(name)
                try:
                    report.update(drive(scene, full, out))
                except BaseException:
                    import traceback
                    report['error'] = traceback.format_exc(); print(report['error'], flush=True)
                finally:
                    u.CloseDesktop(joined)
            thread = threading.Thread(target=worker); thread.start(); thread.join(120)
            assert not thread.is_alive(), 'hidden feel proof timed out'
    finally:
        report['alex_before'] = before; report['alex_after'] = sb.alex()
        report['alex_untouched'] = before == report['alex_after']
        (out / 'feel-l1.json').write_text(json.dumps(report, indent=2, default=str)); u.CloseDesktop(h)
    if report.get('error'):
        raise AssertionError(report['error'])
    assert report['alex_after']['input desktop'] == before['input desktop']
    print('feel L1 passed; alex: ' + ('untouched' if report['alex_untouched'] else 'concurrent input; see snapshots'),
          flush=True)


class StandInLease:
    """In-process lease with the watchdog's save/restore contract. The real guard cannot arm here: Alex's live WM
    guard holds Ctrl+Alt+Backspace (ran 26 Oct: RegisterHotKey error 1409, already registered; hotkeys are per
    window station, so a hidden desktop does not get its own). hidden_proof.py covers the real watchdog."""
    def __init__(self, allowed):
        self.native = Native(mutating=True, allowed=allowed); self.saved = {}

    def acquire(self):
        return {'ready': True}

    def heartbeat(self):
        pass

    def save(self, ref, geometry=True):
        self.saved.setdefault(ref.hwnd, (ref, self.native.placement(ref)))

    def release(self):
        for ref, placement in self.saved.values():
            self.native.restore_placement(ref, placement)


def drive(scene, full, out):
    from manager import Manager
    allowed = set(scene.windows.values())
    native = Native(allowed=allowed)
    refs = {n: reference(hwnd) for n, hwnd in scene.windows.items()}
    baseline = {n: native.placement(r)['normal'] for n, r in refs.items()}
    m = Manager(native, tempfile.mkdtemp(prefix='wm-feel-'), allow_live=True, gate_fn=lambda: [],
                lease_factory=lambda path: StandInLease(allowed))
    results = {'scale': native.scale(), 'tests': []}

    def tick(events=()):
        if m.lease:
            m.lease.heartbeat()
        return m.ingest(native.windows(), WORK, events)

    def settle(seconds=.8):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            tick(); time.sleep(.05)

    def actual():
        return {n: rect(r.hwnd) for n, r in refs.items()}

    def check(label, value):
        row = {'test': label, 'result': value}; results['tests'].append(row)
        print('feel L1 ' + json.dumps(row, default=str), flush=True)

    tick(); m.switch('live')
    try:
        # Lay out the scene exactly (lease first, as the manager does), then let the manager adopt it as it is.
        for n, box in SCENE.items():
            m.lease.save(refs[n]); native.place(refs[n], Rect(*box))
        wait_for(lambda: all(rect(refs[n].hwnd) == Rect(*b) for n, b in SCENE.items()), 3)
        m.boot = True; settle()
        assert actual() == {n: Rect(*b) for n, b in SCENE.items()}, actual()
        costs = []

        def drag(name, path, hold_ms=0, events_at_end=True):
            hwnd = refs[name].hwnd
            tick([{'type': 'drag-start', 'hwnd': hwnd}])
            for box in path + [path[-1]] * (hold_ms // 16):
                native.place(refs[name], Rect(*box))      # what Windows' move loop would do to the dragged window
                time.sleep(1 / 60)
                start = time.perf_counter(); m.drag_tick(native.rect_of(refs[name]))
                costs.append((time.perf_counter() - start) * 1000)
            wait_for(lambda: rect(hwnd) == Rect(*path[-1]), 2)
            ghosts = sum(1 for g in (m.ghost.handles if m.ghost else []) if u.IsWindowVisible(g))
            landing_shown = bool(m.ghost and m.ghost.landing and u.IsWindowVisible(m.ghost.landing))
            tick([{'type': 'drag-end', 'hwnd': hwnd}]); settle()
            return ghosts, landing_shown

        # 1. A sloppy drop that clips the browser: only the notes move, back to exactly the gap.
        path = [(16 + 20 * i, 1389 - 4 * i, 1000, 629) for i in range(1, 11)]
        ghosts, landing = drag('notes', path)
        now = actual()
        assert now['browser'] == Rect(*SCENE['browser']) and now['chat'] == Rect(*SCENE['chat']), now
        assert now['notes'] == Rect(216, 1389, 1000, 629), now['notes']
        check('shallow drop: dragged window pushed back to the gap, neighbours untouched',
              {'notes': now['notes'].values(), 'landing_outline_shown': landing, 'ghosts': ghosts})

        # 2. Hover on the browser, rest 600 ms: its ghost gives way; release: the real browser follows the ghost.
        start = now['notes']
        path = [(start.x, start.y - 29 * i, 1000, 629) for i in range(1, 11)]
        ghosts, landing = drag('notes', path, hold_ms=600)
        now = actual(); state = m.state
        overlap_free = valid(state) and all(not a.near(b, 16) for i, a in enumerate(now.values())
                                            for b in list(now.values())[i + 1:])
        assert ghosts >= 1, 'a neighbour ghost was shown during the dwell'
        assert now['browser'] != Rect(*SCENE['browser']) and overlap_free, now
        check('dwell then release: neighbour ghost shown, then real neighbour moved; actual windows overlap-free',
              {k: v.values() for k, v in now.items()} | {'ghosts_shown': ghosts})

        # 3. Shared edge: put browser|chat back side by side, widen the browser by 300: the chat recedes.
        for n, box in SCENE.items():
            native.place(refs[n], Rect(*box))
        wait_for(lambda: all(rect(refs[n].hwnd) == Rect(*b) for n, b in SCENE.items()), 3)
        m.boot = True; settle()
        path = [(16, 73, 1800 + 30 * i, 1300) for i in range(1, 11)]
        drag('browser', path)
        now = actual()
        assert now['browser'] == Rect(16, 73, 2100, 1300), now['browser']
        assert now['chat'] == Rect(16 + 2100 + 16, 73, 3824 - (16 + 2100 + 16), 1300), now['chat']
        check('shared edge resize: chat recedes with the browser edge', {k: v.values() for k, v in now.items()})

        results['drag_tick_ms'] = {'ticks': len(costs), 'median': round(statistics.median(costs), 3),
                                   'p95': round(sorted(costs)[int(len(costs) * .95)], 3), 'max': round(max(costs), 3),
                                   'meaning': 'manager.drag_tick incl. feel step and real ghost SetWindowPos calls'}
        print('feel L1 drag tick: ' + json.dumps(results['drag_tick_ms']), flush=True)
    finally:
        m.switch('off')
    wait_for(lambda: all(native.placement(r)['normal'] == baseline[n] for n, r in refs.items()), 3)
    check('off restores every fixture to its placement before the lease', True)
    return results


if __name__ == '__main__':
    run(HERE / 'evidence')
