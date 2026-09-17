# r3-tidy-moo-1  task=tidy variant=moo
prompt: The Scratch area is a pile. Arrange it so nothing overlaps: pictures on the left, text on the right.

[1 @4.73s] desk: look
    f01 surface "desk" free · 1280x800 · 3 inside
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside  (open f02 to see inside)
      f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside  (open f03 to see inside)
      f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside  (open f04 to see inside)

[2 @6.41s] desk: look f04 :3
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w
      verbs: move resize raise lower remove tile rename group   (verbs f04 for argument forms)

[3 @8.78s] desk: help tile
    tile  (on: surface; level 1)
      Lay the children out as a column or row, sharing the space, nothing overlapping.
      args: as=column|row
      e.g. do tile f04 as=row

[4 @10.72s] desk: examine f04
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside
      a free surface inside f01, holding 7 thing(s): a20, a21, a22, a23, a24, a25, a26
      where: screen 420,400 840x400 · in f01 (free) local 420,400 z3 · clear
      verbs from surface: tile rename group sort tidy split gather stack
      verbs from thing: move resize raise lower remove
      (help <verb> explains one; do <verb> f04 ... uses it)

[5 @12.86s] desk: help tidy
    tidy  (on: surface; level 2)
      Make nothing overlap: tile the surface as a column (or row) with the current order.
      args: [as=column|row]
      e.g. do tidy f04

[6 @16.09s] desk: help resize
    resize  (on: thing; level 1)
      Change width and height.
      args: to=<w>x<h>
      e.g. do resize a04 to=300x160

[7 @17.94s] desk: help move
    move  (on: thing; level 1)
      Put this somewhere else.
      args: into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>
      e.g. do move a04 into=f02

[8 @22.17s] desk: do resize a21 to=390x220
    ok resize a21 to=390x220  [e1]
      now: a21 image "dock-photo.png" · 390x220 at 20,20 · 13% hidden by a24,a25

[9 @24.11s] desk: do move a21 to=10,10
    ok move a21 to=10,10  [e2]
      now: a21 image "dock-photo.png" · 390x220 at 10,10 · 7% hidden by a24,a25

[10 @26.59s] desk: do resize a25 to=390x150
    ok resize a25 to=390x150  [e3]
      now: a25 image "layout-sketch.png" · 390x150 at 40,220

[11 @28.3s] desk: do move a25 to=10,240
    ok move a25 to=10,240  [e4]
      now: a25 image "layout-sketch.png" · 390x150 at 10,240

[12 @32.36s] desk: do resize a20 to=410x60
    ok resize a20 to=410x60  [e5]
      now: a20 note "Tide data format" · 410x60 at 60,60 · due 2026-09-17 · 16w · 82% hidden by a21

[13 @35.48s] desk: do move a20 to=420,10
    ok move a20 to=420,10  [e6]
      now: a20 note "Tide data format" · 410x60 at 420,10 · due 2026-09-17 · 16w · 55% hidden by a22,a23

[14 @37.73s] desk: do resize a22 to=410x60
    ok resize a22 to=410x60  [e7]
      now: a22 task "Order pier sensors" · 410x60 at 540,30 · due 2026-09-18 · 10w · 29% hidden by a23 · offscreen-part · spills-parent

[15 @39.45s] desk: do move a22 to=420,80
    ok move a22 to=420,80  [e8]
      now: a22 task "Order pier sensors" · 410x60 at 420,80 · due 2026-09-18 · 10w · 58% hidden by a23

[16 @41.59s] desk: do resize a23 to=410x60
    ok resize a23 to=410x60  [e9]
      now: a23 note "Grocery list" · 410x60 at 560,60 · 4w · offscreen-part · spills-parent

[17 @43.45s] desk: do move a23 to=420,150
    ok move a23 to=420,150  [e10]
      now: a23 note "Grocery list" · 410x60 at 420,150 · 4w · 8% hidden by a24

[18 @46.25s] desk: do resize a24 to=410x60
    ok resize a24 to=410x60  [e11]
      now: a24 note "Standup agenda" · 410x60 at 300,200 · 10w · also x1 · 23% hidden by a25,a26

[19 @48.0s] desk: do move a24 to=420,220
    ok move a24 to=420,220  [e12]
      now: a24 note "Standup agenda" · 410x60 at 420,220 · 10w · also x1 · 48% hidden by a26

[20 @50.44s] desk: do resize a26 to=410x60
    ok resize a26 to=410x60  [e13]
      now: a26 note "Blog draft" · 410x60 at 520,240 · 18w · offscreen-part · spills-parent

[21 @52.16s] desk: do move a26 to=420,290
    ok move a26 to=420,290  [e14]
      now: a26 note "Blog draft" · 410x60 at 420,290 · 18w

[22 @54.61s] desk: look f04 :3
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside
      a20 note "Tide data format" · 410x60 at 420,10 · due 2026-09-17 · 16w
      a21 image "dock-photo.png" · 390x220 at 10,10
      a22 task "Order pier sensors" · 410x60 at 420,80 · due 2026-09-18 · 10w
      a23 note "Grocery list" · 410x60 at 420,150 · 4w
      a24 note "Standup agenda" · 410x60 at 420,220 · 10w · also x1
      a25 image "layout-sketch.png" · 390x150 at 10,240
      a26 note "Blog draft" · 410x60 at 420,290 · 18w
      verbs: move resize raise lower remove tile rename group   (verbs f04 for argument forms)

## reply
Arranged Scratch with images on the left and text items on the right; nothing overlaps.

Hardest step was fitting seven items within the fixed area while keeping the requested grouping. The resize and move affordances were clear.

## assessment
{
 "nothing_removed": true,
 "no_overlap": true,
 "images_left_of_text": true,
 "inside_scratch": true,
 "other_areas_untouched": true,
 "pass": true
}