"""Hidden, isolated Chrome evidence. Never controls Alex's browser or focus."""
import asyncio
import base64
import json
import subprocess
import time
import urllib.request
from pathlib import Path

import websockets

HERE = Path(__file__).resolve().parent


class Page:
    def __init__(self, ws):
        self.ws, self.n = ws, 0

    async def call(self, method, **params):
        self.n += 1
        await self.ws.send(json.dumps(dict(id=self.n, method=method, params=params)))
        while True:
            msg = json.loads(await self.ws.recv())
            if msg.get('id') == self.n:
                if 'error' in msg:
                    raise RuntimeError(msg['error'])
                return msg.get('result', {})

    async def js(self, expression):
        out = await self.call('Runtime.evaluate', expression=expression, returnByValue=True, awaitPromise=True)
        if out.get('exceptionDetails'):
            raise RuntimeError(out['exceptionDetails'])
        return out.get('result', {}).get('value')

    async def until(self, expression):
        for _ in range(160):
            if await self.js(expression):
                return
            await asyncio.sleep(.1)
        raise AssertionError('Page timed out: ' + expression + '\n' + str(await self.js('document.body.innerText')))

    async def shot(self, path):
        out = await self.call('Page.captureScreenshot', format='png', captureBeyondViewport=False)
        Path(path).write_bytes(base64.b64decode(out['data']))

    async def point(self, selector, x=.5, y=.5):
        return await self.js('(()=>{let b=document.querySelector(' + json.dumps(selector) +
            ').getBoundingClientRect();return {x:b.x+b.width*' + str(x) + ',y:b.y+b.height*' + str(y) + '}})()')

    async def start_drag(self, selector, receiver):
        a = await self.point(selector, .5, .15)
        # Tall lanes extend below the viewport; release near their visible top.
        b = await self.point(receiver, .5, .07)
        await self.call('Input.dispatchMouseEvent', type='mouseMoved', **a)
        await self.call('Input.dispatchMouseEvent', type='mousePressed', button='left', clickCount=1, **a)
        for i in range(1, 9):
            await self.call('Input.dispatchMouseEvent', type='mouseMoved', buttons=1,
                x=a['x']+(b['x']-a['x'])*i/8, y=a['y']+(b['y']-a['y'])*i/8)
        return b

    async def release(self, point):
        await self.call('Input.dispatchMouseEvent', type='mouseReleased', button='left', clickCount=1, **point)


class Browser:
    def __init__(self):
        self.pages = []
        profile = HERE / 'evidence' / ('chrome-' + str(time.time_ns()))
        exe = next(p for p in (r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe') if Path(p).exists())
        self.proc = subprocess.Popen([exe, '--headless=new', '--disable-gpu', '--no-first-run',
            '--no-default-browser-check', '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=0',
            '--disk-cache-size=1', '--user-data-dir=' + str(profile), 'about:blank'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=0x08000000)
        active = profile / 'DevToolsActivePort'
        for _ in range(100):
            if active.exists() and len(active.read_text().splitlines()) >= 2:
                break
            time.sleep(.1)
        self.port, path = active.read_text().splitlines()[:2]
        self.address = f'ws://127.0.0.1:{self.port}{path}'
        self.profile = profile

    async def page(self, door, path='/lens.html?lens=taskboard&inspect=0'):
        if not hasattr(self, 'control'):
            self.control = Page(await websockets.connect(self.address, max_size=64*1024*1024))
        ctx = (await self.control.call('Target.createBrowserContext'))['browserContextId']
        target = (await self.control.call('Target.createTarget', url='about:blank', browserContextId=ctx))['targetId']
        p = Page(await websockets.connect(f'ws://127.0.0.1:{self.port}/devtools/page/{target}', max_size=64*1024*1024))
        self.pages.append(p)
        await p.call('Network.enable')
        await p.call('Network.setCookie', name='agora_session', value=door.token, url=door.url, httpOnly=True, sameSite='Lax')
        await p.call('Emulation.setDeviceMetricsOverride', width=1600, height=1000, deviceScaleFactor=1, mobile=False)
        await p.call('Page.enable')
        await p.call('Page.navigate', url=door.url+path)
        try:
            await p.until("!!document.querySelector('#paint [data-carry]')")
        except AssertionError:
            await p.shot(HERE / 'evidence/browser-failure.png')
            print('Browser diagnostics:', await p.js("JSON.stringify({url:location.href,html:document.documentElement.outerHTML.slice(-5000)})"), flush=True)
            print('Scene diagnostics:', door.request('/api/scene?lens=taskboard&view=painter&text=1'), flush=True)
            raise
        # Observe actual requests and receipts without replacing their data or admission.
        await p.js("window.receipts=[];window.sent=[];window.originalFetch=fetch;window.fetch=async(...args)=>{let r=await originalFetch(...args);if(args[0]==='/api/do'){sent.push(JSON.parse(args[1].body));receipts.push(await r.clone().json())}return r}")
        return p

    async def close(self):
        for p in self.pages:
            await p.ws.close()
        if hasattr(self, 'control'):
            await self.control.call('Browser.close')
            await self.control.ws.close()
        self.proc.wait(timeout=15)
        # Remove only our disposable profile, confined to this app's evidence directory.
        import shutil
        target = self.profile.resolve()
        assert target.parent == (HERE / 'evidence').resolve() and target.name.startswith('chrome-')
        shutil.rmtree(target, ignore_errors=True)
