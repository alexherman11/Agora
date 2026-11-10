"""Freeze code bytes and one canonical scratch world; never a git operation."""
from datetime import timedelta
import hashlib
import json
from pathlib import Path
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from painter.fixture import Fixture
from painter.install import Q
from painter.fresh_agent import ROOT

HERE=Path(__file__).resolve().parent;LAB=HERE.parent
FROZEN=ROOT/'local/painter-trials/frozen'


def paths():
    return [*sorted((LAB/'components').glob('*.js')),*(HERE/name for name in
        ('arrangement.py','painter.js','primitives.js','theme.js','catalogue.py','install.py','ARRANGEMENT.md','REACH.md')),
        LAB/'apps/taskboard/component-board.lens',LAB/'widgets/common.js',LAB/'widgets/taskboard.js']


def verify(source_root=ROOT):
    manifest=json.loads((HERE/'FREEZE.json').read_text(encoding='utf-8'))
    for name,expected in manifest['sha256'].items():
        assert hashlib.sha256((source_root/name).read_bytes()).hexdigest()==expected,'Frozen bytes changed: '+name
    return manifest


def main():
    if (HERE/'FREEZE.json').exists():raise RuntimeError('Already frozen; do not silently replace a trial baseline.')
    f=Fixture()
    try:
        now=f.k.now().replace(microsecond=0)
        for i,t in enumerate(f.tasks):
            f.door.say('look '+t)
            extra=''
            if i%5==0:extra+=' due='+('2026-10-23' if i%2==0 else '2026-10-26')
            if i==3:extra+=' title='+Q('Prepare a thoughtful and accessible welcome for every neighbour, including people arriving late, people who need a quieter corner, and the volunteers helping them find their way')+' short='
            f.door.say('set '+t+' who='+Q('Alex Anderson' if i%2==0 else 'Jeff Builder')+extra)
        # Deliberately controlled record clock. Old/recent lane entry and an
        # unrelated recent note distinguish time-in-lane from last modification.
        for index,days in ((16,6),(20,4),(12,2)):
            t=f.tasks[index];f.k.clock=lambda:now-timedelta(days=days)
            f.door.say('look '+t);f.door.say('task-move '+t+' to=Backlog');f.door.say('look '+t);f.door.say('task-move '+t+' to=Now')
        f.k.clock=lambda:now-timedelta(days=1)
        f.door.say('look '+f.tasks[16]);f.door.say('task-note '+f.tasks[16]+' text="A recent note does not reset entry into Now."')
        f.k.clock=lambda:now
        peer=f.k.join('proof:neighbour','Neighbour',invite={'admitted':True})['person']
        f.d.entry.sessions['peer']={'account':'proof:neighbour','method':'proof','signer':'peer'}
        # LocalEntry persists only this synthetic scratch identity.
        f.d.entry.path.write_text(json.dumps(f.d.entry.sessions),encoding='utf-8')
        FROZEN.parent.mkdir(parents=True,exist_ok=True)
        with f.k.lock:shutil.copytree(Path(f.d.dir)/'world',FROZEN)
        manifest=dict(at=now.isoformat(),tasks=f.tasks,ids=f.ids,js=f.js,peer=peer,
            task_facts=f.door.rows('taskboard-task'),
            sha256={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths()},
            note='One scratch log snapshot for every run. Simulated original record clocks for time-in-lane. No tweak handles were added after this freeze.')
        (HERE/'FREEZE.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        print('FROZEN',len(manifest['sha256']),'source files;',len(f.tasks),'identical task rows; no git state changed.',flush=True)
    finally:f.close()


if __name__=='__main__':main()
