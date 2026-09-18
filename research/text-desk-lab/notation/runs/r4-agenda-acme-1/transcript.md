# r4-agenda-acme-1  task=agenda variant=acme
prompt: Add 'Review the text desk trial' as the last item of the standup agenda, and make sure the agenda shows only once on the desk, in the Meeting panel.

[1 @6.11s] desk: look
    f01 surface "desk" free · 1280x800 · 3 inside
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside · try: sort gather  (open f02 to see inside)
      f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside · try: tidy split  (open f03 to see inside)
      f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside · try: tidy split  (open f04 to see inside)

[2 @8.06s] desk: look f03
    f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside · try: tidy split
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: dedupe
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27 · try: reveal
      a27 chat "Priya" · 320x160 at 300,200 · 14w

[3 @10.61s] desk: examine a18
    a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: dedupe
      a note (subject s10) on f03; text begins: 1. Yesterday's blockers
      also appears at a24 in f04
      where: screen 440,20 380x220 · in f03 (free) local 20,20 z1 · under a27 · 4% hidden
      verbs from note: due
      verbs from text: append retitle rewrite
      verbs from appearance: fold reveal dedupe
      verbs from thing: move resize raise lower remove
      (help <verb> explains one; do <verb> a18 ... uses it)

[4 @12.98s] desk: help append
    append  (on: text; level 1)
      Add a line at the end of the text. Edits the subject: every appearance changes.
      args: line=<str>
      e.g. do append a18 line="4. Review"

[5 @15.38s] desk: look f04
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside · try: tidy split
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: reveal
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25 · try: reveal
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · try: reveal
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · try: reveal dedupe
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w

[6 @17.81s] desk: do append a18 line="Review the text desk trial"
    ok append a18 line='Review the text desk trial'  [e1]
      subject s10 changed; 2 appearance(s) now show the new content
      now: a18 note "Standup agenda" · 380x220 at 20,20 · 19w · also x1 · try: dedupe

[7 @20.39s] desk: look f04
    !! since your last look: e2 edit s10 by sam
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside · try: tidy split
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: reveal
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25 · try: reveal
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · try: reveal
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 19w · also x1 · 52% hidden by a25,a26 · try: reveal dedupe
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w

[8 @22.67s] desk: read a18
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    Review the text desk trial
    4. Budget check (Sam)
    ---

[9 @25.0s] desk: help rewrite
    rewrite  (on: text; level 1)
      Replace all the text. Write \n between lines. Read first; the desk refuses if it changed since.
      args: text=<str>
      e.g. do rewrite a18 text="one\ntwo"

[10 @28.17s] desk: do rewrite a18 text="1. Yesterday's blockers\n2. Sensor vendor decision\n3. Demo schedule\n4. Budget check (Sam)\nReview the text desk trial"
    ok rewrite a18 text="1. Yesterday's blockers\n2. Sensor vendor decision\n3. Demo schedule\n4. Budget check (Sam)\nReview the text desk trial"  [e3]
      subject s10 changed; 2 appearance(s) now show the new content
      now: a18 note "Standup agenda" · 380x220 at 20,20 · 19w · also x1 · try: dedupe

[11 @30.25s] desk: look f04
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside · try: tidy split
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: reveal
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25 · try: reveal
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · try: reveal
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 19w · also x1 · 52% hidden by a25,a26 · try: reveal dedupe
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w

[12 @32.03s] desk: do remove a24
    ok remove a24  [e4]
      appearance removed; the subject still exists

[13 @33.81s] desk: look f03
    f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside · try: tidy split
      a18 note "Standup agenda" · 380x220 at 20,20 · 19w
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27 · try: reveal
      a27 chat "Priya" · 320x160 at 300,200 · 14w

[14 @35.73s] desk: read a18
    s10 note "Standup agenda" · appears at a18
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    4. Budget check (Sam)
    Review the text desk trial
    ---

## reply
Updated the standup agenda; “Review the text desk trial” is now last. It appears only once, in the Meeting panel.

Hardest step: preserving Sam’s concurrent budget update while making the requested item last. The desk’s change notice made that clear.

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