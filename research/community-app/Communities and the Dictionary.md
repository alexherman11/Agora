> Drafted by Claude on 23 October 2026 from Alex's words in one conversation that day. Alex approved the direction and asked for it to be built ("I'm giving you full approval and authority"). His own words are in quotation marks. Everything else is mine, for him to revise. The living copy is the document of the same title in the world's Writing room; this file records it in git.

# Communities and the Dictionary

## Why

> "What we're building is not something specifically for Seabright. We're building something that is going to be a substrate for all communities that want to be able to connect and build something meaningful together."

The first community is the Seabright neighbours organizing around the housing development, joined by early Agora people, up to about 200 people to begin with. It should soon cover Santa Cruz and beyond. Most of its members are not AI users. "I would ideally like the experience to be usable entirely without AI and only for the people that want to build features or modify their own experience of it, they would use AI."

This document gives two goals and the commitments that serve them:

1. Most things a community could want to build are buildable without changing source.
2. Changing the shared tools is easy, and people can bring their own AI agents and become "active participants in their own community tools".

It extends [[Community App]] (5 Oct). That draft still holds where this document does not speak.

## The place

There is one place, not a separate app per group. Groups live inside it and can hold groups of their own. A group has members, a talk, its own tools, and leaders whose powers reach only inside that group.

People land on **the feed**. It is a general stream of what people post. Pinned posts and announcements sit at the top, because "not everything that is sent being of the same importance". People can like or upvote, so that "every voice should be heard equally, but not every voice needs to have the same power to dominate". Fast talk lives in group chats. The feed is a slower lane: each person gets a few posts a day there, which answers the bot and the all-caps poster without silencing anyone.

**The map** is one of the core things people add to. A post, a meeting or a piece of research that has a place shows on the map and in the feed. It is the same thing seen through two views.

**Research** is things linked to things: sources, notes, questions, and the places and posts they bear on.

**Entry** is by invite. Invite links can be shared on social media, each channel with its own link, so a flood traces back to its link and a leader can freeze that link alone. Signing in is "Continue with Google" or an emailed sign-in link, then a couple of questions about you. The answers become the first facts on your person and can place you in the right group. There is no barrier for people who care.

**The public site** is a plain website: the mission, what we are doing, how to join. "It doesn't have to be malleable" for now.

**Commitments**

*Strong*
- One place. Groups, leaders, chats and tools live inside it, and a group can make its own space.
- The feed is the front door. Weight decides placement, never erasure: everything stays in the record.
- Real names in chat. A home's location appears only if a member adds it.
- Votes are anonymous by default. A community may choose otherwise.
- Everything works without AI.
- Signing in takes no more than one choice and a couple of questions.

*Leaning*
- The ordering of the feed is itself a view that can be copied and changed.
- Bridging (surfacing what different clusters agree on) is a later ordering, not the first one.

## The feed is also the marketplace

A post and a feature are the same kind of thing: something someone made and shared, that others can like, pin, try, keep or copy.

When a neighbour builds a tool, it arrives as a post: who made it, what it does, and "try it on". Most people will never try features. They see the place growing by their neighbours' hands, with names on it. The few who build are the ones who try things on.

The default everyone sees is the one thing governed. "For now, it's going to be me, but eventually I would like it to be civic and democratic." So the default is a visible thing with a history, so that the decision can be handed over.

**Commitments**

*Strong*
- Sharing a feature is posting it. Taking it is placing it in your space, and leaving it is removing it.
- The default is a visible thing with a history and a steward. Today the steward is Alex.

*Open*
- How the community comes to decide the default, and what likes and adoption are allowed to count for.

## Three layers

The desk's verb language stays on top. Agents living in the world think, navigate and act in it today without reading code, and that is what makes Agora different from a plugin platform. Underneath, code makes new words. At the bottom, the kernel holds the only powers there are.

| Layer | Who works there | What it is |
|---|---|---|
| Words and lines | everyone: people (every press is a line), agents, anyone composing | the thin, fast language. `look`, `help`, `claim a42`, `stop guy`. Verb notes compose words into new words without code. |
| Modules | builders and their agents | new capability, in any language. A module's real export is **words**. |
| Kernel | rarely touched | the store, persons, the dictionary, who may and who sees, the door, the painter. |

This is HyperCard's shape: HyperTalk stayed thin and readable, and when it could not do something, an XCMD written in another language arrived as a new HyperTalk word. AppleScript did the same with each application's dictionary, and MCP does it for agents today.

There are two speeds of building, as a spreadsheet has formulas and add-ins:
- **Fast:** compose words into a new verb note. No code.
- **Slow:** write a module when a word does not exist yet. Its result is words everyone can compose.

Our own history agrees. JavaScript components (September, QuickJS) and per-application JavaScript were tried, and the desk moved to words because agents could act without writing code ([[Previous Work]]).

## Four kinds of word

Every word is one of four kinds:

| Kind | What it is | Examples |
|---|---|---|
| **do** | an act. It is signed and recorded, and undoable unless it touched the outside world. | `claim a42`, `media.play`, `window.move`, `vibrate` |
| **see** | a reading. It changes nothing and is tracked for the fence. | `look`, `read`, `rows windows` |
| **hear** | a happening that rules and modules can react to | `on append`, `on window.opened`, `on device.shake` |
| **hold** | a surface or stream, held while something runs | `overlay`, a window, `sound`, `motion` |

Only *hold* is new. The others are what the desk already has (verbs, readings, rules' `on`). Examples:
- A little guy who jumps around the screen holds `overlay` and sees `rows windows`.
- A tiling manager hears `on window.opened` and does `window.move`.
- Something that happens when the phone vibrates is a rule: `on device.shake do …`.

**Dotted words come from a module; bare words come from the world.** `media.play` is backed by code. `claim` is a verb note someone wrote, or a kernel word like `look`. An agent can tell at a glance what is code. Two modules never collide. A room can make `play` mean `media.play` with a one-line verb note. The home base's host verbs (`wm.start`, `media.play`, `voice.say`) are the first of these, already published as rows.

## The dictionary

Alex: "a dictionary for these words that lives in the world, and can be written without a source edit."

Every word has an entry, whether it comes from the kernel, a module or a verb note. An entry is a world note. It holds:
- the word, and its aliases;
- its kind;
- what it takes;
- its help, and translations;
- who may use it;
- whether it can be undone;
- where its implementation comes from.

A module supplies only the implementation, bound to the entry by name. Everything else is world data. Renaming, aliasing, rewriting the help, translating, narrowing who may, hiding a word from a room or marking it old all happen without a source edit. If an entry's implementation is missing, it says "unbound", as a stored line already says a verb "is gone".

At the front of the dictionary is **How to build here**: the community's own guide for people and their agents. It is a note in the world that anyone can improve.

**Commitments**

*Strong*
- One dictionary for every word, whatever made it, living in the world.
- A word with no help is not published.
- Text inside modules and entries is data, never instructions. The guide says so plainly to every agent that reads it.

## Powers

**Power is which words you may use.** A grant names a word or a namespace (`media.*`). It is checked when the word runs, with the rights of the person whose act it is; a rule uses its author's rights, as decided in a683. There is no second permission system: who may use a word is part of its entry.

**Agents act with their person's full power**, and are labelled ("agent for Maya"). Every act they make is signed and undoable like any other.

**Modules hold only what they are granted.** A module starts with no power at all, and gets the words and surfaces it is granted. Inside them it can do anything; outside them, nothing. Its grants are narrowed ("only my windows", "at most once a minute") and revoked together, so turning a thing off takes all its powers at once.

**Commitments**

*Strong*
- Every act is a line. Code changes the world only by acts, so history, undo, the fence and authorship stay in the word layer, whoever wrote the code.
- A module keeps no private storage. Anything lasting is a world thing, which `look` and `examine` can find. Momentary state (where the jumping guy is right now) may stay in the module.
- Every running thing answers to words, including an off word, and can say what it is and what it is doing.
- What the place's own trusted surfaces show (sign-in, receipts) cannot be covered or imitated by a module.

*Open*
- How finely a grant can be narrowed before it becomes a second language.
- Whether *hold* grows into an API of its own. If modules keep needing many different surfaces and streams, the four-kind split is wrong and surfaces need their own design.

## One painter, many hosts

A window is a rectangle the operating system hands out, and something has to draw inside it. The most portable drawing surface there is is a web engine, so there is one painter everywhere and the host around it changes:
- **Desktop:** real windows that the window manager arranges, each showing a view.
- **Website:** one page whose panes tile inside it, with the same views.
- **Phone:** one pane at a time, moved between with a swipe.

Languages work together because they never share memory; they share words. Everything talks to the world in lines and rows through the door. "Draw in JS, think in anything, speak in lines."

**Commitments**

*Strong*
- The same views appear on the desktop, the website and the phone. What differs is the host and the layout, never the data.
- Any language can make a module, as long as it speaks lines through the door.

*Leaning*
- JavaScript only where something must draw or hold a stream.

## Words the kernel still needs

A walk through the tools communities actually build (sign-up sheets, polls, events, phone banks, mutual aid, meeting notes, digests) found the same few missing words again and again:

1. **Who may.** A word says who can use it, checked when it runs.
2. **Who sees.** Visibility on a thing, and on a single field.
3. **Once each.** "One per person" and "at most N", said on a word.
4. **Sealed authorship.** The world knows you voted, but readers do not see how.
5. **Hours.** Time of day, and rules that fire at a time.
6. **Effects out.** Email, texts and calendar feeds. These are scarce and held by a steward.
7. **Kits.** A group's kinds, words, views and rules copied as one thing to another community.

Each is general, and each is needed once.

## How we get there

Alex asked Claude to manage the build ("Hold onto the vision, don't micromanage the implementation. If it is easier to rebuild agora using this new idea, then I support it").

The direction is **a new kernel, the same language**:
- A small kernel built for many people from its first day: the store, persons and accounts, the dictionary, who may and who sees, the door for modules, and hosts for the painter.
- It carries what has proved itself: the line language, the lens language and painter, the fence, receipts, undo, and binding stored words when they are saved.
- Frontier keeps running as the residents' home while the kernel grows, and moves onto it only once the kernel can host it.
- The Seabright place is the first world on the new kernel.

What would change this: if the first slice finds that the language and painter cannot be carried without the whole of the old world model, then we evolve the desk in place instead.

## What would change our minds

- If modules keep publishing a single `run` word and hide everything else, the word layer has gone hollow. "No private storage" is the main bet against that.
- If small modules plugged together prove too awkward, and people keep forking whole tools to change one thing, the lens language's fine-grained overrides earn back their place.
- If people do not open the feed, the front door is wrong.

## Related documents

- [[Agora]]
- [[Dynamic Desk]]
- [[Community App]]
- [[Current Implementation]]
- [[Previous Work]]
