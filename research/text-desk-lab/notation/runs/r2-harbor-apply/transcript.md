# r2-harbor-apply  task=harbor variant=apply
prompt: Gather everything about the Harbor project into the Harbor column, soonest due date first. Leave unrelated things where they are, but nothing Harbor-related may be left covered up.

[1 @3.98s] desk: look
    f01 surface "desk" free · 1280x800 · 3 inside
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside  (open f02 to see inside)
      f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside  (open f03 to see inside)
      f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside  (open f04 to see inside)

[2 @5.48s] desk: open f02
    f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside
      a17 task "Harbor permit renewal" · 384x388 · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · 384x388 · due 2026-09-20 · 17w

[3 @7.03s] desk: open f03
    f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27
      a27 chat "Priya" · 320x160 at 300,200 · 14w

[4 @8.3s] desk: open f04
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w

[5 @12.58s] desk: read a16
    s05 note "Harbor kickoff" · appears at a16 · tags harbor · due 2026-09-20
    ---
    Kickoff for the Harbor project.
    Attendees: Sam, Priya, Alex.
    Decide the pier sensor vendor by the 20th.
    ---

[6 @12.58s] desk: read a17
    s08 task "Harbor permit renewal" · appears at a17 · tags harbor · due 2026-09-30
    ---
    City permit for the Harbor dock expires end of month.
    ---

[7 @12.58s] desk: read a18
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    ---

[8 @12.58s] desk: read a19
    s11 image "whiteboard.jpg" · appears at a19
    ---
    
    ---

[9 @12.58s] desk: read a20
    s07 note "Tide data format" · appears at a20 · tags harbor · due 2026-09-17
    ---
    Harbor tide feed is CSV, one row per 6 minutes. Need a parser before the kickoff.
    ---

[10 @12.58s] desk: read a21
    s12 image "dock-photo.png" · appears at a21
    ---
    
    ---

[11 @12.58s] desk: read a22
    s06 task "Order pier sensors" · appears at a22 · tags harbor · due 2026-09-18
    ---
    Get quotes from two vendors for the Harbor pier sensors.
    ---

[12 @12.58s] desk: read a23
    s09 note "Grocery list" · appears at a23
    ---
    eggs
    rice
    limes
    coffee
    ---

[13 @12.58s] desk: read a24
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    ---

[14 @12.58s] desk: read a25
    s13 image "layout-sketch.png" · appears at a25
    ---
    
    ---

[15 @12.58s] desk: read a26
    s14 note "Blog draft" · appears at a26
    ---
    Why we moved the desk to text.
    
    A screen is already a data structure; the problem is notation.
    ---

[16 @12.59s] desk: read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    ---

[17 @15.91s] desk: look a21 :3
    a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25
      subject s12
      where: screen 440,420 500x340 · in f04 (free) local 20,20 z2 · covers a20 fully, under a24, under a25 · 50% hidden
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  fold (show/hide content on screen)  append line=<str>  (adds a line at the end; edits the subject, so every appearance changes)  retitle title=<str>  rewrite text=<str>  (replaces all the text; write \n between lines)

[18 @22.23s] desk: history a19
    no events yet

[19 @22.23s] desk: history a21
    no events yet

[20 @22.23s] desk: history a25
    no events yet

[21 @24.02s] desk: pivot Harbor
    f02 is a surface in f01; surfaces have no subject

[22 @26.73s] desk: find Harbor
    find 'Harbor': 5 hit(s)
      a16 note "Harbor kickoff" · 384x388 · due 2026-09-20 · 17w  in f02
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23  in f04
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24  in f04
      a17 task "Harbor permit renewal" · 384x388 · due 2026-09-30 · 10w  in f02
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside

[23 @29.34s] desk: find tide
    find 'tide': 2 hit(s)
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 14w  in f03

[24 @29.34s] desk: find sensor
    find 'sensor': 4 hit(s)
      a16 note "Harbor kickoff" · 384x388 · due 2026-09-20 · 17w  in f02
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23  in f04
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1  in f03
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26  in f04

[25 @29.34s] desk: find kickoff
    find 'kickoff': 3 hit(s)
      a16 note "Harbor kickoff" · 384x388 · due 2026-09-20 · 17w  in f02
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 14w  in f03

[26 @29.34s] desk: find pier
    find 'pier': 2 hit(s)
      a16 note "Harbor kickoff" · 384x388 · due 2026-09-20 · 17w  in f02
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23  in f04

[27 @29.34s] desk: find dock
    find 'dock': 2 hit(s)
      a17 task "Harbor permit renewal" · 384x388 · due 2026-09-30 · 10w  in f02
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25  in f04

[28 @29.34s] desk: find vendor
    find 'vendor': 4 hit(s)
      a16 note "Harbor kickoff" · 384x388 · due 2026-09-20 · 17w  in f02
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23  in f04
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1  in f03
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26  in f04

[29 @29.34s] desk: find demo
    find 'demo': 2 hit(s)
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1  in f03
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26  in f04

[30 @38.22s] desk: verbs f02
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

[31 @41.92s] desk: do move a20 into=f02 before=a16
    ok e1: move a20 into=f02 before=a16
      now: a20 note "Tide data format" · 384x256 · due 2026-09-17 · 16w

[32 @44.09s] desk: open f02
    f02 surface "Harbor" column · 400x800 at 0,0 · 3 inside
      a17 task "Harbor permit renewal" · 384x256 · due 2026-09-30 · 10w
      a20 note "Tide data format" · 384x256 · due 2026-09-17 · 16w
      a16 note "Harbor kickoff" · 384x256 · due 2026-09-20 · 17w

[33 @47.78s] desk: do move a22 into=f02 before=a16
    ok e2: move a22 into=f02 before=a16
      now: a22 task "Order pier sensors" · 384x190 · due 2026-09-18 · 10w

[34 @50.25s] desk: open f02
    f02 surface "Harbor" column · 400x800 at 0,0 · 4 inside
      a17 task "Harbor permit renewal" · 384x190 · due 2026-09-30 · 10w
      a20 note "Tide data format" · 384x190 · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · 384x190 · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · 384x190 · due 2026-09-20 · 17w

[35 @54.14s] desk: do move a17 after=a16
    ok e3: move a17 after=a16
      now: a17 task "Harbor permit renewal" · 384x190 · due 2026-09-30 · 10w

[36 @56.44s] desk: open f02
    f02 surface "Harbor" column · 400x800 at 0,0 · 4 inside
      a20 note "Tide data format" · 384x190 · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · 384x190 · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · 384x190 · due 2026-09-20 · 17w
      a17 task "Harbor permit renewal" · 384x190 · due 2026-09-30 · 10w

[37 @58.75s] desk: do move a21 into=f02 after=a17
    ok e4: move a21 into=f02 after=a17
      now: a21 image "dock-photo.png" · 384x150

[38 @64.92s] desk: open f02
    f02 surface "Harbor" column · 400x800 at 0,0 · 5 inside
      a20 note "Tide data format" · 384x150 · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · 384x150 · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · 384x150 · due 2026-09-20 · 17w
      a17 task "Harbor permit renewal" · 384x150 · due 2026-09-30 · 10w
      a21 image "dock-photo.png" · 384x150

[39 @66.89s] desk: do move a27 into=f02 after=a21
    ok e5: move a27 into=f02 after=a21
      now: a27 chat "Priya" · 384x124 · 14w

[40 @69.72s] desk: open f02
    f02 surface "Harbor" column · 400x800 at 0,0 · 6 inside
      a20 note "Tide data format" · 384x124 · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · 384x124 · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · 384x124 · due 2026-09-20 · 17w
      a17 task "Harbor permit renewal" · 384x124 · due 2026-09-30 · 10w
      a21 image "dock-photo.png" · 384x124
      a27 chat "Priya" · 384x124 · 14w

[41 @71.55s] desk: do move a18 into=f02 after=a27
    ok e6: move a18 into=f02 after=a27
      now: a18 note "Standup agenda" · 384x105 · 10w · also x1

[42 @73.92s] desk: open f02
    f02 surface "Harbor" column · 400x800 at 0,0 · 7 inside
      a20 note "Tide data format" · 384x105 · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · 384x105 · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · 384x105 · due 2026-09-20 · 17w
      a17 task "Harbor permit renewal" · 384x105 · due 2026-09-30 · 10w
      a21 image "dock-photo.png" · 384x105
      a27 chat "Priya" · 384x105 · 14w
      a18 note "Standup agenda" · 384x105 · 10w · also x1

[43 @75.8s] desk: do move a24 into=f02 after=a18
    ok e7: move a24 into=f02 after=a18
      now: a24 note "Standup agenda" · 384x91 · 10w · also x1

[44 @79.75s] desk: open f02
    f02 surface "Harbor" column · 400x800 at 0,0 · 8 inside
      a20 note "Tide data format" · 384x91 · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · 384x91 · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · 384x91 · due 2026-09-20 · 17w
      a17 task "Harbor permit renewal" · 384x91 · due 2026-09-30 · 10w
      a21 image "dock-photo.png" · 384x91
      a27 chat "Priya" · 384x91 · 14w
      a18 note "Standup agenda" · 384x91 · 10w · also x1
      a24 note "Standup agenda" · 384x91 · 10w · also x1

[45 @79.75s] desk: open f03
    f03 surface "Meeting" free · 840x380 at 420,0 · 1 inside
      a19 image "whiteboard.jpg" · 400x300 at 420,20

[46 @79.75s] desk: open f04
    f04 surface "Scratch" free · 840x400 at 420,400 · 3 inside
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w

## reply
Gathered Harbor-related items into the Harbor column, with dated items ordered Sep 17, 18, 20, then 30; undated related items follow. Nothing Harbor-related remains covered.

Hardest step was identifying indirect Harbor references (the chat and standup agenda). Image relevance was somewhat unclear because image contents were not available as text.

## assessment
{
 "all_harbor_in_column": true,
 "no_stray_harbor_appearances": true,
 "only_harbor_in_column": false,
 "ordered_by_due": false,
 "nothing_harbor_hidden": true,
 "grocery_survives": true,
 "column_still_tiled": true,
 "pass": false
}