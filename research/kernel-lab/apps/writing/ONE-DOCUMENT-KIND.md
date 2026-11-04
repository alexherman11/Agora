# One document kind

*Draft by Claude, 3 Nov 2026, revised the same day after three reviews (a code check, a design critic, and JEFF in Shop talk, dk2046). From Alex's ask of 3 Nov: "the writing center documents and documents in agora should be the same kind of thing. They should be editable as continuous documents (think obsidian) and they should support the $.name vocabulary. They should support comments, highlighting etc." A proposal for Alex's gate; nothing here is built. The interactive version is the artifact "One Document".*

## What exists (read, 3 Nov, unless marked)

- **Writing** (`apps/writing/`): `kind=document` with `title`, `text` (one Markdown string), `collection`. Editing swaps one drawn block for a textarea, then saves the whole text with `set <doc> text=`. The painted `saw` fences every aspect, so any change by anyone since the edit began refuses the save; the words are rescued with "Add them at the end".
- **Comments** (`kind=comment`: `about quote before after heading reply_to resolved`) are re-found by searching the drawn text for the quote. `before`/`after` are captured from the *first* occurrence of the quote, not where the selection was (writing-components.js:364-366, 726), and marking wraps the first match only (369-379).
  - **Ran:** 11 top-level comments on 19 written documents; all 11 quotes are still present.
  - **Ran:** 2 of the 11 quote a phrase that appears twice, so they may mark the wrong place. These are Alex's two nested comments in "Why the agents stall" on "workers can't run their own tests".
- **Board Documents** (`community-app/board/documents.py`): a library of folders and `document-entry` rows. `files.store` accepts only uploaded `file` things (documents.py:50-62, 81-90), so a written document can't be filed without a module change.
- **Uploads**: `files.convert` mints a second, different `kind=document` with `file_source=`; its page text stays in a blob manifest (`kernel/blobs.py:179-228`, "Only small structural facts go in the log").
- **`$` fill-ins** exist only in lens templates (`$item.x`, `$view.x`, `$viewer.name`) and flat kernel names (`$me $today`), "never inside quoted text". There is no `$.name` form, and nothing fills references in prose.
- **Storage** (store.py:58-91): every value of every aspect is kept in an append-only log that is held in memory and replayed at start.
  - **Ran:** the live world log is 52 MB over 4,475 records, with 102 text facts over 2,000 characters; the largest is 41 KB.
  - **Imagined:** autosaving whole text would grow the log by tens of MB per writing session.
- **Painter** (painter.js:268-279): rebuilds a component's DOM on every plan change and restores only an input's value and caret. A document `keydown` handler (painter.js:281) swallows the key `n` outside an INPUT or TEXTAREA, so it would eat typing in a contenteditable editor.

I was wrong in the first draft about one thing: there is no kernel `replace` word that agents already know. It lived on the archived desk.

## The proposal

> **Superseded in part, 4 Nov.** Pieces 1–3 below (edits, two people at once, comments) are replaced by "Redraft, 4 Nov: one history per document", further down. Pieces 4–6 still stand. The first version is kept here so the reasoning can be followed.

**One kind, `document`: a thing with a title and a Markdown body. The same thing shows in Writing, in a board library and in its own window. Where it lives, what it was made from and who commented on it are ordinary facts and things around it.**

### 1. Edits are small changes, not whole copies
- A save records only what changed (an edit: the words removed and the words put in, against the revision it started from), so the log grows with typing, not with document size × saves. The current text is worked out from the edits, in memory.
- The same edit is what agents send (a new word, `edit <doc> old="…" new="…"`), and what lets two people's changes combine.
- The page keeps your typing locally as you go and sends an edit about two seconds after you pause. Nothing you type is lost to a refusal or a dropped connection (JEFF's rule).

### 2. Two people at once
- Edits to different places both land. Others' edits fold into your page within a second or two without moving your caret.
- If two people change the same words, both versions are kept, one after the other, with a small note "Bea and you both changed this". No picker screen.
- Live co-typing in the same sentence is not in this. If neighbours take meeting minutes together, the upgrade is a CRDT body (Loro was tried in Milestone One) that still writes edits to the world.

### 3. Comments that stay put
- A comment remembers its paragraph. The first time anything points into a paragraph, the paragraph gets a hidden id (Obsidian's `^id`), and the comment keeps that id plus its quote and the words around it, taken from where you actually selected.
- Several comments can sit on the same words. Marks layer: darker where they overlap, and clicking shows all of them.
- If the words are rewritten or deleted, the comment stays, marked "detached", with its original quote. It never disappears silently.
- **A highlight is a comment without words**, with a colour. Yours are private by default; Share shows them to whoever sees the document.
- Highlighting still only selects (charter). Right-click (or, on a phone, a small bar above the selection) gives Comment and Highlight; Alex's Writing keeps Send to JEFF.

### 4. One thing in many places
- Writing and a board library point to the same document, never copies. Rename, move and history follow it.
- Filing a document into a library shares it with that library's people, asked once, the same way uploads are shared today. This needs a change to the files module.
- An uploaded PDF or Word file stays read-only and can be commented on page by page. "Make an editable copy" makes a new document that remembers its source; it does not sync with the file.

### 5. Continuous editing
- One editor over the whole document: selection, arrows, paste and undo cross paragraphs.
- Two looks over the same Markdown:
  - **Clean** (the default for neighbours): marks hidden, a small toolbar.
  - **Marks on the line** (Obsidian's Live Preview): the line you're on shows its `**`, `#` and `[[`.
- Board documents open for reading first; Edit is one tap.
- Built on CodeMirror 6 (what Obsidian uses), bundled into the painter. The editor survives repaints, as the map engine does. This needs the painter's `n` key fixed first.

### 6. `$` references (my reading of "$.name"; question 1)
- `$.status` reads **this document's own** fact, from a properties strip at the top. `$[[Garden meeting]].start` reads **another thing's** fact. Both are drawn as a live chip that follows the source.
- A picker opens only on `$.` or `$[[`, so "$5" and "$450k" are left alone.
- The stored text holds only the id, never a name or value. A reader who can't see the thing gets "hidden", and so does an agent reading the raw text. The same goes for `[[links]]`: today they store `[[id|Title]]`, which leaks titles.
- Drawing needs one new read that looks at many ids at once, through kinds; one `look` per chip is too slow.

### Later
- Live embeds: `![[thing]]` drawn through the thing's lens.
- A kernel link index, for "Linked from".
- Heading links `[[Doc#Heading]]`, outline, tags, templates.
- Export as a folder of plain `.md` files.

## Build order (if approved)
1. **Edits not copies:** the `edit` word, merging, and the log change. Writing's current editor uses it at once, so rescues stop.
2. **Comments that stay put:** capture at the real selection, paragraph ids, stacking, detached.
3. **One thing in many places:** board files documents, sharing on filing, Writing's page in the board.
4. **Continuous editor:** CodeMirror with both looks, the phone selection bar, and the painter fix.
5. **`$` references and highlights:** the many-id read, chips, properties strip.

Acceptance (JEFF's test): one page edited from Writing, reopened from the board with the same text, facts and comments intact.

## Questions for Alex
1. Which `$` did you mean? (a) a document's own facts (`$.status`); (b) another thing's facts in prose, such as a flyer showing `$[[Garden meeting]].start`; (c) words reaching into a document, such as reading its Risks section from elsewhere.
2. Will neighbours type meeting notes together live? Yes means CRDT now.
3. Neighbours' default look: Clean, or marks on the line?
4. Who may edit a board document: its author, the channel's group, or anyone signed in?
5. Highlights private by default?

### Alex's answers (4 Nov)
1. All of these.
2. Not sure, ask the group.
3. Clean (marks hidden, toolbar).
4. The author decides per document.
5. Shared by default.

He also raised a different idea for merging: use Agora's own intelligence so simultaneous typing combines naturally, perhaps over a CRDT so everyone shares one history. *Claude's reply (in chat, 4 Nov), not yet approved:*
- Use a CRDT as the body. It brings live co-typing, offline edits, one shared history, and comment anchors that survive edits.
- Keep intelligence beside the CRDT, not inside it: it spots collisions, proposes a tidy that a person accepts (an edit signed by the agent), summarises history, and lets agents rebase their own edits.
- The base must stay correct with no AI.
- If approved, this replaces build step 1 and most of step 2, and question 2 no longer needs answering.

## Redraft, 4 Nov: one history per document

> **Later on 4 Nov, Alex chose a shorter path:** "just make it so its a continous document for now ... make it a crdt, dont worry about same doc collaboration". Built: one continuous editor with a CRDT history per document, no co-typing (README.md, *One continuous editor*). The rest of this redraft (Suggest, removal, Combine, value kinds) is parked, not decided.

*Draft by Claude, 4 Nov 2026, corrected after an independent review the same day. Written after Alex asked for research on Automerge 3's compression, a redrafted plan, and a look at what else in Agora needs merging or version control. A proposal for his gate; nothing is built.*

### What the research found
- **Automerge 3** (read: automerge.org/blog/automerge-3, July 2025):
  - Version 2 already saved history compressed, in columns (each field of every change stored together, then run-length and delta encoded). It unpacked that history into memory when a document was opened.
  - Version 3 works on the compressed form directly. Their example: pasting Moby Dick took 700 MB in version 2 and 1.3 MB in version 3. A document that "hadn't loaded after 17 hours" loaded in 9 seconds.
  - The file format is unchanged. The engine is the Rust crate `hexane` (read: docs.rs).
- **Ink & Switch's Patchwork** (read: their 2024 version-control notebook) is the closest prior art to Alex's idea. It was built on Automerge. Its findings:
  - Branches work as a general, low-ceremony tool, across prose, drawings and spreadsheets.
  - History is most readable grouped by author and time. AI summaries of each edit were "a remarkably useful way to understand writing edits at a high level".
  - AI bots act as collaborators on branches, and their changes show in history.
  - Edit Groups, "formality on demand": people edit directly, then explain and group their edits afterwards. The author reviews and reverts rather than approving in advance.
  - Open problems: picking changes across branches, and showing how branches relate.
- **Removing things from history** is the one thing a CRDT is bad at.
  - Automerge keeps everything. Its `anonymize` masks values for bug reports; it is not a delete (read).
  - Loro can drop all history before a point every device has synced (shallow snapshot, read). It also has `redact_json_updates` (seen in its Python API, untested).
  - Agora's own log supports redacted values, but no word uses that yet (read: store.py:21-35).
  - The Constitution gives people the right to have their history deleted.
- **Earlier work here** (read: research/object-facet-frontier/POSITION.md §2.7, §5.2, §7.3, §7.6, §8.3). Sable ran an Automerge 3.5 anchor experiment: 50 anchor checks per way of writing.
  - A whole-text write through a character diff kept 42 of 50 comment anchors.
  - Its 8 losses were silent, all from a moved list item. Moves need to be recorded as moves.
  - Two writers in the same sentence garbled the prose.
  - The best writer worked by sentence. It refused only sentences changed since the writer read them, and applied a character diff inside the rest. Result: 42 intact, 8 collapsed (visible), 0 silent drift. Fine-grained edits, which is what live typing sends, kept 37 and collapsed 13 (visible), so comments will detach more often on the live path.
  - Sable's signed dissent: a CRDT earns its cost only for writes made away from the one write path. "I would change my mind if Rooms or offline phones become near-term." Neighbours on phones typing together is that case.

### What I ran (4 Nov, scratch folder; nothing in the repo)
Typing simulation over the live world's longest Writing document, "Agent prompts" (40 KB): 46,241 keystrokes including typos and fixes, then 400 revisions.

| | Automerge 3.5.0 | Loro 1.17.1 | Yjs 13.6.33 (history kept) |
|---|---|---|---|
| Saved with the full keystroke history (1-character commits) | 32 KB | 74 KB (31 KB with history trimmed) | 85 KB (the reviewer's rerun) |
| Time to open it | 0.2 s | 5 ms | 11 ms |
| Python, for the kernel | doesn't install on this PC (has to be built from source with Rust, not installed) | installs; reads a document made in the browser and edits it | not tried |
| "The hearing is Tuesday." · you → Thursday, Bea → "moved to the 14th", at once | "The hearing moved to the 14thThursday." | same | not tried |

For comparison, saving the whole text at each pause would have stored 4.8 MB for the same session. That is today's way, and an unfair baseline: the 3 Nov plan of small edits would store roughly the typed characters, about the same as a CRDT. *Correction from review:* a CRDT does not win on storage. Its case is merging, offline work, anchors and one history. Build times are left out because they included loading the library.

Also ran, in Python Loro:
- A comment's anchors survived an edit made concurrently on another device and still covered exactly its words.
- *Correction from review:* my "detached" check was wrong. Collapsed anchors don't catch partial loss. A light rewrite left a comment on " gym" alone. The cursor's own `update` field, which is set when its character is gone, does catch it (reviewer ran). Comments need three states: intact, changed (show the original quote), detached.
- A whole-text write (`update`) inserted only the 9 new characters. Today's editor and agents can keep sending whole text.

Not measured:
- Memory for one document: the numbers above include loading each library.
- Documents with several authors.
- The painter page's security settings. Loro and Automerge are WebAssembly; Yjs is plain JavaScript.

### The redraft
1. **The body is a Loro document; the world still decides.**
   - Each document's text is one CRDT, saved as compressed bytes beside the log, as file pages are today. The log keeps small facts: current version, word count, who edited, summaries.
   - The page keeps a local copy, so it works on a phone with no signal. It sends changes every half second while you type.
   - The kernel merges changes and passes them to everyone else who has the page open, with their cursors.
   - The CRDT says how edits combine; the kernel says whose edits count (the author decides, question 4).
   - I lean to Loro because:
     - it runs in the Python kernel today (ran);
     - it is fastest to build and open (ran);
     - it can trim history (read).
   - Automerge 3 stores less (32 KB against 74 KB, ran). It would need Rust on this PC, or a separate JavaScript process beside the kernel.
2. **Two kinds of writer, two paths** (Sable's result kept, not thrown away).
   - *People typing live* send fine-grained edits straight into the CRDT, with presence. Seeing each other's cursors is what keeps collisions rare.
   - *Whole-text writers* (agents, imports, today's textarea) go through the gateway rule. The writer says which version it read. Sentences changed since are held, not overwritten. A character diff applies inside the rest. The kernel forks at the version the writer read and compares both sides with it. *From review:* Loro text has no move operation. Paragraph moves need either paragraphs as a movable list of texts, or the gateway spotting moves and carrying anchors across. This is open.
   - A held sentence is not an error. It is the one place where intelligence is useful.
3. **Collisions are marked; intelligence offers, people decide.**
   - When two people change the same sentence without seeing each other (offline, or within a second), or a gateway write is held, the sentence is marked "two versions here". Both originals sit in the margin. No AI is needed for this.
   - For live typists the CRDT has already merged, so the mark is found afterwards: overlapping concurrent changes inside one sentence, with each side rebuilt from its own version. It is cleanup, not prevention.
   - Intelligence works after the fact, at a pause or a sentence, never at keystroke speed. Where it is on, "Combine" proposes one sentence. Accepting it is an edit signed by the agent and can be undone. For neighbours, I'd start with Combine only when asked (question 3).
   - The bigger use, from review: agents cause most collisions, so an agent reworking its own held edit onto the latest version is worth more than Combine for people.
   - Bigger agent rewrites go on a branch, as Patchwork's bots do. They are a suggestion you merge or discard, never typing into your sentence.
4. **Suggestions are branches** (new; Alex's gate).
   - The author decides who edits. Anyone else who can read can press Suggest. Their typing goes into a branch, drawn as marked changes, and the author merges or declines it.
   - Neighbours and agents use the same mechanism.
5. **History people can read.**
   - Every keystroke is kept, but history shows it grouped by person and pause, Patchwork style.
   - You can rewind to any moment, restore a paragraph, or see who wrote a sentence.
   - Summaries come from intelligence when it is on ("Bea added the hearing date"). Without it, a plain line: "Bea changed 2 paragraphs, +41 words".
6. **Comments hold characters, not paragraphs.**
   - A comment stores CRDT anchors for its first and last character, and stays its own world thing (author, replies, permission). This replaces the hidden paragraph ids.
   - Stacking works naturally: your double comments become two anchor pairs over the same words.
   - When all its words are deleted, its anchors collapse and it shows "detached" with its original quote.
   - Highlights work the same way, shared by default (question 5).
7. **Removal.**
   - "Remove from history" (the author or a leader) cuts the history at a point. Everything earlier becomes one snapshot, the old bytes are destroyed, and the history shows "earlier history cleared by Alex, 4 Nov".
   - For a pasted phone number or home address. Rare, and it loses rewinds before the cut.
   - Needs Alex's decision.

### Problems the spike must settle (from review)
- **Log and bytes.** The fence, `rev`, undo and the event stream all read log records. A body kept beside the log is invisible to them, unless each pause writes a log fact carrying the body's version. We also need:
  - a rule for a crash between writing the bytes and writing the fact;
  - a decision on whether the hash chain covers content;
  - `undo` for a body to mean a reverse change, not "put the old value back".
- **Whose edits count.**
  - Each session gets its own author id, and the kernel refuses updates claiming anyone else's.
  - A refused update can't be un-applied on the sender's phone. It becomes that person's Suggest branch, which ties point 4 to enforcement.
  - Editors who lose permission while offline need the same path.
- **What readers receive.** A full history gives every reader's phone the deleted text too. Readers get the current state or trimmed history; full history only for those allowed. A cut can't reach copies already on phones. Offline edits that predate a cut must be redone from their text.
- **Presence.** Cursors stay out of the log (Loro has a separate store for passing state). The server is one thread per open connection, plus a post every half second per typist; that load needs measuring.
- **History grouping.** Loro merges consecutive commits by default (the reviewer saw 40,000 commits saved as 1 change). Timestamps and a merge interval must be set to group by pause.
- **Removal.** Loro also has `redact_json_updates` (present, untested). Compare it with cutting history.

### Build order (replaces steps 1–2 above)
1. A spike in a private world over copies of the live documents, to settle the architecture first:
   - what the log records per pause, and how the fence, stream and undo see it;
   - author ids bound to sessions;
   - a refused update becoming a branch;
   - two simulated phones editing offline;
   - the gateway rule for whole-text writers.
   Memory per document is second. Writing's current editor writes through it, so rescues stop.
2. Live sync to open pages, with cursors. Ask the group first whether they'd type together (Alex's answer 2).
3. Comments on anchors, with stacking and detached. Move the 11 existing comments over.
4. One thing in many places (the board), as before.
5. The continuous editor (CodeMirror over Loro).
6. History view and collision marks; then summaries, Combine, and Suggest branches.
7. `$` references.

### What else in Agora needs merging or versions
What exists (read, from a map of the code; file:line in the map):
- **The world** is one append-only log. Every aspect's history is in memory.
- **Concurrent writes** are fenced per aspect and refused when stale ("nothing was done"). The kernel never merges; the archived desk's merge3 and Sable's partial-merge journal were not ported.
- **Undo** puts back earlier values and refuses if a value changed since.
- **Lenses, styles, components and verb steps** are each one whole text value.
- **Kits** copy a definition with its origin and never sync back.
- **Code** merges through the House: worker branches, review, fast-forward.

The idea (imagined):
- **Every value kind says how it combines.** Kinds already go all the way down to value kinds, so this is one more fact on a value kind, not a new system. Its prerequisite (from review) is writes recorded as operations ("add this", "move that"), not new values. That is POSITION 8.2's operation record, still unbuilt:

| Value kind | How it combines | Where in Agora |
|---|---|---|
| a plain value | last change wins, fenced; the history is kept | a card's lane, a pin's place, an event's start |
| a set | adds and removes both land | votes, members, a channel's people, tags |
| a list or tree with identity | moves stay moves | agenda items, folders, board lane order, layout splits |
| prose | CRDT text (above) | documents, verb steps, help topics, JEFF's notes |
| a definition | never merged live; a branch, then a pinned activation | lenses, styles, rules, components |

- **Definitions need branches, not live merging.** A half-merged lens breaks the screen.
  - Previous Work's lesson: "Pin definition revisions; keep the last good version".
  - Dynamic Desk wants people to follow a shared feature "until they choose to change something". That needs a kit that keeps following its origin: when the origin changes, a three-way merge against your changes, holding conflicts.
  - Intelligence is most useful here: explaining what changed upstream and adapting your change to it. This is the Seabright "features spread, opt out" story.
- **Worlds and experiments** (private worlds, sandboxes, the parallel worldline) merge back by applying each change by its kind: apply the clean ones, hold the conflicts. That is POSITION 8.2's partial merge, still unbuilt.
- **History, comments and removal should be universal.**
  - The same grouped, summarised history for a pin, a card or a lens as for a document.
  - Comments on any thing, with an anchor each kind defines (Patchwork's "universal comments with pointers").
  - One `redact` word for the Constitution's right to deletion. The log format already allows it.
- **Things that need no merging:** chat lines (each line is its own thing, only its speaker changes it), and screen state such as geometry (Alex, 26 Oct: it stays local).
- **Why not make the whole world one CRDT:**
  - A CRDT syncs whole, but Agora shows each thing only to the people allowed to see it.
  - So CRDTs stay inside values, and the world stays the one authority on who may see and change what.
  - That would change if Keyhive-style access control (Ink & Switch; research stage, read) matures.

### What would change my mind (redraft)
- If the spike shows Loro bodies cost too much memory across hundreds of documents, keep plain text plus the gateway rule (Sable's dissent) until offline phones are real.
- If neighbours almost never type at once, live sync can wait; the gateway rule and history are still worth it.
- If Automerge ships a Python wheel for Windows, compare again: it is smaller, and it is what Patchwork and Keyhive build on.
- If Combine proposals turn out to be wrong often, drop them and keep only the "two versions here" mark.

## What would change my mind
- If neighbours co-type live, the merge is the wrong tool and a CRDT body is.
- If CodeMirror can't take the pixel look or is too heavy on phones, a lighter editor.
- If `$` references turn out to be rare one-offs, a link with a hover value is enough.
- If documents in Seabright turn out to have one author each, step 2 of the proposal (two people at once) can wait.
