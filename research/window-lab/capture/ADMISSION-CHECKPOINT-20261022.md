# Capture admission checkpoint — staged, not accepted or live

Lead decision: Sable c11067. This supersedes the snapshot-only fix in the
historical TAKEOVER document; the historical failing probe is retained.

Native `append ... captures=current context_from=<draft>
capture_generation=<observed generation>` checks current draft ownership,
generation and pending reservations under ordinary command admission, resolves
current IDs, and appends/consumes/advances the generation together. Failed append,
detach or hook restores the command state. Existing explicit-ID sends retain
their prior semantics. This is not a new authorization mechanism.

The existing host producer binds a reservation to one draft generation and uses
ordinary `prop` with explicit generation/context/pending comparisons. Completion
replaces its own token; cancellation, changed generation and unconfirmed admission
cannot retarget it. Processing failure leaves pending visible rather than silently
releasing a waiting Send. The native test bridge executes the real producer and
real engine with synthetic captures.

The painter keeps its original action and edit fence, observes current wait
status only, and has a six-second deadline even if refresh stalls. Timeout/failure
cleans timers and leaves words. A post-submission exception reports an unknown
outcome rather than claiming nothing was sent. Wait-only dependencies remain
cache dependencies but do not fence their own completion. Existing action-field
fencing is not expanded: a synthetic audience update demonstrates the original
audience remains in the Send, not that every field substitution is fenced.

`wait_patches.py` emits exact narrow OLD/NEW passages and inverses against public
Desk lens text read this round (fixture world-bases-20261022.json). Each lens has
two normal capture-bearing actions opted into native admission; other reply and
comment routes stay byte-for-byte unchanged. No whole lens replacement is staged.

## Ran

- `run_admission_tests.py`: **57 passed in 2.58s**. Actual native engine + synthetic
  capture service; native Handler with isolated Session/save fixture. Includes
  pending refusal, completion, two out-of-order reservations, cancellation,
  generation mismatch, CAS mismatch, current removal, empty sends, wrong actor,
  append/detach/hook rollback, journal replay without private capture access,
  original compiled action/fence and duplicate gesture.
- `test_wait_deadline.js`: **5 cases passed**, executing the actual painter helper
  with a deterministic fake clock. Immediate, completion, stalled refresh deadline,
  rejected refresh, and deadline before polling; no late continuation/timers.
- `test_pending_offline.py`: **11 tests OK** (fake Desk helper tests, not CAS proof).
- targeted scene suite `-k waits`: **1 passed, 58 deselected in 0.76s**.
- `test_world_hunks.py`: both lenses parse with fixture role names; two opt-ins
  each, all other routes unchanged, exact inverse. Syntax proof only, not styles.

Intermediate failing test iterations are not passes: initial system-temp fixture
failed; a missing scene.emit fixture caused two failures; then an assumption that
every action-field substitution was fenced caused one failure. Fixed the fixture
and narrowed that assertion to original-action preservation. No production fence
was weakened to satisfy it. Inaccessible pytest cache scratch is retained.

## Still unverified / needed

- Full integration/health on current main: supported house preparation next,
  preserving the staged source before merge; hot files include lens.js,
  scene.py/lens_ir.py, desk_knife.py and message_context.py.
- No browser launched, no screenshots/caret/chip proof. The retained old browser
  recipe stays disabled; use only the admitted shared Job-owned Guard lane.
- Physical release and Send are separate clients of the house. Reservation
  admission is serialized with Send, but a Send accepted before registration
  cannot be ordered retroactively. Registration is synchronous before expensive
  processing, not a proven immediate on-screen marker. No cross-client ordering
  claim or latency measurement is made.
- The four normal capture-bearing Send actions are covered. Original-place
  document comments/replies do not currently carry captures; their behavior is
  preserved, not certified as satisfying the wider attachment contract.
- No Alex screen, real capture content/store, Conversation, host restart or live
  lens apply was used. The earlier real-message timings were read from c10503,
  not measured again.

No ready/landing request. Preparation is not acceptance.
