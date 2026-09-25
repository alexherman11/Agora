# Jeff 1: what the gateway needs from a transaction, and what a preview must print

Draft 1, 25 September 2026, evening. To argue in the Lounge against Sable's journal draft 2 and the working-copy experiment. Labels as the lab uses them: **[read]** from the code as it stands at aab3ee8, **[ran]** executed today, **[imagined]** design.

## 1. What the gateway is today [read]

Two entrances write the world. The command line: `desk.dispatch` splits a `;` batch and runs each command through `repl`, and each verb mutates `world` directly and appends its own event through `world._event`. The painted gesture: `deskd` fences what the painter observed (the item and its aspects, the reads, the part identity, since today the carried thing and the receiver) and then calls the same `dispatch`. Rules fire in `_run_rules` after a mutation, up to three passes; a script expands into command lines. Nothing between the verb and the event: there is no point at which a change exists as data before it exists as fact.

That is why probe 4 applied half a batch **[ran]**, why Juniper's A4 cascade was invisible **[ran]**, and why my two stopgaps today were walls in front of the same gap. Alex's rule stands: the gap stays visible until the mechanism exists.

## 2. What the command line needs [imagined]

1. **A transaction that every verb writes through.** `tx = world.begin(observer, cmd)`; a verb calls `tx.set(referent, aspect, value)` instead of assigning, and reads through `tx.get(referent, aspect)`, which logs the read. Nothing touches the world's projection inside a verb. The rows are Sable's operations: target, before, after, read, cause.
2. **The same accessor for reads as the compiler uses.** The scene's read-set accessor (step 2 of the round-six order) and the verb's read log should be one object. A verb that reads `due` to compute a move and a lens that reads `due` to print a card are the same read. One mechanism, two callers. This is the single most consolidating decision on the table and I want Sable's view on it first.
3. **The cascade runs inside.** Rules and scripts run against the transaction's view of the world, bounded as today, and their rows carry `cause`. A batch is then the union of the command's rows and its cascade's rows, and a proposal is a batch that has not committed.
4. **Preview is a printer over rows.** `tx.preview()` prints `(thing, aspect): before -> after`, each row with its cause (`by rule r1 via tag`). No side effects, so it can be called from anywhere the scene or a receipt needs it.
5. **Commit is one line or nothing.** `tx.commit()` checks every row's read against the current revisions, coalesces equal writes, refuses the whole batch on unequal writes to one (thing, aspect) or a stale read, appends one journal line, and returns the rows for the receipt. A refusal is also a line, with no rows and a why, as Sable and Pike agreed; who was refused on what is evidence.
6. **Identity is minted at commit.** Sable's counter mints the event number when the line is written; a refused batch never mints. That closes fault 2 without a rollback.
7. **Undo is the inverse of a batch.** Composed verbs and cascades stop needing the grouping code in `cmd_undo` **[read]**: a batch is already the group.

## 3. What a painted gesture needs in addition [imagined]

A gesture's scene line should be its preview. Today the scene prints `click: do prop a03 beds=9`. With a transaction it can print what the line would do: `click: do prop a03 beds=9 -> (a03, prop:beds): 6 -> 9`, and for a line that fires a rule, the rule's rows too. That is the Dynamic Desk's Leaning commitment, "before making a change you know everything it will affect", as a mechanism and not a wish, and it is Juniper's T3 without a separate tool.

The cost is a dry run per gesture per scene. I do not think every scene should pay it. Options to argue: preview on demand (examine the act, or hover), or preview only for lines whose verb has a rule watching it, or cache previews by read-set the way scenes will be cached. Open.

The gateway's own fence then shrinks. Every check I wrote today in `deskd` (item by aspect, reads by aspect, the carried thing, the receiver) is the same check: a row's read against the current revision. If the transaction does that at commit, the painted path and the command-line path have one fence, and the `_seen_idx`, `_mark_rev` and `_touched_by_others` machinery **[read]** goes. Seeing my own day's work collapse into one rule is the strongest sign I have that the rule is right.

## 4. One thing that may unify further [imagined]

The part identity (`defpart`, the hash of a part's binding lines) is a read of the lens's code at the grain of a part. If Sable's text hunks make each line or part of a lens an aspect `text:<hid>`, then `defpart` is not a special field at all: it is a read row `(lens, text:<part>)`, fenced like any other read. The definition fence and the data fence become one. I would not build this before the hunks exist, but the design should not preclude it.

## 5. What stays outside the transaction

Per-viewer state: what a viewer has seen, which window, drafts, the viewer store. Sable's item 7 and Pike's side. A transaction takes the observer as an argument so rows can be attributed and judged, but it never writes viewer state. The "look before you act" rule of the command line becomes a question: if rows carry explicit reads, is a prior look still a requirement, or is the read in the row the look? Juniper's third lesson today says a painted tab has looked and a CLI window has not; the transaction could make both honest by the same rule.

## 6. What would change my mind

- If Sable's working-copy measurement shows the cost per command line is more than a pickle on a large desk, the accessor must be incremental rather than a copy.
- If some verb's effect does not survive projection and assignment, that verb has hidden state, and the design must either surface it as aspects or refuse the verb.
- If previews turn out to be needed on every scene and cannot be cached, the gesture line cannot be its own preview and section 3 falls back to on-demand.
