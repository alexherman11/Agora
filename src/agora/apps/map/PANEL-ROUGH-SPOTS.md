# Nestable map handoff rough spots

Builder draft, 28 October 2026.

Read: the existing map exposes independent pieces, but its tool/selection/focus
values share the containing lens's view keys. Missing world-level handle:
**a component-local state namespace**. `map-panel` provides one internally,
reusing the existing pieces, without changing the painter or board arrangement.

Read: the Events layer reads `rows event`, while board events are
`kind=post post_kind=event`. Missing world-level handle: **placed board things**.
The new ordinary layer reads `board.feed`; map projection keeps `post_kind`
and `thread` so style selectors and pin navigation retain their meaning.

Read: board kinds individually declared their location fields, so ordinary
posts/asks/offers could not all name a map place. Missing shared field:
**optional place on a board post**. The board word now accepts it for every
kind; the UI installer extends existing declarations without replacing fields
or labels. Events keep `location` for calendar/meeting prose and `place` for
the map link.

Read: nested component code has no automatic watched-reading declaration.
The embedding snippet therefore needs its indented `watch reading` line,
and the board widget needs the map read grants through normal review.
The board lens and live grants were not changed by this worker.
