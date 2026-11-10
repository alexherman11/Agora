"""EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
(people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.

Two-minute read-only observation, and app-name-only summary. No live endpoint.
shadow.py --seconds 120 --out evidence/shadow.jsonl
shadow.py --report evidence/shadow.jsonl
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import time
from manager import Manager
from win32_host import Native,EventFeed,work_area,dpi_aware,hotkey_probe


def report(path):
    samples=0;apps=set();moves=Counter();minimum=Counter();gates=Counter();invalid=0
    with Path(path).open(encoding='utf-8') as f:
        for line in f:
            row=json.loads(line);samples+=1
            apps.update(row.get('observed_apps',[]))
            for reason in row.get('gated',[]):gates[reason]+=1
            if row.get('valid') is False:invalid+=1
            for win in row.get('plan',[]):
                apps.add(win['app'])
                if win['minimise']:minimum[win['app']]+=1
                elif win['managed'] and win['planned']!=win['actual']:moves[win['app']]+=1
    value={'samples':samples,'apps':sorted(apps),'would_move_samples':dict(sorted(moves.items())),
        'would_minimise_samples':dict(sorted(minimum.items())),'gated_samples':dict(gates),'infeasible_samples':invalid,
        'meaning':'lines are distinct plans (the manager writes on change, 26 Oct) plus gated ticks; no window titles recorded'}
    print('L2 shadow: '+json.dumps(value),flush=True);return value


def observe(seconds,path):
    dpi_aware();path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():raise FileExistsError('use a fresh observation path')
    native=Native();host=Manager(native,path.parent/'shadow-state');host.log_path=path
    feed=EventFeed().start();start=time.monotonic();ticks=0;events=0
    print('L2 hotkey probe: '+json.dumps(hotkey_probe()),flush=True)
    try:
        while time.monotonic()-start<seconds:
            batch=feed.drain();events+=len(batch)
            result=host.ingest(native.windows(),work_area(),batch)
            if result and result.get('gated'):
                with path.open('a',encoding='utf-8') as f:f.write(json.dumps(result)+'\n')
            ticks+=1
            if ticks%60==0:print(f'L2 observing: {time.monotonic()-start:.1f}s; read-only',flush=True)
            time.sleep(.25)
    finally:feed.close()
    summary=report(path);summary.update({'seconds':round(time.monotonic()-start,3),'hook_events':events,
        'native_mutating':native.mutating})
    path.with_suffix('.summary.json').write_text(json.dumps(summary,indent=2))
    print('L2 duration: '+json.dumps({k:summary[k] for k in ('seconds','hook_events','native_mutating')}),flush=True)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seconds',type=float,default=120);p.add_argument('--out',type=Path,default=Path('shadow.jsonl'))
    p.add_argument('--report',type=Path);a=p.parse_args()
    report(a.report) if a.report else observe(a.seconds,a.out)
