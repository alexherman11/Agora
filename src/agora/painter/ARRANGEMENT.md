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

Carried items use the window tiling engine's centre-crossing rule: overlap or
waiting alone does not move a neighbour. A translucent landing area previews
the drop, and displaced items animate from their current positions. A sorted
repeat keeps its authored `by` order; its compiler supplies the displayed
items' sort tuples and stable tie order so the preview agrees with the next
reading. Dragging does not rewrite sort fields. The geometry preview is a
read-only host operation; the declared drop gesture still owns the world act
and its revision checks.
The host reads `wm-settings motion_ms` for each preview, shared with native
window motion; no component installation is needed to change that timing.

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

### 26 October polish handles (builder draft)

`format stamp as short-relative` displays `2h`, `Tue`, `Oct 22`. Also available:
`calendar-date`, `month`, `day`, `weekday`, `time`. Existing `relative-date`
keeps its day-based wording. Initials use the first letter from each of the
first two words containing letters; numbers supply no initials. In a reviewed
component, `api.format(setting, value, fallback='text')` applies that setting's shared or personal
format to asynchronously read values. `api.display` remains the projected
display value. Client dates use the browser's local zone; projected displays
use the kernel clock and the supplied ISO zone. `api.node.viewer` exposes only
the already-bound viewer's id/name, including on parts with no gestures.

The catalogue `date-tile` takes `start`, `end`, `place`, `soonDays` (default 3).
Its `date`, `month`, `day`, `weekday`, `time` format handles supply each display.
Parts: `tile month day weekday time place countdown`. Arrange it beside any
dated thing; it adds no calendar backend. Its default skin travels with the
component, without loading the board. Shared token handles include
`date-tile-width`, `date-tile-gap`, `date-tile-radius`, `date-tile-text-size`,
`date-tile-small-size`, `date-tile-day-size`. Board theme tokens can override
that skin through its ordinary parts. Example:

```
meeting : date-tile, start $item.start, end $item.end, place $item.location
  format date as calendar-date
  format month as month
  format day as day
  format weekday as weekday
  format time as time
```

`slots` exposes a `meter` part and `count`, `claim`, `label`. Full or closed
things have no claim control. `poll` displays large choices before voting and
percentage bars after voting or closing. Kernel readings include `you_liked`
and `your_vote` only for the reader; totals remain public and sealed keys never
leave the kernel. `stamp` is the poll's closing-time format handle. Its labels
include `voteCount` (singular vote) and `votes` (plural), alongside the option
labels, whose authored case is preserved.

`file` adds `page` (initial page, default 1) and optional `pageTarget` (apply the
initial page only to this file). Increment `pageRequest` to re-address a reader
even when that same page was requested before. A changed external request
resets the page; unrelated repaints preserve the reader's local page choice.
Readers clamp to available pages and offer a
page picker. Photos open a cleaned full-size Blob on pointer or keyboard action;
only the original poster sees the description editor. `variant=thumbnail`
shows a document's first text lines and page count instead of its full reader.
Bind `owner $file.upload_owner` when arranging file metadata separately from
content. This avoids a late ownership lookup moving a photo card's controls;
omitting it retains the permission-checked lookup fallback. It grants no edit
rights and does not change the kernel's admission checks.

`P.parseDateEntry(text, now?)` is a reusable local parser returning
`{ok, iso, local, label}` or `{ok:false, message}`. Accepted: ISO local dates and
times, `today`, `tomorrow`, or an English weekday plus a time (`Thu 6pm`). It
rejects impossible dates/times and does not guess arbitrary natural language,
use a model, or contact a service. It uses the local browser timezone, including
its DST rules. Calendar smart entry can reuse it without a board dependency.
`P.selectionAction(source, draft, version, action, {label})` supplies a floating
selection-only control, a keyboard-callable `quote` action, and `dispose` for
`api.cleanup`; authors arrange a More-menu fallback. Committing the action clears
the consumed browser selection; merely selecting text does not act. It adds no word authority.

`input, commit submit, submitLabel "Send"` emits **submit** only on non-IME Enter
or its button. It never sends on blur, ignores blank/pending submissions, retains
refused drafts and clears only successfully sent text. Arrange `on submit do ...`
with `$value`. Default `commit=change` retains the existing change gesture.
This works for a quick-add field, a search command or a chat draft; it is not a
board-specific input.

Feed, file reader and Work keep `pageBounds(total, size, page)` inside their
component modules. It clamps the zero-based page and disables unavailable
previous/next controls, including empty and one-page collections. They require
no change to painter widget code or grants.

Board and map components publish from checked-in `board-components.bundle.js`
and `map-components.bundle.js`: each component imports one file into its code
fact. The board file includes its CSS; the map file includes its engine and
worker definitions. Builders regenerate these files before landing with
`src/community/board/build_component_bundles.py`; `--check` detects
stale artifacts without writing. Publication never assembles bundles or patches
the top bar, dock or other widgets.

The shared calendar wraps its grid in the `container` part, an inline-size
container named `calendar`. Its breakpoints measure that part, including inside
a split layout, rather than the desktop viewport. Agenda width uses world style
tokens `calendar-agenda-min` and `calendar-agenda-max`; normal paper/ink/spacing
tokens still apply.

`file, quoteMode inline, replyTarget <post>, replyLabel "Discussion"` keeps the
quoted passage, page and response in a visible draft in that reader. Arrange
`on reply do ... $target $fields`; fields are `text`, `quote`, `source`, `page`,
with a fresh target revision. `startLabel` names the destination when there is
no existing reply target. Without a target, an authored **start** gesture
receives `$group` (replyGroup or the bound row's first group) and `$fields`
containing title and text with the quote and file link. Its returned first made
thing becomes the local reply target for later quotes. Selection never sends;
the explicitly labelled send button does. Failures keep the draft. No authored
destination shows an unavailable explanation. Existing `quoteMode=thread`
keeps the containing thread workflow; shared right-click Comment is unchanged.

Post-kind metadata `compose_fields_first=yes` and `compose_message_rows=3`
arranges declared details before the message and chooses its initial height in
the shared composer. It works for any kind. The submit footer stays reachable
while the dialog scrolls, styled with the existing world tokens.

`map-layers, collapsed yes` starts folded with its Show/Hide layers button inside
the panel, including narrow windows. An explicit toggle persists for that
mounted part. Labels `showlayers`, `hidelayers`, `onmap`, `withoutlocation` are
world-configurable; layer names come from map-layer things, never app-specific
name matching in the renderer.

`api.fire(event, {…values, select:{…localView}})` applies a local view selection
after word admission succeeds and before the first resulting repaint. Use it
to dismiss a one-action dialog atomically with its successful action. Refusal
leaves the selection and draft intact. It has the same local reach as
`api.select`, and does not alter the authored world line or its rights/fences.

The board shell's `extras=feed` default flows additional root parts into the
feed's existing column; a stopped sibling cannot allocate an accidental extra
reading pane. `extras=alongside` preserves literal sibling grid placement.
Board `post.layout=compact` and `post.excerptLines=3` choose feed density;
`detail` selects the reading-pane treatment. `catchup.previewCount=3` bounds
grouped preview rows, with the full group available by expansion.
`compose.advancedFields="closes place"` moves those fields under More options.
World kinds supply `compose_label`, `compose_description`, `compose_icon`,
`accent`, `field_labels`, `field_types`, `fields` and `required`; neighbour-made
kinds use the same declarations. The compact phone destination picker uses
labels `channels`, `yourboard`, `saved` and `queue`, including the admitted queue
count. Board layout/reading/photo/semantic token names and the fixed responsive
breakpoint boundary are enumerated in the board's UI-HANDLES.md guide.

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

> **Superseded in part (builder draft, 26 Oct 2026, the shell's bars as components).** Paint health is screen state now:
> `component-health` keeps observations in the kernel process's memory, per viewer, never recorded and without painted text
> or styles; quarantine is local too; `component-action off` is the viewer's own `view-preference` (`<part>.enabled=no`);
> `paint-clear` (stewards) forgets the old `paint-report` things in one act. `size` joins the style vocabulary;
> `api.child(name, settings, key)`, `api.ask(event)` and lens facts `right_click=ask`, `reconcile_ms` are new.
> See painter/health.py and desktop/kernel-desktop/SHELL.md. The paragraph below is the earlier design.

`component-health` is a painter-only word restricted to its own lens. Reports
are private `paint-report` facts for the viewer; component cards and `components`
derive `health`, `last_error` and `quarantined` from those reports. Each failure
is a happening without publishing private error text to other viewers. Observed
paint data is separate from the projected plan and does not cause repaint loops.
Unreviewed bytes execute only in quarantine. Neither path adds an independent
world capability per nested piece: gestures use the existing guarded bridge.

## Panels and sizes (4 Nov 2026)

Alex asked for side panels that shut to nothing from icons in the window's top bar, like Claude desktop, and for each
app to say what it does at different window widths. Three lens words do it:

```
root : writing-shell, title "Writing"
  sizes narrow 0, middle 1080, wide 1460
  rail : doc-rail
    panel left, icon sidebar, label "Documents", width 292
    shut when narrow middle
page-view : doc-page, measure 780
  comments : column, of tag:comment, prop:about=$d.id as c, each comment-view
    panel right, icon comment, label "Comments", width 300
    shut when narrow
```

- **`sizes <name> <from px>, ...`** goes on the root. It names the window's widths. The current name is `$view.size`, so any
  part can read it (`only when $view.size = wide`). The painter re-reads the plan when the window crosses a size.
- **`panel left|right, icon <name>, label "<words>", width <px>`** goes on any part. The part becomes a side panel,
  either open or shut, and shut means no width at all. Its button goes in the top bar, on its side. Icons come from
  `P.icon`: sidebar, sidebar-right, comment, list, outline, info, files, chat and people.
- **`shut when <sizes>`** or **`shut when <condition>`** is the layout's wish. It takes size names, or a condition in
  `only when`'s form (`shut when $view.open = ""`). When the wish starts, the panel shuts. When it ends, a panel the
  layout shut opens again, but a panel you shut stays shut. A panel you open while the layout wants it shut lies over
  the page, and a click on the page or Escape shuts it again.

Which panels are open is the window's own view, `$view.<panel>` = `open|shut`. It is screen state (Alex, 26 Oct): sent
with each reading and kept in the kernel's memory, never recorded. From Lines:
- `look-view writing` shows what your running window shows now (`window: ... rail=shut, size=narrow` and `panels: ...`).
- `view writing comments=open` changes it. Only the person it is said by (or their agent) is told.
- A lasting choice is a preference: `make kind=view-preference sees=me lens=writing view.comments=shut`.
- A rule that runs `view` can open panels when something happens.

For component authors:
- `api.panelButtons('left'|'right')` returns the buttons, for a component that draws its own top bar. Any panel whose
  button is placed nowhere gets one floating at that top corner.
- `api.panelOpen(name)` and `api.panel(name, open)` read and set a panel, for example to show comments when their
  words are clicked.
- If a component holds a panel inside a container of its own, it marks that container `data-panel-frame` (empty for
  the panel inside it, or `="<panel name>"`). The container is then what opens and shuts.
- The painter puts `data-panel=<side>` on the frame always, `data-shut` while it is shut and `data-over` while it lies
  over the page. A grid gives up the frame's column with `:has()`. Writing does it like this:
  `.wr-page:has(>.wr-margin[data-shut]){grid-template-columns:minmax(0,1fr)}`.

This replaced the 40px fold strip (`fold <label>`, `P.fold`) from earlier the same day, which was never committed.
# Receipt outcomes and local selection (4 November, round 2 builder draft)

`components for="action result"` / `help action-notice` describe the reusable
receipt notice. Arrange it beside actions whose rows may disappear:

```text
root : column
  outcome : action-notice, stateKey actionNotice, scopeKeys "channel thread"
    on undo do undo $value
  done : button, label "Mark done", completionText "Marked done."
    on press do set $view.target done=yes
```

The bundled `actionFeedback` helper publishes pending feedback synchronously,
before admission or a world reread. Its component-local channel holds a navigation
scope and unique action token, followed by the exact returned receipt.
`scopeKeys` names the view fields that define navigation (empty means all).
Components use `feedbackAPI(api).select` for navigation: it clears notices and
invalidates pending completions immediately. Undo checks the current scope and
token again before firing the authored gesture with that exact receipt.
Legacy JSON notices in view state are ignored. Refused Undo retains recovery
and displays the reason; an older completion cannot replace a newer outcome.
`noticeKey` on button and `stateKey` on notice select another local channel.
Pending button presses cannot repeat.

For local navigation, a button's `selectKey="thread replyTo"` assigns its `value`
to each named view key without a world write. Choice uses `selectKey` for one
key, or its original authored `change` gesture when absent.
Both Work arrangements demonstrate reuse with a real Mark done action:
`work-line` emits `done`, the lens authors `set $item lane=Done`, and
`action-notice stateKey workNotice` reverses its exact receipt. Work filters
only navigate; they no longer manufacture completion notices.

The canonical helper is `components/action-feedback.js`; the repository bundle
builder embeds it in complete component artifacts. There is no publication-time
assembly and no widget-runtime dependency. Help is generated from the
`action-notice` entry in `painter/catalogue.py`.

These are components and world arrangements, with no new widget primitive,
grant or tiling engine. The notice exposes body/message/undo/dismiss parts,
labels `undo`, `undone`, `dismiss`, and `notice-*` theme tokens for spacing,
colour and shape. It never sends a message. Shared right-click Comment remains
the existing host interaction mechanism.

Painter subscription hints are optional: a refused hear no longer prevents
the first authorised reading from painting. A screen-local component-health
observation records the limitation, and normal reconciliation continues.
This runtime fix affects newly assembled painter widgets; updating component
code alone cannot patch an already stored widget runtime.
