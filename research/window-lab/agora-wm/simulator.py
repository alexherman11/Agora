"""JSON replay: {state:{work,gap_inner,gap_outer,when_full,reflow}, events:[...]}.
Run simulator.py replay.json output.png. Each output is a contact sheet of steps.
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from engine import State, Rect, solve


def render(s,path,label='',width=960):
    scale=width/s.work.w
    height=int(s.work.h*scale)
    im=Image.new('RGB',(width,height+65),'#f5f2ec');d=ImageDraw.Draw(im)
    font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',16)
    d.text((12,8),label,fill='#263747',font=font)
    colors=['#b7d2e2','#e5c8b4','#c3d9bb','#d5c9e7','#e4dca7','#aecfca']
    for i,(k,w) in enumerate(sorted(s.windows.items())):
        if w.minimised or not w.rect:continue
        r=w.rect;box=[int((r.x-s.work.x)*scale),int((r.y-s.work.y)*scale)+40,
            int((r.right-s.work.x)*scale),int((r.bottom-s.work.y)*scale)+40]
        d.rounded_rectangle(box,radius=5,fill=colors[i%len(colors)],outline='#536779',width=3 if w.pinned else 1)
        d.text((box[0]+7,box[1]+7),k+(' [pin]' if w.pinned else ''),fill='#263747',font=font)
    for r in s.obstacles:
        d.rectangle([(r.x-s.work.x)*scale,(r.y-s.work.y)*scale+40,
            (r.right-s.work.x)*scale,(r.bottom-s.work.y)*scale+40],fill='#999999')
    d.text((12,height+42),'Minimised: '+', '.join(k for k,w in s.windows.items() if w.minimised),fill='#536779',font=font)
    im.save(path)


def replay(data,directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    config=dict(data.get('state',{}))
    if 'work' in config:config['work']=Rect(*config['work'])
    s=State(**config);paths=[]
    for i,event in enumerate(data['events']):
        result=solve(s,event);s=result.state
        path=directory/f'{i:02d}.png';render(s,path,f'{i+1}. {event["type"]} {event.get("key","")}');paths.append(path)
    return s,paths


if __name__=='__main__':
    import sys
    replay(json.loads(Path(sys.argv[1]).read_text()),sys.argv[2])
