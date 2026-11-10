# Alex's workspace in today's words (main, after Jeff's staged evaluator). Four regions in one row; the bar
# cannot fold, the columns cannot hold, the chat cannot format code. The probes say which facts hold today and
# which wait for a word (n/e). Rewrite this file when tracks, fold and blocks land; the facts stay in task.py.
recorded M3=1

step set
T do create f01 kind=note title="Agora" tags=project text="The research project."
T do create f01 kind=note title="Trip" tags=project text="Big Sur, October."
T do create f01 kind=chat title="With JEFF" text="Alex: why does the fence refuse my edit?"
T do append "With JEFF" line="Jeff: Because the card changed since you painted it:\n```\nif seen.rev != now.rev: refuse()\n```"
T do create f01 kind=doc title="Draft: painter continuity" text="Painter continuity\nEvery gesture works in a real browser."
T do create f01 kind=note title="JEFF notes" text="Working notes."
T do create f01 kind=task title="Run the suite" owner=jeff status=doing tags=bg
T do create f01 kind=task title="Index the trip photos" owner=jeff status=doing tags=bg
T do create f01 kind=note title="workspace" tags=lens text="ws : row\n  bar : column, role sheet, of tag:project, each proj\n  chat : column, role sheet, the kind:chat as c\n    msgs : text \"$c.text\", role body\n  doc : column, role sheet, the kind:doc as d\n    t : text \"$d.title\", role heading\n    b : text \"$d.text\", role body, on edit do rewrite $d.item text=\"$value\"\n  tasks : column, role sheet, of tag:bg, each task\nproj : text \"$title\", role meta\ntask : column, role card.plain\n  t : text \"$title\", role title\n  s : text \"$status\", role meta"
probe bar-collapsed-is-mine
probe columns-hold
probe code-formatted

step work
probe finished-task-shows
probe finished-says-when
probe jeff-elsewhere-leaves-my-edit
probe jeff-appends-to-my-doc
