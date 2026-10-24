"""Serialize the app's authored definitions to directly speakable install.lines."""
from pathlib import Path
from install import quote

HERE = Path(__file__).resolve().parent
LENS = '''root : column, role sheet
  let backlog = count(tag:taskboard-task,prop:lane=Backlog)
  let now = count(tag:taskboard-task,prop:lane=Now)
  let done = count(tag:taskboard-task,prop:lane=Done)
  heading : text "Task board", role heading
  hint : text "Drag cards between lanes. History stays with the work. Today: $today", role meta
  toolbar : row, role tools
    undo : text "Undo my last act", role tool, on click do undo
    add : text "", role tool, hint "New task — type a title", commit enter, on edit do task-add title=$value to=Backlog who=Alex when=$today source=local status=open text=""
  board : row, grid 1fr 1fr 1fr, gap x2
    backlog : column, role lane, on drop card do task-move $carried to=Backlog
      heading : text "Backlog · $backlog", role lane.backlog
      cards : column, of tag:taskboard-task,prop:lane=Backlog as task, each card
    now : column, role lane, on drop card do task-move $carried to=Now
      heading : text "Now · $now", role lane.now
      cards : column, of tag:taskboard-task,prop:lane=Now as task, each card
    done : column, role lane, on drop card do task-done $carried
      heading : text "Done · $done", role lane.done
      cards : column, of tag:taskboard-task,prop:lane=Done as task, each card
card : column, role card, carry
  title : text "$title", role title
  who : text "$who · $when", role meta
  status : text "Source status: $source_status", role meta
  moves : row, role tools
    backlog : text "Backlog", role tool, on click do task-move $item to=Backlog
    now : text "Now", role tool, on click do task-move $item to=Now
    done : text "Done", role tool, on click do task-done $item
    take : text "Take", role tool, on click do claim $item
  details : column, fold "Details", role group
    prose : text "$text", role body
  history : column, fold "History", role group
    created : text "Created $made_at by $by · changed $changed_at", role meta
    trail : column, of history:$task.id as event, each event
  note : text "", role tool, hint "Add a note…", commit enter, on edit do task-note $item text=$value
event : column, role event
  action : text "$word · $changes", role body
  by : text "$by · $at", role meta
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
    from v2 import lens, style, VERBS
    lines = ['# Task board v2: structure, appearance and actions are world definitions; summarize is a separate process.',
             '# Say each non-comment physical line through /do. install.py skips existing definitions.']
    for kind in ('taskboard-task', 'taskboard-lane'):
        lines.append('make kind=kind name=' + kind + ' help=' + quote('Task board ' + kind.removeprefix('taskboard-')))
    for i, lane in enumerate(('Backlog', 'Now', 'Done')):
        lines.append(f'make kind=taskboard-lane name={lane} order={i}')
    verbs = [
        ('add', 'title=<text> to=<lane> who=<name> when=<date> source=<key> status=<text> text=<text>',
         'make kind=taskboard-task title=$title lane=$to who=$who when=$when source=$source source_status=$status text=$text seats=1',
         'task.add title="A title" to=Backlog who=Alex when=2026-10-24 source=local status=open text="Details": add a card. Source status remains the imported status.'),
        ('move', '<id> to=<lane>',
         'set $1 lane=$to',
         'task-move <task> to=Backlog|Now|Done: move a card. Look first when typing. History reads its record; undo reverses the move.'),
        ('assign', '<id> who=<name>',
         'set $1 who=$who',
         'task-assign <task> who=<name>: assign the work. Look first. History reads the actual record.'),
        ('done', '<id>',
         'set $1 lane=Done',
         'task-done <task>: finish the card in one undoable act. Its own happening triggers the board announcement rule.'),
        ('note', '<id> text=<text>',
         'set $1 note=$text',
         'task-note <task> text="A note": record a note on the card. History keeps earlier notes. Undo takes it back.'),
    ]
    verbs += [(n, t, s, 'task-' + n + ' ' + t + ': ' + h) for n, t, s, h in VERBS]
    for name, takes, steps, help_ in verbs:
        lines.append(f'verb task-{name} takes={quote(takes)} steps={quote(steps)} help={quote(help_.replace("task.", "task-"))}')
    lines.append('make kind=taskboard-settings name=taskboard filter=all model=qwen2.5:3b')
    lines.append('make kind=style name=taskboard text=' + quote(style(STYLE)))
    lines.append('make kind=lens name=taskboard style=taskboard text=' + quote(lens()))
    lines.append('make kind=rule name="Task board automatic summaries" on=make of_kind=taskboard-task do=' + quote('summarize.task $target'))
    lines.append('make kind=rule name="Task board Done announcement" on=task-done of_kind=taskboard-task do=' + quote('post "Task completed" about=$target'))
    HERE.joinpath('install.lines').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'{len(lines)-2} install lines written')


if __name__ == '__main__':
    main()
