# Bring notes to front

Press an exposed part of an overlapping note to bring it above other notes.
Keyboard focus also raises a note. Recent stacking order is preserved until
the view is reopened. No geometry/content writes occur just to raise a note.

Implementation: one shared delegated pointerdown/focusin handler, eight lines
including its comment, in index.html. It assigns bounded z-index ranks above
the existing drag/resize layer, preserving relative order of the other notes.
It never reorders DOM nodes, prevents default editing, or changes selection.
Stacking remains independent of geometry refreshes; safe reload stays intact.

This is ephemeral interaction state, not a persisted layout setting. If the
user later asks for saved layering, introduce a schema-backed layer contract
and CAS persistence deliberately, rather than writing to core.appearance
with an unsupported field.

tests/stack_browser.py uses the retained shell in Chromium and the same
simulated parent bridge as the other suites. Run it with the entry path:
python tests/stack_browser.py index.html
It does not verify activation in the user's running host browser.
