"""One gated desktop restart, v2 installation, widget installation and layout.

Authorized by Alex's widget build request. Never stages, commits or pushes.
The existing taskboard live verifier is invoked, not edited.
"""
import json
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
DESKTOP=HERE.parents[1]/'desktop/kernel-desktop'
sys.path.insert(0,str(DESKTOP))
from gaming_gate import assert_clear
from install import install,taskboard

PY=HERE.parents[2]/'.venv/Scripts/python.exe'


def run(path,*args):
    assert_clear()
    subprocess.run([str(PY),str(path),*args],check=True,creationflags=0x08000000)


def main():
    # The specifically requested PowerShell inventory, plus the full-screen gate.
    inventory=subprocess.run(['powershell','-NoProfile','-Command',
        'Get-Process RocketLeague,*game* -ErrorAction SilentlyContinue | Select-Object ProcessName,Id | ConvertTo-Json -Compress'],
        capture_output=True,text=True,creationflags=0x08000000,check=False)
    print('Gaming process inventory: '+inventory.stdout.strip(),flush=True)
    assert_clear()
    run(taskboard.HERE/'verify_v2_live.py','--before')
    run(DESKTOP/'kdesk_off.py')
    # If a game starts in the narrow off/on interval, do not start over it.
    run(DESKTOP/'kdesk_on.py','--wait')
    run(taskboard.HERE/'install.py','--no-seed')
    assert_clear()
    door=taskboard.live_door()
    ids=install(door)
    windows=door.say('window.list')['rows']
    work=next(r['box'] for r in windows if r.get('kind')=='work')
    x,y,w,h=work
    gap=16;editor=min(760,int(w*.20));board=(w-editor-gap*4)//2
    top=y+160;height=max(800,h-200)
    lens=door.rows('window',lens='taskboard')[0]
    assert_clear();door.say(f'window.move {lens["id"]} at={x+gap},{top} size={board},{height}')
    assert_clear();door.say(f'window.open taskboard-js at={x+gap*2+board},{top} size={board},{height}')
    assert_clear();door.say(f'window.open guy-editor at={x+gap*3+board*2},{top} size={editor},{min(height,1320)}')
    end=time.monotonic()+30
    shown=[]
    while time.monotonic()<end:
        assert_clear()
        shown=door.say('window.list')['rows']
        if all(any(r.get('shows')==name and r.get('shown') for r in shown)
               for name in ('taskboard','taskboard-js','guy-editor')):break
        time.sleep(.4)
    else:raise RuntimeError('the native demo windows were not all shown')
    run(taskboard.HERE/'verify_v2_live.py')
    evidence=HERE/'evidence';evidence.mkdir(exist_ok=True)
    report=dict(widgets=ids,windows=[r for r in shown if r.get('shows') in ('taskboard','taskboard-js','guy-editor')],
                holds=door.say('holds')['rows'],tasks=len(door.rows('taskboard-task')))
    (evidence/'live.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('LIVE: lens v2 and JS board side by side; guy studio shown; widget holds recorded',flush=True)


if __name__=='__main__':main()
