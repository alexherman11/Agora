# r2-tidy-apply  task=tidy variant=apply
prompt: The Scratch area is a pile. Arrange it so nothing overlaps: pictures on the left, text on the right.

[1 @4.59s] desk: look
    f01 surface "desk" free · 1280x800 · 3 inside
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside  (open f02 to see inside)
      f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside  (open f03 to see inside)
      f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside  (open f04 to see inside)

[2 @6.19s] desk: open f04
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w

[3 @8.2s] desk: verbs a21
    a21 verbs:
      move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>
      resize to=<w>x<h>
      raise (to front)
      lower (to back)
      remove (removes this appearance only; the subject survives)
      fold (show/hide content on screen)
      append line=<str>  (adds a line at the end; edits the subject, so every appearance changes)
      retitle title=<str>
      rewrite text=<str>  (replaces all the text; write \n between lines)

[4 @19.38s] desk: do resize a21 to=390x185
    ok e1: resize a21 to=390x185
      now: a21 image "dock-photo.png" · 390x185 at 20,20

[5 @19.38s] desk: do move a21 to=10,10
    ok e2: move a21 to=10,10
      now: a21 image "dock-photo.png" · 390x185 at 10,10

[6 @19.39s] desk: do resize a25 to=390x185
    ok e3: resize a25 to=390x185
      now: a25 image "layout-sketch.png" · 390x185 at 40,220 · offscreen-part · spills-parent

[7 @19.39s] desk: do move a25 to=10,205
    ok e4: move a25 to=10,205
      now: a25 image "layout-sketch.png" · 390x185 at 10,205

[8 @19.39s] desk: do resize a20 to=400x65
    ok e5: resize a20 to=400x65
      now: a20 note "Tide data format" · 400x65 at 60,60 · due 2026-09-17 · 16w · 85% hidden by a21

[9 @19.39s] desk: do move a20 to=420,10
    ok e6: move a20 to=420,10
      now: a20 note "Tide data format" · 400x65 at 420,10 · due 2026-09-17 · 16w · 62% hidden by a22,a23

[10 @19.39s] desk: do resize a22 to=400x65
    ok e7: resize a22 to=400x65
      now: a22 task "Order pier sensors" · 400x65 at 540,30 · due 2026-09-18 · 10w · 32% hidden by a23 · offscreen-part · spills-parent

[11 @19.39s] desk: do move a22 to=420,85
    ok e8: move a22 to=420,85
      now: a22 task "Order pier sensors" · 400x65 at 420,85 · due 2026-09-18 · 10w · 60% hidden by a23

[12 @19.39s] desk: do resize a23 to=400x65
    ok e9: resize a23 to=400x65
      now: a23 note "Grocery list" · 400x65 at 560,60 · 4w · offscreen-part · spills-parent

[13 @19.39s] desk: do move a23 to=420,160
    ok e10: move a23 to=420,160
      now: a23 note "Grocery list" · 400x65 at 420,160 · 4w · 19% hidden by a24

[14 @19.39s] desk: do resize a24 to=400x65
    ok e11: resize a24 to=400x65
      now: a24 note "Standup agenda" · 400x65 at 300,200 · 10w · also x1 · 40% hidden by a25,a26

[15 @19.39s] desk: do move a24 to=420,235
    ok e12: move a24 to=420,235
      now: a24 note "Standup agenda" · 400x65 at 420,235 · 10w · also x1 · 69% hidden by a26

[16 @19.39s] desk: do resize a26 to=400x65
    ok e13: resize a26 to=400x65
      now: a26 note "Blog draft" · 400x65 at 520,240 · 18w · offscreen-part · spills-parent

[17 @19.39s] desk: do move a26 to=420,310
    ok e14: move a26 to=420,310
      now: a26 note "Blog draft" · 400x65 at 420,310 · 18w

[18 @21.14s] desk: look f04
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside
      a20 note "Tide data format" · 400x65 at 420,10 · due 2026-09-17 · 16w
      a21 image "dock-photo.png" · 390x185 at 10,10
      a22 task "Order pier sensors" · 400x65 at 420,85 · due 2026-09-18 · 10w
      a23 note "Grocery list" · 400x65 at 420,160 · 4w
      a24 note "Standup agenda" · 400x65 at 420,235 · 10w · also x1
      a25 image "layout-sketch.png" · 390x185 at 10,205
      a26 note "Blog draft" · 400x65 at 420,310 · 18w

## reply
Arranged Scratch with images on the left and all text items on the right; verification shows no overlaps.

Hardest step was fitting five text items within the right side, so I resized them uniformly. The layout controls were clear.

## assessment
{
 "nothing_removed": true,
 "no_overlap": true,
 "images_left_of_text": true,
 "inside_scratch": true,
 "other_areas_untouched": true,
 "pass": true
}