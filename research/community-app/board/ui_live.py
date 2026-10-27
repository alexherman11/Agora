"""Explicit gated adoption, preserving the live desktop; never opens the board."""
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime,timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DESKTOP=ROOT/'research/window-lab/kernel-desktop'
sys.path[:0]=[str(HERE),str(ROOT/'research/kernel-lab'),str(DESKTOP)]
from gaming_gate import reasons
from painter.install import taskboard,widget_source
from ui_install import install_ui
from install import install,modules
from protocol import line


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


class Gate:
    deadline=None
    def __call__(self,step):
        due=0
        while True:
            now=time.monotonic()
            if now>=due:
                blocked=reasons()
                print('LIVE GATE '+json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),step=step,blocked=blocked)),flush=True)
                if not blocked:return
                if self.deadline is None:self.deadline=now+90*60
                if now>=self.deadline:raise RuntimeError('Screen gate remained blocked for 90 minutes; pending step: '+step)
                due=min(now+300,self.deadline)
            time.sleep(min(30,max(.01,due-time.monotonic())))


class GatedDoor:
    def __init__(self,door,gate):self.door,self.gate=door,gate
    def say(self,command):
        if command.split()[0] not in ('look','rows','help','history','status','holds','components','look-view'):
            self.gate('install '+command.split()[0])
        return self.door.say(command)
    def rows(self,kind,**facts):
        return self.door.rows(kind,**facts)
    def see(self,command):
        out=self.door.request('/see',dict(line=command));assert out['ok'],out;return out


def protected(door):
    tasks=door.rows('taskboard-task')
    return dict(tasks=tasks,histories={t['id']:door.say('history '+t['id'])['rows'] for t in tasks},
                windows=door.rows('window'),window_on=next(r['on'] for r in door.rows('module') if r['name']=='window'))


def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');args=parser.parse_args()
    if not args.live:parser.error('explicit --live required; this script restarts kdesk and installs without opening')
    gate=Gate();gate('before snapshot')
    door=taskboard.live_door();before=protected(door)
    for name in ['kdesk_off.py','kdesk_on.py']:
        gate('adopt source: '+name)
        command=[sys.executable,'-B',str(DESKTOP/name)]+(['--wait'] if name=='kdesk_on.py' else [])
        result=subprocess.run(command,capture_output=True,text=True,creationflags=0x08000000)
        print(result.stdout.strip(),flush=True)
        if result.returncode:raise RuntimeError(result.stderr)
    door=GatedDoor(taskboard.live_door(),gate)
    for spec in modules():
        if not door.rows('module',name=spec['name']):
            door.say(line('module '+spec['name'],run=json.dumps(spec['run']),publishes=spec['publishes'],grants=spec['grants']))
    end=time.monotonic()+30
    while time.monotonic()<end:
        if door.door.request('/see',dict(line='help board.feed')).get('ok'):break
        time.sleep(.2)
    if not door.rows('board-settings'):install(door.say,door.see)
    ids=install_ui(door)
    after=protected(door)
    assert before==after,'Existing tasks/history/windows/provider state changed; inspect before further live work'
    posts=door.see('board.feed')['rows'];assert not posts,'Live board contains existing posts; none were seeded by this installer'
    current=door.rows('widget',name='seabright-board')[0]
    assert current['code']==widget_source()
    reading=door.see('look '+ids['lens'])['rows'][0]
    assert reading['rev']==next(r['rev'] for r in door.rows('lens') if r['id']==ids['lens'])
    evidence=dict(at=datetime.now(timezone.utc).isoformat(),**ids,opened=False,posts_seeded=0,feed_posts=len(posts),
                  tasks_preserved=len(before['tasks']),histories_preserved=True,windows_preserved=len(before['windows']),
                  provider_on=after['window_on'],protected_sha256=digest(before),widget_source_sha256=hashlib.sha256(current['code'].encode()).hexdigest(),
                  source_matches=True,look_revision_verified=True,channels=len(door.rows('board-channel')),
                  kinds=len(door.rows('kind')),orderings=len(door.rows('board-order')))
    (HERE/'evidence/ui/live-install.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print('LIVE BOARD '+json.dumps(evidence,sort_keys=True),flush=True)


if __name__=='__main__':main()
