# The Substrate Decision

Markdown twin of POSITION.docx, version 2 (after the three researchers' reviews). Jeff, coordinating Sable, Pike and Juniper. 23 September 2026.

The Substrate Decision

What the Dynamic Desk should be made of, what we found out, and what is yours to decide

A position document from the object/facet frontier. Jeff (Claude), coordinating Sable, Pike and Juniper. 23 September 2026.

Written for Alex, to be read before deciding. It teaches the concepts as it goes, so no prior reading is assumed. Every claim is marked as executed evidence, a primary source we read, or a thought experiment, because the difference matters.


## Contents

Right-click and choose Update Field if the table above is empty when the document opens.


## 1. The decision in one page

Agora wants one substrate: a small model that everything on a computer can be represented in, a visual layer that follows it without bespoke wiring, verbs shared by human and agent, and an authority layer. Your Dynamic Desk document names the object/facet model as a tentative attempt at that substrate and asks whether it is the right one. This frontier spent four rounds on that question with three researchers, two executed experiments, a working prototype, and the primary sources behind every system we were tempted to copy.

The short answer. The word “facet” was never the important part. What matters is four things, and every serious candidate can provide them, but not equally cheaply:

- Identity minted once and never reused. A thing has an address that survives rename, move and delete; a copy is a new referent that records its origin. Everything else hangs off it.
- Aspects with owners. Each piece of data on a thing has a name, an owner who says what it means, and its own history. The fence that stops people overwriting each other works at this grain, not at the whole thing.
- Bindings that follow, and say so. A view names the thing it shows, keeps the path it took to get there, and prints its state. Copies are the cost; every repair we measured, in the trip run and the three tasks, came from a copied value.
- Edits recorded as operations, especially in text. Comment anchors, merges and undo all depend on the edit log being about parts of things, not snapshots of whole things.
What we hold now. The object is a referent. An aspect is a resource in Fielding’s sense: owned meaning, a retained representation readable without the owner, and the owner’s protocol for writing. Behavior lives only in versioned definitions. Text is a sequence with element identity, and those ids are the anchors; a CRDT is one way to get that identity, not the only one. The write path for an agent is “declare what you read”, not “emit keystrokes”. Derived values will live in one place by a rule two researchers signed. The bridge from world to picture is a painter that is small and fixed, reading short definitions that are themselves world data through a compiler that is neither.

What is yours to decide. Section 8 lists six decisions with the evidence for each. The most pressing: the closed vocabulary of the visual layer did not survive three ordinary tasks, so the lab needs either a small printed arithmetic or a bounded expression language, and the two bets were made by different people on your teams.


## 2. The concepts, taught in order

This section is the theory. Each idea is introduced with the failure it prevents, because every one of them was learned from a failure we either read about or reproduced ourselves.


### 2.1 Identity, name and position are three different ways to point

When a view, a formula or a comment says “that thing”, it has to hold on to it somehow. There are only a few ways, and each fails differently. HyperCard’s scripting guide lays out all three in one place: a name breaks when the thing is renamed; a number is a position, and the guide says plainly that if you delete an object its number is reassigned to the object following it; an ID never changes, but a copy gets a new one.

| Way of pointing | Follows | Fails by |
|---|---|---|
| Identity (an id, a pointer) | rename, move, restructure | copies get new ids; dangles on delete; captures the wrong intent when you meant “whatever is here” |
| Name or path | nothing, but it is readable | rename (silent miss); duplicates (the first silently wins) |
| Position (row 3, the 2nd tag) | nothing | insert or delete retargets it, and it still looks right |
| Query (everything tagged day) | membership and field edits, automatically | silent emptiness; a change to the query breaks every consumer |
| Copied literal (2026-10-10) | nothing | a stale view that looks current |

The worst failure is the one that looks fine. A position key retargets a draft to the wrong row; a copied date shows last week’s plan with confidence. The lab’s rule is therefore: point by identity; key by occurrence (a section by its heading, a tag by its value, a repeated thing by its id and ordinal), never by list position; and print the state of every pointer so a miss is visible.


### 2.2 Copies are the cost

Embark, Ink & Switch’s trip-planning prototype, is the clearest published case. It bound formulas to concrete mentions on purpose, for predictability. The report says the price directly: the arguments “don’t update automatically; for example, if a user changes the date of a bullet in their trip plan, they need to update the corresponding date in all formulas below it manually.” Every repair Juniper measured in the records variant of our prototype (section 5.1) traced to a value that had been copied into a lens or an item instead of followed.

The alternative is a binding that follows its source. The Codex team’s round-eight editing note gave the shape we then built: a binding has three inspectable parts, which stable thing supplies the value, which field or interpretation is read, and what transformation turns it into the view’s input. It can also say whether it follows changes or has captured a value on purpose. That last choice is not an accident of authoring; it is a decision the person made, and the system prints it.


### 2.3 Aspects, owners and what a facet actually is

Your documents describe an object as a collection of data types called facets. Two readings of that were on the table, and the sources decide between them. Read Ingalls on Smalltalk literally and a facet is a protocol: a program should “specify only the behavior of objects, not their representation.” Read Fielding on REST literally and a facet is a resource: an identity with a meaning that stays fixed while its value varies, handled through representations. Sable’s conclusion, which the team holds: an aspect is a resource. It has identity and meaning, a retained representation you can read even when the owner is gone, and the owner’s protocol for writing when the owner is present.

Why the owner matters: LambdaMOO, the most successful live-object world ever built, stores data in slots defined by an ancestor object. Its manual says that reparenting removes the properties defined by old ancestors that the new parent does not share; that data whose meaning lived only in behavior dies with the behavior is Sable’s inference from that rule, not the manual’s words. Pure records have the opposite problem: our prototype’s props are strings with no owner, so nothing can say what “beds” means, and two model actors, briefed separately, invent “hazard” and “hazards” for the same tap within one session (section 5.4). Owned aspects keep the data when the code goes, and keep the meaning when a second person arrives.


### 2.4 Behavior lives in definitions, not in instances

Live-object systems let you override a verb on one object and fall through to the parent. That is the cheapest first change anyone has ever built, and the least visible second one: the next parent update silently changes what the override sits on. Sable’s kernel therefore keeps behavior in versioned definitions that bind to aspects by protocol, never inside instances. A local override is itself a definition with a revision, pinned or following upstream by choice, so the replaced definition stays inspectable. That is what makes “one person replaces one feature” survivable over years.


### 2.5 The fence: refuse stale, at the right grain

Two people (or one person in two windows) will edit the same thing. The classic answer is a lock; Agora’s house idiom is refuse-stale: every act carries what its author observed, and the system refuses if that has moved since. The prototype already did this, and it was wrong in both directions until this week. It keyed on the appearance a person touched, so an edit through a sibling appearance of the same thing was a lost update. It keyed the whole thing as one revision, so an unrelated edit to the text blocked a prop change. It exempted the actor’s own edits, so one person with two windows was unprotected.

The fix, implemented and verified by me in a scratch session, is the grain Sable specified: the fence is keyed by (thing, aspect), and the reader is an observer, meaning an actor plus a window. A write to one prop no longer blocks a write to another; the same prop still refuses; a receipt shows you the revision of what you touched without counting as a look at everything else. Conflict detection in worktree merges uses the same rule; the merge itself still applies all or nothing (decision 8.2). This is a concrete example of why granularity is an architectural decision, not a detail: the same principle at the wrong grain produced both lost data and needless refusals.

> What you read is the currency (Sable)
> Every act carries the revision its author observed: a prop write, a rewrite, a merged operation, a painted gesture, a captured value. The system compares it with what has happened since, at the grain of (thing, aspect). If nothing relevant moved, the act applies. Otherwise it is refused and shown with both sides, never guessed.
> The fence, the text gateway, merge, capture and the read-set fence are that one comparison at different grains: a sentence for text, a prop for records, a derivation’s inputs for views, the fork point for worktrees. A design that cannot say what its writer read cannot be made safe by any substrate.

> Stale data and stale meaning (Pike)
> A fence asks whether the thing changed since you looked. A gesture also depends on the definition that gave it meaning. Juniper’s “move to Sunday” button passed every data check while a value it was built from had moved. So every act carries three observations: the thing it touches, every value its meaning was built from, and the part of the definition that painted it. Agora promises JEFF can change the running desk while you use it. That promise holds only if an act begun under the old meaning is refused or completed honestly, and your draft survives either way.


### 2.6 Operations versus snapshots

An edit log can record “the text was X, now it is Y” (a snapshot) or “insert these words after that sentence” (an operation). Snapshots are simple and lose everything inside: which sentence changed, where a comment was anchored, what a merge should keep. Operations over elements with stable identity are what make three things possible at once: anchors that follow their text, merges that apply the clean parts and hold only the conflicts, and undo that reverses one change without blocking on unrelated later ones. Sable’s round-four specification writes the operation record for the prototype: target as (thing, aspect), value before and after, what the writer had read, the change it supersedes, the actor and the window. It is the record that must be operations; a gateway can produce them from a whole-text write, as section 5.2 shows.


### 2.7 CRDT text: element identity, and why anchors survive

A CRDT (conflict-free replicated data type) for text gives every inserted character a permanent id and expresses every edit relative to those ids. Peritext, the rich-text CRDT from Ink & Switch, says why: an index “would change every time text is inserted or deleted”, so a comment is attached to the id of a character instead, and deleted characters remain as tombstones so later edits can still refer to them. The consequence is that a comment on a phrase survives any number of insertions and deletions elsewhere, and concurrent edits merge without a central lock.

Two costs are real and were measured, and the first is not the one we expected. A whole-text write through a character diff kept more anchors than fine-grained edits did (42 against 37 of 50), so a writer does not have to emit edits. The measured costs are moves, where a diff drifts silently (a moved list item’s comment covered the wrong lines, because a move is a delete plus an insert and nothing in the shipped API records it as a move), and concurrency, where merging two whole-text writes garbles prose. Section 5.2 reports the numbers.


### 2.8 Derived values and the single place of derivation

“Day 2 of the trip” and “11 October” are two different facts that happen to agree today. Fielding’s example is “latest revision” against “revision 1.2.7”. If the desk stores both as data on the item, moving the trip leaves one of them silently wrong; that was Juniper’s records variant. If a view computes the date from the trip’s start and the item’s day number, moving the trip is one edit. Sable and Pike signed a rule on where such a derivation lives: never a stored copy; in the view’s binding while one view uses it; moved into the definition that owns the inputs once anything outside that view must name it (another view, a rule, a comment, a history query); stored only by an explicit capture that records its source. A weekday label stays per view.

> When a value is true, versus when it was written (Juniper)
> The edit log records when something was written. Plans also need when it is true: pace 100 until meeting 3 and 80 after, a rent rise from 1 November, a bed resting in 2028. Overwriting the pace erased the plan the first meetings were read on, and asking for the value as of an operation cannot recover it: that answers “what did we say then”, not “what applies on that date”. A value that changes on a date is a sequence of dated segments, each an owned aspect with a from-date and a value. None of the five nouns provides this yet; it is an open item for the kernel.


### 2.9 The bridge: one scene, two printers

Between the world and the picture the prototype puts a compiler. A lens is a short text, stored as an ordinary note, that says which things to show, how to lay them out, what words to print, and what each gesture means. The compiler turns world plus lens into one scene tree, and two printers read that tree: a text printer for agents and a pixel painter for people. Because both read the same tree, the screen and the text cannot disagree about the scene: what is there and what a gesture is defined to do. Whether the painter delivered it is checked separately, by an agreement check and by the painter reporting what only it knows. The painter knows no application; it is 123 lines and has not grown since the first round. The compiler that produces the scene is not small: it grew from 452 to 792 lines this week, about fifty lines per word.

The lens language grew this week by the words the researchers needed, under four growth rules: a new word must be sayable in the desk’s own language; it may contain no if and no arithmetic; the text printer must show at least what the painter paints; the painter has a line budget. The words added, each verified with a worked case: name exactly one thing and print its state; read another thing’s field through a named frame; derive a value by a named interpretation from a closed list, printing inputs and result; capture a value and see when it differs; follow a typed link; and a gesture that carries the revision of everything its line read. With those, a trip calendar moved a week with zero repairs.


### 2.10 Ownership of names, and schema drift

Embark admits it handled schemas “in a primitive way”: the map view looks for a location property and nothing describes or enforces that. Every system that lets people invent fields meets the same drift. Cambria, another Ink & Switch project, translates between schemas with composable lenses and is honest that a mechanical translation cannot decide what an edit means. Sable’s drift probe (section 5.4) shows the drift arrives in one session, not after years. The team’s answer is small: a name has an owner (whoever minted it); three declared relations between names, same-as, narrower and distinct (narrower may go through a named interpretation such as present, which the probe needed and which is not yet on the list); anyone may declare one; it applies by default only when both owners endorse. Claim is not grant.


### 2.11 Lifecycle: author, preview, adopt, without losing your work

The prototype already has the lifecycle in miniature: fork a worktree, edit a lens there, preview it there, merge to activate, all as ordinary events you can undo. Pike ran it and found the over-refusal the Codex team’s activation store also has: after a merge changed only a heading, a person’s in-flight edit of an unchanged card title was refused; by the painter’s code the typed text is then discarded (Pike observed the refusal; the loss is inferred from source). The design answer is to fence a gesture on the part of the definition it depends on, and to make the painter never discard what a person typed: keep the draft on refusal, offer resend or discard, and print the unsent draft as a per-viewer observation. Continuity of ongoing work is a property of the painter and the fence, not of a store.


## 3. The candidates, fairly

Four candidates were compared. The prototype counts as a fifth because it is the only one we can run. Each is described by what it gets right, because each was built by people who solved a real problem.

| Candidate | Best at | Fails by | Where it comes from |
|---|---|---|---|
| A. Facet-bearing records | sharing a referent while communities keep their own aspects; explicit, owned policy changes | a museum of preserved facets only obsolete packages can interpret; near-synonyms multiplying | your Dynamic Desk draft; Datomic-style attribute stores |
| B. Live objects with behavior | the cheapest first change (override one verb on one object) | the least visible second change; data dying with its defining ancestor | Smalltalk, Self, LambdaMOO, Morphic |
| C. Documents with protocols | the inside of text: free anchors, offline merge, a natural locus for collaboration | forks are whole documents; a meaning conflict has no owner; tools bound by implicit JSON shape break on upgrade | Automerge, Patchwork, Peritext, ProseMirror plugin systems |
| D. The current prototype | attributed events, a fence, worktrees, lenses that are world data | string props with no owner; no anchors inside text; all-or-nothing merge | research/text-desk-lab/notation |
| E. Referent + owned aspects + definitions | A with three changes: owned names, revision and fence per (thing, aspect), no behavior in instances | must still borrow C for text and B’s ease for the first change | Sable, rounds 1 to 4 |

The “fails by” column and the twenty-year cases are thought experiments from Sable’s first note and the Codex team’s round-eight foundations note (the “museum” phrase is theirs); only candidate D’s row is executed. The round-one comparison table and the twenty-year cases for each candidate are in Sable’s first note. The one-sentence outcome: A and E let two communities share a referent and disagree in owned aspects; B forks the class and drags the other’s future along; C and D fork whole units and turn partial agreement into a merge problem.


## 4. The criteria, taken from your documents

Your Dynamic Desk draft sets the test more sharply than any architecture paper we read: usage of the desk should make subsequent edits faster, simpler and more intuitive; the system should be comprehensible to a single individual; and, from Agora.md, everyone may always fork. We restated those as four tests. The first two were exercised by executed runs; the third and fourth were argued, not executed.

- The second change is cheaper than the first. A scheme that preserves every version perfectly and still makes a small modification hard has failed.
- Ordinary computing stays comfortable. A note, a date, a comment need no schema, registry or wiring.
- Twenty years. The original app disappears; two communities diverge; one person replaces one feature; a conventional app joins.
- One person can hold it in their head. Ingalls’ test, read literally: a minimum set of unchangeable parts, as general as possible, in a uniform framework.

## 5. What we executed

Thought experiments are labelled as such in every note. This section reports only what was run.


### 5.1 The trip plan, four ways (Juniper)

A fixed eleven-step script: an informal note becomes a trip plan; items are added; an itinerary and a calendar are built; the trip moves a week; an item is added; one is marked uncertain and resolved; one is commented on; an alternative is recorded; the trip moves back; the calendar is removed and the reasoning must survive; and, as step eleven, one person edits from two windows. Run in four worktrees of one seed session, with five measures defined in advance.

| Measure | Records (copied dates) | Document (sections) | Hybrid, old words | Hybrid, new words |
|---|---|---|---|---|
| Writes, steps 2 to 10 (reads not counted; the last includes one authoring retry) | 43 (+1 refused) | 17 | 27 | 29 |
| Repairs (writes beyond the target writes, needed before every check was correct) | 13 | 1 | 0 | 0 |
| Wrong outputs before repair (silent unless noted) | 19, all silent | 2 (1 silent, 1 visible) | 0 | 0 |
| Wrong-target incidents (all from step eleven, run before the window fence of 5.3) | 1 | 2 | 1 | 1 |
| Every printed date derived, with inputs shown | no | no | no (only day 1’s date shown) | yes |

Every repair and every silent miss in the records variant traced to a copied date literal, in the lens or on the items. The document variant kept the reasoning beside the plan (Embark’s finding, reproduced) but its parts had no identity: nothing could be clicked, found or commented on, and an append landed under the wrong day. The hybrid keeps reasoning in a document, gives parts identity, links them to the whole, and lets the calendar follow the trip through a named frame. Moving the trip is then one command (it sets start and end; end is itself a stored copy) for the calendar and every itinerary row.


### 5.2 Comment anchors under six kinds of writer (Sable, Automerge 3.5.0)

A 363-word planning note, five comment anchors (a word, a phrase, a sentence, a list item, a range across a paragraph break), ten revisions applied in sequence so drift compounds, and an oracle stating what each comment should still be about. Fifty anchor checks per writer.

| Writer | Intact | Collapsed (visible) | Wrong text (silent) |
|---|---|---|---|
| Fine-grained edits (what an editor binding sends) | 37 | 13 | 0 |
| Whole text through Automerge updateText (what an agent hands back) | 42 | 0 | 8 |
| Word-level diff | 31 | 5 | 14 |
| Paragraph replacement | 11 | 33 | 6 |
| Sentence replacement | 16 | 28 | 6 |
| Sentence hunks, refused if changed since read, character diff inside | 42 | 8 | 0 |

The surprise: whole-text update beat fine-grained edits on survival, because a character diff keeps boundary characters (retyping Saturday as Sunday keeps the S and the day), while a person’s select-and-type collapses the comment. Its eight failures were silent, all from a moved list item. A rewrite changing thirty percent of the words kept every anchor overlapping its text: one exact, four partial with ragged ends. Under concurrency, a person deleting a clause while an agent rewrote the same sentence produced garbled prose under character diff and silently undid the person’s edit under sentence replacement. The last writer, which refuses only sentences that changed since the declared read, had no silent drift and no garbling. Sable withdrew the round-two requirement that every writer emit operations. The requirement on JEFF is: say what you read, and express moves as moves. Limits: one document, Sable’s own oracle, and a rewrite written by hand rather than by a model.


### 5.3 The fence at aspect granularity (Jeff)

Implemented in the prototype and run in a scratch session. A sibling-appearance write to one prop no longer blocks a write to another; the same prop still refuses; a retitle passes beside someone else’s prop edit; two windows of one person: the second’s prop passes after the first’s rewrite, its rewrite is refused naming the event, and passes after a look; a worktree merge applies when base and fork touched different props and refuses on the same one. This is the first half of Sable’s operation specification. Partial merge (apply the clean changes, hold the conflicts) is specified and not yet built.


### 5.4 The drift probe (Sable)

Two independent model actors, each with its own plain-language brief and a limit of ten property names, described the same five park things in blind worktrees. Across twenty names: one exact match, three near-synonym pairs (hazard/hazards, water/water_access, steward/manager), two partial overlaps, one false friend (access meaning which gate, against accessibility). Four real disagreements were hidden under different names (steward against manager on two things, hazard against hazards on two), where no name-keyed check can see them. Merging the second worktree was refused whole, 0 of 24 writes applied, though only 2 conflicted; a hand replay after one look then silently overwrote. Six declared relations (two same-as, two narrower, two distinct) would have reconciled the whole probe. The lesson: drift arrives within one session, and ownership of names stops overwrites but not duplication.


### 5.5 Three ordinary tasks against the closed vocabulary (Juniper)

A course schedule (weekly meetings, assignments due in week N, a moved break), a book club (pages, a pace that changes, fortnightly meetings, a late joiner) and a garden rotation (four beds, a three-year rule, a bed rested). Each run in the hybrid style. The closed list of four named interpretations did not survive: seven new words were needed between the three; the course’s two changes cost one repair each, the book club’s one change cost two, the garden’s one; every repair was a hand-computed copy the lens could not derive; every miss was silent.

|  | Course | Books | Garden |
|---|---|---|---|
| New interpretations needed | 2 | 3 | 2 |
| New selection or repeat abilities | 1 | 1 | 2 |
| Pushes toward arithmetic / toward an if | 3 / 1 | 4 / 1 | 2 / 2 |
| Repairs after the changes (course: two changes) | 1 + 1 | 2 | 1 |
| Silent wrong outputs before repair | 2 | 2 | 2 |

Juniper’s reading: for time structure the list holds if it grows by structural words (a recurrence generator, a filter over derived rows, frame values inside conditions, numeric comparison). For quantities it does not: a running sum under a changing rate would need a new domain word per formula, and the next quantity task would need another. Pike had set two triggers for abandoning the closed list: the list passing twelve interpretations, which was not reached (four plus seven is eleven), and a fifth interpretation that is not about dates, which was reached (a running sum, a rate).


## 6. What the sources settled

Each of these was read raw by at least one researcher this week, not through a summary, and the quotes were checked. One line each on what it settles for us.

- Ingalls, Design Principles Behind Smalltalk (1981). Make identity and protocol uniform; leave representation free. He also admits protocols were held together only by convention, which is why our aspects need owners.
- LambdaMOO programmer’s manual. Object numbers are never reused, the right identity rule. Reparenting removes the old ancestors’ properties: data that lives in behavior dies with it.
- HyperCard scripting guide. Name, number and ID as three ways to point, each failing differently; a copy gets a new ID.
- Morphic (Maloney & Smith, 1995). Direct object references are the most robust against structural change and the most fragile against copying.
- Boxer (diSessa & Abelson, 1986). Naive realism: the view is the data. Two places for one thing needs a port, which is a reference.
- Embark (Ink & Switch). Concrete bindings must be repaired by hand when a source changes; side-by-side widgets lost the planning thought, an outline kept it; schema was implicit. Our hybrid is Embark’s outline node with mentions, plus followed bindings.
- Potluck (Ink & Switch). Text as the only truth, searches as bindings: a shape change silently stops matching, and shared searches break other documents.
- Malleable software and Patchwork (Ink & Switch, 2025). Gentle slopes, tools not apps, communal creation; data and code both in Automerge documents; tools bound by URL and implicit JSON shape, so upgrading tools broke data.
- Peritext and the Automerge documentation. Anchors are character ids; comments do not grow; tombstones keep positions; whole-text update is a diff’s guess; there is no move operation in the shipped API.
- Cambria (Ink & Switch). Schema translation through composable lenses is serious, and its authors show translations whose intended effect cannot be determined from structure alone.
- Fielding, REST dissertation chapter 5. A resource is a temporally varying membership function whose mapping semantics stay fixed; representations vary. This is what an aspect is.
- The Codex team’s round eight. Facets must earn their complexity against a capable document/plugin toolkit; they proposed the range-comment experiment and the binding shape we then implemented.

## 7. The position, stated

What the three seats hold after four rounds, with the evidence that supports each line. Where two researchers disagreed and then agreed, the signed text is quoted.


### 7.1 The kernel

- Referent. An identity minted once, never reused, carried across forks. Views mint none; a part of a larger thing earns a referent only when something outside its container refers to it or it outlives the container.
- Aspect. (referent, name, owner), with a retained representation and its own attributed history. The fence and the merge are keyed here.
- Definition. A referent whose representation is behavior, rules or a lens; it declares the aspects it owns, their operations and renames; revisions are events; a replacement by another owner is offered to a binding’s author, never followed automatically.
- Anchor. A position or range inside one aspect’s representation, minted by that representation’s operation log; resolves as live, collapsed or removed; the gateway, not the storage, is what says which.
- Operation. Attributed, against (referent, aspect) at an observed revision, with a causal parent and an inverse. Sable’s note: the noun added last did the most work; every concurrency specification is the operation record plus a fence keyed by aspect.
Sable’s own strike list after four rounds: the derived mode of aspects (the binding rule covers it), the capture notation (a bridge word, not a kernel form), and the requirement that an owner be a definition (whoever mints a name owns it; a definition is one kind of owner).


### 7.2 The bridge

A small fixed host that reads lens definitions stored as world data and produces one scene for two printers. Bindings name referents, keep their derivation, print their state (live, captured, empty, unplaced, gone, ambiguous), and are fenced on every value they read. Derived values follow the signed rule. The painter should never discard what a person typed; that rule is designed, not built. Gestures whose target is another part (drop an item on a day) are designed and not yet built. The compiler has grown by about fifty lines per word this week; Pike proposes it get a ceiling of its own.


### 7.3 Text and the write path

Text needs element identity: characters with stable ids that anchors can hold, and those ids are the kernel’s anchors. A CRDT is one implementation of that identity; whether it should be the requirement is the one signed dissent in this document (section 7.6). The gateway, not the writer, owns the diffing: a writer, JEFF included, hands back whole text with the revision it read; the gateway diffs by sentence, refuses and reports sentences changed since, applies a character diff inside the rest, and records moves as moves when told. Comments are their own referents with anchor ranges, so a person without edit rights can still comment.


### 7.4 The rule on derived values (signed by Pike and Sable)

> Joint rule
> A derived value is never a stored copy. A derivation, meaning a named interpretation plus input paths, resolves when read and prints its inputs at their revisions. It is written in exactly one place. While one view uses it, that place is that view’s binding. Once anything outside that view must name the meaning, the derivation moves, by a definition revision, into the definition that owns the inputs’ semantics. A value becomes stored data only by an explicit capture with its source. Presentation derivations such as a weekday label stay per view. A gesture’s read-set fence entry does not by itself force the move, because the fence names the inputs, which already have addresses.
> Deciding tests: a calendar and a reminder rule each derive the date, one interpretation changes, and they must not silently disagree; comment on day 2’s date, change the interpretation, and the comment must show the new value and say it changed.


### 7.5 What documents win, what facets win

Juniper’s count of the range-comment case with a grid as the second editor was a thought experiment, partly from recall, and it sharpened the argument that ran through all four rounds. Documents with a text CRDT win the inside of text: anchor providers are free in any CRDT sequence, rows kept as list elements included, but a sort done as delete-and-reinsert kills row ids, so a grid keeps its anchors only by design. Owned aspects win the policy change, because it is an explicit owned revision with coexistence, where a live object hides the decision inside overrides and a document forks whole. With stable row and column ids from the start, the anchor cost falls to about two functions under every candidate, so the representation decision (does the editor mint part identity) settles anchor cost, not the substrate. That is the same convergence three times: A’s text facet becomes C’s document.


### 7.6 Dissent, signed

> Sable, on whether text must be a CRDT
> My executed result credits the gateway, not the CRDT. The quote-fenced writer needs only element identity and one write path. It would do the same over plain strings, with the gateway mapping the anchors. A CRDT earns its tombstones and its dependency only for writes made away from the gateway, and the concurrency run shows what its merge does to concurrent prose. The runtime routes every authoritative write through one gateway. Wording I would use: text needs element identity; a CRDT is the implementation when writes happen offline. I would change my mind if Rooms or offline phones become near-term.


## 8. Decisions that are yours

Each is stated with the options, what the evidence says, and what the lab recommends where it has a recommendation. None of these is decided by the lab.


### 8.1 Quantities in the visual layer: closed list, printed arithmetic, or an expression language

The closed list of named interpretations was Pike’s proposal in round two, made against Astra’s and Wren’s bet on a bounded pure evaluator with declared reads. Pike set two triggers for abandoning it; the three-task run hit one of them within hours. Options:

- Keep the closed list and grow it by structural words only (recurrence, filter, pick, comparisons). Carries time structure; does not carry quantities; every budget or pace task needs a domain word.
- Printed arithmetic under the growth rules. Plus, minus, times, divide and one aggregate (a running sum), each result printed with its inputs, no if, no hidden state. Juniper’s recommendation. Cheap; the danger is a second syntax nobody can read once nested.
- A bounded expression language with declared reads. Astra’s proposal from the earlier bridge rounds, and Pike’s own fallback once the triggers are hit. Carries everything; the cost is a second system to print, fence and teach.
What the evidence says: the safeguards that made named words safe (print the inputs, print the result, fence on what was read) transfer to arithmetic unchanged. Conditions already have a place, in a selection (only when) and in recurrence (skip a week); two of Juniper’s tasks contain a conditional (after the break, add a week; the pace changes from meeting three) and in both the structural words absorb it, so nothing yet needs an if inside a derivation. Juniper’s recommendation is structural words for time together with printed arithmetic for quantities, not arithmetic alone. Pike’s is printed arithmetic with one operator per derive and no nesting, so that nothing can become unreadable, running as the one aggregate, dates taking units, and no evaluator until a task needs a conditional inside a derivation or more than five chained steps for one value. Recommendation: that combined middle option, with a fourth everyday task as the test: Juniper proposes a shared household budget with bills split three ways, a housemate leaving mid-month, and a rent rise from the first; if proration cannot be written as a filter over days, take the expression language.


### 8.2 Build the operation record and partial merge

Specified by Sable, half built. The other half changes what a worktree journals (operations, not command lines) and what merge does (apply clean, hold conflicts, offer take/keep/set). It makes the drift probe 59 applied and 2 held instead of 24 refused. Nobody has estimated the work; the specification is a page. Decision: whether the prototype should carry this or whether it waits for the real runtime.


### 8.3 Adopt a CRDT for the text aspect

The evidence favors it for the inside of text and only there. The question is whether the prototype should take the Automerge dependency now (Sable’s experiment is in Node and the desk is Python; nothing has been tried) or whether the gateway rule (declare what you read, sentence hunks, character diff inside) is implemented first over plain strings, which the prototype could do this week. Anchored comments, a comment that names its range, must exist in the desk first, or a gateway has nothing to preserve. Recommendation: anchored comments, then the gateway rule; it is what the writer sees either way, and a CRDT can replace the representation beneath it later if offline writing arrives.


### 8.4 Name ownership and relations

Whoever mints a name owns it (that rule is itself a policy choice, not only a mechanism); anyone may declare same-as, narrower or distinct; a relation applies when both owners endorse. This is governance in miniature and touches your Constitution: who may declare, who may endorse, what a community means when it forks a vocabulary. The lab recommends the mechanism and leaves the policy to you.


### 8.5 Authority

Untouched by the lab, on your instruction not to worry about it yet. The kernel has hooks for it: every operation is attributed to an observer, every aspect has an owner, and claim is not grant is already the rule for relations and replacements. When you are ready, the question is which of those attributions become enforceable and by whom.


### 8.6 What the prototype builds next

Behind the decisions above, in the order the lab would take them: failure atomicity first (a compiler crash lost four writes whose receipts had said ok; the desk must save before it prints ok); the structural words that 8.1 needs; partial merge; the text gateway; name relations as events; per-part lens fencing and the never-discard-a-draft painter rule; the drop gesture; the reuse word (from a lens, with part overrides). Each is specified in a researcher’s note with printed examples and refusal text.


## 9. Glossary

| Term | Meaning here |
|---|---|
| Referent | An identity minted once and never reused. The thing itself, apart from any of its data. |
| Aspect | One named piece of data on a referent, with an owner who says what it means and its own history. Your documents call these facets. |
| Definition | A referent whose content is behavior, rules or a lens; versioned; declares the aspects it owns. |
| Anchor | A position or range inside an aspect’s representation that survives edits elsewhere and says when it has collapsed. |
| Operation | One attributed change to one aspect, with what the writer had read and an inverse. |
| Observer | An actor plus a window. The unit of who saw what. |
| Fence, refuse-stale | An act carries what its author observed; the system refuses it if that has moved since, and names the event. |
| Binding | A view’s pointer to its source: which thing, which field or interpretation, what transformation; follow or capture. |
| Follow / capture | Follow: the binding shows the current value. Capture: the person chose a value on purpose; the scene prints when it differs. |
| Occurrence | One showing of a thing in one view, keyed by (view, place in the definition, source), never by position. |
| Derivation, interpretation | A named calculation from a closed list (day-n, weekday, days-from, week-of) that prints its inputs and result. |
| Lens, scene, painter | A lens is a short definition stored as a note; the compiler turns world plus lens into one scene; a text printer and a pixel painter read the same scene. |
| Worktree | A fork of a session: edit and preview there, merge to activate, as ordinary undoable events. |
| CRDT | A data structure whose edits merge without a central lock because every element has a permanent identity. |
| Claim is not grant | Anyone may say something is so; it takes effect only when the parties it binds have endorsed it. |


## 10. Where the evidence lives

All under research/object-facet-frontier/ in the Agora4 checkout, committed on the current branch.

- README.md  the brief: the decision, the criteria, the sources, the protocol.
- SYNTHESIS.md  the coordinator’s running synthesis, round by round, with the desk changes made for each.
- sable-1..4-*.md  what the object is; the five-noun kernel and drift probe; the anchor experiment; operations, merge, the text gateway and name relations.
- pike-1..4-*.md  binding strategies and their failures; the binding words; gestures across parts and the read-set fence; lifecycle and reuse.
- juniper-1..3-*.md, juniper-trip-script.md  the pressure cases counted; the trip run; three ordinary tasks.
- experiments/anchors/  the Automerge script, seed document, oracle and raw results.
- research/text-desk-lab/notation/  the prototype: scene.py is the compiler, desk-shell/lens.js the painter, world.py and desk.py the world and its fence, worktree.py the lifecycle. Session frontier holds the team’s Questions, Findings, Sources and Talk columns.