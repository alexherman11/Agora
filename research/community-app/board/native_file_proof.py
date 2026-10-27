"""Never-shown WebView2 proof of the authenticated file/Blob/download boundary."""
import json
import os
import socket
import sys
import threading
import time
import urllib.request
from pathlib import Path
from urllib.parse import quote as urlquote

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path[:0]=[str(HERE),str(ROOT/'research/kernel-lab'),str(ROOT/'research/window-lab/kernel-desktop')]
from test_kdesk import Desk
from painter.install import taskboard,Q
from painter.browser import Page
from widget_browser import CDP
from install import install,modules
from protocol import line
from proof import fixtures


def run():
    from gaming_gate import assert_clear
    assert_clear()
    import webview,widget_guard
    widget_guard.install()
    d=Desk();door=taskboard.Door(d.url,d.entry.token('alex'));result={};downloads=[]
    try:
        for spec in modules():
            door.say(line('module '+spec['name'],run=json.dumps(spec['run']),publishes=spec['publishes'],grants=spec['grants']))
            assert d.host.wait_offered(d.k.module_named(spec['name']))
        ids=install(door.say,lambda cmd:door.request('/see',dict(line=cmd)))
        event=door.say(line('board.post',post_kind='event',text='Native file proof',title='Neighbourhood walk',start='2027-01-01T12:00:00Z',seats='20',**{'in':ids['channels']['Meetings & events']}))['made'][0]
        request=urllib.request.Request(d.url+'/upload',data=fixtures()['camera.txt'],headers={'Authorization':'Bearer '+door.token,'X-Filename':'camera.jpg','Content-Type':'application/octet-stream'})
        with urllib.request.urlopen(request) as response:photo=json.load(response)['made'][0]
        folder=Path(d.dir)/'downloads';folder.mkdir()
        def save(browser,args,name):
            downloads.append(name);args.ResultFilePath=str(folder/name);return True
        widget_guard.choose_download=save
        code="""await agora.ready;
const status=document.createElement('p');status.textContent='Loading';document.body.append(status);
const blob=(await agora.file(PHOTO,'thumbnail')).blob;
const image=document.createElement('img');image.id='photo';image.alt='Cleaned native photo';image.src=URL.createObjectURL(blob);document.body.append(image);
for(const [id,label,action] of [['direct','Direct frame download',()=>{const a=document.createElement('a');a.href=image.src;a.download='frame-escape.png';a.click()}],['file','Download photo',()=>agora.download(PHOTO)],['calendar','Download calendar',()=>agora.downloadReading(CALENDAR)]]){const button=document.createElement('button');button.id=id;button.textContent=label;button.onclick=()=>Promise.resolve(action()).then(()=>{status.textContent=id+' done'},e=>{status.textContent=e.message});document.body.append(button)}
image.onload=()=>{status.textContent='Photo ready'};
""".replace('PHOTO',json.dumps(photo)).replace('CALENDAR',json.dumps('board.calendar '+event))
        widget=door.say('make kind=widget name=native-file-proof code='+Q(code))['made'][0]
        door.say('look '+widget);door.say('widget '+widget+' grants="window.surface file-read board.calendar"')
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        webview.settings['REMOTE_DEBUGGING_PORT']=port
        url=d.url+'/dev/signin?token='+door.token+'&next='+urlquote('/desk/widget.html?widget='+widget,safe='')
        win=webview.create_window('Never-shown file transport proof',url,hidden=True,width=900,height=650)
        def inspect():
            page=None
            try:
                assert win.events.loaded.wait(25)
                end=time.monotonic()+15;target=None
                while time.monotonic()<end:
                    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json/list') as response:targets=json.load(response)
                    target=next((t for t in targets if t['type']=='page' and t['url'].startswith(d.url+'/desk/widget.html')),None)
                    if target:break
                    time.sleep(.1)
                assert target,'Native debugging target unavailable'
                page=Page.__new__(Page);page.c=CDP(target['webSocketDebuggerUrl']);page.session=None;page.errors=[]
                page.c.call('Page.enable');page.c.call('Emulation.setFocusEmulationEnabled',enabled=True)
                page.until('document.querySelector("#photo")?.complete && document.querySelector("#photo").naturalWidth>0',20)
                result['native_blob_decoded']=True
                result['thumbnail_bound']=page.js('document.querySelector("#photo").naturalWidth<=360')
                result['no_component_cookie']=page.js('(()=>{try{document.cookie;return false}catch{return true}})()')
                result['connect_none']=page.js('fetch("/health").then(()=>false,()=>true)')
                def click(selector):
                    point=page.point(selector)
                    page.c.call('Input.dispatchMouseEvent',type='mouseMoved',**point)
                    page.c.call('Input.dispatchMouseEvent',type='mousePressed',button='left',clickCount=1,**point)
                    page.c.call('Input.dispatchMouseEvent',type='mouseReleased',button='left',clickCount=1,**point)
                click('#direct');time.sleep(.3);page.c.js('0')
                result['opaque_download_denied']=not downloads
                click('#file')
                end=time.monotonic()+15
                while time.monotonic()<end and not list(folder.glob('*.png')):page.c.js('0');time.sleep(.05)
                from PIL import Image
                files=list(folder.glob('*.png'))
                if not files:raise AssertionError('Trusted native file download did not finish: '+json.dumps(dict(text=page.js('document.body.innerText'),pending=list(win.native.browser._agora_widget_downloads),downloads=downloads,top=page.c.js('location.href'))))
                with Image.open(files[0]) as image:result['cleaned_download']=not bool(image.getexif()) and image.format=='PNG'
                click('#calendar')
                end=time.monotonic()+15
                while time.monotonic()<end and not list(folder.glob('*.ics')):page.c.js('0');time.sleep(.05)
                result['native_calendar_download']=bool(list(folder.glob('*.ics'))) and b'BEGIN:VCALENDAR' in next(folder.glob('*.ics')).read_bytes()
                result['global_download_setting_unchanged']=webview.settings['ALLOW_DOWNLOADS'] is False
                result['hidden']=not bool(win.native.Visible)
            except Exception as exc:result['error']=repr(exc)
            finally:
                if page:page.c.s.close()
                win.destroy()
        threading.Thread(target=inspect,daemon=True).start()
        webview.start(gui='edgechromium',private_mode=True)
    finally:d.close()
    (HERE/'evidence/ui/native-files.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('NATIVE FILE '+json.dumps(result,sort_keys=True),flush=True)
    count=sum(value is True for value in result.values())
    print(f'NATIVE FILE: {count}/9 checks passed; hidden=True',flush=True)
    return 0 if len(result)==9 and count==9 else 1


if __name__=='__main__':raise SystemExit(run())
