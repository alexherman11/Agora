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

## Reading collections and files (community board candidate)

`posts : list, of reading:"board.feed order=$view.order in=$view.channel" as p,
limit 12, offset $view.offset, each post` arranges an admitted reading. The
trusted widget host evaluates each reading with its viewer/instance principal,
outside the kernel lock. Results retain their ordering unless `by` is authored.
Bound rows carry their own revisions. Dynamic substitutions are quoted data.
`watch reading:"board.badges"` beneath a part observes a viewer-admitted reading
without constructing rows. A changed result invalidates the projection, and
`api.read` reuses that exact observation. Use this for role/name/label inputs
that affect a component without being its main collection. Watched values are
described in `look-view plan=yes`; no module runs in a default kernel reading.
`limit` (1..100) and nonnegative `offset` bound component construction; they are
collection handles, not component settings. `look-view` without a host's
projection reports unobserved reading sources instead of inventing rows.

The lens's JSON `view` fact supplies initial local selection values. Reviewed
components use `api.view()`/`api.select({...})` for transient selection and
`api.draft` for unsaved input. Durable personal choices still use `personal-view`
and `personal-style`. `api.read(line)` shares a viewer-checked reading within a
paint; `api.child(slot, settings)` supplies data to an authored child slot.
`api.cleanup(fn)` disposes resources on reconstruction/removal. Structured
`$fields` in an authored gesture expands validated plain field names and quoted
values in one pass, preserving user text containing dollar signs and semicolons.

`api.file(thing, 'content'|'thumbnail')` returns `{blob,url}`. The trusted parent
first checks `file-read` under widget grants, then fetches `/files/<thing>` with
its own authenticated session. Components receive neither a route nor a session,
token or network capability. URLs are revoked on component disposal. The frame
keeps `connect-src 'none'`; media allows exactly `blob:` (images already allowed
`data: blob:`). The general file component displays extracted PDF pages when a
PDF renderer is unavailable; it never embeds a PDF/plugin or active upload.

`labels ui {"Reply":"Responder","compose":"Escribir"}` provides a component's
UI words without changing domain values. Components call `api.label(key,fallback)`.
The personal handle is `<part>.labels.ui=<JSON>`. It is exposed on every component
help card and in `look-view`. Theme tokens may also be bounded nonnegative
numbers (0..2000) for weights/line heights; names ending `-font` accept plain
font-family names, never CSS text or URLs.

Use `api.P.submit(form, callback)` for local forms. It checks native field
validity, handles submit-button pointer/keyboard activation and Ctrl+Enter, then
calls the guarded action. The frame keeps its no-forms sandbox and
`form-action 'none'`. Native form navigation is never the action transport.

## 26 October: isolation and general editing handles

Builder draft for Claude's review. This section supersedes the earlier
statements about full default look-view, paint-time-only validation and
unreviewed-code refusal. The earlier description remains as experiment history.

`look-view <lens/widget/window>` is now compact: shown counts, settings, display
values, declared parts, gestures, health and last painted observations.
`look-view <target> plan=yes` adds the complete tree, bindings and module bytes.
Compiling structure executes no component code. `health.painted` is a recent
painter observation of visible text and computed styles, with `observed_at`;
`unobserved` means there is no paint evidence. It is not a pixel or accessibility
audit, and a dishonest component can misdescribe itself.

### Validated styles

Invalid targets or values refuse the entire `make`/`set` at write time, explaining
the allowed forms. Legacy invalid styles are skipped and reported in
`look-view.style_errors`; they cannot abort the view. Hex colours accept exactly
3, 4, 6 or 8 digits. `padding` and `radius` accept CSS's 1–4 measure shorthand;
`gap` takes 1–2. Measures are nonnegative, with px/rem/em/%/vh/vw or zero.
Six-digit glow keeps its soft default alpha; explicit four/eight-digit alpha is
preserved. `help part-style` exposes the contract through words.

### Just for me

Prefer these discoverable shortcuts, listed in ordinary `help`:

```
personal-view our-evening dates.month=2026-11
personal-view taskboard-components lane-view.labels.name="{\"Done\":\"Hecho\"}"
personal-view taskboard-components task-view.format.who=initials
personal-style taskboard-components target=card padding="4px 8px"
```

They create private preferences/styles for the caller's person, including when
that person's agent makes them. They do not edit shared tasks or domain values.
Personal styles apply after shared styles. `undo` removes the shortcut's act.

### Domain values and displayed words

```
lane-view : lane, name $lane.name
  labels name {"Done":"Hecho","Now":"Ahora"}
task-view : card, who $task.who
  format who as initials
stamp : text-block, value $task.due
  format value as relative-date
total : badge, label $task.count
  format label as count
```

`labels <setting> <JSON map>` and `format <setting> as initials|relative-date|count|text`
produce `node.display`, leaving `node.settings` and bound facts intact. Components
use `api.display(key)` for visible words; actions use domain settings and facts.
First-party lane, card and catalogue content adopt these handles. Initials use
the first letters of at most two words. Relative dates use the kernel's UTC
date. Counts format numbers or count a JSON collection.

### Happenings and motion

```
task-view : card, title $task.title
  when fact lane changes play settle
  when happening task-priority play pulse
```

Triggers apply to this part's projected facts. Initial paint is not a fact
transition. Happenings must target one of its bound rows and require the widget's
ordinary `hear:<word>` grant. Default theme motions are `settle` and `pulse`.
Add a token with `make kind=part-style lens=... target=tokens motion-breathe=<JSON>`:
`{"from":{"opacity":0.4},"to":{"opacity":1},"duration":250}`.
Only opacity, translate/scale and a duration of 0–2000 ms are allowed. Reduced
motion preferences suppress animation. Unknown motion names are visible refusals.

### One stopped part

Mount/update reconstruction, primitive-created event handlers, timers,
microtasks and animation callbacks carry an owner. Settings are checked before
mount. Module failures, missing components and bad settings become a calm card;
siblings continue. A failed part's inert last successful DOM is marked stale.
The card offers Try again, Use the previous version and Turn it off. Retry keeps
quarantine; only the steward word below clears it. Previous restores only the
latest changed code/arrangement/preference field and refuses a stale revision.
Off affects only this part for this viewer. These are recorded words:

```
component-action our-evening path=root/dates action=retry
component-action our-evening path=root/dates action=previous
component-action our-evening path=root/dates action=off
component-action our-evening path=root/dates action=clear
```

Two failures or time-budget violations quarantine a part. New/unreviewed code,
or a definition with `isolation=worker`, starts quarantined. On this WebView2,
sandboxed sibling frames share a renderer: they do **not** isolate each other's
loops. Quarantine therefore uses a terminable Worker, projected facts and a
bounded DOM vocabulary. It supports content, controls, callbacks and timers;
arbitrary nested modules, synchronous DOM measurement, shared drag and direct
reads are explicit limitations. Arrange those functions as trusted siblings or
wrappers. Unsupported facilities stop only that worker's part.

Use `api.el`, `api.part`, `api.P`, `api.setTimeout`, `api.setInterval`,
`api.requestAnimationFrame` and `api.guard(callback)` so ownership survives an
asynchronous continuation. Reviewed in-page JavaScript still has ambient DOM;
this is fault containment, not protection against deliberately hostile code.
An in-page loop cannot be interrupted by its own thread. The native parent
watchdog records quarantine and verifies renderer ownership before restarting
the view. It refuses to kill a renderer shared with another view. ISOLATION.md
records actual evidence and the recovery boundary.

`component-health` is a painter-only word restricted to its own lens. Reports
are private `paint-report` facts for the viewer; component cards and `components`
derive `health`, `last_error` and `quarantined` from those reports. Each failure
is a happening without publishing private error text to other viewers. Observed
paint data is separate from the projected plan and does not cause repaint loops.
Unreviewed bytes execute only in quarantine. Neither path adds an independent
world capability per nested piece: gestures use the existing guarded bridge.
