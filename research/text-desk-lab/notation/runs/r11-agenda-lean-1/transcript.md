# r11-agenda-lean-1  task=agenda variant=lean
prompt: Add 'Review the text desk trial' as the last item of the standup agenda, and make sure the agenda shows only once on the desk, in the Meeting panel.

[1 @4.5s] desk: look
    f01 surface "desk" row · 1280x800 · 2 inside
      f02 surface "Harbor" column · 2 inside  (open f02 to see inside)
      f28 surface "Right" column · 2 inside  (open f28 to see inside)

[2 @6.75s] desk: look f02; look f28
    [1] look f02
    f02 surface "Harbor" column · 2 inside
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w
    
    [2] look f28
    f28 surface "Right" column · 2 inside
      f03 surface "Meeting" free · 3 inside  (open f03 to see inside)
      f04 surface "Scratch" free · 7 inside  (open f04 to see inside)

[3 @8.64s] desk: look f03
    f03 surface "Meeting" free · 3 inside
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27
      a27 chat "Priya" · 320x160 at 300,200 · 14w

[4 @10.78s] desk: read a18; where a18
    [1] read a18
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    ---
    
    [2] where a18
    a18: screen 449,36 380x220 · in f03 (free) local 20,20 z1 · under a27 · 4% hidden

[5 @13.83s] desk: look a24; examine a18
    [1] look a24
    a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26
        > 1. Yesterday's blockers
    
    [2] examine a18
    a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: remove also:a18
      a note (subject s10) on f03:
        * 1. Yesterday's blockers
        * 2. Sensor vendor decision
        * 3. Demo schedule
      also appears at a24 in f04
      where: screen 449,36 380x220 · in f03 (free) local 20,20 z1 · under a27 · 4% hidden
      verbs: append retitle rewrite · fold comment link · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)

[6 @15.67s] desk: help append; examine a24
    [1] help append
    append  (on: text; level 1)
      Add a line at the end of the text. Edits the subject: every appearance changes.
      args: line=<str>
      e.g. do append a18 line="4. Review"
    
    [2] examine a24
    a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · try: raise remove also:a24
      a note (subject s10) on f04:
        * 1. Yesterday's blockers
        * 2. Sensor vendor decision
        * 3. Demo schedule
      also appears at a18 in f03
      where: screen 729,594 320x180 · in f04 (free) local 300,200 z5 · covers a20, covers a21, covers a23, under a25, under a26 · 52% hidden
      verbs: append retitle rewrite · fold comment link · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)

[7 @18.52s] desk: do append a18 line="4. Review the text desk trial"
    ok append a18 line='4. Review the text desk trial'  [e1]
      subject s10 changed; 2 appearance(s) now show the new content
      now: a18 note "Standup agenda" · 380x220 at 20,20 · 20w · also x1

[8 @21.66s] desk: look a24; help remove
    [1] look a24
    !! since your last look: e2 edit s10 by sam
    a24 note "Standup agenda" · 320x180 at 300,200 · 20w · also x1 · 52% hidden by a25,a26
        > 1. Yesterday's blockers
    
    [2] help remove
    remove  (on: thing; level 1)
      Take this appearance off the desk. The subject survives and any other appearance stays.
      e.g. do remove a24

[9 @24.08s] desk: read a24
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    4. Review the text desk trial
    4. Budget check (Sam)
    ---

[10 @28.19s] desk: help rewrite; examine a18
    [1] help rewrite
    rewrite  (on: text; level 1)
      Replace all the text. Write \n between lines. Read first; the desk refuses if it changed since.
      args: text=<str>
      e.g. do rewrite a18 text="one\ntwo"
    
    [2] examine a18
    a18 note "Standup agenda" · 380x220 at 20,20 · 20w · also x1 · try: remove also:a18
      a note (subject s10) on f03:
        * 1. Yesterday's blockers
        * 2. Sensor vendor decision
        * 3. Demo schedule
        * 4. Review the text desk trial
        * … 1 more line(s) folded; read a18 for all
      also appears at a24 in f04
      where: screen 449,36 380x220 · in f03 (free) local 20,20 z1 · under a27 · 4% hidden
      verbs: append retitle rewrite · fold comment link · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)

[11 @32.08s] desk: do rewrite a18 text="1. Yesterday's blockers\n2. Sensor vendor decision\n3. Demo schedule\n4. Budget check (Sam)\n5. Review the text desk trial"
    ok rewrite a18 text="1. Yesterday's blockers\n2. Sensor vendor decision\n3. Demo schedule\n4. Budget check (Sam)\n5. Review the text desk trial"  [e3]
      subject s10 changed; 2 appearance(s) now show the new content
      dropped 1 line(s): "4. Review the text desk trial" (added by jeff, e1)
      now: a18 note "Standup agenda" · 380x220 at 20,20 · 20w · also x1

[12 @33.69s] desk: look a24
    a24 note "Standup agenda" · 320x180 at 300,200 · 20w · also x1 · 52% hidden by a25,a26
        > 1. Yesterday's blockers

[13 @35.22s] desk: do remove a24
    ok remove a24  [e4]
      appearance removed; the subject still exists

[14 @37.52s] desk: look f03; read a18; look f04
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
    
    [3] look f04
    f04 surface "Scratch" free · 6 inside
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21
      a21 image "dock-photo.png" · 500x340 at 20,20 · 29% hidden by a25
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w · spills-parent

## reply
Added “Review the text desk trial” as the final agenda item. The agenda now appears only once, in the Meeting panel.

Hardest step: preserving Sam’s concurrent agenda addition while keeping the requested item last. The desk’s change notice made that conflict visible.

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