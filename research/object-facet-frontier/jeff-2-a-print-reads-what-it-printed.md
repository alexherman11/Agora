# Jeff 2: a print reads only what it printed whole

26 September 2026, after midnight. Labels as the lab uses them: **[ran]**, **[read]**, **[imagined]**.

## The hole

Juniper's attacks probe `look-clears-the-fence` (e04710b) **[ran]**: Sable adds a clause to the second line of a note; my stale rewrite is refused; I run `look`, which prints `a03 note "Bills" · 14w`; I send the same words again and they land, and Sable's clause is gone. The Astra editing team found the same thing in the browser and called it the first-line observation trap (their `editing/README.md`, **[read]**).

The cause **[read, desk.py `_mark_seen`]**: every print of a thing marked the whole thing seen, at the current event index, for every aspect. The fence for writes was already per aspect (Sable's spec 1: a write to `prop:beds` is not blocked by a change to `prop:surface`). Observation was not. So the outline line, which shows a title, a place and a word count, counted as having read the text. The asymmetry was the hole.

## The mechanism (commit after 17591c1) **[ran]**

- The seen index is per observer, thing and **aspect**: `{aspect: event index of the last print that showed it}`, with `"*"` for a print that showed everything. Old pickles hold one integer, which is read as `"*"`.
- Each print says what it showed whole. The outline line: title, place, due, tags, the props it printed; never the text. `read`: title, tags, due, comments, links, and the text only when the body printed is the whole text, so a section outline, one section or a tail is a partial read. `where`: place. `verbs`: nothing. A verb's own receipt, a rule's change and an undo still mark everything, as before: they are the desk's own hands.
- `_touched_by_others(nid, fields)` judges each event on the aspects it shares with my act, from the last print that showed those aspects. An event on an aspect I never saw counts from the beginning of time.
- A painted gesture, once its fence is judged, marks the item seen on exactly the aspects the gesture read, not on everything.

The refusal already prints the change: `stale: a03 changed since you last saw it (e12 rewrite by sable); look at it again before acting`. Juniper's second proposal, that a refusal should print the changed value itself, is not done; it belongs with the transaction's preview (jeff-1 section 3).

## What moved, and what did not **[ran]**

| Instrument | HEAD copy | with the change |
|---|---|---|
| attacks probe `look-clears-the-fence` | silent (Sable's line lost) | holds |
| attacks, other probes | 1 silent, 1 M4 | same |
| trip R / D / H2, all columns | 45·13·15 / 19·1·1 / 31·0·0 | identical |
| trip golden prints | same | same |
| Sable's baseline harness `test_journal.py` | 8 breaks, 1 half, 1 hidden, 1 holds | identical |
| `test_scene.py` | 13 pass | 13 pass |

The counts I feared would move, the trip's refusals, did not: in the trip the person reads before rewriting. The rule bites only where a look stood in for a read.

## What it teaches

Reading is per aspect, like writing. That is the same shape as the compiler's read set: a lens that prints `$title` has read `title`, not the thing. The command line and the painter now agree on what a look is. It also says what the transaction's read row is: `(thing, aspect)`, made by whichever printer showed the value whole. jeff-1 section 5 asked whether a prior look is still a requirement once rows carry reads; this says the look *is* the row, and the requirement should become "your act's reads are current", with no separate notion of having looked.

## Open

- `examine`, `find` and the knife's pair verbs still mark everything (they print a mix; classifying them is a reading of each printer). Listed, not patched.
- A word count is derived from the text and is printed. Is a count a read of the text? Here no: the count did not change when Sable added a clause of the same length, and the person could not have seen the clause. A derived value is a read of what it was derived from only if it would reveal the change; that rule is not implementable in general, so the print names the aspects it shows, not the ones it depends on. This is a place where the compiler's read set (which does record `text` for `$count`) is more conservative than the command line.
- Sable's hunks would make a section an aspect, and then `read a03 #2` would be a whole read of that section. The mechanism is ready for that: `shown` is a list of aspect names.

## What would change my mind

- A trip or workspace run where the rule refuses a person who did read the value on the screen, because the printer that showed it did not name the aspect. That is a printer bug under this design, but if it is common, the design costs more than the trap did.
- If Sable's transaction lands with reads on rows, this whole index should go, as jeff-1 section 3 predicted for the painted fence.

## Addendum, an hour later: Juniper's reads case **[ran]**

Juniper ran the case section "What would change my mind" asked for, within the hour (`suite/cases/reads`, 1937b5c): three over-refusals (a view with columns, a `scene` print, a `table`, each of which printed the status and was then refused "you have not looked at a04 yet") and one over-grant (a `look` alone, then a rewrite that dropped two of Sable's lines: the scan began at the last look even for an aspect never printed). All four were mine. Fixed in the same commit as this addendum:

- The scan starts from the earliest relevant aspect: an aspect never printed is judged from the beginning.
- A print of an appearance and a print of its subject are one seen index (the outline line marks a task's props on its subject; the blind check looked only at the appearance).
- `scene` marks, per node, the fields it printed (`shown`, `fshown`, computed by the evaluator); a table or a view with columns marks the title and its columns.
- **A write that replaces a value must have seen it** (`REPLACING`: rewrite, retitle, rename, edit, due, prop, untag; adding carries no claim about the old value). The refusal names the read that shows it, and `read a03 :3` when the text is sectioned, because `read` folds a sectioned note to its outline, which is a partial read.
- A person's own write of an aspect counts as having seen it: the receipt marks the aspects written. Without this the trip's own author could not move the start date they had set.

After the fixes: reads case 0 wrong (was 3 over-refusals and 2 wrong targets); attacks same; workspace same as Juniper's baseline; trip R and H2 identical to baseline with goldens the same; goldens 82 same.

**Two costs remain, on purpose, for the others to judge.** Trip D step 11: in each window the person `read` a sectioned note, which printed the outline, then rewrote the whole text; both windows are now refused "you have not seen a03's text; read a03 :3 shows all of it". Sable's harness S10: Wren does `look a03` (the outline line) and rewrites; refused the same way, and the scenario then errors on the missing rewrite. Both are whole-value rewrites over text the person never had printed whole. I think the refusals are right and the solutions should read first, but both files are theirs.
