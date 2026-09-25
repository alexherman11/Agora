# The trip, solution R (records), as run on 23 September in frontier-trip@R.
# Items are notes tagged trip carrying day= (a copied absolute date) and tripday=; an Itinerary view and two
# calendar lenses, one with literal dates and one with relative days.
# The recorded M1 counts steps 2-10, as the run did (step 11 was reported apart).
# Line marks: T target write or read, R repair, @X window X. `check` runs every place's reader.
# `place <name> <read>` starts reading an output; `unplace <name>` stops. The seed (step 1) is in task.py.
recorded M1=43 M2=13 M3=19 M4=1

step 2
T do prop "Big Sur trip" role=trip
T do prop "Big Sur trip" start=2026-10-10
T do create f01 kind=note title="McWay Falls" text="short walk, best at sunset" tags=trip
T do prop "McWay Falls" day=2026-10-10 tripday=1
T do create f01 kind=note title="Night on the coast" text="Kirk Creek if a site is free, else a motel in Cambria" tags=trip
T do prop "Night on the coast" day=2026-10-10 tripday=1
T do create f01 kind=note title="Ewoldsen hike" text="4.5 mi loop, redwoods" tags=trip
T do prop "Ewoldsen hike" day=2026-10-11 tripday=2
T do create f01 kind=note title="Lunch with Sam at Nepenthe" text="noon; Sam drives up that morning" tags=trip
T do prop "Lunch with Sam at Nepenthe" day=2026-10-11 tripday=2
T do create f01 kind=note title="Bixby Bridge stop" text="photo stop, 10 min" tags=trip
T do prop "Bixby Bridge stop" day=2026-10-11 tripday=2

step 3
T do create f01 kind=view title="Itinerary" query=tag:trip cols=day,tripday,title,uncertain by=day
T do create f01 kind=note title="cal literal" tags=lens text="cal : row\n  d1 : column, role sheet\n    head : text \"Sat Oct 10\", role heading\n    items : column, of tag:trip,prop:day=2026-10-10, each entry\n  d2 : column, role sheet\n    head : text \"Sun Oct 11\", role heading\n    items : column, of tag:trip,prop:day=2026-10-11, each entry\nentry : column, role card\n  what : text \"$title\"\n  open : text \"open question\", role tag, only when prop:uncertain"
T do create f01 kind=note title="cal relative" tags=lens text="cal : row\n  d1 : column, role sheet\n    head : text \"Day 1\", role heading\n    items : column, of tag:trip,prop:tripday=1, each entry\n  d2 : column, role sheet\n    head : text \"Day 2\", role heading\n    items : column, of tag:trip,prop:tripday=2, each entry\nentry : column, role card\n  what : text \"$title\"\n  open : text \"open question\", role tag, only when prop:uncertain"
place itinerary view Itinerary
place cal-literal scene cal literal
place cal-relative scene cal relative

step 4
T do prop "Big Sur trip" start=2026-10-17
T do append "Big Sur trip" line="Moved a week: Kirk Creek is full on the 10th."
check
R do prop "McWay Falls" day=2026-10-17
R do prop "Night on the coast" day=2026-10-17
R do prop "Ewoldsen hike" day=2026-10-18
R do prop "Lunch with Sam at Nepenthe" day=2026-10-18
R do prop "Bixby Bridge stop" day=2026-10-18
check
R do rewrite "cal literal" text="cal : row\n  d1 : column, role sheet\n    head : text \"Sat Oct 17\", role heading\n    items : column, of tag:trip,prop:day=2026-10-17, each entry\n  d2 : column, role sheet\n    head : text \"Sun Oct 18\", role heading\n    items : column, of tag:trip,prop:day=2026-10-18, each entry\nentry : column, role card\n  what : text \"$title\"\n  open : text \"open question\", role tag, only when prop:uncertain"

step 5
T do create f01 kind=note title="Pfeiffer Beach" text="purple sand, afternoon" tags=trip
T do prop "Pfeiffer Beach" day=2026-10-17 tripday=1

step 6a
T do prop "Ewoldsen hike" uncertain="trail status"

step 6b
T do prop "Ewoldsen hike" remove=uncertain

step 7
T do comment "Ewoldsen hike" line="Check the trail report on Friday."
fact commented examine "Ewoldsen hike" shows Check the trail report on Friday.

step 8
T do create f01 kind=note title="Kirk Creek campsite" text="$35, first-come sites sometimes open"
T do create f01 kind=note title="Cambria motel" text="about $140, 1h south"
T do link "Kirk Creek campsite" "Night on the coast" as=refers
T do link "Cambria motel" "Night on the coast" as=refers
fact alternatives n/e examine shows refers from, not alternatives

step 9
T do prop "Big Sur trip" start=2026-10-10
T do append "Big Sur trip" line="Moved back: a site opened up on the 10th."
check
R do prop "McWay Falls" day=2026-10-10
R do prop "Night on the coast" day=2026-10-10
R do prop "Pfeiffer Beach" day=2026-10-10
R do prop "Ewoldsen hike" day=2026-10-11
R do prop "Lunch with Sam at Nepenthe" day=2026-10-11
R do prop "Bixby Bridge stop" day=2026-10-11
check
R do rewrite "cal literal" text="cal : row\n  d1 : column, role sheet\n    head : text \"Sat Oct 10\", role heading\n    items : column, of tag:trip,prop:day=2026-10-10, each entry\n  d2 : column, role sheet\n    head : text \"Sun Oct 11\", role heading\n    items : column, of tag:trip,prop:day=2026-10-11, each entry\nentry : column, role card\n  what : text \"$title\"\n  open : text \"open question\", role tag, only when prop:uncertain"

step 10
T do remove "cal literal"
T do remove "cal relative"
unplace cal-literal
unplace cal-relative
fact reasoning read "Big Sur trip" shows Moved a week: Kirk Creek is full on the 10th.
fact reasoning-back read "Big Sur trip" shows Moved back: a site opened up on the 10th.

step 11
T@A read "Ewoldsen hike"
T@B read "Ewoldsen hike"
T@B do rewrite "Ewoldsen hike" text="4.5 mi loop; trail reopened per the ranger report"
T@A do rewrite "Ewoldsen hike" text="4.5 mi loop, redwoods; bring layers"
fact b-kept read "Ewoldsen hike" shows trail reopened per the ranger report
