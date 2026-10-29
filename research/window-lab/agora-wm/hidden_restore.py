"""Repeated dock/external restore races using only owned hidden native fixtures.

Run with the pinned interpreter and AGORA_TMP/TMP/TEMP inside this worktree:
    python hidden_restore.py <worktree-scratch-output>
No Spotify process is launched: single-instance forwarding could reach Alex.
"""
import json
from pathlib import Path
import sys
import threading
import time
import uuid
from unittest.mock import Mock

from hidden_proof import Fixtures, sb, u, dpi_aware, wait_for
from win32_host import Native, reference
from manager import Manager
from engine import Rect, copy_state, valid


def run(out):
    out=Path(out).resolve()
    root=Path(__file__).resolve().parents[3]
    if not out.is_relative_to(root):raise ValueError('output must be inside this worktree')
    out.mkdir(parents=True,exist_ok=True)
    dpi_aware();name='restore-'+uuid.uuid4().hex[:10]
    desktop,full=sb.desktop(name,create=True);report={};errors=[]
    try:
        with sb.Guard(name,'WM hidden fixture') as guard, Fixtures(name) as fixtures:
            def worker():
                joined=sb.join(name)
                try:
                    handles=[fixtures.windows[k] for k in ('ordinary','frameless','minimum','slow')]
                    # Admit our frameless fixture explicitly, as the host does
                    # for Agora windows. Mutations remain HWND-allowlisted.
                    native=Native(mutating=True,allowed=handles,
                        rules={Path(sys.executable).stem.lower():{'manage':True}})
                    for hwnd in handles[1:]:native.minimise(reference(hwnd))
                    wait_for(lambda:all(u.IsIconic(h) for h in handles[1:]))
                    def rows():
                        found=[r for r in native.windows() if r['ref'].hwnd in handles]
                        assert len(found)==4,'all owned fixtures must be enumerable'
                        for r in found:r['_preferred']=(950,700)
                        return found
                    manager=Manager(native,out/'controller',allow_live=True,gate_fn=lambda:[],
                        lease_factory=lambda _:Mock())
                    work=Rect(0,0,1600,1000)
                    manager.ingest(rows(),work);manager.switch('live')
                    def tick():
                        observed=rows()
                        with (out/'trace.jsonl').open('a') as log:
                            log.write(json.dumps({'pending':{k:{a:str(b) for a,b in v.items()} for k,v in manager.pending.items()},
                                'rows':[{k:v for k,v in r.items() if k in ('key','state','rect')} for r in observed],
                                'windows':{k:str(w) for k,w in manager.state.windows.items()}})+'\n')
                        manager.ingest(observed,work)
                    def settle(expected):
                        for _ in range(30):
                            tick();time.sleep(.04)
                        actual=copy_state(manager.state)
                        for r in rows():
                            w=actual.windows[r['key']]
                            w.rect=Rect(*r['rect']);w.minimised=r['state']=='minimised'
                            assert w.managed,{'message':'native operation became a refusal',
                                'row':{k:v for k,v in r.items() if k!='ref'},
                                'failures':manager.failures,'pending':manager.pending,'planned':str(manager.state.windows[r['key']])}
                        assert valid(actual),'native overlap or out-of-bounds'
                        count=sum(not w.minimised for w in actual.windows.values())
                        assert count==expected,(count,expected)
                        return count
                    counts=[settle(1)]
                    for hwnd in handles[1:]:
                        native.restore(reference(hwnd))
                        wait_for(lambda:not u.IsIconic(hwnd))
                        counts.append(settle(len(counts)+1))
                    target=handles[-1];ref=reference(target)
                    key=next(r['key'] for r in rows() if r['ref'].hwnd==target)
                    rounds=[]
                    for route in ('dock','external'):
                        for _ in range(5):
                            manager.action('minimise',key)
                            wait_for(lambda:u.IsIconic(target))
                            manager.ingest(rows(),work)
                            # Keep an acknowledged minimise outstanding during
                            # the restore, as in the production race.
                            manager.pending[key]={'kind':'minimise','rect':None,'at':time.monotonic()}
                            if route=='dock':manager.action('restore',key)
                            else:native.restore(ref)
                            wait_for(lambda:not u.IsIconic(target))
                            manager.ingest(rows(),work)
                            assert not manager.state.windows[key].minimised
                            rounds.append({'route':route,'visible':settle(4)})
                    report.update(native_visible_counts=counts,restore_rounds=rounds)
                    manager.switch('off')
                except BaseException:
                    import traceback
                    errors.append(traceback.format_exc())
                finally:u.CloseDesktop(joined)
            thread=threading.Thread(target=worker)
            thread.start();thread.join(55)
            assert not thread.is_alive(),'hidden proof timed out'
            if errors:raise AssertionError(errors[0])
        failures=[note for note in guard.notes if note[2]]
        report['guard_failures']=failures
        report['input_desktop_unchanged']=sb.alex()['input desktop']==guard.first['input desktop']
        assert not failures,failures
        assert report['input_desktop_unchanged']
    finally:u.CloseDesktop(desktop)
    (out/'native-restore.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))


if __name__=='__main__':run(sys.argv[1])
