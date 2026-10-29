# The system holds the kinds (draft 0, superseded)

> **Draft 0, by Claude, 28 Oct 2026, late. Superseded by draft 1 in [[kinds-intelligence]].** Not reviewed, not approved, not built. This is my thinking before the reviewers; their findings go in draft 1.
> - **Alex's direction (his words, 28 Oct):** "the system should hold all the kinds, things coming into the system can declare what kinds they support, and it is the job of the system to handle duplicates in the on system dictionary. That is why there has to be an intelligence layer to support multiple kinds. It is literally essential for agora to function."
> - **What it replaces:** shape-reads §6 (producer spellings), and the home of values `means=` and of child-kind membership.
> - **Labels:** **read** (code or source), **ran** (numbers as printed), **imagined** (design).

## 0. The property
**A thing from any app is reached by every word that fits its meaning.** Vocabularies are reconciled once, by the system, not by every reader and not by hand for each pair. Two guards:
- reaching never widens authority;
- every machine judgement is a visible proposal: it carries its reason, the log can reverse it, and someone with standing accepts it.

## 1. What exists today (read)
- **Kinds are things** (`kind=kind`), declared per scope (place or group), with `needs`/`extends` (`kernel/kinds.py`). Since tonight there's one declaration per name per scope, and a nearer one needs a leader.
- **Words are dictionary entries** (`kernel/dictionary.py`), with translated labels on one entry and stable ids. Kinds aren't in the dictionary.
- **Readers reconcile spellings:** `needs="title start|starts|dtstart"` lists every vocabulary.
- **Membership is structural:** a thing fits a kind if it has the aspects. Tonight Alex chose *children by declaration*: `meeting` holds only things declared or marked as meetings.
- **Values don't translate:** `Done`, `closed`, `CLOSED` (values.md, draft 2).

## 2. The design (imagined)
### 2.1 One dictionary of kinds, held by the system
- **Every kind is a dictionary entry,** as words are. It holds:
  - names (translations of one entry, as words have);
  - aspects, each with a type and a meaning;
  - parents;
  - value meanings (values.md's lifecycle);
  - the producers that support it;
  - for each fact, who said it, and whether it's proposed or accepted.
- **The kernel's own kinds are entries too,** fixed (`said`, `person`…).
- **Three relations between entries, kept apart** (the `owl:sameAs` lesson: one identity link too strong for most uses):
  1. **same:** one kind, another name (`todo` is `task`). It's a translation on the entry, and the strongest claim.
  2. **supports:** a producer's kind conforms to a shared kind through a mapping (`gh-issue supports task: title=title, status=state with open→open, closed→closed`). The producer's kind stays its own entry.
  3. **narrower:** a child (`meeting` extends `event`). Its things are members by declaration or marker.

### 2.2 Things coming in declare what they support
- **A producer** (a module's offer, a kit, an adapter, a person's import) declares its own kind and what it supports:

  `kind gh-issue supports=task map="title=title start=created_at status=state(open=open closed=closed)"`
- **It may declare only for its own kind.** It can't say someone else's kind supports anything.
- **Declaring support adds candidates for reading.** It never grants:
  - grants and rules still match a thing's own kind, plus `by=` (approved tonight);
  - words that write with app meaning still reach by own kind (shape-reads 5b.6);
  - so a hostile producer that says "supports task" gets its things *listed*, never *acted on as Alex*.
- **Stability rules** (from AT Protocol lexicons): a declared mapping only adds; a type never changes; a rename is a new entry.

### 2.3 The system handles duplicates: the intelligence layer
When a declaration or a new kind arrives, the system looks for the entries it might duplicate, in two passes.

**1. Deterministic first**, cheap and explainable:
- names, and spellings already in the dictionary;
- aspect overlap (the iceberg lattice of shared aspect sets, from the graph research);
- value sets.

**2. Intelligence where that runs out.** A librarian, a resident agent's role or a model behind the model module, proposes:
- same / supports / narrower;
- the aspect map;
- value meanings.

Each proposal carries its reason, its evidence (how many things, which aspects, sample values) and a confidence.

**Proposals are world things,** so the log keeps them, `undo` reverses them, and lenses can show them ("Needs Me").

**Acceptance has two thresholds** (Fellegi–Sunter, the entity-resolution standard):

| Band | Effect on words | Who accepts |
|---|---|---|
| High confidence, lossless, affects reading only | lists and readings include it, marked "matched by the librarian" | automatic, with a notice and an undo |
| The middle | nothing until accepted | the kind's keeper: JEFF on Alex's desktop, a leader in a group. One click with the reason shown. |
| Anything that changes what *acting* words reach or what values mean to them | nothing until accepted | a leader, in person (values review V3: an agent can't attest for its person) |
| Low | dropped, kept as a counted miss | — |

**Model outputs are never recomputed.** A proposal is a record; replaying the log replays the decision, not the model.

**The librarian never runs inside an act.** It works beside the kernel, as modules and residents do. An act reads only the dictionary as it stands.

### 2.4 Reading goes through the dictionary
- **shape-reads' reading** (names filled, values typed, the envelope) resolves through the dictionary. A word asks for `task.start`; the dictionary says `gh-issue`'s start is `created_at`.
- **Every answer carries its source:** declared by the producer, proposed by the librarian, or confirmed. That's Pike's rule that every guess is shown.
- **Acting words admit only declared or confirmed meanings.** Reading words may use proposed ones, marked.

### 2.5 Kinds that arrive with no producer
- Loose notes and imports with no kind get kind *proposals* from use: "38 things share `when`, `where`, `who` and have no kind; an event?"
- A person names it and accepts. Machines notice; people decide.

## 3. Privacy and cost (imagined)
- **What the librarian sends a model:**
  - kind names, aspect names, types, value *sets* and counts;
  - never a thing's text, unless the thing is public or the asker's own (tonight's outside rule);
  - with the local model when it runs; an outside model is an outside service.
- **Cost:** one librarian pass per new declaration or kind, not per thing or per act. A world gains kinds slowly; the trials had 4 vocabularies for 2,174 things.

## 4. What this does to the open frictions (imagined)
- **1 (reaching isn't working):** readings resolve through declared and accepted mappings. Readers stop listing spellings.
- **2 (values):** `means=` lives in the support mapping.
- **6 (over-matching):**
  - children by declaration (approved);
  - "supports" is the declaration;
  - typed aspects keep a screen point off the map.
- **4 (containers):** a Twitch channel declares it supports `chat`, its messages that they support `said`-like reading. But not `said` itself, which is the kernel's (and the House reads it).

## 5. Open questions for the reviewers and Alex
1. Is the librarian a resident (a role JEFF holds, or a new resident), or a module that calls a model, with residents reviewing?
2. Is automatic acceptance for read-only matches right, or should everything go through the keeper at first, until the error rate is known?
3. One dictionary per world, with kits carrying entries between worlds, or a shared upstream dictionary (Seabright and Alex's desktop agreeing on `event`)?
4. How does "same" differ from "supports" in practice? When should two entries merge, rather than one supporting the other?
5. Does this belong in the kernel (`kinds.py` becomes the dictionary's kinds), or in a module with the kernel reading its accepted results?

## 6. What would change my mind
- **If producers rarely declare** (most things arrive as loose notes), the librarian does most of the work, and §2.5 matters more than §2.2.
- **If the librarian's proposals are wrong often** in a replay against the trials' 2,174 things, automatic acceptance goes, and everything goes through the keeper.
- **If one dictionary per world makes worlds drift apart,** the shared upstream comes first.
