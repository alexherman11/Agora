"""Serialize the app's authored definitions to directly speakable install.lines."""
from pathlib import Path
from install import quote

HERE = Path(__file__).resolve().parent
LENS = '''root : column, role sheet
  let backlog = count(tag:taskboard-task,prop:lane=Backlog)
  let now = count(tag:taskboard-task,prop:lane=Now)
  let done = count(tag:taskboard-task,prop:lane=Done)
  heading : text "Task board", role heading
  hint : text "Things + words + a view. Move cards with the lane buttons. History stays with the work.", role meta
  toolbar : row, role tools
    undo : text "Undo my last act", role tool, on click do undo
    add : text "", role tool, hint "New task — type a title", commit enter, on edit do task.add title=$value to=Backlog who=Alex when="Added here" source=local status=open text=""
  board : row, grid 1fr 1fr 1fr, gap x2
    backlog : column, role lane, on drop card do task.move $carried to=Backlog when=recorded
      heading : text "Backlog · $backlog", role lane.backlog
      cards : column, of tag:taskboard-task,prop:lane=Backlog as task, each card
    now : column, role lane, on drop card do task.move $carried to=Now when=recorded
      heading : text "Now · $now", role lane.now
      cards : column, of tag:taskboard-task,prop:lane=Now as task, each card
    done : column, role lane, on drop card do task.done $carried when=recorded
      heading : text "Done · $done", role lane.done
      cards : column, of tag:taskboard-task,prop:lane=Done as task, each card
card : column, role card, carry
  title : text "$title", role title
  who : text "$who · $when", role meta
  status : text "Source status: $source_status", role meta
  moves : row, role tools
    backlog : text "Backlog", role tool, on click do task.move $item to=Backlog when=recorded
    now : text "Now", role tool, on click do task.move $item to=Now when=recorded
    done : text "Done", role tool, on click do task.done $item when=recorded
    take : text "Take", role tool, on click do claim $item
  details : column, fold "Details", role group
    prose : text "$text", role body
  history : column, fold "History", role group
    created : text "Created by $by · source $source_status", role meta
    trail : column, of tag:taskboard-event,prop:about=$task.id as event, each event
  note : text "", role tool, hint "Add a note…", commit enter, on edit do task.note $item text=$value when=recorded
event : column, role event
  action : text "$text", role body
  by : text "$by", role meta
  actor : text "Claimed by $actor_title", role meta, only when $actor != ""
'''

STYLE = '''token paper = #F5F3ED
token card = #FFFFFF
token ink = #263746
token accent = #3F697D
token sage = #457564
token warn = #A24E2C
token gap = 8
token ramp = 1.15
token text = ui 15/1.5
token sheet = paper
token line = ink at 18%
token faint = ink at 10%
token quiet = ink at 82%
token hush = ink at 62%
role sheet : on paper, ink, text, pad gap x2, between gap
role heading : text up 2 medium, ink
role lane : on accent at 4%, pad gap, corner gap, between gap
role lane.backlog : on accent at 12%, accent, text medium, pad gap, corner gap /2
role lane.now : on warn at 10%, warn, text medium, pad gap, corner gap /2
role lane.done : on sage at 12%, sage, text medium, pad gap, corner gap /2
role card : on card, ink, text, pad gap x1.5, edge faint, corner gap, space below gap, between gap /2
role title : text medium, ink
role body : text down, quiet
role meta : text down 2, hush
role tools : between gap, pad gap /2
role tool : text down, accent, on accent at 6%, pad gap /2, corner gap /2
role tool.on : on accent at 14%, accent
role fold : text down 2, hush
role group : between gap /2
role event : border top faint, pad gap /2
role landing : on sage at 12%, edge sage, corner gap
role refusal : text down, warn, on warn at 8%, pad gap
'''

def main():
    lines = ['# Task board: literal world lines. No module, host patch or executable app code.',
             '# Say each non-comment physical line through /do. install.py skips existing definitions.']
    for kind in ('taskboard-task', 'taskboard-event', 'taskboard-lane'):
        lines.append('make kind=kind name=' + kind + ' help=' + quote('Task board ' + kind.removeprefix('taskboard-')))
    for i, lane in enumerate(('Backlog', 'Now', 'Done')):
        lines.append(f'make kind=taskboard-lane name={lane} order={i}')
    verbs = [
        ('add', 'title=<text> to=<lane> who=<name> when=<date> source=<key> status=<text> text=<text>',
         'make kind=taskboard-task title=$title lane=$to who=$who when=$when source=$source source_status=$status text=$text seats=1',
         'task.add title="A title" to=Backlog who=Alex when=2026-10-24 source=local status=open text="Details": add a card. Source status remains the imported status.'),
        ('move', '<id> to=<lane>',
         'set $1 lane=$to; make kind=taskboard-event about=$1 text=$to',
         'task.move <task> to=Backlog|Now|Done: move a card. Look first when typing. One act records the move and its authored trail; undo reverses both.'),
        ('assign', '<id> who=<name>',
         'set $1 who=$who; make kind=taskboard-event about=$1 text=$who',
         'task.assign <task> who=<name>: assign the work. Look first. The history thing is authored by the real caller.'),
        ('done', '<id>',
         'set $1 lane=Done; make kind=taskboard-event about=$1 text="Moved to Done"',
         'task.done <task>: finish the card, recording the move and history in one undoable act.'),
        ('note', '<id> text=<text>',
         'make kind=taskboard-event about=$1 text=$text',
         'task.note <task> text="A note": add an authored, recorded history note. Undo takes it back.'),
    ]
    for name, takes, steps, help_ in verbs:
        lines.append(f'verb task-{name} takes={quote(takes)} steps={quote(steps)} help={quote(help_)} as=entry; rename $entry word=task.{name}')
    lines.append('make kind=style name=taskboard text=' + quote(STYLE))
    lines.append('make kind=lens name=taskboard style=taskboard text=' + quote(LENS))
    lines.append('make kind=rule name="Task board claim history" on=claim do=' + quote('make kind=taskboard-event about=$target text="Work claimed" actor=$by'))
    HERE.joinpath('install.lines').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'{len(lines)-2} install lines written')


if __name__ == '__main__':
    main()
