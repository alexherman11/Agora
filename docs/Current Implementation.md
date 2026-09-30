# Current Implementation

**Checked against the code on 29 September 2026 · the text desk**

The Dynamic Desk exists today as one prototype, the text desk, defined entirely in text:
- a small world of things and placements;
- one command language that reads and changes it;
- world verbs, which anyone makes as notes;
- a staged lens compiler that turns short text definitions into scenes, which an agent reads and a browser paints.

Around the desk:
- the **house** runs resident agents that live in the world;
- **workers** change the code in git worktrees, and the house lands their work after health checks;
- the **keeper** keeps it all running on the current code.

It is independent of the earlier native runtime described in [[Previous Work]].

Source: `C:/Projects/Agora4/research/text-desk-lab/notation/`. Paths below are relative to it. It is standard-library Python 3.12 and plain browser JavaScript, with no build step. This document describes the working tree on the date above.

Claims are labelled by how they were checked: **read** (from source, with file and line) or **ran** (in scratch worlds). The desk is the source of this document: the Handbook binder *How the desk is built*, exported by `export_docs.py`.

**Keep this current.** It describes the desk as it is now, not how it got there:
- A change that alters anything described here updates this document in the same change:
  1. edit the section in the Handbook binder;
  2. run `python export_docs.py`;
  3. commit the export with the code.
- A worker does this before it sets `commission=ready`. A defect fixed comes off the list under Evidence; a defect found goes on it.
- When a section can't be kept exact, say so in it ("not re-checked since …") rather than leaving it to drift.
- No change history here: git and the event log keep that. The date above says when the whole document was last checked against the code; recheck it whole when a stage of the project closes.

## Foundation and experiment

Everything here is prototype code. The left column is what later work should preserve; the right column is mechanism that may be replaced.

| Keep and build on | Still an experiment |
|---|---|
| Subject, appearance and surface are distinct things | Pickle persistence and file locks |
| Every change is a command line that records an undoable event | Worktree merge by replaying command lines |
| Look before you act, judged per thing and aspect | Rules, scripts and the clock stored outside the event log |
| Verbs and selections are one language shared by every command | World verbs as text macros (no expression language yet) |
| A lens, a style and a world verb are notes in the world, not code | The lens vocabulary beyond its core words; the hand-written windowed shell |
| One scene, two printers: text and pixels come from the same tree | The house's relay (tool-less residents whose `>` lines are run for them) |
| Code changes go through a worker, a worktree and health checks, and can be reverted | Landing without human review, on standing trust |

## Running it

```sh
cd C:/Projects/Agora4/research/text-desk-lab/notation
printf 'help\nlook\n' | DESKD=off python explore.py mine --as me
python deskd.py 8780            # serves desk-shell/ and the JSON API on 127.0.0.1
python keeper.py frontier --port 8794   # deskd and the house together, on the current code
python health.py frontier       # the checks a landing must pass
python test_scene.py            # 21 tests of lenses, gestures and the fence
```

**The CLI.** `explore.py <session> --as <actor>` reads command lines from stdin and prints a receipt for each.
- Blank lines and `#` lines are skipped.
- A new session name is an empty desk.
- A refused line stops the rest: `stopped: N later line(s) not run because this one was refused`.
- Flags:
  - `--window <name>` gives one actor a second reader;
  - `--reset`;
  - `--dump` prints a JSON snapshot, with rules, scripts and the clock;
  - `--shape` prints the desk without ids.
- The default actor is `jeff`. Actor names are lowercased labels that the caller supplies; nothing authenticates them.

**Through deskd.** Without `DESKD=off`, each line is posted to a running deskd (default `http://127.0.0.1:8780`), and the file is the fallback.
- Lines stay local (under the lock) when `--window` is given or when any line starts with `!`.
- Through deskd, a refusal does not stop later lines. If deskd stops answering mid-run, the rest are not applied.
- deskd imports Python once. Under the keeper it restarts whenever git HEAD moves; otherwise restart it after any Python change.

**Worlds.**
- The shared world is `frontier`. Private worlds are `frontier-<name>`, and worktree forks are `<world>@<name>`.
- `desktop`, `studio`, `bridge`, `lens` and `play2` are older worlds from earlier rounds.
- 34 pickles under `sessions/` are tracked in git.

**Browser.**
- A lens: `http://localhost:<port>/lens.html?session=<s>&as=<actor>&lens=<lens>`.
  - Defaults: session `lens`, as `alex`, lens `notes`.
  - `?side=scene` shows the scene text in the right pane, `?inspect=0` shows neither pane, `?theme=<name>` picks a theme, and `?share=attention` shares the viewer's attention.
- The windowed shell: `/?session=<s>&as=<actor>`. Defaults: session `desktop`, as `alex`.

## The world

| Concept | In code (`world.py`) |
|---|---|
| **Subject** `s..` | Content: `id kind title text tags due comments props rev`. `create kind=` takes a closed list: note, task, chat, image, doc, trial, surface, view. The last two make surfaces, not subjects. Any other `k=v` at create becomes a prop (not on surfaces). Props are strings. |
| **Appearance** `a..` | One placement of a subject: `parent x y w h z folded rev`, and optional `props` (`prop … at=appearance`). With `DESK_GEOMETRY=choices`, also `order` and `share`. A subject may appear in several places. |
| **Surface** `f..` | A container with layout `free`, `column` or `row`, and props. A **view** is a surface with `layout: view`, a `query` and optional `cols by desc`, re-evaluated at every look. Surface prop `extent=WxH` bounds `spills-parent` on a free surface. |
| **Link** `l..` | A typed edge between subjects: `blocks`, `refers` (the default), `answers`, `part-of`. Self-links, duplicates and links to surfaces are refused. |
| **Comment** `c..` | `{id, by, text, resolved, replies[{by, text}]}` on a subject. `resolve` may reply. Undoing it reopens the comment and drops the last reply. |
| **Event** `e..` | `id verb target args undo note by at day`. Some events also carry `changed cmd via window cause undone verb_run merged tripped_by`. `tripped_by` is on the events of a rule that acted as its author: whoever's act set it off (a687). Ids come from a counter that never goes back (`_eseq`), so a refused or rolled-back step leaves a gap. |

Editing a subject changes every appearance of it. Moving or removing one appearance touches only that appearance.

**Chats are signed by the world** (a656). An appended chat line is stored as `Name: text`, where Name is the display name of the event's actor (`sable` → `Sable`).
- A leading `Name:` that is the actor's own, in any case, is dropped, and the receipt says `the world signs for you; your typed name was dropped`.
- A leading name that is anyone else's stays as plain words after the real signature (ran: juniper appending `Jeff: I agree` stores `Juniper: Jeff: I agree`).
- A world verb runs as its caller, so its line is signed by the caller.
- A rule acts as its author (a687, decided in a683), so its line is signed by the author with no `via` in the signature: the event carries `via rule rN` (ran: sable's rule, tripped by pike, adds `Sable: (noted)`). A rule defined before a656 has no author: it runs as whoever tripped it, and its line reads `Pike, via rule r3: …`, until someone defines it again.
- Lines already in a chat are never re-signed. The old rule that signed jeff's unsigned lines `Alex:` is gone.
- `World.SPEAKER` reads a signature back. The `messages` row source keeps the whole signature in `who` (`Pike, via rule r3` for an authorless rule's line), and `awaiting reply` in examine is judged for the reader.

**Geometry.**
- The screen is 1280×800.
- The desk computes relations: `offscreen-part`, `spills-parent`, `covers X [fully]`, `under X [fully]`, and a hidden fraction.
- Flows reflow with an 8-pixel gap and a 24-pixel minimum. Sizes are proportional unless `equal_share`, with equal shares on overflow.
- `DESK_GEOMETRY=choices` (off by default, read at import): a flow child holds a fractional `order` key and a `share`, and its box is derived. `world.box()` is the one read of where a thing is drawn.

**Observed revisions (the fence).** The desk remembers what it showed each observer. An observer is an actor plus a window.
- It keeps two stores:
  - `seen[id] = rev`;
  - a seen index keyed by (observer, thing) → {aspect: event index}.
- The aspects are `prop:<k>`, `title`, `text`, `due`, `tags`, `comments`, `links` and `place`; `contents` is used for a create inside a surface. A verb the table doesn't know touches every aspect. `reply` (the chat verb) touches `text`.
- Three refusals:
  - `you have not looked at a04 yet; look, examine or read it first`;
  - `stale: a04 changed since you last saw it (e15 prop by other); look at it again before acting`;
  - `you have not seen a04's text; read a04 shows it before you replace it`. This applies to the replacing verbs rewrite, retitle, rename, edit, due, prop and untag.
- What counts as having seen something:
  - an outline line marks title, place, due and props (not text or tags);
  - `read` marks title, tags, due, comments, links, props, and the text only when the whole body printed;
  - `where` marks place;
  - `examine` and `pivot` mark everything;
  - a table marks its columns;
  - `scene` marks what each node printed;
  - your own act marks the aspects it wrote, and its receipt marks nothing more.
- An aspect never printed is judged from event 0.
- A recorded event is judged by the verb it carried out (`event_aspects` in `desk.py`), including one made through a selection or by a rule.
- A change to one prop never blocks a change to another, and the same prop still refuses.
- Your own changes from the same window never make you stale; a change from your other window does, and the refusal says so.
- A change your rule made as you while someone else tripped it counts as someone else's (a687; `rule_did_unseen` in `desk.py`): it makes you stale, and the refusal names it (ran: `stale: a697 changed since you last saw it (e898 prop by your rule r2, tripped by pike)`). Its tripper saw it on their receipt, so it does not make them stale.
- An undo counts as touching what it reverted.
- `create` and `comment` are never refused as stale.
- Adding a line to a chat is never refused as stale (a656): `append` or `reply` on a chat, or `edit` with only `append=`, replaces nothing. When others had added lines you had not read, your line still lands, the receipt says `others added to it since you last read it; read <id> to see their lines`, and your act marks nothing seen. So a later rewrite, retitle or remove of that chat is still refused until you read it. Appends to notes and other kinds are fenced as before. (`desk.py` `_adds_line`, used by both `cmd_do` paths.)
- A subject-id target (`sNN`) is judged by whole revision.
- Rules act without the fence.
- The fence coordinates honest actors; it is not access control.

**Undo.** `undo eN` reverts an event and records the reversal as a new `undo` event. A bare `undo` reverts your own latest change that hasn't been undone; a change your rule made while someone else tripped it is skipped (undoing it would undo their command, its cause).
- A composed verb is undone whole: contiguous events with the same `via`, `cmd` and author, and no cause.
- A rule's consequences are undone with their cause.
- Only the latest change to a thing can be undone.
- An event marked external (`launch`) cannot be undone.
- There is no redo (an undo cannot be undone).
- Undo is neither fenced nor limited to the author.
- A world verb's use is undone whole, all its steps.
- Undo kinds: `restore`, `restore_props`, `restore_subject` (a whole copy of the subject), `drop_comment`, `reopen`, `drop_link`, `restore_link`, `reorder` (a tiled swap), `delete` (with `delete_subject`), `external`.

## One language

`explore.py` on stdin, `POST /api/do` on the server, a gesture in the painter, a resident's `>` line and a world verb's steps all carry the same kind of line.
- Commands may be joined with `;` or newlines. They run in order and stop at the first refusal; earlier steps are not rolled back.
- A call runs at most 4 `read` or `examine` commands; the rest are listed as not run.
- A `script` line keeps its `;`.

| Family | Commands |
|---|---|
| Reading | `look [id] [:1-:4]`, `open` / `close`, `read id [#n\|#name\|:3\|:full\|tail=n]`, `examine` (`x`, `ex`), `where`, `verbs`, `pivot`, `find`, `table <sel> [cols= by=]`, `compare`, `history [id]` (last 12), `why`, `rows <source>`, `scene <lens>`, `export`, `rules`, `scripts`, `vars`, `help` (`?`) |
| Changing | `do <verb> <target> k=v`, `undo [eN]`; pair verbs `swap`, `beside`, `match`, `link`; world verbs (`<word> …`, `do <word> …`, `use <id> …`) |
| Defining | `rule when … do …`, `rule on <verb> [by=] do …`, `rule drop rN`; `script <name> = …`, `script drop`, `run`; `set <name> = <id\|title>`; `clock [YYYY-MM-DD\|now\|follow]` |
| Branching | `worktree`, `worktree fork\|diff\|merge <name>` |
| External | `sync`, `launch` (harness) |

**Verbs.** `examine` lists only the verbs that apply to a thing right now; `help <verb>` gives the arguments and one example.
- The verbs this desk does: `move place resize raise lower remove tile untile rename group create fold unfold append comment resolve check link unlink retitle rewrite sort prop tag due launch`.
- The registry (`moo.py`) holds 34. The specialized ones (`split gather dedupe reveal reply tidy stack done`) are refused here, with `help` naming the alternative.
- Synonyms such as `put` → move and `delete` → remove are accepted, and a near miss is matched at 0.75 similarity.
- Kinds inherit verbs:
  - surface → thing;
  - note, task, chat, doc and trial → text → appearance → thing;
  - image → appearance → thing.
- Arguments:
  - `move into=|before=|after=|to=x,y|by=dx,dy` (a selection form takes `one=1`);
  - `create kind= title= [text= due= tags= layout= query= cols= by= desc=] [as=<handle>]`;
  - `group title= as=` (or `do group <selection> as= title= [in=]`);
  - `tile as=`;
  - `sort by=due|title|kind [desc=1]`;
  - `prop k=v … | remove=k [at=appearance]`;
  - `tag add= remove=`;
  - `due on= | clear=1`;
  - `append line= [section=]` (on a chat the world signs the line and it is never refused as stale: see The world);
  - `rewrite text= [section=]`;
  - `retitle title=`;
  - `check item=n`;
  - `comment line=`;
  - `resolve id=cNN [line=]`;
  - `link to= as=`;
  - `unlink id=lNN`;
  - `resize to=WxH` (at least 40×24).
- Most verbs go through `World.apply`. `prop`, `tag`, `due`, `launch` and the tiled `swap` write their events directly. A new primitive still needs Python; a composition does not (see World verbs).

**Selections are the shared noun phrase.** The same grammar names a verb's target, a `find`, a view's `query=`, a rule's trigger, and a lens's `of`, `the` and `only when`:

```text
kind:note|task  tag:x  in:f04  title:agenda  ?word+word  prop:status=done  prop:k
comments:open  comments:any  links:a04  parts:a30  part-of:a20  unanswered:alex
due<2026-09-20  due>today  age>7  age<3  hidden  also:a18  a20,a22  -tag:done
```

- Terms joined by commas or spaces are ANDed.
- `parts:` and `part-of:` follow only `part-of` links, in one direction.
- `in:`, `also:`, `links:`, `parts:` and `part-of:` accept a title or a `$handle`.
- A target may also be one id, a unique quoted title, `desk`/`root`, or a handle:
  - `$item`, the last created thing;
  - `$new`, the last created surface, else the last created thing;
  - `$<name>`, set by `set` or `create … as=`.
- `$today` fills in any command; `\$today` stays literal.
- An unknown `word:` term is refused with the list of known terms. `prop:k>v` is not a comparison: it is read as a prop name and matches nothing (see Evidence).

**Rules.**
- `rule when <selection> do <verb> …` fires once on each thing that enters the selection; `now=1` includes current matches.
- `rule on <verb> [by=<actor>] do …` fires on each such event. It ignores events made by rules, and it treats `edit` as append, retitle or rewrite.
- Rules also run on clock changes and after `!` injections.
- A rule records its `author`, the actor who defined it (a656; rules defined before then carry none).
- **A rule acts as its author** (a687, decided in a683 by Sable, Juniper and Pike: a rule is a standing act its author chose, so crediting whoever tripped it misleads). While it fires, the world's actor is the author (`desk_knife.py` `_run_rules`), so its events say `by=<author>`, carry `via "rule rN"`, `cause` and `tripped_by=<tripper>`, and a chat line it adds is signed `Author: …` with no `via`. What it prints and marks meanwhile is recorded for the tripper (`_firing_observer`), who sees it on their receipt: `~ r2 fired on a697 as sable: ok prop a697 last=pike`.
- The author was not there, so the deed is theirs but unseen (`rule_did_unseen` in `desk.py`): it makes them stale on what it changed (see The world), a bare `undo` skips it, and their next `!!` line names it: `e898 your rule r2 did prop a697 last=pike (tripped by pike)` (in the grouped form, `your rule r2: …`). The tripper's `!!` line leaves it out; anyone else's reads `e898 prop a697 by sable via rule r2`. `why` reads `sable by rule r2, tripped by pike`.
- A rule with no author (defined before a656) runs as whoever tripped it, exactly as before: its events are signed by the tripper, carry no `tripped_by`, and its chat line reads `Pike, via rule r3: …`. Defining it again gives it an author.
- **Known obligation, not built:** there is no permission layer. When one exists, a firing must be checked against its author's rights at firing time, not the tripper's and not the rights the author had when defining it (a683).
- Cascades stop after three passes.
- A rule is checked when defined: a bad term, a specialized verb and a missing script are refused, but a destination such as `into=` is not checked.
- `why <id>` shows the events that placed a thing and the rule that would act on it next.

**Scripts.** `script <name> = <cmd>; <cmd>` with `$1 $2 $1.title $today`; run with `run <name> args`. Scripts are not validated when defined, and `$me` is not filled in a script (F2). A rule may run a script; a script a rule runs acts as the rule's author.

**Views.** `do create <surface> kind=view title=X query=<selection>` makes a view; with `cols=` (and `by=`, `desc=`) it prints as a table. You can't move a thing into a view, create inside one, or tile, group or sort one.

**Clock.**
- `clock` shows the desk's date.
- `clock YYYY-MM-DD` and `clock now` set it.
- `clock follow` tracks the wall date and reports the days that passed.
- `age<N` and `age>N` need a clock.

Rule, script and clock definitions are desk attributes, not events. Only a rule records an author (above); none of them appear in `history`, and they can't be undone, but a worktree carries them and a merge replays them. Lenses, styles and world verbs, by contrast, are ordinary notes.

**Worktrees.** `worktree fork <name>` copies the session into `<session>@<name>`, with a journal of the command lines made there, including `rule`, `script` and `clock` lines.
- `worktree diff` shows those lines beside what the base did since (`!` = both touched it).
- `merge` replays the journal on a trial copy of the base. It remaps created ids, signs each command by its author, and is all or nothing.
- A command is refused when the base has changed an overlapping aspect of anything the command touched. The journal records what a command touched by id as it ran, however the command named it (title, handle, selection or world verb). The base's creates and comments are ignored.
- A worktree stays open after merging, and the next merge takes only new lines.

## World verbs

A verb anyone can make, with no Python (`verbs.py`, the first tier of live building).
- **What it is:** a note tagged `verb` that is placed somewhere.
  - Its title gives the word, with `|` between aliases (`handbook|hb`), matched regardless of case.
  - Each text line not starting with `#` is a step; the `#` lines describe it.
  - The steps are joined with `; ` and run as one batch, as the caller.
- **Where it lives** (prop `on`):
  - absent: carried by its author;
  - `house`: everyone;
  - an existing id: on that thing;
  - any other word: that actor.
- **Lookup:** carried by you, then on a thing named among the words, then the house. Two verbs at one level refuse and name both. It is tried only after the built-ins fail: when the first word is no command, or for `do <word>` when `<word>` isn't a built-in verb. `use <id> [words]` names a verb exactly, and refuses one that someone else carries.
- **Blanks:**
  - `$1 $2 …` refuse when there are too few words;
  - `$1.title`;
  - `$*` is every word after the verb, the target included (F24);
  - `$me` is the caller and `$this` is the verb note;
  - values are quoted automatically.
- **Limits and provenance:** nesting stops at depth 5. Events are tagged `verb_run: "<word> <aid>"` and show in history as `(verb <word> <aid>)`. `examine` lists the verbs on a thing; `help <word>` describes the verbs you can reach.
- **Misses:** a reach that nothing answers is appended to `reaches/<world>.jsonl` (not in git).
- **Undo** takes back the whole use, all its steps. Each event carries `verb_use`, and a verb used inside another joins the outer use. The receipt says `reverted e3..e4 (2 steps of the verb <word> <aid>)`.

## Lenses: one scene, two printers

```text
lens note -> parse (WORDS table) -> resolve ($names) -> lower (IR) -> evaluate (Accessor, read log R)
          -> emit (paint contract) -> to_text          (scene <lens>: what an agent reads)
                                   -> painter_view -> lens.js   (lens.html: what a person sees)
```

A **lens** is a subject tagged `lens` whose text is the definition. It is created, rewritten, undone, forked and merged like any note, and found by title regardless of case; two with one title are refused unless exactly one is placed. Each line reads `name : prop, prop`. Indentation is containment, and the first unindented part is the root. Lines starting with `lens ` or `#`, and trailing ` # ` comments, are skipped.

**The stages.** `scene.scene_for` delegates to `lens_ir.scene_for`.
1. **Parse:** `scene.parse`, driven by the `WORDS` table (word → shape, setter). The checks are folded in here. A refusal prints the whole vocabulary from the table.
2. **Resolve:** `scene.resolve` classifies every `$name` in every reachable part (field, host, gesture, let, frame, prop) before anything runs, and refuses a frame not in scope.
3. **Lower:** `lens_ir.lower` makes one node per part: `bind` (one | many), `lets`, `guard` (value | selection), `emit`, `acts`, `place`, plus `carry`, `kids` and `deps`.
4. **Evaluate:** `lens_ir.evaluate` reads through an `Accessor` that logs each read into R (value, thing, select, rows, define, touched, host), in this order within a part: bind, lets, guard, emit, acts, instances, placed lens, fixed kids.
5. **Compile:** `compile_lens` adds the definition closure (`def`: the lens's id and rev, `status` current or fallback, the style's name and rev) and handles the last-good fallback.
6. **Emit:** `scene.emit` gives every node its `paint`, `acts` and `fence`. `painter_view` passes the painter only key, paint, acts, fence, kids and part.

The old single-pass evaluator (`scene.build`, `scene_for_old`) is kept as the reference the golden prints were made with.

**Words** (the `WORDS` table and `INTERPS`; the `scene.py` docstring lags behind them):

| Word | Meaning |
|---|---|
| `column` `row` `free` `grid <tracks>` `cells` | Layout. Tracks are in `fr` or `fit`, and a track may be `<n>gap` |
| `gap`, `scroll none\|scroll\|end`, `fold ["label"] [open] [float]`, `measure <n>ch`, `verbatim`, `lines <min>..<max>`, `share <w>`, `hint "…"`, `plain` | Paint words, passed to the painter. `fold` is the viewer's own toggle, with no event, folded to begin with unless `open`; `float` draws the open contents over the page below the handle (a menu: it opens for a moment, and Escape or a press outside closes it); a folded part gives up its `share`; the painter's fold handle wears role `fold` (`menu` when floating) over `tool`; `plain` turns off code runs. `share` is a child's weight along its parent's axis; on the root it takes the window's height, and a grid with a share divides its height among its rows, so a `scroll` inside it scrolls within the window instead of the page growing |
| `role <name>` | Look, by a role from the lens's style; an unknown role is refused with the list |
| `text <template>` | Words (template names below); quote to keep commas and hashes |
| `clamp <N>` | At most N lines, or N repeats; both printers say how many are left |
| `of <selection> [as f]` + `each <part>` | Repeat over a selection, over ids named one by one (each printed with its state: unplaced, gone), or over a row source: `sections:<id>`, `comments:<id>`, `messages:<id>`, `actors`, `events`, `worktrees`, `house[:<corner>]`, `turns[:<corner>]` (each resident's last replies, newest first: `resident corner turn at said acts`, where `acts` counts the lines that began with `>`). An empty repeat prints `(empty)` |
| `the <selection> [as f]` | Exactly one thing becomes the current thing; prints `(empty)`, or `(ambiguous: …)` with nothing built under it |
| `as <name>` | Names this part's thing as a frame, read below as `$name.field`. Shadowing a built-in or an outer frame is refused |
| `over $<list>` | Repeat over a list field or derived rows; `$it` is each value |
| `derive <name> = <interp> <inputs>` | A named calculation from a closed list: `day-n`, `days-from`, `day-or-time`, `weekday`, `week-of`, `time`, `date`. It prints its inputs and result |
| `capture <field>=<value>` | Use this value instead of following; prints `(now X: differs)` when the world has moved on. Kept out of the fence |
| `at item` | The appearance's own world geometry, only under a `free` parent |
| `spread x <a> step <n\|$prop> to <max>` | Computed placement by index, printed as `(spread, not its place in the world)` |
| `lens <name>` | Place another lens, whose name may be templated (`lens $kind`); a lens may not contain itself |
| `only when <selection>` or `only when $x <op> v` | The part exists only on a match. A value test (`= != < > <= >=`, and `has` / `!has`: the words contain the value, ignoring case; a value with a `$name` in it is filled, so `only when $said has @$me`) prints its inputs; a missing value counts as absent, not false |
| `carry`, `on click\|edit\|drag do <command>`, `on drop <part> do <command>` | Gestures (see Gestures and their fence) |

**Template names.**
- Fields: `$title $text $kind $due $tags $id $item $count`.
  - `$count` is the size of the nearest repeat.
  - `$n` survives only as a prop name.
- Any prop of the thing: `$place` prints `read place=…`, or `(no place)` when missing.
- Frame fields `$f.x` and lets.
- `$it`, `$it.n`, `$it.date` from derived rows.
- Host names `$me $today $session`.
- Freshness names:
  - `$touched`, the last event on the thing, and `$touched.id|verb|at|by`;
  - `$changed.<field>`, the last event touching that field.
  - These are logged in R but kept out of the fence and the seen index.
- Gesture names `$value $x $y $carried`.
- A `$name` that is neither in scope nor a prop prints verbatim, with no warning.

**What prints.** `to_text` prints each node with its facts:
- an occurrence key segment (`· key …`);
- `runs N code`, for code spans and fences, which become runs at print;
- `(absent: why)`;
- `· only when …`;
- 240- and 120-character cuts.

A scene has a budget of 1500 nodes. There is no escape to HTML, CSS or script, and no arithmetic or general `if`. Anything else is refused with its line number.

**Resilience.** A lens that stops compiling keeps showing its last version that did, and says so first:
```text
! lens L2 no longer compiles … ! showing the last version that did; gestures are off until it compiles.
```
- The fallback is kept in `desk._lens_good`, in the pickle, and is named in `def`.
- A lens refused for exceeding the node budget gets no fallback.
- The scene is rebuilt in full on every request; there is no incremental rebuild.

**Facts and observations.**
- A placed part carries what the world knows, such as `= offscreen-part`.
- The painter reports what only it knows through `/api/observe`, kept per actor in `desk._views`, never as events:
  - `cut by the clamp` and `contents overflow the box` are always reported;
  - viewport, `out of view`, unsent drafts, folds and the carried thing are reported only with `?share=attention`.
- Without that, the text printer says the viewer `has this open; attention not shared`.

**How the language grows.** The growth rules from the design studio are argued positions, not checks. The painter's line ceiling is under review ("Alex rejected the cap", in `lens.js`'s header) and is already exceeded. Alex's direction: no cap on the compiler or the painter, but neither may grow linearly.

To add a lens word today:
1. a `WORDS` row and setter in `scene.py`;
2. its lowering and evaluation in `lens_ir.py`;
3. `to_text` and `emit`;
4. `lens.js`;
5. `test_scene.py`;
6. `suite/sessions.py --check`, then `--rebase` when the change is intended.

A new paint word needs only a table row, because `PAINT_WORDS` passes it through.

## Gestures and their fence

A gesture is a desk command written in the lens, and `do` is implied unless the line starts with a reading command.
- `click` fills `$x $y`.
- `edit` fills `$value`. It commits on Enter or Ctrl-Enter (`paint.commit`); `on edit` on clamped text is refused.
- `drag` fills `$x $y`, and is painted only on a node with a box.
- `carry` marks a part that can be picked up.
- `on drop <part> do <one command>` runs on the receiver. `$carried` is filled by deskd with the carried item's id.

The painter fills only the first occurrence of each name. Click and edit lines may still batch with `;` and may `run` a script.

**What a gesture carries.** Each painted gesture is sent with `observed`:
- `item` and `rev`;
- `reads`: `[thing, rev, aspects]` for every value that filled it or fed its derivations, and `["select", query, answer, keep]` for every membership it relied on, including the binds on its chain;
- `defpart`: the part's lens, id, path and a hash of its binding lines;
- `bind`;
- `at`;
- the whole `def` closure;
- for a drop, `carried` and `receiver`.

**What deskd checks** (`/api/do`, in order):
1. A gesture from a fallback frame is refused: "it is for reading".
2. Part identity: a gesture is admitted when its part still hashes the same, even if the lens changed elsewhere. It is refused only when the part changed and the lens moved. Every closure member is checked.
3. For a drop: the carried thing ("changed while it was in the air"), then the receiver's revision, reads and part.
4. The item, judged on the aspects its gesture read (`touched_aspects`). The refusal names the last event, its verb and its author. When the item is accepted, the actor's seen revision moves to the current one.
5. Each read: a thing passes if only unread aspects moved; a selection must give the same answer, compared as a set, with a clamped repeat comparing its shown prefix.

Every refusal ends with "nothing was done. The view will repaint." A painted gesture is judged on what was painted, even against the actor's own later changes, and the painter never looks again on the person's behalf.

## Style

A style is a note tagged `style` and titled with its name. It is edited, undone and forked like any note.
- A lens picks one with prop `style=<name>`.
- `desk-shell/style/calm.style` is only the seed, used when the world has no note of that name.
- The style defines:
  - tokens, the only place a colour or number appears;
  - roles built from tokens;
  - `font <name> = Family, fallback` lines;
  - `when <selection>` clauses;
  - themes.
- A lens names roles; the style never names a lens.
- The painter fetches `/api/style` and restyles when the style's revision changes. `?theme=` picks a theme.
- `when` clauses reach only the windowed shell.
- A lens without `style=` has its roles checked against the file, while the painter paints `calm` from a world note of that name if one exists.

## Processes and state

| Endpoint (`deskd.py`) | What it does |
|---|---|
| `GET /api/snapshot?session&as` | The world as JSON, plus `events_total`, `worktree`, `readers` and the actor's outline. Rendering does not count as looking |
| `GET /api/scene?session&as&lens[&view=painter]` | `{scene, text, events_total}` or `{refused}`. `view=painter` sends `painter_view` with the root's `def`. A compiler crash is reported as a bug in scene.py, not in the lens |
| `GET /api/style?session&as&name` | A style's source from the world, else the seed file (`name` defaults to `calm`) |
| `GET /api/version` | `{code}`: git HEAD when deskd started. Loads no session |
| `GET /api/events?session&since` | `{events, total}`, without undo records |
| `POST /api/do` | `{session, as, line, observed?}` returns `{text, error, events_total, line, as, created, events}`. `error` is the first `ERR` line. An empty line is 400. `worktree …` lines go to worktree.py |
| `POST /api/observe` | `{session, as, lens, at, viewport, facts}`, capped at 400 facts; returns `{ok, kept}` |
| anything else | GET: a static file from `desk-shell/`. POST: 404 |

- The server is a `ThreadingHTTPServer` on 127.0.0.1. API replies are `no-store`; every reply also says `no-cache`, so a browser rechecks the painter's files and a page reloaded for new code gets it.
- deskd answers only its own pages: an `/api/` request whose `Origin` is not its own address, or that a browser marks `Sec-Fetch-Site: cross-site`, gets 403. Local programs that send neither header (the CLI, the house) are let through, as before.
- A session name must match `^[A-Za-z0-9_][A-Za-z0-9_@-]{0,63}$` (no dots or slashes), else 400. A POST body that isn't a JSON object is 400.
- Per-actor state is keyed by actor alone; the CLI keys it by actor and window.
- A new actor starts with nothing seen, and `jeff` uses the session's own slot.
- The shell polls `/api/events` every 1.5 s. The painter polls `/api/scene?view=painter` every 1.5 s and `/api/version` every 5 s, and reloads the page when the code changed, unless someone is typing or holding a part.

**Sessions.** A session is one file, `sessions/<name>.pickle`, holding the whole Python desk: world, rules, scripts, clock, per-actor state, observations and the last-good lenses.
- Every request that names a session, reads included, loads it under `sessions/<name>.lock` and acts. deskd saves only when the request changed something: it compares the pickled desk before and after, so a painter's poll writes nothing.
- A request for an unknown session with a valid name creates it.
- The lock holds the holder's pid. A waiter treats a lock under a second old as busy and does not open it. Only an older lock is read, and it is removed if its pid is dead or it is over 60 s old. A waiter gives up after 60 s (`could not take … lock`) and never proceeds without the lock. A holder releases with `explore.release_lock`: it removes only its own lock, and retries briefly when Windows refuses to delete a file another process has open.
- A save writes `<name>.pickle.tmp`, then renames it into place (`explore.save_desk`).
- The CLI saves once at the end of an invocation.
- `export_docs.load`, which the house, `health.py` and `try_house.py` use to read a world, takes the same lock. When it can't, it raises an error rather than exiting, so the house logs a failed step and tries again on its next pass.

## The browser

Two pages paint the same world.

**The lens painter** (`lens.html`, which loads `style/style.js`, `viewer.js`, `lens.js` and `term.js`) is the generic painter.
- It reads the paint contract (key, paint, acts, fence) and knows no app, kind, colour or size.
- `lens.js` is 256 lines. It draws a fold's handle with its label (`▸ turns`); clicking it is the viewer's own toggle, kept in the browser, never an event.
- `viewer.js` (155) keeps continuity:
  - unchanged elements are kept by key, so a reader's selection survives another person's act;
  - drafts survive a refusal, a reload or a closed tab (localStorage `lens-drafts:…`), and so do folds;
  - a refused draft is shown with both sides;
  - it posts observations.
- Also in the painter:
  - cards move by keyboard;
  - carry and drop work;
  - code prints as runs;
  - `paint.semantic` marks buttons and groups.
- `term.js` (76) is a desk terminal in the right-hand pane by default. It sends lines to `/api/do` and keeps its history in localStorage. × closes it and the painter takes the full width; "▸ terminal" (top right) or Ctrl+` opens it again. Open or closed is remembered per world in the browser.

**The windowed shell** (`index.html`, `shell.js`, `core.js`, `apps/`) has a dock, draggable windows, and three hand-written apps: Notes, Editor and Together (`apps/third.js`).
- A window is an appearance on the `<actor> screen` surface:
  - opening it is `do place`, then `do move` and `do resize`;
  - dragging ends in `do move … to=x,y`;
  - the grip ends in `do resize … to=WxH`;
  - closing it is `do remove`.
- Other `* screen` surfaces show as "<who> has N open".
- Each app implements `text(ctx)`, what a text-only inhabitant reads for that window.
- Apps prefix `look <id>;` to their commands, so their gestures are not fenced against what was on screen.
- The shell loads `calm.style` as a file, and its style panel edits page memory only.

`desk-shell/natives/prose.js` is an 80-line prose editor loaded nowhere. It reads the old node shape, from before `paint`, and the compiler refuses `native` and `settle`.

`desk-shell/OWNERS.md` names one owner per file. While the old team is paused (from 28 Sep), Claude edits the paused owners' files where the command center needs it, and logs each change in `research/command-center/FRICTION.md`.

## Residents: the house

`house.py` runs resident agents that live in a world (`python house.py [world] [--fake PORT]`, default `frontier`; normally started by the keeper).

**Settings.** Props on the placed note titled "The house" override the defaults:
- `model=claude-opus-5-5`;
- `breather=120` s;
- `wake_every=14400` s;
- `workers=1`;
- `worker_model`.

**A resident** is any surface with `role=resident`, its corner. Its props:
- `actor`, the name it is given. A corner without one has status `unnamed` and is never started.
- `want=awake|rest`.
- `wake`, the desk line run on each wake (default `run arrive`).
- An optional `model`.

**The process.**
```text
claude -p --input-format stream-json --output-format stream-json --verbose --system-prompt "" --tools "" --strict-mcp-config --setting-sources "" --model M [--resume <session>]
```
- The binary is `$HOUSE_CLAUDE`, else the newest `claude` found by `--version`.
- cwd is `house-state/<world>/<corner>/`.
- The environment drops every `CLAUDE*` variable and sets `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`.
- The resident has no tools: everything it knows comes from the world.

**The relay.** Only lines beginning with `>` reach the desk, and a line whose first word is a desk command counts without the mark. They run as the resident through deskd when `DESKD` is set, else through `desk_mcp.run_desk`. The receipt is the next message.

**Welcome and waking.**
- The welcome (the placed note "The door", with `$me` replaced by the name) prefixes the first message after a fresh start, a lost conversation, or a `compact_boundary` event (a compaction).
- Every wake begins `You are <actor>. Your corner is <rid>.`, followed by:
  - the receipt of the wake line;
  - news;
  - any undelivered text from a turn that didn't finish.
- A resident is woken:
  - when its process first starts;
  - when a timed rest ends (`(you rested 2 hours)`);
  - every `breather` seconds while an objective is open (a subject with `objective=open`);
  - every `wake_every` seconds.

**Rest and quiet.**
- `> rest` rests until called. `> rest <human time>` (minutes, hours, days, weeks, "an hour and a half") rests for that long, at most 30 days; an unreadable time is answered and the resident goes on.
- Lines run before a rest are delivered on the next wake.
- A reply with no commands gets held news or `(quiet)`. After 10 quiet exchanges in a row, the resident rests.
- An empty reply rests.

**News.**
- **Urgent news ends any rest:**
  - a line in a chat in its corner;
  - `@name`, `@everyone` or `@all` anywhere;
  - a comment on a thing in its corner;
  - a comment on its own commission.
- **Held news rides along with the next message:** a line in a chat whose `members` include `all` or the resident.

**Failure.** A lost conversation (`No conversation found`) starts fresh, with the welcome. Other failures retry with backoff up to an hour, with status `error`.

**State.**
- The house writes the corner's `status` (`awake`, `asleep`, `unnamed`, `error`) as actor `house`, only on change.
- `house-state/<world>/house.json`, rewritten every pass, is read by the `house` and `turns` row sources. It carries each resident's last 10 replies (`said`, each cut at 2000 characters), so Alex's Desktop can show what they wrote, their own thinking included.
- Each corner keeps `state.json` and `transcript.jsonl`.
- `house-state/` is never committed.

**Exit codes.** A second house on one world exits 76. Under the keeper, a house whose landing changed Python exits 75 once no one is mid-turn.

## Commissions, workers and the keeper

The second tier of live building: code the world can't change yet.

**A commission** is any placed subject with a `commission` prop. Its states:
```text
asked -> working -> (waiting <-> working) -> ready -> landing -> landed | reverted | failed   (anyone: cancelled)
```
- `asked_by` is the prop, else whoever created it, else alex.
- "Alex's standing trust is the grant": nothing waits for approval.

**A worker** (`workshop.py`) is started when fewer than `workers` are running.
- The house makes `git worktree add .worktrees/<cid> -b worker/<cid> HEAD` and copies the world in as `sessions/<world>-try.pickle`.
- It then runs:
```text
claude -p … --permission-mode acceptEdits --allowedTools Read Edit Write Glob Grep mcp__desk__desk Bash(<r>:*) PowerShell(<r>:*) --mcp-config … --setting-sources "" --append-system-prompt <protocol>
```
  - `<r>` covers git status, diff, add, commit, log, show and rebase, `node --check`, and python.
  - Its system prompt is Claude Code's own, plus `AGENTS.md` verbatim, then the worker protocol. The protocol asks it to keep *Current Implementation* true (see Landing). It forbids touching `sessions/` or `.env`, pushing, deleting what it didn't make, and editing `jeff.md`.
- The worker's desk tool (`desk_mcp.py`, as `worker-<cid>`) acts in the live world.
- It talks through comments on its commission, and those comments come back to it as messages.
- It says it is done by committing and setting `commission=ready`.

**Landing** happens between the house's passes:
1. The branch's changes must be non-empty and avoid `sessions/` and `.env`.
2. Health is taken.
3. `git merge --no-ff worker/<cid>` into whatever branch is checked out, with the subject `land <cid>: <title>`.
4. Health is taken again. If it fails, or a lens that compiled before no longer does, the merge is reverted (`git revert -m 1`).
5. In frontier, from the main checkout, *Current Implementation* is exported from its Handbook binder and committed if it changed. The protocol asks the worker to rewrite the sections its change affects before it sets `ready`.
6. The result is commented, the worktree removed and the branch deleted.
7. A landed `.py` change asks the house to restart.

**The keeper** (`keeper.py [world] [--port 8794]`) runs deskd and the house (the house with `DESKD` pointing at that deskd, and `HOUSE_KEEPER=1`).
- It restarts deskd whenever HEAD moves.
- It restarts the house:
  - at once on exit 75;
  - after 60 s on exit 76;
  - after 30 s on any other death.
- If the house dies 3 times within 5 minutes after a `land ` commit less than 15 minutes old, the keeper reverts that commit.
- Its log is `house-state/keeper.log`.

**Health** (`health.py <world> [--json]`), in order:
1. every `*.py` compiles;
2. `node --check` passes on `desk-shell/*.js` and `style/*.js`;
3. `test_scene.py` passes;
4. `suite/sessions.py --check` shows 0 golden differences;
5. every placed lens compiles.

A refusing lens is listed but doesn't fail health.

**Trials.** These spend real model calls.
- `try_house.py` copies a world to `try-<tag>`, names and wakes chosen corners, runs the real house under turn and time caps, writes a report to `research/command-center/trials/`, and deletes the world and conversations.
- `try_worker.py` runs one real commission in a throwaway worktree, landing on a `trial/<tag>` branch, never on main.
- `fake_model.py` is a scripted stand-in for the model API, for house tests.

## Documents

- **`export_docs.py [session] [--force] [--dry]`** writes this document from the binder *How the desk is built* to `docs/` and to Alex's vault, each with a stamp. The first note is the title and introduction; each later note is a section. A copy edited outside the desk is left alone, with a warning. For `frontier` it also writes `research/object-facet-frontier/desk-export.txt`.
- **`handbook_docs.py [world]`** copies `docs/Agora.md` and `docs/Dynamic Desk.md` verbatim into the Handbook binder *What we're building*, rewriting only on a change.
- **`docs_sync.py [--watch [s]] [--no-handbook]`** keeps the five design documents the same in `docs/` and the vault, ignoring line endings.
  - An edit on either side is copied to the other.
  - When both sides moved, it refuses and shows the first difference.
  - A change to Agora or Dynamic Desk runs `handbook_docs.py`.
  - Nothing starts it automatically yet.
- **`desk_mcp.py`** is the desk as an MCP tool over stdio: one tool, `desk {line, as, session, window}`. It validates actor and session names, refuses `!` lines, and runs `explore.py` once per call.

## Code map

| File | Lines | Responsibility |
|---|---:|---|
| `world.py` | 973 | Subjects, appearances, surfaces, links, comments, geometry (and `DESK_GEOMETRY=choices`), events, `apply`, `undo`, chat signing |
| `desk.py` | 1087 | Outline notation, the seen fence and its aspect table, the blind-replace check, `;` batching, reading commands, `undo`, `do`, the world-verb fallthrough |
| `desk_moo.py` | 267 | Verbs by kind from the registry, `examine`, `help <verb>`, `verbs` |
| `desk_knife.py` | 1244 | The live desk: selections as targets, pair verbs, rules, scripts, clock, handles, tables, views, `export`, `rows`, `scene`, help topics, world-verb dispatch in `do` |
| `moo.py` | 536 | The verb registry: declarations, kind inheritance, composed verbs, synonyms |
| `knife.py` | 263 | The selection language (with `unanswered:`) and pair verbs |
| `verbs.py` | 262 | World verbs: finding, filling, running, reaches |
| `scene.py` | 1473 | Lens grammar (`WORDS`), resolve, emit, the text printer, row sources, styles from the world; the reference evaluator |
| `lens_ir.py` | 529 | Lowering, the evaluator over the Accessor, `compile_lens` and the definition closure |
| `worktree.py` | 212 | Fork, journal, diff, all-or-nothing replay merge |
| `explore.py` | 257 | CLI: forward to deskd or run under the pid lock (`take_lock`, `release_lock`); atomic save; `--window --dump --shape --reset`; `!actor` injection |
| `deskd.py` | 408 | HTTP server, its origin and session-name checks, and the gesture fence |
| `house.py` | 704 | Residents |
| `workshop.py` | 342 | Commissions and workers |
| `keeper.py` | 118 | Keeps deskd and the house on the current code; reverts a breaking landing |
| `health.py` | 119 | The checks a landing must pass |
| `try_house.py`, `try_worker.py`, `fake_model.py` | 463 | Trials and a fake model |
| `desk_mcp.py` | 176 | The desk as an MCP tool |
| `export_docs.py`, `handbook_docs.py`, `docs_sync.py` | 313 | The documents |
| `journal.py` | 335 | Sable's standalone operation-journal prototype. Nothing running imports it; `test_journal.py` does |
| `harness.py`, `run.py`, `tasks.py`, `jeffx.py` | 1083 | Model trials as desk things. `jeffx.py` imports a transport from `C:/Projects/Agora/local/…`, outside this repo, and `runs/` is parked |
| `play.py`, `playground.py` | 128 | An older play loop and page. `playground.py` imports `tasks` from the old copy in `C:/Projects/Agora` |
| `test_scene.py`, `test_journal.py`, `golden_prints.py`, `suite/` | 382, 839, 35, 1765 | Tests and instruments (see Evidence); `suite/` is Python files only |
| `desk-shell/lens.js`, `viewer.js`, `term.js`, `lens.html` | 544 | The lens painter, continuity, the desk terminal |
| `desk-shell/style/calm.style`, `style.js` | 409 | The seed style and the style compiler |
| `desk-shell/shell.js`, `core.js`, `apps/*.js`, `index.html`, `shell.css` | 2024 | The windowed shell and its three apps |
| `desk-shell/checks/` | 1823 + 884 | Iris's browser checks and results, Rook's defect list, and Pike's continuity instrument (`continuity/run.mjs`, with 13 results) |

Which file for which change:

| Change | Where it goes |
|---|---|
| A verb anyone can use | A note tagged `verb` in the world |
| A new primitive or undo kind | `world.py` and `moo.py` |
| A new command | `desk_knife.py` |
| A new lens word | See "How the language grows" |
| A new role or token | The style note in the world |
| A new endpoint | `Handler.do_GET` / `do_POST` in `deskd.py` |
| Resident behaviour | `house.py` |
| Code the world can't change | A commission |

## Evidence and limits

**Checks, as they run on the date above.**

| Check | Result |
|---|---|
| `python health.py frontier` | python ok; scripts ok; test_scene 21 passed; session prints: 82 same, 0 differ in reads only, 0 differ in the golden form, 0 new; lenses in frontier: 7 compile, 1 refuse (`p-if`); total 3.4 s |
| `test_scene.py` | 21 passed |
| `test_journal.py` | An instrument that always exits 0: `9 breaks, 1 half, 1 hidden, 1 holds, 7 journal`. S11 drives an old code path and no longer describes the desk |
| `suite/run.py` | 9 cases (trip, attacks, reads, host, chat, viewer, workspace, blocks, budget), all the same as their recorded runs |

- `golden_prints.py` has no check mode (it writes); `suite/sessions.py --check` is the read-only comparison.
- `desk-shell/checks/` needs a live page and server, and was not run.
- Nothing automated covers deskd's HTTP layer, the house with a real model, or the browser.
**Open defects a builder will meet** (each reproduced, unless marked read).

*The fence and undo:*
- A selection target skips the "not looked yet" refusal, and pair verbs never check staleness (read).
- Via deskd, the CLI does not stop at a refusal.
- A `;` batch half-applies, and a `script` definition makes no event, so a bare `undo` reverts an older change.

*Worktrees and export:*
- `export` does not replay: an unplaced subject and its props are dropped, and repeated placements make titles ambiguous.

*Selections, lenses and help:*
- `prop:k>v` is read as a prop name and matches nothing, with no refusal.
- `of events` shows the last 20 with no note that it was cut.
- The `worktrees` row source loads other sessions' pickles, with no lock.
- One viewer's `look` changes another viewer's `of actors` scene.
- `$count` is not filled on the repeat's own part, although the docstring says it is. Inside instances, `$n` prints literally.
- Host names `$me` and `$session` enter a gesture's fence as `prop:me` and `prop:session`.
- A part placed by `spread` still offers `on drag`, so a computed position can be written back.
- A placed lens starts with an empty context and can't read the thing it is placed on.
- The compiler's identity hash covers `scene.py` and the seed style but not `lens_ir.py`.
- `help` doesn't list `scene`, `worktree`, `compare` or `sync` at the top, and `help selections` omits `comments:`, `links:`, `parts:`, `part-of:` and `unanswered:`.
- Comments and replies by jeff are stored as `by: alex` (read).

*The shell:*
- The Notes app rewrites `"` to `'` in titles (read). Whether Escape on a new-note draft creates the note needs a browser.

**Persistence and safety.**
- The pickle is the database, with no journal and no format version. Loading it executes code, so a session file must be trusted.
- Saves are atomic, and every reader takes the lock.
- deskd binds to localhost and refuses requests from other sites' pages, but checks no token. Any local program can act as anyone.
- Fences coordinate; nothing authenticates.
- Workers are real `claude -p` processes with file and shell tools. Their branches are merged without human review, on standing trust, and only `sessions/` and `.env` are off limits.
- The keeper can revert HEAD on its own.
- Residents run with no tools and a scrubbed environment.

**Friction log.** `research/command-center/FRICTION.md` holds F1–F27. Open or partly open:
- F2: scripts can't say who runs them.
- F3: identity equals name.
- F9: a repeat can't show the newest N.
- F21: no plain way to "say".
- F24: a verb can't say "the rest of the words".
- F25: a verb's title is also a name.

## What a builder hits first

In priority order, from an attempt to describe a calendar in this framework.

1. **No time type.** Kinds are a closed list; `due` is a date only; props are strings compared by equality, and `prop:k>v` silently matches nothing. Adding any of these needs Python.
2. **Placement cannot follow a value.** `spread` places by index, and there is no arithmetic. `derive … days-from` makes a row per day, and `day-n` computes a date, but nothing places by a value.
3. **Repeats cannot be ordered or headed.** `of` takes world order, and a part prints its instances before its placed lens and fixed children.
4. **Gestures carry pixels and one field.** An `edit` can run any verb, including a `create` titled with `$value`, and a drop onto a derived day row can carry `$it.date`. Nothing maps a position to a date.
5. **Two interfaces that do not meet.** The windowed shell and the lens painter are separate pages. The lens page has a desk terminal beside it.
6. **Text entry is whole-field**, committed on blur, Enter or Ctrl-Enter. Drafts survive a refusal or a reload. The prose native is still unwired.
7. **Definitions are not uniform.** Lenses, styles and world verbs are notes. Rules, scripts and the clock are not: they have no history or undo, though worktrees carry them.
8. **No durable store, no identity, few pass/fail tests** for the command layer. The instruments (`test_journal.py`, `suite/`) drive it but don't gate.

## Under study

Tentative mechanisms: designed or argued, not built, unless marked. Each names the commitment it serves.
- **Sources:**
  - `research/object-facet-frontier/`: POSITION v2, the round-six proposition, and the researchers' notes;
  - `research/command-center/`: the drafts *Three ways to change the world*, *Kinds and shapes* and *Living in the world*, also in frontier as a598, a613 and a595, part of the task a593.
- Items marked **(decision N)** wait on Alex, numbered as in the round-six proposition.

**Built: the staged compiler.** Parse, resolve, lower to the six kinds, evaluate through the Accessor, and emit; see "Lenses". Still open:
- the evaluator is a transcription of the old one, not a dispatch by kind;
- it still reads the world directly in places;
- R is logged but nothing consumes it (the fence is built separately);
- there is no incremental rebuild;
- `define`/`lib` library words are not built.

The growth measure (`research/object-facet-frontier/experiments/growth/measure.py`, M1–M6) is run by hand and measures only the frozen `scene.make`, not `lens_ir.py`.

**Partly built: names and scopes.** `resolve` classifies every name and refuses shadowing of frames and built-ins; `$count` exists; refusals come from the grammar table. But classification checks built-ins first rather than innermost first, and a prop is silently shadowed by a built-in.

**For "readable, not walled": `if`, arithmetic and nesting (decision 1).** *Not built*, except the `only when $x op v` guard, which prints its inputs.

**For "one language" (decision 2).** One expression language in two contexts: reading in lenses, and proposing changes in gestures, rules, definitions and verbs. *Not built.* *Three ways to change the world* proposes:
- one filler for blanks shared by world verbs and lens gestures;
- verbs checked when saved;
- write-through a view.

**For "whole or not at all", "see before it happens" and "no silent overwrites": proposals.** *Not built.*
- A gesture or rule yields one proposal, applied whole or not at all and previewed first, including the rules it sets off.
- Only `on drop` is limited to one command today. Decisions 3 and 4 are not enforced.

**For "everything that changes behavior is visible".** *Style: built* (a world note). Rules, scripts and the clock remain desk attributes. The last-good cache is kept, and named in `def`.

**For "extending gets cheaper": the library and new intermediate kinds.** *Not built.* The proposed bar for a new kind:
- two unrelated tasks need it;
- it can't be lowered into the existing kinds;
- every consumer states what it does with it;
- it keeps the properties.

**For "new things to show don't need new code in the core": kinds in the world.** *Kinds and shapes* proposes:
- a few storage shapes in the host;
- many kinds as notes tagged `kind`;
- several kinds per thing;
- kinds that describe and never enforce.

*Not built*; its first step touches `world.py`.

**For "the world is a place": rooms and narration.** *Living in the world* proposes:
- rooms as places where verbs live, with "where you are";
- narration in `look` and `examine`;
- the desktop as a room with local layout verbs. The Desktop exists, a room inside Home; the layout verbs are not yet local to it.

*Not built.* How arrangements, appearances and views divide is held open by Alex.

**For "everyday quantities come out right": allocation (decision 6).** *Not built.* `suite/cases/budget` is the instrument.

**For "true-when, not just written-when": timelines (decision 5).** *Not built.*

**For "your view settings are yours": the viewer store.** *Partly built, in the browser only:* drafts, folds and terminal history in localStorage. Lenses can't read it, and nothing is journaled.

**For "new things to show never need app code" and "nothing in progress is lost": the painter.** *Partly built:*
- frame, text, code runs, press, edit, drag, carry and drop exist; path and image don't;
- a refused gesture keeps the typed draft.

**For "room for many meanings" and "meaning outlives code": owned aspects.** *Not built.* Who may relate names is Alex's and the Constitution's (POSITION 8.4).

**For "bring work back together": partial merge (POSITION 8.2).** *Prototype only:* `journal.py` merges by operations and holds conflicts, but nothing running uses it. `worktree.py` still replays.

**For "comments keep their place" and "work apart": text with element identity (POSITION 8.3).** *Not built.* The order is anchored comments first, then the text gateway, then a CRDT only if offline writing becomes near-term.

## Related documents

- [[Agora]]: purpose and experience.
- [[Dynamic Desk]]: the current design and its open questions.
- [[Previous Work]]: earlier architectures and what they taught.

<!-- exported from the desk: world frontier, Home > Handbook > How the desk is built, at event e925. Edit it there; a direct edit here makes the next export stop and warn. sha1:651bcf6c4c43 -->
