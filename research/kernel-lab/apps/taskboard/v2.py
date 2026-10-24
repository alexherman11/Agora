"""Authored lens and style, serialized by build_lines; no browser app code."""
from pathlib import Path

PALETTE = dict(paper='#FFFFFF', rose='#FBE9E8', peach='#FFF0DC', sage='#EAF3E9', sky='#E8F1FA', lilac='#F0EBF8')


def lens():
    s = '''root : column, role sheet
  the tag:taskboard-settings
  as view
  let backlog = count(tag:taskboard-task,prop:lane=Backlog)
  let now = count(tag:taskboard-task,prop:lane=Now)
  let done = count(tag:taskboard-task,prop:lane=Done)
  heading : text "Task board", role heading
  hint : text "A little space for what matters. Drag to move · right-click for actions.", role meta
  toolbar : row, role tools
    add : text "", role input, hint "Add a task… try Fix the bar p1", commit enter, on edit do summarize.add text="$value"
    undo : text "Undo my last act", role tool, on click do undo
  filters : row, role tools
'''
    for p in ('all', '1', '2', '3', '4'):
        label = 'All tasks' if p == 'all' else 'P' + p
        test = '"all"' if p == 'all' else p
        s += f'    p{p} : text "{label}", role tool, role tool.on when $filter = {test}, on click do task-filter $item priority={p}\n'
    s += '''    summary : text "Summarize board", role tool, on click do summarize.all
  empty : text "A clear board. Add your first task above; p1–p4 sets its priority.", role empty
    only when count(tag:taskboard-task) = 0
  board : row, grid 1fr 1fr 1fr, gap x2
'''
    for key, lane in [('backlog', 'Backlog'), ('now', 'Now'), ('done', 'Done')]:
        s += f'    {key} : column, role lane, on drop card do task-move $carried to={lane}\n'
        s += f'      heading : text "{lane} · ${key}", role lane.{key}\n'
        s += f'      summary : text "Summarize lane", role smalltool, on click do summarize.all lane={lane}\n'
        if key == 'done':
            s += '      completed : column, fold "Completed tasks", role group\n'
            indent = '        '
        else:
            indent = '      '
        s += indent + f'cards : column, of tag:taskboard-task,prop:lane={lane} as task, by priority, each card\n'
    s += '''  help : column, fold "Help & shortcuts", role group
    prose : text "Quick add: description p1–p4 (default p4). Click Details for full text and notes. Right-click a card for priorities, colour, moves, assignment, rename, summary and removal. Drag across lanes. Done folds. All/P1–P4 filter the board. Undo reverses your last act; if another edit depends on it, it refuses safely.", role body
    notes : text "Notes: Ctrl+B bold · Ctrl+I italic · Ctrl+E Markdown source · Ctrl+S save. Checklist source: - [ ] item. Right-click the note for six colours and three styles. Changes and undo stay in History. Summary labels always name the source. Model setting: model-settings model=qwen2.5:3b. Off: off model stops inference; off summarize stops board adapters.", role body
card : column, role card, carry
  only when $view.filter = "all" or $priority = $view.filter
  let description = $short when $short != ""
  let description = $title otherwise
'''
    for name in PALETTE:
        if name != 'paper':
            s += f'  role card.{name} when $colour = "{name}"\n'
    for p in range(1, 5):
        s += f'  on menu "Priority · P{p}" do task-priority $item priority={p}\n'
    for name in PALETTE:
        s += f'  on menu "Colour · {name.title()}" do task-colour $item colour={name}\n'
    for lane in ('Backlog', 'Now', 'Done'):
        s += f'  on menu "Move · {lane}" do task-move $item to={lane}\n'
    s += '''  on menu "Assign · me" do task-assign $item who=Alex
  on menu "Assign · my agent" do task-assign $item who=JEFF
  on menu "Rename" do task-rename $item title="$value"
  on menu "Summarize" do summarize.task $item
  on menu "Remove · undo brings it back" do task-remove $item
  summary : row, role summary
'''
    # Same pinned Lucide release/ISC licence as the desktop; no runtime fetch.
    icon = Path(__file__).parent / 'icons/flag.svg'
    svg = ' '.join(icon.read_text(encoding='utf-8').split()).replace('currentColor', 'var(--t-priority)').replace('"', "'")
    head, body = svg.split('>', 1)
    svg = head + "><g fill='none'>" + body.replace('</svg>', '</g></svg>')
    for p in range(1, 5):
        art = svg.replace('var(--t-priority)', 'var(--t-p' + str(p) + ')')
        s += f'    p{p} : text "{art}", picture, role icon\n'
        s += f'      only when $priority = {p}\n'
    s += '''    short : text "$description", role title, clamp 1
  provenance : text "$short_source", role provenance
    only when $short_source != ""
  details : column, fold "Details", role group
    title : text "$title", role input, hint "Full description / rename", on edit do task-rename $item title="$value"
    full : text "$text", markdown, role body, on edit do summarize.save $item field=text text="$value"
    who : text "Assigned to $who · source: $source_status", role meta
    editor : column, role note
'''
    for name in PALETTE:
        if name != 'paper':
            s += f'      role note.{name} when $note_colour = "{name}"\n'
        s += f'      on menu "Note colour · {name.title()}" do task-note-colour $item colour={name}\n'
    for name in ('normal', 'strong', 'slant'):
        s += f'      on menu "Note style · {name}" do task-note-style $item style={name}\n'
    s += '''      heading : text "Notes", role title
      toolbar : row, role tools
        bold : text "Bold", role tool, on click press Ctrl+B
        italic : text "Italic", role tool, on click press Ctrl+I
        source : text "Checklist / source", role tool, on click press Ctrl+E
        save : text "Save", role tool, on click press Ctrl+S
      prose : text "$note", markdown, role editor, hint "Write a note…", on edit do summarize.save $item field=note text="$value"
        role editor.strong when $note_style = "strong"
        role editor.slant when $note_style = "slant"
      tip : text "Checklist: - [ ] item · Ctrl+B bold · Ctrl+I italic · Ctrl+S save", role meta
    history : column, fold "History", role group
      created : text "Created $made_at by $by · changed $changed_at", role meta
      trail : column, of history:$task.id as event, each event
event : column, role event
  action : text "$word · $changes", role body
  by : text "$by · $at", role meta
'''
    return s


def style(base):
    base = base.replace('#F5F3ED', '#FAF9F6').replace('ui 15/1.5', 'ui 15/1.5')
    base += '''
token p1 = #CF514A
token p2 = #C58332
token p3 = #507EBC
token p4 = #9BA3AC
role summary : between gap
role icon : width gap x2, height gap x2
role provenance : text down 3, hush
role input : on card, ink, edge faint, pad gap, corner gap /2, height gap x4
role smalltool : text down 2, hush, pad gap /2
role empty : text, hush, pad gap x3
role note : on card, pad gap x2, corner gap
role editor : text, ink, height gap x18, pad gap
role editor.strong : text strong, ink, height gap x18, pad gap
role editor.slant : text slant, ink, height gap x18, pad gap
'''
    for name, colour in PALETTE.items():
        if name != 'paper':
            base += f'token pastel_{name} = {colour}\n'
            base += f'role card.{name} : on pastel_{name}, ink, text, pad gap x1.5, edge faint, corner gap, space below gap, between gap /2\n'
            base += f'role note.{name} : on pastel_{name}, pad gap x2, corner gap\n'
    return base


VERBS = [
    ('priority', '<id> priority=<1..4>', 'set $1 priority=$priority', 'Set priority 1 red, 2 orange, 3 blue, 4 grey; sorted within lanes.'),
    ('colour', '<id> colour=<name>', 'set $1 colour=$colour', 'Card colour: paper, rose, peach, sage, sky, lilac.'),
    ('note-colour', '<id> colour=<name>', 'set $1 note_colour=$colour', 'Note colour: paper, rose, peach, sage, sky, lilac.'),
    ('note-style', '<id> style=<normal|strong|slant>', 'set $1 note_style=$style', 'Set the note text style; Markdown marks remain editable.'),
    ('filter', '<id> priority=<all|1..4>', 'set $1 filter=$priority', 'Choose All or a priority chip; this shared board filter is a world fact.'),
    ('rename', '<id> title=<text>', 'set $1 title=$title editing=no', 'Rename a task, retaining its full text and history; use Summarize to refresh short.'),
    ('edit', '<id>', 'set $1 editing=yes', 'Show the inline rename field; enter saves it.'),
    ('text', '<id> text=<text>', 'set $1 text=$text', 'Edit the full task text as Markdown.'),
    ('remove', '<id>', 'forget $1', 'Remove a task; undo brings it back with its history.'),
]
