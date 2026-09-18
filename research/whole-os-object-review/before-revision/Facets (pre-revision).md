Let me back way up and build this from the ground floor, because the facet idea is genuinely a different way of thinking about what's "on" a computer, and it's easy to nod along without it actually clicking.

---

## 1. Start with how Windows thinks

On Windows, the fundamental unit is the **file**, and a file is basically two things:

1. A blob of bytes
2. An extension (`.docx`, `.png`, `.exe`) that tells Windows **which single application owns it**

That second part is the important one. The extension is a _marriage certificate_. A `.docx` belongs to Word. A `.psd` belongs to Photoshop. Double-clicking is really asking "who is this file married to?" and handing it over. All of the interesting stuff about the file — what it means, what it relates to, what you were doing with it — lives _inside the owning application_, in formats nobody else can read. Your emails live inside Outlook. Your browser tabs live inside Chrome. The file system itself knows almost nothing: a name, a size, a date, and who owns it.

Now notice what happens when you right-click a file and hit **Properties**. You get a sad little dialog: size, dates, read-only checkbox, maybe author and camera model if it's a photo. That dialog is Windows _gesturing_ at the idea that a file could carry rich information about itself. It just never follows through.

**A facet is what the Properties dialog wanted to be when it grew up.**

---

## 2. The object is an ID card. Facets are stickers.

In Agora, the fundamental unit is not a file. It's an **entity** — and an entity, by itself, is almost nothing. Strip away everything optional and an entity is basically:

> A permanent, unforgeable ID number, and an empty bag.

That's it. It has no type. No content. No appearance. It's a blank ID card.

Everything else — literally everything — is a **facet**: a labeled sticker attached to the card. Some stickers you'd recognize immediately:

- a **name** facet: "meeting notes from Tuesday"
- a **text-content** facet: the actual words
- a **visual** facet: where it sits on screen and how big it is
- a **tags** facet: `#project-x`, `#urgent`
- a **file-backing** facet: "my bytes live at `/projects/notes/tuesday.md`"

The closest thing you've probably used is a **Trello card** or a **Notion page**. Think about a Trello card: the card itself is just an identity. Then you _attach things to it_ — a description, labels, a due date, a checklist, an image, comments. A card with a due date isn't a different _type_ of card than one without. You just stuck a due-date on it. Nobody had to redesign Trello to allow "cards that have both an image AND a checklist" — attachments combine freely because they're independent.

Facets are that, taken all the way down to the operating system.

---

## 3. The trick: there are no "types of things"

Here's where it gets genuinely different from Windows, and it's the part worth sitting with.

In Windows, "what kind of thing is this?" is the first and most important question. Is it a document? An app? A shortcut? A folder? Everything downstream depends on the answer.

In Agora, **"kind" is just a description of which stickers happen to be on the card.**

- A "note" = an entity wearing `name` + `text-content` + `visual` stickers.
- A "running prototype" = an entity wearing `spec` + `status` + `file-backing` + `visual` stickers.
- A "bookmark" = `name` + `url` + `semantic` stickers.

There IS a `kind-tag` facet — a sticker that says "note" — but it's **advisory**, like a label on a moving box. Writing "kitchen stuff" on a box doesn't make it illegal to put a book in there. The label helps you find things; it doesn't constrain what the box can hold.

The Windows analogy for why this matters: you know how renaming `photo.jpg` to `photo.txt` doesn't change the photo — it just confuses Windows about who to hand it to? That's because in Windows the _label_ (extension) is load-bearing. In Agora, nothing is ever confused that way, because no behavior hangs off the label. Behavior hangs off the actual facets present: "does this thing have text content? Then it's editable as text. Does it have a process spec? Then it can be started and stopped." Both can be true _at once_.

And that "both at once" is the payoff. Watch what this allows:

> You jot a note: "what if we cached the db queries?" — that's an entity with a text facet. Later, JEFF attaches a `derived-from` edge to it and a coding worker builds a prototype. Now someone attaches a `spec` facet to the _note itself_: "serve the demo at :5173." The note is now also a running program. It didn't convert to a new type. It didn't get exported into some other app's format. It just **grew**.

In Windows this journey would cross four applications and three file formats and lose all its history. In Agora it's one entity accumulating stickers.

---

## 4. Three facets worth understanding individually

### 4.1 `spec` and `status` — the thermostat pair

This one has a perfect household analogy: **a thermostat.**

- You set the dial to 70°. That's the **spec** — the desired state. You wrote it; it expresses intent.
- The thermometer reads 66°. That's the **status** — the observed truth. You _can't_ write it; only reality writes it.
- The furnace notices the gap and runs until they match. That's the **reconciler**.

Any Agora object that involves something _live_ — a running program, a server, a download — splits its liveness into these two stickers. Why does this matter? Think about what happens in Windows when you reboot: every running program is just _gone_, and it's your job to remember what was open and restore it by hand. That's because Windows only ever stored the equivalent of _status_ (what's running right now) and never the _spec_ (what _should_ be running).

In Agora, reboot the world and the specs are all still there saying "a node server should be serving this project on port 5173." The reconciler reads them and reality reassembles itself — the same way your furnace doesn't need to be told what to do after a power outage, because the dial is still set to 70.

### 4.2 The capability facet — the right-click menu, generated honestly

In Windows, when you right-click a file, that context menu (_Open, Edit, Print, Extract All..._) comes from the registry — apps sneak entries in during installation, and the menu is a rickety pile of claims about what might work.

In Agora, an object's **capability facet** is the authoritative list of what can actually be done to it: this object can be _started, stopped, edited, published_. And here's the key move: **the buttons a human sees and the tools JEFF sees are both generated from that same list.** The right-click menu and the agent's abilities are the same object, projected two ways. There's never a case where the human can click something JEFF can't do, or JEFF can invoke something invisible to you.

### 4.3 The projection facet behavior — tooltips all the way up

You already use level-of-detail every day without naming it:

- Hover a file → **tooltip** (one line)
- Click it → **preview pane** (a paragraph and a thumbnail)
- Double-click → **the whole thing**

Same object, three sizes of description depending on how much attention you're spending. Agora makes this an obligation of every facet — but with a twist: objects must know how to describe themselves _at different sizes_ not just for the screen, but **for JEFF's mind**. JEFF's context window is like a desk with limited surface area. The thing you're focused on gets described in full detail; the forty other objects in the room get one-line tooltips. Objects in Agora know how to be their own tooltip.

---

## 5. So where do applications go?

This is the question that reveals the whole inversion, so let me do it carefully.

### 5.1 In Windows, apps are landlords

Windows applications **own data**. Outlook doesn't show you your email; Outlook _has_ your email, inside a `.pst` file only Outlook understands. Excel has your table. iTunes had your music library. The app is a landlord and your data is a tenant who can't leave without filling out export paperwork.

This is why everything on a normal computer is siloed: the _app boundary_ is the _data boundary_.

### 5.2 In Agora, apps are lenses and toolboxes

Agora flips the ownership. **The data lives in the world, as entities and facets. An application is just a way of looking at and acting on facets.**

An Agora-native "app" decomposes into three things:

1. **A lens** — a renderer for certain facets. A "text editor" is a lens over `text-content` facets. A "kanban board" is a lens over a group of entities' `status` tags.
2. **A toolbox** — handlers that implement capabilities. Installing a "video trimming" app means entities with video facets _gain a trim capability_ — in your right-click menu AND in JEFF's toolset simultaneously.
3. **Optionally, new facet types and reconcilers** — a CAD app might introduce a `parametric-model` facet and the machinery to regenerate geometry when parameters change.

The best Windows analogy here is a **codec pack**. When you install a video codec on Windows, something subtle and wonderful happens: _every_ video player on the machine can suddenly play that format. The capability soaked into the system rather than into one app. Agora apps work like that for _everything_. Installing an app doesn't add a walled garden; it teaches the whole world new tricks.

A consequence worth pausing on: **two "apps" can be open on the same object at the same time.** You can have the text lens and the outline lens both pointed at the same entity, live, because neither of them _owns_ it — they're both just windows onto the same facets. In Windows this is nearly impossible (two apps fighting over one file = lock errors and "file is in use"). In Agora it's the default.

### 5.3 What about real, existing software — Photoshop, a random Linux app?

They don't disappear, and they don't get to be landlords either. A legacy application gets **wrapped in an entity**:

entity: photoshop_session_3

spec: run photoshop ← so it survives reboots

status: pid 4411, running

surface-binding: its actual window

file-backing: /projects/poster/draft.psd

provenance: opened-by alex, part-of poster-project

The app itself stays opaque — Agora can't see inside Photoshop's brain — but the _fact of it_ becomes a citizen of the world: it has identity, it belongs to a project, it appears in history, it can be found by search, JEFF knows it exists and what file it's touching. Think of how a Mac runs a Windows app in Parallels: the app doesn't know where it really lives, but it's been given a window and a place in the world. Same idea. The `.psd` file stays a real file on a real filesystem (this is deliberate — bytes are never imprisoned in Agora's database), and the entity just _points_ at it and accumulates meaning around it.

So there's a spectrum of citizenship:

Agora-native object full citizen — all facets live and readable

wrapped web/browser partial — Agora sees the page, DOM, URL

wrapped terminal/editor partial — Agora sees files, processes, project

wrapped opaque app resident alien — identity, window, file, history

...but its interior is dark

### 5.4 One more inversion: "installing" vs "growing"

On Windows, functionality arrives in big sealed boxes (install an app) and data gets created inside those boxes. In Agora the arrow points the other way: **the world accumulates facet types, lenses, and capabilities over time** — some downloaded, some built by JEFF and you on a Tuesday afternoon because you wanted a lens that shows your notes as a constellation. An "app" in the Agora app-sharing ecosystem is really a _bundle of lenses, capabilities, and facet definitions_ that other people found useful — closer to sharing a set of Notion templates + plugins than shipping an `.exe`.

---

## 6. The cheat sheet

|Agora concept|Closest familiar thing|The upgrade|
|---|---|---|
|Entity|A file / a Trello card|Permanent ID; survives moves, renames, even deletion (leaves a tombstone)|
|Facet|Trello attachments / Notion properties / file Properties dialog|First-class, typed, composable; ANY combination legal|
|`kind-tag`|File extension|Advisory label, not a marriage certificate; nothing breaks if it's "wrong"|
|`spec` / `status`|Thermostat dial vs. thermometer|The world reassembles itself after reboots and rollbacks|
|Capability facet|Right-click context menu / file associations|Generated from truth; identical for human and JEFF|
|Projection|Tooltip → preview pane → open|Objects self-describe at any size, to screens _and_ to JEFF's attention|
|Edges|Shortcuts / hyperlinks|Carry authorship ("who claimed this link, and when") like tracked changes|
|Native app|Codec pack + Notion template + plugin|Teaches the whole world; owns nothing|
|Legacy app|App in Parallels / a VM window|Opaque inside, but a known citizen with identity and history|
|Event log|Recycle Bin + Ctrl+Z + file history|Universal, permanent, and _why_-aware, not just _what_-aware|

---

## 7. The one-sentence version

If Windows is a city of walled castles where your belongings live inside whichever castle made them, Agora is a city where **your belongings live in the streets and squares under permanent ID, and "applications" are just craftsmen who know how to work on certain kinds of belongings** — any craftsman can work on any object that has the right features, several can work on one object at once, and JEFF is the resident who knows every object, remembers every job, and can hire new craftsmen or train his own.

The reason this isn't how computers already work is honestly historical: the app-owns-data model won in the 1980s because it was simpler to ship. Every attempt to invert it (OpenDoc, WinFS) died because inverting it requires _something_ to make sense of a world of loose, mingled data — and until now, nothing could. A resident mind is the missing piece the architecture was always waiting for.