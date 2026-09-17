# desk-harbor-check-2  task=harbor variant=lean
prompt: Gather everything about the Harbor project into the Harbor column, soonest due date first. Leave unrelated things where they are, but nothing Harbor-related may be left covered up.

[1 @4.28s] desk: look
    f01 surface "desk" row · 1280x800 · 2 inside
      f02 surface "Harbor" column · 2 inside  (open f02 to see inside)
      f28 surface "Right" column · 2 inside  (open f28 to see inside)

[2 @7.36s] desk: look f02; look f28
    [1] look f02
    f02 surface "Harbor" column · 2 inside
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w
    
    [2] look f28
    f28 surface "Right" column · 2 inside
      f03 surface "Meeting" free · 3 inside  (open f03 to see inside)
      f04 surface "Scratch" free · 7 inside  (open f04 to see inside)

[3 @9.12s] desk: look f03; look f04
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

[4 @13.25s] desk: read a16; read a17; read a18; read a19
    [1] read a16
    s05 note "Harbor kickoff" · appears at a16 · tags harbor · due 2026-09-20
    ---
    Kickoff for the Harbor project.
    Attendees: Sam, Priya, Alex.
    Decide the pier sensor vendor by the 20th.
    ---
    
    [2] read a17
    s08 task "Harbor permit renewal" · appears at a17 · tags harbor · due 2026-09-30
    ---
    City permit for the Harbor dock expires end of month.
    ---
    
    [3] read a18
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    ---
    
    [4] read a19
    s11 image "whiteboard.jpg" · appears at a19
    ---
    
    ---

[5 @16.09s] desk: read a20; read a21; read a22; read a23
    [1] read a20
    s07 note "Tide data format" · appears at a20 · tags harbor · due 2026-09-17
    ---
    Harbor tide feed is CSV, one row per 6 minutes. Need a parser before the kickoff.
    ---
    
    [2] read a21
    s12 image "dock-photo.png" · appears at a21
    ---
    
    ---
    
    [3] read a22
    s06 task "Order pier sensors" · appears at a22 · tags harbor · due 2026-09-18
    ---
    Get quotes from two vendors for the Harbor pier sensors.
    ---
    
    [4] read a23
    s09 note "Grocery list" · appears at a23
    ---
    eggs
    rice
    limes
    coffee
    ---

[6 @18.14s] desk: read a25; read a26; read a27
    [1] read a25
    s13 image "layout-sketch.png" · appears at a25
    ---
    
    ---
    
    [2] read a26
    s14 note "Blog draft" · appears at a26
    ---
    Why we moved the desk to text.
    
    A screen is already a data structure; the problem is notation.
    ---
    
    [3] read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    ---

[7 @22.88s] desk: examine a18; examine a19; examine a21; examine a24
    [1] examine a18
    a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: remove also:a18
      a note (subject s10) on f03:
        * 1. Yesterday's blockers
        * 2. Sensor vendor decision
        * 3. Demo schedule
      also appears at a24 in f04
      where: screen 449,36 380x220 · in f03 (free) local 20,20 z1 · under a27 · 4% hidden
      verbs: due · append retitle rewrite · fold comment link prop tag · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)
    
    [2] examine a19
    a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27 · try: raise
      a image (subject s11) on f03:
      where: screen 849,36 400x300 · in f03 (free) local 420,20 z2 · under a27 · 20% hidden
      verbs: retitle · fold comment link prop tag · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)
    
    [3] examine a21
    a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25 · try: raise
      a image (subject s12) on f04:
      where: screen 449,414 500x340 · in f04 (free) local 20,20 z2 · covers a20 fully, under a24, under a25 · 50% hidden
      verbs: retitle · fold comment link prop tag · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)
    
    [4] examine a24
    a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · try: raise remove also:a24
      a note (subject s10) on f04:
        * 1. Yesterday's blockers
        * 2. Sensor vendor decision
        * 3. Demo schedule
      also appears at a18 in f03
      where: screen 729,594 320x180 · in f04 (free) local 300,200 z5 · covers a20, covers a21, covers a23, under a25, under a26 · 52% hidden
      verbs: due · append retitle rewrite · fold comment link prop tag · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)

[8 @27.42s] desk: find Harbor; examine a20; examine a22; examine a27
    [1] find Harbor
    find 'Harbor': 5 hit(s)
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w  in f02
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w  in f02
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23  in f04
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24  in f04
      f02 surface "Harbor" column · 2 inside
      as a selection: ?harbor   e.g. do move ?harbor into=<surface> one=1   (help selections)
    
    [2] examine a20
    a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: raise
      a note (subject s07) on f04:
        * Harbor tide feed is CSV, one row per 6 minutes. Need a parser before the kickoff.
      where: screen 489,454 300x160 · in f04 (free) local 60,60 z1 · under a21 fully, under a24 · 100% hidden
      verbs: due · append retitle rewrite · fold comment link prop tag · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)
    
    [3] examine a22
    a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · try: raise
      a task (subject s06) on f04:
        * Get quotes from two vendors for the Harbor pier sensors.
      where: screen 969,424 280x140 · in f04 (free) local 540,30 z3 · under a23 · 67% hidden
      verbs: due · append retitle rewrite · fold comment link prop tag · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)
    
    [4] examine a27
    a27 chat "Priya" · 320x160 at 300,200 · 14w
      a chat (subject s15) on f03:
        * Priya: can you send the tide parser when it's ready?
        * Alex: yes, after kickoff.
      nothing awaiting a reply
      where: screen 729,216 320x160 · in f03 (free) local 300,200 z3 · covers a18, covers a19
      verbs: append retitle rewrite · fold comment link prop tag · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)

[9 @29.78s] desk: help move; examine f02
    [1] help move
    move  (on: thing; level 1)
      Put this somewhere else.
      args: into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>
      e.g. do move a04 into=f02
    
    [2] examine f02
    f02 surface "Harbor" column · 2 inside · try: sort
      a column surface inside f01, holding 2 thing(s):
        a17 task "Harbor permit renewal" · due 2026-09-30 · 10w
        a16 note "Harbor kickoff" · due 2026-09-20 · 17w
      where: screen 8,8 405x784 · in f01 (row) local 8,8 z1 · clear
      verbs: tile untile rename group create sort · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)

[10 @32.12s] desk: help sort
    sort  (on: surface; level 2)
      Reorder the children of a tiled surface.
      args: by=due|title|kind [desc=1]
      e.g. do sort f02 by=due

[11 @39.52s] desk: do move ?harbor into=f02 one=1
    ok move 4 thing(s) matching ?harbor: a16 a17 a20 a22  [None..e2, 4 steps]
      now: a16 note "Harbor kickoff" · due 2026-09-20 · 17w  (4th of 4 in f02)
      now: a17 task "Harbor permit renewal" · due 2026-09-30 · 10w  (1st of 4 in f02)
      now: a20 note "Tide data format" · due 2026-09-17 · 16w  (3rd of 4 in f02)
      now: a22 task "Order pier sensors" · due 2026-09-18 · 10w  (2nd of 4 in f02)

[12 @42.0s] desk: look f02
    f02 surface "Harbor" column · 4 inside
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w
      a22 task "Order pier sensors" · due 2026-09-18 · 10w
      a20 note "Tide data format" · due 2026-09-17 · 16w
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w

[13 @44.2s] desk: do sort f02 by=due
    ok sort f02 by=due  [e3..e6, 4 steps]
      order now: a20, a22, a16, a17
      now: f02 surface "Harbor" column · 4 inside  (1st of 2 in f01)
      a20 note "Tide data format" · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w

[14 @46.11s] desk: look f02; look f04
    [1] look f02
    f02 surface "Harbor" column · 4 inside
      a20 note "Tide data format" · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w
    
    [2] look f04
    f04 surface "Scratch" free · 5 inside
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w · spills-parent

## reply
Moved all Harbor-tagged items into Harbor and sorted by due date: Sep 17, 18, 20, 30. Verified none remain in Scratch, including the previously covered items. Hardest step was identifying concealed Harbor items; the `?harbor` selection and due-date sort were useful affordances.

## assessment
{
 "all_harbor_in_column": true,
 "pass": true
}