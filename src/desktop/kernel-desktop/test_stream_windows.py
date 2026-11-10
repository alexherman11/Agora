"""Hidden real Chromium regression: fifteen windows and a subsecond Lines reply.

Run with pinned Python: python -m unittest test_stream_windows -v
Uses headless Edge and a disposable world; never touches the visible desktop.
"""
import json
import time
import unittest
import urllib.request
from urllib.parse import quote

from hidden_evidence import Browser, CDP
from test_kdesk import Desk, FEED, quoted


def window_url(base, token, wid, path):
    redirect = '/desk/window-origin?win=' + quote(wid) + '&next=' + quote(path, safe='')
    return base + '/dev/signin?token=' + token + '&next=' + quote(redirect, safe='')


def connect_target(c, target):
    pages = json.loads(urllib.request.urlopen('http://' + c.authority + '/json/list', timeout=5).read())
    return CDP(next(p['webSocketDebuggerUrl'] for p in pages if p['id'] == target))


def lines_help(c):
    result = c.js("""new Promise((resolve,reject)=>{
      const start=performance.now();
      const observer=new MutationObserver(()=>{
        const answer=document.querySelector('#log .ans');
        if(answer){observer.disconnect();clearTimeout(timer);
          resolve({ms:performance.now()-start,text:answer.textContent});}
      });
      observer.observe(document.getElementById('log'),{childList:true,subtree:true});
      const timer=setTimeout(()=>{observer.disconnect();reject(Error('Lines help timed out'));},3000);
      document.getElementById('line').value='help';
      document.getElementById('f').requestSubmit();
    })""")
    assert 'window.open' in result['text'], result
    assert result['ms'] < 1000, result
    return result['ms']


class StreamWindowsTest(unittest.TestCase):
    def test_fifteen_windows_with_native_streams_and_lines(self):
        d = Desk()
        try:
            self.assertTrue(d.say('make kind=lens name=feed text=' + quoted(FEED))['ok'])
            self.assertTrue(d.say('post Fifteen window regression')['ok'])
            ids = []
            for n in range(15):
                before = {w['id'] for w in d.windows()}
                view = 'lines' if n == 14 else 'feed' if n % 2 else 'help'
                self.assertTrue(d.say('window.open ' + view + ' new=yes')['ok'])
                w = d.wait(lambda: next((w for w in d.windows() if w['id'] not in before), None))
                path = ('/desk/frame.html?lens=feed&win=' if view == 'feed'
                        else '/desk/' + view + '.html?win=') + w['id']
                ids.append((w['id'], path))
            with Browser() as browser:
                clients, targets = [], []
                try:
                    for wid, path in ids:
                        target = browser.call('Target.createTarget', url='about:blank', background=True)['targetId']
                        targets.append(target)
                        c = connect_target(browser, target)
                        clients.append(c)
                        c.call('Page.enable')
                        # Reproduce the embedded-runtime boundary: no SharedWorker.
                        c.call('Page.addScriptToEvaluateOnNewDocument', source='window.SharedWorker=undefined;')
                        c.call('Page.navigate', url=window_url(d.url, d.entry.token('alex'), wid, path))
                        c.until("location.pathname.startsWith('/desk/') && typeof KD !== 'undefined'")
                        if 'frame.html' in path:
                            c.until("document.querySelector('iframe')?.contentDocument?.querySelector('#paint')?.textContent.includes('Fifteen window regression')")
                    origins = [c.js('location.origin') for c in clients]
                    self.assertEqual(15, len(set(origins)))
                    # Native streams, including iframe streams, must actually be OPEN.
                    for c in clients:
                        c.js("window.probe=new EventSource('/door/stream')")
                        c.until('probe.readyState===EventSource.OPEN')
                        self.assertTrue(c.js('EventSource.toString().includes("[native code]")'))
                    ms = lines_help(clients[-1])
                    # A live event reaches every isolated pool; sharing the kernel
                    # must not accidentally mean isolated worlds.
                    for c in clients:
                        c.js("window.gotWorld=false;probe.addEventListener('world',()=>gotWorld=true)")
                    self.assertTrue(d.say('post All windows receive the same world')['ok'])
                    for c in clients:
                        c.until('gotWorld')
                    print(f'15 hidden Chromium windows; native SSE on 15 origins; Lines help: {ms:.1f} ms (<1000 ms); world delivery: 15/15', flush=True)
                finally:
                    for c in clients:
                        c.s.close()
                    for target in targets:
                        browser.call('Target.closeTarget', targetId=target)
        finally:
            d.close()


if __name__ == '__main__':
    unittest.main()
