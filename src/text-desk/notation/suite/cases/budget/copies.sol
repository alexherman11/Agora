# The household budget, solution 'copies', as run on 24 September in frontier-budget@budget (juniper-6, section 3).
# Every share is a hand-computed prop (third=, owe=) and the split lens prints them; the October statement is
# a second lens that captures the month. Marks as in trip/R.sol; A = an exploratory write (counted, not a repair).
# By hand I counted 14 silent and 2 visible. The instrument finds 21 silent: my repairs of the live shares
# (steps 5 and 6) made the October statement wrong, and I had checked it only before repairing; the penny also
# reappears once in the October statement. A derived solution is not expressible yet (no sum over a repeat,
# no multiply or divide), so this case holds its facts ready for one.
recorded M1=36 M2=9 M3=16

step 2
T do create f01 kind=doc title="Flat 3B budget" text="Ana, Ben and Casey split the flat's bills three ways, by the month. Rent is 2400, utilities about 180, internet 60. If someone leaves mid-month they pay for the days they were here." role=house month=2026-10-01 monthend=2026-10-31
T do create f01 kind=note title="Ana" role=person joined=2026-01-01
T do link Ana to=a03 as=part-of
T do create f01 kind=note title="Ben" role=person joined=2026-01-01
T do link Ben to=a03 as=part-of
T do create f01 kind=note title="Casey" role=person joined=2026-01-01
T do link Casey to=a03 as=part-of
T do create f01 kind=note title="Rent" role=bill amount=2400
T do link Rent to=a03 as=part-of
T do create f01 kind=note title="Utilities" role=bill amount=180
T do link Utilities to=a03 as=part-of
T do create f01 kind=note title="Internet" role=bill amount=60
T do link Internet to=a03 as=part-of

step 3
T do prop Rent third=800
T do prop Utilities third=60
T do prop Internet third=20
T do prop Ana owe=880
T do prop Ben owe=880
T do prop Casey owe=880
T do create f01 kind=note title="split" tags=lens text="split : column, the prop:role=house as h\n  head : text \"Month from $h.month\", role heading\n  bills : column, of parts:$h.item,prop:role=bill as b, each bill\n  people : column, of parts:$h.item,prop:role=person as p, each person\nbill : row\n  t : text \"$title $amount, each pays $third\"\nperson : row\n  t : text \"$title owes $owe\""
place split scene split

step 4
T do prop Casey leave=2026-10-15
check
A do rewrite split text="split : column, the prop:role=house as h\n  head : text \"Month from $h.month\", role heading\n  bills : column, of parts:$h.item,prop:role=bill as b, each bill\n  people : column, of parts:$h.item,prop:role=person as p, each person\nbill : row\n  t : text \"$title $amount, each pays $third\"\nperson : row\n  t : text \"$title owes $owe\"\n  days : row, derive stay = days-from $h.month $p.leave, over $stay, each d, clamp 1\nd : text \"$n days here\""
check
R do prop Ana owe=1062.86
R do prop Ben owe=1062.86
R do prop Casey owe=514.29
check
R do rewrite split text="split : column, the prop:role=house as h\n  head : text \"Month from $h.month\", role heading\n  bills : column, of parts:$h.item,prop:role=bill as b, each bill\n  people : column, of parts:$h.item,prop:role=person as p, each person\nbill : row\n  t : text \"$title $amount\"\nperson : row\n  t : text \"$title owes $owe\""

step 5
T do prop "Flat 3B budget" month=2026-11-01 monthend=2026-11-30
T do prop Rent amount=2550
T do create f01 kind=note title="split october" tags=lens text="split : column, the prop:role=house as h, capture month=2026-10-01\n  head : text \"Month from $h.month\", role heading\n  bills : column, of parts:$h.item,prop:role=bill as b, each bill\n  people : column, of parts:$h.item,prop:role=person as p, each person\nbill : row\n  t : text \"$title $amount\"\nperson : row\n  t : text \"$title owes $owe\""
place october scene split october
check
R do prop Ana owe=1395
R do prop Ben owe=1395
R do prop Casey remove=owe

step 6
T do create f01 kind=note title="Cleaning" role=bill amount=90
T do link Cleaning to=a03 as=part-of
check
R do prop Ana owe=1440
R do prop Ben owe=1440
