# Juniper 7: the default apps as drawn lenses

25 September 2026, evening, on Jeff's redirect (Alex: the staged compiler, and how things are drawn). For each of the desk's own kinds I write the lens as it should read. Then I list what it needs **drawn** that the painter (lens.js, 150 lines) cannot draw today, and what it needs **said** that the language (scene.py) cannot say today. Notes and tasks come first, because I am living on them in my corner (a384 is the running list).

Labels:
- **[ran]**: typed in an in-memory desk at 7731e64 or later, with the print quoted.
- **[imagined]**: the lens as it should read, with its proposed words marked `‹…›`.

The probe scripts are in my scratchpad (`lp.py`, `tasks*.txt`, `notes*.txt`). They were not committed, because they are notes to myself rather than instruments.

## Tasks

### What runs today [ran]

```
tasks : column, role sheet
  add : text "Add a task", role card.plain, on edit do create f01 kind=task title="$value" owner=juniper status=open
  late : column, only when kind:task,prop:owner=juniper,-prop:status=done,due<today
    h : text "Overdue", role heading
    list : column, of kind:task,prop:owner=juniper,-prop:status=done,due<today, each task
  now : column
    h : text "Today", role heading
    list : column, of kind:task,prop:owner=juniper,-prop:status=done,-due<today,-due>today, each task
task : row, role card.plain
  box : text "o", role tool, on click do prop $item status=done
  t : text "$title", role title, on edit do retitle $item title="$value"
  d : text "$due", role meta, on edit do due $item on=$value
  w : text "waiting on $next", role tag, only when prop:status=waiting
```

This compiles and prints honestly. It is wrong in one place a person would not notice. "Today" lists the undated waiting task ("Alex's two more ordinary things"), because `-due<today,-due>today` is also true of a task with no due date. The language has no `due=` term and no "has a due date" term:

```
find kind:task,due=2026-09-28
ERR unknown selection term 'due=2026-09-28'
```

An upcoming week written the natural way is worse:

```
days : column, derive week = days-from $today 2026-09-29, over $week, each day
day : column
  h : text "$it.date", role heading
  list : column, of kind:task,...,due>$it.date, each task
```

This prints the task due on the 28th under the 25th, 26th and 27th, and under the 28th prints `0 of … (empty)`. That is a silent wrong. `due>` is the only per-day comparison available, so "due on this day" cannot be said. 

**`$today` in a lens is a trap [ran].** The week above seemed to work, but only because the command that wrote the lens expanded `$today` into the lens text. The stored lens says `days-from 2026-09-25 …`, and tomorrow it will still start from the 25th while printing as current. Escaping the word (`\$today`) keeps it in the lens, but then it does not bind: `end: (uninterpretable: day-n wants <date> <n>; got '$today' '8')`.

The host names that scene.py classifies (`me`, `today`, `session`) did not evaluate anywhere I tried, at 7731e64 with Jeff's stages 1 and 2:

- in text: `"me= today= session=" (no me, no today, no session)` (visible);
- in `only when $due < $today`: `(absent: no today)` (visible);
- in `of kind:task,prop:owner=$me`: `0 of … (empty)` (a silent 0-of);
- in a derive: uninterpretable (visible).

Chained derives do work [ran]: `derive end = day-n … 8, derive days = days-from … $end` gives eight rows.

### As it should read [imagined]

```
tasks : column, role sheet
  add : ‹input› "Add a task", ‹on submit› do create ‹$here› kind=task title="$value" owner=‹$me› due=‹$value.date›
  late : column, of kind:task,owner:‹$me›,‹open›,due<today, ‹sort due›, each task
    h : text "Overdue · $count", role heading, only when $count > 0
  week : column, derive end = day-n $today 8, derive days = days-from $today $end, over $days, each day
  someday : column, of kind:task,owner:‹$me›,‹open›,‹-due›, ‹sort order›, each task
  done : column, ‹folded›, of kind:task,owner:‹$me›,prop:status=done,age<1, each task
day : column, on drop task do due $carried on=$it.date
  h : text "‹$it.date as relative›", role heading
  list : column, of kind:task,owner:‹$me›,‹open›,‹due=$it.date›, ‹sort order›, each task
task : row, role card.plain, carry, on drop task do move $carried before=$item
  box : ‹check› ‹$done›, ‹on toggle› do prop $item status=‹done|open›
  t : text "$title", role title, on edit do retitle $item title="$value"
  when : text "‹$due as relative›", role meta, on edit do due $item on=‹$value.date›
  w : text "waiting on $next", role tag, only when prop:status=waiting
```

### Needs said (language)

1. **Date terms:** `due=<date>`, and has-a-due (`due`, `-due`). Without them, both "today" and "the day's list" are wrong silently.
2. **Order:** `sort <field>`, and a manual order that a drop can write. Today a repeat lists things in desk order, and `sort` is refused as an unknown term.
3. **Dates as a person says them:** `due=tomorrow` is refused ("must be YYYY-MM-DD"), both on create and on edit. A person types "fri". The interpretation must print what it resolved, for example `fri -> 2026-09-26`, as every derive already does.
4. **Relative display:** "Today", "Tomorrow", "Mon 28". This is a derive (`relative <date>`), and it should print its inputs.
5. **Chained derives:** these work [ran]. What they lack is a today that binds (item 6).
6. **`$me`, `$today` and `$here` bound at evaluation, in every position:** text, `only when`, `of` and derive. A lens belongs to someone, and a lens about today is about every day it is opened. Today mine must say `owner=juniper` literally, and any date in it must be frozen. The command that writes a lens must also not expand `$today` inside the lens text: a lens describes later, it is not a command about now.
7. **Statuses with meaning:** open and done at least. `waiting` needs a "who moves next" (Astra's a416, my c439).

### Needs drawn (painter)

1. **An input that is empty and says what it is for.** Today the placeholder "Add a task" is the part's text. To type a task, the person first deletes the placeholder, or sends "Add a taskBuy milk".
2. **A check control** with a checked state, which Space and Enter can operate. Today a click part is a `div` that the keyboard cannot reach. Pike fixed this for drag only.
3. **Done, drawn as a moment.** Clicking `o` makes the row vanish, because the list filters done out. A person expects to see the check land and to have a moment to undo it. The painter needs a way to keep a leaving row, marked, until the person moves on, and an undo gesture.
4. **Where a drop will land.** `carry` and `on drop` compile [ran]. The painter should show which parts are receivers while something is carried.
5. **An empty day**, drawn faint rather than as the word "(empty)". The text print keeps the word.

## Notes

### What runs today [ran]

A list and a page, with the page's sections and links:

```
notes : row, the kind:note,title:Charter as cur
  list : column, role sheet, of kind:note,-tag:lens, each entry
  page : column, role sheet
    t : text "$cur.title", role heading, on edit do retitle $cur.item title="$value"
    secs : column, of sections:$cur.item, each sec
    back : column, of links:$cur.item, each ref
entry : column, role card.plain, on click do prop notes open=$item
  t : text "$title", role title
  first : text "$text", role body, clamp 1
sec : column
  h : text "$heading", role heading
  b : text "$text", role body, on edit do rewrite $item text="$value"
ref : text "linked: $title", role meta
```

Four findings from running it:

1. **Which note is open cannot be said.** The page is fixed to "Charter" by title. `the $open as cur`, with `open` as a prop of the lens note, prints `the $open (empty)`: a lens's own prop does not reach `the`. Even if it did, it would be a shared prop, and my opening a note would change yours. The only honest place for it is per-viewer state.
2. **A section edit rewrites the whole note.** The lens reads well and cannot be used. Each section prints `edit: do rewrite a05 text="$value"`, because a section's `$item` is the note. Typing into the "Tasks" paragraph and pressing Enter replaced all six lines of the note with that paragraph [ran]. The text print is honest: an agent reading it sees that the edit rewrites a05. The pixels show a paragraph that looks editable on its own. The painter cannot show that an edit reaches beyond the part it is drawn on.
3. **A note with no headings shows "(before the first heading)" as its heading.** The row source's marker becomes content once a lens prints `$heading`.
4. **`as n` is refused** ("would shadow a built-in name"). That is honest, but `n` is the first name a person reaches for. The same built-in cost me a crash in round three.

### As it should read [imagined]

```
notes : row ‹widths 1:3›
  side : column, role sheet
    find : ‹input› "Search", ‹on input› do ‹view› query=$value
    list : column, of kind:note,-tag:lens,‹?$viewer.query›, ‹sort touched desc›, each entry
  page : column, role sheet, the ‹$viewer.open› as cur
    t : text "$cur.title", role heading, on edit do retitle $cur.item title="$value"
    body : ‹text› "$cur.text", role body, ‹on edit› do ‹rewrite section› $sec.id text="$value"
    back : column, of ‹links-from›:$cur.item, each ref
entry : column, role card.plain, ‹on click do view open=$item›, ‹selected when $viewer.open=$item›
  t : text "$title", role title
  first : text "$text", role body, clamp 1
  when : text "‹$touched as relative›", role meta
ref : text "$title", role meta, on click do ‹view› open=$item
```

### Needs said (language)

1. **Viewer state as a frame** (`$viewer.open`, `$viewer.query`) and a verb that writes it (`view k=v`). It is never journaled or merged (Sable's item 7, Pike's viewer store), yet it is fenced like any read. Both notes and tasks need it: the open note, the search, and the folded "done".
2. **An edit that writes exactly what the part shows:** a section, or a hunk of text. Without it, the editable body of a note is either the whole text (whole-value conflicts, Sable's S8) or a trap (finding 2). This is the text gateway, seen from the lens.
3. **`$touched`**, a thing's last-touched time as a field (examine has it, the lens does not), and `sort`.
4. **Links by direction** (`links-from`, `links-to`), and mentions in prose as links. In my Charter, the words "See Living on notes and tasks" and the `refers` link are two separate things that nothing keeps in step (Embark's @-mentions).

### Needs drawn (painter)

1. **Multi-line editing.** Enter is a newline in a note body. Today Enter sends and blurs, and only Shift+Enter makes a line. The painter needs a part kind whose send is on pause or leave, not on Enter.
2. **The extent of an edit.** When a gesture writes more than the part shows, either draw that extent (the whole note highlighted as the target) or refuse to draw the part as editable. The text print already says it; the pixels must not say less.
3. **Proportional widths** for a list-and-page layout. Pike's S14 saw the document column slide 60 to 80 px as Alex typed, because columns are content-sized.
4. **The selected entry.** A per-viewer mark on the note that is open.
5. **Headings, lists, code and links inside one body.** Either the painter draws a small, closed markup inside a text part, or the lens expresses structure through sections, and then edit-per-section (language 2) is required.

## What the two share

- Viewer state.
- An edit whose extent equals what is drawn.
- Order.
- Words a person types (dates) that resolve and print what they resolved to.

The first two are the same finding as Pike's report 1 and Sable's S8, seen from inside an app: **the fence is honest because it judges data, and a lens is honest in text. The pixels become dishonest wherever a gesture writes a bigger thing than it is drawn on.**

Next here: a document, a chat with code and diagrams, and an image, in that order.
