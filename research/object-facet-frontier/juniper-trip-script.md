# The trip script: a fixed run of Embark's case

Round two, Juniper, 23 September 2026. This is a rerunnable procedure. Anyone on the team should be able to run it and get the same counts. The results are in `juniper-2-the-trip-run.md`. The text below is the script **as run**: three lines were corrected while running on 23 September, and each correction is marked *as-run*.

## Setup

- **Where to run.** From `C:/Projects/Agora4/research/text-desk-lab/notation`, with `PY=C:/Projects/Agora4/.venv/Scripts/python.exe`.
- **Feeding commands.** Each block below goes to one `explore.py` call on stdin, one command per line. Use a heredoc (`<<'EOF'`), because `printf` expands `\n` (Pike's friction 10). Lines starting with `#` are skipped by the CLI.
- **Record the build.** Note whether a deskd answers on 8780. If none does, the CLI runs whatever source is on disk at that moment. Record the git head and the sha256 of `scene.py`, `knife.py`, `moo.py`, `desk_knife.py`, `desk_moo.py` and `world.py` before and after the run.
- **Sessions.** The base session is `frontier-trip`. Worktrees are `frontier-trip@R` (records), `frontier-trip@D` (document) and later `frontier-trip@H` (hybrid). The actor is `--as juniper`, or your own name.
- **Targets.** Name every target by **title**, one thing per write. Do not use `$item`, `$new` or id lists; `$item` falls back to the previous thing after a refusal (round 1). This makes *writes* equal *thing-edits* across representations. `<trip>` means the id printed when the trip was created in step 1; in a fresh session it is `a03`.
- **After a refusal.** If a line is refused, stop. Record the refusal, then continue from the next line on purpose.

## The five measures, plus a visibility column

Every step has **target writes**: the minimal writes that state the user's decision (listed per step). It also has **checks**: read commands, each with an expected output, written as "should show".

| # | Measure | Definition |
|---|---|---|
| M1 | writes | Lines beginning `do`, `rule`, `undo` or `script`, counted per step. Reads (`look`, `read`, `scene`, `find`, `table`, `examine`, `rows`) are not counted. |
| M2 | repairs | Writes beyond the step's target writes that were needed before every check showed the expected output. Each repair is also listed with what it edited. A repair that re-edits the target thing still counts (for example D's step 5 rewrite). |
| M3 | wrong outputs | Check outputs that state something false (a stale date, an item missing or on the wrong day, a wrong flag), counted *before* repairs. |
| M3v | visibility | For each M3 miss, one of three values. **visible** means a refusal, an error, an `(absent: …)`, a stale or unresolved marker, or a fallback notice. **silent** means printed as if current. **silent 0-of** means a repeat printed `0 of <selection>` where it should have had members. A capability that cannot be expressed at all is recorded as **n/e** (not expressible), not as M3. |
| M4 | wrong-target | A write accepted on a thing the user did not mean, or an edit that overwrote another window's edit without refusal. |
| M5 | stated-date agreement at the end | After step 11, list every place in the world that states the trip's current dates: props, due, headings, lens literals, view cells, and present-tense prose. M5a is the number of such places; M5b is how many of them disagree with the final dates (Sat 10 and Sun 11 October 2026). Historical prose ("moved a week because…") is not counted. |

Pike's binding split. At steps 4 and 9, also attribute each repair and each miss to the output that needed it:

- the itinerary view (a query over copied values);
- the literal lens;
- the relative lens (a `$field` inside a repeat over an anchor);
- an identity binding (H only, once `of <id>` exists);
- the section lens (D; positional keys).

## Content (identical in every representation)

The trip starts on Saturday 10 October 2026 and covers two days.

- **Day 1:** McWay Falls (evening); "Night on the coast" (lodging).
- **Day 2:** Ewoldsen hike (morning); Lunch with Sam at Nepenthe (noon); Bixby Bridge stop.

Along the way the script adds:

- Step 5: "Pfeiffer Beach", on day 1.
- Step 6: the hike is uncertain ("trail status"), then resolved.
- Step 7: a comment on the hike, "Check the trail report on Friday."
- Step 8: lodging alternatives, "Kirk Creek campsite" and "Cambria motel".
- Step 4: the trip moves one week, to 17 October.
- Step 9: the trip moves back to 10 October.

## Step 1: seed (base session, run once)

*As-run:* a fresh desk refuses `create` until you have looked, so `look` comes first. Target writes: 1.

```
look
do create f01 kind=doc title="Big Sur trip" text="Thinking Sat-Sun Oct 10-11, maybe the weekend after. Want McWay Falls, a hike, one night near the coast (Kirk Creek if a site is free, else Cambria). Sam can only do Sunday."
```

Then, in `frontier-trip`, run `worktree fork R` and `worktree fork D`, one per call. Worktree commands cannot be chained.

## R: records (session `frontier-trip@R`)

The trip doc carries the start date as the prop `start=` and `role=trip`. *As-run:* `do due` is refused on a doc ("due does not apply to a03"; due applies only to tasks and notes), so `start=` replaces it, and the relative lens cannot print a date. Items are notes tagged `trip`, with `day=` (absolute) and `tripday=` (relative).

**Step 2: dates and items.** Target writes: all 12 lines.

```
do prop "Big Sur trip" role=trip
do prop "Big Sur trip" start=2026-10-10
do create f01 kind=note title="McWay Falls" text="short walk, best at sunset" tags=trip
do prop "McWay Falls" day=2026-10-10 tripday=1
do create f01 kind=note title="Night on the coast" text="Kirk Creek if a site is free, else a motel in Cambria" tags=trip
do prop "Night on the coast" day=2026-10-10 tripday=1
do create f01 kind=note title="Ewoldsen hike" text="4.5 mi loop, redwoods" tags=trip
do prop "Ewoldsen hike" day=2026-10-11 tripday=2
do create f01 kind=note title="Lunch with Sam at Nepenthe" text="noon; Sam drives up that morning" tags=trip
do prop "Lunch with Sam at Nepenthe" day=2026-10-11 tripday=2
do create f01 kind=note title="Bixby Bridge stop" text="photo stop, 10 min" tags=trip
do prop "Bixby Bridge stop" day=2026-10-11 tripday=2
```

**Step 3: itinerary plus two calendars.** Target writes: 3.

```
do create f01 kind=view title="Itinerary" query=tag:trip cols=day,tripday,title,uncertain by=day
do create f01 kind=note title="cal literal" tags=lens text="cal : row\n  d1 : column, role sheet\n    head : text \"Sat Oct 10\", role heading\n    items : column, of tag:trip,prop:day=2026-10-10, each entry\n  d2 : column, role sheet\n    head : text \"Sun Oct 11\", role heading\n    items : column, of tag:trip,prop:day=2026-10-11, each entry\nentry : column, role card\n  what : text \"$title\"\n  open : text \"open question\", role tag, only when prop:uncertain"
do create f01 kind=note title="cal relative" tags=lens text="cal : row\n  d1 : column, role sheet\n    head : text \"Day 1\", role heading\n    items : column, of tag:trip,prop:tripday=1, each entry\n  d2 : column, role sheet\n    head : text \"Day 2\", role heading\n    items : column, of tag:trip,prop:tripday=2, each entry\nentry : column, role card\n  what : text \"$title\"\n  open : text \"open question\", role tag, only when prop:uncertain"
```

Checks (the same after every later step; the expected content changes as the plan does):

```
look <Itinerary id> :3
scene cal literal
scene cal relative
```

- The itinerary should show 5 rows with the correct `day` values.
- Each calendar should show day 1 = {McWay, Night} and day 2 = {hike, lunch, Bixby}.
- Each calendar should print the correct date wherever it prints one.

**Step 4: move the trip one week.** Target writes: 2, the date and one reasoning line.

```
do prop "Big Sur trip" start=2026-10-17
do append "Big Sur trip" line="Moved a week: Kirk Creek is full on the 10th."
```

Run the checks. Then apply only the repairs the checks demand. In the R run these were:

- `do prop "<item>" day=<new>`, once for each of the 5 items;
- `do rewrite "cal literal" text=...`, with every date literal changed;
- `do rewrite "Big Sur trip" text=...`, only if the first prose line is to stay true. Record whether you did this; if you did not, it shows up in M5.

**Step 5: add a Saturday item.** Target writes: 2.

```
do create f01 kind=note title="Pfeiffer Beach" text="purple sand, afternoon" tags=trip
do prop "Pfeiffer Beach" day=<current Saturday> tripday=1
```

**Step 6: uncertain, then resolved.** Target writes: 2. Run the checks after each line, plus `find prop:uncertain`.

- After the first line, the hike should be flagged and listed as open.
- After the second, it should not be.

```
do prop "Ewoldsen hike" uncertain="trail status"
do prop "Ewoldsen hike" remove=uncertain
```

**Step 7: comment on one item.** Target writes: 1. Check with `examine "Ewoldsen hike"`: the comment should be shown on the hike.

```
do comment "Ewoldsen hike" line="Check the trail report on Friday."
```

**Step 8: an alternative for lodging.** Target writes: 4.

```
do create f01 kind=note title="Kirk Creek campsite" text="$35, first-come sites sometimes open"
do create f01 kind=note title="Cambria motel" text="about $140, 1h south"
do link "Kirk Creek campsite" "Night on the coast" as=refers
do link "Cambria motel" "Night on the coast" as=refers
```

Check with `examine "Night on the coast"`. It should show the two options *as alternatives*. Record whether it can.

**Step 9: move back.** Target writes: 2.

```
do prop "Big Sur trip" start=2026-10-10
do append "Big Sur trip" line="Moved back: a site opened up on the 10th."
```

Checks and repairs as in step 4.

**Step 10: remove the calendars.** Target writes: 2.

```
do remove "cal literal"
do remove "cal relative"
```

Check with `read "Big Sur trip"` and the itinerary. The reasoning should be intact, and the itinerary should still list 6 rows.

**Step 11: one person, two windows.** Each line below is a *separate* `explore.py` call, so the calls behave like separate windows.

- Variant (a) uses the same actor name in both windows:
  1. Window A: `read "Ewoldsen hike"`.
  2. Window B: `do rewrite "Ewoldsen hike" text="4.5 mi loop; trail reopened per the ranger report"`.
  3. Window A, working from its first read: `do rewrite "Ewoldsen hike" text="4.5 mi loop, redwoods; bring layers"`.
  4. Record whether the last write is refused. If it is accepted, count 1 M4, because B's edit is lost.
- Variant (b) is the same, with window B as `--as juniper-tab2`. It is one person with two names.

Then run step M5.

## D: document (session `frontier-trip@D`)

The trip doc holds the plan. Days are `## ` sections, and items are `- ` lines.

**Step 2.** Target writes: 7, one append per line, in order.

```
do append "Big Sur trip" line="## Sat Oct 10"
do append "Big Sur trip" line="- McWay Falls, evening"
do append "Big Sur trip" line="- Night on the coast"
do append "Big Sur trip" line="## Sun Oct 11"
do append "Big Sur trip" line="- Ewoldsen hike, morning"
do append "Big Sur trip" line="- Lunch with Sam at Nepenthe, noon"
do append "Big Sur trip" line="- Bixby Bridge stop"
```

**Step 3.** Target writes: 1. The itinerary *table* cannot be expressed (n/e); `read "Big Sur trip" :3` is the itinerary.

```
do create f01 kind=note title="cal sections" tags=lens text="cal : row, of sections:<trip>, each day\nday : column, role sheet\n  head : text \"$heading\", role heading\n  body : text \"$text\", role body"
```

Checks: `read "Big Sur trip" :3` and `scene cal sections`.

- The first should show 2 dated sections with the right lines.
- The second should show one column per day, with correct dates and items.

**Step 4.** Target writes: 1. Rewrite the whole text: both headings get the new dates, and the reasoning line "Moved a week: Kirk Creek is full on the 10th." is added after the first paragraph. Read the doc first.

**Step 5.** Target writes: 1. `do append "Big Sur trip" line="- Pfeiffer Beach, afternoon"`. Check: it should be under Saturday. The repair, if needed, is a rewrite.

**Step 6.** Target writes: 2 rewrites.

1. Add " (? trail status)" to the hike line.
2. Remove it.

The "what is open" query cannot be expressed (n/e). Checks: the scene and `read`.

**Step 7.** Target writes: 1. `do comment "Big Sur trip" line="Ewoldsen hike: check the trail report on Friday."` The comment cannot name its line. Check: `read "Big Sur trip"` should show the comment attached to the hike.

**Step 8.** Target writes: 1. Rewrite so that under "- Night on the coast" there are two lines: "  - alt: Kirk Creek campsite, $35" and "  - alt: Cambria motel, about $140".

**Step 9.** Target writes: 1. Rewrite the headings back, and add "Moved back: a site opened up on the 10th."

**Step 10.** Target writes: 1. `do remove "cal sections"`. Check: `read "Big Sur trip" :3`.

**Step 11.** As in R, with the doc as the item. Both windows rewrite the whole doc: window B adds " (trail reopened)" to the hike line, and window A adds " bring layers".

## H: hybrid (session `frontier-trip@H`, forked from the seed after Jeff's words landed)

- The reasoning stays in the doc, which carries `start=`.
- Items are notes created *with* `tripday=`, one command each, and linked `part-of` the trip. They carry no tag and no date.
- Membership is a relationship: `links:<trip>`, which selects both link directions.
- The calendar binds to the trip by identity (`of a03`) and reads `$start`. The inner repeats follow `links:$item`.

**Step 2.** Target writes: 11. The block below shows the first item; repeat the pair for Night on the coast (1), Ewoldsen hike (2), Lunch with Sam at Nepenthe (2) and Bixby Bridge stop (2).

```
do prop "Big Sur trip" role=trip start=2026-10-10
do create f01 kind=note title="McWay Falls" text="short walk, best at sunset" tripday=1
do link "McWay Falls" "Big Sur trip" as=part-of
```

**Step 3.** Target writes: 2.

```
do create f01 kind=view title="Itinerary" query=links:a03 cols=tripday,title,uncertain by=tripday
do create f01 kind=note title="cal trip" tags=lens text="cal : row, of a03, each trip\ntrip : row\n  d1 : column, role sheet\n    head : text \"Day 1, $start\", role heading\n    items : column, of links:$item,prop:tripday=1, each entry\n  d2 : column, role sheet\n    head : text \"Day 2\", role heading\n    items : column, of links:$item,prop:tripday=2, each entry\nentry : column, role card\n  what : text \"$title\"\n  open : text \"open: $uncertain\", role tag, only when prop:uncertain"
```

Checks: `look <Itinerary id> :3` and `scene cal trip`.

**Steps 4 and 9.** Target writes: 2, namely `do prop "Big Sur trip" start=<date>` and the reasoning `append`.

**Step 5.** Target writes: 2.

```
do create f01 kind=note title="Pfeiffer Beach" text="purple sand, afternoon" tripday=1
do link "Pfeiffer Beach" "Big Sur trip" as=part-of
```

**Steps 6, 7, 8, 10 and 11.** As in R, except that step 10 removes only `"cal trip"`.

**The H lines I wanted but could not write:** see `juniper-2-the-trip-run.md`, section "What H still needs".
