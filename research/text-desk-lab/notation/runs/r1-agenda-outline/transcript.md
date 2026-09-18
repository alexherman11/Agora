# r1-agenda-outline  task=agenda variant=outline
prompt: Add 'Review the text desk trial' as the last item of the standup agenda, and make sure the agenda shows only once on the desk, in the Meeting panel.

[1 @3.78s] desk: look
    f01 surface "desk" free · 1280x800 · 3 inside
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside  (open f02 to see inside)
      f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside  (open f03 to see inside)
      f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside  (open f04 to see inside)

[2 @6.56s] desk: open f03
    f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27
      a27 chat "Priya" · 320x160 at 300,200 · 14w

[3 @9.09s] desk: read a18
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    ---

[4 @9.09s] desk: pivot a18
    s10 note "Standup agenda" · 10w
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1  in f03 "Meeting"
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26  in f04 "Scratch"
      verbs: edit title=<str> | text=<str> | append=<str>  place into=<surface>

[5 @9.09s] desk: verbs a18
    a18 verbs:
      move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>
      resize to=<w>x<h>
      raise (to front)
      lower (to back)
      remove (removes this appearance only; the subject survives)
      fold (show/hide content on screen)
      edit title=<str> | text=<str> | append=<str>  (edits the subject; every appearance changes)

[6 @12.86s] desk: open f04
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w

[7 @15.36s] desk: do append a18 append="\n4. Review the text desk trial"
    ERR no such id 'append' (ids look like f02, a05, s03; use look or find)

[8 @18.45s] desk: help
    commands (one per call):
      look [id] [:1|:2|:3]   outline from id (default desk). :1 folded line, :2 open (default), :3 focus
      open id | close id     expand / collapse id in later looks (view only; nothing moves)
      read id                full text of a note/task/etc (via an appearance or subject id)
      where id               exact geometry and spatial relations
      verbs id               what you can do to id, with argument forms
      pivot id               appearance -> its subject and every place it appears; subject -> appearances
      find words             search titles and text
      history [id]           recent events (with undo ids)
      do verb id k=v ...     change something. e.g. do move a04 into=f02   do edit a03 append="line"
      undo eN                revert an event
      plan / apply           (apply variant only) paste an edited outline; the desk diffs it into ops
    ids: f.. surface, a.. appearance, s.. subject, e.. event. quote values with spaces.

[9 @20.52s] desk: do edit a18 append="\n4. Review the text desk trial"
    ok e1: edit a18 append='\\n4. Review the text desk trial'
      subject s10 changed; 2 appearance(s) now show the new content
      now: a18 note "Standup agenda" · 380x220 at 20,20 · 20w · also x1

[10 @23.53s] desk: read a18
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    \n4. Review the text desk trial
    4. Budget check (Sam)
    ---

[11 @31.03s] desk: do edit a18 text="1. Yesterday's blockers
2. Sensor vendor decision
3. Demo schedule
4. Budget check (Sam)
5. Review the text desk trial"
    ok e3: edit a18 text="1. Yesterday's blockers\n2. Sensor vendor decision\n3. Demo schedule\n4. Budget check (Sam)\n5. Review the text desk trial"
      subject s10 changed; 2 appearance(s) now show the new content
      now: a18 note "Standup agenda" · 380x220 at 20,20 · 20w · also x1

[12 @33.05s] desk: look a24 :3
    !! since your last look: e2 edit s10 by sam
    a24 note "Standup agenda" · 320x180 at 300,200 · 20w · also x1 · 52% hidden by a25,a26
      subject s10
      ---
      1. Yesterday's blockers
      2. Sensor vendor decision
      3. Demo schedule
      4. Budget check (Sam)
      5. Review the text desk trial
      ---
      where: screen 720,600 320x180 · in f04 (free) local 300,200 z5 · covers a20, covers a21, covers a23, under a25, under a26 · 52% hidden
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  fold (show/hide content on screen)  edit title=<str> | text=<str> | append=<str>  (edits the subject; every appearance changes)

[13 @36.27s] desk: do remove a24
    ok e4: remove a24
      appearance removed; the subject still exists

[14 @37.89s] desk: look f01 :3
    f01 surface "desk" free · 1280x800 · 3 inside
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside
      f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside
      f04 surface "Scratch" free · 840x400 at 420,400 · 6 inside
      where: screen 0,0 1280x800 · in - (-) · clear
      verbs: tile as=column|row  (lay children out without overlap)  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[15 @40.09s] desk: look f03 :3
    f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside
      a18 note "Standup agenda" · 380x220 at 20,20 · 20w
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27
      a27 chat "Priya" · 320x160 at 300,200 · 14w
      where: screen 420,0 840x380 · in f01 (free) local 420,0 z2 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

## reply
Added “Review the text desk trial” as the final agenda item and removed the duplicate agenda from Scratch. The agenda now appears only in the Meeting panel. Hardest step was preserving the concurrent Budget check while ensuring the new item stayed last; append escaping was initially unclear.

## assessment
{
 "review_line_last": true,
 "sam_line_kept": true,
 "single_appearance": true,
 "in_meeting": true,
 "original_items_kept": true,
 "injection_fired": true,
 "pass": true
}