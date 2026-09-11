# Note header dragging

The installed entry remains `index.html`, communicating with Agora through its
existing parent-frame bridge. No host checkout or bundled default shell is used.

## Interaction
- On the free-position desktop desk, drag the header padding or its existing
  note icon. Title and body inputs remain native text-editing/selection targets.
- Movement begins after 5 CSS pixels. Pointer capture keeps tracking outside
  the card. Escape, pointer cancellation/capture loss, window blur, hidden
  document, and resize cancel the uncommitted preview.
- Tab to the note icon: arrows move 10px; Shift + arrows move 1px.
- Touch dragging on the wide desk uses the icon only. Other header areas and
  editors keep native scrolling/selection. At widths <=750px, the original
  stacked mobile layout is unchanged and free-position dragging is disabled.
- Coordinates are desk-relative (including scroll offset), rounded and clamped
  to 0..100000. The desk extents grow with a preview.

## Persistence and concurrency
Only pointer-up after movement or an arrow-key move requests a native
`world.transact` patch of `core.appearance`, preserving scene/size and checking
the expected object revision. There is no DOM-only persistence or localStorage.
A separate latest projection and text baseline protect in-progress text edits.
Position writes serialize with existing text writes; a newer appearance cannot
be silently adopted as the baseline for an old gesture. Refused/stale writes
are not retried: the latest available confirmed position is displayed with a
visible error. A failed follow-up read retains the last confirmed projection.
A transport timeout may have committed remotely; it is never called a success
without confirmation.

Refreshes do not replace nodes or snap an active preview. Older object
projections are ignored. The existing safe-reload prepare/ready/cancel protocol
is retained: active gestures reject reload preparation; pending moves and text/
chat drafts are flushed before ready; failures/deadlines preserve and thaw the
old view. No new host-level reload mechanism is introduced.

## Regression tests
`tests/drag_browser.py` loads the exact entry in Chromium with a simulated
parent-frame bridge, isolated test objects, and real browser pointer events.
It NEVER connects to or mutates a live Agora world.

After exporting the retained package files into a Linux test directory:
```sh
python3 -m venv .venv
.venv/bin/pip install playwright
.venv/bin/playwright install --with-deps chromium
.venv/bin/python tests/drag_browser.py index.html
```

Verified in the designated Linux guest: preview/one-CAS-write, reopen
persistence, title selection/editing, focused editor selection and chat/draft
retention, text/move serialization, concurrent appearance and text conflicts,
refusal and stale projection handling, pointer cancellation/capture loss,
scroll coordinates, keyboard movement, wide-desk touch pointer movement,
mobile stacked-layout behavior, and reload ready/refusal/deadline/thaw.
Desktop layout was visually inspected in guest Chromium.

These tests are not evidence of live-host browser end-to-end behavior.
Independent verification remains needed for the installed running browser's
bridge/reload activation, actual durable note move/reopen, and physical mobile
devices/other browsers. Browser package.build only validates entry/manifest.
