"""Headless Chrome evidence for the shared card adapter and real Python engine."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
import threading
import time

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src/desktop/kernel-desktop'))
sys.path.insert(0,str(ROOT/'src/agora'))
from kernel.tiling import preview
import widget_browser

SCRIPT=(ROOT/'src/text-desk/notation/desk-shell/carry-targets.js').read_text(encoding='utf-8')
HTML='''<!doctype html><style>
body{margin:0}article{width:200px;height:160px;background:#dae8dd;box-sizing:border-box;border:1px solid #819b89}
#source{position:absolute;left:0;top:0}#lane{position:absolute;left:300px;top:0;width:220px;height:600px}
</style><article id="source" data-carry="card">Carried card</article>
<section id="lane"><article id="other" data-carry="card">Neighbour</article></section>
<input id="focus" style="position:absolute;top:650px"><script>'''+SCRIPT+'''
const s=document.querySelector('#source'),lane=document.querySelector('#lane'),other=document.querySelector('#other');
const d=CarryTargets.drift(s);
document.querySelector('#focus').focus();
async function move(x){d.move(lane,{clientX:x,clientY:20,startX:50,startY:20});return await d.flush()}
</script>'''


class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        b=HTML.encode();self.send_response(200);self.send_header('Content-Length',str(len(b)))
        self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(b)
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        b=json.dumps(preview(body)).encode()
        self.send_response(200);self.send_header('Content-Length',str(len(b)))
        self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(b)


def run(out):
    out.mkdir(parents=True,exist_ok=True)
    # Browser's own disposable profile belongs to this task's scratch area.
    widget_browser.HERE=out
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with widget_browser.Browser(test_flags=('--enable-logging',
                '--log-file='+str(out/'chrome.log'))) as c:
            c.call('Emulation.setDeviceMetricsOverride',width=800,height=800,deviceScaleFactor=1,mobile=False)
            c.call('Page.navigate',url=f'http://127.0.0.1:{server.server_port}/')
            c.until("typeof d!=='undefined'")
            before=c.js('move(349)')
            assert not before['allowed']
            assert c.js('other.getBoundingClientRect().y')==0
            boundary=c.js('move(350)')
            assert not boundary['allowed'],boundary
            assert c.js('other.getBoundingClientRect().y')==0
            crossing=c.js('move(351)')
            assert crossing['allowed']
            time.sleep(.08)
            middle=c.js('other.getBoundingClientRect().y')
            assert 0<middle<160,middle
            time.sleep(.3)
            assert c.js('other.getBoundingClientRect().y')==160
            c.js('move(349)')
            time.sleep(.08)
            reverse=c.js('other.getBoundingClientRect().y')
            assert 0<reverse<160,reverse
            time.sleep(.3)
            assert c.js('other.getBoundingClientRect().y')==0
            assert c.js("document.activeElement.id")=='focus'
            c.js('Promise.all([move(360),move(340)])')
            time.sleep(.3)
            assert c.js('other.getBoundingClientRect().y')==0
            import base64
            (out/'card.png').write_bytes(base64.b64decode(c.call('Page.captureScreenshot',format='png')['data']))
            result={'checks':8,'middle_y':middle,'reverse_y':reverse,'focus_unchanged':True}
            (out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
            print('hidden card drop: 8 checks passed')
    finally:
        server.shutdown();server.server_close()


if __name__=='__main__':
    run(ROOT/'.tmp/hidden-card-drop')
