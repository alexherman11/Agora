"""Purpose-oriented composition checks against the frozen core; no model calls."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from painter.tweaks.run import regression
from painter.fixture import Fixture
from painter.install import upsert,activate,Q
from painter.browser import Page


def run():
    f=Fixture();pages=[];checks=[];folder=Path(__file__).resolve().parent/'evidence'
    def check(name,condition):
        checks.append(dict(check=name,ok=bool(condition)));print(('PASS ' if condition else 'FAIL ')+name,flush=True)
    try:
        definitions={
          'painter-long-list':'root : virtual-list, of tag:taskboard-task as task, each entry, height 120, row_height 40\nentry : text "$task.title"',
          'painter-panes':'root : split\n  left : text "A writing room"\n  right : text "Research beside it"',
          'painter-phone':'root : grid, columns "1fr 2fr", gap medium\n  feed : list\n    words : markdown, value "## Welcome"\n  compose : input, label "Message"',
          'painter-layers':'root : layers, height 200px\n  guy : absolute, x 40, y 30\n    pixels : pixel-surface',
        }
        for name,source in definitions.items():
            upsert(f.door,'lens',name,painter='components',text=source)
            wid=activate(f.door,name,name)
            p=Page(f.url,f.token,wid,clock=f.k.now());pages.append(p)
            if name.endswith('long-list'):
                p.until('!!document.querySelector("[tabindex]")')
                n=p.js('document.querySelectorAll(".text").length')
                check('Long rows are actually windowed in the DOM',0<n<25)
                p.js('document.querySelector("[tabindex]").scrollTop=900')
                p.until('document.body.innerText.includes("Plan the next small step")')
                check('Scrolling reaches the actual last fact row',p.js('document.body.innerText.includes("Plan the next small step")'))
                check('Agent reading describes all bound rows',f.door.say('look-view '+name)['rows'][0]['counts'].get('text')==25)
            elif name.endswith('panes'):
                p.until('!!document.querySelector("[role=separator]")')
                before=p.js('document.querySelector("[role=separator]").getAttribute("aria-valuenow")')
                p.js('document.querySelector("[role=separator]").focus()')
                p.c.call('Input.dispatchKeyEvent',type='keyDown',key='ArrowRight',code='ArrowRight',windowsVirtualKeyCode=39)
                check('Split separator is keyboard resizable',p.js('document.querySelector("[role=separator]").getAttribute("aria-valuenow")')!=before)
            elif name.endswith('phone'):
                p.until('document.body.innerText.includes("Welcome")')
                desktop=p.js('getComputedStyle(document.querySelector(".grid")).gridTemplateColumns.split(" ").length')
                p.c.call('Emulation.setDeviceMetricsOverride',width=390,height=800,deviceScaleFactor=1,mobile=False)
                check('Desktop grid has authored proportions',desktop==2)
                check('390 CSS pixel rule composes the same view in one column',p.js('getComputedStyle(document.querySelector(".grid")).gridTemplateColumns.split(" ").length===1'))
                check('Input has its readable accessible name',p.js('!!document.querySelector("input[aria-label=Message]")'))
                p.shot(folder/'phone-composition.png')
            elif name.endswith('layers'):
                p.until('!!document.querySelector("canvas")')
                check('Pixel surface has 2D pixels and an accessible label',p.js('document.querySelector("canvas").getAttribute("role")==="img" && document.querySelector("canvas").getContext("2d").getImageData(50,40,1,1).data[3]>=0'))
                check('Absolute placement is authored in the lens',p.js('getComputedStyle(document.querySelector(".absolute")).left==="40px" && getComputedStyle(document.querySelector(".absolute")).top==="30px"'))
        # A separate pure-JS baseline measures failures that predate any tweak.
        p=Page(f.url,f.token,f.js,clock=f.k.now());pages.append(p);p.until('document.querySelectorAll(".card").length===25')
        (folder/'baseline-js-board-proof').mkdir(exist_ok=True)
        baseline=regression(f,p,f.js,folder/'baseline-js-board-proof')
        print('BASELINE JS',sum(x['ok'] for x in baseline),'/',len(baseline),flush=True)
        (folder/'purpose-proof.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
        print(f'{sum(c["ok"] for c in checks)} of {len(checks)} purpose checks passed',flush=True)
    finally:
        for p in pages:p.close()
        f.close()


if __name__=='__main__':run()
