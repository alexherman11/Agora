# Missing kernel words: review handoff

Builder, 24 October 2026. Scope: `src/agora/` only. No git state changes, live installation or desktop restart. Claude owns review, the Board update and commit.

**Read:** repository AGENTS.md and the live charter; SHAPE including section 17; Communities and the Dictionary; taskboard NEEDS, installer, proof and painter; the old desk's carried/receiver fences; `kd_media.py` offers (read only).

**Built:** steward `word-set`/`word-rename`, single-entry translations and reader `language`; stable stored verb/rule bindings and kit transport; `history` and a painter row source; carried identity and both participants' fences; composed-word happenings and rule kind filters; actual made/changed record timestamps and `$today`. Every new word has a dictionary entry and help. Taskboard uses these shared words, with no app module or host logic.

**Ran, final source:** `C:/Projects/Agora4/.venv/Scripts/python.exe -m pytest -q src/agora/tests` printed **`79 passed, 30 subtests passed in 109.95s (0:01:49)`**, exit 0. This includes twelve new general regression tests. Proofs: Council night **`21 of 21 checks passed`**, Hidden hunt **`17 of 17 checks passed`**, Kits **`23 of 23 checks passed`** (including its screenshot checks and an unchanged 21-check Council night), BYO agent **`25 of 25 checks passed`**, Web host **`20 checks passed`**, Task board **`21 of 21 checks passed`**; all exit 0. Existing assertions were retained; the board's unsupported-drag checks were replaced by successful movement and stale competing-drop checks. The current board screenshot was inspected: the dates themselves contain actual timestamps, rather than the compiler's empty event frame. Module aliases retain the caller's group, module authorship, their own entry's metadata and exactly one own-word happening.

## Rough spots repaired: missing world words and source edits

- `kernel/dictionary.py`, `kernel/words.py`, `kernel/kernel.py`, `kernel/kits.py`: missing **word-set**, **word-rename**, **language**, same-entry translated labels, and durable stored heads. Metadata stays world data; implementation remains code. Old saved lines bind before name edits. Kits transport one executable representation with remapped entry ids and preserve translations. The old `rename` can no longer publish a world verb into a module namespace.
- `kernel/history.py`, `kernel/kernel.py`, `kernel/words.py`, `kernel/painter.py`: missing **history** and record dates. Readings filter the current thing and historical/current fact visibility, never raw testimony or another thing's facts. Sealed rows have neither authors nor facts. The facade registers a row source in its imported compiler instance without editing the desk's source.
- `kernel/painter.py`, `kernel/kernel.py`: missing **carried/drop admission**. Observed identities translate at the facade, both participants' reads join the fence, and admission/commit recheck them without waiting on a module under the lock. Prefix fences include removed fields. The unchanged lens.js really drags the scratch cards.
- `kernel/kernel.py`, `kernel/words.py`: missing **a composed word's own happening** and **rule kind filtering**. A committed verb announces once in addition to its parts; entry-bound hearing survives renames. `rule on=… kind=… do=…` or `make kind=rule on=… of_kind=… do=…` filters the target kind, still running as the author. No-record no-ops and see words do not announce acts.
- `kernel/kinds.py` (rewritten), `kernel/kernel.py`, `kernel/words.py`, `kernel/dictionary.py`, `kernel/kits.py`, `painter/arrangement.py` (28 Oct, Claude, on Alex's "looks good to build"; [[fresh-words-reach-kinds]]): missing **a word's shape** (`acts_on=`, `needs=`) and **a kind's shape** (`needs=`, `extends=`). Which things a word reached lived in module code (`board.py` "post_kind is event or kind is event"; `builders.py` "taskboard-task or task") or in a guess from help text, invisible to every other word. Now it is world data, checked once in `guard`, and widened by a steward in one line. Also missing: **`mark`** (set a kind's markers on purpose), **`actions <thing>`** (what reaches it), and a way for the kernel to **retire its own words** it no longer runs.
- `modules/house/house.py`, `modules/house/builders.py`, `community/board/board.py` (28 Oct): the hand-written kind checks became the words' `needs`; nothing else changed.
- `kernel/chat.py`, `kernel/kernel.py` (`happening_for`) and `modules/house/house.py` (`catch_up`), 28 Oct, card dk1245. The missing world word is **who a line may call**: today it's whoever can see the chat, but nothing in the world can say it.
  - **Before:** `say` stored every @name in `to`, even people outside a closed chat, while its receipt said the line didn't reach them. The House wakes everyone in `to`, reading with its own sight.
  - **Now:** `to` stays inside the chat, delivery filters by who may see the line now, and catch-up checks the chat's people.
  - **Live check (read):** 0 of 171 said lines had leaked.
  - **Tests:** 3 new in `tests/test_chat.py`.
- `kernel/kinds.py`, `kernel/kits.py`, `kernel/kernel.py`, 28 Oct, from the shape-reads reviews (`docs/design/kinds/review/`). Each is a fix to the shapes built that day.
  - **An unreadable stored shape now fails closed** (`Unreadable`), and `take` validates shapes. Missing word: **a version on the shape grammar.**
  - **`Refused(kept=)`:** the refusals log keeps word, need and id, never a private title. Missing word: **what a refusal may say to whom.**
  - **The fence counts every declared spelling of an aspect** (`kinds.spellings_of`). Missing word: **the reading's real aspects travelling with a painted row.**
  - **`_module_saw`** accepts the per-aspect `saw` and refuses a malformed one instead of crashing.
  - **`choices()`:** a name many things share lists them with the fact that tells them apart.
  - Tests: `test_shapes.py` 5 new, `test_skeleton.py` 1 new.
- **Security review, 28 Oct** (`docs/design/kinds/review/privacy-authority-review.md`; all ran on scratch worlds). Each fix has a test in `tests/test_chat.py` or `tests/test_house_turns.py`.
  - **`words.py` set_:** only a rule's maker changes `on`/`do`/`of_kind`; a leader may switch it off or forget it. Missing word: **whose act a rule hears** (`by=`, a design point in authority-and-shared-kinds.md).
  - **`modules/house/house.py`:** one turn answers one chat (`_begin`), catch-up wakes once per chat and asks through the agent's own door (`sees_line`). Missing word: **a reading as another person** for modules.
  - **`kernel/refusals.py`:** someone else's row shows the word, and its thing only if visible.
  - **`kernel/chat.py`:** an ambiguous `with=` name is refused, and `reply_to` must be in the same chat.
  - **`kernel/words.py` rows:** `rows <kind>` of a kind nothing is says so and points at a word of that name (JEFF's "0 refusalses").
  - **`modules/map/map.py`:** the geocode viewbox is rounded to 0.1°, and `map.find` geocodes nothing on the side. Missing word: **what may go to an outside service** (outside-and-privacy.md).
- **Security review round 2 and the values review, 28 Oct, late** (`docs/design/kinds/review/privacy-authority-review.md` "Round 2", `review/values-kernel-review.md`; each ran on scratch worlds). Tests: `tests/test_chat.py` (rules, `RefusalRows`), `test_house_turns.py`, `test_shapes.py`, `test_next_steps.py`, `test_module_reader.py`.
  - **`kernel/refusals.py`, `kernel.py` run:** a member's row, read by a steward, loses its `line` and reason. Stewards' own rows stay whole among stewards, as dk939 asked; the desktop's `test_refusals` holds that. A press's vouched text names the button by id, never its label or `does=` line (found by the refusals session). It shows the word, its thing if visible, and only a reason its author vouched for (`Refused(kept=)`, now flagged `vouched`), or an error's class and code place (`code`). A module acting for a member is redacted the same way; its faults stay readable. The "which one?" vouched text no longer repeats the typed name. Missing word, as before: **what a refusal may say to whom.**
  - **`kernel/words.py`:** a leader may switch a member's rule off, never back on. Someone else's `undo` that would re-point a rule or switch it back on leaves it off. `rule_maker` lets a person steer a rule their own agent made. Missing word: **whose act a rule hears** (`by=`).
  - **`kernel/kinds.py` `validate_decl`:** one declaration per name per scope, closed ones too. A nearer declaration that hides an outer one needs a leader. Missing word: **who owns a vocabulary.**
  - **`kernel/next_steps.py`:** `task.review` and `task.verify` are the reviewer's own act, never an agent's or module's for them, and `attested()` ignores records made through one. Missing word: **an attestation**, as distinct from a fact.
  - **`modules/house/house.py`:** `sees_line` hands nothing on without a door. The cursor moves when a line is said to the model, not when it's queued, and never past a line still waiting in another chat.
  - **`kernel/modules.py`:** the reader threads end cleanly when `stop` closes the pipe, and still wake every waiting call. Found in the desktop log, not by a review. No missing word: a bug.
- **Later, 28 Oct (live since the 22:57Z restart):**
  - **`modules/map/map.py` `point_of`:** a thing the map finds is never a search. Its title doesn't go to Nominatim; the reply says it has no readable place. An ambiguous name asks which, and an id is never sent. Only typed text that names nothing may go out. Test: `tests/test_map_outside.py`.
    - **Still open:** drawing geocodes a row's `location` text, private or not. Rows don't say who a thing is for, so the map can't tell. That waits on Alex's outside-services call.
    - **Missing word:** **a thing's audience, readable by a module** (`private_aspects`).
  - **`kernel/words.py` `_module_of`:** `status` alone said "no module called (nothing) here"; it now says to name a module. No missing word: wording.
  - **`desktop/kernel-desktop/kdesk.py`:** each start writes its UTC time to kdesk.log, so a traceback can be placed. No missing word.
- **Three designs Alex approved, 28 Oct, late** (asked in the session; his answers are in `docs/design/kinds/kinds-decisions-for-alex.md`):
  - **Rules hear `by=`** (`kernel.py` `_rule_hears`; `words.py` `_rule_by`, `STEERING`, `make`). Alex: "You, your agents, leaders".
    - A new rule is `by=maker`: it hears its maker, their agents, and the leaders of its group.
    - `by=anyone` hears everyone. Rules made before this have no `by`, and keep hearing everyone.
    - A sealed act fires only `by=anyone` rules. Only the maker changes `by`.
    - Tests: `tests/test_rule_by.py`. The desktop-words rule test now says `by=anyone` where it means everyone.
    - A module acting on its own counts as the person it's installed for; one installed for no one is no one's act. The desktop's `window.opened` and guy rules failed until this; `test_kdesk` and `test_desk_follows_source` cover it.
    - The missing word was **`by`** itself.
  - **Child kinds by declaration** (`kinds.py` `fits`, `mark`). Alex: "Children by declaration".
    - A kind that `extends=` another holds its own kind, kinds extending it, and things marked `is.<kind>=yes` (by `mark`). Never what merely has its shape. Parents stay structural.
    - Tests: `test_shapes.py`. The extends test now marks its note.
    - A word acting on a child kind refuses an unmarked thing too (`kinds._lacks`; kinds-intelligence review K7, ran: `urgent.page` paged an unmarked note).
    - Missing word: **a thing's declared membership** (`is.<kind>`), the first piece of "things declare what kinds they support" (`docs/design/kinds/kinds-intelligence.md`).
  - **Outside services get public text, or the caller's own** (`kernel.py` `place_sees`, `own`, `outside_marks`, called in `module_see`/`module_own`; `map.py` `position`). Alex: "Public, or my own".
    - Every row a module reads says `outside=public|yours|no`, with `outside_not` listing narrower aspects the reader sees.
    - The map geocodes a `location` only when the row allows it; a row without the answer counts as private.
    - Tests: `tests/test_map_outside.py`.
    - Missing word: **a thing's audience, readable by a module**, now `outside`.
  - **The builds review** (`docs/design/kinds/review/approved-builds-review.md`; each ran on a scratch world). Fixed, with tests:
    - **H1:** kits carry a rule's `by`, and a taken rule defaults to `maker` (`kits.py`).
    - **H2:** `own()` is whom a thing was made for, when it says so.
    - **H3:** the map never sends saved text as if typed. A replanned route's stored stops, and a layer's saved `map.find`/`map.near`, go outside only when that thing is public or the caller's own.
    - **M4:** a rule's act is judged by the act that started the chain (`caused_by`).
    - **M6:** undoing a maker's `forget` leaves the rule off.
    - **M7:** a mark on a grandchild kind counts for every kind between.
    - **Low:** `by=` with nothing is refused, and `outside`/`outside_not` are reserved.
    - **Left as they are, with reasons:**
      - **M5:** a module acting on its own counts as its installer, or Alex's window rules never fire. Alex should confirm.
      - **M8:** the derived `contacts` field isn't named in `outside_not`; only the map reads the marks today, and it sends `location` alone.
- **Kinds all the way down, 29 Oct** (Alex approved in the session; design in `docs/design/kinds/kinds-all-the-way-down.md`):
  - `kinds.py`: a need may say its part's kind (`start:time`, `likes:upvote`), parsed into `Need.kind`; `Kinds.met` checks it. Value kinds are the bottom: the kernel's `BASE` (text number time yes-no link person thing), or a declared `value=`. Kinds take `aliases=` (synonyms); `decl` and `fits` read them.
  - `kinds.py`: `aspect_kind` and `parts_of` say what each aspect is a part of; a word whose `acts_on` is a value kind reaches anything with such a part (`_lacks`), and `check_word` returns the part (`part=` chooses among several).
  - `kernel.py` `guard`: sets `part=` on the line, so a verb reads `$part` and a module `kv.part`.
  - `words.py`: `rows <value kind>` lists things by their parts; two see words, **`alike`** and **`aspects`**; `make kind=kind` says which kinds are made of the same parts (`alike_note`).
  - `kits.py`: kinds carry `value` and `aliases`, checked at `validate` and `take`.
  - Tests: `tests/test_parts.py` (16). Two `test_shapes.py` examples of an unreadable shape used `start:time`, now readable; they use `start@time`.
  - Missing words: **a part's kind**, **a value kind**, **a kind's synonym**, and the readings **`alike`** and **`aspects`**. Still missing (found against the Seabright board): **optional typed parts** on a kind (board.py's `fields=`), and **computed parts** (an upvote count over sealed likes).
  - **Later, 29 Oct (Alex: "Yes, go ahead" with clearing loose aspects):**
    - `kinds.py`: **`has=`** on a kind gives optional typed parts (`has="priority:number when:time"`). They're never part of fitting, they're inherited through `extends`, and `aspect_kind`, `alike` and `users` read them. A part may be one of the kernel's own kinds (said, group, widget) without declaring it.
    - `kinds.py` `aspects`: aspects said by one thing only (a setting's knobs) and aspects the kernel computes for the reader (sealed like counts) are counted apart, and the rest are ranked by use. On the live copy that's 89 shared aspects, not 160. **`aspects suggest`** proposes parts from values: all times, numbers, links, yes/no, people, or pointing at one kind; long prose is text. It lists judgment calls: stage-like words, people written as names, hashes, lists, two aspects that always agree. It ends with the exact `set <kind> has=` line.
    - `words.py` `set`: a value that isn't its part's kind is still set, and the reply says so ("high isn't a number: still set").
    - Tests: `test_parts.py`, 19 in all.
    - Missing words: **an optional part**, and **the suggestion** itself. Still missing: **list parts** (a chat's `with`, a card's `blocks`).
    - `kinds.py` `alike`: kinds that share only text parts aren't offered as the same (live: `charter` matched `soul` on where they came from). `_suggest` checks for hashes before prose. Test: `test_kinds_sharing_only_prose_are_not_the_same`. Live since the second kernel restart, 29 Oct.
- `kernel/kernel.py`: missing **external effect metadata admission**. Offers already accepted `undo=external`; do calls now honor that declaration even without an answer flag. Existing entries remain steward-owned and are not overwritten by re-offer. The exact media declarations/adoption boundary are in [NEEDS-FROM-DESKTOP.md](NEEDS-FROM-DESKTOP.md).

## Authored files

Kernel: `kernel/dictionary.py` (new), `kernel/history.py` (new), `kernel/kernel.py`, `kernel/words.py`, `kernel/kits.py`, `kernel/painter.py`.

Regression coverage: `tests/test_missing_words.py` (new; twelve tests). Existing test files and the five other proof implementations were not changed.

Task board: `apps/taskboard/build_lines.py`, `install.lines`, `install.py`, `proof.py`, `NEEDS.md`, `PROOF.md`. Fresh installation is idempotent, with thirteen declarations; no duplicate event kind or event data is needed for history. The older live board was not overwritten.

Contracts/handoff: `SHAPE.md` section 17, this file, `NEEDS-FROM-DESKTOP.md`. Regenerated evidence: taskboard `proof.json`, `drag-receipts.json`, `history-records.json`, `scratch-board.png`; proof `byo-agent.json`, `council-night.json`, `council-phone.png`, `floor-phone.png`, `hunt-evidence.json`, `hunt-phone.png`, `hunt-compass-phone.png`, `kits.json`, `kits-phone.png`, `kits-floor-phone.png`, `web-host.json`, `web-host-phone.png`, `web-host-laptop.png`. Disposable proof worlds remain in the app's ignored scratch evidence directory.

## Boundaries

No live desktop adoption, media source edit, native window test, migration of the installed board or live Board/Shop/Rough spots mutation. This file supplies the source-edit friction log for the coordinator because the task confines writes to this lab. No real media, network service beyond loopback, GPU/model work or visible windows were used.

History is a filtered log reading, currently scanned in memory; no new persistent index. The painter still has no old-desk event stream (`$touched`, `by changed`, `age<`); use explicit timestamps/history rows. Conditional historical visibility which cannot safely be recovered is omitted. Languages currently select dictionary label/help fields; this does not translate app prose or dates. A root drop lane with no bound thing has no independent receiver fence; bound receivers are fenced and regression-tested.

**What would change the assessment:** a leak through a historical visibility transition, a renamed stored head resolving to a different entry after replay/take, or a stale carried/receiver read being admitted. These are explicit regression targets; passing headless tests makes no claim about the running desktop.
