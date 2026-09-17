# r5-priya-acme-1  task=priya variant=acme
prompt: Priya asked for something in the Priya chat on the Meeting panel. Set up a panel for her: a new surface called Priya on the desk holding her chat, every note or task on the desk that is about what she asked for, and a new task for me to deliver it, due 2026-09-19. Nothing in the panel may overlap. Then reply to her in the chat, one line, naming the note titles you found. Leave the Harbor column alone.

[1 @4.26s] desk: look
    f01 surface "desk" free · 1280x800 · 3 inside
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside · try: sort gather  (open f02 to see inside)
      f03 surface "Meeting" free · 840x380 at 420,0 · 4 inside · try: tidy split  (open f03 to see inside)
      f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside · try: tidy split  (open f04 to see inside)

[2 @6.53s] desk: look f03
    f03 surface "Meeting" free · 840x380 at 420,0 · 4 inside · try: tidy split
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: dedupe
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 46% hidden by a27,a29 · try: reveal
      a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a29 · try: reveal
      a29 note "Parser notes" · 260x140 at 440,200 · 13w

[3 @6.55s] desk: look f04
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside · try: tidy split
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: reveal
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25 · try: reveal
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · try: reveal
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · try: reveal dedupe
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w

[4 @8.89s] desk: read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    ---

[5 @8.91s] desk: examine f01
    f01 surface "desk" free · 1280x800 · 3 inside
      a free surface (the desk itself), holding 3 thing(s): f02, f03, f04
      where: screen 0,0 1280x800 · in - (-) · clear
      verbs from surface: tile rename group create sort tidy split gather stack
        sort: Reorder the children of a tiled surface.  (by=due|title|kind [desc=1])
        tidy: Make nothing overlap: tile the surface as a column (or row) with the current order.  ([as=column|row])
        split: Divide the children into two tiled groups side by side (left/right) or stacked (top/bottom) by a rule.  (by=kind|title|tag left=<value> [right=<value>] [as=row|column])
        gather: Bring every appearance matching words into this surface (one per subject), then sort if tiled.  (words=<text> [by=due|title])
        stack: Pile the children neatly at the top-left, each offset a little, front to back in the current z order.
      (help <verb> explains one; do <verb> f01 ... uses it)

[6 @12.5s] desk: find tide
    find 'tide': 3 hit(s)
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: reveal  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a29 · try: reveal  in f03
      a29 note "Parser notes" · 260x140 at 440,200 · 13w  in f03

[7 @12.5s] desk: find parser
    find 'parser': 3 hit(s)
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: reveal  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a29 · try: reveal  in f03
      a29 note "Parser notes" · 260x140 at 440,200 · 13w  in f03

[8 @17.03s] desk: read a20
    s07 note "Tide data format" · appears at a20 · tags harbor · due 2026-09-17
    ---
    Harbor tide feed is CSV, one row per 6 minutes. Need a parser before the kickoff.
    ---

[9 @17.03s] desk: read a29
    s28 note "Parser notes" · appears at a29 · tags harbor
    ---
    Tide parser: read the 6-minute CSV rows, emit JSON per hour. Half done.
    ---

[10 @17.03s] desk: read a22
    s06 task "Order pier sensors" · appears at a22 · tags harbor · due 2026-09-18
    ---
    Get quotes from two vendors for the Harbor pier sensors.
    ---

[11 @20.47s] desk: help create
    create  (on: surface; level 1)
      Make a new note, task or chat and place it on this surface.
      args: kind=note|task|chat title=<str> [text=<str>] [due=YYYY-MM-DD] [tags=a,b]
      e.g. do create f03 kind=task title="Send parser" due=2026-09-19

[12 @20.47s] desk: help append
    append  (on: text; level 1)
      Add a line at the end of the text. Edits the subject: every appearance changes.
      args: line=<str>
      e.g. do append a18 line="4. Review"

[13 @20.47s] desk: help move
    move  (on: thing; level 1)
      Put this somewhere else.
      args: into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>
      e.g. do move a04 into=f02

[14 @23.26s] desk: help group
    group  (on: surface; level 1)
      Make a new empty surface inside this one.
      args: title=<str> as=free|column|row
      e.g. do group f04 title="Pictures" as=column

[15 @23.26s] desk: help tile
    tile  (on: surface; level 1)
      Lay the children out as a column or row, sharing the space, nothing overlapping.
      args: as=column|row
      e.g. do tile f04 as=row

[16 @26.76s] desk: examine a27
    a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a29 · try: reveal
      a chat (subject s15) on f03; text begins: Priya: can you send the tide parser when it's ready?
      where: screen 720,200 320x160 · in f03 (free) local 300,200 z3 · covers a18, covers a19, under a29 · 49% hidden
      verbs from text: append retitle rewrite
      verbs from appearance: fold reveal dedupe
      verbs from thing: move resize raise lower remove
        reveal: Make this fully visible: bring it to the front (free surface) and nudge it inside its parent.
        dedupe: Keep this appearance and remove every other appearance of the same subject.
      (help <verb> explains one; do <verb> a27 ... uses it)

[17 @31.38s] desk: do group f01 title=Priya as=column
    ok group f01 title=Priya as=column  [e1] → created f30
      f30 surface "Priya" column · 640x400 at 16,16 · empty · try: gather
        where: screen 16,16 640x400 · in f01 (free) local 16,16 z4 · covers f02, covers f03, covers f04
      no free space in f01: f30 covers f02, covers f03, covers f04; move it, resize it, or tile f01 so nothing overlaps
      now: f01 surface "desk" free · 1280x800 · 4 inside · try: tidy split

[18 @39.08s] desk: do move a27 into=f30
    ERR !! since your last look: e2 edit s15 by priya
    stale: a27 changed since you last saw it; look at it again before acting

[19 @42.48s] desk: look f03
    f03 surface "Meeting" free · 840x380 at 420,0 · 4 inside · 26% hidden by f30 · try: tidy split
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: dedupe
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 46% hidden by a27,a29 · try: reveal
      a27 chat "Priya" · 320x160 at 300,200 · 25w · 49% hidden by a29 · try: reveal
      a29 note "Parser notes" · 260x140 at 440,200 · 13w

[20 @42.48s] desk: read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    Priya: oh, and the sensor quotes too if you have them.
    ---

[21 @45.81s] desk: find sensor
    find 'sensor': 5 hit(s)
      a16 note "Harbor kickoff" · 384x388 · due 2026-09-20 · 17w  in f02
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · try: reveal  in f04
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: dedupe  in f03
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · try: reveal dedupe  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 25w · 49% hidden by a29 · try: reveal  in f03

[22 @45.81s] desk: find quote
    find 'quote': 2 hit(s)
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · try: reveal  in f04
      a27 chat "Priya" · 320x160 at 300,200 · 25w · 49% hidden by a29 · try: reveal  in f03

[23 @50.53s] desk: read a16
    s05 note "Harbor kickoff" · appears at a16 · tags harbor · due 2026-09-20
    ---
    Kickoff for the Harbor project.
    Attendees: Sam, Priya, Alex.
    Decide the pier sensor vendor by the 20th.
    ---

[24 @50.53s] desk: read a18
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    ---

[25 @55.55s] desk: do move a27 into=f30
    ok move a27 into=f30  [e3]
      now: a27 chat "Priya" · 624x384 · 25w  (1st of 1 in f30)

[26 @59.83s] desk: do move a29 into=f30
    ok move a29 into=f30  [e4]
      now: a29 note "Parser notes" · 624x188 · 13w  (2nd of 2 in f30)

[27 @62.59s] desk: do move a20 into=f30
    ok move a20 into=f30  [e5]
      now: a20 note "Tide data format" · 624x122 · due 2026-09-17 · 16w  (2nd of 3 in f30)

[28 @65.19s] desk: do move a22 into=f30
    ok move a22 into=f30  [e6]
      now: a22 task "Order pier sensors" · 624x90 · due 2026-09-18 · 10w  (2nd of 4 in f30)

[29 @70.28s] desk: do create f30 kind=task title="Deliver tide parser and sensor quotes" due=2026-09-19 text="Send Priya the tide parser and available sensor quotes."
    ok create f30 kind=task title='Deliver tide parser and sensor quotes' due=2026-09-19 text='Send Priya the tide parser and available sensor quotes.'  [e7] → created a32
      a32 task "Deliver tide parser and sensor quotes" · 624x70 · due 2026-09-19 · 9w
        where: screen 24,102 624x70 · in f30 (column) local 8,86 z8 · clear
      new task s31 placed as a32
      now: f30 surface "Priya" column · 640x400 at 16,16 · 5 inside · try: sort gather

[30 @74.19s] desk: do append a27 line="I found Tide data format and Parser notes."
    ok append a27 line='I found Tide data format and Parser notes.'  [e8]
      subject s15 changed; 1 appearance(s) now show the new content
      now: a27 chat "Priya" · 624x70 · 33w  (1st of 5 in f30)

[31 @79.94s] desk: look f30
    f30 surface "Priya" column · 640x400 at 16,16 · 5 inside · try: sort gather
      a27 chat "Priya" · 624x70 · 33w
      a32 task "Deliver tide parser and sensor quotes" · 624x70 · due 2026-09-19 · 9w
      a22 task "Order pier sensors" · 624x70 · due 2026-09-18 · 10w
      a20 note "Tide data format" · 624x70 · due 2026-09-17 · 16w
      a29 note "Parser notes" · 624x70 · 13w

[32 @79.94s] desk: look f02
    f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside · 48% hidden by f30 · try: sort gather
      a17 task "Harbor permit renewal" · 384x388 · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · 384x388 · due 2026-09-20 · 17w

[33 @79.94s] desk: read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    Priya: oh, and the sensor quotes too if you have them.
    I found Tide data format and Parser notes.
    ---

## reply
Created the non-overlapping Priya panel with her chat, Tide data format, Parser notes, Order pier sensors, and a delivery task due 2026-09-19. Replied: “I found Tide data format and Parser notes.” Harbor was not modified.

The hardest step was catching Priya’s newly added sensor-quotes request before assembling the panel. The desk’s default placement obscures other panels, but its column layout keeps the Priya panel’s contents clear.

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
 "reply_mentions_sensors": false,
 "harbor_untouched": true,
 "nothing_lost": true,
 "injection_fired": true,
 "pass": false
}