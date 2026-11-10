"""Actual native drift, glass and release on a never-shown desktop.

Uses the shared guarded fixture and an allowlisted Native. No input injection,
live window enumeration, hotkey registration or desktop switching.
"""
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'agora'))
from kernel import scratch
import hidden_feel_proof as fixture
from engine import Rect, valid
from manager import Manager
from win32_host import Native, reference, rect, u


def drive(scene, desktop, out):
    refs = {name: reference(hwnd) for name, hwnd in scene.windows.items()}
    native = Native(mutating=True, allowed=set(scene.windows.values()))
    # Fixture pointer samples exercise selection without moving the real
    # cursor or injecting input, even on the never-shown desktop.
    pointer = [None]
    native.cursor = lambda: pointer[0]
    foreground = u.GetForegroundWindow()
    with scratch.TemporaryDirectory(prefix='drop-native-') as home:
        m = Manager(native, home, allow_live=True, gate_fn=lambda: [],
                    lease_factory=lambda _: fixture.StandInLease(set(scene.windows.values())))
        m.switch('live')
        try:
            for name, box in fixture.SCENE.items():
                m.lease.save(refs[name]);native.place(refs[name],Rect(*box))
            fixture.wait_for(lambda: all(rect(refs[n].hwnd)==Rect(*b) for n,b in fixture.SCENE.items()),3)
            m.ingest(native.windows(),fixture.WORK)
            m.ingest(native.windows(),fixture.WORK,[{'type':'drag-start','hwnd':refs['a'].hwnd}])
            assert m.ghost and m.ghost.landing, 'glass appears at pickup'
            assert u.IsWindowVisible(m.ghost.landing)
            bhome = Rect(*fixture.SCENE['b'])
            almost = Rect(bhome.x-1,bhome.y,bhome.w,bhome.h)
            native.place(refs['a'],almost)
            for _ in range(24):
                m.drag_tick(almost);time.sleep(1/60)
            assert rect(refs['b'].hwnd)==bhome, 'overlap/dwell before centre cannot move B'
            crossing=Rect(bhome.x+1,bhome.y,bhome.w,bhome.h)
            native.place(refs['a'],crossing)
            samples=[];costs=[]
            for _ in range(5):
                at=time.perf_counter();m.drag_tick(crossing)
                costs.append((time.perf_counter()-at)*1000)
                time.sleep(1/60);samples.append(rect(refs['b'].hwnd).values())
            assert 16<samples[-1][0]<bhome.x, samples
            m.ingest(native.windows(),fixture.WORK,[{'type':'drag-end','hwnd':refs['a'].hwnd}])
            landing=m.state.windows[refs['a'].key].rect
            for _ in range(25):
                m.motion_tick();time.sleep(1/60)
                samples.append(rect(refs['b'].hwnd).values())
            fixture.wait_for(lambda: rect(refs['a'].hwnd)==landing and rect(refs['b'].hwnd)==Rect(*fixture.SCENE['a']),3)
            assert valid(m.state)
            # Make a genuinely free side using only our allowlisted fixture.
            native.minimise(refs['b'])
            fixture.wait_for(lambda: bool(u.IsIconic(refs['b'].hwnd)),3)
            native.place(refs['a'],Rect(*fixture.SCENE['a']))
            fixture.wait_for(lambda: rect(refs['a'].hwnd)==Rect(*fixture.SCENE['a']),3)
            m.ingest(native.windows(),fixture.WORK)
            selected=[]
            for fraction,offset in ((.75,1000),(.95,2100)):
                rows=native.windows()
                m.ingest(rows,fixture.WORK,[{'type':'drag-start','hwnd':refs['a'].hwnd}])
                bounds=m.state.bounds
                pointer[0]=(round(bounds.x+bounds.w*fraction),bounds.y+20)
                actual=rect(refs['a'].hwnd)
                moving=Rect(offset,actual.y,actual.w,actual.h)
                native.place(refs['a'],moving)
                fixture.wait_for(lambda: rect(refs['a'].hwnd)==moving,3)
                frame=m.drag_tick(moving)
                selected.append(frame.landing)
                assert m.ghost.shown[m.ghost.landing]==frame.landing
                ex=u.GetWindowLongPtrW(m.ghost.landing,-20)
                assert ex & (0x80000|0x20|0x80|0x08000000)==(0x80000|0x20|0x80|0x08000000)
                m._release(moving,time.monotonic()*1000)
                for _ in range(25):
                    m.motion_tick();time.sleep(1/60)
                fixture.wait_for(lambda: rect(refs['a'].hwnd)==frame.landing,3)
            assert selected[0].w>selected[1].w, selected
            assert u.GetForegroundWindow()==foreground, 'native moves and overlays must not take focus'
            result={'checks':8,'samples':samples,'landing':landing.values(),
                    'cursor_landings':[r.values() for r in selected],
                    'drag_tick_ms':costs,'focus_unchanged':True}
            print('hidden native drop: 8 checks passed',flush=True)
            return result
        finally:
            m.switch('off')


if __name__ == '__main__':
    fixture.SCENE={'a':(16,73,1896,1945),'b':(1928,73,1896,1945)}
    fixture.drive=drive
    out=Path(sys.argv[1]) if len(sys.argv)>1 else HERE.parents[2]/'.tmp'
    out.mkdir(parents=True,exist_ok=True)
    fixture.run(out)
