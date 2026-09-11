"""Switch source trees while retaining the canonical world and conversation identity."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

root=Path(r'C:\Projects\Agora\worlds\jeff0-desk')
repo=Path(r'C:\Projects\Agora\worlds\docs-restoration\repo')
sys.path[:0]=[str(root),str(repo/'src')]
import control_client as c
from agora3.gateway import Gateway

state=c.call({'op':'status'})
if state['running']:
    raise SystemExit('BUSY: JEFF0 has an active turn; no files or service changed.')
gateway=Gateway(root/'world')
before=gateway.world.replay()
binding=before['agora.agent.resident']
folder=Path(__file__).parent
(folder/'resident-before.json').write_text(json.dumps(binding,indent=2),encoding='utf8')
shutil.copy2(root/'serve_desk.py',folder/'serve-before.py')
shutil.copy2(root/'desk.json',folder/'desk-before.json')
print(c.call({'op':'close'}),flush=True)
service=(root/'serve_desk.py').read_text(encoding='utf8')
old=r'C:\Projects\Agora\worlds\application-experiment\repo\src'
assert repr(old) in service
service=service.replace(repr(old),repr(str(repo/'src')))
(root/'serve_desk.py').write_text(service,encoding='utf8')
settings=json.loads((root/'desk.json').read_text())
settings.update(source_repository=str(repo),runtime_branch='agora4',runtime_commit='pending merge commit')
(root/'desk.json').write_text(json.dumps(settings,indent=2),encoding='utf8')
subprocess.run([sys.executable,str(root/'open_desk.py'),'--no-open'],cwd=root,check=True)
after=gateway.world.replay()
assert before==after,'World changed during the idle source switch'
assert binding==after['agora.agent.resident']
prompt=(repo/'src/agora3/prompts/jeff.md').read_bytes()
report={'source_repository':str(repo),'world_unchanged':True,'objects':len(after),
        'thread_id':binding['facets']['agora.agent']['session']['thread_id'],
        'prompt_sha256':hashlib.sha256(prompt).hexdigest(),'replay':gateway.world.verify()}
(folder/'activation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2),flush=True)
