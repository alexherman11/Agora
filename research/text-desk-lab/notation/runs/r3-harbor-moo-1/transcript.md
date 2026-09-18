# r3-harbor-moo-1  task=harbor variant=moo
prompt: Gather everything about the Harbor project into the Harbor column, soonest due date first. Leave unrelated things where they are, but nothing Harbor-related may be left covered up.

[1 @5.83s] desk: look
    f01 surface "desk" free · 1280x800 · 3 inside
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside  (open f02 to see inside)
      f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside  (open f03 to see inside)
      f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside  (open f04 to see inside)

[2 @8.0s] desk: look f02 :3
    f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside
      a17 task "Harbor permit renewal" · 384x388 · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · 384x388 · due 2026-09-20 · 17w
      verbs: move resize raise lower remove tile untile rename group   (verbs f02 for argument forms)

[3 @9.92s] desk: look f03 :3
    f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27
      a27 chat "Priya" · 320x160 at 300,200 · 14w
      verbs: move resize raise lower remove tile rename group   (verbs f03 for argument forms)

[4 @11.67s] desk: look f04 :3
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w
      verbs: move resize raise lower remove tile rename group   (verbs f04 for argument forms)

[5 @14.88s] desk: find Harbor
    find 'Harbor': 5 hit(s)
      a16 note "Harbor kickoff" · 384x388 · due 2026-09-20 · 17w  in f02
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23  in f04
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24  in f04
      a17 task "Harbor permit renewal" · 384x388 · due 2026-09-30 · 10w  in f02
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside

[6 @20.47s] desk: help move
    move  (on: thing; level 1)
      Put this somewhere else.
      args: into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>
      e.g. do move a04 into=f02

[7 @25.19s] desk: do move a20 before=a16
    ok move a20 before=a16  [e1]
      now: a20 note "Tide data format" · 384x256 · due 2026-09-17 · 16w  (2nd of 3 in f02)

[8 @27.69s] desk: look f02 :3
    f02 surface "Harbor" column · 400x800 at 0,0 · 3 inside
      a17 task "Harbor permit renewal" · 384x256 · due 2026-09-30 · 10w
      a20 note "Tide data format" · 384x256 · due 2026-09-17 · 16w
      a16 note "Harbor kickoff" · 384x256 · due 2026-09-20 · 17w
      verbs: move resize raise lower remove tile untile rename group   (verbs f02 for argument forms)

[9 @33.22s] desk: do move a20 before=a17
    ok move a20 before=a17  [e2]
      now: a20 note "Tide data format" · 384x256 · due 2026-09-17 · 16w  (1st of 3 in f02)

[10 @35.78s] desk: look f04 :3
    f04 surface "Scratch" free · 840x400 at 420,400 · 6 inside
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w
      verbs: move resize raise lower remove tile rename group   (verbs f04 for argument forms)

[11 @38.88s] desk: look f02 :3
    f02 surface "Harbor" column · 400x800 at 0,0 · 3 inside
      a20 note "Tide data format" · 384x256 · due 2026-09-17 · 16w
      a17 task "Harbor permit renewal" · 384x256 · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · 384x256 · due 2026-09-20 · 17w
      verbs: move resize raise lower remove tile untile rename group   (verbs f02 for argument forms)

[12 @41.86s] desk: do move a22 after=a20
    ok move a22 after=a20  [e3]
      now: a22 task "Order pier sensors" · 384x190 · due 2026-09-18 · 10w  (2nd of 4 in f02)

[13 @44.31s] desk: look f02 :3
    f02 surface "Harbor" column · 400x800 at 0,0 · 4 inside
      a20 note "Tide data format" · 384x190 · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · 384x190 · due 2026-09-18 · 10w
      a17 task "Harbor permit renewal" · 384x190 · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · 384x190 · due 2026-09-20 · 17w
      verbs: move resize raise lower remove tile untile rename group   (verbs f02 for argument forms)

[14 @45.78s] desk: do move a16 before=a17
    ok move a16 before=a17  [e4]
      now: a16 note "Harbor kickoff" · 384x190 · due 2026-09-20 · 17w  (3rd of 4 in f02)

[15 @51.83s] desk: look f02 :3
    f02 surface "Harbor" column · 400x800 at 0,0 · 4 inside
      a20 note "Tide data format" · 384x190 · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · 384x190 · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · 384x190 · due 2026-09-20 · 17w
      a17 task "Harbor permit renewal" · 384x190 · due 2026-09-30 · 10w
      verbs: move resize raise lower remove tile untile rename group   (verbs f02 for argument forms)

[16 @53.56s] desk: find Harbor
    find 'Harbor': 5 hit(s)
      a16 note "Harbor kickoff" · 384x190 · due 2026-09-20 · 17w  in f02
      a22 task "Order pier sensors" · 384x190 · due 2026-09-18 · 10w  in f02
      a20 note "Tide data format" · 384x190 · due 2026-09-17 · 16w  in f02
      a17 task "Harbor permit renewal" · 384x190 · due 2026-09-30 · 10w  in f02
      f02 surface "Harbor" column · 400x800 at 0,0 · 4 inside

## reply
Gathered all four Harbor items into the Harbor column, ordered by due date: Sep 17, 18, 20, and 30. Verified no Harbor items remain elsewhere or covered up.

Hardest step was identifying Harbor-related items whose titles didn’t say “Harbor.” The search affordance made that clear.

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