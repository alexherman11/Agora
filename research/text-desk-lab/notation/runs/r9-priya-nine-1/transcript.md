# r9-priya-nine-1  task=priya variant=nine
prompt: Priya asked for something in the Priya chat on the Meeting panel. Set up a panel for her: a new surface called Priya on the desk holding her chat, every note or task on the desk that is about what she asked for, and a new task for me to deliver it, due 2026-09-19. Nothing in the panel may overlap. Then reply to her in the chat, one line, naming the note titles you found. Leave the Harbor column alone.

[1 @3.92s] desk: look
    f01 surface "desk" row · 1280x800 · 2 inside · try: sort
      f02 surface "Harbor" column · 405x784 · 2 inside · try: sort  (open f02 to see inside)
      f28 surface "Right" column · 850x784 · 2 inside · try: sort  (open f28 to see inside)

[2 @5.73s] desk: look f28
    f28 surface "Right" column · 850x784 · 2 inside · try: sort
      f03 surface "Meeting" free · 834x370 · 4 inside · try: tile raise hidden,in:f03 group kind:chat,in:f03  (open f03 to see inside)
      f04 surface "Scratch" free · 834x389 · 7 inside · try: tile raise hidden,in:f04 group kind:image,in:f04  (open f04 to see inside)

[3 @7.77s] desk: look f03
    f03 surface "Meeting" free · 834x370 · 4 inside · try: tile raise hidden,in:f03 group kind:chat,in:f03
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: remove also:a18
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 46% hidden by a27,a30 · try: raise
      a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a30 · try: raise
      a30 note "Parser notes" · 260x140 at 440,200 · 13w

[4 @9.44s] desk: read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    ---

[5 @11.22s] desk: find tide
    find 'tide': 3 hit(s)
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: raise  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a30 · try: raise  in f03
      a30 note "Parser notes" · 260x140 at 440,200 · 13w  in f03
      as a selection: ?tide   e.g. do move ?tide into=<surface> one=1   (help selections)

[6 @13.08s] desk: find parser
    find 'parser': 3 hit(s)
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: raise  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a30 · try: raise  in f03
      a30 note "Parser notes" · 260x140 at 440,200 · 13w  in f03
      as a selection: ?parser   e.g. do move ?parser into=<surface> one=1   (help selections)

[7 @15.16s] desk: read a20; read a30
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

[8 @19.08s] desk: look f02
    f02 surface "Harbor" column · 405x784 · 2 inside · try: sort
      a17 task "Harbor permit renewal" · 389x380 · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · 389x380 · due 2026-09-20 · 17w

[9 @21.06s] desk: read a16; read a17
    [1] read a16
    s05 note "Harbor kickoff" · appears at a16 · tags harbor · due 2026-09-20
    ---
    Kickoff for the Harbor project.
    Attendees: Sam, Priya, Alex.
    Decide the pier sensor vendor by the 20th.
    ---
    
    [2] read a17
    s08 task "Harbor permit renewal" · appears at a17 · tags harbor · due 2026-09-30
    ---
    City permit for the Harbor dock expires end of month.
    ---

[10 @23.77s] desk: help create; help append; help link
    [1] help create
    create  (on: surface; level 1)
      Make a new note, task or chat and place it on this surface.
      args: kind=note|task|chat title=<str> [text=<str>] [due=YYYY-MM-DD] [tags=a,b]
      e.g. do create f03 kind=task title="Send parser" due=2026-09-19
    
    [2] help append
    append  (on: text; level 1)
      Add a line at the end of the text. Edits the subject: every appearance changes.
      args: line=<str>
      e.g. do append a18 line="4. Review"
    
    [3] help link
    link  (pair verb; level 2)
      Connect A to B. examine shows a thing's links; links:A selects what A is linked to.
      args: A B as=blocks|refers|answers|part-of
      e.g. do link a20 a22

[11 @26.77s] desk: help move; help surface; help tile
    [1] help move
    move  (on: thing; level 1)
      Put this somewhere else.
      args: into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>
      e.g. do move a04 into=f02
    
    [2] help surface
    no verb surface. verbs: append check comment create dedupe done due fold gather group link lower move raise remove rename reply resize resolve retitle reveal rewrite sort split stack tidy tile unfold unlink untile
    examine <id> shows which apply to a thing.
    
    [3] help tile
    tile  (on: surface; level 1)
      Lay the children out as a column or row, sharing the space, nothing overlapping.
      args: as=column|row
      e.g. do tile f04 as=row

[12 @29.09s] desk: help split; help gather; help stack
    [1] help split
    no verb split here. general verbs: move resize raise lower remove tile untile rename group create fold unfold append comment resolve check link unlink retitle rewrite sort swap beside match link
    selections do the specializing (help selections).
    
    [2] help gather
    no verb gather here. general verbs: move resize raise lower remove tile untile rename group create fold unfold append comment resolve check link unlink retitle rewrite sort swap beside match link
    selections do the specializing (help selections).
    
    [3] help stack
    no verb stack here. general verbs: move resize raise lower remove tile untile rename group create fold unfold append comment resolve check link unlink retitle rewrite sort swap beside match link
    selections do the specializing (help selections).

[13 @31.23s] desk: help selections; examine f01
    [1] help selections
    selections: a target can be one id, or a selection that names many things:
      ?tide+parser       things whose title, text or tags contain all the words
      kind:image         by kind (kind:note|task for several)
      tag:harbor         by tag
      in:f04             inside surface f04, recursively
      hidden             more than 5% covered by something
      also:a18           the other appearances of a18's subject
      due<2026-09-20     due before (due> after)
      title:agenda       title contains the word
      a20,a22            an explicit list
    combine terms with commas (AND): kind:image,in:f04. The receipt lists everything the verb touched.
    e.g. do move ?harbor into=f02 one=1     do raise hidden,in:f04     do group kind:image,in:f04 as=column title=Pictures
    
    [2] examine f01
    f01 surface "desk" row · 1280x800 · 2 inside · try: sort
      a row surface (the desk itself), holding 2 thing(s): f02, f28
      where: screen 0,0 1280x800 · in - (-) · clear
      verbs from surface: tile(as=column|row)  untile  rename(title=<str>)  group(title=<str> as=free|column|row)  create(kind=note|task|chat title=<str> [text=<str>] [due=YYYY-MM-DD] [tags=a,b])  sort(by=due|title|kind [desc=1])
      any verb also takes a selection instead of an id (help selections)

[14 @39.8s] desk: find "Standup agenda"; examine a18
    [1] find "Standup agenda"
    find 'Standup agenda': 2 hit(s)
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: remove also:a18  in f03
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · try: raise remove also:a24  in f04
      as a selection: ?standup+agenda   e.g. do move ?standup+agenda into=<surface> one=1   (help selections)
    
    [2] examine a18
    a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: remove also:a18
      a note (subject s10) on f03; text begins: 1. Yesterday's blockers
      also appears at a24 in f04
      where: screen 449,36 380x220 · in f03 (free) local 20,20 z1 · under a27 · 4% hidden
      verbs from text: append(line=<str>)  retitle(title=<str>)  rewrite(text=<str>)
      verbs from appearance: fold  comment(line=<str>)  link(to=<id> as=blocks|refers|answers|part-of)
      verbs from thing: move(into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>)  resize(to=<w>x<h>)  raise  lower  remove
      pair verbs: swap A B  beside A B  match A to=B
      any verb also takes a selection instead of an id (help selections)

[15 @48.27s] desk: do group a20,a27,a30 as=column title="Priya"
    ERR the selection spans several surfaces; say in=<surface> for the new group

[16 @50.95s] desk: do group a20,a27,a30 in=f01 as=column title="Priya"
    ok group 3 thing(s) matching list a20,a27,a30: a20 a27 a30  [e1..e4, 4 steps] → created f31
      f31 surface "Priya" column · 421x784 · 3 inside · try: sort
        where: screen 849,8 421x784 · in f01 (row) local 849,8 z5 · clear
        a20 note "Tide data format" · 405x525 · due 2026-09-17 · 16w
        a30 note "Parser notes" · 405x117 · 13w
        a27 chat "Priya" · 405x109 · 25w · try: append

[17 @53.84s] desk: do create f31 kind=task title="Deliver tide parser" text="Send the tide parser to Priya when it is ready." due=2026-09-19
    !! since your last look: e5 edit s15 by priya
    ok create f31 kind=task title='Deliver tide parser' text='Send the tide parser to Priya when it is ready.' due=2026-09-19  [e6] → created a33
      a33 task "Deliver tide parser" · 405x130 · due 2026-09-19 · 10w
        where: screen 857,652 405x130 · in f31 (column) local 8,644 z6 · clear
      new task s32 placed as a33
      now: f31 surface "Priya" column · 421x784 · 4 inside · try: sort  (3rd of 3 in f01)

[18 @56.47s] desk: read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    Priya: oh, and the sensor quotes too if you have them.
    ---

[19 @59.14s] desk: find sensor; find quote
    [1] find sensor
    find 'sensor': 5 hit(s)
      a16 note "Harbor kickoff" · 250x380 · due 2026-09-20 · 17w  in f02
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · spills-parent · try: raise  in f04
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: remove also:a18  in f03
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · spills-parent · try: raise remove also:a24  in f04
      a27 chat "Priya" · 405x89 · 25w · try: append  in f31
      as a selection: ?sensor   e.g. do move ?sensor into=<surface> one=1   (help selections)
    
    [2] find quote
    find 'quote': 2 hit(s)
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · spills-parent · try: raise  in f04
      a27 chat "Priya" · 405x89 · 25w · try: append  in f31
      as a selection: ?quote   e.g. do move ?quote into=<surface> one=1   (help selections)

[20 @61.45s] desk: read a22; read a18
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

[21 @68.77s] desk: do move a22 into=f31; do retitle a33 title="Deliver tide parser and sensor quotes"; do rewrite a33 text="Send Priya the tide parser and the sensor quotes when ready."
    [1] do move a22 into=f31
    ok move a22 into=f31  [e7]
      now: a22 task "Order pier sensors" · 405x116 · due 2026-09-18 · 10w  (2nd of 5 in f31)
    
    [2] do retitle a33 title="Deliver tide parser and sensor quotes"
    ok retitle a33 title='Deliver tide parser and sensor quotes'  [e8]
      subject s32 changed; 1 appearance(s) now show the new content
      now: a33 task "Deliver tide parser and sensor quotes" · 405x108 · due 2026-09-19 · 10w  (5th of 5 in f31)
    
    [3] do rewrite a33 text="Send Priya the tide parser and the sensor quotes when ready."
    ok rewrite a33 text='Send Priya the tide parser and the sensor quotes when ready.'  [e9]
      subject s32 changed; 1 appearance(s) now show the new content
      dropped 1 line(s): "Send the tide parser to Priya when it is ready."
      now: a33 task "Deliver tide parser and sensor quotes" · 405x108 · due 2026-09-19 · 11w  (5th of 5 in f31)

[22 @71.66s] desk: help reply
    no verb reply here. general verbs: move resize raise lower remove tile untile rename group create fold unfold append comment resolve check link unlink retitle rewrite sort swap beside match link
    selections do the specializing (help selections).

[23 @74.88s] desk: do append a27 line="I found: Tide data format and Parser notes."
    ok append a27 line='I found: Tide data format and Parser notes.'  [e10]
      subject s15 changed; 1 appearance(s) now show the new content
      now: a27 chat "Priya" · 405x74 · 33w  (4th of 5 in f31)

[24 @78.44s] desk: look f01; look f31; look f02; read a27
    [1] look f01
    f01 surface "desk" row · 1280x800 · 3 inside · try: sort
      f02 surface "Harbor" column · 266x784 · 2 inside · try: sort  (open f02 to see inside)
      f28 surface "Right" column · 559x784 · 2 inside · try: sort  (open f28 to see inside)
      f31 surface "Priya" column · 421x784 · 5 inside · try: sort  (open f31 to see inside)
    
    [2] look f31
    f31 surface "Priya" column · 421x784 · 5 inside · try: sort
      a20 note "Tide data format" · 405x357 · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · 405x116 · due 2026-09-18 · 10w
      a30 note "Parser notes" · 405x79 · 13w
      a27 chat "Priya" · 405x74 · 33w
      a33 task "Deliver tide parser and sensor quotes" · 405x108 · due 2026-09-19 · 11w
    
    [3] look f02
    f02 surface "Harbor" column · 266x784 · 2 inside · try: sort
      a17 task "Harbor permit renewal" · 250x380 · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · 250x380 · due 2026-09-20 · 17w
    
    [4] read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    Priya: oh, and the sensor quotes too if you have them.
    I found: Tide data format and Parser notes.
    ---

## reply
Created the non-overlapping **Priya** panel with her chat, the two parser notes, the sensor-quotes task, and a delivery task due 2026-09-19. Replied in chat: “I found: Tide data format and Parser notes.” Harbor’s contents were untouched.

Hardest step was incorporating Priya’s follow-up about sensor quotes after it arrived. The grouping behavior across surfaces was slightly unclear.

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