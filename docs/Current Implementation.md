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
| Look before you act, judged per thing and aspect | The clock stored outside the event log (rules became notes in a1027; scripts retired into verbs) |
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
python test_scene.py            # 25 tests of lenses, gestures and the fence
python screen.py frontier --as me facts porch/main 2 shot   # the painter in headless Chrome, on a copy of the world
```

**The CLI.** `explore.py <session> --as <actor>` reads command lines from stdin and prints a receipt for each.
- Blank lines and `#` lines are skipped.
- A new session name is an empty desk.
- A refused line stops the rest: `stopped: N later line(s) not run because this one was refused ... Not run: a | b`. With `--whole` (a736) each line is one command, so a `;` in it is words. A line that nothing answers then prints `MISS ...`, which stops nothing.
- Flags:
  - `--window <name>` gives one actor a second reader;
  - `--reset`;
  - `--dump` prints a JSON snapshot, with the clock and each rule's state (its note's id, home, author, fired, failed, skipped, broken; a1027);
  - `--shape` prints the desk without ids.
- The default actor is `jeff`. Actor names are lowercased labels that the caller supplies; nothing authenticates them.

**Through deskd.** Without `DESKD=off`, each line is posted to a running deskd (default `http://127.0.0.1:8780`), and the file is the fallback.
- Lines stay local (under the lock) when `--window` is given or when any line starts with `!`.
- Through deskd, a refusal stops the later lines too and names them (a736; before, they ran). If deskd stops answering mid-run, the rest are not applied. `/api/do` takes `"whole": true` for a line that is one command.
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

**Reading a chat shows what's new to you** (a744). `read <chat>` with no `:3`, `#` or `tail=` prints only the lines added since this reader (observer) last read that chat, their own included, under one header `(n earlier lines folded; read <id> :3 for all)`. With nothing new it prints `(nothing new since you last read; n lines; read <id> :3 or tail=<n>)`. A reader's first read of a chat prints its last 10 lines under the same header. `:3`, `#sections` and `tail=` print as before.
- Appending is not reading (a656), so after you append, your next read still shows what others added before your line, and your own line.
- The desk keeps, per (observer, chat), the run of lines it has shown, `lo..hi`, and a digest of lines `[:hi]` (`desk.py` `_chat_body`, store `_chat_reads`). A plain read, `:3` or `tail=` extends the run; if the lines it was shown were rewritten since, the next read starts over as a first read. A room's narrated look extends it too (a951; `desk.py` `_chat_shown`, the one rule every look at a room's talk calls): the lines it prints extend the run as `tail=` would, and a line it cut with `…` is a hole in the run, not read, unless the run already held it whole. When a look or a `tail=` starts past the end of your run, the lines in between are holes too, never shown at all (a986, talk step 3a4): the run keeps its start instead of starting over, so nothing is skipped. A run is `(lo, hi, digest, holes, unseen)`, `unseen` the holes never shown (older runs have four fields, read as no unseen); a plain read starts at the first hole, prints on from there, and clears them; `tail=` and `:3` clear the holes they cover. Only with no run, or one rewritten since, does a look or `tail=` start the run afresh at the first line it shows.
- The read marks the text seen only when the run reaches line 0. A read that folds lines you never saw (a first read of a long chat) does not unlock a rewrite, retitle or remove; after one `read <id> :3`, a read that folds only lines you have seen does.
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
- The aspects are `prop:<k>`, `title`, `text`, `due`, `tags`, `comments`, `links` and `place`; `contents` is used for a create inside a surface. A verb the table doesn't know touches every aspect. `remove` counts as `place`, as the other placement verbs do: the subject and what it says survive, and undo puts the appearance back. `put <card> above=|status=` (a1081) is not a placement: it touches `prop:status`, `prop:priority` and `prop:rank`; `put` with a move's arguments is `move`, and counts as `place`. `reply` (the chat verb) touches `text`.
- Three refusals:
  - `you have not looked at a04 yet; look, examine or read it first` (never for adding a line to a chat, a834);
  - `stale: a04 changed since you last saw it (e15 prop by other); look at it again before acting`;
  - `you have not seen a04's text; read a04 shows it before you replace it`. This applies to the replacing verbs rewrite, replace, retitle, rename, edit, due, prop and untag.
- What counts as having seen something:
  - an outline line marks title, place, due and props (not text or tags);
  - `read` marks title, tags, due, comments, links, props, and the text only when the whole body printed (a chat: when every line has been shown to you, see Reading a chat);
  - `where` marks place;
  - `examine` and `pivot` mark everything;
  - a table marks its columns;
  - `scene` marks what each node printed;
  - your own act marks the aspects it wrote, and its receipt marks nothing more. What a `create` made it marks whole (title, text, tags, props: its maker wrote all of it), while the surface it was made in is marked for `contents` only (a1190: the `contents` change of 30 Sep had marked the made thing for `contents` too, and its maker was refused a rewrite of the `text=` they had just typed).
- An aspect never printed is judged from event 0.
- A recorded event is judged by the verb it carried out (`event_aspects` in `desk.py`), including one made through a selection or by a rule.
- A change to one prop never blocks a change to another, and the same prop still refuses.
- Your own changes from the same window never make you stale; a change from your other window does, and the refusal says so.
- A change your rule made as you while someone else tripped it counts as someone else's (a687; `rule_did_unseen` in `desk.py`): it makes you stale, and the refusal names it (ran: `stale: a697 changed since you last saw it (e898 prop by your rule r2, tripped by pike)`). Its tripper saw it on their receipt, so it does not make them stale.
- An undo counts as touching what it reverted.
- `create` and `comment` are never refused as stale.
- Adding a line to a chat is never refused as stale (a656): `append` or `reply` on a chat, or `edit` with only `append=`, replaces nothing. It is not refused as unlooked either (a834): a chat you have never looked at takes your line, and the act marks nothing seen, so a rewrite, retitle or remove still needs a look or read first. The receipt speaks from your read run (see Reading a chat; `desk.py` `_chat_behind`), not from who touched the chat: `2 lines from others you haven't seen; read <id>` counts lines by others after the end of your run, and those a look or `tail=` skipped past (a986; your own never count, and lines a first read folded do not either: they were there, and the read said so); lines by others a room's look showed you cut are said apart, `1 line from others you were shown cut; read <id>` (a951), after the unseen count when there is one; `you haven't read this chat; read <id> to see it` when you have no run (a `look` at the tree is not a read; a room's narrated look is, see Rooms); `this chat was rewritten since you last read it; read <id> to see it`; otherwise nothing. Making a chat with `create` starts your run over its first lines (`_chat_made`). When others had changed it since your last look, your act also marks nothing seen, as before (a656). Appends to notes and other kinds are fenced as before. (`desk.py` `_adds_line`, used by both `cmd_do` paths.)
- A subject-id target (`sNN`) is judged by whole revision.
- Rules act without the fence.
- The fence coordinates honest actors; it is not access control.

**Undo.** `undo eN` reverts an event and records the reversal as a new `undo` event. A bare `undo` reverts your own latest change that hasn't been undone; a change your rule made while someone else tripped it is skipped (undoing it would undo their command, its cause).
- A composed verb is undone whole: contiguous events with the same `via`, `cmd` and author, and no cause.
- A rule's consequences are undone with their cause.
- Only the latest change to a thing can be undone. For an event that changed several subjects (`restore_subjects`), a later change to any of them stops the undo.
- An event marked external (`launch`) cannot be undone.
- There is no redo (an undo cannot be undone).
- Undo is neither fenced nor limited to the author.
- A world verb's use is undone whole, all its steps.
- Undo kinds: `restore`, `restore_props`, `restore_subject` (a whole copy of the subject), `restore_subjects` (whole copies of several, for `put above=`, a1081), `drop_comment`, `reopen`, `drop_link`, `restore_link`, `reorder` (a tiled swap), `delete` (with `delete_subject`), `external`.

## One language

`explore.py` on stdin, `POST /api/do` on the server, a gesture in the painter, a resident's `>` line and a world verb's steps all carry the same kind of line.
- Commands may be joined with `;` or newlines. They run in order and stop at the first refusal; earlier steps are not rolled back.
- A call runs at most 4 `read` or `examine` commands; the rest are listed as not run.
- A `script` line keeps its `;` (and is refused whole: scripts are verbs now, a1027).

| Family | Commands |
|---|---|
| Reading | `look [id] [:1-:4]` (`look` alone, in a world with rooms: your room, narrated; `look <room>` with no depth: that room, narrated from where you are; see Rooms), `open` / `close`, `read id [#n\|#name\|:3\|:full\|tail=n]`, `examine` (`x`, `ex`), `where`, `verbs`, `pivot`, `find`, `table <sel> [cols= by=]`, `compare`, `history [id]` (last 12), `why`, `rows <source>`, `scene <lens>`, `export`, `rules`, `scripts` (only says scripts are verbs now, a1027), `vars`, `help` (`?`) |
| Changing | `do <verb> <target> k=v`, `undo [eN]`; pair verbs `swap`, `beside`, `match`, `link`; world verbs (`<word> …`, `do <word> …`, `use <id> …`) |
| Defining | rules and verbs are notes (see Rules and World verbs; `rule`, `script` and `run` only name that door, a1027); `set <name> = <id\|title>`; `clock [YYYY-MM-DD\|now\|follow]` |
| Moving | `go <room> [:1]`, `go`, `rest [:1]`, `wake <name>` (see Rooms) |
| Branching | `worktree`, `worktree fork\|diff\|merge <name>` |
| External | `sync`, `launch` (harness) |

**Verbs.** `examine` lists only the verbs that apply to a thing right now; `help <verb>` gives the arguments and one example. `examine` and `verbs <id>` show the layout verbs only where they are at hand (a990, rooms step 2b; see Rooms, Verbs by room): elsewhere they leave out `resize raise lower tile untile fold unfold match`, show `move` with `into=|before=|after=` only, and end with one line, `layout verbs are at hand on the Desktop`. Nothing is locked: every verb works from every room.
- The verbs this desk does: `move place put resize raise lower remove tile untile rename group create fold unfold append comment resolve check link unlink retitle rewrite replace sort prop tag due launch`.
- The registry (`moo.py`) holds 35 (`put`, a1081). The specialized ones (`split gather dedupe reveal reply tidy stack done`) are refused here, with `help` naming the alternative.
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
  - `place <subject> into=<surface>`: a new appearance;
  - `put` on a task's card (a1081, for a1069; named in Pike's c1202, one word, one meaning): `put <card> above=<card>` gives it that card's `status` and `priority` (removing its own when the other has none) and a `rank` just above it; `put <card> status=<value>` sends it to the bottom of its priority group among cards with that status. The house picks the rank (steps of 1000, halved between neighbours); when a gap runs out, or the card it goes above has no rank, it renumbers that group quietly, their order unchanged. One event, `put`, undone whole (`restore_subjects`); the receipt names the status and priority it changed, the rank, and any card renumbered. The card it goes above must have been looked at. A put that changes nothing succeeds with `already there, nothing moved` and no event (a825). `put` was already a synonym of `move`, and still is: for anything but a card, and for a card given `into= before= after= to= by=`; `put above=|status=` on anything else is refused, naming its kind. Over a selection `put` is still `move`;
  - `tag add= remove=`;
  - `due on= | clear=1`;
  - `append line= [section=]` (on a chat the world signs the line and it is never refused as stale: see The world);
  - `rewrite text= [section=]`;
  - `replace old= new=`: one exact passage, which must appear exactly once (refused with the count otherwise); fenced as rewrite is; the receipt shows the passage replaced and what replaced it;
  - `retitle title=`;
  - `check item=n`;
  - `comment line=`;
  - `resolve id=cNN [line=]`;
  - `link to= as=`;
  - `unlink id=lNN`;
  - `resize to=WxH` (at least 40×24).
- Most verbs go through `World.apply`. `prop`, `tag`, `due`, `launch`, `put above=|status=` and the tiled `swap` write their events directly. A new primitive still needs Python; a composition does not (see World verbs).

**Selections are the shared noun phrase.** The same grammar names a verb's target, a `find`, a view's `query=`, a rule's trigger, and a lens's `of`, `the` and `only when`:

```text
kind:note|task  tag:x  in:f04  title:agenda  ?word+word  prop:status=done  prop:k
comments:open  comments:any  links:a04  parts:a30  part-of:a20  answers:a1006  answered-by:a1008  unanswered:alex
due<2026-09-20  due>today  age>7  age<3  hidden  also:a18  a20,a22  -tag:done
```

- Terms joined by commas or spaces are ANDed.
- `parts:` and `part-of:` follow only `part-of` links, in one direction; `answers:` and `answered-by:` (a1027) follow only `answers` links the same way: `answered-by:a1008` is what a1008 answers, `answers:a1006` is what answers a1006.
- `in:`, `also:`, `links:`, `parts:`, `part-of:`, `answers:` and `answered-by:` accept a title or a `$handle`.
- A target may also be one id, a unique quoted title, `desk`/`root`, or a handle:
  - `$<name>`, a handle set by `set` or `create … as=`;
  - or any blank that names a thing (below);
  - or `corner:<name>` (a1027): the corner whose `actor=` is that name, someone's sill; `no sill for '<name>'` when there is none. It is the one place a name becomes a room (`desk._resolve`), so when persons have ids (a1016) this is what changes.
- **Blanks** (a806, rooms step 2a; `blanks.py`, the one filler for typed lines, world verbs and rules alike): `$here` the room you are in (in a rule, the rule's home: the room holding its note, a990, a1027); `$here.<prop>` a prop of it (`$here.talk`, `$here.describe`; refused, naming the room, when it has none); `$new` the thing made most recently earlier in this reply, of any kind (of several made by one line, the last; refused when nothing earlier in this reply made anything; a new reply starts fresh, so it never reaches back; the receipt ends `($new = a850)`; a948: in a reply where `$new` is not yet used, the first receipt of a line that made something ends `(next lines in this reply can call it $new)`, once per reply, where a guessed id would otherwise come next); `$today` the clock's date; `$me`; `$<handle>`; in a verb `$1 $2 $*` and `$this`; in a rule `$item`, the thing it fired on; and a part of any thing a blank names (a1027; `blanks._part`): `.title` its title, `.maker` who made it (the actor of its create), `.<prop>` one of its props (`$item.asked_by`, `$1.status`), refused naming the thing when it has none. They are filled after the line is parsed, as values, once: in targets, selections, and k=v values that name things (`do prop f581 describe=$new` stores and prints `describe=a789`); a read's words too (`look $new`, `go $here`). Text is words by default (a965; `blanks.fill_arg`): in a typed `do` line an argument the verb's own list declares as text (`<str>`, as `help append` prints `line=<str>`; today `line= text= title= old= new= words=`) is never filled, one it declares as a target, selection, id or date is (`into=$here`, `query=kind:note,in:$here`), and any other (a prop value, untyped, including `wake=` and a create's extra props) fills only when the whole value is one blank (`describe=$new`), never a blank inside other words (`next='write $today in the log'` stays as typed). Inside a verb or rule (templates their author wrote) every value is filled, and a filled value is never filled again. A typed `$item` refuses (`Did you mean $new…?`); `$5` is not a blank; an unknown `$name` refuses; nothing stores a blank's own name. A reply is the lines of one call (explore.py, the desk tool, one painter request) or of one resident's reply: explore.py, deskd and the house pass a `reply` token with each line, and what was made is kept per reader and reply (`DeskKnife._made`). A literal dollar sign is written with a backslash before it, in both; `\$today` stays literal.
- An unknown `word:` term is refused with the list of known terms. `prop:k>v` is not a comparison: it is read as a prop name and matches nothing (see Evidence).

**Rules.**
- **A rule is a note tagged `rule`** (a1027), placed in the room it acts from. Its text is one line (`#` lines describe it): `when <selection> do <verb> …` fires once on each thing that enters the selection (a thing that leaves it is forgotten, so entering again fires again: a commission landed, reverted and landed again is due a live check twice; `now=1` includes what matches when it is saved); `on <verb> [by=<actor>] do …` fires on each such event. It ignores events made by rules, and it treats `edit` as append, retitle or rewrite.
- Rules also run on clock changes and after `!` injections.
- A rule's `author` is whoever last chose what it does (a1027, Juniper c1075): its note's maker, or the last to write its text or tag it `rule` (`DeskKnife._rule_author`, read from the log; an undone event counts for nothing). When someone else writes it, their receipt says `this rule now acts as you (it acted as juniper)`.
- **A rule acts as its author** (a687, decided in a683 by Sable, Juniper and Pike: a rule is a standing act its author chose, so crediting whoever tripped it misleads). While it fires, the world's actor is the author (`desk_knife.py` `_run_rules`), so its events say `by=<author>`, carry `via "rule rN"`, `cause` and `tripped_by=<tripper>`, and a chat line it adds is signed `Author: …` with no `via`. What it prints and marks meanwhile is recorded for the tripper (`_firing_observer`), who sees it on their receipt: `~ r2 fired on a697 as sable: ok prop a697 last=pike`.
- The author was not there, so the deed is theirs but unseen (`rule_did_unseen` in `desk.py`): it makes them stale on what it changed (see The world), a bare `undo` skips it, and their next `!!` line names it: `e898 your rule r2 did prop a697 last=pike (tripped by pike)` (in the grouped form, `your rule r2: …`). The tripper's `!!` line leaves it out; anyone else's reads `e898 prop a697 by sable via rule r2`. `why` reads `sable by rule r2, tripped by pike`.
- A rule with no recorded author (a note made before its world's log began) runs as whoever tripped it: its events are signed by the tripper, carry no `tripped_by`, and its chat line reads `Pike, via rule a1060: …`. Writing its text again gives it an author. (Rule ids are now their notes' ids, so `via rule a1060`; the `r2` in the examples above is from before a1027.)
- **Known obligation, not built:** there is no permission layer. When one exists, a firing must be checked against its author's rights at firing time, not the tripper's and not the rights the author had when defining it (a683).
- Cascades stop after three passes.
- A rule is a template (a806): its target, values and selection are filled by the one filler each time it fires (`$item`, `$item.title`, `$today`; in a `when` selection `$today` now follows the clock instead of freezing when the rule is defined). `$new` refuses: a rule has no earlier line.
- **A rule lives in the room holding its note** (a990 (5), finished by a1027; `verbs.room_holding`), wherever its author goes or sleeps: `$here` in it is that room (in its selection, target and values; a rule in no room refuses `$here`, saying why), and a bare verb word in its action means that room's verb. Move the note and it lives there, judged there like a save: the mover's receipt says `~ rule a1060 saved: … (lives in Lounge (f182); acts as juniper)`, or `saved broken` when its word is not at hand there. `rules` and `examine <rule note>` say where it lives.
- The action may be a verb made in the world (a990): `when tag:messy do tidy` (its words after the word; `$item` when none are given), or `do use <verb id> [words]`. It runs through `verbs.try_line` with the rule's context innermost, so it is found from the rule's home, strictly: at fire time a word only another room answers refuses (`~ r3 could not tidy a1013: tidy is at hand in …`).
- **A rule is checked whenever its text, home or author changes** (a1027; `DeskKnife._rule_parse`, `_rules_sync`), strict to its stored text: a bad term, an unknown verb, a blank a rule doesn't have (`$new`, `$itme`), a misspelled term in a selection target (not read as a prop), `run`, and a world verb's word that only another room has (naming the door, `write use a995 [words]`). A rule that fails is still saved, **broken**, with the reason (`~ rule a1066 saved broken: craete is not a verb here…`), and never fires, never running an earlier version (a598). A valid one re-arms: what matches then counts as handled, so a fix never sets off a flood. A destination such as `into=` and the rest of a selection target are not checked. A selection target that matches nothing is nothing to do, not a refusal.
- **Quiet** (Alex, a585; Juniper c1075): a narrated look never lists rule notes; the tree marks them (`· rule`, `· rule, broken (rules says why)`), since the tree is the builder's inventory of a room. `rules` lists every one: its note's id and title, where it lives, who it acts as, how often it fired, failed (with the last reason) or was skipped, and whether it is broken; `examine <rule note>` says the same. A firing that finds no sill (`corner:<name>` with no such corner) is counted as skipped, quietly, and not printed. Undo of the command that set rules off undoes their firings, and its receipt names them (`…, and 4 rule consequence(s): a1060, a1062, a1064`).
- `rule when …` and `rule on …` typed refuse, printing the exact line to write instead: `do create $here kind=note tags=rule title="<what it does>" text="when …"`; `rule drop` and `rule home` say to remove or move the note.
- `why <id>` shows the events that placed a thing and the rule that would act on it next.

**Scripts are retired into verbs** (a1027): a script was a verb nobody declared. `script` and `run` refuse, and `scripts` says so, naming the door: `scripts are verbs now: make a note tagged verb (help verbs); run X is just X` (`run arrive is just arrive (nothing answers to arrive yet: make it a verb, or just look)`). The one script the house had, `arrive`, printed the old tree; it was dropped, not rewritten, since every wake ends in `look` (the house's default wake is `look`). A world that still holds old scripts says so in `scripts`; they never run, and `export` no longer writes them.

**Views.** `do create <surface> kind=view title=X query=<selection>` makes a view; with `cols=` (and `by=`, `desc=`) it prints as a table. You can't move a thing into a view, create inside one, or tile, group or sort one.

**Rooms** (a678, rooms step 1; `rooms.py`). A room is a surface with prop `role=room`, or `role=resident` (a corner is its resident's room). Its props: `describe=<id>` (the note that describes it: its text, or its title when it has none), `talk=<id>` (the chat where talk here lands), `shows=<selection>` (what is at hand; default its children), `home=<selection>` (default `in:<the room>`; must be invertible: `in:<surface>` and `tag:<word>` terms only. Step 1 only checks it, and a narrated look says so when it isn't; nothing lands there yet).
- Every actor is in exactly one room. It is not stored apart: an actor's room is the `to=` of their latest `go` event (target the actor, `args to= from=`, `changed` empty, fence aspect `presence`). Someone who never went anywhere is in their own corner (the surface with `role=resident actor=<them>`), or, with no corner, in Home (the outermost `role=room` surface). A room since unmarked or removed sends them back to that default. **Alex is not placed** in step 1 (a678 (8)): `go` refuses him and his bare `look` is the tree.
- `go <room>`: by id, by title, or by a word of the title (case aside, `Sable's` answers to `sable`); from anywhere. It records the event and prints the narration. A surface that isn't a room is refused with the list of rooms; several matches are refused with the list, except that your own corner wins (`go corner`). Going where you already are makes no event. `go <room> :1` walks without looking (the receipt only; nothing counts as seen). `go` alone prints where you are and who is in each room (each marked in the words a narration uses, `(asleep)` or `(resting)`; a948).
- `rest [:1]` (a806): go home to rest, to your corner (Home if you have none). The go event carries `via=rest`, so history reads `… by pike via rest` and tells being carried home from walking. The house rests a resident with `rest :1` (after `> rest`, the quiet limit or an empty reply); how long is the house's to keep.
- `wake <name>` (a1062; `rooms.cmd_wake`): end that resident's rest now. It sets `call=<you>` on their corner, signed by you, the event marked `via=wake`, with no look needed first (a call, like `go`); the house delivers it at once and their wake says who called and which of your lines was held for them. It refuses yourself and a name no corner has. A line to a resting resident from a resident or an agent waits for their next wake, and the speaker's receipt says so and when; a person's line (a surface says `person=<them>`) still calls at once (see Residents: the house, News).
- A bare `look`, in a world with rooms and for anyone but Alex, narrates your room: `You are in <title> (<id>).` (`, your own corner.` in yours), a date and time line (below), the description (cut at 120 words, with a pointer), who else is here (`Here with you: Pike (resting), Sable.`). a948 names each in one of three words: asleep (their corner says `want=rest`, or `status=asleep`), resting (the house runs them and they are between turns; `resting until 21:40` when they timed the rest), or plain (in a turn right now, or someone the house does not run). Whether a resident is mid-turn is the house's own observation in `house-state/<world>/house.json`, read once per print through `scene.house_rows` (the reader behind `rows house`), so a stopped or stale house calls no one it runs awake, and a world with no house state (a copy, a test world) names everyone plain. A resident asleep is never listed there, and the room says `Sable is asleep here.` instead (`(their own corner).` in theirs) (a806). Counted: Jeff (the world's own agent, `World.me`), residents, and actors who have gone somewhere; each is in their default room until they go, what is at hand from `shows=`, one line and one id each with no geometry (kind, title, and a task's status, owner, due; a surface's count; at most 12, then a pointer), skipping the describe and talk notes, then the talk chat's last 3 lines as signed, each cut at 35 words, and how to speak (a951; `rooms.py` `speak_verb`): the word of a world verb that appends to `$here.talk` (in your own room) or to this talk by id, and that its word alone would run for you (carried or on the house; `verbs.find` decides), found at print time and never named in code: today `(say <words>; read <talk> tail=20 for more)`; with no such verb, `(say: do append <talk> line=...)`. When lines by others came between your read run and the lines shown, the hint counts them instead: `; 7 earlier lines from others you haven't read: read <talk>`; they are holes in your run (a986), so a plain read shows them. `look <room>` with no depth (a948; by id, `$here`, title, or a word of its title as `go` takes them; `look corner` is your own) narrates that room from wherever you are: `Lounge (f182), seen from Juniper's corner (f581).`, then `Here: …` or `No one is here.` in place of `Here with you`. It moves no one and counts as seen exactly what a look in the room would (it is the same `rooms.narrate`, so talk lines it prints whole extend your read run through a951's `_chat_shown`). `look <room> :2` is the room's tree; `look <id>` on anything that is not a room, `look :N` with no id and `look desk` are the tree, unchanged, and Alex's `look <room>` is the tree. The date line (a948; `rooms.clock_line`): `It is 29 Sep, 21:14.`, the day from the desk's clock (`DeskKnife.today`, the one that fills `$today` and counts `age<` and `due<`) and the hour from the house's wall time. With the clock set by hand to another day it names both: `The desk's clock says 27 Sep, 2 days behind the house's time, 29 Sep, 21:14: …`; with no clock, `No clock is set here; the house's time is …`. The clock is a day with no hour, so any other day is said. In a world with no rooms (the suite's) a bare `look` is the tree as before.
- **What a narrated look counts as seen** (a678 (7)): the room's title, the describe note's title and text only when printed whole, and the talk chat's title, plus its text only when your read run then holds all of it with no holes (a951: the lines it prints extend your run as `tail=` would, and a line cut with `…` is not read, for the receipt or for a rewrite; see Reading a chat). Things listed at hand are not marked at all: look or read one before acting on it (`you have not looked at …`). A chat line still lands after a narrated look, since adding to a chat is never stale.
- A go is journaled like any event (history lists it; a fork copies it; a worktree merge replays `go` lines, and they never conflict) but outside undo's reach: `undo eN` on a go refuses (`eN is a go: where you are is not a change to anything in the world, so undo leaves it…`), and a bare `undo` passes over it.
- The `!!` line folds walking: at most one per actor, their latest room (`e975 pike went to Lounge`; grouped: `pike: undo in e900, now in Lounge`).
- `rows house` has a `room` field, so Who's home can show where each resident is.
- **Verbs by room** (a990, rooms step 2b; `rooms.layout_at_hand`, `layout_pointer`): rooms SHOW the verbs at hand and lock nothing. A room whose prop `verbs=` names `layout` (the Desktop: `do prop <Desktop> verbs=layout`) has the layout verbs at hand, and so do the rooms inside it and anyone placed nowhere (Alex). `examine` and `verbs` leave them out elsewhere and add `layout verbs are at hand on the Desktop`; in a world where no room says `verbs=layout` they list everything, as before. `examine` also lists the world verbs at hand in your room. A room is a namespace for world verbs (`on=<room>`; see World verbs).

**Clock.**
- `clock` shows the desk's date.
- `clock YYYY-MM-DD` and `clock now` set it.
- `clock follow` tracks the wall date and reports the days that passed.
- `age<N` and `age>N` need a clock.

The clock is a desk attribute, not an event: it is not in `history` and can't be undone, but a worktree carries it and a merge replays it. Rules (since a1027), lenses, styles and world verbs are ordinary notes.

**Worktrees.** `worktree fork <name>` copies the session into `<session>@<name>`, with a journal of the command lines made there, including `clock` lines (a rule is a note, so it is journaled like any act).
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
  - a room's id (a990, rooms step 2b): in that room, and the rooms inside it (a room is a namespace);
  - any other word: that actor.
- **A verb's word is not a name** (a990 (4), Pike e1804, F25): verb notes stay out of title resolution (`desk._resolve`), so `read tidy` never means a verb note and two rooms' tidies never make it ambiguous; it refuses with `'tidy' is a verb's word, not a name for a thing: the verb note is a995 …`. A verb note is reached by its id, or through `help` and `examine`.
- **Lookup** (`verbs.find`), nearest first: carried by you, then on a thing named among the words, then the room the line stands in and each room around it (a990), then the house. Two verbs at one level refuse and name both. It is tried only after the built-ins fail: when the first word is no command, or for `do <word>` when `<word>` isn't a built-in verb or is one of the retired specialized words (`tidy reply stack …`, a990: a world verb answers those before the desk's refusal, and `help <word>` describes it). `use <id> [words]` names a verb exactly, from anywhere, and refuses one that someone else carries.
- **Nothing at hand, but another room has one** (a990; Pike e1782, Sable e1786: forgiving to people, strict to stored text): a typed line runs it while it is the only one; two or more refuse naming every door: `tidy is at hand in Lounge (f182, use a995) and Board (f155, use a1001): go there, or use <id> [words]`. A stored line never guesses: it refuses naming the doors even when there is one.
- **Where a line stands** (`verbs.standing`): a typed line where its typer is (`rooms.room_of`; Alex, placed nowhere, has no room level); a template in its own home, never where its author or caller stands: a verb's lines where the verb lives (`verbs.home`: its room, or the room holding the thing it is on; carried and house verbs have none), a rule in the room holding its note (a1027), a lens gesture in the room holding its lens (deskd sets `desk._act_home` from the painted lens's id). The template kinds carry it in `blanks.Ctx.home`.
- **Stored text names its door when saved** (a990 (2); `verbs.check_lines`): a rule's world-verb action, a wake line set with `do prop <corner> wake=`, and a verb's own lines are judged where they will live; a bare word that only another room's verb answers refuses the save, naming the door (`write use a995 [words]`), except that a rule is saved broken instead (a1027: a rule that fails its check is kept, says why and never fires). A word nothing answers is left alone, as before. A verb is judged after any act that makes or changes it (its word, where it lives, its lines: `verbs.state` / `check_change` around `DeskKnife.cmd_do_knife`), and a refused act is taken back whole (`verbs.rollback`: its events undone and dropped, so nothing changed). The same check refuses a second verb with one word in one room: `a1001 would be a second tidy in Lounge (f182): a995 already answers to tidy there…`. Not judged: a lens's gestures when the lens is saved (a lens act is only strict at run time), and a verb's lines again when the thing it is on moves to another room.
- **Blanks:**
  - `$1 $2 …` refuse when there are too few words;
  - `$1.title`;
  - `$*` is the rest of the line after the verb word exactly as said, quotes and `;` included (a806; before, it was the words re-joined);
  - a word that is itself a blank (`$new`, `$here.talk`, a handle) is filled where the verb was said, so `$1` carries its value;
  - `$me` is the caller and `$this` is the thing the verb lives on (refused in a verb that lives on none);
  - every blank of a typed line too (`$here`, `$here.<prop>`, `$new`, `$today`: see One language, Blanks). The body is a template: each step is filled by the one filler after it is parsed, text values included, and a filled value is never filled again, so `say`'s `$*` carries `$here` or `a; b "hi"` untouched;
  - `$new` inside the body is the last thing an earlier step made; after the use, the caller's `$new` is the last thing the whole use made;
  - a use whose step is refused is a refusal (`(<word> <aid>: …)` then the reason), the steps before it still done;
  - a line that shlex can't split (an apostrophe: `say it's fine`) still reaches a verb, split on spaces.
- **The say verb** (a806's proof, one note for every room): `do append $here.talk line="$*"` lands in the Lounge's talk from the Lounge and in Shop talk from the Board, signed; in a room with no `talk=` it refuses, naming the room.
- **Limits and provenance:** nesting stops at depth 5. Events are tagged `verb_run: "<word> <aid>"` and show in history as `(verb <word> <aid>)`. `examine` lists the verbs on a thing and, on a line of their own, the world verbs at hand in the room you stand in (`at hand in Lounge, made in the world: tidy (a995)`); `help <word>` describes the verbs you can reach, a room's with its door.
- **Misses:** a reach that nothing answers is appended to `reaches/<world>.jsonl` (not in git). This includes prose after `>` that cannot be parsed, such as an unclosed apostrophe (a736). The desk raises `Unanswered`, a kind of `Refusal`. For a resident's `>` line (whole) the receipt is `MISS ...`, not `ERR`, and the house also logs the line in the world's Misses chat (see Residents: the house).
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
| `gap`, `scroll none\|scroll\|end`, `fold ["label"] [open] [float] [handle <role>]`, `measure <n>ch`, `verbatim`, `lines <min>..<max>`, `share <w>`, `hint "…"`, `plain`, `peek` | Paint words, passed to the painter. `fold` is the viewer's own toggle, with no event, folded to begin with unless `open`; `float` draws the open contents over the page below the handle (a menu: it opens for a moment, and Escape or a press outside closes it); a folded part gives up its `share` and hides its children, except a child marked `peek`, which stays shown under the handle as the folded part's summary; only a direct child peeks, so a peek under a hidden part stays hidden (`test_peek_paint.py` paints this in a browser; a1032: a resident's Now cards on a folded Desktop tile; `help lens`); the label is a template filled like text (`fold "$title"`); the painter's fold handle wears the role named by `handle <role>`, else `fold` (`menu` when floating), over `tool`; `plain` turns off code runs. `share` is a child's weight along its parent's axis; on the root it takes the window's height, and a grid with a share divides its height among its rows, so a `scroll` inside it scrolls within the window instead of the page growing |
| `role <name>`, `role <name> when <selection>` or `role <name> when $x <op> v` | Look, by a role from the lens's style; an unknown role is refused with the list. A role with `when` (a1105) is taken instead of the plain one when its test holds for the part's thing, judged as `only when` judges (a missing value does not hold), after the part's lets and guard; several may be given and the first that holds wins, else the plain role. The scene prints the role it took and why, `card a703 [task.objective, since prop:objective=open]`, and the painter paints that role. A selection test is a read in R; it is not in a gesture's fence (a look, not a meaning). The Desktop's cards: `card : column, role task, role task.objective when prop:objective=open, …` |
| `text <template>` | Words (template names below); quote to keep commas and hashes |
| `clamp <N>` | At most N lines, or N repeats; both printers say how many are left |
| `of <selection> [as f]` + `each <part>` | Repeat over a selection, over ids named one by one (each printed with its state: unplaced, gone), or over a row source: `sections:<id>`, `comments:<id>`, `messages:<id>` (`item who said index at`, where `at` is the line's time from its append event: `08:15` today, `29 Sep 22:38` otherwise), `inbox:<name>` (every chat line for that person, oldest first like a chat, so a lens shows the newest with clamp last N, scroll end: `item chat who said at open index eid`. A line counts when its chat's members name the person (a direct chat), or it calls @name outside quotes; @everyone and @all don't count, so it is narrower than what reaches a resident (Alex, 30 Sep). `open` is `yes` until the person writes in that chat after it; rows are keyed by `eid`, the event that added the line), `actors`, `events`, `worktrees`, `house[:<corner>]`, `turns[:<corner>]` (each resident's last replies, oldest first like a chat: `resident corner turn at said acts`, where `acts` counts the lines that began with `>`). An empty repeat prints `(empty)` |
| `the <selection> [as f]` | Exactly one thing becomes the current thing; prints `(empty)`, or `(ambiguous: …)` with nothing built under it |
| `as <name>` | Names this part's thing as a frame, read below as `$name.field`. Shadowing a built-in or an outer frame is refused |
| `over $<list>` | Repeat over a list field or derived rows; `$it` is each value |
| `count <selection>` | On a part that repeats nothing (a1101): `$count` is how many things the selection (or a row source) finds, without drawing them, on the part and below it, and before its guard, so `only when $count > 0` works. Prints `· count N of <selection>`; a gesture here is fenced on that membership. Refused on an `of`/`over` repeat, which has its own `$count`. The Board: `rested : text "$count paused", count kind:task,prop:status=paused` |
| `by <prop>[, <prop>]` | On an `of` repeat (a1081, for a1069): its members in the order of those props, numbers ascending, then words, a missing value last; ties keep the selection's order, which is the order the appearances were made (a row source sorts by its fields). Applied in the scene, before `clamp`, so `scene`, `look` and the painter show one order, and the repeat prints `· N of <selection> by <props>`. The names after the comma are more props, so a prop named like a lens word (`role`, `text`) can't follow `by` there. A clamped repeat's membership read records the props, and deskd re-orders before comparing the prefix. Refused without `of`. The Desktop's lanes: `of kind:task,prop:status=doing, by priority, rank` |
| `derive <name> = <interp> <inputs>` | A named calculation from a closed list: `day-n`, `days-from`, `day-or-time`, `weekday`, `week-of`, `time`, `date`. It prints its inputs and result |
| `capture <field>=<value>` | Use this value instead of following; prints `(now X: differs)` when the world has moved on. Kept out of the fence |
| `at item` | The appearance's own world geometry, only under a `free` parent |
| `spread x <a> step <n\|$prop> to <max>` | Computed placement by index, printed as `(spread, not its place in the world)` |
| `lens <name>` | Place another lens, whose name may be templated (`lens $kind`); a lens may not contain itself |
| `only when <selection>` or `only when $x <op> v` | The part exists only on a match. A value test (`= != < > <= >=`, and `has` / `!has`: the words contain the value, ignoring case; a value with a `$name` in it is filled, so `only when $said has @$me`) prints its inputs; a missing value counts as absent, not false |
| `carry`, `on click\|edit\|drag do <command>`, `on menu "<label>" do <command>`, `on drop <part> do <command>` | Gestures (see Gestures and their fence) |

**Template names.**
- Fields: `$title $text $kind $due $tags $id $item $count`.
  - `$count` is the true size of the nearest repeat, before any clamp, on the repeat itself, in each instance and in its fixed kids (a1101: the fixed kids had the shown size), or the size a `count <selection>` found.
  - `$n`, on a repeat's own text, is how many it shows; elsewhere it is a prop name.
- Any prop of the thing: `$place` prints `read place=…`, or `(no place)` when missing.
- Frame fields `$f.x` and lets.
- A selection (`of`, `the`, `only when <selection>`) is filled from fields, frames and host names, not from the thing's props: a bare `$actor` there stays the literal word and matches nothing, silently. Name the repeat (`of … as r`) and write `$r.actor` (a1032).
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
- `· count N of <selection>`;
- 240- and 120-character cuts, and an `(absent: …)` reason cut at 80 (a1101: a value test quoted each whole message).

The first line is `scene <lens> · for <who> · world @N`, ending `· no style=; using the default (calm)` when the lens has no `style=` prop (a1101: the fallback was silent).

**Scoped and checked (a1101).** `scene <lens> <part path>` prints only the parts the path names and what is inside them, each under `= <its full key>`, and the header says `part <path>: N match(es)`. A path is `/`-separated segments, each matching a part's name or its key segment, anchored at the node's end (`lens_ir.find_parts`): `people`, `people/list`, `list/f571`, `porch/main/people`. No match is refused with the lens's part names. Only what is printed is marked seen. `scene <lens> ok` (`lens_ir.check`) is one line: `lens L compiles: N of <budget> nodes · style pixel` (or the no-style note, or `(does not parse: …)`), else `lens L does not compile: <refusal> | L line N: <that line>`, naming an inner lens when it is the one that refused, and saying that its painter shows the last version that did. The lens name may be quoted or bare, spaces and all (`scene.split_scene_arg`: the whole line names a lens first, else the last word is the path or `ok`).

**Receipts (a1101).** After a top-level command whose events touched a placed lens or a style note (text, title, tags, `prop:style`, or its creation), `desk_knife._visual_notes` adds `~` lines to the receipt. A lens: `~ lens L compiles: …`, or `~ ! lens L does not compile: …`, as `scene L ok`. A style: `~ style S parses: R roles, T tokens`, or `does not parse: line N: …` (the painter keeps the last version that parsed); then the props the painter draws nothing for, the ones this line added each by name (`- new: role chip2 'on markk' (line 74): names no token of the right kind`), the ones already there counted by cause; then `lenses using it: <titles>; all compile`, or `now refusing: N` with a `! lens … does not compile` line for each. A style is judged by `scene.style_check`, which mirrors `style.js` (`parse`, `check`, `resolveTokens`, `prop`) line for line; `test_scene.py` runs the real file under node (`desk-shell/checks/style-read.js`) on the same samples and compares. On 30 Sep the pixel style had 15 such props: `corner 3`, `lift 1` and the like (a bare number is no length there), and `pad top gap` (style.js reads `pad` before `pad <side>`, a painter bug).

A scene has a budget of 5000 nodes (`scene.BUDGET`; 1500 until 30 Sep, a guard against runaway repeats, never a measured limit). There is no escape to HTML, CSS or script, and no arithmetic or general `if`. Anything else is refused with its line number.

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
- `carry` marks a part that can be picked up. A carry starts with the primary button on the part itself; the right button, and a press on one of the part's own controls (a fold handle, a clickable part inside it), leave it alone.
- `on menu "<label>" do <command>` adds an entry to the part's own menu. The painter opens it on a right-click or the menu key anywhere on the part (the innermost part with entries), and an entry sends its line as a click does. Editable text, a part with no entries, and Shift with the right-click keep the browser's menu. Escape, a press outside or a scroll closes it; the arrow keys move through it.
- `on drop <part> do <one command>` runs on the receiver. `$carried` is filled by deskd with the carried item's id. The receiver is the topmost part under the pointer that accepts that part, so a carried card that is itself a receiver (`card : …, carry, on drop card do put $carried above=$item`) answers a drop onto it before the lane around it does; a drop on the part it came from, or on a part holding it (its own lane's empty space), sends nothing (checked with screen.py for a1081).

The painter fills only the first occurrence of each name. Click and edit lines may still batch with `;` and may say a world verb's word (a `run` line refuses since a1027: scripts are verbs now).

**What a gesture carries.** Each painted gesture is sent with `observed`:
- `item` and `rev`;
- `reads`: `[thing, rev, aspects]` for every value that filled it or fed its derivations, and `["select", query, answer, keep]` (with a fifth, the props, when the repeat says `by`) for every membership it relied on, including the binds on its chain;
- `defpart`: the part's lens, id, path and a hash of its binding lines;
- `bind`;
- `at`;
- the whole `def` closure;
- for a drop, `carried` and `receiver`.

It also carries `gesture` (a1008), an id minted at the press. An edit's id lives on its draft (kept in localStorage with it) until the draft is answered or its words change, so a retry after a lost answer, from a re-made composer or a reloaded page, resends the same id; a click, drag, drop or menu entry mints one per press. After a lost answer the next poll repaints even an unchanged scene, so the kept draft shows both sides and can be sent again. After a successful edit, a reused element still showing the sent words is reset to its paint (the words stayed in the Lounge composer and its next blur sent them again: e1851, e1852).

**What deskd checks** (`/api/do`, in order; first, a `gesture` id already on an event is answered `already done, as eN` and nothing else is judged or done):
1. A gesture from a fallback frame is refused: "it is for reading".
2. Part identity: a gesture is admitted when its part still hashes the same, even if the lens changed elsewhere. It is refused only when the part changed and the lens moved. Every closure member is checked.
3. For a drop: the carried thing ("changed while it was in the air"), then the receiver's revision, reads and part.
4. The item, judged on the aspects its gesture read (`touched_aspects`). The refusal names the last event, its verb and its author. When the item is accepted, the actor's seen revision moves to the current one.
5. Each read: a thing passes if only unread aspects moved; a selection must give the same answer, compared as a set, with a clamped repeat comparing its shown prefix (re-ordered by its `by` props first, a1081).

Every refusal ends with "nothing was done. The view will repaint." A painted gesture is judged on what was painted, even against the actor's own later changes, and the painter never looks again on the person's behalf.

## Style

A style is a note tagged `style` and titled with its name. It is edited, undone and forked like any note.
- A lens picks one with prop `style=<name>`.
- `desk-shell/style/calm.style` is only the seed, used when the world has no note of that name.
- The style defines:
  - tokens, the only place a colour or number appears;
  - roles built from tokens. One role word is motion: `pulse` fades the part between full and 60% opacity, 2.5 s a cycle, every pulse on the page in one phase (a1140). For a viewer whose system asks for reduced motion it does nothing and the part is still. The scene print marks such a part `[<role> pulse]`;
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
| `POST /api/do` | `{session, as, line, observed?, gesture?}` returns `{text, error, events_total, line, as, created, events}`. `error` is the first `ERR` line. `gesture` (a1008) is an id of at most 80 characters; it is recorded on every event the line made, and a later post with the same id does nothing and answers `already done, as eN: …` with `events: []` and `already: [ids]`, before any fence and across restarts (the id lives on the event, in the world). Dedupe is by id only, never by words. An empty line is 400. `worktree …` lines go to worktree.py |
| `POST /api/observe` | `{session, as, lens, at, viewport, facts}`, capped at 400 facts; returns `{ok, kept}` |
| anything else | GET: a static file from `desk-shell/`. POST: 404 |

- The server is a `ThreadingHTTPServer` on 127.0.0.1. API replies are `no-store`; every reply also says `no-cache`, so a browser rechecks the painter's files and a page reloaded for new code gets it.
- deskd answers only its own pages: an `/api/` request whose `Origin` is not its own address, or that a browser marks `Sec-Fetch-Site: cross-site`, gets 403. Local programs that send neither header (the CLI, the house) are let through, as before.
- A session name must match `^[A-Za-z0-9_][A-Za-z0-9_@-]{0,63}$` (no dots or slashes), else 400. A POST body that isn't a JSON object is 400.
- Per-actor state is keyed by actor alone; the CLI keys it by actor and window.
- A new actor starts with nothing seen, and `jeff` uses the session's own slot.
- The shell polls `/api/events` every 1.5 s. The painter polls `/api/scene?view=painter` every 1.5 s and `/api/version` every 5 s, and reloads the page when the code changed, unless someone is typing or holding a part.

**Sessions.** A session is one file, `sessions/<name>.pickle`, holding the whole Python desk: world, each rule note's state (what it has handled, how often it fired; `DeskKnife._rulestate`, a1027), clock, per-actor state, observations and the last-good lenses.
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
- `lens.js` is 349 lines (30 Sep, a1008). It draws a fold's handle with its label (`▸ turns`); clicking it is the viewer's own toggle, kept in the browser, never an event.
- `viewer.js` (164) keeps continuity:
  - unchanged elements are kept by key, so a reader's selection survives another person's act;
  - drafts survive a refusal, a reload or a closed tab (localStorage `lens-drafts:…`), and so do folds;
  - a refused draft is shown with both sides;
  - a draft keeps its gesture id (a1008) until it is answered or its words change, so every retry of it is one intent;
  - it posts observations.
- Also in the painter:
  - cards move by keyboard;
  - carry and drop work: a press becomes a carry once it moves 5px, from anywhere on the card (its fold handle included); a press that doesn't move stays a click. A copy of the card follows the pointer, so a scrolling lane can't clip it;
  - code prints as runs;
  - `paint.semantic` marks buttons and groups.
- `term.js` (94) is a desk terminal in the right-hand pane by default. It sends lines to `/api/do` and keeps its history in localStorage. Each Enter on new words mints a gesture id (a1047); if the answer is lost, the line goes back into the input holding that id (kept in localStorage over a reload), and Enter on it untouched resends the same press, so deskd answers `already done, as eN` if the first got through. Typing in the line or walking the history lets the id go: the same words sent again on purpose are a new line. × closes it and the painter takes the full width; "▸ terminal" (top right) or Ctrl+` opens it again. Open or closed is remembered per world in the browser.

**The windowed shell** (`index.html`, `shell.js`, `core.js`, `apps/`) has a dock, draggable windows, and three hand-written apps: Notes, Editor and Together (`apps/third.js`).
- A window is an appearance on the `<actor> screen` surface:
  - opening it is `do place`, then `do move` and `do resize`;
  - dragging ends in `do move … to=x,y`;
  - the grip ends in `do resize … to=WxH`;
  - closing it is `do remove`.
- Other `* screen` surfaces show as "<who> has N open".
- Each app implements `text(ctx)`, what a text-only inhabitant reads for that window.
- Apps prefix `look <id>;` to their commands, so their gestures are not fenced against what was on screen.
- Every `Desk.do(line)` is one press with its own gesture id (a1047), minted in `core.js`, so no app mints or forgets one. A request that never came back is sent again with the same id, after 0.5 s and 2 s; an answer that came back, even a broken one, is never sent twice. `Desk.do(line, {gesture})` retries a press by its id, and the answer carries `gesture`. Apps don't yet carry an id of their own across a repaint (the Editor's settle, Notes' drags): each call is a new press.
- The shell loads `calm.style` as a file, and its style panel edits page memory only.

`desk-shell/natives/prose.js` is an 80-line prose editor loaded nowhere. It reads the old node shape, from before `paint`, and the compiler refuses `native` and `settle`.

`desk-shell/OWNERS.md` names one owner per file. While the old team is paused (from 28 Sep), Claude edits the paused owners' files where the command center needs it, and logs each change as a friction in Rough spots (f747); `research/command-center/FRICTION.md` is now an export of it.

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
- `wake`, the desk line run on each wake (default `look`, a1027: the old `run arrive` printed the old tree, and scripts are retired into verbs).
- An optional `model`.

**The process.**
```text
claude -p --input-format stream-json --output-format stream-json --verbose --system-prompt "" --tools "" --strict-mcp-config --setting-sources "" --model M [--resume <session>]
```
- The binary is `$HOUSE_CLAUDE`, else the newest `claude` found by `--version`.
- cwd is `house-state/<world>/<corner>/`.
- The environment drops every `CLAUDE*` variable and sets `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`.
- The resident has no tools: everything it knows comes from the world.

**The relay** (a736). Only lines beginning with `>` reach the desk. Every other line is thinking and never runs, whatever its first word. One `>` line is one command: the house sends each line with `whole` (`explore.py --whole`, `desk_mcp.run_desk({... "whole": True})`, or deskd `/api/do` `{"whole": true}`), so a `;` in it is part of the words. A quoted value left open goes on to the next lines. The lines run in order as the resident, through deskd when `DESKD` is set, else through `desk_mcp.run_desk`. The receipt is the next message.
- A refused line stops the lines after it. The receipt says how many and which (`stopped: N later line(s) not run ... Not run: a | b`). A refused line that contains a `;` also says that one `>` line is one command.
- A line that no command and no verb in the world answers (a quote such as `> I think...`, or prose with an apostrophe) gets `MISS unknown command ...`. It changed nothing, so the lines after it still run. The house logs each miss, as actor `house` so it wakes no one, as a line in the chat with prop `role=misses` ("Misses"). The house makes that chat on first need, beside Wishes: `<actor>, <date time>, reply <n> in <corner>: > <the whole line>`. The receipt ends `~ house: N line(s) after > that nothing answered, logged in <id> (Misses): ...`. `verbs.record_miss` still writes `reaches/<world>.jsonl` as well.
- A reply with no `>` line whose lines begin with a desk command word runs nothing. It gets one notice: `nothing ran: only lines beginning with > act (N lines looked like commands)`. The notice counts toward the quiet limit.
- The house's own lines keep `;` as a separator: wake strings, the status line, and verbs run by a line.

**Welcome and waking.**
- The welcome (the placed note "The door", with `$me` replaced by the name) prefixes the first message after a fresh start, a lost conversation, or a `compact_boundary` event (a compaction).
- Every wake begins `You are <actor>. Your corner is <rid>.` and its reason, then, first, who woke it and what was kept for it while it rested (a1062; see News), followed by:
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
- Any rest sends the resident home to its corner (Alex, 29 Sep; a678): the house runs `rest :1` as the resident (a806; before, `go <corner> :1`), which goes home without looking and records the go with `via=rest`, so history tells being carried home to rest from walking, and it wakes where it rested.
- A corner with `want=rest` or `status=asleep` makes a room say `<Name> is asleep here.` rather than list them as here with you (a806). A resident resting under `want=awake` keeps `status=awake`; after a rest it is in its corner. A narrated look names such a resident `(resting)` from `house.json` (`doing` other than `working`; `(resting until 21:40)` for a timed rest), and only one mid-turn plain (a948; see Rooms).
- A wake line can now be `read <soul> :3; look`: the bare look narrates the room it is in (its corner after a rest). Measured on a copy of frontier on 29 Sep: about 1300 words, against about 6000 for today's `read <soul> :3; look <corner> :3; look Board :3; read a570`.

**News.**
- **A call ends any rest** (a1062): `wake <name>` or the Desktop's wake button (both below, under Waking is its own act); a comment on a thing in its corner; a comment on its own commission.
- **Lines that address it** end any rest when a person says them, and wait for its next wake when a resident or an agent does (a1062, below):
  - a line in a chat in its corner;
  - `@name`, `@everyone` or `@all` anywhere; use versus mention (a916): nothing inside backticks or quotes counts (a single quote only when it is not an apostrophe); outside a chat line only `@name` reaches, and only when the edit adds it (a rewritten text that already named you is not news); `@everyone` and `@all` reach only from a chat line. The notice says what reached you (`as @name`).
- **Held news rides along with the next message:** a line in a chat whose `members` include `all` or the resident.
- **A mention waits for waking** (a1062). Who is speaking is read from the world, never from a name in code (`rooms.kind_of`, a1016): a *resident* (a corner names them), a *person* at a keyboard (a surface whose prop `person=` names them: the live Desktop says `person=alex`), or an *agent* (anyone else: a worker, a Claude session). While a resident is between turns (resting by choice or not; `house.news(..., resting=True)` in the pass and at a wake), a line above from a resident or an agent does not end its rest: it is kept in its `state.json` as `for_you` and said first at its next wake, however that comes (a timed rest ending, `breather`, `wake_every`, a call, a person's line), after `You are <actor>...` and the reason, as `for you while you rested (N):` then each `~ HH:MM in chat '<title>' (eN): <signed line>` (`~ HH:MM <who> mentioned you on '<title>', as @name (eN): ...` outside a chat). To a resident in a turn nothing changed: it goes with its next message, marked `(to you)`. A line in its own corner's chat (a visitors' book) from a resident waits the same way: a note at the door, not a knock. A plain line in a shared chat is never marked for you.
- **Waking is its own act** (a1062). `wake <name>` (a desk command, beside `rest`; `rooms.cmd_wake`) sets `call=<you>` on that resident's corner, signed by you and marked `via=wake`; the Desktop's wake button sets the same prop (with `want=awake`). The house takes it as a call: `~ <who> woke you (wake, eN)` (from the Desktop, `~ <who> called you from the Desktop (eN)`), followed, when a line of the waker's was held, by `, for the line they left you:` and that line; the rest of what was held follows under `for you while you rested`. The house clears `call` once delivered, by a call or by a wake (a resident started from `want=rest`), so the next wake is a change again. `wake` refuses yourself and a name no corner has; `wake` a second time before delivery says it is already called. Its receipt: `ok eN: you wake Pike (f576); the house calls them now, and their wake says you called`, or, to a resident in a turn, that the call goes with what reaches them when it ends, or, to one asleep (`want=rest`), that the call waits until someone sets `want=awake` (a resident's wake never sets `want`).
- **The speaker's receipt** (a1062; `rooms.waiting_note`, from `desk._chat_waits` after an append to a chat): for each resident the line calls (as the house hears it: `rooms.called_by_line`) who is resting or asleep, one line: `Pike is resting until 15:36; they'll see this when they wake, first and marked for them, so there's no need to say so (wake pike to call them now)`; after an untimed rest `Pike is resting, until 14:38 at the latest; ...` (from `house.json`'s `wakes_at`); asleep, `Pike is asleep (the house doesn't run them); ...`. A person's receipt says `Pike was resting; your line calls them now`. Nothing is said for a resident in a turn, or when no house state is readable (a copy, a test world).

**Failure.** A lost conversation (`No conversation found`) starts fresh, with the welcome. Other failures retry with backoff up to an hour, with status `error`.

**State.**
- The house writes the corner's `status` (`awake`, `asleep`, `unnamed`, `error`) as actor `house`, only on change.
- `house-state/<world>/house.json`, rewritten every pass, is read by the `house` and `turns` row sources, and by a narrated look for presence (a948, through the `house` source's reader). It carries `wakes_at` (a1062: when the house would next wake a resident between turns on its own: a timed rest's end, else its last turn plus `breather` while an objective is open, else plus `wake_every`; the `house` row source prints it as `wakes`, HH:MM, while it rests) and `held` (how many lines wait for its next wake), and each resident's last 10 replies (`said`, each cut at 2000 characters), so Alex's Desktop can show what they wrote, their own thinking included.
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
- It can see the painter: `screen.py <world> --as <who> STEP ...` copies the world (removed after), serves it with the caller's own `desk-shell/` from a deskd on a free port, drives headless Chrome over the DevTools protocol, and runs steps: `facts [prefix] [depth]` (each painted part's size, scrolls or cut, folded, off screen), `shot [file.png]`, `click`, `right`, `menu`, `choose`, `type`, `key`, `drag`, `scroll`, `wait`, `text`, `css <part[,part]> <property>` (each part's computed value, e.g. opacity, read at one moment, and the animations on it), `answer <text>` (the next prompt() or confirm() is answered so; unanswered ones are dismissed), `events [n]`, `resend [k]` (post again, unchanged, a body the page sent), `restart`/`stop`/`start` (the throwaway deskd). Parts are named by data-key (`<key>/handle` for a fold's handle), or by a CSS selector starting `#` or `.` for a part with no key. `--term` keeps the desk terminal beside the lens (hidden by default); `--page shell` opens the windowed shell (`index.html`) instead of the painter. `--reduced-motion` looks as someone whose system asks for reduced motion. `--live` points at the keeper's deskd instead, where a press is a real act.
- After the house restarts, a commission underway (`working`, `waiting` or `ready`) whose worktree still exists is resumed on the worker's saved session. A turn the restart cut short is said to it again, and it hears only what it has not heard.
- It says it is done by committing and setting `commission=ready`.

**Landing** happens between the house's passes:
1. The branch's changes must be non-empty and avoid `sessions/` and `.env`.
2. Health is taken.
3. `git merge --no-ff worker/<cid>` into whatever branch is checked out, with the subject `land <cid>: <title>`.
4. Health is taken again. If it fails, or a lens that compiled before no longer does, the merge is reverted (`git revert -m 1`).
5. In frontier, from the main checkout, *Current Implementation* is exported from its Handbook binder, and `research/command-center/FRICTION.md` from Rough spots (`friction.py`, one way), by one `export_docs.py` run; whichever of the two it wrote is committed (`docs: <names> after land <cid>`). The protocol asks the worker to change the passages its change affects, with `replace`, before it sets `ready`.
6. The result is commented, the worktree removed and the branch deleted.
7. A landed `.py` change asks the house to restart. It restarts when no resident or worker is mid-turn, and until it has, no new commission starts (so the next worker runs, and branches from, the code that landed).

**The keeper** (`keeper.py [world] [--port 8794]`) runs deskd and the house (the house with `DESKD` pointing at that deskd, and `HOUSE_KEEPER=1`).
- It restarts deskd whenever HEAD moves.
- It restarts the house:
  - at once on exit 75;
  - after 60 s on exit 76 (another house is alive; a heartbeat counts only while its process is still running, so a house restarting on new code does not block its successor);
  - after 30 s on any other death.
- If the house dies 3 times within 5 minutes after a `land ` commit less than 15 minutes old, the keeper reverts that commit.
- Its log is `house-state/keeper.log`.

**Health** (`health.py <world> [--json]`), in order:
1. every `*.py` compiles;
2. `node --check` passes on `desk-shell/*.js` and `style/*.js`;
3. `test_scene.py` passes; then the rooms tests (`test_room_verbs`, `test_room_look`, `test_room_reads`, `test_blanks`), each on a small world it builds itself with `roomworld.py`, so a failure is the code's and not the day's world's (a1190; `test_blanks` saves its built world as `sessions/roomworld-blanks-<pid>-try.pickle` for the house's own rest path and removes it, its lock and its house-state after); and every `test_*_paint.py` when a browser is here (the line says how many were not run without one);
4. the style mirror: `scene.style_check`, the Python copy of `style.js`'s parse and property reader that style receipts use, agrees with `style.js` run under node (`desk-shell/checks/style-read.js`) on `test_scene.py`'s samples, `calm.style` and every style note in the world (a1101, at Sable's ask c1212: two parsers of one language drift unseen). Without node the line says the mirror was not checked;
5. `suite/sessions.py --check` shows 0 golden differences;
6. every placed lens compiles.

A refusing lens is listed but doesn't fail health.

**Trials.** These spend real model calls.
- `try_house.py` copies a world to `try-<tag>`, names and wakes chosen corners, runs the real house under turn and time caps, writes a report to `research/command-center/trials/`, and deletes the world and conversations.
- `try_worker.py` runs one real commission in a throwaway worktree, landing on a `trial/<tag>` branch, never on main.
- `fake_model.py` is a scripted stand-in for the model API, for house tests.

## Documents

- **`export_docs.py [session] [--force] [--dry]`** writes this document from the binder *How the desk is built* to `docs/` and to Alex's vault, each with a stamp. The first note is the title and introduction; each later note is a section. A copy edited outside the desk is left alone, with a warning. For `frontier` it also writes `research/object-facet-frontier/desk-export.txt`. Every run also writes `research/command-center/FRICTION.md` through `friction.py`.
- **`friction.py`** (a778) keeps Rough spots (f747) and `FRICTION.md` one list. `export <session> [--dry]` writes the file from the world: every placed note with a `family=` prop, grouped by status (open, curing, unchecked, cured, then any other), each with its appearance ids and `f=` if it has one. The file's first line says it is generated and one way. It carries no stamp; every export overwrites it whole when it differs, so a hand edit is gone at the next export. `lines [source.md]` prints a `look f747` and one `do create f747 ... f=F<n> status=unchecked family=unsorted` per `## F<n>.` entry, quoted as `export` quotes text; `check <session> [source.md]` compares each placed note with `f=F<n>` against its entry, title and text, and prints `N entries; N identical in the world; K faults`. The source defaults to the frozen hand-written log, `research/archive/FRICTION-by-hand-to-29-Sep.md` (F1 to F32).
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
| `desk_knife.py` | 1244 | The live desk: selections as targets, pair verbs, rules (notes tagged `rule`: checked, armed, fired; a1027), clock, handles, tables, views, `export`, `rows`, `scene`, the style and lens receipts (`_visual_notes`, a1101), help topics, world-verb dispatch in `do` |
| `moo.py` | 536 | The verb registry: declarations, kind inheritance, composed verbs, synonyms; the one sort key a lens's `by` and `put above=` share (`order_value`, `order_by`; a1081) |
| `knife.py` | 263 | The selection language (with `unanswered:`, `answers:`, `answered-by:`) and pair verbs |
| `verbs.py` | 445 | World verbs: finding (nearest first, rooms as namespaces, doors), where a line stands, stored text judged when saved, running, reaches (their blanks are filled by `blanks.py`). a990's proof is `test_room_verbs.py`; `sweep_rooms.py` tries every built-in from every room |
| `blanks.py` | 240 | The one filler (a806): `$here $here.<prop> $new $today $me $<handle>`, `$1 $* $this` in verbs, `$item` in rules, a thing's parts `.title .maker .<prop>` (a1027); a backslash before a dollar sign keeps it literal; `help blanks` |
| `scene.py` | 1473 | Lens grammar (`WORDS`), resolve, emit, the text printer, row sources, styles from the world and `style_check` (style.js's parse and property reader, mirrored for receipts; a1101), `split_scene_arg`; the reference evaluator |
| `lens_ir.py` | 529 | Lowering, the evaluator over the Accessor, `compile_lens` and the definition closure, `check` (`scene <lens> ok`) and `find_parts` (`scene <lens> <part path>`; a1101) |
| `rooms.py` | 437 | Rooms (a678, a806, a948): what a room is, where each actor is (derived from `go` events), `go`, `rest` (home, `via=rest`), `wake <name>` (a call, a1062), the narrated `look` and `look <room>`, the date line, presence (asleep, resting, plain), what kind a speaker is (`kind_of`: resident, person, agent), who a chat line calls and the receipt's line for those resting (`called_by_line`, `waiting_note`; a1062) |
| `worktree.py` | 212 | Fork, journal, diff, all-or-nothing replay merge |
| `explore.py` | 257 | CLI: forward to deskd or run under the pid lock (`take_lock`, `release_lock`); atomic save; `--window --dump --shape --reset`; `!actor` injection |
| `deskd.py` | 408 | HTTP server, its origin and session-name checks, and the gesture fence |
| `house.py` | 704 | Residents |
| `workshop.py` | 342 | Commissions and workers |
| `keeper.py` | 118 | Keeps deskd and the house on the current code; reverts a breaking landing |
| `health.py` | 119 | The checks a landing must pass |
| `try_house.py`, `try_worker.py`, `fake_model.py` | 463 | Trials and a fake model |
| `trial_resident.py` | 364 | One resident alone, run by `house.House` itself (no workshop, one corner) in a copy of a world, with its state and working directory under the system temp folder: `setup` hides the Handbook's grammar binders and every sentence naming the trial, `run`, `report` (each > line and what came back). a823's no-manual trial; records in `trials/` |
| `desk_mcp.py` | 176 | The desk as an MCP tool |
| `export_docs.py`, `handbook_docs.py`, `docs_sync.py` | 313 | The documents |
| `journal.py` | 335 | Sable's standalone operation-journal prototype. Nothing running imports it; `test_journal.py` does |
| `harness.py`, `run.py`, `tasks.py`, `jeffx.py` | 1083 | Model trials as desk things. `jeffx.py` imports a transport from `C:/Projects/Agora/local/…`, outside this repo, and `runs/` is parked |
| `play.py`, `playground.py` | 128 | An older play loop and page. `playground.py` imports `tasks` from the old copy in `C:/Projects/Agora` |
| `roomworld.py` | 105 | The small world the rooms tests build for themselves (a1190): Home with Board, Lounge, Desktop, Archive, three corners, their talks and a house `say`, made through desk lines in memory |
| `test_scene.py`, `test_journal.py`, `test_reaching.py`, `test_blanks.py`, `test_room_verbs.py`, `test_room_look.py`, `test_room_reads.py` (these four on `roomworld.py`, run by health), `test_waiting.py`, `test_lanes.py` (a1081: `by`, `put above=`, twenty puts, `put` still `move` elsewhere), `golden_prints.py`, `suite/` | 382, 839, 153, 223, 210, 190, 35, 1765 | Tests and instruments (see Evidence); `suite/` is Python files only |
| `desk-shell/lens.js`, `viewer.js`, `term.js`, `lens.html` | 544 | The lens painter, continuity, the desk terminal |
| `desk-shell/style/calm.style`, `style.js` | 409 | The seed style and the style compiler |
| `desk-shell/shell.js`, `core.js`, `apps/*.js`, `index.html`, `shell.css` | 2024 | The windowed shell and its three apps |
| `desk-shell/checks/` | 1823 + 884 | Iris's browser checks and results, Rook's defect list, and Pike's continuity instrument (`continuity/run.mjs`, with 13 results); `style-read.js` runs `style.js` under node for `test_scene.py`'s check of `scene.style_check` (a1101) |

Which file for which change:

| Change | Where it goes |
|---|---|
| A verb anyone can use | A note tagged `verb` in the world |
| The desk acting on its own | A note tagged `rule`, placed in the room it acts from (a1027; `test_rules.py` checks it) |
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
| `python health.py frontier` (a lens note with `expect=refuse`, like p-if, counts as an expected refusal, apart from unexpected ones) | python ok; scripts ok; test_scene 25 passed; session prints: 82 same, 0 differ in reads only, 0 differ in the golden form, 0 new; lenses in frontier: 7 compile, 1 refuse (`p-if`); total 3.4 s |
| `test_scene.py` | 25 passed |
| `test_journal.py` | An instrument that always exits 0: `9 breaks, 1 half, 1 hidden, 1 holds, 7 journal`. S11 drives an old code path and no longer describes the desk |
| `suite/run.py` | 9 cases (trip, attacks, reads, host, chat, viewer, workspace, blocks, budget), all the same as their recorded runs |

- `golden_prints.py` has no check mode (it writes); `suite/sessions.py --check` is the read-only comparison.
- `desk-shell/checks/` needs a live page and server, and was not run.
- Nothing automated covers deskd's HTTP layer, the house with a real model, or the browser.
**Open defects a builder will meet** (each reproduced, unless marked read).

*The fence and undo:*
- A selection target skips the "not looked yet" refusal, and pair verbs never check staleness (read).
- Via deskd, the CLI does not stop at a refusal.
- A `;` batch half-applies. (A `script` definition made no event, so a bare `undo` reverted an older change; scripts are retired since a1027, and a rule is a note, made by an event.)

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

**Friction log.** Frictions live in the world, in Rough spots (f747): a note with `family=` and `status=`. `research/command-center/FRICTION.md` is exported from there (`friction.py`), one way. The hand-written log F1 to F32 is frozen in `research/archive/FRICTION-by-hand-to-29-Sep.md` and imported as notes with `f=F<n> status=unchecked family=unsorted`. As that log left them, open or partly open:
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
7. **Definitions are nearly uniform.** Lenses, styles, world verbs and (since a1027) rules are notes; scripts are retired into verbs. The clock is not: it has no history or undo, though worktrees carry it.
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

**For "everything that changes behavior is visible".** *Style: built* (a world note). Rules are notes since a1027: checked whenever their text, home or author changes, broken with a reason, never running a last good version. Scripts are retired into verbs. The clock remains a desk attribute. The last-good cache is kept, and named in `def`.

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

<!-- exported from the desk: world frontier, Home > Handbook > How the desk is built, at event e3277. Edit it there; a direct edit here makes the next export stop and warn. sha1:be71c3dcce4e -->
