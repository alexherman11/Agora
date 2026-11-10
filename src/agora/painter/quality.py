"""Faithful hidden A/B screenshots of identical frozen facts; no image synthesis."""
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from painter.tweaks.run import Copy
from painter.browser import Page
from PIL import Image,ImageChops,ImageStat

HERE=Path(__file__).resolve().parent
f=Copy();pages=[];folder=HERE/'evidence'
try:
    before=f.door.rows('taskboard-task')
    for name,mid in [('A',f.ids['taskboard-components']),('B',f.js)]:
        p=Page(f.url,f.token,mid,clock=f.k.now());pages.append(p)
        p.until('document.querySelectorAll(".card").length===25');p.shot(folder/f'frozen-{name}.png')
    assert before==f.door.rows('taskboard-task')
    a=Image.open(folder/'frozen-A.png').convert('RGB');b=Image.open(folder/'frozen-B.png').convert('RGB')
    together=Image.new('RGB',(a.width+b.width,max(a.height,b.height)),'white');together.paste(a,(0,0));together.paste(b,(a.width,0));together.save(folder/'board-comparison.png')
    diff=ImageChops.difference(a.crop((1,46,1583,1014)),b.crop((1,46,1583,1014)))
    result=dict(identical_task_facts=True,card_count=25,mean_absolute_channel_difference=round(sum(ImageStat.Stat(diff).mean)/3,4),
                note='Native title labels excluded. Pixel distance is diagnostic, not a usability or aesthetic verdict.')
    (folder/'quality.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result),flush=True)
finally:
    for p in pages:p.close()
    f.close()
