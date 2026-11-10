# Seabright round 2 — source increment, delivery still pending

Builder review for Sable, task dk2599, fresh worktree
`kernel-dk2599-8dc06161e3`, based on landed round 1 `3d9dbb48c`.
No commit or live publication was made here. **Neither round is claimed
activated/resident-verified.** Live byte publication remains held on Alex's
import decision, as read in Shop talk. No workaround was attempted.

## Follow-up evidence (5 November; supersedes status below)

Read: helper reported all six journeys PASS, including actual map Undo, on
the preceding build. It then found notice leakage between views, delayed
feedback, connection-pill overlap, missing Lost pet, internal Search kinds,
misleading model-limit wording, and absent Work reuse.

Source fixes now cover those issues; standalone widget/runtime activation
remains blocked by this worker's no-widget scope. New async checks cover stale
Undo, navigation away/back before admission completes, immediate input clearing
and remount locking. Real fixture receipts verify Work Mark done/Undo.
Fresh hidden browser screenshots and outcomes of these latest bytes are still
pending. This does not claim activation or a second resident acceptance.

## Earlier evidence and critique (retained)


**Read:** current task, charter, guide, window list, component IDs, prior worker
handoffs and the helper's six-journey findings through Agora. The helper reported
five journeys passed and map drag/Undo failed before these fixes. This builder
did not reproduce those six journeys in a browser.

**Viewed:** helper baseline images under
`C:/Projects/Agora4/.worktrees/kernel-dk2669-08e8186041/.scratch/dk2669/shots/`.
Reviewed `feed`, `thread`, `composer-event`, `calendar`, `asks`, `documents`,
and `map`, each `-1438.png` and `-388.png`. These are earlier baseline rasters,
not screenshots of round 1 or round 2 fixes. Two local contact sheets and a
SHA-256 manifest are in this worktree's `.tmp/baseline-review-{1,2}.png` and
`.tmp/baseline-manifest.json`. Asks narrow and Documents desktop were also
opened at original size.

| Surface | Concrete baseline critique | Response / remaining check |
| --- | --- | --- |
| Feed/thread | Light paper and green accents are coherent. Small metadata and activity compete poorly with body text; very wide one-line cards waste space. Reply outcomes were invisible in helper journeys. | Keep direction; fix reply lifecycle and exact-receipt action outcomes. Typography/density still needs resident comparison; no measured contrast claim. |
| Composer | Message field precedes event details; narrow final action is below the initial viewport. Helper saw unrelated map kinds and required capacity. | Preserve landed field-order/footer change; scope kind declarations in world data; populate defaults and make event capacity optional. Fresh before/after still needed. |
| Calendar | Empty day is explicit; the month grid dominates the narrow screen. Header controls compete at narrow widths. | Preserve container-based round 1 layout; expose attendance receipt recovery. Phone agenda priority remains a resident visual check. |
| Asks/offers | Duplicate heading, fused badges, tiny digit-bearing avatars, cramped input labels and large unstructured whitespace. | Authored spacing, readable helper heading, initials format, generic input/badge presentation, status/side filters, explicit Reply, completed-item recovery. |
| Documents | Duplicate native picker/drop affordances; detached narrow desktop form; folder label crowds its input. | One keyboard-accessible picker/drop surface, full available library width, stacked label, explicit empty-name feedback, singular page label. Duplicate library/channel heading and upload batch recovery remain rough. |
| Map | Heavy open Layers panel competes with map; narrow controls crowd the canvas. Help advertises absent Add and exposes a raw command. | Preserve collapsed Layers from round 1; capability-dependent help/Route; Details disclosure; exact movement receipt notice. Fresh narrow screenshot must confirm notice placement and map access. |

Empty/error/loading: inspected only the earlier rasters and executed handler
states described below. The baseline host's "kernel is away" toast is not
evidence of a fresh runtime failure here. Summary pending/slow/failure states,
empty-folder feedback and refused Undo are explicit in source and adapter
checks. No screenshot or contrast pass is inferred from these checks.

## Built

- General painter startup catches refused event hints, paints from authorised
  reads, records the limitation in screen-local component health, and retains
  normal reconciliation. No permission changes.
- Shared host menu uses a readable text excerpt for untitled items and Comment
  link labels. No Seabright-specific Comment handler.
- Reusable `action-notice` plus catalogue button completion/selection handles:
  exact receipt Undo, inline refusal, dismissal, protection of a newer notice.
  Local `restore` outcomes are reused by Tasks & work filters.
- Map moves, claims, RSVP, private board actions and ask completion publish
  recovery outcomes. Only the exact admitted receipt is reversed.
- Replies clear the currently mounted input, block pending repeats, preserve
  refused drafts and newer typing. The same thread handles Asks text blocks
  through configurable view keys.
- Dialog titles match their actions. Composer kind scope/defaults come from
  world declarations. Search has a button, query reset and authored date format.
  Summary visibly reports progress/failure with no automatic model request.
- Documents form and page grammar improvements; map unavailable affordances and
  technical fact disclosure. Board and map bundles remain ready-to-import files;
  Documents now has its own generated bundle too.

World-capable intent is in lens/data files and component metadata. Source
changes repair general mechanisms or add the general action-outcome capability.
No widgets, HUD, tiling engine, security settings or credentials were changed.

## Ran

All Python commands used `C:/Projects/Agora4/.venv/Scripts/python.exe`.

| Check | Printed result | What it proves |
| --- | --- | --- |
| `node test_round2_components.cjs` | `ROUND2 COMPONENT CHECKS 43` | Real component handlers in a DOM adapter: remount/double-send, failure retention, exact Undo, newer notice protection, Work reuse, dialogs, scope/defaults, scoped reply, own-offer restriction, Offer clearing, Documents picker/pagination, event count, visible Upvote, menu-name function, map contracts, stubbed offline/empty summary, query reset |
| `node test_round2_painter.cjs` | `ROUND2 PAINTER CHECKS 5` | Actual startup block and view subscription function reach refresh after zero, one, six or seven refused subscription hints; reports health after paint |
| `test_round2_world.py` | `ROUND2 WORLD CHECKS 14`; `ROUND2 FIXTURE REMOVED` | Real words/receipts and compiled Asks bindings; replies, done/filter/Undo, two-coordinate recovery preserving an unrelated later act, default seats, RSVP reversal, hide reversal, no grant/widget/window changes |
| `node test_round1_components.cjs` | `ROUND1 COMPONENT CHECKS 23` | Existing handler regressions retained, including document quoting and pagination |
| `test_round1_world.py` | `ROUND1 WORLD CHECKS 8`; `ROUND1 FIXTURE REMOVED` | Imports and exact document quote world outcomes retained |
| `test_asks.py --asks-probe` | `ASKS PROBE OK` | Existing isolated ask/offer claim/completion/nesting regressions |
| `test_calendar.py --probe` | `CALENDAR WORLD {"checks": 24}` | Existing event/attendance/catch-up world regressions |

Adapter tests do not establish browser layout, selection, focus, pointer/drag
or native menu behaviour. The map world check reverses the same `set lat/lon`
receipt used by the drag handler; it is not a new drag journey. Summary uses
an in-memory fixed stub; no real inference was requested.

An initial world check incorrectly filtered `rows` by virtual id; the test now
finds the returned row by id. A discovery check exposed missing receipt wording;
the component card now explicitly documents receipt and local-view recovery.
Both were corrected before the 14-check pass.

Broader pytest did **not** pass: it printed `E.FEEEEEEE.` then stopped during
cleanup with `PermissionError [WinError 5]` on
`.tmp/pytest-round2-final`. No retry or permission workaround was attempted.
The RSVP test wrapper also constructed a nonexistent worktree-local Python
path; it now uses the pinned interpreter. The broad suite remains unverified.
House must inspect/remove that inaccessible owned scratch directory.

Follow-up filled remaining source gaps: refused `hear:view` is now reported;
own offers cannot claim; unbounded event facts omit the places-left caption;
action-row controls share token-based treatment and a visible Upvote label;
Documents has a native Choose files button and no one-page pagination;
offline/empty model answers have explicit unavailable states. The 43/5/23
component/startup/round-1 checks were run after these changes, along with
bundle and menu/painter syntax checks. No git commands were run in follow-up.
The world event default of 500 is preserved, so blank capacity is not an
unlimited attendance contract.

## Delivery remaining

See [ROUND2-PUBLICATION.md](ROUND2-PUBLICATION.md). Sable must review this source
and arrange the already-authorised helper's model-stubbed hidden reruns against
each increment before House commits/lands it (JEFF dk2735). Helper
acknowledgement is pending. Required: all seven desktop/narrow
surfaces, six real journeys, visible-control sweep, after screenshots and
resident critique. No new worker was started here.

The existing Chromium access-denial boundary was not retried or bypassed.
This worktree has no fresh before/after screenshots and no live outcome proof.
Activation is held pending Alex's decision; restart alone cannot update stored
component bytes. The standalone plain-lens fallback and missing widgets remain
outside this component publication. Painter startup source repair is not
activated in old stored widget runtimes.

Still unaddressed: document batch upload remainder/retry fencing, exhaustive
buttons/keyboard/screen-reader/contrast audit, persistent recovery after window
closure, fresh native Comment regression, and all resident/live acceptance.
No live fixture posts, uploads or Conversation messages were made. Real fixture
worlds used by the direct proofs were closed; the two explicit cleanup probes
verified removal. The inaccessible pytest scratch is the stated cleanup limit.
