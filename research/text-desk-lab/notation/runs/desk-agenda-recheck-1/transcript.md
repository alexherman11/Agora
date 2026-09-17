# desk-agenda-recheck-1  task=agenda variant=lean
prompt: Add 'Review the text desk trial' as the last item of the standup agenda, and make sure the agenda shows only once on the desk, in the Meeting panel.

[1 @4.5s] desk: look
    f01 surface "desk" row · 1280x800 · 2 inside
      f02 surface "Harbor" column · 2 inside  (open f02 to see inside)
      f28 surface "Right" column · 2 inside  (open f28 to see inside)

[2 @6.0s] desk: look f02; look f28
    [1] look f02
    f02 surface "Harbor" column · 2 inside
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w
    
    [2] look f28
    f28 surface "Right" column · 2 inside
      f03 surface "Meeting" free · 3 inside  (open f03 to see inside)
      f04 surface "Scratch" free · 7 inside  (open f04 to see inside)

[3 @7.5s] desk: look f03
    f03 surface "Meeting" free · 3 inside
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27
      a27 chat "Priya" · 320x160 at 300,200 · 14w

[4 @9.28s] desk: examine a18
    a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: remove also:a18
      a note (subject s10) on f03:
        * 1. Yesterday's blockers
        * 2. Sensor vendor decision
        * 3. Demo schedule
      also appears at a24 in f04
      where: screen 449,36 380x220 · in f03 (free) local 20,20 z1 · under a27 · 4% hidden
      verbs: due · append retitle rewrite · fold comment link prop tag · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)

[5 @12.05s] desk: do append a18 text="4. Review the text desk trial"; do remove a24
    [1] do append a18 text="4. Review the text desk trial"
    ok append a18 text='4. Review the text desk trial'  [e1]
      subject s10 changed; 2 appearance(s) now show the new content
      now: a18 note "Standup agenda" · 380x220 at 20,20 · 20w · also x1
    
    [2] do remove a24
    !! since your last look: e2 edit s10 by sam
    ok remove a24  [e3]
      appearance removed; the subject still exists

[6 @13.94s] desk: look f03; look f04; read a18
    [1] look f03
    f03 surface "Meeting" free · 3 inside
      a18 note "Standup agenda" · 380x220 at 20,20 · 20w
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27
      a27 chat "Priya" · 320x160 at 300,200 · 14w
    
    [2] look f04
    f04 surface "Scratch" free · 6 inside
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21
      a21 image "dock-photo.png" · 500x340 at 20,20 · 29% hidden by a25
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w · spills-parent
    
    [3] read a18
    s10 note "Standup agenda" · appears at a18
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    4. Review the text desk trial
    4. Budget check (Sam)
    ---

[7 @16.77s] desk: help rewrite
    rewrite  (on: text; level 1)
      Replace all the text. Write \n between lines. Read first; the desk refuses if it changed since.
      args: text=<str>
      e.g. do rewrite a18 text="one\ntwo"

[8 @19.09s] desk: do rewrite a18 text="1. Yesterday's blockers\n2. Sensor vendor decision\n3. Demo schedule\n4. Budget check (Sam)\n5. Review the text desk trial"
    ok rewrite a18 text="1. Yesterday's blockers\n2. Sensor vendor decision\n3. Demo schedule\n4. Budget check (Sam)\n5. Review the text desk trial"  [e4]
      subject s10 changed; 1 appearance(s) now show the new content
      dropped 1 line(s): "4. Review the text desk trial" (added by jeff, e1)
      now: a18 note "Standup agenda" · 380x220 at 20,20 · 20w

[9 @20.92s] desk: look f03; read a18
    [1] look f03
    f03 surface "Meeting" free · 3 inside
      a18 note "Standup agenda" · 380x220 at 20,20 · 20w
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27
      a27 chat "Priya" · 320x160 at 300,200 · 14w
    
    [2] read a18
    s10 note "Standup agenda" · appears at a18
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    4. Budget check (Sam)
    5. Review the text desk trial
    ---

## reply
Updated the sole Standup agenda in the Meeting panel; “Review the text desk trial” is now last.

Hardest step: accommodating a concurrent agenda edit while keeping the requested item last. The duplicate-location indicator made finding and removing the extra appearance clear.

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