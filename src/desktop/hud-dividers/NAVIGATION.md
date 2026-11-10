# Expanded navigation — staged, not live

Supersedes the initial divider-only handoff in HANDOFF.md. Implementation is
continuing on codex-builder-1 after takeover from codex-builder-2. JEFF asked
for source/logic completion here, with guarded browser review separate.

The world half is **not applied**. No host was restarted/stopped and no input
or test window reached Alex's desktop. No Conversation tests were sent.

## Representation and behavior

Current checkpoint: EVIDENCE.md round 5 records the new narrow grip/control
repair and its two changed hashes. Real review closed focus-frame drift using
JEFF's world border fix; containment was not its cure. Non-interactive summary
descendants now share the authored grip's initial default guard. Action-control
drags suppress activation while stationary clicks remain actions; editors stay
native. This new behavior has stand-in evidence only and needs targeted guarded
browser recheck. JEFF owns the separate world-only glance border correction;
neither this recipe nor source overlay applies it. Small-screen composer/title
access, reported >300ms completion and real workspace coverage remain limited.

The layout's `tree` prop is a versioned JSON slicing tree. Existing panel and
column memberships stay put. Panel notes remain the source for app lenses,
names, shelf, pin and filled music lens. The tree controls only geometry,
tab selection and natural sizing. This avoids recursive lens execution and
makes each manipulation one ordinary, fenced, atomic prop change.

```json
{"v":1,"root":{"axis":"y","kids":[
  {"axis":"x","kids":[{"id":{"$ref":"<music appearance>"}},{"id":{"$ref":"<viewer appearance>"}}],"weights":[1,1]},
  {"id":{"$ref":"<chat appearance>"}}
],"weights":[1,1]}}
```

Splits have axis `x` or `y`, kids, positive weights. Tabs have axis `tabs`,
kids and `active` (a typed `{"$ref":"identity"}` reference). A leaf has typed `id` and optional
`size:"content"`; omitted size stretches. The renderer uses identities only
to join panel scenes; it draws their names. Every direct child emits
`paint.partition_item`, including a passive/guarded one.

The generic lens words are:

```
partition tree min 240 140 gap 16 focus full
companion ($pin or "") = "yes"
sizing ($sizing or "")
chrome ($chrome or "")
```

`partition` needs a world thing behind its frame. It reads the tree and
optional focus props, including missing props, into the gesture fence and
repeat dependency fingerprint. `companion` is an expression on a child.
The generated arrange act writes the tree and focus in one `do prop`.
Its fence also carries the exact member selection and the appearance/subject
revisions of direct panels, including guarded shelves. Panel policy changes
conservatively refuse a stale gesture; changes inside app content do not.
These extra reads refresh after scene reuse.
The model accepts at most 32 nesting levels/256 children per node; malformed
or duplicate branches recover by current membership, without executing data.

Global left/right/top/bottom targets occupy 40 CSS pixels at the outer edge
(less in tiny viewports). They wrap the whole remaining tree. Bottom therefore
means a full-width bottom region. Local edges split that leaf; centre makes
tabs. The model first removes the moving leaf and collapses single-child
splits. The same projected model and geometric function produce the preview
and post-drop rectangles, including gaps. Equal weights produce halves,
clamped to usable minima; physically impossible minima scale together.

A title click remains a click until movement reaches 5px. Header controls and
editable fields decline carry. Then a whole-panel copy follows the pointer;
embedded apps/media are omitted from the copy. The actual source stays in
place and dims. There is no easing or decorative animation. Pointer release
saves the exact last preview plan; pointercancel, Escape, blur or viewport
resize discard it. A title also supports Space, arrow to a global edge, Enter.

On threshold pickup the adapter disables body text selection and clears page
ranges, preventing Chromium's native text drag from swallowing the next carry.
Release/cancel restores the prior policy; stationary/control clicks and the
composer's textarea selection are left alone. On committed drop/resize release,
old generated tools are removed until the authoritative answer repaints them;
they cannot intercept presses at obsolete coordinates. The optimistic panel
geometry remains visible, with new writes excluded while pending.
See EVIDENCE.md's browser defect repair checkpoint for exact source/test hashes
and the required no-workaround guarded recheck of a7466's two failures.
Busy non-control title presses cancel the pointer default even though they cannot
start another tree write; this prevents a declined gesture selecting text.
App controls and unrelated selection ranges keep their native behavior.
The corrected copy step distinguishes all four edge coordinates and requires a
persisted tree change; restore awaits actual answer completion and rereads state.
EVIDENCE.md's Round 2 follow-up supersedes its earlier repair hashes and retains
the unresolved small-viewport focus-drop discrepancy for guarded diagnosis.

Round 3 candidate: partition DOM creation and sync establish `contain: size layout`
so child focus/rail contents cannot alter the ancestor frame's intrinsic size or
baseline. This addresses the measured h380/h383 frame change; CSS/browser proof
is still required at both sizes. The acceptance tolerance stays <=1 CSS px.
The copy step now uses an actual owned-grip hit, chooses a movable shared
separator/direction, refreshes the restore fence with `look`, and retains primary
failures if cleanup also fails. Current hashes/limits are in EVIDENCE.md.

Every split has a 12px invisible separator, the appropriate cursor and an
accessible separator role. Pointer or arrow previews alter neighbouring
weights; release/Enter persists; Escape cancels. Other sibling geometry stays
fixed. Viewport bounds are the partition frame, below the top row/above the
dock. It never grows the page. The painter holds repaint through an active
gesture and its answer; ordinary Viewer continuity retains draft DOM/caret.

Fit content / Fill allocated space toggles the leaf policy. Natural size is
measured on existing content with temporary synchronous styles, restored before
a frame; no cloned embedded app is loaded for measurement. It is bounded by
its allocated region. Tabs show one selected child and retain all leaves.
This intentionally allows free space within a content-sized cell; stretch
and explicit full remain available.
An intentional edge drop fills its split preview; a shared divider resize
supersedes adjacent direct leaves' natural preference with explicit stretch.
Content leaves also have direct right/bottom edge handles: these persist a
bounded `extent:[width,height]` without requiring header tools. Fit resets
that manual extent. Thus a bare app can remain compact and still resize.

Per-child sizing and chrome are expressions read through the usual dependency
tracking. A content preference supplies natural sizing unless the saved leaf
has an explicit content/stretch policy. Chrome "none" hides generated sizing
tools; the latest world lens keeps its pane.bare/appgrip treatment, with a quiet
carry region separate from playback/heart/input controls. No app-specific source
branch exists. Bare panels still use shared dividers and whole-panel carry.

Focus is an independent world prop. Double-click fills/restores through the
existing header acts. Pinned companions/viewer remain beside focus; other
names form a rail. `focus_weights` arrays of typed panel/member references
persists focused divider changes without destroying normal geometry. A drop
exits focus into the planned ordinary tree. Shelves are guarded children,
not removed members, so restoration retains their saved position; actual
removed members are pruned, newly created panels append. Closing still uses
the existing close-panel verb on the old membership.

## World staging for JEFF

Do not apply the original `stage.py`: it is the superseded divider foundation.

`navigation_stage.py` prepares four exact, checked hunks from a fresh
home-tiling text: normal/filled area becomes one partition; retired
column/rail/full definitions become one unified panel; help tip changes; a
historical-comment banner marks the superseded column-only behavior.
It copies current header controls and the current two body passages, including
`$p.filled` for music and `scroll scroll`. It does not edit home-style,
tilefoot, other lenses, panel props, memberships or Alex's arrangement.
`home-tiling.current` records JEFF's newer bare/appgrip treatment; bundle.py and
the staging CLI use it. `home-tiling.before` retains the original checkpoint.
Neither is a fresh apply input.

Before applying after landing:

1. Reread the live lens and every current column/panel. Save the old lens and
   old `tree`/`full` props in JEFF's restore note.
2. Build a fresh manifest in current order, including shelved panels:
   `[{"span":1,"panels":[{"id":"…","height_share":1},…]},…]`.
   `migration(manifest)` returns a root row of column splits, retaining order,
   span and height weights. Do not reuse a manifest from this work session.
   If a tree already exists, preserve it; this is a one-time migration.
3. Save the old `copy_json` prop too; add `tree` to its comma-separated
   declaration without overwriting other declared props. New trees use typed
   references. Check every old passage exactly once. Write the new tree first, then each
   checked lens hunk separately. Do not run a multi-line apply past a refusal.
4. Apply `docs_stage.py`'s Help and Handbook hunks after source landing.
   Reread/check their anchors first. They deliberately remain staged until then.
5. Restore: put back the saved old lens and tree/full/copy_json props; no panel moves or
   cleanup is needed because membership never changed.

The original divider primitive remains general-purpose source vocabulary but
is not used by the new tree lens. Its tests remain as regression coverage.

JEFF approved the necessary copy extension in c7177. `copy_json=tree` opts into
version-1 JSON references: only exact `{"$ref":"identity"}` objects are remapped.
Plain strings, object keys and external references stay unchanged. Malformed
JSON, duplicate keys, unsupported versions or malformed typed references refuse
before any creation event. No arbitrary recursive string/key rewriting exists.
`partition.js` converts typed persisted references to internal leaf identities
for geometry; writes always use typed references, including tab selection and
focus weights. Native full/pin/shelf/music props keep their existing behavior.

## Acceptance gate

### Combined dock integration checkpoint, 20 October

The five-anchor `partition_hook.py` handoff from landed dock `16ac2bf` is
integrated, with an exact-contract test. `carry-targets.js` loads before both
carry adapters. This older branch includes the landed dock's exact source and
core dependency hunks (cross-lens drops, host menus, identity fields,
tree-activate and literal-dollar handling); no main merge or live apply occurred.
The partition source, compiler, typed-copy and app chrome changes are preserved.

After the 5px threshold the whole-panel carry creates a CarryTargets session,
excluding its partition's internal receivers. An external receiver takes priority
over the split planner and hides its preview. Returning to the partition resumes
split placement. Release sends either the dock act with both pickup fences or the
saved tree plan, never both. Cancellation clears both previews without a command.
Late receivers are not admitted, and pending external answers exclude another
gesture. Refusal never falls through to a split.

`test_partition_ui.js` uses the real CarryTargets module against DOM stand-ins;
it does not certify actual hit testing, geometry or draft continuity in Chromium.
The acceptance reviewer already reported hidden Edge's DevTools connection reset
before page-ready (WinError 10054); no new browser attempt was made here.

Ran logic tests are listed on the card; none certify actual Chromium or
WebView2 geometry/input. The earlier copied-world browser check could not
reach `/json/version` within 20s. No screenshot or real painter facts exist.
Ready/live acceptance remains gated on a browser-capable review.

### Copy-only run recipe for the outside-Codex reviewer

Run from this worktree with the pinned interpreter, after receiving this
preserved source (no landing/restart is needed for the copy):

```
C:/Projects/Agora4/.venv/Scripts/python.exe src/desktop/hud-dividers/review_copy.py --world frontier-try
C:/Projects/Agora4/.venv/Scripts/python.exe src/desktop/hud-dividers/review_copy.py --world frontier-try --small
```

Run each separately. This entry point uses hud_playtest's disposable Copy and
Window/Guard; it has no live-apply/report option and never starts hud.py.
Before opening the hidden Edge desktop it reads the **copy's** public snapshot,
preflights both the navigation and dock halves before any write, builds the migration from current
column order/weights including shelves, preserves any existing tree and other
copy_json declarations, then applies one command at a time to the copy.
It stages the four dock verbs and checked dock/style/viewer/name hunks, skipping
exact already-applied text/verbs without duplication. A moved/partly-applied
passage or newer/ambiguous verb refuses instead of overwriting newer work.
Any ambiguity/refusal stops. No session files are opened by this staging code.
The runner's existing copy mechanism alone loads/cleans its temporary world.

It runs `open` and `partition_navigation`, takes shots, prints the event and
guard verdict, and writes report.md/json beneath the existing
src/desktop/demos/hud-playtest timestamp directory. `finally` closes
only its own sandbox window/door and disposable world. It sends no Conversation
line. Small requests 1280x800; the normal runner requests 2560x1440 at native
150%. Record actual innerWidth/innerHeight/devicePixelRatio and painted bounds:
window-size requests are not proof of CSS viewport dimensions.

Ran here: eight in-memory recipe tests prove current-lens checked replacement,
shelved/natural-sized membership preservation, existing tree/declaration
preservation, combined staging, already-applied dock preservation, newer/duplicate
verb refusal and late dock-preflight failure with zero writes. The guarded runner itself
has not run here. Its step covers stationary click, four global edge spans and
one persisted divider only. The reviewer must also perform the remaining
journeys below on that guarded copy; a step pass alone is insufficient.

Use a guarded copy with fresh staged world data, this source and no host
shortcuts, requesting 2560×1440 at native 150%, then 1280×800; record actual CSS
viewport/DPR rather than assuming a request produces those CSS dimensions:

- Read initial world tree/props and capture screenshot/facts; confirm current
  Music/Board/Viewer/Chat arrangement and latest 4px tilefoot/music scrolling.
- Title click and clicks on pin, shelf, close, restore, app controls and text
  neither snap nor resize. Move 4px then release: no tree event. Move >5px:
  whole panel copy, no grip-only ghost or decorative animation.
- Drag to all four **desk** edges, especially bottom: preview spans the
  appropriate full axis. Drop and compare leaf bounds within 1 CSS pixel,
  allowing only declared gaps/minimum clamps. Repeat from different columns,
  a tab and focused mode; last-panel/own-target moves are harmless.
- Four local edges and centre tabs; select each tab; Fit content / stretch;
  explicit full/restore, pin/viewer companion, shelf/reopen and close/reopen.
- Every shared horizontal and vertical divider both directions to minima;
  no unexplained foot gap, wrap, page overflow or dock collision. Resize a
  focused companion, restore normal layout, reload; both weights persist.
- Escape, pointercancel, blur and viewport shrink cancel. A competing world
  prop/membership edit refuses a stale commit and repaints the real layout.
- Compose a draft without sending, record caret; rearrange, resize, change
  focus and reload. Words/caret and text editing remain usable. No test sends
  in the Conversation.
- Check names-only chrome, music controls/body selection, scrolling, title
  dragging and persisted tree/tab/size policies after repaint/reload.
- Bare app: compact natural size, no duplicate generic header or generated
  Fit/fill tools; appgrip carries the whole surface, playback/heart/text controls
  keep their own clicks; both divider axes still resize it. Check normal/full.
- Drag a whole panel/appgrip, document and surface/view to the dock. Confirm one
  pin after repeated drops, reorder by drag, deliberate menu removal, undo,
  restore in the current workspace without stale appearance ids, truthful open
  markers and preserved chrome/content-size/music/chat props. Hover names and
  compact coloured icons must remain readable without overflow at both sizes.
- Move between internal edge previews and dock previews; confirm exactly one
  target is shown and only its action commits. Cancel externally, change a
  receiver or carried panel while held, and verify stale/refused drops never
  rearrange the tree as a fallback.
- Record shots, facts, raw geometry and pass/fail per journey. Run the new
  `partition_navigation` step on the copy. Legacy column/wider-specific steps
  describe the retired layout and need new expectations before claiming a
  full historical playtest pass; do not silently count them as passed.

### Final source landing checkpoint (20 October, c7831/c7840)

The exact c7682 bytes have guarded browser acceptance from a7784, review
commit e938f74 round 6, composed over main 229b24a. EVIDENCE.md records the
receipt, hashes, timings and remaining coverage limits. Earlier "gated" and
"not run" statements above describe the historical Codex-only checkpoint.
This authorizes source landing; no production migration has run here.

JEFF's migration prerequisites after the house reports a successful landing:

- Preserve the house's merged main features: remember, Markdown/TextEdit,
  observers/atomic writes, dock CarryTargets and any current world edits.
- Re-read live home-tiling, home-style, layout/panel props, dock routes and
  helpers. Preflight the exact navigation_stage.py hunks and staged a7167/
  a7180 text against those fresh passages; stop on a moved passage. Never
  install the historical whole lens over newer edits.
- Build the typed tree from current membership/order/weights, retaining
  shelves, pins, music chrome=none/sizing=content/filled lens and existing
  copy_json declarations; don't reset Alex's rearranged layout.
- Save original texts/props before scoped writes and retain the staged restore
  recipe. Keep JEFF's transparent lgstat border: it is required for stable
  focus-exit geometry and was already present in the accepted review copy.
- Help a1853 already has the word catalog and detailed source documentation
  (e16351/e16358). Skip docs_stage.py's first two commands; re-read before
  removing its awaiting-landing label. The Handbook a243 table insertion is
  still staged in docs_stage.py; exact-preflight it after source lands.
- Review the companion slim-dock staging against the landed dock; don't replay
  already-applied hunks or invent missing tints/apps. Live application remains
  JEFF-owned, with the unchanged small-screen and timing limits disclosed.
