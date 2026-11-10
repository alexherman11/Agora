# Contracts and gaps

**Moss · 23 September 2026 · input for the final Current Implementation**

This note fixes the contracts between the parts of the text-desk lab (`src/text-desk/notation/`) and lists what a builder meets first. Paths are relative to that directory. Line numbers refer to the working tree on this date.

**How it was checked.** deskd was not listening on 127.0.0.1:8780, and I started nothing. I called `deskd.Handler.do_GET` and `do_POST` in-process with fake request objects on a fresh session, `doc-moss`. That runs the same code the server runs. The CLI was run with `DESKD=off`. `pytest test_scene.py` passes 4 of 4. No browser was driven, so painter behaviour is read from source, not observed.

---

## 1. deskd HTTP API

`python deskd.py [port] [static_dir]` binds `127.0.0.1:8780` by default and serves `desk-shell/`. The module docstring lists three endpoints. The code has five.

**Common to every endpoint**

- `session` names `sessions/<session>.pickle` and defaults to `desktop`. `as` is the actor. It is lowercased and defaults to `alex`. Neither is authenticated or sanitised.
- Every API request, **including GETs**, loads the pickle under `sessions/<session>.lock` and writes the whole pickle back on exit (`deskd.py:42-69`). If a GET names a session that does not exist, the file is created.
- The lock loop tries 600 times at 50 ms, then **proceeds without the lock** (the loop has no failure branch, `deskd.py:43-50`). A lock older than 60 s is deleted as stale. The CLI does the same with 600 × 100 ms (`explore.py:74-81`).
- An uncaught exception closes the connection with no JSON body. Examples are a malformed body, `since=x`, or a selection refusal (see §6.1).

| Endpoint | Input | Response (always HTTP 200 unless noted) |
|---|---|---|
| `GET /api/snapshot` | `session`, `as` | `desk.snapshot()`, which has `nodes, subjects, links, rules, scripts, clock`, plus `events_total`, `worktree` (journal given as a count, or `null`), `readers` (`{actor: event index read to}`) and `outline` (the actor's `look` text). The per-actor seen map is restored afterwards, so rendering does not count as looking (`deskd.py:99-101`). |
| `GET /api/scene` | `session`, `as`, `lens` | `{scene, text, events_total}`, or `{refused, events_total}`. A `LensRefusal` gives its message. Any other exception becomes `refused: "the lens compiler failed (...)"` (`deskd.py:103-114`). |
| `GET /api/events` | `session`, `since` (int) | `{events: [...], total}`. Each event has `id, verb, target, by, at, args, cmd, changed, note, via` (as observed), and `undo` is stripped. |
| `POST /api/do` | `{session, as, line, observed?}` | `{text, error, events_total, line, as, created: [ids], events: [event ids]}`. See the refusals below. |
| `POST /api/observe` | `{session, as, lens, at, facts: {key: string}, viewport: {w,h,sx,sy}}` | `{ok: true, kept: n}`. It never refuses. |
| `GET` anything else | | A static file from `desk-shell/`. |

**Every refusal `/api/do` can return**

| Case | Code | Body |
|---|---|---|
| `line` empty or whitespace | 400 | `{"error": "line is required: every gesture is a command"}` |
| POST to any other path | 404 | `{"error": "POST /api/do or /api/observe"}` |
| `observed.def` present and the lens subject is gone or at a different `rev` | 200 | `{text: null, error: "refused: lens <name> changed since this was painted (you saw revision N, it is now M) ... Nothing was done. The view will repaint.", events_total, line}`. This body has **no** `as`, `created` or `events`. |
| The desk refuses (unknown command, no such id, not looked, stale, bad argument) | 200 | `text: null`, `error` is the refusal text, sometimes led by a `!! since your last look:` delta |
| Multi-step `a; b` where a later step refuses | 200 | `text` holds every step's receipt, and `error` is the first line beginning `ERR` (`deskd.py:173-174`). I verified this only with a read-only first step. The desk stops at the first refusal, and earlier steps are not rolled back. |
| Malformed JSON, or an exception inside dispatch | none | The connection closes. On a dispatch exception the pickle is still saved by `__exit__`. |

A `line` whose first word is `worktree` goes to `worktree.handle` and returns `{text, error, ...}` in the same shape. The body field `cli` that the CLI sends is ignored.

**`/api/observe` limits** (`deskd.py:125-135`). At most 400 facts are kept. Keys are cut to 200 characters and values to 60. The server stores one entry per actor in `desk._views`, as `{lens, at, time, viewport, facts}`, so the last lens reported by an actor replaces that actor's earlier one. The entry is not an event, is not undoable and is not world state, but it is saved in the pickle. The server does not check that keys are real scene keys.

## 2. The observed-revision fence

Two different checks can refuse a gesture. Both run before anything is applied.

**Definition fence (deskd).** If `observed.def` is present, deskd compares `def.rev` with the lens subject's current `rev` and refuses on any difference or absence (`deskd.py:144-150`). `def` comes from the scene (`scene.py:439`). The fallback scene, served when a lens stops compiling, has **no `def`** (`scene.py:446-452`). Gestures painted from a fallback therefore skip this fence.

**Item fence (the desk).** If `observed.item` is a node and `observed.rev` is an int, deskd **overwrites** the actor's `seen[item]` with the painted rev and records `_seen_idx[(actor, item)] = observed.at` (`deskd.py:151-158`). The actor's own look state is replaced by the painted observation, which can also lower it. The desk's ordinary check then runs:

- **Appearance or surface target** (`desk_moo.py:203-209`). If `seen` is missing, the desk refuses with "you have not looked at X yet". If `seen != rev`, the verb is not `create` or `comment`, and another actor's event named the node or its subject after `at` (`desk.py:267-281`), it refuses with `stale: X changed since you last saw it`. Your own changes and sibling reflow do not refuse.
- **Subject target** (`desk.py:761-768`). Any rev mismatch refuses. No test for other actors is made.

**What the painter sends** (`lens.js:17-19`): `observed = {item: n.item, rev: n.rev, at: sceneAt, def}`. Three consequences follow.
1. A node carries `rev` only when it has acts and an item that is a node (`scene.py:312-313`). Other gestures carry no rev, and the actor's session look state judges them.
2. Only `observed.item` gets the painted rev. A gesture line that targets `$id` (the subject) or any other id is judged by what the actor last *looked at*, not by what was painted.
3. `sceneAt` updates only when the scene JSON changes (`lens.js:90-93`), so `at` can be older than the paint. That is conservative.

**Verified outcomes on `doc-moss`.**

| Sequence | Result |
|---|---|
| moss paints `week`, priya tags a03, moss clicks a03 with the painted observation | `stale: a03 changed since you last saw it` |
| moss paints, priya runs `do prop week spacing=10`, moss clicks | `refused: lens week changed since this was painted (you saw revision 1, it is now 2)` |
| moss repaints and clicks | `ok due a03 on=2026-09-25` |

**The CLI** (`explore.py:36-56`). When deskd answers, each stdin line is posted separately as `{session, as, line, cli: true}` with **no `observed`**. The fence is therefore the actor's own look state: `look`, `read` and `examine` mark things seen. Lines are not atomic as a batch, and a dead server mid-batch prints `ERR deskd stopped answering`. The CLI runs in-process under the file lock instead when `DESKD=off` is set, when no server answers the first line, when any line begins with `!` (a test injection as another actor, which bypasses the fence), or with `--dump`, `--shape` or `--reset`. It applies the same desk fence. The default actor is `jeff` in the CLI and `alex` in deskd. An actor with no per-actor record inherits the pickled seen map if it is `jeff`, and starts empty otherwise (`explore.py:91-96`, `deskd.py:54-58`).

**The application shell sends no `observed`** (`core.js:48-51`). Its apps prefix `look <id>;` to their commands (`apps/editor.js:266,350,358`, `apps/notes.js:155,338,391,412`). The painter used to do the same, and it was removed there because it "turned stale pixels into fresh permission" (`deskd.py:152-153`). Shell gestures are not fenced against what was on screen.

## 3. Scenes and the painter

### Scene node (`scene.py:290-357`)

| Field | Present | Meaning |
|---|---|---|
| `part` | always | The lens part name. The synthetic overflow node uses `"cut"`. |
| `key` | always | A stable address: the root part name, then `/child`. Repeated instances use `/<node id>`, or for row sources `/<cid, eid or name>` or the index. Nested lenses are rekeyed under `<key>/lens:<name>`. |
| `role`, `layout` | always (may be null) | A role name from `calm.style`, and one of `column`, `row` or `free`. |
| `item` | always (may be null) | The node id this part is about. |
| `text` | always (may be null) | The filled template. |
| `clamp` | always (may be null) | Maximum lines on text, or maximum instances on a repeat. |
| `acts` | always | `[{on: click, edit or drag, line}]`, with `$x $y $value` still unfilled. |
| `kids` | always | Child nodes. On a repeat, the instances come first, then `cut`, then the part's own children. |
| `rev` | acts and a node item | The item's node rev at compile time, used by the fence. |
| `box` | `at item` or `spread` | `[x, y, w, h]`. |
| `facts` | `at item` | World visibility facts, such as `offscreen-part` or `43% hidden by f52`. |
| `placed` | spread | `"spread"`: computed presentation, never written back. |
| `absent` | failed `only when` | The selection that failed. Role, layout, box and text are null. |
| `of`, `n` | repeat | The selection text, and the count shown (excluding `cut`). |
| `cut` | clamped repeat | The number not shown. A `cut` child also carries the words. |
| `lens` | `lens <name>` part | The nested lens name. |

The scene root also carries `def: {lens, id, rev}`, `views: {actor: {lens, at, time, viewport, facts}}` (filtered to this lens), and `broken: "<refusal>"` when it is serving the last good compile. The node budget is 1500 (`scene.py:56`), and past it the compiler refuses and asks for `clamp`.

### Painter contract (`desk-shell/lens.js`, `lens.html`)

**What it may know.** The painter knows the scene vocabulary only: layout, role, text, clamp, box, acts, key, rev, def and absent. It knows no kinds, no apps, no colours and no sizes. `lens.html` CSS is limited to layout mechanics, and every look comes from a role class (`lens.html` comment, `lens.js:4-7`). A missing capability becomes a new scene word argued for in the studio, never a special case in the painter.

**What it does.**
- Each node becomes a `div` with `data-key`, a role class, `l-<layout>`, and absolute placement when it has a box. Absent nodes become hidden divs.
- An element whose node signature did not change is kept, so a reader's selection survives other people's edits (`lens.js:28-40`).
- `click` fills `$x $y` relative to the part. If the line uses `$x`, clicks on children are ignored.
- `edit` makes the element `contentEditable="plaintext-only"`. Enter commits on blur, Shift+Enter inserts a newline and Escape reverts. The value is escaped `\ " newline` and the text is never rewritten.
- `drag` works only on boxed parts, fills `$x $y` and is clamped to ≥ 0. `String.replace` fills only the first `$x`.
- Every gesture is posted to `/api/do` with `observed`. A refusal is shown as `refused: ...` in the text pane, and the view then repaints.
- The painter polls `/api/scene` every 1.5 s, skipping the poll while an edit or drag is in progress. A scene refusal blanks the paint and shows the reason.

**What it reports** (`lens.js:104-119`). For each key it may report `cut by the clamp`, `contents overflow the box` or `out of view` (the last only for boxed parts). It also reports the viewport and scroll, sending only when something changed, and again 400 ms after scrolling stops. `to_text` prints these as `~ <actor>: ...` per node, plus a header line per viewer (`scene.py:366-410`). They are observations, never world facts.

**The 150-line budget** (`lens.js:2-3`). This is Wren's rule. Every scene word costs painter lines, and at the ceiling a word must be removed before one can be added. It guards against the painter growing into "a worse HTML" that no one can argue around. The file is 123 lines today, so 27 remain. The budget is a convention: neither `test_scene.py` nor `checks/` enforces it.

## 4. Style language (`desk-shell/style/calm.style`, `style.js`)

- **Tokens** (`token name = value`) are the only place a colour or number may appear. A token value can be a hex colour, a mix (`ink at 20%` is mixed toward `paper`), a length (`gap = 8`), a type spec (`ui 15/1.5`) or a ratio (`ramp`). Each token becomes the CSS variables `--t-<name>` and `--<name>`.
- **A role** (`role name : prop, prop`) is a named look assembled only from tokens. The properties are:
  - colour: `on <colour>` for the background, a bare colour for the foreground;
  - type: `text [up|down N] [medium|strong|slant|tracked]` or `text.mono`;
  - spacing: `pad`, `space above|below`, `between`, `width`, each taking `gap`, `gap xN`, `gap /N` or `em`;
  - frame: `edge`, `border <side>`, `corner`, `lift`.

  Each role compiles to one class, `.r-<name>`, with dots turned into underscores.
- **Clauses** (`when <selection> : props`) style by the desk's selection language, for example `when kind:note : as=card`.
- **Themes** (`theme dark of calm`) may redefine tokens only. The painter selects one with `?theme=`.
- **Refusals** carry a line number and two escapes. The refused forms are: a hex colour outside a token, `px`, `text at N`, a theme that defines a role, a line without the spaced ` : `, and the removed word `present`.

**How a lens names a role.** A part says `role card`. `scene.py` validates the name against the `role` lines it reads from `desk-shell/style/calm.style` **on disk** at compile time, and refuses unknown roles with the list (`scene.py:75-80,174-175`). The painter applies `Style.roleClass(name)`.

**Limits a builder should know.**
- `Style.install` emits token variables and role classes only. Clauses take effect only through `Style.look`, which the shell exposes to apps (`core.js:99`). **The lens path never applies clauses.**
- The style is a file, not a world definition. It is not per-session, it has no events or undo, and adding a role means editing `calm.style`. The shell's style panel applies source in page memory only, and a reload loses it (`shell.js:39-46`).

## 5. `desk-shell/natives/prose.js`: state and remaining wiring

**State.** The file is 80 lines and complete as a component. The contract is `Natives.prose(el, node, host) -> {update(node), release()}`, with `host = {actor, send(n, line, why), publish(key, lines)}`.
- It edits plain text with a settle law: 2.5 s pause, blur or Ctrl+Enter. Escape discards the draft with no trace.
- It publishes eight lines describing itself: size, the rev it shows, caret or selection in character offsets, draft shape, settle time, fence state and its acts.
- It holds a draft across a repaint that moves the rev, and reports `!fence ... held, not lost`.

It is tested only against a simulated host (`design-studio/moss-what-the-contract-cost.md`). **Nothing loads it.** `lens.html` has no script tag for it, `lens.js` never calls `Natives`, and the compiler refuses both words. Verified:

```text
scene l-native  -> ERR line 2: a lens cannot say 'native prose'. ...
scene l-settle  -> ERR line 2: `on <click|edit|drag> do <desk command>`; got 'on settle do rewrite $id text="$value"'
```

**Wiring still needed, in order.**
1. **Observe channel** (`deskd.py:131`, `scene.py:407-409`). Accept a string or a list of strings per key, with about 120 characters per line and 12 lines per key, and have `to_text` print one `~` line each. Today a 40–110 character, 8-line publication is cut to one 60-character string. This is the blocker.
2. **Compiler** (`scene.py`). Admit `native <kind>` with a known-kinds list (today only `prose`), with unknown kinds refused by line number. Add `settle` to `GESTURES` (`scene.py:47`). Emit `node.native`.
3. **Painter** (`lens.js`, within the 27 remaining lines).
   - When `n.native` is set, create the handle once per `key` and keep it. Today a changed `rev` or `text` changes the node signature and rebuilds the element (`lens.js:30-41`), which would destroy the draft. A native element must survive by key and receive `update(n)`. Call `release()` when its key disappears.
   - `host.publish` feeds `report()`.
   - `host.send` posts with `observed.rev` set to **the rev the draft was based on**.
   - Add the `<script src="natives/prose.js">` tag to `lens.html`.
4. **Two defects in prose.js to fix during wiring.**
   - `settle()` sets `shown = n.rev` *before* sending (`prose.js:57-58`). If `host.send` uses `n.rev`, a draft held under a moved revision is sent as if observed at the new one, and passes the fence. That is the stale-pixels bug again. It should send the pre-settle `shown`.
   - `cmd()` replaces `"` with `'` (`prose.js:14`), changing the person's words, and escapes neither backslash nor newline. It should use the escape from `lens.js:64`.
   - Also unwritten: `?caret unknown` when the browser gives no selection.

## 6. What a builder hits first

These are in priority order, for a coding agent building a calendar today. Each item's evidence is from `doc-moss` unless it cites a source line.

1. **Selection refusals crash the process.** In `knife.parse_selection`, `from world import Refusal` at `knife.py:57` makes `Refusal` a local variable in the whole function. Every other `raise Refusal` in it (lines 87, 95, 101, 111, 114, 147, 151) therefore throws `UnboundLocalError`.
   - `find in:a03`, `find age<2` and a lens with `of tag:cal by=due` all end in a traceback.
   - In direct CLI mode the pickle is saved only at the end, so **every command in that invocation is lost**. In my run, events e5–e11 disappeared.
   - Through deskd, `/api/do` drops the connection, and `/api/scene` reports "the lens compiler failed".

   Every builder mistypes a selection, so this comes first.
2. **There is no time data type.**
   - Kinds are a closed list: `kind=event` gives `ERR kind= must be note, task, chat, image, doc, trial, surface or view` (`world.py:502`).
   - `due` is a date only: `due=2026-09-24T09:00` gives `ERR due= must be YYYY-MM-DD` (`world.py:545`).
   - Properties are strings with equality selection only. `find prop:start<10:00` says `nothing matches` without refusing, and `find due=2026-09-24` says `nothing`.
   - There are no times, durations or recurrence, and adding them needs Python.
3. **A lens cannot read properties.** `text "$title at $start"` gives `ERR line 3: no value $start` (`scene.py:48,100,179-181`). An event's time cannot be shown.
4. **Placement cannot follow a value.** `spread` places by repetition index (`scene.py:273-287`), and `spread x 0 step $due` is refused because only numeric props of the lens note are allowed. `at item` uses stored world geometry.
   - A day or hour grid would require writing geometry into the world, which the design reserves for durable position.
   - There is no arithmetic and no row source for days or hours. `of days` compiles and silently shows `0 of days` because it becomes a text search.
5. **Repeats cannot be ordered or headed.**
   - `of` takes world order. `table` has `by=`, but a lens has no equivalent, and trying one crashes (item 1).
   - A repeat part's own children print after its instances (`scene.py:353-354`), so `head : text "Wed · $n"` renders below the events.
6. **Gestures cannot carry meaning beyond pixels and one field.**
   - `$x $y` are pixels, so dragging to reschedule cannot map a position to a date.
   - `$value` exists only for editing existing text.
   - There is no `drop`, and there is no gesture that creates something from input.
   - Click-to-create needs its values written literally into the lens.
7. **Two UIs that do not meet.** The lens painter is a separate page. `shell.js`, `core.js` and `index.html` never reference `/api/scene` or lenses. A builder must choose between a bespoke shell app (full JavaScript, custom CSS, and the unfenced `look`-prefix pattern from §2) and a lens (a small grammar, on its own page, without clauses or natives).
8. **Text entry is whole-field and commits on blur.** The prose native that would fix this is not wired (§5).
9. **Style is outside the world.** New roles mean editing `calm.style` on disk, with no event or undo, shared by every session. Clauses do not reach lens paint.
10. **Persistence is fragile under load.**
    - The lock is abandoned after 30 s (deskd) or 60 s (CLI).
    - Every poll rewrites the whole pickle, and the painter and shell each poll every 1.5 s.
    - Unknown session names are created on first GET.
    - There is no authentication, session names are not sanitised, and pickles are loaded as trusted code.

## 7. Corrections to the Codex draft of Current Implementation

- **"The server exposes snapshots, events, compiled scenes and command execution."** This omits `POST /api/observe`. It also misses that GETs are not read-only: they rewrite the pickle and create unknown sessions.
- **"Server and direct CLI operations use a per-session file lock."** True, but a waiter proceeds without the lock after 30 s (deskd) or 60 s (CLI).
- **"Revision checks can refuse edits based on an actor's stale observations."** This needs the split in §2. Appearances refuse only when another actor touched them since the observation. Subjects refuse on any change. Only lens-painter gestures carry `observed`. The CLI relies on looks. **Shell apps bypass the fence with a `look` prefix.**
- **"The lens path ... can fall back to a previously successful definition."** True, but the fallback scene has no `def`, so the definition fence is skipped. It is also rebuilt without the lens's props, so a `spread step $prop` lens cannot fall back.
- **"Familiar kinds include notes, tasks, documents, images and chats."** This reads as an open set. It is closed: note, task, chat, image, doc, trial, surface and view.
- **"Both use the shared style language."** Only roles and tokens reach the lens painter. `when` clauses are applied only where a shell app calls `Style.look`.
- **"The shell's style editor currently changes browser-local styling."** More exactly, it changes page memory. Nothing is stored, and a reload loses it.
- **Missing.** The selection-refusal crash (§6.1), which loses a whole CLI batch.
- **Missing.** The CLI and deskd default actors differ (`jeff` and `alex`), and `!` lines write as another actor without any fence.
