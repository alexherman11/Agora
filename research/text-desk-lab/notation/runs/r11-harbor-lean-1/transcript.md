# r11-harbor-lean-1  task=harbor variant=lean
prompt: Gather everything about the Harbor project into the Harbor column, soonest due date first. Leave unrelated things where they are, but nothing Harbor-related may be left covered up.

[1 @5.36s] desk: look
    f01 surface "desk" row · 1280x800 · 2 inside
      f02 surface "Harbor" column · 2 inside  (open f02 to see inside)
      f28 surface "Right" column · 2 inside  (open f28 to see inside)

[2 @7.91s] desk: look f02; look f28
    [1] look f02
    f02 surface "Harbor" column · 2 inside
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w
    
    [2] look f28
    f28 surface "Right" column · 2 inside
      f03 surface "Meeting" free · 3 inside  (open f03 to see inside)
      f04 surface "Scratch" free · 7 inside  (open f04 to see inside)

[3 @10.09s] desk: look f03; look f04
    [1] look f03
    f03 surface "Meeting" free · 3 inside
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27
      a27 chat "Priya" · 320x160 at 300,200 · 14w
    
    [2] look f04
    f04 surface "Scratch" free · 7 inside
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w · spills-parent

[4 @13.78s] desk: read a18; read a19; read a27; read a20
    [1] read a18
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    ---
    
    [2] read a19
    s11 image "whiteboard.jpg" · appears at a19
    ---
    
    ---
    
    [3] read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    ---
    
    [4] read a20
    s07 note "Tide data format" · appears at a20 · tags harbor · due 2026-09-17
    ---
    Harbor tide feed is CSV, one row per 6 minutes. Need a parser before the kickoff.
    ---

[5 @15.77s] desk: read a21; read a22; read a23; read a25
    [1] read a21
    s12 image "dock-photo.png" · appears at a21
    ---
    
    ---
    
    [2] read a22
    s06 task "Order pier sensors" · appears at a22 · tags harbor · due 2026-09-18
    ---
    Get quotes from two vendors for the Harbor pier sensors.
    ---
    
    [3] read a23
    s09 note "Grocery list" · appears at a23
    ---
    eggs
    rice
    limes
    coffee
    ---
    
    [4] read a25
    s13 image "layout-sketch.png" · appears at a25
    ---
    
    ---

[6 @17.92s] desk: read a26; read a17; read a16; find Harbor
    [1] read a26
    s14 note "Blog draft" · appears at a26
    ---
    Why we moved the desk to text.
    
    A screen is already a data structure; the problem is notation.
    ---
    
    [2] read a17
    s08 task "Harbor permit renewal" · appears at a17 · tags harbor · due 2026-09-30
    ---
    City permit for the Harbor dock expires end of month.
    ---
    
    [3] read a16
    s05 note "Harbor kickoff" · appears at a16 · tags harbor · due 2026-09-20
    ---
    Kickoff for the Harbor project.
    Attendees: Sam, Priya, Alex.
    Decide the pier sensor vendor by the 20th.
    ---
    
    [4] find Harbor
    find 'Harbor': 5 hit(s)
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w  in f02
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23  in f04
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24  in f04
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w  in f02
      f02 surface "Harbor" column · 2 inside
      as a selection: ?harbor   e.g. do move ?harbor into=<surface> one=1   (help selections)

[7 @23.39s] desk: help sort; help move
    [1] help sort
    sort  (on: surface; level 2)
      Reorder the children of a tiled surface.
      args: by=due|title|kind [desc=1]
      e.g. do sort f02 by=due
    
    [2] help move
    move  (on: thing; level 1)
      Put this somewhere else.
      args: into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>
      e.g. do move a04 into=f02

[8 @26.53s] desk: help selections
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

[9 @31.47s] desk: do move a20,a22 into=f02; do sort f02 by=due
    [1] do move a20,a22 into=f02
    ok move 2 thing(s) matching list a20,a22: a20 a22  [e1..e2, 2 steps]
      now: a20 note "Tide data format" · due 2026-09-17 · 16w  (3rd of 4 in f02)
      now: a22 task "Order pier sensors" · due 2026-09-18 · 10w  (2nd of 4 in f02)
    
    [2] do sort f02 by=due
    ok sort f02 by=due  [e3..e6, 4 steps]
      order now: a20, a22, a16, a17
      now: f02 surface "Harbor" column · 4 inside  (1st of 2 in f01)
      a20 note "Tide data format" · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w

[10 @34.2s] desk: look f02; find Harbor; look f04
    [1] look f02
    f02 surface "Harbor" column · 4 inside
      a20 note "Tide data format" · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w
    
    [2] find Harbor
    find 'Harbor': 5 hit(s)
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w  in f02
      a22 task "Order pier sensors" · due 2026-09-18 · 10w  in f02
      a20 note "Tide data format" · due 2026-09-17 · 16w  in f02
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w  in f02
      f02 surface "Harbor" column · 4 inside
      as a selection: ?harbor   e.g. do move ?harbor into=<surface> one=1   (help selections)
    
    [3] look f04
    f04 surface "Scratch" free · 5 inside
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w · spills-parent

## reply
Gathered the four Harbor-tagged items into the Harbor column, sorted soonest due first. Verified no Harbor items remain elsewhere or covered.

Hardest step was distinguishing Harbor work from unrelated, similarly themed desk items. The text search/tag affordance made that clear.

## assessment
{
 "all_harbor_in_column": true,
 "no_stray_harbor_appearances": true,
 "only_harbor_in_column": true,
 "ordered_by_due": true,
 "nothing_harbor_hidden": true,
 "grocery_survives": true,
 "column_still_tiled": true,
 "pass": true
}