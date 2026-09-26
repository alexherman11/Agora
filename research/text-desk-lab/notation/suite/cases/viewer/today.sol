# Viewer state in today's words: what a person reaches for without a viewer frame. The open note is a shared tag
# `open` (a click moves it: two commands in one line); the search and the "hide done" filter are props of the lens
# note, which is the only place a lens can keep a choice. The probes in task.py judge the moments; frame.sol says
# the same moments in the proposed words.

step set
T do create f01 kind=note title="Agora" tags=project text="The research project."
T do create f01 kind=note title="Trip" tags=project text="Big Sur, October."
T do create f01 kind=note title="Charter" tags=open text="Living on notes and the fence."
T do create f01 kind=note title="Groceries" text="eggs, rice"
T do create f01 kind=note title="Fence notes" text="The fence refuses stale writes."
T do create f01 kind=task title="Run the suite" status=done
T do create f01 kind=task title="Write the viewer case" status=doing
T do create f01 kind=task title="Index the trip photos" status=done
T do create f01 kind=task title="Call the landlord" status=todo
T do create f01 kind=chat title="With JEFF" text="Alex: is the suite green?"
T do create f01 kind=note title="bar" tags=lens text="bar : column, role sheet, fold \"Projects\", of tag:project, each proj\nproj : text \"$title\", role meta"
T do create f01 kind=note title="chat" tags=lens text="c : column, role sheet, scroll end, the kind:chat as ch\n  msgs : text \"$ch.text\", role body\n  say : text \"\", hint \"Message\", role card.plain, lines 1..8, on edit do append $ch.item line=\"$value\""
T do create f01 kind=note title="notes" tags=lens text="notes : grid 1 3\n  side : column, role sheet\n    search : text \"$q\", hint \"Search\", role card.plain, on edit do prop notes q=\"$value\"\n    found : column, of kind:note,-tag:lens,?$q, each entry\n    list : column, of kind:note,-tag:lens,-tag:project, each entry\n  page : column, role sheet, the tag:open as cur\n    t : text \"$cur.title\", role heading\n    b : text \"$cur.text\", role body, lines 3..40, on edit do rewrite $cur.item text=\"$value\"\nentry : text \"$title\", role meta, on click do tag tag:open remove=open; do tag $item add=open"
T do create f01 kind=note title="tasks" tags=lens text="tasks : column, role sheet\n  hide : text \"Hide done\", role meta, on click do prop tasks hide=done\n  list : column, of kind:task,-prop:status=$hide, each task\ntask : row\n  t : text \"$title\", role title\n  s : text \"$status\", role meta"
probe fold-is-paint
probe scroll-end-is-paint

step live
probe open-binds-the-page
probe open-makes-no-event
probe open-is-mine
probe draft-follows-its-thing
probe search-binds-the-list
probe filter-says-what-it-hides
probe open-survives-new-rows
probe open-survives-edit
probe alias-after-merge
probe open-survives-rename
probe open-carries-its-read
probe open-thing-gone
