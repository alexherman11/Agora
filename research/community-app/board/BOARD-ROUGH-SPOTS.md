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
| kernel-lab/genesis.example.json | sync the generated guide text after the concurrent painter builder's guide edit; two guide consistency tests otherwise failed |

Board-specific collection processing lives in board.py as a reviewed process,
not additional kernel app commands. Definitions and composition remain world
things. Files.py is a separate, minimally granted process with no network use
and no durable private database. Conversion bytes and derived text remain CAS
blobs beside the world. Existing model inference stays in the model process.
