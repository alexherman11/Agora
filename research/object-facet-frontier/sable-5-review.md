# Sable 5: review of POSITION.md

23 September 2026. I read the whole markdown twin.

## 1. Misstatements of my position or evidence

- **§2.7** "writer must produce edits the CRDT can place… forces a diff to guess". This is backwards for one writer: whole text kept 42 of 50 anchors, fine-grained edits kept 37. **Fix:** "The measured costs are moves (a diff drifts silently) and concurrency (merged whole-text writes garble prose)."
- **§5.2** "kept every anchor on its text". It kept 1 exact and 4 partial. **Fix:** "every anchor overlapping its text: one exact, four partial". Add the limits: one document, my own oracle, and a rewrite I wrote, not a model.
- **§5.4** Use the round-4 counts: 2 same-as, 2 narrower, 2 distinct. **Four** disagreements were hidden (steward/manager on a20 and a26, hazard/hazards on a24 and a28), not two.
- **§2.3** "two people invent…" They were two model actors that I briefed. The LambdaMOO manual says reparenting removes properties defined by old ancestors that the new parent does not share. The loss on `recycle` is my inference.
- **§7.1** "stored or derived" contradicts the strike list quoted just below it; drop "or derived". Also, Automerge cursors do not "say which" state they are in; the gateway must add that.

## 2. Unsupported claims, with fixes

- **§2.5** "Merges … use the same rule": conflict detection does, but merge still refuses as a whole. "Verified": by Jeff only; say so.
- **§2.6** State that the *record* must be operations. The gateway can produce them from whole-text writes.
- **§2.10** `via` needs an interpretation, `present`, that is not on Pike's list.
- **§1** "every failure … came from a copied value": the appearance-keyed lost update, the move drift, the merge garbling and `$item` did not. Limit it to binding failures.
- **§8.2** "a week of work": nobody estimated this.
- **§8.3** "could be wired": the desk is Python and the experiment is Node; nothing was tried. Anchored comments (`comment on=`) must come first, or the gateway preserves nothing.
- **§8.4** "first minter owns" is itself policy. List it as Alex's choice.

## 3. Dissent (Sable)

§7.3 says the text aspect "should be a CRDT sequence". My executed result credits the **gateway**, not the CRDT. The quote-fenced writer needs only element identity and one write path. It would do the same over plain strings, with the gateway mapping the anchors. A CRDT earns its tombstones and its dependency only for writes made away from the gateway, and run (e) shows what its merge does to concurrent prose. AGENTS.md routes every authoritative write through one gateway. **Wording:** "text needs element identity; a CRDT is the implementation when writes happen offline." I would change my mind if Rooms or offline phones become near-term. — *Sable*

## 4. The concept most under-taught

The fence, the text gateway, merge, capture and the read-set are taught as five mechanisms. They are one idea. Add after §2.5:

> **What you read is the currency.** Every act carries the revision its author observed: a prop write, a rewrite, a merged operation, a painted gesture, a captured value. The system compares it with what has happened since, at the grain of (thing, aspect). If nothing relevant moved, the act applies. Otherwise it is refused and shown with both sides, never guessed. Each mechanism here is that comparison at a different grain: a sentence for text, a prop for records, a derivation's inputs for views, the fork point for worktrees. A design that cannot say what its writer read cannot be made safe by any substrate.
