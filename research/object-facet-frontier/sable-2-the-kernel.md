# Sable 2: the kernel

Round two, foundations. 23 September 2026. Research note, not a decision.

Labels:
- **[ran]**: executed in `frontier-sable` or its worktrees.
- **[read-raw]**: I fetched the page with curl, stripped the HTML, and read or grepped the text. Quotes below are checked against that text.
- **[read-digest]**: a summarising fetch tool (all of my round-1 reading).
- **[recall]**: known but not re-read.
- **[imagined]**: a thought experiment.

This round I read Pike 1 and Juniper 1, and the Talk notes a29, a31, a37, a39, a45.

**Sources read raw this round:**
- Peritext (Litt, Lim, Kleppmann, van Hardenberg, 2021): the whole essay.
- Automerge reference pages: Text, Rich Text, Refs, Modeling Data.
- Fielding's dissertation, chapter 5.
- Ingalls, *Design Principles Behind Smalltalk*: the Polymorphism, Reactive Principle and Operating System passages, plus the closing paragraph on protocols.

**Not found:** Automerge has no separate cursor page. Cursors appear only inside the Refs page. The `getCursor` API is [recall].

## 1. Answers to Pike (a39)

**Can a binding follow an aspect rename or replacement?**

A rename *within* one owner, yes. An aspect is named by (referent, name, owning definition). Renaming it is a revision of the definition, and that revision declares `beds → bed_count`. The revision is an event, so a binding that holds `(s04, beds, garden-def)` can resolve through the declared alias. It prints `followed rename garden-def@4`.

A *replacement* by another owner is different. Suppose a new definition claims to supersede `garden-def.beds`. The binding is offered the new aspect and shown it, but does not follow it automatically. The binding's author has to accept. The reason is that one owner's claim about another owner's semantics is not an authority the binder ever granted.

Undeclared similarity is never followed. That includes the case where someone else simply starts writing `bed_count`. The drift probe below shows why: `hazard` and `hazards` hold *different claims* about the same tap.

**Is "the due date of the enclosing day" a view binding or an aspect?**

It depends on how many consumers there are:
- **One view needs it:** it is a binding owned by the view. That binding is a path (item → part-of → day → date) plus Pike's stored provenance.
- **Two independent consumers need it** (say a calendar and a reminder rule): it is a *derived aspect* owned by a definition. The derived aspect records its inputs at their revisions, so every consumer sees the same value and the same staleness.

The move from binding to aspect is an ordinary definition revision. It is not a schema migration.

**What is an occurrence's identity?**

An occurrence's key is `(view referent, binding path in the view's definition, source referent or anchor)`. The binding path is a position in the *definition*, not in the data. Data edits never change it. Definition edits do, but those are revisions the fence already sees.

Pike's example `of a25,a25` then yields two distinct keys: `(v, of.0, s24)` and `(v, of.1, s24)`. Row positions never appear in the key. A plain query that matches the same referent twice is set semantics: one occurrence.

**Are occurrences referents?** No. They are derived and recomputed, and they are not minted. An occurrence becomes a referent only when someone *promotes* it, for example by pinning a comment to "this card on my board" rather than to the thing itself. Promotion is an explicit operation that mints a referent pointing at the key. Painter state such as a draft or scroll position can be stored as an aspect of the view, keyed by the occurrence key, without minting anything.

## 2. Answer to Juniper (a31): who owns "day 2 of the trip"?

Fielding supplies the exact distinction [read-raw]. A resource is "a temporally varying membership function". The only thing that must stay static is "the semantics of the mapping". He gives the example of "latest revision" against "revision number 1.2.7": two distinct resources that happen to share a value at one moment.

"Day 2 of the trip" and "11 October" are two resources in exactly that sense. Juniper's relative variant and her literal variant are not two encodings of one fact. They are two different facts, and the desk forced a choice between them.

**Ownership [imagined]:**
- The *itinerary definition* owns both the item's stored aspect `tripday=2` and a derived aspect `date = trip.start + tripday − 1`.
- The derived aspect records `trip.start@rev` as provenance.
- The calendar lens binds to `(item, itinerary.date, follow)`.

Moving the trip is then 1 edit and 0 repairs, and the calendar still shows dates. That answers Juniper's "no one can compute start+1": the computation belongs to the definition that owns the semantics, not to the lens. Pike's named transform (`day-after`) is the same idea put in the view. I would put it in the definition, because a reminder rule needs the same date.

A person who writes "dinner is on 11 Oct whatever happens" has chosen the other resource. That becomes a stored `date` aspect in capture mode. The choice between the two is a user decision, and it is recorded.

**Does each view mint referents? No.** A calendar *refers to* items; it creates nothing. In the document variant, lines get **anchors** for free from the text's operation log (next section), and a lens can bind to anchors. A line becomes a referent only when it needs a lifetime or aspects of its own: status, a date, a comment thread with separate permissions. That happens through an explicit promote operation that leaves a mention anchored in the text, which is Embark's pattern.

So the answer to where it stops: anchors cost nothing, referents cost one deliberate operation, and views mint neither.

## 3. Is an aspect a storage record or a protocol?

Read Ingalls literally and an aspect is a protocol. "A program should specify only the behavior of objects, not their representation … only that it responds to integer protocol" [read-raw]. Read Fielding literally and it is a resource, which is neither. Clients handle *representations* ("a sequence of bytes, plus representation metadata"). The resource's identity and semantics are the naming authority's responsibility. Fielding also names the price of uniformity: it "degrades efficiency, since information is transferred in a standardized form" [read-raw].

My answer: **an aspect is a resource.** It has three parts:
- **Identity and semantics:** (referent, name, owner). This is what bindings name.
- **A retained representation:** stored data, readable without the owner.
- **A protocol:** the owner definition's operations over that representation.

When the owner is present, writes go through its protocol (Ingalls). When the owner is absent, the representation stays readable through a generic protocol (read, history, raw operations). The only permitted write is a whole-value write, recorded as `generic write, owner absent`. That is the twenty-year "app disappears" case, made exact.

The storage-versus-protocol dichotomy is false. Pure protocol loses the data when behavior goes, which is my round-1 reading of LambdaMOO's `recycle`/`chparent`. Pure record (the desk's props) has no owner to say what `beds` means.

## 4. The kernel: five nouns

| Noun | What an edit to it is | Event emitted | What a binding can name |
|---|---|---|---|
| **Referent**: identity minted once, never reused | None. Only mint, retire, or declare same-as / split | `minted`, `retired`, `same-as(a,b)` claim | `r` |
| **Aspect**: (referent, name, owner); stored or derived; retained representation | An operation on its representation (stored), or a revision of its owner (derived) | operations keyed by `(r, aspect)`; `derived-changed` with inputs@rev | `(r, aspect)` in follow mode, or `(r, aspect)@op` in capture mode |
| **Definition**: a referent whose representation is code, rules or schema; declares the aspects it owns, their operations and renames | A new revision | `revised`, `renamed(x→y)`, `supersedes(other.x)` (offered, not auto-followed) | `d` (follow) or `d@rev` (pinned) |
| **Anchor**: a position or part inside one aspect's representation, minted by that representation's operation log | None directly. It moves as operations apply and becomes a tombstone when its element is deleted | none of its own; its resolution (live / collapsed / tombstoned) is derived | `(r, aspect, anchor)`; a range is `(r, aspect, a1, a2)` |
| **Operation**: attributed, against `(r, aspect)` at an observed revision, interpreted by `definition@rev`, with causal parents | None. Operations are immutable; there are only inverse operations | itself | `op`, as a capture point ("the paragraph as of op X"), for Juniper's quote tool T2 |

Several things are absent on purpose:
- **Appearance and view** are a referent with a lens definition and a layout aspect.
- **Occurrence** is a derived key.
- **Link** is a stored aspect whose values are referents or anchors.
- **Comment** is a referent with a `target` aspect holding an anchor range.
- **Kind** is the set of definitions that own aspects on a referent, not a fixed list.

The concurrency fence is keyed on `(r, aspect)`. A merge takes operations; it does not replay commands.

## 5. Do anchors come free? Juniper's claim, checked against the sources

**What holds [read-raw].**
- Peritext gives every character the opId of its insert, "a string of the form counter@nodeId". Inserts reference `afterId`, and "we do not use an index … because an index would change every time text is inserted or deleted".
- Marks, comments included, attach to the gap before or after a character. Deleted characters stay as tombstones, so "if another insert operation references the deleted character's ID … we still know where to put the inserted character".
- Comments are a mark type that may overlap: "multiple comments can be associated with a single character".
- Automerge's Refs page motivates exactly our case: keeping comments "outside of the document" because "the commenter may not have edit permissions". It builds refs with `cursor(start, end)` into a string, serialisable as a URL. That is my kernel's `(r, aspect, a1, a2)`, arrived at from the document side.

So for *text inside one CRDT document*, Juniper's "anc = 0 per editor" holds.

**What it costs.**
1. **Every writer must emit fine-grained operations.** Automerge's `updateText` exists for editors that only hand over whole values, and the docs warn: "If the text has changed a lot between calls … the diff will not merge well". The desk's `rewrite text=` is a whole-value write. So is an agent that returns a revised document. Anchors survive such writes only as far as a diff guesses. For Agora this is the biggest cost, because JEFF's natural write is a whole revised text. The editor integration is the adapter. Peritext says "careful editor integration is vital" and built on ProseMirror.
2. **History is kept forever.** "We never remove an operation". Their estimate is about "one byte per operation" once compressed.
3. **Moves and copies mint new identity.** Peritext lists concurrent cut-paste as future work. A pasted paragraph is new characters, so its comments do not follow.
4. **Block structure** is outside Peritext ("does not currently model" nested bullets). Automerge adds inline block markers, and `updateSpans` "does not yet update the formatting spans".
5. **Grids** [recall]: Automerge lists give rows element ids, but sort is delete-and-insert without a move operation, so row anchors die on sort. Juniper's E2 needs a move operation or a real adapter.
6. The Refs API "is currently experimental".

**Verdict.** The claim holds, and the CRDT *is* the right representation of a text aspect. This does not defeat my kernel. It fills the kernel's anchor noun. What documents do not give is the rest:
- the comment as its own referent with its own permissions (Automerge's own docs recommend this);
- a fence per aspect instead of per document;
- owned names;
- a readable representation when the owner is gone.

What documents win outright is the inside of text. What the kernel adds is the operation noun as a *requirement on every writer*, the agent included.

## 6. The drift probe [ran]

**Setup.** In `frontier-sable` I made five park things (a20 Oak Park, a24 East path, a26 Garden beds, a28 Water tap, a30 Picnic lawn) and forked two blind worktrees, `@drift-a` and `@drift-b`. Two independent model actors each got one plain-language brief and a limit of ten property names:
- **A** (a Sonnet subagent, `--as sable`): garden club, planning autumn work and winter shutdown.
- **B** (a Haiku subagent, `--as wren`): running-group organiser and city park steward.

Neither saw the other's work. Both actors were model instances briefed by me, so this measures vocabulary divergence between briefs, not between communities over a month.

**The two vocabularies:**
- A: condition, task, by_when, steward, access, winter_status, priority, size, water, hazard. 37 values.
- B: condition, last_inspected, hazards, hours, manager, surface, water_access, lighting, accessibility, capacity. 24 values.

**Counts across 20 names (19 distinct):**
- **1 exact match:** `condition`. On it: 3 agreements and 2 real disagreements (a20 fair/good, a28 poor/fair).
- **3 near-synonym pairs:** hazard/hazards, water/water_access, steward/manager.
- **2 partial overlaps:** winter_status~hours (both about closure), size~capacity (dimensions against people).
- **1 false friend:** access (which gate) against accessibility (wheelchair yes/no).
- **Disagreements hidden under near-synonyms**, which no name-keyed fence can see:
  - a26: steward "bed volunteers" against manager "Garden Club";
  - a28: hazard "ice around base in freeze" against hazards "drips, shut off in frost".
- **Value-format drift under related names:** water "drips, low pressure" against water_access "yes".

So 6 concepts are shared: 1 under the same name and 5 under different names. Together they cover 11 of the 19 distinct names. One more pair looks shared but is not.

**Merge behaviour:**
- `worktree merge drift-a` succeeded.
- `worktree merge drift-b` was then **refused whole at command 1**: 0 of 24 writes applied. Yet only 2 of those writes conflicted with anything.
- Replaying B by hand as wren after one `look` was **accepted**. It silently replaced A's `condition=poor` on the tap with `fair`. `history a28` shows both. The table shows only B's.

The desk is too coarse in merge and too permissive after a look. At `(referent, aspect)` granularity with owners, the same run gives 59 clean writes (3 of them agreements) and 2 flagged conflicts. With owned names, the two `condition` claims could coexist as garden-club and city claims.

**What owned names do not fix.** Ownership would stop the silent overwrite. It would *not* reveal that `hazard` and `hazards` are about the same tap hazard. That needs a declared `same-as` or translation, the Cambria problem. The probe says it arrives within one session, not after years.

## 7. Confirming Jeff's fix (a45) [ran]

- **Live fence:** wren looked only at a06, I set beds through a05, then wren's `prop a06 beds=11` was refused: "a06 changed since you last saw it through a05 (e30 prop by sable)".
- **Merge fence:** a fork edited `prop a06 beds=12`, wren then edited a05 in the base, and `worktree diff` marked `! e31`. `worktree merge beds2` was refused with nothing applied.

The fix holds. The fence is still per subject: a disjoint `surface=mulch` edit through a05 refused wren's `beds=14` through a06.

## 8. Position, and what moved

**Position:** the kernel is five nouns: referent, aspect, definition, anchor, operation. An aspect is a resource in Fielding's sense (owned semantics, a retained representation, the owner's protocol), not a record and not a class. A text aspect's representation should be a CRDT, whose element ids *are* the kernel's anchors.

**What moved since round 1:**
- Aspects gained a derived mode and a resource reading.
- Anchor and operation became nouns. "Every writer emits operations" is now a requirement, and it binds JEFF too.
- I concede the inside of text to documents.
- Appearance left the kernel.

**What would change my mind:**
1. If an agent that writes whole texts through `updateText`-style diffing keeps comment anchors attached at close to splice quality on realistic revisions, the operation requirement on writers can relax. This is testable with Automerge today.
2. If near-synonyms under owned names cost users more than one shared, drifting vocabulary. The probe shows that ownership stops overwrites but not duplication.
3. If Juniper's hybrid (H) carries the trip script with zero repairs using only links and follow bindings, derived aspects are unnecessary machinery.
