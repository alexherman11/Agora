"""Adopt the reviewed opening repair through reversible off/undo of window only."""
import argparse
import json
from pathlib import Path
import re
import sys,time
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from painter.live import Door,processes,health,digest
from painter.install import taskboard
from painter.process_gate import check


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--builder-pid',type=int);args=ap.parse_args()
    check()
    if processes(args.builder_pid):raise RuntimeError('Another codex exec is active; no window restart performed.')
    for _ in range(3):
        if not health():raise RuntimeError('Kernel is not answering; another restart may be underway.')
        time.sleep(.4)
    base=taskboard.live_door();d=Door(base.url,base.token);before=d.rows('taskboard-task')
    module=d.rows('module',name='window')[0];d.say('look '+module['id']);off=d.say('off '+module['id'])
    record='r'+re.search(r'\br(\d+)\b',off['text'])[1]
    time.sleep(1)
    d.say('undo '+record)
    end=time.monotonic()+30
    while time.monotonic()<end:
        answer=d.request('/see',dict(line='window.list'))
        rows=answer.get('rows',[])
        boards=[w for w in rows if w.get('shows') in ('taskboard','taskboard-js','taskboard-components') and w.get('shown')]
        if len(boards)==3:break
        time.sleep(.3)
    receipts=[]
    for name in ('taskboard','taskboard-js','taskboard-components'):
        receipt=d.say('window.open '+name)['text'];receipts.append(receipt);print(receipt,flush=True)
    after=d.rows('taskboard-task');assert before==after,'Task facts changed while reloading window provider'
    result=dict(off_record=record,tasks_unchanged=True,task_count=len(after),task_hash=digest(after),receipts=receipts,
                windows=d.request('/see',dict(line='window.list')).get('rows',[]))
    (Path(__file__).resolve().parent/'evidence/live-window-open-repair.json').write_text(json.dumps(result,indent=2),encoding='utf-8')


if __name__=='__main__':main()
