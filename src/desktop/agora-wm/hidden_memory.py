"""Native causal restoration acceptance; only disposable hidden HWNDs."""
import sys, threading, time, uuid, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from hidden_proof import Fixtures, sb, u, dpi_aware, wait_for
from win32_host import Native, reference, rect
from manager import Manager
from engine import Rect, valid, copy_state
from unittest.mock import Mock

def run(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    dpi_aware();name='memory-'+uuid.uuid4().hex[:10]
    h,full=sb.desktop(name,create=True);before=sb.alex();report={'scenarios':[]};errors=[]
    try:
        for manual in (False,True):
            with Fixtures(name) as fixtures:
                def worker():
                    joined=sb.join(name);manager=None
                    try:
                        handles=[fixtures.windows[k] for k in ('ordinary','minimum')]
                        for hwnd in handles:fixtures.kinds[hwnd]='minimum'
                        native=Native(mutating=True,allowed=handles)
                        refs=[reference(hwnd) for hwnd in handles]
                        measured={}
                        for ref in refs:
                            native.place(ref,Rect(30,30,240,160));time.sleep(.15)
                            measured[ref.key]=(rect(ref.hwnd).w,rect(ref.hwnd).h)
                        pref=(950,700) if manual else (600,400)
                        native.place(refs[0],Rect(16,16,*pref));native.minimise(refs[1]);time.sleep(.3)
                        work=Rect(0,0,1400,900) if manual else Rect(0,0,650,450)
                        def rows():
                            found=[r for r in native.windows() if r['ref'].hwnd in handles]
                            for r in found:r['_preferred']=pref
                            return found
                        # All windows belong to this process and disappear with it. Native's HWND allowlist
                        # and never-shown desktop fence mutations; a mocked lease avoids external watchdogs.
                        manager=Manager(native,out/('manual' if manual else 'restore'),allow_live=True,
                            gate_fn=lambda:[],lease_factory=lambda _:Mock())
                        manager.ingest(rows(),work)
                        for key,size in measured.items():manager.state.windows[key].minimum=size
                        manager.switch('live')
                        def settle():
                            for _ in range(30):manager.ingest(rows(),work);time.sleep(.04)
                            actual=copy_state(manager.state)
                            for r in rows():
                                actual.windows[r['key']].rect=Rect(*r['rect'])
                                actual.windows[r['key']].minimised=r['state']=='minimised'
                            assert valid(actual),'native placements invalid'
                            active=sb.alex()
                            assert active['input desktop']==before['input desktop']
                            assert active['foreground'] not in fixtures.windows.values()
                            return actual
                        initial=settle();baseline=initial.windows[refs[0].key].rect
                        native.restore(refs[1]);time.sleep(.15);displaced=settle()
                        a=displaced.windows[refs[0].key]
                        assert manager.state.displacement.get(refs[0].key),'no causal displacement recorded'
                        if manual:
                            assert not a.minimised and a.rect!=baseline,'expected shrink'
                            native.minimise(refs[0]);time.sleep(.15)
                            assert settle().windows[refs[0].key].minimised
                            assert refs[0].key not in manager.state.displacement,'manual override retained stale debt'
                        else:assert a.minimised,'expected constrained displacement to minimise A'
                        assert native.close(refs[1]),'close request failed'
                        wait_for(lambda:not u.IsWindow(refs[1].hwnd));final=settle()
                        assert refs[1].key not in final.windows,'closed window still managed'
                        restored=final.windows[refs[0].key]
                        if manual:assert restored.minimised,'close undid manual minimise'
                        else:
                            assert not restored.minimised,'close did not restore displaced window'
                            assert restored.rect==baseline,(restored.rect,baseline)
                        report['scenarios'].append({'manual_override':manual,'before':baseline.values(),
                            'displaced_minimised':a.minimised,'displaced_rect':a.rect.values(),
                            'after_close_minimised':restored.minimised,'after_close_rect':restored.rect.values(),
                            'measured_minimum':list(measured[refs[0].key]),'native_nonoverlap':True,
                            'closed_opener_removed':True})
                    except BaseException:
                        import traceback
                        errors.append(traceback.format_exc())
                    finally:
                        if manager:manager.switch('off')
                        u.CloseDesktop(joined)
                thread=threading.Thread(target=worker);thread.start();thread.join(20)
                assert not thread.is_alive(),'hidden memory proof timed out'
                if errors:raise AssertionError(errors[0])
        after=sb.alex();report['input_desktop_unchanged']=before['input desktop']==after['input desktop']
        report['fixture_never_foreground']=True
    finally:u.CloseDesktop(h)
    (out/'native-memory.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

if __name__=='__main__':run(sys.argv[1])
