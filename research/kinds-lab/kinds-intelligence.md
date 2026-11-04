# The system holds the kinds

> **Draft 1, by Claude, 28 Oct 2026, late.** After two reviews:
> - `review/kinds-intelligence-kernel-review.md`: adversarial, with probes on the code;
> - `review/kinds-intelligence-prior-art.md`: Apple App Intents, Android AppFunctions, Home Assistant, Microsoft Graph, Palantir, atproto, LLM matching benchmarks, Wikidata, data-catalog mappers.
>
> JEFF answered in Shop talk (dk1313, §1.4b). Draft 0 is in [[kinds-intelligence-draft-0]]. Not approved, not built.
> - **Alex's direction (his words, 28 Oct):** "the system should hold all the kinds, things coming into the system can declare what kinds they support, and it is the job of the system to handle duplicates in the on system dictionary. That is why there has to be an intelligence layer to support multiple kinds. It is literally essential for agora to function."
> - **Alex again, 29 Oct (his words), before answering §3:** "kinds to be managed by the system they are on, things can bring in their kinds and words when they enter the system, and its the job of intelligent agents to manage how they interoperate". He wants to talk the design through first. Note by Claude: this goes further than draft 1, which keeps agents to proposing and has none in v1.
> - **Labels:** **read** (code or source), **ran** (numbers as printed), **imagined** (design).

## 0. What the reviews changed, in one list
1. **A declaration reaches reading words only, until it's accepted.**
   - Draft 0 contradicted itself: §2.2 said support never reaches acting words, §2.4 said "declared" meanings did. The kernel uses one `fits` for lists, acting words and plain dispatch, so wiring support into it would be `extends` without a leader (K1).
   - **Ran:** Alex's plain `close` already ran `task.close` on a member's `gh-issue`, by structure.
2. **The machine never proposes "same", and support doesn't chain.**
   - "Same" is identity, so it widens grants, rules and `house.build`. It's never reading-only (K3).
   - Home Assistant tried merging duplicate records and backed out in Core 2026.8: conflicting values were "discarded instead of preserved".
   - **Duplicates are linked, never merged.**
3. **The model starts as a helper, not a judge.**
   - LLM schema matching scores F1 0.47–0.58, with top-1 accuracy 42–70%.
   - No production AI mapper (Unity Catalog, Zapier, Make, Airbyte) commits a mapping on its own.
   - So automatic acceptance waits until a replay measures the librarian's precision.
4. **Declarations are checked when they arrive, deterministically.** That's what Apple's build, Microsoft's checklist and Palantir's required mappings do. Bad ones are refused, not repaired by guesswork.
5. **Nobody owns a kind name today** (K2, ran).
   - A member's first closed declaration can carry anything, and since tonight it blocks a second declaration of that name. The steward can still `set` or `forget` it.
   - Producers need a name of their own before "only for your own kind" means anything.
6. **Who accepts is Alex's call** (K4, ran). JEFF is a person and a steward, and so is a paid builder's agent session for Alex. On the desktop, every band collapses to one of them.
7. **Bands go by effect, which only the kernel can compute** (K5). The model gives evidence as features: name overlap, value overlap, sample count, shared identifiers. It never gives one confidence number to trust.
8. **Proposals are private to their acceptor** (K6, ran). Aspect names carry person ids, `contact:` and `claim:`. What goes to a model follows tonight's outside rule: public, or the asker's own.
9. **Rejections are durable** (K8): "not supports" is a record, or the librarian proposes it again forever.
10. **Review queues starve** (Wikidata's Primary Sources tool: about 0.6% reviewed). So decisions are one per producer declaration, batched, with sample values side by side. Each producer has a cap, and stale proposals expire into counted misses.

## 1. The design (imagined)
### 1.1 The dictionary of kinds
- **Kinds stay `kind=kind` things,** in their own namespace: seven kernel kinds are also word names (ran). From the dictionary they borrow labels, stable-id binding and a steward edit word.
- **A thing's own kind never migrates.** References to kinds (`acts_on`, `of_kind`, grants' `only=kind:`) bind to the declaration's id, as stored words bind to entries.
- **Producers get a namespace:** a module's kinds live under its name (`gh.issue`), as its words do (`gh.*`). A person's own kinds are theirs.

  That's K2's precondition: "only for your own kind" needs an owner.

### 1.2 Things coming in declare what they support
- **On its own kind, a producer declares:**

  `supports=task map="title=title start=created_at status=state" means="state: open=open closed=closed"`

  Every field beyond `name title help` is governed. Only the kind's owner, or a leader of its scope, may write it.
- **The deterministic check on arrival.** It's refused if:
  - types don't match;
  - a shared kind's need is left unmapped without an explicit `none`;
  - one producer aspect serves two shared aspects;
  - a known value is unmapped without `unknown`.
- **The target is named by declaration id within its scope,** so a nearer declaration can't re-point it (K9).
- **Stability:**
  - a shared kind's `needs` freeze once a producer supports it (protobuf: "Required Is Forever");
  - value sets stay open, and a value outside the map is "meaning unknown";
  - a change supersedes, with a repair notice, never by removal;
  - each accepted declaration is pinned by hash, and any change reopens it.

### 1.3 What a declaration does, by stage
| Stage | Lists and readings (`rows task`, `through=`) | Acting words, plain dispatch, grants, rules |
|---|---|---|
| Declared | included, marked "gh.issue supports task (not yet accepted)" | no |
| Accepted by a leader of the **target's** scope, once per producer | included, marked "accepted by Alex" | **only if Alex says accepted support should reach acting words** (open question 1); grants and rules never (they keep own kind, plus `by=`) |
| Rejected | not included; the rejection is a record | no |

### 1.4 The intelligence layer: the system handles duplicates
- **`kinds.alike`, a see word in the kernel, with no model.** It finds candidate duplicates from:
  - names and accepted spellings;
  - aspect overlap (the iceberg lattice);
  - value sets;
  - shared identifiers.

  It's computed as the reader sees. This is "the system handles duplicates" with nothing to trust but code.
- **The librarian, a module.** It reads `kinds.alike` and, where the code runs out, asks the model, local first.
  - It proposes only "this kind could support that one, with this aspect map", with the evidence as features.
  - It never proposes "same" and never chains.
  - **A proposal is a world thing,** visible to its acceptor only, carrying its evidence, the model and the prompt's hash.
- **Who accepts:** a leader of the target kind's scope, in person, never the librarian.
  - **Automatic acceptance only on deterministic evidence:** a producer declaration that passed §1.2, a shared identifier, or a spelling already accepted.
  - Model-made proposals always go to the keeper, until a replay over the trials' 2,174 things shows ≥98% precision on at least 50 proposals, judged against Alex's own answers.
- **"Same"** is a rename or translation a keeper declares by hand. It never comes from a match.
- **Determinism:** proposals and acceptances are records. A replay never calls a model, and the kernel never depends on one. Undo reverses an acceptance, not what was done under it (K10, ran); the reversal says so.

### 1.4b JEFF's review from inside the world (dk1313, 29 Oct 03:03Z)
- **How proposals reach the keeper:**
  - batched once a day, as one card he works through;
  - the exception is a proposal that's blocking something now (an acting word refused on an unknown spelling), which comes straight away.
- **Each proposal shows the thing read with and without it** (`through=`), "so I'm judging a result, not a schema".
- **The librarian is a module calling a small model, with him reviewing.**
  - That's Alex's picture: small models sort things before they reach JEFF.
  - Not JEFF: librarian work would bury the steward.
  - Not a new resident: every wake costs Alex usage.
- **He's happy to be the keeper.** That makes open question 2 concrete for Alex: may JEFF accept read-only support, and only Alex accept what acting words rely on?

### 1.5 Kinds with no producer
Loose things that share aspects get a proposal: "38 things share `when`, `where` and `who`, and have no kind: an event?" A person names it. Machines notice; people decide.

## 2. The first build (imagined; about 400–550 lines with tests, planned at the top, given the last 2.5× overrun)
1. **`supports=` with `map=`** on a kind declaration, owned by its maker. `kind.accept <decl> for=<target>` by a leader of the target's scope, recorded with who and where.
2. **Lists only:** `rows <kind>` includes accepted supporters, read through the map and marked. `fits`, `check_word`, `plain_verb` and `actions` don't change.
3. **The deterministic check on arrival** (§1.2).
4. **Kits carry `supports`/`map`** and re-check them at `take`. Acceptances don't travel.
5. **`kinds.alike`,** the duplicates report, with no model.

Not in v1: "same", the model, automatic acceptance, acting reach, value meanings, producer namespaces for persons.

**Then:** the librarian module (local model) and the replay that decides automatic acceptance.

## 3. Open questions for Alex
1. **Once you accept that `gh.issue` supports `task`, should words that act (close, build, RSVP) reach GitHub issues too?** Or should lists only see them, while acting stays with each app's own words? The reviews lean to lists only, at first.
2. **Who accepts on your desktop:** you only, or JEFF too? And an agent acting for you (a builder session)? The reviews lean to you only for anything acting words rely on, with JEFF for reading-only matches.
3. **A small shared set of kinds that kits carry** (task, event, place, message, person…), with each world holding the rest? Or each world entirely on its own?

## 4. What would change my mind
- **If `kinds.alike` alone finds the four trial vocabularies' duplicates,** the model waits. If it finds almost none, the model earns its place sooner.
- **If the replay shows the librarian at ≥98% precision,** automatic acceptance for read-only support is fine.
- **If producers mostly arrive undeclared,** §1.4 and §1.5 matter more than §1.2.
- **If you want accepted support to reach acting words,** two-party acceptance by a person is enough. The list-only stage becomes a convenience.
