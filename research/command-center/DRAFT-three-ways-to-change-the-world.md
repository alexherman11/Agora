# Three ways to change the world (draft)

> **Draft by Claude, 29 Sep 2026, from a conversation with Alex. Not a design status.** Nothing here is Held, Leaning or Open in *Dynamic Desk* until Alex says so. Alex's words are quoted verbatim and marked; everything else is my proposal. Labels: **[ran]** executed, **[read]** a primary source, **[recall]** remembered, not re-read, **[imagined]** design. Part of the task "Restructuring the desk", beside *Living in the world*.

## The question

Alex, after the lesson on live building:

> "so verbs that get made for the desk and ones that get made for lens are not the same. Can you think through how we could unify these views? Sit with this one for a while and think it through"

and, on the second pass:

> "dont be too worried about previous rounds results, you should trust your intuition and be comfortable doubting previous assumptions"

My first answer was that every lens gesture should call a named verb. The second pass, made from evidence, changed that. Most of what lenses do is not a verb at all: it is the lens being written through. The claim of this draft is that there are **three ways to change the world**, and the desk-versus-lens split is two of them fused together:

1. **Write through a view**: drag, drop, edit, compose. The meaning comes from what the part shows.
2. **Act**: a named verb, the same whether it is typed, clicked, or fired by a rule.
3. **Adjust the view**: open, tab, scroll, theme. The viewer's own state, not the world's.

## 1. What exists today [read, with two things ran]

Six mechanisms each say what an act does:

| | Written | Blanks | Checked against | A step fails | Runs as |
|---|---|---|---|---|---|
| Built-in verbs (`moo.py`) | Python, by kind with inheritance | Python arguments | the seen fence on the target; inner steps call `World.apply` directly | whole or nothing (earlier steps undone) | caller |
| World verbs (`verbs.py`) | note tagged `verb` | `$1 $* $me $this $1.title` | the seen fence, every step | earlier steps stay | caller |
| Scripts | desk setting, not an event | `$1 $1.title` | the seen fence | earlier steps stay | caller |
| Rules | desk setting | implicit target | none: the rule marks the thing seen, then acts | noted, goes on | the desk, `via=rule rN` |
| Lens gestures | inline in a lens part | `$item $title $prop $frame.field` at paint time; `$x $y $value $carried` at gesture time | what was painted: every value the line was built from, membership, the carried thing and the receiver | earlier steps stay | the person gesturing |
| Commissions | a task | prose | health before and after | revert | a worker |

Three of the differences are accidents rather than choices:

- **World verbs are stricter than built-ins, in the wrong place.** [ran] Alex made a house verb `wave`: `do append talk line="*$me waves at $1*"`. Wren, who had never looked at the chat, used it: `ERR you have not looked at a03 yet`. Wren never chose a03; the verb's author did. A built-in composition doesn't have this problem, because its inner steps call `World.apply` directly.
- **World verbs and built-ins fail differently.** A built-in composition undoes its earlier steps on a refusal; a world verb keeps them. I chose the world-verb behavior by copying `;` batches. I now think that was wrong: one use of a verb is one intent.
- **Filling blanks is done in three places by convention.** The painter escapes `$value` (`lens.js`, the blur handler), `verbs.run` quotes its fills, and `cmd_run` has a copy of the same code. [ran] A typed value built to break out (`shout hi"; do remove a03; do prop a05 x="y`) stayed plain text. So there is no injection today, but every new place that fills a blank must remember to escape.

## 2. What gestures actually do [read; the sorting is my judgment]

I collected every gesture line in the lab's lenses, tests and notes (`grep` over `research/text-desk-lab/notation`, `research/command-center`, `research/object-facet-frontier`). There were many duplicates across tests and prose; these are the distinct meanings:

**Drops**
- `prop $carried status=open|doing|done` on the Board's columns, whose lists are `of kind:task,prop:status=…`
- `prop $carried tripday=$day.n` on a trip's day columns
- `due $carried on=$it.date` on calendar cells
- `move $carried into=$item` and `into=f01` on containers
- `move $carried before=$item` in an ordered list
- `link $item to=$other`

**Edits and composers**
- `retitle $item title="$value"` where the part shows `$title`
- `rewrite $item text="$value"` where it shows `$text`
- `due $item on=$value` where it shows `$due`
- `retitle-section`, `rewrite-section` on section rows
- `create Board kind=task title="$value" status=open` above the BACKLOG list
- `append $item line="$value"` under `of messages:$id`
- `comment $d.item line="$value"` under a comments list

**Drags**
- `move $item to=$x,$y` under `at item`
- `prop $item amount=$y` on a scaled axis

**Clicks**
- world acts with plain-language names: `prop $item status=done`, `status=doing`, `want=awake`, `want=rest`, `objective=open`, `tag $item add=…`, `remove`, `resolve`, `reveal`, `check`, `beds=1`
- viewer state written into the world: `prop notes open=$item`, `prop tabs tab=a`, `prop $me theme=…`, `view scroll=…`
- reading: `look $item`, `why $target`, `worktree diff $name`, `find`
- a script: `run tidy $item`

The pattern:
- **Drops, drags, edits and composers** nearly all say *make the world match what this part shows*. The only clear exception is `link`.
- **Clicks** are where the named verbs are.
- **A few clicks** aren't world changes at all.

The lens says every write-through twice: once to show (`of prop:status=doing`) and once to write (`do prop $carried status=doing`). If someone edits one and not the other, they drift apart and nothing says so.

## 3. The proposal [imagined]

### 3.1 Write through a view

In programming-language research a *lens* is a pair of functions [recall: Foster, Pierce et al., the bidirectional-lens papers and Boomerang]:
- *get* shows a view of some data;
- *put* takes a changed view and writes the change back.

Ours has *get*. Each lens writes its *put* by hand, gesture by gesture. The compiler already holds what it needs to derive it: the part's selection and its text template. Databases know the same problem as "updatable views" [recall].

**Inverting a selection.** A drop on a part writes through the nearest repeat at or under it (on the Board, the drop lands on `doing`, and the repeat is its child `dl`). Each term of that repeat's selection is handled in one of three ways:
- **Already true of the carried thing:** nothing to write. For example, `kind:task` when a task is dropped.
- **Invertible:** write it.
  - `prop:k=v` becomes `prop k=v`;
  - `tag:x` becomes a tag add, and `-tag:x` a tag remove;
  - `in:f04` becomes `move into=f04`;
  - a term with a frame value (`prop:tripday=$day.n`) is written with that instance's value.
- **Neither:** `due<today`, `age>7`, `?word`, `comments:open`, `kind:task` when a note is dropped. The drop is refused, naming the term. The lens can say explicitly what it means instead.

**Inverting text.**
- A part whose text is exactly one field (`text $title`, `$text`, `$due`, `$status`) writes that field on edit.
- A composite template (`"$title · $due"`) is not invertible, so it needs an explicit act.

**Inserting.**
- A composer attached to a list creates a new member that satisfies the list's selection.
- Under a row source, it inserts a row: `messages:` appends a line, `comments:` adds a comment. Each core row source defines its insert once, in the host.

**Placement.**
- `move to=$x,$y` under `at item` is the inverse of showing the item's own position.
- A value placed on a linear scale inverts to that value. A non-linear derive doesn't invert.

**The check that keeps it honest.** After the write, re-evaluate the part for that thing: it must now show where it was put. If a card dropped on NOW doesn't appear in NOW, the write is undone and refused with the reason. (The bidirectional-lens papers call this law PutGet [recall].) It costs one selection evaluation, and it catches every mistake in the inversion rules themselves.

**What the lens says, and what the scene prints.** The lens says only that a part accepts something:

```text
# today
doing : column, role drop, on drop card do prop $carried status=doing
  dl : column, of kind:task,prop:status=doing, each card

# proposed
doing : column, role drop, on drop card
  dl : column, of kind:task,prop:status=doing, each card
```

The scene prints the derived meaning, so a reader never has to work it out:

```text
drop card here: do prop $carried status=doing   (so it shows in dl: kind:task,prop:status=doing)
```

**Explicit acts stay.** `on drop … do …` is the escape hatch for anything that isn't an inverse (`link`, "assign and notify"). An explicit act has to state what it does. A write-through can't drift from what it shows.

### 3.2 Act: named verbs

A named verb is an act with a name people use in speech: done, wake, resolve, say, start. It is the same thing whether it is typed, clicked, or fired by a rule.

- **Call shape: the built-ins' own,** `<verb> <target> [k=v…] [words…]`. World verbs stop being positional.
- **Blanks use the lens's names,** so an explicit lens act and a verb body are the same text:
  - `$item`: the thing acted on (the target);
  - `$value`: the words after the target, i.e. the text given;
  - `$<k>`: each `k=v` argument;
  - `$me`: the caller;
  - `$this`: where the verb lives.

  Pulling an inline act out into a named verb becomes a cut-and-paste. This also closes F24:

  ```text
  say   (a note tagged verb, on=house)
    # say something in a chat: say <chat> <words>
    do append $item line=$value

  typed:     say a570 hello there          → $item=a570, $value="hello there"
  composer:  tsay : …, on edit do say $item $value
  ```
- **Where a verb lives is a selection.** `on=` takes an actor, an id, `house`, or any selection (`on=kind:task`, `on=tag:project`). A selection is MOO's inheritance without a class tree.
- **Lookup, nearest first:**
  1. what you carry;
  2. the target and the things named;
  3. verbs whose `on` selection matches the target;
  4. where you are;
  5. the house.

  Two verbs answering at one level refuse, naming both. Built-ins can't be shadowed: a `prop` that means different things in different rooms would be dangerous for agents.
- **Verbs never live on views.** An act that exists only inside a lens recreates the app silo, and a resident who never sees the lens can't do it. Alex: "views and lenses should just represent the underlying objects and information." A lens can *call* any verb (`on click do done $item`). It can't own one.
- **One use is one intent: all or nothing.** If a step refuses, the earlier steps are undone, as `moo.py`'s compositions already do. A `;` batch typed by hand stays as it is, because it is several intents.
- **The fence judges what the caller supplied.**
  - Targets that came from the caller (`$item`, `$k`, and for a gesture every painted read) are judged against what the caller saw.
  - Things the verb reaches by itself (a literal `a570` in its body) are read fresh at run time, so they can't be stale.

  This fixes `wave` and matches the built-ins. The receipt prints what the verb read.
- **Checked when saved.**
  - The body must parse as desk lines, every blank must be one the verb has, and every command must exist.
  - A verb that fails the check is still saved, because we never discard what someone wrote. It is marked broken, with the reason.
- **A broken verb refuses. It never runs its last good version.** A lens can show its last good version safely; doing an old act silently would be guessing.
- **Filled once, in one place.** Blanks are filled after the line is parsed, with values, not by pasting text into a command. That removes the three copies of the escaping code.
- **Rules call named verbs.** A rule becomes a note: `when <selection> do <verb> …`. It runs as its author, who endorsed the standing automation. Scripts retire into carried verbs, and `run` becomes `use`.

### 3.3 Adjust the view

`open=`, `tab=`, `theme` and `scroll` are one viewer's state, kept per viewer and never journaled. Written as props, they add history nobody wants, and two viewers fight over one lens's `open`. Reading clicks (`look`, `why`) just read. This is the smallest of the three, and it is needed for the other two to stay clean.

## 4. How it fits the compiler [imagined]

- **Write-through is a compiler feature.** Its inputs are two things the compiler already lowers: `bind`, the selection a part repeats over, and `emit`, its text template. A derived *put* is printed with the scene and carried with the gesture like any act.
- **The `acts` kind then holds only explicit acts:** a named verb call, or an escape hatch.
- **Verbs get a parse stage like lenses** (checked when saved) and one filling stage. They don't need the rest of the pipeline until the expression language grows. If it gains a printed `if`, verbs and lenses should share it.

## 5. Against LambdaMOO [recall]

- MOO had no views, so it had no manipulation. Everything was a named verb, found on the player, the room, the direct object and the indirect object, and up each one's parents.
- Our named verbs are MOO verbs, with two differences:
  - they are recipes over built-ins rather than programs;
  - they run as the caller, not as the verb's owner.
- Write-through is what a world with views adds. Viewer state is what a world with many viewers adds.

## 6. What this replaces from my own first pass

- **"Every gesture calls a named verb."** Replaced by the three ways. Most gestures are write-throughs.
- **Lens-local verbs.** Dropped: a verb that lives only in a view is a silo.
- **Sentence forms (`say <words…> in <chat>`).** Dropped: they would be a second syntax. The built-in call shape plus `$value` is enough.
- **A verb's reads joining the fence.** Dropped: they are fresh. They are printed, not fenced.

## 7. Open questions

- **Drop into a column whose items appear elsewhere.** Status columns select by prop, so a drop changes the prop and the card's appearance stays where it is in the world. That seems right. But should `in:` terms move the appearance, or place a new one?
- **Dragging out of a part onto nothing.** Taking something out of a selection is rarely unique ("not doing" could mean open or done). I'd propose that it does nothing and says so.
- **Where a composer's new thing appears.** A selection doesn't say which surface. Either the lens names it (`into Board`), or it goes to where the viewer is.
- **Whether write-through is on by default** wherever it can be, or opt-in per part (`on drop card` with no `do`). I lean opt-in: the lens should say a part accepts things.
- **Order in a sorted list.** A drop between two items would need a sort key between theirs. I'd refuse unless the list is in world order.
- **What `$item` means.** In a lens, `$item` is an appearance. For a typed verb it is whatever the caller named: an appearance, a subject or a title. This needs one rule.
- **"Where you are" for a resident.** Their corner? The last room they looked at? *Living in the world* proposes rooms; this draft only needs the answer to exist.
- **Who a rule may bind.** A rule runs as its author, but it may act on things its author doesn't own. That belongs to the authority layer, which is Open in *Dynamic Desk*.

## 8. What would change my mind

- If new lenses mostly write things that *aren't* inverses ("drop on a person means assign and notify"), write-through is a convenience, and explicit acts stay primary.
- If the check that a thing shows where it was put refuses often and confuses people, the inversion rules are too clever. They should shrink to `prop:k=v`, `tag:` and single fields.
- If sharing `$item` between "the thing under the pointer" and "what the caller named" causes mistakes, the blanks need different names.
- If judging only what the caller supplied lets a real stale overwrite through, the fence rule is too loose.
- If residents' verbs turn out mostly one-line and single-target, positional blanks were fine, and the call-shape change isn't worth its churn.

## 9. What to try first

Smallest first, each able to stand alone:

1. **World verbs: the fence rule and all-or-nothing.** This fixes the refused `wave` [ran]. Host, `verbs.py`.
2. **The built-in call shape and lens blanks for world verbs** (`$item $value $k`), with `$1` kept for a while. This closes F24; `script` retires into carried verbs. Host, `verbs.py` and `desk_knife.py`.
3. **`on=` as a selection, and the "matches the target" level in lookup.** Host, `verbs.py`.
4. **Write-through for `prop:`, `tag:` and single-field text,** with the check and the printed meaning; explicit acts unchanged. The test: rewrite the command-center lens without its three hand-written status drops, and check that every drag does exactly what it did before. The compiler and painter are Jeff's and Pike's files (OWNERS.md), so this waits on their return or Alex's word.
5. **Viewer state out of the world.**
6. **Rules as notes calling named verbs.**

Steps 1–3 are good first commissions for the worker path. They are small, have clear "done when" tests, and live in files the house owns.

## Related

- *Living in the world (draft)*: rooms as places for verbs, reaches, layout as text. This draft's lookup levels and "where you are" depend on it.
- `research/command-center/LESSON-how-the-desk-grows.html`: tier 1 and tier 2, and verbs beside the compiler.
- `research/command-center/FRICTION.md`: F21 (no `say`), F24 (`$*` includes the target).
- *Dynamic Desk*: "Verbs should be learned once, and used anywhere where they apply"; "It should be easy to mint new useful verbs from within the desk"; "Every view is fully able to be restyled, rearranged, copied, or replaced".
