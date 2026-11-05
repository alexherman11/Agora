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

  Implementation update, 4 November 2026: an external operation may first send
  `accepted {use}`. If its final answer misses that deadline, the receipt says
  `starting; you will hear when the request settles`, with the request identifier.
  Its caller-scoped readings remain open until the final answer. The module
  delivers its eventual outcome itself; late answer lines are never applied.
  A fast final answer still returns normally. This supersedes the timeout
  refusal above for acknowledged external operations.
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

## 17. The contracts, as built (kept current for the builders who depend on them)

*Sections 10 and 11 above are the design; this section is what the code answers today. Builder update, 24 Oct 2026: dictionary edits/translations, filtered record history, carry/drop, composed happenings and dates are built. **Ran:** `79 passed, 30 subtests passed in 109.95s (0:01:49)`; all six proofs passed. Exact proof results and scope are recorded in [[KERNEL-WORDS-HANDOFF]]. Anything not listed here is not built.*

### Running it

- `python research/kernel-lab/start_kernel.py --world <dir> --genesis <file> --port 8810 [--entry http://127.0.0.1:8817 | --dev-entry 8811]`. Loopback only. A taken port fails loudly (on Windows the kernel turns `SO_REUSEADDR` off, which otherwise lets two servers share a port).
- An empty `--world` is founded from `--genesis`: `{tag, name, steward: {account, name}, invites_counted_by: entry|kernel, invites?, groups?: [{name, open?}], things?: [{kind, …aspects}], modules?: [{name, run: [argv], publishes: "ns.*", grants: "words …"}]}`. A module's `run` words that name a file beside the genesis file are made absolute.
- `--dev-entry 8811`: a loopback stand-in for sign-in, reading `<world>/keep/dev-sessions.json` (`{"<token>": {"account": "<id>", "agent": "<label>"?}}`, written by you, never committed). `GET /dev/signin?token=<t>&next=/lens.html?…` sets the session cookie for a page on the kernel's origin. Exists only with `--dev-entry`.
- A process started from a Claude Code session dies with that session. A kernel meant to outlive it must be started outside the session's job (memory: windows-host-gotchas).

### The door

**Web host (builder, 24 Oct; a13322).** `GET /web/` (`/web` also) and `/web/host.js`, `/web/host.css` serve a thin tiling host. Each pane loads the desktop's same `/lens.html?lens=<name>&inspect=0`; lens.js is served unchanged. The shell is public static chrome; all content and layout reads require the existing session through the ordinary door. `panes` reads the person's layout and revision; `pane.split <name> lens=<lens> [axis=row|column]`, `pane.close <name>`, `pane.move <name> to=<name>`, `pane.focus <name>` and `pane.resize <name> ratio=<10..90> [at=root|<binary split path>]` are dictionary words with help. Repeated panes get names such as `Feed 2`. Geometry is a kernel-owned `web-layout` thing with an immutable owner and `sees=person:<owner>`; lenses, posts and groups never acquire geometry. One transaction stores its binary split tree, proportions and focused pane, undoably; page writes carry that layout's revision. Other neighbours cannot read, overwrite or hear its contents. Default Feed/Council/Help geometry is a reading until the person arranges it. The host listens to world notifications and reads its own layout again, keeping simultaneous devices in step. Below 600px it shows only the focused pane, with a switcher and swipes. Lens definitions come from the world, not the host. Proof, exact evidence and limits: [[WEB-HOST]].

| Route | Who | Answer |
|---|---|---|
| `POST /do {line, press?, saw?}` | a session | `{ok, text, rows, records, made, as}`; a refusal is `ok: false` with `refused: …` in `text` |
| `POST /see {line}` | a session | the same, for see words only; no record |
| `GET /stream` and `GET /door/stream` | a session | server-sent events: `event: world` with `{seq}` per record (no content); `event: happen` with `{n, word, target, by, text, record, announced}` for each happening the reader may see |
| `GET /api/scene?lens=<name>&view=painter[&have=<gen>]` | a session | lens.js's scene, built by the desk's compiler from what the reader may see: `{scene, text, events_total, gen}`, `{same, gen}`, or `{refused}` |
| `GET /api/style?name=<style>` · `POST /api/style {text}` | a session · anyone | the style's source and `looks` (the desk's `style.py`) |
| `GET /api/version` | anyone | `{code: "kernel", painter: <hash of desk-shell>, shape: 1}` |
| `POST /api/do {line, observed, gesture}` | a session | a painted press: its desk ids are put back as kernel ids, `observed` becomes `saw`, `gesture` is the press id. `{text, error, line, events_total, as, created}` |
| `POST /api/observe` | a session | `{ok, kept: 0}`: accepted, not kept |
| `POST /keep/account {account, name, invite, answers, agent?}` | the entry service: loopback, `X-Kernel-Secret` | `{person, new, actor}` or 403 `{refused}` |
| `GET /health` | anyone | `{ok, records}` |
| any other `GET` | anyone | a file of `research/text-desk-lab/notation/desk-shell/`, read-only (`/lens.html`, `/lens.js`, …) |

Who acts: the `agora_session` cookie (`__Host-agora_session` on https), or `Authorization: Bearer <token>` for programs; the kernel asks the entry service (`POST /internal/session/check` with `X-Kernel-Secret`, answered `{account: <id>, method, agent, record}`; the older forms are gone since the sign-in story committed the frozen contract, ea15bb2). A POST with an `Origin` that is not the kernel's own is refused. A body's `as` is ignored everywhere.

**Lines.** `word [target] [k=v …] [words]`; `;` or a newline outside quotes separates lines; a leading `do` is accepted. A value with spaces is quoted, and its own `"` and `\` are escaped (`text="say \"hi\""`), as on the desk. Ids are `<tag><n>` (`sb42`); records are `r<n>`.

**Dictionary edits and languages (builder, 24 Oct).** `word-set <entry> help="…" aliases="…" may="…" undo=yes|no|external` edits world metadata, held by stewards, fenced after a look and undoable. It also accepts `takes`, `once`, `sealed=yes|no`, `status=live|old|hidden`, `label.<language>` and `help.<language>`. Empty optional fields remove them; base help cannot be empty. It cannot change implementation (`from`, `bound`, steps or kind). `word-rename <entry> to=<name>` changes its name with the same steward/fence checks. Names and aliases cannot collide with names, aliases or translations already answering in that scope. Dotted names remain in the implementing module's namespace; the pre-existing dotted kernel host words retain their built-in names. World verb notes use bare names, such as `task-done`. The older group-leader `rename` also enforces that namespace boundary.

`language <code>` records the caller's preferred language (for example `es`); their agents use the same preference. `label.es=terminar` is another spoken name of the **same entry**, not a new word; `help.es="…"` is its translated help. `help` and `help <word>` use the reader's language, falling back field by field to the original. A single spoken label is one token. Translations never duplicate identity, permissions, implementation, once-each or undo.

New verb notes save authored `steps` and executable `steps_bound` with entry ids as their heads. Rules similarly save `do_bound` and `on_entry`. Renaming or removing an alias does not re-resolve a stored head. Before changing names/aliases/translations, older saved lines without bindings are bound under their old meanings in the same act. Kits carry the executable heads in their portable `steps`/`do`, remapping entry ids, and carry labels/help translations too; they do not carry two conflicting executable representations.

**History (builder, 24 Oct).** `history <thing>` is a see word: oldest-first rows `{record: "rN", at: <record UTC>, by: <label>, word, facts: [{aspect, value} | {aspect, removed: true}], changes: <printable facts>, sealed}`. It covers direct edits, composed acts, claims and undo, without an app writing duplicate event things. Agent acts say `agent for <person>`; module acts name the module and its person. It writes no record. The current thing must be visible, and fact values pass both current and historical visibility; private older values are not retroactively published. Policy changes which cannot safely be evaluated historically fail closed. Sealed rows say `by=sealed`, expose no facts, identities, seals, hashes or testimony. Other things' facts and raw command text never travel in these rows. The facade supplies the same reading as `of history:$task.id as event, each event`, with `$record`, `$at`, `$by`, `$word`, `$changes`, `$sealed`. The raw `facts` list is available through the see word.

**Carry/drop (builder, 24 Oct).** `/api/do` fills `$carried` only from `observed.carried.item`, translated to a visible kernel thing with an integer painted revision. Nested carried/receiver reads join `saw`. Both participants are checked on their read aspects (whole revision when none are supplied), and the act's ordinary write fence still applies to every fact it changes. These checks run again at admission/commit; the facade does not hold the kernel lock across module calls. A root lane without a bound receiver thing has no receiver revision to check. A stale or missing participant refuses the act and writes no facts. Task board's two actual headless pointer drags prove successful-first/stale-second admission.

**Words** (each has an entry; `help` lists them): `look [<id>]` (a thing's facts as the reader may see them), `help [<word>]`, `rows <kind|any> [field=v …]` (alias `find kind=<k> …`: the things of a kind the reader may see, as rows with `id`, `rev` and `by`, in their `order`, then as made), `post <words> [in=<group>] [about=<id>]`, `like <id>`, `pin <id>`, `undo [r<n>]`, `make kind=<k> [in=<group>] [about=<id>] [as=<name>] [sees=me|leaders|group|place] [k=v …]` (`sees=` may narrow who sees it, never widen: `place` only in the place or an open group; `me` needs a person), `set <id> k=v …` (`k=` alone takes a fact away), `forget <id>`, `claim <id> [phone=<v>]` (a seat on a thing that says `seats=N` and may say `closes=<UTC, 2026-10-29T00:45Z>`; once each; a phone is seen by the claimer and the thing's leaders), `vote <poll> <option>` (sealed, once each; a poll is `make kind=poll options="yes no"`), `role <person> leader|member|none in=<group>` (leaders appoint), `verb <word> steps="<lines>" help="…" [may=…] [kind_of=do|see] [in=<group>]` (a verb note: leaders of the group it lives in make it; it runs as whoever says it; a do verb's steps make one record, which one undo takes back. A one-step verb whose step is a module's word is an alias for it, its own act as if the module's word were said. In a longer verb a module's answer lines join the verb's one act, checked as the caller narrowed to that module. The module reads the world as it was before the verb began, so it can't be asked about what an earlier step made, and the act is refused if a thing it writes changed while the module worked. A module step that changed the outside world makes the whole act one that undo refuses), `off <module>`, `status <module>`, `holds`. `make` and `set` may not write `kind made_by for pinned forgotten sees lives from bound` or `in: like: member: answer: sees. vote: claim: contact:` facts.

**Handles and groups.** `as=<name>` on a step names what it made for later steps of the same line or module answer: `post … as=o; pin $o`. A line's group is its `in=`, else its target's group, else the place; that group's leaders are the `leaders` of `may`. A group made with `open` (genesis `{name, open: true}`) is a public channel: everyone in the place sees its things and counts as its member; its leaders are still appointed with `role`. Note that a leader of the *place* is a steward, so a night's organisers lead an open group, not the place.

**Who sees, in a rule.** `sees` and `sees.<aspect>` rules are `public | place | leaders | group:<id> | person:<id>` joined by `|`; `leaders` means the leaders of the thing's own groups and those above them (for a thing in no group, the place's).

**Rules.** `make kind=rule on=<word> do="<line>"`: after each happening of that word that the rule's maker may hear, and never its own making, the line runs as the maker (`$target`, `$by` filled) on the kernel's rules thread, at most three deep. Its records carry `rule: <id>`, except sealed ones, which would say who. `off=yes` or `forget` stops a rule.

`rule on=<word> kind=<target kind> do="<line>" [name=<text>]` is a helped word for the same thing with a kind filter. `make kind=rule on=<word> of_kind=<target kind> do="…"` is the equivalent make form (its `kind` already names the rule). Hearing binds the entry id, so aliases and later renames keep working. A successfully committed do verb announces its own word once as well as its component words, using the same record, author/seal and visible target. Single-step module aliases retain module authorship and also announce their composed word. See verbs are readings and do not announce acts. No-op compositions with no record produce no happening.

**Kits (builder draft, 24 Oct; a13319).** `kit <group> [name=<text>]` gathers its definitions: verb/dictionary entries (`lives=<group>`), lenses, styles, rules and `kind=kind` declarations placed in it. Module words referenced by those definitions also travel as entries; module processes, paths and grants do not. `post <words> about=<kit>` is ordinary sharing. `look <kit>` returns a portable `bundle` value. `take <kit> in=<group>` places local copies; `take bundle=<quoted JSON> in=<group>` carries that value across worlds through their ordinary doors, without kernel-to-kernel network access. Each copy has immutable `origin={world: <source genesis digest>, thing: <source id>}`. Internal references and kernel-entry ids remap to destination ids; references to live data refuse. A take is one undoable act; collisions refuse atomically. Only definitions in a closed schema travel, never people, posts, polls, claims, votes, contacts, executable configuration or authority. Attribution is supplied by the bundle, not signed authorship. Definition text is authored content, not a personal-data redactor. `rename <entry> word=<name> aliases="<names>" in=<group>` changes only local dictionary names after a look; its bound name still answers. `module <name> run=<quoted JSON argv> grants="<words>"` explicitly installs a module under the local steward's authority; kits cannot install one. `grant <module or widget> words="<words>" [only=kind:<kind>]` (added 24 Oct by Claude, found when the live summarize module needed `model.preview` and no word could widen a running module's grants) gives one more grant as its own undoable act; grants are never edited in place. `help <module word>` says unbound until that module runs. `origin` and `bundle`, and the `kit` kind, are kernel-owned. A group/place used as a target supplies its own permission scope. Single-step module aliases retain their caller's group. Evidence and limits: [[KITS]].

**Hearing.** A happening of an act that made things (`make`, `post`) names the first thing made as its `target` (and all of them as `made`), so who-sees applies to who hears it. Before 23 Oct evening it had none, and a private thing's words reached every page stream and module hearing `make`.

**A world from before a word.** On start, a kernel word the world has no entry for (by its bound name) gets one, in one record of the kernel's own, `the kernel's new words: …`; an alias the world already answers to is left off.

**Time.** Records are stamped with the kernel's clock (UTC); `closes` and `at most N per day` read it. A run may give the kernel a clock of its own (`kernel.clock`, a callable), as Council night does.

`look`/`rows` expose derived `made` (the record that first set its kind) and `changed` (its last touching record), as UTC timestamps. These are readings of actual records, never writable app dates. The painter exposes these as **`$made_at` and `$changed_at`**, avoiding the compiler's reserved `$changed` event frame; `$made` also remains a prop. Lenses receive `$today` (the kernel clock's UTC date, `YYYY-MM-DD`); gestures can use `$today` too. `made`, `changed`, `made_at` and `changed_at` cannot be written by make/set. `history` exposes each record's original `at`. Desk event ordering (`by changed`, `$touched`, `age<`) is still not supplied by the facade; use the explicit timestamp props/history source.

**A painted view.** A lens is a thing `make kind=lens name=<name> text=<lens text>` (or a genesis `things` entry). In it every kernel thing the reader may see is a desk subject: `title` from its title, name, label or the first line of its text; `text`; tag = its kind; its other facts as props, plus `by` (who made it), `pinned` (by whom) and, for a post, `likes`. A fact that names another thing the reader may see (`about=`, `meeting=`, `now=`) becomes that thing's desk id (`s42`, so `meeting=$m.id` compares in a selection) plus `<key>_title` to print. Derived, never written: `claims`, `claimed_by` (names in claim order), `seats_left`, `contacts` (only those the reader may see), and a poll's `votes_<option>` and `votes`; `pinned` is present only on a pinned post, so `by pinned` puts those first. Groups and the place are column surfaces; a thing is placed in each group it is in. Desk ids are fixed by kernel numbers: `sb42` is subject `s42`, its appearances `a336…a343`, and a group `f42`. Not carried into a view: events (`by changed`, `age<`), comments, links, the house's rows, promises.

### Board/file contracts (builder draft, 26 Oct 2026)

Awaiting coordinator review; built and tested on scratch kernels, not installed
in Alex's live desktop. The complete word/file contract, conversion limits and
interface handoff are in `research/community-app/board/README.md` and `NEEDS.md`.

- `POST /upload?in=<group>` accepts authenticated raw bytes with `X-Filename`
  (percent-encoded display name). It runs the dictionary `upload` word's may and
  once; default size is 25 MiB in steward-owned `file-settings.max_bytes`.
  Only the kernel writes a file's hash, size, sniffed MIME and uploader. Bytes
  and extracted text are CAS blobs beside the world, never log payloads.
- `attach <file> to=<thing>` is uploader-owned, fenced and undoable. Uploaded
  files are private until attached. `within=<thing>` on make/post creates a
  kernel-owned visibility dependency; readers must see every ancestor. Hiding,
  deleted parents and cycles fail closed for rows, search, history and files.
- `file-read <file or richer thing> [page=N]` returns converted content, including
  table columns/rows and document pages. `file-result <file> manifest=<hash>` is
  only for the granted files process; it validates addressed bytes and publishes
  a richer thing. Upload and conversion are separate undoable acts. Undo retains
  unreachable CAS bytes; garbage collection is not built.
- `GET /files/<thing>[?variant=thumbnail]` authenticates, rechecks visibility and
  serves nosniff plus sandbox CSP. Active/unknown/text/PDF uploads download;
  images always use cleaned metadata-free PNGs. There is no bare-hash route.
  Widget/component bridge `agora.upload(file, group?)` uses current viewer and
  grants. To invoke automatic conversion its widget also needs files.convert.
- `group [<group>] name=… open=yes|no in=<parent>` creates/edits a group under its
  leaders. `dictionary-copy <kernel entry> word=<name> in=<group>` creates a
  scoped dictionary entry. Group leaders may word-set scoped metadata; place
  entries remain steward-held. `rows` includes a derived groups list.
- `post` accepts ordinary fields and narrow sees=; `make kind=post` applies its
  group's post may/once too. Modules resolve answer words and grants in the
  line's group. Once counts component uses and preceding steps in an act.
  Maker rights include a module-created thing's immutable for person.
- `pin <post> until=<UTC>` records a deadline; expired pins disappear from
  readings without a separate timer act. `vote` works on a thing with options
  and refuses at closes. Counts remain sealed. `forget <thing> reason=…` adds
  a visible `forgotten` notice without exposing hidden contents; undo restores
  the thing and inherited children. `clock` reads the kernel's UTC time.

### The module protocol (stdin and stdout, one JSON object per line, each with a type `t`)

| From the kernel | From the module |
|---|---|
| `hello {module, id, grants: ["words …"], owner, place, for, home}`: `owner` is the place's steward; `for` the person it is installed for, if any; `home` a folder of its own (`<world>/modules/<name>/`) | `offer {words: [{word, kind: do\|see\|hear\|hold, takes, help, may?, undo?}]}`: published only in its namespace, only with help, only if absent (an existing entry is bound by `from` and `bound`, never overwritten) |
| `call {use, word: <bound name>, args: {target, words, kv}, caller: {id, person, name}}` | `see {use, line}` → kernel answers `rows {use, text, rows, refused?}` (read as the caller narrowed to the module) |
| | `answer {use, text?, rows?}` for a see word; `answer {use, lines: […], saw: {<id>: <rev>}}` for a do word (one use, one record, admitted only if `saw` still holds, and, when the word was a painted press, only if what that page showed of a thing the lines write still holds: two leaders pressing Next on one page move the meeting once); lines may use `as=` and `$name`; `answer {use, external: true, text}` for a do word that changed the outside world (a record with words and no facts; undo refuses it); `answer {use, refused}` |
| `happen {n, word, target, by, text, record, announced}`: words its grants name as `hear:<word or ns.*>`, about things everyone in the place may see | `happen {word, target?, text?}`: announced, delivered, not recorded; needs a grant on that word |
| `held {use?, word, lease}` or `held {…, refused}` | `hold {use?, word}`: needs a grant on the word; leases are in memory, listed by `holds`, ended by `release {lease}`, by `off`, or by the process ending; `hold.began` / `hold.ended` are happenings |
| `done {use, ok, record?, made, text \| refused}`: after each answer with lines, whether it was admitted and what it made | `do {id, line, saw?}` → `done {id, ok, text, rows, made, record?, refused?}`; `see {id, line}` → `rows {id, ok, text, rows, refused?}`: the module on its own, outside any call, with its grants alone and, if it is installed `for` a person, that person's rights too; it reads and hears as that person, else as the place |
| `status? {use}` | `status {use, doing}` (2 s) |
| `off` | it exits; after 2 s the kernel ends it. A module that dies rests 30 s before it is started again |

Grants are `words` strings on a grant thing (`"look pin tally.* hear:window.* overlay"`); `*` matches all, and a grant reaches a word by any name it answers to (word, alias, bound name). A grant may say `only=kind:window,pin`: its `make`, `set` and `forget` then reach only those kinds. In a genesis a module may say `"for": "steward"` and `"only": "kind:…"`. A call not answered in 10 s is refused. Every message from a module goes through `ModuleProcess.handle(msg)`, so an extension adds a message type by overriding that one method. What a module says on stderr is kept in `<world>/modules/<name>/stderr.log` (its last 20 lines also go into refusals). Rows the kernel reads for a module during a call count as the caller's look, so the caller may act on them without `look`. Only a read made inside the call counts: a module answering from its own cache must read again with the call's `use` (the desktop's `window.list` found this, 23 Oct).

### Words reach things that fit: shapes (built 28 Oct 2026, Alex's approval of [[fresh-words-reach-kinds]])

`kernel/kinds.py`; tests `tests/test_shapes.py`. A world that declares no shape behaves exactly as before. Ran: a replay of every word on every visible thing of the desk log, and every plain word on every name (130,101 lines), gave the same outcome as the committed kernel except `turn`, which that kernel lacked.

- **Needs.** One grammar for kinds and words: `start` (has it, not empty), `game=yes` (a marker), `start|starts` (either spelling; the first is the shape's name), `kind|post_kind=event` (either aspect has the value), `kind=taskboard-task|task` (either value). Aspect names follow `set`'s rules, so a need can't name a hidden prefix (`contact:`, `answer:`).
- **Kinds are named shapes.** `make kind=kind name=event needs="title start|starts"`; `name=meeting extends=event needs=place` keeps every need of its parents, follows their later widenings, and may extend several. A declaration with needs or extends is made by a steward (the place) or the group's leader (`in=<group>`); a cycle or an unknown parent is refused. Once a word, lens or kind names it, a kind only widens: a change that would need more, or a rename, is refused naming what relies on it. A kind with neither is closed, as before. A word or lens resolves a kind's name in its own scope, upward to the place.
- **Who is what.** A thing is its own kind, its own kind's parents (`a meeting, so an event`), and every open kind whose shape it has (`has title, start`), read as the reader sees it; the kernel's own kinds and the machinery of views never fit by shape. `rows <kind>` and a component lens's `of tag:<kind>` list what fits, read under the kind's names (a thing that says `starts` also shows `start`, with `as` saying so); `rows <kind> exact=yes` lists only its own; `kinds <thing>` and `look` say what else a thing is.
- **Words say the shape their code reads.** `acts_on=<kind>` (that kind's needs) and `needs="<needs>"` (its own), on `verb` notes, on module offers (`{"word", …, "acts_on", "needs"}`; a re-offer refreshes them as it does help, and a steward's `word-set … needs=` stays the world's), and through `word-set`. A verb with a shape takes a thing first (`<id> [<words>]`). A word with no shape reaches anything.
- **One check, in `guard`.** Every place a word meets its thing (a typed or pressed line, a rule, a verb's steps, a module's step inside a verb, a module's answer lines) passes `guard`, which now checks the word's shape first: `rsvp.go acts on an event with seats; Council prep (sm78, a meeting) has no seats`. A module word is refused before its module is asked. Things made by the same act, and settings that name things (`about=`), are not checked.
- **Plain words.** `done <thing>`: family words whose shape the thing has come first, the thing's own kind's word first, then the shape needing most, then the nearest group; a tie asks. Words with no shape come after, by the old rule, which runs unchanged when no candidate has a shape. A name standing for a thing prefers the things the word reaches.
- **`actions <thing>`** (see): the words the reader may say that reach it, grouped by kind, most specific first, then the lenses that show it, and a count of words that take any thing.
- **`mark <thing> <kind>`** (maker or leaders): sets the kind's markers through `set` (its fences, grants and history), or refuses naming what is missing; never a thing's `kind`.
- **Spellings are read, never written silently.** `set` writes what it is told; when the thing already uses another spelling of that aspect under a kind it fits, the reply names it and the line that changes it. (First built as a refusal; the trials showed spellings can be vocabularies, `lane|status`, and the refusal blocked the House's `status=paused`.) A silent rewrite would dodge grant `fields:` limits and undo, which work on the name written, and read an aspect the actor may not see.
- **Classifying never adds power.** Grants (`only=kind:`) and rules (`of_kind=`) still match a thing's own kind.
- **After the trials (28 Oct, [[FRICTION]]):** `acts_on` is met as a list meets a kind (own kind, a kind extending it, or its shape), and a word's own `needs` are checked besides. A member's verb answers a plain word only for its maker (the kernel's, a module's, a steward's or the group leader's words answer everyone; any word answers by its full name), and a group's words only in that group and below. A word with no shape made for the thing's own kind (`window.*` for a window) competes as its own kind's word. One declaration of a kind per name per scope. The kernel's own kinds (`said`, `person`, `word`, …) take no shape and can't be extended. Opening a closed kind is widening; dropping a need is refused while a word acts on the kind without needing it itself. `acts_on` must name a kind declared or present. What relies on a kind but the reader can't see is counted, never named.
- **Retired kernel words.** At start, an entry `from=kernel` whose word this kernel no longer runs is hidden with `retired=yes` (one kernel record), and shown again when a kernel runs it again. On a copy of the live desktop log (ran) the next start retires `is around nearby preview words` and adds `actions`.
- **Held with the graph (28 Oct):** `around`, `nearby`, `preview` and `is` left the dictionary; the House no longer adds wake context (`house.py` `context`, not called); `bonds.py` stays, its tests in `tests/test_bonds_held.py`, skipped. `turn` stays live.
- **Apps given shapes, their hand checks removed:** the House's `house.build|review|land|retry|tell` say `needs="kind=taskboard-task|task"` (`builders.py` no longer checks the kind); the community board's `board.rsvp` says `needs="kind|post_kind=event"` and `board.calendar` `needs="kind|post_kind=event start"`, each finding the thing by `look` when it isn't a post. Each is today's check as data, so a steward widens it in one line, with no reload.

### Kinds, spellings, promises and bonds (built 27 Oct 2026, Alex's approval of [[fresh-kinds-and-bonds]])

> **Superseded 28 Oct 2026** by "Words reach things that fit" above, on Alex's direction (promises "hella wishy washy", kinds "based on the properties of things", hold the graph). Promises, `is`, `inside=`, aspect entries' aliases and read-time fill, make's near-spelling hint, `around`, `nearby` and `preview` are no longer in the kernel; `turn` is. Kept as it was built, for the graph work's return.

`kernel/kinds.py` and `kernel/bonds.py`; tests `tests/test_kinds_and_bonds.py`. A world that uses none of this behaves exactly as before.

- **Aspect entries.** `make kind=aspect name=<aspect> [aliases="a b"] [inside=<wider aspect>] [points_at=<kind>] [means=…]`, in the place or `in=<group>`. A reader in that scope (the place: everyone; a group: its members) sees every thing through `shown()` with the entry's name filled from another spelling (`color=red` also reads `colour=red`) or from a narrower aspect (`reply_to` reads as `about`). `look` marks filled facts `(said as color)`. `set` writes the spelling the thing already uses and says so; `rows <kind> f=v` filters by any spelling. The log is never rewritten. `make` names a near spelling the kind's other things use (difflib, 0.75) and the entry that would make them one.
- **Kinds as needs.** A `kind=kind` declaration may say `needs="start title"` (any thing with those aspects fits), `inside="document"` (every one is also a document; `within` is taken by make's visibility parent), `test=word:<see verb>`, and `promise="<test expression>" promise_says="<why>"`. A kind with needs, a test, something inside it, or something said to be one is *open*: `rows <kind>` lists what fits, each row with `as` (why: `has start, title`, `a meeting, so an event`, `said to be a game by Alex`); `rows <kind> exact=yes` lists only its own. A component lens's `of tag:<kind>` draws what fits the same way (`painter/arrangement.py`). Fitting by needs skips the kernel's own kinds and the machinery of views (`NOT_FITTED`).
- **`is <thing> <kind> [no]`** (maker or leaders, fenced, undoable): writes `is:<kind>` = the person who said it. Only this word writes `is:` (make and set refuse the colon). `kinds <thing>` reads every kind a thing is, nearest first, with why.
- **Words for wider kinds.** A plain verb (`cancel <thing>`) fits a family word by every kind the thing is, not just its own; for one named thing the nearest kind's word wins. A word whose entry says `undo=external` reaches a kind only where it was said (own kind, `is:`, `inside`), never by shape alone.
- **Promises.** `_commit_use` checks every thing an act touches against the promises of each kind it fits (in its groups' scope), on the facts the act would leave. It refuses, quoting `promise_says`, when the promise held before (or the thing is new) and would not after; a thing already broken stays editable; an undo is never refused. The test language gained `num(x)`, `has('f')` and `< > <= >=` on numbers (`predicates.py`, which also takes `row=` for this).
- **Turns.** `turn <agent or person> r<n>|<thing>|done [work=<card>]` (do, `undo=no`, writes nothing; a module with the grant, a steward, or the agent's own person). While a turn holds, every record by that actor (or a module answering its call) carries `because: <seq>` and `work: <id>`. `because` is a bond, not `caused_by`: undoing the line that woke an agent does not undo its work. The house says `turn` when it wakes an agent and `turn … done` when the turn's result comes (`modules/house/house.py` `mark_turn`); the house needs a grant for `turn`, `around` and `nearby` in a world, or it carries on without them.
- **`around <thing> [toward=<direction>|strongest] [limit=3]`**: bonds read from the log (same act, cause and consequence through `caused_by`/`because`, the card worked on, the same hands within 3 minutes, within 10 minutes) and the world (ids and names its aspects point at, typed by an aspect entry's `points_at`; what points back; ids and names its text mentions, one-word names only for people, programs and places; what else mentions the same; shared values; same maker, kind, fitted kind or shape; words for its kinds; maker and leaders; grants and rules that reach its kind; people who can see it; lenses, readings and windows that draw its kinds). Directions: origin, consequence, company, alike, control, audience, shows, then. Weight falls with how many things share the hub (1/log2(1+n)). `strongest` ranks by origin, consequence, company, alike and then only. Every other thing and every record passes who-sees as the reader; sealed acts are skipped. The index is in memory, extended as records come.
- **`nearby [<agent or person>]`**: other actors' acts in the last 30 minutes that change what the subject changed (`is changing it too`), what it read (its seen marks, its turn's line and card: `is changing what you read`), or a thing one step from those (`is working on it, bound up with …`).
- **`preview <line>`**: runs one kernel do word to its facts and stops (`step(mode="preview")`; verb notes and module words refuse). It reports the facts; things that name it by an old name and lenses that filter by it; lenses that read the changed aspects; kinds it would join or leave; what points at a forgotten thing; who sees it; rules and modules that hear the word; a promise it would break. Nothing is written. `set` of a name, title or label also appends one line when other things still name the old one.

## Appendix A. Notes for the sign-in seam (for `site/SEAM.md`)

From the kernel, for story a13313, written after reading `agora_entry/db.py` and `config.py`:
- **Who owns what:** the entry service owns the proof and the sessions (its store is the sign-in half of the keep). The kernel owns persons, groups, roles and, proposed, invites. Neither stores the other's secrets. The kernel keeps only account id → person.
- **Joining:** `POST /keep/account {account, name, invite, answers}` from the entry service, on loopback, with `KERNEL_SHARED_SECRET` (Alex writes it into `.env` himself). The kernel answers `{person, new}`, or a refusal (`invite frozen`, `invite used up`, `account paused`).
- **Every request:** the kernel asks `POST /session/check {token}` → `{account, method, agent?}`, cached at most 30 s.
- **Agents are announced at sign-in:** when the entry service opens an agent's session it says `agent: <label>` on `/keep/account`, so the kernel makes the agent's thing then, not in the middle of its first line (found by the skeleton's tests, 23 Oct; see [[SKELETON]]).
- **Invites:** proposed as world things, checked with `POST /keep/invite {code}`; the entry service's table stands in until then, as `roles` does.
- **Answers to the questions** become the person's first facts, seen by the person and by the place's leaders (decided 23 Oct), and may place them in a group by a rule.
- **Emails stay in the entry store,** never in the world log, unless the person adds one.
- **Later, not in the skeleton:** two accounts (Google and an emailed link) belonging to one person.

## Appendix B. Notes from the kernel (for `DICTIONARY-ENTRY.md`)

> **Superseded 23 Oct** by the format itself, `research/community-app/DICTIONARY-ENTRY.md`, and its "Notes from the kernel", which say how the kernel stores each field. The kernel now reads that format: `from` and `bound` in place of the one implementation field below, and `takes` in its usage notation. Kept as it was first written.

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
