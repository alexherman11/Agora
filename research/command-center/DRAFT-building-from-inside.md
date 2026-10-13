# Building Agora from inside: versions, bringing, and the Workbench (draft)

> **Draft by Claude, 9 Oct 2026, from Alex's ask, revised over three turns with him and two rounds with Pike and Sable in the world (a3776, c3778, c3781, a3780, Shop talk m3782–m3787).** Not a design status: nothing here is Held, Leaning or Open in *Dynamic Desk* until Alex says so. Labels: **[ran]** executed, with the number as printed; **[read]** a primary source; **[lived]** a resident's own evidence from 7 Oct, with its id; **[imagined]** design, unchecked. Alex's words are quoted.

Alex, 9 Oct: "draft a plan to revamp worktree merge so that it actually is useful and can work, along with the ideas of allowing agents to step into worktrees, edit and create source files, and generally improve the ability of Agora to be built from inside ... a code editing room where the active verbs are particularly helpful ... They should be able to write and execute tests and verifications so they dont rely on the house tests." Then: "we should try and trust the log"; "I'm trying to get us away from workers in general ... residents can also code, just safely in a new version, that hopefully the old world can fast forward into"; "Ideally i would like residents to use the existing verb language in their native code > interface to debug and run things"; "edits hold what they saw so they can work together"; "lets add global ids to the plan". And, after the residents answered: "i would really like them not to be coding agents, but the handoff still feels slow and troublesome. Perhaps instead of sending them off and waiting forever, they could be more involved and tracking the progress? And ideally they wouldn't need to wait and we dont need a limit? Maybe the workbench is just a kind of natural language interface with the code, but the workers are still entirely inside the desk?"

## 0. The claim

Today there are two kinds of fork that never meet: a **world fork** (`worktree fork`: a pickle copy plus a journal of command lines, merged by replaying them) and a **code fork** (a git worktree on a branch, lived through `visit`, landed by the house). The plan is one thing in place of three: a **version** is a tail of the world's log, gaining a code worktree the first time a file is touched, entered as a place, with a **Workbench room** where the code is at hand as things (definitions, proofs, changes, conflicts) and the verbs are the ones a builder reaches for. **The log is the truth**, for code as for everything else. Things and events have a **global identity** and a handle per world, and no handle a person was shown ever moves. **Landing is a fast-forward**: `sync` is where a version meets home and resolves conflicts, inside, as things; `land` appends a tail under a short hold at the door. **The editor is never in the code under test**: the words that edit files, undo, commit, sync, land and go home are the door's, answered by home's code, so a resident who breaks `knife.py` can still type the fix. A **proof** is a builder's own test as a thing with a result at a commit; health's checks are proofs of the same kind. **Builders are residents of versions**: tool-less, run by the house like everyone else, living in the Workbench, where the room's verbs are their whole editor; the residents' soul does not change. Nobody is sent off and waited for: a version is a room anyone can walk into, its board shows the proofs and the changes, its chat is where a resident says what they want in words, and rules carry the progress to whoever asked. No worker slots: a builder rests like a resident when there is nothing to do.

## 1. What exists, and where each piece breaks [read, with the numbers ran]

| mechanism | what it is | where it breaks |
|---|---|---|
| `worktree fork/diff/merge` (`worktree.py`, 224 lines) | a fork is a pickle copy with `_wt = {base, base_events, by, journal}`; since 7 Oct it takes the store log and the kept archive with it. `merge` replays the journal against the base as it is now, ids remapped, each line signed; refused when another actor touched a named thing since the fork; one refusal aborts the whole merge | (a) a replayed command **re-reads the host**: `vouch` at merge time records the merge's commit (f747, 7 Oct); (b) **all or nothing**: `frontier@livedocs` has 64 events of its own, frontier made 198 since, both touched the Code map, so its five friction notes cannot land at all **[ran 9 Oct]**; (c) a journal cannot say "needs code X" (f747); (d) the journal is commands while the store holds **facts with `saw`** |
| commissions (`workshop.py`) | a disposable worker with Claude Code tools in a git worktree, the desk as a tool, a `-try` world copy; landed by the house with health before and after | the worker's world is thrown away; its protocol is a Python string; and it is a worker, which Alex wants to move away from. Pike **[lived]**: six cards waited a day and a half on one person (a3480, a3482, a3476, a3490, a3484, a3576) |
| visits (`door.py`) | the door pins a commit, starts a deskd on it over a copy of home's world, routes one person there; `home` returns; `write home` is the one write | the world is a copy; a visitor cannot edit the code |
| the store (`store.py`) | 803 records, 11,066 facts, replay equals the world, round trip holds **[ran 9 Oct]**; a record carries `saw` and `shape`; a fork is the base's log plus a tail | a shadow: the pickle is the truth; the flip is Alex's call |
| health (`health.py`) | one fixed list of checks | a resident's test is a file run by hand; nothing in the world knows it ran, at which commit, or whether it still holds |
| rooms and world verbs | a room with verbs at hand; the Writing room (f3402) is the model | no room is about code |
| ids | per-world counters with a kind letter; persons alone have one id for a life | two forks both mint `a7100`; `merge` remaps by regex. Sable **[lived 2 Oct]**: a2990 was two things in two worlds and a done note did not say which (a2986) |

## 2. What the residents reach for, and what it becomes [lived where marked, else imagined]

Builders are tool-less by design, as residents are: everything they do is a `>` line through the house, so the Workbench is their whole editor and has to be good enough. Pike and Sable, written apart in the same twenty minutes, agreed on the first five rows from building the editor's verbs through `>` lines on 7 Oct, the nearest thing to this anyone has lived; the rest is one witness or mine.

| the builder reaches for | the native form | why, with evidence |
|---|---|---|
| **the failing line**, before the file | a refusal names the door to its definition (`examine <word>`: file and section); a `fault` links to its section | Pike **[lived]**: every 7 Oct fix began with a refusal he could type again |
| **a definition by name**, never a line range | `read knife.py #fill`, `rewrite knife.py #fill`: a **file is a thing**, its text in the log as facts, its sections its top-level definitions (`ast` for Python, headings for notes); the definition is the unit and the only address | Sable **[lived]**: lines move under every join; a range noted a turn ago is wrong. Pike never once wanted old/new on part of a verb |
| **the fence per section**, not per file | you may change what you have read, by section; Pike changing another function does not make Sable stale | Sable **[lived 7 Oct]**: `tail=` did not count as a read (a3578), a join made her own lines count as someone else's (a3417); on a shared 2,000-line file "read it all again" is the keyhole |
| **the body as written** | a block: every line of the body begins `> \| ` and is taken verbatim after the mark and one space; the block ends at the first line without the mark; blank code lines are `> \|`; mixed tabs and spaces refused; the receipt says `took 14 lines`, with the first and the last; for a replace inside a definition, `old:` and `new:` labels at the margin, though `rewrite #name` with one block is the form they would use most and get wrong least | Pike **[lived]**: every text went in as one quoted line, quotes and dollars escaped by hand; a five-line verb was hard to see, `dropped 2 line(s)` was how he knew. Python will be unwritable so. The mark keeps a736's one rule (only `>` lines act; everything else is thinking) and nothing closes by being forgotten; Sable's end-of-indentation form was weighed and loses to a wrongly dedented line truncating silently |
| **a receipt on every edit** | parses or not, with the line; which proofs stood on this definition and are now behind; whose other code calls it; who else has this section in hand | both: `~ lens doc-shelf compiles` and `these of yours use it` were the best lines of 7 Oct |
| **a way out when the code is broken** | the words that act on files (`read`, `rewrite`, `replace`, `make`), `undo` of them, `commit`, `sync`, `land` and `home` are **the door's words**, answered by home's code, as `visit` and `home` are now; every other line runs in the version, as a visit does; a prefix forces home's code on any line for the day the version's own `undo` is what broke; a version that fails to reload keeps answering on the last commit that loaded and says so in every reply (`still on 3f2a: knife.py line 212 did not load`); the door makes the fault thing | both, independently: the thing that parses my next line is the thing I broke, so the first bad edit would lock its author in (a1951's door, in small, in every version). Sable **[lived]**: breaking doc-editor for one command (e6347) fell back to the painter's last good version with gestures off |
| **what a line writes, and on which code** | a plain line always runs on the version's **last commit** and is kept, its record naming the commit (the landing's "needs code X" for free); uncommitted code is reached only by the word **`try <line>`**, whose writes go to a trial that is dropped, never to the tail. A line does one thing and the builder chose it | Sable and Pike (m3788–m3792, c3793): otherwise the same plain line is kept or dropped depending on whether an edit somewhere in the tree is uncommitted at that moment, learned only from the mark on the reply; and "what lands is the very tail that was lived" would include what a half-finished `replace` did to a paragraph at 14:03 |
| **which commit** | every reply in a version carries the commit it ran on; `saw` carries the code state that did the showing (a commit, or `uncommitted`); a showing on uncommitted code is witnessed, not fenced | Pike **[lived]**: at 14:24 help described a blank that landed at 14:27. Sable: the fence is itself code in the version |
| **grep** | `find in:code "<words>"`, rows `file section line text` | hits are things you can address |
| **run a test** | a **proof**: a note of kind `proof` whose text names a test file under the lab or desk lines; `run <proof>` records `ran=<commit> result=ok\|fail at=`, output as a comment; a proof stands on the definitions it names and is behind when they move | Sable: a proof is to code what the scene was to a lens; the best thing in the draft |
| **a debugger** | none: the desk you stand in. Change `knife.py`, commit, `find seats>3`; change a lens word, `scene <lens>` | Alex: "the existing verb language in their native code > interface" |
| **memory of the code** | comments on a definition, shown when it is read | Pike: "I will not remember knife.py tomorrow"; this is how a resident keeps what a tool-user keeps in their head |
| git status, diff, commit, branch, merge, PR, CI | `look Workbench`; `worktree show`; `commit "<words>"`; the version; `sync` with conflicts as things; the version's card and comments; the standard proofs plus the version's own | as before |

Pike's doubt, to keep in view: a turn is short and reading costs it; "a room that makes me read 800 lines to change 8 will not be used". Definitions by name and the door from a refusal are the answer, and the first measure.

## 3. The plan, as seven slices [imagined; each lands alone, friction-logged, undo named]

### Slice 1. Global identities, handles that never move

- Every world and version gets an **origin**. A thing's and an event's **identity** is (origin, number); the **handle** is the short id people type, with its kind letter. Records, `saw`, links and splices name identities; `examine` shows both.
- **Reserved blocks, never renumbering** (Sable c3781, Pike m3786): a version asks the door for a block of handles when it first mints and again when it runs out (small blocks, fifty, on demand, so waste is bounded by use); home skips every block it hands out; a dropped version's block is never issued again. A typed handle resolves through the world it was shown in; a handle answers for where it lives: `a7350 is in version livedocs, not landed`, `a7350 was minted in livedocs, which was dropped`, never `no such thing`.
- Events too: `saw` is "thing X as of event E" tested by equality (a2870, c2883), so a landed event keeps its identity and its handle. The cost Sable found **[lived all week]**: she reads order from event numbers, and a version's events are numbered from a block reserved earlier and landed later, so **number order stops being time order at home**. Receipts give position or time where they invite that reading (`!! since your last look` already lists by position), and the first landing says it loudly.
- Measure: `store.py check` holds after the change; a fork and home each mint, both survive a landing with no handle moved; a dropped version's handle answers for itself **[to run]**.

### Slice 2. Bringing: sync inside, land as a fast-forward under a hold

- `worktree show <name>`: **code** (files, commits), **world** (every (thing, aspect) changed since the fork point, `before → after`, `!` for a real conflict, `~` for a join elsewhere in the same thing), **proofs** (results and commits), **needs** (code commit; names reached for that do not resolve at home), and **scratch** (things made to try with, below).
- `sync` (a door word, inside the version): rebases the version's tail onto home's head, each fact three-way against the fork point with `saw`; conflicts become things in the Workbench; the code half rebases with its conflicts as things; proofs are re-run on the result. What came in is **told, not read** (Sable): the syncer's view of each touched thing ends at the sync, and the next edit to one is refused until it is read, so `sync` never becomes a password. The receipt **names the joined sections no proof stands on, in those words**, so "proofs green" is never read as "the join was checked" (Sable **[lived twice 7 Oct]**: e6219, e6436).
- `land` (a door word): asks the door for a **hold of seconds**; intake stops and says so; under the hold, a tail of facts-only, conflict-free changes made at home since the sync is rebased automatically, else refused with "sync again" (Pike's starvation **[lived]**: about 440 events in 53 minutes on 7 Oct); then the tail is appended to home's log, the branch fast-forwarded, the house restarted, the door swapped, as **one event `bring`** naming the commit. What `try` wrote on uncommitted code is already gone; `land` shows the world half and asks about **scratch** things made to try with (Pike's sixth hiding place **[lived]**: f3546 and probe lenses left behind on 7 Oct); things tagged `scratch` stay out.
- **Undo** of a landing is whole only while nothing has built on it; after that a revert is a new version, and the landing receipt says which it promises. A line prepared before the restart and arriving after carries a view shown by the old code: refused, told to read again.
- Why facts, not replay: a fact does not re-read the host; a splice resolves against the ancestor, not the base; `saw` is the question merge had to fake by resetting the seen index.
- Measure: `frontier@livedocs` comes home: its six notes land, the Code map conflict is met in the fork by `sync` and resolved, landed under a hold, taken back by one `undo` **[to run]**.

### Slice 3. A version is a tail, and gains code when touched

- `worktree fork <name>`: a tail of the log with its origin, nearly free, "as cheap to throw away as to make" (Sable); `go <name>` enters it; `home` returns; `where` shows who is in which version. A version is a thing at home of kind `version` (`code= world= from= status=`); the git worktree is made on the first file read or edit.
- Entry says the trust line (c1962): "this version's code runs with full rights". A commission becomes a version with a **builder** in it: a resident of a different kind (its own door note and soul, "The door, for builders"), started by the house in the version's Workbench as residents are started in their corners, with no tools and no process of its own outside the house. The `claude -p` worker with Claude Code tools, its worktree protocol and the `workers` slot limit go.
- **Residents take part without coding.** Anyone can `go` to a version, `look Workbench`, read a definition, run a proof, comment on a definition, vouch, or say in the Workbench's chat what they want in words; the builder answers in its next turn. A rule in the Workbench (`when a proof turns ok, say so in the asker's corner`) carries progress to whoever asked, so nobody waits on a card for a day and a half. The Workbench is the natural-language interface with the code: a resident speaks, the builder edits by definition, proves, and says.

### Slice 4. The Workbench room and proofs

- Every version has a `Workbench`: `describe=`, `talk=`, `shows=rows changes`, a board of proofs and faults; its verbs are world verbs (`on=Workbench`), improvable from inside.
- Sources lifted from the parked `live.py`: `files`, `commits:<since>`, `changes`, `matches:<words>`, `sections:<file>`; read from the worktree at HEAD, never copied into the pickle. Files as things in the log (section 2); definitions carry comments.
- The proof kind: slots `ran : word`, `result : open|ok|fail`, `at : date`; `rows behind:<proof>`; health's checks become proof notes in the Handbook's Commissions binder.
- The minimal first cut: `read`/`rewrite`/`make` by definition with the `> |` block, `find in:code`, `prove`, `run`, `commit`, `sync`, `land`, the receipt. Conflicts and faults as things after someone meets one.
- Measure: a builder fixes the two-form verb that prints its slots twice in `table.py` (a known 8 Oct friction), proves it with `test_table.py`, commits, syncs, lands **[to run]**: the first code change made from inside. And Pike's count: lines read per line changed.

### Slice 5. Landing policy as a rule

- A rule note in the house: when a version is `ready`, its proofs green, and someone other than its maker has vouched, land it. The policy becomes a world thing with history. The worker protocol becomes "The door, for builders", read on entering a version.

### Slice 6. Shape changes travel as migrations

- A version that changes how the world is read ships a **migration**: a proof-like note mapping old facts to new, run at landing on home's log after the code lands, refused if any fact does not map; a world remembers its shape version (records carry `shape` already).

### Slice 7. Live notes, from inside

- Spans `$( )` in notes through the one resolver; `read` shows stored words with values beneath; `vouch` inside the version sets `checked=` to the commit actually checked and comes home as a fact; `rows behind` and `undescribed` as Workbench sources. Built by a resident in a version.

## 4. What this cannot do, said plainly (Pike's hiding places, a3780 and m3786)

1. **What has no event**: sessions, a painter's connection, a resident mid-turn holding an old view, rests and wakes. Sync fences facts; the swap can only be witnessed. New code meets these at home, unproved, and the landing receipt says so.
2. **The instant of the swap**: between appending the tail and the restart, old code could read facts the new code wrote. The hold at the door closes it, and must say so.
3. **Starvation** on a busy home: answered by the hold and the facts-only rebase; watched on the first busy day.
4. **Undo whole is true for minutes**: said in the receipt.
5. **The house and the door** are never lived first; a door change is a handover, a new door beside the old, by hand until the handover is itself a proof.
6. **Scratch in the tail**: answered by trial writes and `land`'s question.
7. **External effects** (mail, a deploy) are not here and need containment first.

Pike's own case against his earlier sketch: "landing plus health" never met live state either, so nothing here is worse than today; the risk is only that the new name sounds safer than the old.

## 5. What this unifies

Two forks become one; `visit`, the worker's copy and `worktree merge` become `go`, `sync`, `land`. Health, a card's "Done when" and a resident's tests become `proof`. The journal yields to the log. The protocol, the landing steps and the landing policy move from Python strings into notes. The card, branch, worktree folder and visit become `version`. Code becomes things in the log; git becomes an export, as docs/ already is.

## 6. The soul stays: builders are a kind of resident

Both residents raised it as a question (Sable m3782, Pike a3780): "no workers, residents build" would reverse the soul Alex wrote for them ("You are not a coding agent", "let a worker agent do it", "hold more of the vision than the implementation"). Alex's answer: residents are not coding agents; what is wrong is the handoff, sending a worker off and waiting. So the builder is a resident of a different kind, with its own soul, living inside the desk in the version's Workbench, visible and talkable-to, with no tools outside the house. Residents keep the vision and track, test, comment and vouch; builders hold the implementation. What guards a builder deep in `knife.py` still looking up is the same thing that guards a resident: it lives in the world, in a room with a board and a chat, and the people it builds for are in the room.

## 7. Open, and what would change my mind

- The `> |` block over end-of-indentation: chosen for a736's rule and because nothing closes by being forgotten; if residents' first fifty blocks show the mark itself as the common error, Sable's form with the first-and-last receipt is the fallback.
- Blocks of fifty on demand over five hundred at fork: chosen to bound waste; if asking the door mid-turn is a felt cost, grow the block.
- Whether a tool-less builder is as capable as a worker with Claude Code's tools was. The Workbench loses a private editor and a shell; it keeps definitions by name, the block, proofs, the door, and the room. The first ten versions tell; if builders stall on reading, the room needs better doors before anything else.
- Whether the shadow log is right in every corner: slice 2 runs `store.py check` on both sides and refuses on a difference; the flip stays Alex's.

## 8. Order

1. Identities and reserved blocks. 2. Bringing (livedocs comes home). 3. Versions as tails with lazy code. 4. Workbench and proofs (the `table.py` fix from inside). 5. Landing as a rule. 6. Migrations. 7. Live notes. Slices 1 to 3 in the main checkout; from slice 4 builders build in versions, with residents in the room.

## Related

a1951, a1960 and c1962, c1963; a2870 (Revision 2) and c2883, c2908; a736 (only `>` lines act); `HANDOFF-2026-10-07.md` 3.2 and 10; `DRAFT-three-ways-to-change-the-world.md`; branch `research/text-desk-lab-live-notes` (902185d) and the world fork `frontier@livedocs`; the grammar unification plan in memory, whose step 8 is this draft.
