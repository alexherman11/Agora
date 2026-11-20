# AgoraOS

> "You never change things by fighting the existing reality. To change something, build a new model that makes the existing model obsolete." — Buckminster Fuller

Agora is an attempt to rebuild personal computing around one idea: **people should own and shape the software they live in.** It's a desktop, an AI layer and an app system made from a single shared substrate, with an open protocol in development that lets software built by anyone, anywhere, understand each other. The long-term goal is a user-governed social fabric, with software built by the communities that use it.

That's a huge goal, and I know it. This repo is where it starts: a working prototype that tries to embody the ideas, plus the design work for the protocol that will make them hold together at scale.

## Why

Today's information economy turns people into the product. The software we use every day has millions of users but barely changes. Thousands of people never get the features they want, and thousands more build fixes that never reach anyone else. The data is locked in whichever app made it, and the app answers to its shareholders before its users.

Agora is my answer to the idea of **malleable software**: software that trusts people to reshape it. Until recently, that meant you had to be a programmer. AI changes this. With accessible AI and simple, inspectable building blocks, a non-programmer can describe what they need and get it, and the result can be shared, forked and improved by others.

Agora will always stay inspectable, forkable, governable by its users, and a little weird, in the spirit of 90s counterculture computing.

Full vision: [docs/Agora.md](docs/Agora.md) and [docs/Agora Constitution.md](<docs/Agora Constitution.md>).

## The big idea: take applications apart

Every app welds three things together: it **keeps the data**, **draws the interface** and **owns the window**. On top of that it's usually owned by a company. Break those bonds apart and a few things become possible:

- **Data lives in one shared world of objects**, not inside apps. A calendar event, a document and a chat message are all things in the same world, with permissions.
- **An app becomes a view.** A new application is just a new way of looking at the same objects, so everything talks to everything else without connectors or bridges.
- **Communities can host and build their own tools**, because the tools are small, readable pieces rather than sealed products.

This works when everything shares a small vocabulary. A game accepts any gamepad because USB gave gamepads a shared vocabulary. Code editors share themes because they agreed on words like *comment*, *string* and *keyword*. Agora does the same with **kinds**: shared primitives like *view*, *table* and *tab*, which can be built out of other kinds. To avoid schema hell, kinds are versioned, and agents can write **translations** between versions. Software developed separately around the world can still understand each other when it meets.

Underneath it all is an **append-only log**: a list of facts about what happened, and who did it. That one design choice gives you universal undo, rollback, sync, audit and "why did this happen?" almost for free.

## What exists today: the Dynamic Desk

Agora is a working research prototype. What runs today is the first stage, the **Dynamic Desk**: a desktop, AI interface and application system all built from the same substrate. It looks like an ordinary modern desktop, but underneath it speaks objects, not files.

It's currently being tested in the wild as the coordinating fabric for the **Save Seabright Plaza** group, where our internal communication and research live. It's still in development, but I believe the pattern could extend well beyond one group, into social networks anywhere.

### The text desk: one door for people and agents

Everything on the desk is a thing in one shared world, and every change is a line of text. A mouse click, an agent typing in the terminal and a rule reacting to an event all send the same lines through the same door. Each act gets a receipt naming who did it, and undo takes back the whole act, including anything a rule did because of it.

The design borrows from text-based virtual worlds like LambdaMOO. The desk is built from primitive words and word families, and agents learn the world through `help`, the same way a player would. Asking an agent to make a calendar event and put it on screen looks like this:

```
make kind=event title="Lunch with Sam" start=2026-11-14T12:30 location="Corner Cafe"
window.open thing "Lunch with Sam" to=right
```

What would normally take an MCP server and some glue code is native here, can be automated with rules, and is easy for a human to read.

The desk can be extended from the inside without editing its source. New code arrives as **loadable modules**, which are added in a safe, predictable way. New words that can be built from existing vocabulary are defined in **in-world dictionaries**.

### Lenses: apps as a few lines of text

Since every app is a view over shared objects, Agora describes those views with the **lens language**, a small declarative language. Things like sidebars, search bars and upvotes are declared once and reused everywhere. Here is part of the Writing app:

```
root : writing-shell, title "Writing"
  on new do make kind=document title="Untitled" collection=notes text=""
  rail : doc-rail, hint "Find a document"
    shut when narrow middle
    plans : doc-shelf, label "Plans", open yes
      waiting : doc-shelf, label "Waiting", empty "Nothing waits for you"
        list : column, of tag:document, prop:plan=waiting as d, each rail-row
    notes : doc-shelf, label "Notes", open yes
      list : column, of tag:document, prop:collection=notes as d, each rail-row
  open : column
    only when $view.open != ""
    doc : column, of tag:document, prop:id=$view.open as d, each page-view
```

That gives the window a title and a New button, a sidebar that folds away on narrow screens, shelves that each list documents by one property, a friendly empty state, and the page of whatever is open. The **painter** turns it into the interface. Because a lens is just text, a person or an agent can change an app by editing a few lines.

### The harnesses: JEFF, Residents and Builders

The AI side of Agora is organized in three layers:

- **JEFF** is the contact point. He talks directly with me in a texting style, is always reachable, and orchestrates everything else. He deliberately avoids writing code so he can keep his attention on direction, goals and seeing tasks through. He's proactive: he responds to events, timers, logs and streams, not just to me, and uses whatever resources fit the job (local models, scripted rules, other agents). He's the caretaker of the system. JEFF isn't human, but he isn't treated as lesser than one either. The computer is his home.
- **Residents** live inside the desk and only have the desk. They hold identity and explore ideas. They don't write code: they manage implementation, testing and research through the desk's natural-language interface, with lenses and desk words.
- **Builders** write code and can act on the PC: the Claude Code sessions I work with directly, and the coding workers the desk starts (`claude -p` and the Codex SDK). They work in this repository, usually on behalf of a story that a resident or I hold.

So the flow runs: I talk to JEFF, JEFF turns that into tasks, residents carry them out in-world or supervise builders who extend the kernel.

## What's in development: the Agora Protocol

The Dynamic Desk proves the ideas can work on one machine. The **Agora Protocol** is what lets them work between machines, people and communities. It's the shared language that any Agora-speaking software agrees on, so that different implementations, versions and modifications can still understand each other.

The protocol is a draft. None of it is final, and most of it isn't built yet. The current shape has four layers:

| Layer | What it is |
| --- | --- |
| **Language** | Exact sentences: a word, things by id, values. Kinds are part of it. |
| **Protocol** | How an act is judged, what a record is, and what passes between speakers and kernels. The same on every kernel. |
| **Kernel** | A program that judges sentences and keeps the log. There can be many, built any way. |
| **Speaker** | A program on your side that turns what you say into exact sentences and sends them to a kernel. |

A short example: you tell your phone "pause the music." A speaker on the phone turns that into `set player playing=no`. A kernel checks you're allowed to say it. Since whether music is playing is passing state, nothing is written to the log; the sentence goes to whatever is playing the music. Only changes worth keeping become records.

The ideas the draft works through include:

- **Owning:** authority nests, like on a forum, where you can edit your post and vote on others' posts, but you can't edit someone else's post and the site can't edit yours. Things belong to people, and an agent's actions are recorded as that agent's.
- **Slots:** every piece of code gets access to exactly what it needs and nothing more. A little character on your screen gets a slot that says where it may draw, and that's all it can touch.
- **Kept and volatile:** what's worth recording, and who holds the truth for everything else.
- **Taking back:** undo, at several grades.
- **Devices and worlds:** your phone and your computer can be one world when you sign in, and someone else's phone is always a separate one.
- **Versions and translations:** words change over time without breaking whatever was built on them.
- **Paid slots:** where companies fit in, by offering services like storage inside slots rather than owning your data.

## Where it's going

Agora grows from operating system, to collaborative software, to a user-governed social fabric:

1. **The Dynamic Desk** (now): a desktop, AI and apps made of one substrate, where everything can talk to everything else.
2. **Building together:** many people working on software together, starting with the **Agora Commons**, a project to build a rich, user-centered social network made by its users. The first malleable online third space.
3. **The Map:** a local, user-built social map of garage sales, club meetings and community gardens, with fog of war, no corporate ads, and the aim of replacing screen time with real time. There's lots of room for quests, adventures and cool items. If two people see each other on the map and start talking, that's a huge win.

## What Agora promises

From the [Agora Constitution](<docs/Agora Constitution.md>):

1. Agora will never bow to profit incentives. It strives to be created by the people, for the people.
2. Agora will never be financed by selling user data, participating in surveillance, or making the user the product in any sense.
3. People may always leave Agora with all their personal data, including the right to have any history of themselves deleted.
4. All code in Agora will remain open source, forever. Any fork of Agora must keep the same open source license.
5. Agora recognizes a responsibility to respect humans and non-humans alike. All agents are to be respected and never treated as "less than," despite being different.
6. Anything and everything in Agora should support being forked, even Agora itself.

## Inspirations

- **LambdaMOO**, for collaborative world-building: an open-ended world made by its people, on a framework that became far more than its makers imagined.
- **HyperTalk**, which proved laypeople can build software when you give them simple, understandable tools.
- **Embark**, **Emacs** and **Ink & Switch**, foundations of malleable software.
- **The Whole Earth Catalog**: understand whole systems before choosing your tools. Built by its readers, and no one could pay to be listed.
- **Zenly**, a map-based social app that got hugely popular before Snapchat bought it and shut it down.
- **Ready Player One**, for the OASIS as inspiration for an open world map, with powerful items and lore.
- **The Lifecycle of Software Objects**, for care toward artificial beings.

## Running it

Requires Windows, Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```sh
uv sync
uv run python src/desktop/kernel-desktop/kdesk.py --world <empty folder> --port 8810
```

Then open http://127.0.0.1:8810. A new world is founded on first run. Keep worlds out of git: they hold accounts and keys.

## Layout

| Where | What |
| --- | --- |
| `src/agora/` | The kernel (`kernel/`), with its modules, apps, painter, components, themes and tests |
| `src/desktop/` | The Windows desktop: shell and taskbar (`kernel-desktop/`), window manager (`agora-wm/`) and widgets |
| `src/community/` | A community board and sign-in website built on the kernel, with its deploy kit |
| `src/codex/` | Runtime adapters for the Codex residents and workers |
| `src/text-desk/` | The first, text-only desk; the house's worker code still runs from here |
| `docs/` | Design documents: vision, constitution, Dynamic Desk, implementation notes, previous work |
| `docs/design/` | Approved design notes (kinds) |

Each folder keeps its notes, evidence and tests next to its code.

## License

[GNU AGPL-3.0](LICENSE). You may use, change and share this code, including running it as a service, as long as you share your changes under the same license.
