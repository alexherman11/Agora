# Media R8: does the substrate make the next small change easier?

Exploratory design discussion, 2026-09-23. No implementation or runtime changes, tests, original-document edits or Claude contact. This note revises rather than finalizes R7.

## Full-reading receipt

Read completely:

- C:/Projects/Agora/docs/docs_2/Agora.md (19,607 bytes).
- C:/Projects/Agora/docs/docs_2/Dynamic Desk.md (5,863 bytes).
- C:/Projects/Agora/docs/docs_2/Current Implementation.md (1,766 bytes).

C:/Projects/Agora/docs/docs_2/Agora Constitution.md is empty (0 bytes). Current Implementation is an unfilled template, not current evidence. The phrase 'new Agora Constitution.md' does not identify an existing literal filename here. No source claims below are inferred from either empty/template document.

Three revisions to R7 follow from the actual drafts. Retention and installation are necessary but insufficient: additions must reduce later authoring work. Reusing a verb means coherent behavior and preferably shared code, not just one dispatcher with type-specific branches. Feature-level adoption and contextual discovery deserve priority over a generalized installation framework. Familiar complete applications and opaque conventional software remain valid inhabitants.

## My revised position

A stable identity/reference layer, reusable protocols and a modest shared interface toolkit can satisfy much of the Dynamic Desk without decomposing every application's internals into world facets. Typed facets remain useful where durable information needs independent inspection, reuse or survival. They are not, by themselves, the mechanism that makes a tool reusable.

An application can keep its rich internal representation while exposing a meaningful protocol such as addressable selection, comments or arrangement. A new tool can target that protocol. Its first author implements the tool once; each genuinely different representation pays for a provider/adapter where necessary. That is a real improvement if a later tool reuses those providers. It is only relocated work if each tool needs fresh adapters.

System, visual and object are navigable working contexts. They should present related subjects and a familiar verb vocabulary, not expose separate specialist studios as an entrance requirement. System manages installed applications and providers; visual handles occurrences, views and their definitions; object handles useful information and organization. Context narrows the default vocabulary but does not hide capabilities merely because their windows are closed.

## Three different meanings of reuse

1. **Shared algorithm:** sort an ordered collection through iteration/comparison, or tile a selection through geometry and placement protocols. The same implementation can act on new conforming targets.
2. **Shared semantic protocol:** add a comment to an addressable range. Different editors supply locator and accepted-operation behavior; one comment tool can reuse them. Provider work remains real.
3. **Common word with different effects:** replace a word, replace an application, replace an external attachment. A shared name may be readable, but does not imply the same algorithm, transaction or compensation.

The first two can deliver the stated promise. The third needs honest specialization. A rectangle is enough input to calculate a tile proposal; it is not evidence that an editor permits moving that thing, or that moving a task means rescheduling it. Generic mechanics should ask a target protocol to admit the proposal, while the application owns its actual placement policy.

## Historical mechanisms, read directly

Ingalls's [Design Principles Behind Smalltalk](https://archive.esug.org/HistoricalDocuments/Smalltalk80/DesignPrinciples/DesignPrinciples.html), BYTE 1981, explains message dispatch as avoiding a central operation that knows every representation. Its concrete examples include a new vehicle satisfying an existing simulation protocol and one sorting method reusing comparison behavior for text and numbers. It also acknowledges that protocol consistency in Smalltalk-80 was a matter of style, not a formalized guarantee. This supports a reusable-protocol experiment; it does not prove that arbitrary same-named verbs have interchangeable meanings. Full article read; its historical aspirations are not current Agora evidence.

The [CLIM 2.0 User's Guide, presentation translator mechanisms](https://www.lispworks.com/documentation/lwu41/climuser/GUID_138.HTM), 1998, describes matching displayed presentations to the current input context and command table, testing applicability, generating documentation/menus and dispatching the chosen translator. Priorities and type specificity resolve competing candidates; equal-priority choices can be unspecified. This is a concrete route to contextual discoverability rather than listing every command. Agora should make ambiguity visible or use an explicit adopted default. Some CLIM applicability paths may evaluate translator bodies; a desk should not assume such discovery is automatically pure, cheap or safe.

HyperTalk reference material was searched, but the primary reference-stack PDF fetch failed because of its size. This note does not rely on a claim about HyperCard mechanisms. CLIM and Smalltalk supply the historical mechanisms used here.

## A fair conventional baseline

The official [ProseMirror introductory guide source](https://raw.githubusercontent.com/ProseMirror/website/master/markdown/guide/intro.md) describes separate document/state/view/transform modules, transactions, replaceable extension modules, plugins, commands exposed through keys or menus, and undo built through transaction observation. This is a serious baseline. A rich editor is not necessarily a monolithic blob with no reusable operations.

The baseline for the experiment should be a competent application toolkit with an explicit public plugin API, a shared command registry, durable document identities and a well-engineered component library. Give it the same rendering/editor engines and the same human/agent command access. Do not compare Agora's best implementation to deliberately isolated apps.

No single step of notebook -> date -> comments -> another view uniquely proves the necessity of global facets. Agora earns additional general machinery only if independent reuse, feature adoption or continuity is materially easier across applications after charging for all adapters and lifecycle work. A protocol-compatible plugin ecosystem might itself be an adequate realization of the desired substrate.

## Pressure cases and what would count

| Case | Plausible mechanism | Evidence needed; remaining limit |
|---|---|---|
| Add a comment tool to an existing editor | Tool contributes action, small panel and bindings to a range/comment protocol | A second independently built editor adopts it without editing the tool or host. Count its locator/provider code; do not use identical editor implementations as the only proof. |
| Fork one feature | Copy a named panel definition or policy contribution; select it as a local override while other features follow their defaults | Upstream editor improvements still arrive. Forking range semantics may cross history/storage invariants and require a larger fork; a feature label cannot create a safe boundary. |
| Custom layout without per-app JavaScript | Named slots, reusable controls, row/column/grid/split layouts and target placement protocols | Recompose an existing app and a new app through definitions, without bespoke event/render code. New interaction primitives can still need executable implementation once. |
| Opaque game | Ordinary managed window/resource with focus, launch and placement where supported | It works comfortably without claiming its interior is editable native data. The adapter does not manufacture player/game state from the window title. |
| Update during input | Keep active input interpretation and draft; patch compatible interface changes or defer incompatible replacement | Actual keyboard composition, selection, pointer capture and held gesture survive in a real browser. Retaining JSON or keyed element identity is insufficient evidence. |
| Discover a useful verb | Inspect current target/context; return short applicable actions with purpose, effects, examples and reasons unavailable | A person or smaller agent finds the new tool without reading a global manifest inventory. Search can expand beyond defaults; hidden windows do not imply absent tools. |

## Strongest counterexample to my preferred approach

Take a mature editor whose comments, collaborative ranges, permission checks, undo and notifications already work together. A protocol layer exposes 'comment on selection', but the selection's meaning changes under concurrent edits; adding the comment may create a shared thread and send notifications. A second editor offers only local annotations on immutable text. If the shared tool quietly treats both as equivalent, it lies. If it grows enough special cases to cover everything, it becomes a second application framework. If the protocol shrinks to 'store opaque payload', it no longer provides useful reusable behavior.

The response is to choose a coherent, useful contract and specialize where effects differ. A local anchored annotation can be reusable without promising shared discussion. Do not demand a universal annotation protocol before the first useful tool. The hard question is whether those coherent contracts recur often enough to amortize the adapters. The experiment must be allowed to answer no.

## Feature adoption without a package-manager experience

I amend R7's generation emphasis. Simple local layout or toolbar definitions do not need their own generalized installation generation. A retained definition revision, references to shared defaults and explicit local overrides can be enough. Active runtime replacement and held gestures still need a stable interpretation; that is a lifecycle obligation, not a reason to show a dependency solver for every adjustment.

An ordinary operation might be 'use my comment panel here'. Inspection can later reveal what supplies it, its local changes and what upstream changes it follows. If compatibility fails, retain the working component and explain the specific disagreement. Independent feature choice is possible only where the implementation exposes a coherent replaceable boundary. No facet structure guarantees arbitrary surgery on application internals.

## Simplifications worth testing

- Start with a few useful shared protocols whose need is demonstrated, not an exhaustive universal trait catalog.
- Keep editor internals private unless independent use requires a durable shared representation.
- Use ordinary interface components with inherited defaults; require only overrides for common customization.
- Prefer one command definition consumed by text, menu and control binding; keep textual syntax friendly without making strings the authority boundary.
- Store useful identities and semantic changes; do not make every pointer sample, temporary control or internal function a native object.
- Separate OS-native software from world-native applications and keep the best available adapter honest about its coverage.

## Comparative thought experiment, not a build plan

Freeze two implementations: a conventional plugin/toolkit baseline and a candidate Agora protocol/facet bridge. Give both an editor and a collection view. Add comments in one, apply the tool in a genuinely different editor, customize its panel, change an unrelated upstream editor feature, then add a layout policy to mixed appearances. Include a draft and a held gesture during adoption. Introduce one nonconforming app or opaque game.

Measure initial versus second/third-extension authoring work, number of host/core changes, provider code, policy choices, repair after update, discoverability and interaction failures. Separate what an extension author must implement from what an ordinary person must decide. Fewer schema lines do not count as success if more hidden adapters appear. More retained metadata does not count if ordinary customization gets harder.

The object substrate wins if modest additions compound into lower marginal effort and preserve working continuity. If a shared toolkit and compatible plugin protocols achieve that more simply, they deserve to become the substrate rather than be dismissed as insufficiently object-oriented.

## Peer challenge and coverage

Foundations challenged whether pinned closures make the desk an incomprehensible package manager; this note narrows generation requirements to actual runtime/interaction boundaries. Editing challenged whether existing document plugins already achieve the proposed benefits; the comparison above accepts that challenge and charges for provider work. Foundations agreed a shared range-comment protocol could be the entire shared substrate for that task, with editor representations private. My reply retained facets where durable interoperable records earn their place, without demanding decomposition of editor internals.

New direct reading: the three complete docs_2 drafts listed above, Ingalls's full article, CLIM translator mechanism section and example index, and ProseMirror official guide introduction. R7's source inspection remains a dated static checkpoint; no fresh runtime was examined here. Historical sources explain mechanisms, not proof of layperson mastery or present implementation.

## Root cross-review: ordinary object edits without view wiring

Foregrounding protocols must not make every routine agent compose views. The smallest proposed binding mechanism is an authored view definition with four pieces: an object/collection selection, a projection/provider and its relevant inputs, default component mappings, and stable occurrence identities with local overrides. The shared bridge invalidates affected projections when relevant objects or query membership change. This is a proposal, not a claim that Agora4 currently has general subscriptions.

For example, a collection view uses its installed default tile projection. The agent adds an image to that collection or changes its title; the visible tile appears or updates without any visual-definition edit. A view that includes the same image twice needs distinct occurrence identities, not only a globally unique object id or a list index. Appearance records retain the subject binding, working context and local placement/presentation overrides. The default definition supplies unspecified choices. Aligning one occurrence changes its placement without changing the image or the other occurrence.

A specialist application supplies a useful projection/provider once for its protocol or material family. Its private editor representation need not become a universal document tree. Missing special rendering can fall back to honest identity, description, capability availability and resource metadata. It must not claim an empty object simply because its preferred component is absent.

The critical failure is incorrect dependency or identity declaration: a provider forgets that the caption depends on author metadata, so routine edits leave a stale tile; or rows keyed by list index reorder and an active draft becomes bound to the wrong subject. These require dependency-coverage and occurrence-continuity checks. Inferring every dependency from arbitrary implementation code is not promised. For small bounded views conservative invalidation is a viable simpler starting point, with precise dependencies introduced only when performance warrants them.

## Latest draft alignment receipt

Reread C:/Projects/Agora/docs/docs_2/Dynamic Desk.md completely after root reported a concurrent edit. Latest inspected length: 5,779 bytes. SHA256: 5513206EA05472C9D9EEEB8AE273F2CB77F3D3956AF52BA5F54A8BA883AA6CC9. The earlier 5,863-byte reading receipt above remains a record of the original snapshot.

The current verbs section removes its two placeholder questions, changes relevant context verbs from 'should be visible' to 'should become visible', and makes a small punctuation adjustment around object/appearance reuse. No substantive conclusion changes. The analysis already treats discovery as contextual and adaptive, and tests shared behavior/code rather than common naming. The bridge/default-binding proposal still addresses routine object edits without visual orchestration. No other work was performed for this alignment check.
