# Alex's workspace with the layout words Jeff is lowering (grid tracks, fold, scroll end, measure, verbatim,
# lines). Same world and facts as today.sol; only the lens changes.
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
T do create f01 kind=note title="workspace" tags=lens text="ws : grid 1 3 3 1\n  bar : column, role sheet, fold, of tag:project, each proj\n  chat : column, role sheet, scroll end, the kind:chat as c\n    msgs : text \"$c.text\", role body, verbatim\n    say : text \"\", hint \"Message\", role card.plain, lines 1..8, on edit do append $c.item line=\"$value\"\n  doc : column, role sheet, measure 70ch, the kind:doc as d\n    t : text \"$d.title\", role heading\n    b : text \"$d.text\", role body, lines 3..40, on edit do rewrite $d.item text=\"$value\"\n  tasks : column, role sheet, of tag:bg, each task\nproj : text \"$title\", role meta\ntask : column, role card.plain\n  t : text \"$title\", role title\n  s : text \"$status\", role meta\n  when : text \"$changed.status\", role meta"
probe bar-collapsed-is-mine
probe columns-hold
probe code-formatted

step work
probe finished-task-shows
probe finished-says-when
probe jeff-elsewhere-leaves-my-edit
probe jeff-appends-to-my-doc
