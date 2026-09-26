# Viewer state in the proposed words (Juniper a475 `view open=`, the codex contract's `on click view open=$item`,
# sable-10's declared frame read through the accessor and recorded in R). Same world and moments as today.sol.
# `view k=v` writes the frame of this observer (actor + window) for this placed lens, never the world; `$viewer.k`
# reads it, and the read is printed and recorded; an unset key drops the term it is in (the filter below).
# Today the notes and tasks lenses are refused and their probes are n/e; the bar and chat use today's words.

step set
T do create f01 kind=note title="Agora" tags=project text="The research project."
T do create f01 kind=note title="Trip" tags=project text="Big Sur, October."
T do create f01 kind=note title="Charter" text="Living on notes and the fence."
T do create f01 kind=note title="Groceries" text="eggs, rice"
T do create f01 kind=note title="Fence notes" text="The fence refuses stale writes."
T do create f01 kind=task title="Run the suite" status=done
T do create f01 kind=task title="Write the viewer case" status=doing
T do create f01 kind=task title="Index the trip photos" status=done
T do create f01 kind=task title="Call the landlord" status=todo
T do create f01 kind=chat title="With JEFF" text="Alex: is the suite green?"
T do create f01 kind=note title="bar" tags=lens text="bar : column, role sheet, fold \"Projects\", of tag:project, each proj\nproj : text \"$title\", role meta"
T do create f01 kind=note title="chat" tags=lens text="c : column, role sheet, scroll end, the kind:chat as ch\n  msgs : text \"$ch.text\", role body\n  say : text \"\", hint \"Message\", role card.plain, lines 1..8, on edit do append $ch.item line=\"$value\""
T do create f01 kind=note title="notes" tags=lens text="notes : grid 1 3\n  side : column, role sheet\n    search : text \"$viewer.query\", hint \"Search\", role card.plain, on edit view query=\"$value\"\n    found : column, of kind:note,-tag:lens,?$viewer.query, each entry\n    list : column, of kind:note,-tag:lens,-tag:project, each entry\n  page : column, role sheet, the $viewer.open as cur\n    t : text \"$cur.title\", role heading\n    b : text \"$cur.text\", role body, lines 3..40, on edit do rewrite $cur.item text=\"$value\"\nentry : text \"$title\", role meta, on click view open=$item"
T do create f01 kind=note title="tasks" tags=lens text="tasks : column, role sheet\n  hide : text \"Hide done\", role meta, on click view hide=done\n  list : column, of kind:task,-prop:status=$viewer.hide, each task\ntask : row\n  t : text \"$title\", role title\n  s : text \"$status\", role meta"
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
