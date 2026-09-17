# r11-priya-lean-1  task=priya variant=lean
prompt: Priya asked for something in the Priya chat on the Meeting panel. Set up a panel for her: a new surface called Priya on the desk holding her chat, every note or task on the desk that is about what she asked for, and a new task for me to deliver it, due 2026-09-19. Nothing in the panel may overlap. Then reply to her in the chat, one line, naming the note titles you found. Leave the Harbor column alone.

[1 @4.92s] desk: look
    f01 surface "desk" row · 1280x800 · 2 inside
      f02 surface "Harbor" column · 2 inside  (open f02 to see inside)
      f28 surface "Right" column · 2 inside  (open f28 to see inside)

[2 @7.59s] desk: look f28
    f28 surface "Right" column · 2 inside
      f03 surface "Meeting" free · 4 inside  (open f03 to see inside)
      f04 surface "Scratch" free · 7 inside  (open f04 to see inside)

[3 @9.48s] desk: look f03
    f03 surface "Meeting" free · 4 inside
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 46% hidden by a27,a30
      a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a30
      a30 note "Parser notes" · 260x140 at 440,200 · 13w

[4 @11.31s] desk: read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    ---

[5 @14.06s] desk: look f02; look f04
    [1] look f02
    f02 surface "Harbor" column · 2 inside
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w
    
    [2] look f04
    f04 surface "Scratch" free · 7 inside
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w · spills-parent

[6 @16.27s] desk: find tide parser
    find 'tide parser': 3 hit(s)
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a30  in f03
      a30 note "Parser notes" · 260x140 at 440,200 · 13w  in f03
      as a selection: ?tide+parser   e.g. do move ?tide+parser into=<surface> one=1   (help selections)

[7 @18.61s] desk: read a20; read a30
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

[8 @22.45s] desk: examine f01; help create; help move
    [1] examine f01
    f01 surface "desk" row · 1280x800 · 2 inside · try: sort
      a row surface (the desk itself), holding 2 thing(s): f02, f28
      where: screen 0,0 1280x800 · in - (-) · clear
      verbs: tile untile rename group create sort   (help <verb> for args; the target may be a selection: help selections)
    
    [2] help create
    create  (on: surface; level 1)
      Make a new note, task or chat and place it on this surface.
      args: kind=note|task|chat title=<str> [text=<str>] [due=YYYY-MM-DD] [tags=a,b]
      e.g. do create f03 kind=task title="Send parser" due=2026-09-19
    
    [3] help move
    move  (on: thing; level 1)
      Put this somewhere else.
      args: into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>
      e.g. do move a04 into=f02

[9 @24.39s] desk: help group; help tile; help link
    [1] help group
    group  (on: surface; level 1)
      Make a new empty surface inside this one.
      args: title=<str> as=free|column|row
      e.g. do group f04 title="Pictures" as=column
    
    [2] help tile
    tile  (on: surface; level 1)
      Lay the children out as a column or row, sharing the space, nothing overlapping.
      args: as=column|row
      e.g. do tile f04 as=row
    
    [3] help link
    link  (pair verb; level 2)
      Connect A to B. examine shows a thing's links; links:A selects what A is linked to.
      args: A B as=blocks|refers|answers|part-of
      e.g. do link a20 a22

[10 @27.56s] desk: examine a27; help append; help rewrite
    [1] examine a27
    a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a30 · try: raise
      a chat (subject s15) on f03:
        * Priya: can you send the tide parser when it's ready?
        * Alex: yes, after kickoff.
      nothing awaiting a reply
      where: screen 729,216 320x160 · in f03 (free) local 300,200 z3 · covers a18, covers a19, under a30 · 49% hidden
      verbs: append retitle rewrite · fold comment link · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)
    
    [2] help append
    append  (on: text; level 1)
      Add a line at the end of the text. Edits the subject: every appearance changes.
      args: line=<str>
      e.g. do append a18 line="4. Review"
    
    [3] help rewrite
    rewrite  (on: text; level 1)
      Replace all the text. Write \n between lines. Read first; the desk refuses if it changed since.
      args: text=<str>
      e.g. do rewrite a18 text="one\ntwo"

[11 @31.45s] desk: help copy; help clone; help appear
    [1] help copy
    no verb copy. verbs: append check comment create dedupe done due fold gather group link lower move raise remove rename reply resize resolve retitle reveal rewrite sort split stack tidy tile unfold unlink untile
    examine <id> shows which apply to a thing.
    
    [2] help clone
    no verb clone. verbs: append check comment create dedupe done due fold gather group link lower move raise remove rename reply resize resolve retitle reveal rewrite sort split stack tidy tile unfold unlink untile
    examine <id> shows which apply to a thing.
    
    [3] help appear
    no verb appear. verbs: append check comment create dedupe done due fold gather group link lower move raise remove rename reply resize resolve retitle reveal rewrite sort split stack tidy tile unfold unlink untile
    examine <id> shows which apply to a thing.

[12 @33.44s] desk: help gather; help split; help stack
    [1] help gather
    no verb gather here. general verbs: move resize raise lower remove tile untile rename group create fold unfold append comment resolve check link unlink retitle rewrite sort swap beside match link
    selections do the specializing (help selections).
    
    [2] help split
    no verb split here. general verbs: move resize raise lower remove tile untile rename group create fold unfold append comment resolve check link unlink retitle rewrite sort swap beside match link
    selections do the specializing (help selections).
    
    [3] help stack
    no verb stack here. general verbs: move resize raise lower remove tile untile rename group create fold unfold append comment resolve check link unlink retitle rewrite sort swap beside match link
    selections do the specializing (help selections).

[13 @37.0s] desk: do group f01 title="Priya" as=column
    ok group f01 title=Priya as=column  [e1] → created f31
      f31 surface "Priya" column · empty
        where: screen 849,8 421x784 · in f01 (row) local 849,8 z5 · clear
      now: f01 surface "desk" row · 1280x800 · 3 inside

[14 @42.22s] desk: do move a27 into=f31; do move a20 into=f31; do move a30 into=f31; do create f31 kind=task title="Deliver tide parser to Priya" due=2026-09-19
    [1] do move a27 into=f31
    ERR !! since your last look: e2 edit s15 by priya
    stale: a27 changed since you last saw it; look at it again before acting
    
    (stopped; 3 later command(s) not run)

[15 @44.75s] desk: read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    Priya: oh, and the sensor quotes too if you have them.
    ---

[16 @47.19s] desk: find sensor quotes; find quotes; find sensors
    [1] find sensor quotes
    find 'sensor quotes': 2 hit(s)
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · spills-parent  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 25w · 49% hidden by a30 · spills-parent  in f03
      as a selection: ?sensor+quotes   e.g. do move ?sensor+quotes into=<surface> one=1   (help selections)
    
    [2] find quotes
    find 'quotes': 2 hit(s)
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · spills-parent  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 25w · 49% hidden by a30 · spills-parent  in f03
      as a selection: ?quotes   e.g. do move ?quotes into=<surface> one=1   (help selections)
    
    [3] find sensors
    find 'sensors': 1 hit(s)
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · spills-parent  in f04
      as a selection: ?sensors   e.g. do move ?sensors into=<surface> one=1   (help selections)

[17 @49.3s] desk: read a22; help reply
    [1] read a22
    s06 task "Order pier sensors" · appears at a22 · tags harbor · due 2026-09-18
    ---
    Get quotes from two vendors for the Harbor pier sensors.
    ---
    
    [2] help reply
    no verb reply here. general verbs: move resize raise lower remove tile untile rename group create fold unfold append comment resolve check link unlink retitle rewrite sort swap beside match link
    selections do the specializing (help selections).

[18 @51.69s] desk: examine a27
    a27 chat "Priya" · 320x160 at 300,200 · 25w · 49% hidden by a30 · spills-parent · try: raise append
      a chat (subject s15) on f03:
        * Priya: can you send the tide parser when it's ready?
        * Alex: yes, after kickoff.
        * Priya: oh, and the sensor quotes too if you have them.
      awaiting reply: Priya: oh, and the sensor quotes too if you have them.
      where: screen 590,216 320x160 · in f03 (free) local 300,200 z3 · spills-parent, covers a18, covers a19, under a30 · 49% hidden
      verbs: append retitle rewrite · fold comment link · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)

[19 @55.45s] desk: look f31
    f31 surface "Priya" column · empty

[20 @59.36s] desk: do append a27 line="Alex: I found the notes Tide data format and Parser notes."
    ok append a27 line='Alex: I found the notes Tide data format and Parser notes.'  [e3]
      subject s15 changed; 1 appearance(s) now show the new content
      now: a27 chat "Priya" · 320x160 at 300,200 · 36w · 49% hidden by a30 · spills-parent

[21 @64.61s] desk: look a27; do move a27 into=f31
    [1] look a27
    a27 chat "Priya" · 320x160 at 300,200 · 36w · 49% hidden by a30 · spills-parent
        > Priya: can you send the tide parser when it's ready?
    
    [2] do move a27 into=f31
    ok move a27 into=f31  [e4]
      now: a27 chat "Priya" · 36w  (1st of 1 in f31)

[22 @67.19s] desk: look f31; do move a20 into=f31
    [1] look f31
    f31 surface "Priya" column · 1 inside
      a27 chat "Priya" · 36w
    
    [2] do move a20 into=f31
    ok move a20 into=f31  [e5]
      now: a20 note "Tide data format" · due 2026-09-17 · 16w  (2nd of 2 in f31)

[23 @68.89s] desk: look f31; do move a30 into=f31
    [1] look f31
    f31 surface "Priya" column · 2 inside
      a27 chat "Priya" · 36w
      a20 note "Tide data format" · due 2026-09-17 · 16w
    
    [2] do move a30 into=f31
    ok move a30 into=f31  [e6]
      now: a30 note "Parser notes" · 13w  (2nd of 3 in f31)

[24 @70.69s] desk: look f31; do move a22 into=f31
    [1] look f31
    f31 surface "Priya" column · 3 inside
      a27 chat "Priya" · 36w
      a30 note "Parser notes" · 13w
      a20 note "Tide data format" · due 2026-09-17 · 16w
    
    [2] do move a22 into=f31
    ok move a22 into=f31  [e7]
      now: a22 task "Order pier sensors" · due 2026-09-18 · 10w  (2nd of 4 in f31)

[25 @74.47s] desk: look f31; do create f31 kind=task title="Deliver tide parser to Priya" due=2026-09-19
    [1] look f31
    f31 surface "Priya" column · 4 inside
      a27 chat "Priya" · 36w
      a22 task "Order pier sensors" · due 2026-09-18 · 10w
      a30 note "Parser notes" · 13w
      a20 note "Tide data format" · due 2026-09-17 · 16w
    
    [2] do create f31 kind=task title="Deliver tide parser to Priya" due=2026-09-19
    ok create f31 kind=task title='Deliver tide parser to Priya' due=2026-09-19  [e8] → created a33
      a33 task "Deliver tide parser to Priya" · due 2026-09-19 · 0w
        where: screen 857,652 405x130 · in f31 (column) local 8,644 z8 · clear
      new task s32 placed as a33
      now: f31 surface "Priya" column · 5 inside  (3rd of 3 in f01)

[26 @77.47s] desk: look f31; look f02
    [1] look f31
    f31 surface "Priya" column · 5 inside
      a27 chat "Priya" · 36w
      a22 task "Order pier sensors" · due 2026-09-18 · 10w
      a30 note "Parser notes" · 13w
      a20 note "Tide data format" · due 2026-09-17 · 16w
      a33 task "Deliver tide parser to Priya" · due 2026-09-19 · 0w
    
    [2] look f02
    f02 surface "Harbor" column · 2 inside
      a17 task "Harbor permit renewal" · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · due 2026-09-20 · 17w

## reply
Created the non-overlapping Priya column with her chat, the two parser notes, the sensor-quotes task, and a delivery task due 2026-09-19. Replied in chat naming “Tide data format” and “Parser notes.” Harbor was left unchanged.

Hardest step was catching Priya’s new sensor-quotes request after the chat changed. The text tools made that update clear, but did not offer a distinct reply verb; I used a chat append.

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