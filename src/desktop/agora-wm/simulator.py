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


def film(state,key,ticks,path,width=480,every=4):
    """A drag as a filmstrip: real windows (filled), neighbour ghosts (outlined), the landing (dashed), one panel
    per `every` ticks. ticks: [(rect, t_ms)]. Uses feel.Gesture; the last panel is the release."""
    from feel import Gesture,Feel
    g=Gesture(state,key,ticks[0][0],ticks[0][1],Feel(scale=1.5));panels=[]
    scale=width/state.work.w;height=int(state.work.h*scale)
    font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',13)
    def box(r):return [int((r.x-state.work.x)*scale),int((r.y-state.work.y)*scale)+22,int((r.right-state.work.x)*scale),int((r.bottom-state.work.y)*scale)+22]
    def panel(label,windows,ghosts,landing,dragged):
        im=Image.new('RGB',(width,height+24),'#f5f2ec');d=ImageDraw.Draw(im);d.text((6,3),label,fill='#263747',font=font)
        for k,r in sorted(windows.items()):
            d.rectangle(box(r),fill='#e5c8b4' if k==key else '#b7d2e2',outline='#536779')
            d.text((box(r)[0]+4,box(r)[1]+2),k,fill='#263747',font=font)
        for r in ghosts.values():d.rectangle(box(r),outline='#c0392b',width=2)
        if landing:
            b=box(landing)
            for x in range(b[0],b[2],8):d.line([x,b[1],min(x+4,b[2]),b[1]],fill='#27ae60',width=2);d.line([x,b[3],min(x+4,b[2]),b[3]],fill='#27ae60',width=2)
            for y in range(b[1],b[3],8):d.line([b[0],y,b[0],min(y+4,b[3])],fill='#27ae60',width=2);d.line([b[2],y,b[2],min(y+4,b[3])],fill='#27ae60',width=2)
        return im
    homes={k:w.rect for k,w in state.windows.items() if w.rect and not w.minimised}
    for i,(r,t) in enumerate(ticks[1:]):
        f=g.step(r,t)
        if i%every==0:panels.append(panel(f'{t-ticks[0][1]} ms {f.kind}',{**homes,key:r},f.ghosts,f.landing,r))
    result=g.release(*ticks[-1])
    panels.append(panel('released',result.placements,{},None,None))
    cols=4;rows=(len(panels)+cols-1)//cols
    sheet=Image.new('RGB',(cols*(width+6),rows*(height+30)),'#ffffff')
    for i,p in enumerate(panels):sheet.paste(p,((i%cols)*(width+6),(i//cols)*(height+30)))
    sheet.save(path);return result
