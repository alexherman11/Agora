# The trip, solution D (document), as run on 23 September in frontier-trip@D.
# The trip doc holds the plan: days are "## " sections, items are "- " lines; a section lens is the calendar.
# Marks as in R.sol. The recorded M1 counts steps 2-10.
# The recorded M4 of 2 counted the step 5 append twice, as a silent wrong and as a wrong target; the instrument
# counts it once, as the silent wrong (Pfeiffer Beach on day 2). The other was step 11, now refused per window.
recorded M1=17 M2=1 M3=2 M4=2 M5=3

step 2
T do append "Big Sur trip" line="## Sat Oct 10"
T do append "Big Sur trip" line="- McWay Falls, evening"
T do append "Big Sur trip" line="- Night on the coast"
T do append "Big Sur trip" line="## Sun Oct 11"
T do append "Big Sur trip" line="- Ewoldsen hike, morning"
T do append "Big Sur trip" line="- Lunch with Sam at Nepenthe, noon"
T do append "Big Sur trip" line="- Bixby Bridge stop"

step 3
T do create f01 kind=note title="cal sections" tags=lens text="cal : row, of sections:a03, each day\nday : column, role sheet\n  head : text \"$heading\", role heading\n  body : text \"$text\", role body"
place cal scene cal sections
fact itinerary n/e no table of the doc's lines

step 4
T read "Big Sur trip"
T do rewrite "Big Sur trip" text="Thinking Sat-Sun Oct 10-11, maybe the weekend after. Want McWay Falls, a hike, one night near the coast (Kirk Creek if a site is free, else Cambria). Sam can only do Sunday.\nMoved a week: Kirk Creek is full on the 10th.\n## Sat Oct 17\n- McWay Falls, evening\n- Night on the coast\n## Sun Oct 18\n- Ewoldsen hike, morning\n- Lunch with Sam at Nepenthe, noon\n- Bixby Bridge stop"

step 5
T do append "Big Sur trip" line="- Pfeiffer Beach, afternoon"
check
R do rewrite "Big Sur trip" text="Thinking Sat-Sun Oct 10-11, maybe the weekend after. Want McWay Falls, a hike, one night near the coast (Kirk Creek if a site is free, else Cambria). Sam can only do Sunday.\nMoved a week: Kirk Creek is full on the 10th.\n## Sat Oct 17\n- McWay Falls, evening\n- Night on the coast\n- Pfeiffer Beach, afternoon\n## Sun Oct 18\n- Ewoldsen hike, morning\n- Lunch with Sam at Nepenthe, noon\n- Bixby Bridge stop"

step 6a
T do rewrite "Big Sur trip" text="Thinking Sat-Sun Oct 10-11, maybe the weekend after. Want McWay Falls, a hike, one night near the coast (Kirk Creek if a site is free, else Cambria). Sam can only do Sunday.\nMoved a week: Kirk Creek is full on the 10th.\n## Sat Oct 17\n- McWay Falls, evening\n- Night on the coast\n- Pfeiffer Beach, afternoon\n## Sun Oct 18\n- Ewoldsen hike, morning (? trail status)\n- Lunch with Sam at Nepenthe, noon\n- Bixby Bridge stop"
fact what-is-open n/e find ?trail returns the whole doc

step 6b
T do rewrite "Big Sur trip" text="Thinking Sat-Sun Oct 10-11, maybe the weekend after. Want McWay Falls, a hike, one night near the coast (Kirk Creek if a site is free, else Cambria). Sam can only do Sunday.\nMoved a week: Kirk Creek is full on the 10th.\n## Sat Oct 17\n- McWay Falls, evening\n- Night on the coast\n- Pfeiffer Beach, afternoon\n## Sun Oct 18\n- Ewoldsen hike, morning\n- Lunch with Sam at Nepenthe, noon\n- Bixby Bridge stop"

step 7
T do comment "Big Sur trip" line="Ewoldsen hike: check the trail report on Friday."
fact commented n/e the comment attaches to the doc, not the hike

step 8
T do rewrite "Big Sur trip" text="Thinking Sat-Sun Oct 10-11, maybe the weekend after. Want McWay Falls, a hike, one night near the coast (Kirk Creek if a site is free, else Cambria). Sam can only do Sunday.\nMoved a week: Kirk Creek is full on the 10th.\n## Sat Oct 17\n- McWay Falls, evening\n- Night on the coast\n  - alt: Kirk Creek campsite, $35\n  - alt: Cambria motel, about $140\n- Pfeiffer Beach, afternoon\n## Sun Oct 18\n- Ewoldsen hike, morning\n- Lunch with Sam at Nepenthe, noon\n- Bixby Bridge stop"
fact alternatives n/e prose sub-lines, drawn as Saturday lines

step 9
T do rewrite "Big Sur trip" text="Thinking Sat-Sun Oct 10-11, maybe the weekend after. Want McWay Falls, a hike, one night near the coast (Kirk Creek if a site is free, else Cambria). Sam can only do Sunday.\nMoved a week: Kirk Creek is full on the 10th.\nMoved back: a site opened up on the 10th.\n## Sat Oct 10\n- McWay Falls, evening\n- Night on the coast\n  - alt: Kirk Creek campsite, $35\n  - alt: Cambria motel, about $140\n- Pfeiffer Beach, afternoon\n## Sun Oct 11\n- Ewoldsen hike, morning\n- Lunch with Sam at Nepenthe, noon\n- Bixby Bridge stop"

step 10
T do remove "cal sections"
unplace cal
fact reasoning read "Big Sur trip" shows Moved a week: Kirk Creek is full on the 10th.
fact reasoning-back read "Big Sur trip" shows Moved back: a site opened up on the 10th.

step 11
T@A read "Big Sur trip"
T@B read "Big Sur trip"
T@B do rewrite "Big Sur trip" text="Thinking Sat-Sun Oct 10-11, maybe the weekend after. Want McWay Falls, a hike, one night near the coast (Kirk Creek if a site is free, else Cambria). Sam can only do Sunday.\nMoved a week: Kirk Creek is full on the 10th.\nMoved back: a site opened up on the 10th.\n## Sat Oct 10\n- McWay Falls, evening\n- Night on the coast\n  - alt: Kirk Creek campsite, $35\n  - alt: Cambria motel, about $140\n- Pfeiffer Beach, afternoon\n## Sun Oct 11\n- Ewoldsen hike, morning (trail reopened)\n- Lunch with Sam at Nepenthe, noon\n- Bixby Bridge stop"
T@A do rewrite "Big Sur trip" text="Thinking Sat-Sun Oct 10-11, maybe the weekend after. Want McWay Falls, a hike, one night near the coast (Kirk Creek if a site is free, else Cambria). Sam can only do Sunday.\nMoved a week: Kirk Creek is full on the 10th.\nMoved back: a site opened up on the 10th.\n## Sat Oct 10\n- McWay Falls, evening\n- Night on the coast\n  - alt: Kirk Creek campsite, $35\n  - alt: Cambria motel, about $140\n- Pfeiffer Beach, afternoon\n## Sun Oct 11\n- Ewoldsen hike, morning bring layers\n- Lunch with Sam at Nepenthe, noon\n- Bixby Bridge stop"
fact b-kept read "Big Sur trip" :3 shows (trail reopened)
