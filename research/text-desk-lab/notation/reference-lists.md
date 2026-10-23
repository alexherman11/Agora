# Ordered reference lists and staged Viewer pins (a11866)

This is source plus **staged** world policy. Nothing here changes the live Viewer.
Read on 22 October: Home Board is `home-board` (a5548), not `task-board` or
`board-goals`. Rowan already put it first in Alex's existing Viewer pins:
`a5548,f155,a5202,a5080`. Alex subsequently changed `viewing` himself; do not
restore an earlier selection, Back target, search, renderer or draft.

## The missing generic capability

Existing `join` builds text from a selection. An explicit ordered identity list
combined with a negative identity is not an ordered filtered-list source.
There is no existing add/remove/move expression in the closed `expr.FUNCS`.

A desk author can now compute a persistent ordered reference-list edit, then
use the ordinary fenced `prop` verb to store it:

```text
refs-add(list, item)
refs-remove(list, item)
refs-before(list, item, before)
```

Add appends; remove removes one exact identity; before moves an existing member
before an existing anchor (empty text means the end). Commas and whitespace
separate explicit a/f/s identities. Changed lists are newline-separated, which
the existing repeat already accepts. Exact semantic no-ops return the original
spelling. Invalid/duplicate input, missing move members/anchors, selections,
names/URLs, non-text arguments and oversized input/output refuse as an expression
`none` with its reason. Bounds: 256 identities, 16384 UTF-8 bytes.

These functions are pure: no lookup, permission, event, navigation or new store.
They do not canonicalize subject/appearance aliases. World policy must supply
the same admitted appearance identity used by the UI; it must not treat an
arbitrary subject alias as a distinct shortcut. Existing unavailable references
are retained in order, not silently discarded.

## Rowan's staged world policy and exact inverse

`viewer_pin_stage.py` exports three verb texts and two checked Viewer hunks.
Importing it applies nothing. Create verb notes in the existing lens/verb scope
with titles `viewer-pin`, `viewer-unpin`, `viewer-pin-before`, tags=verb and
on=house. Their exact text is `VERBS[title]`; do not invent source verbs.
Arguments are Viewer appearance, lens appearance, and (for reorder) existing
anchor appearance. The actor and role must match the caller's own home-view.
Pin accepts the same kind/tag test as the existing Viewer's `islens`; that
existing `has` test is substring-based, not a newly strengthened tag predicate.
Other roles/owners/non-lenses are skipped with the ordinary guard receipt,
not reported as a successful pin. New source grants no additional write authority.

Each step writes only `pins`. Guards suppress duplicate additions and absent
removals, so those make no event. Ordinary stale writes refuse. The Unpin
menu reads `v.pins` explicitly, so compiled action fences include that prop.

`patch(live_viewer_text)` checks exact old anchors and returns the additive
replacement. Apply only after source landing, live re-read and lead review.
It adds:

- **Pin this lens**, only on an unpinned lens's existing Viewer header;
- **Unpin** on each shortcut's contextual menu.

Existing order, names, active role and one-click selection stay world-owned.
No change to the existing selection action is proposed. Structural pins remain
in the existing `pins` prop; tab/history/window-value migration is separate.
Reorder is exposed to world authors through the verb, not a new drag controller.

Inverse: `patch(applied_text, reverse=True)` checks/removes exactly those two
additions. Retire the three new verb notes only after checking for consumers.
Each actual unpin is a normal logged prop edit with an ordinary conflict-checked
undo receipt. Re-pin restores at the end; `viewer-pin-before` restores a recorded
position. A lead may restore the old pins value after re-reading it and checking
there were no intervening pin edits. Never undo Alex's intervening navigation.

## Ran and limits

```text
python research/text-desk-lab/notation/test_reference_lists.py
python -m pytest -p no:cacheprovider research/text-desk-lab/notation/test_scene.py::test_time_and_date_interpretations research/text-desk-lab/notation/test_scene.py::test_day_or_time research/text-desk-lab/notation/test_scene.py::test_words_of -q
```

12 isolated tests pass: pure list edits/types/bounds, actual world verb dispatch,
owner/role/target guards, duplicate and absent-remove event delta 0, stale write
refusal, preservation of unrelated refs/navigation/stand-in draft props, compiled
order/active state/menu fences, patch/inverse, last-pin removal and ordinary undo
restoring the exact order. Three existing
expression tests pass. The tiny compiler fixture supplies only style roles and
inert content; this is not the full live Viewer or painted acceptance.

Initial test failures (fixture actor argument collision, quoted variable instead
of expression binding, unsupported text concatenation for a tag guard, and wrong
scene traversal keys) were corrected. The current policy deliberately reuses the
existing Viewer's lens predicate. No failure is being relabelled as browser proof.

No live edits, messages, source/host activation, sessions access, browser launch,
clipboard, OS focus or restarts. Real unsent composer/caret preservation and
1280/2560 visual layout are unverified. Guarded copy acceptance must exercise
Home Board and another lens, add/no-op/unpin/undo/reorder, active selection,
reload persistence, stale refusal and unchanged unsent composer state.
