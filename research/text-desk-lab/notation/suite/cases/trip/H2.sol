# The trip, solution H2 (hybrid, Pike's binding words), as run on 23 September in frontier-trip@H2.
# The trip doc carries start= and end=; items are notes with tripday= linked part-of the trip; every shown date
# is derived (days-from, day-n) from the trip's start. Marks as in R.sol; A = an authoring retry (a write, not a repair).
recorded M1=29 M2=0 M3=0 M4=1

step 2
T do prop "Big Sur trip" role=trip start=2026-10-10 end=2026-10-11
T do create f01 kind=note title="McWay Falls" text="short walk, best at sunset" tripday=1
T do link "McWay Falls" to=a03 as=part-of
T do create f01 kind=note title="Night on the coast" text="Kirk Creek if a site is free, else a motel in Cambria" tripday=1
T do link "Night on the coast" to=a03 as=part-of
T do create f01 kind=note title="Ewoldsen hike" text="4.5 mi loop, redwoods" tripday=2
T do link "Ewoldsen hike" to=a03 as=part-of
T do create f01 kind=note title="Lunch with Sam at Nepenthe" text="noon; Sam drives up that morning" tripday=2
T do link "Lunch with Sam at Nepenthe" to=a03 as=part-of
T do create f01 kind=note title="Bixby Bridge stop" text="photo stop, 10 min" tripday=2
T do link "Bixby Bridge stop" to=a03 as=part-of

step 3
T do create f01 kind=note title="cal trip" tags=lens text="cal : row, the prop:role=trip as trip\n  days : row, derive days = days-from $trip.start $trip.end, over $days, each day\nday : column, role sheet\n  head : text \"Day $it.n, $it.date\", role heading\n  items : column, of parts:$trip.item,prop:tripday=$it.n, each entry\nentry : column, role card\n  what : text \"$title\"\n  open : text \"open: $uncertain\", role tag, only when prop:uncertain"
T do create f01 kind=note title="itinerary" tags=lens text="itin : column, the prop:role=trip as trip\n  rows : column, of parts:$trip.item, each row\nrow : row, derive date = day-n $trip.start $tripday\n  d : text \"$date\"\n  t : text \"$title\"\n  u : text \"open: $uncertain\", only when prop:uncertain"
A do rewrite itinerary text="itin : column, the prop:role=trip as trip\n  rows : column, of parts:$trip.item as stop, each row\nrow : row, derive date = day-n $trip.start $stop.tripday\n  d : text \"$date\"\n  t : text \"$title\"\n  u : text \"open: $uncertain\", only when prop:uncertain"
place cal scene cal trip
place itinerary scene itinerary

step 4
T do prop "Big Sur trip" start=2026-10-17 end=2026-10-18
T do append "Big Sur trip" line="Moved a week: Kirk Creek is full on the 10th."

step 5
T do create f01 kind=note title="Pfeiffer Beach" text="purple sand, afternoon" tripday=1
T do link "Pfeiffer Beach" to=a03 as=part-of

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
T do link "Kirk Creek campsite" to="Night on the coast" as=refers
T do link "Cambria motel" to="Night on the coast" as=refers
fact alternatives n/e examine shows refers from, not alternatives

step 9
T do prop "Big Sur trip" start=2026-10-10 end=2026-10-11
T do append "Big Sur trip" line="Moved back: a site opened up on the 10th."

step 10
T do remove "cal trip"
T do remove itinerary
unplace cal
unplace itinerary
fact reasoning read "Big Sur trip" shows Moved a week: Kirk Creek is full on the 10th.
fact reasoning-back read "Big Sur trip" shows Moved back: a site opened up on the 10th.

step 11
T@A read "Ewoldsen hike"
T@B read "Ewoldsen hike"
T@B do rewrite "Ewoldsen hike" text="4.5 mi loop; trail reopened per the ranger report"
T@A do rewrite "Ewoldsen hike" text="4.5 mi loop, redwoods; bring layers"
fact b-kept read "Ewoldsen hike" shows trail reopened per the ranger report
