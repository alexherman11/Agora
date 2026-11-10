# Seabright map panel

Builder handoff for the board/calendar worker. The map engine, map lens and existing
search/inspector/layers components remain the same design. `map-panel` composes
those pieces in a bounded container, with a private state prefix per part path.

After installing the map's component cards/layers, the board component line is:

```
  map : map-panel, map Seabright, board yes, height 520px
    watch reading:"map.layers Seabright"
```

Place this under `root : board-shell`, alongside `centre`, not inside the thread.
The existing board shell places extras in the feed column. The panel supplies its
own Map entry and expands in that column, in the same window. The indented watch
is needed for fresh pins when the map reading changes without other board changes.
The board lens has deliberately not been edited here.

The containing widget needs `map.layers map.tile map.find map.where map.place`
read grants (in addition to its existing `rows look board.*`). Its installer must
request those through the normal widget review process. No live grants were changed.
Opening a map or selecting a pin performs no world write. Layer visibility and look
controls in the panel are local to that panel/window, not global preferences.
Optional `on put`, `on move`, `on edit`, etc. lines enable editing using the parent
widget's ordinary guarded grants. The Add control appears only with `on put`.
The panel omits the route tool; the full standalone map lens retains its planner.

For a standalone panel use `root : map-panel, map Seabright, height 100vh`.
Without `board yes` it starts expanded and pins open the existing map inspector.
An optional `on open do ... $thing` overrides post navigation outside the board.
With `board yes`, post pins select `thread`/`replyTo` in the containing board;
reply pins select their owning thread. Other things open in the map inspector.

## Places and layers

**Events should use `place` for the map link**, e.g. a spot/structure id, a named
place, or `36.9672,-122.0088`. Keep `location` as the human meeting-place text
used by the date tile and calendar export. Existing `at` links and coordinates
still work. New board posts of every kind accept optional `place`; rerunning
the board UI installer adds that optional composer field, preserving existing
kind fields/types/labels. No place is required.

The new Board layer reads `board.feed` under the viewer's rights, including
events/asks/offers stored as `kind=post post_kind=...`, and respecting board
hide/mute marks. Existing Events/Spots/Places/Routes layers are preserved.
Only placed visible rows produce pins; place references are resolved through
the same viewer's reads. Public/own outside-geocoding rules remain in force.

Examples of reusable styling handles:

```
make kind=part-style lens=seabright-board target=map-panel.pin[post_kind=ask] color=blue
make kind=part-style lens=seabright-board target=map-panel.pin[layer=board] color=green
make kind=part-style lens=seabright-board target=map-panel.layer[layer=board] background=paper
```

The original `geo-map.pin` and `map-layers.layer` handles work in manually
arranged maps. Shared layer things still supply `look` and `color`. Pin buttons
support keyboard activation; linked places are not draggable away from their link.

## Recovery

Read: previous worktree `kernel-dk1536-072daf1c70` had no tracked diff or untracked
files and the same HEAD as this worker. There were no saved changes to transfer.
No new map design was substituted.
