# desk-big-recheck-1  task=big variant=lean
prompt: Somewhere on this desk are the notes and tasks for the Harbor project. Collect all of them into a new column called Harbor on the left of the desk, soonest due first, and make sure none of them is still showing anywhere else. You have a budget of 40 desk calls; it is a big desk, so do not read everything.

[1 @4.61s] desk: look
    f01 surface "desk" row · 1280x800 · 3 inside
      f02 surface "Inbox" column · 6 inside  (open f02 to see inside)
      f68 surface "Mid" column · 2 inside  (open f68 to see inside)
      f05 surface "Pile" free · 7 inside  (open f05 to see inside)

[2 @6.14s] desk: find Harbor
    find 'Harbor': 6 hit(s)
      a60 note "Kickoff notes" · due 2026-09-20 · 10w  in f02
      a61 task "Order pier sensors" · 260x140 at 40,40 · due 2026-09-18 · 7w · hidden by a63  in f03
      a64 note "Tide feed" · due 2026-09-17 · 10w  in f06
      a65 task "Permit renewal" · 260x140 at 300,200 · due 2026-09-30 · 10w · also x1  in f04
      a66 task "Permit renewal" · 260x140 at 20,40 · due 2026-09-30 · 10w · also x1  in f05
      a67 task "Dock survey" · 260x140 at 30,200 · due 2026-09-25 · 7w  in f05
      as a selection: ?harbor   e.g. do move ?harbor into=<surface> one=1   (help selections)

[3 @9.88s] desk: examine f01
    f01 surface "desk" row · 1280x800 · 3 inside · try: sort
      a row surface (the desk itself), holding 3 thing(s):
        f02 surface "Inbox" column · 6 inside  (examine f02 for inside)
        f68 surface "Mid" column · 2 inside  (examine f68 for inside)
        f05 surface "Pile" free · 7 inside  (examine f05 for inside)
      where: screen 0,0 1280x800 · in - (-) · clear
      verbs: tile untile rename group create sort   (help <verb> for args; the target may be a selection: help selections)

[4 @11.58s] desk: help create; help move; help sort
    [1] help create
    create  (on: surface; level 1)
      Make a new note, task, chat, doc, image or surface inside this surface.
      args: kind=note|task|chat|doc|image|surface title=<str> [text=<str>] [due=YYYY-MM-DD] [tags=a,b] [layout=column|row|free]
      e.g. do create f03 kind=task title="Send parser" due=2026-09-19
    
    [2] help move
    move  (on: thing; level 1)
      Put this somewhere else.
      args: into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>
      e.g. do move a04 into=f02
    
    [3] help sort
    sort  (on: surface; level 2)
      Reorder the children of a tiled surface.
      args: by=due|title|kind [desc=1]
      e.g. do sort f02 by=due

[5 @13.78s] desk: do create f01 kind=surface title="Harbor" layout=column
    ok create f01 kind=surface title=Harbor layout=column  [e1] → created f69
      f69 surface "Harbor" column · empty
      new column surface f69 inside f01
      now: f01 surface "desk" row · 1280x800 · 4 inside

[6 @15.72s] desk: do move f69 before=f02
    ok move f69 before=f02  [e2]
      now: f69 surface "Harbor" column · empty  (1st of 4 in f01)

[7 @19.52s] desk: help selections
    selections: a target can be one id, or a selection that names many things:
      ?tide+parser       things whose title, text or tags contain all the words
      kind:image         by kind (kind:note|task for several)
      tag:harbor         by tag
      in:f04             inside surface f04, recursively
      hidden             more than 5% covered by something
      also:a18           the other appearances of a18's subject
      due<2026-09-20     due before (due> after)
      age<2              touched within the last 2 days by the clock (age>7: untouched for a week); needs clock
      title:agenda       title contains the word
      a20,a22            an explicit list
    combine terms with commas (AND): kind:image,in:f04. The receipt lists everything the verb touched.
    find <selection> lists what it matches, grouped by surface: find kind:image   find tag:harbor,in:f04   find hidden
    e.g. do move ?harbor into=f02 one=1     do raise hidden,in:f04     do group kind:image,in:f04 as=column title=Pictures

[8 @26.17s] desk: do move a60 into=f69; do move a61 into=f69; do move a64 into=f69; do move a65 into=f69
    [1] do move a60 into=f69
    ok move a60 into=f69  [e3]
      now: a60 note "Kickoff notes" · due 2026-09-20 · 10w  (1st of 1 in f69)
    
    [2] do move a61 into=f69
    ok move a61 into=f69  [e4]
      now: a61 task "Order pier sensors" · due 2026-09-18 · 7w  (2nd of 2 in f69)
    
    [3] do move a64 into=f69
    ok move a64 into=f69  [e5]
      now: a64 note "Tide feed" · due 2026-09-17 · 10w  (2nd of 3 in f69)
    
    [4] do move a65 into=f69
    ok move a65 into=f69  [e6]
      now: a65 task "Permit renewal" · due 2026-09-30 · 10w · also x1  (2nd of 4 in f69)

[9 @29.92s] desk: do move a67 into=f69; do remove a66; do sort f69 by=due
    [1] do move a67 into=f69
    ok move a67 into=f69  [e7]
      now: a67 task "Dock survey" · due 2026-09-25 · 7w  (2nd of 5 in f69)
    
    [2] do remove a66
    ok remove a66  [e8]
      appearance removed; the subject still exists
    
    [3] do sort f69 by=due
    ok sort f69 by=due  [e9..e13, 5 steps]
      order now: a64, a61, a60, a67, a65
      now: f69 surface "Harbor" column · 5 inside  (1st of 4 in f01)
      a64 note "Tide feed" · due 2026-09-17 · 10w
      a61 task "Order pier sensors" · due 2026-09-18 · 7w
      a60 note "Kickoff notes" · due 2026-09-20 · 10w
      a67 task "Dock survey" · due 2026-09-25 · 7w
      a65 task "Permit renewal" · due 2026-09-30 · 10w

[10 @31.64s] desk: look f01; find Harbor
    [1] look f01
    f01 surface "desk" row · 1280x800 · 4 inside
      f69 surface "Harbor" column · 5 inside  (open f69 to see inside)
      f02 surface "Inbox" column · 5 inside  (open f02 to see inside)
      f68 surface "Mid" column · 2 inside  (open f68 to see inside)
      f05 surface "Pile" free · 5 inside  (open f05 to see inside)
    
    [2] find Harbor
    find 'Harbor': 6 hit(s)
      a60 note "Kickoff notes" · due 2026-09-20 · 10w  in f69
      a61 task "Order pier sensors" · due 2026-09-18 · 7w  in f69
      a64 note "Tide feed" · due 2026-09-17 · 10w  in f69
      a65 task "Permit renewal" · due 2026-09-30 · 10w  in f69
      a67 task "Dock survey" · due 2026-09-25 · 7w  in f69
      f69 surface "Harbor" column · 5 inside
      as a selection: ?harbor   e.g. do move ?harbor into=<surface> one=1   (help selections)

## reply
Created the leftmost **Harbor** column and collected its five unique project notes/tasks, sorted soonest due first. Verified no Harbor items remain elsewhere.

Hardest step was handling the duplicate Permit renewal appearance without duplicating it in the new column. The selection behavior around `one=1` was not clearly documented, so I used explicit moves and removed the extra appearance.

## assessment
{
 "harbor_column_exists": true,
 "all_five_present": true,
 "no_duplicates_elsewhere": true,
 "only_harbor": true,
 "ordered_by_due": true,
 "on_the_left": true,
 "hides_nothing": true,
 "within_budget": true,
 "pass": true
}