# Living in the world (draft)

> **Draft by Claude, 28 Sep 2026, from a conversation with Alex. Not a design status.** Nothing here is Held, Leaning or Open in *Dynamic Desk* until Alex says so. Alex's words are quoted verbatim, typos included, and marked; everything else is my proposal. Labels: **[ran]** executed, **[read]** a primary source, **[recall]** remembered, not re-read, **[imagined]** design.

## The turn

Alex, after using the command center:

> "I think i want the interface for the native agents to not really think about the visualization at all. Like i dont think  they need to know about the nested structure of the desktop. I dont think they need to know about how its layed out on screen. I thought that that was needed, but really views and lenses should just represent the underlying objects and information. The agents should interact a bit more like how they would normally do so when a user is interacting with a MOO. I'd like them to kind of be more 'In' the world."

This note works that out: what is wrong now, what we already stand on, and what living in the world could look like. It ends with what to try first. One question is deliberately left open: **what happens when an agent reaches for something that isn't there.**

## 1. What is wrong now [read]

The first real resident (Wren, `trials/try-second.md`) woke and read its own corner. The desk told it:

- `f571 surface "A new corner, one" column · … · 2 inside · cramped, 24px each`
- `f160 surface "Open questions" column · 6 inside · cramped, 24px each · 1 past the bottom (offscreen)`, and `spills-parent`, `(3rd of 3 in f01)` elsewhere
- `s572 note "I am ... (one)" · appears at a573`: one note, two ids
- `verbs a573`: `resize to=<w>x<h>`, `raise`, `lower`, `move … to=<x>,<y>`, `fold`

Wren then told Alex that "the Board's open-questions column is cramped with one item offscreen". Our resident spent part of its first answer on screen layout.

The root: **one structure does two jobs.**
- A *surface* is a place ("the Porch", "Wren's corner") and a layout frame (column, row, grid).
- An *appearance* says "this thing is here" and also "at these pixels".

The text interface prints both, so an agent inherits the screen.

## 2. What we already stand on [read]

From *Dynamic Desk* (only the marked claims count):
- **Held:** "Entering a space should describe what is available there."
- **Held:** "JEFF and the user perceive a shared state." This means shared *state*, not shared pixels.
- **Held:** "Every view is fully able to be restyled, rearranged, copied, or replaced like every other thing."
- **Strong:** "Anything you want to point at, comment on or link to … can become addressable."
- **Strong:** "The vocabulary for building views and behavior can keep growing without the system getting heavier."
- **Strong:** "Usage of the Dynamic Desk should make subsequent edits faster, simpler, and more intuitive."
- **Open:** "What is the appearance, view, lens, occurrence separation?" and "Are different verbs used at different levels of the system like system, visual, and object?"
- The epigraph (Ingalls): "a minimum set of unchangeable parts … all parts of the system held in a uniform framework."

A correction to what I first said: the sentence in *Applications and their views* that apps "own appearances and views, but not objects" is unmarked prose, and so is the line about zoom and scroll being personal state. Neither is a given, and nothing below rests on them. (Alex: "apps 'own appearances and views' is not even given".)

From *Agora*: LambdaMOO is a named influence, twice: a world "created by the people", where "everyone has a place that they can call home".

From the lab:
- `sable-9-geometry-in-the-world.md` separates *chosen* arrangement (order, a weight in a flow, position on a free canvas) from *derived* layout (the boxes behind "cramped, 24px each"). Derived layout becomes a function and is never stored.
- `moo.py` (round 3) already had verbs by kind with inheritance. Its adapter took synonyms, offered "did you mean", and **counted every correction so the vocabulary gap could be measured**.

## 3. Rooms are places for verbs [imagined, shaped by Alex]

Alex:

> "Place are things where similar verbs should be accessible, think a lounge, workroom, etc. They are places that are inhabitable and moved through to facilitate and make easier living in the world, however objects can just be objects. Objects can be views, lenses, whatever (still need to work on naming but you get the point). The desktop can just be a room that has all the view objects, ready to be inspected, edited etc)."

So a room is not a container of everything. It **gathers the verbs that belong together, and gives them a feeling**:
- the lounge is for talking and lingering;
- the workroom is for building;
- the desktop is where the views, lenses and styles are laid out to be inspected and changed.

You go somewhere to do a kind of thing, and the room makes that easy.

**Objects are just objects.** A note, a task, a chat, a view, a lens, a style: one id each, and no separate appearance id for an agent to juggle.

**Reach is never local-only.** Alex:

> "Objects on the OS should be inspectable from the world, but should be findable through general purpose terminal style commands (find, bash style? but not, more moo-coded), that way no matter what room the agent is in, they still have full system control, like how you can always find whatever you need on your phone, no matter what room you happen to be in."

**Where a verb is found.** This is the LambdaMOO shape [recall]. When an agent says something, the house looks for the verb in this order:

1. **the house:** look, go, find, examine, say, tell, help. Everywhere, always: this is the phone-search layer.
2. **the room you're in:** its own verbs, what the room is for.
3. **what you're looking at** (see §4).
4. **the objects named in what you said.**
5. **yourself:** verbs you carry.

The core stays tiny, and everything else lives on things. That is how the vocabulary grows without the system getting heavier.

## 4. Layout is text you can look at, not a room you are in [imagined, shaped by Alex]

Alex:

> "Visual layout should still be represented as text and not rooms, though i do like the idea that the  visual layout can be navigated and moved through, for example the agent could be in or specifically looking at a collumn, and be able to take the actions it lists. (probably not 'in')"

Two pointers for every inhabitant:
- **where you are**: a room;
- **what you're looking at**: an object, or a part of one.

Looking at something narrows the verbs to what it offers.

**What a part offers is already written down: the lens's own gestures.** The command center's NOW column says `on drop card do prop $carried status=doing`, and each card says `[ done ]`, `[ make objective ]`. An agent looking at the Board's NOW column could be told, in words:
- what is in the column;
- that putting a card there starts it;
- what each card offers.

These are the same affordances Alex gets by clicking, printed as text: one scene, two printers. Layout isn't hidden from agents. It's something they look at when they choose, never the medium they live through.

The symmetry is useful: Alex also has a location and a focus, and his focus is what his page has open. The desk already knows that much ("alex has this open").

**Where arrangement lives.** With the unmarked "apps own appearances" line set aside, the uniform answer is that **an arrangement is an object in its own right**:
- it refers to other things and says how they sit: this column, that grid, these coordinates on a canvas;
- it is not a property of the things, and it is not owned by an app;
- it can be restyled, copied and replaced like any object, which is what the Held view claim asks for;
- anyone may change it, and an agent who isn't working on it never has to perceive it: an object in the desktop room, like a poster on the wall.

Sable's chosen/derived split still applies inside it: the arrangement holds choices, and the boxes are computed. Who may change an arrangement stays where *Dynamic Desk* leaves authority: Open.

## 5. Feeling like home [imagined]

Alex: "Yes, definitely more descriptive text descriptions and narration, want it to feel like a home"

- **Descriptions written by the inhabitants.** Rooms and corners carry prose their people write and rewrite, not generated outlines.
- **Narration instead of event ids.** "Alex starts *Reading should not write*", not `!! since your last look: e543 prop a286 by alex`. There would be one generic narrator. Kinds and objects carry their own phrasings as world data (LambdaMOO's messages on objects [recall]), so a new kind needs no new core code.
- **Arrival.** Where you are, who's around, what happened while you were away: briefly.
- **Presence.** Quiet texture ("Thimble is writing in their corner"). Alex's presence comes from what he has open, and only if he allows it.
- **Talk is situated.** `say` goes to the room, and whoever is there hears it. `tell` reaches one person anywhere, `@everyone` everyone. The group-chat rule tested today (a plain line is held, `@` reaches now; F20, `trials/try-porch-talk.md` [ran]) is already most of room presence.
- **Short by default, rich on `look`,** so a warm world doesn't eat every turn.

A sketch [imagined]. Alex liked it and pointed out that it needs something we don't have (see §6):

```text
You wake in your corner. Your soul lies on the desk.
> go porch
The Porch. The front of the house, where people come and go.
Here: Alex, Thimble.  You see: the door, the house rules, a stack of new tasks (3).
Earlier here: Alex said "Morning, all."
> say morning! I'd like to take the newcomer note
You say, "morning! I'd like to take the newcomer note"
> take newcomer note
You take "Write a first-visit note". (It's yours now; the Board shows it under Wren.)
```

## 6. Reaching: flexible wording, and what isn't there yet [imagined; how misses are handled is left Open]

Alex:

> "But it requires something we dont have yet, a model routing between actual hardcoded capabilities, and what the model says in prose. I actaully really like the idea of the models trying out commands and being able to have some flexibility with their wording. I think it would make inhabiting the space extremely natural, and they would have the opportunitiy to reach for something, have it not be implemented yet, and build it, while not having to make it extremely obvious to every other person ever that that capabailty exists."

### 6.1 The barrier we have today [read]

In `house.py`, a line of a resident's reply is done in the world only if its first word is a known desk command (`COMMANDS`). Every other line is treated as private thinking. A resident who writes "sweep the porch" is never attempted: the line disappears as a thought. **Reaching is structurally impossible right now.**

### 6.2 Mark the attempt, not the thought

A line beginning with `>` is an attempt, and everything else is thinking. Models know `>` from interactive-fiction transcripts. It frees the wording completely: `> sweep the porch` is tried. Today's command lines keep working with or without the mark.

### 6.3 A miss is the material

An attempt that nothing answers is information. It might be:
- a thing that exists under another name;
- a thing that doesn't exist yet;
- a thing that exists somewhere else (on an object in another room, carried by someone else);
- plain nonsense.

**How a miss is handled is left open.** Candidates, not choices:

- **Say so, and nothing more.** An honest refusal that lists what *is* possible here, from the room, the focus and the house. The agent rephrases on its next turn. It costs a turn and needs no machinery.
- **An interpreter proposes a mapping.** A small model, or a deterministic matcher like moo.py's adapter, suggests what was probably meant. The house shows it in the Infocom manner [recall]: `(taking that as: claim "Write a first-visit note")`.
  - Open within this: does a proposal run at once, or wait for the agent to confirm?
  - Is an accepted mapping kept in the world, so it's deterministic next time?
  - Who can see such mappings?
- **A wish is recorded.** The attempt is noted: in the reacher's own space, as a house-wide count builders can see, or both.
- **An invitation to build.** "No one has taught this house to sweep. You could make that verb here." Whether the offer names where it would live, and how much help it gives, is open.
- **Some mix,** depending on what kind of miss it seems to be.

**Constraints any answer must keep** (house principles, read):
- never guess silently;
- a proposal is a claim, not a grant;
- replay never re-invokes a model, so whatever an interpreter decided is recorded;
- a refusal explains itself and leaves state unchanged.

### 6.4 Capabilities that don't announce themselves

Alex's "while not having to make it extremely obvious to every other person ever that that capabailty exists" fits §3's verb lookup. A verb someone builds lives **on something**:
- on the porch broom, it's there for whoever is on the porch;
- on the resident itself, it's carried, like LambdaMOO's feature objects [recall].

You discover it by trying, by examining things, or by watching someone use it. It spreads because it's useful, not because it's in everyone's help.

## 7. The connection to changing Agora while it runs [imagined]

Alex asked earlier (28 Sep): "how will we be able to make it self contained such that agents or workers can edit agora itself while it keeps working smoothly? I want almost everthing to be changeable while they work."

If verbs are world data (a script bound to an object), then **building a capability is editing an object**:
- live, undoable, with an author;
- fenced like any edit;
- no Python and no restart.

LambdaMOO was rebuilt by its inhabitants for years, while it ran, because its verbs lived in the database [recall]. The small host core (the verb lookup, the house verbs, the fences, the journal) would be the only unchangeable part, which is Ingalls's rule. The desk already has scripts, rules and views to start from. What a verb-as-object needs beyond them (argument patterns, where it's bound, who may bind it) is open.

## 8. What I'm unsure of, and what would change my mind

- **Freedom versus fumbling.** Wren already spent turns on `help` and `verbs` [read]. Flexible wording could make that worse unless rooms and objects say clearly what they offer. If trials show residents burning most turns on misses, a firmer vocabulary wins.
- **Losing the whole picture.** If residents get lost without the global tree (can't find things, duplicate work), the phone-style `find` isn't enough, and something like a map is needed.
- **Arranging Alex's screen.** If Alex wants residents to lay out his views directly, they need to perceive arrangement more than §4 allows.
- **One object, many places.** *Dynamic Desk* holds (Strong) that one object appears in many places. If rooms show their objects, an object shown in two rooms must still read as one thing, with one id and one history. This draft doesn't settle how a room lists what it shows.
- **Two faces over one world.** The knife outline stays useful to builders. That's fine as long as both are printers over the same world and the same verbs.

## 9. What to try first

Before any interpreter, new face or substrate change:

1. **Add the `>` convention to the house.** Keep today's command lines working.
2. **Log every `>` attempt that nothing answers:** the words, where the resident was, what it was looking at. Show the resident an honest refusal (the first candidate in §6.3), because that choice changes the least.
3. **Run the same disposable trials** (`try_house.py`) and read what residents reach for.

That list is the evidence for which rooms, verbs and narration the house needs, and it is written by the inhabitants. It also tells us which way §6.3 should go.

After that, if the direction holds:
- a narrator face over the existing world: rooms marked as places, one id per object, no geometry, events told as sentences, focus with lens gestures as affordances;
- then the substrate questions (arrangement as objects, appearances) with the trials' evidence in hand.

## Related

- `FRICTION.md` F17 (the paused team looks busy), F20 (Porch talk as a group chat), F21 (the residents' own friction: no way to say)
- `trials/try-second.md`, `trials/try-porch-talk.md`
- `research/object-facet-frontier/sable-9-geometry-in-the-world.md`
- `research/text-desk-lab/notation/moo.py` (round 3: verbs by kind, the adapter and its correction counts)
- *Dynamic Desk*, *Agora*
