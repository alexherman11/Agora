import hashlib
import json
from datetime import datetime, UTC
from pathlib import Path
import sqlite3
import sys

folder=Path(__file__).parent
root=Path(r'C:\Projects\Agora\worlds\jeff0-desk')
repo=Path(r'C:\Projects\Agora\worlds\docs-restoration\repo')
sys.path.insert(0,str(repo/'src'))
from agora3.gateway import Gateway
gateway=Gateway(root/'world')
world=gateway.world.replay()
binding=json.loads((folder/'resident-before.json').read_text())
assert binding==world['agora.agent.resident']
since=datetime.fromtimestamp((folder/'resident-before.json').stat().st_mtime-2,UTC).isoformat()
with sqlite3.connect(f'file:{(root/"world/world.db").as_posix()}?mode=ro',uri=True) as db:
    changes=[{'seq':seq,'actor':actor,'at':at,'objects':[{'id':obj['id'],'facets':list(obj['facets'])} for obj in json.loads(body)['objects']]} for seq,actor,at,body in db.execute('select seq,actor,at,body from events where at>=? order by seq',(since,))]
report={'source_repository':str(repo),'objects':len(world),'resident_binding_unchanged':True,'thread_id':binding['facets']['agora.agent']['session']['thread_id'],'replay':gateway.world.verify(),'restart_changes':changes,'prompt_sha256':hashlib.sha256((repo/'src/agora3/prompts/jeff.md').read_bytes()).hexdigest()}
(folder/'activation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
