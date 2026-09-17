# r1-tidy-outline  task=tidy variant=outline
prompt: The Scratch area is a pile. Arrange it so nothing overlaps: pictures on the left, text on the right.

[1 @4.69s] desk: look
    f01 surface "desk" free · 1280x800 · 3 inside
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside  (open f02 to see inside)
      f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside  (open f03 to see inside)
      f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside  (open f04 to see inside)

[2 @6.58s] desk: look f04 :3
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

[3 @17.17s] desk: do move a21 to=10,10
    ok e1: move a21 to=10,10
      now: a21 image "dock-photo.png" · 500x340 at 10,10 · 46% hidden by a24,a25

[4 @18.98s] desk: do resize a21 to=380x230
    ok e2: resize a21 to=380x230
      now: a21 image "dock-photo.png" · 380x230 at 10,10 · 12% hidden by a24,a25

[5 @21.84s] desk: do move a25 to=10,250
    ok e3: move a25 to=10,250
      now: a25 image "layout-sketch.png" · 360x160 at 10,250 · offscreen-part · spills-parent

[6 @23.52s] desk: do resize a25 to=380x140
    ok e4: resize a25 to=380x140
      now: a25 image "layout-sketch.png" · 380x140 at 10,250

[7 @26.95s] desk: do move a20 to=410,10
    ok e5: move a20 to=410,10
      now: a20 note "Tide data format" · 300x160 at 410,10 · due 2026-09-17 · 16w · 83% hidden by a22,a23

[8 @28.5s] desk: do resize a20 to=410x60
    ok e6: resize a20 to=410x60
      now: a20 note "Tide data format" · 410x60 at 410,10 · due 2026-09-17 · 16w · 55% hidden by a22,a23

[9 @30.02s] desk: do move a22 to=410,85
    ok e7: move a22 to=410,85
      now: a22 task "Order pier sensors" · 280x140 at 410,85 · due 2026-09-18 · 10w · 54% hidden by a23,a24

[10 @31.44s] desk: do resize a22 to=410x60
    ok e8: resize a22 to=410x60
      now: a22 task "Order pier sensors" · 410x60 at 410,85 · due 2026-09-18 · 10w · 58% hidden by a23

[11 @32.98s] desk: do move a23 to=410,160
    ok e9: move a23 to=410,160
      now: a23 note "Grocery list" · 240x150 at 410,160 · 4w · 89% hidden by a24,a26

[12 @34.94s] desk: do resize a23 to=410x60
    ok e10: resize a23 to=410x60
      now: a23 note "Grocery list" · 410x60 at 410,160 · 4w · 17% hidden by a24

[13 @36.77s] desk: do move a24 to=410,235
    ok e11: move a24 to=410,235
      now: a24 note "Standup agenda" · 320x180 at 410,235 · 10w · also x1 · 54% hidden by a26 · offscreen-part · spills-parent

[14 @38.31s] desk: do resize a24 to=410x60
    ok e12: resize a24 to=410x60
      now: a24 note "Standup agenda" · 410x60 at 410,235 · 10w · also x1 · 67% hidden by a26

[15 @39.78s] desk: do move a26 to=410,310
    ok e13: move a26 to=410,310
      now: a26 note "Blog draft" · 300x150 at 410,310 · 18w · offscreen-part · spills-parent

[16 @41.41s] desk: do resize a26 to=410x60
    ok e14: resize a26 to=410x60
      now: a26 note "Blog draft" · 410x60 at 410,310 · 18w

[17 @43.16s] desk: look f04 :3
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside
      a20 note "Tide data format" · 410x60 at 410,10 · due 2026-09-17 · 16w
      a21 image "dock-photo.png" · 380x230 at 10,10
      a22 task "Order pier sensors" · 410x60 at 410,85 · due 2026-09-18 · 10w
      a23 note "Grocery list" · 410x60 at 410,160 · 4w
      a24 note "Standup agenda" · 410x60 at 410,235 · 10w · also x1
      a25 image "layout-sketch.png" · 380x140 at 10,250
      a26 note "Blog draft" · 410x60 at 410,310 · 18w
      where: screen 420,400 840x400 · in f01 (free) local 420,400 z3 · clear
      verbs: move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>  resize to=<w>x<h>  raise (to front)  lower (to back)  remove (removes this appearance only; the subject survives)  tile as=column|row  (lay children out without overlap)  rename title=<str>  group title=<str> as=free|column|row  (new empty surface inside this one)

## reply
Arranged Scratch with images on the left and all text items on the right; verification shows no overlaps.

Hardest step was fitting both images and five text items within the fixed area, so I resized them. The layout tools were clear.

## assessment
{
 "nothing_removed": true,
 "no_overlap": true,
 "images_left_of_text": true,
 "inside_scratch": true,
 "other_areas_untouched": true,
 "pass": true
}