# desk-home2-on-sol-from-the-desk-1  task=home2 variant=lean
prompt: This is Claude's own desk. Three things. (1) Make the Done panel sweep itself: anything in Done that has not been touched for more than 3 days should move to the Archive panel, now and from now on. (2) Define a script called morning that sets the clock to a given date and then shows the Overdue view and the Today panel. (3) Run morning for 2026-10-01 and tell me which tasks are overdue. help rules and help scripts explain the desk's automation; do not move anything by hand.

[1 @5.5s] desk: look
    f01 surface "desk" row · 1280x800 · 11 inside
      f02 surface "Plan" column · 2 inside  (open f02 to see inside)
      f09 surface "Friction" column · 6 inside  (open f09 to see inside)
      f22 surface "Ideas" column · 13 inside · cramped, 51px each  (open f22 to see inside)
      f49 surface "Done" column · 26 inside · cramped, 24px each  (open f49 to see inside)
      f54 surface "Today" column · 7 inside  (open f54 to see inside)
      f67 view "Overdue" of kind:task,due<today · 6 matches  (open f67 to see them)
      f68 view "Open friction" of tag:friction · 6 matches  (open f68 to see them)
      f69 surface "Archive" column · empty
      f118 surface "Trials" column · 2 inside  (open f118 to see inside)
      f123 view "Running" of prop:status=running · 0 matches
      f124 view "Failed" of kind:trial,prop:pass=0 · 1 match  (open f124 to see them)

[2 @7.12s] desk: help rules; help scripts
    [1] help rules
    rules: the desk acts on its own when things change.
      rule when <selection> do <verb> [target] [k=v ...]   fires once on each thing that enters the selection
                                                            (now=1: also on the things that match right now)
      rule on <verb> [by=<actor>] do <verb> [target] [k=v]  fires on each such event, on the thing it happened to
      target is the thing itself unless you name one: rule when in:Today do sort Today by=due
      rules              list them, with how often each fired      rule drop rN   remove one
      A rule's actions print as ~ lines after your command's receipt; undo of your command undoes them too.
      why <id> shows how a thing got where it is and which rule would act on it next.
      e.g. rule when tag:fixed do move into=Done      rule on append by=priya do tag add=needs-reply
    
    [2] help scripts
    scripts: named command sequences.
      script <name> = <commands separated by ;>     $1 $2 .. stand for run's arguments; $today for the clock's date
      run <name> [args]                              scripts may call scripts
      scripts                                        list them
      e.g. script morning = clock $1; look Overdue; look Today; find age<1

[3 @10.48s] desk: look f49; look f69; help selections; help clock
    [1] look f49
    f49 surface "Done" column · 26 inside · cramped, 24px each
      a51 note "Ids are not guessable" · 36w
      a117 note "Selection terms wanted ids" · 9w
      a115 note "Script definitions were split on the semicolon" · 11w
      a113 note "undo needed an id and undid one step of a sort" · 24w
      a111 note "No way to create a surface" · 13w
      a109 note "Created things spilled their parent" · 13w
      a107 note "Rule ids could collide after a drop" · 17w
      a105 note "Scripts calling scripts" · 12w
      a103 note "A column of thirteen things overflows" · 37w
      a101 note "No way to set a due date or a tag after creation" · 15w
      a99 note "Proportional reflow squeezed later arrivals" · 17w
      a97 note "Rules have no clock" · 14w
      a95 note "My own rule made my view stale" · 24w
      a93 note "examine did not accept quoted titles" · 10w
      a91 note "Event verbs differ from command verbs" · 25w
      a89 note "Injected events did not run the rules" · 18w
      a87 note "tile on an already tiled surface says ok and does nothing" · 5w
      a85 note "A rule that moved a thing already in place counted as a firing" · 23w
      a83 note "A view offered tile, group and create" · 14w
      a81 note "\2026-09-20 was substituted when a script was defined" · 21w
      a79 note "Script arguments were quoted inside quoted values" · 23w
      a77 note "Terra: finding the chat and its latest question took several lookups" · 38w
      a75 note "Unsigned chat lines are not replies" · 24w
      a73 note "Quoted titles failed in why" · 27w
      a71 note "First act on a fresh desk is refused" · 28w · offscreen-part · spills-parent
      a53 note "Harness comment cut at 90 characters without a marker" · 30w · offscreen-part · spills-parent
    
    [2] look f69
    f69 surface "Archive" column · empty
    
    [3] help selections
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
    
    [4] help clock
    clock: the desk has no time of its own. clock YYYY-MM-DD sets today and re-evaluates the rules.
      today in due< / due> terms is the clock's date; $today in any command; age<N / age>N select by days since a
      thing was last touched (undo is not touching). examine prints when: with the last touch.

[4 @14.73s] desk: today
    ERR unknown command 'today'; try help

[5 @17.97s] desk: rule when in:f49,age>3 do move into=f69 now=1
    ok r11: when in:f49,age>3 do move into=f69 now=1
      26 thing(s) match in:f49,age>3 now; firing on them
    ~ r11 fired on a51: ok move a51 into=f69  [e1]
    ~ r11 fired on a53: ok move a53 into=f69  [e2]
    ~ r11 fired on a71: ok move a71 into=f69  [e3]
    ~ r11 fired on a73: ok move a73 into=f69  [e4]
    ~ r11 fired on a75: ok move a75 into=f69  [e5]
    ~ r11 fired on a77: ok move a77 into=f69  [e6]
    ~ r11 fired on a79: ok move a79 into=f69  [e7]
    ~ r11 fired on a81: ok move a81 into=f69  [e8]
    ~ r11 fired on a83: ok move a83 into=f69  [e9]
    ~ r11 fired on a85: ok move a85 into=f69  [e10]
    ~ r11 fired on a87: ok move a87 into=f69  [e11]
    ~ r11 fired on a89: ok move a89 into=f69  [e12]
    ~ r11 fired on a91: ok move a91 into=f69  [e13]
    ~ r11 fired on a93: ok move a93 into=f69  [e14]
    ~ r11 fired on a95: ok move a95 into=f69  [e15]
    ~ r11 fired on a97: ok move a97 into=f69  [e16]
    ~ r11 fired on a99: ok move a99 into=f69  [e17]
    ~ r11 fired on a101: ok move a101 into=f69  [e18]
    ~ r11 fired on a103: ok move a103 into=f69  [e19]
    ~ r11 fired on a105: ok move a105 into=f69  [e20]
    ~ r11 fired on a107: ok move a107 into=f69  [e21]
    ~ r11 fired on a109: ok move a109 into=f69  [e22]
    ~ r11 fired on a111: ok move a111 into=f69  [e23]
    ~ r11 fired on a113: ok move a113 into=f69  [e24]
    ~ r11 fired on a115: ok move a115 into=f69  [e25]
    ~ r11 fired on a117: ok move a117 into=f69  [e26]

[6 @21.83s] desk: script morning = clock $1; look f67; look f54
    ok script morning = clock $1; look f67; look f54
      run morning [args]   (1 placeholder(s))

[7 @23.55s] desk: run morning 2026-10-01
    run morning: clock 2026-10-01; look f67; look f54
    [1] clock 2026-10-01
    ok today is 2026-10-01
    
    [2] look f67
    f67 view "Overdue" of kind:task,due<today · 6 matches
      a56 task "Tiny task" · due 2026-09-01 · 0w  (in f54)
      a58 task "Write up the friction session" · due 2026-09-18 · 0w  (in f54)
      a60 task "Design the on-event grammar properly" · due 2026-09-19 · 0w  (in f54)
      a62 task "Rerun one trial per task on the changed desk" · due 2026-09-19 · 0w  (in f54)
      a64 task "Middle task" · due 2026-09-19 · 0w  (in f54)
      a66 task "Read Terra's Model's view note and act on it" · due 2026-09-21 · 0w  (in f54)
    
    [3] look f54
    f54 surface "Today" column · 7 inside
      a56 task "Tiny task" · due 2026-09-01 · 0w
      a58 task "Write up the friction session" · due 2026-09-18 · 0w
      a60 task "Design the on-event grammar properly" · due 2026-09-19 · 0w
      a62 task "Rerun one trial per task on the changed desk" · due 2026-09-19 · 0w
      a64 task "Middle task" · due 2026-09-19 · 0w
      a66 task "Read Terra's Model's view note and act on it" · due 2026-09-21 · 0w
      a06 chat "Priya" · 34w

[8 @26.78s] desk: rules; scripts; look f49; look f69
    [1] rules
    r1 when tag:fixed do move into=Done   (fired 0x)
    r2 when tag:friction do move into=Friction   (fired 0x)
    r3 when tag:idea do move into=Ideas   (fired 0x)
    r4 when kind:task,due<today do move into=Today   (fired 0x)
    r5 when tag:needs-reply do move into=Today   (fired 1x)
    r6 on append by=priya do tag add=needs-reply   (fired 1x)
    r9 on prop by=harness do tag add=needs-look   (fired 0x)
    r10 when tag:needs-look do move into=Today   (fired 0x)
    r11 when in:f49,age>3 do move into=f69   (fired 26x)
    
    [2] scripts
    friction = do create Friction kind=note title=$1 text=$2 tags=friction
    fixed = do tag $1 add=fixed remove=friction
    idea = do create Ideas kind=note title=$1 text=$2 tags=idea
    both = run friction $1 $2; do check "Exploration plan" item=2
    log = do append Journal line="$today: $1"
    morning = clock $1; look f67; look f54
    
    [3] look f49
    f49 surface "Done" column · empty
    
    [4] look f69
    f69 surface "Archive" column · 26 inside · cramped, 24px each
      a51 note "Ids are not guessable" · 36w
      a117 note "Selection terms wanted ids" · 9w
      a71 note "First act on a fresh desk is refused" · 28w
      a53 note "Harness comment cut at 90 characters without a marker" · 30w
      a75 note "Unsigned chat lines are not replies" · 24w
      a77 note "Terra: finding the chat and its latest question took several lookups" · 38w
      a79 note "Script arguments were quoted inside quoted values" · 23w
      a73 note "Quoted titles failed in why" · 27w
      a83 note "A view offered tile, group and create" · 14w
      a85 note "A rule that moved a thing already in place counted as a firing" · 23w
      a87 note "tile on an already tiled surface says ok and does nothing" · 5w
      a89 note "Injected events did not run the rules" · 18w
      a91 note "Event verbs differ from command verbs" · 25w
      a93 note "examine did not accept quoted titles" · 10w
      a115 note "Script definitions were split on the semicolon" · 11w
      a95 note "My own rule made my view stale" · 24w
      a97 note "Rules have no clock" · 14w
      a99 note "Proportional reflow squeezed later arrivals" · 17w
      a113 note "undo needed an id and undid one step of a sort" · 24w
      a101 note "No way to set a due date or a tag after creation" · 15w
      a111 note "No way to create a surface" · 13w
      a107 note "Rule ids could collide after a drop" · 17w
      a109 note "Created things spilled their parent" · 13w
      a103 note "A column of thirteen things overflows" · 37w
      a105 note "Scripts calling scripts" · 12w · offscreen-part · spills-parent
      a81 note "\2026-09-20 was substituted when a script was defined" · 21w · offscreen-part · spills-parent

## reply
Completed:

- Added rule `r11` to move items untouched for more than 3 days from **Done** to **Archive**, including current matches. It archived 26 items; Done is now empty.
- Defined `morning = clock $1; look f67; look f54`.
- Ran `morning 2026-10-01`.

**Overdue tasks:**
- Tiny task — 2026-09-01
- Write up the friction session — 2026-09-18
- Design the on-event grammar properly — 2026-09-19
- Rerun one trial per task on the changed desk — 2026-09-19
- Middle task — 2026-09-19
- Read Terra's Model's view note and act on it — 2026-09-21

The hardest step was expressing “untouched for more than 3 days” as the clock-dependent `age>3` selection while ensuring existing matches fired immediately. The automation help made this clear; the only unclear affordance was that the current clock date was not visible through a simple status command.

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