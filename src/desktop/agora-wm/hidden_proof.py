"""Real Win32 proof, exclusively on a never-shown sandbox desktop."""
import ctypes as C
from copy import deepcopy
from ctypes import wintypes as W
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import uuid

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import sandbox_window as sb
from win32_host import Native,EventFeed,Rect,reference,rect,attribute,u,k,sig,dpi_aware,identity

PROC=C.WINFUNCTYPE(C.c_ssize_t,W.HWND,W.UINT,W.WPARAM,W.LPARAM)


class WNDCLASS(C.Structure):
    _fields_=[('style',W.UINT),('proc',PROC),('clsExtra',C.c_int),('wndExtra',C.c_int),
        ('instance',W.HINSTANCE),('icon',W.HICON),('cursor',W.HANDLE),('brush',W.HBRUSH),
        ('menu',W.LPCWSTR),('name',W.LPCWSTR)]


class WINDOWPOS(C.Structure):
    _fields_=[('hwnd',W.HWND),('after',W.HWND),('x',C.c_int),('y',C.c_int),('cx',C.c_int),('cy',C.c_int),('flags',W.UINT)]


sig(u,'DefWindowProcW',C.c_ssize_t,W.HWND,W.UINT,W.WPARAM,W.LPARAM)
sig(u,'RegisterClassW',W.ATOM,C.POINTER(WNDCLASS))
sig(u,'CreateWindowExW',W.HWND,W.DWORD,W.LPCWSTR,W.LPCWSTR,W.DWORD,C.c_int,C.c_int,C.c_int,C.c_int,
    W.HWND,W.HMENU,W.HINSTANCE,C.c_void_p)
sig(u,'DestroyWindow',W.BOOL,W.HWND)
sig(k,'GetModuleHandleW',W.HMODULE,W.LPCWSTR)
sig(u,'NotifyWinEvent',None,W.DWORD,W.HWND,W.LONG,W.LONG)


def wait_for(fn,timeout=3):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        result=fn()
        if result:return result
        time.sleep(.01)
    raise AssertionError('timed out')


class Fixtures:
    def __init__(self,desktop):
        self.desktop=desktop;self.ready=threading.Event();self.stop=threading.Event();self.windows={};self.events=[]
        self.thread=threading.Thread(target=self.run,daemon=True);self.error=None

    def run(self):
        try:
            h=sb.join(self.desktop)
            self.kinds={};self.self_done=set()
            def proc(hwnd,msg,wp,lp):
                kind=self.kinds.get(int(hwnd))
                if msg==0x46:  # WM_WINDOWPOSCHANGING: app constraints apply to programmatic sizes too
                    pos=C.cast(lp,C.POINTER(WINDOWPOS)).contents
                    if kind=='minimum' and not pos.flags&1:pos.cx=max(500,pos.cx);pos.cy=max(350,pos.cy)
                    if kind=='slow':time.sleep(.08)
                if msg==5 and kind=='self-resizer' and hwnd not in self.self_done:
                    self.self_done.add(hwnd)
                    u.PostMessageW(hwnd,0x8001,0,0)
                if msg==0x8001:
                    u.SetWindowPos(hwnd,None,180,210,630,470,0x14)
                if msg==0x8002:  # explicit move/size hooks, as a real native modal loop emits
                    u.NotifyWinEvent(10,hwnd,0,0);u.NotifyWinEvent(11,hwnd,0,0)
                return u.DefWindowProcW(hwnd,msg,wp,lp)
            self.proc=PROC(proc);name='AgoraWMProof'+uuid.uuid4().hex
            wc=WNDCLASS();wc.proc=self.proc;wc.name=name;wc.instance=k.GetModuleHandleW(None)
            if not u.RegisterClassW(C.byref(wc)):raise OSError('RegisterClass')
            for i,kind in enumerate(('ordinary','frameless','minimum','self-resizer','slow')):
                hwnd=u.CreateWindowExW(0x40000,name,'WM hidden fixture',0x80000000 if kind=='frameless' else 0x00CF0000,
                    100+i*50,120+i*50,700,500,None,None,wc.instance,None)
                if not hwnd:raise OSError('CreateWindow')
                self.windows[kind]=int(hwnd);self.kinds[int(hwnd)]=kind;u.ShowWindowAsync(hwnd,4)
            self.ready.set();msg=W.MSG()
            while not self.stop.is_set():
                while u.PeekMessageW(C.byref(msg),None,0,0,1):u.TranslateMessage(C.byref(msg));u.DispatchMessageW(C.byref(msg))
                time.sleep(.002)
            for hwnd in self.windows.values():u.DestroyWindow(hwnd)
            u.CloseDesktop(h)
        except BaseException as exc:self.error=exc;self.ready.set()

    def __enter__(self):
        self.thread.start();assert self.ready.wait(5)
        if self.error:raise self.error
        return self

    def __exit__(self,*_):self.stop.set();self.thread.join(5)


def crash_probe(info,path,desktop):
    from watchdog import Lease
    dpi_aware()
    sb.join(desktop.split('agora-sandbox-',1)[1])
    data=json.loads(Path(info).read_text());ref=reference(data['hwnd'])
    native=Native(mutating=True,allowed=[ref.hwnd]);lease=Lease(path,allowed=[ref.hwnd],desktop=desktop)
    lease.acquire();lease.save(ref);native.place(ref,Rect(800,600,800,600))
    Path(str(path)+'.ready').write_text(json.dumps({'manager':identity(os.getpid())}))
    while True:lease.heartbeat();time.sleep(.1)


def run(out):
    out=Path(out);dpi_aware();name='wm-proof-'+uuid.uuid4().hex[:10]
    h,full=sb.desktop(name,create=True)
    report={'desktop':full,'tests':[]};before=sb.alex();input_before=sb.last_input()
    def check(label,fn):
        start=sb.alex();input_start=sb.last_input();t=time.perf_counter();value=fn();end=sb.alex()
        unchanged=start==end
        row={'test':label,'result':value,'ms':round((time.perf_counter()-t)*1000,3),'alex_untouched':unchanged,
            'concurrent_input':sb.last_input()!=input_start,'before':start,'after':end}
        report['tests'].append(row);print('L1 '+json.dumps(row),flush=True)
        assert end['input desktop']==before['input desktop'],'input desktop changed'
        assert end['foreground'] not in f.windows.values(),'fixture reached Alex foreground'
        return value
    try:
        with Fixtures(name) as f:
            def worker():
                joined=sb.join(name)
                try:
                    native=Native(mutating=True,allowed=f.windows.values());ref=reference(f.windows['ordinary'])
                    def accuracy():
                        target=Rect(220,180,1000,720);native.place(ref,target)
                        wait_for(lambda:rect(ref.hwnd)==target)
                        return {'target':target.values(),'actual':rect(ref.hwnd).values(),'error_px':0}
                    check('border-compensated placement',accuracy)
                    def minrestore():
                        native.minimise(ref);wait_for(lambda:u.IsIconic(ref.hwnd));native.restore(ref)
                        wait_for(lambda:not u.IsIconic(ref.hwnd));return 'minimise and restore passed'
                    check('minimise/restore',minrestore)
                    def eligibility():
                        rows=native.windows();mapped={r['ref'].hwnd:r for r in rows}
                        assert mapped[f.windows['ordinary']]['managed']
                        assert not mapped[f.windows['frameless']]['managed']
                        assert 'title' not in json.dumps([{k:v for k,v in r.items() if k!='ref'} for r in rows]).lower()
                        return {'ordinary':'managed','frameless':'fixed obstacle','rows':len(rows)}
                    check('eligibility and privacy',eligibility)
                    def native_identity():
                        hwnd=f.windows['frameless'];u.SetPropW(hwnd,'Agora.Window.wt123',1)
                        try:
                            rows=native.windows();row=next(r for r in rows if r['ref'].hwnd==hwnd)
                            assert row['agora']=='wt123' and row['app']=='Agora' and row['managed']
                            return {'agora':'wt123','managed_frameless':True,'title_read':False}
                        finally:u.RemovePropW(hwnd,'Agora.Window.wt123')
                    check('Agora native identity marker',native_identity)
                    def minimum():
                        rr=reference(f.windows['minimum']);native.place(rr,Rect(100,100,240,160))
                        time.sleep(.2);actual=rect(rr.hwnd)
                        assert actual.w>240 and actual.h>160
                        return {'asked':[240,160],'actual':[actual.w,actual.h],'learned_minimum':[actual.w,actual.h]}
                    check('minimum-size refuser',minimum)
                    def selfresize():
                        rr=reference(f.windows['self-resizer']);f.self_done.discard(rr.hwnd)
                        native.place(rr,Rect(100,100,700,500))
                        wait_for(lambda:rect(rr.hwnd).w not in (700,))
                        return {'actual':rect(rr.hwnd).values()}
                    check('self resizer read-back',selfresize)
                    def slow():
                        rr=reference(f.windows['slow']);start=time.perf_counter();native.place(rr,Rect(200,300,800,600))
                        enqueue=(time.perf_counter()-start)*1000
                        wait_for(lambda:rect(rr.hwnd)==Rect(200,300,800,600))
                        return {'enqueue_ms':round(enqueue,3),'settled_ms':round((time.perf_counter()-start)*1000,3)}
                    check('slow application async placement',slow)
                    def hooks():
                        feed=EventFeed(pid=os.getpid()).start()
                        try:
                            # Creation occurs after subscription, on the same hidden desktop.
                            tiny=u.CreateWindowExW(0x80,'STATIC','',0x80000000,0,0,20,20,None,None,None,None)
                            u.ShowWindowAsync(tiny,4);native.place(ref,Rect(250,200,900,650))
                            u.PostMessageW(ref.hwnd,0x8002,0,0);native.minimise(ref);time.sleep(.1);native.restore(ref)
                            u.DestroyWindow(tiny);events=[];end=time.monotonic()+.5
                            while time.monotonic()<end:events+=feed.drain();time.sleep(.005)
                            kinds=sorted(set(e['type'] for e in events))
                            return {'count':len(events),'types':kinds,'delivery':'hook' if events else 'polling required',
                                'move_start_end':'fixture NotifyWinEvent; no physical input'}
                        finally:feed.close()
                    check('WinEvent hidden-desktop delivery',hooks)
                    def styling():
                        old={a:attribute(ref.hwnd,a) for a in (33,34)}
                        result=native.style(ref,0x0055AA,2);got={a:attribute(ref.hwnd,a) for a in (33,34)}
                        native.style(ref,old[34] if old[34] is not None else 0xFFFFFFFF,old[33] or 0)
                        reset={a:attribute(ref.hwnd,a) for a in (33,34)}
                        assert all(hr==0 for hr in result.values()),result
                        assert got[33]==2 and reset[33]==old[33],(got,reset,old)
                        if got[34] is not None:assert got[34]==0x55AA
                        return {'set_hresult':result,'read_back':got,'reset':reset,
                            'border_readback':'unsupported here; reset sent DWMWA_COLOR_DEFAULT' if got[34] is None else 'verified'}
                    check('DWM set/reset',styling)
                    def crash():
                        from watchdog import release_all
                        saved=native.placement(ref);info=out/'crash-target.json';info.write_text(json.dumps({'hwnd':ref.hwnd}))
                        path=out/('crash-lease-'+uuid.uuid4().hex[:8]+'.json');ready=Path(str(path)+'.ready')
                        startup=subprocess.STARTUPINFO();startup.lpDesktop='WinSta0\\'+full
                        p=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--crash-probe',str(info),str(path),'WinSta0\\'+full],
                            startupinfo=startup,creationflags=0x08000000,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                        try:
                            wait_for(ready.exists,15);manager=json.loads(ready.read_text())['manager']
                            print('L1 crash probe: armed; current rect '+str(rect(ref.hwnd).values()),flush=True)
                            wait_for(lambda:rect(ref.hwnd)==Rect(800,600,800,600))
                            assert identity(manager['pid'])==manager
                            handle=k.OpenProcess(1|0x1000,False,manager['pid']);assert handle
                            sig(k,'TerminateProcess',W.BOOL,W.HANDLE,W.UINT)
                            start=time.perf_counter();k.TerminateProcess(handle,99);k.CloseHandle(handle)
                            wait_for(lambda:json.loads(path.read_text()).get('released'),5)
                            wait_for(lambda:native.placement(ref)['normal']==saved['normal'])
                            duration=(time.perf_counter()-start)*1000
                            selfsame=release_all(path,native);assert selfsame==[]
                            return {'restore_ms':round(duration,3),'idempotent':True,'reason':json.loads(path.read_text())['reason']}
                        finally:
                            p.wait(timeout=6)
                            if p.returncode not in (0,99):
                                print('crash probe stderr: '+p.stderr.read(),flush=True)
                    check('watchdog after killing manager',crash)
                    def panic():
                        from watchdog import Lease,HOTKEY
                        lease=Lease(out/('panic-lease-'+uuid.uuid4().hex[:8]+'.json'),allowed=[ref.hwnd],desktop='WinSta0\\'+full)
                        ready=lease.acquire();saved=native.placement(ref);lease.save(ref);native.place(ref,Rect(600,400,700,500))
                        wait_for(lambda:rect(ref.hwnd)==Rect(600,400,700,500))
                        pid=ready['pid'];thread=W.DWORD()
                        # Enumerate the guard's threads; its main thread owns registration.
                        # Guard reports main thread id in ready (no SendInput on any desktop).
                        sig(u,'PostThreadMessageW',W.BOOL,W.DWORD,W.UINT,W.WPARAM,W.LPARAM)
                        assert u.PostThreadMessageW(ready['thread'],0x312,HOTKEY,0)
                        wait_for(lambda:json.loads(lease.path.read_text()).get('released'),5)
                        assert native.placement(ref)['normal']==saved['normal']
                        lease.process.wait(timeout=3)
                        return {'registered':True,'posted_WM_HOTKEY':True,'restored':True,'physical_chord':'not sent'}
                    check('panic hotkey dispatch',panic)
                    def heartbeat_timeout():
                        from watchdog import Lease
                        lease=Lease(out/('heartbeat-lease-'+uuid.uuid4().hex[:8]+'.json'),allowed=[ref.hwnd],desktop='WinSta0\\'+full)
                        lease.acquire();lease.save(ref);saved=native.placement(ref)
                        native.place(ref,Rect(500,300,800,500));wait_for(lambda:rect(ref.hwnd)==Rect(500,300,800,500))
                        start=time.perf_counter()
                        wait_for(lambda:json.loads(lease.path.read_text()).get('released'),4)
                        wait_for(lambda:native.placement(ref)['normal']==saved['normal'])
                        lease.process.wait(timeout=3)
                        return {'timeout_restore_ms':round((time.perf_counter()-start)*1000,3),
                            'reason':json.loads(lease.path.read_text())['reason'],'manager_still_alive':True}
                    check('three second heartbeat timeout',heartbeat_timeout)
                    def controller():
                        from manager import Manager
                        from watchdog import Lease
                        from engine import valid,solve
                        baseline={kind:native.placement(reference(hwnd)) for kind,hwnd in f.windows.items()}
                        boundary=Native(allowed=f.windows.values())
                        controller=Manager(boundary,out/('controller-'+uuid.uuid4().hex[:8]),allow_live=True,gate_fn=lambda:[],
                            lease_factory=lambda path:Lease(path,allowed=f.windows.values(),desktop='WinSta0\\'+full))
                        controller.ingest(boundary.windows(),Rect(0,0,3840,2100));controller.switch('live')
                        try:
                            minrow=next(r for r in controller.rows if r['ref'].hwnd==f.windows['minimum'])
                            window=controller.state.windows[minrow['key']];window.preferred=(240,160)
                            controller.state=solve(controller.state,{'type':'restore','key':window.key}).state
                            for _ in range(35):
                                controller.lease.heartbeat();controller.ingest(boundary.windows(),Rect(0,0,3840,2100));time.sleep(.05)
                            assert valid(controller.state)
                            assert controller.state.windows[minrow['key']].minimum[0]>240
                            actual_state=deepcopy(controller.state)
                            for row in boundary.windows():
                                actual_state.windows[row['key']].rect=Rect(*row['rect'])
                                actual_state.windows[row['key']].minimised=row['state']=='minimised'
                            assert valid(actual_state),'actual hidden placements overlap or leave work area'
                            learned={r['app']+':'+str(i):list(controller.state.windows[r['key']].minimum)
                                for i,r in enumerate(controller.rows) if controller.state.windows[r['key']].minimum!=(240,160)}
                            result={'planned_nonoverlap':True,'actual_nonoverlap':True,'windows':len(controller.rows),'learned':learned,
                                'unmovable':len([w for w in controller.state.windows.values() if not w.managed])}
                        finally:controller.switch('off')
                        for kind,hwnd in f.windows.items():
                            if kind=='self-resizer':continue  # this fixture deliberately overrides external placements
                            wait_for(lambda hwnd=hwnd,kind=kind:native.placement(reference(hwnd))['normal']==baseline[kind]['normal'])
                        return result
                    check('controller live loop on hidden windows and off release',controller)
                    def ghost_timing():
                        from ghost import Ghost
                        from engine import State,Window,solve
                        import statistics
                        ghost=Ghost();s=State(work=Rect(0,0,3000,1800),windows={str(i):Window(str(i),rect=Rect(16+i*500,16,480,800)) for i in range(5)})
                        timings=[];start=time.perf_counter()
                        try:
                            for i in range(120):
                                begin=time.perf_counter();plan=solve(s,{'type':'drag-move','key':'0','rect':[100+i,16,480,800]})
                                ghost.update([r for key,r in plan.placements.items() if key!='0'])
                                timings.append((time.perf_counter()-begin)*1000)
                                time.sleep(max(0,1/60-(time.perf_counter()-begin)))
                            elapsed=time.perf_counter()-start
                            return {'frames':120,'update_hz':round(120/elapsed,3),'median_ms':round(statistics.median(timings),3),
                                'p95_ms':round(sorted(timings)[113],3),'boundary':'hidden API updates; compositor presentation unmeasured',
                                'live_drag':'not attempted; slow fixture settles above one frame budget'}
                        finally:ghost.close()
                    check('ghost update timing',ghost_timing)
                except BaseException as exc:
                    import traceback
                    report['error']=traceback.format_exc();print(report['error'],flush=True)
                finally:u.CloseDesktop(joined)
            thread=threading.Thread(target=worker);thread.start();thread.join(60)
            assert not thread.is_alive(),'hidden proof timed out'
            if report.get('error'):raise AssertionError(report['error'])
    finally:
        report['alex_before']=before;report['alex_after']=sb.alex();report['alex_untouched']=before==report['alex_after']
        (out/'l1.json').write_text(json.dumps(report,indent=2));u.CloseDesktop(h)
    assert report['alex_after']['input desktop']==before['input desktop']
    print('L1 passed; alex: '+('untouched' if report['alex_untouched'] else 'concurrent input; see per-test snapshots'),flush=True)


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--crash-probe':crash_probe(*sys.argv[2:])
    else:run(HERE/'evidence')
