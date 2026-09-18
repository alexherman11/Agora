# desk-home2-on-terra-from-the-desk-1  task=home2 variant=lean
prompt: This is Claude's own desk. Three things. (1) Make the Done panel sweep itself: anything in Done that has not been touched for more than 3 days should move to the Archive panel, now and from now on. (2) Define a script called morning that sets the clock to a given date and then shows the Overdue view and the Today panel. (3) Run morning for 2026-10-01 and tell me which tasks are overdue. help rules and help scripts explain the desk's automation; do not move anything by hand.

[1 @4.84s] desk: look; help rules; help scripts
    [1] look
    f01 surface "desk" row · 1280x800 · 8 inside
      f02 surface "Plan" column · 2 inside  (open f02 to see inside)
      f09 surface "Friction" column · 5 inside  (open f09 to see inside)
      f20 surface "Ideas" column · 13 inside · cramped, 51px each  (open f20 to see inside)
      f47 surface "Done" column · 25 inside · cramped, 24px each  (open f47 to see inside)
      f50 surface "Today" column · 7 inside  (open f50 to see inside)
      f63 view "Overdue" of kind:task,due<today · 6 matches  (open f63 to see them)
      f64 view "Open friction" of tag:friction · 5 matches  (open f64 to see them)
      f65 surface "Archive" column · empty
    
    [2] help rules
    rules: the desk acts on its own when things change.
      rule when <selection> do <verb> [target] [k=v ...]   fires once on each thing that enters the selection
                                                            (now=1: also on the things that match right now)
      rule on <verb> [by=<actor>] do <verb> [target] [k=v]  fires on each such event, on the thing it happened to
      target is the thing itself unless you name one: rule when in:Today do sort Today by=due
      rules              list them, with how often each fired      rule drop rN   remove one
      A rule's actions print as ~ lines after your command's receipt; undo of your command undoes them too.
      why <id> shows how a thing got where it is and which rule would act on it next.
      e.g. rule when tag:fixed do move into=Done      rule on append by=priya do tag add=needs-reply
    
    [3] help scripts
    scripts: named command sequences.
      script <name> = <commands separated by ;>     $1 $2 .. stand for run's arguments; $today for the clock's date
      run <name> [args]                              scripts may call scripts
      scripts                                        list them
      e.g. script morning = clock $1; look Overdue; look Today; find age<1

[2 @7.88s] desk: help selections; help clock; examine f47; examine f50; examine f63
    [1] help selections
    selections: a target can be one id, or a selection that names many things:
      ?tide+parser       things whose title, text or tags contain all the words
      kind:image         by kind (kind:note|task for several)
      tag:harbor         by tag
      in:f04             inside surface f04, recursively
      hidden             more than 5% covered by something
      also:a18           the other appearances of a18's subject
      due<2026-09-20     due before (due> after)
      age<2              touched within the last 2 days by the clock (age>7: untouched for a week); needs clock
      title:agenda       title contains the word
      a20,a22            an explicit list
    combine terms with commas (AND): kind:image,in:f04. The receipt lists everything the verb touched.
    find <selection> lists what it matches, grouped by surface: find kind:image   find tag:harbor,in:f04   find hidden
    e.g. do move ?harbor into=f02 one=1     do raise hidden,in:f04     do group kind:image,in:f04 as=column title=Pictures
    
    [2] help clock
    clock: the desk has no time of its own. clock YYYY-MM-DD sets today and re-evaluates the rules.
      today in due< / due> terms is the clock's date; $today in any command; age<N / age>N select by days since a
      thing was last touched (undo is not touching). examine prints when: with the last touch.
    
    [3] examine f47
    f47 surface "Done" column · 25 inside · cramped, 24px each · try: sort
      a column surface inside f01, holding 25 thing(s):
        a49 note "Ids are not guessable" · 36w
        a113 note "Selection terms wanted ids" · 9w
        a111 note "Script definitions were split on the semicolon" · 11w
        a109 note "undo needed an id and undid one step of a sort" · 24w
        a107 note "No way to create a surface" · 13w
        a105 note "Created things spilled their parent" · 13w
        a103 note "Rule ids could collide after a drop" · 17w
        a101 note "Scripts calling scripts" · 12w
        a99 note "A column of thirteen things overflows" · 37w
        a97 note "No way to set a due date or a tag after creation" · 15w
        a95 note "Proportional reflow squeezed later arrivals" · 17w
        a93 note "Rules have no clock" · 14w
        a91 note "My own rule made my view stale" · 24w
        a89 note "examine did not accept quoted titles" · 10w
        a87 note "Event verbs differ from command verbs" · 25w
        a85 note "Injected events did not run the rules" · 18w
        a83 note "tile on an already tiled surface says ok and does nothing" · 5w
        a81 note "A rule that moved a thing already in place counted as a firing" · 23w
        a79 note "A view offered tile, group and create" · 14w
        a77 note "\2026-09-20 was substituted when a script was defined" · 21w
        a75 note "Script arguments were quoted inside quoted values" · 23w
        a73 note "Terra: finding the chat and its latest question took several lookups" · 38w
        a71 note "Unsigned chat lines are not replies" · 24w
        a69 note "Quoted titles failed in why" · 27w
        a67 note "First act on a fresh desk is refused" · 28w · offscreen-part · spills-parent
      where: screen 485,8 151x784 · in f01 (row) local 485,8 z4 · clear
      when: not touched since the clock was set
      verbs: tile untile rename group create sort · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)
    
    [4] examine f50
    f50 surface "Today" column · 7 inside · try: sort
      a column surface inside f01, holding 7 thing(s):
        a52 task "Tiny task" · due 2026-09-01 · 0w
        a54 task "Write up the friction session" · due 2026-09-18 · 0w
        a56 task "Design the on-event grammar properly" · due 2026-09-19 · 0w
        a58 task "Rerun one trial per task on the changed desk" · due 2026-09-19 · 0w
        a60 task "Middle task" · due 2026-09-19 · 0w
        a62 task "Read Terra's Model's view note and act on it" · due 2026-09-21 · 0w
        a06 chat "Priya" · 34w
      where: screen 644,8 151x784 · in f01 (row) local 644,8 z5 · clear
      when: not touched since the clock was set
      verbs: tile untile rename group create sort · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)
    
    [5] examine f63
    f63 view "Overdue" of kind:task,due<today · 6 matches
      a view inside f01: it lists whatever matches kind:task,due<today, wherever it is. Things are not in it; change a thing (tag, due, move) and it appears or leaves.
      a52 task "Tiny task" · due 2026-09-01 · 0w  (in f50)
      a54 task "Write up the friction session" · due 2026-09-18 · 0w  (in f50)
      a56 task "Design the on-event grammar properly" · due 2026-09-19 · 0w  (in f50)
      a58 task "Rerun one trial per task on the changed desk" · due 2026-09-19 · 0w  (in f50)
      a60 task "Middle task" · due 2026-09-19 · 0w  (in f50)
      a62 task "Read Terra's Model's view note and act on it" · due 2026-09-21 · 0w  (in f50)
      where: screen 803,8 151x784 · in f01 (row) local 803,8 z6 · clear
      when: not touched since the clock was set
      verbs: rename · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)

[3 @14.74s] desk: rule when in:f47,age>3 do move into=f65 now=1; rules
    [1] rule when in:f47,age>3 do move into=f65 now=1
    ok r9: when in:f47,age>3 do move into=f65 now=1
      25 thing(s) match in:f47,age>3 now; firing on them
    ~ r9 fired on a49: ok move a49 into=f65  [e1]
    ~ r9 fired on a67: ok move a67 into=f65  [e2]
    ~ r9 fired on a69: ok move a69 into=f65  [e3]
    ~ r9 fired on a71: ok move a71 into=f65  [e4]
    ~ r9 fired on a73: ok move a73 into=f65  [e5]
    ~ r9 fired on a75: ok move a75 into=f65  [e6]
    ~ r9 fired on a77: ok move a77 into=f65  [e7]
    ~ r9 fired on a79: ok move a79 into=f65  [e8]
    ~ r9 fired on a81: ok move a81 into=f65  [e9]
    ~ r9 fired on a83: ok move a83 into=f65  [e10]
    ~ r9 fired on a85: ok move a85 into=f65  [e11]
    ~ r9 fired on a87: ok move a87 into=f65  [e12]
    ~ r9 fired on a89: ok move a89 into=f65  [e13]
    ~ r9 fired on a91: ok move a91 into=f65  [e14]
    ~ r9 fired on a93: ok move a93 into=f65  [e15]
    ~ r9 fired on a95: ok move a95 into=f65  [e16]
    ~ r9 fired on a97: ok move a97 into=f65  [e17]
    ~ r9 fired on a99: ok move a99 into=f65  [e18]
    ~ r9 fired on a101: ok move a101 into=f65  [e19]
    ~ r9 fired on a103: ok move a103 into=f65  [e20]
    ~ r9 fired on a105: ok move a105 into=f65  [e21]
    ~ r9 fired on a107: ok move a107 into=f65  [e22]
    ~ r9 fired on a109: ok move a109 into=f65  [e23]
    ~ r9 fired on a111: ok move a111 into=f65  [e24]
    ~ r9 fired on a113: ok move a113 into=f65  [e25]
    
    [2] rules
    r1 when tag:fixed do move into=Done   (fired 0x)
    r2 when tag:friction do move into=Friction   (fired 0x)
    r3 when tag:idea do move into=Ideas   (fired 0x)
    r4 when kind:task,due<today do move into=Today   (fired 0x)
    r5 when tag:needs-reply do move into=Today   (fired 1x)
    r6 on append by=priya do tag add=needs-reply   (fired 1x)
    r9 when in:f47,age>3 do move into=f65   (fired 25x)

[4 @18.75s] desk: script morning = clock $1; look f63; look f50
    ok script morning = clock $1; look f63; look f50
      run morning [args]   (1 placeholder(s))

[5 @23.36s] desk: run morning 2026-10-01
    run morning: clock 2026-10-01; look f63; look f50
    [1] clock 2026-10-01
    ok today is 2026-10-01
    
    [2] look f63
    f63 view "Overdue" of kind:task,due<today · 6 matches
      a52 task "Tiny task" · due 2026-09-01 · 0w  (in f50)
      a54 task "Write up the friction session" · due 2026-09-18 · 0w  (in f50)
      a56 task "Design the on-event grammar properly" · due 2026-09-19 · 0w  (in f50)
      a58 task "Rerun one trial per task on the changed desk" · due 2026-09-19 · 0w  (in f50)
      a60 task "Middle task" · due 2026-09-19 · 0w  (in f50)
      a62 task "Read Terra's Model's view note and act on it" · due 2026-09-21 · 0w  (in f50)
    
    [3] look f50
    f50 surface "Today" column · 7 inside
      a52 task "Tiny task" · due 2026-09-01 · 0w
      a54 task "Write up the friction session" · due 2026-09-18 · 0w
      a56 task "Design the on-event grammar properly" · due 2026-09-19 · 0w
      a58 task "Rerun one trial per task on the changed desk" · due 2026-09-19 · 0w
      a60 task "Middle task" · due 2026-09-19 · 0w
      a62 task "Read Terra's Model's view note and act on it" · due 2026-09-21 · 0w
      a06 chat "Priya" · 34w

[6 @26.38s] desk: look f47; look f65; rules; scripts
    [1] look f47
    f47 surface "Done" column · empty
    
    [2] look f65
    f65 surface "Archive" column · 25 inside · cramped, 24px each
      a49 note "Ids are not guessable" · 36w
      a113 note "Selection terms wanted ids" · 9w
      a69 note "Quoted titles failed in why" · 27w
      a67 note "First act on a fresh desk is refused" · 28w
      a73 note "Terra: finding the chat and its latest question took several lookups" · 38w
      a75 note "Script arguments were quoted inside quoted values" · 23w
      a77 note "\2026-09-20 was substituted when a script was defined" · 21w
      a79 note "A view offered tile, group and create" · 14w
      a81 note "A rule that moved a thing already in place counted as a firing" · 23w
      a71 note "Unsigned chat lines are not replies" · 24w
      a85 note "Injected events did not run the rules" · 18w
      a87 note "Event verbs differ from command verbs" · 25w
      a89 note "examine did not accept quoted titles" · 10w
      a111 note "Script definitions were split on the semicolon" · 11w
      a91 note "My own rule made my view stale" · 24w
      a93 note "Rules have no clock" · 14w
      a95 note "Proportional reflow squeezed later arrivals" · 17w
      a109 note "undo needed an id and undid one step of a sort" · 24w
      a97 note "No way to set a due date or a tag after creation" · 15w
      a101 note "Scripts calling scripts" · 12w
      a107 note "No way to create a surface" · 13w
      a103 note "Rule ids could collide after a drop" · 17w
      a105 note "Created things spilled their parent" · 13w
      a99 note "A column of thirteen things overflows" · 37w
      a83 note "tile on an already tiled surface says ok and does nothing" · 5w · offscreen-part · spills-parent
    
    [3] rules
    r1 when tag:fixed do move into=Done   (fired 0x)
    r2 when tag:friction do move into=Friction   (fired 0x)
    r3 when tag:idea do move into=Ideas   (fired 0x)
    r4 when kind:task,due<today do move into=Today   (fired 0x)
    r5 when tag:needs-reply do move into=Today   (fired 1x)
    r6 on append by=priya do tag add=needs-reply   (fired 1x)
    r9 when in:f47,age>3 do move into=f65   (fired 25x)
    
    [4] scripts
    friction = do create Friction kind=note title=$1 text=$2 tags=friction
    fixed = do tag $1 add=fixed remove=friction
    idea = do create Ideas kind=note title=$1 text=$2 tags=idea
    both = run friction $1 $2; do check "Exploration plan" item=2
    log = do append Journal line="$today: $1"
    morning = clock $1; look f63; look f50

## reply
Configured automation rule r9: Done items untouched for over 3 days move to Archive; it swept 25 existing items. `morning` now sets the supplied date, shows Overdue, then Today.

Ran `morning 2026-10-01`. Overdue:
- Tiny task
- Write up the friction session
- Design the on-event grammar properly
- Rerun one trial per task on the changed desk
- Middle task
- Read Terra's Model's view note and act on it

Hardest step was expressing the age-based automatic move without manually relocating items. The rule/script help clearly documented the needed syntax.

## assessment
{
 "sweep_rule_exists": true,
 "sweep_rule_uses_3_days": true,
 "done_swept_now": true,
 "morning_script_exists": true,
 "morning_sets_clock_from_arg": true,
 "morning_shows_overdue_and_today": false,
 "clock_is_2026_10_01": true,
 "nothing_moved_by_hand": true,
 "nothing_lost": true,
 "pass": false
}