# Foundations R8: forkable futures and the smallest useful object foundation

23 September 2026. Exploratory design research, not a specification, benchmark, implementation claim or adoption decision. No code or runtime changes. This note reconsiders R7 using Alex's new drafts and peer critique.

## Reading receipt and the changed question

Before further research I read these files in full:

- `C:/Projects/Agora/docs/docs_2/Agora.md` (19,607 bytes).
- `C:/Projects/Agora/docs/docs_2/Dynamic Desk.md` (5,773 bytes).
- `C:/Projects/Agora/docs/docs_2/Current Implementation.md` (1,766 bytes).

`Current Implementation.md` is an unfilled evidence template. It establishes no runtime behavior. `Agora Constitution.md` in that directory is empty (0 bytes). I did not fill or edit any of these documents. Applicable Agora4 AGENTS were read in R7; this round changes only its specifically authorized research note.

Three implications change or qualify R7:

1. **Everyday partial adoption, not merely data survival.** The freedom to fork a tool or place means someone should adopt a useful part without accepting an unwanted redesign or becoming its maintainer. Retaining facet records after uninstall is helpful but far short of this product goal. Live, composable definitions deserve more weight than my R7 emphasis gave them.
2. **Common referents do not require common total descriptions.** The two park profiles can agree which place they concern and share some content while disagreeing about curation, activities or assertions. A canonical schema for the whole park would introduce unnecessary coordination and possibly institutional power. A uniform identity system cannot decide which claims are true or who speaks for the park.
3. **A comprehensible foundation must remove work.** Schema, interface, handler, package, instance and revision distinctions can all be real without becoming six mandatory authoring steps. 'Use makes later changes easier' is a stronger criterion than 'the data model can encode them.' I withdraw a facet-first architectural preference until it beats competent alternatives on ordinary reuse and change.

System/visual/object remain working contexts over the same world. Shell/application/object remain composition responsibilities. These two axes do not choose a storage model or require per-application authoring studios.

## Primary-source research and limits

### Ingalls: uniformity protects modularity, not a fixed representation

Read the complete text of Daniel H. H. Ingalls, [Design Principles Behind Smalltalk](https://archive.esug.org/HistoricalDocuments/Smalltalk80/DesignPrinciples/DesignPrinciples.html), BYTE, August 1981, reproduced with permission. Figures' captions were read; figures were not separately inspected.

Ingalls connects individual comprehensibility with a small general core, uniform reference and messaging, and components that do not depend on one another's internals. Polymorphism lets representations differ behind a shared protocol. His treatment includes files and subsystems rather than requiring their elimination. The final section explicitly says protocols have not been formalized and are then maintained by convention.

**My inference:** do not turn the uniform-framework aspiration into a requirement for every application's state to use one public shape. Nor does a common verb spelling suffice: the shared behavior must be understandable. The source does not establish that a 1981 single-machine programming environment solves decades of independent community forks.

### Cambria: a serious interoperability candidate, with an admitted counterexample

Read the complete main essay and all three appendices of Litt, van Hardenberg and Henry, [Project Cambria](https://www.inkandswitch.com/cambria/), October 2020. Interactive demonstrations were not operated; this is author-reported research evidence, not a reproduction.

Cambria relates evolving schemas through composed transformations and explores collaboration between different application versions. Its integration retains writer schemas and translates on read. The authors explicitly expose a faulty scalar/array deletion implementation and explain why compatibility can trade off consistency, preservation of unseen data and predictable local actions. They also identify transformations whose intended operation cannot be determined from structural field editing alone.

**My inference:** schema translation deserves a real place in the comparison, but it cannot remove decisions about what an edit means. A graph of mechanically composable adapters is not a graph of automatically composable human agreements. Decades-long divergence may require coherent shared subsets rather than complete translation.

### Fielding: resource identity and representation can evolve separately

Read the conceptual derivation and resource/representation/connector portions of Roy Fielding's [dissertation chapter 5](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm), especially sections 5.1 and 5.2. The complete dissertation was not read. Diagram captions were read; diagrams were not separately inspected.

The chapter distinguishes a resource from particular representations, and argues that a uniform interface supports independent evolution. It explicitly acknowledges costs: generic representations can be inefficient for specialized interaction, and durable identification still depends on maintaining the naming relationship. Representation negotiation does not dictate internal storage.

**My inference:** an object could be a durable resource with several inspectable representations and operations, without being a bag of globally registered facets. This supplies a serious candidate for the common desk. It does not mean all native editing should become HTTP, or that network requests belong in every pointer gesture.

### Historical correction kept outside the user drafts

The new Agora draft's statement that Emacs lacked undo is false as written: the [GNU Emacs manual](https://www.gnu.org/software/emacs/manual/html_node/emacs/Undo.html) documents buffer undo and selective undo. Its bankruptcy assertion was not substantiated and should not support an architectural conclusion. I made no changes to the draft and do not guess which historical system the passage intended.

## Five-year thought experiment: two park profiles, one useful feature

This is an imagined walkthrough, not an executed test.

A gardening club and a running club refer to the same park. They share an agreed place reference and selected public facts. The gardeners have bed histories and watering notes; runners have routes and time trials. Both use photos and a public guestbook, but curate different front pages. Someone improves the guestbook's keyboard accessibility. Each community wants that improvement without changing its map, calendar or moderation policy.

### Durable facet records

The park subject holds or links to independently identified aspects. Public guestbook material can have its own contract and lifetime. A feature implementation binds to that aspect and can be adopted separately. Queries can combine admitted aspects without asking each application to export a new bundle.

This works well if facet boundaries match actual reusable parts. It fails if guestbook behavior requires a new whole-park schema, if the interface merely wraps app-private state with another metadata copy, or if each community mints synonyms faster than useful common contracts emerge. The cost is not just bytes: someone must understand which of many similar facets a tool actually supports.

### Live prototypes and shared definitions

The gardener copies a working park profile, changes its arrangement, and retains references to the common park and guestbook. An accessibility component can be replaced where it is used. The reference graph makes direct adaptation tangible, and local override can be easier to grasp than publishing a package.

This works well when inherited behavior is coherently factored. It fails when tomorrow's parent change alters moderation or deletion semantics along with keyboard handling. Copying a live interface can retain unintended control references; copying the whole graph can duplicate data the user intended to share. A live graph still needs understandable 'shared with' and 'my version' behavior. It does not automatically choose those relationships.

### Resource/document-centered composition

Each profile is an editable document or composition that links to the park and embeds a guestbook service/component. The documents can use different internal schemas. The adopted accessibility component needs only the guestbook's small operation protocol; map and calendar representations remain private to their tools.

This may provide the same everyday flexibility with fewer public type concepts. It fails if embedded features are opaque islands, if their configuration cannot be inspected and copied, or if cross-component selection and edits repeatedly lose context. A conventional plugin architecture that avoids these failures is a serious candidate, not an inferior baseline by definition.

All three can satisfy the five-year example. The discriminating issue is how much new explanation, adaptation and ongoing maintenance the second community needs, not whether the diagram uses objects.

## Twenty-year thought experiment: the meaning and machinery change

This is also an imagined pressure case. Twenty years is a horizon for questions, not a forecast.

The park has changed boundaries. One club dissolved, another split, the platform runs on different machines, and tools disagree on reservations: the old guestbook marks attendance; newer tools reserve capacity with cancellation rules. Historical messages must retain what they meant. A person wants an old page's layout but current accessibility and a new reservation panel. Some old code cannot run anymore.

**Facet model:** retained subject IDs and exact historical formats help distinguish old claims from current ones. New aspects can coexist. Its worst outcome is a museum of nominally preserved facets that only obsolete packages can interpret, surrounded by translators nobody maintains. Independent schema names alone do not provide shared meaning or recover the necessary old assets. Keeping every format forever is not the same as useful access.

**Live model:** direct access to tools and their definitions can let inhabitants adapt their environment incrementally. Its worst outcome is inherited history becoming an inscrutable graph of overrides, environment assumptions and accidental shared behavior. Preserving a heap or source does not preserve operating resources. Conversely, automatically replacing every dependency to keep it runnable can alter what old interactions mean.

**Resource/document model:** widely understood representations and explicit references can keep human material useful after applications disappear. Local tools can evolve behind compatible operations. Its worst outcome is a pile of readable exports that cannot resume the living shared activity, plus links whose stewards disappeared. An exportable snapshot is valuable but does not itself preserve community continuity.

No candidate can guarantee perpetual operation without stewardship. The relevant comparison is which maintenance obligations people can understand, share and transfer. Long-term continuity includes keeping useful representations and explanations, replacing implementations and allowing communities to diverge; it cannot simply mean never changing anything.

A disputed park boundary also demonstrates a limit of technical normalization. The two groups may share a referent while retaining differently attributed boundary claims. Neither a shared object ID nor an adapter should silently decide they agreed on one polygon.

## What can be removed now

The draft asks for a humble general foundation. The following are candidates to omit until a workflow proves their value:

- **A mandatory global facet registry for informal work.** Local records, notes and annotations can begin without a published type. Retain interpretation where necessary; publication and standardization can follow actual reuse.
- **A universal taxonomy of object kinds.** Familiar kinds and profiles can offer defaults. They need not constitute one exclusive class hierarchy or confer correctness and authority.
- **A generic bidirectional conversion engine as a prerequisite.** A few explicit domain representations and operations may be easier to maintain. Add translation when it genuinely reduces repeated integration work.
- **Package lifecycle machinery for every local definition.** A toolbar arrangement or appearance rule can be an editable retained definition. Runtime installation and current interaction generation matter where code is actually activated; they need not be a user-visible process for changing spacing.
- **Every internal item as a top-level identity.** Preserve subject, occurrence and anchor identities where reference or independent lifetime requires them. Do not make each widget field a permanent world citizen.
- **Universal deep-copy and universal selective-merge semantics.** Ordinary duplicate/fork can have domain-defined behavior. A global graph language is not needed before a concrete copy boundary proves insufficient.
- **One canonical schema for a place or application.** Shared features can agree on a narrower protocol while keeping their own representations and interpretations.

What I would tentatively retain is an understandable reference to a subject, useful inspection, discoverable operations, retained accepted changes with recovery appropriate to the domain, and editable definitions at useful boundaries. These are evaluation obligations; they are not yet a complete kernel schema. Facets, resource representations or a live graph can each implement them.

Keeping the interface small should also reduce hidden implementation machinery. Renaming a forest of mandatory registries 'automatic' would not meet the individual-comprehensibility test.

## Peer challenges, replies and resulting changes

I challenged Editing on whether immutable nominal contracts accumulate twenty years of adapter obligations and whether a central schema registry could be removed. Editing agreed that local representations can remain informal, while interpretation cannot simply be discarded: a date's time semantics must live somewhere. Its concrete partial-adoption case is a guestbook component depending only on the guestbook contract, not on a whole-park upgrade. I adopt that as a sharper test.

Editing challenged live inheritance in return: how does a fork inherit future fixes without silently inheriting changed deletion or visibility? My answer is limited. A retained shared definition can carry compatible changes under the user's chosen update policy; a semantic change needs an intelligible adoption boundary. A producer's compatibility label alone is not proof. A purported accessibility fix entangled with changed moderation cannot be automatically separated by choosing a better object ontology. We should not promise otherwise.

I challenged Media on whether pinning every definition's full transitive closure creates a package-manager experience. Media withdrew that blanket prescription. Simple definitions can be retained revisions with local overrides; only semantically relevant dependencies need a compatibility policy, usually summarized as shared defaults. Runtime replacement still needs its real interaction boundary.

Media's strongest counterexample to facets is a capable editor plugin architecture that already shares data, commands, transactions, selection and undo. Extracting those internals into world facets might increase schema and adapter work without improving one ordinary task. We agree to judge a shared range-comment feature by independent reuse in a second unrelated editor. A small comment protocol may be the entire common substrate for that feature. Each editor still owes a locator/mutation mapping. Shared action semantics, shared algorithms and special adaptation are three different quantities.

Media also cautions that 'comment' might mean local annotation in one tool and permission changes, collaboration and notifications in another. A familiar verb cannot conceal that difference. Offer a coherent common subset or a specialized operation; do not count the common spelling as interoperability.

## Strongest counterexample and explicit reconsideration conditions

**Against my R7 preference:** a well-designed document editor with composable plugins can let an ordinary person adopt the guestbook or comment feature, preserve their existing layout and history, and share content with another tool through a small protocol. If exposing open world facets adds nominal definitions, migrations and adapter code but removes no meaningful step, my proposed foundation is unnecessary for that task. This is not answered by adding more invariants to the facet model.

**Current position:** I no longer privilege facets. I tentatively favor a small common reference/inspection/action boundary, with the representation choice still contested. Facets may win as reusable public aspects; they need not own every internal representation.

I would favor facets if separately authored tools repeatedly reuse useful aspects with fewer special adapters and less user explanation than the document/protocol candidate, while local invention remains low-ceremony. I would favor live prototypes if extracting and adapting a running feature is substantially easier without making update effects and copy relationships harder to understand. I would favor resource/document composition if it achieves the same partial adoption and shared work with fewer permanent concepts and better useful access when old code disappears.

These are proposed discriminating comparisons, not measured thresholds or benchmark results. The next revealing design exercise is deliberately small: two independently authored editors, one reusable range-comment tool, a local appearance customization, and a later incompatible comment-policy change. Record every adapter, automatic inference and user decision. The model that merely preserves everything but makes normal work tedious should lose.

## Second pressure case: an informal plan becomes a workspace

The coordinator rightly challenged a possible misreading of the plugin baseline: winning an implementation comparison does not excuse losing Agora's coherent world. Independent shared subjects, contextual discovery and verbs, authored visual rules, partial adoption and useful fallback remain the product obligations. A collection of opaque applications that cannot meet these is not an adequate baseline.

The coordinator also brought an actual-use observation from Embark: composing widgets did not by itself preserve planning thought, whereas tools hosted in an outline retained context. I did not independently read that Embark study during this round, so this is an attributed peer finding, not my primary-source verification.

A candidate small invariant is **continuity of authored context**: adding or changing a capability extends an existing working place without implicitly replacing or relocating its user-authored material, meaningful references or ongoing work. That material remains available for continued editing from the current context. Merely retaining the old prose in an archive is too weak.

Imagined example: someone writes a loose plan with uncertainties, names, dates and a sketch. They turn one phrase into an addressable task and add a date instrument to another. A view rule shows unresolved tasks beside the plan; subsequent matching items appear automatically. The original questions and reasons remain present. This need not require declaring a published schema, converting the note's kind to workspace, or hand-binding each new task's appearance. A board or spatial composition could preserve the same relations as an outline; no particular container shape follows from the invariant.

Now remove the task instrument. The authored plan and its meaningful references should remain usable in that same working place, even if specialized behavior becomes unavailable. Conversely, explicitly asking to reorganize or replace the plan is allowed; the invariant concerns implicit damage caused by capability adoption.

This case complements cross-editor comment reuse. The first asks whether independently built tools can share a feature cheaply; this one asks whether invention during ordinary thought preserves the person's work. A candidate should not win merely because one of those tasks is outside its chosen measurement.

## Latest-reading receipt after concurrent draft edit

23 September 2026, final bounded alignment check: reread the ENTIRE current `C:/Projects/Agora/docs/docs_2/Dynamic Desk.md`. Verified length **5,779 bytes** and SHA256 **5513206EA05472C9D9EEEB8AE273F2CB77F3D3956AF52BA5F54A8BA883AA6CC9**. The earlier 5,773-byte receipt above remains an honest record of the first snapshot and is not replaced by this one.

The revised Verbs and capabilities section removes its two introductory placeholder questions and refines the prose about context-relevant vocabulary becoming visible and reuse across objects/appearances. This does not change the analysis. It reinforces the existing distinction between shared operation meaning, shared implementation where appropriate and the work of adapting representations. Tentative object/facet status, the visual bridge, continuity and individual comprehensibility remain unchanged. No user draft was edited by this researcher.
