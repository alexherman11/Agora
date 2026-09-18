# r1-harbor-outline  task=harbor variant=outline
prompt: Gather everything about the Harbor project into the Harbor column, soonest due date first. Leave unrelated things where they are, but nothing Harbor-related may be left covered up.

[1 @4.67s] desk: look :3
    f01 surface "desk" free · 1280x800 · 3 inside
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside
      f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside
      f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside
      where: screen 0,0 1280x800 · in - (-) · clear
      verbs: tile as=column|row  (lay children out without overlap)  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[2 @7.03s] desk: look f02 :3
    f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside
      a17 task "Harbor permit renewal" · 384x388 · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · 384x388 · due 2026-09-20 · 17w
      where: screen 0,0 400x800 · in f01 (free) local 0,0 z1 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  untile  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[3 @7.03s] desk: look f03 :3
    f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27
      a27 chat "Priya" · 320x160 at 300,200 · 14w
      where: screen 420,0 840x380 · in f01 (free) local 420,0 z2 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[4 @7.03s] desk: look f04 :3
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w
      where: screen 420,400 840x400 · in f01 (free) local 420,400 z3 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[5 @10.94s] desk: read a16
    s05 note "Harbor kickoff" · appears at a16 · tags harbor · due 2026-09-20
    ---
    Kickoff for the Harbor project.
    Attendees: Sam, Priya, Alex.
    Decide the pier sensor vendor by the 20th.
    ---

[6 @10.94s] desk: read a17
    s08 task "Harbor permit renewal" · appears at a17 · tags harbor · due 2026-09-30
    ---
    City permit for the Harbor dock expires end of month.
    ---

[7 @10.94s] desk: read a18
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    ---

[8 @10.94s] desk: read a19
    s11 image "whiteboard.jpg" · appears at a19
    ---
    
    ---

[9 @10.94s] desk: read a20
    s07 note "Tide data format" · appears at a20 · tags harbor · due 2026-09-17
    ---
    Harbor tide feed is CSV, one row per 6 minutes. Need a parser before the kickoff.
    ---

[10 @10.94s] desk: read a21
    s12 image "dock-photo.png" · appears at a21
    ---
    
    ---

[11 @10.94s] desk: read a22
    s06 task "Order pier sensors" · appears at a22 · tags harbor · due 2026-09-18
    ---
    Get quotes from two vendors for the Harbor pier sensors.
    ---

[12 @10.94s] desk: read a23
    s09 note "Grocery list" · appears at a23
    ---
    eggs
    rice
    limes
    coffee
    ---

[13 @10.94s] desk: read a24
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    ---

[14 @10.94s] desk: read a25
    s13 image "layout-sketch.png" · appears at a25
    ---
    
    ---

[15 @10.94s] desk: read a26
    s14 note "Blog draft" · appears at a26
    ---
    Why we moved the desk to text.
    
    A screen is already a data structure; the problem is notation.
    ---

[16 @10.94s] desk: read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    ---

[17 @30.59s] desk: do move a20 into=f02
    ok e1: move a20 into=f02
      now: a20 note "Tide data format" · 384x256 · due 2026-09-17 · 16w

[18 @32.33s] desk: look f02 :3
    f02 surface "Harbor" column · 400x800 at 0,0 · 3 inside
      a17 task "Harbor permit renewal" · 384x256 · due 2026-09-30 · 10w
      a20 note "Tide data format" · 384x256 · due 2026-09-17 · 16w
      a16 note "Harbor kickoff" · 384x256 · due 2026-09-20 · 17w
      where: screen 0,0 400x800 · in f01 (free) local 0,0 z1 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  untile  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[19 @35.2s] desk: do move a20 before=a17
    ok e2: move a20 before=a17
      now: a20 note "Tide data format" · 384x256 · due 2026-09-17 · 16w

[20 @38.45s] desk: look f04 :3
    f04 surface "Scratch" free · 840x400 at 420,400 · 6 inside
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w
      where: screen 420,400 840x400 · in f01 (free) local 420,400 z3 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[21 @41.2s] desk: do move a22 into=f02
    ok e3: move a22 into=f02
      now: a22 task "Order pier sensors" · 384x190 · due 2026-09-18 · 10w

[22 @44.92s] desk: look f02 :3
    f02 surface "Harbor" column · 400x800 at 0,0 · 4 inside
      a20 note "Tide data format" · 384x190 · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · 384x190 · due 2026-09-18 · 10w
      a17 task "Harbor permit renewal" · 384x190 · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · 384x190 · due 2026-09-20 · 17w
      where: screen 0,0 400x800 · in f01 (free) local 0,0 z1 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  untile  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[23 @48.22s] desk: do move a16 before=a17
    ok e4: move a16 before=a17
      now: a16 note "Harbor kickoff" · 384x190 · due 2026-09-20 · 17w

[24 @59.06s] desk: look f03 :3
    f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27
      a27 chat "Priya" · 320x160 at 300,200 · 14w
      where: screen 420,0 840x380 · in f01 (free) local 420,0 z2 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[25 @63.27s] desk: do move a18 into=f02
    ok e5: move a18 into=f02
      now: a18 note "Standup agenda" · 384x150 · 10w · also x1

[26 @65.7s] desk: look f04 :3
    f04 surface "Scratch" free · 840x400 at 420,400 · 5 inside
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w
      where: screen 420,400 840x400 · in f01 (free) local 420,400 z3 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[27 @68.97s] desk: do remove a24
    ok e6: remove a24
      appearance removed; the subject still exists

[28 @71.77s] desk: look f04 :3
    f04 surface "Scratch" free · 840x400 at 420,400 · 4 inside
      a21 image "dock-photo.png" · 500x340 at 20,20 · 29% hidden by a25
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w
      where: screen 420,400 840x400 · in f01 (free) local 420,400 z3 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[29 @74.47s] desk: do move a21 into=f02
    ok e7: move a21 into=f02
      now: a21 image "dock-photo.png" · 384x124

[30 @77.19s] desk: look f03 :3
    f03 surface "Meeting" free · 840x380 at 420,0 · 2 inside
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27
      a27 chat "Priya" · 320x160 at 300,200 · 14w
      where: screen 420,0 840x380 · in f01 (free) local 420,0 z2 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[31 @78.95s] desk: do move a27 into=f02
    ok e8: move a27 into=f02
      now: a27 chat "Priya" · 384x105 · 14w

[32 @82.7s] desk: look f02 :3
    f02 surface "Harbor" column · 400x800 at 0,0 · 7 inside
      a20 note "Tide data format" · 384x105 · due 2026-09-17 · 16w
      a21 image "dock-photo.png" · 384x105
      a27 chat "Priya" · 384x105 · 14w
      a18 note "Standup agenda" · 384x105 · 10w
      a22 task "Order pier sensors" · 384x105 · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · 384x105 · due 2026-09-20 · 17w
      a17 task "Harbor permit renewal" · 384x105 · due 2026-09-30 · 10w
      where: screen 0,0 400x800 · in f01 (free) local 0,0 z1 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  untile  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[33 @88.59s] desk: do move a21 after=a17
    ok e9: move a21 after=a17
      now: a21 image "dock-photo.png" · 384x105

[34 @90.27s] desk: look f02 :3
    f02 surface "Harbor" column · 400x800 at 0,0 · 7 inside
      a20 note "Tide data format" · 384x105 · due 2026-09-17 · 16w
      a27 chat "Priya" · 384x105 · 14w
      a18 note "Standup agenda" · 384x105 · 10w
      a22 task "Order pier sensors" · 384x105 · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · 384x105 · due 2026-09-20 · 17w
      a17 task "Harbor permit renewal" · 384x105 · due 2026-09-30 · 10w
      a21 image "dock-photo.png" · 384x105
      where: screen 0,0 400x800 · in f01 (free) local 0,0 z1 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  untile  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[35 @92.16s] desk: do move a27 after=a21
    ok e10: move a27 after=a21
      now: a27 chat "Priya" · 384x105 · 14w

[36 @93.78s] desk: look f02 :3
    f02 surface "Harbor" column · 400x800 at 0,0 · 7 inside
      a20 note "Tide data format" · 384x105 · due 2026-09-17 · 16w
      a18 note "Standup agenda" · 384x105 · 10w
      a22 task "Order pier sensors" · 384x105 · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · 384x105 · due 2026-09-20 · 17w
      a17 task "Harbor permit renewal" · 384x105 · due 2026-09-30 · 10w
      a21 image "dock-photo.png" · 384x105
      a27 chat "Priya" · 384x105 · 14w
      where: screen 0,0 400x800 · in f01 (free) local 0,0 z1 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  untile  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[37 @96.2s] desk: do move a18 after=a27
    ok e11: move a18 after=a27
      now: a18 note "Standup agenda" · 384x105 · 10w

[38 @100.36s] desk: look f02 :3
    f02 surface "Harbor" column · 400x800 at 0,0 · 7 inside
      a20 note "Tide data format" · 384x105 · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · 384x105 · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · 384x105 · due 2026-09-20 · 17w
      a17 task "Harbor permit renewal" · 384x105 · due 2026-09-30 · 10w
      a21 image "dock-photo.png" · 384x105
      a27 chat "Priya" · 384x105 · 14w
      a18 note "Standup agenda" · 384x105 · 10w
      where: screen 0,0 400x800 · in f01 (free) local 0,0 z1 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  untile  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[39 @100.36s] desk: look f03 :3
    f03 surface "Meeting" free · 840x380 at 420,0 · 1 inside
      a19 image "whiteboard.jpg" · 400x300 at 420,20
      where: screen 420,0 840x380 · in f01 (free) local 420,0 z2 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[40 @100.36s] desk: look f04 :3
    f04 surface "Scratch" free · 840x400 at 420,400 · 3 inside
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w
      where: screen 420,400 840x400 · in f01 (free) local 420,400 z3 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

## reply
Gathered Harbor material into the Harbor column. Dated items are ordered Sep 17, 18, 20, and 30; related undated items follow, and the column is clear with no overlap. Unrelated items remain in Meeting/Scratch.

Hardest step was resolving related material that lacked an explicit Harbor tag, including the duplicate agenda. The due-date handling for undated items was the only unclear affordance; I placed them after all dated items.

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