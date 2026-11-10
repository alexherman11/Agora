> Design brief written by Claude, 9 Nov 2026, at Alex's request: "what you would give to a super intelligent AI if you wanted it to design the protocol". It describes Agora's kernel as it exists and what Alex wants. It deliberately contains **no proposed protocol design**. Labels: **read** (from source or documents), **ran** (a number printed by a recorded run), **Alex** (his own words, quoted).

# Design brief: turn the Agora kernel into a protocol

## 1. The ask

Design a protocol that the Agora kernel could become. Alex's words (9 Nov 2026):

> "what I'm really after is a way to make it so that the agora Kernel is something that could be loaded on a device and basically just is a protocol almost. Something that may rarely change in small ways, but is moreso a language with which agents can build software and manage it on their own devices such that it can work with and interface with any other Agora speaking software."

His answers to three questions asked while this brief was being prepared:

- **One world or many?** "Both could exist, I think I would want all my devices on one world, but it should be possible for both to exist. My phone and someone elses phone are obviously different worlds, my phone and computer dont have to be the same, but some sort of sign in should allow them to be the same."
- **Views?** "The protocol should not carry views."
- **Who governs it?** "To start me, then stewards, then the public."

Earlier, in the same conversation, he described the goal of updating the system "through itself": "not updating the code underneath, but playing changes through that add functionality", and asked whether "everything is build on the same primitives so basically anything on a computer can be described as something on those primitives".

You are free to keep, change or discard anything described below. Nothing is kept because it was chosen first.

## 2. What Agora is, in one page

Agora is a personal computing environment shared by one person (Alex) and a persistent agent (JEFF), built on one substrate so that anything on a computer can be represented, viewed, changed and extended in the same way. The long-term vision (`docs/Agora.md`) is a malleable, forkable, user-governed system that grows from an operating system into collaborative software and a local social fabric (a map, communities). The axiom: "everyone may always fork. You may fork a tool, a place, a document, even Agora itself."

Today Agora is Alex's Windows desktop, served on loopback port 8810 by a kernel written in Python. The same kernel was first built for a 200-person neighbourhood community (Seabright), most of whom are not AI users. Agents live in it: JEFF, several resident agents, and coding workers they commission.

Design principles from `docs/Dynamic Desk.md` (Alex's document; "Strong" means held):
- "A system should be built with a minimum set of unchangeable parts; those parts should be as general as possible; and all parts of the system should be held in a uniform framework." (Ingalls, quoted at the top)
- Agora stays usable far into the future, even as it grows to cover the full range of applications. Each new capability costs less than the one before.
- One object can appear in many places and is the same object in all of them. Identity is never reused and survives renames, moves and forks.
- Several people and agents can work on the same thing at once without breaking it or losing each other's work.
- Anything you point at stays pointed at.
- Leaning: data keeps its meaning after the program that made it is gone; there is one language to learn, and it applies everywhere.
- Code makes new words; it never replaces the word layer. Every act is a line, whoever wrote the code that made it.
- Ordinary programs and games keep working beside Agora. Never use the host's most fragile mechanisms (drivers, code injection).
- There is always a way back when something breaks. Something independent can restore and recover.
- Two tiers of change: the world tier (lenses, styles, verbs, rules, kinds) changes live and is safe to receive from a stranger because it is data; the source tier is reviewed and travels through a repository. Someone else's change never requires an edit to my source.

## 3. The kernel as it is (read, `src/agora/`)

The kernel's own description of itself (SHAPE.md): "the small part that holds the only powers there are, so that everything above it can be words." The test it was built to pass: **"an act by a neighbour pressing a button, an act by their agent typing a line, and an act by a module answering a call are the same thing to the kernel."**

Size: about 11,000 lines of standard-library Python 3.12. The main files are `kernel.py` (2,341 lines), `words.py` (1,418), `kinds.py` (1,171), `store.py` (160) and `lines.py` (79). Every file opens with a rule: the kernel "never names its tenants: no app, module, person, kind or field name appears in this code except the kernel's own". Names that still appear are listed as debt.

### 3.1 The store: a log of facts

A world is a directory:

```
<world>/
  log/0001.jsonl   the record: append-only, one JSON line per act, fsynced before the act is answered
  keep/            accounts, sessions, agent keys, the seal secret: never copied by a fork
  cache/           snapshots and indexes: derived, deletable
  seen/            what each person has been shown (look-before-act marks)
```

A record:

```json
{"v": 1, "seq": 812, "at": "2026-10-24T16:12:03Z",
 "by": "sb17", "for": "sb3", "via": "agent",
 "words": "pin sb240", "entry": "sb9",
 "parts": [{"word": "pin", "target": "sb240",
            "facts": [["sb240", "pinned:sb5", "0", true]]}],
 "saw": {"sb240": {"title": 790, "pinned:sb5": 0}},
 "press": "g7f3…", "prev": "d41c…", "digest": "9e0a…"}
```

- **Facts are the truth:** `[thing, aspect, hash of the value before, value]`. A fact of length 3 means the aspect is now absent. `State.apply` refuses a fact whose before-hash doesn't match memory (`BrokenLog`).
- **Words are testimony:** what was said, kept for reading and never parsed on replay. A word whose code changes or disappears cannot change history. Replay restores state and never repeats effects.
- **Hashing:** `h(v)` is the first 16 hex characters of SHA-256 over canonical JSON (sorted keys, compact). Absent is `"0"`.
- **Chain:** each record holds `prev`, the digest of the record before it. Its own `digest` is SHA-256 over the record **with every fact value replaced by its hash**. So a steward can redact a value to `{"redacted": <hash>, "by", "why"}` and the chain still verifies. Redaction is the one exception to append-only.
- **Record shape versions:** `v` plus a table of readers (`READERS`). Every reader ever written is kept, and shape changes happen at read time, never by rewriting the log. Readers carry aspects they don't understand rather than dropping them.
- **Optional fields** appear only when true: `for`, `via`, `entry`, `saw`, `press`, `seal` (with `by: "sealed"`), `rule`, `caused_by`, `because`, `work`, `undoes`, `external`, `passive`. Kernel housekeeping records (genesis, new kernel words) have no `entry`.
- A half-written last line, with no newline after it, "never happened" and is dropped on replay.
- **Ran:** 200 simulated people in process gave a post in 1.75 ms and a like in 1.65 ms, fsync included; a full replay of 1,801 records took 74 ms. The old desk's log was 29,530 records and 61.8 MB after 16 days.

### 3.2 Things, ids, principals

- There is **one kind of stored thing**. A post, a person, a group, a dictionary entry, a grant, an invite, a kind declaration, a lens, a module, a window: each is a thing with a `kind` and open-ended aspects.
- **Placement:** an aspect `in:<place>` whose value is the order key there. The same thing can be in many places.
- **Ids:** a world is born with a tag of 2–4 letters, and its things are `<tag><n>` (`sb42`, `dk838`); records are `r<n>`. The patterns are `^[a-z]{2,4}\d+$` and `^r\d+$` (`lines.py`). A fork takes a fresh tag. Ids are short because agents type them all day; people are shown names, never ids.
- **Persons:** one id for a life; names are labels. Accounts (Google, email) live outside the world, in a separate entry service and the keep. The kernel maps an account to a person.
- **Agents:** an agent thing `for` a person, made at sign-in. It acts with its person's full power and is labelled "agent for Maya". Records say `by` the agent and `for` the person.
- **Modules:** processes with no person behind them, unless installed `for` one. They hold only their grants.
- **Authentication:** only the session cookie or a bearer key says who acts. Any `as=` in a request body is ignored.

### 3.3 Lines: the one language

- Grammar: `word [target] [k=v …] [words]`. Lines split on `;` or newlines outside quotes (`split_batch`). Quoting follows shlex, falling back to splitting on spaces.
- `as=<name>` names something a step made, for later steps (`post … as=o; pin $o`). Blanks such as `$me`, `$here`, `$now` and `$today` are filled after parsing, once, as values.
- **Receipts:** `ok pin sb240 [r812]`, with `~` lines for side effects, plus rows for programs.
- **Refusals** name the way that is open: `refused: pin is for leaders of Seabright; help pin says more`, `you have not looked at sb15 yet; look sb15 first`, `stale: sb240 changed since you looked (r10 by Maya); look sb240 again`. A refusal about a thing you cannot see reads exactly like one about a thing that doesn't exist.
- **Batches:** separate lines are separate records, and a batch stops at the first refusal. All the steps of one word's use are one record.

### 3.4 The dictionary

Every word is an **entry**, and an entry is a world thing, whatever made the word: the kernel, a verb note composed of other words, or a module. Entry fields:

| Field | Meaning |
|---|---|
| `word`, `aliases`, `label.<lang>`, `help`, `help.<lang>` | Names and help. **A word with no help is not published.** |
| `word_kind` | `do` (an act) · `see` (a reading, writes no record) · `hear` (a subscription to happenings) · `hold` (a lease on a surface or stream) |
| `from`, `bound` | Where the implementation comes from (`kernel`, `verb`, `module:<name>`) and the name it is asked by. A missing implementation answers "unbound", and nothing else breaks. |
| `takes` | What follows the word. |
| `may` | `anyone members leaders stewards maker lead nobody`, joined by `or`. |
| `once` | `per person per target` · `at most N per day per person` · `at most N per person per <field>`, read from the log on every use. |
| `sealed` | Whether the record hides its author (see 3.6). |
| `undo` | `yes · no · external` |
| `acts_on`, `needs` | The shape the word's code reads (see 3.7). |
| `status` | `live · old · hidden` |
| `lives` | The group or place it lives in. Lookup is nearest first: the line's group, the groups around it, then the place. |

- **Binding:** a stored line (a verb's steps, a rule's action) binds each word to its entry's **id** when it is saved (`steps_bound`, `do_bound`). Renames and aliases never change what an old line does.
- **Namespaces:** dotted words belong to a module (`media.play`). Bare words are world words (`claim`).
- **The floor:** `look`, `help`, `undo`, `off` and `status` stay available to stewards whatever an entry says. Help falls back to what the code knows.
- **Editing entries:** `word-set` and `word-rename` change everything except the implementation, without a source edit.

The kernel's own words today: `look help rows(find) post like pin undo make set forget claim vote role verb rule off status holds word-set word-rename language history kit take rename module grant group dictionary-copy upload attach file-read actions mark kinds alike aspects say clock recent who`. Several of these (`post`, `like`, `pin`, `claim`, `vote`) exist for the Seabright community app.

### 3.5 The act loop (`Kernel.step`, kernel.py:1437)

A line passes these stages in order:
1. **Door:** the session says who acts.
2. **Parse.**
3. **Find the word.** Floor fallback for stewards; then a plain word (`done`, `close`) is resolved to the family member that fits the thing.
4. **Find the thing:** `shown()`; an unseen thing reads as nonexistent.
5. **May.**
6. **Shape:** `guard` checks the word's `acts_on`/`needs` against the thing, then the thing's own `allows.<word>` predicate.
7. **Once.**
8. **Fence:** look before act (see 3.6).
9. **Run:** kernel code, a verb note's steps through this same loop, or a module call.
10. **Commit:** all facts of the use become one record; append, fsync, apply.
11. **Out:** a receipt, then happenings, one per part, delivered to rules, modules and open pages that may hear them.

One lock covers steps 4–10 for kernel and verb-note words, for a few milliseconds. **A module computes with no lock held**; its answer lines come back through the same checks.

### 3.6 Authority, privacy, the fence, undo

- **Who may:** one check, `may(actor, entry, target, group)`. Power is which words you may use; there is no second permission system.
  - **Grants** are things: `{to, words: "pin tally.* hear:window.*", where, only=kind:<k>}`. A grant holds only while its grantor still may use the word. Grants are never edited in place.
  - **Groups** are things with `in:<parent>`; membership is `member:<person> = leader|member` on the group. Leaders of the place are stewards. Today the steward is Alex.

  | Who acts | Rights used |
  |---|---|
  | person | their own |
  | agent | its person's |
  | verb note | its caller's, step by step |
  | rule | its maker's, at firing time |
  | module answering a call | the caller's ∩ the module's grants |
  | module acting on its own | its grants, plus its person's rights if it is installed for one |

- **Who sees:** every thing, and any single aspect, has a visibility: `public · place · leaders · group:<id> · person:<id>`. `shown(reader, thing)` returns the thing minus what the reader may not see, or nothing. Every read passes it: readings, receipts, happenings, history, painted scenes and help. Attachments never widen their parent's visibility (`visibility_of`). `shown()` also derives counts (`likes`, `votes_<option>`, `seats_left`, `claimed_by`); these are hard-coded today.
- **Sealed authorship:** a sealed act's record stores `seal = HMAC(seal secret, person|entry_id|target)` instead of the person, and the fact is keyed by the seal (`like:<seal>`). Once-each compares seals; your own undo recomputes yours; a fork carries seals, never people. Stated honestly in the design: a seal protects against readers and copies, not against the host, who holds the keep.
- **The fence:** per thing and **per aspect**. A typed line needs seen marks: `look` records the last record number of every aspect shown. A page press sends `saw: {thing: {rev, aspects}}`; a module sends `saw: {thing: rev}`. An act is refused if an aspect it writes, or one it read, changed since. A like never makes an edit of the text stale. Your own act counts as having seen what it wrote. Text changed concurrently on other lines is joined by `merge3`.
- **Undo by facts:** `undo [r<n>]` writes a new record that puts back each fact's previous value. It is refused when:
  - a fact it set has changed since, unless every later write was itself undone;
  - something made later points at what it made;
  - the act was `external`;
  - it is itself an undo (there is no redo).

  What rules did because of the act (`caused_by`) goes back with it. Undo's own may: your own acts, a leader's for their group, a steward's for any. History only grows.
- **Refusals are logged** outside the world (`keep/refusals.jsonl`), because "a refusal is the promise that nothing was written".

### 3.7 Kinds: shapes all the way down (`kinds.py`)

- **A shape is a list of needs.** One grammar serves kinds and words:

  | Need | Means |
  |---|---|
  | `start` | has a non-empty start |
  | `start\|starts` | either spelling; the first is the shape's own name |
  | `game=yes` | a marker someone set on purpose |
  | `kind\|post_kind=event` | either aspect has that value |
  | `kind=taskboard-task\|task` | one of these values |
  | `start:time` | a typed part: its value must read as a time |

- **Value kinds** are the bottom: the kernel holds `text number time yes-no link person thing`, each with a check. A declared kind may be a value kind: `make kind=kind name=upvote value=number`.
- **A kind is a named shape:** `make kind=kind name=event needs="title start|starts:time"`.
  - `extends=` inherits needs; `has=` declares optional typed parts; `aliases=` gives synonyms. A kind with no needs and no parents is closed.
  - Only leaders declare kinds with needs. Kinds are referred to by name and **only widen**; a narrowing change or a rename is refused, naming what relies on the kind.
- **Fitting** (`Kinds.fits`), in order:
  1. own kind;
  2. a synonym;
  3. own kind extends it;
  4. kernel machinery never fits by shape;
  5. otherwise every need must be met, as the reader sees the thing;
  6. a **child** kind (one with parents) holds only things declared or marked `is.<kind>=yes`. This came from trials in which all 300 board events became "meetings" structurally.
- **Words declare shapes:** `acts_on=<kind>` and `needs=…`. A word with no shape reaches anything. A word acting on a value kind (`acts_on=upvote`) reaches any thing with such a part and is told which one (`part=`). Plain words pick the family member that fits: own kind first, then the most needs, then the nearest group; a tie asks.
- **Classifying never adds power:** grants (`only=kind:`) and rules match a thing's own kind only.
- **Spellings are read through, never written silently.** The fence counts every spelling.
- **Readings:** `kinds <thing>`, `actions <thing>`, `alike <kind>`, `aspects [loose|suggest]`.
- **Ran:**
  - Before shapes existed, 130,101 replayed lines matched the old kernel exactly.
  - A naming pass on the live world cut loose shared aspects from 87 to 54.
- **Alex's direction**, not yet built: "kinds to be managed by the system they are on, things can bring in their kinds and words when they enter the system, and its the job of intelligent agents to manage how they interoperate"; and "kind is what it's made of, state is the values of its parts" (Alex agreed with this phrasing). Prior-art review found LLM schema matching scores F1 0.47–0.58, and no production mapper commits a mapping on its own.

### 3.8 Composing in the world

- **Verb notes:** `verb <word> steps="<lines>" help="…" [acts_on= needs= may=]`. A do verb's steps make **one** record, which one undo takes back. It runs as its caller, so composing never adds power. Calls nest at most 4 deep. Verb steps have **no conditionals or expressions**; those exist only in lenses (`expr.py`) and in `allows=` predicates (`predicates.py`).
- **Rules:** `rule on=<word> kind=<k> do="<line>"` runs as its maker after each happening the maker may hear, on a rules thread, at most 3 deep. By default rules hear only their maker, the maker's agents and leaders; `by=anyone` must be said.
- **Kits:** `kit <group>` gathers verbs, lenses, styles, rules and kind declarations. `take bundle=<json> in=<group>` places copies in another world **through its ordinary door**, remapping ids, keeping an immutable `origin={world, thing}`. People, posts, votes, contacts, grants, authority and module processes never travel. Taking again collides and refuses atomically; there is no update path.
- **Files:** content-addressed blobs beside the world, never in the log; the cap is 25 MiB by default.

### 3.9 Modules: code that makes words

A module is a process in any language. It speaks newline-delimited JSON over stdin/stdout (`kernel/modules.py`; a JavaScript example is `modules/tally/tally.js`, 90 lines). SHAPE notes that a remote module could "use the same messages over a WebSocket to the door, later".

| From the kernel | From the module |
|---|---|
| `hello {module, id, grants, owner, place, for, home}` | `offer {words: [{word, kind, takes, help, may?, undo?, acts_on?, needs?}]}`, published only in its own namespace and only with help |
| `call {use, word: <bound name>, args, caller}` | `see {use, line}` → `rows {…}`, read as caller ∩ grants |
| | `answer {use, lines, saw}`: lines, **never facts**; admitted only if `saw` still holds. Or `answer {use, external: true, text}`, or `refused`, or `accepted {use}` for slow external work |
| `done {use, ok, record?, made, refused?}` | `do {id, line}` / `see {id, line}`: acting on its own, with its grants |
| `happen {…}`: what its `hear:` grants name and it may see | `happen {word, target?, text?}`: announced, delivered, not recorded |
| `held {…}` | `hold {word}` / `release {lease}` |
| `status?` / `off` | `status {doing}` / exits (killed after 2 s) |

- A call not answered in 10 s is refused.
- A dying module rests 30 s before it is restarted.
- `off <module>` revokes every grant in one undoable record.
- The kernel enforces what a module does **in the world**, not what it does **on the machine**: files and network are "observed, not contained". WASI was named as the candidate sandbox.

### 3.10 The door (HTTP on loopback)

| Route | What it does |
|---|---|
| `POST /do {line, press?, saw?}` | runs an act |
| `POST /see {line}` | runs a reading |
| `GET /stream` | server-sent events: `event: world` (a record number only) and `event: happen` (filtered by who-sees) |
| `POST /api/do`, `GET /api/scene` | the painter's routes |
| `POST /keep/account` | the sign-in seam (shared secret, loopback) |

- A POST from a foreign `Origin` is refused.
- A repeated `press` id answers "already done".

### 3.11 Above the kernel, and outside the protocol per Alex

- **Lenses:** views as text notes, compiled to one scene with two printers, text for agents and pixels for people.
- **A component painter:** reviewed JavaScript components, trusted only by `reviewed_code = sha256(code)`.
- **Themes and styles:** closed vocabularies, with no CSS.
- **The Windows host:** windows are world things reconciled by a module; a window manager; AppBars; a watchdog with a panic chord.
- **The keeper:** owns the sockets and module processes, so the kernel restarts under live requests. **Ran:** 582 requests through a restart, 0 failed.

The protocol need not carry any of this, but these are the protocol's heaviest users today.

### 3.12 Agents, the heaviest users

- **JEFF:** a `person` with his own session, plus a `house-agent` thing saying how he runs: provider, model, prompt, charter, soul. The House module keeps one long-lived model process per agent. That process is Claude Code in headless stream-json mode with **all built-in tools off** and three MCP tools only (`see`, `do`, `lines`), posting each line to the door as himself.
  - He is woken only when addressed, never by a timer.
  - His words are said into the chat that woke him.
  - Every act in a turn carries `because=<record>`, so it traces back to the message that caused it.
  - All the House's message wording lives in a world document (the Agent Book), read by heading on every render.
- **Coding workers:** started in git worktrees for a Board card. They land through the House, which runs checks and fast-forwards `main`.
- **The point for you:** an agent with only see, do and lines can already build and manage software here. The "help teaches itself" work measured a fresh agent on 20 tasks: 12/7/1 (done / partly / failed) before the help rebuild, and 15/5/0 after.

## 4. Lessons the project has paid for (read, `docs/Previous Work.md`)

The kernel is roughly the sixth architecture since late August 2026. Lessons from the earlier ones:

| Lesson | Learned in |
|---|---|
| One authenticated write path; a refused act leaves no trace | Milestone One, Agora3 |
| Replay restores state and never repeats effects | Design vault, Agora3 |
| Refuse stale writes; record what the actor saw | Milestone One, text desk |
| Pin definition revisions; keep the last good version and recovery outside | Lenses, components, Agora3 |
| "Candidate ready" is not "installed"; adoption rechecks inputs | Agora3 yard, parallel work |
| Never wait on another runtime while holding a lock | Agora4 recovery (a live deadlock) |
| Verify the real tool inventory, not mocks | Astra harness |
| Grouped intent needs selection, admission and compensation | Arrangement lab |
| Convergence is not correctness; report conflicting authors | Tessera (three builders composing without a coordinator) |
| A fixed vocabulary can't let JEFF invent abilities | Milestone One (four verbs) |
| Per-app JavaScript and heavy machinery per change (VMs, packages) cause friction | Agora4 apps |
| It carried later features before one claim was tested | The spine attempt |

From the kernel's own tests (SKELETON.md):
- An agent must be announced at sign-in, or a refused line writes a record.
- A module must be asked by its bound name.
- A made thing's happening must name its target, or who-sees never applies to it.
- A rule must not answer its own making.
- A grant reaches a word by any name the word answers to.
- Building a seam from both sides at once crosses.

## 5. Known gaps and frictions (read)

- Verb notes can't compute: no expressions or conditionals, so logic becomes module code.
- Computed values (`likes`, `seats_left`) are hard-coded in `shown()`. Live readings (CPU, the song, a timer) live outside the log in `live.json`.
- `make`/`set` refuse colon facts (`like:`, `vote:`, `claim:`, `contact:`), and sealing is per entry at commit. So the social words can't be rebuilt from general ones yet.
- Kits are snapshots: no updates, no merge, no dependencies.
- Identity is host-vouched: sessions, a shared secret with the entry service, an HMAC seal secret on the host. There are no keys and no signatures.
- The log is one linear chain, written by one process holding one lock.
- Modules are not sandboxed.
- The live painter still imports an archived compiler (`src/text-desk/notation/`).
- No worker pacing governor exists; workers stall and hand off. Workspaces are not cleaned.
- Documentation lags: `docs/Current Implementation.md` still describes the archived desk.

## 6. Constraints on any design

- **Authority:** Alex directs. A new design comes to him first as something he can question; he approves before it is built.
- **Seabright:** about 200 neighbours, mostly not AI users; it must work without AI, and login comes first.
- **Alex's PC and games:** nothing may interfere with his game; no kernel drivers or code injection; everything has an off switch.
- **Visual state:** geometry, scroll and paint stay local to a screen; the world keeps intent and preferences.
- **Words, not code:** every act is a line. People see names, not ids. Refusals name the way out. A word with no help is not published.
- **No preferences in source:** source edits should trend toward zero over time, and no preference (a name, list, size, model or wording) belongs in source.
- **Evidence:** claims are labelled ran, read or imagined, and say what would change the author's mind.

## 7. What we'd like back

1. **The protocol:** what it standardises, what it leaves to implementations, and why. Name its parts and their boundaries.
2. **How Alex's three answers are met:** many devices as one world, joined by sign-in; separate worlds that still interoperate; no views; governance passing from Alex to stewards to the public.
3. **What changes in today's kernel**, piece by piece (keep, generalise, move out, delete), and the order to migrate a live world with thousands of records without losing history.
4. **How it stays rarely-changing** while the language above it keeps growing weekly.
5. **How agents build, ship, update and manage software on it,** across devices and between people, including software that needs real computation or device seams.
6. **How you would know it works:** conformance, a second implementation, the experiments to run first, and what result would make you abandon a part.
7. **The hardest open problems you found,** stated plainly.

Think long. Challenge anything here, including Alex's answers if the evidence points elsewhere, and say so.

## 8. Where to read more (in `C:/Projects/Agora4`)

| Topic | Files |
|---|---|
| Vision and principles | `docs/Agora.md`, `docs/Dynamic Desk.md`, `docs/Agora Constitution.md` |
| History | `docs/Previous Work.md` |
| The kernel's design and built contracts | `src/agora/SHAPE.md` (§17 is what exists) |
| Evidence and test lessons | `src/agora/SKELETON.md` |
| Code | `src/agora/kernel/`: `store.py`, `lines.py`, `kernel.py`, `words.py`, `kinds.py`, `modules.py`, `door.py` |
| Kinds | `docs/design/kinds/kinds-all-the-way-down.md`, `fresh-words-reach-kinds.md`, `kinds-intelligence.md`, `kinds-decisions-for-alex.md` |
| Seams | `src/community/site/SEAM.md` (sign-in), `src/community/DICTIONARY-ENTRY.md` (the entry format) |
| JEFF and the House | `src/agora/modules/house/`, `src/agora/mcp/agora_mcp.py` |
| A module | `src/agora/modules/tally/tally.js` |
| The desktop host | `src/desktop/kernel-desktop/README.md` |
