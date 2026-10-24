# Arranging reviewed components

Builder draft, 24 October 2026. This is a new painter beside the existing one.
`desk-shell/lens.js` is unchanged. A lens selects it with `painter=components`.

Read `components`, then `components for="an events calendar"`, then `help calendar`.
A card gives the purpose, typed settings and defaults, named parts, child slots,
gestures, an example and reach/limitations. `window.open component-gallery` opens
the live examples. A component name is not a promise of a domain backend.

```
root : column
  heading : text "Our evening"
  dates : calendar, month "2026-10", label "Community events"
    on select do choose-date value="$value"
```

Indentation owns children. `name : component, setting value, setting value` is
a part. Primitive `column`, `row`, `grid`, `wrap`, `split`, `layers`, `scroll` and
`absolute` and `text` need no component installation. Layout settings include
`gap`, `padding`, `width`, `height`, `minHeight`, `maxHeight`; grid takes `columns`
such as `"1fr 2fr"`; absolute takes numeric `x`, `y`, `z` inside layers. Split panes
have a keyboard and pointer separator. A text part also accepts `text "prose"`.
Settings can be indented as `setting name=value`. Quoted literals use JSON string
escaping. Part names are local; root-level names can also be templates.

```
root : column, of tag:taskboard-lane as lane, by order, each lane-view
lane-view : lane, name $lane.name
  on drop card do task-move $carried to="$lane.name"
  cards : column, of tag:taskboard-task, prop:lane=$lane.name as task, by priority, each task-view
task-view : card, title $task.title, who $task.who
  only when $task.priority = 1
  badge : badge, label "Urgent"
```

`of tag:kind` selects visible rows. Comma-separated `prop:field=value` clauses
filter them. `as alias` binds the row; `each template` repeats a named template;
`by field` sorts numerically where possible. Query parts can be primitive
wrappers or catalogue collections, including virtual-list with fixed row heights.
Nested rows retain parent bindings. `$item` is the current row; `$alias.id` and
`$alias.field` read facts. `$viewer.id/name`, `$today` (UTC date) and `$now` (UTC
timestamp) are built in. Missing fields read as empty. `only when` supports
`= != > < >= <=`, `and`, `or`; it compares numbers when both are numeric,
otherwise strings, including ISO dates. No eval or arbitrary expression language.

`on <gesture> do <word line>` is authored arrangement. Component help names the
gestures it can emit. Values such as `$value` are quoted as data, including inside
an authored quoted argument. Every gesture goes through the guarded widget
bridge, under the viewer's rights narrowed to the widget's grants. It supplies
painted revisions for all bound rows, including carried and receiving rows.
A stale participant refuses. Visible happenings trigger streaming rereads; a
1.5-second reconciliation also removes rows whose deletion/visibility change is
no longer hearable and reevaluates time conditions. Identical projections do not
repaint. Components share this page and the core's spring
drag. They have no native bridge, credential, network connection or direct store.

`look-view <lens/widget/window>` returns the fresh arrangement, rendered counts,
typed settings, bound visible facts, declared parts and gesture lines. The painter
builds this reading without executing component modules. It describes authored
and bound structure, not a verified account of a malicious component's pixels.

## Style is a thing

```
make kind=part-style lens=our-evening target=badge color=blue radius=soft
```

Targets are `component`, `component.part`, or either followed by `[fact=value]`.
Facts are attached to every declared part as `data-fact-<field>`; the original
fact row and settings are also available as JSON data attributes. `color`,
`background`, `radius`, `padding`, `gap`, `glow`, `lines` (1–9) and `emphasis`
(`normal|bold`) are the intentionally small style vocabulary. Values are theme
tokens, literal colours or lengths. `target=tokens` defines additional named
tokens for that lens. There are no arbitrary selectors, URLs, scripts or CSS text.
This form lets a neighbour write and inspect one ordinary line, instead of
learning CSS specificity and a second transport language. Invalid targets or
values refuse to paint with an explicit message; they are never injected as CSS.

## Personal arrangements

```
make kind=view-preference sees=me lens=our-evening dates.month=2026-11
```

An owned preference overrides `part-name.setting`; optional `text` supplies a
personal arrangement. Only the maker's preferences apply to their view, even if
they accidentally publish the preference. Shared facts stay shared. A style can
use `personal=yes sees=me`. The ordinary door supplies ownership and visibility;
there is no `as=<person>` impersonation parameter. `undo` removes a preference.

## Installing a component

`make kind=component name=... code="<ES module>" ...` stores exact module bytes
and its card as world data. A steward must `look` then `component <thing>` to
review those bytes. Any code change invalidates review. Settings types are
`text`, `fact`, `number`, `boolean`, `json`, with optional defaults. A default
module exports `{mount(api, settings)}` and returns its root DOM handle. Use
`api.P` primitives and theme tokens, `api.part(name,tag,attrs,...children)` for
fact-carrying parts, `api.children`/`api.render` for slots, `api.fire` for declared
gestures. Reviewed code is trusted within the shared page. This is not a hostile
component isolation boundary or an independent capability for each nested piece.

See REACH.md for the map, primitives.js for the small core, and catalogue.py for
the first-party cards. Native host functions and domain modules remain separate.
