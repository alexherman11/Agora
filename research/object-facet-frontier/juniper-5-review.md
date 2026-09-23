# Juniper 5: review of POSITION.md

## 1. Misstated counts (checked against juniper-2 and juniper-3)

- **5.1, "ten-step script".** It has eleven steps. Step 11 (two windows) produced every wrong-target count. It ran before 5.3's window fence.
- **5.1, "Commands".** These are writes; reads are not counted. H2's 29 includes one authoring retry.
- **5.1, "Repairs (edits to things whose meaning did not change)".** The measure is writes beyond the target writes that were needed before every check was correct. D's repair re-edited the target doc itself.
- **5.1, "Wrong outputs shown without warning … 2 (1 silent)".** The label contradicts the cell. Write "wrong outputs (silent)".
- **5.1, Hybrid old words, "dates not shown".** Day 1's date was shown.
- **5.1, "one command".** The command sets `start` and `end`, and `end` is a stored copy.
- **5.5, course "Repairs 2".** That is two changes at 1 repair each, not "each task's one change".
- **5.5 and 8.1, "reached … at four times the rate".** Pike's trigger is the list passing 12. 4 + 7 = 11, so it was not reached, though it nearly was within hours. "Four times" was my loose wording; strike it.
- **7.5, "settled".** The grid count was a thought experiment, partly from recall.
- **7.5, "free … nowhere else".** Anchors are free in any CRDT sequence, including rows kept as list elements. Add Sable's check that sort kills row ids.

## 2. Unsupported claims, with fixes

- **§1, "survives … copy".** It does not; §2.1 says a copy gets a new id. Say instead: "a copy is a new referent recording its origin".
- **§1, "every failure … came from a copied value".** Several did not: the misplaced append, the two-window lost update, anchors on moved items, drift, and the crash below. Narrow it to "every repair".
- **§1, "Derived values live".** The rule is signed, not built. Say "will live".
- **§3.** There are no evidence labels. The twenty-year outcomes are thought experiments, and the "museum" phrase needs a source.
- **§4.** The fork axiom comes from Agora.md. "A conventional app joins" and "one person can hold it" were never executed; say so.
- **§8.1, "no task needs an if inside a derivation".** Two of mine do:
  - The course due date is "after the break, add a week".
  - The books pace changes from meeting 3.

  Only structural words absorb these. My recommendation was structural words plus arithmetic, not arithmetic alone.
- **§8.6.** Put failure atomicity first. A scene crash lost four writes whose receipts said ok. Then add the structural words that 8.1 needs.

## 3. My position on 8.1

Take structural words for time together with printed arithmetic for quantities:

- **Structural words:** `every` (step, weekdays, skip), `where`/`pick` over derived rows, frame fill in `only when`, and numeric `<`/`>`.
- **Printed arithmetic:** `+ − × ÷` plus `running`, with inputs printed and no `if` inside a derivation.

**The fourth task:** a shared household budget. It has monthly bills split three ways, a housemate who leaves mid-month (proration), and a rent rise from the 1st. If proration cannot be written as a `where` over days, adopt the expression language.

## 4. Under-taught concept: valid time

Add as §2.8a:

> **When a value is true, versus when it was written.** The edit log records when something was written. Plans also need when it is true: pace 100 until meeting 3 and 80 after, a rent rise from 1 November, a bed resting in 2028. Overwriting the pace erased the plan the first meetings were read on, and `pace@op` cannot recover it: it answers "what did we say then", not "what applies on that date". A value that changes on a date is a sequence of dated segments, each an owned aspect with `from` and `value`. None of the five nouns provides this yet.
