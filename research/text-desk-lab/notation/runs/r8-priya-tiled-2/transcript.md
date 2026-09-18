# r8-priya-tiled-2  task=priya variant=tiled
prompt: Priya asked for something in the Priya chat on the Meeting panel. Set up a panel for her: a new surface called Priya on the desk holding her chat, every note or task on the desk that is about what she asked for, and a new task for me to deliver it, due 2026-09-19. Nothing in the panel may overlap. Then reply to her in the chat, one line, naming the note titles you found. Leave the Harbor column alone.

[1 @4.98s] desk: look
    f01 surface "desk" row · 1280x800 · 2 inside · try: sort
      f02 surface "Harbor" column · 405x784 · 2 inside · try: sort  (open f02 to see inside)
      f28 surface "Right" column · 850x784 · 2 inside · try: sort  (open f28 to see inside)

[2 @7.62s] desk: look f28
    f28 surface "Right" column · 850x784 · 2 inside · try: sort
      f03 surface "Meeting" free · 834x370 · 4 inside · try: tile raise hidden,in:f03 group kind:chat,in:f03  (open f03 to see inside)
      f04 surface "Scratch" free · 834x389 · 7 inside · try: tile raise hidden,in:f04 group kind:image,in:f04  (open f04 to see inside)

[3 @10.23s] desk: look f03 :3
    f03 surface "Meeting" free · 834x370 · 4 inside · try: tile raise hidden,in:f03 group kind:chat,in:f03
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: remove also:a18
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 46% hidden by a27,a30 · try: raise
      a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a30 · try: raise
      a30 note "Parser notes" · 260x140 at 440,200 · 13w
      verbs: move resize remove tile rename group create   (verbs f03 for argument forms)

[4 @13.27s] desk: read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    ---

[5 @15.67s] desk: find tide parser
    find 'tide parser': 3 hit(s)
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: raise  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a30 · try: raise  in f03
      a30 note "Parser notes" · 260x140 at 440,200 · 13w  in f03
      as a selection: ?tide+parser   e.g. do move ?tide+parser into=<surface> one=1   (help selections)

[6 @18.0s] desk: look f02 :3
    f02 surface "Harbor" column · 405x784 · 2 inside · try: sort
      a17 task "Harbor permit renewal" · 389x380 · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · 389x380 · due 2026-09-20 · 17w
      verbs: move resize remove tile untile rename group create   (verbs f02 for argument forms)

[7 @20.11s] desk: look f04 :3
    f04 surface "Scratch" free · 834x389 · 7 inside · try: tile raise hidden,in:f04 group kind:image,in:f04
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: raise
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25 · try: raise
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · try: raise
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · try: raise remove also:a24
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w · spills-parent
      verbs: move resize remove tile rename group create   (verbs f04 for argument forms)

[8 @22.55s] desk: find parser
    find 'parser': 3 hit(s)
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: raise  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a30 · try: raise  in f03
      a30 note "Parser notes" · 260x140 at 440,200 · 13w  in f03
      as a selection: ?parser   e.g. do move ?parser into=<surface> one=1   (help selections)

[9 @25.8s] desk: read a20
    s07 note "Tide data format" · appears at a20 · tags harbor · due 2026-09-17
    ---
    Harbor tide feed is CSV, one row per 6 minutes. Need a parser before the kickoff.
    ---

[10 @27.53s] desk: read a30
    s29 note "Parser notes" · appears at a30 · tags harbor
    ---
    Tide parser: read the 6-minute CSV rows, emit JSON per hour. Half done.
    ---

[11 @30.42s] desk: help create
    create  (on: surface; level 1)
      Make a new note, task or chat and place it on this surface.
      args: kind=note|task|chat title=<str> [text=<str>] [due=YYYY-MM-DD] [tags=a,b]
      e.g. do create f03 kind=task title="Send parser" due=2026-09-19

[12 @33.41s] desk: help surface
    no verb surface. verbs: append create dedupe done due fold gather group lower move raise remove rename reply resize retitle reveal rewrite sort split stack tidy tile unfold untile
    examine <id> shows which apply to a thing.

[13 @35.69s] desk: examine f01
    f01 surface "desk" row · 1280x800 · 2 inside · try: sort
      a row surface (the desk itself), holding 2 thing(s): f02, f28
      where: screen 0,0 1280x800 · in - (-) · clear
      verbs from surface: tile(as=column|row)  untile  rename(title=<str>)  group(title=<str> as=free|column|row)  create(kind=note|task|chat title=<str> [text=<str>] [due=YYYY-MM-DD] [tags=a,b])  sort(by=due|title|kind [desc=1])
      any verb also takes a selection instead of an id (help selections)

[14 @37.75s] desk: help group
    group  (on: surface; level 1)
      Make a new empty surface inside this one.
      args: title=<str> as=free|column|row
      e.g. do group f04 title="Pictures" as=column

[15 @43.86s] desk: do group f01 title="Priya" as=column
    ok group f01 title=Priya as=column  [e1] → created f31
      f31 surface "Priya" column · 421x784 · empty
        where: screen 849,8 421x784 · in f01 (row) local 849,8 z5 · clear
      now: f01 surface "desk" row · 1280x800 · 3 inside · try: sort

[16 @46.72s] desk: help move
    !! since your last look: e2 edit s15 by priya
    move  (on: thing; level 1)
      Put this somewhere else.
      args: into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>
      e.g. do move a04 into=f02

[17 @49.11s] desk: read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    Priya: oh, and the sensor quotes too if you have them.
    ---

[18 @52.89s] desk: find sensor
    find 'sensor': 5 hit(s)
      a16 note "Harbor kickoff" · 250x380 · due 2026-09-20 · 17w  in f02
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · spills-parent · try: raise  in f04
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: remove also:a18  in f03
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · spills-parent · try: raise remove also:a24  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 25w · 49% hidden by a30 · spills-parent · try: raise append  in f03
      as a selection: ?sensor   e.g. do move ?sensor into=<surface> one=1   (help selections)

[19 @56.31s] desk: find quote
    find 'quote': 2 hit(s)
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · spills-parent · try: raise  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 25w · 49% hidden by a30 · spills-parent · try: raise append  in f03
      as a selection: ?quote   e.g. do move ?quote into=<surface> one=1   (help selections)

[20 @58.94s] desk: read a22
    s06 task "Order pier sensors" · appears at a22 · tags harbor · due 2026-09-18
    ---
    Get quotes from two vendors for the Harbor pier sensors.
    ---

[21 @62.42s] desk: read a16
    s05 note "Harbor kickoff" · appears at a16 · tags harbor · due 2026-09-20
    ---
    Kickoff for the Harbor project.
    Attendees: Sam, Priya, Alex.
    Decide the pier sensor vendor by the 20th.
    ---

[22 @66.66s] desk: read a18
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    ---

[23 @70.31s] desk: do move a27,a20,a30,a22 into=f31
    ok move 4 thing(s) matching list a27,a20,a30,a22: a27 a20 a30 a22  [e3..e6, 4 steps]
      now: a27 chat "Priya" · 405x438 · 25w · try: append  (1st of 4 in f31)
      now: a20 note "Tide data format" · 405x91 · due 2026-09-17 · 16w  (4th of 4 in f31)
      now: a30 note "Parser notes" · 405x97 · 13w  (3rd of 4 in f31)
      now: a22 task "Order pier sensors" · 405x116 · due 2026-09-18 · 10w  (2nd of 4 in f31)

[24 @73.02s] desk: look f31 :3
    f31 surface "Priya" column · 421x784 · 4 inside · try: sort
      a27 chat "Priya" · 405x438 · 25w · try: append
      a22 task "Order pier sensors" · 405x116 · due 2026-09-18 · 10w
      a30 note "Parser notes" · 405x97 · 13w
      a20 note "Tide data format" · 405x91 · due 2026-09-17 · 16w
      verbs: move resize remove tile untile rename group create   (verbs f31 for argument forms)

[25 @75.73s] desk: do create f31 kind=task title="Deliver tide parser and sensor quotes" due=2026-09-19
    ok create f31 kind=task title='Deliver tide parser and sensor quotes' due=2026-09-19  [e7] → created a33
      a33 task "Deliver tide parser and sensor quotes" · 405x130 · due 2026-09-19 · 0w
        where: screen 857,652 405x130 · in f31 (column) local 8,644 z8 · clear
      new task s32 placed as a33
      now: f31 surface "Priya" column · 421x784 · 5 inside · try: sort  (3rd of 3 in f01)

[26 @79.34s] desk: help reply
    no verb reply here. general verbs: move resize raise lower remove tile untile rename group create fold unfold append retitle rewrite sort swap beside match
    selections do the specializing (help selections).

[27 @81.53s] desk: help append
    append  (on: text; level 1)
      Add a line at the end of the text. Edits the subject: every appearance changes.
      args: line=<str>
      e.g. do append a18 line="4. Review"

[28 @84.31s] desk: do append a27 line="Alex: I found Tide data format and Parser notes."
    ok append a27 line='Alex: I found Tide data format and Parser notes.'  [e8]
      subject s15 changed; 1 appearance(s) now show the new content
      now: a27 chat "Priya" · 405x357 · 34w  (1st of 5 in f31)

[29 @87.36s] desk: look f31 :3
    f31 surface "Priya" column · 421x784 · 5 inside · try: sort
      a27 chat "Priya" · 405x357 · 34w
      a22 task "Order pier sensors" · 405x94 · due 2026-09-18 · 10w
      a30 note "Parser notes" · 405x79 · 13w
      a20 note "Tide data format" · 405x74 · due 2026-09-17 · 16w
      a33 task "Deliver tide parser and sensor quotes" · 405x130 · due 2026-09-19 · 0w
      verbs: move resize remove tile untile rename group create   (verbs f31 for argument forms)

[30 @90.12s] desk: read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    Priya: oh, and the sensor quotes too if you have them.
    Alex: I found Tide data format and Parser notes.
    ---

[31 @92.59s] desk: look f02
    f02 surface "Harbor" column · 266x784 · 2 inside · try: sort
      a17 task "Harbor permit renewal" · 250x380 · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · 250x380 · due 2026-09-20 · 17w

[32 @101.58s] desk: help resize
    resize  (on: thing; level 1)
      Change width and height.
      args: to=<w>x<h>
      e.g. do resize a04 to=300x160

## reply
Created the Priya panel with chat, relevant notes/tasks, and delivery task due 2026-09-19; no items overlap. Replied: “Tide data format” and “Parser notes”; Harbor contents were untouched, though its width auto-adjusted.

Hardest step was incorporating Priya’s follow-up about sensor quotes. Search results made indirect sensor-vendor notes ambiguous.

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