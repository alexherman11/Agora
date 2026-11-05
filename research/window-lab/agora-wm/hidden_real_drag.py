"""House-only outcome check: real queued mouse gestures, native and Agora.

No SendInput, cursor warping, desktop switching, synthetic WinEvents, or
programmatic movement during a gesture. A native modal loop that cannot be
driven on a hidden desktop FAILS; never fall back to the simulated feel proof.
Run with the pinned Python, outside the worker sandbox. All artifacts go to
AGORA_REVIEW_EVIDENCE, scratch to AGORA_TMP. No live world is opened.
"""
import ctypes as C
from ctypes import wintypes as W
import json
import os
from pathlib import Path
import sys
import threading
import time
import traceback
import uuid

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / 'kernel-desktop'))
from drag_evidence import assess


def write(path, value):
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')


def hidden_identity(sb, name):
    """A fixture cannot be invoked directly on the input/default desktop."""
    u = sb.u32
    u.GetThreadDesktop.argtypes = [W.DWORD]
    u.GetThreadDesktop.restype = W.HANDLE
    current = sb.desk_name(u.GetThreadDesktop(sb.k32.GetCurrentThreadId()))
    expected = 'agora-sandbox-' + name
    if current != expected or sb.alex()['input desktop'] == expected:
        raise RuntimeError('fixture requires its named, non-input hidden desktop')


def drive(sb, scene, screen, out, name):
    from win32_host import Native, EventFeed, Rect, reference, rect, u
    from manager import Manager
    from hidden_feel_proof import StandInLease, wait_for
    import gaming_gate
    hwnds = dict(scene.windows, agora=screen.wins['drag-fixture']['hwnd'])
    allowed = set(hwnds.values())
    refs = {key: reference(hwnd) for key, hwnd in hwnds.items()}
    native = Native(mutating=True, allowed=allowed)
    work = Rect(0, 0, 2200, 1500)
    boxes = {'native': Rect(40, 70, 850, 650), 'agora': Rect(940, 70, 850, 650)}
    manager = Manager(native, out / 'manager', allow_live=True, gate_fn=gaming_gate.reasons,
                      lease_factory=lambda _: StandInLease(allowed))
    feed = EventFeed().start()
    traces = {}
    try:
        # Native.windows enumerates this hidden desktop; explicitly limit ingestion too.
        def rows():
            return [r for r in native.windows() if r['ref'].hwnd in allowed]

        last_full = 0.0

        def tick(trace=None):
            nonlocal last_full
            began = time.perf_counter()
            events = [e for e in feed.drain() if e['hwnd'] in allowed]
            # Match the production fast path: geometry per frame, full enumeration
            # for lifecycle events and the periodic safety check.
            if (not manager.gesture or time.monotonic() - last_full >= 1
                    or any(e['type'] in ('drag-start', 'drag-end', 'close', 'hide', 'minimise') for e in events)):
                manager.ingest(rows(), work, events)
                last_full = time.monotonic()
            if manager.gesture:
                manager.drag_tick(native.rect_of(refs[active]))
            manager.motion_tick()
            if trace is not None:
                trace['events'].extend(e['type'] for e in events if e['hwnd'] == hwnds[active])
                trace['tick_ms'].append((time.perf_counter() - began) * 1000)
                trace['neighbour'].append(rect(hwnds[other]).values())
                trace['alive'] &= all(u.IsWindow(h) for h in allowed)
                trace['visible'] &= all(u.IsWindowVisible(h) and not u.IsIconic(h) for h in allowed)

        manager.ingest(rows(), work)
        manager.switch('live')
        for active in ('native', 'agora'):
            hidden_identity(sb, name)
            other = 'agora' if active == 'native' else 'native'
            # Reset only between gestures, through the allowlisted native seam.
            for key in boxes:
                manager.lease.save(refs[key])
            # Both cases start on the left and drag across the other window.
            native.place(refs[active], boxes['native'])
            native.place(refs[other], boxes['agora'])
            wait_for(lambda: rect(hwnds[active]) == boxes['native'] and rect(hwnds[other]) == boxes['agora'])
            manager.boot = True
            for _ in range(25):
                tick()
                time.sleep(.016)
            trace = dict(input=[], events=[], alive=True, visible=True, rings=0,
                         neighbour=[rect(hwnds[other]).values()], input_lag_ms=[], tick_ms=[])
            traces[active] = trace
            hwnd = hwnds[active]
            start = rect(hwnd)
            if active == 'native':
                # Non-client caption down; DefWindowProc owns the real move loop.
                target = hwnd
                sx, sy = start.x + 140, start.y + 12
                sb.post(hwnd, 0xA1, 2, sb.xy(sx, sy))  # WM_NCLBUTTONDOWN, HTCAPTION
            else:
                # Read the real production strip; no JS dispatch or drag callbacks.
                win = screen.wins['drag-fixture']['w']
                grip = win.evaluate_js("""(() => {
                  const e=document.querySelector('.name.pywebview-drag-region');
                  if (!e || !window.pywebview) return null;
                  const r=e.getBoundingClientRect(); return [(r.x+20)*devicePixelRatio,(r.y+r.height/2)*devicePixelRatio];
                })()""")
                assert grip, 'production Agora drag strip not ready'
                target, point = sb.deepest(hwnd, *grip)
                screen_point = W.POINT(point.x, point.y)
                sb.u32.MapWindowPoints(target, None, C.byref(screen_point), 1)
                sx, sy = screen_point.x, screen_point.y
                sb.post(target, 0x200, 0, sb.xy(point.x, point.y))
                sb.post(target, 0x201, 1, sb.xy(point.x, point.y))
            trace['input'].append('down')
            try:
                end = time.monotonic() + 2
                while not manager.gesture and time.monotonic() < end:
                    tick(trace)
                    time.sleep(.008)
                assert manager.gesture, f'{active}: mouse down did not start the OS move loop'
                # A fast diagonal/downward drag, followed by a hold to observe the full slide.
                for i in range(1, 25):
                    point = W.POINT(sx + i * 42, sy + i * 13)
                    sb.u32.MapWindowPoints(None, target, C.byref(point), 1)
                    previous = rect(hwnd)
                    began = time.perf_counter()
                    sb.post(target, 0x200, 1, sb.xy(point.x, point.y))
                    until = time.monotonic() + .1
                    while rect(hwnd) == previous and time.monotonic() < until:
                        tick(trace)
                        time.sleep(.004)
                    assert rect(hwnd) != previous, f'{active}: queued mouse move did not move the real window'
                    trace['input_lag_ms'].append((time.perf_counter() - began) * 1000)
                    tick(trace)
                    time.sleep(.008)
                trace['input'].append('move')
                for _ in range(35):
                    tick(trace)
                    time.sleep(.016)
                assert manager.ghost and manager.ghost.landing, 'landing preview absent'
                landing = manager.ghost.shown[manager.ghost.landing]
                trace['landing'] = landing.values()
                # Paint evidence comes from the actual preview HWNDs, not style declarations.
                for i, (handle, box) in enumerate(manager.ghost.shown.items()):
                    if box is None or not u.IsWindowVisible(handle):
                        continue
                    im = sb.print_window(handle)
                    im.save(out / f'{active}-ring-{i}.png')
                    pixels = im.convert('RGB')
                    border = [pixels.getpixel((x, y)) for x in range(0, im.width, max(1, im.width // 80))
                              for y in (min(2, im.height - 1), max(0, im.height - 3))]
                    border += [pixels.getpixel((x, y)) for y in range(0, im.height, max(1, im.height // 80))
                               for x in (min(2, im.width - 1), max(0, im.width - 3))]
                    if sum(max(p) - min(p) >= 45 for p in border) >= len(border) // 3:
                        trace['rings'] += 1
            finally:
                # Release our own queue even on assertion failure; never release global input.
                sb.post(target, 0x202, 0, sb.xy(0, 0))
                trace['input'].append('up')
                sb.post(hwnd, 0x202, 0, sb.xy(0, 0))
            for _ in range(70):
                tick(trace)
                time.sleep(.016)
            assert manager.gesture is None, 'mouse up did not end the OS move loop'
            trace['drop'] = rect(hwnd).values()
            trace['metrics'] = assess(trace)
            sb.print_window(hwnd).save(out / f'{active}-after.png')
        return traces
    finally:
        write(out / 'traces.json', traces)
        manager.switch('off')
        feed.close()


def fixture(out, name):
    import sandbox_window as sb
    hidden_identity(sb, name)  # before creating any window, world or browser
    import webview
    from kd_window import GuiScreen
    from test_kdesk import Desk, quoted
    from types import SimpleNamespace
    from urllib.parse import quote
    import hidden_feel_proof as native_fixture
    result = {'ok': False}
    desk = Desk()
    native_fixture.SCENE = {'native': (40, 70, 850, 650)}
    screen = GuiScreen(SimpleNamespace(token=desk.entry.token('alex')))
    response = desk.say('make kind=lens name=drag-proof text=' + quoted('root : text "Hidden drag fixture"'))
    assert response['ok'], response.get('text')
    shown = threading.Event()
    closed = []

    def run():
        joined = sb.join(name)
        try:
            path = '/desk/frame.html?lens=drag-proof&name=Hidden%20drag%20fixture'
            url = desk.url + '/dev/signin?token=' + quote(desk.entry.token('alex')) + '&next=' + quote(path)
            screen.open('drag-fixture', 'frame', 'Hidden drag fixture', url, (940, 70, 850, 650),
                        lambda: closed.append(True), shown.set)
            assert shown.wait(35), 'Agora WebView2 window never loaded'
            with native_fixture.Scene(name) as scene:
                result['gestures'] = drive(sb, scene, screen, out, name)
            assert not closed, 'Agora close callback fired during drag'
            result['ok'] = True
        except BaseException:
            result['error'] = traceback.format_exc()
        finally:
            write(out / 'fixture-result.json', result)
            for rec in list(screen.wins.values()):
                rec['w'].destroy()
            screen.anchor.destroy()
            desk.close()
            sb.u32.CloseDesktop(joined)

    # The same production profile/drag/host setup, on the inherited hidden desktop.
    screen.start(lambda: threading.Thread(target=run, daemon=True).start())


def run(out):
    import gaming_gate
    gaming_gate.assert_clear()  # before desktop, native fixture, kernel or browser startup
    import sandbox_window as sb
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'fixture-result.json').exists():
        raise RuntimeError('evidence directory already used; require a fresh House review')
    name = 'house-drag-' + uuid.uuid4().hex[:12]
    result = {'ok': False, 'desktop': name}
    guard = sb.Guard(name, 'Hidden drag fixture')
    try:
        with guard, sb.job_scope(name) as job:
            try:
                sb.start(name, [sys.executable, '-B', str(Path(__file__).resolve()), '--fixture', str(out), name],
                         env={'AGORA_KEEPER': '', 'AGORA_REVIEW_EVIDENCE': str(out)}, job=job)
                deadline = time.monotonic() + 150
                while not (out / 'fixture-result.json').exists():
                    gaming_gate.assert_clear()  # abort and close our owned job if a game starts
                    if time.monotonic() >= deadline:
                        raise TimeoutError('hidden real drag fixture timed out')
                    time.sleep(.25)
                result['fixture'] = json.loads((out / 'fixture-result.json').read_text(encoding='utf-8'))
                assert result['fixture']['ok'], result['fixture'].get('error', 'gesture failed')
                gaming_gate.assert_clear()
            finally:
                if sb.state_file(name).exists():
                    result['cleanup'] = sb.close(name)
                    assert result['cleanup']['ok'], result['cleanup']
        code, words = guard.verdict()
        result['guard'] = words
        assert code == 0, words
        result['ok'] = True
    except BaseException:
        result['error'] = traceback.format_exc()
    finally:
        result['guard'] = guard.verdict()[1]
        write(out / 'result.json', result)
    print(json.dumps(result, indent=2), flush=True)
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--fixture':
        destination = Path(sys.argv[2])
        try:
            fixture(destination, sys.argv[3])
        except BaseException:
            write(destination / 'fixture-result.json', {'ok': False, 'error': traceback.format_exc()})
            raise
    else:
        destination = Path(os.environ.get('AGORA_REVIEW_EVIDENCE', HERE.parents[2] / '.tmp' / 'real-drag'))
        raise SystemExit(run(destination))
