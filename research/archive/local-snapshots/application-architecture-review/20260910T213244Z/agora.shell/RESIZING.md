# Note corner resizing

The retained agora.shell entry now has four subtle corner grips on the
free-position desk (>750px). Drag any corner; the opposite corner stays fixed.
Minimum size is 160 × 140 CSS pixels, maximum 100000 × 100000. Top/left
expansion stops at the desk origin for ordinary nonnegative-position notes.
Tab to a corner and use arrows to move it by 10px (Shift: 1px).
Escape, cancellation, capture loss, blur, hidden document, and viewport resize
discard the preview. A movement threshold avoids writes on a plain click.
Only the grips claim touch gestures; text editors retain selection/scrolling.
At narrow mobile widths, controls are hidden and the existing stacked layout
remains unchanged (saved desktop geometry is not changed).

Resizing shares header dragging's gesture lifecycle and serialized CAS writer,
rather than introducing a second persistence or reload mechanism.
Pointer release saves width/height and position atomically in core.appearance.
The original scene is preserved. Concurrent appearance changes are not rebased
or retried; refusal/staleness restores the latest confirmed geometry and shows
an error. Text baselines, editor nodes/selection and chat drafts are preserved.
Active resizing blocks reload preparation; pending geometry saves are flushed
by the existing safe-reload handshake.

## Verification
Run tests/drag_browser.py as documented in DRAGGING.md. It tests the exact
retained entry using Chromium and a simulated parent bridge, never live notes.
All existing drag tests and new resize tests passed in the designated Linux
guest: four corners, preview/one CAS request/reopen, opposite-corner anchoring,
size/edge bounds, keyboard/no-op, focus/selection/chat/drafts, cancellation,
remote geometry conflicts and refusal/stale projection, text-write serialization,
reload refusal/flush/thaw, touch events and narrow stacked layout.
The resized desktop layout was visually inspected in Chromium.
A regression found Escape was not delivered when the first interaction focused
no frame editor; pointer gestures now focus the frame window without replacing
the active editor or its selection. Regression tests passed with this fix.

Not verified here: installed host-browser activation, the live parent bridge's
durable save/reopen cycle, physical touch devices and other browsers.
