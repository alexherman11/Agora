"""Render the real pages/lenses in headless Edge, against a fresh headless world.

No visible windows, no live world writes, no shell changes. Minimal stdlib CDP
transport avoids installing browser automation packages. Also exercises real clicks.
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

from test_kdesk import Desk
from restyle import install

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

    def call(self, method, **params):
        self.seq += 1
        payload = json.dumps(dict(id=self.seq, method=method, params=params)).encode()
        mask = os.urandom(4)
        n = len(payload)
        header = bytes((0x81, 0x80 | (n if n < 126 else 126 if n < 65536 else 127)))
        if n >= 126:
            header += struct.pack('!H' if n < 65536 else '!Q', n)
        self.s.sendall(header + mask + bytes(x ^ mask[i % 4] for i, x in enumerate(payload)))
        while True:
            r = self.receive()
            if r.get('id') == self.seq:
                if 'error' in r:
                    raise RuntimeError(r['error'])
                return r.get('result')

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
    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='edge-kdesk-', dir=HERE / 'state')
        self.process = subprocess.Popen([r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
            '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
            '--remote-debugging-port=0', '--remote-allow-origins=*', '--disable-background-networking',
            '--user-data-dir=' + self.tmp.name, 'about:blank'], stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, creationflags=0x08000000)
        active = Path(self.tmp.name) / 'DevToolsActivePort'
        end = time.monotonic() + 20
        while not active.exists() and time.monotonic() < end:
            time.sleep(.1)
        port = active.read_text().splitlines()[0]
        pages = json.loads(urllib.request.urlopen(f'http://127.0.0.1:{port}/json/list').read())
        self.cdp = CDP(next(p['webSocketDebuggerUrl'] for p in pages if p['type'] == 'page'))
        self.cdp.call('Page.enable')
        # The shared lens HTML still names a Google font. Desktop evidence and
        # desktop runtime use local system type; no external asset is necessary.
        self.cdp.call('Network.enable')
        self.cdp.call('Network.setBlockedURLs', urls=['https://fonts.googleapis.com/*', 'https://fonts.gstatic.com/*'])
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
        for _ in range(10):
            try:
                self.tmp.cleanup()
                break
            except PermissionError:
                c.call('Runtime.evaluate', expression='new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))', awaitPromise=True)
                time.sleep(.5)


def main():
    evidence = HERE / 'evidence'
    evidence.mkdir(exist_ok=True)
    d = Desk()
    try:
        install(d.entry.token('claude'), d.srv.server_address[1])
        for raw in (HERE / 'lenses' / 'bars.lines').read_text(encoding='utf-8').splitlines():
            if raw and not raw.startswith('#'):
                assert d.say(raw)['ok'], raw
        for line in ('make kind=button bar=taskbar label=Feed does="window.open feed"',
                     'make kind=button bar=taskbar label=Help does="window.open help"',
                     'make kind=button bar=taskbar label=Wave does="guy.say hi Alex!"',
                     'post A little more room to think. The desktop brings your tools together, with the same words underneath.',
                     'post The neighbourhood picnic is on Sunday. Bring something to share, and a question for the table.',
                     'window.open feed', 'window.open help', 'window.open lines'):
            assert d.say(line)['ok'], line
        with Browser() as c:
            def visit(path, w, h, ready):
                c.call('Emulation.setDeviceMetricsOverride', width=w, height=h, deviceScaleFactor=1, mobile=False)
                url = d.url + '/dev/signin?token=' + d.entry.token('alex') + '&next=' + quote(path, safe='')
                c.call('Page.navigate', url=url)
                c.until('location.pathname === ' + json.dumps(path.split('?')[0]) + ' && document.readyState !== "loading" && ' + ready)
                time.sleep(.3)
            def shot(name):
                c.until('[...document.images].every(i=>i.complete && i.naturalWidth>0)')
                assert c.js('[...document.querySelectorAll(".strip button")].every(b=>{const r=b.getBoundingClientRect();return r.width>0&&r.left>=0&&r.right<=innerWidth;})'), 'window controls outside the viewport'
                # Edge's software compositor can return a stale tile immediately
                # after a viewport/navigation change. Flush a capture, then keep
                # the next settled frame; no pixels or page content are edited.
                c.call('Page.captureScreenshot',format='png',captureBeyondViewport=False,fromSurface=True)
                c.call('Runtime.evaluate',expression='new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))',awaitPromise=True)
                time.sleep(.2)
                data = c.call('Page.captureScreenshot', format='png', captureBeyondViewport=False, fromSurface=True)['data']
                (evidence / name).write_bytes(base64.b64decode(data))
            visit('/desk/bar.html?lens=topbar', 2560, 40, '!!document.querySelector("iframe")?.contentDocument?.querySelector("[data-tip]")')
            shot('bars-v2-top.png')
            # Native task rows in a hidden world are empty by contract. Supply a fixture
            # through the same UI functions so executable icons/layout can be inspected.
            visit('/desk/taskbar.html',2560,44,'document.querySelectorAll("#pins button").length===3 && document.querySelectorAll("#tray button").length===2')
            import native_shell
            tasks = native_shell.windows()
            fixture = [dict(name=x['program'], icon=x['icon']) for x in tasks[:12]]
            c.js('document.getElementById("wins").append(...' + json.dumps(fixture) + '.map(w=>chip(w.name,w.icon,"window.start","running")));fit();true')
            shot('bars-v2-bottom.png')
            # These real clicks are headless word calls: they never open Windows Start.
            c.js('document.getElementById("start").click();true')
            d.wait(lambda: any(r.get('words', '').startswith('window.start') for r in d.k.log.records))
            c.js('[...document.querySelectorAll("#pins button")].find(b=>b.title==="Wave").click();true')
            d.wait(lambda: 'hi Alex!' in d.say('status guy')['text'])
            added=d.say('make kind=widget bar=taskbar side=right shows=cpu icon=cpu label=CPU order=5')
            assert added['ok']
            c.until('[...document.querySelectorAll("#tray button")].some(b=>b.title.startsWith("CPU:"))')
            d.say('forget '+added['made'][0])
            for view in ('feed','help','lines','thing'):
                window = d.window(view)
                if view == 'feed':
                    path = '/desk/frame.html?lens=feed&name=Feed&win=' + window['id']
                    ready = '!!document.querySelector("iframe")?.contentDocument?.querySelector("[data-key]")'
                elif view == 'thing':
                    post = d.say('rows post')['rows'][0]
                    assert d.say('window.open thing '+post['id'])['ok']
                    thing=d.wait(lambda:d.window('thing'))
                    path = '/desk/thing.html?target=' + post['id']+'&win='+thing['id']
                    ready = '!!document.getElementById("aspects")?.textContent'
                else:
                    path = '/desk/' + view + '.html?win=' + window['id']
                    ready = 'typeof KD!=="undefined"'
                visit(path, 820, 800, ready)
                if view == 'help':
                    c.until('document.querySelectorAll(".word").length>10')
                    c.js('document.getElementById("filter").value="window";document.getElementById("filter").dispatchEvent(new Event("input"));true')
                    c.js('[...document.querySelectorAll(".word")].find(x=>x.textContent.includes("window.open")).click();true')
                if view == 'lines':
                    c.js('say("window.list");true')
                    c.until('document.querySelector(".ans")!==null')
                time.sleep(.3)
                c.until('[...document.images].every(i=>i.complete && i.naturalWidth>0)')
                shot('tiles-v2-' + view + '.png')
                if view == 'feed':
                    c.js('document.querySelector("iframe").contentDocument.querySelectorAll("[data-tip]")[0].click();true')
                    d.wait(lambda: any(p.get('likes') == 1 for p in d.say('rows post')['rows']))
                    c.js('document.querySelector("iframe").contentDocument.querySelectorAll("[data-tip]")[1].click();true')
                    d.wait(lambda: any(p.get('pinned') for p in d.say('rows post')['rows']))
                    c.js('document.querySelector("iframe").contentDocument.querySelectorAll("[data-tip]")[2].click();true')
                    d.wait(lambda: bool(d.say('rows pin')['rows']))
            visit('/desk/taskbar.html',480,44,'document.querySelectorAll("#pins button").length>=3')
            c.js('document.getElementById("wins").replaceChildren(...Array.from({length:80},(_,i)=>chip("Window "+i,"icons/app-window.svg","window.start","running")));fit();true')
            assert c.js('document.body.scrollWidth <= innerWidth'), str(c.js('({width:innerWidth,scroll:document.body.scrollWidth,parts:[...document.body.children].map(e=>({id:e.id,cls:e.className,width:e.getBoundingClientRect().width,x:e.getBoundingClientRect().x}))})'))
            c.js('[...document.querySelectorAll("button")].find(b=>b.getAttribute("aria-label")==="All running windows").click();true')
            d.wait(lambda: d.window('tasks'))
            visit('/desk/tasks.html?win='+d.window('tasks')['id'],820,800,'document.querySelectorAll(".task").length>0')
            c.until('[...document.images].every(i=>i.complete && i.naturalWidth>0)')
            shot('tiles-v2-tasks.png')
            extra = []
            try:
                for _ in range(8):
                    target = c.call('Target.createTarget', url=d.url+'/desk/help.html')['targetId']
                    pages = json.loads(urllib.request.urlopen('http://' + c.authority + '/json/list').read())
                    tab = CDP(next(p['webSocketDebuggerUrl'] for p in pages if p['id'] == target))
                    extra.append((target,tab))
                    tab.until('document.querySelectorAll(".word").length>10 && [...document.images].every(i=>i.complete&&i.naturalWidth>0)')
                    assert tab.js('EventSource.name === "DesktopStream"')
                    tab.js('window.received=0;window.probeStream=new EventSource("/door/stream");probeStream.addEventListener("world",()=>received++);true')
                d.say('post stream delivery probe')
                for _,tab in extra:
                    tab.until('received>0')
            finally:
                for target,tab in extra:
                    tab.s.close()
                    c.call('Target.closeTarget', targetId=target)
            from kd_guy import art
            art.picture('stand',1,'hi Alex!',False).save(evidence / 'tiles-v2-wave.png')
            print('Hidden browser: Start, Wave, Help search, Lines, Like, Pin, Keep in dock, 80-window overflow, 8 concurrent pages/streams: OK; 8 images saved.')
    finally:
        d.close()


if __name__ == '__main__':
    main()
