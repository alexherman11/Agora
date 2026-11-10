"""Native WM smoke proof: only newly-created HWNDs on a never-shown desktop."""
import sys, threading, time, uuid, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from hidden_proof import Fixtures, sb, u, dpi_aware
from win32_host import Native, reference
from manager import Manager
from engine import Rect, valid, copy_state
from unittest.mock import Mock

dpi_aware();name='adaptive-'+uuid.uuid4().hex[:10]
h,full=sb.desktop(name,create=True);before=sb.alex();report={};errors=[]
try:
    with Fixtures(name) as f:
        def worker():
            joined=sb.join(name)
            try:
                handles=[f.windows[k] for k in ('ordinary','frameless','minimum','slow')]
                native=Native(mutating=True,allowed=handles)
                # Frameless surrogate is explicitly Agora-marked, like a lens.
                u.SetPropW(handles[1],'Agora.Window.adaptive_fixture',1)
                for hwnd in handles[1:]:native.minimise(reference(hwnd))
                time.sleep(.4)
                def rows():
                    result=[r for r in native.windows() if r['ref'].hwnd in handles]
                    for r in result:r['_preferred']=(950,700)
                    return result
                manager=Manager(native,Path(sys.argv[1])/'controller',allow_live=True,gate_fn=lambda:[],lease_factory=lambda _:Mock())
                work=Rect(0,0,1600,1000)
                manager.ingest(rows(),work);manager.switch('live')
                def settle():
                    for _ in range(35):manager.ingest(rows(),work);time.sleep(.04)
                    actual=copy_state(manager.state)
                    for r in rows():
                        actual.windows[r['key']].rect=Rect(*r['rect'])
                        actual.windows[r['key']].minimised=r['state']=='minimised'
                    assert valid(actual),'native overlap or out-of-bounds'
                    return sum(not w.minimised for w in actual.windows.values())
                counts=[settle()]
                for hwnd in handles[1:]:
                    native.restore(reference(hwnd));time.sleep(.15);counts.append(settle())
                assert counts==[1,2,3,4],counts
                # A repeated external restore and polling must not evict the others.
                native.restore(reference(handles[-1]));assert settle()==4
                report['native_visible_counts']=counts;report['repeat_restore_visible']=4
                report['learned_minima']=[list(w.minimum) for w in manager.state.windows.values()]
                manager.switch('off')
            except BaseException:
                import traceback
                errors.append(traceback.format_exc())
            finally:u.CloseDesktop(joined)
        t=threading.Thread(target=worker);t.start();t.join(25)
        assert not t.is_alive(),'proof timed out'
        if errors:raise AssertionError(errors[0])
        after=sb.alex();report['input_desktop_unchanged']=before['input desktop']==after['input desktop']
        report['fixture_never_foreground']=after['foreground'] not in f.windows.values()
        assert report['input_desktop_unchanged'] and report['fixture_never_foreground']
finally:u.CloseDesktop(h)
Path(sys.argv[1]).mkdir(parents=True,exist_ok=True)
(Path(sys.argv[1])/'native-adaptive.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
