# Review coverage

**Dated documentation audit · September 9, 2026; restoration disposition added
September 10.** This maps the 56 review entries to their active design homes. It
is an adoption record, not another set of future requirements. The exact runtime
API remains in [[Runtime Guide]], and [[Design Commitments]] defines the status
vocabulary used by the restored long-form documents.

The September 10 restoration brought back the detailed workflows, alternatives,
failure cases and moral rationale that the compressed rewrite had removed. It did
not reinstate the review's false universal claims. Where a mechanism was too broad,
the active notes now classify it as a current invariant, a local contract, a
candidate mechanism, an open question or a rejected universal. This preserves the
reasoning without promoting every old proposal back into law.

It also carries forward four substantial documents that existed only on the older
`docs` line: [[Personal Lenses]], [[Executable Components]], [[Astra Harness]] and
[[Security Addendum]]. Their status banners distinguish verified behavior of that
prototype from the current Agora3 runtime. The implemented lessons remain visible;
their obsolete operation names and limits do not become current contracts.

| Review | Former claim or concern | Revised discussion |
|---|---|---|
| 01 | One literal or one binding owns a target | [[Presentation and Operators]] |
| 02 | One presentation engine must resolve all geometry | [[Presentation and Operators]] |
| 03 | All dependency graphs must be acyclic | [[Objects and Facets]] |
| 04 | Pure derivations cannot perform I/O or model calls | [[Objects and Facets]] |
| 05 | Reading a value must never execute authored computation | [[Objects and Facets]] |
| 06 | Every evaluator must run outside the host / in the guest | [[Presentation and Operators]] |
| 07 | Code versions are pinned while data can be live | [[Objects and Facets]] |
| 08 | All maintained layout must be derived, never durable placement | [[Presentation and Operators]] |
| 09 | Meaning may influence layout, never the reverse | [[Presentation and Operators]] |
| 10 | Appearances must be separate scene records, never facets | [[Objects and Facets]] |
| 11 | One flat board and one global z-order | [[Presentation and Operators]] |
| 12 | Measurement and arrangement never interleave | [[Presentation and Operators]] |
| 13 | Every operator is an idempotent retraction | [[Presentation and Operators]] |
| 14 | Intersecting done-sets guarantee convergence | [[Presentation and Operators]] |
| 15 | All operations minimize movement under one global metric | [[Presentation and Operators]] |
| 16 | The input type is the sandbox; property tests prove the contract | [[Presentation and Operators]] |
| 17 | Integer arithmetic and the same build remove agreement testing | [[Presentation and Operators]] |
| 18 | Attachment order, a small round cap, and newest-hold suspension | [[Presentation and Operators]] |
| 19 | A single yields flag defines manual interaction | [[Presentation and Operators]] |
| 20 | Undo is delta inversion; every delta animates | [[Presentation and Operators]] |
| 21 | Four verbs and parameterized families are the entire interface | [[Presentation and Operators]] |
| 22 | Authoritative native writes use an authenticated gateway and journal | [[Security]] |
| 23 | Replay reconstructs native state without repeating effects | [[Security]] |
| 24 | Protected authority and recovery stay beyond authored code's control | [[Security]] |
| 25 | Broad guest development authority is the starting profile | [[Security]] |
| 26 | Everything is either pure derivation, observation, or maintained effect | [[Reconcilers]] |
| 27 | Reconcilers take one smallest step and are never orchestrated | [[Reconcilers]] |
| 28 | One reconciler is the sole possible observer of a status | [[Reconcilers]] |
| 29 | Each verb has one effect class; external effects are always one-time | [[Security]] |
| 30 | Grants never survive rollback | [[Security]] |
| 31 | Every rung needs its own decision; approvals are one-use | [[Security]] |
| 32 | Human controls and agent tools derive from one list | [[Security]] |
| 33 | No behavior may depend on a kind-tag | [[Objects and Facets]] |
| 34 | Every facet renders to pixels and tokens | [[Objects and Facets]] |
| 35 | Bytes must live in a filesystem; file and facet can never both be writable | [[Objects and Facets]] |
| 36 | Facets version independently and use declared merge classes | [[Objects and Facets]] |
| 37 | Copy is not an operation | [[Objects and Facets]] |
| 38 | Grants and all overlays never copy or publish | [[Objects and Facets]] |
| 39 | Every entity has exactly one log of record | [[Objects and Facets]] |
| 40 | Unknown facets are preserved; unknown action-critical constraints block | [[Objects and Facets]] |
| 41 | Every conflict must become an entity | [[Objects and Facets]] |
| 42 | No client enumerates the world; all selection uses a fixed declarative query vocabulary | [[Objects and Facets]] |
| 43 | New behavior must use the full source/build/install loop | [[Native Development]] |
| 44 | Never adopt a partially passing bundle | [[Native Development]] |
| 45 | Capability-creation tests must start with the tools absent | [[Native Development]] |
| 46 | Search must precede minting, with rationale and reuse thresholds | [[Native Development]] |
| 47 | Every facet definition needs its own self-contained file form | [[Extensions]] |
| 48 | Updates are always offers, never pushes | [[Extensions]] |
| 49 | A single heat field unifies attention, layout, memory, and identity | [[Agora Spec]] |
| 50 | Never build platform clones; native replacements need object-specific justification | [[The Web]] |
| 51 | All web anchors target frozen casts, never live documents | [[The Web]] |
| 52 | Publishing is a read grant on a collection | [[The Web]] |
| 53 | Agora remains useful without JEFF and independent of renderer/input | [[Agora Spec]] |
| 54 | Conversation never blocks; workers are ephemeral and JEFF persists | [[Native Development]] |
| 55 | The witness is irreversible; everything important is recorded | [[Constitution]] |
| 56 | Core technical vocabulary requires constitutional promotion | [[Constitution]] |

## Concrete friction and experiment findings

All seven current constraints from the review—whole-package replacement,
self-contained browser source, split execution paths, broad 1,000-object action
inputs, object-level revisions, polling and note-attached appearance—are listed
in [[Native Development]] as measured directions for improvement, not permanent
requirements.

[[Presentation and Operators]] and [[Native Development]] retain the experiment's
additional findings: cheap native intent, an executable escape path, inspectable
actual rendering, shared action discovery, selection/focus/draft continuity and
less duplication in extension deployment. Exact composer size, the broken human
registry lookup and selection-loss failures are recorded as evidence rather than
hidden behind successful agent actions.

The old commitments to a universal heat model, mandatory native-product novelty,
one publication mode, immutable witness retention, fixed worker topology,
constitutional technical promotion and predetermined governance/organization are
now explicitly rejected or reframed as options in the restored detailed notes.
Their motivating problems—attention abuse, coherent publication, continuity,
accountable power and practical exit—remain active. Rights-oriented values remain
in the unratified [[Constitution]]; this documentation revision changes neither
actual license terms nor deployed guarantees.
