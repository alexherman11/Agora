# Native note colors and note actions

Right-click the non-editor part of a note (header padding/icon, border/footer)
to open its color palette. Right-click title/body retains the browser's
copy/paste/spelling menu. The footer Note actions button also opens the palette
for keyboard/touch access. Arrow keys, Home/End navigate; Enter/Space select;
Escape/Tab dismiss and return focus. Outside click, blur, scroll or resize
dismiss. Menu placement is clamped to the viewport. It uses menuitemradio roles,
selection checks, names and swatches, not color-only controls.

Native facet: desk.note-style = {"color": "blue"}.
Allowed values: yellow (default), green, blue, pink, lavender, gray.
No facet means yellow. Light/dark tokens are defined by the view. Changing a
color does not modify core.appearance, core.title, or core.text. Agents can
change the same facet with world.transact using the current object revision;
no package edit is needed for a palette selection. Adding a new palette color
would require revising both schema and renderer.

Color writes reuse the geometry writer's serialized presentation slot, called
positionPromise for compatibility. It waits for in-flight text writes; text
writes wait for it. The menu-opening style baseline is checked against the
latest projection before native CAS. Refused/stale writes are not rebased or
retried; the last confirmed appearance and an error are shown. Dirty text
baselines remain separate. Colors render only from confirmed projections.

An open menu blocks safe-reload preparation. A selected color closes the menu,
then its pending write is flushed by the existing reload handshake. DOM nodes,
editor selection, stacking, chat and unsent drafts are not replaced.

Tests: tests/corner_color_browser.py, plus existing drag/snap/stack suites.
Run with the entry path using Playwright/Chromium as in DRAGGING.md.
Tests use a simulated parent bridge; live-host activation/persistence and
physical mobile/other-browser behavior need independent verification.
