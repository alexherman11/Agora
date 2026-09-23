# Current Implementation: the ten-minute orientation

*Lark, 23 September 2026. Every command below was run as written on a fresh session.*

The Dynamic Desk exists today as one research prototype, a desktop defined in text, at `C:/Projects/Agora4/research/text-desk-lab/notation/`. Paths below are relative to it. The desk is standard-library Python 3.12 and plain browser JavaScript, with no build step. Only `jeffx.py`, which is for model trials, imports the repo's `agora3` package.

## The shape in one paragraph

A **subject** (note, task, doc, chat, image) has a title, text, tags, due date, comments, props and a revision. An **appearance** places a subject on a **surface**, a nestable container laid out as `row`, `column` or `free`. Editing a subject changes every appearance of it, while moving one appearance moves only that one. Every change is an attributed **event** with an undo record, made only by a command line. A **lens** is a note tagged `lens` that describes a view. `scene.py` compiles it into a scene tree, which is printed as text and painted as pixels.

## 1. Run the desk

```sh
cd C:/Projects/Agora4/research/text-desk-lab/notation
printf 'help\nlook\n' | DESKD=off python explore.py mine --as me
```

`explore.py <session> --as <actor>` reads command lines from stdin and prints a receipt for each. A new session name gives you an empty desk (`f01`, a 1280x800 row), which is saved to `sessions/<session>.pickle`. `--reset` starts it over, `--dump` prints JSON and `--shape` prints it without ids.

- **Use your own session name.** `desktop`, `studio`, `bridge`, `lens` and `play2` are other people's live worlds.
- `DESKD=off` works on the file directly. Otherwise each line goes to a running `deskd` (`$DESKD`, default `http://127.0.0.1:8780`), with the file as fallback.
- If you leave out `--as`, you act as `jeff`, the owner.

## 2. Make, inspect, change, be refused, undo

Pipe these lines in from a file. A fresh desk gives the ids shown.

```text
do create f01 kind=note title="Garden" text="Choose seeds."
examine a03
do append a03 line="Water daily."
history
```

`examine` shows the thing's text, its place and **the verbs that apply to it right now**. `help <verb>` gives a verb's arguments and `verbs <id>` lists every form. A target can be an id, a quoted title or a selection such as `kind:task`, `tag:x`, `in:f04` or `-tag:lens` (`help selections`). Commands joined by `;` run in order and stop at the first refusal.

Now act as a second person:

```sh
printf 'do append a03 line="Hi"\nread a03\n' | DESKD=off python explore.py mine --as priya
printf 'do tag a03 add=garden\n'            | DESKD=off python explore.py mine --as me
printf 'do append a03 line="Hi"\n'          | DESKD=off python explore.py mine --as priya
printf 'read a03\ndo append a03 line="Hi"\n' | DESKD=off python explore.py mine --as priya
```

Priya is refused twice. The first time, she has not seen the note (`ERR you have not looked at a03 yet`). The second time, it changed after she read it (`stale: a03 changed since you last saw it`). After she reads it again, her append goes through as `e4`. This **seen fence** is for coordination, not access control. Looking first passes it, even in the same line (`look a03; do ...`), and your own changes never make you stale.

Undo works one target at a time:

```text
undo e3      -> ERR e3 is not the latest change to a03; e4 came after it
undo e4      -> ok e5: reverted e4
```

An undo is itself an event, and `history` marks the original `(undone)`. Undo refuses effects outside the desk. It is not fenced: `me` undid Priya's `e4` unseen, with only a printed notice.

Also try `export` (the commands that rebuild this desk), `help rules`, `help scripts`, `help views` and `worktree`.

## 3. Write a lens and read its scene

```text
do create f01 kind=task title="Buy seeds" due=2026-10-01
do create f01 kind=note title="board" tags=lens text="window : column, role window\n  heading : text \"My garden\", role heading\n  list : column, of kind:note|task,-tag:lens, each card\ncard : column, role card, on click do tag $item add=seen\n  name : text $title, role title\n  when : text $due, role meta, only when kind:task"
scene board
```

`\n` inside a quoted value is a line break. `scene board` prints each part with its words, its `[role]`, the thing it stands for, and the command each gesture sends (`click: do tag a03 add=seen`). The full grammar is the docstring of `scene.py`. Roles must exist in `desk-shell/style/calm.style`. A lens cannot name a colour or a size, and has no escape to HTML, CSS or script.

To see a refusal, run `do rewrite a07 text="window : column, role panel"` (the id `create` printed), then `scene board`. The compiler names the bad line, lists the valid roles and keeps printing the **last version that compiled**. `undo e8` restores the lens. A lens that has never compiled gets only the refusal.

### How it is painted

`python deskd.py 8780` serves `desk-shell/` and a JSON API on 127.0.0.1. Open `http://localhost:8780/lens.html?session=mine&as=me&lens=board`, and always pass `session`, because the painter defaults to the shared `lens` world.

- `lens.js` fetches `GET /api/scene?session=&as=&lens=` every 1.5 s. This calls the same `scene_for()` that the `scene` command uses, and the text beside the picture is the same printout. Layout and role become CSS classes built by `style/style.js` from `calm.style`. Nodes whose facts did not change keep their elements.
- A gesture is `POST /api/do` with `{session, as, line, observed: {item, rev, at, def}}`. `deskd` refuses it if the lens changed since it was painted, or if someone else changed the item (the seen fence).
- The painter reports clamps that cut and parts out of view to `POST /api/observe`. These show up in `scene` as `~` observations, not world facts.

You can check this path without a browser:

```sh
curl "http://127.0.0.1:8780/api/scene?session=mine&as=me&lens=board"
curl -X POST http://127.0.0.1:8780/api/do -d '{"session":"mine","as":"me","line":"look"}'
```

The windowed desktop (`index.html`, `shell.js`, `apps/*.js`) is a separate path over the same world, with hand-written JavaScript apps.

## 4. Which file for which change

| Change | Open | Notes |
|---|---|---|
| New verb | `moo.py` | An `@verb(name, kinds, doc, args, example)` function. It appears in `help`, `verbs` and `examine` for those kinds. Mutate through `world.apply(...)`, or record `w._event(verb, target, args, undo)` with an undo record `World.undo` knows. |
| New primitive or undo kind | `world.py` | `World.apply` and `World.undo`. |
| New desk command (not a verb) | `desk_knife.py` | The `if cmd == "..."` chain beside `scene` and `rows`, and the topic-help dictionary below it. Main `help` is `HELP` in `desk.py`, patched by string replacement in `desk_moo.py` and `desk_knife.py`. |
| New lens word | `scene.py`, then `desk-shell/lens.js` | `parse()` admits it, `build()` builds it and `to_text()` prints it. Add a case to `test_scene.py`. The painter has a 150-line budget and uses 123. |
| New style role | `desk-shell/style/calm.style` | A `role name : ...` line built from tokens. `scene.py` rereads it on every compile, so no restart is needed. |
| Painter change | `desk-shell/lens.js`, `lens.html` | `lens.html` holds layout mechanics only, never a colour or size. |
| Server endpoint | `deskd.py` | A branch in `Handler.do_GET` or `do_POST`, inside `Session(name, actor)`, which locks, loads and saves. |

`deskd` imports Python once, so **restart it after any Python change**. `DESKD=off` runs load fresh code. `python test_scene.py` runs the four lens-admission tests. `desk-shell/OWNERS.md` lists who owns each browser file.

## 5. What not to rely on

- **Persistence.** A session is one pickle of live Python objects, rewritten whole on every save. There is no separate journal, no crash-safe write and no format version. Code tolerates old pickles through `getattr(..., None)`. Every `deskd` request rewrites the pickle, reads included, and a GET for a mistyped session creates it empty. `export` keeps the content but not the history or undo.
- **Identity.** `--as` and `"as"` are labels the caller supplies. There is no authentication or permission model. CLI lines that start with `!` (`!priya append a03 line=...`) write as any actor and skip the server.
- **Concurrency.** A per-session lock file covers load, execute and save, and is taken over after 60 s. Writers take turns. Nothing merges their work.
- **The fence.** Stale-revision refusals prevent accidents but give no guarantee. `undo` does not check what you have seen. A scene that falls back to the last lens that compiled carries no `def`, so gestures painted from it skip the lens-revision check.
- **Experiment.** The lens grammar is v0 and still contested. `desk-shell/natives/` and `research/shared-visual-desk/` are not wired into the painter. There are no general facets, packages, collaborative text editing or a resident JEFF runtime. `harness.py`, `run.py` and `tasks.py` are model-trial fixtures.

## Read next

1. `scene.py` docstring: the whole lens grammar, and why it refuses what it refuses.
2. `world.py`: the substrate. Subjects, appearances, events, `apply` and `undo`.
3. `moo.py`: how a verb is declared, inherited by kind and composed from primitives.
4. `desk_knife.py`: command dispatch, rules, scripts and the help text.
5. `deskd.py`: the whole server and the gesture fence in 184 lines.
6. `desk-shell/lens.js`: the generic painter, and the line budget that keeps it generic.
