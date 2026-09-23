import json
import socket
import sqlite3
import sys
from pathlib import Path

root=Path(r'C:\Projects\Agora\worlds\jeff0-desk')
old=Path(r'C:\Projects\Agora\worlds\improved-desk')
repo=Path(r'C:\Projects\Agora\worlds\application-experiment\repo')
sys.path[:0]=[str(root),str(repo/'src')]
import control_client as c
from agora3.gateway import Gateway

new=Gateway(root/'world')
with sqlite3.connect(f"file:{old/'world/world.db'}?mode=ro",uri=True) as db:
    old_events=db.execute('SELECT * FROM events ORDER BY seq').fetchall()
    old_objects={row[0]:json.loads(row[1]) for row in db.execute('SELECT id,body FROM objects')}
with new.world.connection() as db:
    prefix=[tuple(row) for row in db.execute('SELECT * FROM events WHERE seq<=? ORDER BY seq',(old_events[-1][0],))]
assert old_events==prefix
current=new.world.replay()
changed=[key for key,value in old_objects.items() if current[key]!=value]
assert set(changed)=={'agora.package.agora.shell','agora.installation.agora.shell'},changed
before=json.loads((Path(__file__).parent/'binding-before-restart.json').read_text())
assert before==new.world.get('agora.agent.resident')
status=c.call({'op':'status'})
assert status['running'] is False and status['error'] is None
assert status['system']['native_bridge']['connected']
assert status['system']['guest']['vm_id']=='bbdd25e7-1e05-4d94-a257-168cd78b04da'
assert status['system']['yard']['vm_id']=='32cea95c-58f1-4cc9-8351-916e5d4628c3'
with socket.socket() as sock:
    assert sock.connect_ex(('127.0.0.1',8870))!=0,'Archived service still listening'
page=c.browser(op='observe')
view=next(row for row in new.applications.list()['views'] if row['package']=='agora.documents' and row['open'])
child=c.browser(op='observe',view=view['id'])
assert not page['errors'] and not child['errors'],(page['errors'],child['errors'])
assert 'Live Markdown' in child['text']
shot=root/'evidence/jeff0-ready.png'
c.browser(op='screenshot',path=str(shot))
report={'ready':True,'thread_id':before['facets']['agora.agent']['session']['thread_id'],
        'same_binding_after_restart':True,'original_events':len(old_events),
        'identical_event_prefix':True,'original_objects':len(old_objects),
        'unchanged_original_objects':len(old_objects)-len(changed),'changed':changed,
        'messages':len(new.world.query(['core.message'],1000)['items']),
        'discussions':len(new.world.query(['studio.comment-thread'],1000)['items']),
        'replay':new.world.verify(),'system':status['system'],'browser_errors':[],
        'app_frame_observation_verified':True,'old_service_stopped':True,'screenshot':str(shot)}
(Path(__file__).parent/'final-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k!='system'},indent=2))
