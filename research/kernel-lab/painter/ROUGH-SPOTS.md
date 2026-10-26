# Painter rough spots and source boundary

Builder draft for Claude's review, 24 October 2026. No git state changed.

Small general kernel additions in `kernel/words.py`:

* `component`: the missing steward word for reviewing inline component bytes;
  `reviewed_code` is reserved so ordinary `set` cannot forge review.
* `look-view`: the missing data-only description word for arrangements and facts.
* `components` and `help <component>`: the missing discoverability words/cards.

Their implementations live in `painter/arrangement.py`. The stopped run had
already added `component`, `look-view` and the reserved hash; this run finishes
and tests them. Existing grant/undo scope edits in `kernel.py` and `words.py`
belong to the pixel-guy builder and are preserved. No edits to kd_guy.py, sprite.py,
the old lens painter, git index, branches or history.

The painter runs through the existing guarded widget host. No native desktop
code changes are needed to serve inline world modules. Live verification found
that `window.open`/`window.focus` said "brought forward" even when Windows refused
keyboard activation and Chrome still occluded the requested board. A small
`kd_window.py` repair now checks actual activation, then raises the ordinary
requested window without activation if necessary. It never makes it topmost,
attaches input threads or synthesizes input. Four fault-path tests cover this
opening contract; native pixels must still establish the final visible result.
`widget_browser.py` also accepts optional test-only background-throttling flags;
its default host/runtime behaviour is unchanged.

Known boundaries to measure: components are trusted and can use ambient DOM;
cards/lanes are five app components above primitives; per-person state is an
owned world preference; rich text is a safe display subset and source editor;
virtualisation currently windows fixed-height arranged rows after binding, not
server-side pagination. Core focus defaults do not establish screen-reader QA.
The native shared Comment mechanism has not yet been attached to this painter.

New source is a proposed implementation until Claude reviews and adopts it.
Running scratch tests imports the candidate; it does not alter a resident/live
kernel. Live installation must verify that the running kernel answers the new
words before writing component definitions.

## 26 October: community board presentation (builder draft)

Claude owns review and commit. Missing general world handles supplied by this
candidate, with no `lens.js` edit or git-state operation:

| Source | Missing world capability |
| --- | --- |
| kernel `words.py` | `look` on ordinary things returns its current `rev`, so a file/post read can supply an explicit gesture fence. Immutable `via_actor` preserves verified agent origin through a module wrapper; ordinary lines cannot forge it. `vote` preserves an option's declared case (with unique case-insensitive fallback), rather than refusing `Saturday` because it lowercased it. No new dictionary word. |
| `arrangement.py` | A collection over an admitted reading (`of reading:"..."`), preserving its order and painted revisions; `limit`/`offset` bound construction. Dynamic values are quoted data, not executable fragments. |
| `arrangement.py`, `painter.js` | `watch reading:"..."` observes metadata (such as current names/roles) without constructing a collection; changes repaint and `api.read` reuses the observed result. |
| desktop `widgets.py` | Evaluate those readings as this viewer's widget principal, outside the kernel lock; private instance projection supplies validation of later health/control reports. No new kernel dictionary word or dispatch was added. |
| `painter.js` | Local selection/drafts, structured authored form fields, declared child-slot settings, per-paint shared readings, owner cleanup and permission-checked file Blob handles. |
| desktop `widgets.py`, `pages/widget-host.js` | File-check under widget grants followed by the trusted parent's authenticated `/files/<thing>` fetch. The child gets only a Blob. `connect-src 'none'` is unchanged; `media-src` changes from none to exactly `blob:`. Images already allowed `data: blob:`. |
| desktop `pages/widget-host.js` | Bounded bridge backpressure: more than eight attachment reads previously disappeared silently, leaving pending promises and projection refresh stuck. Queue up to 64; excess receives a polite explicit refusal. |
| desktop `pages/widget-host.js` | Pace component-view calls below the existing forty/second server cap, instead of turning an attachment-rich burst into component failures. Other widget painters retain their existing timing. |
| desktop `pages/widget-host.js`, `painter.js` | Permission-checked `download` and `downloadReading` run the actual download in the trusted parent. The opaque frame retains no allow-downloads, no allow-forms and no network. Files recheck `/files`; calendar text comes from an admitted see reading. The parent forces octet-stream download and sanitises names. |
| desktop `widget_browser.py` | The hidden driver permits only top-frame authenticated GETs to exact `/files/<thing>` paths. Opaque children still cannot request them. |
| `primitives.js` | Silent overlay disposal lets reconstruction clean up old modal listeners without closing a newly reconstructed draft. |
| `primitives.js` | `P.submit` validates a form and dispatches its guarded local action on pointer/keyboard activation without native form navigation. The no-forms sandbox otherwise blocks native submission before a submit event. No allow-forms or form-action exemption was added. |
| `painter.js` | Preserve a selected passage across reconstruction only when the bound part's complete text is unchanged. Changed sources still require a new selection and the world checks exact quotes. |
| `arrangement.py`, `handles.py` | General `labels ui` / personal UI label maps; bounded numeric theme tokens and safe plain font-family tokens so line height, weight and reading type are world facts too. |
| catalogue / general components | Sealed `poll`, claimable `slots`, converted `file`, declared `field-list`; table `sortable` text-cell handle. |

The board's application-specific components, styles, arrangement, installer and
acceptance are in `research/community-app/board/`. Module readings remain the
authority for ranking, privacy, quotas, votes and admission. A last painter
observation is not a pixel or screen-reader audit. The first candidate run found
the bridge backpressure bug while opening thirteen actual converted attachments;
the failed run is retained in `ui-quick2-run.txt`.

## 26 October: failure boundaries and missing editing words

Builder draft; Claude reviews/commits. No git state changed. Missing world-level
capabilities and the source seams that now supply them:

| Source | Missing word or capability |
| --- | --- |
| `kernel/words.py`, `painter/handles.py` | A part-style write that cannot paint must refuse atomically; exact alpha colours, CSS spacing shorthand and safe motion tokens. |
| `painter/arrangement.py` | Compact `look-view`, full `plan=yes`, node-local validation, display labels/formatters, personal modifiers and declarative event/fact motion. |
| `painter/health.py`, kernel dispatch | `component-health`, `component-action`, private viewer reports and happening targets, revision-checked previous-version recovery, steward-only quarantine clear; `personal-view`/`personal-style` shortcuts. |
| `painter/isolation.js`, `painter/painter.js` | One component's stopped card, callback ownership, stale last-good DOM, timing and observed text/computed styles. |
| `painter/quarantine.js` | A terminable execution thread for a looping part; bounded DOM/control vocabulary when sandboxed sibling frames share a renderer. |
| `painter/install.py` | Install the new painter support and explicit health/control/hear grants; publish the updated guide. |
| `components/{card,lane,catalogue}.js` | Visible display values independent of domain settings. No component-specific kernel word was added. |
| desktop `pages/widget-host.js`, `widgets.py` | A trusted parent's phase/heartbeat watchdog that can record quarantine while its painter thread is frozen; blob Workers inherit the existing no-network CSP. |
| desktop `widget_guard.py` | Renderer failure recovery and a native ownership check before terminating a hung renderer. No PID comes from JavaScript, no shared renderer is killed, and opaque frames have no native recovery authority. |
| `painter/process_gate.py` | Remove the old full-screen-browser exception; both games and full-screen foreground programs block live steps. |
| `painter/browser.py`, proofs, desktop native test | Updated explicit plan contract and hidden/native acceptance seams. Hidden native pointer tests cannot await stopped compositor frames. |
| kernel building guide, ARRANGEMENT.md, ISOLATION.md | Agent-discoverable handles and a precise separation between projected structure, reported paint, native liveness and live adoption. |

The first in-page loop needs external recovery and can pause that view. Worker
quarantine is a thread boundary, not process-memory isolation; arbitrary browser
APIs are not emulated. See ISOLATION.md for the measurements, test outputs,
initial cold-model proof failure, and live adoption status.

## 26 October: board acceptance follow-through (builder draft)

Additional missing handles found while exercising the board, for Claude's
review; the UI job has made no git-state changes:

| Source | Missing world capability |
| --- | --- |
| `arrangement.py` | Pass a full reading row to a declared JSON setting without stringifying away its structure; `personal-view view.*` supplies initial selection defaults. |
| `isolation.js` | Discard an obsolete generation's media capabilities while retaining its last-good text. A stopped attachment says that its previous preview needs reopening, rather than retaining a revoked image URL. |
| `components/file.js` | Reserve photo space while permission-checked bytes decode; use the thumbnail variant in feed cards and cleaned full content in a thread. Imported ICS exposes its richer event's authored RSVP/calendar gestures. |
| `components/slots.js`, catalogue | A general `label` heading, falling back to an event slot's title, distinguishes event capacity from an independent volunteering slot. |
| desktop `widget_guard.py`, trusted parent | A one-use native download handshake for the exact trusted top page's Blob URL. pywebview globally disables downloads; enabling all downloads would weaken the boundary. The native handler permits only a registered, unexpired URL, sanitises the name and asks for the user's destination. The hidden proof replaces only the chooser with a scratch destination. |
| `board.py` | `board.badges` must expose visible leadership scope for allowed actions. Feed/search must restrict themselves to declared board channels, so unrelated world posts do not appear. Calendar filenames use the event's human title. |

PDF page text and quote attribution are verified. Original PDF page graphics
still depend on an installed renderer; none was installed during this job.
The native download/file proof exercises a never-shown WebView2, not a public
web deployment. The frozen fresh-agent tweak trial remains the next review.

## 26 October: neighbourhood polish (builder draft, review pending)

| Source edits | Missing world-level handle or reading |
| --- | --- |
| `kernel/kernel.py` | Read my own sealed choice/upvote (`your_vote`, `you_liked`) without exposing another person's sealed keys. |
| `painter/handles.py`, `arrangement.py`, `painter.js`, `primitives.js` | Short relative and calendar formats, letters-only initials, dynamic `api.format`, viewer identity on nongesture parts, a bounded local smart-date parser and disposable selection-only actions. |
| `components/date-tile.js`, `poll.js`, `slots.js`, `file.js`, `field-list.js`, `painter/catalogue.py` | Reusable date tiles, private-choice result bars, meters for any claimable thing, reader page/pageTarget handles, clean full-size photo viewing, owner-only description editing, date formatting for generic fields. |
| desktop `kd_window.py`, `pages/widget-host.js`, `pages/widget-slots.js` | Human widget window titles without an implementation prefix. |
| board `board.py` | Change RSVP status without claiming a second seat; page search and imported calendar catch-up results identify their owning thread/file; decisions retain the deciding leader. |
| board `board-components.js`, `board-theme.css`, `board.lens`, `ui_install.py` | Authored compact feed and conditional reading pane, theme measures, grouped catch-up preview count, compose tile declarations/advanced fields, selection quote fallback, live search filters. New handles are in UI-HANDLES.md and ARRANGEMENT.md. |
| board `ui_proof.py`, `test_polish.py`, `polish_dates_proof.js` | Hidden regression interactions and explicit layout/privacy/date/contrast checks. Existing interactions are preserved with new labels and tile flow. |
| `painter/proof.py` | Compare replay and live scratch facts at the same committed instant, holding the existing writer lock while asynchronous paint reports can arrive. No assertion weakened. |
| `painter/browser.py`, board proof driver | Recognise Chromium's alternate detached-session wording; service both hidden browsers' intercepted requests during waits. The two-person check also verifies the frame's timeOrigin stayed unchanged. |
| board `polish_live.py` | Gated installation without a board opening, with preserved task/history/window/provider snapshots and a fresh structural projection. |
| `painter/painter.js`, board composer | Successful gesture-local selection before repaint (`api.fire` values.select); dismiss a committed one-action dialog without reconstructing a blank replacement over Undo. Failed actions retain their form/draft. |
| `kernel/kernel.py` | Snapshot dictionary enumeration and shown-row facts while module registration/writes run concurrently; avoid dictionary-resolution work for zero reactions. Counts and reader-only seals retain their existing authority. |
| board shell, installer and guide | `root.extras=feed` keeps a stopped extra sibling in the feed's scroll column instead of displacing/narrowing the thread. `alongside` remains available. |
| `painter/browser.py`, UI capture driver | Publish whole PNGs atomically with a unique scratch file and bounded transient-lock retry; never truncate an existing proof raster while a reader has it open. |
| general `file`, catalogue, board entry/lens | `pageRequest` re-addresses an open reader; search thread/file/page travel in one local selection so an intermediate page-one render cannot win. |
| general `file.owner`, board lens | Supply already-projected upload ownership so poster controls have their space immediately and do not move the reply footer after a late metadata lookup. Admission remains with the kernel. |

| general selection action and board thread lens | Consume the selection only on explicit quote; render the existing forgotten/Undo reading inside an open hidden thread so phone users can restore it without an invalid reply form. |
| general poll labels | Singular `voteCount` handle for a one-vote total, preserving the existing plural `votes` label. |
| board shell navigation | Reuse Saved/queue world readings in the compact phone picker; preserve leader admission and clear bookmark ordering when returning to channels. |

The parser accepts English weekday/today/tomorrow plus local time or ISO local
date/time. Responsive breakpoints remain CSS defaults, explicitly identified in
the guide. All work is uncommitted for Claude; `lens.js` is untouched.
