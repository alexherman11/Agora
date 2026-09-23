import json, subprocess, sys, urllib.request
from pathlib import Path
root=Path(r'C:\Projects\Agora\worlds\jeff0-desk')
repo=Path(r'C:\Projects\Agora\worlds\docs-restoration\repo')
sys.path[:0]=[str(root),str(repo/'src')]
import control_client as c
from agora3.gateway import Gateway
port=json.loads((root/'desk.json').read_text())['port']
g=Gateway(root/'world')
def status():
    req=urllib.request.Request(f'http://127.0.0.1:{port}/api/rpc',data=json.dumps({'method':'chat.status','args':{}}).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+g.keep['operator']})
    with urllib.request.urlopen(req,timeout=10) as r: return json.load(r)['result']
s=status()
assert not s['running'] and not s['voice'].get('active'), 'Busy; restart deferred.'
assert str(repo/'src') in (root/'serve_desk.py').read_text().replace('\\\\','\\'), 'Unexpected source checkout'
before=g.world.get('agora.agent.resident')
old=json.loads((root/'ready.json').read_text())
print(json.dumps({'idle':True,'old_pid':old['pid']}),flush=True)
print(json.dumps(c.call({'op':'close'},timeout=30)),flush=True)
subprocess.run([sys.executable,str(root/'open_desk.py'),'--no-open'],cwd=root,check=True)
after=g.world.get('agora.agent.resident')
assert before==after, 'Resident binding changed'
s=status()
ready=json.loads((root/'ready.json').read_text())
assert ready['pid'] != old['pid'] and ready['launch_id'] != old['launch_id']
report={'restarted':True,'pid':ready['pid'],'resident_binding_unchanged':True,'resident':s['resident']['id'],'resumable':s['resident']['resumable'],'running':s['running'],'error':s['error'],'replay':g.world.verify(),'source':str(repo),'live_model_turn_started':False}
Path(r'C:\Projects\Agora\local\ui-selection-restart.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report),flush=True)
