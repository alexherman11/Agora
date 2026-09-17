# r5-big-acme-1  task=big variant=acme
prompt: Somewhere on this desk are the notes and tasks for the Harbor project. Collect all of them into a new column called Harbor on the left of the desk, soonest due first, and make sure none of them is still showing anywhere else. You have a budget of 40 desk calls; it is a big desk, so do not read everything.

[1 @6.39s] desk: find Harbor
    find 'Harbor': 6 hit(s)
      a60 note "Kickoff notes" · 284x124 · due 2026-09-20 · 10w  in f02
      a61 task "Order pier sensors" · 260x140 at 40,40 · due 2026-09-18 · 7w · hidden by a63 · try: reveal  in f03
      a64 note "Tide feed" · 284x30 · due 2026-09-17 · 10w  in f06
      a65 task "Permit renewal" · 260x140 at 300,200 · due 2026-09-30 · 10w · also x1 · try: dedupe  in f04
      a66 task "Permit renewal" · 260x140 at 20,40 · due 2026-09-30 · 10w · also x1 · try: dedupe  in f05
      a67 task "Dock survey" · 260x140 at 30,200 · due 2026-09-25 · 7w  in f05

[2 @9.73s] desk: look
    f01 surface "desk" free · 1280x800 · 4 inside
      f02 surface "Inbox" column · 300x800 at 0,0 · 6 inside · try: sort gather  (open f02 to see inside)
      f03 surface "Projects" free · 640x400 at 310,0 · 6 inside · try: tidy split  (open f03 to see inside)
      f04 surface "Reading" free · 640x390 at 310,410 · 3 inside · try: tidy split  (open f04 to see inside)
      f05 surface "Pile" free · 320x800 at 960,0 · 7 inside · try: tidy split  (open f05 to see inside)

[3 @12.56s] desk: help append
    append  (on: text; level 1)
      Add a line at the end of the text. Edits the subject: every appearance changes.
      args: line=<str>
      e.g. do append a18 line="4. Review"

[4 @14.8s] desk: examine f01
    f01 surface "desk" free · 1280x800 · 4 inside
      a free surface (the desk itself), holding 4 thing(s): f02, f03, f04, f05
      where: screen 0,0 1280x800 · in - (-) · clear
      verbs from surface: tile rename group create sort tidy split gather stack
        sort: Reorder the children of a tiled surface.  (by=due|title|kind [desc=1])
        tidy: Make nothing overlap: tile the surface as a column (or row) with the current order.  ([as=column|row])
        split: Divide the children into two tiled groups side by side (left/right) or stacked (top/bottom) by a rule.  (by=kind|title|tag left=<value> [right=<value>] [as=row|column])
        gather: Bring every appearance matching words into this surface (one per subject), then sort if tiled.  (words=<text> [by=due|title])
        stack: Pile the children neatly at the top-left, each offset a little, front to back in the current z order.
      (help <verb> explains one; do <verb> f01 ... uses it)

[5 @17.19s] desk: help create
    create  (on: surface; level 1)
      Make a new note, task or chat and place it on this surface.
      args: kind=note|task|chat title=<str> [text=<str>] [due=YYYY-MM-DD] [tags=a,b]
      e.g. do create f03 kind=task title="Send parser" due=2026-09-19

[6 @20.05s] desk: help group
    group  (on: surface; level 1)
      Make a new empty surface inside this one.
      args: title=<str> as=free|column|row
      e.g. do group f04 title="Pictures" as=column

[7 @25.76s] desk: do group f01 title=Harbor as=column
    ok group f01 title=Harbor as=column  [e1] → created f68
      f68 surface "Harbor" column · 640x400 at 16,16 · empty · try: gather
        where: screen 16,16 640x400 · in f01 (free) local 16,16 z5 · covers f02, covers f03, covers f04
      no free space in f01: f68 covers f02, covers f03, covers f04; move it, resize it, or tile f01 so nothing overlaps
      now: f01 surface "desk" free · 1280x800 · 5 inside · try: tidy split

[8 @29.05s] desk: examine f68
    f68 surface "Harbor" column · 640x400 at 16,16 · empty · try: gather
      a column surface inside f01, empty
      where: screen 16,16 640x400 · in f01 (free) local 16,16 z5 · covers f02, covers f03, covers f04
      verbs from surface: untile rename group create gather
      verbs from thing: move resize raise lower remove
        gather: Bring every appearance matching words into this surface (one per subject), then sort if tiled.  (words=<text> [by=due|title])
      (help <verb> explains one; do <verb> f68 ... uses it)

[9 @31.84s] desk: help move
    move  (on: thing; level 1)
      Put this somewhere else.
      args: into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>
      e.g. do move a04 into=f02

[10 @42.98s] desk: do gather f68 words=Harbor by=due
    ok gather f68 words=Harbor by=due  [e2..e12, 11 steps]
      5 subject(s) matched; 6 step(s)
      now: f68 surface "Harbor" column · 640x400 at 16,16 · 5 inside · try: sort gather
      a64 note "Tide feed" · 624x70 · due 2026-09-17 · 10w
      a61 task "Order pier sensors" · 624x70 · due 2026-09-18 · 7w
      a60 note "Kickoff notes" · 624x70 · due 2026-09-20 · 10w
      a67 task "Dock survey" · 624x70 · due 2026-09-25 · 7w
      a65 task "Permit renewal" · 624x70 · due 2026-09-30 · 10w

[11 @47.22s] desk: look f01
    f01 surface "desk" free · 1280x800 · 5 inside · try: tidy split
      f02 surface "Inbox" column · 300x800 at 0,0 · 5 inside · 47% hidden by f68 · try: sort gather  (open f02 to see inside)
      f03 surface "Projects" free · 640x400 at 310,0 · 5 inside · 51% hidden by f68 · try: tidy split  (open f03 to see inside)
      f04 surface "Reading" free · 640x390 at 310,410 · 2 inside · try: tidy split  (open f04 to see inside)
      f05 surface "Pile" free · 320x800 at 960,0 · 5 inside · try: tidy split  (open f05 to see inside)
      f68 surface "Harbor" column · 640x400 at 16,16 · 5 inside · try: sort gather  (open f68 to see inside)

[12 @52.17s] desk: do move f68 before=f02
    ok move f68 before=f02
      note: f01 is a free surface, so before/after only changed stacking order, not position. tile it for order to mean position.  [e13]
      now: f68 surface "Harbor" column · 640x400 at 16,0 · 5 inside · try: sort gather

[13 @54.7s] desk: look f01
    f01 surface "desk" free · 1280x800 · 5 inside
      f68 surface "Harbor" column · 640x400 at 16,0 · 5 inside · try: sort gather  (open f68 to see inside)
      f02 surface "Inbox" column · 300x800 at 0,1000 · 5 inside · offscreen-part · spills-parent · try: sort gather  (open f02 to see inside)
      f03 surface "Projects" free · 640x400 at 310,2000 · 5 inside · offscreen-part · spills-parent · try: tidy split  (open f03 to see inside)
      f04 surface "Reading" free · 640x390 at 310,3000 · 2 inside · offscreen-part · spills-parent · try: tidy split  (open f04 to see inside)
      f05 surface "Pile" free · 320x800 at 960,4000 · 5 inside · offscreen-part · spills-parent · try: tidy split  (open f05 to see inside)

[14 @58.25s] desk: do tidy f01 as=row
    ok tidy f01 as=row  [e14]
      now: f01 surface "desk" row · 1280x800 · 5 inside · try: sort gather
      f02 surface "Inbox" column · 246x784 · 5 inside · try: sort gather
      f68 surface "Harbor" column · 246x784 · 5 inside · try: sort gather
      f03 surface "Projects" free · 246x784 · 5 inside · try: tidy split
      f04 surface "Reading" free · 246x784 · 2 inside · try: tidy split
      f05 surface "Pile" free · 246x784 · 5 inside · try: tidy split

[15 @61.8s] desk: do move f68 before=f02
    ok move f68 before=f02  [e15]
      now: f68 surface "Harbor" column · 246x784 · 5 inside · try: sort gather  (1st of 5 in f01)

[16 @66.59s] desk: look f01 :2
    f01 surface "desk" row · 1280x800 · 5 inside · try: sort gather
      f68 surface "Harbor" column · 246x784 · 5 inside · try: sort gather  (open f68 to see inside)
      f02 surface "Inbox" column · 246x784 · 5 inside · try: sort gather  (open f02 to see inside)
      f03 surface "Projects" free · 246x784 · 5 inside · try: tidy split  (open f03 to see inside)
      f04 surface "Reading" free · 246x784 · 2 inside · try: tidy split  (open f04 to see inside)
      f05 surface "Pile" free · 246x784 · 5 inside · try: tidy split  (open f05 to see inside)

[17 @69.45s] desk: look f68
    f68 surface "Harbor" column · 246x784 · 5 inside · try: sort gather
      a64 note "Tide feed" · 230x147 · due 2026-09-17 · 10w
      a61 task "Order pier sensors" · 230x147 · due 2026-09-18 · 7w
      a60 note "Kickoff notes" · 230x147 · due 2026-09-20 · 10w
      a67 task "Dock survey" · 230x147 · due 2026-09-25 · 7w
      a65 task "Permit renewal" · 230x147 · due 2026-09-30 · 10w

## reply
Created the leftmost **Harbor** column with all 5 Harbor subjects, sorted soonest due first. Removed their other appearances, including the duplicate Permit renewal.

Hardest step was fitting the new column into the crowded desk; I tiled the desk into a row to make Harbor clearly leftmost. The move/reorder behavior on a free surface was initially unclear.

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