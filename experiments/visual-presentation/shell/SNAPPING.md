# Note adjacency snapping

On the wide/free-position desk, header pointer dragging snaps a note alongside
another when its proposed edge is within 12 CSS pixels of a 12px gap.
All four sides are supported. Nearby leading/trailing edges align within
the same 12px threshold; otherwise partial side overlap is enough.
The closest valid candidate wins; ties follow stable note iteration order.
Distant notes do not attract one another. Snaps outside desk position bounds
are rejected. A dashed outline marks an active snapped preview.

Move beyond the threshold to pull away, or hold Alt to bypass snapping.
Keyboard movement and corner resizing remain precise and unsnapped.
The narrow (<=750px) stacked mobile desk is unchanged.

Snapping is a one-time positioning aid, NOT a maintained relationship:
neighbors are never moved or written, and later moving/resizing either note
does not reposition the other. Only a completed drag writes the resulting
native core.appearance position through the existing serialized CAS writer.
Cancellation, refusal, stale writes, editing/drafts and safe reload keep the
existing drag behavior. Neighbor geometry is read from the visible desk during
preview and release; it is not transactionally locked to the dragged note.

## Tests
Run both tests with Playwright/Chromium (see DRAGGING.md setup):
  python tests/snap_browser.py index.html
  python tests/drag_browser.py index.html

Tests use a simulated parent bridge and no live world mutations. Snap tests
cover all sides, 12px gap, preview/one-CAS-write/reopen, unchanged neighbors,
alignment/unequal dimensions/partial overlap/proximity/bounds, pull-away/Alt,
cancellation/refusal/concurrent source writes, drafts/focus, and unchanged
resize, keyboard and mobile behavior. The existing suite covers drag/resize
editing, cancellation, conflicts and safe-reload regression.

Live-host activation and native bridge save/reopen, physical touch devices and
other browsers require independent verification.

## Two-sided corners
Compatible horizontal and vertical adjacency constraints now combine, with a
12px gap to both neighbors. Two-side candidates take priority over single-side
alignment, then nearest pointer distance breaks ties. Both orthogonal overlaps
are checked at the final coordinates; non-overlapping distant edges cannot
form a corner. Alt bypass and release/CAS persistence are unchanged.
