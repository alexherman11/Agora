"""Record the builder's completion and source friction through live words."""
from pathlib import Path
import sys
import time
from install import taskboard,quote

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'desktop/kernel-desktop'))
from gaming_gate import assert_clear

assert_clear()
d=taskboard.live_door()
text=('JavaScript widget path built for Claude review, no git state changed. Missing world capabilities supplied: '
      'in-page module principal and isolated observations; explicit widget activation and self-description; '
      'portable widget definitions without grants; trusted postMessage bridge; window/bar/overlay mounts; '
      'native iframe network interception; full-desktop alpha painting and hit regions; media artwork/timeline readings; '
      'guy speech/hop happenings and fallback discovery. See src/agora/widgets/WIDGETS.md and WIDGET-PROOF.md. '
      'Live v2 preserves all 25 original task identities, facts and history prefixes. '
      'An initial desktop restart plus one recovery restart were required. Original planned single-restart target was missed. '
      'The live alpha setting was reapplied after navigation; startup does this in source now. '
      'Limits: no hard CPU quota, infinite-loop visual teardown proof, SES, or multiple-monitor proof.')
name='JavaScript widgets — Rough spots'
notes=d.rows('note',name=name)
if notes:
    mid=notes[0]['id'];d.say('look '+mid);assert_clear();d.say('set '+mid+' text='+quote(text))
else:
    assert_clear();d.say('make kind=note name='+quote(name)+' text='+quote(text))
cards=d.rows('taskboard-task',source='builder-js-widgets')
if not cards:
    assert_clear()
    result=d.say('task-add title="JavaScript widgets: sandbox, beautiful views and desktop surfaces" to=Done who=Codex '
                 'when=2026-10-24 source=builder-js-widgets status=done text='+quote(text))
    tid=result['made'][0]
    for _ in range(25):
        row=next(r for r in d.rows('taskboard-task') if r['id']==tid)
        if row.get('short'):break
        time.sleep(.1)
    d.say('look '+tid);assert_clear();d.say('set '+tid+' priority=4 colour=sage note_colour=sage note_style=normal')
print('LIVE: own Done card and Rough spots note recorded; existing work preserved',flush=True)
