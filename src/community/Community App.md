> DRAFT, by Claude, 5 October 2026, from Alex's dictation of 2 October and the conversation since. Alex's own words are in quotation marks. Everything else is a proposal for workshopping, not a decision. When this settles it may move beside [[Dynamic Desk]]; until then it lives here.

> "The key principles that I want are that basically anything can be built, and I want that to be primary."

## Overview

This document describes the first public Agora: an app for a neighborhood organizing around a large housing development in Seabright, Santa Cruz, built on the same substrate as the [[Dynamic Desk]]. It is written in that document's form and uses its labels:

- **Strong**: we uphold this. It is intuitive, or has arisen as a design requirement from our research.
- **Leaning**: we think it might be something we should uphold, or something we know we want but don't know is possible.
- **Open**: actively trying to figure it out.

Why here and not somewhere easier: the community is fighting a process that is fixed and not theirs to touch. A tool that reshapes itself under their hands is a daily, small demonstration that the thing you use is yours to change. That is not a side effect of Agora; it may be its best first argument. And it gives the desk what it has lacked, people using it for something they care about.

What this app is, in Alex's words: "a map where people can post things and events can be visible on the map", "a large group chat within the app that is also malleable and stylable", "some sort of more structured thing where people are able to upvote things, so things that are relevant stay up at top", "a shared space for research and collaboration", "they have privacy, they have whatever people invent", for "between 200 and 1,000 people", where "ideally I want as much of it to be done without editing the source code as possible". It starts with "about 20-30 tech savvy people in the movement" and should grow quickly.

It need not use everything the desk has built. "We can take pieces that we like, and we don't have to use everything."

**Commitments:**
*Strong*
- Anything can be built in it, by the people in it, and that comes before any particular feature.
- It is "not better in each aspect", but the whole is more useful than the tools it replaces, and it becomes more so with time.
- Whatever is useful is preserved; whatever is not goes away, and nothing is lost on the way out.
- It works with no AI at all. Agents are a helper, never a requirement, and no member needs an AI subscription.
*Leaning*
- The first version is the smallest thing thirty organizers use every day, not the whole neighborhood's app.
*Open*
- What they do on the first day that they cannot do in their group text today.

## One shared world, many personal apps

There is one world: the community's data, pins, posts, chat, meetings, research. There is no single app over it. Each person's app is their own selection of definitions, which lenses, kinds, verbs, rules and styles they have taken up. A feature is a set of definitions by an author. "Say Stacey makes a feature for her chat, and it would be useful for other people... eventually everyone has that feature. Or maybe some people don't want that feature that got made, and they're able to choose not to have it."

This is the Dynamic Desk's substrate pushed from one person to many: definitions are things in the world, so adopting, declining and sharing a feature are acts on things, not changes to code.

**Commitments:**
*Strong*
- Data is one truth. What each person sees and can do is their own, and taking up a definition is a choice.
- Adoption is placement. Taking someone's feature is placing their thing in your space; leaving it is removing it; changing it is copying it first. Nothing is installed.
- Data is additive and open; kinds and definitions describe and never enforce. A new kind or aspect never breaks anyone's view.
- Anyone may make a thing of a new kind without permission, and sharing it is one act.
- Everyone may fork. The community's whole world can be taken by anyone who leaves, and its data is theirs to export whole.
*Leaning*
- The default app a newcomer gets is decided by a steward at first ("at the beginning me") and by the community later ("features upvoted... we can vote in features for the canonical app"). The mechanism is open; the requirement now is that the default set is a visible thing with a history, so the decision can be handed over.
- A feature carries its dependencies by name. A selected lens that reaches for a helper names it; nothing is silently omitted or swept in whole.
*Open*
- How the community's vote on a feature relates to its adoption count, and what either is allowed to do on its own.
- Whether a feature can be adopted at a pinned version, or always follows its author.

## Places

The unit people make on purpose is a place, not a feature. A room is a few things that live there, a few verbs that work there, a view of them, and a chat. Making the flyer campaign is making a room: routes live here, you can claim one and mark it done, here is who is on it. Rooms are copied, not configured. The app is a building the community adds rooms to, and a room is the thing you invite someone into. The desk already has rooms with verbs that live in them; none has yet been made by someone who was not fluent in the grammar.

**Commitments:**
*Strong*
- Entering a place says what lives there and what you can do there.
- A place can be made, copied and shared by its members, and it carries its own verbs, view and talk.
*Leaning*
- The map, the big chat, the announcements and the research space are rooms like any other, not fixed parts of the app.
*Open*
- What the first rooms are, and whether a room's chat is the room or merely in it.

## People

A person is a thing with one id for a life, and their names are labels on it. Nobody enters without a path back to a member: by "direct invite from other members", or by "privileged QR codes" that a leader makes "to get people at a community event on board quickly". Either is a thing with a maker, a number of uses, an expiry, and a record of who came through it, so the web of trust is visible data rather than policy, and a flood of accounts traces to one inviter.

Leaders have "special permissioned roles to pin messages and things. Not like super powerful but just slightly." A role is a thing: a holder, a short list of powers, who granted it and when. A verb declares the power it needs; an aspect declares the power that may write it. Grants and removals are ordinary events, visible and undoable, and a leader's acts are as undoable as anyone's. This is the only permission the app has, and it should stay small; growing the list of powers is a community decision.

**Commitments:**
*Strong*
- One person, one account, names as labels, pseudonyms allowed; the inviter knows who you are, the world need not.
- Every act has an author, and every author is a person the world can name.
- Roles are visible things with a history. Nobody's power is hidden in code.
*Leaning*
- Default open editing, wiki style: anyone edits, everything is attributed and undoable, abuse is reverted socially. Locks are not built; roles cover what locks would have.
- The first powers are pin, announce and make codes.
*Open*
- Whether a role can be delegated, and whether roles expire.
- What a member's privacy is against the host.

## Things, links and the graph

Everything is a thing with aspects: a pin, a post, a chat line, a meeting, a route, a wish, a definition, a person, a place. A pin is a thing with a location aspect; attaching things to a pin is placing them on it; comments are lines in a thing's thread; an upvote is a verb writing an aspect; the announcements area is a view sorted by that aspect.

Everything in Agora is a connected graph, and the app needs many ways for connections to form. The desk has typed links; what it lacks is gestures that make them. A wish links to the thing it was said on, an answer to the wish, a verb to the definition that made it, a pin to the meeting it is about, a search hit to the search. An @-mention of a thing in text makes a link without asking. Press one thing and tap another, and the only question is what the relation is. Two things that keep appearing together can be offered as a link.

Privacy is a property of the store, not of a view. Each thing carries a visibility: everyone in the community, the members of some place, or one person; every read passes one place that applies it for the reader.

**Commitments:**
*Strong*
- One thing can appear in many places, and it is the same thing in all of them.
- A thing's identity is minted once, never reused, and survives renames, moves and forks.
- Links are typed, two-way and first class; anything can link to anything.
- A view adopted from someone else shows you only what your own visibility allows.
*Leaning*
- Mentioning a thing links to it; linking should be automatic wherever a thing is named.
- The graph is the app's memory, and search is how you walk it: things, lines, definitions, wishes, people and places alike, with a result being a thing you can link to and a saved search being a view.
*Open*
- Which relations the community reaches for first, and whether link kinds should be made by people as kinds are.
- How a document people research in together keeps its comments in place as it changes.

## Reaching

The raw material for the app's growth is not what people write. It is what they do, what they repeat, and what they bump into. A reach has a person, a thing, a place, a time and what was said or done, and the world keeps all five. Ordinary software keeps only what succeeded; here the misses are where the next version is written, in place, by the people who missed, with their names on them.

Kinds of reach the world should notice:
- **The line at a thing.** A long press shows what a thing can do, and under the options a free box "where you can say what you want to happen to that item". If something answers, it runs and the receipt shows the line it ran. If nothing answers, the words are kept on that thing as a wish, with who and when, and the next person who reaches there sees it and can join with a press. This is the residents' own line, given to everyone, without the grammar.
- **Worn paths.** "If people reliably move through the same menus and hit the same sequences of buttons to access a tool or feature, maybe that tool or feature can be moved up to the top where it could be accessed in one tap." A chain reliably repeated is a verb that does not know it is one yet; naming it and placing it where the person stands is the whole act.
- **The empty place.** A view that shows nothing, a room with no things: what a person does next, there, is a reach.
- **Two things at once.** Pointing at two things is reaching for a relation.
- **Search that finds nothing.** The purest miss, and every app throws it away.
- **Undo.** An undo says "not that". Undos clustering on one verb mean the verb is wrong, not the people.
- **Checking again and again.** Someone who opens the same thing five times a day is reaching for being told.
- **Refusal.** When the world refuses an act, the refusal carries the next act in it.

Wishes pile up on kinds of things, not in a tracker elsewhere. After a month the pins carry, in their own margins, the record of what pins wanted to be able to do. That is the specification of the app, and answering it is the builders' job. When a wish is answered, the people who reached are told, where they reached.

**Commitments:**
*Strong*
- Every reach is kept where it happened, with its person, and is joinable by others.
- Every answered reach tells the people who made it.
- The free box is honest about what it is: a line at this thing, some of which are answered now and the rest kept and read. It is not a chat with an agent.
- A thing that moved because of a worn path says it moved and goes back in one press.
*Leaning*
- Every action shows the line it ran, and a run of actions can be named and becomes a verb.
- The communal paths, worn by many, are the evidence the default app changes on.
*Open*
- How a reach that half-matches a verb is offered back, and how much the world may guess.
- When noticing becomes nagging.

## Agents

Agents in this world are gardeners of the place, not assistants to each person. A few residents, known by name, read the day's acts in their own turns the way they read the desk's Board now: they keep the map tidy, tell a newcomer what happened this week, notice when three people keep doing the same thing by hand and offer it back as a rule with that person's name on it, and answer wishes in batches. Five hundred people's acts are a long chat, not a thousand conversations; Alex's subscriptions pay for gardening, which is batched, never for a conversation per member.

A very small model may sit under the free box and try to carry out an ask at once: choosing among the verbs that apply to the pressed thing, filling their blanks, assembling one line, and running it. It may chain lines, one step at a time against the world's receipts, within a short budget, on a fork of the world so the person sees what it would do before it does. "If it can't be done, then it gets queued for work by a larger model." Every answered ask becomes an example for the small one.

**Commitments:**
*Strong*
- Nothing in the app waits on a model. A pin goes on the map without one.
- An agent's act is attributed to the agent, and a rule it offered runs as the person who accepted it.
- Agents are residents: they have a name, a place, and a record, and members can address them.
*Leaning*
- A small model never writes syntax; it chooses among what the thing can do, and the desk validates.
- A model's chain runs on a fork and is shown before it is applied; a refused step turns the ask into a wish.
*Open*
- Whether the residents' own transcripts may be used to teach the small model, which is theirs to be asked.
- How the gardeners read five hundred strangers, when the evidence so far is for six colleagues.

## The record

Every change is an act by a person, recorded with what it changed, and undoable. Nothing changes silently for anyone. The truth is a log; the state is derived from it. Undo and replay restore what was recorded; they never re-send a message or repeat an effect outside the world.

The format of the record outlives the code that wrote it. Every later version reads every earlier record.

**Commitments:**
*Strong*
- Every act has an author, a time, and an undo.
- The record is plain, versioned, and readable by any later code.
- A fork keeps every identity, and bringing a thing between worlds is a difference by identity, never a replay of acts.
- What a person has seen is theirs, kept beside the world, never in it.
*Leaning*
- Search over history is an index beside the record, never the record.
*Open*
- Offline use on phones, and what merging means when two people edited the same aspect apart.

## Appearance

It is "both an app and a website, with the same world underneath both from two different types of views." One world, one stream of records, and every client, phone or browser, paints the scenes it is given and sends gestures back as lines with intent ids. No client holds data of its own. What differs between app and website is lenses and styles, not data.

The desk's own rule is one scene, two printers: the same tree prints as text for agents and as pixels for people. A native app is a third printer of the same scene. Declarative native toolkits are already scene-tree renderers, so the mapping is near, and gestures come back as acts. The hard part is layout: the scene should carry intent, a column, a row, a grid, a flow, a map, and let each printer lay out for its screen.

The open ambition is visual richness that does not grow the core. A lens says what is shown: a map with pins placed by a location aspect and a camera. It cannot draw a miniature earth. Drawing is a printer's job, and a printer for a kind of node may be as rich as its author likes, in JavaScript or Kotlin or Swift, as long as three things hold: the scene is its only input, every act goes back as a line, and the text printer can say what is there. A style may pick the printer for a kind, so one style paints the map flat and another paints it as a toy earth. Printers are things with authors, adopted like definitions.

**Commitments:**
*Strong*
- Every view can be restyled, rearranged, copied or replaced like every other thing.
- Every node kind has a text printing. If an agent cannot read it, it does not exist.
- A new kind of thing to show needs a printer at the edge, never code in the core.
*Leaning*
- Phone first. The map is a view like any other.
- Native printers change slowly, with app releases; web printers change daily. New visuals land on the web first, and the native app carries a web printer for whatever it has no native one for.
- Transitions are diffs: because parts keep their keys, a thing moving between places can be seen to move.
*Open*
- Where a printer's code lives, and who may adopt a printer that runs code on their phone.
- What the map looks like, and whether a miniature earth is a style or a kind.
- Depth, time and the graph itself as visible things, not only lists.

## Code

Source edits are rare and never visible. "I'm willing to accept some source code edits as long as it doesn't take down the app for anyone, and those source code edits are able to go into effect relatively easily, and on an individual scale." The desk's door already makes a landing invisible; a route per person makes a code version something one person can step into and back out of. Most of what would have been code is definitions in the world.

**Commitments:**
*Strong*
- A code change never takes the place down for anyone.
- A code change reaches each person on their own schedule, and there is always a way back.
*Leaning*
- The kernel shrinks over time: the store, the fence, the record, the compiler and the printers, and little else.
*Open*
- Which parts of the desk come to the first version: the lens language yes, the command line for leaders and agents, the house as gardeners, the pickle no. What else is dropped.

## Hosting and growth

"For now runs on my PC or some of my rented stuff. I can host for now, but maybe neighbours help in the future." A world is a directory of plain files; copying it is moving it.

**Commitments:**
*Strong*
- The community's data lives in plain files it can copy whole.
*Leaning*
- Hosting can pass from one person to another without the world noticing.
*Open*
- Backups, uptime and who is responsible when the host sleeps.
- What a neighbor hosting a fork of the place means for the people in both.

## Biggest challenges

Whether a neighbor can read a definition at all. The lens language was written for agents and is terse; if the middle of the ladder from using to writing is unreachable without the grammar, it is forms all the way down and the text stays behind glass.

Who can change what, lived before it is written. Every open question in [[Agora]] about the canonical version and forking arrives here on day one, with real stakes.

Scale as physics: a real server, a phone-first page, and a store that is not one file saved whole.

Getting out of the way. The measure is that on a Tuesday a neighbor finds the meeting time and the route she claimed and does not think about the tool at all, until the day she needs it to be different and finds that it can be.

## Related documents

- [[Agora]]
- [[Dynamic Desk]]
- [[Current Implementation]]
- [[Agora Constitution]]
