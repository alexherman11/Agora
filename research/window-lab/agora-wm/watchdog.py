"""EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
(people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.

Separate recovery process, single durable lease writer, 3-second deadline.
JSON lines over private inherited pipes. No registry, shell state or injections.
Saved HWNDs carry a per-lease property, guarding even HWND reuse within a process.
"""
import argparse
import ctypes as C
from ctypes import wintypes as W
import json
import os
from pathlib import Path
import queue
import secrets
import socket
import subprocess
import sys
import threading
import time
from win32_host import Native, WindowRef, identity, same, attribute, u, k, dpi_aware

PROP='Agora.WM.Lease'
HOTKEY=0x4A72


def write(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp')
    with tmp.open('w',encoding='utf-8') as f:
        json.dump(data,f,indent=2);f.flush();os.fsync(f.fileno())
    # Windows readers/AV can briefly deny replacement despite a complete temp.
    # Keep the old lease intact and retry the same durable bytes, never truncate.
    for attempt in range(30):
        try:os.replace(tmp,path);break
        except PermissionError:
            if attempt==29:raise
            time.sleep(.01)


def release_all(path,native=None):
    """Idempotent, identity+cookie checked. Retain failures for explicit recovery."""
    path=Path(path);native=native or Native(mutating=True)
    data=json.loads(path.read_text(encoding='utf-8'));out=[]
    for entry in data.get('windows',[]):
        if entry.get('released'):continue
        ref=WindowRef(**entry['ref'])
        if not same(ref) or u.GetPropW(ref.hwnd,PROP)!=entry['cookie']:
            entry['released']=True;entry['outcome']='identity/cookie no longer matches; untouched'
        else:
            try:
                if entry.get('restore_geometry',True):native.restore_placement(ref,entry['placement'])
                old=entry['dwm'];native.style(ref,old.get('34',0xFFFFFFFF),old.get('33',0))
                u.RemovePropW(ref.hwnd,PROP)
                entry['released']=True;entry['outcome']='restored'
            except (OSError,PermissionError) as exc:
                entry['outcome']=type(exc).__name__
        out.append({'app':Path(ref.process['exe']).stem,'outcome':entry['outcome']})
        write(path,data)  # progress survives a second crash
    data['released']=all(x.get('released') for x in data.get('windows',[]));write(path,data)
    return out


def watch(path,owner,allowed=None):
    path=Path(path)
    if path.exists():
        old=json.loads(path.read_text())
        if not old.get('released'):raise RuntimeError('unreleased lease exists; recover before acquiring')
    native=Native(mutating=True,allowed=allowed)
    data={'version':1,'owner':owner,'guard':identity(os.getpid()),'released':False,'windows':[]}
    write(path,data)
    hotkey=bool(u.RegisterHotKey(None,HOTKEY,0x4003,8))
    if not hotkey:
        data['released']=True;write(path,data)
        print(json.dumps({'ready':False,'reason':'panic hotkey unavailable','error':C.get_last_error()}),flush=True)
        return
    commands=queue.Queue()
    def reader():
        for line in sys.stdin:
            try:commands.put(json.loads(line))
            except ValueError:commands.put({'op':'release'})
        commands.put({'op':'release'})
    threading.Thread(target=reader,daemon=True).start()
    print(json.dumps({'ready':True,'pid':os.getpid(),'thread':k.GetCurrentThreadId()}),flush=True)
    deadline=time.monotonic()+3;reason='off'
    try:
        while True:
            msg=W.MSG()
            if u.PeekMessageW(C.byref(msg),None,0x312,0x312,1) and msg.wParam==HOTKEY:
                reason='panic';break
            if time.monotonic()>deadline:reason='heartbeat expired';break
            if identity(owner['pid'])!=owner:reason='manager ended';break
            try:cmd=commands.get(timeout=.025)
            except queue.Empty:continue
            op=cmd.get('op')
            if op=='heartbeat':deadline=time.monotonic()+3;continue
            if op=='release':break
            if op=='save':
                try:
                    ref=WindowRef(**cmd['ref']);native.check(ref)
                    entry=next((v for v in data['windows'] if v['ref']==ref.record() and not v.get('released')),None)
                    if entry is None:
                        if u.GetPropW(ref.hwnd,PROP):raise RuntimeError('another WM lease owns this window')
                        entry={'ref':ref.record(),'placement':native.placement(ref),
                            'dwm':{str(a):attribute(ref.hwnd,a) for a in (33,34)},'cookie':secrets.randbits(30)+1,
                            'restore_geometry':cmd.get('geometry',True)}
                        entry['dwm']={a:v for a,v in entry['dwm'].items() if v is not None}
                        data['windows'].append(entry);write(path,data)
                        if not u.SetPropW(ref.hwnd,PROP,entry['cookie']):raise OSError('cannot mark window')
                    elif cmd.get('geometry',True) and not entry.get('restore_geometry',True):
                        # A border-only lease upgrades at the first actual move, saving
                        # where the person has placed it since the border was applied.
                        entry['placement']=native.placement(ref);entry['restore_geometry']=True;write(path,data)
                    print(json.dumps({'saved':True,'key':ref.key}),flush=True)
                except Exception as exc:
                    print(json.dumps({'saved':False,'reason':str(exc)}),flush=True)
    finally:
        data['reason']=reason;write(path,data)
        try:release_all(path,native)
        except BaseException as exc:
            failed=json.loads(path.read_text());failed['release_error']=repr(exc);write(path,failed)
            raise
        finally:u.UnregisterHotKey(None,HOTKEY)


class Lease:
    def __init__(self,path,allowed=None,desktop=None):
        self.path=Path(path);self.lock=threading.Lock();self.process=None;self.allowed=allowed;self.desktop=desktop

    def acquire(self):
        owner=identity(os.getpid());argv=[sys.executable,str(Path(__file__).resolve()),'--watch',str(self.path),'--owner',json.dumps(owner)]
        if self.allowed is not None:argv+=['--allowed',json.dumps(list(self.allowed))]
        if self.desktop:argv+=['--desktop',self.desktop]
        # WMI starts outside the manager's job tree, like taskbar_guard. A plain
        # subprocess died with the venv launcher's job in the crash proof.
        server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(10)
        token=secrets.token_hex(24);argv+=['--connect',str(server.getsockname()[1]),'--token',token]
        pyw=Path(sys.executable).with_name('pythonw.exe')
        if pyw.exists():argv[0]=str(pyw)
        command=subprocess.list2cmdline(argv)
        ps="$r=Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine='"+command.replace("'","''")+"'}; if($r.ReturnValue -ne 0){exit 1}"
        try:
            subprocess.run(['powershell','-NoProfile','-Command',ps],check=True,capture_output=True,timeout=15,creationflags=0x08000000)
            conn,_=server.accept();conn.settimeout(3)
            reader=conn.makefile('r',encoding='utf-8');writer=conn.makefile('w',encoding='utf-8')
            if reader.readline().strip()!=token:conn.close();raise RuntimeError('guard channel authentication failed')
            self.process=GuardProcess(conn,reader,writer)
            ready=self._read(3);self.process.pid=ready.get('pid');self.process.owner=identity(self.process.pid) if self.process.pid else None
        finally:server.close()
        if not ready.get('ready'):raise RuntimeError(f'guard not armed: {ready}')
        return ready

    def _read(self,timeout):
        replies=queue.Queue()
        threading.Thread(target=lambda:replies.put(self.process.stdout.readline()),daemon=True).start()
        try:
            line=replies.get(timeout=timeout)
            if not line:raise RuntimeError('guard ended before acknowledgement')
            return json.loads(line)
        except queue.Empty:raise TimeoutError('guard acknowledgement timed out')

    def _send(self,msg):
        if not self.process or self.process.poll() is not None:raise RuntimeError('guard is not running')
        self.process.stdin.write(json.dumps(msg)+'\n');self.process.stdin.flush()

    def save(self,ref,geometry=True):
        with self.lock:
            self._send({'op':'save','ref':ref.record(),'geometry':geometry});reply=self._read(1)
            if not reply.get('saved'):raise RuntimeError(f'guard refused save: {reply}')

    def heartbeat(self):
        with self.lock:self._send({'op':'heartbeat'})

    def release(self):
        if self.process and self.process.poll() is None:
            with self.lock:self._send({'op':'release'})
            self.process.wait(timeout=2)
        elif self.path.exists():
            # Mutual recovery: if the independent guard itself died, the
            # still-running manager can perform the same identity-checked off.
            release_all(self.path,Native(mutating=True,allowed=self.allowed))


class GuardProcess:
    def __init__(self,conn,reader,writer):
        self.conn=conn;self.stdout=reader;self.stdin=writer;self.pid=None;self.owner=None
    def poll(self):
        return None if self.pid and identity(self.pid)==self.owner else 0
    def wait(self,timeout=3):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            if self.poll() is not None:
                self.conn.close();return 0
            time.sleep(.025)
        raise TimeoutError('guard did not exit')


if __name__=='__main__':
    dpi_aware()
    p=argparse.ArgumentParser();p.add_argument('--watch',type=Path);p.add_argument('--owner');p.add_argument('--allowed')
    p.add_argument('--release-all',type=Path);p.add_argument('--desktop');p.add_argument('--connect',type=int);p.add_argument('--token');a=p.parse_args()
    if a.connect:
        conn=socket.create_connection(('127.0.0.1',a.connect),timeout=10);conn.settimeout(None)
        sys.stdin=conn.makefile('r',encoding='utf-8');sys.stdout=conn.makefile('w',encoding='utf-8')
        print(a.token,flush=True)
    if a.desktop:
        if 'agora-sandbox-' not in a.desktop:raise SystemExit('test desktop must be a sandbox')
        sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
        import sandbox_window
        sandbox_window.join(a.desktop.split('agora-sandbox-',1)[1])
    if a.release_all:
        data=json.loads(a.release_all.read_text())
        if identity(data.get('owner',{}).get('pid',0))==data.get('owner') and not data.get('released'):
            raise SystemExit('manager still alive; use wm.mode off')
        print(json.dumps(release_all(a.release_all)))
    elif a.watch:watch(a.watch,json.loads(a.owner),json.loads(a.allowed) if a.allowed else None)
