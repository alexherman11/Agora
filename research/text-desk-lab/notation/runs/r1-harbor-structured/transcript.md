# r1-harbor-structured  task=harbor variant=structured
prompt: Gather everything about the Harbor project into the Harbor column, soonest due date first. Leave unrelated things where they are, but nothing Harbor-related may be left covered up.

[1 @3.8s] look: {"args": {"level": 3}}
    f01 surface "desk" free · 1280x800 · 3 inside
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside  (open f02 to see inside)
      f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside  (open f03 to see inside)
      f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside  (open f04 to see inside)

[2 @5.58s] open: {"args": {"target": "f02"}}
    ERR open needs an id

[3 @5.58s] open: {"args": {"target": "f03"}}
    ERR open needs an id

[4 @5.58s] open: {"args": {"target": "f04"}}
    ERR open needs an id

[5 @9.77s] open: {"args": {"id": "f02"}}
    ERR open needs an id

[6 @12.0s] open: {"target": "f02"}
    f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside
      a17 task "Harbor permit renewal" · 384x388 · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · 384x388 · due 2026-09-20 · 17w

[7 @13.73s] open: {"target": "f03"}
    f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27
      a27 chat "Priya" · 320x160 at 300,200 · 14w

[8 @13.73s] open: {"target": "f04"}
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w

[9 @17.2s] read: {"target": "a16"}
    s05 note "Harbor kickoff" · appears at a16 · tags harbor · due 2026-09-20
    ---
    Kickoff for the Harbor project.
    Attendees: Sam, Priya, Alex.
    Decide the pier sensor vendor by the 20th.
    ---

[10 @17.2s] read: {"target": "a17"}
    s08 task "Harbor permit renewal" · appears at a17 · tags harbor · due 2026-09-30
    ---
    City permit for the Harbor dock expires end of month.
    ---

[11 @17.2s] read: {"target": "a18"}
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    ---

[12 @17.22s] read: {"target": "a19"}
    s11 image "whiteboard.jpg" · appears at a19
    ---
    
    ---

[13 @17.22s] read: {"target": "a20"}
    s07 note "Tide data format" · appears at a20 · tags harbor · due 2026-09-17
    ---
    Harbor tide feed is CSV, one row per 6 minutes. Need a parser before the kickoff.
    ---

[14 @17.22s] read: {"target": "a21"}
    s12 image "dock-photo.png" · appears at a21
    ---
    
    ---

[15 @17.22s] read: {"target": "a22"}
    s06 task "Order pier sensors" · appears at a22 · tags harbor · due 2026-09-18
    ---
    Get quotes from two vendors for the Harbor pier sensors.
    ---

[16 @17.22s] read: {"target": "a23"}
    s09 note "Grocery list" · appears at a23
    ---
    eggs
    rice
    limes
    coffee
    ---

[17 @17.22s] read: {"target": "a24"}
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    ---

[18 @17.22s] read: {"target": "a25"}
    s13 image "layout-sketch.png" · appears at a25
    ---
    
    ---

[19 @17.22s] read: {"target": "a26"}
    s14 note "Blog draft" · appears at a26
    ---
    Why we moved the desk to text.
    
    A screen is already a data structure; the problem is notation.
    ---

[20 @17.22s] read: {"target": "a27"}
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    ---

[21 @23.52s] verbs: {"target": "a20"}
    a20 verbs:
      move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>
      resize to=<w>x<h>
      raise (to front)
      lower (to back)
      remove (removes this appearance only; the subject survives)
      fold (show/hide content on screen)
      edit title=<str> | text=<str> | append=<str>  (edits the subject; every appearance changes)

[22 @23.52s] verbs: {"target": "a22"}
    a22 verbs:
      move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>
      resize to=<w>x<h>
      raise (to front)
      lower (to back)
      remove (removes this appearance only; the subject survives)
      fold (show/hide content on screen)
      edit title=<str> | text=<str> | append=<str>  (edits the subject; every appearance changes)

[23 @23.52s] verbs: {"target": "f02"}
    f02 verbs:
      move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>
      resize to=<w>x<h>
      raise (to front)
      lower (to back)
      remove (removes this appearance only; the subject survives)
      tile as=column|row  (lay children out without overlap)
      untile
      rename title=<str>
      group title=<str> as=free|column|row  (new empty surface inside this one)

[24 @28.83s] do: {"target": "a20", "verb": "move", "args": {"into": "f02", "before": "a16"}}
    ok e1: move a20 into=f02 before=a16
      now: a20 note "Tide data format" · 384x256 · due 2026-09-17 · 16w

[25 @30.91s] look: {"target": "f02", "level": 3}
    f02 surface "Harbor" column · 400x800 at 0,0 · 3 inside
      a17 task "Harbor permit renewal" · 384x256 · due 2026-09-30 · 10w
      a20 note "Tide data format" · 384x256 · due 2026-09-17 · 16w
      a16 note "Harbor kickoff" · 384x256 · due 2026-09-20 · 17w
      where: screen 0,0 400x800 · in f01 (free) local 0,0 z1 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  untile  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[26 @40.77s] do: {"target": "a22", "verb": "move", "args": {"into": "f02", "before": "a16"}}
    ok e2: move a22 into=f02 before=a16
      now: a22 task "Order pier sensors" · 384x190 · due 2026-09-18 · 10w

[27 @42.36s] look: {"target": "f02", "level": 3}
    f02 surface "Harbor" column · 400x800 at 0,0 · 4 inside
      a17 task "Harbor permit renewal" · 384x190 · due 2026-09-30 · 10w
      a22 task "Order pier sensors" · 384x190 · due 2026-09-18 · 10w
      a20 note "Tide data format" · 384x190 · due 2026-09-17 · 16w
      a16 note "Harbor kickoff" · 384x190 · due 2026-09-20 · 17w
      where: screen 0,0 400x800 · in f01 (free) local 0,0 z1 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  untile  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[28 @50.14s] do: {"target": "a20", "verb": "move", "args": {"before": "a22"}}
    ok e3: move a20 before=a22
      now: a20 note "Tide data format" · 384x190 · due 2026-09-17 · 16w

[29 @51.61s] look: {"target": "f02", "level": 3}
    f02 surface "Harbor" column · 400x800 at 0,0 · 4 inside
      a17 task "Harbor permit renewal" · 384x190 · due 2026-09-30 · 10w
      a20 note "Tide data format" · 384x190 · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · 384x190 · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · 384x190 · due 2026-09-20 · 17w
      where: screen 0,0 400x800 · in f01 (free) local 0,0 z1 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  untile  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[30 @53.45s] do: {"target": "a17", "verb": "move", "args": {"after": "a16"}}
    ok e4: move a17 after=a16
      now: a17 task "Harbor permit renewal" · 384x190 · due 2026-09-30 · 10w

[31 @57.53s] look: {"target": "f02", "level": 3}
    f02 surface "Harbor" column · 400x800 at 0,0 · 4 inside
      a20 note "Tide data format" · 384x190 · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · 384x190 · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · 384x190 · due 2026-09-20 · 17w
      a17 task "Harbor permit renewal" · 384x190 · due 2026-09-30 · 10w
      where: screen 0,0 400x800 · in f01 (free) local 0,0 z1 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  untile  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[32 @57.55s] look: {"target": "f04", "level": 3}
    f04 surface "Scratch" free · 840x400 at 420,400 · 5 inside
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w
      where: screen 420,400 840x400 · in f01 (free) local 420,400 z3 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[33 @57.55s] find: {"words": "Harbor"}
    find 'Harbor': 5 hit(s)
      a16 note "Harbor kickoff" · 384x190 · due 2026-09-20 · 17w  in f02
      a22 task "Order pier sensors" · 384x190 · due 2026-09-18 · 10w  in f02
      a20 note "Tide data format" · 384x190 · due 2026-09-17 · 16w  in f02
      a17 task "Harbor permit renewal" · 384x190 · due 2026-09-30 · 10w  in f02
      f02 surface "Harbor" column · 400x800 at 0,0 · 4 inside

## reply
Gathered all 4 Harbor items into the Harbor column, ordered by due date: Sep 17, Sep 18, Sep 20, Sep 30. Verified they are clear and no Harbor search hits remain elsewhere.

The hardest step was preserving the required order while moving items into the column. The ordering behavior during insertion was slightly unclear, but the final layout is correct.

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