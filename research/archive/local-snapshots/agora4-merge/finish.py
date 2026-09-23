import hashlib
import json
from pathlib import Path
import subprocess
import sys

folder=Path(__file__).parent
root=Path(r'C:\Projects\Agora\worlds\jeff0-desk')
repo=Path(r'C:\Projects\Agora\worlds\docs-restoration\repo')
sys.path.insert(0,str(repo/'src'))
from agora3.gateway import Gateway

commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
assert subprocess.check_output(['git','branch','--show-current'],cwd=repo,text=True).strip()=='agora4'
subprocess.run(['git','merge-base','--is-ancestor','2a0e60a','HEAD'],cwd=repo,check=True)
assert not subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True).strip()
settings=json.loads((root/'desk.json').read_text())
assert settings['source_repository']==str(repo)
settings['runtime_commit']=commit
sources=subprocess.check_output(['git','ls-files','src'],cwd=repo,text=True).splitlines()
settings['runtime_source_hashes']={name:hashlib.sha256((repo/name).read_bytes()).hexdigest() for name in sources}
(root/'desk.json').write_text(json.dumps(settings,indent=2),encoding='utf8')
gateway=Gateway(root/'world')
assert gateway.world.get('agora.agent.resident')==json.loads((folder/'resident-before.json').read_text())
chat=json.loads((folder/'final-chat.json').read_text())
assert not chat['running'] and chat['error'] is None
assert len(chat['messages'])==40 and 'JEFF0' in chat['reply']
report={'branch':'agora4','commit':commit,'worktree_clean':True,'resident_binding_unchanged':True,'replay':gateway.world.verify(),'live_acknowledged':True,'messages':len(chat['messages'])}
(folder/'complete.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
