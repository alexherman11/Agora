# JEFF's exact scoped patches — after source landing, no live apply by builder

All payload notes below are plain staged notes. None is tagged lens/style/verb.
Read current targets first, save complete originals and old pin props in
Restore: slim dock, then check ALL passages before the first write.
Use the Desk tool one command at a time; inspect every receipt. Stop on drift.

- Four new verbs on=f5189: title dock-pin (body a7328), dock-open (a7330),
  dock-place (a7332), dock-place-after (a7334). Tag only the newly created
  definitions verb. Check that no same-name verb already exists first.
- home-style a5206: append the exact body of a7326 immediately after the
  unique line `role appgrip : on spbg, spbg, height gap, pad gap x0`.
  No existing token or role is replaced, including tilefoot and music.
- home-dock a5564: replace its body only if it still equals a7336 (the complete
  old body read during this commission), using the complete body of a7324.
  If somebody changed it, reconcile scope first; do not overwrite.
- home-viewer a5486: replace this exact passage:

```
    title : text "$title"
      role heading
      clamp 2
      share 1
```

with:

```
    title : text "$title"
      role heading
      clamp 2
      share 1
      carry
      tip "$title" "Drag to the dock to pin this."
```

- home-thing a6784: replace this exact passage:

```
  name : text "$item"
    role hitname
    clamp 1
    share 1
```

with:

```
  name : text "$item"
    role hitname
    clamp 1
    share 1
    carry
    tip "$title" "Drag to the dock to pin this."
```

Existing pins stay. Optional colours (save old values first): a5567 tint=purple,
a5569 tint=amber, a5571 tint=blue, a5573 tint=green. Pin the REAL Waiting on you
panel through dock-pin a5668 f5565, then give that pin a distinct tint/glyph.
Calendar and Seabright are not seeded: this commission found no live app
definitions for them. Their real definitions can use the same protocol later.

Reverse in opposite order: swap each exact old/new passage; replace only
the appended style namespace with nothing, retaining its anchor; reverse
home-dock only if it still equals the staged new body. Restore recorded pin
props and undo a newly seeded pin event. Keep user-added pins. New verbs may
stay dormant; any untagging must target only the identities just created.

No home-tiling change, no arrangement reset, no viewer content or chat context
assignment. The a7045 external carry hook is a separate source dependency,
not a world replacement. Full safe copy recipe/checklist: a7338.
