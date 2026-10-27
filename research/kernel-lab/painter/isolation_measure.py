"""Never-shown WebView2 measurements; disposable server/profile, bounded child.

Reports travel over HTTP, so a frozen renderer cannot block the measuring host.
The launcher checks the screen gate before creating even hidden native windows.
"""
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = Path(__file__).resolve().parent
DESKTOP = HERE.parents[1] / 'window-lab/kernel-desktop'
sys.path.insert(0, str(DESKTOP))


def descendants(root):
    from gaming_gate import Process
    from ctypes import wintypes as w
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.CreateToolhelp32Snapshot.restype=w.HANDLE
    k.Process32FirstW.argtypes=[w.HANDLE,ctypes.POINTER(Process)]
    k.Process32NextW.argtypes=k.Process32FirstW.argtypes
    k.CloseHandle.argtypes=[w.HANDLE]
    h=k.CreateToolhelp32Snapshot(2,0);p=Process();p.size=ctypes.sizeof(p);rows=[]
    try:
        more=k.Process32FirstW(h,ctypes.byref(p))
        while more:
            rows.append((int(p.pid),int(p.parent),p.exe));more=k.Process32NextW(h,ctypes.byref(p))
    finally:k.CloseHandle(h)
    owned={root}
    while True:
        new=owned|{pid for pid,parent,_ in rows if parent in owned}
        if new==owned:break
        owned=new
    return [(pid,name) for pid,_,name in rows if pid in owned and pid!=root]


def process_memory(pid):
    from ctypes import wintypes as w
    class Counters(ctypes.Structure):
        _fields_=[('cb',w.DWORD),('faults',w.DWORD)]+[(name,ctypes.c_size_t) for name in ('peak_ws','ws','peak_paged','paged','peak_nonpaged','nonpaged','pagefile','peak_pagefile','private')]
    k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.restype=w.HANDLE
    k.CloseHandle.argtypes=[w.HANDLE]
    api=ctypes.WinDLL('psapi');api.GetProcessMemoryInfo.argtypes=[w.HANDLE,ctypes.c_void_p,w.DWORD]
    h=k.OpenProcess(0x1000|0x10,False,pid)
    try:
        m=Counters();m.cb=ctypes.sizeof(m)
        if h and api.GetProcessMemoryInfo(h,ctypes.byref(m),m.cb):return dict(pid=pid,private_bytes=m.private,working_set=m.ws)
    finally:
        if h:k.CloseHandle(h)


def child(case):
    from gaming_gate import assert_clear
    assert_clear()
    import webview
    import widget_guard
    widget_guard.install()
    reports = {}
    counts = {}
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(self.path)
            q = parse_qs(parsed.query)
            if parsed.path == '/beat':
                with lock: counts[q['who'][0]] = counts.get(q['who'][0], 0) + 1
                body = b'ok'
            elif parsed.path == '/report':
                with lock:
                    reports[q['who'][0]] = json.loads(q['value'][0])
                    counts[q['who'][0]]=counts.get(q['who'][0],0)+1
                body = b'ok'
            else:
                body = page(q.get('case', [case])[0], self.server.server_port).encode()
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            try: self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError): pass

    def page(which, port):
        base = f'http://127.0.0.1:{port}'
        script = """
const base=BASE;
const report=(who,value)=>fetch(base+'/report?who='+who+'&value='+encodeURIComponent(JSON.stringify(value)));
const beat=who=>{let n=0;setInterval(()=>{document.body.dataset.tick=++n;document.body.style.background=n%2?'#efefdf':'#dfefff';fetch(base+'/beat?who='+who)},50)};
report('ready-'+WHICH,{ua:navigator.userAgent});beat(WHICH);
if(WHICH==='workers'){
  for(const who of ['good','bad']){const source='const base='+JSON.stringify(base)+';setInterval(()=>fetch(base+"/beat?who='+who+'"),50);'+(who==='bad'?'setTimeout(()=>{fetch(base+"/beat?who=hang-start");while(true){}},1800);':'');new Worker(URL.createObjectURL(new Blob([source],{type:'text/javascript'})))}
}else if(WHICH==='frames'){
  for(const who of ['good','bad']){const f=document.createElement('iframe');f.sandbox='allow-scripts';f.srcdoc='<body><script>const base='+JSON.stringify(base)+';setInterval(()=>{document.body.textContent=Date.now();fetch(base+"/beat?who='+who+'")},50);'+(who==='bad'?'setTimeout(()=>{fetch(base+"/beat?who=hang-start");while(true){}},1800);':'')+'<\\/script>';document.body.append(f)}
}else if(WHICH==='loop'){setTimeout(()=>{fetch(base+'/beat?who=hang-start');while(true){}},1800)}
else if(WHICH.startsWith('cost')){
  const start=performance.now(),n=+WHICH.slice(4);let ready=0;
  if(!n)report(WHICH,{startup_ms:performance.now()-start,n});
  addEventListener('message',()=>{if(++ready===n)report(WHICH,{startup_ms:performance.now()-start,n})});
  for(let i=0;i<n;i++){const f=document.createElement('iframe');f.sandbox='allow-scripts';f.srcdoc='<body><button>Component '+i+'</button><script>parent.postMessage("ready","*")<\\/script>';document.body.append(f)}
}
""".replace('BASE', json.dumps(base)).replace('WHICH', json.dumps(which))
        return '<!doctype html><body><script>' + script + '</script>'

    servers = [ThreadingHTTPServer(('127.0.0.1', 0), Handler) for _ in range(2 if case in ('windows','crash') else 1)]
    for srv in servers: threading.Thread(target=srv.serve_forever, daemon=True).start()
    windows = []
    for i, srv in enumerate(servers):
        which = ('loop' if i == 0 else 'other') if case == 'windows' else 'crash'+str(i) if case=='crash' else case
        windows.append(webview.create_window('Hidden isolation measurement', f'http://127.0.0.1:{srv.server_port}/?case={which}', hidden=True, width=800, height=600))
    result = dict(case=case)

    def memory():
        # Only this disposable child's descendants, never resident WebViews.
        # Include all runtime processes; label this aggregate honestly. Process
        # counts/PIDs come from the WebView environment below, on its UI thread.
        renderers = [m for pid,name in descendants(os.getpid()) if name.lower()=='msedgewebview2.exe' and (m:=process_memory(pid))]
        from System import Action
        native=[];done=threading.Event()
        def inspect():
            try:
                core=windows[0].native.browser.webview.CoreWebView2
                result['runtime_version']=str(core.Environment.BrowserVersionString)
                native.extend(dict(pid=int(p.ProcessId),kind=str(p.Kind)) for p in core.Environment.GetProcessInfos())
            finally:done.set()
        windows[0].native.BeginInvoke(Action(inspect));done.wait(2)
        return dict(processes=native, runtime_process_memory=renderers, private_bytes=sum(p['private_bytes'] for p in renderers),
                    working_set=sum(p['working_set'] for p in renderers))

    def measure():
        try:
            end = time.monotonic()+25
            while len([k for k in reports if k.startswith('ready-')]) < len(windows) and time.monotonic()<end: time.sleep(.05)
            result['hidden'] = all(not bool(w.native.Visible) for w in windows)
            result['ready'] = dict(reports)
            if case.startswith('cost'):
                while case not in reports and time.monotonic()<end: time.sleep(.05)
                time.sleep(.5)
                result.update(reports.get(case, {})); result.update(memory())
            elif case=='crash':
                time.sleep(1);before=dict(counts)
                from System import Action
                def crash():windows[0].native.browser.webview.CoreWebView2.CallDevToolsProtocolMethodAsync('Page.crash','{}')
                windows[0].native.BeginInvoke(Action(crash))
                end=time.monotonic()+12
                while counts.get('ready-crash0',0)<2 and time.monotonic()<end:time.sleep(.1)
                time.sleep(2)
                result['before_crash']=before;result['after_crash']=dict(counts);result.update(memory())
            else:
                while not counts.get('hang-start') and time.monotonic()<end:time.sleep(.05)
                time.sleep(.25); before = dict(counts)
                time.sleep(3.0); result['before_hang'] = before
                result['after_hang'] = dict(counts); result.update(memory())
            print('WEBVIEW2_MEASURE '+json.dumps(result), flush=True)
        except Exception as e:
            print('WEBVIEW2_MEASURE '+json.dumps(dict(case=case,error=repr(e))),flush=True)
        finally:
            # A hung script also blocks graceful close; the launcher terminates
            # this disposable process tree after receiving the measurements.
            os._exit(0)

    threading.Thread(target=measure,daemon=True).start()
    webview.start(gui='edgechromium', private_mode=True)


def main():
    from gaming_gate import assert_clear
    results=[]
    for case in (('workers',) if '--workers' in sys.argv else ('crash',) if '--crash' in sys.argv else ('cost0','cost5','cost20','cost100','frames','windows')):
        assert_clear()
        p=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--child',case],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',creationflags=0x08000000)
        # Record descendants before child exits, then clean up only that tree.
        owned={}
        end=time.monotonic()+45
        while p.poll() is None and time.monotonic()<end:
            for pid,name in descendants(p.pid):owned[pid]=name
            time.sleep(.1)
        if p.poll() is None: p.kill()
        out,err=p.communicate(timeout=10)
        from ctypes import wintypes as w
        kernel=ctypes.WinDLL('kernel32');kernel.OpenProcess.restype=w.HANDLE
        kernel.CloseHandle.argtypes=[w.HANDLE];kernel.TerminateProcess.argtypes=[w.HANDLE,w.UINT]
        for pid in reversed(list(owned)):
            handle=kernel.OpenProcess(1,False,pid)
            if handle:
                kernel.TerminateProcess(handle,0);kernel.CloseHandle(handle)
        lines=[l for l in out.splitlines() if l.startswith('WEBVIEW2_MEASURE ')]
        r=json.loads(lines[-1].split(' ',1)[1]) if lines else dict(case=case,error=err[-2500:])
        results.append(r);print(json.dumps(r),flush=True)
    filename='isolation-worker-measurement.json' if '--workers' in sys.argv else 'isolation-crash-measurement.json' if '--crash' in sys.argv else 'isolation-measurements.json'
    (HERE/'evidence'/filename).write_text(json.dumps(results,indent=2),encoding='utf-8')


if __name__=='__main__':
    if '--child' in sys.argv:child(sys.argv[-1])
    else:main()
