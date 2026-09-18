# Tessera scene experiment: software as a reactive addressed graph

This replaces the fixed panel renderer for the next trial. The viewport is a blank
stage. Authors control its composition, positioning, color, typography, and motion.
No HTML, CSS source, JavaScript, callbacks, or feature-specific renderer handlers.
Existing field/query/derive/action/reaction/constraint semantics still apply.

## Added view semantics (all data)

* `widget`: scene, surface, canvas, portal, stack, row, grid, text, badge, input,
  textarea, select, button, link, line, circle. Panel still works but has NO imposed
  layout. Generic defaults only: stack=flex column; row=flex row; surface=absolute,
  canvas=relative; all others are neutral elements. Every visual property may be
  changed by style claims. `scene` fills viewport. No stock three-column layout.
* `context`: expression returning a record. Establishes row for this view and
  descendants; e.g. `["record","surfaces","studio"]`. Existing lists also work.
* `box`: `{x:expr,y:expr,width:expr,height:expr,z:expr}` sets base absolute geometry
  in pixels (x/y relative to parent padding box); style rules may override geometry.
* `role`: semantic string; multiple roles can be space-separated.
* `to`: on portal, expression returning destination view id. Its entire rendered
  subtree moves to that live address after graph construction, retaining its row
  context/identity. Missing hosts leave a diagnosed visible orphan. Hosts must have
  unique static view IDs. Portals can carry cards between independently authored
  windows WITHOUT rewriting either source tree. Avoid cyclic hosts (diagnosed).
* `dropRole`: semantic string marking a drop surface. Gesture exposes its VIEW ID.
* `line`: use x1,y1,x2,y2 expressions (local pixels); a neutral SVG line primitive,
  full-parent overlay, pointer-events none. `circle`: cx,cy,r expressions.
  Lines may set `space:"viewport"` to paint in viewport coordinates. Vector
  properties are evaluated AFTER portals/layout, so they may use measured geometry:
  `["measure","card.shell",cardId,"centerX"]` (also centerY,x,y,width,height,
  right,bottom). Null if the addressed occurrence is absent. A stable view id plus
  the row record id addresses an occurrence independent of its host. Measurement
  is available only to vector-paint expressions; it cannot feed layout or writes.
  This stratification avoids a geometry feedback loop while supporting live links.
  `box.height:"auto"` and arbitrary style height:auto are permitted for intrinsic
  card content. The renderer routes by actual layout, not guessed preferred sizes.
* `onChange`: `{action,args}` for input/select immediate declarative commands,
  optional; otherwise local bind and button applies. Context includes event.value.

Expressions: `["env","width"]`, height are viewport size. `["event","value"]`.
`["frame","width"]` and height are the nearest surface's EFFECTIVE resolved
dimensions (including other authors' styles), provided to its children. Descendants
must size from frame, percentages, or flexible layout rather than a stored preferred
width/height; those preferred values can be overridden by layout contributions.
Style values are expressions evaluated with each matched view's row/local context.
`when` is an optional style predicate. Selectors: id:, role:, widget:. Whitelisted
CSS properties cover layout, geometry, transforms, transitions, typography,
backgrounds/gradients, borders, shadows, overflow, opacity, visibility, cursor,
pointerEvents. No URLs/imports/script. Highest explicit priority wins per property;
equal-priority disagreement is diagnosed and that property falls back to base.
Browser rendering expands CSS shorthands into property atoms before resolving
different contributors. Within ONE rule, a narrower declaration refines a broader
one (backgroundSize refines background), independent of JSON property order.
Priorities are policy, not an implicit author order. No style rule can run an action.

## Gesture records: motion is data, final decisions are actions

`{"kind":"gesture","id":"tools.move","selector":"role:surface",
"handle":"role:surface-grip","mode":"drag","preview":[
 {"op":"set","collection":"surfaces","id":["row","id"],"field":"x","value":["gesture","x"]},
 {"op":"set","collection":"surfaces","id":["row","id"],"field":"y","value":["gesture","y"]}
],"commit":{"action":"surface.move","args":{"id":["row","id"],"x":["gesture","x"],"y":["gesture","y"]}}}`

Gesture mode drag or resize. Handle is a matching descendant. It targets the
nearest matching ancestor only, avoiding a card drag also moving its window.
Native controls inside a handle retain their own activation; the handle's
non-control area starts motion. This keeps a contributed button usable in a grip.
All matching gesture contributions on that same node join their preview writes;
unequal sets are conflicts (no last-handler winner). Commits join atomically via
the normal actions/reactions; identical action+args coalesce.
`gesture` values: dx,dy,x,y,width,height,startX,startY,startWidth,startHeight,
pointerX,pointerY,drop. x/y = start box x/y + pointer delta; width/height = start
box width/height + delta. Drop = hovered view id with requested `dropRole` from
gesture record (or null). Preview supports ordinary set/add/union on existing
records. It is browser-local scratch state; no network writes until pointer-up.
EVERY dependent style/query/line sees preview state, so connected visuals follow
motion. Pure transforms/clamping/snapping use normal expressions/derivations.
Escape cancels preview. Commit refusal restores prior state and shows reason.
Gesture `when` optional predicate. Commit action must implement intentional final
clamping/docking: renderer does not know the domain meaning of movement or drops.

## Shared ports for trial 3 (language fixtures, not prebuilt feature code)

Base declares only fields for shared data and root `scene`. No default arrangement.
`surfaces`: title:string, x/y/width/height/z:number, dock:string default free,
hidden:boolean false. Each agent seeds its own window record and writes its own
surface view with context record, role surface, box from these fields. Controls
under that view inherit the surface record. Title grip uses role surface-grip;
resize grip role resize-grip. Authors choose their own static view IDs/initial boxes.

`cards`: title/body/color:string, x/y:number, host:string. Common card template
authored by Studio builder uses role shared-card and role card-grip handle.
All three agents may contribute children/styles to `card.face` and `card.tools`.
Portal target = cards.host. Drop surfaces use dropRole card-host. Card x/y are local
within host. When changing host, commit may reset x/y to an intentional default;
this is authored behavior, not renderer behavior.

Studio builder (notes_builder): visually distinctive document studio window,
editable shared cards, create/edit/delete actions, common card template with portal
host, local drag gesture+card.move action (drop across hosts). Host `studio.host`.
Canvas builder (tasks_builder): visually distinct spatial atlas window, host
`atlas.host`; shares Studio cards and adds connectors and a graph tool palette,
dynamic line endpoints following cards during drag, seeds its own cards/connections.
Toolkit builder (library_builder): authored scene/background/theme controls, window
move+resize gestures and actions, window dock/reflow/focus modes, floating control
console with host `console.host`. Scene can be radically restyled via preferences.

Directly negotiate peer details as needed; declare owned ports in own *.ports.md.
Builders write ONLY own studio/atlas/toolkit.tessera.json and cases. Root implements
generic semantics and tests, never integrates feature declarations. First outputs
frozen before testing. Each agent must ALSO author one independently keyed style
rule affecting role:surface (not just own window). Deliberate overlap: Studio wants
surface borderRadius 20px at priority10; Atlas wants 6px at priority10; Toolkit
supplies a user-chosen override at priority30. Equal-priority conflict must be
visible if override disabled; neither author loses their declaration.

Visual acceptance: three clearly different but composed windows; drag+resize;
drop one shared card across windows; connected edges follow a dragged card;
dock/reflow scene while preserving identities; switch scene appearance; expose a
competing style and recover; run pointer previews locally, commit only at end;
two clients move different windows concurrently without whole-scene invalidation.
