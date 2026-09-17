# r8-harbor-tiled-1  task=harbor variant=tiled
prompt: Gather everything about the Harbor project into the Harbor column, soonest due date first. Leave unrelated things where they are, but nothing Harbor-related may be left covered up.

[1 @5.09s] desk: look
    f01 surface "desk" row · 1280x800 · 2 inside · try: sort
      f02 surface "Harbor" column · 405x784 · 2 inside · try: sort  (open f02 to see inside)
      f28 surface "Right" column · 850x784 · 2 inside · try: sort  (open f28 to see inside)

[2 @7.41s] desk: look f02 :3
    f02 surface "Harbor" column · 405x784 · 2 inside · try: sort
      a17 task "Harbor permit renewal" · 389x380 · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · 389x380 · due 2026-09-20 · 17w
      verbs: move resize remove tile untile rename group create   (verbs f02 for argument forms)

[3 @9.19s] desk: look f28 :3
    f28 surface "Right" column · 850x784 · 2 inside · try: sort
      f03 surface "Meeting" free · 834x370 · 3 inside · try: tile raise hidden,in:f03 group kind:chat,in:f03
      f04 surface "Scratch" free · 834x389 · 7 inside · try: tile raise hidden,in:f04 group kind:image,in:f04
      verbs: move resize remove tile untile rename group create   (verbs f28 for argument forms)

[4 @11.28s] desk: look f03 :3
    f03 surface "Meeting" free · 834x370 · 3 inside · try: tile raise hidden,in:f03 group kind:chat,in:f03
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: remove also:a18
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27 · try: raise
      a27 chat "Priya" · 320x160 at 300,200 · 14w
      verbs: move resize remove tile rename group create   (verbs f03 for argument forms)

[5 @13.09s] desk: look f04 :3
    f04 surface "Scratch" free · 834x389 · 7 inside · try: tile raise hidden,in:f04 group kind:image,in:f04
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: raise
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25 · try: raise
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · try: raise
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · try: raise remove also:a24
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w · spills-parent
      verbs: move resize remove tile rename group create   (verbs f04 for argument forms)

[6 @16.69s] desk: find Harbor
    find 'Harbor': 5 hit(s)
      a16 note "Harbor kickoff" · 389x380 · due 2026-09-20 · 17w  in f02
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · try: raise  in f04
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: raise  in f04
      a17 task "Harbor permit renewal" · 389x380 · due 2026-09-30 · 10w  in f02
      f02 surface "Harbor" column · 405x784 · 2 inside · try: sort
      as a selection: ?harbor   e.g. do move ?harbor into=<surface> one=1   (help selections)

[7 @21.02s] desk: read a20
    s07 note "Tide data format" · appears at a20 · tags harbor · due 2026-09-17
    ---
    Harbor tide feed is CSV, one row per 6 minutes. Need a parser before the kickoff.
    ---

[8 @23.52s] desk: read a22
    s06 task "Order pier sensors" · appears at a22 · tags harbor · due 2026-09-18
    ---
    Get quotes from two vendors for the Harbor pier sensors.
    ---

[9 @27.31s] desk: do move ?harbor into=f02 one=1
    ERR stopped at move f02: cannot move a surface into itself; earlier steps undone

[10 @30.05s] desk: do move a20,a22 into=f02 one=1
    ok move 2 thing(s) matching list a20,a22: a20 a22  [e1..e2, 2 steps]
      now: a20 note "Tide data format" · 389x108 · due 2026-09-17 · 16w  (3rd of 4 in f02)
      now: a22 task "Order pier sensors" · 389x117 · due 2026-09-18 · 10w  (2nd of 4 in f02)

[11 @32.62s] desk: look f02 :3
    f02 surface "Harbor" column · 405x784 · 4 inside · try: sort
      a17 task "Harbor permit renewal" · 389x259 · due 2026-09-30 · 10w
      a22 task "Order pier sensors" · 389x117 · due 2026-09-18 · 10w
      a20 note "Tide data format" · 389x108 · due 2026-09-17 · 16w
      a16 note "Harbor kickoff" · 389x259 · due 2026-09-20 · 17w
      verbs: move resize remove tile untile rename group create   (verbs f02 for argument forms)

[12 @34.97s] desk: help sort
    sort  (on: surface; level 2)
      Reorder the children of a tiled surface.
      args: by=due|title|kind [desc=1]
      e.g. do sort f02 by=due

[13 @37.05s] desk: do sort f02 by=due
    ok sort f02 by=due  [e3..e6, 4 steps]
      order now: a20, a22, a16, a17
      now: f02 surface "Harbor" column · 405x784 · 4 inside · try: sort  (1st of 2 in f01)
      a20 note "Tide data format" · 389x108 · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · 389x117 · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · 389x259 · due 2026-09-20 · 17w
      a17 task "Harbor permit renewal" · 389x259 · due 2026-09-30 · 10w

[14 @40.05s] desk: find Harbor
    find 'Harbor': 5 hit(s)
      a16 note "Harbor kickoff" · 389x259 · due 2026-09-20 · 17w  in f02
      a22 task "Order pier sensors" · 389x117 · due 2026-09-18 · 10w  in f02
      a20 note "Tide data format" · 389x108 · due 2026-09-17 · 16w  in f02
      a17 task "Harbor permit renewal" · 389x259 · due 2026-09-30 · 10w  in f02
      f02 surface "Harbor" column · 405x784 · 4 inside · try: sort
      as a selection: ?harbor   e.g. do move ?harbor into=<surface> one=1   (help selections)

## reply
Gathered all four Harbor items into the Harbor column and sorted them soonest due first. Verified no Harbor-related items remain elsewhere or covered.

Hardest step was excluding the Harbor surface itself from the Harbor search selection. The search selection included the destination surface, making direct item selection necessary.

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