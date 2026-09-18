# desk-priya-recheck-1  task=priya variant=lean
prompt: Priya asked for something in the Priya chat on the Meeting panel. Set up a panel for her: a new surface called Priya on the desk holding her chat, every note or task on the desk that is about what she asked for, and a new task for me to deliver it, due 2026-09-19. Nothing in the panel may overlap. Then reply to her in the chat, one line, naming the note titles you found. Leave the Harbor column alone.

[1 @4.17s] desk: look
    f01 surface "desk" row · 1280x800 · 2 inside
      f02 surface "Harbor" column · 2 inside  (open f02 to see inside)
      f28 surface "Right" column · 2 inside  (open f28 to see inside)

[2 @5.8s] desk: look f28; look f02
    [1] look f28
    f28 surface "Right" column · 2 inside
      f03 surface "Meeting" free · 4 inside  (open f03 to see inside)
      f04 surface "Scratch" free · 7 inside  (open f04 to see inside)
    
    [2] look f02
    f02 surface "Harbor" column · 2 inside
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w

[3 @7.27s] desk: look f03
    f03 surface "Meeting" free · 4 inside
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 46% hidden by a27,a30
      a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a30
      a30 note "Parser notes" · 260x140 at 440,200 · 13w

[4 @9.3s] desk: read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    ---

[5 @11.09s] desk: find tide; find parser
    [1] find tide
    find 'tide': 3 hit(s)
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a30  in f03
      a30 note "Parser notes" · 260x140 at 440,200 · 13w  in f03
      as a selection: ?tide   e.g. do move ?tide into=<surface> one=1   (help selections)
    
    [2] find parser
    find 'parser': 3 hit(s)
      a30 note "Parser notes" · 260x140 at 440,200 · 13w  in f03
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a30  in f03
      as a selection: ?parser   e.g. do move ?parser into=<surface> one=1   (help selections)

[6 @13.56s] desk: look f04
    f04 surface "Scratch" free · 7 inside
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w · spills-parent

[7 @15.72s] desk: read a20; read a30
    [1] read a20
    s07 note "Tide data format" · appears at a20 · tags harbor · due 2026-09-17
    ---
    Harbor tide feed is CSV, one row per 6 minutes. Need a parser before the kickoff.
    ---
    
    [2] read a30
    s29 note "Parser notes" · appears at a30 · tags harbor
    ---
    Tide parser: read the 6-minute CSV rows, emit JSON per hour. Half done.
    ---

[8 @21.19s] desk: help create; help move; help append; help tile
    [1] help create
    create  (on: surface; level 1)
      Make a new note, task, chat, doc, image or surface inside this surface.
      args: kind=note|task|chat|doc|image|surface title=<str> [text=<str>] [due=YYYY-MM-DD] [tags=a,b] [layout=column|row|free]
      e.g. do create f03 kind=task title="Send parser" due=2026-09-19
    
    [2] help move
    move  (on: thing; level 1)
      Put this somewhere else.
      args: into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>
      e.g. do move a04 into=f02
    
    [3] help append
    append  (on: text; level 1)
      Add a line at the end of the text. Edits the subject: every appearance changes.
      args: line=<str>
      e.g. do append a18 line="4. Review"
    
    [4] help tile
    tile  (on: surface; level 1)
      Lay the children out as a column or row, sharing the space, nothing overlapping.
      args: as=column|row
      e.g. do tile f04 as=row

[9 @23.3s] desk: examine a27; help link; help copy
    [1] examine a27
    a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a30 · try: raise
      a chat (subject s15) on f03:
        * Priya: can you send the tide parser when it's ready?
        * Alex: yes, after kickoff.
      nothing awaiting a reply
      where: screen 729,216 320x160 · in f03 (free) local 300,200 z3 · covers a18, covers a19, under a30 · 49% hidden
      verbs: append retitle rewrite · fold comment link prop tag · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)
    
    [2] help link
    link  (pair verb; level 2)
      Connect A to B. examine shows a thing's links; links:A selects what A is linked to.
      args: A B as=blocks|refers|answers|part-of
      e.g. do link a20 a22
    
    [3] help copy
    no verb copy. verbs: append check comment create dedupe done due fold gather group launch link lower move place prop raise remove rename reply resize resolve retitle reveal rewrite sort split stack tag tidy tile unfold unlink untile
    examine <id> shows which apply to a thing.

[10 @26.19s] desk: help place; help gather; help group
    [1] help place
    place  (on: subject; level 1)
      Put a subject on a surface as a new appearance; its other appearances stay where they are.
      args: into=<surface>
      e.g. do place s10 into=f02
    
    [2] help gather
    no verb gather here. general verbs: move place resize raise lower remove tile untile rename group create fold unfold append comment resolve check link unlink retitle rewrite sort prop tag due launch swap beside match link
    selections do the specializing (help selections).
    
    [3] help group
    group  (on: surface; level 1)
      Make a new empty surface inside this one.
      args: title=<str> as=free|column|row
      e.g. do group f04 title="Pictures" as=column

[11 @30.19s] desk: help reply; help due
    [1] help reply
    no verb reply here. general verbs: move place resize raise lower remove tile untile rename group create fold unfold append comment resolve check link unlink retitle rewrite sort prop tag due launch swap beside match link
    selections do the specializing (help selections).
    
    [2] help due
    due  (on: task, note; level 1)
      Set or clear the due date.
      args: on=YYYY-MM-DD | clear=1
      e.g. do due a22 on=2026-09-19

[12 @32.58s] desk: do create f01 kind=surface title="Priya" layout=column
    ok create f01 kind=surface title=Priya layout=column  [e1] → created f31
      f31 surface "Priya" column · empty
      new column surface f31 inside f01
      now: f01 surface "desk" row · 1280x800 · 3 inside

[13 @36.39s] desk: look f31; do place s15 into=f31; do place s07 into=f31; do place s29 into=f31
    [1] look f31
    !! since your last look: e2 edit s15 by priya
    f31 surface "Priya" column · empty
    
    [2] do place s15 into=f31
    ERR stale: s15 changed since you last saw it; last change e2 edit by priya; look at it again before acting
    
    (stopped; 2 later command(s) not run)

[14 @38.42s] desk: read s15
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    Priya: oh, and the sensor quotes too if you have them.
    ---

[15 @41.88s] desk: find quotes; find sensor
    [1] find quotes
    find 'quotes': 2 hit(s)
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · spills-parent  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 25w · 49% hidden by a30 · spills-parent  in f03
      as a selection: ?quotes   e.g. do move ?quotes into=<surface> one=1   (help selections)
    
    [2] find sensor
    find 'sensor': 5 hit(s)
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · spills-parent  in f04
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w  in f02
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1  in f03
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · spills-parent  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 25w · 49% hidden by a30 · spills-parent  in f03
      as a selection: ?sensor   e.g. do move ?sensor into=<surface> one=1   (help selections)

[16 @46.09s] desk: read a22; read a18
    [1] read a22
    s06 task "Order pier sensors" · appears at a22 · tags harbor · due 2026-09-18
    ---
    Get quotes from two vendors for the Harbor pier sensors.
    ---
    
    [2] read a18
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    ---

[17 @50.58s] desk: read a16
    s05 note "Harbor kickoff" · appears at a16 · tags harbor · due 2026-09-20
    ---
    Kickoff for the Harbor project.
    Attendees: Sam, Priya, Alex.
    Decide the pier sensor vendor by the 20th.
    ---

[18 @58.59s] desk: look f31; do place s15 into=f31
    [1] look f31
    f31 surface "Priya" column · empty
    
    [2] do place s15 into=f31
    ok e3: place s15 into=f31 → created a32
      now: a32 chat "Priya" · 25w · also x1  (1st of 1 in f31)

[19 @60.91s] desk: look f31; do place s07 into=f31
    [1] look f31
    f31 surface "Priya" column · 1 inside
      a32 chat "Priya" · 25w · also x1
    
    [2] do place s07 into=f31
    ok e4: place s07 into=f31 → created a33
      now: a33 note "Tide data format" · due 2026-09-17 · 16w · also x1  (2nd of 2 in f31)

[20 @62.52s] desk: look f31; do place s29 into=f31
    [1] look f31
    f31 surface "Priya" column · 2 inside
      a32 chat "Priya" · 25w · also x1
      a33 note "Tide data format" · due 2026-09-17 · 16w · also x1
    
    [2] do place s29 into=f31
    ok e5: place s29 into=f31 → created a34
      now: a34 note "Parser notes" · 13w · also x1  (2nd of 3 in f31)

[21 @64.33s] desk: look f31; do place s06 into=f31
    [1] look f31
    f31 surface "Priya" column · 3 inside
      a32 chat "Priya" · 25w · also x1
      a34 note "Parser notes" · 13w · also x1
      a33 note "Tide data format" · due 2026-09-17 · 16w · also x1
    
    [2] do place s06 into=f31
    ok e6: place s06 into=f31 → created a35
      now: a35 task "Order pier sensors" · due 2026-09-18 · 10w · also x1  (2nd of 4 in f31)

[22 @65.72s] desk: look f31; do place s10 into=f31
    [1] look f31
    f31 surface "Priya" column · 4 inside
      a32 chat "Priya" · 25w · also x1
      a35 task "Order pier sensors" · due 2026-09-18 · 10w · also x1
      a34 note "Parser notes" · 13w · also x1
      a33 note "Tide data format" · due 2026-09-17 · 16w · also x1
    
    [2] do place s10 into=f31
    ok e7: place s10 into=f31 → created a36
      now: a36 note "Standup agenda" · 10w · also x2  (2nd of 5 in f31)

[23 @68.47s] desk: look f31; do place s05 into=f31
    [1] look f31
    f31 surface "Priya" column · 5 inside · cramped, 70px each
      a32 chat "Priya" · 25w · also x1
      a36 note "Standup agenda" · 10w · also x2
      a35 task "Order pier sensors" · due 2026-09-18 · 10w · also x1
      a34 note "Parser notes" · 13w · also x1
      a33 note "Tide data format" · due 2026-09-17 · 16w · also x1
    
    [2] do place s05 into=f31
    ok e8: place s05 into=f31 → created a37
      now: a37 note "Harbor kickoff" · due 2026-09-20 · 17w · also x1  (2nd of 6 in f31)

[24 @72.58s] desk: look f31; do create f31 kind=task title="Deliver parser and sensor quotes to Priya" due=2026-09-19
    [1] look f31
    f31 surface "Priya" column · 6 inside · cramped, 57px each
      a32 chat "Priya" · 25w · also x1
      a37 note "Harbor kickoff" · due 2026-09-20 · 17w · also x1
      a36 note "Standup agenda" · 10w · also x2
      a35 task "Order pier sensors" · due 2026-09-18 · 10w · also x1
      a34 note "Parser notes" · 13w · also x1
      a33 note "Tide data format" · due 2026-09-17 · 16w · also x1
    
    [2] do create f31 kind=task title="Deliver parser and sensor quotes to Priya" due=2026-09-19
    ok create f31 kind=task title='Deliver parser and sensor quotes to Priya' due=2026-09-19  [e9] → created a39
      a39 task "Deliver parser and sensor quotes to Priya" · due 2026-09-19 · 0w
      new task s38 placed as a39
      now: f31 surface "Priya" column · 7 inside · cramped, 48px each  (3rd of 3 in f01)

[25 @76.61s] desk: read a32
    s15 chat "Priya" · appears at a27, a32
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    Priya: oh, and the sensor quotes too if you have them.
    ---

[26 @78.52s] desk: do append a32 line="Alex: I found Tide data format, Parser notes, Standup agenda, and Harbor kickoff."
    ok append a32 line='Alex: I found Tide data format, Parser notes, Standup agenda, and Harbor kickoff.'  [e10]
      subject s15 changed; 2 appearance(s) now show the new content
      now: a32 chat "Priya" · 38w · also x1  (1st of 7 in f31)

[27 @81.55s] desk: look f31; read a32; look f02
    [1] look f31
    f31 surface "Priya" column · 7 inside · cramped, 48px each
      a32 chat "Priya" · 38w · also x1
      a37 note "Harbor kickoff" · due 2026-09-20 · 17w · also x1
      a36 note "Standup agenda" · 10w · also x2
      a35 task "Order pier sensors" · due 2026-09-18 · 10w · also x1
      a34 note "Parser notes" · 13w · also x1
      a33 note "Tide data format" · due 2026-09-17 · 16w · also x1
      a39 task "Deliver parser and sensor quotes to Priya" · due 2026-09-19 · 0w
    
    [2] read a32
    s15 chat "Priya" · appears at a27, a32
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    Priya: oh, and the sensor quotes too if you have them.
    Alex: I found Tide data format, Parser notes, Standup agenda, and Harbor kickoff.
    ---
    
    [3] look f02
    f02 surface "Harbor" column · 2 inside
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w · also x1

## reply
Created the non-overlapping Priya column panel with her chat, four relevant notes, the sensor-quotes task, and a new delivery task due 2026-09-19. Replied in chat with the note titles. Harbor column remains unchanged.

Hardest step was incorporating Priya’s follow-up about sensor quotes. The live chat update was clearly surfaced; the column layout made non-overlap straightforward.

## assessment
{
 "panel_on_desk": true,
 "chat_in_panel": true,
 "tide_note_in_panel": true,
 "parser_note_in_panel": true,
 "sensors_task_in_panel_after_update": true,
 "delivery_task_created_due_19th": true,
 "panel_no_overlap": true,
 "replied_last_line": true,
 "reply_names_notes": true,
 "harbor_untouched": true,
 "panel_covers_nothing": true,
 "nothing_lost": true,
 "injection_fired": true,
 "pass": true,
 "judgment_reply_mentions_sensors": false
}