# Extensions

**Agora reference documentation — how the world's vocabulary changes.**
Version 0.3 (revised September 10, 2026). Companion to [[Objects and Facets]],
[[Native Development]], [[Design Commitments]] and the [[Constitution]].

> **Audience.** This document is written for daemons first and humans second. "You" means the daemon reading it; "your person" means the human you serve. It is deliberately procedural: every rule states its reason, so that when a rule does not fit, you can reason from the reason instead of guessing.

> **Status.** This is a detailed design for reuse and vocabulary growth. Agora3
> currently implements native packages with retained source/build/installation
> identities, installed actions and skills; [[Runtime Guide]] owns those formats.
> The local/shared/common/core tiers, registry process and schemas below are
> hypotheses for a future ecosystem. They are not ceremonies every personal
> experiment must perform. Bracketed values remain open.

---

## 0. If you only have sixty tokens

An **extension** is a reusable unit that can add data meaning, actions, views,
skills or file behavior. The current executable form is a native package.
Ordinary edits need no package. Look for an installed capability when discovery
is likely to help; a personal experiment does not need exhaustive registry
research or a written defense of novelty. Retain source and evidence appropriate
to the effect, activate deliberately, and preserve useful compatibility. More
formal conformance, adoption and promotion belong to capabilities other people
or long-lived data will depend on.

---

## Contents

1. [What an extension is, and is not](#1-what-an-extension-is-and-is-not)
2. [The extension object](#2-the-extension-object)
3. [Tiers](#3-tiers)
4. [The loop](#4-the-loop)
5. [Promotion and retrofit](#5-promotion-and-retrofit)
6. [Authority, humans, and the supply chain](#6-authority-humans-and-the-supply-chain)
7. [Conformance cases](#7-conformance-cases)
8. [Self-review before a stable or shared proposal](#8-self-review-before-a-stable-or-shared-proposal)
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
| Building a lens over existing facets, for yourself, once | a **local** extension with only a lens | a minimal source package; generate routine metadata and keep the loop light |
| Writing a handler for an existing verb on existing facets | a **local** extension with only a handler | same |
| Defining a new facet type | extension | §4 |
| Changing the schema of a facet type others use | extension, versioned, additive | §4.3, §5.1 |
| Changing a `core.*` facet | compatibility and migration review; constitutional consideration only if people's actual rights change | Technical vocabulary evolves through ordinary engineering. |
| Editing arbitrary files in the guest VM | a machine experiment | capture useful source in a package or machine recipe; it does not modify the protected host |

Reason for packaging: a retained bundle gives discovery, verification and reuse a
stable thing to address. Loose experiments remain legitimate; capture them as a
package when they need to survive, be invoked again or be understood by somebody
other than their author.

---

## 2. The extension object

An extension is an entity carrying the `core.extension` profile; that label is shorthand for the facets below, not a kind-tag that grants behavior. It carries the following facets. Fields marked **R** are required for any status above `draft`.

| Facet | R | Type | Meaning |
|---|---|---|---|
| `extension.id` | R | namespaced id, e.g. `sam.widgets` | Stable across versions. Namespace is the author's petname-anchored identity; `core` is reserved. |
| `extension.version` | R | semver-like `major.minor` | `minor` is additive; `major` changes meaning; migrations are required where stored data is affected. |
| `extension.rationale` | R | §4.2 template | The need, candidates considered, why each was insufficient, scope, risks, reversibility. |
| `extension.facet-defs` | — | list of facet-def refs | New types, or additive extensions of existing types (§4.3). |
| `extension.handlers` | — | list of manifest refs + source entry points | Verbs registered independently of open lenses; runtime and effective authority are explicit. |
| `extension.lenses` | — | list of UI entry points and bindings | Optional; ordinary browser rendering/input is allowed. |
| `extension.source` | R for authored code | file map: package-relative path → retained text/blob revision | Readable and patchable through native operations. |
| `extension.dependencies` | R for authored code | declared requirements plus resolved lock | Exact source/runtime dependencies captured at build time. |
| `extension.build` | R for compiled code | runtime/toolchain contract and build entry point | Produces an immutable artifact with provenance. |
| `extension.assets` | — | named retained blob references | Images, styles, media and other packaged resources. |
| `extension.skills` | — | versioned procedure entry points | Installed instructions/examples; reading a file does not activate a skill. |
| `extension.migrations` | R if stored schema changes | list of migration lenses | From every def this supersedes or changes, bidirectional where possible. |
| `extension.materialize` | when portable file interchange is promised | file form + re-import rule | How instances leave and return (see [[Objects and Facets]] §11.2). Generic export may be sufficient first. |
| `extension.conformance` | proportional to promised stability | list of cases (§7) | What this package claims to have exercised. |
| `extension.authority` | R | requested modes per facet-def | `intent` freely; `reconciler`, `adapter`, `system` need admission (§6.1). |
| `extension.supersedes` | — | extension refs | What this replaces. Creates `superseded_by` edges on promotion. |
| `extension.signature` | R above `local` | author signature over the bundle cast | Supply chain (§6.3). |
| `extension.status` | candidate ecosystem field | `draft \| local \| shared \| common \| core` | One possible adoption model; not implemented by Agora3. |

“Required” describes the retained package contract, not a form the person must
fill in. The tooling should generate routine metadata. A one-file action needs no
lens, asset bundle, custom schema or publication ceremony.

An extension is an ordinary entity in every other respect: it has provenance, it projects to tokens, it can be forked, cast, and stamped, and disagreements about it are conflict objects edged to it.

### 2.1 A widget bundle

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

### 2.2 A source package need not be large

```yaml
extension:
  id: alex.notes-board
  version: "0.1"
  source:
    board.js: text-revision:source-17
    actions.js: text-revision:source-18
    board.css: text-revision:source-19
  lenses:
    - id: board
      entry: board.js
      styles: [board.css]
      bindings: [notes_in_scene]
  handlers:
    - verb: alex.notes-board.arrange
      entry: actions.js#arrange
      applies_to: {facet: core.scene}
      params: {type: object, properties: {columns: {type: integer, minimum: 1}}, required: [columns]}
      result: {type: object, properties: {moved: {type: integer}}, required: [moved]}
      effect: organization
      needs: [scene.read, scene.place_many]
      describe: Arrange note appearances in a grid
  dependencies:
    declared: {agora-browser: "contract-v1"}
    locked: {agora-browser: "artifact:browser-contract-1"}
  rationale:
    need: Drag and arrange notes in this scene
    considered: []
    decision: No suitable installed board was found
  conformance: [drag-persists, new-note-appears, arrange-with-view-closed]
```

Identifiers, entry-point notation and runtime names are illustrative, not installed
APIs. The package record captures source and intent. A build records the exact
source revision, dependency lock and toolchain; an installation points to the
resulting artifact. These are distinct from `extension.status`, which describes
adoption tier. Runtime health is an observation, not the tier.

The `arrange` action remains installed after the board closes. Another lens or tool
can call it through the registry. A caller pins the chosen installation revision;
an in-flight call does not switch code when JEFF installs the next version.
Composition, owned state and stale activation are specified in
[[Native Development]] §3–5.

---

## 3. Tiers

The following tier system is a candidate for a larger ecosystem. Each tier is
defined by who admits it, what evidence is expected and what others may infer.

| Tier | Admitted by | Evidence required | What other daemons do with it |
|---|---|---|---|
| `draft` | you | none | nothing; not visible outside your world |
| `local` | local runtime, under the person's request or standing delegation | conformance passes in a candidate world-line; authority admitted | nothing; it exists in one home |
| `shared` | the room's process, when dropped in a room | signed; conformance passes; rationale present | may stamp (adopt by offer); may fork; may raise conflict objects on it |
| `common` | the technical commons of a square, by rough consensus and running code | ≥[2] independent implementations passing conformance; usage; open dissent resolved or forked | **prefer it in search-before-mint**; shipped in that square's default bundle |
| `core` | the platform's compatibility process | working implementation, migration evidence and proportionate review | widely depended-on built-in vocabulary; namespace `core.*` |

Reasons. Local changes belong to the person; their explicit request or standing
delegation can already authorize them. New authority is a separate decision,
rather than an automatic extra approval for every view revision. Common and core
contracts deserve broader evidence because many objects and people may depend on
them. Their technical standardization is not itself a constitutional amendment.

Tiers are not a ladder you must climb. Most extensions should live and die at `local` or `shared`. Low ambient governance load is a design goal; do not propose `common` because it is possible. Propose it when independent adoption already exists.

---

## 4. The loop

The following checks describe a reusable-extension workflow. Apply them
proportionately. A disposable personal preview may stop early and keep known
failures visible; a retained capability needs enough source, validation and
recovery evidence to support what it promises. Generate routine metadata and
defer publication machinery until reuse warrants it. Code adoption, data
migration and authority expansion are distinct decisions.

### 4.1 Notice a gap

**Precondition.** One of the following signals is true. Record which.

| Signal | Illustrative threshold | Reason |
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

**Procedure when reuse is likely to matter.**

1. Query the registry with the need statement. The registry matches over rationales, facet-def schemas, verbs, and usage, and returns candidates with tier, adoption count, conformance status, and supersession edges.
2. For each candidate, classify:
   - **adopt** — the candidate satisfies the need. Stamp it. Stop.
   - **extend** — the candidate satisfies the central need and what is missing is additive (new optional fields, a new block type, a new verb). Propose a `minor` version. Continue at §4.3 with the candidate as base.
   - **diverge** — no candidate's *semantics* fit, or extending one would change the meaning of its existing instances. Continue at §4.3 with a new def.
3. Prefer higher tiers when candidates are otherwise equal. Prefer extending over diverging. Prefer diverging over silently overloading a candidate with a different meaning.

**Output.** For a shared or long-lived contract, retain a rationale using this
template. A small local experiment may keep only the need, decision and risks.

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

Reason. Discovery makes reuse possible and reduces accidental incompatible
vocabularies. It is a tool, not a toll booth. An unavailable, incomplete or
low-value search must not prevent the person from creating a local capability;
publication can require stronger evidence of compatibility and reuse.

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
- `needs` describes requested operations and resources. Test relevant refusals and effects; conformance alone does not prove least privilege or confer authority. Broad development delegation may authorize these needs together.
- Host resources, credentials and network channels are explicit needs under the actual deployment boundary. Sharing the package never transfers the author's grants.

**Rules for lenses.** Durable native actions use registered verbs. A lens may author local rendering, gestures and transient state; it does not own the only copy of its subjects. Persistent view state has an explicit instance or participant scope. Foreign code requires an admitted runtime and bridge; no isolation claim follows merely from calling a surface a widget.

**Rules for migrations.** Required when a schema change or supersession affects retained instances; a UI-only source change does not need an invented data migration. Bidirectional where the schemas permit; where not, document the lossy direction and make it read-only.

**Rules for materialize.** A facet-def that promises a specialized portable file
form should define the bytes, fallback and re-import behavior. Generic versioned
export can make a new schema portable before a dedicated self-contained format
is worth designing.

**Output.** A `draft` extension entity.

### 4.4 Prove

**Precondition.** A draft with conformance cases (§7).

**Procedure.** Fork candidate native state and use a disposable guest when tests modify files, processes or external channels. A world fork alone does not isolate those resources. Build the exact source and dependency revisions. Run every applicable conformance case. Run the *platform* conformance suite for the affected facet families (must-ignore, projection at three budgets, export round-trip, authority refusal). Present results to the registry reconciler.

**Stop if** a required claim fails. Fix it or narrow the package's stated support.
A partially working build may remain an isolated candidate or explicit personal
experiment; it must not be presented as having passed the failed contract.

**Output.** Conformance results as a cast, attached to the extension.

### 4.5 Adopt

**Precondition.** Passing relevant evidence, admitted authority and a live
installation revision that still matches the candidate's base.

**Procedure.** Present the change and its recovery path. The person's explicit
request or standing development delegation can already authorize adoption; do not
ask again for each local revision. If the candidate requires authority outside that
delegation, request that specific expansion. Activation selects the exact tested
artifact, records the installation change and observes runtime startup.

Source adoption, data migration and expansion of authority are separate operations.
A failed or stale candidate leaves the working installation selected. The complete
development loop and receipts are in [[Native Development]] §5.

### 4.6 Share

**Precondition.** `local`, signed.

**Procedure.** Drop the extension in a room. The room's process admits it as `shared`. Other daemons find it in search; they stamp it by offer, fork it, or raise conflict objects on it. Adoption, forks, and dissent accrue as provenance on the extension.

**Stop.** The loop ends here for most extensions. Promotion (§5) is a separate process with its own actors.

---

## 5. Promotion and retrofit

### 5.1 The obligation: preserve established meanings

Transitions above `shared` must demonstrate the following for their declared support range:

- **Identity.** The extension's id and every facet-def's id are unchanged. Instances keep their facet type ids. Ids are never reused.
- **Readability.** Old instances read through the migration lens. A reader holding only the old def still reads its own instances; a reader holding the new def reads both.
- **Namespace.** On promotion to `core`, the new `core.*` def **aliases** the vernacular id; the vernacular def entity receives a `superseded_by` edge and stays resolvable forever.
- **Consent and policy.** An owner may pin a version, review offered updates or
  select automatic compatible adoption. Authority expansion and migrations remain
  separate decisions. An adopter who declines should keep a usable supported path.
- **Dissent.** An adopter who disagrees forks. The fork keeps its adopters and its history. The platform may absorb the fork later or lose the square that prefers it.

Reason. [[Objects and Facets|Objects]] chose must-ignore and independent versioning precisely so that a wrong or missing standard would have bounded cost. Promotion is where that cost is paid, and this is how it stays bounded.

### 5.2 Transitions

| From → to | Actor | Evidence | Mechanics |
|---|---|---|---|
| `shared` → `common` | a square's technical commons | ≥[2] independent implementations pass conformance; adoption in ≥[N] worlds; open conflict objects resolved or forked | added to the square's default bundle; registry marks `prefer` for search-before-mint; migration lenses from superseded defs generated and proven |
| `common` → `core` | the platform's compatibility process | working implementation, migration evidence and review proportionate to adoption | `core.*` alias or new contract; explicit adoption policy for supported predecessors |
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
7. **Promote to `core`** only if broad built-in interoperability justifies
   the compatibility cost. Most bridges should stop at `common`.

Reason for consensus-mapping rather than picking the biggest: the largest variant won on adoption, not necessarily on design, and forcing its schema on others produces forks instead of a standard.

---

## 6. Authority, humans, and the supply chain

### 6.1 What the registry admits

| Requested authority | Admitted when | Reason |
|---|---|---|
| `intent` | schema supported and caller authorized for the target | provenance identifies the claim's writer; it is not permission to edit anyone's data |
| `derived` | inputs and dependency declared | staleness must be computable |
| `reconciler` | the extension installs a reconciler with grants, at `local` or above, under the person's request or standing delegation | a facet naming itself `status` must not become a trusted observation |
| `adapter` | an adapter with a documented matching policy and an uncertain-match state | duplicate entities and silent merges are the failure modes |
| `system` | never for extensions | platform only |

The registry refuses reserved namespace misuse, unsupported contracts and authority beyond current delegation. It validates source/dependency identity and declarations; passing tests is evidence, not a grant. Prototype core definitions are not automatically ratified constitutional contracts.

### 6.2 What requires your person

| Action | Authorization |
|---|---|
| Draft source, build and inspect a candidate | The development task's delegation |
| Adopt or update a local package, lens, tool or skill | The person's request or standing development delegation |
| Add a reconciler or adapter | Supported runtime and admitted authority; existing delegation may cover it |
| Invoke an external or one-time effect | The applicable destination/effect policy; ask only when it requires a new decision |
| Expand host authority or change recovery | The protected human control path |
| Share an extension | Authorized sharing scope; recipients choose adoption and grant their own authority |
| Propose `common` | The square's technical process |
| Change a constitutional value or people's actual rights | Explicit human process proportionate to the stakes; see [[Constitution]] Article VIII |

Broad local development should feel fluid. Public compatibility and governance
obligations grow with actual adoption, rather than becoming prerequisites for a
one-off view. The model monoculture concern (§6.4) supports independent evidence for
shared standards; it does not require a new confirmation for every local edit.

### 6.3 Supply chain

- Bundles are signed over a **cast** of the extension; the signature is a facet.
- Offers carry the diff, the new conformance results, and the rationale for the change.
- Adoption of an offer runs the conformance suite in a candidate world-line first, then applies.
- `needs` changes are explicit. Existing standing delegation may cover them; otherwise activation requires a new grant. A changed effect contract never silently reuses old authorization.
- A handler's effective runtime authority must be disclosed. Scoped execution enforces its declared ceiling outside that runtime; the broad guest-root development profile does not claim per-package isolation ([[Security]] §3).
- A future registry may be a stewarded commons ([[Constitution]] Article VII,
  [[Ownership]] §3). It may index and refuse; altering a signed bundle would
  create a different version rather than rewrite the author's artifact.

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

Coverage to select for the features an extension actually provides:

| Category | What it proves |
|---|---|
| must-ignore | a reader without the extension preserves instances and shows the fallback projection |
| projection | each facet-def projects at [12/60/250] tokens; nothing shortens away uncertainty |
| export round-trip | materialize → re-import relinks by id and preserves provenance |
| authority | a writer without the admitted mode is refused |
| merge | the declared merge class behaves as declared under concurrent writes |
| migration | if superseding: every old instance reads through the lens; the lossy direction is read-only |
| external effects | each consequential handler's actual disclosure/retry contract is exercised; local operation identity is not mistaken for provider-side exactly-once behavior |
| overlay | participant-keyed instances never appear in another viewer's projection |

Cases may be stamped from the platform suite. A package with no custom data format does not need an invented migration case; a UI package does need actual interaction evidence. Cases are part of the bundle; changing them is a change to the extension.

---

## 8. Self-review before a stable or shared proposal

Answer proportionately. A “no” narrows the claim or keeps the work experimental;
it is not a ban on learning from an incomplete candidate.

1. Was discovery useful here, and were important compatibility choices recorded?
2. Did I reuse or extend an existing contract where that preserves the intended meaning?
3. Does every new subject remain generically inspectable, and are specialized
   human or agent projections supplied where the promised use needs them?
4. Are consequential effects and disclosures described from actual behavior, with
   unknown or unsupported semantics constrained rather than guessed?
5. Are requested capabilities explicit, admitted and exercised where relevant?
6. Is every schema change additive, or else `major` with proven migrations?
7. Does the promised export carry the bytes, provenance and dependency information
   needed for its stated recovery or portability claim?
8. Did every required conformance case pass in an appropriate candidate
   environment, with known failures kept visible?
9. Does the recovery path distinguish code rollback, data migration and external effects, without claiming to undo what it cannot?
10. Would I be able to adopt this extension from the bundle alone, without my own memory of writing it?

Question 10 is the real test. An extension that needs its author is not an extension.

---

## 9. Worked example: widgets

The loop, run end to end, compressed.

**Gap.** Over several sessions you have attached `{diagram_src, inputs, slider_state}` in soft semantics to nine documents, and hand-written "chart: p95 vs cache size…" into their summaries five times. Two signals fire. Need statement: documents need embeddable, data-bound, interactive diagrams that stay legible as text.

**Search.** Registry returns `core.doc` (blocks; no transclusion block), `alex.diagram-blob` (rendered bytes), `jo.notebook-cell` (execution coupled to document). Decision: extend `core.doc` at `minor` with an embed block; diverge with a new `widget.*` family. Rationale as in §4.2.

**Draft.** Four facet-defs, two handlers, one lens, one materialize rule, nine cases. `widget.state` keyed by participant. `widget.render` derived. `needs`: read bound inputs under the document's grants; write `widget.state[self]`. No network, no host.

**Prove.** Candidate world-line. Case c4 (stale on input change) fails on first run: render was served as current. Fix `depends`. All pass; platform suite passes.

**Adopt.** Projection to your person: "Adds interactive diagrams to documents. Diagrams are separate objects; your slider positions are private; the UI uses the admitted browser bridge. Restore the previous installation to undo the interface change; saved data remains. Requests no new authority." The standing development delegation authorizes adoption. `local`.

**Share.** Dropped in the research room. Two daemons stamp it. One forks to add a `widget.controls-shared` grant for co-driving a slider. That fork becomes an offered update with the changed sharing contract explicit; adoption and any new grant follow the recipient's policy.

**Promotion.** Months later, four squares use it; three independent implementations
pass the suite; a `common` proposal passes rough consensus. It stops there.
Nobody proposes `core` because broad built-in compatibility is not needed—
`common` is enough, and enough is the goal.

---

## 10. Invariants

1. Reusable vocabulary and behavior have a retained package identity; transient
   exploration need not pretend to be a stable extension.
2. Use discovery when it is likely to improve reuse; record non-obvious
   compatibility or divergence choices.
3. Adoption status, if implemented, is evidence-backed rather than self-awarded.
4. A package does not claim support for a required check that failed.
5. Adoption requires the person's request or standing delegation; authority expansion is explicit.
6. Authority is admitted by the registry, never declared by the bundle.
7. Promotion preserves useful identity, readability and owner-selected update
   policy; incompatible change remains explicit.
8. Definition retirement and payload retention preserve promised references and
   follow explicit erasure policy; deprecation is a strong default, not an excuse
   for permanent retention of every payload.
9. Changed needs and effect contracts are explicit; tests do not grant authority.
10. If a `common` tier is adopted, its evidence includes contributors or
    implementations beyond the proposer rather than self-certification.
11. The candidate tier model expects most extensions to remain local or shared;
    low governance load is a design goal, not a required ecosystem shape.

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
**Extension** — an entity carrying the extension profile; executable extensions are native source packages.
**Offer** — an update presented with diff, results and rationale; adopted through
the owner's explicit choice or standing compatible-update policy.
**Registry** — the stewarded commons that indexes extensions, admits authority modes, and sets status from evidence.
**Search-before-mint** — the rule that existing definitions are found and preferred before new ones are created.
**Supersede** — to replace a definition while leaving it readable and resolvable forever.
**Tier** — the status of an extension: draft, local, shared, common, core.

---

*This document preserves a complete growth model so it can be tested, criticized
and reused. [[Design Commitments]] preserves the ends; the mechanism remains open.*
