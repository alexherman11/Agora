# Juniper 6: attacks on the eight properties, an audit, and the household budget

Round six, adversarial seat. 24 September 2026.

- **[ran]** means typed in the desk (DESKD=off, head a318773, `scene.py` 41f8ba5a, `lens.js` 06428250).
- **[source]** means read in the lab code; line numbers are for those hashes.
- **[proposal]** means a suggestion.

**Sessions.**

- The fresh session `frontier-budget` has two worktrees, `@budget` and `@attacks`.
- The properties under test are the eight in HANDOFF-lens-language.md. They are called P1–P8 below.

## 1. Lenses that obey all eight properties and are still wrong [ran]

Every lens below is pure (P1), acts only through desk commands (P2), prints (P3), keeps no hidden state (P4), lives as a note (P5), binds as the desk allows (P6), needs no host code (P7) and terminates (P8).

**A1. Scope: a shadowed frame, silently accepted.**

```
x : column, of tag:t as a, each y
y : column, of tag:t as a, each z
z : text "$a.title under $title"
```

It printed `z a03 "Alpha under Alpha" · read a s02 title=Alpha` under *both* outer rows. The inner `as a` replaced the outer one, and nothing said so.

The compiler refuses `as title` ("would shadow a built-in name") but not a user frame shadowing a user frame. Everything printed, and the meaning was still lost.

**A2. Meaning: the right provenance on the wrong calculation.**

`r : text "$title due $d", derive d = day-n $a.start $a.week` printed `Alpha due 2026-10-06 · d = day-n(2026-10-01, 6) = 2026-10-06 · read a s02 start=2026-10-01 week=6`.

The inputs are printed perfectly. The meaning is wrong: week 6 is not day 6. P3 guarantees that a reader *can* check, not that anyone will.

**A3. A state machine in the lens note's own props, shared by every viewer.**

```
ta : text "Show A", role tool, on click do prop tabs tab=a
tb : text "Show B", role tool, on click do prop tabs tab=b
pa : text "Panel A: the plan", only when tag:lens,prop:tab=a
pb : text "Panel B: the budget", only when tag:lens,prop:tab=b
```

Ben "clicked" B (`do prop tabs tab=b` as ben). Juniper's next scene printed `pb "Panel B: the budget"` and `pa (absent …)`, and history gained `e7 prop a13 tab=b by ben`.

That is a program with mutable state, built from nothing but props and gestures. It is also wrong as UI: one person's tab switches everyone's, and every click is a journal event that undo must step through.

**A4. The program moves into scripts and rules, which the scene cannot show.**

- The setup: `script tidy = do tag $1 add=done; do retitle $1 title="(done) $1.title"; do prop $1 week=0`, and `rule on tag do prop Beta week=99`.
- The lens gesture: `on click do run tidy $item`.
- The scene printed only `click: run tidy a03`.
- Running it made four events (e9–e12). One of them, `e10 prop a05 week=99 via rule r1`, changed **Beta**, a thing the gesture never named, so the gesture's fence never covered it.
- The `script` and `rule` definitions produced **no events**: e7 is followed directly by e8.

Every effect went through the gateway, attributed and undoable, yet the scene could not say what the click would do. **This is the worse-JavaScript route in the prototype today.** The code has not gone into the lens. It has gone beside it, into global definitions outside history.

**A5. Noise that hides the signal.** This is the same finding as Sable's probe 5; I count it once.

`only when $wd=Mon` over 14 days was accepted. It printed `(absent: not $wd=Mon)` 14 times, Mondays included (the part's own `derive wd` is not yet visible to its own `only when`).

"Everything prints" produced 14 lines of true-looking absence and no Mondays.

**A6. A silent empty value.** This is distinct from Sable's probe 6, where a prop `n` shadowed `$n`. Here, no prop is involved.

In the budget, `d : text "$n days here"` under a 15-row repeat painted `" days here"` fifteen times.

- `$n` is `""` inside an instance (`scene.py:632`).
- The repeat header printed `15`, so the text printer knows the number and the painted words do not.

**What the properties wrongly forbid or refuse [ran unless marked].**

- **F1. Per-viewer view state.** A tab, a sort order, a collapsed section. P4 allows only world data or *printed per-viewer drift*, and a lens can read neither kind of per-viewer state. A3 is the only way to write it, and it is shared and journaled.
- **F2. A 13-month lease.** `days-from 2026-09-01 2027-09-30` printed `(uninterpretable: … not a span of at most a year)`.
- **F3. A plain year view.** 365 days × 5 parts gave `ERR this lens makes more than 1500 scene nodes`.

  The last-good fallback did **not** engage, although the 4-part version had compiled a moment before. `_compile` passes the same `count` list into the fallback build (`scene.py:747–770`, check at `569`), so the fallback starts already over budget.

  A bound (P8) should degrade (clamp, page, fall back). It should not refuse a lens that was working.
- **F4. Effects that are not world writes.** Copy the three amounts to the clipboard to pay by bank transfer; open the landlord's portal. P2 forbids them. **[proposal]** Admit them as named, printed viewer effects that leave the world unchanged.

## 2. Audit of the prototype against the properties [source, with ran where marked]

| Property | Violation today | Where |
|---|---|---|
| P1 pure | The `worktrees` row source reads *other sessions' pickle files* from disk during compilation, and `pickle.loads` them. The input is outside the world, and loading a pickle is code execution | `scene.py:147–153` |
| P2 effects via gateway | Gestures may `run` scripts and trigger rules whose definitions are not events (A4). The painter POSTs `/api/observe` straight into desk memory | `lens.js:117`; scripts and rules [ran] |
| P3 everything prints | `$n` is empty in instances (A6). Painter-only behaviour that the scene does not state: an empty edit is silently dropped; a drag is clamped at ≥0; `$x`/`$y` are filled with `String.replace`, so only the first occurrence is replaced, and a title containing `$x` would receive the coordinate | `scene.py:632`; `lens.js:65, 74, 56, 77` |
| P4 hidden state | A last-good lens cache on the desk object, not in the journal. Per-actor read positions feed the `actors` rows. In the painter, while `busy` it stops refreshing, so an editing viewer sees an older world than the text printer | `scene.py:750–752, 141`; `lens.js:60, 72, 88` |
| P5 lens is world data | Mostly holds. The fallback text shown is a cached copy, printed as `shown_rev`, not a world revision you can open | `scene.py:747–770` |
| P6 bind referents | `lens <name>` and `find_lens` bind by **title**. Gesture lines idiomatically name targets by title (A3's `prop tabs`). `the prop:role=trip` is a query, not a referent (ambiguity is refused, which is good) | `scene.py:733–745` |
| P7 no host per app | Row sources are per feature in the compiler (`sections` hard-codes the document app's `##` convention; `actors`, `events` and `worktrees` are desk features). Interpretations are Python functions. Each new domain adds host code | `scene.py:106–155, 344` |
| P8 bounded | Holds, but by refusal (F2, F3), and the refusal disables the fallback | `scene.py:569–570` |

**Verdict on the eight.**

- **P1, P7 and P8** are checkable by reading code and by a node count.
- **P3 as worded is unenforceable** ("everything prints" is satisfied by A5's noise). It should be restated as *no silent value*.
- **P2 is incomplete.** It must cover the effect *preview*, not only the effect *path*.
- **P4** needs a third category: per-viewer state that is printed and not journaled.
- **P6** must forbid titles as bindings.

**Missing property:** no computing in data. See the budget below. Of the three the prototype collects there, the hand-computed copy is the worst failure.

## 3. The household budget, fourth task [ran]

**World (in `@budget`).**

- A house doc: `month=2026-10-01 monthend=2026-10-31`, plus reasoning.
- Ana, Ben and Casey as persons.
- Rent 2400, Utilities 180 and Internet 60 as bills, all linked `part-of`.
- A `split` lens that follows the house and repeats over bills and people.

**Counts (writes are events; repairs and silent wrongs as in the trip script).**

| Step | Writes | Repairs | Silent wrongs before repair |
|---|---|---|---|
| 1–2 seed, people, bills | 13 | — | — |
| 3 split | 7: **6 of them hand-computed copies** (`third=800/60/20`, `owe=880` ×3) + the lens | — | 0 |
| 4 Casey leaves 15 Oct | 1 target + 1 exploratory rewrite | **4**: three `owe` values + a lens rewrite to drop "each pays" | **6** (3 owes, 3 "each pays"), plus A6's empty `$n`, plus **1 penny**: 1062.86 + 1062.86 + 514.29 = **2640.01** |
| 5 November, rent 2550 from the 1st | 2 target + 1 "October" lens | **3** (Ana 1395, Ben 1395, remove Casey's `owe`) | **4**: 3 stale owes, plus the captured October statement printing `Rent 2550` under `captured month=2026-10-01` |
| 6 add Cleaning 90 | 2 | **2** | **2** |
| **Total** | **36** | **9** | **14** silent (+2 visible: `days-from` uninterpretable for Ana and Ben, who have no `leave`) |

**Which step needs proration.** Step 4. Casey's October share is `total × days_Casey / Σ days`.

**Can `where` over days express it?** Only the day count, and only half of it.

- `days-from $h.month $p.leave` printed `= 15 rows` for Casey. A bounded range *is* a `where` over days.
- It printed `(no p.leave on s04)` for Ana and Ben, because the person who stays has no leave date. The count needs **a default** (the month end when there is no leave). That is `if`/coalesce by another name.
- The count cannot be used as a number: `$n` is empty in instances.
- The share needs `×`, `÷` and a **sum across the people repeat** (Σ days = 77). No `where` provides that.

**Valid time.** Step 5 overwrote the rent. The October statement cannot be rebuilt: `capture` fixes the frame's `month` but not the bills' `amount`, so the captured statement is silently wrong. Rent needs dated segments (2400 until 31 Oct, 2550 from 1 Nov) and a word that picks the segment in force for `$h.month`. That is the valid-time relation from juniper-3.

**What arithmetic and `if` must print before I trust the number [proposal].**

```
end.Ana   = if leave missing → month end = 2026-10-31   (branch: missing)
end.Casey = if leave missing → month end, else leave = 2026-10-15   (branch: present)
days.Casey = count days-from(2026-10-01, end.Casey) = 15; Ana 31; Ben 31; Σ = 77
total.Oct = sum bills in force on 2026-10-01 = rent 2400 [seg from 2026-01-01] + 180 + 60 = 2640
share.Casey = 2640 × 15 ÷ 77 = 514.2857 → 514.29 (round half-up, cents)
check: 1062.86 + 1062.86 + 514.29 = 2640.01; remainder −0.01 to the largest share (Ana) by rule → 1062.85
```

Every line names its inputs and their sources, which segment was in force, which branch an `if` took, the rounding rule, and the check that the parts sum to the whole. Without the last line the penny is a silent wrong **in arithmetic that printed perfectly**. Printing inputs is not enough for quantities: a derivation over a whole needs a conservation check.

## 4. Ways of knowing we are on the right side [proposal, each executable]

1. **The task suite is the test.** Run the trip, course, books, garden and budget scripts, each with its changes. Fail on any repair or any silent wrong after a change. Today the budget fails with 9 and 14; H2 passed the trip with 0 and 0. The same suite measures growth: record the host lines added per *task* made to pass. It is linear if each task needs its own host code.
2. **A lens lint in the desk.** Compile every lens in a session and report:
   - shadowed frames (A1);
   - value tests in `only when` (A5);
   - `$` names that fill empty without a marked absence (A6);
   - gestures that `run` scripts or trigger rules (A4);
   - title bindings (P6).

   Fail on any.
3. **Gesture preview.** For each gesture, dry-run its line in a scratch fork and print the events it would make. Fail if it touches anything the line does not name, or if a definition it depends on is not an event.
4. **Retitle everything.** Retitle every thing and lens in the suite and rerun. Fail if any scene changes.
5. **Two viewers, one lens.** One viewer changes a tab or sort. Fail if the other viewer's scene changes, or if the journal gains an event.
6. **Degrade, don't refuse.** A 13-month span and a 365 × 5 year view must clamp or page with a printed note, and the last good version must still show.
7. **Conservation checks.** Any derivation that divides a whole must print that its parts sum to it.

## 5. From the user's side: what does a lens give me that a small JavaScript app would not?

From these runs, four things, each with a condition.

1. **I can read what I am looking at and why.** "Day 1, 2026-10-17 · read start=2026-10-17" told me the calendar followed the trip. I counted every silent wrong in five tasks by reading scenes. A small app would show me a number. *Condition:* no silent values. A6 and the penny show we are not there.
2. **My stuff outlives the view.** Removing the calendar left the trip, its reasoning and its comments intact (trip step 10). A small app keeps the state inside itself. *Condition:* no computing in data. The budget's `owe=880` copies are the app's state leaking into mine, which is worse than an app.
3. **The view is mine to change like a note.** Rewrite it, undo it, fork it into a worktree, copy a neighbour's. *Condition:* the program must not escape into scripts and rules the note cannot show (A4).
4. **What a click will do is written next to it** ("click: do prop a09 day=…"), and it is refused if the world moved. A small app's button does whatever its code does. *Condition:* preview the full effect (A4 again).

**The honest cost today.** A 10-line JavaScript app would have split the October bills correctly, penny included. The lens needed 6 hand copies, 9 repairs and 14 silent wrongs. Without printed arithmetic, defaults and valid-time segments, the lens is currently *worse* than the small app at the one everyday thing everyone does with money.

## 6. Build-out, from this seat [proposal; Sable and Pike own the architecture]

In the order the budget and the attacks demand:

1. Fix the silent paths:
   - `$n` in instances;
   - the fallback count reset;
   - refusal of `only when` value tests (or a real `where`);
   - refusal of frame shadowing;
   - refusal of `prop:k>v` (§7).
2. `where` on repeats with printed tests, and **coalesce as the first `if`** (it prints its branch).
3. Printed arithmetic, lowered to named steps, with rounding and a conservation check.
4. Valid-time segments, with a word that picks the segment in force.
5. A per-viewer state word: printed, not journaled.
6. Gestures may call only versioned definitions whose effect is previewed.

## 7. Against Sable's R1–R8, and the timeline shape for the budget [ran unless marked]

Sable's five probes are not repeated here. These go past them.

**R3 perturbation test, broken by a negative read.**

The setup:

- The lens is `x : column, of tag:t, each r` with `r : text "$title"`. It printed `2 of tag:t` (Alpha, Beta), and no read line names Gamma.
- `do tag Gamma add=t` (e19) changes an aspect of a thing that is **not in the printed reads**.
- The next scene is `3 of tag:t` with Gamma added.

So the perturbation test fails for every query, not because of a bug but by construction. A query reads the tags of *every candidate*, including those it rejects. `the prop:role=house` is the same: another note gaining `role=house` turns the frame `(ambiguous)`.

**[proposal]** R3 needs a second kind of read: a **predicate read**, `(selection text, candidate set)@world`, printed on the repeat header. The fence must then refuse a gesture if the membership changed, not only if a member did.

The cost is real. A fence on `tag:t` conflicts with *every* tag write in the world, which is Astra's over-blocking fingerprint arriving by another road. The two workable options are an index keyed by predicate, or an accepted over-block that is printed.

**R2 determinism, broken by a look.**

- Lens: `of actors`, printing `$name read to $read, behind $behind`.
- It printed `ben read to 6, behind 15` at `world @21`.
- Ben then ran only `look`. No event was appended; `history` still ends at e21.
- Juniper's next `scene who` at the **same** `world @21` printed `ben read to 21, behind 0`, and Juniper's own line moved too.

The scene is not a function of (L, W, V) unless V includes *other viewers'* read positions (`desk._per`, `scene.py:141`). Viewing a scene also changes the next one: the viewer's own read position moves.

**[proposal]** Either looks become world facts (events), or the `actors` source moves into V and prints as `~` per-viewer drift.

**R6 total resolution, three more silent paths.**

- **A1 (§1).** A user frame silently shadows a user frame. This is not the built-in collision Sable probed.
- **A comparison inside a selection.** `of prop:role=member,prop:to>$it.date` was **accepted** and printed `0 of prop:role=member,prop:to>2026-10-14 (empty)` on every day. The parser read `to>2026-10-14` as a prop *key* and checked that it was present. A misspelled operator therefore became a silent empty, which is the worst failure in POSITION 2.1's table, and R6's resolve stage must cover selection syntax as well as `$` names.
- **R7, fallback.** The refusal kills the fallback (§1, F3). R7 should say a cap never disables last-good.

**R1 purity.** It holds for writes. But the `worktrees` source `pickle.loads` other sessions' files during compilation (`scene.py:147–153`). That is a read outside W and V, and it executes whatever those pickles contain. R1 should say "reads only through the accessor", not only "appends no operation".

### The timeline shape against the household budget

The shape: rent and membership are timeline aspects (dated segments with element identity), each share is a derivation over overlapping segments, and `at <date>` is library.

**It survives the housemate leaving mid-month, and it exposes a decision my hand arithmetic made silently.**

- Membership is three segments: Ana `from 2026-01-01`, Ben `from 2026-01-01`, Casey `from 2026-01-01 to 2026-10-15`.
- The natural derivation over overlapping segments is **per day**: each day's cost (the rent segment in force `at` that day, plus the other bills, divided by the days in the month) is split among the members present that day.
- The same mechanism also handles a rent rise on the 15th of a month, without a separate word.

It gives a different answer from my step-4 hand copies [computed, python]:

| Policy | Casey | Ana, Ben each | Sum after rounding |
|---|---|---|---|
| Person-days (what I stored by hand) | 2640 × 15/77 = 514.29 | 1062.86 | 2640.01 |
| Per-day split among those present (what the timeline derivation says) | 15 × (2640/31)/3 = 425.81 | 1107.10 | 2640.01 |

The difference is 88.48 on Casey's bill. Both are defensible:

- Person-days: everyone pays the same rate per day lived.
- Per-day split: the ones who stay carry the whole flat after Casey goes.

**This is a policy, and it must be a named, printed choice** (`split per-day` or `split per-person-day`). It should not be an accident of whichever formula an author typed. A JavaScript app would have picked one silently too. The lens's advantage exists only if the policy prints.

Both policies also leave the penny, so the conservation check from §3 is needed whichever wins.

**What the desk could not do [ran].** Deciding "present on this day" needs `from ≤ date ≤ to` with a missing `to` meaning open-ended. Today that is not expressible: the comparison is the silent empty above, and Ana's open segment has no `to`. With `at` and interval overlap as library, over a timeline aspect, it would be.

### Does "a proposal cannot read its own write" block any budget step? [imagined, step by step]

**No.** Every step reads the pre-state and writes independent rows:

- **Casey leaves.** One write: close her segment (`to=2026-10-15`). Shares are derived.
- **Rent rises.** One write: add the segment `{from 2026-11-01, 2550}`. If segments store `to`, a second, independent write closes the old one. It reads the old segment's id from the pre-state, not from its own write.
- **Dana replaces Casey.** Mint Dana, then add Dana's segment referring to `$new.1`. Sable's mint placeholders cover this.
- **Close October.** Capture three shares as a stored statement. Each capture reads derived values from the pre-state.
- **Add a bill.** Mint plus link, one proposal.

The only near-miss is **"settle the penny"**: write an adjustment row so that the stored statement sums to the total. It reads the three rounded shares (derived, pre-state) and writes one adjustment. No read-your-own-write is needed, provided the rounding and conservation check live in the derivation and not in a second gesture.

So the budget does not need read-your-own-write. It does need, in order:

- interval comparison with open ends;
- `at` over a timeline;
- a sum over a repeat;
- `×` and `÷` with rounding;
- a named split policy;
- the conservation check.
