# Execution receipt — 20 October 2026

Source/staged text only. No live migration, lens replacement, host restart,
remote fetch, local file selection or real Conversation check.

Ran:

- `test_viewer_tabs.py`: **10 tests, OK**, last printed 0.186s. Actual
  in-memory dispatch/repaint, staged routes, shelf/resume, synthetic draft and
  context unchanged, event undo, refusal/no-write, snapshot persistence, patch
  round-trip/drift checks.
- `node test_viewer.cjs`: **8 pass, 0 fail**, 24.6891ms. Actual modules with
  fake DOM/storage: tab reading, draft independence, persistence/corrupt input,
  read-only Agora-link hook, intentional HTTP external-open only. `node --test`
  could not spawn its isolated process (EPERM); direct Node runs the same tests
  in process.
- `test_navigation.py`: **10 tests, OK**, 0.005s.
- `test_scene.py`: ordinary run hit `PermissionError` in a tempfile-created
  fixture directory. Retried in a one-process test harness overriding only
  tempfile.mkdtemp to existing `agora_tmp.directory(prefix)`, using
  uuid/os.makedirs with inherited ACL under this worktree: **58 passed**.
  Production source/security settings were not changed for this harness.
- `test_reach.py`: ordinary run had four empty-file-result failures; same
  inherited-ACL temporary-directory harness: **all passed**. Its existing
  fixture uses tempfile.mkdtemp and failed to persist refusal rows.
- `git diff --check`: passed.
- Full `health.py frontier-try --json`: **176.3s, ok=false**. Snapshot
  **e14601**, 14593 events; **73 lenses compile, 0 unexpected refusals**.
  Python and JavaScript parse checks pass. New viewer-tabs room test passes.
  Temp ACL/write failures affect scene, agent-reach, captures, house-merge,
  landing queue/return/wait, lived, room-look, scripts-mirror, witnessed,
  store and visit fixtures. Also refusal-row fixture failures, textedit-test
  lock timeout, door timeout, browser paint failures. No claim of a clean
  full-health pass. The two newly required help entries (browse and remember)
  were then added to the live Help binder; this old supplied copy has not been
  refreshed or re-judged with them. House must judge the resulting live export.

Read:

- Live charter, commission/comments, builders' notebook, current home-viewer,
  view, open-found, unview, search/tiling and dock staged routes.
- Real dispatch, reducer, painter reuse, reader continuity and link modules.
- Live Handbook/Help sections updated by exact replacements: One language,
  The browser, lens help; new browse help. Rough spots note records the missing
  world words. They say source awaits landing; active chrome stays unchanged.
- Staged Study notes: “Viewer tabs — staged exact passages” and
  “Viewer tabs — source boundary and JEFF apply/reversal”. Read-back readable
  old/new passage body matches generated text exactly (9709 characters).
  This avoids the world's create-text conversion of JSON's literal backslash-n.
  Disk `patches.json` remains machine-readable; no world JSON reader is implied.

Blocked/not run:

- Guarded hidden-desktop `screen.py ... --visible --lens home-viewer
  --size 2560x1440 facts viewer 2 shot screen-tabs.png` availability check
  failed at sandbox_window.open_edge's first document.readyState
  Runtime.evaluate: **WinError 10054 / ConnectionClosedError**. No screenshot
  or facts, real keyboard/composer proof, viewport/overflow or reading-scroll
  acceptance. No fallback to Alex's screen or repeated browser attempt.
- World chrome/migration apply and browser-capable acceptance remain JEFF's
  next step. Existing browser navigation routes outside the scoped
  view/search/pins/open-with integration are not all audited or migrated.
- Web/device rendering, cross-world tabs and global visited-history log remain
  unavailable. Per-browser reading continuity is not cross-device state.

# Source repair after guarded review — 20 October

This section supersedes any deployment recommendation above. The guarded
review of the previous source found stale projection titles, search pollution
and accumulating closed notes. This repair is source-only, not a new browser
acceptance receipt.

RAN on this branch:

- `test_viewer_tabs.py`: 16 tests, 0.345s, OK. Actual in-memory commands and
  repaint cover refreshed labels and legacy placement, 25 close/init/reload/new
  cycles with unchanged node/subject counts, serialization, final blank tab,
  separate actors, forged ownership refusal without writes, explicit narrow
  search selectors and actual search-lens repaint, six-hunk reversal, and undo
  of a reused slot. Existing snapshot/history/draft/context cases still pass.
- `test_navigation.py`: 10 tests, 0.007s, OK.
- `node test_viewer.cjs`: 8 tests, 8 pass, 0 fail, 53.681ms. Fake DOM only.
  The initial `node --test` launcher failed at subprocess spawn EPERM; direct
  execution of the same test file avoids that extra subprocess.
- Direct `test_scene.py` stopped at `test_rooms_go_look_and_replay` with a
  system-temp PermissionError. Rerunning the unchanged suite using a test-only
  `tempfile.mkdtemp` shim to existing inherited-ACL `agora_tmp.directory`
  printed **58 passed**. The shim changes fixture allocation only, no source.

READ: live source/card/reviewer receipt and home-search at e15494; JEFF owns
the menu role/bounds and 20 direct-viewing route repairs. No live world lens,
viewer snapshot or chat was changed by this source repair.

NOT RUN on these repaired bytes: guarded browser gestures/keyboard/selection,
screenshots, narrow viewport/menu overflow, integrated tiling/dock, or full
health. The old guarded receipt belongs to the prior source. No new browser
startup attempt was made; this is an outstanding targeted review, not evidence
that the current environment cannot launch a browser.

`HANDOFF.md` describes owned-slot reuse, rollback and the exact supplemental
home-search patch in `search-exclusions.json`. Source hashes are recorded in
the commission receipt. No painter/partition file changed.
