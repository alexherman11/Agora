"""Arrange the three authorized live boards through window words; keep task data."""
import json
from pathlib import Path
import sys,time
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from painter.live import Door,digest
from painter.install import taskboard
from painter.process_gate import check

HERE=Path(__file__).resolve().parent
check();base=taskboard.live_door();d=Door(base.url,base.token)
before=d.rows('taskboard-task');rows=d.request('/see',dict(line='window.list'))['rows']
work=next(r['box'] for r in rows if r['kind']=='work');gap=16;width=(work[2]-gap*4)//3
old={r['shows']:r for r in rows if r['kind']=='window' and r.get('shows') in ('taskboard','taskboard-js','taskboard-components')}
top=old['taskboard']['box'][1];height=min(old['taskboard']['box'][3],work[1]+work[3]-top-gap)
receipts=[]
for i,name in enumerate(('taskboard','taskboard-js','taskboard-components')):
    w=old[name];d.say('look '+w['id'])
    receipts.append(d.say(f'window.move {w["id"]} at={work[0]+gap+i*(width+gap)},{top} size={width},{height}')['text'])
    # Opening an existing view brings it forward without the focus word's toggle.
    d.say('window.open '+name)
time.sleep(1)
after=d.rows('taskboard-task');assert before==after,'Task facts changed during window arrangement'
current=[r for r in d.request('/see',dict(line='window.list'))['rows'] if r.get('shows') in old]
record=dict(task_count=len(after),tasks_unchanged=True,task_hash=digest(after),windows=current,previous=old,receipts=receipts)
(HERE/'evidence/live-layout.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print('Arranged three boards in columns; task facts unchanged:',len(after),flush=True)
print(json.dumps([{k:r.get(k) for k in ('shows','box','shown','front')} for r in current]),flush=True)
