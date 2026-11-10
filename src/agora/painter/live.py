"""Gated live adoption/install and exact task-preservation evidence. Never touches git."""
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent;LAB=HERE.parent;ROOT=LAB.parents[1];DESKTOP=ROOT/'src/desktop/kernel-desktop'
sys.path[:0]=[str(LAB),str(DESKTOP)]
from painter.process_gate import check as gate
from painter.install import taskboard,install,Q,upsert


class Door(taskboard.Door):
    def request(self,path,body=None):
        if body and path=='/do' and body.get('line','').split()[0] not in ('look','rows','help','status','holds','history','look-view','components'):
            gate()
        return super().request(path,body)


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def health():
    import urllib.request
    try:
        with urllib.request.urlopen('http://127.0.0.1:8810/health',timeout=2) as r:return json.load(r)
    except Exception:return None


def processes(builder_pid=None):
    out=subprocess.run(['powershell.exe','-NoProfile','-Command',
        'Get-CimInstance Win32_Process | Where-Object { $_.Name -eq "codex.exe" -and $_.CommandLine -match "(?:^|\\s)exec(?:\\s|$)" } | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress'],
        capture_output=True,text=True,creationflags=0x08000000)
    value=json.loads(out.stdout) if out.stdout.strip() else []
    rows=value if isinstance(value,list) else [value]
    if builder_pid:
        own=next((r for r in rows if r['ProcessId']==builder_pid),None)
        if own and 'codex-components-out.md' not in own.get('CommandLine',''):
            raise RuntimeError('The excluded PID is not this commissioned component builder.')
        rows=[r for r in rows if r['ProcessId']!=builder_pid]
    return rows


def restart(builder_pid=None):
    gate();running=processes(builder_pid)
    if running:raise RuntimeError('Another codex exec is active; wait before desktop restart. PIDs: '+','.join(str(p['ProcessId']) for p in running))
    for _ in range(3):
        if not health():raise RuntimeError('Desktop is already not answering; another restart may be underway.')
        time.sleep(.5)
    for name in ('kdesk_off.py','kdesk_on.py'):
        gate();args=[sys.executable,str(DESKTOP/name)]+(['--wait'] if name=='kdesk_on.py' else [])
        done=subprocess.run(args,capture_output=True,text=True,creationflags=0x08000000)
        print(done.stdout.strip(),flush=True)
        if done.returncode:raise RuntimeError(done.stderr)
    end=time.monotonic()+45
    while time.monotonic()<end:
        if health():return
        time.sleep(.5)
    raise RuntimeError('Desktop did not answer after restart; see its existing state log.')


def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--install',action='store_true');ap.add_argument('--restart',action='store_true');ap.add_argument('--builder-pid',type=int);args=ap.parse_args()
    gate();original=taskboard.live_door();door=Door(original.url,original.token)
    tasks=door.rows('taskboard-task');histories={t['id']:door.request('/see',dict(line='history '+t['id']))['rows'] for t in tasks}
    windows=door.request('/see',dict(line='window.list'))
    before=dict(at=datetime.now(timezone.utc).isoformat(),tasks=len(tasks),task_hash=digest(tasks),
                missing_priority=sum(not str(t.get('priority','')).isdecimal() for t in tasks),windows=windows.get('rows',[]),
                history_hashes={t:digest(h) for t,h in histories.items()})
    print('Live before:',len(tasks),'tasks;',before['missing_priority'],'missing priorities;',len(before['windows']),'window/work rows.',flush=True)
    if not args.install:return
    (HERE/'evidence/live-before.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
    if not door.request('/see',dict(line='help look-view')).get('ok'):
        if not args.restart:raise RuntimeError('Running kernel lacks the new words; explicitly --restart after review/testing.')
        restart(args.builder_pid)
    # Reconnect to the same kept person/session. No account/session files changed.
    original=taskboard.live_door();door=Door(original.url,original.token)
    ids=install(door)
    plan=door.request('/see',dict(line='look-view taskboard-components'))
    if not plan.get('ok'):raise RuntimeError(plan.get('text'))
    after=door.rows('taskboard-task')
    preserved=tasks==after
    prefixes=all(door.request('/see',dict(line='history '+t))['rows'][:len(h)]==h for t,h in histories.items())
    if not preserved or not prefixes:raise RuntimeError('Task preservation check failed; board not opened.')
    # The board intent is the only new visible window. Its ordinary close/× is
    # the off switch; off taskboard-components additionally revokes its powers.
    gate();opened=door.say('window.open taskboard-components to=left')
    end=time.monotonic()+15;current={}
    while time.monotonic()<end:
        rows=door.request('/see',dict(line='window.list')).get('rows',[])
        current=next((w for w in rows if w.get('kind')=='window' and w.get('shows')=='taskboard-components'),{})
        if current.get('shown'):break
        time.sleep(.3)
    note='Rough spots: component and part-style things needed steward component review, data-only look-view, and components/help discovery. Repository implementations: painter/arrangement.py and kernel/words.py. No lens.js edit. Frozen A/B trial: 6/10 component, 9/10 JS; full TWEAKS.md records code needs and failures. Post-trial repair adds responsive metadata to primitive layouts. Builder leaves review/commit to Claude.'
    upsert(door,'note','painter-rough-spots',title='Rough spots · Component painter',text=note)
    result=dict(at=datetime.now(timezone.utc).isoformat(),task_count=len(after),tasks_unchanged=preserved,history_prefixes_unchanged=prefixes,
                task_hash=digest(after),opened=opened.get('text'),window=current,counts=plan['rows'][0]['counts'],ids=ids)
    (HERE/'evidence/live.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Live preserved:',len(after),'task identities/facts and their history prefixes.',flush=True)
    print('Component board shown:',bool(current.get('shown')),'box:',current.get('box'),flush=True)


if __name__=='__main__':main()
