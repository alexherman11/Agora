"""Prepare the canonical service without starting it or touching the old service."""
import json
from pathlib import Path
import shutil

old = Path(r'C:\Projects\Agora\worlds\improved-desk')
new = Path(r'C:\Projects\Agora\worlds\jeff0-desk')
repo = Path(r'C:\Projects\Agora\worlds\application-experiment\repo')
new.mkdir(exist_ok=True)
for name in ('logs','control','evidence'):
    (new/name).mkdir(exist_ok=True)
for name in ('control_client.py','source_fixture.py','fixture_tunnel.py','browser_specs.py','browser_worker.cjs','open_desk.py','Open Agora Desk.ps1'):
    shutil.copy2(old/name,new/name)
service=(old/'serve_desk.py').read_text(encoding='utf8')
service=service.replace('str(ROOT / "runtime/src")',repr(str(repo/'src')))
(new/'serve_desk.py').write_text(service,encoding='utf8')
settings=json.loads((old/'desk.json').read_text())
settings.update(world=str(new/'world'),port=8873,resident='jeff0',source_repository=str(repo))
(new/'desk.json').write_text(json.dumps(settings,indent=2),encoding='utf8')
worker=(new/'browser_worker.cjs').read_text(encoding='utf8')
worker=worker.replace('async function frame(p=page){','async function frame(p=page,view=null){')
worker=worker.replace("return f;}\nasync function snapshot", "if(view){const handle=await f.locator('[data-view='+JSON.stringify(view)+'] iframe').elementHandle();if(!handle)throw Error('Application view is not open');f=await handle.contentFrame();if(!f)throw Error('Application frame unavailable');await f.waitForFunction(()=>document.body?.children.length>0);}return f;}\nasync function snapshot")
worker=worker.replace('const f=await frame(p);let content=', 'const f=await frame(p,req.view);let content=')
worker=worker.replace('const f=await frame(p);let target;', 'const f=await frame(p,req.view);let target;')
worker=worker.replace('const f=await frame();const timeout=spec.timeout', 'const f=await frame(page,spec.view);const timeout=spec.timeout')
worker=worker.replace("return{viewport:{width:innerWidth", "return{views:[...document.querySelectorAll('[data-view]')].map(n=>({id:n.dataset.view,package:n.dataset.package,title:n.querySelector('header')?.innerText})),viewport:{width:innerWidth")
worker=worker.replace('await interact({...step,wait:', 'await interact({view:req.view,...step,wait:')
worker=worker.replace('await waitForUI(step)', 'await waitForUI({view:req.view,...step})')
worker=worker.replace('await waitForUI(req.settle)', 'await waitForUI({view:req.view,...req.settle})')
worker=worker.replace('snapshot({selectors:req.selectors||[]})', 'snapshot({view:req.view,selectors:req.selectors||[]})')
(new/'browser_worker.cjs').write_text(worker,encoding='utf8')
specs=(new/'browser_specs.py').read_text(encoding='utf8')
specs+='''\nfor spec in extra_specs:
    if spec['name'] in {'experiment.observe', 'experiment.interact', 'experiment.sequence'}:
        spec['input_schema']['properties']['view'] = {'type': 'string'}
        spec['description'] += ' Optional view selects an open application iframe by its application.list view ID; omit for the desktop. Each application owns a separate document.'
'''
(new/'browser_specs.py').write_text(specs,encoding='utf8')
print(json.dumps({'prepared':str(new),'started':False,'port':8873}))
