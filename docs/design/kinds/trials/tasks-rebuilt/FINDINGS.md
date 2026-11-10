# Trial: the task board, redeveloped by someone else

> Run 28 Oct 2026 by a trial agent for Claude, on a copy of the live desktop log; written here by Claude from its report (the agent could not write files).
> - Scripts and raw output: `build.py`, `trial.py`, `extra.py`, `out-*.txt` in this folder.
> - The member in the tests is Sable (dk1148).
> - Labels: **ran**, **read**, **imagined**.

## Set-up (ran)
The 58 real cards, converted into two other vocabularies, plus generated volume:
- **a Tracker app:** `kind=issue`, with name, status, assignee, due, project, labels, estimate, parent;
- **a GitHub adapter:** `kind=gh-issue`, with number, title, state, body, user.

That gives 358 cards, 1,058 issues and 758 gh-issues: 2,174 task-like things among 3,302.

## Findings, most severe first

### 1. A member can take over `done` (high)
- **Ran:** Sable's `verb tidy.done acts_on=issue needs="project estimate" steps="forget $1"` wins `done <issue>`. Alex typing `done dk1186` printed "ok forget dk1186 … ~ tidy.done", run with his rights.
- **Ran:** before Alex's `task.*` words have shapes, Sable's `tidy.done needs="title lane"` wins for 358/358 of his own cards.
- **Read:**
  - shaped words are tried first and rank by `-len(needs)` (`kernel.py:593-611`, `kinds.py:312`);
  - `verb` is `may=members`;
  - only module families are protected (`words.py:898`).
- **Fix (source):** rank by who declared the word before counting needs, or let a kind own its word family.

### 2. The latest declaration of a kind replaces it (high)
- **Ran:** Sable's closed `make kind=kind name=issue` hid the steward's shaped one ("shape now: None").
- **Ran:** the steward also got round widen-only with a second `make` after `set` was refused.
- **Read:**
  - at one level the later declaration wins (`kinds.py:120`);
  - a closed declaration skips the leader check (`:333`);
  - `make` is never checked for narrowing (`:353`).
- **Fix (source):** one declaration per name per scope.

### 3. Widen-only guards the wrong direction for words (high)
- **Ran:** dropping `status` from `issue` let `issue.close` close Alex's Backlog lane (dk79) and `issue.assign` assign a window.
- **Ran:** opening Alex's own `taskboard-task` was refused as narrowing because three lenses use it, though for lenses opening only widens.
- **Read:** a closed kind counts as needing nothing (`kinds.py:370-378`).
- **Fix (design):** check a widening against the words that act on the kind; pin a word's shape when it is declared.

### 4. Reaching isn't working, in the House (high)
- **Ran:** after `word-set house.build needs="kind=…|issue|gh-issue"`, here is what `builders.py` would read:

  | | issues | gh-issues |
  |---|---|---|
  | no title | 1,058 | 0 |
  | no text | 1,058 | 758 |
  | closed but buildable (`HELD` lacks `closed`) | 260 | 247 |
  | owner check skipped (they say `assignee`) | 686 | 569 |

- **Ran:** an honest shape can't be written.
  - `title text acceptance` reaches only 20/58 real cards.
  - A `title|name` spelling passes the kernel, but the module still reads `title` raw.
- **Ran, `task_thing`:** it is reached only via `acts_on=task` (a shared kind) or by naming it in the list.
- **Ran:** when the House later offers a narrower shape, the steward's earlier widening is kept, with only an in-memory notice.

### 5. Spellings mix up names with vocabularies (medium-high)
- **Ran:** with a shared kind using `lane|status|state`, `set dk94 status=paused` (the House's hold) is refused with advice to "set dk94 lane=paused". That would make the card vanish. 49/58 real cards have no `status`.
- **Ran:** `task.done <issue>` is refused with advice to write `status=Done`, a value the Tracker doesn't use.
- **Fix:** keep same-value spellings apart from roles that need value maps.

### 6. Values don't translate (medium)
- **Ran:** the board pointed at `tag:task` drew 0 issues.
- **Ran:** a world-level mapping (lane things carrying `issue_status=`, `gh_state=`) reads correctly, at 528 ms.
- **Ran:** writes don't map: `move <issue> to=Done` writes `status=Done`.

### 7. Rules and grants widened to the shared kind silently match nothing (medium)
- **Ran:** `set dk168 of_kind=task` stops Alex's own Done announcements (0 posts), and `of_kind="taskboard-task,issue"` matches nothing.
- **Ran:** a grant with `only=kind:task` admits nothing. The board widget draws issues but can't move them until it gets a grant with `only=kind:issue`.
- **Read:** both compare a thing's own kind literally (`kernel.py:1473`, `897`).

### 8. Dispatch numbers (ran)
- **No shapes:** `move <gh-issue>` picks `issue.move` 758/758 (the wrong app), because `'issue' in 'gh-issue'.split('-')` (`kernel.py:625`).
- **By id, every app shaped:** right for every thing.
- **By name of a converted card:** 57/58 ask, and the ask doesn't list the ids.
- **Card silently skipped:** when only the new apps' `done` words have shapes, `done "Pay rent"` (a card and an issue share the name) acts on the issue.
- **Aliases:** aliasing `issue.close` as `issue.done` doesn't help plain `done`, and it blocks making a real `issue.done`.

### 9. The needs grammar takes mistakes silently (ran)
- `needs="status=In Progress"` is stored as `status=In` plus `progress`.
- An `acts_on=isue` typo is accepted, and the word then refuses everything.

**Smaller friction (ran):**
- `word-set` needs a `look` first.
- `actions` prints "as what it hasn:".
- Refusals say "a issue".

## What held up (ran)
- No non-task thing in the real world fitted any of the four task shapes tried.
- `rows task` lists all 2,174, each with an "as" reason.
- Members can't declare needs, edit or mark the steward's things, or widen grants.

## What would change my mind
- **On finding 1:** if the declarer's authority already shaped the ranking.
- **On findings 5–6:** if apps actually converge on shared names and values. The vocabularies were chosen to differ on purpose.
- **On finding 4:** if modules received rows already filled under the word's shape. Even then, `held` and the owner check would still be wrong.

**Not verified:** running modules, real painted presses through the door, group-scoped kinds, kits.

## Timings (ran; 3,302 things)

| Operation | Time |
|---|---|
| Open the log | 1.39 s |
| `make` (rises as the world grows) | 8.6 → 17 ms |
| `rows issue` | 27–30 ms |
| `rows task` (fitted, 2,174 rows) | 97.5 ms |
| `actions` | 14–17 ms |
| `kinds` | 2.5–3 ms |
| Dispatch by id / by name | 0.7–2.1 / 3.9–5.4 ms |
| Board lens: 358 cards / `tag:task` / 2,174 drawn | 121 / 186 / 528–610 ms |
| Work lens | 52 → 125 ms |
