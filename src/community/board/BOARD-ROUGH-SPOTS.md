# Board builder — missing words found

Builder draft, 26 October 2026. These are source edits awaiting Claude's review,
not live-installed behavior. No painter/ or components/ source edits.

| Source | World-level word/property that was missing |
|---|---|
| kernel/blobs.py (new) | upload, attach, file-result, file-read; bytes outside testimony; inherited attachment access and safe serving |
| kernel/world_words.py (new) | group, dictionary-copy, clock, forgotten |
| kernel/words.py | dictionary registration/help; rich post facts and narrow sees; within; pin until; forget reason; poll closing; group list reading; steward file-settings |
| kernel/kernel.py | inherited who-sees; effective pin expiry; option counts on rich posts; group-scoped module answers/grants; once of component words; human ownership through immutable for; no empty things after undo |
| kernel/dictionary.py | group leaders can word-set scoped entries while place words stay steward-held |
| kernel/door.py | authenticated byte upload and visibility-checked file routes, caps, no active uploaded pages |
| kernel-desktop/widgets.py | upload as the widget's person intersected with current grants |
| kernel-desktop/pages/widget-host.js | agora.upload(file, group?) on the shared widget/component bridge |
| kernel-desktop/kdesk.py | bounded upload bodies may exceed the old 100 KB bridge-line cap; other bridge messages retain their cap |
| modules/model/model.py | explicitly requested, caller-visible photo context uses the cleaned thumbnail and labels its suggestion |
| pyproject.toml | approved pypdf/Pillow dependencies pinned to installed versions |
| agora/genesis.example.json | sync the generated guide text after the concurrent painter builder's guide edit; two guide consistency tests otherwise failed |

Board-specific collection processing lives in board.py as a reviewed process,
not additional kernel app commands. Definitions and composition remain world
things. Files.py is a separate, minimally granted process with no network use
and no durable private database. Conversion bytes and derived text remain CAS
blobs beside the world. Existing model inference stays in the model process.

## Meetings & events calendar (Claude, 28 Oct 2026, card dk1500)

| Source | World-level word/property that was missing |
|---|---|
| board.py `board.events` | a reading that joins a dated thing to its RSVP things with names (who is coming); `rows` cannot join or count related things |
| board.py `board.post` | kind `defaults` (world data) and a title standing in for empty text, so a quick calendar add need not ask for seats |
| board-components.js | a lens cannot choose a part by a fact of the *selected* thing (`only when` sees view and the row, not the chosen channel's facts), so navigation copies `board-channel.opens` into `$view.opens` |
| agora/components/calendar.js | the catalogue `calendar` was a month grid with no week, add or RSVP |

Seen while testing, not fixed: the painter re-renders the whole tree when a reading changes, so a press that
lands while another member's change arrives can be lost between pointer-down and release (the proof presses
again, as a person would). Keyed, in-place repaint would remove it.

## 'New since' header (Claude, 29 Oct 2026, card dk1512)

| Source | World-level word/property that was missing |
|---|---|
| board.py `board.seen in=` | a last-seen marker per channel; one board-wide marker meant catching up in one channel cleared all |
| board.py `board.catch-up` | new conversations (category `new`), `at` and `first`, so a view can find the oldest unseen thing |
| board-components.js `$view.focus` | no word to scroll a thread to one post; the thread pane does it once per jump (draft-remembered) |

Seen, not fixed: the `catch-up` verb (install.py, `steps='board.catch-up'`) does not pass `in=` through, so
`catch-up in=<group>` silently answers for the whole board. Kernel line keys are lowercase only
(`kernel/lines.py` KEY), so no component's camelCase setting (`weekStart`, `previewCount`) can be named in
`personal-view`; lowercase settings (`view`, `label`) work.

## Scoped Documents metadata admission (Codex, existing dk1614 follow-through)

Missing world capability: a provider's make/set grant could limit kinds or
existing thing ids/fields, but could not bind new folder/entry metadata to one
document library. Source draft adds `only=...;library:<id>` admission in
`kernel/document_scope.py`, called by `Kernel.reaches`, and passes the full make
shape before any post delegation in `words.py`. The clause requires inherited
library visibility, one matching group and metadata-only writes; unrelated file,
policy and cross-library writes refuse. Regression cases are in `test_shapes.py`.
No grants, root creation, live source publication, activation or migration.
See DOCUMENTS-SCOPE-REVIEW.md for held resolver decisions and unexecuted tests.

## Documents outer call and provider read selection (dk1614)

Missing world capability: `grant ... only=library:<id>` did not constrain an
outer Documents word or the rows a provider received while answering it.
`Kernel.module_word/module_see` now enforce a per-call library context, using
`document_scope.selection/read_rows`; atomic answer admission retains that
selection. Grant scope matching checks location/issuer and bound aliases.
Recovered exact dk1561 source adds inherited metadata creation and restores
provider word offers. No installer permission expansion or live publication.
Memory checks passed; persisted-world and UI review remain held. See
DOCUMENTS-ISSUANCE.md for exact principals, clauses, evidence and resolvers.
