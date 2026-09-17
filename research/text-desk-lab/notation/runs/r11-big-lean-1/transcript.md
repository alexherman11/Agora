# r11-big-lean-1  task=big variant=lean
prompt: Somewhere on this desk are the notes and tasks for the Harbor project. Collect all of them into a new column called Harbor on the left of the desk, soonest due first, and make sure none of them is still showing anywhere else. You have a budget of 40 desk calls; it is a big desk, so do not read everything.

[1 @4.69s] desk: look
    f01 surface "desk" row · 1280x800 · 3 inside
      f02 surface "Inbox" column · 6 inside  (open f02 to see inside)
      f68 surface "Mid" column · 2 inside  (open f68 to see inside)
      f05 surface "Pile" free · 7 inside  (open f05 to see inside)

[2 @6.16s] desk: find Harbor
    find 'Harbor': 6 hit(s)
      a60 note "Kickoff notes" · due 2026-09-20 · 10w  in f02
      a61 task "Order pier sensors" · 260x140 at 40,40 · due 2026-09-18 · 7w · hidden by a63  in f03
      a64 note "Tide feed" · due 2026-09-17 · 10w  in f06
      a65 task "Permit renewal" · 260x140 at 300,200 · due 2026-09-30 · 10w · also x1  in f04
      a66 task "Permit renewal" · 260x140 at 20,40 · due 2026-09-30 · 10w · also x1  in f05
      a67 task "Dock survey" · 260x140 at 30,200 · due 2026-09-25 · 7w  in f05
      as a selection: ?harbor   e.g. do move ?harbor into=<surface> one=1   (help selections)

[3 @9.55s] desk: help create; help move; help beside; help sort
    [1] help create
    create  (on: surface; level 1)
      Make a new note, task or chat and place it on this surface.
      args: kind=note|task|chat title=<str> [text=<str>] [due=YYYY-MM-DD] [tags=a,b]
      e.g. do create f03 kind=task title="Send parser" due=2026-09-19
    
    [2] help move
    move  (on: thing; level 1)
      Put this somewhere else.
      args: into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>
      e.g. do move a04 into=f02
    
    [3] help beside
    beside  (pair verb; level 2)
      Put A right after B, in B's surface.
      args: A B
      e.g. do beside a20 a22
    
    [4] help sort
    sort  (on: surface; level 2)
      Reorder the children of a tiled surface.
      args: by=due|title|kind [desc=1]
      e.g. do sort f02 by=due

[4 @12.03s] desk: help; help selections; examine f01
    [1] help
    commands (several per call, separated by ; run in order, stopping at the first refusal; at most 4 reads per call):
      look [id] [:1|:2|:3]   outline from id (default desk). :1 folded line, :2 open (default), :3 focus
      open id | close id     expand / collapse id in later looks (view only; nothing moves)
      read id                full text of a note/task/etc (via an appearance or subject id)
      where id               exact geometry and spatial relations
      verbs id               what you can do to id, with argument forms
      pivot id               appearance -> its subject and every place it appears; subject -> appearances
      find words             search titles and text
      history [id]           recent events (with undo ids)
      examine id             a thing's detail: its lines, comments, links, and the verbs that apply right now
      help [verb]            what a verb does, its arguments, one example
      do verb target k=v ... change something. target is an id or a selection (help selections)
                             e.g. do move a04 into=f02   do move kind:image,in:f04 into=f28   do remove also:a18
      do swap A B | do beside A B | do match A to=B    pair verbs
      do group <selection> as=column title=X          a new surface around the selection
      undo eN                revert an event
    ids: f.. surface, a.. appearance, s.. subject, e.. event. quote values with spaces.
      $new                   the surface created earlier in this session; $item the last created thing
    
    [2] help selections
    selections: a target can be one id, or a selection that names many things:
      ?tide+parser       things whose title, text or tags contain all the words
      kind:image         by kind (kind:note|task for several)
      tag:harbor         by tag
      in:f04             inside surface f04, recursively
      hidden             more than 5% covered by something
      also:a18           the other appearances of a18's subject
      due<2026-09-20     due before (due> after)
      title:agenda       title contains the word
      a20,a22            an explicit list
    combine terms with commas (AND): kind:image,in:f04. The receipt lists everything the verb touched.
    e.g. do move ?harbor into=f02 one=1     do raise hidden,in:f04     do group kind:image,in:f04 as=column title=Pictures
    
    [3] examine f01
    f01 surface "desk" row · 1280x800 · 3 inside · try: sort
      a row surface (the desk itself), holding 3 thing(s): f02, f68, f05
      where: screen 0,0 1280x800 · in - (-) · clear
      verbs: tile untile rename group create sort   (help <verb> for args; the target may be a selection: help selections)

[5 @16.25s] desk: help group; help tile; help remove
    [1] help group
    group  (on: surface; level 1)
      Make a new empty surface inside this one.
      args: title=<str> as=free|column|row
      e.g. do group f04 title="Pictures" as=column
    
    [2] help tile
    tile  (on: surface; level 1)
      Lay the children out as a column or row, sharing the space, nothing overlapping.
      args: as=column|row
      e.g. do tile f04 as=row
    
    [3] help remove
    remove  (on: thing; level 1)
      Take this appearance off the desk. The subject survives and any other appearance stays.
      e.g. do remove a24

[6 @22.75s] desk: do group f01 title=Harbor as=column
    ok group f01 title=Harbor as=column  [e1] → created f69
      f69 surface "Harbor" column · empty
        where: screen 850,8 420x784 · in f01 (row) local 850,8 z6 · clear
      now: f01 surface "desk" row · 1280x800 · 4 inside

[7 @26.8s] desk: do move a60 into=f69; do move a61 into=f69; do move a64 into=f69; do move a65 into=f69; do move a67 into=f69; do remove a66
    [1] do move a60 into=f69
    ok move a60 into=f69  [e2]
      now: a60 note "Kickoff notes" · due 2026-09-20 · 10w  (1st of 1 in f69)
    
    [2] do move a61 into=f69
    ok move a61 into=f69  [e3]
      now: a61 task "Order pier sensors" · due 2026-09-18 · 7w  (2nd of 2 in f69)
    
    [3] do move a64 into=f69
    ok move a64 into=f69  [e4]
      now: a64 note "Tide feed" · due 2026-09-17 · 10w  (2nd of 3 in f69)
    
    [4] do move a65 into=f69
    ok move a65 into=f69  [e5]
      now: a65 task "Permit renewal" · due 2026-09-30 · 10w · also x1  (2nd of 4 in f69)
    
    [5] do move a67 into=f69
    ok move a67 into=f69  [e6]
      now: a67 task "Dock survey" · due 2026-09-25 · 7w  (2nd of 5 in f69)
    
    [6] do remove a66
    ok remove a66  [e7]
      appearance removed; the subject still exists

[8 @30.36s] desk: look f69; look f01
    [1] look f69
    f69 surface "Harbor" column · 5 inside
      a60 note "Kickoff notes" · due 2026-09-20 · 10w
      a67 task "Dock survey" · due 2026-09-25 · 7w
      a65 task "Permit renewal" · due 2026-09-30 · 10w
      a64 note "Tide feed" · due 2026-09-17 · 10w
      a61 task "Order pier sensors" · due 2026-09-18 · 7w
    
    [2] look f01
    f01 surface "desk" row · 1280x800 · 4 inside
      f02 surface "Inbox" column · 5 inside  (open f02 to see inside)
      f68 surface "Mid" column · 2 inside  (open f68 to see inside)
      f05 surface "Pile" free · 5 inside  (open f05 to see inside)
      f69 surface "Harbor" column · 5 inside  (open f69 to see inside)

[9 @34.14s] desk: do sort f69 by=due
    ok sort f69 by=due  [e8..e12, 5 steps]
      order now: a64, a61, a60, a67, a65
      now: f69 surface "Harbor" column · 5 inside  (4th of 4 in f01)
      a64 note "Tide feed" · due 2026-09-17 · 10w
      a61 task "Order pier sensors" · due 2026-09-18 · 7w
      a60 note "Kickoff notes" · due 2026-09-20 · 10w
      a67 task "Dock survey" · due 2026-09-25 · 7w
      a65 task "Permit renewal" · due 2026-09-30 · 10w

[10 @38.17s] desk: look f01
    f01 surface "desk" row · 1280x800 · 4 inside
      f02 surface "Inbox" column · 5 inside  (open f02 to see inside)
      f68 surface "Mid" column · 2 inside  (open f68 to see inside)
      f05 surface "Pile" free · 5 inside  (open f05 to see inside)
      f69 surface "Harbor" column · 5 inside  (open f69 to see inside)

[11 @39.58s] desk: do move f69 before=f02
    ok move f69 before=f02  [e13]
      now: f69 surface "Harbor" column · 5 inside  (1st of 4 in f01)

[12 @42.23s] desk: look f01; look f69; find Harbor
    [1] look f01
    f01 surface "desk" row · 1280x800 · 4 inside
      f69 surface "Harbor" column · 5 inside  (open f69 to see inside)
      f02 surface "Inbox" column · 5 inside  (open f02 to see inside)
      f68 surface "Mid" column · 2 inside  (open f68 to see inside)
      f05 surface "Pile" free · 5 inside  (open f05 to see inside)
    
    [2] look f69
    f69 surface "Harbor" column · 5 inside
      a64 note "Tide feed" · due 2026-09-17 · 10w
      a61 task "Order pier sensors" · due 2026-09-18 · 7w
      a60 note "Kickoff notes" · due 2026-09-20 · 10w
      a67 task "Dock survey" · due 2026-09-25 · 7w
      a65 task "Permit renewal" · due 2026-09-30 · 10w
    
    [3] find Harbor
    find 'Harbor': 6 hit(s)
      a60 note "Kickoff notes" · due 2026-09-20 · 10w  in f69
      a61 task "Order pier sensors" · due 2026-09-18 · 7w  in f69
      a64 note "Tide feed" · due 2026-09-17 · 10w  in f69
      a65 task "Permit renewal" · due 2026-09-30 · 10w  in f69
      a67 task "Dock survey" · due 2026-09-25 · 7w  in f69
      f69 surface "Harbor" column · 5 inside
      as a selection: ?harbor   e.g. do move ?harbor into=<surface> one=1   (help selections)

## reply
Created the leftmost **Harbor** column with all five project items, sorted soonest due first. Removed the duplicate Permit renewal appearance; Harbor items no longer appear elsewhere.

Hardest step was handling the duplicate task without losing it. The search result’s “also x1” indicator was helpful.

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