# Seabright round 1 audit — 4 November 2026

Builder evidence for Sable, task dk2599. **Audit only; neither polish round is delivered.**
No application source, live lens, styles, grants or settings were changed.

## What is known

**Read, live through Agora:** standing rules dk838, task dk2599, guide dk371,
Seabright delivery cards, board plan, channel/lens/component metadata and widget
grants. Meetings & events routes to calendar, Asks & offers to its nested lens,
and Research & documents to its document library. The board includes map-panel.
The board widget already has the five scoped document words, file subscriptions
and five map reads. The older permission holds in DELIVERY-RESOLUTION.md do not
describe this current board widget. Do not replay installers or add grants.
The guide's statement that no calendar or map was added is also historical.
The live plan is an authored plan, **not paint evidence**.

**Ran:** `calendar_ui_proof` reached four setup checks, then Chromium failed
before a page opened. Its result has `screenshots: []`. No fresh screenshot,
pointer interaction, keyboard interaction, right-click Comment or drag outcome
was obtained.

The supported `widget_browser.Browser` startup was diagnosed once with stderr
captured, retaining its exact launch flags:

```
CreateFile: Access is denied. (0x5)
FATAL:mojo\public\cpp\platform\platform_channel.cc:112
Check failed: . : Access is denied. (0x5)
crash server failed to launch, self-terminating
```

The diagnostic printed exit code `4294930433` and `Owned profile removed: True`.
No security flags were changed, alternate renderer used, or live desktop touched.
Resolver: Sable/House must provide an authorized hidden evidence run; this worker
cannot repair the execution boundary.

**Ran, world-level only:**

- `test_calendar.py --probe`: `CALENDAR WORLD {"checks": 24}`, exit 0.
  Covers event creation, named attendance, Going/Maybe, one reservation per person,
  invalid dates, default seats, channel catch-up and reply facts.
- `test_asks.py --asks-probe`: `ASKS PROBE OK`, exit 0. Exercises the actual lens
  gesture lines for ask/offer, matching and completion, nested reuse, private
  filtering and idempotent installation in an isolated world.
- `test_documents_ui.test_published_document_word_arguments()`:
  `PUBLISHED DOCUMENT ARGUMENTS: passed`, exit 0. Real published files module:
  browse, folder, upload fixture bytes, store, rename, move and invalid arguments.
  This function deliberately opens no browser; it is not picker/drop evidence.
- Aggregate pytest invocation did not produce a successful suite result. It
  printed `..EEE.EEEE [100%]` then failed during teardown with WinError 5 on its
  newly created `.tmp/pytest-round1` directory. This is a harness access failure,
  not seven established product defects. No ACL changes or removal attempts were
  made against the inaccessible directory.

Raw outputs are in `evidence/tonight-round1/`. All model trials were omitted.
The full older `ui_proof.py` seeds via `Proof.run()`, which calls `model_proof`;
do not run it blindly under this audit's no-live-model constraint.

## Ranked critique for resident selection

The following are candidates, not fixes or fresh browser reproductions.
“Read image” means an archived repository PNG opened during this audit.

| Rank | Finding and evidence | Proposed smallest reusable correction | Required outcome check |
| --- | --- | --- | --- |
| 1 | **Read source:** asks inputs say “Press Enter to post”, but the shared `input` component binds native `change`, with no Enter listener. Editing then tabbing away can publish; Enter behavior does not match the promised explicit submit. `asks.lens`, `components/catalogue.js:8–14`. | Use a general explicit submission capability and an authored form/button; keep ordinary change-bound inputs unchanged. Define the missing submit/commit handle before application wiring. | Type, Tab and Escape must not post. Explicit button/Enter posts once, clears only on success, retains draft on refusal. |
| 2 | **Read image + source:** `calendar/conversation-1440.png` shows weekday names stacked letter by letter and event chips squeezed after the thread opens. Calendar reserves a 240–300px agenda beside its grid; its layout switches on viewport width, although its containing column is narrow. | Repair the shared calendar's sizing relative to available component width; keep sizes/style choices in exposed world handles. No alternate tiling engine. | Desktop board with/without thread, 390px viewport, and the same calendar in a narrow unrelated host. Weekday labels remain readable; RSVP stays reachable. |
| 3 | **Read source:** file reader “Quote selection” sets `quote/source/page/replyTo` directly, with `replyTo=api.view().thread`. The documents arrangement has no thread reply surface, so this visible action can change invisible state. `components/file.js:31–36`, `documents.lens`. | Declare the general quote destination contract; offer actions only when a destination exists, or visibly explain unavailability. Keep right-click **Comment** on the existing shared host mechanism. Do not add Seabright-specific Comment code. | Select text in a standalone reader and nested Documents, activate each offered quote/comment control, verify visible destination and exact stored quotation. Reuse in another lens. |
| 4 | **Read live lens + source:** asks cards have claim and Mark done, but no reply/open-conversation control. Completed items disappear under the default active filter; no visible status filter or undo is authored. The world probe proves the underlying actions and alternate filter exist. | World lens edits using existing thread navigation, filters and receipt-specific undo where available. Expose the complete lifecycle without a second store. | Ask, reply before committing to help, claim, complete, find completed item, recover a mistaken completion. |
| 5 | **Read source; hypothesis to reproduce:** document initial attachment reads file/entry revisions, while “Finish sharing uploaded file” retries with only `{target,entry}`. The retry is missing that explicit fresh read/fence sequence. | Repair the generic document upload recovery path after proving the exact refusal. Retain pending upload and use fresh existing permissions; never broaden grants. | Force a recoverable attach refusal, retry, verify one entry/one file and shared visibility; no duplicate post/upload. |
| 6 | **Read source:** document batch upload clears all queued files on the first error (`queue.length=0`) and redraws its status after completion. Remaining filenames and which files succeeded are not retained as visible outcomes. | Retain a per-file result/retry list through redraw using existing component state. Text and spacing via labels/tokens. | Three files with a failing middle file; successful files stay usable, remaining files are listed and recoverable, navigation preserves destination. |
| 7 | **Read source:** file Previous/Next page and feed Newer/Older remain active at their limits, clamping back to the same value. These controls can look broken although their handlers run. | General disabled boundary states with readable labels and keyboard semantics. | First/last page and single-page document; enabled transitions actually change content, unavailable controls explain the boundary. |
| 8 | **Read images:** desktop feed has long sparse cards with metadata/activity substantially smaller than body text; narrow event composer gives a large message field precedence over event dates and places the final action below the initial viewport. Phone calendar prioritizes the month grid over agenda/RSVP, with a global Write a post action competing with Add event. | First try existing personal/shared spacing, typography, reading-width and composition handles. Preserve the light green direction. Reordering meaningful fields is a world arrangement choice for resident review. | Fresh desktop/narrow comparisons with populated and empty states; readable hierarchy, primary action visible or clearly reachable, no clipped text or keyboard focus. |

## Visual review limits

Opened historical images, not generated tonight:

- `evidence/ui/feed-catchup-1440.png`
- `evidence/ui/compose-event-390.png`
- `evidence/calendar/phone-month-390.png`
- `evidence/calendar/conversation-1440.png`

Hierarchy: clear channel heading and restrained green primary actions; compact
metadata competes with body on sparse cards. Spacing: generous feed whitespace,
but severe calendar compression inside the desktop thread layout. Colour:
light paper/card separation remains consistent; **no current contrast measurement**
was possible. Typography: calendar weekday wrapping is visibly broken in the
archived narrow container. Labels/affordances: ambiguous Enter publishing and
quote destination need direct verification. Empty/loading/error states: not
freshly rendered; old screenshots display “the kernel is away”, so they cannot
prove a healthy current host. Documents and map have no fresh visual critique.

## Control inventory and trace

Inventory is **read from source**, not a claim every control was activated.
Search source links below name the responsible files; the world is the authority
for what an individual viewer may do.

| Area | Visible controls / handler destination | Verification this turn |
| --- | --- | --- |
| Shell/navigation | channel picker/buttons, All conversations, Saved, leaders queue → local view; search Enter → search view; phone search toggles field; Write a post → composer | Live route facts read only |
| Feed/thread | Reply/back → thread state; Post reply → `board.reply`; Upvote → `like`; More → quote, bookmark/follow/hide/mute, history, reason, report, edit and leader actions | Calendar probe admits replies; no browser activation |
| Catch-up | heading → oldest unseen; expand → local state; Mark all seen → `board.seen`; Summarise → private snapshot/model | 24-check world probe covers catch-up facts; model deliberately untested |
| Composer | kind tiles, change kind, channel, fields, advanced/date picker, picker/drop, remove attachment, Post, Cancel | Source trace only |
| Calendar | date cells/chips, previous/next, Today, Month/Week, Add/Cancel/submit, Going/Maybe, Open conversation | World event/RSVP outcomes passed; UI setup 4 checks only |
| Asks/offers | two inputs → `board.post`; I can help/I need this → `claim`; Mark done → `set done=yes` | Actual resolved lens gesture lines passed; no pointer or Enter evidence |
| Documents | breadcrumbs, Make folder, picker/drop, entry expand, Organise, Rename, destination/Move, Finish sharing | Published-word path passed for folder/store/rename/move; upload UI/retry not exercised |
| File reader | Download, photo expand/description, page picker/Previous/Next/Quote, table sorting, media controls, calendar attachment Going/Add to calendar | Source trace only; shared Comment is separate |
| Search | text query/filter inputs, result → owning thread and addressed file/page | Source trace only; no source navigation outcome |
| Map | entry toggle; search, layers, inspector and map canvas; panel limits edits to authored gestures | Live map component and read grants confirmed; tiles, pins, pan/zoom/right-drag untested |
| Shared context menu | selected text → Comment/Copy; object actions, Look/Open, Ask | `pages/menu.js` and `test_shared_menu.py` read; no new invocation |
| Recovery/pagination | world Undo for authored receipt; post hide reason; pages clamp at bounds; pending share retry | Asks completion/world read succeeded; UI recovery pending |

## Continuation and delivery

Sable's live next_action requests the audit and ranked critique before choosing
the build. Candidate priorities above are ready for that review, but the required
fresh screenshots and browser journeys remain blocked. Do not call this round 1
complete, and do not begin “round 2 of the activated increment” against unchanged
source.

Next authorized stage: obtain hidden desktop/narrow captures and direct outcomes
through an execution context whose supported browser can start; reproduce the
top candidates, then select fixes. Preserve the live arrangement. General
mechanism fixes go through source/House; styles, labels, filters and arrangement
changes use world words. Each actual increment still needs resident critique,
House landing, safe activation and fresh outcome checks, then round 2.

Fixture cleanup: the calendar/asks/document fixtures closed their own servers
and module hosts. Their scratch worlds and the browser profile were removed.
The only residual test directory observed is inaccessible `.tmp/pytest-round1`;
its contents/cleanup cannot be verified from this worker. Leave it for the House
owner to inspect using normal authority. No live fixture posts, uploads or
Conversation messages were made. Authorized progress messages went to Shop talk.
