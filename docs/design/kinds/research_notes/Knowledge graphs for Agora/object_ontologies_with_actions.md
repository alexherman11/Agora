# Object ontologies with actions: how typed objects, links and verbs form an operational graph

*Researcher notes, 28 Oct 2026. Sources fetched on that date unless noted. Claims are labelled by source quality; vendor docs = documented behaviour, vendor blogs/third parties = claims. Things I know only from memory are kept out of Cited Findings and sit under Inferences or Gaps, marked "recall".*

## 1. Palantir Foundry Ontology: objects, properties, links, actions, functions; how apps and AIP agents use it

### Takeaway
Foundry splits its ontology into a **semantic** half (object types, properties, link types) and a **kinetic** half (action types, functions, dynamic security). Every edit, whether from a person in Workshop or an AIP agent, goes through the same **action types**. An action type is a typed, parameterised transaction bound to existing object and link types, with validation, rules and side effects. That shared path is what makes the ontology "operational" rather than a read-only model.

### Cited Findings
- Palantir calls the Ontology "an operational layer for the organization". It sits on top of datasets, virtual tables and models and connects them to their real-world counterparts. — [Palantir docs: Ontology overview](https://www.palantir.com/docs/foundry/ontology/overview/)
- Palantir's own split: **semantic elements** (objects, properties, links) describe entities and how they relate; **kinetic elements** (actions, functions, dynamic security) "enable change". — [Ontology overview](https://www.palantir.com/docs/foundry/ontology/overview/)
- The core-concepts page calls the Ontology "the digital twin of an organization", built by mapping datasets and models to object types, properties, link types and action types. "Digital twin" is Palantir's own framing, i.e. marketing language inside the docs. — [Palantir docs: Core concepts](https://www.palantir.com/docs/foundry/ontology/core-concepts/)
- Definitions from the core-concepts page:
  - **Object type**: "the schema definition of a real-world entity or event". An object is one instance; an **object set** is a group of instances.
  - **Property**: a characteristic. A **shared property** "can be used on multiple object types", which centralises its metadata.
  - **Link type**: a relationship between two object types; a link is one instance of it.
  - **Action type**: "the schema definition of a set of changes or edits to objects, property values, and links" that a user applies at once, plus the side effects on submission.
  - **Function**: "code-based logic that takes in input parameters and returns an output", with objects and object sets as possible inputs.
  - **Interface**: "an Ontology type that describes the shape of an object type and its capabilities". It lets you work with several object types that share a shape, i.e. polymorphism.
  - **Roles**: "the central permissioning model in the Ontology".
  - **Object Views**: "a central hub for all information and workflows related to a particular object".

  — [Core concepts](https://www.palantir.com/docs/foundry/ontology/core-concepts/)
- An action is "a single transaction that changes the properties of one or more objects, based on a user-defined logic". Edits are "committed to the Ontology when the user takes the action". The latest object data, with user edits merged in, is "captured in an object type's writeback dataset". — [Palantir docs: Action types overview](https://www.palantir.com/docs/foundry/action-types/overview/)
- Defining an action once is what lets "the same action logic and validations [be] made available across all user-facing applications, ensuring consistent edits to the Ontology". — [Action types overview](https://www.palantir.com/docs/foundry/action-types/overview/)
- The docs' example action changes an employee's role. It takes a parameter in a standardised form, creates a link automatically, validates that only authorised people (such as HR) can run it, and notifies the old and new manager as a side effect. — [Action types overview](https://www.palantir.com/docs/foundry/action-types/overview/)
- **Action rules** (documented):
  - Ontology rules: create object; modify object(s); create-or-modify; delete object(s); create or delete link(s) for many-to-many links; **function rule**; **interface rules**, which act on any object type that implements an interface.
  - One-to-one and one-to-many links are changed by editing the foreign-key property with a Modify rule.
  - A function rule must stand alone: "When this rule is present, no other rule may be configured."
  - Side-effect rules: Notification (sent after all edits apply), Webhook (before or after edits), Schedule (triggers a build).
  - Rules "compile into one edit per object". They cannot reference objects created in the same action, and order constraints apply.

  — [Palantir docs: Action rules](https://www.palantir.com/docs/foundry/action-types/rules/)
- The action-types documentation also has pages on submission criteria, permissions and "read and write authorizations", an action log, action metrics, and "Undo or revert Actions". I saw these only as sidebar titles; I did not read their contents. — [Action types overview](https://www.palantir.com/docs/foundry/action-types/overview/)
- Applications named in the docs: **Object Explorer** for search, **Object Views** as reusable per-object pages, **Quiver** for complex analysis, **Workshop** for building applications. — [Ontology overview](https://www.palantir.com/docs/foundry/ontology/overview/)
- **AIP agents (AIP Chatbot/Agent Studio)** get these tool types: Action, Object query, Function, Update application variable, Command, Request clarification, and the legacy Ontology semantic search, now replaced by "Ontology context".
  - Action tools "can be configured to run automatically or to run after confirmation from the user".
  - The object-query tool "specifies the object types that the LLM can access".
  - Native tool calling allows parallel calls; prompted tool calling allows "a single tool at a time".

  — [Palantir docs: Agent Studio tools](https://www.palantir.com/docs/foundry/agent-studio/tools/)
- **AIP Logic** is described as a no-code environment for LLM-powered functions. They take Ontology objects as input and can make Ontology edits, applied automatically or "staged for human review". This comes from a search summary of the docs; I did not fetch the page. — [Palantir docs: Logic](https://www.palantir.com/docs/foundry/logic/overview/)
- A third-party write-up says AIP Logic presents the ontology to the LLM as tools (Query Objects, Calculator, Apply Action), and that objects a user cannot see are not given to the LLM either. Secondary source, not verified against Palantir docs. — [Pebblous blog](https://blog.pebblous.ai/project/CURK/ontology/enterprise-ontology-paradigm/en/)

### Inferences
- The pattern that matters for Agora: **verbs are first-class schema objects** (action types), not methods inside application code. They are declared over object and link types and interfaces, carry their own validation, permissions, side effects and log, and every surface reuses them: forms, tables, Object Views, agents. This is close to Agora's "verbs live in a world dictionary". Palantir adds an explicit transaction boundary, submission criteria and an audit log to each verb.
- Agents are *not* given raw write access. They are handed a configured subset of action types, and each one can be set to auto-run or confirm-first. This is a mechanism Agora's "many agents act through the same verbs" could copy directly: per-agent verb grants plus a confirm flag.
- Interfaces plus interface rules give **verbs bound to a shape rather than a concrete type**. That is the closest Foundry comes to "open aspects".
- The writeback-dataset design (source data plus an edit layer merged into the current state) is an event-sourcing-like split between imported truth and human/agent decisions. *Inferred from one sentence; not verified in detail.*

### Gaps
- I could not read the pages on submission criteria, action permissions, the action log or undo, so the exact permission model for actions (who may run a given action on a given object) is unverified here.
- Customer-reported outcomes ("what it enables"): I found no primary customer case studies in this pass; only vendor framing and critics. Treat any outcome claims as unverified.
- OSDK (Ontology SDK) and how external code calls actions: not fetched.
- Dates: Palantir doc pages carry no visible publish dates in what I fetched. They were live on 28 Oct 2026.

## 2. Tana supertags: types with fields, extension, commands on tagged nodes

### Takeaway
A Tana supertag makes the node itself a typed object. The node does not just carry a label.
- The tag holds a template (fields, default values, child search nodes) and **commands that appear as buttons on every tagged node** and run on events.
- "Extend" gives inheritance by projection: the child tag can add fields and override defaults, but cannot delete what it inherited.
- A node can hold several supertags.

### Cited Findings
- In Tana "the content *is* the tag": a supertag applies to the whole node, not to its relation to a topic. — [Tana docs: Supertags](https://outliner.tana.inc/learn/features/supertags)
- Each supertag has a **template**: fields such as Due date or Status, default values (e.g. a new Task starts with Status "Inbox"), plus search nodes and regular nodes, all given to every node that gets the tag. Field options:
  - auto-initialize rules;
  - pinned fields, shown on top and in filter/sort/group menus;
  - optional fields, suggested rather than always shown;
  - done-state mapping (checking the box sets Status to Done);
  - "show as checkbox".

  — [Tana docs: Supertags](https://outliner.tana.inc/learn/features/supertags)
- **Extend**: a supertag can extend another so that the parent's template "projects" into it. The docs' example is "Design task" extending "Task" with its own default Project. Inherited content cannot be moved or deleted, but fields can be added and defaults changed. — [Tana docs: Supertags](https://outliner.tana.inc/learn/features/supertags)
- When nodes from several supertags are viewed together, the pinned fields of all of them appear. The docs do not say how field conflicts are resolved. — [Tana docs: Supertags](https://outliner.tana.inc/learn/features/supertags)
- **Commands bound to the type**: commands attached to a supertag show as buttons on all tagged nodes, with that node as primary context. Commands can also fire on events: on capture, when added, when removed, when checked or unchecked. Tags added or removed via the API do not fire these events. — [Tana docs: Supertags](https://outliner.tana.inc/learn/features/supertags)
- **Base types**: 13 fixed system types (Meeting, Task, Person, Project, Day, etc.) tell the system what a tag *means* regardless of its name. They mainly help AI and switch on features such as meeting transcription, a meeting agent and calendar sync. The docs call them "a work in progress". — [Tana docs: Supertags](https://outliner.tana.inc/learn/features/supertags)
- **AI per supertag**: custom autofill of title, fields or description from a prompt; audio-enabled tags that transcribe and post-process with a command; AI instructions for identifying what to tag; AI field suggestions. — [Tana docs: Supertags](https://outliner.tana.inc/learn/features/supertags)
- **Views**: each supertag has a Supertag page that by default shows a table of all its nodes, with more view tabs available. Search nodes inside a template can pull related items (a Project lists its Tasks). — [Tana docs: Supertags](https://outliner.tana.inc/learn/features/supertags)
- The docs page now says "Tana Outliner" is a separate product from "Tana, the meeting platform". That is a 2026 product split visible on the page. — [Tana docs: Supertags](https://outliner.tana.inc/learn/features/supertags)

### Inferences
- Tana is the clearest consumer example of **verbs on the kind**: commands live on the supertag and show as buttons on its instances, and lifecycle events (added/removed/checked) act as type-level triggers. It is lighter than Palantir: no transaction, permission or audit model is documented.
- Several supertags on one node is close to Agora's "open aspects". Extension is single-parent projection, with additive fields and overridable defaults. That is closer to prototype delegation than to class inheritance, since you cannot remove inherited fields.
- The base-types layer shows a recurring need: user-named kinds still have to map onto a small set of system-understood kinds, so AI and integrations know what a "Meeting" is. Agora may need a similar mapping from world-defined kinds to well-known kinds.
- The API caveat (events do not fire for API-made changes) is a warning for Agora. If agents act through a different path than people, type-level triggers diverge.

### Gaps
- Folders: the Tana docs page does not compare supertags with folders. The contrast (a node belongs in many tag-views at once, rather than sitting in one location) is my inference, not documented.
- I did not verify whether extension supports multiple parents, or how conflicting fields are resolved when two supertags define the same field.

## 3. Capacities, Notion, Anytype: types, relations, inheritance, views

### Takeaway
All three treat "type" as a schema of properties with views on top, and none of them has real type inheritance.
- **Capacities** is one-type-per-object with a small fixed default set of properties.
- **Notion** makes the *database* the type; relations link databases and rollups aggregate across a relation.
- **Anytype** gives each object one Type, keeps properties when the Type changes, and builds views as live queries ("Sets"), either by Type or by Relation.

### Cited Findings
- **Capacities**:
  - Every piece of content is an object, and each object is an instance of an object type. Types are either basic (Page, Tag, Image, Weblink) or custom.
  - Every type has five default properties (title, description, icon, created at, tags), and users add more to custom types.
  - The docs say a type works like one database table for one kind of thing, and a "collection" is a hand-picked subgroup inside one type.
  - In the API, types appear as "structures" (GET /space/structures).

  These points come from search-result summaries of the docs pages; my direct fetches of two Capacities pages returned 404. — [Capacities docs: object type like a database?](https://docs.capacities.io/faq/editing/object-type-like-database); [Capacities: content types](https://docs.capacities.io/reference/content-types); [Capacities developer API: structures](https://developers.capacities.io/api/concepts/structures)
- **Notion relations**:
  - Relations link items across databases. Between two different databases they are one-way by default, and a matching property can be added to make them two-way.
  - A self-relation can have separate directional properties (Next/Previous).
  - A relation can be limited to 1 page, and you choose which properties of related pages show in the relation field.
  - On CSV export, relations become plain-text URLs that cannot be re-imported. Duplicating a database with a two-way relation makes the copy one-way.

  — [Notion help: Relations & rollups](https://www.notion.com/help/relations-and-rollups)
- **Notion rollups**: pick a relation, a property on the related pages, and a calculation (count, percent, unique values, sum, average, median, min, max, range, earliest/latest date, date range). "You can't roll up a rollup", which is a restriction to prevent loops. — [Notion help: Relations & rollups](https://www.notion.com/help/relations-and-rollups)
- **Anytype types**:
  - Each Object gets one Type, which can be changed later. The docs' image: "If an Object is a cookie, then the Type is the cookie cutter."
  - "When changing Types, the Properties are retained on the Object", so properties belong to the object, not only the type.
  - Types are specific to each Channel/Space; sharing them across Spaces needs import/export.
  - Types configure layout, header properties and templates.
  - Views organise Objects of a Type (calendar, kanban), and views are the suggested way to bulk-change Types.

  — [Anytype docs: Types](https://doc.anytype.io/anytype-docs/basics/types)
- **Anytype Sets and Collections**:
  - Sets are live queries, not storage. Sets "don't store Objects like regular databases".
  - A Set is either "by Type" or "by Relation", and a Set by Relation lists objects of *any* type that have that relation.
  - Collections are manual, folder-like lists of objects of any type.

  — [Anytype docs: Sets](https://doc.anytype.io/anytype-docs/basics/sets-and-collections/sets); [Anytype glossary (revision)](https://doc.anytype.io/anytype-docs/~/revisions/SFjMNGZIAXS10yHETGw8/basics/glossary)
- Older Anytype community threads show users asking for cross-type sets and per-set multiple types. Staff then described a planned ID-storing "collection". These are dated forum posts, not current behaviour. — [Anytype community: Is each Set limited to a single Type?](https://community.anytype.io/t/is-each-set-limited-to-a-single-type/1700); [Anytype community: Collections 2.0 architecture](https://community.anytype.io/t/collections-2-0-architecture-changing-how-we-use-types/30113/66)

### Inferences
- None of these three documents type inheritance (I found no inheritance feature in the pages read). Flexibility comes instead from properties that outlive type changes (Anytype), relation-based queries across types (Anytype Set-by-Relation), and multiple tags (Tana).
- Anytype's "Set by Relation" is the closest of these to an ECS query: select every object that *has* an aspect, whatever its type. That matches Agora's "open aspects + kind" better than one-type-per-object.
- Notion's "database = type" ties the type to a container. Its export loss (relations become URLs) is a small, concrete case of graph lock-in.
- None of these three put **verbs on types** in what I read. Behaviour sits in templates, plus buttons and automations in Notion and Capacities (not verified here). Verbs are the weak point of the consumer tools, and the strong point of Palantir and Tana.

### Gaps
- I could not fetch Capacities pages directly (404s), so the Capacities findings rest on search-result summaries of its docs.
- I did not verify Notion buttons or database automations as "verbs on a database", nor Capacities AI or actions on object types.
- I did not confirm whether Anytype relations are global per space and shared across types. Recall says they are, but it is unverified.

## 4. Entity–component–system and prototypes as alternatives to class hierarchies

### Takeaway
- **ECS** defines an entity by the components attached to it, not by its place in a hierarchy. Behaviour lives in global systems that *query* for entities holding certain components, so which verbs apply is decided by which aspects are present.
- **Prototypes** (JavaScript, descended from Self) let any object delegate to another live object, and changing that prototype changes every object that inherits from it.

Both are composition- or delegation-based alternatives to fixed classes.

### Cited Findings
- **ECS**:
  - An entity is "usually" just a unique ID, a component holds the data for one aspect, and a system "act[s] globally over all entities that have the required components".
  - ECS "prioritizes composition over inheritance", avoiding deep inheritance trees. Components can be added or removed at runtime.
  - Example: a render system processes only entities with model, transform and drawable components.
  - Named drawback: indirect data flow through components "can be a place for bugs to hide".

  — [Wikipedia: Entity component system](https://en.wikipedia.org/wiki/Entity_component_system)
- **JavaScript prototypes**:
  - Each object links to a prototype, and lookup walks the chain until a match or `null`.
  - Setting a property creates an own property that shadows the inherited one, which is a form of method overriding.
  - The chain can be mutated or swapped at runtime, so "concepts like static dispatching do not exist in JavaScript".
  - Changing a shared prototype changes behaviour for all existing instances.

  — [MDN: Inheritance and the prototype chain](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Inheritance_and_the_prototype_chain)

### Inferences
- A mapping for Agora: **aspects ≈ components; verbs ≈ systems keyed by required aspects; kind ≈ a named prototype** whose defaults and verbs an object delegates to, and can locally shadow. Tana's "extend" (add and override, can't delete inherited) already sits between the two.
- ECS answers "which verbs apply to this object?" with "every verb whose required aspects the object has". That is a query, not a lookup on a type. Palantir's interfaces plus interface rules are a typed version of the same idea.
- Prototype delegation gives live, world-editable kinds: edit the kind and all instances change. The cost is the ECS drawback in another form: behaviour becomes non-local and harder to trace. Agora would need provenance ("this verb comes from kind X via aspect Y").

### Gaps
- Self language primary sources (Ungar & Smith, "Self: The Power of Simplicity", 1987) were not fetched. That JS prototypes descend from Self is recall only, and MDN does not mention it.
- I did not survey ECS frameworks (Bevy, Flecs) for relation and query features such as Flecs "relationships", which would bear on typed links.

## 5. Where verbs live and how applicability is decided (Palantir, Tana, Windows shell)

### Takeaway
Three placements recur.
- **On the type**: Windows ProgID `shell\verb`, Tana supertag commands, Palantir action types scoped to object types.
- **On a shared shape or interface**: Palantir interface rules, Windows `*` / `AllFilesystemObjects`, ECS systems.
- **As global functions with typed parameters**: Palantir functions, AIP tools.

Applicability is then filtered by item attributes or a query (Windows `AppliesTo` with AQS, `AttributeMask`, selection-count model), by validation (Palantir submission criteria), and by permissions and agent grants.

### Cited Findings
- **Windows: verbs on the file type.**
  - A static verb is registered under `HKEY_CLASSES_ROOT\<ProgID>\Shell\<verb>\command`, with the command line as the default value.
  - The default value of `Shell` names the default verb.
  - Fallback order when no verb is specified: default verb → first verb in registry (if ordered) → Open → Open With.

  — [Microsoft Learn: Creating Shortcut Menu Handlers](https://learn.microsoft.com/en-us/windows/win32/shell/context-menu-handlers) (page updated 2025-07-03)
- **Canonical verbs** (open, opennew, print, printto, explore, properties) are language-independent names that the system localises. `printto` is never shown but enables drag-to-printer. — [Microsoft Learn](https://learn.microsoft.com/en-us/windows/win32/shell/context-menu-handlers)
- **Verb visibility tiers**:
  - extended verbs appear only on Shift+right-click (an `extended` value);
  - `ProgrammaticAccessOnly` verbs never appear in menus but can be invoked via ShellExecuteEx;
  - `SuppressionPolicy` hides verbs by policy.

  — [Microsoft Learn](https://learn.microsoft.com/en-us/windows/win32/shell/context-menu-handlers)
- **Conditional applicability**:
  - `AppliesTo` (an Advanced Query Syntax condition over the item's fast properties) shows or hides a verb; `DefaultAppliesTo` decides the default; `HasLUAShield` shows a UAC shield.
  - Example: BitLocker verbs on `drive` use `AppliesTo = System.Volume.BitlockerProtection:=2`.
  - `AttributeMask`/`AttributeValue` test SFGAO item attributes (e.g. read-only).
  - `MultiSelectModel` (Single / Document / Player) hides a verb when the selection count doesn't fit. Limits: Document 15 items; Player 100 items for legacy handlers, unlimited for COM.

  — [Microsoft Learn](https://learn.microsoft.com/en-us/windows/win32/shell/context-menu-handlers)
- **Shared verb stores and broad targets**:
  - Verbs can be registered once under `CommandStore` and reused via `SubCommands`, or shared through `ExtendedSubCommandsKey`.
  - Verbs can be registered on `*` (all files) and predefined shell objects such as `DesktopBackground`, `Directory` and `Folder`.
  - `ShellNew` adds per-type creation to the New menu.
  - Per-user registration under HKCU avoids elevation.

  — [Microsoft Learn](https://learn.microsoft.com/en-us/windows/win32/shell/context-menu-handlers)
- **Palantir**:
  - Action rules act on existing object and link types, or on any type implementing an interface.
  - A function rule delegates the whole edit to code.
  - Agents see only the actions and object types configured as tools, each set to auto-run or confirm.

  — [Palantir Action rules](https://www.palantir.com/docs/foundry/action-types/rules/); [Agent Studio tools](https://www.palantir.com/docs/foundry/agent-studio/tools/)
- **Tana**: commands attach to a supertag and appear on all its instances; event triggers fire on tag added/removed/checked. — [Tana docs: Supertags](https://outliner.tana.inc/learn/features/supertags)

### Inferences
- The Windows shell is an old, battle-tested **verb dictionary keyed by type plus predicate**. It has canonical verb names, which suggests Agora's dictionary should separate a verb's stable name from its display label. It also has visibility tiers (normal / extended / programmatic-only, a natural home for agent-only verbs), predicate-based `AppliesTo`, a selection-cardinality model, and shared command stores for reuse across types. All of these map closely onto "verbs live in a world dictionary".
- One design choice for Agora follows: bind verbs to **aspects or predicates** (ECS/Windows `AppliesTo`/Palantir interfaces) rather than only to kinds, and keep "kind" as the default bundle of aspects and verbs.
- Palantir's confirm-vs-auto flag per agent tool, plus Windows' `HasLUAShield`, point to the same need: a verb should carry its own risk marker that every surface (menu, agent, lens) honours.

### Gaps
- Windows dynamic verbs (IContextMenu / IExplorerCommand handlers, and the Windows 11 modern context menu that hides legacy verbs under "Show more options") were not covered in detail.
- I did not confirm how Palantir resolves conflicts when many actions apply to one object, or how actions are surfaced on Object Views.

## 6. What failed or is criticised: lock-in, upkeep cost, rigidity

### Takeaway
Criticism of Palantir centres on **lock-in**: data and relationships live in a proprietary shape that exports flatten. It also covers **cost and time**: months to a year to stand up, consulting-heavy upkeep. Notion shows the same flattening on a small scale. Most of the criticism is opinion or from competitors; no independent cost studies were found.

### Cited Findings
- HASH (a competitor) argues that "Data exists within Palantir in a proprietary shape and format". Exports to CSV or JSON are not readily usable by other systems, and migration "would be long and expensive", since permissions and integrations must be rebuilt. HASH proposes an open-source type system with versioning and provenance as the alternative, and admits it lacks Foundry's feature parity (e.g. no-code apps). Vendor-authored, 3 Apr 2025. — [HASH: The Problem with Palantir](https://hash.ai/blog/the-problem-with-palantir)
- Commentary cites the NYPD's 2017 public complaint that Palantir would not give its analytics in a portable format. Michael Burry argues the moat is "obstruction of data transfer". Palantir's stated counter: the customer owns the raw data, but how the software organises and links it is Palantir's IP. All of this comes from news and blog summaries, not primary documents. — [PWS: Burry on Palantir's moat](https://www.pws.io/palantirs-moat-is-just-obstruction-of-data-transfer-michael-burry-says); [Finviz news](https://finviz.com/news/313131/palantirs-moat-is-just-obstruction-of-data-transfer-michael-burry-says); [Webull news](https://www.webull.ca/news-detail/13084418433442816)
- A production Foundry instance is said to take months to over a year, with specialised teams modelling relationships by hand (consulting-firm commentary). — [Xpert.Digital](https://xpert.digital/en/why-managed-ai-is-the-better-choice/?amp=1)
- A balanced take frames the open question as upkeep: Palantir wins only if customers keep "ontologies, access controls, action logs, evaluations and human approvals current as organizations, models and workflows change". — [BTW Media](https://btw.media/en/palantirs-real-ai-test-is-whether-the-ontology-still-holds-months-later)
- Practitioner critique of ontology building as demanding and consulting-dependent. — [Creative Differences (Substack)](https://creativedifferences.substack.com/p/interested-in-ontologies-let-me-tell); see also [Vonng: Ontology again](https://blog.vonng.com/en/db/ontology-again/) (not read in full)
- **Notion**: relations export to CSV as URLs that can't be re-imported, and duplicating a database turns a two-way relation one-way. — [Notion help](https://www.notion.com/help/relations-and-rollups)
- **Anytype**: types are per-Space and cross-Space sharing needs import/export, which is friction for community-shared kinds. — [Anytype docs: Types](https://doc.anytype.io/anytype-docs/basics/types)
- **ECS**: indirect data flow is hard to debug. — [Wikipedia: ECS](https://en.wikipedia.org/wiki/Entity_component_system)
- **Tana**: base types are "a work in progress", and API-made tag changes skip event triggers. — [Tana docs](https://outliner.tana.inc/learn/features/supertags)

### Inferences
- The failure that recurs across scales is that **links and verbs do not survive export**: Palantir's proprietary shape, Notion's relation URLs. Agora's world dictionary should make kinds, links and verbs exportable as plain text in the same notation people and agents use, so the graph is never only inside the engine.
- Upkeep cost scales with how centrally the ontology is designed. Palantir's model expects modellers. Agora's bet on residents and agents evolving kinds in the world could lower that cost, or turn it into drift. It needs versioned kinds and provenance on verbs (HASH's argument).
- Rigidity is less documented than lock-in. The evidence I found is indirect: Notion's one-database-per-type and Anytype's one-type-per-object. What would change my view: practitioner reports of Palantir schema migrations (renaming or splitting object types with live actions), which I did not find.

### Gaps
- No independent, quantitative study of ontology upkeep cost or lock-in.
- No first-hand practitioner reports on Tana, Capacities or Anytype type-model rigidity at scale were fetched.
- Customer success claims for Palantir (what it "enables") were not gathered from primary case studies.
