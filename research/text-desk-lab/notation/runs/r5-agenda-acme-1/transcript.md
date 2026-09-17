# r5-agenda-acme-1  task=agenda variant=acme
prompt: Add 'Review the text desk trial' as the last item of the standup agenda, and make sure the agenda shows only once on the desk, in the Meeting panel.

[1 @3.98s] desk: look
    f01 surface "desk" free · 1280x800 · 3 inside
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside · try: sort gather  (open f02 to see inside)
      f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside · try: tidy split  (open f03 to see inside)
      f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside · try: tidy split  (open f04 to see inside)

[2 @5.91s] desk: look f03 :2
    f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside · try: tidy split
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: dedupe
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27 · try: reveal
      a27 chat "Priya" · 320x160 at 300,200 · 14w

[3 @7.59s] desk: read a18
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    ---

[4 @9.8s] desk: look f04 :2
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside · try: tidy split
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: reveal
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25 · try: reveal
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · try: reveal
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · try: reveal dedupe
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w

[5 @11.83s] desk: examine a18
    a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: dedupe
      a note (subject s10) on f03; text begins: 1. Yesterday's blockers
      also appears at a24 in f04
      where: screen 440,20 380x220 · in f03 (free) local 20,20 z1 · under a27 · 4% hidden
      verbs from note: due
      verbs from text: append retitle rewrite
      verbs from appearance: fold reveal dedupe
      verbs from thing: move resize raise lower remove
        due: Set or clear the due date.  (on=YYYY-MM-DD | clear=1)
        reveal: Make this fully visible: bring it to the front (free surface) and nudge it inside its parent.
        dedupe: Keep this appearance and remove every other appearance of the same subject.
      (help <verb> explains one; do <verb> a18 ... uses it)

[6 @13.62s] desk: help append
    append  (on: text; level 1)
      Add a line at the end of the text. Edits the subject: every appearance changes.
      args: line=<str>
      e.g. do append a18 line="4. Review"

[7 @16.27s] desk: do append a18 line="4. Review the text desk trial"
    ok append a18 line='4. Review the text desk trial'  [e1]
      subject s10 changed; 2 appearance(s) now show the new content
      now: a18 note "Standup agenda" · 380x220 at 20,20 · 20w · also x1 · try: dedupe

[8 @18.5s] desk: look f03 :2
    !! since your last look: e2 edit s10 by sam
    f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside · try: tidy split
      a18 note "Standup agenda" · 380x220 at 20,20 · 20w · also x1 · try: dedupe
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27 · try: reveal
      a27 chat "Priya" · 320x160 at 300,200 · 14w

[9 @20.3s] desk: read a18
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    4. Review the text desk trial
    4. Budget check (Sam)
    ---

[10 @22.84s] desk: help rewrite
    rewrite  (on: text; level 1)
      Replace all the text. Write \n between lines. Read first; the desk refuses if it changed since.
      args: text=<str>
      e.g. do rewrite a18 text="one\ntwo"

[11 @26.19s] desk: do rewrite a18 text="1. Yesterday's blockers\n2. Sensor vendor decision\n3. Demo schedule\n4. Budget check (Sam)\n5. Review the text desk trial"
    ok rewrite a18 text="1. Yesterday's blockers\n2. Sensor vendor decision\n3. Demo schedule\n4. Budget check (Sam)\n5. Review the text desk trial"  [e3]
      subject s10 changed; 2 appearance(s) now show the new content
      now: a18 note "Standup agenda" · 380x220 at 20,20 · 20w · also x1 · try: dedupe

[12 @28.27s] desk: look f03 :2
    f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside · try: tidy split
      a18 note "Standup agenda" · 380x220 at 20,20 · 20w · also x1 · try: dedupe
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27 · try: reveal
      a27 chat "Priya" · 320x160 at 300,200 · 14w

[13 @29.98s] desk: do dedupe a18
    ok dedupe a18  [e4]
      removed a24; a18 is now the only appearance
      now: a18 note "Standup agenda" · 380x220 at 20,20 · 20w

[14 @32.53s] desk: look f03 :2
    f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside · try: tidy split
      a18 note "Standup agenda" · 380x220 at 20,20 · 20w
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27 · try: reveal
      a27 chat "Priya" · 320x160 at 300,200 · 14w

[15 @34.69s] desk: read a18
    s10 note "Standup agenda" · appears at a18
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    4. Budget check (Sam)
    5. Review the text desk trial
    ---

## reply
Done. The agenda appears only in the Meeting panel, and “Review the text desk trial” is its final item.

Hardest step: a concurrent edit added Sam’s budget item, so I preserved it and reordered the agenda. The dedupe affordance clearly kept the Meeting appearance.

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