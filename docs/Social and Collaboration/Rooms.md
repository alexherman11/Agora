# Rooms — The Multiplayer Layer Agora Was Secretly Named For

First, an observation: you've just independently resolved the biggest tension in your own spec. "Agora" means _the gathering place_ — the plural, public square — and yet everything in the design so far describes a private home for one human and one agent. I flagged that mismatch earlier and guessed the social layer was the real long game. What you and your girlfriend sketched on the couch _is that layer_. The room is the agora. So let me take it seriously and build it up slowly, because I think it's not a feature — it's the second half of the product.

---

## 1. Why your computer can't do this today

Think about what "being on the computer with someone" currently means. You have exactly three options, and they're all bad in revealing ways:

**Screen sharing.** You beam your _pixels_ at someone. They can look but not touch; there's one cursor that matters and it's yours; the moment the call ends, the shared thing evaporates. It's not a shared space — it's holding your monitor up to a window.

**The shared doc.** Google Docs was a genuine miracle in 2006: two cursors, one document, no emailing `essay_FINAL_v3.docx` back and forth. But notice the _boundary_ of the miracle: it stops at the edge of the document. The doc is multiplayer; the _desktop around it_ is single-player. You and your collaborator are two ghosts who can only touch each other inside this one rectangle.

**The game world.** Minecraft servers, Animal Crossing islands, Discord "study with me" calls. Interestingly, these are the _closest_ thing to what you described — persistent shared places with presence, decoration, and stuff you made together. Millions of people already choose to do homework "next to" each other in a Discord voice channel with a lofi playlist. The demand for ambient digital togetherness is proven and enormous. It's just that the only industry that ever built persistent shared _places_ was the games industry — so the places are all made of blocks and can't hold your actual homework.

Here's the underlying reason for all three failures, and it connects straight back to the spec's second invariant: **you can't share pixels, you can only show them.** A screen is a rendering — private, ephemeral, meaningless to copy. Google Docs became multiplayer _precisely because_ a document stopped being pixels and became structured state (a stream of operations that could be merged). The entire modern collaboration industry is, in a sense, one insight — _structured state can be shared; renderings can't_ — applied to exactly one object type at a time. Docs. Then design files (Figma). Then whiteboards. Then code editors (Live Share).

Agora's whole premise is that _everything_ is structured state and the screen is just a projection. Which means Agora doesn't have to bolt multiplayer onto each app one at a time.

> **In Agora, multiplayer isn't a feature of applications. It's a property of the world.**

If the canonical truth is objects, facets, and events — then sharing a space is just... replicating events between two homes. The hard part is already in the architecture. What's left is the _human_ design, and that's the fun part.

---

## 2. What a room actually is

Let's define it with the machinery we already built. A **room** is:

1. **A shared world-line** — a region of world whose event log is replicated to everyone in it. Your private world is a ledger with one witness; a room is a ledger with several.
2. **An entity like any other** — and this is the move that makes your couch-sketch real. The room itself is an object with facets:

entity: our_room # yours and hers

facets:

name: "the corner booth"

members: alex, sam

wallpaper: blob-ref → that photo from October

ambience: playlist-ref, autoplay: gentle

on-enter: open shared-chat, ping presence

layout: her desk zone / your desk zone / the shared table

The playlist you both like isn't an app running in the room — it's a _facet of the room_. The wallpaper is a facet. The "preloads with a video call" behavior is an `on-enter` facet. Which means the room is customizable with the exact same machinery as everything else in Agora, and — this matters — **JEFF can decorate.** "Jeff, make it cozier in here" is a legal, ordinary request, because coziness is stored in mutable state.

3. **A capability boundary.** Entering the room doesn't mean merging your lives. Your home world stays yours. You _bring_ objects into the room the way you bring things to a friend's apartment — deliberately, one at a time — and bringing an object in means granting the room's members capabilities on it. Your homework can sit on the shared table where she can _see_ it while only you can _edit_ it. Or you hand her the pen. The `acl` on every entity was designed for workers; it turns out it was also designed for this.

---

## 3. The togetherness part — presence without performance

What you described with your girlfriend is something subtle that almost no software targets: **parallel presence.** Not collaboration — _company_. Sitting in the same room doing _separate_ things, which is most of what couples and close friends actually do together.

The schema already has the primitive for it: presence facets. In a room, presence becomes mutual and ambient:  

- You can _feel_ where she is — her zone of the room glows faintly around whatever she's focused on, the way you can sense someone across a real room without watching them.
- Her focus is visible but her _content_ isn't, unless shared. Presence ≠ surveillance. You know she's deep in her essay; you can't read it. This distinction — legible presence, private content — is exactly the difference between sitting near someone and reading over their shoulder, and getting it right is the entire ballgame emotionally.
- And deixis goes multiplayer. The spec already treats "look at _this_" as fundamental between you and JEFF. In a room, **highlight-to-everyone** is the same mechanism with more witnesses: you flare an object's salience, and it gently pulses in _her_ viewport too. That's the digital version of turning your laptop around to show someone something — an act humans perform approximately nine hundred times a day, for which no OS has ever had a primitive.

The room accumulates what shared physical spaces accumulate: **sediment.** The half-finished crossword object from three weeks ago. The playlist that's grown by accretion. The inside-joke sticky note neither of you will delete. This is the thing games understood and productivity software never did — a _place_ is persistent state plus presence plus memory, and a place you keep returning to becomes _yours_ in a way no Google Doc ever becomes yours. You're not designing a collaboration feature. You're designing a **third place** that happens to be able to hold real work.

---

## 4. Scaling it up: the engineering room

Now take the same object and change the members list and the furniture. Here's where your Slack observation cuts deep, so let me sharpen it:

**Slack's original sin is that conversation lives in a different universe than the things being discussed.** The code is in GitHub. The design is in Figma. The discussion _about_ them is in Slack, connected by links that rot, in channels organized by time rather than by topic-actually-meant. Six months later, the _decision_ is findable in none of them. Every engineering team runs an informal, failing archaeology program trying to reconnect conversations to artifacts.

In a room, this problem doesn't get solved — it gets _deleted_, because it can't be expressed. A message in an Agora room is an entity. The code it discusses is an entity. They're linked by an edge, _born linked_, sitting next to each other on the same table:

msg_2214: "this retry logic scares me"

├── attached-to → code_object: retry.ts (lines 40–62)

├── asserted_by: priya

└── resolved-by → commit-event 8841

The thread doesn't _reference_ the work. The thread is _stapled to_ the work, and the event log means the conversation, the code change it caused, and the reason both exist are one queryable braid. Onboarding a new engineer stops being "read these seventeen pinned docs" and becomes _entering the room_ — where the history of every object answers "why is it like this?" because the ledger never forgot.

And your tool-sharing instinct is exactly right, and the facet model makes it almost embarrassingly easy. Remember: in Agora an "app" is a bundle of lenses and capabilities, not a walled castle. So when one engineer builds herself a little log-visualizer lens on a Tuesday, sharing it is **dropping it in the room** — like setting a tool on the communal workbench. Everyone's right-click menus and everyone's JEFFs learn the trick simultaneously. The codec-pack effect goes social: a long-lived team room becomes a _workshop that has accumulated craft_, which is the mechanism behind the spec's §6 growth flywheel — not an app store, but ten thousand workbenches, and the best tools migrating from room to room the way good recipes migrate between kitchens.

---

## 5. The two JEFFs problem (which is actually a delight)

Here's the question the spec has never had to face: you walk into the room, and so does your JEFF. She walks in with _hers_.

This forces genuinely new design, and all of it is interesting:

- **Etiquette.** Your JEFF knows things about you — your history, your habits, what you tried last night at 2am. What may he _say_ in the room? The obvious rule mirrors human discretion: what happened in your home world is confidential by default; what happens in the room is common knowledge among members. JEFF needs, literally, the concept of _discretion_ — and notice your architecture can actually enforce it, because his memories carry provenance tags saying where they came from.
- **Two witnesses, two ledgers.** The room has one shared event log, but each JEFF weaves it into a _different_ memory — hers indexed by what matters to her, yours by what matters to you. Just like a real shared evening: one event, two rememberings. When the world-is-reversible-witness-is-not principle meets multiplayer, you get something lovely — a rolled-back experiment in the team room is forgotten by the _room_ but remembered _differently by every JEFF who watched_, each carrying home the lesson relevant to their human.
- **Room agents.** Long-lived rooms probably deserve their own resident — not anyone's personal JEFF, but a _household_ agent belonging to the room itself: keeper of the shared context, the one who knows where the team left things, who maintains the workshop. Every clubhouse eventually acquires a caretaker. There's something quietly right about a couple's room having its own small keeper who belongs to _neither of them and both_.

---

## 6. The fine print (honest as always)

**Whose undo?** Rollback in a shared world-line is a _shared decision_ — you can't unilaterally rewind a room your teammate is standing in. But branching saves the day: fork the room's state to try something (git-brain for engineers; "let me try rearranging, don't look" for couples), then merge or discard. Personal memory, as always, survives either way.

**Consent at the boundary.** The room's edge is where all the capability discipline earns its keep. Bringing an object in is an explicit grant; _leaving_ a room should be as clean — you take your objects, your grants revoke, your JEFF's room-memories stay tagged as room-memories.

**And the poignant case:** what happens to the room if the couple breaks up, or the team dissolves? The ledger has an answer that whiteboards never could: **fork the world-line.** Each person keeps a complete copy of the shared history — every object, every event, the whole sediment — frozen or carried forward separately. Nobody can delete the past out from under the other, and nobody has to keep living in it. That's a gentler divorce than any filesystem has ever offered, and it falls out of the architecture for free.

---

## 7. The cheat sheet

|Room concept|Closest familiar thing|The upgrade|
|---|---|---|
|A room|Discord channel + Minecraft server + shared Google Doc|One persistent _place_ that holds real work, decoration, and history|
|Room facets|Server icon, channel topic, spotify group session|Playlist/wallpaper/on-enter are mutable state — JEFF can redecorate|
|Bringing an object in|Attaching a file to Slack|A live grant, not a dead copy — one object, no version forks|
|Presence|Green dot / "in a meeting"|Ambient, spatial, legible-but-private: company without surveillance|
|Highlight-to-everyone|Turning your laptop around|A native primitive for _look at this_|
|Messages|Slack threads|Entities stapled to artifacts; discussion and work share a table|
|Tool sharing|"Can you send me that script?"|Drop it on the workbench; everyone's menus and JEFFs learn it|
|Room history|Pinned posts + tribal knowledge|The ledger _is_ the onboarding doc|
|Breakup/dissolution|Fighting over the shared drive|Fork the world-line; both keep the whole past|

---

## 8. The one-sentence version

Every collaboration tool ever built shares a _document_; what you sketched with your girlfriend is sharing a _place_ — and because Agora already made the whole world out of shareable structured state with a ledger underneath, the room isn't a new architecture, it's just the front door opening: the same objects, facets, events, and witnesses, but with two chairs.

And one closing thought. You started this conversation with an OS for one person and one agent — a _home_. The moment homes exist, the next thing humans build is always the same: places to be together. The couple's corner booth and the engineers' workshop are the same primitive at two temperatures, and the name you chose was pointing here the whole time. The agora was never the house. It's the square the houses open onto.