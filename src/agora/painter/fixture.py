"""Controlled scratch world, HTTP actors and two boards over identical facts."""
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import sys
import time

HERE=Path(__file__).resolve().parent;LAB=HERE.parent
sys.path[:0]=[str(LAB),str(LAB.parents[0]/'desktop/kernel-desktop')]
from test_kdesk import Desk
from painter.install import install,taskboard,Q


class Fixture:
    def __init__(self):
        self.d=Desk();self.k=self.d.k;self.url=self.d.url
        self.token=self.d.entry.token('alex');self.door=taskboard.Door(self.url,self.token)
        taskboard.install(self.door)
        settings=self.door.rows('taskboard-settings')[0]
        self.door.say('look '+settings['id']);self.door.say('set '+settings['id']+' model=painter-proof-unavailable')
        # Deterministic unavailable-model fallback; never invokes local inference.
        for rule in self.door.rows('rule'):
            if 'summarize' in str(rule.get('do','')):
                self.door.say('look '+rule['id']);self.door.say('set '+rule['id']+' off=yes')
        self.tasks=[]
        titles=['Fix the bar before the neighbourhood demo','Confirm the accessible entrance','Review invitation wording',
                'Print a large type agenda','Ask the library about the projector','Prepare tea and a quiet corner',
                'Check the microphone reaches the back row','Write a welcome for newcomers','Collect crossing questions',
                'Share the bus timetable','Check door signage; include the side entrance','Bring spare pens',
                'Confirm chairs and space for wheelchairs','Draft follow-up for volunteers','Test the map on a phone',
                'Ask neighbours to review the board','Set aside a break','Prepare the host checklist',
                'Find council meeting notes','Summarize meeting actions','Keep original notes alongside summary',
                'Arrange a ride home','Recheck dates on flyers','Thank the setup team','Plan the next small step']
        for i,title in enumerate(titles):
            lane='Backlog' if i<16 else 'Now' if i<23 else 'Done'
            t=self.door.say(f'task-add title={Q(title)} to={lane} who={"Alex" if i%2==0 else "JEFF"} '
                            f'text={Q(title)} source=painter-proof-{i} status=open when=2026-10-24')['made'][0]
            self.door.say('look '+t);self.door.say(f'set {t} priority={i%4+1} colour={"sage" if i==1 else "paper"} '
                f'short={Q(title)} short_source=local-fallback note={Q("## Evening notes"+chr(10)+"**Welcome** every neighbour."+chr(10)+"- [ ] Bring tea" if i<2 else "")} note_colour=sage')
            self.tasks.append(t)
        self.ids=install(self.door)
        # Only install the JS board. The rejected desktop-guy demos stay off.
        source='\n\n'.join((LAB/'widgets'/f).read_text(encoding='utf-8') for f in ('common.js','taskboard.js'))
        self.js=self.door.say('make kind=widget name=taskboard-js title="Task board · JavaScript" style=bars code='+Q(source))['made'][0]
        self.door.say('look '+self.js)
        self.door.say('widget '+self.js+' grants="window.surface describe rows look history task-add task-move task-assign task-done task-note task-priority task-colour task-note-colour task-note-style task-filter task-rename task-edit task-text task-remove summarize.* make set forget undo hear:make hear:set hear:forget hear:undo" only=kind:taskboard-task,taskboard-settings')

    def close(self):self.d.close()
