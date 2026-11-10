# Source audit: the kernel and Lines (26 Oct – 3 Nov 2026)

*Evidence for [[SOURCE-EDITS-AUDIT]]. Written by a read-only helper Claude started on 4 Nov; kept as it reported, lightly
trimmed. Labels: **read**, **ran**, **imagined**.*

Scope: 33 non-merge commits; 27 change `kernel/` source, 6 are tests/docs. Read: every diff (39f996a3b, e7c6d8960,
fbc25b03d by hunk); cards dk1813, dk1614, dk1027, dk1811. "Logged" means in the repo.

| commit | what | class | avoidable | how / logged |
|---|---|---|---|---|
| 0a13edce4 | board world: blobs, `/files`, `visibility_of`, groups, clock; plus `make kind=post` shim, `file-settings` steward-only by kind name, `pin_until`, likes only on posts, help text in source | U+S, B/P/C | partly | Kind-level write policy and a general expiring fact. No |
| cf135a623 | `via_actor`, rev on look rows, vote case-folding | U/G | no | No |
| 8df3c934f | concurrency copies; `you_liked` only for posts | G+B | partly | A general "your sealed act on this" reading. No |
| 395b9e07f | door routes theme files to the theme module; kits FIELDS gain theme | S+P | partly | Module-served door paths; kinds declaring kit fields. No |
| fbc25b03d | help engine (epic dk748): START/USEFUL lists and other help content in source | U+C+P | partly | First screen as a topic thing. FRICTION-STUDY |
| 98a2d7407 | `paint-clear`: a one-time migration as a permanent kernel word | B | yes | `forget` a filtered set, or a one-off script. No |
| 5b3779cda | a module's re-offer refreshes its fields | G/U | no | FRICTION-STUDY |
| 96e2a6236 | `forgotten` skips kind paint-report | B | yes | Knock-on of 98a2d7407. No |
| 6d5f93d29 | Lines, plainly (Alex's P1–P7); plus `NOT_NAMED` kind list and `usage_kind` guessing a kind from help text | U+P | no (P part yes) | A kind flag "not nameable". FRICTION-STUDY |
| 6d8e0cf2d | third fresh agent's bugs | G | no | FRICTION-STUDY |
| 397a55b5c | `chat.py` (say/chat, reserved kind `said`); `make` and `happening_for` special-case chat/said | B (U seed) | partly | `sees=` as a list of people, @-addressing as a general reading; `say` as a verb. No |
| 102c30f8e | `say acts=`; `set` on said: speaker only | B | yes | Aspect-level write policy on the kind. No |
| b2bb0e61c | @names inside `text=` | G in B | — | No |
| 7dc2144a5 | `next_steps.py` (236 lines; kinds taskboard-task/task/story/epic), task.* words, `rows nextsteps:` hack | B | mostly | next/revise/followup are plain `set`; review/verify need a general attestation. Named later |
| c58ca70c3 | refusals log (dk939) | U/S | no | REFUSALS |
| 6a71e5443 | a rule rests when its module is off | G | no | commit message |
| 39f996a3b | shapes (`acts_on`/`needs`), rules `by=`, retiring words, security fixes; plus `TELLS_APART`, `NOT_FITTED` lists, `turn work=`, and bonds.py (679 lines, held and dormant) | U+G, P/B | core no; bonds yes | Held research code belongs on a branch. Logged extensively |
| 299497e6d | `$` fill-ins (dk1368); FILL_INS help table in source | U+C | no | not in repo |
| 84d64a880 | `search` (dk1322); SEARCH_TEXT fields, lane "now" ranks first, regex over lens text | U+P | partly | Kinds' typed parts say which fields are text and what "done" is. No |
| 6894568ea | Documents (dk1614): `document_scope`, a `library:` grant clause, document kinds and fields in the kernel | B | yes | A general `within:<container>` grant clause. Named in BOARD-ROUGH-SPOTS, then built bespoke anyway |
| 4de378750 | Documents 2: files.* tables; `module_see` branches on `docs.WORDS`; plus a real `scope_grants` fix | B+G | yes (B part) | `within:` for module reads too |
| e7c6d8960 | Kinds all the way down v1 (approved) | U | no | Logged |
| 4ec84d22b | Twitch (dk1811): `chat.receive`, `external_id` | B | yes | Forced by `said` being a reserved kind: kind-level "who may make this kind" + a uniqueness key. No |
| 628209e33 | `kernel/scratch.py` (Windows ACL, Codex sandbox) | T/S | partly | Test helper in the kernel package |
| fbf90fb85 | card rules (dk1813): `card_signals.py` with `"JEFF"`, `alex_ask`, `module_named("house")`, English templates | B (worst) | yes | The card said "only if a rule cannot say it". Missing: rules over a reading (`each`), dedupe key, `$row.<aspect>` addressing. Unverified |
| 13db35c94 | `lead` as a may word | U | partly | SHAPE §15: may as a predicate, not more vocabulary |
| b3b3c2e3b | `say about=` may name what the act made | G in B | partly | The general `_about` (words.py:852) still lacks it: chat duplicates general handling |

**Tally (read, judgement):** of 27 source commits about 9 mainly bespoke, 3 mixed, 8 universal, 6 general fixes, 1 seam.
Avoidable: yes 8, partly 12, no 7. About 16 of 27 have no repo-visible rough spot. 5 of the 7 worker commits that touch kernel
source are bespoke, mostly old-desk ports on 2–3 Nov.

**Growing, not shrinking (ran):** built-in words 40 at cb0bac2a4 (24 Oct) → 75 at HEAD, zero retired (`paint-clear` still
live); about 19 of the 35 new words serve one app (task.* ×6, chat ×3, files ×4, painter ×4, paint-clear, turn). Kernel
source 13 files / 3,756 lines → 25 files / 8,969 lines.

## Hotspots (ran: commits per file and per enclosing function)
words.py 17, kernel.py 15, helping.py 6, chat.py 6, dictionary.py 5, door.py 4, kits.py 3. By function: `KERNEL_ENTRIES` 13,
`KERNEL` dict 11, `make` 7, `set_` 6, `rows` 6, chat `say` 6, `word_set` 5, verb fill-in 5, `_fire_rules` 4, help lists 4+3,
kits FIELDS 3, `shown` 3. Two magnets: the word registry (a word cannot exist without a source entry, so the kernel is the
cheapest place for code) and `make`/`set_`/`shown` (kinds can say their shape but not their policy).

## Tenant names inside the kernel (read, HEAD)
- People: card_signals.py:35,52 `"JEFF"`; words.py:129 and chat.py:4,23 `with="Alex, JEFF"` in help
- House/taskboard: card_signals.py:72 `module_named("house")`; next_steps.py:14 KINDS, :16 MATERIAL, :20 PRIORITY;
  words.py:23-37 task.* first in the dictionary, :938 `rows nextsteps:`; readings.py:70; kernel.py:558 NOT_NAMED; :1454 `turn work=`
- Documents: document_scope.py throughout; kernel.py:1010, 1836, 1854, 1961-1991
- Chat: words.py:247 RESERVED_KINDS (`said`, `paint-report`, `web-layout`), :685, :767; kernel.py:1106; chat.py whole file
- Board: kernel.py:500 posts and likes, `pin_until`; words.py:306, 665, 680, 764; painter.py:189; blobs.py:129, 226
- Search: helping.py:21 "search Seabright"; words.py:1005, 1011-1014, 1066
- Painter/desktop/theme: helping.py:24; door.py:171, 209; kits.py:11-24, 88; world_words.py:72; kinds.py:61-63; bonds.py:38, 74;
  words.py:21, 692, 799, 1214-1215; painter.py:27 imports the archived old desk
- Aspect lists: kernel.py:589 TELLS_APART; kernel.py:1272 SUPPLIED

## Universal edits that paid off (read)
- `visibility_of` / `within=` (0a13edce4): reused by chat, card_signals, document_scope, blobs, map, board, documents.
- Refusals log (c58ca70c3): its first day produced 6a71e5443's four fixes.
- Shapes (39f996a3b): board.py and builders.py kind checks became world `needs` ("word-set board.rsvp needs=… without
  editing this file").
- Rules `by=`: card-rules.lines is 5 world rules. `lead` (13db35c94): resident authority became a world opt-in.
- Re-offer refresh (5b3779cda) stopped hand fixes after module changes.
- Value kinds / `has=` (e7c6d8960) could already retire SEARCH_TEXT and TELLS_APART; nothing uses them for that yet.

## Missing mechanisms (imagined, counts read)
1. **Kind policy as world data** (who may make/set which aspects, immutable aspects, made only by X, kit fields, flags,
   per-reader readings). ~10.
2. **An in-process extension tier** (reviewed Python bound to a world entry, living in the app's folder). ~9. Moves code
   rather than deleting it, but kernel diffs would then mean mechanism.
3. **Relational authority** (`may=`/`sees=` as a predicate over aspects; SHAPE §15). ~6.
4. **Set-at-a-time rules and verbs** (`each <reading> do=`, dedupe key, `$row.<aspect>`). ~4.
5. **Container-scoped grants and reads** (`within:<id>`). 3.
6. **Help and first-screen content as topic things.** 6.

## The helper's thinking (imagined)
The kernel is the only place where code runs in-process, inside the act's transaction, sees everything and can make reserved
kinds, so anything needing atomic multi-thing writes, iteration, dedupe or "only this module may make X" lands there. Old-desk
ports turned each helper into a kernel file; workers named the missing word and then built the bespoke thing. A header should
give an admission test (no kind, word, module, person or aspect name in code except the kernel's own; `if kind ==` means stop),
list the tenant debt with the mechanism that retires each item, and be backed by a ratchet test counting tenant names in
`kernel/` against a shrinking allowlist.
