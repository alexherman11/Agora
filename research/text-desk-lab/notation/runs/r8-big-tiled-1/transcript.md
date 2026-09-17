# r8-big-tiled-1  task=big variant=tiled
prompt: Somewhere on this desk are the notes and tasks for the Harbor project. Collect all of them into a new column called Harbor on the left of the desk, soonest due first, and make sure none of them is still showing anywhere else. You have a budget of 40 desk calls; it is a big desk, so do not read everything.

[1 @5.39s] desk: look
    f01 surface "desk" row · 1280x800 · 3 inside · try: sort
      f02 surface "Inbox" column · 297x784 · 6 inside · try: sort  (open f02 to see inside)
      f68 surface "Mid" column · 633x784 · 2 inside · try: sort  (open f68 to see inside)
      f05 surface "Pile" free · 316x784 · 7 inside · try: tile raise hidden,in:f05 group kind:chat,in:f05  (open f05 to see inside)

[2 @7.3s] desk: find Harbor
    find 'Harbor': 6 hit(s)
      a60 note "Kickoff notes" · 281x121 · due 2026-09-20 · 10w  in f02
      a61 task "Order pier sensors" · 260x140 at 40,40 · due 2026-09-18 · 7w · hidden by a63 · try: raise  in f03
      a64 note "Tide feed" · 284x30 · due 2026-09-17 · 10w  in f06
      a65 task "Permit renewal" · 260x140 at 300,200 · due 2026-09-30 · 10w · also x1 · try: remove also:a65  in f04
      a66 task "Permit renewal" · 260x140 at 20,40 · due 2026-09-30 · 10w · also x1 · try: remove also:a66  in f05
      a67 task "Dock survey" · 260x140 at 30,200 · due 2026-09-25 · 7w  in f05
      as a selection: ?harbor   e.g. do move ?harbor into=<surface> one=1   (help selections)

[3 @10.61s] desk: help create
    create  (on: surface; level 1)
      Make a new note, task or chat and place it on this surface.
      args: kind=note|task|chat title=<str> [text=<str>] [due=YYYY-MM-DD] [tags=a,b]
      e.g. do create f03 kind=task title="Send parser" due=2026-09-19

[4 @13.14s] desk: help append
    append  (on: text; level 1)
      Add a line at the end of the text. Edits the subject: every appearance changes.
      args: line=<str>
      e.g. do append a18 line="4. Review"

[5 @16.17s] desk: examine f01
    f01 surface "desk" row · 1280x800 · 3 inside · try: sort
      a row surface (the desk itself), holding 3 thing(s): f02, f68, f05
      where: screen 0,0 1280x800 · in - (-) · clear
      verbs from surface: tile(as=column|row)  untile  rename(title=<str>)  group(title=<str> as=free|column|row)  create(kind=note|task|chat title=<str> [text=<str>] [due=YYYY-MM-DD] [tags=a,b])  sort(by=due|title|kind [desc=1])
      any verb also takes a selection instead of an id (help selections)

[6 @25.17s] desk: help group
    group  (on: surface; level 1)
      Make a new empty surface inside this one.
      args: title=<str> as=free|column|row
      e.g. do group f04 title="Pictures" as=column

[7 @29.62s] desk: help move
    move  (on: thing; level 1)
      Put this somewhere else.
      args: into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>
      e.g. do move a04 into=f02

[8 @32.11s] desk: do group f01 title="Harbor" as=column
    ok group f01 title=Harbor as=column  [e1] → created f69
      f69 surface "Harbor" column · 420x784 · empty
        where: screen 850,8 420x784 · in f01 (row) local 850,8 z6 · clear
      now: f01 surface "desk" row · 1280x800 · 4 inside · try: sort

[9 @37.05s] desk: do remove a66
    ok remove a66  [e2]
      appearance removed; the subject still exists

[10 @39.81s] desk: do move ?harbor into=f69
    ERR stopped at move f69: cannot move a surface into itself; earlier steps undone

[11 @46.72s] desk: find Harbor
    find 'Harbor': 6 hit(s)
      a60 note "Kickoff notes" · 179x102 · due 2026-09-20 · 10w  in f02
      a61 task "Order pier sensors" · 260x140 at 40,40 · due 2026-09-18 · 7w · hidden by a63 · try: raise  in f03
      a64 note "Tide feed" · 284x26 · due 2026-09-17 · 10w  in f06
      a65 task "Permit renewal" · 260x140 at 300,200 · due 2026-09-30 · 10w · spills-parent  in f04
      a67 task "Dock survey" · 260x140 at 30,200 · due 2026-09-25 · 7w · spills-parent  in f05
      f69 surface "Harbor" column · 420x784 · empty
      as a selection: ?harbor   e.g. do move ?harbor into=<surface> one=1   (help selections)

[12 @49.16s] desk: do move ?harbor,kind:note into=f69
    ok move 2 thing(s) matching ?harbor,kind:note: a60 a64  [e13..e14, 2 steps]
      now: a60 note "Kickoff notes" · 404x735 · due 2026-09-20 · 10w  (1st of 2 in f69)
      now: a64 note "Tide feed" · 404x24 · due 2026-09-17 · 10w  (2nd of 2 in f69)

[13 @51.52s] desk: do move ?harbor,kind:task into=f69
    ok move 3 thing(s) matching ?harbor,kind:task: a61 a65 a67  [e15..e17, 3 steps]
      now: a61 task "Order pier sensors" · 404x80 · due 2026-09-18 · 7w  (4th of 5 in f69)
      now: a65 task "Permit renewal" · 404x96 · due 2026-09-30 · 10w  (3rd of 5 in f69)
      now: a67 task "Dock survey" · 404x116 · due 2026-09-25 · 7w  (2nd of 5 in f69)

[14 @55.09s] desk: look f69
    f69 surface "Harbor" column · 420x784 · 5 inside · try: sort
      a60 note "Kickoff notes" · 404x423 · due 2026-09-20 · 10w
      a67 task "Dock survey" · 404x116 · due 2026-09-25 · 7w
      a65 task "Permit renewal" · 404x96 · due 2026-09-30 · 10w
      a61 task "Order pier sensors" · 404x80 · due 2026-09-18 · 7w
      a64 note "Tide feed" · 404x24 · due 2026-09-17 · 10w

[15 @57.95s] desk: do sort f69 by=due
    ok sort f69 by=due  [e18..e22, 5 steps]
      order now: a64, a61, a60, a67, a65
      now: f69 surface "Harbor" column · 420x784 · 5 inside · try: sort  (4th of 4 in f01)
      a64 note "Tide feed" · 404x24 · due 2026-09-17 · 10w
      a61 task "Order pier sensors" · 404x79 · due 2026-09-18 · 7w
      a60 note "Kickoff notes" · 404x422 · due 2026-09-20 · 10w
      a67 task "Dock survey" · 404x115 · due 2026-09-25 · 7w
      a65 task "Permit renewal" · 404x95 · due 2026-09-30 · 10w

[16 @61.17s] desk: look f01
    f01 surface "desk" row · 1280x800 · 4 inside · try: sort
      f02 surface "Inbox" column · 195x784 · 5 inside · try: sort  (open f02 to see inside)
      f68 surface "Mid" column · 416x784 · 2 inside · try: sort  (open f68 to see inside)
      f05 surface "Pile" free · 207x784 · 5 inside · try: tile raise hidden,in:f05 group kind:chat,in:f05  (open f05 to see inside)
      f69 surface "Harbor" column · 420x784 · 5 inside · try: sort  (open f69 to see inside)

[17 @63.86s] desk: do move f69 before=f02
    ok move f69 before=f02  [e23]
      now: f69 surface "Harbor" column · 420x784 · 5 inside · try: sort  (1st of 4 in f01)

[18 @67.27s] desk: look f01
    f01 surface "desk" row · 1280x800 · 4 inside · try: sort
      f69 surface "Harbor" column · 420x784 · 5 inside · try: sort  (open f69 to see inside)
      f02 surface "Inbox" column · 195x784 · 5 inside · try: sort  (open f02 to see inside)
      f68 surface "Mid" column · 416x784 · 2 inside · try: sort  (open f68 to see inside)
      f05 surface "Pile" free · 207x784 · 5 inside · try: tile raise hidden,in:f05 group kind:chat,in:f05  (open f05 to see inside)

[19 @68.66s] desk: look f69
    f69 surface "Harbor" column · 420x784 · 5 inside · try: sort
      a64 note "Tide feed" · 404x24 · due 2026-09-17 · 10w
      a61 task "Order pier sensors" · 404x79 · due 2026-09-18 · 7w
      a60 note "Kickoff notes" · 404x422 · due 2026-09-20 · 10w
      a67 task "Dock survey" · 404x115 · due 2026-09-25 · 7w
      a65 task "Permit renewal" · 404x95 · due 2026-09-30 · 10w

[20 @72.73s] desk: find Harbor
    find 'Harbor': 6 hit(s)
      a60 note "Kickoff notes" · 404x422 · due 2026-09-20 · 10w  in f69
      a61 task "Order pier sensors" · 404x79 · due 2026-09-18 · 7w  in f69
      a64 note "Tide feed" · 404x24 · due 2026-09-17 · 10w  in f69
      a65 task "Permit renewal" · 404x95 · due 2026-09-30 · 10w  in f69
      a67 task "Dock survey" · 404x115 · due 2026-09-25 · 7w  in f69
      f69 surface "Harbor" column · 420x784 · 5 inside · try: sort
      as a selection: ?harbor   e.g. do move ?harbor into=<surface> one=1   (help selections)

## reply
Created the leftmost **Harbor** column. It contains all five Harbor items, sorted soonest due first; search confirms none remain elsewhere. Removed the duplicate Permit renewal appearance.

Hardest step was excluding the newly named Harbor surface from the Harbor search selection. The selection syntax’s dynamic matching was slightly unclear.

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