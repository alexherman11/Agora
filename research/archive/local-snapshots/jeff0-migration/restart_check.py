import json
from pathlib import Path
import subprocess
import sys

root=Path(r'C:\Projects\Agora\worlds\jeff0-desk')
sys.path.insert(0,str(root))
import control_client as c
from chat_control import rpc

status=rpc('chat.status')
if status['running'] or status['error']:
    raise RuntimeError('Resident must be idle and healthy before restart.')
binding=rpc('world.get',{'id':'agora.agent.resident'})
(Path(__file__).parent/'binding-before-restart.json').write_text(json.dumps(binding,indent=2),encoding='utf8')
print({'before_thread':binding['facets']['agora.agent']['session']['thread_id']},flush=True)
print(c.call({'op':'close'}),flush=True)
subprocess.run([sys.executable,str(root/'open_desk.py'),'--no-open'],cwd=root,check=True)
after=rpc('world.get',{'id':'agora.agent.resident'})
if binding!=after:
    raise RuntimeError('Resident binding changed during restart.')
print({'resident_binding_unchanged':True,'restarted':True},flush=True)
