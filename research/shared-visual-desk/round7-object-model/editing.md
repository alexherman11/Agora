# Editing: a subject that outlives its editors

2026-09-23. First-pass exploration, not a selected specification or implementation. Static source review against Agora4 HEAD `f717590dd2033b9fad26dbd09c8822449eff7cdb`; the working tree also contains unrelated experimental changes. No runtime, model, browser, migration or test execution was performed. This note is the only file written by Editing in this round.

## Position

Retaining composable facets is a better starting point for the user's ambition than requiring every object to select one authoritative kind. A subject can acquire new interpretations without changing identity or surrendering its data to the latest application. However, an extensible bag of typed data is only the storage half of that promise. Independently released editors need a way to determine which operations they can still perform, what they must preserve, and which interpretation of their work will remain meaningful.

Do not equate four identities: the durable subject, the nominal facet contract and its schema revision, the installed operation implementation, and the particular interface generation a view is using. Identical JSON shapes do not imply equivalent contracts: two records containing `value: number` can mean metres and temperatures. Conversely, changing an editor implementation need not change either the subject or the data schema.

## What exists, and what remains a design proposal

The native runtime already stores objects as facet maps. `world.py:123-160` accepts an object revision and a patch of named facets: unmentioned facets remain; supplied bodies replace entire facets; null detaches. This gives atomic batch rejection and preservation of unrelated facets, not field-level or semantic merge. Revisions belong to the whole object, so unrelated changes can cause refusal.

`schemas.py:92-108` validates submitted bodies against the current definition found by facet name. `Gateway.define_schema` (`gateway.py:153-187`) can replace that global definition after checking up to 1,000 current instances. The check establishes that current values validate; it does not establish compatibility with existing readers, future old-writer output, or unchanged operation meaning. Stored bodies do not carry the immutable definition identity/version illustrated in Objects and Facets section 2.4.

The installation path is stricter: `application_schema.py:101-126` retains an identical existing definition and refuses a different definition under the same name. Its instruction to migrate explicitly is not an implemented general migration protocol. Application `accepts`, `read_facets`, and `write_facets` are lists of names, not schema-version or semantic-operation contracts. The manifest's descriptive `contracts` object is bounded but not interpreted as an enforceable compatibility proof.

`application_data.py:11-17,31-48` gives a view a filtered subject projection and restricts writes to granted facets. The native owner preserves facets the view never sees, which is a good property. A view can still replace an understood facet with a reconstructed body that omits unfamiliar optional fields; if the current schema accepts the result, validation alone cannot detect the loss.

`applications.py:168-202` refresh checks accepted facet names and nonexpanded grants. Existing views can remain on pinned builds until refreshed. This is not a demonstrated semantic compatibility test. `applications.py:204-233` uninstalls by disabling the installation and closing/revoking its open views; it explicitly preserves subject content and schemas. Installed package actions are discoverable separately from open views (`packages.py:243-259`). These are useful foundations, not the entire proposed lifecycle.

Objects and Facets already preserves much of the necessary reasoning: immutable v2 definitions and explicit persisted migrations (section 3.7); unknown data, dependencies and scoped operation constraints (3.5); copy distinctions (4.4); and independent code/data rollback (11.3). The runtime intentionally implements a smaller contract. Runtime Guide's ordinary-write section and Implementation Status's current-runtime table say so. Their older generic statement that multi-application mounting is absent is superseded by the separate Application Experiment/current source; the documents are not perfectly synchronized.

## Two mechanisms worth borrowing, with their limits

**Stable interface contracts with explicit discovery.** Microsoft's [Interface Design Rules](https://learn.microsoft.com/en-us/windows/win32/com/interface-design-rules) require a distinct IID and an immutable published interface definition. Its [QueryInterface rules](https://learn.microsoft.com/en-us/windows/win32/com/rules-for-implementing-queryinterface) distinguish object identity from the several interfaces exposing it and require consistent interface discovery. Read both complete short articles. These are concrete mechanisms for letting independent clients agree on what they are calling.

My inference for Agora is narrower than adopting COM: bind an offered operation to an identified contract and implementation generation while keeping durable object identity independent. COM's fixed interface set for one runtime instance should not become a rule that a persistent Agora subject can never gain facets or newly installed operations. Applicable capabilities can change; an already captured edit must not silently acquire a new meaning. Media independently emphasized this distinction.

**Unknown-data retention and explicit presence.** Protocol Buffers' [proto3 guide](https://protobuf.dev/programming-guides/proto3/) explains that its binary messages retain unknown fields, while JSON conversion and field-by-field reconstruction can lose them. It also distinguishes wire-safe and conditionally compatible changes; successful parsing is not identical to preserved meaning. Read the field-number, update and unknown-field sections, not the whole guide. This is evidence about a particular protocol, not an argument that Agora should use Protobuf or abandon JSON.

The [field-presence application note](https://protobuf.dev/programming-guides/field_presence/) gives the sharper counterexample: implicit presence conflates an unset scalar with its default, and merging cannot express setting that field to its default without another mechanism. Its old/new-client example loses explicit presence even though the value survives. Read presence semantics, merging and change-compatibility sections. My inference: an edit contract must distinguish leave unchanged, set to zero/empty, clear, and remove. A generic reconstructed save is a poor long-term interchange contract. An Agora JSON envelope can preserve opaque unfamiliar values perfectly well; the decisive issue is the operations applied to them.

## Pressure case: Notes and Review evolve separately

This is a constructed future scenario, not a report of the existing Notes/Documents example.

1. Notes 1 creates document D with title, text and a date. Review 1 reads that same subject and adds review metadata. They share a text contract rather than importing copies of one another's data. The date contract distinguishes an absent date from a deliberately cleared one.
2. Review 2 adds anchored annotations and an approval, while Notes remains at version 1. An annotation records its content basis and locator interpretation; approval records which content was reviewed. Adding these facets should not make Notes unable to rename D. Renaming is independent of their text basis.
3. Notes 1 replaces D's text. Preserving every unfamiliar Review byte is insufficient: unchanged offsets might now identify another sentence, and an unqualified approved flag could falsely bless changed text. A safe interpretation retains the annotation about the old content and marks its applicability to current text unresolved, or applies a declared compatible rebase. Approval remains evidence about the reviewed revision. No manual presentation repair should be required.
4. Review 3 changes text representation, perhaps to structured blocks. Installing Review 3 does not itself rewrite D. A declared read translation may keep Notes useful without changing authoritative data. Persisting a migration is a separate revision-checked operation retaining the resulting changes and failed-case evidence. Notes may remain a reader, or use an explicitly supported edit translation. An old plain-text save cannot be assumed to preserve structured blocks merely because it still produces text.
5. Roll back Review's code. Data remain at their present revision. The older application either supports it, uses a declared translation, or exposes limited/read-only operation. Code rollback is not an instruction to erase later content.
6. Duplicate D for a new proposal. A reference creates another use of the same subject; a duplicate creates new identity. Review approval normally cannot turn into approval of the new proposal, though it may be retained as provenance about the source. Opaque unknown facets create a real question: copying raw bytes preserves data but cannot reliably retarget unknown internal references. A domain copy can declare the relevant rules; a generic copy should retain opaque material as inherited evidence without claiming all new-object interpretations remain operative.
7. Uninstall Review. D, schema definitions, annotations and retained evidence remain inspectable. Review-specific controls become unavailable; a later compatible application can adopt the retained data. Generic inspection must not imply that an unsupported structured editor is fully replaceable by a JSON form.
8. Delete one annotation, remove D from a board, close Notes, or erase D. These are different subjects and consequences even if interfaces label several controls Delete. An operation must name its actual target. No universal deletion cascade follows merely from co-location on an object.

## Dependencies without universal vetoes

Root's challenge is essential: adding a new facet must not silently prohibit all old writes. Separate a claim's validity about its recorded inputs from its applicability to the current subject.

A candidate minimum dependency relationship identifies the source facet/part, its revision or other domain basis, and the interpretation contract. After accepted text edits, a maintained index can identify affected interpretations and mark them stale or invoke their declared rebase path. Changing title does not affect an annotation whose basis is text. This requires finer dependency identity than today's containing-object revision if unrelated edits are to remain cheap. It need not require all data to use field-level revisions.

Retain the locator/anchor contract identity, original basis and enough source material to interpret the old claim independently of the currently installed rebaser. Removing that handler can make rebasing unavailable; it does not entitle another handler to assert a current location. The fallback is an honestly labeled historical or unresolved annotation. Retained contract text alone does not prove the old material remains available.

These dependencies invalidate dependent interpretation; they do not automatically veto source edits. A stronger coupled invariant must be part of an explicitly adopted domain/compound-operation contract stating which writes it governs. An arbitrary extra facet cannot confer that status on itself. A revision-bound approval often avoids a blocking rule entirely: it remains true that somebody approved the previous content, without claiming approval of the new content.

The unresolved cost is authoring and enforcing those relationships. A generic graph cannot infer that a caption was written to fit a particular width, or that an approval concerns only text rather than title too. Dependency declarations, lawful rebasing and meaningful failure states still require domain design. Automatic visual refresh should follow accepted changes and declared dependencies; it should not depend on each app remembering to refresh every other app. Foundations supplied a historical Newton counterexample to voluntary notifications.

## What an agent should inspect, and what remains open

Routine inspection should return the subject, relevant facets and schema identities, available operations and their current applicability, and any affected interpretations already stale. Expanding an operation should reveal the target, understood contract version, fields/parts it may replace, handling of unfamiliar data, and whether it edits, translates, migrates or only presents. Agents should not need to read every unfamiliar facet before changing an independent title.

Capability discovery should support targeted questions such as which installed operation can edit this text representation, with a concrete unsupported-version reason. A package name, nominal type match or large tool inventory is not enough. Competing handlers can remain available with inspectable defaults. A changing default affects newly resolved commands; it must not retarget an action already captured by a view or agent.

The everyday path should stay small. Adding a personal tag or an independent due-date facet uses an existing admitted definition, or introduces a new small definition, and attaches data to the same subject. It needs no migration of unrelated facets and no coordinated release of every editor. Formal migration appears when an existing interpretation or representation changes, not whenever the object gains another useful aspect. Optional fields within an existing facet still require a preserving edit path; accepting the JSON shape does not establish semantic compatibility.

Open questions worth testing before selecting a spec:

- Which contract identities must be immutable, and which display aliases can follow newer revisions?
- Can small application authors cheaply declare preserving updates, dependency bases and supported schema versions, or does this merely relocate bespoke adapter work?
- Which new optional fields are genuinely independent, and which extensions change the meaning of old operations despite identical syntax?
- What narrow generic operations remain useful on unknown data without claiming domain understanding?
- Which cross-facet invariants justify atomic coupled writes, and which should instead retain independent historical claims with current applicability?
- How do copy and merge preserve unknown internal relationships honestly? Facet-local merge alone does not establish whole-object semantic consistency.
- Can an independent third editor adopt the evolved document without migration code supplied by either original author, and what information is actually missing when it cannot?

Earlier security-review memory prompted the mixed-version questions, but its old prototype findings were not treated as current evidence. Current observations above were checked against today's Agora4 source. No proposal here has been implemented or exercised.

