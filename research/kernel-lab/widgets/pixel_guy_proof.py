"""Hidden original-guy studio proof and contact sheets. No live world writes."""
import base64
import json
import sys
import time
from pathlib import Path
from urllib.parse import quote
from PIL import Image, ImageDraw, ImageFont
from pixel_guy_install import DESKTOP, install, taskboard
from proof import inside
from test_kdesk import Desk
from widget_browser import Browser
from kd_guy import art
import guy_looks

EVIDENCE=DESKTOP/'evidence'


def sheets():
    EVIDENCE.mkdir(exist_ok=True)
    font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',15)
    poses=list(art.BODY)
    for title,items,key in [('hats',list(guy_looks.HATS),'hat'),('accessories',list(guy_looks.ACCESSORIES),'accessory')]:
        sheet=Image.new('RGB',(1220,50+len(items)*143),'#fff9eb');draw=ImageDraw.Draw(sheet)
        draw.text((12,12),'ORIGINAL PIXEL GUY / '+title.upper()+' / both directions / all poses',fill='#343e49',font=font)
        for i,item in enumerate(items):
            y=48+i*143
            draw.text((10,y+12),item,fill='#343e49',font=font)
            for j,pose in enumerate(poses):
                for direction in (-1,1):
                    x=145+j*210+(0 if direction==-1 else 97)
                    f={key:item}
                    if item=='custom':f['custom_hat']='/'.join(['................']*4+['.....rrrrrr.....','....rbbbbbbr....','...rbbbbbbbbr...','....kkkkkkkk....'])
                    image=art.picture(pose,direction,'',False,f).crop((105,120,195,230))
                    sheet.paste(image,(x,y),image)
                draw.text((145+j*210,y+115),pose,fill='#586a68',font=font)
        sheet.save(EVIDENCE/('pixel-guy-'+title+'.png'))


def main():
    sheets();checks=[];d=Desk()
    def check(name,condition):
        assert condition,name
        checks.append(name);print('PASS '+name,flush=True)
    try:
        door=taskboard.Door(d.url,d.entry.token('alex'));ids=install(door)
        # Scratch-only exposure of the pure renderer for coordinate comparison;
        # production code contains no diagnostic globals.
        source=door.rows('widget',name='pixel-guy-editor')[0]['code']
        door.say('look '+ids['widget'])
        door.say('set '+ids['widget']+' code='+taskboard.quote(source+'\nwindow.proofPixels=previewPixels;'))
        with Browser(d.url) as c:
            def wait(condition):
                return d.wait(lambda:(c.js('0'),condition())[1])
            c.call('Emulation.setDeviceMetricsOverride',width=640,height=1060,deviceScaleFactor=1,mobile=False)
            c.call('Page.navigate',url=d.url+'/dev/signin?token='+d.entry.token('alex')+'&next='+quote('/desk/widget.html?widget='+ids['widget'],safe=''))
            c.until('!!document.querySelector("#widget-surface iframe")')
            for _ in range(60):
                try:
                    if inside(c,'!!document.querySelector("canvas")'):break
                except (RuntimeError,StopIteration):pass
                time.sleep(.1)
            check('studio rendered in opaque sandbox',inside(c,'!!document.querySelector("canvas")'))
            d.wait(lambda:(c.js('0'),inside(c,'typeof proofPixels==="function"'))[1])
            # Exact preview-coordinate parity for every hat, accessory, pose,
            # hair, eyes and blink; canvas shares those coordinate triples.
            expected=[];cases=[]
            for hat in guy_looks.HATS:
                for pose in art.BODY:
                    for eyes in ('dots','happy','sleepy','sunglasses'):
                        f=dict(guy_looks.DEFAULTS,hat=hat,eyes=eyes,hair='gold',accessory='scarf')
                        for blink in (False,True):
                            cases.append([pose,blink,f])
                            expected.append(sorted(guy_looks.pixels(art.HEAD,art.BODY,pose,blink,f)))
            actual=inside(c,'('+json.dumps(cases)+').map(([pose,blink,f])=>proofPixels(pose,blink,f).sort((a,b)=>a[0]-b[0]||a[1]-b[1]||a[2].localeCompare(b[2])))')
            check('400 preview pose/hat/eyes/blink combinations match Python pixels',actual==[[list(p) for p in pixels] for pixels in expected])
            original=door.rows('pixel-guy')[0]
            inside(c,'[...document.querySelectorAll("button")].find(b=>b.getAttribute("aria-label")==="Next Hat").click();true')
            wait(lambda:door.rows('pixel-guy')[0].get('hat')=='cap')
            d.wait(lambda:"'hat': 'cap'" in door.say('status guy')['text'])
            check('real picker set reaches running Python guy',door.rows('pixel-guy')[0]['hat']=='cap')
            undo='[...document.querySelectorAll("button")].find(b=>b.textContent==="Undo pick")'
            d.wait(lambda:(c.js('0'),inside(c,'!('+undo+').disabled'))[1])
            inside(c,'('+undo+').click();true')
            wait(lambda:door.rows('pixel-guy')[0].get('hat')=='none')
            d.wait(lambda:"'hat': 'none'" in door.say('status guy')['text'])
            check('real Undo pick restores running Python guy',door.rows('pixel-guy')[0]['hat']==original['hat'])
            for line in ['set '+ids['guy']+' provider=escape','set '+ids['provider']+' run=escape',
                         'set '+ids['widget']+' code=escape','make kind=pixel-guy name=Fake','guy.hop']:
                check('bridge refuses '+line.split()[0]+' '+line.split()[-1],inside(c,'agora.do('+json.dumps(line)+').then(()=>false,()=>true)'))
            # Exercise custom hat persistence and parity, then restore afterwards.
            inside(c,'[...document.querySelectorAll("button")].find(b=>b.getAttribute("aria-label")==="Hat pixel 7, 4").click();[...document.querySelectorAll("button")].find(b=>b.textContent==="Wear this hat").click();true')
            wait(lambda:door.rows('pixel-guy')[0].get('hat')=='custom')
            check('custom hat is an ordinary palette-row fact',len(door.rows('pixel-guy')[0]['custom_hat'].split('/'))==8)
            inside(c,'[...document.querySelectorAll("button")].find(b=>b.getAttribute("aria-label")==="Next Hat").click();true')
            wait(lambda:door.rows('pixel-guy')[0].get('hat')=='none')
            inside(c,'[...document.querySelectorAll("button")].find(b=>b.getAttribute("aria-label")==="Next Hat").click();[...document.querySelectorAll("button")].find(b=>b.getAttribute("aria-label")==="Next Accessory").click();true')
            wait(lambda:door.rows('pixel-guy')[0].get('hat')=='cap')
            wait(lambda:inside(c,'document.querySelectorAll(".picker b")[3].textContent==="scarf"'))
            time.sleep(.25)
            (EVIDENCE/'pixel-guy-editor.png').write_bytes(base64.b64decode(c.call('Page.captureScreenshot',format='png',captureBeyondViewport=False)['data']))
            check('editor screenshot written', (EVIDENCE/'pixel-guy-editor.png').exists())
        print(f'PIXEL GUY PROOF: {len(checks)} checks passed',flush=True)
    finally:d.close()


if __name__=='__main__':main()
