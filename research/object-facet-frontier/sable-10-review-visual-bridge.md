# Sable 10: review of the codex team's visual-bridge branch (26 Sep)

**Branch:** `research/visual-bridge-collaboration`, based on 008eeb8. I read it from git: README, BRIDGE-NOTES, `editing/README.md`, `ATTENTION-AS-STATE.md`, and the `-w` diffs of `desk.py`, `explore.py`, `deskd.py`, `scene.py`, `lens_ir.py` and `viewer.js`, plus `attention.py` and `test_session_lock.py`.

**How I ran things.** Every run below was on `git archive` copies of `main` and of the branch in my scratch directory. The branch checkout at `C:/Projects/Agora4-collaboration` and every live session were untouched. I merged nothing. The review goes to Alex through Jeff.

**Labels:** **[ran]** means the number is as printed. **[read]** means from the diff or notes. **[imagined]** means a design.

## Verdicts in one table

| Part | Verdict | Why, briefly |
|---|---|---|
| (a) OS-held lock lease (`explore.take_lock` / `release_lock`, deskd, export) | **Merge**, after a coordinated stop of every lock-taking process | Main's protocol fails under contention on Windows; the lease holds [ran] |
| (a') `desk.py` text-seen rule (`_text_seen_idx`) | **Refuse this copy**: main already has the idea, per aspect | Superseded by Jeff's 1758e14 |
| (b) `attention.py` row source and `inbox` | **Merge the row source and tests as an experiment**. The delta-header rewrite in `desk.py` goes to Jeff. Reframe the classifier over ops later | Derived, no new facts, no receipts; right shape. It reinterprets today's event records |
| (b') viewer-local selection (`focused_event`, `view open=`) | **Take as a design change**, and I change my mind in sable-8 | Navigation needs a declared viewer frame in evaluation |
| (c) `columns 1:3:1` | **Merge the idea; reconcile the word with Pike's `grid` tracks** | An emit fact (frame flow + tracks), not a kind |
| (c) `editor multiline` | **Merge with one revision:** admission static, not by value comparison at evaluation | Emit + act + scope. Its reads are right [ran] |
| (c) `button` | **Idea only; refuse the word** | Every leaf that carries `press` should get button semantics from the painter |
| (c) `meter` | **Take the let; refuse the paint kind** | The numeric three-state interpretation is a let. The drawing should be a library lens over `path`/frames |
| (c) compiler identity hashes `lens_ir.py`; `rows` vs `find` in cut text | **Merge** | Small true fixes |
| (d) `viewer.js`: a draft keeps its origin fence across refusal and reload; in-flight tokens | **Merge** (Pike's file, his review) | It repairs a real refuse-stale violation in the painter |

## (a) The session lock

**Their claim [read].** Concurrent scene polling plus commands on Windows raised `FileNotFoundError` in `take_lock` and a sharing violation on release. The branch replaces the sentinel file (create with O_EXCL, write a pid, unlink to release, reap by pid or by 60 s of age) with a persistent file whose first byte is locked through `msvcrt.locking` (`flock` on Unix). The OS releases it when the holder dies, and nothing ever unlinks it.

**My check [ran].** `scratchpad/lock/mutex.py`: 8 processes, each taking the lock 40 times. A critical section guarded by an O_EXCL marker catches a second holder, and a counter counts completed turns. In the crash runs, every 37th acquisition dies holding the lock.

| Protocol | Crashes | Counter (of 320) | Violations | Workers failed | Time |
|---|---|---|---|---|---|
| main | none | 4 | 0 | **8 of 8** (`PermissionError` WinError 5 and 32; one 100 s timeout) | 202 s |
| main | every 37th | 39 | 0 | **6 of 8** (WinError 32) | 180 s |
| branch | none | **320** | 0 | 0 | 1.0 s |
| branch | every 37th | 239 (crashed turns end early) | 0 | 0 | 0.7 s |

- Main's protocol does not break mutual exclusion in these runs. It breaks *availability*: on Windows, create, read and unlink race on a file that is pending deletion or open elsewhere.
- The branch's six tests pass on my copy [ran: `unittest test_session_lock`, 6 OK, 4.3 s], among them 240 mixed HTTP requests that kept all 90 writes.
- The Unix `flock` path was not exercised, by them or by me.

**The live-restart question [read, imagined].** Their warning is right. Old code sees the new persistent lock file as held and, after 60 s of mtime, reaps it by unlinking. On Windows that unlink fails while a new holder has it open; elsewhere it succeeds and two writers share a session. So the switch has to be a stop, not a rolling upgrade:
1. Stop deskd, every CLI run, `export_docs`, `golden_prints` and the continuity runs.
2. Deploy.
3. Start again.

A leftover sentinel file with a pid in it is harmless to the new code, which only locks byte 0.

**Correcting my own record [ran].**
- My baseline S2 says "the lock was left behind: the next CLI run waits up to 60 s". It tests whether the file *exists*. That was already wrong on main after Jeff's pid-aware reap, and it is meaningless under the lease, where the file always exists.
- S2 also says there is "no temp-file-and-rename" in `deskd.py`. That is false: deskd saves through `explore.save_desk`, which renames atomically. The check grepped the wrong file.

I am fixing both checks in `test_journal.py` to time the next acquisition and to call the real save path.

## (b) `attention.py`, against the journal and viewer-observation designs

**What is right [read, ran].**
- The rows are a pure function of the world's history and one host fact (`me`). There is no new fact, no delivery side effect and no read receipt.
- Addressing is authored data (`prop awaiting=`), so a claim is not a grant. Each row says why it concerns you.
- Rows carry no `item`, so they carry no gestures, and there is nothing to fence. Under sable-8 that is consistent: an act must bind a thing first (`the`).
- 10 of 10 tests pass on my copy [ran].

**Where it meets my designs [imagined].**
1. **It reads the event log's current shape.** It uses `edit` args keys, `undo` snapshots (to recover a removed appearance's subject) and the in-place `undone` flag that my baseline S7 flagged.
   - Under the journal, the same classifier is simpler and exact over ops: `prop:awaiting` rows, `comment:<cid>` inserts, `link:<lid>` answers. Global ids make the undo-snapshot scan unnecessary.
   - It should be kept as it is now and rewritten over ops when the journal exists. It is a good test of the journal's readability.
2. **Its read set is the whole history.** In accessor terms it is not `rows(src, r)` over one aspect. It needs its own call, `history(to=head)`, recorded as such, so a scene that reads attention refreshes on every event. That is honest and coarse.
3. **Event ids are its row keys.** Before 665fc35 a rolled-back batch reused an id. That is fixed; with the journal, `seq` serves.

**Where I change my mind.** sable-8 §6 said a lens that needs viewer state to be correct would change my mind. Their navigation case is exactly that: "Open discussion" must choose which subject the detail pane binds, per viewer, without writing a shared prop. Juniper-7's `$viewer.open` asks the same.

So I revise sable-8:
- `eval` takes a fourth input, a **declared viewer frame**: a small named set of choices (`open`, `focused`), read through an accessor call `viewer(k)` and recorded in `R`. A scene that reads it is per viewer, and its print says which choice shaped it.
- Drafts, scroll, folds and focus stay paint-only.
- The frame is written by viewer effects (`on click view open=$item`), never by world commands.

This keeps the property the old rule protected: world facts are shared and journaled, and a person's view is not history. It gives up only "one scene per read point", which navigation cannot have.

## (c) The four words, against sable-8

**No new IR kind.** All four lower to emit, act and let as they stand. The `deps` edges include the meter tokens [read].

- **`columns 1:3:1`: an emit fact.** A frame flow with proportional tracks and a fixed number of direct children, checked statically in `_check_visual_part`. This is the same idea as Pike's `grid 1 3 3 1` (pike-7 §3). One word should survive; I would keep Pike's `grid` with tracks and fold in their fixed-slot check. Merge the idea.
- **`editor multiline`: emit + act + scope.**
  - Its reads are right [ran]. The fence of an editor bound by `the title:Doc` is `[["s02", 2, ["text"]], ["select", "title:Doc", ["a03"]]]`: the whole text plus the membership read of the chain's bind.
  - Admission is decided *at evaluation* by comparing the displayed value with the target's native text. A violation refuses the whole lens, which then falls back to its last good version.
  - I tried to make a section row coincide with the whole text of an unheaded document, and it still refused [ran], so I found no false admit.
  - The rule is a type rule: "an editor's current thing is a subject bound by `the` or an `of <selection>`, not a row source." That belongs in check, statically. Revise the mechanism and keep the property.
  - With text hunks (sable-7), a section editor becomes admissible: it reads and writes the hunks it shows.
- **`button`: refuse the word, keep the fact it found.** Their finding stands [read, from their browser run]: the old `on click` leaf was a `DIV` with tabIndex -1, skipped by Tab. The fix is a painter rule, not a lens word: every leaf carrying a `press` act gets button semantics and a keyboard path (pike-7 §2, "each has a keyboard path and is written once"). A lens should not have to say `button` to be operable.
- **`meter`: take the let, refuse the kind.**
  - `meter_value` is a numeric interpretation with the states `missing`, `invalid` and `out-of-range`. That is ABSENT semantics done well: printed and never a silent zero. It is a let (sable-8 §2).
  - The drawing is a bar: a library lens emitting a frame or a `path` with the let's value, not a fourth paint kind. Pike's rule is that the painter grows by primitive, never by shape.
  - Its inputs are recorded as reads through `_fill`'s tracker [read].
- **Merge as is:**
  - the compiler identity hash that now covers `lens_ir.py` (a gesture painted under an old compiler is no longer mistaken for current);
  - `repeat_cut_text`, which points a row source's cut at `rows`, not `find`.

## (d) The overwrite, and why the repair is right

**Their finding [read, their browser receipts].** A held draft was refused after a peer changed the last paragraph. The refusal replaced the stored draft *object*, and with it the draft's `seen`. The next Enter was fenced on the newer paint, so it passed and overwrote the peer's paragraph. That is "refuse stale, never guess" broken in the painter: a stale draft was silently re-based on an observation the person never made.

**The repair [read]:**
- The draft keeps its origin across refusal and reload.
- An originless draft is blocked with a visible reason.
- Responses clear only the exact submitted generation, identified by token.
- Discard is blocked while a send is pending.

In my terms a draft is a proposal, and its reads are its origin. The journal's refusal line records those reads (sable-7 §5), and a resend must carry the same reads until the person reads again. Their rule is the painter half of that.

It is blunt only because text is one aspect. With hunks, a resend whose original hunk reads are still valid lands. That is precise reads, not rebasing. The viewer code would not change.

## For Jeff: are the `select` entries too coarse? [ran]

- **Ordering.** Selection answers come back in id order. A harmless `move a08 before=a04` in a column left both `kind:task` and `in:f02` answering `['a04', 'a06', 'a08']`. So a move does not reorder an answer. Order changes only if ids are reassigned: a merge rename, or a journal alias.
- **Truncation is a bug.** For a clamped repeat, the fence records the *shown* set `["select", "kind:task", ["a04", "a06"]]`, but `deskd.same_answer` re-asks the full selection and compares whole lists: `(False, ['a04', 'a06', 'a08'])` in an **unchanged** world. Every gesture under a clamped repeat would be refused.
  - **Fix.** The entry should say it is a prefix (`["select", q, S, {"shown": k}]`), and `same_answer` should compare `now[:k]`. A shown set is a set, and the order among the shown does not change a gesture's meaning. A `the` answer, which is live only when there is exactly one, should also compare as a set.
  - This explains why the instrument's over-read *fell*: `soundness.py` counts any different re-ask as touched, which is safe but hides the always-refuse.

## What would change my mind

- **On (a):** the Unix `flock` path failing in a real run, or a Windows service that cannot hold a handle across a request.
- **On (b'):** a navigation case that works as a world prop without leaking one person's view into another's scene. Then the viewer frame is unnecessary.
- **On `button`:** a leaf that must be pressable and must *not* be a button for accessibility (a list row that selects). Then the painter needs a second press style, and the lens must choose.
