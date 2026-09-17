# r2-tidy-relations  task=tidy variant=relations
prompt: The Scratch area is a pile. Arrange it so nothing overlaps: pictures on the left, text on the right.

[1 @4.11s] desk: look
    f01 surface "desk" free · 1280x800 · 3 inside
      f02 surface "Harbor" column · left · 2 inside  (open f02 to see inside)
      f03 surface "Meeting" free · top-mid · 3 inside  (open f03 to see inside)
      f04 surface "Scratch" free · bottom-mid · 7 inside  (open f04 to see inside)

[2 @5.61s] desk: open f04
    f04 surface "Scratch" free · bottom-mid · 7 inside
      a20 note "Tide data format" · bottom-mid · due 2026-09-17 · 16w · hidden by a21,a24
      a21 image "dock-photo.png" · bottom-mid · 50% hidden by a24,a25
      a22 task "Order pier sensors" · right · due 2026-09-18 · 10w · 67% hidden by a23
      a23 note "Grocery list" · bottom-right · 4w
      a24 note "Standup agenda" · bottom-right · 10w · also x1 · 52% hidden by a25,a26
      a25 image "layout-sketch.png" · bottom-mid
      a26 note "Blog draft" · bottom-right · 18w

[3 @7.28s] desk: look f04 :3
    f04 surface "Scratch" free · bottom-mid · 7 inside
      a20 note "Tide data format" · bottom-mid · due 2026-09-17 · 16w · hidden by a21,a24
      a21 image "dock-photo.png" · bottom-mid · 50% hidden by a24,a25
      a22 task "Order pier sensors" · right · due 2026-09-18 · 10w · 67% hidden by a23
      a23 note "Grocery list" · bottom-right · 4w
      a24 note "Standup agenda" · bottom-right · 10w · also x1 · 52% hidden by a25,a26
      a25 image "layout-sketch.png" · bottom-mid
      a26 note "Blog draft" · bottom-right · 18w
      verbs: move resize raise lower remove tile rename group   (verbs f04 for argument forms)

[4 @9.17s] desk: verbs f04
    f04 verbs:
      move to=<x>,<y> | by=<dx>,<dy> | into=<surface> | before=<node> | after=<node>
      resize to=<w>x<h>
      raise (to front)
      lower (to back)
      remove (removes this appearance only; the subject survives)
      tile as=column|row  (lay children out without overlap)
      rename title=<str>
      group title=<str> as=free|column|row  (new empty surface inside this one)

[5 @11.61s] desk: where f04
    f04: screen 420,400 840x400 · in f01 (free) local 420,400 z3 · clear

[6 @13.5s] desk: where a20
    a20: screen 480,460 300x160 · in f04 (free) local 60,60 z1 · under a21 fully, under a24 · 100% hidden

[7 @15.75s] desk: where a21
    a21: screen 440,420 500x340 · in f04 (free) local 20,20 z2 · covers a20 fully, under a24, under a25 · 50% hidden

[8 @15.77s] desk: where a22
    a22: screen 960,430 280x140 · in f04 (free) local 540,30 z3 · under a23 · 67% hidden

[9 @15.77s] desk: where a23
    a23: screen 980,460 240x150 · in f04 (free) local 560,60 z4 · covers a22, under a24 · 1% hidden

[10 @15.77s] desk: where a24
    a24: screen 720,600 320x180 · in f04 (free) local 300,200 z5 · covers a20, covers a21, covers a23, under a25, under a26 · 52% hidden

[11 @15.77s] desk: where a25
    a25: screen 460,620 360x160 · in f04 (free) local 40,220 z6 · covers a21, covers a24

[12 @15.77s] desk: where a26
    a26: screen 940,640 300x150 · in f04 (free) local 520,240 z7 · covers a24

[13 @29.56s] desk: do move a21 to=10,10
    ok e1: move a21 to=10,10
      now: a21 image "dock-photo.png" · bottom-mid · 46% hidden by a24,a25

[14 @32.28s] desk: look a21
    a21 image "dock-photo.png" · bottom-mid · 46% hidden by a24,a25

[15 @34.11s] desk: do resize a21 to=380x180
    ok e2: resize a21 to=380x180
      now: a21 image "dock-photo.png" · center

[16 @36.41s] desk: do move a25 to=10,210
    ok e3: move a25 to=10,210
      now: a25 image "layout-sketch.png" · bottom-mid

[17 @37.98s] desk: look a25
    a25 image "layout-sketch.png" · bottom-mid

[18 @39.47s] desk: do resize a25 to=380x180
    ok e4: resize a25 to=380x180
      now: a25 image "layout-sketch.png" · bottom-mid

[19 @41.45s] desk: do move a20 to=410,10
    ok e5: move a20 to=410,10
      now: a20 note "Tide data format" · right · due 2026-09-17 · 16w · 83% hidden by a22,a23

[20 @43.17s] desk: look a20
    a20 note "Tide data format" · right · due 2026-09-17 · 16w · 83% hidden by a22,a23
        > Harbor tide feed is CSV, one row per 6 minutes. Need a parser before the kickoff.

[21 @44.58s] desk: do resize a20 to=205x120
    ok e6: resize a20 to=205x120
      now: a20 note "Tide data format" · right · due 2026-09-17 · 16w · 46% hidden by a22,a23

[22 @46.08s] desk: do move a24 to=410,140
    ok e7: move a24 to=410,140
      now: a24 note "Standup agenda" · bottom-right · 10w · also x1 · 29% hidden by a26

[23 @47.34s] desk: look a24
    a24 note "Standup agenda" · bottom-right · 10w · also x1 · 29% hidden by a26
        > 1. Yesterday's blockers

[24 @48.92s] desk: do resize a24 to=205x120
    ok e8: resize a24 to=205x120
      now: a24 note "Standup agenda" · bottom-right · 10w · also x1 · 7% hidden by a26

[25 @50.86s] desk: do move a26 to=410,270
    ok e9: move a26 to=410,270
      now: a26 note "Blog draft" · bottom-right · 18w · offscreen-part · spills-parent

[26 @52.8s] desk: look a26
    a26 note "Blog draft" · bottom-right · 18w · offscreen-part · spills-parent
        > Why we moved the desk to text.

[27 @54.38s] desk: do resize a26 to=205x120
    ok e10: resize a26 to=205x120
      now: a26 note "Blog draft" · bottom-right · 18w

[28 @56.48s] desk: do move a22 to=625,10
    ok e11: move a22 to=625,10
      now: a22 task "Order pier sensors" · right · due 2026-09-18 · 10w · 40% hidden by a23 · offscreen-part · spills-parent

[29 @57.77s] desk: look a22
    a22 task "Order pier sensors" · right · due 2026-09-18 · 10w · 40% hidden by a23 · offscreen-part · spills-parent
        > Get quotes from two vendors for the Harbor pier sensors.

[30 @59.28s] desk: do resize a22 to=205x120
    ok e12: resize a22 to=205x120
      now: a22 task "Order pier sensors" · right · due 2026-09-18 · 10w · 49% hidden by a23

[31 @60.64s] desk: do move a23 to=625,140
    ok e13: move a23 to=625,140
      now: a23 note "Grocery list" · bottom-right · 4w · offscreen-part · spills-parent

[32 @62.11s] desk: look a23
    a23 note "Grocery list" · bottom-right · 4w · offscreen-part · spills-parent
        > eggs

[33 @63.66s] desk: do resize a23 to=205x120
    ok e14: resize a23 to=205x120
      now: a23 note "Grocery list" · bottom-right · 4w

[34 @66.25s] desk: look f04 :3
    f04 surface "Scratch" free · bottom-mid · 7 inside
      a20 note "Tide data format" · right · due 2026-09-17 · 16w
      a21 image "dock-photo.png" · center
      a22 task "Order pier sensors" · right · due 2026-09-18 · 10w
      a23 note "Grocery list" · bottom-right · 4w
      a24 note "Standup agenda" · bottom-right · 10w · also x1
      a25 image "layout-sketch.png" · bottom-mid
      a26 note "Blog draft" · bottom-right · 18w
      verbs: move resize raise lower remove tile rename group   (verbs f04 for argument forms)

## reply
Arranged Scratch with both pictures on the left and all text items on the right; verified no overlap indicators remain.

Hardest step was fitting all items within the compact Scratch area while preserving clear left/right separation. The resize affordance was useful; its effect on content readability was not previewed.

## assessment
{
 "nothing_removed": true,
 "no_overlap": true,
 "images_left_of_text": true,
 "inside_scratch": true,
 "other_areas_untouched": true,
 "pass": true
}