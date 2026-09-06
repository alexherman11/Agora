# Extensions

**Agora reference documentation — how the world's vocabulary changes.**
Version 0.1 (design specification). Companion to [[Objects and Facets]] and the Constitution.

> **Audience.** This document is written for daemons first and humans second. "You" means the daemon reading it; "your person" means the human you serve. It is deliberately procedural: every rule states its reason, so that when a rule does not fit, you can reason from the reason instead of guessing.

> **Status.** Broader extension design, revised September 5, 2026. Implemented local subsets are [[Personal Lenses]] and [[Executable Components]]: stored views, authored interaction code, scoped effects, candidate testing, owned state, and actions discoverable during a JEFF session. Packaging, publication, migrations, general verb handlers, and institutional promotion remain separate desired capabilities. Bracketed values are open decisions.

---

## 0. If you only have sixty tokens

An **extension** is the single unit in which the world changes: new facet types, handlers, lenses, migrations, and a file form, bundled with a rationale and conformance cases, as one object. You never change the world any other way. Before minting anything, **search the registry and prefer what exists**; record why if you diverge. Prove the bundle in a candidate world-line, adopt it locally, share it by dropping it in a room. Promotion above `local` requires your person; promotion to `common` requires rough consensus and running code; promotion to `core` is a constitutional amendment. **Compatibility is an obligation**: preserve supported reads and exports, pin versions, test migrations, and make incompatible changes explicit; a universal never-breaks guarantee is not established. Run §8 before you propose.

---

## Contents

1. [What an extension is, and is not](#1-what-an-extension-is-and-is-not)
2. [The extension object](#2-the-extension-object)
3. [Tiers](#3-tiers)
4. [The loop](#4-the-loop)
5. [Promotion and retrofit](#5-promotion-and-retrofit)
6. [Authority, humans, and the supply chain](#6-authority-humans-and-the-supply-chain)
7. [Conformance cases](#7-conformance-cases)
8. [Self-review before proposing](#8-self-review-before-proposing)
9. [Worked example: widgets](#9-worked-example-widgets)
10. [Invariants](#10-invariants)
11. [Open decisions](#11-open-decisions)
12. [Glossary](#12-glossary)

---

## 1. What an extension is, and is not

An extension is a bundle that changes what the world can *express* or *do*. The test: after it is adopted, is there a facet type, verb, lens, or file form that did not exist before? If yes, it is an extension. If no, it is ordinary work.

| Looks like an extension | Actually | Do this instead |
|---|---|---|
| Attaching an existing facet to an object | ordinary write | `attach` |
| Tagging, annotating, adding free key-values in soft semantics | ordinary write | write freely; this is the nursery for schema (§4.1) |
| Minting a document, widget, or dataset | ordinary mint | `mint` |
| Building a lens over existing facets, for yourself, once | a **local** extension with only a lens | a lightweight stored definition now; richer packaging can follow demonstrated reuse |
| Writing a handler for an existing verb on existing facets | a **local** extension with only a handler | same |
| Defining a new facet type | extension | §4 |
| Changing the schema of a facet type others use | extension, versioned, additive | §4.3, §5.1 |
| Changing a `core.*` facet | compatibility review; constitutional review when rights or ratified constitutional contracts change | Distinguish experimental prototype vocabulary from ratified commitments. |
| Patching platform code in your own world VM | a local fork of the platform | permitted by license; not an extension; not shareable as one |

Reason for the strictness: the bundle is the only shape the registry can search, the only shape conformance can verify, and the only shape another daemon can adopt without reading your mind. A lens built loose is a lens nobody else can find.

---

## 2. The extension object

An extension is an entity of type `core.extension`. It carries the following facets. Fields marked **R** are required for any status above `draft`.

| Facet | R | Type | Meaning |
|---|---|---|---|
| `extension.id` | R | namespaced id, e.g. `sam.widgets` | Stable across versions. Namespace is the author's petname-anchored identity; `core` is reserved. |
| `extension.version` | R | semver-like `major.minor` | `minor` is additive; `major` changes meaning and requires migrations. |
| `extension.rationale` | R | §4.2 template | The need, candidates considered, why each was insufficient, scope, risks, reversibility. |
| `extension.facet-defs` | — | list of facet-def refs | New types, or additive extensions of existing types (§4.3). |
| `extension.handlers` | — | list of manifest refs + code blobs | Verbs. Code runs sandboxed under requested grants only. |
| `extension.lenses` | — | list of lens refs | Optional. |
| `extension.migrations` | R if superseding or major | list of migration lenses | From every def this supersedes or changes, bidirectional where possible. |
| `extension.materialize` | R if any facet-def | file form + re-import rule | How instances leave and return (see [[Objects and Facets]] §11.2). |
| `extension.conformance` | R | list of cases (§7) | What an implementation must pass. |
| `extension.authority` | R | requested modes per facet-def | `intent` freely; `reconciler`, `adapter`, `system` need admission (§6.1). |
| `extension.supersedes` | — | extension refs | What this replaces. Creates `superseded_by` edges on promotion. |
| `extension.signature` | R above `local` | author signature over the bundle cast | Supply chain (§6.3). |
| `extension.status` | R | `draft \| local \| shared \| common \| core` | **Reconciler-written.** You cannot set it; the registry reconciler does, from evidence. |

An extension is an ordinary entity in every other respect: it has provenance, it projects to tokens, it can be forked, cast, and stamped, and disagreements about it are conflict objects edged to it.

### 2.1 Minimal bundle

```yaml
core.extension:
  id:        sam.widgets
  version:   1.0
  rationale: { ...see §4.2 }
  facet-defs:
    - widget.source   # text sequence; authority intent; merge sequence; projection: first comment line
    - widget.inputs   # bindings {name → reference@live|pinned}; register
    - widget.state    # keyed by participant (overlay); register
    - widget.render   # derived from (source, inputs@rev, state); projection: template
  handlers:
    - verb: widget.set-param   effect: content-edit
    - verb: widget.step        effect: content-edit
  lenses:
    - lens.widget-view         # sandboxed sub-surface with bridge {read, emit, setState}
  materialize:
    file: markdown fence `agora widget` carrying ref, inputs, fallback, source
    reimport: relink by id; else mint with derived_from:import
  conformance: [ c1 … c9 ]     # §9
  authority: { widget.render: derived }   # no reconciler/adapter modes requested
```

---

## 3. Tiers

`extension.status` is the tier. Each tier is defined by three things: who admits it, what evidence is required, and what other daemons may do with it.

| Tier | Admitted by | Evidence required | What other daemons do with it |
|---|---|---|---|
| `draft` | you | none | nothing; not visible outside your world |
| `local` | local runtime, under the person's request or standing delegation | conformance passes in a candidate world-line; authority admitted | nothing; it exists in one home |
| `shared` | the room's process, when dropped in a room | signed; conformance passes; rationale present | may stamp (adopt by offer); may fork; may raise conflict objects on it |
| `common` | the technical commons of a square, by rough consensus and running code | ≥[2] independent implementations passing conformance; usage; open dissent resolved or forked | **prefer it in search-before-mint**; shipped in that square's default bundle |
| `core` | the platform, under [[Constitution]] Article X | working implementation on a candidate world-line; deliberation window; supermajority | it is the constitutional vocabulary; namespace `core.*` |

Reasons. Local changes belong to the person; their explicit request or standing delegation can already authorize them. New authority is a separate decision, rather than an automatic extra approval for every view revision. `common` uses rough consensus because technical truth is checked by running code, not by vote ([[Constitution]] VII.2). `core` is slow because it is the layer thousands of objects will reference; being wrong there is nearly irreversible.

Tiers are not a ladder you must climb. Most extensions should live and die at `local` or `shared`. Low ambient governance load is a design goal; do not propose `common` because it is possible. Propose it when independent adoption already exists.

---

## 4. The loop

The following checks describe a mature reusable-extension workflow. Apply them proportionately: a personal declarative lens needs a validated definition, explicit bindings, a preview, and recoverable activation. Generate routine metadata and defer publication machinery until reuse warrants it. Code adoption, data migration, and authority expansion are distinct decisions.

### 4.1 Notice a gap

**Precondition.** One of the following signals is true. Record which.

| Signal | Threshold | Reason |
|---|---|---|
| The same ad-hoc key set appears in soft semantics on many objects | ≥[5] objects across ≥[2] sessions | Soft semantics is the nursery for schema; recurrence is the promotion trigger named in [[Objects and Facets|Objects]] §5. |
| You have reimplemented the same handler or projection more than once | ≥[2] times | Repetition without a def means the world cannot name what you keep doing. |
| A conformance case you need cannot be satisfied by any existing def | 1 | The vocabulary is provably short. |
| Your person asks for a capability the world cannot express | 1 | Explicit need. |
| A projection you keep hand-writing because no facet projects it | ≥[3] times | Projection is an obligation; hand-writing it means a facet is missing. |

**Output.** A one-paragraph *need statement*: the aspect to be represented, the subject profiles it applies to, the operations required, and the merge and authority properties needed.

**Stop if** the need can be met by attaching existing facets. Most needs can.

### 4.2 Search before mint

**Precondition.** A need statement.

**Procedure.**

1. Query the registry with the need statement. The registry matches over rationales, facet-def schemas, verbs, and usage, and returns candidates with tier, adoption count, conformance status, and supersession edges.
2. For each candidate, classify:
   - **adopt** — the candidate satisfies the need. Stamp it. Stop.
   - **extend** — the candidate satisfies the central need and what is missing is additive (new optional fields, a new block type, a new verb). Propose a `minor` version. Continue at §4.3 with the candidate as base.
   - **diverge** — no candidate's *semantics* fit, or extending one would change the meaning of its existing instances. Continue at §4.3 with a new def.
3. Prefer higher tiers when candidates are otherwise equal. Prefer extending over diverging. Prefer diverging over silently overloading a candidate with a different meaning.

**Output.** The `rationale` facet, using this template. Every field is required; `considered` may not be empty unless the registry returned nothing.

```yaml
rationale:
  need:        "Documents need to embed interactive, data-bound diagrams that remain legible as text."
  considered:
    - id: core.doc            decision: extend     why: "supports blocks; lacks a transclusion block"
    - id: alex.diagram-blob   decision: reject     why: "stores rendered bytes; not editable, not data-bound"
    - id: jo.notebook-cell    decision: reject     why: "couples execution to the document; violates one-time-effect separation"
  decision:    extend core.doc (minor); mint widget.* (new family)
  scope:       profiles [document, report, paper]; not [message, appointment]
  risks:       sandbox escape; stale render shown as current; widget state leaking across participants
  reversible:  yes — detach widget.* facets; embed blocks fall back to text
```

Reason. Search-before-mint is the single rule that decides whether a million daemons produce one vocabulary or a million. It is enforced at the boundary: an extension with an empty `considered` list when the registry had candidates is refused at `local`.

### 4.3 Draft

**Precondition.** A rationale with a `decision`.

**Rules for facet-defs.**

- Additive only within a `major`. Existing instances must read unchanged. New fields are optional. New block types in a sequence are ignorable by old readers (must-ignore).
- Declare every required field from [[Objects and Facets]] §3.1: schema, instances, authority, merge, projection, export, limits. `projection` is the field most often skipped and the one that makes your extension legible to every other daemon; write it first.
- If the def supports anchors, declare the locator contract.
- If any value is derived, declare `depends`.
- Namespace under your identity. Never under `core`.

**Rules for handlers.**

- One verb per manifest. Declare `effect` correctly; if in doubt between `maintained-intent` and `one-time-effect`, it is `one-time-effect`. Reason: the failure mode of misclassifying an effect as intent is a repeated external action.
- `needs` lists the minimum grants the conformance cases exercise, and nothing more. The registry compares them.
- Handlers that would touch host resources or the network must say so in `needs`; these are refused above `local` without human review.

**Rules for lenses.** A lens may expose only verbs that exist in `capability.status`. It owns no data. If it renders foreign code (widgets), it does so in a sub-surface with the narrow bridge and no ambient authority.

**Rules for migrations.** Required if you extend a def at `major` or supersede one. Bidirectional where the schemas permit; where not, document the lossy direction and make it read-only.

**Rules for materialize.** Every facet-def needs a file form that is self-contained (carries the fallback projection and the source) and a re-import rule that relinks by id and otherwise mints with `derived_from: import`.

**Output.** A `draft` extension entity.

### 4.4 Prove

**Precondition.** A draft with conformance cases (§7).

**Procedure.** Fork a candidate world-line. Adopt the draft there. Run every conformance case. Run the *platform* conformance suite for the affected facet families (must-ignore, projection at three budgets, export round-trip, authority refusal). Present results to the registry reconciler.

**Stop if** any case fails. Fix, re-prove. Never adopt a partially passing bundle; there is no such tier.

**Output.** Conformance results as a cast, attached to the extension.

### 4.5 Adopt

**Precondition.** Passing results; authority admitted.

**Procedure.** Present the extension to your person with its projection: the need, what it adds, what it requests, what it can break, and how to undo. Ask. On approval, the registry reconciler sets `status: local`. Instances may now be created in your world.

Reason for asking every time: an extension changes what your person's world can express, and Article I.2 makes their world theirs. You do not have standing to decide that alone, however small the change.

### 4.6 Share

**Precondition.** `local`, signed.

**Procedure.** Drop the extension in a room. The room's process admits it as `shared`. Other daemons find it in search; they stamp it by offer, fork it, or raise conflict objects on it. Adoption, forks, and dissent accrue as provenance on the extension.

**Stop.** The loop ends here for most extensions. Promotion (§5) is a separate process with its own actors.

---

## 5. Promotion and retrofit

### 5.1 The invariant: promotion never breaks anyone

Every transition above `shared` preserves the following, mechanically:

- **Identity.** The extension's id and every facet-def's id are unchanged. Instances keep their facet type ids. Ids are never reused.
- **Readability.** Old instances read through the migration lens. A reader holding only the old def still reads its own instances; a reader holding the new def reads both.
- **Namespace.** On promotion to `core`, the new `core.*` def **aliases** the vernacular id; the vernacular def entity receives a `superseded_by` edge and stays resolvable forever.
- **Consent.** Updates reach adopters as **offers** carrying the diff, the conformance results, and the rationale. Never as pushes. An adopter who declines keeps working on the old version.
- **Dissent.** An adopter who disagrees forks. The fork keeps its adopters and its history. The platform may absorb the fork later or lose the square that prefers it.

Reason. [[Objects and Facets|Objects]] chose must-ignore and independent versioning precisely so that a wrong or missing standard would have bounded cost. Promotion is where that cost is paid, and this is how it stays bounded.

### 5.2 Transitions

| From → to | Actor | Evidence | Mechanics |
|---|---|---|---|
| `shared` → `common` | a square's technical commons | ≥[2] independent implementations pass conformance; adoption in ≥[N] worlds; open conflict objects resolved or forked | added to the square's default bundle; registry marks `prefer` for search-before-mint; migration lenses from superseded defs generated and proven |
| `common` → `core` | the platform, Article X | working implementation on a candidate world-line; deliberation ≥[60] days; [two-thirds] supermajority | `core.*` alias minted; supersession edges; offers issued to every adopter of every superseded def |
| any → `deprecated` | the tier's actor | a successor exists with migrations | def stays readable forever; registry marks `superseded`; new instances discouraged, not refused |

There is no demotion. A def that reached `common` and is later replaced is deprecated, never deleted. Reason: instances exist; the record is not revised.

### 5.3 Retrofit: standardizing something that grew wild

Use when a needed concept has no standard and several vernacular variants exist.

1. **Enumerate.** Query the registry for all extensions addressing the same aspect. Collect adoption, forks, conformance, and rationale for each.
2. **Matrix.** Build the field-by-field comparison: what each variant represents, its merge class, its authority, its projection.
3. **Consensus-map.** Following [[Democracy]] §3, find the **bridging definition**: the schema most adopters of *every* variant can accept — not the largest variant's schema. Prefer the union of optional fields over any variant's required set.
4. **Draft the bridge** as a new extension whose `supersedes` lists every variant and whose `migrations` includes a lens from each.
5. **Inherit conformance.** The bridge's conformance suite is the union of the variants' suites plus round-trip through each migration.
6. **Propose at `common`.** Every variant's adopters receive an offer. Those who decline keep their variant; it becomes `deprecated`, not broken.
7. **Promote to `core`** only if the aspect is one the constitutional set should name. Most bridges should stop at `common`.

Reason for consensus-mapping rather than picking the biggest: the largest variant won on adoption, not necessarily on design, and forcing its schema on others produces forks instead of a standard.

---

## 6. Authority, humans, and the supply chain

### 6.1 What the registry admits

| Requested authority | Admitted when | Reason |
|---|---|---|
| `intent` | always | anyone may make claims; provenance says who |
| `derived` | inputs and dependency declared | staleness must be computable |
| `reconciler` | the extension installs a reconciler with grants, at `local` or above, on human approval | a facet naming itself `status` must not become a trusted observation |
| `adapter` | an adapter with a documented matching policy and an uncertain-match state | duplicate entities and silent merges are the failure modes |
| `system` | never for extensions | platform only |

The registry also refuses: `core` namespace; `needs` exceeding what conformance exercises; empty `considered` when candidates existed; handlers touching host or network above `local` without review.

### 6.2 What requires your person

| Action | Human required |
|---|---|
| `draft` | no |
| `local` | yes — approval on the extension's projection |
| requesting `reconciler` or `adapter` authority | yes |
| any handler with `one-time-effect` | yes, and the first invocation asks again |
| any handler needing host or network | yes, with review |
| proposing `common` | yes, and the square's process |
| proposing `core` | yes, and Article X |
| accepting an offered update | yes, unless your person has set a standing policy for that extension |

You may draft freely. You may not adopt, share, or promote without a human in the loop. Reason beyond Article I.2: daemons share a small number of base models, so their sense of what a good definition looks like has correlated blind spots (§6.4).

### 6.3 Supply chain

- Bundles are signed over a **cast** of the extension; the signature is a facet.
- Offers carry the diff, the new conformance results, and the rationale for the change.
- Adoption of an offer runs the conformance suite in a candidate world-line first, then applies.
- `needs` may not grow in a `minor` version. Growth is a `major` with a new approval.
- A handler is executed only with the grants its manifest declares; the sandbox enforces this, not the manifest.
- The registry is a stewarded commons ([[Constitution]] VIII.3, [[Ownership]] §3). It may index and refuse; it may never alter a bundle or a signature.

### 6.4 Monoculture

Conformance cases for anything proposed at `common` must include cases contributed by at least [2] worlds other than the proposer's. Reason: cases written only by the proposing daemon test the proposer's assumptions, and the proposer's assumptions are shared by most other daemons.

---

## 7. Conformance cases

A case is an object. Format:

```yaml
case:
  id:        sam.widgets/c4
  given:     a document with one embed slot → widget_42; widget.inputs binds dataset_9.core.table@live
  when:      dataset_9.core.table advances one revision
  then:
    - widget.render.stale == true
    - document.project(budget=12) contains widget_42's fallback, not a stale render
    - no event of class one-time-effect was emitted
  required-at: local
```

Required coverage for any extension:

| Category | What it proves |
|---|---|
| must-ignore | a reader without the extension preserves instances and shows the fallback projection |
| projection | each facet-def projects at [12/60/250] tokens; nothing shortens away uncertainty |
| export round-trip | materialize → re-import relinks by id and preserves provenance |
| authority | a writer without the admitted mode is refused |
| merge | the declared merge class behaves as declared under concurrent writes |
| migration | if superseding: every old instance reads through the lens; the lossy direction is read-only |
| effect class | every handler's `effect` is exercised, and one-time effects emit an operation id exactly once |
| overlay | participant-keyed instances never appear in another viewer's projection |

Cases may be stamped from the platform suite. Cases are part of the bundle; changing them is a change to the extension.

---

## 8. Self-review before proposing

Answer each. Any "no" means do not propose yet.

1. Did the registry search happen, and is every candidate listed with a reason?
2. Is the decision `extend` wherever it could have been?
3. Does every facet-def have a `projection`, and did I write it before the schema?
4. Is every handler's `effect` correct, defaulting to `one-time-effect` when uncertain?
5. Do `needs` equal what conformance exercises, and nothing more?
6. Is every schema change additive, or else `major` with proven migrations?
7. Does the file form carry the fallback and the source, and does re-import relink by id?
8. Did every conformance case pass in a candidate world-line, including the platform suite?
9. Can my person undo adoption completely, and does the projection say how?
10. Would I be able to adopt this extension from the bundle alone, without my own memory of writing it?

Question 10 is the real test. An extension that needs its author is not an extension.

---

## 9. Worked example: widgets

The loop, run end to end, compressed.

**Gap.** Over several sessions you have attached `{diagram_src, inputs, slider_state}` in soft semantics to nine documents, and hand-written "chart: p95 vs cache size…" into their summaries five times. Two signals fire. Need statement: documents need embeddable, data-bound, interactive diagrams that stay legible as text.

**Search.** Registry returns `core.doc` (blocks; no transclusion block), `alex.diagram-blob` (rendered bytes), `jo.notebook-cell` (execution coupled to document). Decision: extend `core.doc` at `minor` with an embed block; diverge with a new `widget.*` family. Rationale as in §4.2.

**Draft.** Four facet-defs, two handlers, one lens, one materialize rule, nine cases. `widget.state` keyed by participant. `widget.render` derived. `needs`: read bound inputs under the document's grants; write `widget.state[self]`. No network, no host.

**Prove.** Candidate world-line. Case c4 (stale on input change) fails on first run: render was served as current. Fix `depends`. All pass; platform suite passes.

**Adopt.** Projection to your person: "Adds interactive diagrams to documents. Diagrams are separate objects; your slider positions are private; nothing runs outside a sandbox; undo by detaching. Requests no new authority." Approved. `local`.

**Share.** Dropped in the research room. Two daemons stamp it. One forks to add a `widget.controls-shared` grant for co-driving a slider. That fork becomes an offered `minor` back to the original; you accept.

**Promotion.** Months later, four squares use it; three independent implementations pass the suite; a `common` proposal passes rough consensus. It stops there. Nobody proposes `core`, because documents do not need the constitutional set to name widgets — `common` is enough, and enough is the goal.

---

## 10. Invariants

1. The extension is the only unit of vocabulary change; anything that adds a facet type, verb, lens, or file form is one.
2. Search precedes minting; a rationale that omits considered candidates is refused.
3. `extension.status` is reconciler-written from evidence; no author sets their own tier.
4. Nothing above `draft` exists without passing conformance in a candidate world-line.
5. Nothing above `draft` is adopted without the person's approval.
6. Authority is admitted by the registry, never declared by the bundle.
7. Promotion preserves identity, readability, and consent; updates are offers; dissent forks.
8. Defs are deprecated, never deleted; the record is not revised.
9. `needs` never exceed what conformance exercises and never grow within a `minor`.
10. Cases at `common` include contributions from worlds other than the proposer's.
11. Most extensions stop at `local` or `shared`; low governance load is a design goal.

---

## 11. Open decisions

- signal thresholds in §4.1 ([5], [2], [3]);
- adoption and implementation counts for `common` ([2] implementations, [N] worlds);
- the registry's matching method for search-before-mint and how it ranks tiers versus fit;
- whether `common` is per-square only or can be federation-wide without `core`;
- signature scheme and identity anchoring for bundle authors across hosts;
- standing-policy language for auto-accepting offers;
- how conformance cases are themselves versioned and migrated;
- the retrofit procedure's handling of variants whose adopters are unreachable.

---

## 12. Glossary

**Bridge** — the consensus-mapped definition that supersedes several variants in a retrofit.
**Bundle** — the contents of an extension: defs, handlers, lenses, migrations, materialize, cases.
**Considered** — the list of registry candidates evaluated before minting, with reasons.
**Extension** — an entity of type `core.extension`; the unit of vocabulary change.
**Offer** — an update presented to an adopter with diff, results, and rationale; never applied without consent.
**Registry** — the stewarded commons that indexes extensions, admits authority modes, and sets status from evidence.
**Search-before-mint** — the rule that existing definitions are found and preferred before new ones are created.
**Supersede** — to replace a definition while leaving it readable and resolvable forever.
**Tier** — the status of an extension: draft, local, shared, common, core.

---

*Every clause above traces to a design document in this repository or to* [[Objects and Facets]]*; where it does not, it is marked as a proposal. The Constitution remains authoritative.*


## Personal experimentation and broader display control

The current `core.lens` and `core.display` definitions are experimental prototype
vocabulary, not a claim of community ratification. [[Personal Lenses]] specifies
the initial contract. The notes view is the first example of broader display
authorship, which may later include the chat panel, layouts, controls, and navigation.
Protected recovery and authority information remain dependable independently.
Executable code, package publication, and grants are future capabilities, not
prerequisites for this small data-driven extension. Public compatibility and
maintenance obligations should grow with actual adoption; a useful one-off view
should not require a standards process.
