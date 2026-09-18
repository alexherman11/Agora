# r3-big-moo-1  task=big variant=moo
prompt: Somewhere on this desk are the notes and tasks for the Harbor project. Collect all of them into a new column called Harbor on the left of the desk, soonest due first, and make sure none of them is still showing anywhere else. You have a budget of 40 desk calls; it is a big desk, so do not read everything.

[1 @6.51s] desk: find Harbor
    find 'Harbor': 6 hit(s)
      a60 note "Kickoff notes" · 284x124 · due 2026-09-20 · 10w  in f02
      a61 task "Order pier sensors" · 260x140 at 40,40 · due 2026-09-18 · 7w · hidden by a63  in f03
      a64 note "Tide feed" · 284x30 · due 2026-09-17 · 10w  in f06
      a65 task "Permit renewal" · 260x140 at 300,200 · due 2026-09-30 · 10w · also x1  in f04
      a66 task "Permit renewal" · 260x140 at 20,40 · due 2026-09-30 · 10w · also x1  in f05
      a67 task "Dock survey" · 260x140 at 30,200 · due 2026-09-25 · 7w  in f05

[2 @10.42s] desk: look
    f01 surface "desk" free · 1280x800 · 4 inside
      f02 surface "Inbox" column · 300x800 at 0,0 · 6 inside  (open f02 to see inside)
      f03 surface "Projects" free · 640x400 at 310,0 · 6 inside  (open f03 to see inside)
      f04 surface "Reading" free · 640x390 at 310,410 · 3 inside  (open f04 to see inside)
      f05 surface "Pile" free · 320x800 at 960,0 · 7 inside  (open f05 to see inside)

[3 @13.51s] desk: help split
    split  (on: surface; level 3)
      Divide the children into two tiled groups side by side (left/right) or stacked (top/bottom) by a rule.
      args: by=kind|title|tag left=<value> [right=<value>] [as=row|column]
      e.g. do split f04 by=kind left=image

[4 @15.36s] desk: help append
    append  (on: text; level 1)
      Add a line at the end of the text. Edits the subject: every appearance changes.
      args: line=<str>
      e.g. do append a18 line="4. Review"

[5 @17.5s] desk: examine f01
    f01 surface "desk" free · 1280x800 · 4 inside
      a free surface (the desk itself), holding 4 thing(s): f02, f03, f04, f05
      where: screen 0,0 1280x800 · in - (-) · clear
      verbs from surface: tile rename group sort tidy split gather stack
      (help <verb> explains one; do <verb> f01 ... uses it)

[6 @19.69s] desk: help gather
    gather  (on: surface; level 3)
      Bring every appearance matching words into this surface (one per subject), then sort if tiled.
      args: words=<text> [by=due|title]
      e.g. do gather f02 words=harbor by=due

[7 @22.19s] desk: help group
    group  (on: surface; level 1)
      Make a new empty surface inside this one.
      args: title=<str> as=free|column|row
      e.g. do group f04 title="Pictures" as=column

[8 @24.7s] desk: help move
    move  (on: thing; level 1)
      Put this somewhere else.
      args: into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>
      e.g. do move a04 into=f02

[9 @28.66s] desk: help tile
    tile  (on: surface; level 1)
      Lay the children out as a column or row, sharing the space, nothing overlapping.
      args: as=column|row
      e.g. do tile f04 as=row

[10 @31.14s] desk: do group f01 title=Harbor as=column
    ok group f01 title=Harbor as=column  [e1] → created f68
      f68 surface "Harbor" column · 640x400 at 16,16 · empty
        where: screen 16,16 640x400 · in f01 (free) local 16,16 z5 · covers f02, covers f03, covers f04
      now: f01 surface "desk" free · 1280x800 · 5 inside

[11 @34.58s] desk: examine f68
    f68 surface "Harbor" column · 640x400 at 16,16 · empty
      a column surface inside f01, empty
      where: screen 16,16 640x400 · in f01 (free) local 16,16 z5 · covers f02, covers f03, covers f04
      verbs from surface: untile rename group gather
      verbs from thing: move resize raise lower remove
      (help <verb> explains one; do <verb> f68 ... uses it)

[12 @44.75s] desk: help tidy
    tidy  (on: surface; level 2)
      Make nothing overlap: tile the surface as a column (or row) with the current order.
      args: [as=column|row]
      e.g. do tidy f04

[13 @50.76s] desk: do gather f68 words=Harbor by=due
    ok gather f68 words=Harbor by=due  [e2..e12, 11 steps]
      5 subject(s) matched; 6 step(s)
      now: f68 surface "Harbor" column · 640x400 at 16,16 · 5 inside
      a64 note "Tide feed" · 624x70 · due 2026-09-17 · 10w
      a61 task "Order pier sensors" · 624x70 · due 2026-09-18 · 7w
      a60 note "Kickoff notes" · 624x70 · due 2026-09-20 · 10w
      a67 task "Dock survey" · 624x70 · due 2026-09-25 · 7w
      a65 task "Permit renewal" · 624x70 · due 2026-09-30 · 10w

[14 @56.58s] desk: look f01
    f01 surface "desk" free · 1280x800 · 5 inside
      f02 surface "Inbox" column · 300x800 at 0,0 · 5 inside · 47% hidden by f68  (open f02 to see inside)
      f03 surface "Projects" free · 640x400 at 310,0 · 5 inside · 51% hidden by f68  (open f03 to see inside)
      f04 surface "Reading" free · 640x390 at 310,410 · 2 inside  (open f04 to see inside)
      f05 surface "Pile" free · 320x800 at 960,0 · 5 inside  (open f05 to see inside)
      f68 surface "Harbor" column · 640x400 at 16,16 · 5 inside  (open f68 to see inside)

[15 @58.33s] desk: do move f68 before=f02
    ok move f68 before=f02  [e13]
      now: f68 surface "Harbor" column · 640x400 at 16,0 · 5 inside

[16 @60.48s] desk: look f01
    f01 surface "desk" free · 1280x800 · 5 inside
      f68 surface "Harbor" column · 640x400 at 16,0 · 5 inside  (open f68 to see inside)
      f02 surface "Inbox" column · 300x800 at 0,1000 · 5 inside · offscreen-part · spills-parent  (open f02 to see inside)
      f03 surface "Projects" free · 640x400 at 310,2000 · 5 inside · offscreen-part · spills-parent  (open f03 to see inside)
      f04 surface "Reading" free · 640x390 at 310,3000 · 2 inside · offscreen-part · spills-parent  (open f04 to see inside)
      f05 surface "Pile" free · 320x800 at 960,4000 · 5 inside · offscreen-part · spills-parent  (open f05 to see inside)

[17 @63.14s] desk: do tidy f01 as=row
    ok tidy f01 as=row  [e14]
      now: f01 surface "desk" row · 1280x800 · 5 inside
      f02 surface "Inbox" column · 246x784 · 5 inside
      f68 surface "Harbor" column · 246x784 · 5 inside
      f03 surface "Projects" free · 246x784 · 5 inside
      f04 surface "Reading" free · 246x784 · 2 inside
      f05 surface "Pile" free · 246x784 · 5 inside

[18 @65.67s] desk: look f01
    f01 surface "desk" row · 1280x800 · 5 inside
      f02 surface "Inbox" column · 246x784 · 5 inside  (open f02 to see inside)
      f68 surface "Harbor" column · 246x784 · 5 inside  (open f68 to see inside)
      f03 surface "Projects" free · 246x784 · 5 inside  (open f03 to see inside)
      f04 surface "Reading" free · 246x784 · 2 inside  (open f04 to see inside)
      f05 surface "Pile" free · 246x784 · 5 inside  (open f05 to see inside)

[19 @67.51s] desk: do move f68 before=f02
    ok move f68 before=f02  [e15]
      now: f68 surface "Harbor" column · 246x784 · 5 inside  (1st of 5 in f01)

[20 @70.22s] desk: look f01
    f01 surface "desk" row · 1280x800 · 5 inside
      f68 surface "Harbor" column · 246x784 · 5 inside  (open f68 to see inside)
      f02 surface "Inbox" column · 246x784 · 5 inside  (open f02 to see inside)
      f03 surface "Projects" free · 246x784 · 5 inside  (open f03 to see inside)
      f04 surface "Reading" free · 246x784 · 2 inside  (open f04 to see inside)
      f05 surface "Pile" free · 246x784 · 5 inside  (open f05 to see inside)

[21 @70.22s] desk: find Harbor
    find 'Harbor': 6 hit(s)
      a60 note "Kickoff notes" · 230x147 · due 2026-09-20 · 10w  in f68
      a61 task "Order pier sensors" · 230x147 · due 2026-09-18 · 7w  in f68
      a64 note "Tide feed" · 230x147 · due 2026-09-17 · 10w  in f68
      a65 task "Permit renewal" · 230x147 · due 2026-09-30 · 10w  in f68
      a67 task "Dock survey" · 230x147 · due 2026-09-25 · 7w  in f68
      f68 surface "Harbor" column · 246x784 · 5 inside

[22 @72.48s] desk: look f68
    f68 surface "Harbor" column · 246x784 · 5 inside
      a64 note "Tide feed" · 230x147 · due 2026-09-17 · 10w
      a61 task "Order pier sensors" · 230x147 · due 2026-09-18 · 7w
      a60 note "Kickoff notes" · 230x147 · due 2026-09-20 · 10w
      a67 task "Dock survey" · 230x147 · due 2026-09-25 · 7w
      a65 task "Permit renewal" · 230x147 · due 2026-09-30 · 10w

## reply
Created the leftmost Harbor column with all 5 Harbor items, due soonest first. Verified they appear only in Harbor.

Hardest step was placing the new column without overlaps; tidying the desk into a row resolved it. The move/reorder behavior before tiling was somewhat unclear.

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