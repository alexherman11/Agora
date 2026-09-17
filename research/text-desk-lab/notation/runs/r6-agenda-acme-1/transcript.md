# r6-agenda-acme-1  task=agenda variant=acme
prompt: Add 'Review the text desk trial' as the last item of the standup agenda, and make sure the agenda shows only once on the desk, in the Meeting panel.

[1 @4.81s] desk: look
    f01 surface "desk" free · 1280x800 · 3 inside
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside · try: sort gather  (open f02 to see inside)
      f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside · try: tidy split  (open f03 to see inside)
      f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside · try: tidy split  (open f04 to see inside)

[2 @6.25s] desk: look f03 :2
    f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside · try: tidy split
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: dedupe
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27 · try: reveal
      a27 chat "Priya" · 320x160 at 300,200 · 14w

[3 @8.89s] desk: examine a18
    a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: dedupe
      a note (subject s10) on f03; text begins: 1. Yesterday's blockers
      also appears at a24 in f04
      where: screen 440,20 380x220 · in f03 (free) local 20,20 z1 · under a27 · 4% hidden
      verbs from note: due(on=YYYY-MM-DD | clear=1)
      verbs from text: append(line=<str>)  retitle(title=<str>)  rewrite(text=<str>)
      verbs from appearance: fold  reveal  dedupe
      verbs from thing: move(into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>)  resize(to=<w>x<h>)  raise  lower  remove
        due: Set or clear the due date.
        reveal: Make this fully visible: bring it to the front (free surface) and nudge it inside its parent.
        dedupe: Keep this appearance and remove every other appearance of the same subject.
      (help <verb> [<verb> ...] explains; do <verb> a18 ... uses one)

[4 @12.88s] desk: do append a18 line='Review the text desk trial'
    ok append a18 line='Review the text desk trial'  [e1]
      subject s10 changed; 2 appearance(s) now show the new content
      now: a18 note "Standup agenda" · 380x220 at 20,20 · 19w · also x1 · try: dedupe

[5 @15.34s] desk: look a18
    !! since your last look: e2 edit s10 by sam
    a18 note "Standup agenda" · 380x220 at 20,20 · 19w · also x1 · try: dedupe
        > 1. Yesterday's blockers

[6 @17.03s] desk: read a18
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    Review the text desk trial
    4. Budget check (Sam)
    ---

[7 @22.08s] desk: do rewrite a18 text='1. Yesterday\'s blockers
2. Sensor vendor decision
3. Demo schedule
4. Budget check (Sam)
Review the text desk trial'
    ERR could not parse: No closing quotation

[8 @25.5s] desk: help rewrite
    rewrite  (on: text; level 1)
      Replace all the text. Write \n between lines. Read first; the desk refuses if it changed since.
      args: text=<str>
      e.g. do rewrite a18 text="one\ntwo"

[9 @29.76s] desk: do rewrite a18 text="1. Yesterday's blockers\n2. Sensor vendor decision\n3. Demo schedule\n4. Budget check (Sam)\nReview the text desk trial"
    ok rewrite a18 text="1. Yesterday's blockers\n2. Sensor vendor decision\n3. Demo schedule\n4. Budget check (Sam)\nReview the text desk trial"  [e3]
      subject s10 changed; 2 appearance(s) now show the new content
      now: a18 note "Standup agenda" · 380x220 at 20,20 · 19w · also x1 · try: dedupe

[10 @33.62s] desk: look a18
    a18 note "Standup agenda" · 380x220 at 20,20 · 19w · also x1 · try: dedupe
        > 1. Yesterday's blockers

[11 @34.98s] desk: do dedupe a18
    ok dedupe a18  [e4]
      removed a24; a18 is now the only appearance
      now: a18 note "Standup agenda" · 380x220 at 20,20 · 19w

[12 @38.41s] desk: look f03 :2
    f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside · try: tidy split
      a18 note "Standup agenda" · 380x220 at 20,20 · 19w
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27 · try: reveal
      a27 chat "Priya" · 320x160 at 300,200 · 14w

[13 @41.08s] desk: read a18
    s10 note "Standup agenda" · appears at a18
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    4. Budget check (Sam)
    Review the text desk trial
    ---

## reply
Added “Review the text desk trial” as the final agenda item and removed the duplicate appearance. The agenda now appears only in the Meeting panel.

Hardest step: a concurrent edit placed another item after the new one, so I reordered the agenda. The desk’s change warning made that clear.

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