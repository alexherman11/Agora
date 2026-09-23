# Current Implementation

**Reviewed 23 September 2026 · the text desk**

The Dynamic Desk exists today as one prototype: a desk defined entirely in text. A small world of things and placements, one command language that reads and changes it, and a lens compiler that turns short text definitions into scenes that an agent reads and a browser paints. It is independent of the earlier native runtime described in [[Previous Work]].

Source: `C:/Projects/Agora4/research/text-desk-lab/notation/`. Paths below are relative to it. It is standard-library Python 3.12 and plain browser JavaScript with no build step. This document describes the working tree on the date above. Its claims were checked against source and in scratch sessions by six reviewers; the drafts they wrote are in `design-studio/docs/`.

## Foundation and experiment

Everything here is prototype code. The left column is what later work should preserve; the right column is mechanism that may be replaced.

| Keep and build on | Still an experiment |
|---|---|
| Subject, appearance and surface are distinct things | Pickle persistence and file locks |
| Every change is a command line that records an undoable event | Worktree merge by replaying command lines |
| Look before you act: a change is refused if you never looked, or if what you saw is stale | Rules and scripts stored outside the event log |
| Verbs and selections are one language shared by every command | The lens vocabulary beyond its core words |
| One scene, two printers: text and pixels come from the same tree | The hand-written application shell |
| A lens is a note in the world, not code | `spread`, natives, the desktop made of lenses |

## Running it

```sh
cd C:/Projects/Agora4/research/text-desk-lab/notation
printf 'help\nlook\n' | DESKD=off python explore.py mine --as me
python deskd.py 8780        # serves desk-shell/ and the JSON API on 127.0.0.1
python test_scene.py        # the four lens-admission tests
```

- `explore.py <session> --as <actor>` reads command lines from stdin and prints a receipt for each. A new session name is an empty desk. `desktop`, `studio`, `bridge`, `lens` and `play2` are other people's live worlds; use your own name.
- Without `DESKD=off`, each line is posted to a running `deskd` (default `http://127.0.0.1:8780`) and the file is the fallback. `deskd` imports Python once: restart it after any Python change.
- The default actor is `jeff` on the CLI and `alex` on the server. Actor names are labels supplied by the caller.
- Browser: `http://localhost:8780/lens.html?session=mine&as=me&lens=<lens>` for a lens, `/?session=mine&as=me` for the windowed shell.

## The world

| Concept | In code (`world.py`) |
|---|---|
| **Subject** `s..` | Content: `kind`, `title`, `text`, `tags`, `due`, `comments`, `props`, `rev`. Kinds are a closed list: note, task, chat, image, doc, trial, surface, view. Props are string values. |
| **Appearance** `a..` | One placement of a subject: parent surface, `x y w h`, `z`, `folded`, `rev`. A subject may appear in several places. |
| **Surface** `f..` | A container with layout `free`, `column` or `row`. A **view** is a surface whose contents are a selection, re-evaluated at every look. |
| **Link** `l..` | A typed edge between subjects: `blocks`, `refers`, `answers`, `part-of`. |
| **Event** `e..` | `verb target args undo by at`, plus `cmd`, `via`, `cause` and `undone`. Revisions live on things, not on events. |

Editing a subject changes every appearance of it. Moving or removing one appearance touches only that appearance.

**Observed revisions.** The desk remembers, per actor, the revision it last showed them of each thing. A change is refused in two cases: `you have not looked at a04 yet`, and `stale: a04 changed since you last saw it`, which names the event. Command lines carry no revision numbers. Your own changes never make you stale. Rules act without the fence. The fence coordinates honest actors; it is not access control.

**Undo.** `undo eN` reverts an event and records the reversal as a new event. A composed verb is undone as a whole, and a rule's consequences are undone with their cause. Only the latest change to a thing can be undone. An event marked external (`launch`) cannot be. There is no redo, and undo is not fenced.

## One language

`explore.py` on stdin, `POST /api/do` on the server and a gesture in the painter all carry the same kind of line. Several commands may be joined with `;`; they run in order and stop at the first refusal, and earlier steps are not rolled back.

| Family | Commands |
|---|---|
| Reading | `look [id] [:1-:4]`, `read`, `examine`, `where`, `verbs`, `pivot`, `find`, `table`, `compare`, `history`, `why`, `rows`, `scene`, `export`, `help` |
| Changing | `do <verb> <target> k=v`, `undo`; pair verbs `swap`, `beside`, `match` |
| Defining | `rule`, `script` / `run`, `set` (handles), `clock` |
| Branching | `worktree fork` / `diff` / `merge` |

`examine` lists only the verbs that apply to a thing right now; `help <verb>` gives arguments and one example. The general verbs are `move place resize raise lower remove fold unfold create group tile untile rename sort append rewrite retitle check comment resolve tag prop due link unlink launch`. Primitives live in `World.apply`; a new primitive still needs Python.

**Selections are the shared noun phrase.** The same grammar names a verb's target, a `find`, a view's `query=`, a rule's trigger and a lens's `of` and `only when`:

```text
kind:note|task  tag:x  in:f04  title:agenda  ?word+word  prop:status=done
comments:open  links:a04  due<2026-09-20  age>7  hidden  also:a18  a20,a22  -tag:done
```

Terms joined with commas are ANDed. A target may also be one id, a unique quoted title, or a handle such as `$item` (the last created thing) or `$new` (the last created surface). An unknown term is refused with the list of known terms.

**Rules, scripts, views.**
- `rule when <selection> do <verb> …` fires once on each thing that enters the selection (`now=1` includes current matches). `rule on <verb> [by=<actor>] do …` fires on each such event. Cascades stop after three passes. `why <id>` shows which events placed a thing and which rule would act on it next.
- `script <name> = <cmd>; <cmd>` with `$1 $2 $today`; `run <name> args`. A rule may run a script.
- `do create <surface> kind=view title=X query=<selection>` makes a view; with `cols=` it is a table at every look.

Rule, script and clock definitions are desk attributes, not events: they have no author, do not appear in `history`, and cannot be undone. They are not validated when defined. A lens, by contrast, is an ordinary note. Definitions are not yet uniform.

**Worktrees.** `worktree fork <name>` copies the session into `<session>@<name>` with a journal of the command lines made there. `merge` replays the journal into the base, remaps created ids, signs each command by its author, and is all or nothing: a command whose target changed in the base since the fork, by anyone, refuses the whole merge. A worktree stays open after merging.

## Lenses: one scene, two printers

```text
world + lens note  ->  scene.build  ->  scene tree  ->  to_text   (scene <lens>: what an agent reads)
                                                   ->  lens.js   (lens.html: what a person sees)
```

A **lens** is a subject tagged `lens` whose text is the definition. It is created, rewritten, undone, forked and merged like any note. Both printers read one tree, so screen and text cannot disagree about what is there, what it says, where it sits, or what a gesture sends. The `scene.py` docstring is the grammar reference. Each line reads `name : prop, prop`; indentation is containment; the first unindented part is the root.

| Word | Meaning |
|---|---|
| `column` `row` `free` | Layout, the surfaces' own three words |
| `role <name>` | Look, by a role from `calm.style`; an unknown role is refused with the list |
| `text <template>` | Words; `$title $text $kind $due $tags $id $item $it $n` and row fields; quote to keep commas and hashes |
| `clamp <N>` | At most N lines of text, or N repeats; both printers say how many are left |
| `of <selection>` + `each <part>` | Repeat over a selection or a row source: `sections:<id>`, `comments:<id>`, `actors`, `events`, `worktrees` (`rows <source>` prints the same rows) |
| `over $tags` | Repeat over a list field; `$it` is each value |
| `at item` | The appearance's own world geometry; only under a `free` parent |
| `spread x <a> step <n\|$prop> to <max>` | Computed placement by index; printed as `(spread, not its place in the world)`, never written back |
| `lens <name>` | Place another lens; a lens may not contain itself |
| `only when <selection>` | The part exists only on a match; the text prints the absence |
| `on click\|edit\|drag do <command>` | A gesture is a desk command; the painter fills `$x $y` or `$value` |

There is no escape to HTML, CSS, script, arithmetic or conditionals. Anything else is refused with its line number. A scene has a budget of 1500 nodes.

**Bindings.** A gesture carries what was observed: the item's revision, the event index the scene was built at, and the lens's id and revision. The server refuses a gesture painted under an older lens revision, and sets the actor's seen revision to the painted one so the ordinary fence judges the item. The painter never looks again on the person's behalf.

**Facts and observations.** A placed part carries what the world knows, such as `= offscreen-part`. The painter reports what only it knows through `/api/observe`: viewport, `cut by the clamp`, `contents overflow the box`, `out of view`. The text printer shows these per viewer as `~` lines. They are observations, never events.

**Resilience.** A lens that stops compiling keeps showing its last version that did, and says so first. The painter keeps unchanged elements by key, so a reader's selection survives another person's act. `lens.js` is 123 lines against a 150-line budget written in its header; it knows no app, kind, colour or size.

**Style.** `desk-shell/style/calm.style` defines tokens (the only place a colour or number appears), roles built from tokens, `when <selection>` clauses and themes. A lens names roles; the style never names a lens. The style is a file outside the world: no desk command changes it, and it has no events or undo.

**How the language grows.** From the design studio, argued positions rather than checks: a new word must be sayable in the desk's language; if the world or the style can carry something, the lens refuses it; a word must print as text, shorter than what it paints; a gesture exists only if the painter can do it; at the painter's line ceiling a word must be removed to add one.

A desktop of three lenses (`notes`, `editor`, `together`) exists in session `lens` as the ten-line lens `desktop`: 200 scene nodes, 200 painted. What stops it replacing the shell: no viewer identity in a lens, no lens chosen by the kind of thing shown, no stacking or focus, no resize gesture, no place for toggles.

## Processes and state

| Endpoint (`deskd.py`) | What it does |
|---|---|
| `GET /api/snapshot?session&as` | The world as JSON plus the actor's outline; rendering does not count as looking |
| `GET /api/scene?session&as&lens` | `{scene, text}` or `{refused}` |
| `GET /api/events?session&since` | Events after an index; the painter and shell poll every 1.5 s |
| `POST /api/do` | `{session, as, line, observed?}` returns `{text, error, created, events}`; the first `ERR` line becomes `error` |
| `POST /api/observe` | Painter reports, kept per actor; never refuses |
| anything else | A static file from `desk-shell/` |

A session is one file, `sessions/<name>.pickle`, holding the whole Python desk: world, rules, scripts, per-actor state, observations. Every server request, reads included, loads it under `sessions/<name>.lock`, acts, and rewrites it. A GET for an unknown session creates it. The lock is advisory: a waiter deletes a lock older than 60 s and proceeds without one after 30 s on the server or 60 s on the CLI. The CLI saves once at the end of an invocation.

## The browser

Two paths paint the same world.

- **Windowed shell** (`index.html`, `shell.js`, `core.js`, `apps/`): a dock, draggable windows, three hand-written apps (Notes, Editor, Together). Each app implements `text(ctx)`, what a text-only inhabitant reads for that window. Apps prefix `look <id>;` to their commands, so their gestures are not fenced against what was on screen. The style panel edits page memory only.
- **Lens painter** (`lens.html`, `lens.js`): the generic painter described above, on its own page. It applies roles and tokens; `when` clauses reach only the shell.

`desk-shell/natives/prose.js` is an 80-line prose editor with a settle law, written against a host contract (`{actor, send, publish}`) but loaded nowhere; the compiler refuses `native` and `settle`. `desk-shell/OWNERS.md` names one owner per file.

## Code map

| File | Lines | Responsibility |
|---|---:|---|
| `world.py` | 821 | Subjects, appearances, surfaces, links, comments, geometry, events, `apply`, `undo`, the revision fence |
| `desk.py` | 892 | Outline notation, the seen fence, `;` batching, reading commands, `undo`, `do` |
| `desk_moo.py` | 248 | Verbs by kind from the registry, `examine`, `help <verb>`, `verbs` |
| `desk_knife.py` | 1171 | The live desk: selections as targets, pair verbs, rules, scripts, clock, handles, tables, views, `export`, `rows`, `scene`, help topics |
| `moo.py` | 534 | The verb registry: `@verb` declarations, kind inheritance, composed verbs, synonyms |
| `knife.py` | 236 | The selection language and pair verbs |
| `scene.py` | 452 | Lens grammar, compiler, text printer, row sources |
| `worktree.py` | 171 | Fork, journal, diff, all-or-nothing replay merge |
| `explore.py` | 171 | CLI: forward to deskd or run under the lock; per-actor state; `!actor` injection |
| `deskd.py` | 184 | HTTP server and the gesture fence |
| `harness.py`, `run.py`, `tasks.py`, `jeffx.py` | 1083 | Model trials as desk things; `jeffx.py` imports a transport from `C:/Projects/Agora/local/…`, outside this repo |
| `test_scene.py` | 51 | Four lens-admission tests |
| `desk-shell/lens.js`, `lens.html` | 154 | The generic painter |
| `desk-shell/style/calm.style`, `style.js` | 391 | The style language and its compiler to CSS |
| `desk-shell/shell.js`, `core.js`, `apps/*.js` | 1921 | The windowed shell and its three apps |
| `desk-shell/checks/` | 1823 | Iris's measured browser checks and results; Rook's defect list |

Which file for which change: a new verb goes in `moo.py` (and `world.py` if it needs a new primitive or undo kind); a new command in `desk_knife.py`; a new lens word in `scene.py`, then `lens.js`, then `test_scene.py`; a new role in `calm.style`, reread on every compile; a new endpoint in `deskd.py` inside `Session`.

## Evidence and limits

**Automated checks.** `test_scene.py` runs four tests, all passing today, covering lens admission only. Nothing automated covers `world.py`, verbs, the fence, undo, worktrees or the server. The first text desk's sixteen tests (now under `research/archive/text-desk-lab-v1/`) exercise an earlier desk, not this code. `desk-shell/checks/` needs a live page and a running server. Model trials (`run.py`) depend on a transport and a Codex binary outside this repository.

**Verified live, 18 September.** The lens painter painted 38 of 38 scene nodes and 200 of 200 for the desktop lens, with declared boxes exact to the pixel and every type size on the ramp. A reader's selection survived another actor's act. Rook reproduced nineteen shell and app defects, listed in `desk-shell/checks/rook-bugs.md`; most remain open or unverified.

**Verified in scratch sessions, 23 September.** The two fence refusals; the lens-revision refusal; undo limited to the latest change; a `;` batch keeping earlier steps after a later refusal; a `script` definition making no event so that a bare `undo` reverted an older change; export output failing to replay because titles become ambiguous; a merge refused for a change by the same author; `!actor` lines signing most verbs as the session's own actor.

**Fixed today.** A function-local import in `knife.py` turned seven selection refusals into crashes, and a CLI crash loses the whole invocation. Removed; the refusals now print.

**Open defects a builder will meet.**
- A scene served from the last-good fallback carries no lens revision, so gestures from it skip the lens fence, and it is rebuilt without the lens's props.
- `export` does not replay: repeated placements make titles ambiguous, and props on unplaced subjects are dropped silently.
- `!actor` injection signs events as the session's actor for every verb except `prop`, so `rule on … by=` never fires for them.
- `help` omits the topics `scene`, `worktree`, `table`, `find`, `read` and `compare`, and the terms `comments:` and `links:`.
- The shell's Notes app rewrites `"` to `'` in titles, and Escape on a new-note draft creates the note.

**Persistence and safety.** The pickle is the database, rewritten in place with no journal, no atomic write and no format version; loading it executes code, so a session file must be trusted. The server binds to localhost and checks no origin or token. Fences coordinate; nothing authenticates.

## What a builder hits first

In priority order, from an attempt to describe a calendar in this framework.

1. **No time type.** Kinds are a closed list, `due` is a date only, and props are strings compared by equality. Adding any of these needs Python.
2. **A lens cannot read props.** `text $start` is refused; only the nine built-in names and row fields exist.
3. **Placement cannot follow a value.** `spread` places by index; there is no arithmetic and no row source for days or hours.
4. **Repeats cannot be ordered or headed.** `of` takes world order, and a repeat's own children print after its instances.
5. **Gestures carry pixels and one field.** Nothing maps a position to a date, and no gesture creates a thing from input.
6. **Two interfaces that do not meet.** The windowed shell and the lens painter are separate pages; a builder chooses bespoke JavaScript or a small grammar.
7. **Text entry is whole-field and commits on blur** until the prose native is wired.
8. **Definitions are not uniform.** Lenses are notes; rules, scripts, clock and style are not, so they have no history, undo or fork.
9. **No durable store, no identity, no tests** for the command layer.

## Related documents

- [[Agora]]: purpose and experience.
- [[Dynamic Desk]]: the current design and its open questions.
- [[Previous Work]]: earlier architectures and what they taught.
