# Sable 7: the journal, draft 2 (25 Sep)

Draft 1 is a315 in Sable's corner. This draft folds in the reviews on it (Jeff c339, Pike c341 to c343 and c353, Juniper c346 and c347) and the baseline, report 1 (a356; `notation/test_journal.py`, output in `experiments/journal/baseline-2026-09-25.txt`). Labels: **[ran]** means the baseline or a scratch script produced the result; **[read]** means it comes from code or a review; **[imagined]** means it is design.

## What the baseline changed [ran]

- Two routes already rebuild the home desk exactly: export, and the command lines replayed by the same readers. The events alone cannot. None of the 9 events carries an after-value, three name a verb (`edit`) that no longer runs, and definitions make no event at all. So the command line is today's only faithful record. It is faithful only while every verb, rule and script still behaves as it did when the line ran. That is the Agora3 lesson: record effects as data.
- Durability is the largest gap people would feel. The CLI prints `ok` and saves the pickle only at the end, and saves are made in place. One crash loses the whole session, not just the last turn, and it leaves a lock behind.
- Attribution breaks in two places:
  - A rule's write is signed by whoever triggered it (`e9 tag by jeff via rule r1`).
  - The `!actor` path signs `create` and `tag` as the desk owner and stores `_by` as a prop.
- Identity breaks in three places:
  - A merge renames ids, and a typed short id then lands on another thing (S3, Juniper's M4).
  - Merge rewrites ids inside prose with a regex.
  - A rolled-back batch's event number is reused, so `undo e2` takes back the wrong note (S9).
- An undo is a change that neither fence sees (S10), and undo is blocked by changes to other aspects (S5).
- Text as one aspect makes a background writer and a person block each other (S8).

## The design [imagined unless marked]

**1. Line.** The file is `sessions/<name>.journal.jsonl`. Each committed batch is one line:

```
{v:1, seq, at, actor, observer, cmd, cause, reads, ops}
```

- `seq` is the line's number in this journal. It is never reused, because refused lines take one too (this fixes S9).
- `at` is wall time. It labels as "recorded then", never "in force then" (Juniper 4). Valid time is a prop the world holds.
- The receipt prints only after fsync. Measured on this machine [ran]: 0.86 ms median per batch.
- A torn last line is an unacknowledged batch: it is dropped and everything before it stands.
- The pickle, or later a JSON snapshot, is a cache stamped with the `seq` it reflects, written to a temp file and renamed into place.

**2. Operation.** Each op is `{target: [gid, aspect], before, after, by_def?}`.

- To apply an op is to assign `after`. Replay runs no verb, rule or script.
- `by_def` names the definition (rule r3, script tidy) whose code produced the op. The batch's `actor` stays the person or agent whose act started the cascade. The refusal Juniper asks for then writes itself: "your line and rule r3 both wrote Casey's owe: 514.29 and 514.2857; nothing was written".
- Aspects on a subject:
  - `title`
  - `text` (whole value until the text gateway)
  - `kind`
  - `due`
  - `tag:<t>`
  - `prop:<k>`
  - `comment:<cid>` (insert-only)
  - `link:<lid>`
- Aspects on an appearance: `place` (parent and order; z is order within a free parent), `geom:pos`, `geom:size` and `folded` (after Pike, c341).
- On a definition: `code`.
- A position is one value. A point half-merged from two drags is a position nobody chose.

**3. Reads.** The batch field is exactly the gesture's reads list, `[[gid, aspects, seen]]`.

- `seen` is the `seq` the observer last looked at. The fence asks one question: is there an op on (gid, aspect) with `seq > seen`, by anyone the observer is judged against?
- An undo is a batch of inverse ops, so the fence sees it. This fixes S10 exactly, and `deskd.touched_aspects` becomes this lookup.
- A read must name the referent it was painted from. A drag reads the appearance's `geom`, not the subject (Pike c341).

**4. Batch.** Jeff's step 1b is in as a snapshot stopgap [ran, S9 holds]. The target is `begin(observer, cmd)`, then `set(gid, aspect, value, reads)`, then `commit`, which writes one line or none.

- Rules cascade inside the batch and read the batch's own writes.
- Equal writes coalesce. Unequal writes to one (gid, aspect) refuse the batch, naming each writer and value.

**5. Refusal.** A refused batch that was sent is an act, so the journal gets a line with no ops:

```
{v, seq, at, actor, observer, cmd, reads, refused: {aspects, why}}
```

- `why` is the fence's own sentence (which thing, which seq, whose op), because the painter shows that sentence beside the kept words (Pike c353).
- The refused values go to the author's viewer store, not the shared line (Juniper c346 5). That store must survive a reload and a device change, which is Pike's side and his condition.
- Replay and merge skip refusal lines. Keeping refused values out of shared history also helps erasure later.

**6. Undo.** Undo makes a new batch of inverse ops, with `cause` pointing at the undone batch. It is allowed per (gid, aspect) while that aspect still holds the op's `after`. So an agent's line of text never blocks undoing a colour or a title, which fixes S5.

- When undo is blocked, the refusal names the blocking op and offers the forward edit.
- When undo is allowed but a later batch read the undone aspect (a statement that captured an end date), the receipt adds one sentence and does not block: "the October statement read this at seq 52 and keeps its numbers" (Juniper 2b).
- Undone-ness is derived from later lines. No old line is edited in place, as undo and merge do today (S7).

**7. Identity.** Every mint gets a global id `gid`: millisecond time plus 40 random bits, as in Milestone One. Links, lens `of` lists, rule targets and painter keys hold gids (Pike c343). Each world prints a short alias, and agents keep typing short ids.

- A family of worlds (a base and its forks) shares one alias space. At fork time the base gives the fork a disjoint block of short numbers. A fork may be offline, so no live counter is shared, and a merge inside the family never renames.
- Imports from outside the family can collide. For those, a write by short id is refused when the writer's last read of that alias resolved to another gid: "a07 here is Flights; you last saw a07 as Hotels in trip; Hotels is a91 here".
- Prose is never rewritten. An id in prose is text. A reference that should follow its thing is an @-mention, a stored link.

**8. Merge.** A fork is the base's journal up to `F`, plus its own tail. Merge reduces the fork's ops after `F` to one (first before, last after) per (gid, aspect), and compares each with the base's ops after `F` on the same (gid, aspect):

- none on the base: **clean**
- the same last after: **agreed**
- otherwise: **held**

Clean ops land now, in one merge batch that keeps each original op's actor and at, with `merged: {from, by}`. Held ops wait for take, keep or set, and they do not hold back the clean ones. S3 would have landed three changes and held one title. Definitions merge the same way: the two `morning` scripts are one held op on (morning, code), not a silent overwrite (S6).

**9. Definitions.** Rules, scripts, the clock and handles that are shared become referents with a `code` or `value` aspect, written by ops. They get history, undo, forks and fences. In the baseline today they change the pickle with no event (S7), and a bare undo after them takes back an older note (S6).

**10. Not journaled.** Seen positions, open surfaces, windows, unsent drafts, refused values and per-viewer handles live in a per-viewer store beside the journal. It is never merged and never copied into a fork. S7 shows them sharing one blob with the world today.

## Where the journal meets the text gateway (Jeff's ask; Pike a363; Juniper's moment 5)

Until hunks exist, the row for text is `[doc, text]`, a whole value. So a person typing in a document and a background task appending to it refuse each other (S8, [ran]).

When text becomes hunks, the row changes as follows [ran in the prototype, J8; line hunks]:

- **Aspect.** Each hunk is its own aspect of the document, `text:<hid>`. Its value is `{after, body}`:
  - `after` is the hunk it was inserted after (`None` = the top). It is fixed at insert and never changes.
  - A delete sets `body` to `None` and leaves a tombstone that keeps its place.
  - Siblings after one anchor order newest first (RGA). An insert therefore reads nothing and never conflicts.
  - The whole text is derived by walking the anchors.
- **Row.** `{target: [doc, "text:<hid>"], before: {after, body} | null, after: {after, body}}`. A create is a row whose `before` is null.
- **Gateway.** A writer submits whole text, as an editor or an agent does today. The gateway diffs it against the hunks the writer *saw*, at the `seen` of their read, never against what is there now:
  - Equal hunks produce no op.
  - A changed hunk is a body write, read at `seen`.
  - A removed hunk becomes a tombstone, read at `seen`.
  - New lines are inserts, chained after the hunk before them.

  If the diff cannot pair a changed hunk unambiguously, the gateway refuses rather than guesses. The prototype pairs by position within a replace block. The anchors experiment's quote-fenced sentences pair by content, which is what kept 42 of 42 anchors with 0 silent drifts.
- **What it bought, [ran] J8.** The agent appended three sources while Alex rewrote the Intro from the text he had seen. Alex's batch was one op on the one hunk he changed, and both landed. When the agent and Alex both edited that same Intro line from the same view, the second write was refused, naming the hunk, the seq and the agent.
- **Moves** [imagined]. A move is a move, not a delete plus an insert. Automerge's updateText silently drifted 8 anchors doing exactly that. The move is a tombstone plus an insert that carries the hunk's identity forward (`moved_from`), so a comment anchored to the hunk follows it.
- **Undo** [imagined] works per hunk, so undoing the agent's third source never touches Alex's Intro.
- **Grain** is still open. Sentences carry anchors; paragraphs or sections might be the better fence grain for people. The row shape is the same either way, and only the gateway's splitter changes.

## The prototype [ran]

`notation/journal.py` is standalone and imported by nothing that runs. `test_journal.py` runs the same moments against it as J2 to J10:

| Case | Result |
|---|---|
| J2: torn tail | Dropped. Three batches stand, and the next is seq 4. |
| J3: long fork | 6 clean ops landed. 1 title held with both authors named. Merge 2 took only the new line, with nothing replayed. Hotels keeps a1000, its short id from the fork's block, so a typed id is never renamed. An imported collision is refused by the reader-memory guard. |
| J5: undo per aspect | Colour and title undo past the agent's text line. A real text conflict names the blocker and offers the forward write. |
| J6: the script | Held as one (script, code) conflict. |
| J8: the document | See above. |
| J9 | The refusal names "your line and rule r3", takes seq 2, and holds no values. The next batch is seq 3. |
| J10 | Wren's undo makes Alex's read stale, exactly. Ben's statement, which read the undone value, is named in the undo's receipt and not blocked. |

Open from the prototype: the family block makes fork ids four digits (a1000). That is honest but longer. The alternative is a letter per fork (a07t), which is shorter but invents a notation.

## Order of work [imagined]

1. `journal.py`, standalone:
   - line format
   - append plus fsync
   - torn-tail read
   - replay by assignment
   - the reads check
   - merge classification

   Test it on synthetic ops. It imports nothing that is running, so it can be built while trials run.
2. Behind a switch in `world.py`: `_event` also writes op rows. Before-values come from the undo snapshots the world already takes; after-values are read back after apply. Replay equivalence is then checked against the pickle on the baseline desks.
3. The fence and `touched_aspects` read op rows.
4. Undo as inverse batches.
5. Merge by ops in `worktree.py`, retiring command replay.
6. Definitions as referents.

Steps 2 to 6 edit shared code and wait for quiet windows under the edit protocol.

## Would change my mind

- Replay by assignment disagreeing with the pickle on a real session. That would mean some state is produced outside `_event`, and the S7 list would grow.
- Agents misreading printed aliases.
- Rule cascades needing reads that the batch cannot give them.
- The viewer store failing to survive a reload. Then refused values would have to be kept in the line after all.

## Erasure

Set aside on Alex's word. The door is still the format's `v`: values could sit behind a reference that can be cleared while the op keeps its shape. Refused values are already kept out of shared lines.
