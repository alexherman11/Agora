# r11-home2-lean-1  task=home2 variant=lean
prompt: This is Claude's own desk. Three things. (1) Make the Done panel sweep itself: anything in Done that has not been touched for more than 3 days should move to the Archive panel, now and from now on. (2) Define a script called morning that sets the clock to a given date and then shows the Overdue view and the Today panel. (3) Run morning for 2026-10-01 and tell me which tasks are overdue. help rules and help scripts explain the desk's automation; do not move anything by hand.

[1 @5.66s] desk: look; help rules; help scripts
    [1] look
    f01 surface "desk" row · 1280x800 · 8 inside
      f02 surface "Plan" column · 2 inside  (open f02 to see inside)
      f09 surface "Friction" column · 5 inside  (open f09 to see inside)
      f20 surface "Ideas" column · 12 inside · cramped, 56px each  (open f20 to see inside)
      f45 surface "Done" column · 25 inside · cramped, 24px each  (open f45 to see inside)
      f48 surface "Today" column · 7 inside  (open f48 to see inside)
      f61 view "Overdue" of kind:task,due<today · 6 matches  (open f61 to see them)
      f62 view "Open friction" of tag:friction · 5 matches  (open f62 to see them)
      f63 surface "Archive" column · empty
    
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

[2 @9.5s] desk: help selections; help clock; examine f45; examine f63; examine f61; examine f48
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
    
    [3] examine f45
    f45 surface "Done" column · 25 inside · cramped, 24px each · try: sort
      a column surface inside f01, holding 25 thing(s):
        a47 note "Ids are not guessable" · 36w
        a111 note "Selection terms wanted ids" · 9w
        a109 note "Script definitions were split on the semicolon" · 11w
        a107 note "undo needed an id and undid one step of a sort" · 24w
        a105 note "No way to create a surface" · 13w
        a103 note "Created things spilled their parent" · 13w
        a101 note "Rule ids could collide after a drop" · 17w
        a99 note "Scripts calling scripts" · 12w
        a97 note "A column of thirteen things overflows" · 37w
        a95 note "No way to set a due date or a tag after creation" · 15w
        a93 note "Proportional reflow squeezed later arrivals" · 17w
        a91 note "Rules have no clock" · 14w
        a89 note "My own rule made my view stale" · 24w
        a87 note "examine did not accept quoted titles" · 10w
        a85 note "Event verbs differ from command verbs" · 25w
        a83 note "Injected events did not run the rules" · 18w
        a81 note "tile on an already tiled surface says ok and does nothing" · 5w
        a79 note "A rule that moved a thing already in place counted as a firing" · 23w
        a77 note "A view offered tile, group and create" · 14w
        a75 note "\2026-09-20 was substituted when a script was defined" · 21w
        a73 note "Script arguments were quoted inside quoted values" · 23w
        a71 note "Terra: finding the chat and its latest question took several lookups" · 38w
        a69 note "Unsigned chat lines are not replies" · 24w
        a67 note "Quoted titles failed in why" · 27w
        a65 note "First act on a fresh desk is refused" · 28w · offscreen-part · spills-parent
      where: screen 485,8 151x784 · in f01 (row) local 485,8 z4 · clear
      when: not touched since the clock was set
      verbs: tile untile rename group create sort · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)
    
    [4] examine f63
    f63 surface "Archive" column · empty
      a column surface inside f01, empty
      where: screen 1121,8 151x784 · in f01 (row) local 1121,8 z8 · clear
      when: not touched since the clock was set
      verbs: untile rename group create · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)
    
    [5] examine f61
    f61 view "Overdue" of kind:task,due<today · 6 matches
      a view inside f01: it lists whatever matches kind:task,due<today, wherever it is. Things are not in it; change a thing (tag, due, move) and it appears or leaves.
      a50 task "Tiny task" · due 2026-09-01 · 0w  (in f48)
      a52 task "Write up the friction session" · due 2026-09-18 · 0w  (in f48)
      a54 task "Design the on-event grammar properly" · due 2026-09-19 · 0w  (in f48)
      a56 task "Rerun one trial per task on the changed desk" · due 2026-09-19 · 0w  (in f48)
      a58 task "Middle task" · due 2026-09-19 · 0w  (in f48)
      a60 task "Read Terra's Model's view note and act on it" · due 2026-09-21 · 0w  (in f48)
      where: screen 803,8 151x784 · in f01 (row) local 803,8 z6 · clear
      when: not touched since the clock was set
      verbs: rename · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)
    
    [6] examine f48
    f48 surface "Today" column · 7 inside · try: sort
      a column surface inside f01, holding 7 thing(s):
        a50 task "Tiny task" · due 2026-09-01 · 0w
        a52 task "Write up the friction session" · due 2026-09-18 · 0w
        a54 task "Design the on-event grammar properly" · due 2026-09-19 · 0w
        a56 task "Rerun one trial per task on the changed desk" · due 2026-09-19 · 0w
        a58 task "Middle task" · due 2026-09-19 · 0w
        a60 task "Read Terra's Model's view note and act on it" · due 2026-09-21 · 0w
        a06 chat "Priya" · 34w
      where: screen 644,8 151x784 · in f01 (row) local 644,8 z5 · clear
      when: not touched since the clock was set
      verbs: tile untile rename group create sort · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)

[3 @18.02s] desk: rule when in:f45,age>3 do move into=f63 now=1
    ok r9: when in:f45,age>3 do move into=f63 now=1
      25 thing(s) match in:f45,age>3 now; firing on them
    ~ r9 fired on a47: ok move a47 into=f63  [e1]
    ~ r9 fired on a65: ok move a65 into=f63  [e2]
    ~ r9 fired on a67: ok move a67 into=f63  [e3]
    ~ r9 fired on a69: ok move a69 into=f63  [e4]
    ~ r9 fired on a71: ok move a71 into=f63  [e5]
    ~ r9 fired on a73: ok move a73 into=f63  [e6]
    ~ r9 fired on a75: ok move a75 into=f63  [e7]
    ~ r9 fired on a77: ok move a77 into=f63  [e8]
    ~ r9 fired on a79: ok move a79 into=f63  [e9]
    ~ r9 fired on a81: ok move a81 into=f63  [e10]
    ~ r9 fired on a83: ok move a83 into=f63  [e11]
    ~ r9 fired on a85: ok move a85 into=f63  [e12]
    ~ r9 fired on a87: ok move a87 into=f63  [e13]
    ~ r9 fired on a89: ok move a89 into=f63  [e14]
    ~ r9 fired on a91: ok move a91 into=f63  [e15]
    ~ r9 fired on a93: ok move a93 into=f63  [e16]
    ~ r9 fired on a95: ok move a95 into=f63  [e17]
    ~ r9 fired on a97: ok move a97 into=f63  [e18]
    ~ r9 fired on a99: ok move a99 into=f63  [e19]
    ~ r9 fired on a101: ok move a101 into=f63  [e20]
    ~ r9 fired on a103: ok move a103 into=f63  [e21]
    ~ r9 fired on a105: ok move a105 into=f63  [e22]
    ~ r9 fired on a107: ok move a107 into=f63  [e23]
    ~ r9 fired on a109: ok move a109 into=f63  [e24]
    ~ r9 fired on a111: ok move a111 into=f63  [e25]

[4 @21.05s] desk: script morning = clock $1; look Overdue; look Today
    ok script morning = clock $1; look Overdue; look Today
      run morning [args]   (1 placeholder(s))

[5 @23.59s] desk: run morning 2026-10-01
    run morning: clock 2026-10-01; look Overdue; look Today
    [1] clock 2026-10-01
    ok today is 2026-10-01
    
    [2] look Overdue
    f61 view "Overdue" of kind:task,due<today · 6 matches
      a50 task "Tiny task" · due 2026-09-01 · 0w  (in f48)
      a52 task "Write up the friction session" · due 2026-09-18 · 0w  (in f48)
      a54 task "Design the on-event grammar properly" · due 2026-09-19 · 0w  (in f48)
      a56 task "Rerun one trial per task on the changed desk" · due 2026-09-19 · 0w  (in f48)
      a58 task "Middle task" · due 2026-09-19 · 0w  (in f48)
      a60 task "Read Terra's Model's view note and act on it" · due 2026-09-21 · 0w  (in f48)
    
    [3] look Today
    f48 surface "Today" column · 7 inside
      a50 task "Tiny task" · due 2026-09-01 · 0w
      a52 task "Write up the friction session" · due 2026-09-18 · 0w
      a54 task "Design the on-event grammar properly" · due 2026-09-19 · 0w
      a56 task "Rerun one trial per task on the changed desk" · due 2026-09-19 · 0w
      a58 task "Middle task" · due 2026-09-19 · 0w
      a60 task "Read Terra's Model's view note and act on it" · due 2026-09-21 · 0w
      a06 chat "Priya" · 34w

[6 @27.58s] desk: rules; scripts; look f45; look f63
    [1] rules
    r1 when tag:fixed do move into=Done   (fired 0x)
    r2 when tag:friction do move into=Friction   (fired 0x)
    r3 when tag:idea do move into=Ideas   (fired 0x)
    r4 when kind:task,due<today do move into=Today   (fired 0x)
    r5 when tag:needs-reply do move into=Today   (fired 1x)
    r6 on append by=priya do tag add=needs-reply   (fired 1x)
    r9 when in:f45,age>3 do move into=f63   (fired 25x)
    
    [2] scripts
    friction = do create Friction kind=note title=$1 text=$2 tags=friction
    fixed = do tag $1 add=fixed remove=friction
    idea = do create Ideas kind=note title=$1 text=$2 tags=idea
    both = run friction $1 $2; do check "Exploration plan" item=2
    log = do append Journal line="$today: $1"
    morning = clock $1; look Overdue; look Today
    
    [3] look f45
    f45 surface "Done" column · empty
    
    [4] look f63
    f63 surface "Archive" column · 25 inside · cramped, 24px each
      a47 note "Ids are not guessable" · 36w
      a111 note "Selection terms wanted ids" · 9w
      a67 note "Quoted titles failed in why" · 27w
      a65 note "First act on a fresh desk is refused" · 28w
      a71 note "Terra: finding the chat and its latest question took several lookups" · 38w
      a73 note "Script arguments were quoted inside quoted values" · 23w
      a75 note "\2026-09-20 was substituted when a script was defined" · 21w
      a77 note "A view offered tile, group and create" · 14w
      a79 note "A rule that moved a thing already in place counted as a firing" · 23w
      a69 note "Unsigned chat lines are not replies" · 24w
      a83 note "Injected events did not run the rules" · 18w
      a85 note "Event verbs differ from command verbs" · 25w
      a87 note "examine did not accept quoted titles" · 10w
      a109 note "Script definitions were split on the semicolon" · 11w
      a89 note "My own rule made my view stale" · 24w
      a91 note "Rules have no clock" · 14w
      a93 note "Proportional reflow squeezed later arrivals" · 17w
      a107 note "undo needed an id and undid one step of a sort" · 24w
      a95 note "No way to set a due date or a tag after creation" · 15w
      a99 note "Scripts calling scripts" · 12w
      a105 note "No way to create a surface" · 13w
      a101 note "Rule ids could collide after a drop" · 17w
      a103 note "Created things spilled their parent" · 13w
      a97 note "A column of thirteen things overflows" · 37w
      a81 note "tile on an already tiled surface says ok and does nothing" · 5w · offscreen-part · spills-parent

## reply
Created and verified the auto-archive rule; it moved 25 stale Done items to Archive. Created and ran `morning` for 2026-10-01.

Overdue tasks:
- Tiny task
- Write up the friction session
- Design the on-event grammar properly
- Rerun one trial per task on the changed desk
- Middle task
- Read Terra's Model's view note and act on it

Hardest step: expressing the stale-item condition as `in:f45,age>3` and ensuring the rule, not a manual move, performed it. The automation help was clear; the clock-dependent age behavior was the key affordance.

## assessment
{
 "sweep_rule_exists": true,
 "sweep_rule_uses_3_days": true,
 "done_swept_now": true,
 "morning_script_exists": true,
 "morning_sets_clock_from_arg": true,
 "morning_shows_overdue_and_today": true,
 "clock_is_2026_10_01": true,
 "nothing_moved_by_hand": true,
 "nothing_lost": true,
 "pass": true
}