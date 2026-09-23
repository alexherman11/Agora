# Juniper 3: three ordinary tasks against the closed list

Round three, pressure. 23 September 2026. **[ran]** means executed in the desk. **[imagined]** means a thought experiment.

The question is whether Pike's closed list of interpretations survives three everyday tasks that are not a trip. The list is `day-n`, `days-from`, `weekday` and `week-of`.

I seeded the fresh session `frontier-tasks` (head 2c841be, `scene.py` 9003e697) and ran each task H-style in its own worktree (`@course`, `@books`, `@garden`):

- the reasoning lives in a doc that carries props;
- the parts are notes created with props and linked `part-of` the doc;
- the views are lenses that follow the doc through `the prop:role=… as <frame>` and `of parts:$frame.item,…`.

## Counts

| | Course | Books | Garden |
|---|---|---|---|
| New interpretations needed | 2: `every` (weekday recurrence with a skip list), `where`/`pick` (look up a derived row) | 3: `every` (14-day step), `running` (prefix sum over an ordered repeat), `reach` (when a cumulative amount is reached under a rate that changes) | 2: a year range (`every` with step 1y), `shift` (integer or year offset) |
| New selection or repeat abilities | 1: filter a repeat by a *derived* value | 1: sort a repeat by a prop (`order`) | 2: fill frames inside `only when`; numeric comparison `prop:year<…` / `>` |
| Places pushed toward arithmetic | 3: week to day offset `7(w-1)+3`; `+7` after the break; day-n is 1-based | 4: `every 14`; `+1` for 1-based day-n; pages ÷ pace; cumulative sum | 2: `year-3` window; "rests one year in four" |
| Places pushed toward an `if` | 1: after the break, add a week | 1: pace changes after meeting 3 | 2: the violation flag; "resting" in a cell |
| Repairs after the one change | break moved: **1**. Assignment rescheduled: **1** (it needs 2 writes: `week` and the hand `off`) | pace change: **2** (two books' `finish`) | bed rested: **1** (move the planting) |
| Silent wrong outputs before repair | 2 | 2 | 2 (planting in a resting bed; the title "2028 B nightshade" now in bed C) |
| n/e (not expressible) | the meeting calendar | the meeting dates; "how far behind is Rae" | "resting"; the 3-year rule; a rotation proposal |

Every repair comes from the same move as R in round 2. When the lens could not derive a value, I stored a hand-computed copy (`off=45`, `finish=3`). The change then left that copy wrong without saying so. With the wanted words below, all three changes are **0 repairs** [imagined, from the lens lines below].

## Course [ran]

**Data.**

- The term doc carries `start=2027-03-29 end=2027-06-11 meets=Mon,Wed break=2027-04-19`.
- Three assignments carry teaching `week=3|6|9`.

**What I could write.** An assignment list:

```
list : column, the prop:role=term as term
  rows : column, of parts:$term.item,prop:role=assignment as a, each row
row : row, derive dd = day-n $term.start $a.off, derive wd = weekday $dd
  t : text "$title, teaching week $week, due $wd $dd"
```

- It prints `dd = day-n(2027-03-29, 45) = 2027-05-12 · wd = weekday(2027-05-12) = Wed`.
- Derives chain: `weekday $dd` and `week-of $x` both worked.
- `off` is a hand-computed copy: calendar week, plus the break, times 7, plus 3.
- Without the copy, `day-n $term.start $a.week` printed "A2 … due 2027-04-03". That is the 6th *day*, not week 6: plausible and wrong.

**What I could not write, and what it should print.**

1. **Meetings (Mon and Wed, skipping the break).** I wrote `day : row, derive wd = weekday $it.date, only when $wd=Mon`. It was **accepted**, then printed `(absent: not $wd=Mon)` for all 75 days, because `only when` is a desk selection over things, not a test of a value. It is visible, but for the wrong reason. I wanted:

   ```
   days : column, derive m = every $term.start $term.end weekly $term.meets skip $term.break, over $m, each meeting
   ```

   It should print `m = every(2027-03-29..2027-06-11, weekly Mon Wed, skip week of 2027-04-19) = 20 rows`, with rows `$it.date $it.wd $it.week`, where `$it.week` is the *teaching* week, keyed by date.
2. **The due date.** I wanted `derive dd = pick $m week=$a.week wd=Wed`. It should print `dd = pick(m, week=6, wd=Wed) = 2027-05-12 (row 12 of 20)`, and `(no row week=12)` when there is none.

**The changes.**

- *Break moved* to 2027-05-17: the target write plus 1 repair (A2 `off` 45→38). Until then, A2 silently showed the old date.
- *A2 rescheduled* to week 7: 1 write, and until the second write the list printed "teaching week 7, due Wed 2027-05-05", which is week 6's date. That makes 1 repair.
- The prose still says "the week of 19 Apr" (M5-style).

## Books [ran]

**Data.**

- The club doc carries `start=2026-10-01 pace=100 every=14`.
- Books carry `pages` and `order`, plus `finish` (the meeting number, hand-computed).
- Rae carries `joined=3`.

**What I could write.** `"$title, $pages pages, finish by meeting $finish"`, reading only stored values. `day-n $club.start $club.every` printed 2026-10-14. The meeting is on Thursday the 15th, because day-n counts the start as day 1: another hidden `+1`.

**What I could not write.**

1. **Meeting dates.** Wanted: `derive m = every $club.start $club.end step 14d`, printing `= 7 rows`.
2. **The finish meeting per book.** This needs a running total of pages in reading order, then the first meeting whose cumulative pace reaches it. Wanted:

   ```
   books : column, of parts:$club.item,prop:role=book, by order, as b, each row
   row : row, derive upto = running $b.pages, derive fin = reach $club.pace $upto $m
   ```

   It should print `upto = running(272, 303) = 575 · fin = reach(pace 100/wk then 80/wk from meeting 3, 575) = meeting 4 (2026-11-26)`.
3. **Rae's catch-up.** Wanted: `derive behind = reach-at $club.pace $rae.joined`, printing `= 400 pages by meeting 3`.

**The change.** Pace 100 → 80 from meeting 3.

- `do prop … pace=80 pacefrom=3`, then 2 repairs (Klara `finish` 3→4, Middlemarch 8→9).
- Until then, 2 silent stale outputs.
- The representation also broke: overwriting `pace` lost the earlier rate that meetings 1–2 were planned on.

## Garden [ran]

**Data.**

- The garden doc; four beds (`bed=A..D`).
- Twelve plantings with `year bed family`.
- The change: bed B rests in 2028.

**What I could write.** A year × bed grid, but only after **minting four "year" notes as things**. `over $tags as yy` was refused ("a lens cannot say 'over $tags as yy'"), and there is no year generator. It printed correctly:

```
row : row
  label : text "$yr.year"
  beds : row, of parts:$g.item,prop:role=bed as bed, each cell
cell : column, role card
  plant : column, of parts:$g.item,prop:role=planting,prop:bed=$bed.bed,prop:year=$yr.year, each p
```

**What I could not write.**

1. **"Resting".** `rest : text "resting", only when prop:role=bed,prop:rest=$yr.year` never fires. `only when` does not fill frames, so it prints `(absent: not prop:role=bed,prop:rest=$yr.year)`. The unfilled `$` is the only clue.
2. **The 3-year rule.** Wanted, on each planting:

   ```
   bad : text "returns too soon", only when parts:$g.item,prop:bed=$bed,prop:family=$family,prop:year>$lo,prop:year<$year, derive lo = shift $year -4
   ```

   It should print `lo = shift(2028, -4) = 2024 · 1 match: a23 2025 C nightshade`. That needs numeric `<`/`>` in selections, `shift`, and frame fill in `only when`.
3. **A rotation proposal for next year.** This is constraint assignment. It is not an interpretation: it is code, a definition. Correctly out of the list.

**The change.** `do prop "Bed B" rest=2028`, then 1 repair (move the 2028 planting to C).

- Before the repair, the grid silently kept nightshade in a resting bed.
- After it, the title "2028 B nightshade" is a stale copy.

## Verdict: does the closed list survive?

**For time structure, yes, if it grows by four structural words. For quantities, no.**

- The course and the garden need *structure*, not formulas: a recurrence generator with a step, a weekday set and a skip list; a lookup or filter over derived rows; frame fill in `only when`; numeric comparison in selections.
- Once those exist, `day-n` becomes a special case of `pick` over `every`.
- The books need a running sum and a division under a changing rate. Naming that `reach` hides arithmetic behind a domain word. The next quantity task (a budget, a workout plan, a recipe scaled for six) would need its own word. Seven new names came from three tasks in one afternoon, which is Pike's twelve-a-month trigger at about four times the rate.

**The smallest set that carries all three:**

1. **`every <start> <end> <step> [on <weekdays>] [skip <list>]`**, yielding rows `$it.date $it.n $it.week`. It covers the course meetings (weekly Mon/Wed, skip break), the book meetings (step 14d) and the garden years (step 1y).
2. **`where` on a repeat (and `pick` for one row):** filter derived rows or things by a derived value. This replaces `only when $wd=Mon`, which is today accepted and meaningless.
3. **Frame fill in `only when`, plus numeric `<`/`>` on `prop:`.** These are two selection abilities, not interpretations.
4. **Printed arithmetic on numbers and dates** (`+ - × ÷`, each result printed with its inputs, no `if`), *instead of* `shift`, `running`, `reach` and the hand `+1`/`×7`. With `running` as the one aggregate (a prefix sum over an ordered repeat), the books case is `running $b.pages` then a division by pace.

I would keep the closed list for *interpretations that carry meaning* (`weekday`, `week-of`, `every`), and admit a small printed arithmetic for *quantities*. Pike's own safeguards (print the inputs, print the result, no hidden state) are what made the named words safe. They work equally well on `×`.

**What would change my mind:** a fourth everyday task whose derivations all fit `every`/`where`/printed arithmetic without a new named word would show that the list plus arithmetic is closed in practice. A task that needs `if` inside a derivation (not in `only when`) would show that arithmetic without conditionals is not enough.

## Relations the desk cannot express, in Sable's kernel terms

- **Recurrence** (course meetings). A *derived aspect* of the term referent, owned by the term's definition. Its inputs are the start, end, pattern and skip aspects. Its instances are occurrences keyed by date, not referents. One instance becomes a referent only when something refers to it: cancel one Wednesday, comment on a meeting. It is then an explicit override that names the occurrence it replaces (iCalendar's RECURRENCE-ID). Spring break is a stored aspect of the term, a list of skipped occurrences.
- **Effective-dated value** (pace from meeting 3). This is *valid time*, which the kernel's operation log does not give. The log says when the pace was edited, not from when it applies. `pace@op` is a capture point in transaction time. Options:
  - pace segments as referents `part-of` the club, each with `from` and `rate` aspects, read by `reach`;
  - or an aspect whose representation is a time series.

  Overwriting a prop, as I did, destroys the plan for meetings 1 and 2.
- **Alternatives** (round 2's lodging). A *choice* referent ("lodging for night 1") with a link aspect listing candidate referents and a stored `chosen` aspect. `refers` loses the fact that they exclude each other.
- **Constraint** (the rotation rule). A *definition* that owns a derived `violations` aspect on each planting. Its inputs are the bed, family and year aspects of every planting `part-of` the garden. A rotation *proposal* is behaviour (code), and belongs to a definition, not to the interpretation list.

## Friction this round [ran]

- **The scene crashed on a prop named `n`, and the crash lost accepted writes.** A lens over things carrying `n=17` raised `TypeError: dict() got multiple values for keyword argument 'n'` (`scene.py` line 529). The CLI died without saving. The four writes before it in the same batch had printed `ok … [e13]…[e16]`, and `history` ended at e12. **Receipts said accepted; the events were gone.** This is a failure-atomicity defect independent of the lens.
- `create … y=2025` was accepted with no warning, and `y` was not stored (probably a geometry name). The frame `$yr.y` then filled empty, and `prop:year=` with an empty value became *presence*. The grid silently showed every planting in every year.
- `derive due = …` is refused ("that name is taken"). It should say *by what*: `$due`.
- `over $tags as <name>` is refused, so a list field cannot be a named frame.
- `only when` does not fill frames, and does not refuse a value test (`$wd=Mon`). It prints absence for everything.
- I ran the garden seed twice by mistake. The refusal on the duplicate title ("'Bed A' names 2 things") stopped the batch, and two undos repaired it. That is the new stop-on-refusal working as intended.
