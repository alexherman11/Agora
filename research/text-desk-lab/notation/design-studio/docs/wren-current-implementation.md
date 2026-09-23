# Current Implementation

**Reviewed 23 September 2026 · the text-desk notation lab · alternative draft (Wren)**

A desk defined entirely in text: a small world of things and placements, one command language to read and change it, and a lens compiler that turns short text definitions into scenes an agent and a browser both read. It is independent of the native runtime in [[Previous Work]].

Source: `C:/Projects/Agora4/research/text-desk-lab/notation/` (paths below are relative). Claims were checked against source and in a scratch session.

## Foundation and experiment

| Keep and build on (the contract) | Still an experiment (the mechanism) |
|---|---|
| Subject / appearance / surface separation | Pickle persistence, file locks |
| Every change is a desk command line that records an undoable event | Worktree merge by replaying commands |
| Look-before-act fencing on observed revisions | Rules and scripts stored outside the event log |
| Verbs and selections as one language | The lens vocabulary beyond its core words |
| One scene, two printers | `spread`, natives, the desktop lens |
| A lens is a world note, not code | The hand-written app shell (`index.html`, `apps/`) |

All of it is prototype code; the left column is what later work should preserve.

## The world

| Concept | What it is in code |
|---|---|
| **Subject** (`s..`) | Content: `kind`, `title`, `text`, `tags`, `due`, `comments`, `props`, `rev`. Kinds include note, task, chat, doc. |
| **Appearance** (`a..`) | One placement of a subject: parent surface, `x y w h`, `z`, `folded`, `rev`. A subject may appear many times. |
| **Surface** (`f..`) | A container with layout `free`, `column` or `row`. A *view* is a surface with layout `view` whose contents are a selection, re-evaluated at every look. |
| **Link** (`l..`) | A typed edge between subjects: `blocks`, `refers`, `answers`, `part-of`. |
| **Event** (`e..`) | `id verb target args undo by at` plus optional `day`, `changed`, `via`, `cause`, `undone`. |

Editing a subject changes every appearance; moving or removing one appearance touches only that appearance.

**Observed revisions.** Every subject and node has a `rev`. The desk remembers, for each actor, the revision it last *showed* that actor (`seen`), which items they have open, and how far through the event log they have read. `do` is refused in two cases:

- `you have not looked at a04 yet` means the actor never looked at the target.
- `stale: a04 changed since you last saw it` means another actor changed it after the look., naming the event.

People and agents act on what they *saw*; the fence turns a stale picture into a refusal instead of a silent overwrite. Command lines carry no revision numbers. Rules bypass the fence. It coordinates work; it is not access control, and actor names are unauthenticated.

**Undo.** `undo eN` reverts an event; bare `undo`, the caller's latest.

- A composed verb (`sort`, a selection move, `group`) is undone as a whole.
- Undoing a command also undoes the rule actions it caused.
- Undo is linear per target: `e7 is not the latest change to a08; e8 came after it`.
- An event marked `external` (`do launch`) cannot be undone.
- Undo appends an event; history is never erased.

## One language: verbs and selections

`explore.py <session> --as <actor>` reads command lines on stdin; `deskd.py` accepts the same lines at `POST /api/do`. A gesture, a terminal line and an agent tool call are one kind of thing.

| Family | Commands |
|---|---|
| Reading | `look [id] [:1-:4]`, `read`, `examine`, `where`, `verbs`, `pivot`, `find`, `history`, `why`, `table` |
| Changing | `do <verb> <target> k=v`, `undo`; pair verbs `swap`, `beside`, `match` |
| Defining | `rule`, `script`/`run`, `set` (handles), `clock` |
| Sessions | `worktree fork / diff / merge`, `export` |
| Lenses | `scene <lens>`, `rows <source>` |

`examine` lists only the verbs that apply right now: a checklist offers `check`, an open comment `resolve`.

**Selections are the shared noun phrase.** The same grammar selects a verb's target, `find`, a view's `query=`, a rule's trigger, a lens's `of` and `only when`:

```text
kind:note|task  tag:x  in:f04  title:agenda  ?word+word  prop:status=done
due<2026-09-20  age>7  hidden  also:a18  a20,a22  -tag:done     (commas mean AND)
```

Primitive verbs live in `world.apply`, composed ones in `moo.py` and `knife.py`; a new primitive still needs Python.

## Rules and scripts

- `rule when <selection> do <verb> …` fires once on each thing that *enters* the selection. Add `now=1` to include things that match already.
- `rule on <verb> [by=<actor>] do …` fires on each matching event.
- Rules cascade at most three passes. Their actions are tagged `via rule rN` and print as `~` lines after the receipt.
- `script <name> = <commands; …>` with `$1 $2 $today`; a rule may `run` a script.

Rule and script definitions are Desk attributes, not events: not undoable, not fenced (`export` reproduces them). A lens is a world note. Definitions are not yet uniform.

## Persistence and the server

A session is one pickle, `sessions/<name>.pickle`: world, rules, scripts, per-actor state. The CLI forwards to `deskd` (port 8780) when it answers, else loads directly; both take `sessions/<name>.lock`, broken as abandoned after 60 s.

| Endpoint | What it serves |
|---|---|
| `GET /api/snapshot` | The world plus the actor's outline |
| `GET /api/events` | Events after an index |
| `GET /api/scene` | A compiled lens |
| `POST /api/do` | Command lines |
| `POST /api/observe` | Painter reports |
| Static files | `desk-shell/` |

Saves rewrite the pickle: no separate journal, no crash safety.

## Lenses: one scene, two printers

```text
world + lens note  ->  scene.build  ->  scene tree  ->  to_text   (scene <lens>: what an agent reads)
                                                   ->  lens.js   (lens.html: what a person sees)
```

A **lens** is a subject tagged `lens` whose text is the definition, so it is edited, undone, forked and merged like any note. Both printers read one tree, so screen and text cannot disagree about what is there, what it says, where it sits, or what a gesture sends. The `scene.py` docstring is the grammar reference.

A line reads `name : prop, prop`. Indentation is containment. The first unindented part is the root.

| Word | Meaning |
|---|---|
| `column` `row` `free` | Layout (the surfaces' own three words) |
| `role <name>` | Look by role from `calm.style`; an unknown role is refused |
| `text <template>` | Words; `$title $text $kind $due $tags $id $item $it $n` and row fields |
| `clamp <N>` | At most N lines, or N repeats (`N more not shown … find …`) |
| `of <selection>` / `over $tags` + `each <part>` | Repeat over a selection, a row source (`sections:<id> comments:<id> actors events worktrees`), or a list field |
| `at item` | The appearance's own world geometry; only under a `free` parent |
| `lens <name>` | Place another lens; a lens that contains itself is refused with the cycle named |
| `only when <selection>` | The part exists only on a match; the text prints `(absent: not …)` |
| `spread x <a> step <n\|$prop> to <max>` | Computed placement; prints `(spread, not its place in the world)` |
| `on click\|edit\|drag do <command>` | A gesture is a desk command; the painter fills `$x $y` or `$value` |

No escape to HTML, CSS, script, arithmetic or `if/else`; anything else is refused with a line number; 1500-node budget.

**Bindings.** Each gesture carries four facts: the item's `rev`, the world position the scene was painted at, and the lens's id and revision. `deskd` refuses a gesture painted under an older lens revision. It also sets the actor's `seen` to the painted `rev`, so the ordinary fence refuses stale pixels.

**Facts and observations.** A placed part carries world facts, such as `= offscreen-part`. The painter reports what only it knows through `/api/observe`: viewport, `cut by the clamp`, `contents overflow the box`, `out of view`. The text printer shows these per viewer as `~` lines. They are observations, never events.

**Resilience.** A lens that stops compiling keeps showing its last good version and says so first. The painter reuses unchanged elements by key, so a reader's selection survives another's act. `lens.js` is 123 lines against a 150-line budget in its header, and knows no app, kind, colour or size.

**Style.** `desk-shell/style/calm.style` (`token`, `role`, `when <selection>`, `theme`) is a file outside the world; no desk command changes it. A lens names roles; the style never names a lens.

## How the lens language grows

From `wren-11`, `wren-12` and `THE-MISSING-PIECE.md`. Argued positions, not checks; only the budget is written into code (the painter's header).

| Rule | Test |
|---|---|
| **(a) Displacement** | If the world or the style can carry it, the lens refuses it |
| **(b) Print ≤ paint** | A word must print as text, shorter than what it paints; a gesture exists only if the painter can do it (`drop` was removed for this) |
| **(c) Budget** | 150 painter lines; at the ceiling a word must be removed to add one |
| **(d) No third category** | No screen object whose kind a person cannot see; `spread` fails this and remains contested |

## A desktop made of lenses

Session `lens`, note `desktop`, ten lines:

```text
desk : column, role desk
  bar : row, role bar
    apps : text a desktop made of lenses · $n installed, role meta, of tag:lens, each app
  stage : row
    left : column, lens notes
    right : column
      top : column, lens editor
      bottom : column, lens together
app : text $title, role dockitem
```

`scene desktop` prints a bar listing the four lenses, then `notes` (draggable cards at world positions, renamable titles), `editor` (documents by section, each paragraph editable via `rewrite … section=`) and `together` (actors, worktrees, events from row sources), with a painter's `~` reports inline.

What stops it replacing `shell.js` (359 lines): no `$me` (lenses hard-code places such as `in:Canvas`), no lens chosen by the kind of thing shown, no stacking or focus, no `resize` gesture, nowhere for toggles like theme, and a shell made only of lenses cannot report that lenses are broken. The main shell (`index.html`) mounts no lenses; its apps are hand-written JavaScript with a hand-written `text(ctx)`.

## Code map

| Area | Files |
|---|---|
| World, verbs, events, undo | `world.py` |
| Reading, fencing, `do` | `desk.py` → `desk_moo.py` (verb registry, `examine`) → `desk_knife.py` (selections, rules, scripts, views, `scene`) |
| Composed verbs | `moo.py`, `knife.py` |
| CLI, server, worktrees | `explore.py`, `deskd.py`, `worktree.py` |
| Lens compiler | `scene.py`, `test_scene.py` (4 tests) |
| Painter, style | `desk-shell/lens.js`, `lens.html`, `style/` |
| App shell | `desk-shell/core.js`, `shell.js`, `apps/` |
| Model trials | `harness.py`, `run.py`, `tasks.py`, `jeffx.py` (imports `agora3.jeff` from `C:/Projects/Agora/local/…`) |

## Not yet built

Viewer identity in lenses; lens-for-a-thing; a mounted native (`desk-shell/natives/prose.js` is unmounted); operation identity and input schemas for gestures; definitions as events; typed properties (props are strings); incremental scenes (whole rebuild on a 1.5 s poll); a durable journal; authenticated actors; tests for world, fence and undo.

## Related documents

- [[Agora]]: purpose and experience.
- [[Dynamic Desk]]: the design and its open questions.
- [[Previous Work]]: earlier architectures.
