# r4-harbor-acme-1  task=harbor variant=acme
prompt: Gather everything about the Harbor project into the Harbor column, soonest due date first. Leave unrelated things where they are, but nothing Harbor-related may be left covered up.

[1 @3.95s] desk: look
    f01 surface "desk" free · 1280x800 · 3 inside
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside · try: sort gather  (open f02 to see inside)
      f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside · try: tidy split  (open f03 to see inside)
      f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside · try: tidy split  (open f04 to see inside)

[2 @5.48s] desk: find Harbor
    find 'Harbor': 5 hit(s)
      a16 note "Harbor kickoff" · 384x388 · due 2026-09-20 · 17w  in f02
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · try: reveal  in f04
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: reveal  in f04
      a17 task "Harbor permit renewal" · 384x388 · due 2026-09-30 · 10w  in f02
      f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside · try: sort gather

[3 @8.64s] desk: look f02 :3
    f02 surface "Harbor" column · 400x800 at 0,0 · 2 inside · try: sort gather
      a17 task "Harbor permit renewal" · 384x388 · due 2026-09-30 · 10w
      a16 note "Harbor kickoff" · 384x388 · due 2026-09-20 · 17w
      verbs: move resize raise lower remove tile untile rename group   (verbs f02 for argument forms)

[4 @8.64s] desk: look f03 :3
    f03 surface "Meeting" free · 840x380 at 420,0 · 3 inside · try: tidy split
      a18 note "Standup agenda" · 380x220 at 20,20 · 10w · also x1 · try: dedupe
      a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27 · try: reveal
      a27 chat "Priya" · 320x160 at 300,200 · 14w
      verbs: move resize raise lower remove tile rename group   (verbs f03 for argument forms)

[5 @8.64s] desk: look f04 :3
    f04 surface "Scratch" free · 840x400 at 420,400 · 7 inside · try: tidy split
      a20 note "Tide data format" · 300x160 at 60,60 · due 2026-09-17 · 16w · hidden by a21,a24 · try: reveal
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25 · try: reveal
      a22 task "Order pier sensors" · 280x140 at 540,30 · due 2026-09-18 · 10w · 67% hidden by a23 · try: reveal
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · try: reveal dedupe
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w
      verbs: move resize raise lower remove tile rename group   (verbs f04 for argument forms)

[6 @12.12s] desk: read a16
    s05 note "Harbor kickoff" · appears at a16 · tags harbor · due 2026-09-20
    ---
    Kickoff for the Harbor project.
    Attendees: Sam, Priya, Alex.
    Decide the pier sensor vendor by the 20th.
    ---

[7 @12.12s] desk: read a17
    s08 task "Harbor permit renewal" · appears at a17 · tags harbor · due 2026-09-30
    ---
    City permit for the Harbor dock expires end of month.
    ---

[8 @12.12s] desk: read a18
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    ---

[9 @12.12s] desk: read a19
    s11 image "whiteboard.jpg" · appears at a19
    ---
    
    ---

[10 @12.14s] desk: read a20
    s07 note "Tide data format" · appears at a20 · tags harbor · due 2026-09-17
    ---
    Harbor tide feed is CSV, one row per 6 minutes. Need a parser before the kickoff.
    ---

[11 @12.14s] desk: read a21
    s12 image "dock-photo.png" · appears at a21
    ---
    
    ---

[12 @12.14s] desk: read a22
    s06 task "Order pier sensors" · appears at a22 · tags harbor · due 2026-09-18
    ---
    Get quotes from two vendors for the Harbor pier sensors.
    ---

[13 @12.14s] desk: read a23
    s09 note "Grocery list" · appears at a23
    ---
    eggs
    rice
    limes
    coffee
    ---

[14 @12.14s] desk: read a24
    s10 note "Standup agenda" · appears at a18, a24
    ---
    1. Yesterday's blockers
    2. Sensor vendor decision
    3. Demo schedule
    ---

[15 @12.14s] desk: read a25
    s13 image "layout-sketch.png" · appears at a25
    ---
    
    ---

[16 @12.14s] desk: read a26
    s14 note "Blog draft" · appears at a26
    ---
    Why we moved the desk to text.
    
    A screen is already a data structure; the problem is notation.
    ---

[17 @12.14s] desk: read a27
    s15 chat "Priya" · appears at a27
    ---
    Priya: can you send the tide parser when it's ready?
    Alex: yes, after kickoff.
    ---

[18 @16.38s] desk: examine a19
    a19 image "whiteboard.jpg" · 400x300 at 420,20 · 20% hidden by a27 · try: reveal
      a image (subject s11) on f03; text begins: (no text)
      where: screen 840,20 400x300 · in f03 (free) local 420,20 z2 · under a27 · 20% hidden
      verbs from image: retitle
      verbs from appearance: fold reveal dedupe
      verbs from thing: move resize raise lower remove
      (help <verb> explains one; do <verb> a19 ... uses it)

[19 @16.38s] desk: examine a21
    a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25 · try: reveal
      a image (subject s12) on f04; text begins: (no text)
      where: screen 440,420 500x340 · in f04 (free) local 20,20 z2 · covers a20 fully, under a24, under a25 · 50% hidden
      verbs from image: retitle
      verbs from appearance: fold reveal dedupe
      verbs from thing: move resize raise lower remove
      (help <verb> explains one; do <verb> a21 ... uses it)

[20 @16.38s] desk: examine a25
    a25 image "layout-sketch.png" · 360x160 at 40,220
      a image (subject s13) on f04; text begins: (no text)
      where: screen 460,620 360x160 · in f04 (free) local 40,220 z6 · covers a21, covers a24
      verbs from image: retitle
      verbs from appearance: fold reveal dedupe
      verbs from thing: move resize raise lower remove
      (help <verb> explains one; do <verb> a25 ... uses it)

[21 @16.38s] desk: examine a27
    a27 chat "Priya" · 320x160 at 300,200 · 14w
      a chat (subject s15) on f03; text begins: Priya: can you send the tide parser when it's ready?
      where: screen 720,200 320x160 · in f03 (free) local 300,200 z3 · covers a18, covers a19
      verbs from text: append retitle rewrite
      verbs from appearance: fold reveal dedupe
      verbs from thing: move resize raise lower remove
      (help <verb> explains one; do <verb> a27 ... uses it)

[22 @16.38s] desk: help gather
    gather  (on: surface; level 3)
      Bring every appearance matching words into this surface (one per subject), then sort if tiled.
      args: words=<text> [by=due|title]
      e.g. do gather f02 words=harbor by=due

[23 @16.38s] desk: help sort
    sort  (on: surface; level 2)
      Reorder the children of a tiled surface.
      args: by=due|title|kind [desc=1]
      e.g. do sort f02 by=due

[24 @16.38s] desk: help reveal
    reveal  (on: appearance; level 2)
      Make this fully visible: bring it to the front (free surface) and nudge it inside its parent.
      e.g. do reveal a22

[25 @16.38s] desk: help move
    move  (on: thing; level 1)
      Put this somewhere else.
      args: into=<surface> | before=<id> | after=<id> | to=<x>,<y> | by=<dx>,<dy>
      e.g. do move a04 into=f02

[26 @22.44s] desk: do gather f02 words=harbor by=due
    ok gather f02 words=harbor by=due  [e1..e6, 6 steps]
      4 subject(s) matched; 2 step(s)
      now: f02 surface "Harbor" column · 400x800 at 0,0 · 4 inside · try: sort gather
      a20 note "Tide data format" · 384x190 · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · 384x190 · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · 384x190 · due 2026-09-20 · 17w
      a17 task "Harbor permit renewal" · 384x190 · due 2026-09-30 · 10w

[27 @25.02s] desk: look f02 :3
    f02 surface "Harbor" column · 400x800 at 0,0 · 4 inside · try: sort gather
      a20 note "Tide data format" · 384x190 · due 2026-09-17 · 16w
      a22 task "Order pier sensors" · 384x190 · due 2026-09-18 · 10w
      a16 note "Harbor kickoff" · 384x190 · due 2026-09-20 · 17w
      a17 task "Harbor permit renewal" · 384x190 · due 2026-09-30 · 10w
      verbs: move resize raise lower remove tile untile rename group   (verbs f02 for argument forms)

[28 @25.03s] desk: look f04 :3
    f04 surface "Scratch" free · 840x400 at 420,400 · 5 inside · try: tidy split
      a21 image "dock-photo.png" · 500x340 at 20,20 · 50% hidden by a24,a25 · try: reveal
      a23 note "Grocery list" · 240x150 at 560,60 · 4w
      a24 note "Standup agenda" · 320x180 at 300,200 · 10w · also x1 · 52% hidden by a25,a26 · try: reveal dedupe
      a25 image "layout-sketch.png" · 360x160 at 40,220
      a26 note "Blog draft" · 300x150 at 520,240 · 18w
      verbs: move resize raise lower remove tile rename group   (verbs f04 for argument forms)

[29 @25.03s] desk: find Harbor
    find 'Harbor': 5 hit(s)
      a16 note "Harbor kickoff" · 384x190 · due 2026-09-20 · 17w  in f02
      a22 task "Order pier sensors" · 384x190 · due 2026-09-18 · 10w  in f02
      a20 note "Tide data format" · 384x190 · due 2026-09-17 · 16w  in f02
      a17 task "Harbor permit renewal" · 384x190 · due 2026-09-30 · 10w  in f02
      f02 surface "Harbor" column · 400x800 at 0,0 · 4 inside · try: sort gather

## reply
Gathered the four Harbor-tagged items into the Harbor column, ordered by due date (Sep 17, 18, 20, 30). Verified no Harbor search results remain elsewhere or covered up.

Hardest step was distinguishing project items from unrelated overlapping Scratch items. The gather-by-keyword affordance made the due-date ordering straightforward.

## assessment
{
 "all_harbor_in_column": true,
 "no_stray_harbor_appearances": true,
 "only_harbor_in_column": true,
 "ordered_by_due": true,
 "nothing_harbor_hidden": true,
 "grocery_survives": true,
 "column_still_tiled": true,
 "pass": true
}