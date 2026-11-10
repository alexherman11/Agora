# A lens about me and about today (juniper-7). The escaped \$today is the only way to write the word into a
# lens today; the third probe writes it the natural way and says what happens.
recorded M3=1

step 1
T do create f01 kind=task title="mine" owner=juniper due=2026-09-24
T do create f01 kind=note title="mine" tags=lens text="h : column\n  a : text \"me=$me\"\n  b : column, of kind:task,prop:owner=$me, each t\nt : text \"$title\", only when $due < \$today\n  w : column, derive end = day-n \$today 8, derive days = days-from \$today $end, over $days, each d, clamp 1\nd : text \"$it.date\""
T do create f01 kind=note title="week" tags=lens text="w : column, derive end = day-n \$today 8, derive days = days-from \$today $end, over $days, each d, clamp 1\nd : text \"$it.date\""
probe binds-everywhere
probe follows-the-clock

step 2
T clock 2026-09-26
probe follows-the-clock
probe writing-leaves-today-alone
