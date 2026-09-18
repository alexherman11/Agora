# r1-tidy-structured  task=tidy variant=structured
prompt: The Scratch area is a pile. Arrange it so nothing overlaps: pictures on the left, text on the right.

[1 @4.34s] look: {"level": 3}
    f01 surface "desk" free · 1280x800 · 3 inside
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside
      f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside
      f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside
      where: screen 0,0 1280x800 · in - (-) · clear
      verbs: tile as=column|row  (lay children out without overlap)  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

[2 @6.45s] open: {"target": "f04"}
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w

[3 @6.45s] look: {"target": "f04", "level": 3}
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

[4 @12.36s] verbs: {"target": "a21"}
    a21 verbs:
      move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>
      resize to=<w>x<h>
      raise (to front)
      lower (to back)
      remove (removes this appearance only; the subject survives)
      fold (show/hide content on screen)
      edit title=<str> | text=<str> | append=<str>  (edits the subject; every appearance changes)

[5 @20.86s] do: {"target": "a21", "verb": "resize", "args": {"to": "400x190"}}
    ok e1: resize a21 to=400x190
      now: a21 image "dock-photo.png" · 400x190 at 20,20

[6 @20.86s] do: {"target": "a21", "verb": "move", "args": {"to": "10,5"}}
    ok e2: move a21 to=10,5
      now: a21 image "dock-photo.png" · 400x190 at 10,5

[7 @20.86s] do: {"target": "a25", "verb": "resize", "args": {"to": "400x190"}}
    ok e3: resize a25 to=400x190
      now: a25 image "layout-sketch.png" · 400x190 at 40,220 · offscreen-part · spills-parent

[8 @20.86s] do: {"target": "a25", "verb": "move", "args": {"to": "10,205"}}
    ok e4: move a25 to=10,205
      now: a25 image "layout-sketch.png" · 400x190 at 10,205

[9 @20.86s] do: {"target": "a20", "verb": "resize", "args": {"to": "410x70"}}
    ok e5: resize a20 to=410x70
      now: a20 note "Tide data format" · 410x70 at 60,60 · due 2026-09-17 · 16w · 85% hidden by a21

[10 @20.86s] do: {"target": "a20", "verb": "move", "args": {"to": "420,5"}}
    ok e6: move a20 to=420,5
      now: a20 note "Tide data format" · 410x70 at 420,5 · due 2026-09-17 · 16w · 56% hidden by a22,a23

[11 @20.86s] do: {"target": "a22", "verb": "resize", "args": {"to": "410x70"}}
    ok e7: resize a22 to=410x70
      now: a22 task "Order pier sensors" · 410x70 at 540,30 · due 2026-09-18 · 10w · 33% hidden by a23 · offscreen-part · spills-parent

[12 @20.86s] do: {"target": "a22", "verb": "move", "args": {"to": "420,82"}}
    ok e8: move a22 to=420,82
      now: a22 task "Order pier sensors" · 410x70 at 420,82 · due 2026-09-18 · 10w · 58% hidden by a23

[13 @20.86s] do: {"target": "a23", "verb": "resize", "args": {"to": "410x70"}}
    ok e9: resize a23 to=410x70
      now: a23 note "Grocery list" · 410x70 at 560,60 · 4w · offscreen-part · spills-parent

[14 @20.86s] do: {"target": "a23", "verb": "move", "args": {"to": "420,159"}}
    ok e10: move a23 to=420,159
      now: a23 note "Grocery list" · 410x70 at 420,159 · 4w · 20% hidden by a24

[15 @20.86s] do: {"target": "a24", "verb": "resize", "args": {"to": "410x70"}}
    ok e11: resize a24 to=410x70
      now: a24 note "Standup agenda" · 410x70 at 300,200 · 10w · also x1 · 44% hidden by a25,a26

[16 @20.88s] do: {"target": "a24", "verb": "move", "args": {"to": "420,236"}}
    ok e12: move a24 to=420,236
      now: a24 note "Standup agenda" · 410x70 at 420,236 · 10w · also x1 · 68% hidden by a26

[17 @20.88s] do: {"target": "a26", "verb": "resize", "args": {"to": "410x70"}}
    ok e13: resize a26 to=410x70
      now: a26 note "Blog draft" · 410x70 at 520,240 · 18w · offscreen-part · spills-parent

[18 @20.88s] do: {"target": "a26", "verb": "move", "args": {"to": "420,313"}}
    ok e14: move a26 to=420,313
      now: a26 note "Blog draft" · 410x70 at 420,313 · 18w

[19 @22.83s] look: {"target": "f04", "level": 3}
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside
      a20 note "Tide data format" · 410x70 at 420,5 · due 2026-09-17 · 16w
      a21 image "dock-photo.png" · 400x190 at 10,5
      a22 task "Order pier sensors" · 410x70 at 420,82 · due 2026-09-18 · 10w
      a23 note "Grocery list" · 410x70 at 420,159 · 4w
      a24 note "Standup agenda" · 410x70 at 420,236 · 10w · also x1
      a25 image "layout-sketch.png" · 400x190 at 10,205
      a26 note "Blog draft" · 410x70 at 420,313 · 18w
      where: screen 420,400 840x400 · in f01 (free) local 420,400 z3 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

## reply
Arranged Scratch with both pictures on the left and all text items on the right, with no overlaps. Verified the final layout.

Hardest step was fitting five text items within the right column; resizing them made the separation possible. The layout controls were clear.

## assessment
{
 "nothing_removed": true,
 "no_overlap": true,
 "images_left_of_text": true,
 "inside_scratch": true,
 "other_areas_untouched": true,
 "pass": true
}