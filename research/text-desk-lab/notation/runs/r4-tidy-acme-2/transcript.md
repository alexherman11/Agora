# r4-tidy-acme-2  task=tidy variant=acme
prompt: The Scratch area is a pile. Arrange it so nothing overlaps: pictures on the left, text on the right.

[1 @4.42s] desk: look
    f01 surface "desk" free · 1280x800 · 3 inside
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside · try: sort gather  (open f02 to see inside)
      f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside · try: tidy split  (open f03 to see inside)
      f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside · try: tidy split  (open f04 to see inside)

[2 @8.31s] desk: look f04 :2
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside · try: tidy split
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: reveal
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25 · try: reveal
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · try: reveal
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · try: reveal dedupe
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w

[3 @10.89s] desk: help split
    split  (on: surface; level 3)
      Divide the children into two tiled groups side by side (left/right) or stacked (top/bottom) by a rule.
      args: by=kind|title|tag left=<value> [right=<value>] [as=row|column]
      e.g. do split f04 by=kind left=image

[4 @13.88s] desk: do split f04 by=kind left=image
    ok split f04 by=kind left=image  [e1..e10, 10 steps] → created f28 (left), f29 (right)
      f28 surface "Images" column · 408x384 · 2 inside · try: sort gather
        where: screen 428,408 408x384 · in f04 (row) local 8,8 z1 · clear
      now: f04 surface "Scratch" row · 840x400 at 420,400 · 2 inside · try: sort gather
      f28 surface "Images" column · 408x384 · 2 inside · try: sort gather
      f29 surface "Rest" column · 408x384 · 5 inside · try: sort gather

[5 @16.31s] desk: look f04 :3
    f04 surface "Scratch" row · 840x400 at 420,400 · 2 inside · try: sort gather
      f28 surface "Images" column · 408x384 · 2 inside · try: sort gather
      f29 surface "Rest" column · 408x384 · 5 inside · try: sort gather
      verbs: move resize raise lower remove tile untile rename group   (verbs f04 for argument forms)

[6 @19.38s] desk: look f28 :2
    f28 surface "Images" column · 408x384 · 2 inside · try: sort gather
      a21 image "dock-photo.png" · 392x180
      a25 image "layout-sketch.png" · 392x180

[7 @19.39s] desk: look f29 :2
    f29 surface "Rest" column · 408x384 · 5 inside · try: sort gather
      a20 note "Tide data format" · 392x67 · due 2026-09-17 · 16w
      a26 note "Blog draft" · 392x67 · 18w
      a24 note "Standup agenda" · 392x67 · 10w · also x1 · try: dedupe
      a23 note "Grocery list" · 392x67 · 4w
      a22 task "Order pier sensors" · 392x67 · due 2026-09-18 · 10w

## reply
Arranged Scratch with pictures tiled on the left and text/task items tiled on the right; nothing overlaps.

Hardest step was identifying the appropriate layout action. The `split by=kind left=image` affordance was clear and handled the arrangement directly.

## assessment
{
 "nothing_removed": true,
 "no_overlap": true,
 "images_left_of_text": true,
 "inside_scratch": true,
 "other_areas_untouched": true,
 "pass": true
}