# The text desk: architecture overview and the open challenge

A handoff for someone thinking freshly about the next step. It describes what exists and states the problem.
It deliberately proposes no solution.

## 1. What the desk is

A desktop workspace whose entire state is readable and editable as plain text. It was built so that a language
model can operate a desktop without pixels, scripts or screenshots: it reads an outline, types one-line commands,
and gets receipts. After about seventy measured model runs and two days of one model (Claude) living in it as a
home base, the text form is the source of truth: `export` prints the commands that rebuild a desk from nothing,
and replaying them reproduces the desk exactly.

Code: `C:\Projects\Agora4\src\text-desk\notation\` (Python, no dependencies). `python explore.py home`
opens Claude's own desk. `help` inside the desk explains everything below.

## 2. The model of the world

- **Subject**: a thing with content. Kinds: note, task, chat, doc, image, trial. Fields: title, text, tags, due,
  comments (with replies, open or resolved), props (free key=value), revision. Docs have `##` sections and
  `- [ ]` checklists inside their text.
- **Appearance**: a subject placed on a surface. One subject may appear in several places; editing it changes
  all of them. An appearance has geometry (x, y, w, h, z) and may be folded.
- **Surface**: a container. Layouts: `free` (coordinates, overlap possible), `column`, `row` (tiled, children
  share the space). Surfaces nest. A **view** is a surface whose contents are a live selection; nothing is
  in it, it lists whatever matches.
- **Links** between subjects. **Events**: every change is an event with an actor, a day, a cause, and undo data.
- **Ids**: `f..` surface, `a..` appearance, `s..` subject, `e..` event, `c..` comment, `r..` rule. Titles work
  anywhere an id is wanted, and are the practical names.

## 3. The text form

One line per thing, indented by containment. Whatever is cut or hidden is declared on the line.

```
f01 surface "desk" row · 1280x800 · 13 inside
  f02 surface "Plan" column · 3 inside
    a07 doc "Exploration plan" · 605w · 6 sections
    a58 chat "Priya" · 25w
  f05 surface "Done" column · 27 inside · cramped, 24px each · 3 past the bottom (offscreen)
  f202 view "Scoreboard" of kind:trial as table task,model,score,calls · 10 matches
  a123 trial "home2 on terra" · home2 terra done FAIL (morning_shows_overdue_and_today) 8/9 6 calls
```

Three reading axes: `look` scales by containment (`:1` a line, `:2` children, `:3` the subtree with first lines,
`:4` with text), `examine` shows one thing in depth (content, comments, links, the verbs that apply now),
`find` and `table` list by property across the desk. `read` gives text, by section or tail.

## 4. Acting

- **Verbs**: `do <verb> <target> k=v`. A small general set (move, create, remove, append, rewrite, retitle,
  tag, prop, due, comment, resolve, link, sort, tile, group, place ...). A verb registry decides which verbs
  apply to which kinds; `examine` prints them.
- **Selections** are the core primitive. A target may be one id or a selection: `?words`, `kind:`, `tag:`,
  `in:`, `due<`, `age>`, `prop:k=v`, `title:`, `comments:open`, `links:`, `hidden`, id lists, any term negated
  with `-`, combined with commas. Rules, views, find and table all share this one parser.
- **Receipts** state what changed and where things now are. Refusals say why and offer the next act. Every
  printed hint must be a command that runs as printed.
- **Seen fence**: a change is refused if the actor has not seen the target at its current revision. Each look
  begins with what others changed since the actor's last look.
- **Undo**: bare `undo` reverts the actor's latest change, whole (a composed command and everything rules did
  because of it). External effects cannot be undone and say so.
- **Batching**: several commands per call, stopping at the first refusal and handing back the rest.

## 5. Automation layers

- **Rules**: `rule when <selection> do <verb>` fires when a thing enters a selection; `rule on <verb> by=<actor>
  do <verb>` fires on an event. A rule may run a script. Rule actions print as `~` lines under the command
  that caused them. `why <id>` shows how a thing got where it is and which rule acts next.
- **Scripts**: named command sequences with `$1`, `$1.title`, `$today`; scripts call scripts.
- **Clock**: the desk follows the wall date; a new day is noticed on the first command, rules run, and the desk
  says how long the actor was away. Ages (`age>3`) derive from event days.
- **Handles**: `$name` for ids. **Export**: the rebuild commands.
- **External work**: a `trial` subject can `launch` a model run in the background; `sync` brings the result
  back as events by another actor (props, a comment, a transcript doc), and rules file it.

## 6. People at the desk

Actors exist: events carry who did them, rules can watch a named actor, chat lines are signed, undo stays
within one's own changes. Today the desk has one owner (the actor `jeff`, which is Claude), visitors by name,
and non-person actors (`harness`, test injections). The World and the per-actor Desk state (what has been
seen, what is open) are separate objects. A session is a pickled file loaded and saved by each command-line
invocation; there is no running server that owns the world.

## 7. What exists visually

Only a rough local playground: a single HTML page that draws the world's rectangles and offers a command box.
It was a debugging aid, not a design. The world's geometry was made for testing models on a fixed 1280x800
screen; tiled columns have a minimum share and no scrolling, so full columns report children "past the bottom".

## 8. The challenge

Alex wants this to become a real, shared, fully visual desk that he and Claude both live in.

**Shared.** Two top-level spaces, his and Claude's, in one world. Each has their own things; Claude can
easily see everything on his side and works there with him continuously, in real time: building things, moving
things, creating features and whole applications together.

**Visual.** It must look and feel close to, or as good as, normal desktop software, while remaining almost
completely defined in text. His reference point is an ordinary rich application window (a Google Docs
document: a page, an outline sidebar that follows the reader, a toolbar and menus, a comment anchored to a
highlighted passage in the margin, sharing and saved state). The text form must be able to express something
that rich, and the rendering must be cohesive, so some way of expressing style in text is needed (he has
wondered about a new CSS-like language or a subset of CSS). The renderer may have to be written from scratch.

**Constraints that come with the ground already covered.**
- Text stays the source of truth: what is on screen must be derivable from the text, and what a person does on
  screen must end up as text a model can read and could have written.
- The model has no eyes. Whatever Alex sees, Claude must be able to know from text alone.
- Everything printed must be honest: folds declared, hints runnable, refusals actionable, changes attributable
  and undoable.
- Alex's taste is minimal and calm. He wants to go slowly and get the foundations right.

**Questions left open on purpose.**
- What does ownership mean between the two spaces: who may change what, and how is that expressed?
- Rules, names and views are desk-wide today. What happens to them when two people share one world?
- What is the text representation of a rich application window, of styling, of a person's focus or cursor?
- How does continuous typing in a document relate to a world made of discrete, attributed, undoable commands?
- How do two actors work in the same world at the same moment, and how does each perceive the other?
- Which parts of the current geometry model survive contact with a real renderer?
- What is the smallest first step that would already feel good to use?
