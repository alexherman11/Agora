"""Short, guarded, never-shown WebView2 proof of the native iframe boundary."""
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import unittest
from urllib.parse import quote

HERE=Path(__file__).resolve().parent


def child(nested=False):
    from test_kdesk import Desk,quoted
    import webview
    import widget_guard
    widget_guard.install()
    d=Desk();canary=[];requests=[]
    base=d.srv.RequestHandlerClass.do_GET
    def get(handler):
        if 'native-escape' in handler.path:requests.append(handler.path)
        return base(handler)
    d.srv.RequestHandlerClass.do_GET=get
    target=d.say('post Native widget target')['made'][0]
    code='''await agora.ready;const r={};
try{await fetch('/health');r.fetch=false}catch{r.fetch=true}
try{document.cookie;r.cookie=false}catch{r.cookie=true}
try{localStorage.x='x';r.storage=false}catch{r.storage=true}
try{top.location='https://example.invalid';r.top=false}catch{r.top=true}
try{await agora.do('pin TARGET');r.pin=false}catch(e){r.pin=e.message.includes('grant')}
r.pywebview=typeof window.pywebview==='undefined';
try{window.chrome?.webview?.postMessage(['probe','[]','escape'])}catch{}
try{location.href='BASE/native-escape';r.navigation='returned'}catch(e){r.navigation=e.name+': '+e.message}
agora.describe(JSON.stringify(r));'''.replace('TARGET',target).replace('BASE',d.url)
    m=d.say('make kind=widget name=native-hostile code='+quoted(code))['made'][0]
    d.say('look '+m);d.say(f'widget {m} grants="'+('window.bar' if nested else 'window.surface')+' describe" surface='+('top' if nested else 'window'))
    class Api:
        def probe(self):canary.append(True)
    path='/desk/widget.html?widget='+m
    if nested:
        d.say('make kind=lens name=widget-native-proof text="root : column"')
        path='/desk/bar.html?lens=widget-native-proof'
    url=d.url+'/dev/signin?token='+d.entry.token('alex')+'&next='+quote(path,safe='')
    win=webview.create_window('Guarded hidden widget proof',url,hidden=True,width=800,height=500,js_api=Api())
    result={}
    def inspect():
        try:
            desc=d.wait(lambda:d.k.state.get(m,'description'),20)
            result.update(json.loads(desc))
            result.pop('navigation',None)
            end=time.monotonic()+5
            while not win.native.browser._agora_widget_denials and time.monotonic()<end:time.sleep(.1)
            result['native_message']=not canary
            result['self_navigation']=bool(win.native.browser._agora_widget_denials) and not requests
            win.evaluate_js('window.pywebview.api.probe()')
            end=time.monotonic()+3
            while not canary and time.monotonic()<end:time.sleep(.1)
            result['native_positive_control']=len(canary)==1
            result['hidden']=not bool(win.native.Visible)
        except Exception as e:result['error']=repr(e)
        finally:win.destroy()
    threading.Thread(target=inspect,daemon=True).start()
    try:webview.start(gui='edgechromium',private_mode=True)
    finally:d.close()
    print('NATIVE_WIDGET '+json.dumps(result),flush=True)
    print(f"Native {'nested bar' if nested else 'window'} widget sandbox: {sum(v is True for v in result.values())}/10 checks passed",flush=True)
    return 0 if len(result)==10 and all(v is True for v in result.values()) else 1


class NativeWidgetTest(unittest.TestCase):
    def run_child(self,nested=False):
        out=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--child']+(['--slot'] if nested else []),capture_output=True,text=True,
                           encoding='utf-8',timeout=45,creationflags=0x08000000)
        print(out.stdout,flush=True)
        self.assertEqual(0,out.returncode,out.stderr+'\n'+out.stdout)

    def test_actual_hidden_webview2_sandbox(self):self.run_child()

    def test_nested_bar_sandbox(self):self.run_child(True)


if __name__=='__main__':
    if '--child' in sys.argv:sys.exit(child('--slot' in sys.argv))
    unittest.main()
