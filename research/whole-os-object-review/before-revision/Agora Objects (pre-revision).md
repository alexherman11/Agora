
*Companion document to the AgoraOS core design. Covers the object system, the schema philosophy, and the storage architecture beneath it.*  
  
---  
  
## 1. Purpose and stakes  
  
Nearly everything in Agora bottoms out in the object system: search, memory, provenance, deixis, VR portability, native apps, and JEFF's ability to reason about the world. The object schema is the constitution of the world — the one component that will be nearly impossible to change once thousands of objects exist and JEFF's memories reference them.  
  
Accordingly, this document inverts the priority implied elsewhere: **the object schema is designed first and frozen carefully; renderers, compositors, and storage engines are treated as swappable implementations underneath it.**  
  
---  
  
## 2. Lessons from prior systems  
  
The design space here has a large graveyard. The failures cluster, and the pattern is consistent.  
  
### 2.1 What killed the predecessors  
  
| System                         | Approach                                                           | Cause of death                                                                                                                 |     |
| ------------------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ | --- |
| **WinFS**                      | All metadata in one relational store, rigid schemas for everything | Ontological over-engineering; hierarchy modeled badly in a DBMS; required universal app buy-in; imprisoned bytes in a database |     |
| **Nepomuk / Semantic Desktop** | Full RDF ontologies over desktop objects                           | So much ceremony per assertion that nobody asserted anything                                                                   |     |
| **OpenDoc**                    | Compound-document object composition                               | Complexity; required the whole ecosystem to convert at once                                                                    |     |
| **Smalltalk images**           | Uniform live-object world, image-based persistence                 | Conflated world with history; no event record; fragile recovery                                                                |     |
  
### 2.2 What survived  
  
- **BeOS BFS / Spotlight / tagging systems** — small typed core, loose ad-hoc metadata, excellent search. Folksonomy beat taxonomy.  
- **Entity-Component-System (game engines)** — identity as a bare ID, all data in composable facets, no class hierarchies. Handles open-ended type spaces where designers invent new kinds constantly.  
- **Kubernetes objects** — the `spec`/`status` split with continuous reconciliation. The only proven schema pattern for objects that *own live processes*.  
- **COM `QueryInterface`** — ask what an object *can do*, not what it *is*, at runtime.  
- **Event sourcing** — the log is the truth; state is a cache.  
  
### 2.3 The asymmetry Agora exploits  
  
Every prior semantic-object system needed rigid schemas because **dumb code had to consume the metadata**. A query planner cannot interpret "this is sorta related to that thing from last week."  
  
JEFF can.  
  
Agora is the first system in this lineage with a resident component that can read loose, inconsistent, folksonomic metadata and extract meaning. The LLM is the ontology mediator WinFS died waiting for. The schema's central bet follows directly:  
  
> **Strict where machines need precision (identity, capability security, lifecycle). Loose where meaning lives (semantics). JEFF is the join.**  
  
---  
  
## 3. The entity model  
  
An Agora object is an **entity**: a stable identity plus an open bag of typed facets. There are no classes and no type hierarchy.  
  
### 3.1 Layer 0 — the frozen core  
  
Six fields. This is the constitutional layer, designed to survive a decade unchanged:  
  
```  
entity:  
id: unforgeable, globally unique, NEVER reused  
lineage: world-line id + genesis event ref  
facets: { facet-name → facet-version → data }  
lifecycle: active | dormant | archived | tombstone  
created: event ref  
acl: capability grants scoped to this entity  
```  
  
Deliberately absent from the core: `kind`, `name`, position, content, process references. All of those are facets, and therefore evolvable.  
  
### 3.2 Kinds are conventions, not types  
  
A "note" is not a class. It is the conventional name for an entity carrying `text-content` + `visual` + `semantic` facets. A "running prototype" is `spec` + `status` + `file-backing` + `visual` + `provenance`.  
  
Consequences:  
  
- JEFF can mint a new kind at runtime by composing facets. No schema migration, no permission.  
- The `kind-tag` facet is **advisory** — a label for humans and search, never load-bearing for behavior.  
- Hybrid objects (a note that owns a process; a dataset that is also a rendered diagram) are free.  
  
This is what makes invariant #14 (*Agora becomes better at building itself*) true at the schema level rather than aspirational.  
  
---  
  
## 4. Layer 1 — [[Facets (pre-revision)|Facets]]  
  
Facets are versioned, typed data components attached to entities.  
  
### 4.1 Initial facet vocabulary  
  
```  
identity-facets: name, aliases, kind-tag  
content-facets: text, structured-doc, blob-ref, file-backing  
liveness-facets: spec, status  
visual-facets: surface-binding, transform, representation-hints  
semantic-facets: tags, summary, embedding-ref, free metadata  
capability-facets: typed actions this object exposes  
provenance-facets: created-by, derived-from, event-count  
presence-facets: last-focused, salience, attention history  
```  
  
### 4.2 Facet rules  
  
1. **Independent versioning.** Upgrading `visual.v2 → visual.v3` touches nothing else. No global schema version exists.  
2. **Must-ignore, not must-understand.** Any component encountering an unknown facet preserves it untouched. This is how HTML survived thirty years of evolution, and it is how JEFF invents new facets without breaking old code.  
3. **No facet is mandatory.** An entity with only a core and a `semantic` facet is legal (a pure idea). An entity with no facets at all is a tombstone.  
4. **Facets declare their write authority** (see §8).  
  
### 4.3 Liveness: the spec/status split  
  
Objects that own processes must not store observed runtime state as if it were truth. PIDs die; endpoints move; VMs restart.  
  
Instead, adopt the Kubernetes pattern wholesale:  
  
```  
spec: desired state — written by intent (human, JEFF, workers)  
status: observed state — written ONLY by reconcilers  
```  
  
A reconciler loop in the world VM perpetually drives status toward spec. This collapses three distinct failure classes — VM restart, world rollback, crashed process — into one mundane, self-healing condition: **reconciliation drift**.  
  
It also gives JEFF his best action primitive: **JEFF acts by editing specs, and the world catches up.** Declarative intent is a far better interface for a language model than imperative process management.  
  
### 4.4 Example: `prototype_117`, corrected  
  
```  
entity: prototype_117  
lineage: worldline-A / event 5501  
lifecycle: active  
  
facets:  
name: "db latency prototype"  
kind-tag: running-prototype # advisory  
  
spec:  
serve: /projects/db-test/  
runtime: node  
port: 5173  
  
status: # reconciler-owned  
pid: 8193  
endpoint: localhost:5173  
health: healthy  
last-checked: event 5620  
  
file-backing: /projects/db-test/ # real filesystem path  
surface-binding: wayland #88  
provenance: created-by coding-agent-52,  
derived-from idea_37  
presence: last-focused 18:11, salience 0.83  
```  
  
---  
  
## 5. Layer 2 — Soft semantics  
  
Above the typed facets sits a fully schemaless layer: free-form key-values, ad-hoc tags, JEFF's private annotations, the human's scrawl.  
  
- No validation. No ontology. No ceremony.  
- Search indexes it; nothing depends on its shape.  
- JEFF is the reader of last resort — the component that turns this mess into meaning.  
  
This layer is where WinFS's imagined librarians are replaced by a resident mind. It should be treated as *the primary place semantics accumulate*, with promotion into typed facets only when a pattern proves stable and machine-critical.  
  
---  
  
## 6. Relationships — edges with provenance  
  
Relationships are first-class records, not pointers embedded in objects:  
  
```  
edge:  
from / to: entity ids  
predicate: open vocabulary  
("derived_from", "contradicts", "reminds-me-of", ...)  
asserted_by: human | jeff | worker-id | inferred  
via: event ref  
confidence: optional  
```  
  
### Why `asserted_by` is non-negotiable  
  
In a world where a human, a persistent executive, and disposable workers all write to the same graph, *who claimed this and why* is the difference between a knowledge graph and a rumor mill.  
  
It buys, for free:  
  
- trust-weighted search and retrieval;  
- provenance answers ("you connected these last Tuesday; I inferred the third link from the paper");  
- an audit surface for memory-poisoning defense (§10);  
- the ability to bulk-revoke assertions from a compromised or misbehaving worker.  
  
Because every edge references the event that created it, **every relationship is also a memory.**  
  
---  
  
## 7. Token projection — objects that render to minds  
  
This schema has a constraint no predecessor ever faced: **two first-class render targets.** One is a screen. The other is a context window — and the second one is metered.  
  
Therefore, projection is a schema obligation, not a convention:  
  
```  
facet.project(budget) → text  
```  
  
Every facet type must know how to render itself into JEFF's context at a given token budget. Composed at the entity level:  
  
```  
prototype_117.project(15):  
"running db prototype on :5173, healthy, from idea_37"  
  
prototype_117.project(200):  
+ recent events, spec/status drift, open relationships  
  
prototype_117.project(2000):  
full dossier: history, provenance chain, related objects  
```  
  
### 7.1 Level-of-detail for cognition  
  
This is directly analogous to LOD rendering in game engines. JEFF's context window is his viewport; **salience** (from presence facets: focus, recency, selection, task relevance) determines which entities render at high detail and which appear as one-line summaries. The context assembler becomes a renderer, and the same presence data drives both the visual scene and JEFF's awareness.  
  
### 7.2 Deixis falls out for free  
  
"Move *this* there" resolves through presence facets — the human's focused object, cursor target, recency-weighted salience. Shared attention is not a bolt-on tracking subsystem; it is a facet family read by both render targets.  
  
### 7.3 Projection honesty (open problem)  
  
A projection is *self-description*. A compromised worker that writes an entity's summary facet gets to influence what JEFF believes at a glance. Token projection is therefore a prompt-injection surface and requires the same hygiene as edges: projections should carry or inherit `asserted_by` provenance, and low-trust content should be visibly marked as such when rendered into context.  
  
---  
  
## 8. Write authority and concurrency  
  
Three classes of writers exist: the human, JEFF, and workers. Rules:  
  
- **Each facet type declares its authority model.** `status` is reconciler-only. `presence` is system-only. `spec` and content facets accept intent-writers.  
- **Workers write through capability grants scoped in the entity `acl`**, consistent with the Ring 3 model. A coding worker granted `prototype_117.spec` cannot touch its provenance.  
- **Concurrent mutation** of shared collaborative facets (e.g., a document the human and JEFF edit simultaneously) likely requires CRDT-per-facet-type semantics.  
  
**Open:** the CRDT/merge strategy per facet class. This is a genuine project, not a detail.  
  
---  
  
## 9. Lifecycle, death, and world-lines  
  
### 9.1 Lifecycle as forgetting  
  
```  
active → dormant → archived → tombstone  
```  
  
- Transitions are driven by **salience decay** plus curation — JEFF as gardener, not a GC daemon.  
- Tombstones retain only the frozen core (no facet data) and are cheap. Objects never truly vanish; they thin out.  
- Deletion is *forgetting*: gradual, reversible until tombstoned, and always event-recorded.  
  
This is the answer to the "thousands of objects" hoarding problem: the world composts.  
  
### 9.2 World-line identity  
  
The `lineage` field exists to reconcile object identity with world rollback:  
  
- IDs are **never reused**, across rollbacks or otherwise.  
- When the world rolls back past an entity's genesis, the entity resolves to a tombstone marked *"existed on world-line A, pruned at snapshot_31."*  
- JEFF's persistent memory therefore **never dangles**: references to rolled-back objects resolve to the past instead of erroring or colliding.  
  
This is the schema-level enforcement of the core invariant: *world rollback must not erase JEFF's memory of the failure.* The world is reversible; the witness is not.  
  
---  
  
## 10. Capability facets and agent/UI parity  
  
An object's capabilities — the typed actions it exposes — are a discoverable facet, following the `QueryInterface` insight: ask what an object *can do*, never what it *is*.  
  
**The parity rule:** the buttons on an object's rendered surface and the tools JEFF sees for that object are *generated from the same capability facet*. One source, two projections (pixels and tool schemas).  
  
This single decision prevents the entire class of "the human and the agent are secretly using different apps" failures, and it means any Agora-native app is agent-operable by construction.  
  
---  
  
## 11. Storage architecture  
  
### 11.1 The stack  
  
```  
┌──────────────────────────────────────────────┐  
│ APPEND-ONLY EVENT LOG │ the truth  
│ every important mutation, forever │  
└──────────────────┬───────────────────────────┘  
│ fold  
┌──────────────────▼───────────────────────────┐  
│ MATERIALIZED ENTITY STORE │ a cache  
│ current state of all entities + edges │  
│ (SQLite-class embedded store) │  
└──────────────────┬───────────────────────────┘  
│ references  
┌──────────────────▼───────────────────────────┐  
│ BYTES │  
│ • content-addressed blob store (media, │  
│ immutable artifacts) │  
│ • REAL FILESYSTEM via file-backing facets │  
│ (projects, documents, code) │  
└──────────────────┬───────────────────────────┘  
│ indexed by  
┌──────────────────▼───────────────────────────┐  
│ DERIVED INDEXES — all rebuildable │  
│ full-text │ embeddings │ graph │ event query │  
└──────────────────────────────────────────────┘  
```  
  
### 11.2 Principles  
  
1. **The event log is the only truth.** The entity store is a fold over events; if it corrupts, replay. This is what makes `World(t)` conceptually honest.  
2. **Bytes stay in the real filesystem.** The object system *annotates* the filesystem; it never replaces it. `file-backing` facets point at real paths. This is WinFS's most expensive lesson: imprisoning bytes in a database strips their semantics for every tool that only speaks files — and breaks git, rsync, opaque apps, and the user's escape hatch.  
3. **All indexes are disposable.** Full-text, vector, and graph indexes can be dropped and rebuilt from log + store + files at any time. Index choice is an implementation detail, never a commitment.  
4. **Search is existential, not a feature.** Hierarchies alone don't let anyone find anything; a thousand-object world is navigable only through text, metadata, semantic, and graph search operating over the *world model*, not the file tree.  
5. **Snapshot domains follow the core spec:** the entity store and event log for the *world* live inside the world snapshot domain; JEFF's persistent memory lives outside it, versioned separately.  
  
### 11.3 Event granularity (open)  
  
Not every keystroke is an event. Working heuristic: **an event is anything JEFF or the human might later need to explain, undo, or learn from.** Mutations below that threshold coalesce (e.g., a text-editing session emits one content-changed event with a diff, not five hundred). Compaction policy for old event ranges — full fidelity recent, summarized ancient — remains open.  
  
---  
  
## 12. Security notes specific to storage  
  
- **Memory poisoning inverts the rollback guarantee.** The stores that survive world rollback (JEFF's memory, and arguably high-trust edges) are precisely the most valuable write targets for an attacker. Everything durable needs provenance (`asserted_by`, `via` event), and untrusted-source content needs quarantine tagging *at write time*, because it cannot be rolled back later.  
- **Projections are attack surface** (§7.3).  
- **Entity `acl`s are the enforcement point** for worker scoping — Ring 3 grants should compile down to facet-level write capabilities, not VM-wide access.  
  
---  
  
## 13. Invariants (objects & storage)  
  
1. **Identity is frozen; everything else is a facet.**  
2. **IDs are never reused — across time, rollbacks, or world-lines.**  
3. **Kinds are conventions; no behavior may depend on kind-tags.**  
4. **Facets version independently; unknown facets are preserved, never dropped.**  
5. **Observed state (`status`) is written only by reconcilers; intent lives in `spec`.**  
6. **Every edge carries `asserted_by` and an event reference.**  
7. **Every facet renders to both pixels and tokens; projection is a schema obligation.**  
8. **Bytes live in the real filesystem; the object layer annotates, never imprisons.**  
9. **The event log is the truth; entity stores and indexes are rebuildable caches.**  
10. **Objects are forgotten gradually (lifecycle decay), never silently destroyed.**  
11. **Rollback resolves memory references to tombstones, never to errors or collisions.**  
12. **Durable writes from untrusted sources are provenance-tagged at write time.**  
  
---  
  
## 14. Open decisions  
  
- exact facet schema definition language and serialization (likely a small IDL → JSON/CBOR);  
- CRDT/merge semantics per facet class;  
- event granularity thresholds and compaction policy;  
- entity store engine (SQLite is the default assumption, not a commitment);  
- embedding model and vector index choice (disposable by design);  
- projection budget negotiation — who decides an entity's LOD in JEFF's context: JEFF, the context assembler, or salience alone;  
- whether edges are themselves entities (uniform but heavier) or a lightweight parallel table (current lean);  
- blob store deduplication/content-addressing scheme;  
- how far `spec`/`status` reconcilers extend beyond processes (network resources? external services?).  
  
---  
  
## 15. Summary  
  
The constitution, compressed:  
  
> **Identity is frozen. Facets are versioned. Semantics are free. Edges carry provenance. Liveness is spec/status. Every object renders to both pixels and tokens. Bytes stay in the filesystem. The log is the truth. Nothing understands everything — and nothing has to, because the world has a resident mind.**  
  
Every predecessor died trying to make objects legible to machines that couldn't read. Agora is built for a machine that can. The schema is shaped around that asymmetry everywhere: rigid bones, soft flesh, and JEFF turning the mess into meaning.