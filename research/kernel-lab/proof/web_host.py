"""One painter, many hosts: concurrent laptop/phone, headless Chrome, loopback only.

Imagined: Seabright neighbours and their message. Ran: numbered browser/HTTP
checks, screenshots and replay in an isolated disposable world. No live desktop.
"""
import argparse
import asyncio
import base64
import json
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

PROOF = Path(__file__).resolve().parent
LAB = PROOF.parent
sys.path[:0] = [str(LAB), str(LAB / 'tests')]
from kernel.kernel import Kernel
from kernel.door import serve
from kernel.painter import STATIC
from kernel import scratch
from test_skeleton import StandInEntry, post
from test_painter import FEED, quoted, walk
from hosts.web.layout import leaves
from shoot import CHROME


class World:
    def __init__(self):
        self.temp = scratch.TemporaryDirectory(prefix='web-host-')
        self.secret = secrets.token_hex(16)
        self.entry = StandInEntry(self.secret)
        self.k = Kernel(self.temp.name, {'tag': 'sb', 'name': 'Seabright',
            'steward': {'account': 'google:dana', 'name': 'Dana'},
            'invites_counted_by': 'kernel', 'invites': [{'code': 'neighbour', 'uses': 9}],
            'groups': [{'name': 'Council watch', 'open': True}]})
        self.srv, self.host = serve(self.k, self.entry.url, self.secret, 0, LAB)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = f'http://127.0.0.1:{self.srv.server_address[1]}'
        self.entry.kernel_url = self.url
        self.entry.sessions['dana'] = {'account': 'google:dana', 'method': 'google'}
        self.maya, self.maya_info = self.entry.sign_in('google:maya', 'Maya', invite='neighbour')
        self.luis, _ = self.entry.sign_in('google:luis', 'Luis', invite='neighbour')
        self.person = self.k.accounts['google:maya']
        council = FEED.replace('root : column, role sheet, of tag:post as p, each card',
            'root : column, role sheet\n  heading : text "Council watch · Neighbour updates"\n  updates : column, of tag:post as p, each card')
        for name, text in [('feed', FEED), ('council', council),
                           ('help', 'root : column, role sheet, of tag:help-topic as h, each topic\ntopic : text "$text"\n')]:
            self.do('dana', f'make kind=lens name={name} text={quoted(text)}')
        self.do('dana', 'make kind=help-topic text="Welcome to Seabright. Share news in Feed; follow our Council watch. Pane help explains arranging your view."')
        self.seed = self.do('dana', 'post Council meets Tuesday. What should we ask about the crossing?')['made'][0]
        self.private = self.do(self.maya, 'make kind=post sees=me text="Private draft: my crossing question"')['made'][0]
        self.do(self.maya, 'make kind=help-topic sees=me text="Private help: my own reminder"')
        self.k.dev_sessions = lambda: self.entry.sessions

    def do(self, token, line, saw=None, mode='do'):
        code, out = post(self.url + '/' + mode, {'line': line, **({'saw': saw} if saw is not None else {})}, token=token)
        assert code == 200 and out['ok'], out
        return out

    def layout(self, token):
        return self.do(token, 'panes', mode='see')['rows'][0]

    def get(self, path, token):
        req = urllib.request.Request(self.url + path, headers={'Authorization': 'Bearer ' + token})
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.load(response)

    def close(self):
        self.host.stop_all()
        for s in (self.srv, self.entry.srv):
            s.shutdown()
            s.server_close()
        self.temp.cleanup()


class CDP:
    def __init__(self, socket):
        self.socket, self.n = socket, 0

    async def call(self, method, **params):
        self.n += 1
        await self.socket.send(json.dumps({'id': self.n, 'method': method, 'params': params}))
        while True:
            msg = json.loads(await self.socket.recv())
            if msg.get('id') == self.n:
                if 'error' in msg:
                    raise RuntimeError(msg['error'])
                return msg.get('result', {})

    async def js(self, expr):
        out = await self.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if out.get('exceptionDetails'):
            raise RuntimeError(out['exceptionDetails'])
        return out.get('result', {}).get('value')

    async def until(self, expr):
        for _ in range(150):
            if await self.js(expr):
                return
            await asyncio.sleep(.1)
        raise AssertionError('Timed out: ' + expr)

    async def shot(self, path):
        result = await self.call('Page.captureScreenshot', format='png')
        path.write_bytes(base64.b64decode(result['data']))


async def browser_checks(w, port, browser_ws, out, check):
    import websockets
    sockets = []
    async with websockets.connect(browser_ws) as sock:
        browser = CDP(sock)

        async def page(token, width, path='/web/'):
            context = (await browser.call('Target.createBrowserContext'))['browserContextId']
            target = (await browser.call('Target.createTarget', url='about:blank', browserContextId=context))['targetId']
            s = await websockets.connect(f'ws://127.0.0.1:{port}/devtools/page/{target}', max_size=64*1024*1024, close_timeout=1)
            sockets.append(s)
            p = CDP(s)
            await p.call('Network.enable')
            await p.call('Network.setCookie', name='agora_session', value=token, url=w.url, httpOnly=True, sameSite='Lax')
            await p.call('Emulation.setDeviceMetricsOverride', width=width, height=900 if width > 600 else 844, deviceScaleFactor=1, mobile=width < 600)
            await p.call('Page.enable')
            await p.call('Page.navigate', url=w.url+path)
            if path == '/web/':
                await p.until("document.querySelectorAll('.pane').length===3")
                await p.until("[...document.querySelectorAll('iframe')].every(f=>f.contentDocument?.querySelector('#paint [data-key]'))")
            else:
                await p.until("!!document.querySelector('#paint [data-key]')")
            return p

        async def word(p, line):
            await p.js(f"document.querySelector('#line').value={json.dumps(line)}; document.querySelector('#words').requestSubmit()")
            await p.until('!busy')

        async def text(p, lens):
            return await p.js(f"document.querySelector('[data-lens={lens}] iframe').contentDocument.querySelector('#paint').innerText")

        try:
            laptop = await page(w.maya, 1440)
            phone = await page(w.maya, 390)
            other = await page(w.luis, 1440)
            check('Laptop opens three unchanged painter panes', await laptop.js("[...document.querySelectorAll('iframe')].map(f=>f.title).join(',')==='Feed,Council,Help'"), 'Feed, Council, Help at 1440px')
            check('Phone shows exactly one pane', await phone.js("[...document.querySelectorAll('.pane')].filter(p=>p.getBoundingClientRect().width>0).length===1"), '390px, the same three views available')
            untouched = w.layout(w.luis)['layout']
            await word(laptop, 'pane.move Feed to=Help')
            check('A word rearranges panes', leaves(w.layout(w.maya)['layout']['tree'])[0]['lens'] == 'help', 'pane.move Feed to=Help, admitted by the door')
            # Real mouse drag, through Chrome input, not a JS drop event.
            coords = await laptop.js("['help','council'].map(l=>{const r=document.querySelector(`[data-lens=${l}] .pane-head`).getBoundingClientRect();return {x:r.x+12,y:r.y+12}})")
            a, b = coords
            await laptop.call('Input.dispatchMouseEvent', type='mouseMoved', **a)
            await laptop.call('Input.dispatchMouseEvent', type='mousePressed', button='left', clickCount=1, **a)
            for step in range(1, 16):
                await laptop.call('Input.dispatchMouseEvent', type='mouseMoved', button='left', buttons=1,
                    x=a['x']+(b['x']-a['x'])*step/15, y=a['y']+(b['y']-a['y'])*step/15)
                await asyncio.sleep(.03)
            await laptop.call('Input.dispatchMouseEvent', type='mouseReleased', button='left', clickCount=1, **b)
            await laptop.until("document.querySelector('.pane').dataset.lens==='council'")
            check('A mouse drag rearranges panes by the same word', leaves(w.layout(w.maya)['layout']['tree'])[0]['lens'] == 'council', 'real Chrome mouse input: Help onto Council')
            check('Another neighbour retains their layout', w.layout(w.luis)['layout'] == untouched and await other.js("document.querySelector('.pane').dataset.lens==='feed'"), 'Luis has not moved')
            # Phone was open throughout. Switch to Council using actual touch input on its pane strip.
            await phone.call('Emulation.setTouchEmulationEnabled', enabled=True)
            rect = await phone.js("(()=>{const r=document.querySelector('#swipe').getBoundingClientRect();return {x:r.x+85,y:r.y+12}})()")
            # The small strip is a swipe handle: gestures may end beyond its hit box under pointer capture.
            await phone.call('Input.dispatchTouchEvent', type='touchStart', touchPoints=[dict(rect, radiusX=2, radiusY=2)])
            await phone.call('Input.dispatchTouchEvent', type='touchMove', touchPoints=[dict(x=rect['x']-90,y=rect['y'],radiusX=2,radiusY=2)])
            await phone.call('Input.dispatchTouchEvent', type='touchEnd', touchPoints=[])
            await phone.until("document.querySelector('.pane.active').dataset.lens==='council'")
            check('A touch swipe shows Council on the concurrent phone', await phone.js("document.querySelectorAll('.pane.active').length===1"), 'Chrome touch input, not synthetic DOM events')
            await laptop.js("document.querySelector('[data-lens=feed] .compose input').value='I can attend Council and ask about the crossing.'; document.querySelector('[data-lens=feed] .compose').requestSubmit()")
            await phone.until("document.querySelector('[data-lens=council] iframe').contentDocument.querySelector('#paint').innerText.includes('I can attend Council')")
            await laptop.until("document.querySelector('[data-lens=feed] iframe').contentDocument.querySelector('#paint').innerText.includes('I can attend Council')")
            post_id = next(t for t in w.k.things('post') if w.k.state.get(t, 'text', '').startswith('I can attend'))
            check('A Feed post arrives live in Council on the phone', w.k.state.get(post_id, 'made_by') == w.person, f'{post_id}, ordinary post as Maya; no reload')
            check('Who-sees filters every laptop and phone pane', all([('Private help' if l=='help' else 'Private draft') in await text(p,l) for p in (laptop,phone) for l in ('feed','council','help')]), 'Maya sees her own private post and help in all three panes on both hosts')
            check('Who-sees excludes private things in every other neighbour pane', all(['Private' not in await text(other,l) for l in ('feed','council','help')]),
                  'Luis cannot see Maya’s draft or private help')
            # Standalone desktop frame contract: same lens.html URL, same scenes, stable thing mapping.
            for lens in ('feed','council','help'):
                desktop = await page(w.maya, 900, f'/lens.html?lens={lens}&inspect=0')
                await desktop.until("document.querySelector('#paint').innerText.length>0")
                await laptop.until(f"document.querySelector('[data-lens={lens}] iframe').contentDocument.querySelector('#paint').innerText.length>0")
                direct = await desktop.js("[...document.querySelectorAll('#paint [data-key]')].map(n=>n.dataset.key)")
                embedded = await laptop.js(f"[...document.querySelector('[data-lens={lens}] iframe').contentDocument.querySelectorAll('#paint [data-key]')].map(n=>n.dataset.key)")
                check(f'{lens.title()} uses the desktop painter and identities', direct == embedded,
                      'same lens URL, exact painted node keys; native window not started')
            feed_scene = w.get('/api/scene?lens=feed&view=painter&text=1', w.maya)
            app = f'a{int(post_id[2:])*8}'
            check('Painted post maps to its one kernel thing', any(app in n.get('key','').split('/') for n in walk(feed_scene['scene'])), f'{post_id} -> {app}; shared data, no copies')
            check('Painter JavaScript is byte-for-byte unchanged', urllib.request.urlopen(w.url+'/lens.js').read() == (STATIC/'lens.js').read_bytes(), 'served source equals desk-shell/lens.js')
            layout = w.layout(w.maya)['layout']
            await laptop.call('Page.reload')
            await laptop.until("document.querySelector('.pane')?.dataset.lens==='council'")
            await laptop.until("[...document.querySelectorAll('iframe')].every(f=>f.contentDocument?.querySelector('#paint [data-key]'))")
            check('Reload keeps the personal tiling', w.layout(w.maya)['layout'] == layout, 'new document, stored tree unchanged')
            await laptop.js("document.querySelector('[data-lens=feed] .compose input').value='An unfinished neighbour update'; document.querySelector('[data-lens=feed] iframe').contentWindow.hostContinuity='same painter'")
            await word(laptop, 'pane.split Help lens=feed axis=column')
            await laptop.until("document.querySelectorAll('.pane').length===4")
            check('Rearranging preserves the existing painter and draft', await laptop.js("document.querySelector('[data-pane=p1] .compose input').value==='An unfinished neighbour update' && document.querySelector('[data-pane=p1] iframe').contentWindow.hostContinuity==='same painter'"), 'Chrome moveBefore keeps iframe state and host composer')
            await word(laptop, 'pane.close "Feed 2"')
            await laptop.until("document.querySelectorAll('.pane').length===3")
            check('Split and close keep the same underlying things', post_id in w.k.state.things, 'four panes, then three; post remains')
            await word(laptop, 'pane.resize Council ratio=60')
            check('A resize word persists personal proportions', w.layout(w.maya)['layout']['tree']['ratio']==60, '60 percent to the first column')
            await laptop.js("document.querySelector('[data-lens=feed] .compose input').value=''")
            await phone.until("document.querySelector('.pane.active').dataset.lens==='council'")
            await laptop.shot(out/'web-host-laptop.png')
            await phone.shot(out/'web-host-phone.png')
            check('Screenshots captured at both requested widths', await laptop.js('innerWidth') == 1440 and await phone.js('innerWidth') == 390, '1440×900 and 390×844 PNGs')
            replay = Kernel(w.temp.name)
            check('Facts replay preserves personal layouts and posts', replay.state.snapshot() == w.k.state.snapshot(), 'exact state comparison; no words re-executed')
        finally:
            await asyncio.gather(*(socket.close() for socket in sockets))


def run(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    checks = []
    def check(name, ok, detail):
        checks.append({'number': len(checks)+1, 'check': name, 'ok': bool(ok), 'detail': detail})
        print(f"{len(checks):02d} {'ok' if ok else 'FAIL'} {name} · {detail}", flush=True)
        assert ok, (name, detail)
    w = World()
    profile = scratch.mkdtemp(prefix='web-host-chrome-')
    proc = None
    try:
        exe = next(p for p in CHROME if Path(p).exists())
        proc = subprocess.Popen([exe, '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
            '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=0', f'--user-data-dir={profile}', 'about:blank'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=0x08000000 if sys.platform=='win32' else 0)
        active = Path(profile)/'DevToolsActivePort'
        for _ in range(100):
            if active.exists() and len(active.read_text().splitlines()) >= 2:
                break
            time.sleep(.1)
        port, path = active.read_text().splitlines()[:2]
        asyncio.run(browser_checks(w, port, f'ws://127.0.0.1:{port}{path}', out, check))
    finally:
        (out/'web-host.json').write_text(json.dumps({'checks': checks}, indent=2, ensure_ascii=False), encoding='utf-8')
        if proc:
            if sys.platform == 'win32':
                subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'], capture_output=True)
            else:
                proc.terminate()
            proc.wait(timeout=15)
        w.close()
        target = Path(profile).resolve()
        assert target.parent == Path(tempfile.gettempdir()).resolve() and target.name.startswith('web-host-chrome-')
        shutil.rmtree(target, ignore_errors=True)
    print(f'{len(checks)} checks passed', flush=True)
    return checks


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', default=str(PROOF/'evidence'))
    run(ap.parse_args().out)
