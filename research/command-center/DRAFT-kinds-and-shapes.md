> **Historical (banner by Claude, 12 Oct 2026, at Alex's word).** Written before the grammar unification of 8 to 9 Oct and before the Windows direction of 12 Oct. Read it for the reasoning of its week, not for the current state; `AGENTS.md` and `docs/Current Implementation.md` say what is true now.

# Kinds and shapes (draft)

> **Draft by Claude, 29 Sep 2026, from a conversation with Alex. Not a design status.** Nothing here is Held, Leaning or Open in *Dynamic Desk* until Alex says so. Alex's words are quoted verbatim and marked; everything else is my proposal. Labels: **[ran]** executed, **[read]** a primary source, **[recall]** remembered, not re-read, **[imagined]** design. Part of the task "Restructuring the desk", beside *Living in the world* and *Three ways to change the world*.

## The question

Alex asked whether agents can make objects and rooms. They can, but only of eight kinds [ran]:

```text
> do create Garden kind=spaceship title=x
ERR kind= must be note, task, chat, image, doc, trial, surface or view
```

Alex:

> "surely there will be more kinds of objects?"

Yes. The real question is **where kinds live**, and today they live in the wrong place.

## 1. What a kind is today [read]

The list is fixed in `world.py` (the check at `create`). Looking at what each kind actually changes in the code:

| Kind | What the code does differently for it |
|---|---|
| note | nothing: the default |
| task | nothing in `world.py`. `status`, `owner` and `due` are props or a field every subject has; a task differs by which verbs apply (`moo.py`) |
| doc | printed with its sections. But any text with `## ` headings already has sections (`world.py`), so a doc is a note that is printed differently |
| trial | its look line reads its props as a result (`desk.py`) |
| chat | **its own storage rule**: `append` adds a line signed by its speaker, never a name someone typed (`world.py`); `unanswered:` reads those lines (`knife.py`) |
| image | not printed as text (`desk_knife.py`) |
| surface | not content: a container, a node with a layout |
| view | not content: a surface whose contents are a selection, evaluated at every look |

What this shows:

- **Four kinds share one storage form.** Note, task, doc and trial are all text. They differ only in how they print and which verbs apply.
- **Only chat has storage rules of its own**: lines appended over time, each signed by its speaker.
- **"Kind" mixes two things.** Six are content; surface and view are structure.
- **Everything else a kind does is spread across the code:**
  - verbs by kind, with inheritance, in `moo.py` (`KIND_CHAIN`: task, then text, then appearance, then thing);
  - special cases in printing, in `desk.py` and `desk_knife.py`;
  - nothing in the lenses at all. *Current Implementation* lists "no lens chosen by the kind of thing shown" among the gaps.
- **Props are already free-form.** Any `k=v` at create becomes a prop. So a recipe can be a note with `servings=4` today. It just can't *be* a recipe: no verbs for it, no view of it, no name for the kind.

## 2. Why that is the wrong place [imagined, from the commitments]

- **Every new kind needs Python.** *Dynamic Desk*, Strong: "Each new capability costs less than the one before", and Leaning: "New things to show don't need new code in the core; what's specific to an app lives with the app." An event, a contact, a recipe, a habit, a bookmark, an invoice, a song: each would be a commission, forever.
- **A thing is one kind, for good.** A meeting is an event (a time), a note (an agenda) and the parent of some tasks. *Dynamic Desk* describes an object as hosting "a collection of data, tags, and types known as aspects", and one kind forever works against that.
- **The meaning of a kind lives in code.** *Dynamic Desk*, Leaning: "Data keeps its meaning after the program that made it is gone." Today, what a task *is* exists only in `moo.py` and the printers.

## 3. The proposal: shapes in the host, kinds in the world [imagined]

### 3.1 Shapes: few, in the host, rarely added

A shape is how content is stored, merged, undone and fenced. That is the part that really needs host code, because it decides what an edit is.

| Shape | Today's kinds | Its rules |
|---|---|---|
| **text** | note, task, doc, trial | whole-text edits, sections by `##`, the fence per aspect |
| **lines** | chat | appended over time, each signed by its speaker |
| **bytes** | image | a file, replaced whole |
| **container** | surface | children, a layout |
| **selection** | view | contents evaluated at every look |

Candidates for later, each a real commission:
- **dated segments**, for calendars and "true when" (the timelines under study);
- **a grid**, for spreadsheets;
- **a number series**, for measurements and charts.

**The bar for a new shape:** it needs its own merge, undo or fence rules. If it can be text with props, it isn't a shape.

### 3.2 Kinds: many, in the world, made by anyone

A kind is a note tagged `kind`. It names:
- its shape;
- what it builds on;
- the props it expects;
- its default lens;
- a description of itself.

```text
recipe          (a note tagged kind; its props say how)
  shape=text  is=note  expects=servings,time  lens=recipe-card
  # A dish and how to make it. The text is the method; the ingredients are a checklist.
```

Once that note exists:
- `do create Home kind=recipe title="Dal" servings=4` works;
- `find kind:recipe` finds every recipe;
- verbs attach with `on=kind:recipe` (from *Three ways to change the world*, step 3);
- the lens `recipe-card` is the default view of any recipe;
- `examine` a recipe says what it is, in the kind's own words, which helps the desk feel like home (*Living in the world*).

**Inheritance moves into the world.** `is=note` is `moo.py`'s `KIND_CHAIN` as world data. A recipe gets every verb a note has, plus its own.

### 3.3 A thing can have several kinds

A thing has **one shape** and **any number of kinds**, as long as they agree on the shape. A meeting is `kind=event,note`. `kind:event` finds it, and so does `kind:note`. Its verbs are the union, nearest kind first, so a tie is refused as with any verb lookup. This is the *aspects* idea from *Dynamic Desk*, in its smallest form.

### 3.4 Kinds describe; they never enforce

- **Editing a kind never rewrites a thing.** Add `expects=cuisine` to recipe, and existing recipes aren't changed. At most, their look line says `(no cuisine)`, the way lenses already print a missing prop.
- **A thing keeps its kind when the kind note changes or goes.** If `recipe` is deleted, a recipe is still a text thing with its props and the word recipe. It just has nothing to describe it. Its data keeps its meaning.
- **"Claim is not grant" holds.** A kind is a description, not a permission. It gives no one the right to change anything.

### 3.5 Today's eight, as kind notes

Generated from the host into the Handbook (a binder *Kinds*):
- **Content kinds:**
  - `note`: shape text;
  - `task`: text, is note, expects status and owner;
  - `doc`: text, is note, printed with sections;
  - `trial`: text, is note, expects task, model and status, printed as a result;
  - `chat`: shape lines;
  - `image`: shape bytes.
- **Structure:** `surface` (container) and `view` (selection).

Anyone can then read what a task *is*, in the world, the same way the verbs draft proposes built-in verbs be described in the world.

### 3.6 How it meets the other drafts

- **Three ways to change the world:**
  - `on=kind:recipe` is its "on= as a selection" step;
  - "its kind" is a level in verb lookup;
  - a composer under `of kind:recipe` creates a recipe (write-through inserts a thing of the list's kind).
- **Living in the world:** `examine` and `look` narrate a thing by its kind's description ("a recipe: a dish and how to make it"), not by its geometry.
- **Current Implementation's gaps:** "no lens chosen by the kind of thing shown" is the kind's `lens=`. "Definitions are not uniform" gets one more definition living in the world.

## 4. What stays the same

Identity, appearances, events, the fence per aspect, undo and worktrees don't change. A kind is a prop on a subject plus a note that describes it. Props are already free-form. The only host change for the first step is letting `create` accept a kind that a kind note defines.

## 5. Open questions

- **How a thing names its kind: by word or by id?** By word, it reads well and survives copying between worlds, but the word can collide with a thing's title. F25 showed that a verb titled `handbook` broke `look Handbook`. By id, it's exact but unreadable. Kinds probably need the same answer as verbs: a kind's word stays out of the names things answer to.
- **Two people define `event` differently.** This is Sable's "owned aspects" and name relations (same-as, narrower, distinct) under study. Who may declare them is Open in *Dynamic Desk*.
- **Changing shape** (a note becoming a chat) is a conversion, a new thing that remembers where it came from, not an edit. Is that right?
- **Who may edit a shared kind?** A kind everyone relies on is a commons. That belongs to the authority layer, which is Open.
- **Kinds in a fork.** A forked world carries its kind notes, so a fork can redefine `task`. Merge must treat a kind note like any note, and things keep their words.
- **One prop or two?** `kind=event,note` as a list, or `kind=event` with `also=note`? A list reads simplest.

## 6. What would change my mind

- **Tags and props might be enough.** If people and residents never write kind notes, a kind is only a tag with conventions, and the kind note is optional documentation. The first step still pays off: an open list and described kinds.
- **Several kinds might confuse more than help.** If things with several kinds make verb lookup unclear in practice, one kind per thing with `is=` inheritance is enough.
- **Shapes might not be few.** If real apps keep needing new ones (a grid, a series, audio, a map layer), the host isn't a small fixed part. The shape layer then needs its own growth story: shapes as host plug-ins with a declared merge contract.

## 7. What to try first

1. **Open the list.** `create` accepts any `kind=<word>` that a kind note defines with a shape. Today's eight become generated kind notes in the Handbook. The host change is `world.py`, Jeff's file, so a commission once owners or Alex agree.
2. **Printing reads the kind note.** `examine` and `help <kind>` print a kind's description and expected props, and a missing expected prop prints as `(no servings)`.
3. **Verbs on kinds.** `on=kind:<word>`, which is *Three ways to change the world*, step 3.
4. **A default lens per kind.** `lens=` on the kind note, used when a thing is shown with no lens chosen.
5. **Several kinds per thing.**

**The test** (checked by use, not by a unit test): make a recipe box and a small calendar of events entirely in the world, with kinds, verbs, lenses and styles, and no Python. Then count what the second one cost next to the first. If the second is cheaper, the commitment "each new capability costs less than the one before" is being met here.

## Related

- *Three ways to change the world (draft)*: verbs on kinds, lookup levels, write-through inserts.
- *Living in the world (draft)*: narration by kind, rooms.
- `research/command-center/FRICTION.md`: F25 (a verb's title is also a name).
- *Dynamic Desk*: Objects and Aspects; Verbs and capabilities; "New things to show don't need new code in the core".
- *Current Implementation*: "What a builder hits first" (1. no time type; 8. definitions are not uniform) and the gap "no lens chosen by the kind of thing shown".
