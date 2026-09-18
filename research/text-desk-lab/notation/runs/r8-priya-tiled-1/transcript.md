# r8-priya-tiled-1  task=priya variant=tiled
prompt: Priya asked for something in the Priya chat on the Meeting panel. Set up a panel for her: a new surface called Priya on the desk holding her chat, every note or task on the desk that is about what she asked for, and a new task for me to deliver it, due 2026-09-19. Nothing in the panel may overlap. Then reply to her in the chat, one line, naming the note titles you found. Leave the Harbor column alone.

[1 @4.23s] desk: look
    f01 surface "desk" row · 1280x800 · 2 inside · try: sort
      f02 surface "Harbor" column · 405x784 · 2 inside · try: sort  (open f02 to see inside)
      f28 surface "Right" column · 850x784 · 2 inside · try: sort  (open f28 to see inside)

[2 @7.02s] desk: look f28
    f28 surface "Right" column · 850x784 · 2 inside · try: sort
      f03 surface "Meeting" free · 834x370 · 4 inside · try: tile raise hidden,in:f03 group kind:chat,in:f03  (open f03 to see inside)
      f04 surface "Scratch" free · 834x389 · 7 inside · try: tile raise hidden,in:f04 group kind:image,in:f04  (open f04 to see inside)

[3 @8.88s] desk: look f03
    f03 surface "Meeting" free · 834x370 · 4 inside · try: tile raise hidden,in:f03 group kind:chat,in:f03
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: remove also:a18
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 46% hidden by a27,a30 · try: raise
      a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a30 · try: raise
      a30 note "Parser notes" · 260x140 at 440,200 · 13w

[4 @11.45s] desk: read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    ---

[5 @13.56s] desk: find tide parser
    find 'tide parser': 3 hit(s)
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: raise  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a30 · try: raise  in f03
      a30 note "Parser notes" · 260x140 at 440,200 · 13w  in f03
      as a selection: ?tide+parser   e.g. do move ?tide+parser into=<surface> one=1   (help selections)

[6 @16.56s] desk: read a20
    s07 note "Tide data format" · appears at a20 · tags harbor · due 2026-09-17
    ---
    Harbor tide feed is CSV, one row per 6 minutes. Need a parser before the kickoff.
    ---

[7 @16.56s] desk: read a30
    s29 note "Parser notes" · appears at a30 · tags harbor
    ---
    Tide parser: read the 6-minute CSV rows, emit JSON per hour. Half done.
    ---

[8 @19.03s] desk: find parser
    find 'parser': 3 hit(s)
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: raise  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a30 · try: raise  in f03
      a30 note "Parser notes" · 260x140 at 440,200 · 13w  in f03
      as a selection: ?parser   e.g. do move ?parser into=<surface> one=1   (help selections)

[9 @23.09s] desk: help create
    create  (on: surface; level 1)
      Make a new note, task or chat and place it on this surface.
      args: kind=note|task|chat title=<str> [text=<str>] [due=YYYY-MM-DD] [tags=a,b]
      e.g. do create f03 kind=task title="Send parser" due=2026-09-19

[10 @25.2s] desk: help surface
    no verb surface. verbs: append create dedupe done due fold gather group lower move raise remove rename reply resize retitle reveal rewrite sort split stack tidy tile unfold untile
    examine <id> shows which apply to a thing.

[11 @27.47s] desk: help split
    no verb split here. general verbs: move resize raise lower remove tile untile rename group create fold unfold append retitle rewrite sort swap beside match
    selections do the specializing (help selections).

[12 @30.19s] desk: examine f01
    f01 surface "desk" row · 1280x800 · 2 inside · try: sort
      a row surface (the desk itself), holding 2 thing(s): f02, f28
      where: screen 0,0 1280x800 · in - (-) · clear
      verbs from surface: tile(as=column|row)  untile  rename(title=<str>)  group(title=<str> as=free|column|row)  create(kind=note|task|chat title=<str> [text=<str>] [due=YYYY-MM-DD] [tags=a,b])  sort(by=due|title|kind [desc=1])
      any verb also takes a selection instead of an id (help selections)

[13 @34.12s] desk: help group
    group  (on: surface; level 1)
      Make a new empty surface inside this one.
      args: title=<str> as=free|column|row
      e.g. do group f04 title="Pictures" as=column

[14 @38.2s] desk: do group f01 title="Priya" as=column
    ok group f01 title=Priya as=column  [e1] → created f31
      f31 surface "Priya" column · 421x784 · empty
        where: screen 849,8 421x784 · in f01 (row) local 849,8 z5 · clear
      now: f01 surface "desk" row · 1280x800 · 3 inside · try: sort

[15 @41.78s] desk: look f03
    !! since your last look: e2 edit s15 by priya
    f03 surface "Meeting" free · 543x370 · 4 inside · try: tile raise hidden,in:f03 group kind:chat,in:f03
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: remove also:a18
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 46% hidden by a27,a30 · spills-parent · try: raise
      a27 chat "Priya" · 320x160 at 300,200 · 25w · 49% hidden by a30 · spills-parent · try: raise append
      a30 note "Parser notes" · 260x140 at 440,200 · 13w · spills-parent

[16 @41.78s] desk: look f04
    f04 surface "Scratch" free · 543x389 · 7 inside · try: tile raise hidden,in:f04 group kind:image,in:f04
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: raise
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25 · try: raise
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · spills-parent · try: raise
      a23 note "Grocery list" · 240x150 at 560,60 · 4w · spills-parent
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · spills-parent · try: raise remove also:a24
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w · spills-parent

[17 @44.33s] desk: read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    Priya: oh, and the sensor quotes too if you have them.
    ---

[18 @47.31s] desk: find sensor
    find 'sensor': 5 hit(s)
      a16 note "Harbor kickoff" · 250x380 · due 2026-09-20 · 17w  in f02
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · spills-parent · try: raise  in f04
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: remove also:a18  in f03
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · spills-parent · try: raise remove also:a24  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 25w · 49% hidden by a30 · spills-parent · try: raise append  in f03
      as a selection: ?sensor   e.g. do move ?sensor into=<surface> one=1   (help selections)

[19 @47.33s] desk: find quote
    find 'quote': 2 hit(s)
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · spills-parent · try: raise  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 25w · 49% hidden by a30 · spills-parent · try: raise append  in f03
      as a selection: ?quote   e.g. do move ?quote into=<surface> one=1   (help selections)

[20 @52.7s] desk: read a22
    s06 task "Order pier sensors" · appears at a22 · tags harbor · due 2026-09-18
    ---
    Get quotes from two vendors for the Harbor pier sensors.
    ---

[21 @52.7s] desk: read a18
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    ---

[22 @52.7s] desk: read a16
    s05 note "Harbor kickoff" · appears at a16 · tags harbor · due 2026-09-20
    ---
    Kickoff for the Harbor project.
    Attendees: Sam, Priya, Alex.
    Decide the pier sensor vendor by the 20th.
    ---

[23 @59.84s] desk: do move a27,a30,a20,a22 into=f31
    ok move 4 thing(s) matching list a27,a30,a20,a22: a27 a30 a20 a22  [e3..e6, 4 steps]
      now: a27 chat "Priya" · 405x438 · 25w · try: append  (1st of 4 in f31)
      now: a30 note "Parser notes" · 405x79 · 13w  (4th of 4 in f31)
      now: a20 note "Tide data format" · 405x108 · due 2026-09-17 · 16w  (3rd of 4 in f31)
      now: a22 task "Order pier sensors" · 405x117 · due 2026-09-18 · 10w  (2nd of 4 in f31)

[24 @64.23s] desk: do create f31 kind=task title="Deliver Priya's requested materials" due=2026-09-19
    ok create f31 kind=task title="Deliver Priya's requested materials" due=2026-09-19  [e7] → created a33
      a33 task "Deliver Priya's requested materials" · 405x130 · due 2026-09-19 · 0w
        where: screen 857,652 405x130 · in f31 (column) local 8,644 z8 · clear
      new task s32 placed as a33
      now: f31 surface "Priya" column · 421x784 · 5 inside · try: sort  (3rd of 3 in f01)

[25 @68.44s] desk: help reply
    no verb reply here. general verbs: move resize raise lower remove tile untile rename group create fold unfold append retitle rewrite sort swap beside match
    selections do the specializing (help selections).

[26 @71.42s] desk: help append
    append  (on: text; level 1)
      Add a line at the end of the text. Edits the subject: every appearance changes.
      args: line=<str>
      e.g. do append a18 line="4. Review"

[27 @75.39s] desk: do append a27 line="I found: Tide data format; Parser notes."
    ok append a27 line='I found: Tide data format; Parser notes.'  [e8]
      subject s15 changed; 1 appearance(s) now show the new content
      now: a27 chat "Priya" · 405x357 · 32w  (1st of 5 in f31)

[28 @80.12s] desk: look f31
    f31 surface "Priya" column · 421x784 · 5 inside · try: sort
      a27 chat "Priya" · 405x357 · 32w
      a22 task "Order pier sensors" · 405x95 · due 2026-09-18 · 10w
      a20 note "Tide data format" · 405x88 · due 2026-09-17 · 16w
      a30 note "Parser notes" · 405x64 · 13w
      a33 task "Deliver Priya's requested materials" · 405x130 · due 2026-09-19 · 0w

[29 @80.12s] desk: read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    Priya: oh, and the sensor quotes too if you have them.
    I found: Tide data format; Parser notes.
    ---

## reply
Created the Priya column panel with her chat, both parser notes, sensor-quotes task, and delivery task due 2026-09-19. Verified column layout has no overlaps; Harbor was unchanged. Replied: “I found: Tide data format; Parser notes.”

Hardest step was catching Priya’s follow-up about sensor quotes. The chat had no dedicated reply verb, so I used append to send the one-line response.

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