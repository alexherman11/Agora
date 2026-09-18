# r3-tidy-moo-2  task=tidy variant=moo
prompt: The Scratch area is a pile. Arrange it so nothing overlaps: pictures on the left, text on the right.

[1 @5.98s] desk: look
    f01 surface "desk" free · 1280x800 · 3 inside
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside  (open f02 to see inside)
      f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside  (open f03 to see inside)
      f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside  (open f04 to see inside)

[2 @9.48s] desk: look f04 :2
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w

[3 @14.83s] desk: examine f04
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside
      a free surface inside f01, holding 7 thing(s): a20, a21, a22, a23, a24, a25, a26
      where: screen 420,400 840x400 · in f01 (free) local 420,400 z3 · clear
      verbs from surface: tile rename group sort tidy split gather stack
      verbs from thing: move resize raise lower remove
      (help <verb> explains one; do <verb> f04 ... uses it)

[4 @17.89s] desk: help tidy
    tidy  (on: surface; level 2)
      Make nothing overlap: tile the surface as a column (or row) with the current order.
      args: [as=column|row]
      e.g. do tidy f04

[5 @21.45s] desk: help tile
    tile  (on: surface; level 1)
      Lay the children out as a column or row, sharing the space, nothing overlapping.
      args: as=column|row
      e.g. do tile f04 as=row

[6 @25.03s] desk: help split
    split  (on: surface; level 3)
      Divide the children into two tiled groups side by side (left/right) or stacked (top/bottom) by a rule.
      args: by=kind|title|tag left=<value> [right=<value>] [as=row|column]
      e.g. do split f04 by=kind left=image

[7 @27.73s] desk: do split f04 by=kind left=image
    ok split f04 by=kind left=image  [e1..e10, 10 steps] → created f28 (left), f29 (right)
      f28 surface "Images" column · 408x384 · 2 inside
        where: screen 428,408 408x384 · in f04 (row) local 8,8 z1 · clear
      now: f04 surface "Scratch" row · 840x400 at 420,400 · 2 inside
      f28 surface "Images" column · 408x384 · 2 inside
      f29 surface "Rest" column · 408x384 · 5 inside

[8 @30.23s] desk: look f04 :3
    f04 surface "Scratch" row · 840x400 at 420,400 · 2 inside
      f28 surface "Images" column · 408x384 · 2 inside
      f29 surface "Rest" column · 408x384 · 5 inside
      verbs: move resize raise lower remove tile untile rename group   (verbs f04 for argument forms)

[9 @33.34s] desk: look f28 :2
    f28 surface "Images" column · 408x384 · 2 inside
      a21 image "dock-photo.png" · 392x180
      a25 image "layout-sketch.png" · 392x180

[10 @35.38s] desk: look f29 :2
    f29 surface "Rest" column · 408x384 · 5 inside
      a20 note "Tide data format" · 392x67 · due 2026-09-17 · 16w
      a26 note "Blog draft" · 392x67 · 18w
      a24 note "Standup agenda" · 392x67 · 10w · also x1
      a23 note "Grocery list" · 392x67 · 4w
      a22 task "Order pier sensors" · 392x67 · due 2026-09-18 · 10w

## reply
Arranged Scratch with images tiled on the left and all text items tiled on the right; no overlaps remain.

Hardest step was fitting the mixed-size pile cleanly within the fixed area. The split-by-kind affordance was clear and handled the layout directly.

## assessment
{
 "nothing_removed": true,
 "no_overlap": true,
 "images_left_of_text": true,
 "inside_scratch": true,
 "other_areas_untouched": true,
 "pass": true
}