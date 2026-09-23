# Sable 4: operations and merge

Round four, foundations. 23 September 2026. These are three specifications written against the desk as it is today. They are not a decision.

**What I read in the lab's source before writing** [source]:
- `world.py`: `_event`, `undo`, and the subject edit path.
- `desk_moo.py`: `cmd_do` and its fence.
- `desk.py`: `_touched_by_others` and `_mark_seen`.
- `moo.py`: `v_prop` and `v_rewrite`.
- `worktree.py`: fork, diff and merge.

**What I checked by running** [ran]: the drift-probe values quoted below, in `frontier-sable`.

**The desk today, in brief.**
- An event is `{id, verb, target, args, undo, by, at, changed}`.
- `undo` holds a *snapshot*: `restore_props` keeps the whole props dict, and `restore_subject` keeps the whole subject.
- Undo refuses if any later event names the same target.
- The fence refuses if another actor's event named the node or its subject since this actor last looked. The one exception is a windowed reader, who is judged on revision alone.
- A worktree journals command lines and replays them against the base, all or nothing.

The three specs below change the unit of all of this from *(node, whole snapshot)* to *(referent, aspect, before → after)*.

## Spec 1. The operation record and partial merge

**Aspects in the desk today.** Each is written `(referent, aspect)`:

| What | Aspect key |
|---|---|
| title | `(s, title)` |
| text | `(s, text)`, written by sentence hunks (spec 2) |
| due date | `(s, due)` |
| tags | `(s, tag:<name>)`, one aspect per tag |
| one prop | `(s, prop:<k>)` |
| geometry | `(a, geom)` |
| placement and parent | `(a, place)` |
| surface layout and title | `(f, layout)`, `(f, title)` |

Links and comments are referents of their own. A comment is append-only, so it never conflicts.

**Operation record.** One command yields one *batch* of one or more operations:

```
{ op: "e57.2", batch: "e57", target: ["s04", "prop:beds"], before: "5", after: "6",
  read: "e31",          # the last op on this (referent, aspect) the writer had seen
  parent: "e31.1",      # the op this one supersedes on this aspect (causal parent)
  by: "wren", observer: "wren@tab2", via: "a06", cmd: "do prop a06 beds=6",
  merged: null | "<worktree name>", at, day }
```

- **Inverse:** `{target, before: after, after: before}`.
- **Batch:** keeps today's receipts (`[e57]`) and today's undo of a whole command.
- **`changed`:** stays as a derived list, for looks and rules.

**The fence** checks each operation of the command. It refuses only if some operation since the observer's `read` on the *same* `(referent, aspect)` came from another observer. The refusal names the aspect:

```
stale: s04 prop:beds changed since you read it (e32 by sable: 8 → 10)
```

A write to `prop:surface` no longer blocks a write to `prop:beds`.

**The two-window case.**
- The unit of "who saw what" becomes the *observer*, `(actor, window or session)`, not the actor. This removes `_touched_by_others`' self-exemption for windows, so Pike's F2 applies everywhere.
- Within one observer, a receipt still counts as a look.
- Two windows of one person are two observers. Each refuses the other's unseen writes to the same aspect and nothing else.

**Worktree merge by operations.**
- The worktree journals operations, not lines. A `mint` operation records each thing created there under a local id. On merge, mints get base ids first, and every target is remapped. The remapping mechanism already exists.
- Let F be the fork point. For each worktree operation, in order, look at the base's operations since F on the same `(referent, aspect)` that did not come from this worktree. Then:
  - none: **clean**. Apply it as a new operation carrying `merged: <name>` and its original `by`.
  - the base's latest `after` equals the worktree's `after`: **agreed**. Record nothing and count it.
  - otherwise: **conflict**. Hold it, and hold every later worktree operation whose `parent` chain runs through it.
- Clean operations apply even when others conflict. The merge is no longer all or nothing.
- Receipt:

```
ok merged drift-b: 18 applied, 3 agreed, 3 held (6 ops still in drift-b)
  ! a20 prop:condition   here: fair (sable e41)   there: good (wren)
  ! a28 prop:condition   here: poor (sable e44)   there: fair (wren)
  ...
  resolve: worktree take drift-b 1 | worktree keep drift-b 1 | worktree set drift-b 1 value="..."
```

- `take` applies the worktree's value as a new operation, with `parent` = the base's operation. `keep` discards the held operation and records that it was discarded. `set` writes a third value. All three are ordinary operations, and all three are undoable.
- A later `worktree merge` of the same worktree takes only new and still-held operations.

**The drift probe under this spec** [ran for the values; the arithmetic is mine].
- Of 61 writes, merging A then B gives 59 clean (3 of them agreed) and 2 held: `condition` on a20 and on a28.
- The desk today refused all 24 of B's writes.
- With the name relations of spec 3 endorsed before the merge, 4 more are held (6 in all): steward/manager on a20 and a26, and hazard/hazards on a24 and a28. The total becomes 55 clean and 6 held.
- The a24 pair ("floods after heavy rain" against "floods near bottom") is probably the same claim in other words. Flagging it is right; resolving it is a person's call.

**Undo of a merged operation.**
- It is the operation's inverse, fenced like any write. It applies only if the aspect's current value is still the operation's `after`. Otherwise it refuses and names the later operation.
- `undo e57` undoes the batch.
- `undo merge drift-b` undoes every operation that merge applied, newest first. It is atomic: if any of those aspects moved since, it refuses and lists them.
- Undo no longer blocks on *unrelated* later events. My round-1 `undo e12` failed because a link touched the same thing. Under this spec the link is its own referent.

## Spec 2. The write gateway for text

The text aspect's representation stays a plain string in this desk. Every write to it goes through one gateway. `rewrite` and `append` become clients of the gateway.

**Command.** `do rewrite a18 text="…" [read=e42]`. `read` defaults to the observer's last look at `(s, text)`, which the CLI already tracks.

**Gateway steps:**

1. **Base.** Reconstruct the text as of `read` by applying the inverses of later text operations to the current text. Each text operation stores its hunk's `before` and `after` and the quote around it.
2. **Diff.** Split base and new text into sentences: whitespace runs, and runs up to `.!?` or a line end. Each list item and each heading counts as one sentence. Compute hunks with a longest-common-subsequence diff.
3. **Apply each hunk,** in order:
   - Find `prev sentence + old + next sentence` in the *current* text.
   - Unique: apply it, with a character diff inside the hunk so anchors survive. Record one operation per hunk.
   - Not found, or found twice: **refuse this hunk only**, and show the current text beside it.
4. **Moves.** A sentence removed in one hunk and added unchanged in another is recorded as a `move-text` operation, not a delete plus an insert. For an edit combined with a move, the writer declares the move first:

   `do move-text a18 from="- Replace the washer" after="## Tasks"`

   `from` and `after` are unique sentence prefixes; the gateway refuses ambiguous ones. The anchors inside the moved span go with it.

5. **Anchors.** A comment gets an anchor with `do comment a18 on="the drip under the standpipe" line="…"`. The anchor stores a character range. The gateway maps it through every splice it applies:
   - text before the splice: unchanged;
   - text after the splice: shifted;
   - endpoints inside the splice: through the character diff, or collapsed and *marked* `(anchored text removed)`;
   - inside a move-text span: carried.

   This is the Automerge cursor behaviour without Automerge, because the gateway is the only writer.

**Receipt:**

```
ok rewrite a18 read=e42  [e57: 5 ops]
  applied 4 of 5 changed sentences (2 edited, 1 added, 1 removed); 1 move kept (c04 moved with it)
  refused 1 — changed since you read it (e51 by alex):
    you read:  "Bring gloves, a trowel and something warm to drink, because the east path floods and the morning will be cold."
    it is now: "Bring gloves, a trowel and something warm to drink."
    you wrote: "Please bring gloves, a trowel and a hot drink, since the east path floods and it will be a cold morning."
  comments: c02 kept · c03 on a refused sentence, unchanged · c05 kept
  to retry that sentence: read a18, then rewrite again (only refused sentences will differ)
```

**`history a18 text`** shows one line per operation:

```
e57.1 text a18 edit  "Last winter the tap…" → "The tap by the gate froze twice last winter…"  by jeff read=e42
e57.3 text a18 move  "- Replace the washer…" after "## Tasks"  by jeff
e57.5 text a18 REFUSED "Bring gloves…"  (changed by e51)  by jeff
```

A refused hunk is recorded as a non-mutating note, so the attempt is visible.

**What a model writer is told.** These lines go into `prompts/runtime`-style guidance and into `help rewrite`:
1. Read before you rewrite. `read` prints `read=eN`; the desk remembers it for you.
2. You may send the whole text. Sentences you did not mean to change must be byte-identical: do not re-wrap, re-punctuate or re-space them.
3. A refusal is normal, not an error. Re-read, then send again; only the refused sentences need to differ.
4. To move a sentence or list item, say `move-text`. Retyping it elsewhere orphans its comments.
5. Prefer several small rewrites to one sweeping one when others are editing. Refusals are counted per sentence.

## Spec 3. Name relations as events

**Owners of names.** A prop name's owner is the observer who first wrote it in this world. That is recorded in the first operation as `name: minted`. Later writers may write the name, and they are attributed. A lens or rule definition may claim a name it writes. Claiming is itself an operation, visible in `history`.

**Command.** `do relate <a> same-as|narrower|distinct <b> [via=<interpretation>]` creates a relation referent `rN`. `do endorse rN` records an endorsement. **Anyone may declare. A relation applies by default only when both names' owners have endorsed it.** Declaring counts as endorsing for an owner. Until both have endorsed, it is *offered*: printed, never applied. Interpretations for `via` come from Pike's closed list. The probe needs one addition: `present` (any value → yes).

**What the relations do:**

| Relation | table / find | Fence and merge | Similar-name nudge |
|---|---|---|---|
| `a same-as b` | a column for either name shows both, with the source marked (`drips…ᵇ`); `find prop:a` matches b | a write to either touches one aspect, so disagreement conflicts | silenced for the pair |
| `a narrower b [via]` | `find prop:b` also matches things with a (through via); b's column shows a's values marked, never the reverse | a write to a beside a differing b prints `related: …`. It warns, and never refuses | silenced |
| `a distinct b` | nothing | nothing | silenced. The desk stops suggesting the pair |

**Receipt:**

```
ok relate hazard same-as hazards  [e63] → r1  (offered: hazards is wren's; do endorse r1)
  would unite 2 things; they differ on 2: a24 "floods after heavy rain" (sable) / "floods near bottom" (wren);
  a28 "ice around base in freeze" (sable) / "drips, shut off in frost" (wren)
```

When the relation applies, the endorsement receipt says `applies now` and lists the same disagreements as conflicts to resolve.

**The six declarations the probe needs** [ran for the values]:
1. `hazard same-as hazards`
2. `steward same-as manager`
3. `water narrower water_access via=present`
4. `winter_status narrower hours`
5. `access distinct accessibility`
6. `size distinct capacity`

**Two corrections to my round-3 counts:**
- `size` against `capacity` is *distinct* (dimensions against people), not narrower.
- `water` against `water_access` is *narrower via present*, not same-as. The water text implies yes, but yes does not imply the text.

The six declarations are unchanged in number.

## What I would strike from the kernel after three rounds

- **The derived mode of aspects.** Under the rule Pike and I signed (a83), a derivation lives in a binding until something outside the view must name it. It then becomes an aspect like any other, whose owner happens to compute it. The kernel needs no mode for that.
- **The capture notation `(r, aspect)@op`.** Capture is Pike's binding word, not a kernel form.
- **The rule that an aspect's owner must be a *definition*.** The desk's names are owned by whoever minted them, and ownership is all that relations and fences need. A definition is one kind of owner.

What survives is referent, aspect, anchor and operation, plus an owner on each name. Definition remains the noun for versioned behaviour, not a precondition for owning a field. Operation survives as the *record* the gateway produces; it is not a demand on writers, which round 3 already removed. The noun that did the most work was the one I added last, the operation. Every spec in this note is the operation record plus a fence keyed by (referent, aspect).
