# Implementation validation — September 5, 2026

This records the approved foundation repairs, first personal lens, and documentation
revision. The earlier holistic assessment and `probe-results.json` remain the review
baseline. They describe the implementation before these changes.

## Delivered scope

- Cooperating threads and processes serialize world operations. Duplicate event
  application is idempotent, and current reads resume at a persisted byte cursor.
- Replay handles incomplete UTF-8 suffixes and reports unexplained complete
  corruption. New sealing appends record evidence of the interrupted suffix.
  Rebuild constructs a replacement before replacing an existing destination.
- Stale text flushes refuse without discarding the pending session. Exported
  anchors persist CRDT identity; unavailable live positions resolve historically.
- Import sources require explicit local authorization. Bounded preparation and
  full validation precede blob persistence; refusals leave no imported blobs.
- Scene cycles no longer recurse through labels. Full rendered projections obey
  the existing token estimator, long names retain labels, and scene bounds apply
  to both generic attachment and placement.
- Local browser sessions establish the actor and enforce host, origin, session,
  content type, and mutation-token checks. JEFF turns cannot overlap, and Stop
  prevents subsequent tool dispatch. World data is separate from system instructions.
- `core.lens` and `core.display` provide declarative list/text views, explicit
  sources, selected-object detail, pinned activation, retained drafts, and restore.
  Shell controls and JEFF use the same public registry and lens resolution.
- The feature horizon in Spec §22 replaces the post-M1 build order. It includes
  broader display authorship, everyday use, continuity, effects, rooms, devices,
  ownership, and distribution. Internal world-root authority remains an open choice.

## Automated verification

`uv run pytest`: **99 passed**, one upstream Starlette/AnyIO deprecation warning.
`uv run ruff check .`, `uv run ruff format --check .`, `node --check shell/app.js`,
and `git diff --check` passed after formatting.

The suite includes the original acceptance workflow and new invariants in
`tests/test_repairs.py` and `tests/test_lenses.py`. In particular:

- Four independent Python processes each append twelve entities to one temporary
  world; the materialized result equals rebuild. Separate tests cover threads,
  multiple store handles, and duplicate application.
- Current/reopened reads and an active current lens cannot decode old log records.
- Stale text, anchors after reopen and replacement, retained scene revisions,
  malformed committed payloads, torn UTF-8, failed rebuild, invalid coordinates,
  empty-world refusals, import bounds, and cyclic references are exercised.
- Pinned definitions survive later drafts and reopening. Restore preserves note
  identities/content. Fake JEFF creates and revises a lens through derived tools.
- Foreign-origin/host requests, actor claims, missing sessions, malformed requests,
  overlapping turns, and cancellation during a blocked provider call are exercised.

## Browser verification

Used an isolated temporary world containing synthetic Garden notes, Reading list,
and Weekend ideas. No personal world was used. At a 1280×720 browser viewport:

1. Selected notes and verified that full text and the explicit JEFF selection
   indicator changed together.
2. Found that replacing list rows lost keyboard focus. Fixed focus preservation
   and verified Down and Up navigation across completed refreshes.
3. Returned to the default desk and restored the previous pinned definition.
4. Inspected the stored definition, previewed its latest draft without changing
   world revision, and activated that exact version.
5. Created a fourth synthetic note with direct controls and saw it enter the live
   scene-bound list while JEFF remained idle.
6. Restarted the server with model credentials removed, reloaded the page, and
   read the saved note through the still-active lens.

No browser warning/error logs were reported in the final check. The temporary
browser tab and both test-server processes were closed afterward. This was a
desktop browser check, not a cross-browser or mobile accessibility certification.

## Live provider trials

`implementation-validation.json` retains both trials, their synthetic tool
transcripts, replies, model identifier, and resulting views. The configured
provider received synthetic notes and the ordinary tool/context vocabulary;
no personal world content or repository documents were included.

The first two-turn trial created and revised a working lens. On the revision,
JEFF first proposed an unsupported density, corrected its schema error, but then
mistakenly described `comfortable` as denser than `compact`. That outcome is
retained, not counted as semantic success.

The component descriptions now explicitly distinguish tight compact rows from
roomier comfortable rows. A second fresh two-turn trial used the same requests:

> Make my notes readable as a compact list, with a preview when I select one.

> Make the list denser and show who last edited each note. Revise the same lens.

The second trial previewed and activated both versions without tool refusals.
State checks verified that the view was active, the lens identity was unchanged,
the density remained compact, author metadata was visible, and original notes
were unchanged. JEFF correctly explained that compact was already the tightest
supported spacing.

Workflow adherence still varied: the first trial omitted a separate preview call
(activation validates internally), and the second omitted placing the lens object
on the desk. Its active definition remains referenced by `core.display`; placing
it is useful for later discovery. These are observations to retain in subsequent
usability evaluation, not grounds for claiming reliable autonomous behavior from
two small trials. No comparative model-advantage or latency/cost study was performed.

## Limits kept explicit

The first renderer changes the workspace; the right-hand conversation panel is
still shell code. General executable extensions, OS enforcement, multi-user grants,
external effects, collaboration, and device synchronization are not implemented.
Imports capture snapshots rather than writing back to source files. Stale text
refusal is not concurrent CRDT merging. A second failure during interrupted-tail
recovery can require investigation. Cancellation does not undo recorded changes
or guarantee cancellation of an in-flight provider request.

These tests establish the named cases on this checkout. They do not establish
production security, arbitrary power-loss recovery, distributed safety, or the
larger hypothesis that Agora improves a model's capabilities over conventional tools.
