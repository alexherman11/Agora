# r6-big-acme-1  task=big variant=acme
prompt: Somewhere on this desk are the notes and tasks for the Harbor project. Collect all of them into a new column called Harbor on the left of the desk, soonest due first, and make sure none of them is still showing anywhere else. You have a budget of 40 desk calls; it is a big desk, so do not read everything.

[1 @4.22s] desk: look
    f01 surface "desk" free · 1280x800 · 4 inside
      f02 surface "Inbox" column · 300x800 at 0,0 · 6 inside · try: sort gather  (open f02 to see inside)
      f03 surface "Projects" free · 640x400 at 310,0 · 6 inside · try: tidy split  (open f03 to see inside)
      f04 surface "Reading" free · 640x390 at 310,410 · 3 inside · try: tidy split  (open f04 to see inside)
      f05 surface "Pile" free · 320x800 at 960,0 · 7 inside · try: tidy split  (open f05 to see inside)

[2 @6.05s] desk: find Harbor
    find 'Harbor': 6 hit(s)
      a60 note "Kickoff notes" · 284x124 · due 2026-09-20 · 10w  in f02
      a61 task "Order pier sensors" · 260x140 at 40,40 · due 2026-09-18 · 7w · hidden by a63 · try: reveal  in f03
      a64 note "Tide feed" · 284x30 · due 2026-09-17 · 10w  in f06
      a65 task "Permit renewal" · 260x140 at 300,200 · due 2026-09-30 · 10w · also x1 · try: dedupe  in f04
      a66 task "Permit renewal" · 260x140 at 20,40 · due 2026-09-30 · 10w · also x1 · try: dedupe  in f05
      a67 task "Dock survey" · 260x140 at 30,200 · due 2026-09-25 · 7w  in f05

[3 @9.72s] desk: examine f01
    f01 surface "desk" free · 1280x800 · 4 inside
      a free surface (the desk itself), holding 4 thing(s): f02, f03, f04, f05
      where: screen 0,0 1280x800 · in - (-) · clear
      verbs from surface: tile(as=column|row)  rename(title=<str>)  group(title=<str> as=free|column|row)  create(kind=note|task|chat title=<str> [text=<str>] [due=YYYY-MM-DD] [tags=a,b])  sort(by=due|title|kind [desc=1])  tidy([as=column|row])  split(by=kind|title|tag left=<value> [right=<value>] [as=row|column])  gather(words=<text> [by=due|title])  stack
        sort: Reorder the children of a tiled surface.
        tidy: Make nothing overlap: tile the surface as a column (or row) with the current order.
        split: Divide the children into two tiled groups side by side (left/right) or stacked (top/bottom) by a rule.
        gather: Bring every appearance matching words into this surface (one per subject), then sort if tiled.
        stack: Pile the children neatly at the top-left, each offset a little, front to back in the current z order.
      (help <verb> [<verb> ...] explains; do <verb> f01 ... uses one)

[4 @12.47s] desk: help group gather
    group  (on: surface; level 1)
      Make a new empty surface inside this one.
      args: title=<str> as=free|column|row
      e.g. do group f04 title="Pictures" as=column
    
    gather  (on: surface; level 3)
      Bring every appearance matching words into this surface (one per subject), then sort if tiled.
      args: words=<text> [by=due|title]
      e.g. do gather f02 words=harbor by=due

[5 @15.42s] desk: help move
    move  (on: thing; level 1)
      Put this somewhere else.
      args: into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>
      e.g. do move a04 into=f02

[6 @18.55s] desk: do group f01 title="Harbor" as=column
    ok group f01 title=Harbor as=column  [e1] → created f68
      f68 surface "Harbor" column · 640x400 at 16,16 · empty · covers f02,f03,f04 · try: gather
        where: screen 16,16 640x400 · in f01 (free) local 16,16 z5 · covers f02, covers f03, covers f04
      no free space in f01: f68 covers f02, covers f03, covers f04; move it, resize it, or tile f01 so nothing overlaps
      now: f01 surface "desk" free · 1280x800 · 5 inside · try: tidy split

[7 @20.95s] desk: examine f68
    f68 surface "Harbor" column · 640x400 at 16,16 · empty · covers f02,f03,f04 · try: gather
      a column surface inside f01, empty
      where: screen 16,16 640x400 · in f01 (free) local 16,16 z5 · covers f02, covers f03, covers f04
      verbs from surface: untile  rename(title=<str>)  group(title=<str> as=free|column|row)  create(kind=note|task|chat title=<str> [text=<str>] [due=YYYY-MM-DD] [tags=a,b])  gather(words=<text> [by=due|title])
      verbs from thing: move(into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>)  resize(to=<w>x<h>)  raise  lower  remove
        gather: Bring every appearance matching words into this surface (one per subject), then sort if tiled.
      (help <verb> [<verb> ...] explains; do <verb> f68 ... uses one)

[8 @28.61s] desk: do gather f68 words=Harbor by=due
    ok gather f68 words=Harbor by=due  [e2..e12, 11 steps]
      5 subject(s) matched; 6 step(s)
      now: f68 surface "Harbor" column · 640x400 at 16,16 · 5 inside · covers f02,f03,f04 · try: sort gather
      a64 note "Tide feed" · 624x70 · due 2026-09-17 · 10w
      a61 task "Order pier sensors" · 624x70 · due 2026-09-18 · 7w
      a60 note "Kickoff notes" · 624x70 · due 2026-09-20 · 10w
      a67 task "Dock survey" · 624x70 · due 2026-09-25 · 7w
      a65 task "Permit renewal" · 624x70 · due 2026-09-30 · 10w

[9 @31.64s] desk: look f01
    f01 surface "desk" free · 1280x800 · 5 inside · try: tidy split
      f02 surface "Inbox" column · 300x800 at 0,0 · 5 inside · 47% hidden by f68 · try: sort gather  (open f02 to see inside)
      f03 surface "Projects" free · 640x400 at 310,0 · 5 inside · 51% hidden by f68 · try: tidy split  (open f03 to see inside)
      f04 surface "Reading" free · 640x390 at 310,410 · 2 inside · try: tidy split  (open f04 to see inside)
      f05 surface "Pile" free · 320x800 at 960,0 · 5 inside · try: tidy split  (open f05 to see inside)
      f68 surface "Harbor" column · 640x400 at 16,16 · 5 inside · covers f02,f03,f04 · try: sort gather  (open f68 to see inside)

[10 @33.77s] desk: do move f68 before=f02
    ERR f01 is a free surface, so before/after would only change stacking, not position. tile f01 as=row|column first, then before/after orders it; or move to=<x>,<y>

[11 @37.38s] desk: do tile f01 as=row
    ok tile f01 as=row  [e13]
      now: f01 surface "desk" row · 1280x800 · 5 inside · try: sort gather

[12 @39.58s] desk: look f01
    f01 surface "desk" row · 1280x800 · 5 inside · try: sort gather
      f02 surface "Inbox" column · 246x784 · 5 inside · try: sort gather  (open f02 to see inside)
      f68 surface "Harbor" column · 246x784 · 5 inside · try: sort gather  (open f68 to see inside)
      f03 surface "Projects" free · 246x784 · 5 inside · try: tidy split  (open f03 to see inside)
      f04 surface "Reading" free · 246x784 · 2 inside · try: tidy split  (open f04 to see inside)
      f05 surface "Pile" free · 246x784 · 5 inside · try: tidy split  (open f05 to see inside)

[13 @41.66s] desk: do move f68 before=f02
    ok move f68 before=f02  [e14]
      now: f68 surface "Harbor" column · 246x784 · 5 inside · try: sort gather  (1st of 5 in f01)

[14 @44.8s] desk: look f68
    f68 surface "Harbor" column · 246x784 · 5 inside · try: sort gather
      a64 note "Tide feed" · 230x147 · due 2026-09-17 · 10w
      a61 task "Order pier sensors" · 230x147 · due 2026-09-18 · 7w
      a60 note "Kickoff notes" · 230x147 · due 2026-09-20 · 10w
      a67 task "Dock survey" · 230x147 · due 2026-09-25 · 7w
      a65 task "Permit renewal" · 230x147 · due 2026-09-30 · 10w

[15 @46.67s] desk: find Harbor
    find 'Harbor': 6 hit(s)
      a60 note "Kickoff notes" · 230x147 · due 2026-09-20 · 10w  in f68
      a61 task "Order pier sensors" · 230x147 · due 2026-09-18 · 7w  in f68
      a64 note "Tide feed" · 230x147 · due 2026-09-17 · 10w  in f68
      a65 task "Permit renewal" · 230x147 · due 2026-09-30 · 10w  in f68
      a67 task "Dock survey" · 230x147 · due 2026-09-25 · 7w  in f68
      f68 surface "Harbor" column · 246x784 · 5 inside · try: sort gather

## reply
Created the **Harbor** column at the left of the desk. It contains all five Harbor items, ordered soonest due first; verification confirms none remain elsewhere.

Hardest step: fitting a new left-side column on a full desk required tiling the desk into rows and reordering Harbor first. The gather affordance usefully deduplicated the repeated Permit renewal item.

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