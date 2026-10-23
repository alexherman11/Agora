# Capture / explicit Comment integration — 22 October

Scope: Sable c12811. Source-only ordinary judging; no world activation.

Read: house preservation HEAD a72cb822c55e10a12acf771a3f8bdc44b048fc2e,
against main c60a1423d252e94fdd26a2ea7a2d021b2e948d0a.
The house preservation commit contains one literal conflict block in lens.js,
composer Send, originally around lines 878–928. No git merge was replayed.

Resolved that single block by composing both behaviors:

- Freeze the original edit origin, plain/quoted authored action, quote and words
  at the press. Refresh only attachment waiting status, never audience/topic,
  reply, capture generation or edit fence.
- Retain bounded attachment waiting, duplicate-press exclusion, changed-words
  refusal, unknown-delivery warning and finally cleanup across every exit.
- After waiting, revalidate Comment's source/context snapshot. Preserve its
  single-pass token substitution and source_quote envelope on the same send.
- Clear words/quote only on a successful receipt and cleared Viewer draft.
  Stale source, timeout and uncertain delivery retain them.

Ran on the resolved combined source:

| Check | Result |
| --- | --- |
| run_admission_tests.py | 58 passed in 12.00s |
| test_pending_offline.py | 11 tests, OK |
| test_wait_deadline.js | 5 fake-clock cases passed |
| selection-menu/test_send_receipts.cjs | 2 actual sender/Viewer mock cases passed |
| selection-menu/test_composer_quote.cjs | 8 composer + 2 compiled-pair + 4 new combined cases passed |
| test_selection_snapshot.py | 5 passed, 14 subtests passed in 0.46s |
| test_world_hunks.py | both stored lens fixtures parse; two opt-ins each; exact inverses |
| node --check lens.js; git diff --check | exit 0 |

The four new combined regressions exercise actual composer code with fake clock,
DOM and transport: pending quoted Send plus duplicate press and replacement
paint/action; source becoming stale while waiting; deadline with quote retained;
and words changed while waiting. The fixture now supplies the painter's kept
map and deterministic timers. These mocks do not prove native ordering or pixels.

Exact changed bytes this round:

- notation/desk-shell/lens.js:
  `2a25528cc527984e757edbb44a3462a67a0c0168cddf61ecb2ecf8ab5f250e38`
- window-lab/selection-menu/test_composer_quote.cjs:
  `ae500fdfb6a202d033188f7800d07c7379b08ccd32c7355a576b611f26a63788`

Paths above are under research/text-desk-lab and research respectively:
the full painter path is research/text-desk-lab/notation/desk-shell/lens.js.
The full test path is research/window-lab/selection-menu/test_composer_quote.cjs.
This report adds one evidence path. The source increment versus captured main
has the prior 27 capture paths plus the shared composer fixture and this report:
29 tracked candidate paths. Session copies and scratch are excluded.
Historical manifests remain historical; they do not hash this new resolution.

Limits preserved: no browser/Guard/native capture attempt, live message,
Conversation test, capture-folder access, process or restart action. No broad
health rerun; historical full-scene result remains 2 failed / 57 passed due to
system-temp PermissionErrors, not a pass or certified baseline. Four world
hunks remain staged/unapplied. Hidden-copy 1280/2560 pending-chip/joined-send
shots, caret continuity and physical drag-release registration ordering remain
owed. Stored lens inverse tests do not certify current live lens applicability.

Rollback: source revert through ordinary house lifecycle; JEFF owns exact
staged world inverses. No world rollback is needed for this round.
