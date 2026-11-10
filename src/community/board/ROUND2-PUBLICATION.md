# Round 2 publication handoff — held, not an activation command

Source base: round 1 `3d9dbb48c`. House commits and lands this worktree; the
builder does not commit. **Do not replay whole installers against the live
world.** No grants, widgets, HUD code or provider changes are part of this
publication. Preserve existing facts not named below.
JEFF's latest Shop talk (dk2735) requires the browser helper to check this
actual round 2 build before committing. The helper subsequently reported all six journeys passing, including map Undo,
then reported notice navigation/latency and other defects. The follow-up below
fixes those in source. A fresh helper rerun of these latest bytes is pending.

## Ordered follow-up mapping

All rows below are source-ready, uncommitted and inactive. Each component's
single complete import artifact is mapped in the next table.

| Request | Source / artifact | Built behavior |
| --- | --- | --- |
| 1. Refused hear | `painter/painter.js` | Motion and view hint refusals skip, report component-health, and permit first paint/reconciliation. Runtime activation remains separate. |
| 2. Untitled names | desktop `pages/menu.js` | Shared header and Comment label use readable first words; raw ID labels are skipped. Native route unchanged. |
| 3. Reply clearing | `board-components.bundle.js` | Uses the input commit-on-submit pattern: pending guard in persistent draft, clear and lock immediately on submit and repaint, retain refusal/new typing. |
| 4. Dialog titles | same board bundle | Report to leaders, Hide with a reason, Record a decision, Edit post. |
| 5. Done + Undo | `components/action-notice.js`; board/map bundles; `slots.js`; Work overview | Exact receipt recovery for moves, Hide/Save/Follow/Mute, claims and Mark done. Work Mark done changes the task lane and reuses exact-receipt Undo. Lenses author the Undo binding; help documents both contracts. |
| 6. Asks & offers | `asks.lens`, catalogue component, board bundle | Spaced badges, formatted initials, one helper heading, Reply and scoped thread. Offer uses shared `input commit=submit`; current mounted input clears. |
| 7. Composer/capacity | board bundle; `definitions.json`; `ui_install.py` | World kind scope excludes map kinds. Seats optional; places-left text only if `seats > 0`. Existing world default 500 retained. |
| 8. Actions/search | board bundle and `board.lens` | Shared token-based row button treatment, visible Upvote label, human dates, Search button and query reset on Back. |
| 9. Documents | `document-components.bundle.js`; `components/file.js` | Drop group with one native Choose files button; hidden picker. One-page reader says 1 page and omits pagination. |
| 10. Summarise | board bundle | Offline/refused status shows disabled action and reason. Empty/failed answer says not available; slow pending request says not available yet and keeps duplicate guard. |
| Own offer | `components/slots.js` | Take a place disabled with visible reason for the offer's owner. |

Capacity is optional to type, not a new unlimited-RSVP protocol. Clearing the
form field still permits the existing world kind default of 500 to apply.
No model/provider setting or admission word changed.

Before an eventual authorised copy, House reads the current target, preserves
its previous code/metadata/text and records each exact publication receipt.
Rollback restores those exact previous fields through the approved mechanism;
never replace unrelated subsequent changes or use unqualified Undo.
Review exact component bytes after copying, then activate and verify outcomes
through the normal House path once Alex's import hold is resolved.

One repository file supplies each component's complete `code` field:

| Components (live IDs read this turn where listed) | File relative to repository root |
| --- | --- |
| Button `dk228`, Input `dk229`, Choice `dk231`, Badge | `src/agora/components/catalogue.js` |
| Action notice (new reviewed component/card) | `src/agora/components/action-notice.js` |
| Calendar `dk247` | `src/agora/components/calendar.js` |
| Slots `dk352` | `src/agora/components/slots.js` |
| File reader `dk353` | `src/agora/components/file.js` |
| Board shell `dk355`, catch-up `dk358`, entry `dk359`, post `dk361`, thread `dk362`, composer `dk365` (other board components may use the same reviewed bundle) | `src/community/board/board-components.bundle.js` |
| Map shell `dk868`, Geo map `dk869`, Map inspector (panel/layers also use this bundle) | `src/agora/apps/map/map-components.bundle.js` |
| Document library/toolbar/upload/list/entry `dk1854`–`dk1858` | `src/community/board/document-components.bundle.js` |
| Work line `dk1486` | `src/agora/components/work-line.js` |
| Work overview `dk1485` | `src/agora/components/work-overview.js` |

The generated bundles already contain their CSS; map also includes its existing
engine/worker. `build_component_bundles.py --check` checks nine complete artifacts (six shared component files and three app bundles).
There is no publication-time concatenation.

Metadata and world text are necessary, not optional:

- New `action-notice` card, button/choice settings and parts are in
  `src/agora/painter/catalogue.py`. Merge these schema additions into
  existing cards; retain unrelated settings. No gesture needs a new grant.
- Board thread: `threadKey` and `replyKey`, defaults `thread`/`replyTo`.
  Composer: `kindScope`, default `board`. Defined in `ui_install.py`.
- Geo map and inspector: `routes` boolean default false. Standalone map lens
  explicitly sets it true because it has a planner. Defined in map `install.py`.
- Work overview slots include `notice`, as well as `rows`. Work line adds
  `done` part/gesture, with `on done do set $item lane=Done` in both Work
  arrangements. Publish these metadata and lens changes with the component.
  This uses existing set/undo rights; no task announcement/message is sent.
- Action notice adds `scopeKeys`, from `painter/catalogue.py`. The new shared
  helper `components/action-feedback.js` is a build input, not a separate
  component to import. Bundles already include it. Notices are component-local,
  synchronous and token/scope guarded; old JSON view notices are ignored.
- Document library adds `showHeading` (default true); embedded Documents suppresses its duplicate heading.
- Document upload parts now include `choose`; the drop surface is a group
  containing a native button. Use metadata from `documents_install.py`.
- Replace the authored lens text from `board.lens`, `asks.lens`, map `map.lens`,
  and Work `work.lens`/`task-work.lens`, after comparing existing live edits.
  Asks view defaults additionally include empty `asksThread`/`asksReplyTo`;
  preserve existing channel and other view defaults. Do not reset whole views.
- First give map kinds spot/map/map-layer/route/structure `compose_scope=map`
  as declared in map `install.py`. Then give board post kinds in
  `definitions.json` `compose_scope=board`. Legacy custom post kinds such as
  Lost pet with a fields declaration remain available. The map metadata is
  necessary for both composer and Search filtering; copying JS alone is insufficient.
  For event, remove `seats` from `required`, keep `start` and its existing seats
  default. Preserve neighbour-made fields/defaults. Custom post kinds intended
  for this composer need the matching scope too; map-only kinds do not.
- Guide texts: painter `ARRANGEMENT.md` into the existing painter guide text;
  board `UI-HANDLES.md` into the board handles guide text, preserving unrelated
  later edits. Metadata describes the new capabilities even before these guides.

Two source fixes have separate runtime activation boundaries:

- `src/agora/painter/painter.js`: refused-hear startup recovery.
  It enters newly built painter runtimes. **No patch to existing widget/HUD
  bytes is supplied or authorised by this handoff.** Existing standalone blank
  frames therefore are not claimed repaired live.
- `src/desktop/kernel-desktop/pages/menu.js`: general menu/Comment naming.
  Needs the normal host-page activation. No new Comment wiring or alternate
  interaction route exists.

Safe fixture sequence for the existing helper: preserve baseline, load the
matching component bytes and metadata plus authored lenses in an isolated
world, stub the model before opening any hidden page, run desktop and narrow
journeys and compare exact outcomes. No real posts/uploads, no visible window,
no live import workaround. Specifically test nested Asks reply on a narrow
screen, map Undo after an unrelated later act, and notice refusal after a
conflicting later edit. Recheck shared text selection → right-click Comment
with an untitled post and a document.

Sable's resident review and those actual browser outcomes remain pending.


## Browser-defect follow-up (5 November)

The helper's six passing journeys describe the preceding bytes, not this
follow-up. Latest checks: 20 feedback/race handler assertions, 43 round-2
component assertions, 5 painter startup assertions, 23 round-1 component
assertions, 17 isolated-world assertions including Work task Done/Undo and
confirmed fixture removal, nine checked artifacts. These are not browser
layout or fresh pointer evidence.

The map notice now anchors above the bottom connection pill, using the
`--map-notice-top` world style token (default 64px). Hidden desktop/narrow
overlap verification remains for the existing helper. Model-limit refusals
retain their real reason; all model tests were stubs.

Standalone blank cause, read from helper dk2712: the old Asks widget has
refused event hints and still embeds the old painter; the live Asks/Documents
lenses lack a component widget, so the plain-lens fallback mounts nothing.
The painter fix permits painting after refused hints in a newly built runtime.
It neither creates missing widgets nor replaces stored runtime bytes.
No widget or grant repair is authorized here.

Going still does not toggle off. The current board.rsvp contract accepts only
going/maybe; implementing withdrawal requires its own supported world contract.
Receipt-specific Undo still reverses the attendance action.
