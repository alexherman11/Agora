# r7-agenda-knife-1  task=agenda variant=knife
prompt: Add 'Review the text desk trial' as the last item of the standup agenda, and make sure the agenda shows only once on the desk, in the Meeting panel.

[1 @5.5s] desk: look
    f01 surface "desk" free · 1280x800 · 3 inside
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside · try: sort  (open f02 to see inside)
      f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside · try: tile group  (open f03 to see inside)
      f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside · try: tile group  (open f04 to see inside)

[2 @8.31s] desk: look f03
    f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside · try: tile group
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: remove also:
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27 · try: raise
      a27 chat "Priya" · 320x160 at 300,200 · 14w

[3 @11.16s] desk: read a18
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    ---

[4 @14.14s] desk: look a24
    a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · try: raise remove also:
        > 1. Yesterday's blockers

[5 @16.16s] desk: examine s10
    s10 note "Standup agenda" · 10w
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: remove also:  in f03 "Meeting"
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · try: raise remove also:  in f04 "Scratch"
      verbs: append line=<str>  (adds a line at the end; edits the subject, so every appearance changes)  retitle title=<str>  rewrite text=<str>  (replaces all the text; write \n between lines)  place into=<surface>

[6 @19.22s] desk: do append s10 line="4. Review the text desk trial"
    ok e1: append s10 line='4. Review the text desk trial'
      subject s10 changed; 2 appearance(s) now show the new content

[7 @21.42s] desk: look a24
    !! since your last look: e2 edit s10 by sam
    a24 note "Standup agenda" · 320x180 at 300,200 · 20w · also x1 · 52% hidden by a25,a26 · try: raise remove also:
        > 1. Yesterday's blockers

[8 @24.3s] desk: read s10
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    4. Review the text desk trial
    4. Budget check (Sam)
    ---

[9 @28.3s] desk: do rewrite s10 text="1. Yesterday's blockers\n2. Sensor vendor decision\n3. Demo schedule\n4. Budget check (Sam)\n5. Review the text desk trial"
    ok e3: rewrite s10 text="1. Yesterday's blockers\n2. Sensor vendor decision\n3. Demo schedule\n4. Budget check (Sam)\n5. Review the text desk trial"
      subject s10 changed; 2 appearance(s) now show the new content

[10 @30.58s] desk: look a24
    a24 note "Standup agenda" · 320x180 at 300,200 · 20w · also x1 · 52% hidden by a25,a26 · try: raise remove also:
        > 1. Yesterday's blockers

[11 @32.48s] desk: do remove a24
    ok remove a24  [e4]
      appearance removed; the subject still exists

[12 @35.09s] desk: look f03
    f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside · try: tile group
      a18 note "Standup agenda" · 380x220 at 20,20 · 20w
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27 · try: raise
      a27 chat "Priya" · 320x160 at 300,200 · 14w

[13 @38.48s] desk: read s10
    s10 note "Standup agenda" · appears at a18
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    4. Budget check (Sam)
    5. Review the text desk trial
    ---

## reply
Updated the Standup agenda; “Review the text desk trial” is now last. It appears only once, in the Meeting panel.

Hardest step: preserving Sam’s concurrent agenda update while keeping the requested item last. The duplicate-removal affordance was clear.

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