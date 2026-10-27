# Missing kernel words: review handoff

Builder, 24 October 2026. Scope: `research/kernel-lab/` only. No git state changes, live installation or desktop restart. Claude owns review, the Board update and commit.

**Read:** repository AGENTS.md and the live charter; SHAPE including section 17; Communities and the Dictionary; taskboard NEEDS, installer, proof and painter; the old desk's carried/receiver fences; `kd_media.py` offers (read only).

**Built:** steward `word-set`/`word-rename`, single-entry translations and reader `language`; stable stored verb/rule bindings and kit transport; `history` and a painter row source; carried identity and both participants' fences; composed-word happenings and rule kind filters; actual made/changed record timestamps and `$today`. Every new word has a dictionary entry and help. Taskboard uses these shared words, with no app module or host logic.

**Ran, final source:** `C:/Projects/Agora4/.venv/Scripts/python.exe -m pytest -q research/kernel-lab/tests` printed **`79 passed, 30 subtests passed in 109.95s (0:01:49)`**, exit 0. This includes twelve new general regression tests. Proofs: Council night **`21 of 21 checks passed`**, Hidden hunt **`17 of 17 checks passed`**, Kits **`23 of 23 checks passed`** (including its screenshot checks and an unchanged 21-check Council night), BYO agent **`25 of 25 checks passed`**, Web host **`20 checks passed`**, Task board **`21 of 21 checks passed`**; all exit 0. Existing assertions were retained; the board's unsupported-drag checks were replaced by successful movement and stale competing-drop checks. The current board screenshot was inspected: the dates themselves contain actual timestamps, rather than the compiler's empty event frame. Module aliases retain the caller's group, module authorship, their own entry's metadata and exactly one own-word happening.

## Rough spots repaired: missing world words and source edits

- `kernel/dictionary.py`, `kernel/words.py`, `kernel/kernel.py`, `kernel/kits.py`: missing **word-set**, **word-rename**, **language**, same-entry translated labels, and durable stored heads. Metadata stays world data; implementation remains code. Old saved lines bind before name edits. Kits transport one executable representation with remapped entry ids and preserve translations. The old `rename` can no longer publish a world verb into a module namespace.
- `kernel/history.py`, `kernel/kernel.py`, `kernel/words.py`, `kernel/painter.py`: missing **history** and record dates. Readings filter the current thing and historical/current fact visibility, never raw testimony or another thing's facts. Sealed rows have neither authors nor facts. The facade registers a row source in its imported compiler instance without editing the desk's source.
- `kernel/painter.py`, `kernel/kernel.py`: missing **carried/drop admission**. Observed identities translate at the facade, both participants' reads join the fence, and admission/commit recheck them without waiting on a module under the lock. Prefix fences include removed fields. The unchanged lens.js really drags the scratch cards.
- `kernel/kernel.py`, `kernel/words.py`: missing **a composed word's own happening** and **rule kind filtering**. A committed verb announces once in addition to its parts; entry-bound hearing survives renames. `rule on=… kind=… do=…` or `make kind=rule on=… of_kind=… do=…` filters the target kind, still running as the author. No-record no-ops and see words do not announce acts.
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
