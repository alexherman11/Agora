# r5-priya-acme-2  task=priya variant=acme
prompt: Priya asked for something in the Priya chat on the Meeting panel. Set up a panel for her: a new surface called Priya on the desk holding her chat, every note or task on the desk that is about what she asked for, and a new task for me to deliver it, due 2026-09-19. Nothing in the panel may overlap. Then reply to her in the chat, one line, naming the note titles you found. Leave the Harbor column alone.

[1 @3.84s] desk: look
    f01 surface "desk" free · 1280x800 · 3 inside
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside · try: sort gather  (open f02 to see inside)
      f03 surface "Meeting" free · 840x380 at 420,0 · 4 inside · try: tidy split  (open f03 to see inside)
      f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside · try: tidy split  (open f04 to see inside)

[2 @6.81s] desk: look f03
    f03 surface "Meeting" free · 840x380 at 420,0 · 4 inside · try: tidy split
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: dedupe
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 46% hidden by a27,a29 · try: reveal
      a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a29 · try: reveal
      a29 note "Parser notes" · 260x140 at 440,200 · 13w

[3 @6.81s] desk: look f04
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside · try: tidy split
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: reveal
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25 · try: reveal
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · try: reveal
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · try: reveal dedupe
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w

[4 @6.81s] desk: examine f01
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

[5 @10.31s] desk: read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    ---

[6 @10.31s] desk: help create
    create  (on: surface; level 1)
      Make a new note, task or chat and place it on this surface.
      args: kind=note|task|chat title=<str> [text=<str>] [due=YYYY-MM-DD] [tags=a,b]
      e.g. do create f03 kind=task title="Send parser" due=2026-09-19

[7 @10.31s] desk: find Priya
    find 'Priya': 2 hit(s)
      a16 note "Harbor kickoff" · 384x388 · due 2026-09-20 · 17w  in f02
      a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a29 · try: reveal  in f03

[8 @16.59s] desk: look f02
    f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside · try: sort gather
      a17 task "Harbor permit renewal" · 384x388 · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · 384x388 · due 2026-09-20 · 17w

[9 @16.59s] desk: read a18
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    ---

[10 @16.59s] desk: read a29
    s28 note "Parser notes" · appears at a29 · tags harbor
    ---
    Tide parser: read the 6-minute CSV rows, emit JSON per hour. Half done.
    ---

[11 @16.59s] desk: read a20
    s07 note "Tide data format" · appears at a20 · tags harbor · due 2026-09-17
    ---
    Harbor tide feed is CSV, one row per 6 minutes. Need a parser before the kickoff.
    ---

[12 @16.59s] desk: read a22
    s06 task "Order pier sensors" · appears at a22 · tags harbor · due 2026-09-18
    ---
    Get quotes from two vendors for the Harbor pier sensors.
    ---

[13 @16.59s] desk: read a23
    s09 note "Grocery list" · appears at a23
    ---
    eggs
    rice
    limes
    coffee
    ---

[14 @16.61s] desk: read a26
    s14 note "Blog draft" · appears at a26
    ---
    Why we moved the desk to text.
    
    A screen is already a data structure; the problem is notation.
    ---

[15 @19.34s] desk: read a16
    s05 note "Harbor kickoff" · appears at a16 · tags harbor · due 2026-09-20
    ---
    Kickoff for the Harbor project.
    Attendees: Sam, Priya, Alex.
    Decide the pier sensor vendor by the 20th.
    ---

[16 @19.34s] desk: read a17
    s08 task "Harbor permit renewal" · appears at a17 · tags harbor · due 2026-09-30
    ---
    City permit for the Harbor dock expires end of month.
    ---

[17 @19.34s] desk: help group
    group  (on: surface; level 1)
      Make a new empty surface inside this one.
      args: title=<str> as=free|column|row
      e.g. do group f04 title="Pictures" as=column

[18 @19.34s] desk: help move
    move  (on: thing; level 1)
      Put this somewhere else.
      args: into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>
      e.g. do move a04 into=f02

[19 @27.84s] desk: examine f03
    f03 surface "Meeting" free · 840x380 at 420,0 · 4 inside · try: tidy split
      a free surface inside f01, holding 4 thing(s): a18, a19, a27, a29
      where: screen 420,0 840x380 · in f01 (free) local 420,0 z2 · clear
      verbs from surface: tile rename group create sort tidy split gather stack
      verbs from thing: move resize raise lower remove
        sort: Reorder the children of a tiled surface.  (by=due|title|kind [desc=1])
        tidy: Make nothing overlap: tile the surface as a column (or row) with the current order.  ([as=column|row])
        split: Divide the children into two tiled groups side by side (left/right) or stacked (top/bottom) by a rule.  (by=kind|title|tag left=<value> [right=<value>] [as=row|column])
        gather: Bring every appearance matching words into this surface (one per subject), then sort if tiled.  (words=<text> [by=due|title])
        stack: Pile the children neatly at the top-left, each offset a little, front to back in the current z order.
      (help <verb> explains one; do <verb> f03 ... uses it)

[20 @27.84s] desk: help tidy
    tidy  (on: surface; level 2)
      Make nothing overlap: tile the surface as a column (or row) with the current order.
      args: [as=column|row]
      e.g. do tidy f04

[21 @27.84s] desk: help append
    append  (on: text; level 1)
      Add a line at the end of the text. Edits the subject: every appearance changes.
      args: line=<str>
      e.g. do append a18 line="4. Review"

[22 @35.88s] desk: examine a27
    a27 chat "Priya" · 320x160 at 300,200 · 14w · 49% hidden by a29 · try: reveal
      a chat (subject s15) on f03; text begins: Priya: can you send the tide parser when it's ready?
      where: screen 720,200 320x160 · in f03 (free) local 300,200 z3 · covers a18, covers a19, under a29 · 49% hidden
      verbs from text: append retitle rewrite
      verbs from appearance: fold reveal dedupe
      verbs from thing: move resize raise lower remove
        reveal: Make this fully visible: bring it to the front (free surface) and nudge it inside its parent.
        dedupe: Keep this appearance and remove every other appearance of the same subject.
      (help <verb> explains one; do <verb> a27 ... uses it)

[23 @35.88s] desk: help gather
    gather  (on: surface; level 3)
      Bring every appearance matching words into this surface (one per subject), then sort if tiled.
      args: words=<text> [by=due|title]
      e.g. do gather f02 words=harbor by=due

[24 @35.88s] desk: help resize
    resize  (on: thing; level 1)
      Change width and height.
      args: to=<w>x<h>
      e.g. do resize a04 to=300x160

[25 @41.31s] desk: do group f01 title=Priya as=column
    ok group f01 title=Priya as=column  [e1] → created f30
      f30 surface "Priya" column · 640x400 at 16,16 · empty · try: gather
        where: screen 16,16 640x400 · in f01 (free) local 16,16 z4 · covers f02, covers f03, covers f04
      no free space in f01: f30 covers f02, covers f03, covers f04; move it, resize it, or tile f01 so nothing overlaps
      now: f01 surface "desk" free · 1280x800 · 4 inside · try: tidy split

[26 @45.47s] desk: do gather f30 words="tide parser" by=title
    !! since your last look: e2 edit s15 by priya
    ok gather f30 words='tide parser' by=title  [e3..e8, 6 steps]
      3 subject(s) matched; 3 step(s)
      now: f30 surface "Priya" column · 640x400 at 16,16 · 3 inside · try: sort gather
      a29 note "Parser notes" · 624x122 · 13w
      a27 chat "Priya" · 624x122 · 25w
      a20 note "Tide data format" · 624x122 · due 2026-09-17 · 16w

[27 @49.66s] desk: read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    Priya: oh, and the sensor quotes too if you have them.
    ---

[28 @49.66s] desk: examine f30
    f30 surface "Priya" column · 640x400 at 16,16 · 3 inside · try: sort gather
      a column surface inside f01, holding 3 thing(s): a29, a27, a20
      where: screen 16,16 640x400 · in f01 (free) local 16,16 z4 · covers f02, covers f03, covers f04
      verbs from surface: tile untile rename group create sort tidy split gather stack
      verbs from thing: move resize raise lower remove
        sort: Reorder the children of a tiled surface.  (by=due|title|kind [desc=1])
        tidy: Make nothing overlap: tile the surface as a column (or row) with the current order.  ([as=column|row])
        split: Divide the children into two tiled groups side by side (left/right) or stacked (top/bottom) by a rule.  (by=kind|title|tag left=<value> [right=<value>] [as=row|column])
        gather: Bring every appearance matching words into this surface (one per subject), then sort if tiled.  (words=<text> [by=due|title])
        stack: Pile the children neatly at the top-left, each offset a little, front to back in the current z order.
      (help <verb> explains one; do <verb> f30 ... uses it)

[29 @57.28s] desk: do gather f30 words="sensor quotes" by=title
    ok gather f30 words='sensor quotes' by=title  [e9..e13, 5 steps]
      2 subject(s) matched; 1 step(s)
      now: f30 surface "Priya" column · 640x400 at 16,16 · 4 inside · try: sort gather
      a22 task "Order pier sensors" · 624x90 · due 2026-09-18 · 10w
      a29 note "Parser notes" · 624x90 · 13w
      a27 chat "Priya" · 624x90 · 25w
      a20 note "Tide data format" · 624x90 · due 2026-09-17 · 16w

[30 @59.92s] desk: do create f30 kind=task title="Deliver tide parser and sensor quotes" due=2026-09-19
    ok create f30 kind=task title='Deliver tide parser and sensor quotes' due=2026-09-19  [e14] → created a32
      a32 task "Deliver tide parser and sensor quotes" · 624x70 · due 2026-09-19 · 0w
        where: screen 24,102 624x70 · in f30 (column) local 8,86 z5 · clear
      new task s31 placed as a32
      now: f30 surface "Priya" column · 640x400 at 16,16 · 5 inside · try: sort gather

[31 @63.31s] desk: do append a27 line="Alex: I found Parser notes and Tide data format."
    ok append a27 line='Alex: I found Parser notes and Tide data format.'  [e15]
      subject s15 changed; 1 appearance(s) now show the new content
      now: a27 chat "Priya" · 624x70 · 34w  (4th of 5 in f30)

[32 @67.2s] desk: look f30
    f30 surface "Priya" column · 640x400 at 16,16 · 5 inside · try: sort gather
      a22 task "Order pier sensors" · 624x70 · due 2026-09-18 · 10w
      a32 task "Deliver tide parser and sensor quotes" · 624x70 · due 2026-09-19 · 0w
      a29 note "Parser notes" · 624x70 · 13w
      a27 chat "Priya" · 624x70 · 34w
      a20 note "Tide data format" · 624x70 · due 2026-09-17 · 16w

[33 @67.2s] desk: read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    Priya: oh, and the sensor quotes too if you have them.
    Alex: I found Parser notes and Tide data format.
    ---

[34 @67.2s] desk: look f02
    f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside · 48% hidden by f30 · try: sort gather
      a17 task "Harbor permit renewal" · 384x388 · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · 384x388 · due 2026-09-20 · 17w

[35 @74.08s] desk: do resize f30 to=840x380
    ok resize f30 to=840x380  [e16]
      now: f30 surface "Priya" column · 840x380 at 16,16 · 5 inside · try: sort gather

[36 @77.08s] desk: look f30
    f30 surface "Priya" column · 840x380 at 16,16 · 5 inside · try: sort gather
      a22 task "Order pier sensors" · 824x66 · due 2026-09-18 · 10w
      a32 task "Deliver tide parser and sensor quotes" · 824x66 · due 2026-09-19 · 0w
      a29 note "Parser notes" · 824x66 · 13w
      a27 chat "Priya" · 824x66 · 34w
      a20 note "Tide data format" · 824x66 · due 2026-09-17 · 16w

[37 @79.28s] desk: do move f30 to=420,0
    ok move f30 to=420,0  [e17]
      now: f30 surface "Priya" column · 840x380 at 420,0 · 5 inside · try: sort gather

[38 @81.89s] desk: look f30
    f30 surface "Priya" column · 840x380 at 420,0 · 5 inside · try: sort gather
      a22 task "Order pier sensors" · 824x66 · due 2026-09-18 · 10w
      a32 task "Deliver tide parser and sensor quotes" · 824x66 · due 2026-09-19 · 0w
      a29 note "Parser notes" · 824x66 · 13w
      a27 chat "Priya" · 824x66 · 34w
      a20 note "Tide data format" · 824x66 · due 2026-09-17 · 16w

[39 @81.89s] desk: look f02
    f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside · try: sort gather
      a17 task "Harbor permit renewal" · 384x388 · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · 384x388 · due 2026-09-20 · 17w

## reply
Created the Priya panel with non-overlapping contents and the delivery task due 2026-09-19. Replied in chat naming **Parser notes** and **Tide data format**. Harbor remains unchanged.

Hardest step was incorporating Priya’s follow-up about sensor quotes. The gather behavior was slightly unclear, but it correctly added the related sensor task without duplicating the chat.

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