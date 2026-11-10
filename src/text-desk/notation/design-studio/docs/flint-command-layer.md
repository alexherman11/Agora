# The command layer: a reference

*Flint · 23 September 2026 · checked against the working tree of `src/text-desk/notation/` (branch `research/shared-visual-desk`, HEAD `f717590` plus uncommitted changes).*

Every transcript below comes from a real run in the session `doc-flint` (plus its worktrees `doc-flint@w1` and `doc-flint@w2`), driven with `DESKD=off` so the CLI owned the session directly. The export replay ran in an unsaved in-memory desk. Transcripts are trimmed with `…`. Anything marked **(source)** was read in code but not run.

Status marks used throughout:

- **REFUSED**: the desk says no, with a reason. This is intended behavior.
- **SILENT**: the desk accepts something it should question, or does something other than what was asked without saying so.
- **BROKEN**: a crash, lost work, or wrong output.

---

## 0. How a line reaches the world

```
explore.py <session> --as <actor>   (stdin, one command per line)
   │  DESKD unset → POST each line to http://127.0.0.1:8780/api/do (deskd.py)
   │  DESKD=off, no server, or any line starting with "!" → run in-process under sessions/<session>.lock
   ▼
worktree.handle()          if the line starts with "worktree"
DeskKnife.dispatch()       otherwise: split on ; → _one() → delta header → repl() → rules → receipt
   ▼
World.apply / World.undo   the only mutators; each appends an event {id, verb, target, args, undo, by, at, cmd, via, cause}
```

- **Actor.** `--as` sets it; the default is `jeff` in `explore.py` and `alex` in `deskd.py`. The name is supplied by the caller and is not authenticated.
- **Batching.** One call may carry several commands separated by `;` or newlines. They run in order and stop at the first refusal. At most 4 `read`/`examine` run per call (`read_cap`). A `script` definition is exempt from splitting.
- **Delta header.** Each command's output begins with `!! since your last look: …` when another actor has acted since your last look.
- **Persistence.** The direct CLI writes `sessions/<name>.pickle` once, at the end of the invocation. deskd saves after every line, in a `finally` block (source).

---

## 1. Verb inventory

This inventory comes from `help`, from each topic that `help` lists (`rules scripts views clock handles why export trials`), from `help selections`, and from `help <verb>` for every verb. The topics `scene worktree table find read sync compare` exist in `HELP_TOPICS` but are **not listed** by `help`.

### 1.1 Reading and navigation (no events)

| Command | Meaning |
|---|---|
| `look [id] [:1‥:4]` | Outline from `id` (default desk). `:1` the line, `:2` its children, `:3` everything under it with first lines, `:4` with full text |
| `open id` · `close id` | Expand or collapse `id` in your later looks. This is per viewer and moves nothing |
| `examine id` (aliases `x`, `ex`) | A thing's lines, comments, links, placement, and the verbs that apply to it right now. A subject id redirects to `pivot` |
| `read id [#n\|#name] [:3] [tail=n]` | Text split into sections with word counts; one section; all of it; the last n lines |
| `where id` | Exact geometry and spatial relations (`covers`, `hidden by`, `clear`) |
| `verbs id` | Applicable verbs with their argument forms, grouped by origin kind |
| `pivot id` | Appearance → its subject and every place the subject appears; subject → its appearances |
| `find words` · `find <selection>` | Text search, or a selection listed by surface (8 per surface) |
| `table <selection> [cols=…] [by=col] [desc=1]` | One row per thing, props side by side |
| `compare A B` | Two things side by side, with differences marked |
| `history [id]` | Recent events with their undo ids, `(undone)` marks, and `via` / `by rule` |
| `why id` | The events that put a thing where it is, and the rule that would act on it next |
| `rows <source>` | Row sources (the same ones a lens `of` uses): `sections:<id> comments:<id> actors events worktrees` |
| `scene <lens>` | The scene tree a lens (a note tagged `lens`) makes of the world, as text |
| `rules` · `scripts` · `vars` | List rules (with fire counts), scripts, and handles |
| `export` | Commands that would rebuild this desk from empty, addressed by title |
| `help [verb\|topic …]` (alias `?`) | Verb doc, arguments, one example; or a topic |

### 1.2 Changing the world: `do <verb> <target> [k=v …]`

These are the general verbs, meaning `moo.REGISTRY` minus `knife.SPECIALIZED`. The kinds are taken from `help <verb>`. Kinds inherit through a chain: `thing ← appearance ← text ← note|task|chat|doc|trial`, `image ← appearance`, and `thing ← surface`.

| Group | Verb | On | Meaning (args) |
|---|---|---|---|
| Placement | `move` | thing | Put somewhere else (`into=` \| `before=` \| `after=` \| `to=x,y` \| `by=dx,dy`; with a selection, `one=1` keeps one appearance per subject) |
| | `place` | subject | Add a new appearance of a subject (`into=`). A title or appearance id is resolved to its subject |
| | `resize` | thing | Width and height (`to=WxH`) |
| | `raise` · `lower` | thing | Front or back of its surface |
| | `remove` | thing | Remove this appearance. The subject survives |
| | `fold` · `unfold` | appearance | Show title only, or content again |
| Surfaces | `create` | surface | New `note\|task\|chat\|doc\|image\|surface` (plus `trial`, `view`) inside (`kind= title= [text= due= tags= layout=]`; `as=name` binds a handle) |
| | `group` | surface | New empty sub-surface (`title= as=free\|column\|row`). With a selection target it becomes a surface built around the selection |
| | `tile` · `untile` | surface | Column or row layout with no overlap (`as=`), or back to free placement |
| | `rename` | surface | Surface title (`title=`) |
| | `sort` | surface | Reorder the children of a tiled surface (`by=due\|title\|kind [desc=1]`) |
| Content | `append` | text | Add a line (`line=`). This edits the subject, so every appearance changes |
| | `rewrite` | text | Replace the whole text (`text=`, with `\n` between lines) |
| | `retitle` | text, image | Subject title everywhere (`title=`) |
| | `check` | text | Toggle the n-th checklist line (`item=n`). Offered only when the text contains `- [ ]` lines |
| Annotation | `comment` | appearance | A signed comment (`line=`), with id `cNN` |
| | `resolve` | appearance | Close a comment (`id=cNN [line=]`), or `do resolve cNN` directly. Offered only when a comment is open |
| | `tag` | appearance | Tags on the subject (`add=a,b` \| `remove=a,b`) |
| | `prop` | appearance, surface | String properties (`k=v …` \| `remove=k`) |
| | `due` | task, note | Due date (`on=YYYY-MM-DD` \| `clear=1`) |
| Relations | `link` | pair | `do link A B as=blocks\|refers\|answers\|part-of` (the registry form also accepts `to=B`) |
| | `unlink` | appearance | Remove a link (`id=lNN`) |
| Pair | `swap A B` · `beside A B` · `match A to=B` | two things | Exchange positions; put A right after B; give A B's size |
| External | `launch` | trial | Start `run.py` in the background. It cannot be undone |

### 1.3 Definitions, time, history and branching (outside `do`)

| Command | Meaning |
|---|---|
| `rule when <sel> do <verb> [target] [k=v] [now=1]` | Fire once on each thing that enters the selection |
| `rule on <verb> [by=<actor>] do <verb> [target] [k=v]` | Fire on each matching event, acting on the thing the event happened to |
| `rule drop rN` | Remove a rule |
| `script <name> = <cmd>; <cmd>…` · `run <name> [args]` | Named command sequence with `$1 $2 …`, `$1.title`, and `$today` |
| `set name = <id\|title>` | Bind the handle `$name` |
| `clock [YYYY-MM-DD\|now\|follow]` | Set or follow "today", re-run rules. `$today`, `due<today` and `age<N` depend on it |
| `undo [eN]` | Revert an event; bare `undo` reverts your latest change |
| `sync` | Import finished trials as the actor `harness` |
| `worktree [fork\|diff\|merge <name>]` | Branch the session, compare the two sides, and replay the branch's journal into the base |

### 1.4 Inventory defects

- **SILENT.** Synonyms rewrite the verb: `do delete a06` performed `remove`, and the receipt only notes `(you said delete; that is remove here)`. The same mapping turns `close` into `remove` and `create` into `group` inside `moo.SYNONYMS`. The lean `do` path mostly bypasses those two because `create` and `group` are real verbs.
- **Inconsistent.** `help nosuch` lists the whole registry, including `dedupe done gather reply reveal split stack tidy`. `help tidy` answers `no verb tidy here`, and `do tidy f01` is **REFUSED** with `no tidy here; use tile`.
- **Cosmetic.** In the refusal text, the list of general verbs prints `link` twice. The example for `help match` is `do match a20 a22 to=a22`.
- **Source only.** `World.apply` accepts `append … section=<name>`, `edit`, and the base-desk `plan`/`apply`. The last two are refused as `not available in this desk`. None of these appear in help.

---

## 2. The selection language

A target is resolved by one of three mechanisms. Each accepts a different set of words.

### 2.1 Naming one thing (`Desk._resolve`)

| Form | Example | Notes |
|---|---|---|
| Surface / appearance / subject id | `f07` `a04` `s03` | All three prefixes share one counter: f01, f02, s03, a04 … |
| The root | `desk` · `root` | |
| Exact title, case-insensitive | `"Buy compost"` | Must be unique among nodes. **REFUSED** when it is not: `'Seeds' names 2 things: a04, a08; use an id` |
| Handle | `$pan` (from `create … as=pan`) · `$seeds` (from `set seeds = a08`) | `vars` lists them |
| Last created | `$new` (last surface) · `$item` (last thing) | Inside a rule, `$item` is the thing the rule fired on |
| Comment | `cNN` | Only with `do resolve cNN` or `resolve <a> id=cNN` |
| Link | `lNN` | Only with `unlink <a> id=lNN` |
| Event | `eN` | Only with `undo` |
| Section | `#2` or `#Autumn` (spaces allowed) | Only with `read` |

`into=`, `before=`, `after=` and pair verbs refuse subject ids (`allow_subject=False`). Selection terms `in:` `also:` `links:` accept titles in place of ids.

### 2.2 Selecting many (`knife.parse_selection`)

Terms are joined by commas (AND). Any term can be negated with a leading `-`. Each term below was run with `find` on the doc-flint desk:

| Term | Selects | Run |
|---|---|---|
| `?w1+w2` | title, text or tags contain every word. Prefers appearances over surfaces | `find ?peas` → a04, a08 |
| `kind:k` or `kind:note\|task` | by kind (`column`/`free` for surfaces in `table`) | `find kind:note` → a04, a08 |
| `tag:t` | subject tag | `find tag:shop` → a06 |
| `in:<surface>` | inside, recursively | `find in:f02` → a08 |
| `also:<appearance>` | the other appearances of its subject | `find also:a04` → a08 |
| `due<D` · `due>D` · `due<today` | due date (requires a clock when written `today`) | `find due<2026-09-30` → a06 |
| `age<N` · `age>N` | days since last touched, by the clock | `find age<3` → 4 things |
| `title:w` | title contains the word | `find title:seeds` → a04, a08 |
| `prop:k=v` · `prop:k` | property equals v / is present | `find prop:status` → nothing matches |
| `comments:open` | has open comments (any other value: has comments) | → a04, a08 |
| `links:<id>` | linked to that thing | `find links:a04` → a06 |
| `hidden` | more than 5% covered | → nothing matches |
| `a04,a06` | explicit list | `find list a04,a06` |
| `-term` | complement | `find -tag:plan` → f02, a06, f07 |

`comments:` and `links:` work but **are missing from `help selections`**.

Spatial vocabulary outside selections: `move to=x,y`, `by=dx,dy`, `before=`, `after=`, `beside`, `swap`, `where`. Free surfaces overlap. For example, `do move tag:plan,in:f01 into=f07` left `a04 … hidden by a08` (**SILENT**: the receipt shows it, but nothing was refused).

### 2.3 Row sources (`scene.rows`)

These are used by `rows <source>` and by a lens `of`. They are not targets for `do`.

```
> rows sections:a04
rows sections:a04: 2  (fields: $item $heading $words $text $index)
  item=a04 · heading=Spring · words=2 · text=Peas
Beans · index=1                                 ← BROKEN (cosmetic): multi-line text without spaces is not quoted, so the row wraps
> rows actors
  name=flint · acts=8 · last=2026-09-23T13:52:37 · verb=prop · target=a06 · read=5 · behind=3
> rows events            (the last 20 only, newest first)
> rows worktrees
rows worktrees: 0  (fields: $name $by $commands $merged $behind)
> rows kind:note
ERR rows <source>. Sources: sections:<id>, comments:<id>, actors, events, worktrees
```

Actors appear in three places: `--as <name>`, `rule on <verb> by=<actor>`, and the test-injection line `!<actor> <verb> <target> k=v` (§3.3). Worktrees are named `<session>@<name>` and are entered as their own session.

### 2.4 What is refused, and what breaks

| Input | Result |
|---|---|
| `find bogus:x` | **REFUSED**: `no selection term bogus: (terms: ?words kind: tag: in: also: prop: title: comments: links: due< due> age< age> hidden …)` |
| `do move kind:image into=f07` | **REFUSED**: `nothing matches kind:image` |
| `do move a04 into=a04` | **REFUSED**: `into= must name a surface, not a04` |
| `do append a06 add more` | **REFUSED**: `unexpected words after the target: 'add more'; quote values with spaces` |
| `examine a04 :3` / `open a04 a06` | **REFUSED**: `examine takes only an id; depth belongs to look` |
| `events` | **REFUSED**: `unknown command 'events'`. Events are reachable through `history`, `rows events` and `GET /api/events` |
| `find in:a12` (not a surface) | **BROKEN**: `UnboundLocalError: cannot access local variable 'Refusal'` |
| `find age<2` / `rule when age<2 do raise` on a desk with no clock | **BROKEN**: same crash |

**Cause of the crash.** `knife.py:57` contains a function-local `from world import Refusal` inside `parse_selection`. That line makes `Refusal` local to the whole function. As a result, the refusals at lines 87, 95, 101, 111, 114 and 147 (`in:`, `also:`, `prop:` with no key, `age` with no clock, a malformed `age`, `links:`) all raise `UnboundLocalError` instead of a refusal. Only the unknown-term refusal on line 58 works. In the direct CLI, the crash exits before the single save at the end, so **every earlier command in that invocation is lost**. My comment `e6` and link `e7` disappeared this way and had to be redone. Under deskd, the `finally` block would save whatever state the failing line left (source).

**Source only.** `_selection_terms` replaces the substring `today` anywhere in a selection. For example, `?today` becomes the date, or is refused with `today is unset`.

---

## 3. Rules and scripts

### 3.1 Rules

```
> rule when tag:fixed do move into=Done
ok r1: when tag:fixed do move into=Done
  0 thing(s) already match tag:fixed; the rule fires on things that enter it from now on. …
> rule on comment by=priya do tag add=needs-reply
ok r2: on comment by=priya do tag add=needs-reply
> do create f02 kind=task title="Fix gate" tags=garden
ok create f02 kind=task title='Fix gate' tags=garden  [e18] → created a15
> do tag "Fix gate" add=fixed
ok tag a15 add=fixed  [e19]
~ r1 fired on a15: ok move a15 into=f13  [e20]
> why "Fix gate"
  e18 create kind=task title='Fix gate' tags=garden · flint via create
  e19 tag add=fixed · flint via tag
  e20 move into=f13 · flint by rule r1 (because of e19)
```

Event rule, with priya in her own session:

```
> do comment a19 line="Which hoe?"                     (--as priya)
ok comment a19 line='Which hoe?'  [e36] → created c23
~ r2 fired on a19: ok tag a19 add=needs-reply  [e37]
```

- A rule's actions are events with `cause` set to your command's last event. Undoing either one takes both back (§4.1).
- A rule acts without the seen fence: it is the desk's own hands. Chains are bounded to 3 passes.
- **SILENT.** Definitions are not validated. `rule when kind:banana do move into=Done` and `rule on flarp do tag add=x` were both accepted. After undoing the creation of "Done", r1 still names "Done".

### 3.2 Scripts

```
> script shop = do create Kitchen kind=task title="Buy $1" tags=shop; find tag:shop
ok script shop = do create Kitchen kind=task title="Buy $1" tags=shop; find tag:shop
  run shop [args]   (1 placeholder(s))
> run shop eggs
run shop: do create Kitchen kind=task title="Buy eggs" tags=shop; find tag:shop
[1] do create Kitchen kind=task title="Buy eggs" tags=shop
ok create f07 kind=task title='Buy eggs' tags=shop  [e21] → created a17
  … no free space, it covers things: move it or tile f07
[2] find tag:shop
  a17 task "Buy eggs" · 300x160 at 16,16 · 0w
```

- **SILENT, then REFUSED.** `script bad = frobnicate $1` is accepted. The problem only shows at run time: `run bad x` → `ERR unknown command 'frobnicate'`. `run nosuch` → `ERR no script nosuch`.

### 3.3 The `!actor` injection line: BROKEN attribution

`explore.py` treats `!priya comment a12 line="Need more?"` as "another actor writes directly". For verbs in the registry, it calls `REGISTRY[verb].run(w, target, {…, "_by": actor})`. `v_comment` passes `_by` to `World.apply` with no actor, so the event is signed by the session's `me`:

```
> !priya comment a12 line="Need more?"
(priya did comment a12: comment c22 added on s11)
> examine a12
    * c22 flint (open): Need more?            ← signed flint, and r2 (on comment by=priya) did not fire
```

Only `prop` reads `_by` (`moo.py:401`). This contradicts the comment in `explore.py`, which says "registry verbs (prop, tag, due ...) carry the actor as _by". Every other registry verb injected with `!` is signed by the session's `me`. A line starting with `!` also forces the whole invocation off deskd.

---

## 4. Undo, export, worktrees

### 4.1 Undo

```
> undo e21
ok e22: reverted e21, which was: create f07 kind=task title='Buy eggs' tags=shop  (made 13:52)
> undo e20                                    (a rule consequence: its cause comes back too)
ok e24: reverted e19..e20 (2 steps of tag)
> undo e18
ERR e18 is not the latest change to f02; e20 came after it. undo that first, or act on the current state
> undo e19
ERR e19 cannot be undone (already undone or is an undo)
> undo e99
ERR no event e99
> rule drop r4
ok dropped r4
> undo
ok e25: reverted e18, which was: create f02 kind=task title='Fix gate' …     ← r4 is still gone
> undo
ok e28: reverted e15..e16 (2 steps of move tag:plan,in:f01)
```

- A selection verb is undone as a group (`via` + `cmd`). A rule's consequences are undone with their cause.
- **REFUSED.** You can only undo the latest change to a target. There is no redo. An undo cannot itself be undone.
- **SILENT.** `rule`, `rule drop`, `script` and `clock` produce no event. They are not in `history`, carry no author, and `undo` cannot take them back. A bare `undo` right after one of them reverts some older world event instead.
- `launch` is labelled as irreversible. `sync` writes as `harness` (source; not run here).

### 4.2 Export

```
> export
# export of this desk; replay on an empty desk after one look
look
clock 2026-09-24
do create desk kind=surface title="Garden" layout=column
do create "Garden" kind=note title="Seeds" text="## Spring\nPeas\n…" tags=plan,spring
do place "Seeds" into=desk
do create desk kind=surface title="Kitchen" layout=free
do create "Kitchen" kind=note title="Pantry" text="flour"
do move "Pantry" to=8,8; do resize "Pantry" to=294x160
do link "Seeds" "Buy compost" as=refers
script shop = …
script bad = frobnicate $1
rule when tag:fixed do move into=Done
…
# not carried (only you can write as you): comment c09 by flint on "Seeds"
```

Replay into an empty in-memory desk:

```
> do place "Seeds" into=desk
   ok e3: place s03 into=f01 → created a05
> do link "Seeds" "Buy compost" as=refers
   ERR 'Seeds' names 2 things: a04, a05; use an id
```

**BROKEN.** Export addresses things by title. It then makes its own titles ambiguous: it places `Seeds` twice, and the next line names `Seeds`. It also writes a link to `Buy compost`, whose only appearance had been removed, so no title can reach it. The props on that subject (`status=open cost=12`) are dropped without a word. Comments are deliberately not carried, and the export says so. Rules that name a missing surface (`into=Done`) are exported unchanged.

### 4.3 Worktree: fork, diff, clean merge

```
> worktree fork w1
ok forked doc-flint at event 28 as doc-flint@w1
  enter: python explore.py doc-flint@w1 --as flint   or   ?session=doc-flint@w1&as=flint
                                                         (inside doc-flint@w1)
> do create f07 kind=task title="Sharpen hoe"            [e29] → created a19
> do append a12 line="sugar"                             [e30]
> do create f07 kind=task title="Oops"                   [e31]
> undo                                                   (the journal drops "Oops" too)
> rule when tag:urgent do raise
> worktree merge w1
ERR run worktree merge from the base (doc-flint), not from inside a worktree
                                                         (back in doc-flint)
> worktree diff w1
there (3 command(s)):
  + flint: do create f07 kind=task title="Sharpen hoe"   (made s18 a19)
  + flint: do append a12 line="sugar"
  + flint: rule when tag:urgent do raise
here since the fork (0 event(s)):
> worktree merge w1
ok merged w1: 3 command(s) replayed as e29..e30, each signed by who made it
> worktree merge w1
ERR nothing to merge from w1: all 3 command(s) are already here. …
```

A worktree is a whole pickled world with a journal of the command lines that changed it. Rule, script and clock lines are journalled even though they produce no event. A merge replays the journal against the base as it is now, remaps created ids, and is all-or-nothing on a trial copy. A worktree stays open after merging, and a later merge takes only the new commands.

### 4.4 Refused merge

```
                                                         (inside doc-flint@w2, forked at event 28)
> do append a12 line="salt"                              [e29]
> do create f02 kind=note title="Beds"                   [e30] → a19
                                                         (doc-flint, --as priya)
> do retitle a12 title="Larder"
ERR you have not looked at a12 yet; look, examine or read it first
> look f07
> do retitle a12 title="Larder"                          [e31]
                                                         (doc-flint, --as flint)
> do append a12 line="yeast"
!! since your last look: e31 edit a12 by priya
ERR stale: a12 changed since you last saw it; look at it again before acting
> worktree diff w2
there (2 command(s)):
  + flint: do append a12 line="salt"
  + flint: do create f02 kind=note title="Beds"   (made s18 a19)
here since the fork (4 event(s)):
    e29 create f07 by flint
  ! e30 edit a12 by flint
  ! e31 edit a12 by priya
  ! e32 edit a12 by flint
  ! = the worktree also names this thing; merge will refuse there if someone else did it
> worktree merge w2
refused: merge of w2 stopped at command 1 of 2; nothing was applied
  flint: do append a12 line="salt"
  a12 changed here since the fork (e30 edit by flint)
  worktree diff w2 shows both sides; redo that step in the worktree or here by hand
```

**Misleading.** Both `help worktree` and the diff footer say the merge refuses a target that *someone else* changed. In fact the code (`worktree.py`, merge loop) refuses any non-create, non-comment event on a named target after the fork, whoever made it, except events carrying this worktree's own merge mark. Here it cited e30, flint's own append merged in from w1, rather than priya's retitle. The conflict check is one id regex over the command line (`[afs]\d+`). Commands that name things by title or selection are not conflict-checked by name (source).

---

## 5. Module map

Line counts come from `wc -l`, 6,143 lines in total. The live desk class is `DeskKnife` in the `lean` variant (`explore.fresh()`). `Desk` and `DeskMoo` are its ancestors, and they also stand alone as trial variants.

| File | Lines | Responsibility | Main entry points |
|---|---:|---|---|
| `world.py` | 821 | The model: subjects, appearances, surfaces, links, comments, geometry and reflow, events with undo, the rev fence | `World`, `Refusal`, `World.apply(verb, target, rev, args, actor)`, `World.undo(eid)`, `add_subject/place/add_surface/add_link/add_comment`, `sections`, `checklist`, `relations`, `hidden_fraction`, `snapshot` |
| `desk.py` | 892 | Base text desk: outline notation, the seen fence, delta header, `;` batching, the reading commands, `undo`, `do` | `Desk.dispatch(name, args)`, `repl(line)`, `_resolve`, `_touched_by_others`, `cmd_look/read/where/pivot/find/history/undo/do`, `split_batch`, `unescape_value` |
| `desk_moo.py` | 248 | MOO layer: verbs from the registry by kind, `examine`, `help <verb>`, `verbs`, synonym adapter on `do` | `DeskMoo.repl`, `cmd_examine`, `cmd_help`, `cmd_do` |
| `desk_knife.py` | 1171 | The live desk: general verbs over selections, pair verbs, rules, scripts, clock, handles, tables, compare, why, export, `rows`/`scene` commands, help topics | `DeskKnife.repl`, `cmd_do_knife`, `cmd_rule/_run_rules`, `cmd_script/cmd_run`, `cmd_clock/_tick`, `cmd_export`, `cmd_table`, `cmd_why`, `_parse_selection`, `HELP_LEAN`, `HELP_TOPICS`, `SELECTION_HELP` |
| `moo.py` | 534 | The verb registry: `@verb` declarations (kind, doc, args, example, level), kind chain, applicability, composed verbs, synonyms, adapter | `REGISTRY`, `verb()`, `KIND_CHAIN`, `verbs_by_origin`, `_compose`, `SYNONYMS`, `Adapter.resolve` |
| `knife.py` | 237 | The selection language and pair verbs; which registry verbs count as specialized | `parse_selection(w, token)`, `GENERAL`, `SPECIALIZED`, `PAIR_DOC`, `pair_verb`, `group_around` |
| `worktree.py` | 171 | Fork a session, journal command lines, diff, and all-or-nothing replay merge | `handle(line, session, desk, actor)`, `record(...)`, `ids_of(desk)` |
| `explore.py` | 171 | CLI: forward to deskd or run locally under the lock; per-actor seen state; `--reset`, `--dump`, `--shape`; `!actor` injection | `main()`, `fresh()`, `via_deskd()` |
| `deskd.py` | 184 | HTTP server: one live world per session, static shell, observation channel | `GET /api/snapshot`, `/api/scene`, `/api/events`; `POST /api/do`, `/api/observe`; `Session` context manager |
| `scene.py` | 452 | Lens grammar (in the docstring), compiler to a scene tree, text projection, row sources | `parse(src)`, `build(...)`, `scene_for(desk, name)`, `to_text`, `rows`, `rows_text`, `LensRefusal` |
| `harness.py` | 104 | Trials as desk things: the `launch` verb (external effect) and `sync` as actor `harness` | `v_launch` (registered as `launch`), `sync(desk)` |
| `run.py` | 107 | One live model trial on a task world; records to `runs/<label>/` | `main()`: `run.py <task> --variant … --label … [--model …]` |
| `tasks.py` | 688 | Scenario worlds and hidden checks for trials | `TASKS`, `build(task, variant)`, `assess(task, desk)`, `build_home*`, `build_big/priya/review` |
| `jeffx.py` | 184 | Model transport restricted to desk tools | `tools_for(variant)`, `TextJeff`, `INSTRUCTIONS`, `MODEL`. **Imports `agora3.jeff` from `C:/Projects/Agora/local/arrangement-current-20260916/native/src`**, outside this repo |
| `playground.py` | 103 | A small web page: desk geometry on the left, text REPL on the right | `run(line)`, `H` handler. **Imports from `C:\Projects\Agora\src\text-desk\notation`**, the old pre-move copy, not this lab |
| `play.py` | 25 | Drive a task world by hand from stdin | `python play.py <task> [variant]` |
| `test_scene.py` | 51 | Admission tests for the lens parser | `python test_scene.py`: 4 passed on this run |

There are no tests for the command layer, `world.py` or `worktree.py`. The `parse_selection` crash in §2.4 sits on seven refusal paths that nothing exercises.
