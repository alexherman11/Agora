# r3-agenda-moo-1  task=agenda variant=moo
prompt: Add 'Review the text desk trial' as the last item of the standup agenda, and make sure the agenda shows only once on the desk, in the Meeting panel.

[1 @3.52s] desk: look
    f01 surface "desk" free · 1280x800 · 3 inside
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside  (open f02 to see inside)
      f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside  (open f03 to see inside)
      f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside  (open f04 to see inside)

[2 @5.8s] desk: look f03
    f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27
      a27 chat "Priya" · 320x160 at 300,200 · 14w

[3 @7.7s] desk: examine a18
    a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1
      a note (subject s10) on f03; text begins: 1. Yesterday's blockers
      also appears at a24 in f04
      where: screen 440,20 380x220 · in f03 (free) local 20,20 z1 · under a27 · 4% hidden
      verbs from note: due
      verbs from text: append retitle rewrite
      verbs from appearance: fold reveal dedupe
      verbs from thing: move resize raise lower remove
      (help <verb> explains one; do <verb> a18 ... uses it)

[4 @9.98s] desk: look f04
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w

[5 @11.92s] desk: help append
    append  (on: text; level 1)
      Add a line at the end of the text. Edits the subject: every appearance changes.
      args: line=<str>
      e.g. do append a18 line="4. Review"

[6 @13.92s] desk: read s10
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    ---

[7 @16.7s] desk: do append a18 line="4. Review the text desk trial"
    ok append a18 line='4. Review the text desk trial'  [e1]
      subject s10 changed; 2 appearance(s) now show the new content
      now: a18 note "Standup agenda" · 380x220 at 20,20 · 20w · also x1

[8 @18.55s] desk: examine a24
    !! since your last look: e2 edit s10 by sam
    a24 note "Standup agenda" · 320x180 at 300,200 · 20w · also x1 · 52% hidden by a25,a26
      a note (subject s10) on f04; text begins: 1. Yesterday's blockers
      also appears at a18 in f03
      where: screen 720,600 320x180 · in f04 (free) local 300,200 z5 · covers a20, covers a21, covers a23, under a25, under a26 · 52% hidden
      verbs from note: due
      verbs from text: append retitle rewrite
      verbs from appearance: fold reveal dedupe
      verbs from thing: move resize raise lower remove
      (help <verb> explains one; do <verb> a24 ... uses it)

[9 @21.25s] desk: do remove a24
    ok remove a24  [e3]
      appearance removed; the subject still exists

[10 @24.41s] desk: look f03
    f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside
      a18 note "Standup agenda" · 380x220 at 20,20 · 20w
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27
      a27 chat "Priya" · 320x160 at 300,200 · 14w

[11 @24.41s] desk: read s10
    s10 note "Standup agenda" · appears at a18
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    4. Review the text desk trial
    4. Budget check (Sam)
    ---

[12 @27.55s] desk: help rewrite
    rewrite  (on: text; level 1)
      Replace all the text. Write \n between lines. Read first; the desk refuses if it changed since.
      args: text=<str>
      e.g. do rewrite a18 text="one\ntwo"

[13 @30.31s] desk: do rewrite a18 text="1. Yesterday's blockers\n2. Sensor vendor decision\n3. Demo schedule\n4. Budget check (Sam)\n5. Review the text desk trial"
    ok rewrite a18 text="1. Yesterday's blockers\n2. Sensor vendor decision\n3. Demo schedule\n4. Budget check (Sam)\n5. Review the text desk trial"  [e4]
      subject s10 changed; 1 appearance(s) now show the new content
      now: a18 note "Standup agenda" · 380x220 at 20,20 · 20w

[14 @33.22s] desk: look f03
    f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside
      a18 note "Standup agenda" · 380x220 at 20,20 · 20w
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27
      a27 chat "Priya" · 320x160 at 300,200 · 14w

[15 @33.22s] desk: read s10
    s10 note "Standup agenda" · appears at a18
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    4. Budget check (Sam)
    5. Review the text desk trial
    ---

[16 @33.22s] desk: look f04
    f04 surface "Scratch" free · 840x400 at 420,400 · 6 inside
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21
      a21 image "dock-photo.png" · 500x340 at 20,20 · 29% hidden by a25
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w

## reply
Updated the standup agenda: “Review the text desk trial” is now its last item. The agenda appears only once, in the Meeting panel.

Hardest step: handling a concurrent agenda edit while keeping the requested item last. The desk’s change notice made that conflict clear.

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