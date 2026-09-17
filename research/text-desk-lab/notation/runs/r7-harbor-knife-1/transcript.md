# r7-harbor-knife-1  task=harbor variant=knife
prompt: Gather everything about the Harbor project into the Harbor column, soonest due date first. Leave unrelated things where they are, but nothing Harbor-related may be left covered up.

[1 @3.83s] desk: look
    f01 surface "desk" free · 1280x800 · 3 inside
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside · try: sort  (open f02 to see inside)
      f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside · try: tile group  (open f03 to see inside)
      f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside · try: tile group  (open f04 to see inside)

[2 @6.94s] desk: look f02
    f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside · try: sort
      a17 task "Harbor permit renewal" · 384x388 · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · 384x388 · due 2026-09-20 · 17w

[3 @6.94s] desk: look f03
    f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside · try: tile group
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: remove also:
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27 · try: raise
      a27 chat "Priya" · 320x160 at 300,200 · 14w

[4 @6.94s] desk: look f04
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside · try: tile group
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: raise
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25 · try: raise
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · try: raise
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · try: raise remove also:
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w

[5 @12.55s] desk: read a17
    s08 task "Harbor permit renewal" · appears at a17 · tags harbor · due 2026-09-30
    ---
    City permit for the Harbor dock expires end of month.
    ---

[6 @12.55s] desk: read a16
    s05 note "Harbor kickoff" · appears at a16 · tags harbor · due 2026-09-20
    ---
    Kickoff for the Harbor project.
    Attendees: Sam, Priya, Alex.
    Decide the pier sensor vendor by the 20th.
    ---

[7 @12.55s] desk: read a18
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    ---

[8 @12.56s] desk: read a19
    s11 image "whiteboard.jpg" · appears at a19
    ---
    
    ---

[9 @12.56s] desk: read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    ---

[10 @12.56s] desk: read a20
    s07 note "Tide data format" · appears at a20 · tags harbor · due 2026-09-17
    ---
    Harbor tide feed is CSV, one row per 6 minutes. Need a parser before the kickoff.
    ---

[11 @12.56s] desk: read a21
    s12 image "dock-photo.png" · appears at a21
    ---
    
    ---

[12 @12.56s] desk: read a22
    s06 task "Order pier sensors" · appears at a22 · tags harbor · due 2026-09-18
    ---
    Get quotes from two vendors for the Harbor pier sensors.
    ---

[13 @12.56s] desk: read a23
    s09 note "Grocery list" · appears at a23
    ---
    eggs
    rice
    limes
    coffee
    ---

[14 @12.56s] desk: read a24
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    ---

[15 @12.56s] desk: read a25
    s13 image "layout-sketch.png" · appears at a25
    ---
    
    ---

[16 @12.56s] desk: read a26
    s14 note "Blog draft" · appears at a26
    ---
    Why we moved the desk to text.
    
    A screen is already a data structure; the problem is notation.
    ---

[17 @15.95s] desk: find Harbor
    find 'Harbor': 5 hit(s)
      a16 note "Harbor kickoff" · 384x388 · due 2026-09-20 · 17w  in f02
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · try: raise  in f04
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: raise  in f04
      a17 task "Harbor permit renewal" · 384x388 · due 2026-09-30 · 10w  in f02
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside · try: sort

[18 @27.95s] desk: do move a20,a22 to=f02
    ERR stopped at move a20: expected <a>,<b>, got 'f02'; earlier steps undone

[19 @29.89s] desk: help move
    move  (on: thing; level 1)
      Put this somewhere else.
      args: into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>
      e.g. do move a04 into=f02

[20 @31.78s] desk: do move a20,a22 into=f02
    ok move 2 thing(s) matching list a20,a22: a20 a22  [e1..e2, 2 steps]
      now: a20 note "Tide data format" · 384x190 · due 2026-09-17 · 16w  (3rd of 4 in f02)
      now: a22 task "Order pier sensors" · 384x190 · due 2026-09-18 · 10w  (2nd of 4 in f02)

[21 @33.89s] desk: look f02
    f02 surface "Harbor" column · 400x800 at 0,0 · 4 inside · try: sort
      a17 task "Harbor permit renewal" · 384x190 · due 2026-09-30 · 10w
      a22 task "Order pier sensors" · 384x190 · due 2026-09-18 · 10w
      a20 note "Tide data format" · 384x190 · due 2026-09-17 · 16w
      a16 note "Harbor kickoff" · 384x190 · due 2026-09-20 · 17w

[22 @35.67s] desk: help sort
    sort  (on: surface; level 2)
      Reorder the children of a tiled surface.
      args: by=due|title|kind [desc=1]
      e.g. do sort f02 by=due

[23 @37.67s] desk: do sort f02 by=due
    ok sort f02 by=due  [e3..e6, 4 steps]
      order now: a20, a22, a16, a17
      now: f02 surface "Harbor" column · 400x800 at 0,0 · 4 inside · try: sort
      a20 note "Tide data format" · 384x190 · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · 384x190 · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · 384x190 · due 2026-09-20 · 17w
      a17 task "Harbor permit renewal" · 384x190 · due 2026-09-30 · 10w

[24 @45.25s] desk: look f02
    f02 surface "Harbor" column · 400x800 at 0,0 · 4 inside · try: sort
      a20 note "Tide data format" · 384x190 · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · 384x190 · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · 384x190 · due 2026-09-20 · 17w
      a17 task "Harbor permit renewal" · 384x190 · due 2026-09-30 · 10w

[25 @45.27s] desk: look f04
    f04 surface "Scratch" free · 840x400 at 420,400 · 5 inside · try: tile group
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25 · try: raise
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · try: raise remove also:
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w

## reply
Gathered the four Harbor-tagged items into the Harbor column and sorted them by soonest due date: Sep 17, 18, 20, then 30. The previously covered Harbor items are no longer in Scratch.

Hardest step was distinguishing explicit Harbor project items from generic related meeting material. The desk’s tags made that clear; image relevance was otherwise unclear.

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