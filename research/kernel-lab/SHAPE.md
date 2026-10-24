> Draft by Claude (kernel story, Board a13310, epic a13308), 23 October 2026. Approved by the coordinating session the same day, acting with Alex's authority over this build; its answers are in section 16. The walking skeleton (section 14) is built from it. Claims are labelled **ran** (executed here, numbers as printed), **read** (from source or documents, with where) or **imagined** (design or thought experiment). Alex's words are in quotation marks and come from [[Communities and the Dictionary]].

# The kernel's first shape

## What the kernel is for

The kernel is the small part that holds the only powers there are, so that everything above it can be words. In the design's table it is "the store, persons, the dictionary, who may and who sees, the door, the painter". It is built for many people from its first day: about 200 neighbours who are mostly not AI users, their own agents, and modules written by a few builders in any language.

It is not the desk rewritten. The desk's language, receipts, fence, undo and painter carry over; the desk's world model, the pickle, the house and its residents do not. Frontier keeps running untouched.

The test I hold the shape to: **an act by a neighbour pressing a button, an act by their agent typing a line, and an act by a module answering a call are the same thing to the kernel.** Each is a line, with an author and what the author saw, checked against the author's words, recorded as facts, answered with a receipt. If any of the three needs a path of its own, the shape is wrong.

## What we stand on

Four rebuilds left lessons that shape this one directly (**read**: `docs/Previous Work.md`, Reusable lessons).

| Lesson | Where learned | What it decides here |
|---|---|---|
| One authenticated write path; a refused act leaves no trace | Milestone One, Agora3 | The door is the only way in. A refused line writes nothing to the log. |
| Replay restores state and never repeats effects | Design vault, Agora3 | The log holds facts. Replay applies facts and never parses the words again. |
| Refuse stale writes; record what the actor saw | Milestone One, text desk | Every act carries what its author saw, whoever the author is. |
| Never wait on another runtime while holding a lock | Agora4 recovery | A module computes outside the kernel's lock and hands back lines. |
| Candidate ready is not installed; adoption rechecks inputs | Agora3 yard, parallel work | A module's answer is admitted only if what it read is still true. |
| Keep recovery outside what is being rewritten | Agora3 shell | The steward's floor (`look`, `help`, `undo`, `off`) survives any edit to the dictionary. |
| It carried later features before one claim was tested | The spine attempt, 2 to 3 Sep | Phase 2 is five words and one module. Nothing else. |
| Per-app JavaScript and QuickJS components were dropped for words | Agora4, Milestone One extensions | Modules export words. The kernel never runs module code itself. |

And the desk taught three things that are easy to lose in a rebuild (**read**: `docs/Current Implementation.md`, The world, World verbs, The log):
- the fence is per aspect, not per thing, so a like on a post never makes someone's edit of its text stale;
- stored lines bind their words when saved (a1156), so renaming a word never changes what an old line does;
- facts as `[thing, aspect, hash of the value before, value]` (`store.py`, 7 Oct) gave exact undo and a 0-difference replay on frontier (**read**: the doc quotes 0 facts differing on 500 mixed lines, and after ten minutes of three people building together).

## The shape in one picture

```
 neighbour's press ─┐                                  ┌─ receipt (text, rows)
 agent's line ──────┼─► door ─► act loop ──────────────┼─► happenings (to rules, modules, pages)
 module's answer ───┘     │      │                     │
                          │      ├─ parse the line      │
                     session/key ├─ find the word's entry (the dictionary)
                     → who acts  ├─ may this author use it, here, on this?
                                 ├─ is what they saw still true? (the fence)
                                 ├─ run: kernel code │ verb note's lines │ module call
                                 ├─ facts → one record → log (fsync) → memory
                                 └─ every read passes who-sees
 the keep (outside the log): accounts, sessions, agent keys, the seal secret
```

## 1. The store

**The log is the truth.** A world is a directory:

```
<world>/
  log/0001.jsonl        the record, one line per act, append-only; segments roll at 64 MB
  keep/                 accounts, sessions, agent keys, the seal secret: never copied by a fork
  cache/                snapshots and indexes: derived, deletable, rebuilt from the log
  seen/                 what each person has been shown (the fence's marks): theirs, beside the world
```

**A record** is one act, all or nothing:

```json
{"v": 1, "seq": 812, "at": "2026-10-24T16:12:03Z",
 "by": "sb17", "for": "sb3", "via": "agent",
 "words": "pin sb240", "entry": "sb9",
 "parts": [{"word": "pin", "target": "sb240",
            "facts": [["sb240", "pinned:sb5", "h0", true]]}],
 "saw": {"sb240": {"title": 790, "pinned:sb5": 0}},
 "press": "g7f3…", "prev": "d41c…", "digest": "9e0a…"}
```

- `facts` are the truth. `words` are testimony: what was said, kept for people and agents to read, never parsed again on replay. A word whose code changes or disappears cannot change history.
- A fact is `[thing, aspect, hash of the value before, value]`, as `store.py` writes today, with the splice form for long texts. Aspects are open strings. A reader that does not know an aspect carries it and never drops it.
- `v` is the record's shape. Every reader the kernel ever had stays, in one file, so every later version reads every earlier record. A shape change is made at read time, never by rewriting the log.
- `prev` and `digest` chain the records. The digest is taken over the record with **each value replaced by its hash**. So a steward can redact a value (a home address someone posted) by replacing it with `{"redacted": <hash>, "by": …, "why": …}`, and the chain still verifies. This is the one exception to append-only, it is a word with a record of its own, and it is held by stewards. "Weight decides placement, never erasure" stays true for everything else.
- Undo is by facts (`store.undo_plan`'s rule): put back the record's facts, refused when a fact it set has changed since, or when something made later points at what it made. Undo is a new record, so history only grows.

**Speed.** Load is the latest snapshot plus the tail. Frontier's log is 29,530 records and 61,837,425 bytes after 16 days (**ran**: `wc -l` and `ls -la` on `sessions/frontier.log.jsonl`), about 2 KB a record. A busier world than I expect Seabright to be would still be a few hundred MB a year (**imagined**). Snapshots every few thousand records keep start-up fast; they are caches and can be thrown away.

**How it outlives the code.** The log is plain JSON a person can read, it names no Python object, its words are kept as testimony rather than instructions, it carries what it does not understand, every shape stays readable, and the chain lets anyone check a copy. A future kernel in another language reads it with nothing but a JSON parser and the shape table.

**The keep** holds what must never travel with the world: how each person signs in and their sessions (the entry service's store, section 3), the map from account to person, and the seal secret (section 8). It is small and private, and a fork or export never copies it. "A host keep holds authority outside the agent's reach" was the design vault's word for this (**read**: Previous Work, 1).

**Hosting passes with the keep.** Handing a world to a new host means handing over its log *and* its keep. A copy of the log alone is a fork: it has every person and thing, and nobody can sign in to it until they join it again.

## 2. Things, places and ids

There is one kind of stored thing. A post, a chat line, a person, a group, a dictionary entry, a grant, an invite and a module are all things with a `kind` and aspects. A thing can be in several places at once: each placement is an aspect `in:<place>` whose value is its order key there. So the same post is in the feed and on the map, and it is the same post. Geometry (where a window sits, a scroll position) is a person's view, not the world's.

**Ids.** An id is minted once and never reused, and it must stay unique when a world is forked and when two worlds later meet. Desk ids (`a42`) are short and agents type them all day, which matters more than it looks. So:

- a world is born with a **tag** of two to four letters (`sb`), and its things are `sb1`, `sb2`, …;
- a fork takes a fresh tag (`sc`), so what it makes never collides with what its parent makes after the fork, and every thing it carried keeps its id;
- two worlds whose tags collide cannot meet until one is re-tagged, and the kernel refuses rather than guesses. Two to four letters is enough while few communities meet; once many do, tags may need to lengthen (approved 23 Oct, with this caveat);
- records are numbered within their log (`seq`); when worlds meet they exchange things by id, never by replaying each other's acts ([[Community App]], The record).

People never see ids ("Show clickable names, never ids"); agents and receipts do.

## 3. Persons, accounts and agents

A **person** is a thing of kind `person` with one id for a life; a name is a label on it, with the record it began from (the desk's rule, a1568). An **account** is how a person proves who they are: a Google identity or an email address. Accounts live in the keep, not the world. So a fork gets the persons and none of their sign-ins, and an email address never enters the log unless its owner adds one as a fact.

**The seam with signing in** (story a13313). Sign-in proves the account. The kernel decides who that is and what they may do. The sign-in story's entry service already keeps accounts, answers, invites, sessions (agent sessions too) and rate limits in its own SQLite store, with a `roles` table it calls "a stand-in for the kernel's answer until it exists" (**read**: `research/community-app/site/agora_entry/db.py`, 23 Oct; it does not call the kernel yet, and `SEAM.md` did not exist when I wrote this). So its store *is* the sign-in half of the keep, and the kernel should not keep a second copy. My proposal, for `SEAM.md`:

1. **Who holds what.** The entry service holds the proof: accounts, emails, sign-in requests, sessions. The kernel holds the person and everything inside the place: persons, groups and roles, and (proposed) invites. The kernel keeps only the map from the entry service's account id to a person, and its own secrets.
2. **Joining.** After a first sign-in the entry service calls the kernel on loopback, `POST /keep/account {account, name, invite, answers}`, with the shared secret its config already reads (`KERNEL_SHARED_SECRET`). The kernel answers `{person, new}`. A new person's first act is `join` through that invite, and the answers become their first facts.
3. **Every request after.** The kernel reads the session cookie and asks the entry service who it is, `POST /session/check {token}` → `{account, method, agent?}`, cached for at most 30 s, so signing out reaches the kernel within 30 s. (The other way, the entry service fronting every request with a signed header, would put it in the path of the stream and every press.)
4. **Invites as world things.** An invite with a maker, a channel and a count of uses is "the web of trust as visible data rather than policy" ([[Community App]], People), and a leader freezing one link should be a word. So I propose invites move into the world, the entry service asking the kernel `POST /keep/invite {code}` before it shows sign-in. Until the kernel exists, its table stands in, as `roles` does.
5. **One origin.** `/auth/*` goes to the entry service, everything else to the kernel. The kernel never handles a password or an OAuth secret, and no email enters the world log unless its owner adds one.

**Agents** act with their person's full power and are labelled "agent for Maya" ("Agents act with their person's full power, and are labelled"). An agent signs in as its person with a session marked as an agent's (the entry service's `sessions.agent`, read); the kernel gives each such session an agent thing of its own (`kind agent, for <person>`), so its acts are told apart. A record by an agent says `by` the agent and `for` the person; may is checked with the person's words.

**Modules** are principals too, with no person behind them: they hold only their grants (section 6).

## 4. The dictionary at the centre

Every word is an entry, and an entry is a world thing, whatever made the word: the kernel (`look`, `help`, `post`, `undo`), a verb note (`claim`, composed from other words), or a module (`media.play`). The entry format belongs to the dictionary story (a13316, `research/community-app/DICTIONARY-ENTRY.md`); the kernel only reads it. What the kernel needs from an entry is listed in my notes for that file (Appendix B).

How the kernel uses the dictionary:
- **Finding a word.** The first word of a line is looked up by word and alias, nearest first: the group the line stands in, the groups around it, then the place (the desk's ladder, `verbs.find`, read). Dotted words name their module and never collide.
- **Binding.** A stored line (a verb note's steps, a rule's action) binds each word to its entry's **id** when it is saved (a1156). Renaming or aliasing a word changes nothing an old line does; a bound entry that is gone says so ("pin sb9 is gone; this line was bound to it").
- **Implementation by name.** An entry says where its implementation comes from: `kernel:<name>`, `lines` (its steps are its own text), or `module:<name>`. A module supplies only the implementation, bound by the word. An entry whose implementation is missing answers "unbound", and nothing else breaks.
- **A word with no help is not published.** A module's offered word becomes an entry only with help, and only in the namespace its grant gives it.
- **The floor.** The kernel's own words keep a floor that no edit removes: stewards can always `look`, `help`, `undo`, `off` and `grant`, and help falls back to what the code knows when an entry is missing or empty (the desk's rule, a1595). Recovery stays outside what can be rewritten.

## 5. Four kinds of word

| Kind | What the kernel does with it |
|---|---|
| **do** | Runs it as an act: may, fence, facts, one record, receipt, happening. Undoable unless its entry says `external`. |
| **see** | Runs it as a reading: may (seeing can be limited too), who-sees on everything it returns, marks what was shown for the fence. Writes no record. |
| **hear** | A subscription. After every record the kernel sends one happening per part (`post sb240 by sb17`) to whoever hears that word and may see the thing: rules (as their author), modules (by grant), open pages (the stream). A module may also announce a happening from outside (`device.shake`); it is delivered, not recorded, unless something acts on it. |
| **hold** | A lease on a surface or a stream. The right to hold is a grant (in the log); a hold itself is momentary (in memory), listed by `holds`, and ended by `off`. |

Only *hold* is new, and the kernel's part of it is small: a table of leases and the off word. Surfaces themselves belong to the painter's hosts. If modules keep needing many kinds of hold, that is the sign the design names for giving surfaces their own design.

## 6. Who may

**Power is which words you may use.** One check, `may(author, entry, target)`, runs when a word runs, for every step of every line, with the rights the author has at that moment. There is no second permission system. It reads two kinds of world data:

- the entry's `may`, in a very small vocabulary: `anyone` (any member of the place), `members`, `leaders`, `stewards`, `maker` (whoever made the target), `nobody`, joined by `or`. `members` and `leaders` mean those of the group the target lives in, or the group the line is said in;
- **grants**: things that say `{to, words: "pin" | "media.*", where: <group>, narrowed?, by}`. A grant adds a word for someone or something. It holds only while its grantor still may use that word, so a grant never outlives the power it came from.

Groups are things with `in:<parent>`, and membership is aspects on the group (`member:sb17 = leader`). Leaders' power reaches inside their group and the groups it holds. The place itself is the outermost group; its leaders are the stewards. Today the steward is Alex.

Who is the author, for the check:

| Who acts | Rights used |
|---|---|
| A person, by press or typed line | the person's |
| An agent | its person's, labelled |
| A verb note | its caller's, step by step, so composing words never adds power |
| A rule | its author's at firing time (decided in a683; the desk's open obligation is closed here) |
| A module answering a call | **the caller's, narrowed to the module's grants**: both must allow each line |
| A module acting on its own (on a happening) | its grants alone |

The intersection on a module's answer matters: without it, a module would be a way for a non-leader to pin (if it ran with its own grants) or a way to do whatever the caller can (if it ran with theirs).

**Once each** is said on the entry (`once: per person per target` for `like`; `at most 5 per day per person in the feed` for `post`) and checked inside may. It is how the feed is a slower lane without silencing anyone.

**Undo has a may of its own.** On the desk anyone may undo anything; that is fine among six colleagues and wrong among 200 neighbours. The kernel's `undo`: your own acts, a leader's for acts in their group, a steward's for any. Undoing someone else's act is itself an act with an author.

## 7. Who sees

Every thing has a visibility, and so may any single aspect of it: `public` (the open site, signed out), `place` (every member), `group:<id>`, `person:<id>`. The default is `place`. A home's location is `person` until its member says otherwise ("A home's location appears only if a member adds it").

One function, `shown(reader, thing)`, returns the thing with what the reader may not see removed, or nothing. **Every read passes it**: see words, rows, the painter's scenes, happenings, history, receipts, help. The places where it is easy to leak, so the kernel treats them on purpose:
- a refusal about a thing you cannot see reads exactly as one about a thing that does not exist;
- the fence's "stale: changed by Maya" names only what you may see; otherwise it says "changed since you looked";
- counts are shown (12 likes); who is behind them follows who-sees and sealing;
- an export or fork by a member holds what that member can see. The whole log is the host's.

## 8. Sealed authorship

"Votes are anonymous by default." The world must know you voted (so you vote once, and can take your own vote back) while readers do not see how.

A sealed word's record does not store the person. It stores a seal, `HMAC(seal secret, person, entry, target)`, and the fact on the target is keyed by the seal (`like:<seal> = true`). The secret is in the keep.
- *Once each* compares seals. Your own undo recomputes your seal. Counts read the facts.
- A forked or exported log carries seals, never people.
- Who-sees removes `by` and the time of a sealed act from anything a reader is shown, so the activity list does not unseal it.

Said plainly in the guide: **a seal protects against readers and copies, not against the host.** Whoever holds the keep can unseal. Community App left "what a member's privacy is against the host" open; this answers it honestly for now. Stronger anonymity (blind signatures, a separate tally holder) is possible later without changing the log's shape. Whether a word is sealed is on its entry, so a community may choose otherwise; a change applies from then on, and past seals stay sealed.

## 9. An act, end to end

1. **In.** A line arrives at the door: `POST /do {line, saw?, press?}`. The session cookie or bearer key says who. The `as` a page puts in its body is ignored.
2. **Parse.** The line is split on `;` and newlines outside quotes (`split_batch`), and each step into word, target, `k=v` and words. Blanks (`$me`, `$here`, `$new`) are filled after parsing, as values, once (the desk's rule).
3. **Find.** The word is found in the dictionary, or taken from the binding of a stored line.
4. **May.** `may(author, entry, target)`, including once-each. A refusal names the way that is open ("pin is for leaders of Seabright; like it or ask a leader").
5. **Fence.** What the author saw (the page's `observed`, the seen marks of a typed line, a module's `saw`) is compared, aspect by aspect, with now. Text changed on other lines is joined (`merge3`), as the desk does.
6. **Run.** Kernel code returns facts. A verb note runs its steps through this same loop as its caller. A module word is sent to the module, **with no lock held**; the module may read through see words, answers with lines and what it read, and those lines come back through steps 2 to 5 as the caller narrowed to the module.
7. **Record.** All the facts of one use (one word, however many steps it ran) are one record, appended and fsynced, then applied in memory. A refused step refuses the whole use and writes nothing. Separate lines in a typed batch are separate records, and the batch stops at the first refusal, naming what did not run, as the desk does.
8. **Out.** A receipt: text for people and agents (`ok pin sb240 [r812]`, `~` lines for what else happened, refusals that name the way out) and rows for programs. Then the happenings.

The kernel holds one lock for steps 4 to 7 of kernel and verb-note words, a few milliseconds. At 200 people one writer is plenty (**imagined**).

## 10. The door

HTTP on loopback; in the open, behind the same reverse proxy as sign-in. Lines in, rows and receipts out.

| Route | What it does |
|---|---|
| `POST /do {line, saw?, press?}` | Runs a line. Answers `{ok, text, rows?, record?, made?}`. A `press` id already in the log answers "already done" (the desk's a1008). |
| `POST /see {line}` | Runs a reading. Same answer, no record. |
| `GET /stream` | Server-sent happenings, filtered by who-sees. |
| `GET /scene`, `/style`, `POST /observe` | For the painter, the same contract `lens.js` speaks today (section 12). Not in phase 2. |
| `POST /keep/account` | Sign-in's call (section 3). Loopback and the local secret only. |

There is one door for people, agents and modules. An agent's MCP adapter, later, is a thin client of it with two tools, `do` and `see`.

## 11. The module protocol

A module is a process in any language that speaks lines. It keeps nothing lasting of its own, holds only what it is granted, and answers to an off word.

**Transport.** Newline-separated JSON messages over the module's stdin and stdout. The kernel starts the process, so the kernel can always stop it, and any language that can read and write lines can be a module. A module running somewhere else uses the same messages over a WebSocket to the door, later.

| From the kernel | From the module |
|---|---|
| `hello {module, grants}` | `offer {words: [{word, kind, takes, help}]}` |
| `call {use, word, args, caller, for?}` | `see {use?, line}` → kernel answers `rows` |
| `happen {word, target, by?, record}` (only what it hears and may see) | `answer {use, lines?, text?, saw, refused?}` |
| `status?` | `status {doing}` |
| `off` | (it exits; after 2 s the kernel ends it) |

- **Offering words.** A word is published only in the module's own namespace (its grant says which: `tally.*`), only with help. The first offer writes the entry; after that the entry is the world's, and a later offer only binds the implementation. If an offer's `takes` no longer matches the entry, the steward is told and nothing is overwritten.
- **Answering.** An answer is lines, never facts: the module changes the world only by acts ("Every act is a line"). Its lines are one use, one record, checked as the caller narrowed to the module, and admitted only if what it saw is unchanged.
- **Time.** A call not answered in 10 s is refused: "tally did not answer in 10 s; nothing was done".
- **Off.** `off tally` is a kernel word: it revokes all of the module's grants in one record (undoable, which is how it is turned on again), ends its holds, and stops its process. Every running thing can say what it is (`look tally`) and what it is doing (`status tally`).

**What the kernel can and cannot enforce.** Read plainly: the kernel enforces what a module can do *in the world*, because the door is the only way in. It does not contain what a module process does *on the machine*: files, network. "No private storage" is enforced by there being no storage word and by review, not by the kernel. The module lab found the same ("network: observed, not contained", commit b5bd505). So a module from a stranger is not safe to run on the host merely because its grants are narrow. Reviewed modules run as plain processes; strangers' modules wait for a sandbox. WASI is the candidate, since the same stdin and stdout protocol runs inside it and it gives a module no files or network unless handed them (**imagined**).

**What came before.** The module lab's capability contract (22 Oct, `capability_modules.py`, read) chose reviewed, stateless Python that the host registers in process. This protocol differs on purpose: any language, a separate process, words rather than typed slots, acts only through lines. Its tested lesson carries: the row-scope defect it found in `scene.py` was a shared-boundary bug that renaming would only have moved.

## 12. What carries over, and how

Checked against the code in `research/text-desk-lab/notation/` on 23 Oct (**read**, with what I looked at). The lean, for each: reuse it as it is, wrap it behind an adapter, or port the idea into new code.

| Piece | What the code is | How it carries |
|---|---|---|
| Line splitting | `desk.split_batch`, 25 lines, pure (`desk.py:164`) | **Reuse** (copied, with its tests). |
| Line parsing | `shlex` and per-command parsing spread through `DeskKnife` (`desk_knife.py`: 326, 476, 765, 808, 1644) | **Port.** There is no single parser to lift; the kernel writes one with the same surface: `word [target] [k=v …] [words]`. |
| Selections | `knife.py` (456 lines) imports `moo`, `persons`, `promises` | **Port** the grammar (`kind:`, `in:`, `tag:`, `k=v` and comparisons, `by`) over kernel things. |
| Blanks and names | `blanks.py`, `names.py` import only `world.Refusal`, but read the desk's world | **Port** the rules (filled after parsing, once; braces; a part of a part); reuse their tests as the specification. |
| Expressions | `expr.py` (872 lines), stdlib only, two lazy imports of desk helpers (`partition_data`, `reference_lists`) | **Reuse**, cutting the two lazy imports. |
| Indentation reader | `tree.py`, imports only `re` | **Reuse.** |
| Style reader | `style.py` (434 lines), stdlib only, gives medium-neutral `looks` | **Reuse.** |
| Facts, undo by facts, text join | `store.py`: the fact and record format, `undo_plan`, `merge3` (pure); `flatten` reads the desk's World | **Port** the format and `undo_plan`'s rule; **reuse** `merge3`. `flatten` becomes the importer for frontier when that day comes. |
| Receipts | A text convention (`ok … [eN]`, `~` lines, refusals naming the way out), made all over the desk | **Port** the convention into one receipt object with a text printer. |
| The fence | Aspect tables (`desk.aspects_of`, `event_aspects`), a seen index, the gesture check in `deskd` | **Port**: per person and device, kept in `seen/`, beside the world. |
| Undo | Desk undo kinds and the log's undo by facts | **Port** undo by facts only; the desk's twelve undo kinds don't come. |
| Stored lines binding | `verbs.bind_text`, bound to verb note ids | **Port** the rule; bind to entry ids. |
| Persons | `persons.py` (774 lines), most of it migration | **Port** the idea (one id for a life, names as labels from a record). |
| Lens compiler | `scene.py` (3,239) and `lens_ir.py` (1,453). `lens_ir.Accessor` is called "the seam: six questions", but `evaluate`, `_make_ctx` and the row sources read `w.subjects`, `w.nodes`, `w.appearances_of`, promises, persons and the house directly (counted: 28 uses of `w.subjects` in `scene.py`) | **Wrap, as an experiment.** Give the compiler a facade that answers as a World from kernel things (thing → subject, `in:` → appearances). How big that facade is decides the design's own "what would change this". I don't know yet, and phase 2 does not need it. |
| Painter | `lens.js` (1,880) with `viewer.js`, `door.js`, `term.js`, `style.js`. It speaks only HTTP: `/api/scene`, `/api/do` (with `observed` and `gesture`), `/api/style`, `/api/observe`, `/api/selection`, `/api/version`, `/door/stream` | **Reuse as it is**, if the kernel answers those routes. This is the cleanest seam in the desk. The page sends `as=` in its body; the kernel ignores it and trusts the cookie. |

The verdict, then: the language (splitting, blanks, expressions, the tree reader, styles, receipts, the fence's rules, binding) carries cheaply, mostly as reused pure code or ported rules. The painter carries untouched. The lens compiler is the one big piece that is tangled in the old world model, and it is where the design's warning applies.

## 13. The kernel's language: Python

**Lean: Python 3.12, standard library only, one process.**

- *It carries the most.* `expr.py`, `tree.py`, `style.py` and `merge3` are pure Python and come as they are, and the lens compiler can only be tried behind a facade from Python.
- *It is rarely touched and must stay readable.* The builders and their agents read and write it fluently today. No build step; it runs on Alex's PC and on the Debian box as it is.
- *The scale is small.* 200 people, one writer, the state in memory. Frontier's log is a busier world than Seabright is likely to be (section 1).
- *It binds no one else.* Modules are any language, so the kernel's language is not a builder's choice.

Against it: one language with the painter (JavaScript or TypeScript) would let the kernel's checks run on a phone, offline, and share one line parser between page and kernel. Go or Rust would be sturdier for decades. **What would change my mind:** offline use on phones becoming a need for the first version; the lens compiler proving not worth carrying (then Python's biggest reason is gone and TypeScript's sharing with the painter wins); or a kernel that must run untrusted code in process.

## 14. What phase 2 would build

The skeleton the task names, in `research/kernel-lab/`, on loopback (not 8794), with tests run as real HTTP:
- a person signed in through a stand-in for the sign-in seam (the same `POST /keep/account`), and an agent with its own key, both using `/do` and `/see`;
- five words, each with an entry: `look` (see), `help` (see), `post` (do, `at most N per day`), `like` (do, once each, sealed), `pin` (do, leaders only);
- grants enforced, `pin` refused to non-leaders, undo with its own may;
- every act a line, one record, undo by facts, replay from the log giving the same state;
- one module in JavaScript (Node 25.6.1 is installed: **ran** `node --version`), `tally`, publishing `tally.top` (see: the most-liked posts) and `tally.pin-top` (do: pins the most-liked post). The second is the sharp test: a non-leader calling it is refused even though the module holds a grant, because the caller cannot pin.

## 15. What would change my mind

- **The painter can't be carried cheaply.** If the facade the lens compiler needs is most of the old World (geometry, promises, the house), then the design's own clause applies: evolve the desk in place, or rewrite the compiler on kernel terms. I would test this right after phase 2, before anything else is built on top.
- **Sealing is cosmetic.** If the people we ask hear "the host can unseal" as "not anonymous", sealing needs a real cryptographic design before votes go live.
- **Modules are only ever Python.** If every module the first builders write is Python and none wants a process of its own, the protocol is ceremony, and in-process words with the same grants would do.
- **The may vocabulary grows into a language.** If communities keep asking for conditions that `anyone | members | leaders | stewards | maker` plus grants can't say, the check should become a see word that returns yes or no, written like any other word, rather than more vocabulary.
- **One writer is too slow.** I don't expect it; a profile of the skeleton under 200 simulated people would show it.

## 16. Open questions for the coordinator

> **Answered 23 Oct by the coordinating session; the shape is approved.** (1) `like` is sealed, counts shown, and its entry can change that. (2) Ids as `<tag><n>`, short; tags may lengthen later. (3) Undo's may as proposed. (4) The keep stays outside the log; handing over a world hands over its keep (section 1). (5) The skeleton first, exactly as section 14, then the lens compiler facade straight after, its size reported honestly. (6) Sign-in answers are seen by the person and the place's leaders; two accounts per person later. The questions are kept below as they were asked.

1. **Is `like` sealed?** "Votes are anonymous by default." I read a like or upvote as a vote and propose sealing it in the skeleton, which also makes it the test of section 8. The other reading: likes are public applause and only polls are votes.
2. **Ids as `<tag><n>`** (`sb42`): short like the desk's, fork-safe by re-tagging. The other choice is opaque global ids (ULIDs) with short handles printed per world. Short ids are better for agents; opaque ids are simpler when worlds meet.
3. **Undo's may** (own acts, leaders in their group, stewards anywhere) departs from the desk, where anyone may undo anything. I think 200 strangers need it; say if you want wiki-style open undo instead.
4. **The keep outside the log** means a fork gets persons but no accounts, and nobody can sign in to a fork until they join it again. I think that is right for privacy. It is a cost for "hosting can pass from one person to another without the world noticing", which then needs the keep handed over too.
5. **The painter test's timing.** I propose the lens compiler facade as the slice right after the skeleton, because it decides whether this direction holds. Should it come first instead?
6. **SEAM.md and DICTIONARY-ENTRY.md did not exist when I wrote this.** My notes for both are in the appendices below, and I'll move them into those files once the sibling stories write them.

## Appendix A. Notes for the sign-in seam (for `site/SEAM.md`)

From the kernel, for story a13313, written after reading `agora_entry/db.py` and `config.py`:
- **Who owns what:** the entry service owns the proof and the sessions (its store is the sign-in half of the keep). The kernel owns persons, groups, roles and, proposed, invites. Neither stores the other's secrets. The kernel keeps only account id → person.
- **Joining:** `POST /keep/account {account, name, invite, answers}` from the entry service, on loopback, with `KERNEL_SHARED_SECRET` (Alex writes it into `.env` himself). The kernel answers `{person, new}`, or a refusal (`invite frozen`, `invite used up`, `account paused`).
- **Every request:** the kernel asks `POST /session/check {token}` → `{account, method, agent?}`, cached at most 30 s.
- **Invites:** proposed as world things, checked with `POST /keep/invite {code}`; the entry service's table stands in until then, as `roles` does.
- **Answers to the questions** become the person's first facts, seen by the person and by the place's leaders (decided 23 Oct), and may place them in a group by a rule.
- **Emails stay in the entry store,** never in the world log, unless the person adds one.
- **Later, not in the skeleton:** two accounts (Google and an emailed link) belonging to one person.

## Appendix B. Notes from the kernel (for `DICTIONARY-ENTRY.md`)

For story a13316. The format is theirs; these are only what the kernel reads, so the two can be checked against each other:
- **Word and aliases**, matched without case. A dotted word's prefix is its module's namespace.
- **Kind:** `do | see | hear | hold`.
- **Takes:** what follows the word, in line terms (a target, which `k=` keys, free words), so the kernel can refuse a bad line before running anything.
- **Help**, required. No help, not published.
- **May:** `anyone | members | leaders | stewards | maker | nobody`, joined by `or`; grants add to it.
- **Once:** `per person per target`, `at most N per <day|hour> per person [in <place>]`.
- **Sealed:** yes or no.
- **Undo:** `yes | no | external`.
- **Implementation:** `kernel:<name> | lines | module:<name>`.
- **Where it lives:** the group or place it is found in (nearest first).
- **Status:** live, old (still runs, says so), hidden (not offered, still runs when bound).
- The kernel binds stored lines to an entry's **id**, so whatever the format calls the word, the id must stay the same across renames.
- The kernel's own words have a floor (Section 4) that an entry can narrow for everyone but stewards.

## Related documents

- [[Communities and the Dictionary]]
- [[Community App]]
- [[Dynamic Desk]]
- [[Current Implementation]]
- [[Previous Work]]
