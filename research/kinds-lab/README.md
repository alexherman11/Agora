# Kinds that nest, and a graph you can walk

> Draft by Claude, 27 Oct 2026, for Alex's design gate. **A proposal, not built.** Nothing in the kernel, the old desk or the live desktop world was changed. All probes ran read-only on copies of the desktop world's log. Asked for in clutter decision C10 ([[clutter-lab/README]]); his words are quoted below. The working notes behind this are in `NOTES.md`; the probes are in `trials/`. The page for his answers, [Kinds that nest](https://claude.ai/artifact/3L3AbeF9N5zAdRuDuqydHT), is published from `design.html` beside this file; his answers save to its store (`decisions/<id>`, twelve decisions K1 to K12).

Labels as AGENTS.md asks: **ran** (executed here, number as printed), **read** (a primary source, or a secondary summary where it says so), **recall** (from memory, not checked this session), **imagined** (design or thought experiment).

## What Alex asked

On 27 Oct, on the clutter page, in place of downloading an embedding model:

> "i want to start making a graph out of the agora space. Becasue we have so many objects that are not well linked, i think we need ways to traverse them. … for something like a railing on the side of a boardwalk in a marsh, you can think of it as a railing, you can think of it as a fence, you can think of it as a wood and a wall, and they're all kind of the same things, but some of them are subsets of other things. And a railing is a type of wall, but a wall isn't necessarily a railing. … we will have things like a document and then we will have things like a pamphlet, or we'll have things like a running program, or we'll have things like a video game. And I think we have to have almost like an object-type inheritance type thing. So we have like nested kinds. So if something specifies a certain number of features or aspects … If something has less than it, it kind of sits inside. And so a verb for something that is sitting inside of it, something that has the same but less of the aspects, should probably also apply to the outer one. Maybe not always … I want you to think kind of deeply on this and explore this idea of how we can think about kinds more dynamically"

And on decision C2 of the same page: a kind's lifetime should be "an optional parameter on kinds", which nested kinds could inherit.

**How I read it.** He reaches for nested kinds *because* things are unlinked. A book with no citations is still findable because it sits on a shelf among its kin. Today's kinds are flat islands: 23 of the desktop world's 50 kinds have exactly one thing (**ran**). Nesting turns islands into shelves within shelves, so a railing leads to other walls. The graph and the nesting are one idea.

## What is there today

**Kinds are strings** (**read**: `kernel/kernel.py`, `readings.py`). A thing's `kind` aspect is a name. A `kind=kind` thing can declare fields and a compose form, but it constrains nothing (KITS.md says so). Of 50 kinds in use, 16 are declared (**ran**).

**A kind already does nine jobs**, each of which nesting would change differently (**read**):

| Job | Where | Should it pass down a nesting? |
|---|---|---|
| Views pick things by kind | `rows <kind>`, a board's `model_kind`, a map layer's `shows rows spot` | Yes, freely: it only reads |
| Words find their targets | namespace = kind or a hyphen part; `<kind>` in usage | Yes, with exceptions (below) |
| Authority | `grant … only=kind:window` | **No**, not through someone else's classifying |
| Hearing | `rule … of_kind=` | Yes: rules act as their author anyway |
| Explaining | `help <kind>` lists words whose help mentions it | Yes |
| Making | declared `fields`, `required`, compose labels | Yes, accumulating |
| Look | `accent nb-kind-*` | Yes, nearest wins |
| Name hints | `window.close Help` prefers a window called Help | Yes |
| Lifetime (proposed, C2) | `lifetime` on a kind | Yes, nearest wins |

**Names already nest, and mix up two relations.** `plain_verb` fits `task.*` words to `taskboard-task` because `task` is a hyphen part of the name (**read**). Across the world that rule gives 13 hyphenated kinds 141 family words (**ran**, `trials/fits.py`). By my reading it is right where the name means *a kind of* (`taskboard-task` gets `task.*`) and wrong where it means *settings for* or *part of*: `wm-settings` gets `wm.close` and `wm.minimise`, which act on native windows; `model-settings` gets `model.summarize`. Most hyphen names in this world mean *belongs to*. The kernel reads them as *is a*.

**One name, several kinds.** "Document" has three makers in one world (**read**): the community post kind (dk337, "Share a document"), the upload reader (`blobs.py` classifies a file as file, photo, document, table, event or media; dk863 is `seabright-ground.json`), and the Writing app (`apps/writing/install.py`, Markdown with collections and comments). They have different aspects and share a bare string. The Writing app is not installed live yet (**ran**: no writing documents in the log at 27 Oct afternoon). When it is, its `rows document` (**read**: `writing.lens`) will also list the uploaded JSON file, which has no text to draw (**imagined**). "Event" has two makers (community, upload).

**Kinds hide in code.** The window manager classifies native windows by a cascade of tests, each with a `why`: not top-level, cloaked, shell class, owned dialog, frameless with no app rule, elevated (**read**: `agora-wm/win32_host.py`). The game gate defines "video game" three ways at once: a declared list (`KNOWN`, `rocketleague.exe` first), a name test (`'game' in name`, minus `HELPERS`), and a state test (full-screen in front). Each exception (the touch keyboard on 26 Oct, Agora's own wallpaper before 27 Oct) was a source edit after a misfire (**read**: `kernel-desktop/gaming_gate.py`, `win32_host.gate`). None of this is visible, explainable or correctable from the world.

**Rocket League is the whole question in one case.** It appears in the world twice: Alex's dock request (dk806, "i want rocket league to appear here") and a task (dk811: it won't open, a window error, not signed into Steam). There are no links between them, and the game is not a thing (**ran**). Its third appearance is the gate's hard-coded list.

## What the probes found

All on a copy of the desktop log (533 live things at 11:57, 27 Oct). Scripts in `trials/`.

**1. Structure finds adjectives well and nouns badly.** (**ran**, `lattice.py`, and the first pairwise test.)
- Pairwise "kind A's aspects are a subset of kind B's" proposed 20 nestings. By my reading about 6 make sense. The rest come from overloaded aspect names: `text` is prose on a note, CSS on a style, lens source on a lens; `shows`, `order` and `on` mean different things on different kinds. `note` and `guide` have the same shape, as do `soul` and `charter`.
- Computing the whole concept lattice (Formal Concept Analysis over kinds × aspects) after a five-line cleanup (title and label joined to name, colour and color joined, `text` on styles, themes and lenses renamed as code) gave 23 concepts. About 11 are useful, about 8 weak, 3 or 4 wrong (homonyms survive: `on`, `where`, and `about`, which is a link on some kinds and prose on a chat).
- The useful ones are **adjectives that cut across nouns**: *writing people read* (11 kinds: ask-request, board-catch-up, charter, guide, note, post, said, soul, taskboard-event, taskboard-task, topic); *chooses a model* (house-agent, model-settings, taskboard-settings); *a file* (document, file, which also settles the document collision); *sits on a bar*; *in a chat*; *carried from the old desk*.
- Synonyms in use: `name` 207, `title` 82, `label` 27; `colour` 34, `color` 3 (**ran**).

**2. The space is badly linked, and most of the missing links are already written down as text.** (**ran**, `connect.py`.) Over 158 content things (everything but words, grants, components, modules, widgets, buttons, help topics and kind declarations), counting islands and the largest connected group:

| Edges counted | Isolated things | Largest group |
|---|---|---|
| none | 158 | 1 |
| links that say what a thing is about (not who made it or where it sits) | 81 | 31 |
| + text values naming another thing (`lane=Now`, `who=claude`) | 30 | 84 |
| + ids mentioned in long text, + things changed in one act | 25 | 100 |
| + flat kinds as shelves | 6 | 136 |

By my reading about three quarters of the name-valued links are real: `who=claude` (30 tasks point at the agent), `lane=Backlog` (25), `style=bars` (11). The wrong ones are exactly where the aspect doesn't say what kind it points at: `lane=Now` matches both the lane and a widget called Now. If an aspect said "a lane names a taskboard-lane", the text would resolve to one thing.

**3. Words that take any thing mostly need something narrower.** (**ran**, `top.py`.) 25 words take any `<thing>` or `<id>`. By their help, 7 really mean anything (look, set, forget, history, help, test, ask). 9 need an adjective they cannot say: `claim` needs seats, `map.near`, `map.where` and `map.show` need a location, `model.summarize`, `model.classify` and `model.preview` need prose, `component` and `widget` need code. 9 are `task.*` words that need a task.

**4. The dictionary already marks the risky words.** (**ran**.) Of 127 do words, 111 can be undone, 8 cannot (`undo` itself, `wm.focus`, `wm.minimise`, `wm.pin`, `wm.unpin`, `wm.restore`, `wm.arrange`, `component.health`), and 8 are external (`media.*`, `house.stop`, `house.wake`, `wm.close`). Nearly all the irreversible ones act on the PC itself, which is the running-program family Alex used as his example.

**5. Under a small proposed vocabulary, islands join shelves.** (**imagined** vocabulary, **ran** over real data, `dryrun.py`.) For example: `wm-settings` reads as "a settings, so a preference; settings for the window manager", beside five other settings. Alex's Rocket League request reads as "a request, so a remark", beside 36 other remarks. JEFF's `house-agent` thing gets the adjective *chooses a model*. I first filed it as "an agent", but its aspects say it is settings for running JEFF. The adjective was a fact; my noun was a judgement call, and arguably wrong. 114 of 158 content things gain an outer noun under that vocabulary, and 88 gain an adjective other than "titled".

## The idea

### A kind is a named way of seeing a thing

A kind is a **test** that says which things it sees (most often "has these aspects", Alex's definition), plus the **words** that work through it, plus **defaults** it passes to what it sees: look, fields, lifetime. A thing can be seen many ways at once. The railing is seen as a railing, a wall, a fence and as wooden, and each way of seeing brings its own words.

The kernel already has bounded tests (`test <thing> expr=`, `predicates.py`: `field`, `used`, and/or/not, equality) and runs them **as the reader** (**read**). So a kind defined by a test never reveals what the reader can't see: a thing whose location is hidden from you is not "located" for you. Missing for this: membership in a list, comparisons, and a way for one test to ask about another kind (`is('wall')`).

**Four meanings of "more dynamically"**, all one mechanism here:
1. *Computed*: adjectives are live tests over aspects, so a thing that gains a location appears on the map.
2. *Over a life*: a note becomes a task, a post becomes a decision; each `is:` is a fact with its own history.
3. *By who is looking*: a group's kinds apply in that group (below).
4. *Found*: the world's own concept lattice proposes kinds nobody declared, as probe 1 found *chooses a model*.

### Nouns and adjectives

Alex's railing example holds three different relations. A railing *is* a wall (what it is). It *serves as* a fence (a role: it marks a boundary). It *is made of* wood, which is not essential: replace it with steel and it is still the railing. OntoClean's rule (Guarino and Welty; **read**, secondary) is that a property not essential to its things may not sit above one that is: "student" cannot be a superclass of "person". So:

- **Nouns** say what a thing is. They are declared, they nest, they carry identity, making and look.
- **Adjectives** say what a thing has, does or is in right now: located, timed, writing, wooden, running, full-screen, chooses a model. They are computed and never parents.

Probe 1 is the evidence: structure found adjectives reliably and nouns poorly.

### `is` is a promise the world checks

`railing is wall` promises that every railing has what a wall has, so wall's words can reach it. That is Alex's own rule ("has the same but less of the aspects … sits inside") turned into something the world can check:
- **declared and fits**: fine;
- **declared but doesn't fit** (a railing missing `height`): a broken promise, shown the way a stale link is shown ("Nothing goes silently stale");
- **fits but not declared**: a suggestion, offered as one click ("Railing looks like a wall: it has height, length and stands. Is it one? Yes · No"). Nobody types `is=`. This is Windows Game Bar's move (**read**, secondary): it guesses, and per app offers "Remember this is a game"; "Record what happened" stays greyed out until that is checked.

**One `is` for things and kinds.** `dk812 is railing` and `railing is wall` are the same relation, stored like placements: SHAPE gives a thing an aspect `in:<place>` for each place it is in, so a thing gets `is:<kind>` for each kind it has been declared to be, each with its own history ("became a task on 3 Nov, by Alex"). Kinds nest by `is:` as groups nest by `in:`. Wikidata is the warning against splitting the two: one quality study found that nearly half of 935k "subclass of" edges were later replaced by "instance of" (**read**, secondary: arxiv 2107.00156). People confuse "a kind of" with "one of". One relation means nobody has to choose.

**Kinds are things that things follow.** Kind declarations are already things (dk337). If `is` means *follow*, a kind behaves like a prototype in Self or JavaScript (**recall**): its things take its defaults (look, fields, lifetime, words) unless they say otherwise, nearest wins. That answers C2: `lifetime` is set on a kind and passes down; a narrower kind or one thing can say otherwise. Dynamic Desk already leans this way ("A copy is a new thing that remembers where it came from"; "A value that depends on another either follows it or says plainly that it has stopped following"). The risk is the fragile parent: change a kind and everything that follows it changes. The carry rules below keep that from reaching anything irreversible.

### Words say what they need

A word's usage names what it needs: a noun (`task.done <task>`) or an adjective (`map.near <located>`, `model.summarize <writing>`, `claim <seated>`). It reaches every thing that has it, by promise or by fit. When several kinds a thing has offer the same word, the nearest kind's version wins: the dictionary's ladder over groups (find a word in the line's group, then around it, then the place) gets a twin ladder over kinds.

This is how Windows' own shell builds a file's verbs (**read**, secondary): from the file's ProgID, then `SystemFileAssociations\<ext>`, then its PerceivedType (image, text, document, gamemedia, …), then `*` and AllFilesystemObjects, merged. A verb registered on "image" reaches every image format. Rich Hickey's "Maybe Not" (Clojure Conj 2018; **read**, secondary) argues the same split: a schema says what a thing may hold, and each function's *selection* says what it requires, in context.

### Maybe not always

Seven ways a word should not simply carry, each with a real or near-real case:
1. **Same word, different act.** `close` is three acts today: `window.close` (forget the window thing, undoable; its help says it *is* a forget, narrower), `wm.close` (WM_CLOSE to a native window, external), `pane.close`. The narrower kind brings its own version.
2. **The narrower kind's rule forbids it.** Square and rectangle (**recall**): setting a rectangle's width breaks a square. A pamphlet's fixed panels against a document's "add page". A decision (`leaders_only`, dk338) against a post's edit by anyone. This is the database view-update problem (**recall**): reading through a view always works; writing through it works only when the write can be put back. Agora already calls its views lenses, and bidirectional lenses (get and put, with laws; **recall**) are the cleanest frame. A do word carries when the narrower kind can take the write back.
3. **It can't be undone, and its author never thought of this kind.** The window manager moving a game.
4. **Authority** (next section).
5. **Spelling.** `colour` against `color`: a mapping, not a refusal.
6. **Who is looking.** A trail crew's railing is an asset to inspect; a birding group's is a perch.
7. **State.** A game at its menu against a game in a match. Some "kinds" are states: adjectives that come and go.

A rule set that needs no new knob, because it reads what the dictionary already holds (`word_kind`, `undo`):
- **see** and **hear** words carry freely;
- **undoable do** words carry, nearest kind's version first;
- **external do** words, and the 8 that can't be undone, reach a narrower kind only where that kind said yes;
- a kind may **withhold** any word, with a reason the refusal quotes and a way out ("a railing has no door; add gate instead");
- when two outer kinds offer different versions, **ask** (Alex's P2: "ask only when two fit"), and keep the answer on the narrower kind.

### Classifying never adds power

If anyone could declare `secret-note is window`, every grant `only=kind:window` would silently reach secret notes. So a grant names kinds as they stood when it was made, the way stored lines bind their words when saved (a1156). Nesting widens what views show and what words can be tried; it never widens what a module or a grant may do. This sits beside SHAPE's "composing words never adds power". Places and kinds differ here: power flows down groups (a leader reaches inner groups) but never down kinds.

### Aspects mean one thing

Structure can only be trusted if an aspect means the same everywhere. RDF properties work because each has one meaning (**recall**). So aspects get dictionary entries, like words: what the aspect means, what kind it points at (`lane` names a taskboard-lane; `who` names a person or agent), and what it is the same as (`title`, `label` and `name`; `colour` and `color`). `text` means prose people read; a style's CSS is a different aspect. Without this, probes 1 and 2 show what happens: false nestings and ambiguous links. With it, typed aspects are the cheapest graph win there is.

### The graph: roads, shelves and footpaths

- **Roads**: aspects that point at things, typed. Explicit ids today, plus the text values that already name things (probe 2: typing them cuts the isolated things from 81 to 30).
- **Shelves**: kinds. A thing leads to its kinds, its kinds lead to wider kinds, and every kind leads to its other things. Flat kinds already connect almost everything inside one kind; nesting connects across kinds.
- **Footpaths**, suggested and not asserted: ids, @names and names mentioned in text; things changed in one act; one person's burst of acts; later, similarity (an embedding model, on Alex's yes).

Edges nest too, as aspects (RDF's subPropertyOf; **recall**): `reply_to` is a narrower `about`; `made_by`, `for` and `via_actor` are all "who". So one relation, *narrower than*, runs over kinds, aspects and words. `window.close` is already a narrower `forget` by its own help text.

Readings to walk it (names to argue over):
- `kinds <thing>`: what it is, nearest first, and what it has ("a railing, so a wall and a fence; located, wooden");
- `links <thing>`: what it points at and what points at it, by road name;
- `others <thing>`: things on the same shelves, nearest shelf first.

(`near` is taken: `map.near` is nearness for located things. That is itself a narrower kind of "near".)

### Kinds per group

Agora.md: two groups may keep their own page for one park, "where both pages agree on the underlying content … bridge by place, rather than make it a dividing line." Kinds, nestings and withholdings made in a group apply in that group, nearest first, as words do. The trail crew's railing and the birders' railing are one thing. `same as` between two groups' kinds, or two worlds' (kits already carry kind declarations across worlds), is the bridge.

### Move the hidden kinds into the world

- **Video game**: a world kind, `is program`. Membership is `is:game` facts, with Alex's yes deciding. The gate's name and full-screen tests become suggestions with their `why`. The WM's refusal becomes a withholding anyone can read ("wm.move: Rocket League is a game; games are left alone"). The gate's *state* test stays in the module: whether a window is full-screen right now is screen state, and that stays off the world by Alex's 26 Oct rule.
- **Native window classes**: the WM's `why` cascade becomes adjectives (owned dialog, frameless, elevated) with app rules as yeses.
- **Upload kinds**: the upload reader's file, photo, document, table, event and media become narrower kinds of Windows' own types. Don't invent a file ontology; adopt PerceivedType and MIME as outer kinds through an adapter, and say `same as`. Apple's Uniform Type Identifiers (**read**, secondary) split the same space two ways: physical (`public.item` → `public.data`) and functional (`public.content` → `public.image`), with a type conforming to both. That is the railing-and-wood split again.
- **The hyphen rule**: kept as a suggestion source, read as "belongs to" unless a yes says "a kind of".

**Rocket League, worked through (imagined).** An adapter publishes installed programs. Rocket League is a thing: a program, so (on Alex's yes, which the gate already suggests) a game; also a Steam title, which needs the Steam program signed in (a road). The dock request (dk806) and the task (dk811) point at it. The dock's words (pin, launch) reach it as an app. The WM's words are withheld, with the reason shown. `kinds Rocket League` explains all of this, and `links` leads from the task to Steam, where the sign-in problem lives.

**Document and pamphlet, worked through (imagined).** "Document" becomes an outer noun with words people expect everywhere: read, find, comment on, summarize, send to JEFF. The Writing app's documents, uploaded files with pages, and the community's shared documents are narrower kinds. The Writing app's `comment` kind then reaches an uploaded PDF as far as the comment's anchor can be put back: a quote with words around it maps onto a PDF's text; a heading may not. Where it can't be put back, the refusal says so and offers a comment on the whole document. A pamphlet is a narrower document with fixed panels: it withholds "add page" and says "a pamphlet has six panels; make it a booklet to add pages".

## What I am leaning on

| Source | What it gives | How known |
|---|---|---|
| Formal Concept Analysis (Wille, 1982) | Alex's two pictures as one lattice; kinds computable from the world | recall; used in probe 1 |
| OntoClean (Guarino and Welty) | material and role are not parents of identity | read, secondary |
| Windows shell association arrays | verbs merged from type, perceived type and `*`, nearest first | read, secondary (older MSDN) |
| Xbox Game Bar, "Remember this is a game" | guess, then a per-app yes that unlocks verbs | read, secondary (community guides) |
| Apple UTIs | physical and functional hierarchies, conformance to both | read, secondary |
| Hickey, "Maybe Not" (2018) | requirement belongs to the use, not the schema | read, secondary |
| Wikidata P279 studies | people confuse "kind of" with "one of"; taxonomies drift | read, secondary |
| Self, JavaScript prototypes (Ungar and Smith; Lieberman) | kinds as things that things follow | recall |
| Liskov; square and rectangle; view update (Bancilhon and Spyratos); bidirectional lenses (Foster, Pierce et al.) | when a write may pass through a view | recall |
| Go interfaces, Rust traits, entity-component systems | capabilities without inheritance | recall |
| RDF and OWL | global meaning for properties; subPropertyOf; equivalentClass | recall |
| Ranganathan's faceted classification | one item, several independent facets to walk | recall |

## What would change my mind

- **If adjectives and typed aspects give Alex what he wants on their own**, nouns needn't nest at all. Go and Rust chose capabilities without inheritance on purpose. The probes lean this way: structure found adjectives, and my one noun call in the dry run was arguably wrong. Nesting nouns would then be for finding and explaining only. I'd test this with the Rocket League slice: count how many of its needs a noun nesting met that an adjective could not.
- **If promises are not kept up**, for example if a month from now fewer than half the new kinds say what they are, declarations alone fail, and suggestions (and perhaps embeddings) have to carry more.
- **If carried words surprise**, for example if a word that reached a thing only by nesting does the wrong thing more than rarely in use, carrying becomes opt-in for do words too.
- **If almost every kind has one parent**, a tree is enough (the hyphen convention, made honest) and the lattice is overbuilt.
- **If per-group kinds fragment shared views**, for example if two groups' tasks can't share one board, then world kinds should be the default and group kinds the exception.
- **If the cleaned lattice stays noisy** after aspects have meanings, structure should not even suggest; suggestions then come from names and use.

## What not to do yet

Nothing here should be built before Alex answers. Order if he says yes:
1. **Aspects mean one thing**: entries for the 20 or so most-used aspects, with what they point at. That's world data, cheap, and the precondition for everything else.
2. **Readings only**: `kinds <thing>`, `links <thing>` and `others <thing>`, over typed aspects and declared `is:`, in a hidden sandbox. Nothing acts differently yet.
3. **The Rocket League slice**: programs published by an adapter, game as a world kind with the gate reading it, the dock and the WM honouring withholdings. A real case that stresses the whole idea, per [[realistic-system-proofs]].
4. Only then, words carrying down the ladder in the kernel.

## Source and friction

No source was edited. Words found missing, for the Rough spots note when this is built:
- **a kind as a test** (`predicates.py` lacks list membership, comparisons and `is(kind)`);
- **`is:<kind>`** as an aspect with history;
- **aspect entries** (meaning, points at, same as);
- **a kind ladder for words**, twin to the group ladder;
- **withhold** on a kind;
- **suggestions as one-click yeses**, not things (so they don't become clutter).

Follow-up outside this lab: the Writing app's `rows document` will pick up uploaded files when it's installed (above).
