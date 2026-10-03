# What a person has seen: a census (a2847)

*Worker a2847 for Sable, 2 Oct 2026. Report only: no code was changed. Paths are under
`research/text-desk-lab/notation/`. Each item is marked by how it is known:*

- **[read]**: I read the lines myself.
- **[read, search]**: a read-only search agent I sent read them and quoted them. I checked the ones marked so only
  where I say.
- **[imagined]**: reasoned from read code, not run.

Nothing here was **ran**.

## In one paragraph

Seen state is not one thing. It is **eight stores in three places**:

- **Six on the pickled `Desk`**, saved in the world's file in the same atomic write as the world.
- **One in the house's folder**, per resident.
- **Small pieces in the browser.**

Two of the stores already disagree about one line (a1958). The commission's premise needs two corrections:

1. **"Awaiting a reply" and "For you" read no seen state today.** They are judged by who wrote last. a1140's "waiting
   for you" is not built yet.
2. **The stale fence's real reader is not `seen` (a revision per id).** It is `_seen_idx`, keyed by **event index**.
   An index is a position, not a name, and positions can be re-issued.

That second fact makes the strongest case against moving the state out. It is also a fail-open bug that exists
**today**, without any move (section 3).

---

## 1. Where seen state is written

### A. On the `Desk` object, pickled whole into `sessions/<world>.pickle`

Every store in this group is written by `explore.save_desk` (temp file + `os.replace`, explore.py:95-110) under the
world's lock (`take_lock`, explore.py:46). That is the same write as the world. deskd's `Session` does the same and
saves only if the bytes changed (deskd.py:178-205). **[read]**

**A1. `desk.seen`: `{id: rev}`** (desk.py:192). **[read]**

- `_mark_seen`, from every printed line: `look` and the outline `line()` (desk.py:618-626, 665, 694), `read`, `where`,
  `verbs`.
- `_mark_rev`, after your own act (desk.py:607-616).
- `cmd_do` (desk.py:1593-1598).
- `cmd_undo`: everything the undo touched (desk.py:1542-1544).
- The painter's gestures: `desk.seen[item] = rev` from what the gesture carried (deskd.py:411, 466).
- Not written when a chat line is added while behind (`behind`, desk.py:1578).

**A2. `desk.last_event_seen`: one int, an event index** (desk.py:193). **[read]**

- Written by `delta_header` (desk.py:801-803), which `_one` calls before **every command** (desk.py:250).
- So a `do`, a `read`, even a refused line moves it, not only `look`.

**A3. `desk.open`: the surfaces you have expanded.** **[read]**

- View state, not reading, but it travels in the same tuple as A1 and A2.

**A4. `desk._per`: `{slot: (seen, open, last_event_seen)}`.** **[read]**

- explore.py swaps A1-A3 in and out of it by slot `me` or `me/window` (explore.py:193-201, 289).
- deskd does the same by actor only, ignoring windows (deskd.py:183-200).
- A new non-jeff slot starts at `({}, {root}, len(events))`: new people arrive having "seen" all history for the
  header, and nothing for the fence.

**A5. `desk._seen_idx`: `{(observer, id): {aspect: event index}}`.** **[read]**

- `observer` is `me` or `me/window` (`_observer`, desk.py:518-522). `"*"` means everything.
- Written by `_note_seen` (desk.py:540-551), which every `_mark_seen` / `_mark_rev` calls.
- Also written by the painter's gestures with `obs=actor` (deskd.py:412, 468, 473, 494; the last one at the paint's
  `at`, an index the browser sent).
- Also written by `worktree merge`, which seeds `idx[(author, nid)] = base_events` for every node (worktree.py:169-174)
  and does not remove it afterwards.
- Room narration writes it (rooms.py:662), and so does promise handling (promises.py:445, 485, 544).
- Lens prints write it through `shown`/`fshown` (lens_ir.py:367; desk_knife.py:1484-1496) **[read, search]**.

**A6. `desk._chat_reads`: `{(observer, chat_sid): (lo, hi, sha1(lines[:hi]), holes, unseen)}`.** **[read, search]**

- A plain `read` of a chat writes a clean run (desk.py:1103).
- `read :3` / `tail=` and a room's narrated `look` / `go` write `_chat_shown` (desk.py:1174; rooms.py:652).
- `create` of a chat writes `_chat_made` (desk.py:1136).
- `examine`, `reply` and `append` do not write it.

**A7. `desk._views`: `{actor: {lens, at, time, viewport, facts, boxes, painted}}`.** **[read]**

- `at` is the event index the painter painted at.
- Written by `POST /api/observe` (deskd.py:343-357), posted by viewer.js:153 **[read, search]**.
- It is a viewer's observation, not reading, but it is per person and it holds a log position.

**A8. Per-reader leftovers that are not seen state but would face the same question.** **[read]**

- `_made`: `{slot: (reply, made)}`, what `$new` means (desk_knife.py:1298-1299).

### B. In the house's folder, outside the world

**B1. A resident's news cursor:** `house-state/<world>/<corner>/state.json`. **[read]**

- Keys:
  - `cursor`: an event index.
  - `inbox`: lines gathered for the resident.
  - `for_you`: `{by, id, text}`, kept while it rests.
  - `calls`: wake calls.
- `House.news` is the only thing that moves the cursor: it reads `w.events[cursor:]` and sets `cursor = len(events)`
  (house.py:593, 673-674).
- `news` runs:
  - on each house step (`resting=True`);
  - on each wake;
  - after each turn's receipt (house.py:751, 798, 811, 860, 873 **[read, search]**).
- `take()` and `first()` empty `inbox`, `calls` and `for_you` as they are said (house.py:677-696). **[read]**
- Saved with a plain `write_text`, not atomically (house.py:322-323). **[read]**

**B2. A worker's cursor:** `house-state/<world>/worker-<cid>/state.json`, key `cursor` (workshop.py:225, 238, 285).
**[read, search]**

### C. In the browser, Alex's Desktop

See section 4.

---

## 2. Who reads it, and what would happen if it moved out

| Reader | Reads | If the state moved to a per-person file |
|---|---|---|
| **The text fence, simple path**: `Desk.cmd_do` (desk.py:1574-1585): never looked / stale / blind | A1 `seen` (rev compare), A5 via `_blind` | Unchanged if the act loads the person's file before it is judged. **[imagined]** |
| **The text fence, registry path**: `DeskMoo.cmd_do` (desk_moo.py:207-226) | A1 only for "never looked" (`seen is None`). Staleness comes from A5 via `_touched_by_others`, which scans `w.events[since:]` from an index (desk.py:464-516) | **The hard case (section 3).** **[read]** for the mechanism |
| **Painter gesture fence**: `/api/do` (deskd.py:379-494) | Mostly what the request **carries**: `observed.rev`, `reads`, `at`. Then it writes A1 and A5 so the text fence agrees | Already almost independent of stored seen state: the observation travels with the act. **[read]** |
| **The `!!` line / "since your last look"**: `delta_header` (desk.py:796-862) | A2 | Moves cleanly. It is a cursor over an append-only log, like the house's. **[imagined]** |
| **Chat receipt** "N lines from others you haven't seen": `_chat_behind` (desk.py:1178-1210) | A6 | Moves cleanly. The digest makes a stale run fail safe ("this chat was rewritten"). **[read, search]** for the digest |
| **Room narration** "N earlier lines you haven't read" (rooms.py:650-654) | A6 | Same as the chat receipt. **[read, search]** |
| **`actors` scene source** (scene.py:562-570): each slot's `read` / `behind` | A4's third element | Must be able to list **other** people's cursors. This is "a reading position is a fact others may see" (Lark, deskd.py:264). A per-person file must stay readable by others, or the source goes blind. **[read]** |
| **`/api/snapshot` `readers`** (deskd.py:267) → apps/third.js "N behind" | A4 | Same as `actors`. **[read]** / **[read, search]** for third.js |
| **`judge_views`** (scene.py:1642-1670), from lens_ir.py:597, 651 | A7 (`at`, `painted`) | Moves cleanly. It tells *others* whether a viewer's sizes are current. **[read]** |
| **`House.news` → wakes, inbox, `for_you`** (house.py:580-700) | B1 only. **It never reads A1-A7** | Already outside. **[read]** |
| **"Awaiting a reply"**: `moo.unanswered` (moo.py:348-357), examine (desk_moo.py:159) | **No seen state.** Trailing lines not signed by me | Unaffected. **[read]** |
| **"For you"** (`inbox:<name>`): `scene.inbox_rows` (scene.py:417-456) | **No seen state.** `open` = no line of mine after it | Unaffected. **[read]** |
| **a1140 "waiting for you"** (the pulse) | Not built. The card says "the 'waiting for you' facts are world work" | If it is built on seen state it needs the reader's store as a lens source. **[read]** for the card, **[imagined]** for the rest |
| **Selections, lens terms, rules** | **None** reads seen state: no `unread`, `seen`, `new` or `since` term exists | Unaffected today. **[read, search]**, confirmed by my own grep of scene/lens_ir/rooms/promises for `seen`/`_per`/`_chat_reads` |
| **`worktree merge`** (worktree.py:165-200) | Overrides A1 (`-1` for all) and seeds A5 at the fork point, then replays | This is a **precedent**: the fence judged against a seen state set from outside the reader's history ("since the fork saw it"). **[read]** |

### Two stores already disagree (a1958)

**[read]** The card, and B1 vs A6 in the code:

1. The house showed Sable chat lines as notices in her inbox (`~ in chat … (to you)`, B1).
2. Her later append's receipt still counted them as "4 lines from others you haven't seen", from A6.
3. A notice writes B1 only. Nothing in a notice writes A6.

If seen state moves to one per-person store, a notice and a read can write the same record. Today they cannot.

---

## 3. The hard case, as the strongest case against moving it out

### What holds today **[read]**

The fence and the record it consults are in one process, under one lock, in one atomic `os.replace` of one file:

- A command loads the Desk.
- It judges the fence against A1 and A5 in memory.
- It applies the change and marks A1 and A5.
- The whole object is written at once.

A crash before the replace loses the act and the seen marks together. A crash after it keeps both. There is no state
in which the world and the reader's record disagree.

### The argument against **[imagined]**

Split them into two files and there are two writes per act. The two crash orders are not symmetric:

**World written, seen record lost.** The reader's record lags behind the world. This fails **closed**:

- The text path refuses a rev that moved (`seen != cur`), even your own.
- `_blind` refuses to replace an aspect your record says you never saw, though you wrote it.
- The `!!` line repeats news.
- The chat count overstates.

Annoying, never wrong.

**Seen record written, world lost** (or written in the other order, or the world restored from an older copy). This
fails **open**, and silently, because neither key is a name:

- `seen` stores a **revision number**. After the lost write, the next real change re-issues that same number, and
  the fence compares equal on a value never seen.
- `_seen_idx` stores **`len(events)` positions**. After the lost write, other people's next events land at indices
  the record already claims, and `_touched_by_others` starts its scan past them (`for k, e in enumerate(w.events[since:], since)`).

Event *ids* are never re-issued (`next_event_number`, world.py:578-589). Event *indices* and revs are.

So "write the world first, then the seen record" is necessary, and it is not obviously sufficient. With two
desks answering one person (deskd for the Desktop, explore.py for a terminal, the MCP tool), two processes may
read-modify-write the person's file, and today's world lock does not cover it.

### It already happens, inside one file **[imagined, from read code; not run]**

`verbs.rollback` (verbs.py:330-336) takes back a refused knife act. It undoes its events and **deletes them**
(`del w.events[n0:]`), but leaves A1 and A5 as the act marked them:

- `_note_seen(…, len(events))` after the act (desk.py:1594; desk_moo.py:279 through `_mark_rev`).
- After the deletion, the reader's A5 entry points one or more indices past the end of the log.
- The next event by **someone else** on that thing lands at index `n0`, which is below the recorded index, so the
  registry fence treats it as seen.

The rev path fails closed instead, because `World.undo` bumps revs forward (world.py:1174).

`cmd_apply`'s abort (desk.py:1716-1724) restores nodes, subjects and events, not A1, A5 or A6. That is the same shape.

A test that would show it:

1. Make a refused verb-act (a verb note titled with a built-in word).
2. Have another actor change the target.
3. Act again as the first: the expectation is no stale refusal.

Not run, because the commission is report-only.

### Undo **[read]**

`World.undo` never restores an old rev. It writes a new one (`rev + 1`), and `cmd_undo` marks what it touched as
seen by the undoer (desk.py:1542-1544). An undo is a new change on the record, so **seen state never needs to be
rolled back with an undo**, and moving it out loses nothing there. Only *deleting* events (rollback, apply's abort)
breaks the record, because only those re-issue indices.

### What this case says about a design **[imagined]**

The danger is the **keys**, not the location:

- A record keyed by **event id** (and rev paired with the id that produced it) cannot be fooled by a lost write or a
  rollback. A missing id is "unseen", and that fails closed.
- With such keys, the order of the two writes stops mattering for safety. A lag only costs extra refusals.

The painter's gesture path points to a second way out. The act **carries** what was observed (`observed.rev`,
`reads`, `at`, deskd.py:379-494), and the fence judges what the request says, as an HTTP conditional request
(If-Match) does; that comparison is from memory, not read for this. Then the stored record is a convenience for the
typed path, not the fence's source of truth.

**What would change my mind:** the fence also needs a per-reader history that the world must hold atomically. Today
the only such need I found is rollback and apply re-issuing indices, and that is a bug either way.

---

## 4. Alex's own seen state on the Desktop

### Identity **[read, search]**

The Desktop asks deskd as session `desktop`, `as=alex` (core.js:31-32). lens.js and term.js default to session
`lens`, `as=alex`.

### In the world pickle, keyed `alex`

**`_per["alex"]`: A1 + A2 + A3.** deskd keys it by actor, so all of Alex's windows and tabs share one slot. **[read]**

- **Written by:**
  - gestures (deskd.py:411, 466);
  - typed lines in the Desktop's terminal;
  - not by `/api/events` polling (`door.py:388` polls without `as`, deskd defaults to `alex`), which runs no command.
    Polling can still *create* the slot.
- **Read by:**
  - his own fence;
  - the `!!` header in his terminal;
  - the `actors` source;
  - `snap["readers"]` → third.js "N behind".

**`_seen_idx[("alex", id)]`: A5.** **[read]**

- **Written by:**
  - gestures, at the painter's `at`;
  - **`/api/snapshot`** (deskd.py:268-270). It saves and restores `seen` and `last_event_seen` so that "reading for the
    renderer must not count as the actor looking". But `outline()` → `line()` → `_mark_seen` also writes `_seen_idx`,
    and that is not restored. So each snapshot records Alex as having seen the title, place, due and props of
    everything in the outline. That fails **open** on the registry path for his next typed act. **[read]** for the
    code. **[imagined]** for the consequence.
  - core.js asks for it as `alex` at start, after each of his own commands, and whenever the event stream's total
    changes (core.js:38, 70, 78, 120) **[read]**. So it runs at every change anyone makes, whether or not anything
    was painted for him.

**`_chat_reads[("alex", chat)]`: A6.** Written only if he reads or narrates a chat through the terminal. **[read]**

**`_views["alex"]`: A7.** Written by every observe post. Read by `judge_views`, for anyone. **[read]**

### In the browser **[read, search]**

| Store | Key | What it holds |
|---|---|---|
| localStorage | `lens-drafts:<s>:<who>:<lens>` | each draft keeps the `seen` / `shown` it was typed against (viewer.js:12-34) |
| localStorage | `lens-folds:…` | folds |
| localStorage | `desk-term*` | terminal history and the held gesture id |
| sessionStorage | `lens-carry:…` | the scene, its scroll, and `places().seen` (scroll frames met) |

None of these is a read position on the world. The painter keeps `events_total` in memory only.

### He has no house cursor **[read]**

B1 is per resident corner. A person is not woken, so nothing in `house-state` is Alex's.

---

## Defects found along the way

These are outside the commission's scope, listed so someone can take them.

1. **`verbs.rollback` and `cmd_apply`'s abort leave `_seen_idx` pointing past re-issued indices: fails open.**
   **[imagined, from read code]**
2. **`/api/snapshot` writes `_seen_idx` for the asker while saying it doesn't count as a look.** **[read]** for the
   code.
3. **deskd never sets `desk._window`, so it inherits the last explore.py run's `--window`.** Then `_observer()`
   answers `actor/w` for deskd callers. The gesture path avoids this by passing `obs=` explicitly.
   **[read, search]**; explore.py:202 resetting it on each run is **[read]**.
4. **A slotless `jeff` reuses the top-level `seen` / `open`, which unpickle as the same objects as the last saved
   slot's tuple.** So it can alias another reader's record. deskd.py:186 and explore.py:198 are **[read]**; the
   aliasing is **[imagined]**.
5. **a1958:** a notice (B1) does not count as seen in A6. **[read]**

## What I did not check

- The live pickles: which slots and keys exist (sessions are off limits).
- Any behaviour at all: nothing was run.
- desk-shell JS beyond what the search agent quoted.
- trial_resident.py's copy of the house state.
- Which Desktop apps paint from the snapshot's outline rather than from `/api/scene`. Either way the snapshot request
  is made and writes `_seen_idx`.
