"""Offscreen widget renderer. Stdlib CDP transport, based on hidden_evidence's
existing transport. The browser draws JavaScript; a native alpha surface displays
its pixels. No browser window appears. Profile state is disposable.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import tempfile
import time
import urllib.request
from urllib.parse import urlsplit, quote




HERE = Path(__file__).resolve().parent


class CDP:
    def __init__(self, url):
        p = urlsplit(url)
        self.authority = p.netloc
        self.s = socket.create_connection((p.hostname, p.port), timeout=20)
        key = base64.b64encode(os.urandom(16)).decode()
        request = f'GET {p.path} HTTP/1.1\r\nHost: {p.netloc}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n'
        self.s.sendall(request.encode())
        response = b''
        while not response.endswith(b'\r\n\r\n'):
            response += self.s.recv(1)
        assert b'101' in response.splitlines()[0], response
        assert base64.b64encode(hashlib.sha1((key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()) in response
        self.seq = 0
        self.responses = {}
        self.on_event = lambda event: None

    def read(self, n):
        out = b''
        while len(out) < n:
            b = self.s.recv(n-len(out))
            if not b:
                raise EOFError('CDP closed')
            out += b
        return out

    def receive(self):
        first, second = self.read(2)
        size = second & 127
        if size == 126:
            size = struct.unpack('!H', self.read(2))[0]
        elif size == 127:
            size = struct.unpack('!Q', self.read(8))[0]
        mask = self.read(4) if second & 128 else None
        payload = self.read(size)
        if mask:
            payload = bytes(x ^ mask[i % 4] for i, x in enumerate(payload))
        return json.loads(payload)

    def send(self, method, **params):
        self.seq += 1
        session = params.pop('_session', None)
        payload = json.dumps(dict(id=self.seq, method=method, params=params,
                                  **({'sessionId':session} if session else {}))).encode()
        mask = os.urandom(4)
        n = len(payload)
        header = bytes((0x81, 0x80 | (n if n < 126 else 126 if n < 65536 else 127)))
        if n >= 126:
            header += struct.pack('!H' if n < 65536 else '!Q', n)
        self.s.sendall(header + mask + bytes(x ^ mask[i % 4] for i, x in enumerate(payload)))
        return self.seq

    def call(self, method, **params):
        seq = self.send(method, **params)
        while True:
            r = self.responses.pop(seq, None) or self.receive()
            if r.get('id') == seq:
                if 'error' in r:
                    raise RuntimeError(r['error'])
                return r.get('result')
            if r.get('id'):
                self.responses[r['id']] = r
            else:
                self.on_event(r)

    def js(self, expression):
        r = self.call('Runtime.evaluate', expression=expression, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'):
            raise RuntimeError(r['exceptionDetails'])
        return r.get('result', {}).get('value')

    def until(self, expression, timeout=20):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if self.js(expression):
                return
            time.sleep(.1)
        raise AssertionError('browser wait: ' + expression + '\n' + str(self.js('({state:document.readyState,text:document.body.innerText,images:[...document.images].map(i=>({src:i.src,complete:i.complete,width:i.naturalWidth}))})')))


class Browser:
    def __init__(self, url=None, host_key=None, test_flags=()):
        self.test_flags = list(test_flags)
        self.allowed_origin = (urlsplit(url).scheme + '://' + urlsplit(url).netloc) if url else None
        self.host_key = host_key or os.environ.get('AGORA_WIDGET_HOST_KEY','')

    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='edge-kdesk-', dir=HERE / 'state',ignore_cleanup_errors=True)
        chrome=Path('C:/Program Files/Google/Chrome/Application/chrome.exe')
        executable=str(chrome) if chrome.is_file() else r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
        private='--incognito' if chrome.is_file() else '--inprivate'
        self.process = subprocess.Popen([executable,
            '--headless=new', private, '--disable-gpu', '--no-first-run', '--no-default-browser-check',
            '--remote-debugging-port=0', '--remote-allow-origins=*', '--disable-background-networking',
            '--user-data-dir=' + self.tmp.name, *self.test_flags, 'about:blank'], stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, creationflags=0x08000000)
        active = Path(self.tmp.name) / 'DevToolsActivePort'
        end = time.monotonic() + 20
        port=None
        while time.monotonic() < end:
            try:
                lines=active.read_text().splitlines()
                if lines and lines[0].isdigit():port=lines[0];break
            except (FileNotFoundError,PermissionError):pass
            time.sleep(.1)
        if port is None:
            self.process.terminate();self.process.wait(timeout=5)
            self.tmp.cleanup()
            raise RuntimeError('offscreen browser did not publish its local debugging port')
        pages = json.loads(urllib.request.urlopen(f'http://127.0.0.1:{port}/json/list').read())
        anchor = CDP(next(p['webSocketDebuggerUrl'] for p in pages if p['type'] == 'page'))
        target = anchor.call('Target.createTarget',url='about:blank',background=True)['targetId']
        pages = json.loads(urllib.request.urlopen(f'http://127.0.0.1:{port}/json/list').read())
        self.cdp = CDP(next(p['webSocketDebuggerUrl'] for p in pages if p['id'] == target))
        anchor.s.close()
        self.cdp.call('Page.enable')
        # The shared lens HTML still names a Google font. Desktop evidence and
        # desktop runtime use local system type; no external asset is necessary.
        self.cdp.call('Network.enable')
        self.cdp.call('Network.setBlockedURLs', urls=['https://fonts.googleapis.com/*', 'https://fonts.gstatic.com/*'])
        if self.allowed_origin:
            c = self.cdp
            main = c.call('Page.getFrameTree')['frameTree']['frame']['id']
            def firewall(event):
                if event.get('method') != 'Fetch.requestPaused':
                    return
                p = event['params']
                url = urlsplit(p['request']['url'])
                local = url.scheme + '://' + url.netloc == self.allowed_origin
                path_ok = url.path in ('/desk/widget.html', '/desk/kd.css', '/desk/kd.js', '/desk/widget-host.js', '/dev/signin') or url.path.startswith('/desk/widget/')
                if p.get('frameId') == main and local and path_ok:
                    headers=dict(p['request'].get('headers') or {})
                    if url.path.startswith('/desk/widget/'):
                        headers['X-Agora-Widget-Host']=self.host_key
                    c.send('Fetch.continueRequest', requestId=p['requestId'],headers=[{'name':k,'value':str(v)} for k,v in headers.items()])
                else:
                    c.send('Fetch.failRequest', requestId=p['requestId'], errorReason='BlockedByClient')
            c.on_event = firewall
            c.call('Fetch.enable', patterns=[{'urlPattern':'*'}])
        return self.cdp

    def __exit__(self, *exc):
        try:
            self.cdp.call('Browser.close')
        except Exception:
            pass
        self.cdp.s.close()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            self.process.wait(timeout=5)
        for _ in range(10):
            try:
                self.tmp.cleanup()
                break
            except PermissionError:
                time.sleep(.5)


