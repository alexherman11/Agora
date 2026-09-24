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

**A5. Noise that hides the signal.**

`only when $wd=Mon` over 14 days was accepted. It printed `(absent: not $wd=Mon)` 14 times, Mondays included (the part's own `derive wd` is not yet visible to its own `only when`).

"Everything prints" produced 14 lines of true-looking absence and no Mondays.

**A6. A silent empty value.**

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

1. Fix the four silent paths: `$n` in instances, fallback count reset, refusal of `only when` value tests (or a real `where`), and refusal of frame shadowing.
2. `where` on repeats with printed tests, and **coalesce as the first `if`** (it prints its branch).
3. Printed arithmetic, lowered to named steps, with rounding and a conservation check.
4. Valid-time segments, with a word that picks the segment in force.
5. A per-viewer state word: printed, not journaled.
6. Gestures may call only versioned definitions whose effect is previewed.
