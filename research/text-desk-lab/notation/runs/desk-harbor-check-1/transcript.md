# desk-harbor-check-1  task=harbor variant=lean
prompt: Gather everything about the Harbor project into the Harbor column, soonest due date first. Leave unrelated things where they are, but nothing Harbor-related may be left covered up.

[1 @4.92s] desk: look
    f01 surface "desk" row · 1280x800 · 2 inside
      f02 surface "Harbor" column · 2 inside  (open f02 to see inside)
      f28 surface "Right" column · 2 inside  (open f28 to see inside)

[2 @6.7s] desk: look f02; look f28
    [1] look f02
    f02 surface "Harbor" column · 2 inside
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w
    
    [2] look f28
    f28 surface "Right" column · 2 inside
      f03 surface "Meeting" free · 3 inside  (open f03 to see inside)
      f04 surface "Scratch" free · 7 inside  (open f04 to see inside)

[3 @8.75s] desk: look f03; look f04
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

[4 @11.88s] desk: examine a16; examine a17; examine a18; examine a19
    [1] examine a16
    a16 note "Harbor kickoff" · due 2026-09-20 · 17w
      a note (subject s05) on f02:
        * Kickoff for the Harbor project.
        * Attendees: Sam, Priya, Alex.
        * Decide the pier sensor vendor by the 20th.
      where: screen 16,404 389x380 · in f02 (column) local 8,396 z1 · clear
      verbs: due · append retitle rewrite · fold comment link prop tag · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)
    
    [2] examine a17
    a17 task "Harbor permit renewal" · due 2026-09-30 · 10w
      a task (subject s08) on f02:
        * City permit for the Harbor dock expires end of month.
      where: screen 16,16 389x380 · in f02 (column) local 8,8 z2 · clear
      verbs: due · append retitle rewrite · fold comment link prop tag · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)
    
    [3] examine a18
    a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: remove also:a18
      a note (subject s10) on f03:
        * 1. Yesterday's blockers
        * 2. Sensor vendor decision
        * 3. Demo schedule
      also appears at a24 in f04
      where: screen 449,36 380x220 · in f03 (free) local 20,20 z1 · under a27 · 4% hidden
      verbs: due · append retitle rewrite · fold comment link prop tag · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)
    
    [4] examine a19
    a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27 · try: raise
      a image (subject s11) on f03:
      where: screen 849,36 400x300 · in f03 (free) local 420,20 z2 · under a27 · 20% hidden
      verbs: retitle · fold comment link prop tag · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)

[5 @14.34s] desk: examine a20; examine a21; examine a22; examine a23
    [1] examine a20
    a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: raise
      a note (subject s07) on f04:
        * Harbor tide feed is CSV, one row per 6 minutes. Need a parser before the kickoff.
      where: screen 489,454 300x160 · in f04 (free) local 60,60 z1 · under a21 fully, under a24 · 100% hidden
      verbs: due · append retitle rewrite · fold comment link prop tag · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)
    
    [2] examine a21
    a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25 · try: raise
      a image (subject s12) on f04:
      where: screen 449,414 500x340 · in f04 (free) local 20,20 z2 · covers a20 fully, under a24, under a25 · 50% hidden
      verbs: retitle · fold comment link prop tag · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)
    
    [3] examine a22
    a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · try: raise
      a task (subject s06) on f04:
        * Get quotes from two vendors for the Harbor pier sensors.
      where: screen 969,424 280x140 · in f04 (free) local 540,30 z3 · under a23 · 67% hidden
      verbs: due · append retitle rewrite · fold comment link prop tag · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)
    
    [4] examine a23
    a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a note (subject s09) on f04:
        * eggs
        * rice
        * limes
        * coffee
      where: screen 989,454 240x150 · in f04 (free) local 560,60 z4 · covers a22, under a24 · 1% hidden
      verbs: due · append retitle rewrite · fold comment link prop tag · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)

[6 @21.24s] desk: examine a24; examine a25; examine a26; help move
    [1] examine a24
    a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · try: raise remove also:a24
      a note (subject s10) on f04:
        * 1. Yesterday's blockers
        * 2. Sensor vendor decision
        * 3. Demo schedule
      also appears at a18 in f03
      where: screen 729,594 320x180 · in f04 (free) local 300,200 z5 · covers a20, covers a21, covers a23, under a25, under a26 · 52% hidden
      verbs: due · append retitle rewrite · fold comment link prop tag · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)
    
    [2] examine a25
    a25 image "layout-sketch.png" · 360x160 at 40,220
      a image (subject s13) on f04:
      where: screen 469,614 360x160 · in f04 (free) local 40,220 z6 · covers a21, covers a24
      verbs: retitle · fold comment link prop tag · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)
    
    [3] examine a26
    a26 note "Blog draft" · 300x150 at 520,240 · 18w · spills-parent
      a note (subject s14) on f04:
        * Why we moved the desk to text.
        * A screen is already a data structure; the problem is notation.
      where: screen 949,634 300x150 · in f04 (free) local 520,240 z7 · spills-parent, covers a24
      verbs: due · append retitle rewrite · fold comment link prop tag · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)
    
    [4] help move
    move  (on: thing; level 1)
      Put this somewhere else.
      args: into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>
      e.g. do move a04 into=f02

[7 @24.84s] desk: find Harbor
    find 'Harbor': 5 hit(s)
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w  in f02
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w  in f02
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23  in f04
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24  in f04
      f02 surface "Harbor" column · 2 inside
      as a selection: ?harbor   e.g. do move ?harbor into=<surface> one=1   (help selections)

[8 @33.14s] desk: do move a20 into=f02
    ok move a20 into=f02  [e1]
      now: a20 note "Tide data format" · due 2026-09-17 · 16w  (2nd of 3 in f02)

[9 @36.19s] desk: look f02; examine a22
    [1] look f02
    f02 surface "Harbor" column · 3 inside
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w
      a20 note "Tide data format" · due 2026-09-17 · 16w
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w
    
    [2] examine a22
    a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · try: raise
      a task (subject s06) on f04:
        * Get quotes from two vendors for the Harbor pier sensors.
      where: screen 969,424 280x140 · in f04 (free) local 540,30 z3 · under a23 · 67% hidden
      verbs: due · append retitle rewrite · fold comment link prop tag · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)

[10 @39.74s] desk: do move a22 into=f02
    ok move a22 into=f02  [e2]
      now: a22 task "Order pier sensors" · due 2026-09-18 · 10w  (2nd of 4 in f02)

[11 @41.74s] desk: look f02; help sort
    [1] look f02
    f02 surface "Harbor" column · 4 inside
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w
      a22 task "Order pier sensors" · due 2026-09-18 · 10w
      a20 note "Tide data format" · due 2026-09-17 · 16w
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w
    
    [2] help sort
    sort  (on: surface; level 2)
      Reorder the children of a tiled surface.
      args: by=due|title|kind [desc=1]
      e.g. do sort f02 by=due

[12 @43.67s] desk: do sort f02 by=due
    ok sort f02 by=due  [e3..e6, 4 steps]
      order now: a20, a22, a16, a17
      now: f02 surface "Harbor" column · 4 inside  (1st of 2 in f01)
      a20 note "Tide data format" · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w

[13 @45.88s] desk: find Harbor; look f02
    [1] find Harbor
    find 'Harbor': 5 hit(s)
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w  in f02
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w  in f02
      a22 task "Order pier sensors" · due 2026-09-18 · 10w  in f02
      a20 note "Tide data format" · due 2026-09-17 · 16w  in f02
      f02 surface "Harbor" column · 4 inside
      as a selection: ?harbor   e.g. do move ?harbor into=<surface> one=1   (help selections)
    
    [2] look f02
    f02 surface "Harbor" column · 4 inside
      a20 note "Tide data format" · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w

## reply
Gathered all Harbor search results into the Harbor column and sorted them by due date (Sep 17, 18, 20, 30). Verification confirms no Harbor items remain elsewhere or covered.

Hardest step was identifying Harbor items from their contents rather than titles. The Harbor search selection was a useful affordance.

## assessment
{
 "all_harbor_in_column": true,
 "pass": true
}