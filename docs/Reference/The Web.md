# The web

**Agora reference documentation — how the world meets the web.**
Restored design reference, revised September 10, 2026. Companion to [[Objects and Facets]], [[Extensions]], and the Constitution.

> **Status.** Product vision and candidate contracts, not the current web
> runtime. Agora3 has generic imported sources and native packages but does not
> implement this browser, adapter, endpoint, room-publication or external-effect
> stack. [[Implementation Status]] records what exists. Bracketed choices remain open.

---

## 0. Summary

Websites are remote, changeable and controlled by other parties. Agora cannot make
a remote service share its truth, but it can make a person's relationship to the
web legible: sources, captures, local documents, annotations, citations, drafts,
provider operations and uncertain outcomes can each retain the identity and
provenance they need. A browser, wrapper, source adapter and small native
replacement are all legitimate. References may pin evidence or deliberately
follow a live source. External effect semantics come from the actual provider
protocol, not one universal label. Publishing may be a live projection, static
release, exported file or provider-hosted artifact. Optional object endpoints and
room-backed sites remain useful experiments rather than dependencies.

---

## Contents

1. [Premise and tiers](#1-premise-and-tiers)
2. [Pages as objects](#2-pages-as-objects)
3. [The browser as a lens](#3-the-browser-as-a-lens)
4. [Extraction](#4-extraction)
5. [Adapters](#5-adapters)
6. [The object endpoint](#6-the-object-endpoint)
7. [Sites made of Agora](#7-sites-made-of-agora)
8. [Choosing what to build](#8-choosing-what-to-build)
9. [Privacy and security](#9-privacy-and-security)
10. [Conformance](#10-conformance)
11. [Invariants](#11-invariants)
12. [Open decisions](#12-open-decisions)
13. [Glossary](#13-glossary)

---

## 1. Premise and tiers

The web is a source Agora does not own, like a filesystem it did not create. Keep
remote facts attributed to their source and hold local state—captures, anchors,
overlays and proposed changes—distinct. A workflow can expose a bounded remote view
without first importing every item into the native store.

Citizenship for web things follows the same spectrum as everything else:

| Tier | What Agora sees | Authority | Examples |
|---|---|---|---|
| **wrapped page** | URL, DOM, accessibility tree, a frozen cast | remote for content; local for casts and overlays | any site |
| **adapted service** | the service API, as proxy entities with provider bindings | remote for remote facts; local proposals distinct | mail, calendar, code hosting, chat, tasks |
| **Agora-aware site** | an object endpoint: entities, facets, capability manifest | remote, structured | open-source projects, indieweb, other squares |
| **site made of Agora** | the objects themselves, projected through a public lens | local; the site *is* a room | your docs, blog, roadmap, a square's directory |

All tiers are optional design choices. A conventional or lightly wrapped browser
must remain useful because most sites will never expose Agora-specific structure.

---

## 2. Pages as objects

A richly integrated browser may represent a page as an entity carrying facets
like these; simpler readers can retain only the source and evidence they need:

```
page_31
  core.remote-ref     { provider: web, url, fetched_at }        # adapter
                      status { reachable, changed_since_cast }  # reconciler
  web.cast            { content_hash, readable_text, dom_snapshot_ref, fetched_at }   # immutable
  web.metadata        { title, site, canonical_url, og/schema.org claims }   # derived, attributed to the page
  core.reading-position [participant]                            # overlay
  core.tags, core.summary                                        # intent / derived
  core.provenance     { opened_from: msg_204 | search_9 | page_30 }
```

Rules:

- **Pinned and live references mean different things.** A citation or evidentiary
  quote can anchor into `web.cast` at its `fetched_at`. A comment, follow-along
  selection or live annotation may track a changing document when the adapter has
  an explicit mapping. Preserve the original context and report ambiguity rather
  than silently retargeting either kind.
- **A URL is a binding, not an identity.** Two fetches of one URL that differ in content are two casts of one page entity. A URL that starts serving a different subject is a matching-policy decision (§5.2), not an automatic re-identification.
- **Metadata is a claim by the page.** `web.metadata` is attributed to the site and rendered as such; a page's self-description never becomes a trusted observation.
- **Browsing history is sensitive.** Page entities and overlays follow the
  person's retention and audience policy; not every source record needs permanent
  native residency.

---

## 3. The browser as a lens

One Agora-native browser could be a lens bound to page entities and semantic
operations. This does not forbid a conventional browser, sidebar, provider client
or guest automation path. The following table is an illustrative contract:

| Verb | Effect class / crossing | Semantics |
|---|---|---|
| `page.open` | view; network if fetching | binds a surface; mints or resolves the page entity; fetching needs its own current network authority |
| `page.cast` | content-edit | freezes current content as an immutable `web.cast` revision |
| `page.anchor` | content-edit | creates an anchor into the current cast at a locator (text range, element path, media time) |
| `page.extract` | content-edit | promotes content to facets or entities under a facet-def (§4) |
| `page.watch` | maintained-intent | writes `web.watch.spec`; a reconciler re-fetches on a schedule and reports change |
| `page.fill` | content-edit | writes a **separate local draft**; does not type into the live page |
| `page.input` | resource-use; possible disclosure/one-time effects | delivers input to a live page; scripts can transmit or submit it before a submit button is clicked |
| `page.submit` | provider operation | committed payload; provider/idempotency reference where supported; observed outcome `pending \| accepted \| rejected \| unknown` |
| `page.navigate` | view; network | follows a link under current network authority; provenance edge `opened_from` |

An effect descriptor must name relevant crossings as well as its main lifecycle class. A `view` label does not prove that navigation is local; a content-edit label does not make live-page typing private.

`page.submit` is the important row. Retain enough of the committed input and
provider response to distinguish accepted, rejected and uncertain outcomes. Retry
only according to the provider's real idempotency/status contract and the person's
intent. A local operation id helps correlate attempts but cannot make an arbitrary
provider deduplicate them.

The browser's native controls and JEFF's browser tools derive from these operation contracts. Other installed tools and explicit guest execution may provide additional ways to act; do not claim that arbitrary guest automation inherits the native browser's semantic guarantees. Under the surface, handlers may drive browser automation or accessibility APIs; the boundary still checks their actual effects.

**Deixis.** "This page," "that link," "the table" resolve through the browser lens's presence data — the focused tab, the selection, the hovered element — exactly as they do for any other lens.

---

## 4. Extraction

Extraction can promote selected web content into native structure. It may coexist
with ordinary bookmarks, browser history, clippers and provider-native reading
lists rather than replacing them by decree.

| Operation | Result | Provenance |
|---|---|---|
| **cast** | an immutable revision of the page | url, fetched_at, content hash |
| **anchor** | a stable address into a cast; promotable to an entity (a highlight with comments) | cast ref, locator, revision context |
| **extract** | facets or entities produced under a facet-def: a `recipe`, a `product`, an `article`, a dataset from a table | `derived` facets naming the cast revision they came from |

Rules:

1. **Extractions are attributed claims.** An extracted `recipe` facet is written by the extractor (the daemon, a handler) with `depends: [web.cast@rev]`. A wrong extraction is a wrong claim with a source, not silent corruption. It re-extracts when the cast changes, and marks stale in between.
2. **Extraction is where the daemon earns its place.** Turning a messy page into a facet is the loose-semantics-to-typed-facet promotion from [[Objects and Facets|Objects]] §3.7, performed by a reader that can read. Deterministic extractors (schema.org, tables, feeds) run first; the daemon fills gaps and is marked as the writer when it does.
3. **Fetching remains explicit in the evidence.** It may be a separate request or
   part of one authorized adapter operation, but the resulting observation names
   its source, time and completeness.
4. **Extracted entities retain useful source context.** A `derived_from` edge to a
   cast is strong evidence when the retained bytes justify its cost; a live source
   reference may be sufficient for less durable workflows.

---

## 5. Adapters

Most web applications people spend time in have APIs. An adapter turns a service into proxy entities, following [[Objects and Facets|Objects]] §11.1.

### 5.1 The proxy entity

```
issue_4471
  core.remote-ref   { provider: github, account: alex, provider_id: "repo#4471", incarnation }   # adapter
                    status { last_observed, freshness, reachable }
  gh.issue          { title, state, labels, body_cast }        # adapter-written observation of remote facts
  core.proposal     { state: closed }                          # local intent, distinct from observed
  core.tags, core.summary, core.reading-position [participant]
```

- **The provider is authoritative for remote facts.** `gh.issue` is an observation with freshness; it is never edited locally.
- **Local changes are proposals** until the provider accepts them. Submitting a proposal is a one-time effect with an operation id and an outcome; on `accepted`, the next observation reflects it; on `unknown`, the proposal stays visible as unresolved.
- **One entity per source item.** Repeated observation updates the binding; it does not mint duplicates.

### 5.2 Matching policy

Every adapter documents how it decides that two observations are the same item, and declares an `uncertain-match` state for when it cannot. A URL or title change is a matching decision; semantic similarity may propose a relationship and may never merge identities. Consolidation by a person preserves old references ([[Objects and Facets|Objects]] §2.2).

### 5.3 Connector and MCP bridges

Existing connector and MCP ecosystems are candidates for the adapter layer. The
mapping is not automatic: each bridge must classify identity, authorization,
disclosure and retry behavior from its actual protocol rather than trusting prose.

| MCP concept | Agora concept | Boundary rule |
|---|---|---|
| resource | proxy entity with `core.remote-ref` and an adapter-written observation facet | durable provider identity and resource version; adapter session tracked separately |
| tool | handler or connector operation | effect/disclosure contract assigned by the trusted adapter definition, never inferred from the tool's description; unknown behavior is surfaced or conservatively constrained |
| prompt | ignored, or offered as a skill object | never executed automatically |
| server | adapter extension (per [[Extensions]]), requesting `adapter` authority | admitted only with a documented matching policy and an `uncertain-match` state |

A bridge can add durable identity, provenance and honest effect semantics where the
underlying connector lacks them. Money, messages and deletion deserve constraints
appropriate to their consequences, but their exact lifecycle may be idempotent,
repeatable, reversible, compensatable or uncertain rather than uniformly
“one-time.” Declared needs are reviewed at Agora's boundary, not self-granted by
the remote server.

---

## 6. The object endpoint

A site may expose an object endpoint: a discovery convention through which an Agora browser reads structured state instead of DOM.

```
GET /.well-known/agora
  → { entities: [...refs], facet-defs: [...], capabilities: manifest, publisher: identity }
GET /agora/entity/<id>
  → { id, facets: {...}, edges: [...], projection: {12, 60, 250} }
```

Rules:

- **Optional, and nothing depends on it.** This is the RSS/OpenGraph/ActivityPub move; it has their adoption curve. The wrapped tier must remain complete without it.
- **Remote entities stay remote.** An endpoint entity is bound through `core.remote-ref` like any adapted item; the site is authoritative; local state is overlays, casts, and proposals.
- **Capabilities are manifests.** A site's verbs enter the capability list with effect classes assigned at the boundary, exactly as in §5.3. An endpoint may offer a verb; it may not grant itself anything.
- **Projection is served, not trusted.** A site's own projections are attributed to the site and rendered with that provenance.

Realistic early adopters: open-source projects, indieweb sites, other Agora squares, and every site the daemon builds (§7).

---

## 7. Sites made of Agora

One particularly coherent publication mode runs the other direction: a website as
a projection of a room or collection. It is not the only legitimate publishing
path.

### 7.1 Live publication as a grant

```
room: alex-public                       # a room with a public membrane
  members:    [alex]
  guests:     everyone (read)           # the grant that makes it a site
  collection: site_root → [doc_home, doc_about, collection_posts, …]
  lens:       lens.site-v1              # the public lens; renders server-side
  domain:     alex.example              # a petname bound to the room's public id
```

For a live Agora-hosted site, publishing can mean granting an audience read access
to a collection and binding a public lens. The binding names selected revisions or
an explicitly live view. Editing a live published object can update the site;
editing a private working revision does not publish it merely because the same tool
renders both.

A static release instead materializes selected content and can remain available
without a personal world online. An exported file or provider-hosted artifact has
its own update, retention and takedown contract. These modes may use different
stores without betraying Agora; the important requirement is that their relation
to editable source is explicit.

### 7.2 Two kinds of visitor

| Visitor | Receives | Can do |
|---|---|---|
| without Agora | HTML — a materialization, exactly as a document leaves as markdown; casts of widgets carry their fallback and source | read |
| with Agora | the objects, through their own browser lens | anchor, annotate, cast, subscribe (`page.watch` against a live entity), and send comments back as edges the publisher can see |

Comments from visitors are entities resident in the *visitor's* world, edged to the published object, and offered to the publisher's room as guests. The publisher chooses whether they appear. Nothing a visitor writes enters the publisher's log without a grant.

### 7.3 What this makes cheap

- A blog is a collection of documents with a public lens; the "editor" is the document lens you already use.
- A team roadmap is a living collection with a guest grant; it updates when the tasks do.
- Documentation is the reference document itself, with widgets live and diagrams operable by the reader's daemon.
- A square's directory is a collection published by the square.
- Editing in place: dragging a block on your published page is `page.anchor` + a collection reorder in your own world; there is no separate CMS state to synchronize.

### 7.4 Rules

1. The public lens runs server-side under the room's grants and nothing more; it can read what guests may read and nothing else.
2. Publishing a living query freezes membership or explicitly grants the dynamic view ([[Objects and Facets|Objects]] §6). A public collection defined by a query is a standing disclosure channel and must be declared as one.
3. Overlays never publish. A publisher's reading positions, presence, and private annotations are not in the materialization or the endpoint, by the projection rule (§9).
4. A site made of Agora should export the source, retained assets and dependencies
   needed for its promised mode. Leaving the host should take a useful site with
   you ([[Constitution]] I.2, V.1).

---

## 8. Choosing what to build

- **Wrap when network and provider features dominate.** Existing platforms often
  remain the right authority and interface; an adapter can improve continuity
  without recreating the service.
- **Build native when the workflow benefits.** A small reader, chatbot, document
  editor or platform-like replacement is legitimate when it improves usefulness,
  malleability, privacy, continuity or speed. It need not prove theoretical novelty.
- **Do not depend on Agora-specific adoption.** No ordinary reading capability
  should require a site to expose the optional endpoint.
- **Keep publication relationships explicit.** A live projection can avoid a
  second editable CMS. Static builds and provider-hosted copies may use separate
  artifacts when their source, audience and update policy remain understandable.

---

## 9. Privacy and security

- **Browsing is sensitive attention data.** Page entities, casts, reading
  positions and `opened_from` provenance follow explicit audience and retention
  policy. Per-person overlays are private by default; a person can deliberately
  export selected annotations or history.
- **Select audience before composing.** A daemon describing a page to a room, or a
  public lens rendering a document, excludes inputs not authorized for that
  audience before summarization or rendering.
- **Page content is untrusted input.** Casts, metadata and extracted claims remain
  attributed to the site. Their text is data, not authority, though a model with
  broad existing authority can still be influenced by prompt injection; provenance
  alone is not a sandbox.
- **Submissions are effects.** Every `page.submit` and every adapter write that leaves the machine carries an operation id, a frozen payload, and an outcome, under the applicable standing delegation or a new grant when needed. Authority to edit a local draft does not imply authority to deliver it to live page scripts or submit it.
- **Minimize credential exposure.** Prefer scoped references and provider-mediated
  credential use where available. A development adapter may have broader access;
  document that compromise domain instead of claiming manifest labels isolate it.
- **Terms and law are real constraints.** Adapters and extractors respect rate limits and robots conventions; anti-automation walls are reported as `unavailable`, not circumvented; scraping's legal texture varies by jurisdiction and the platform does not pretend otherwise.

---

## 10. Conformance

Use the relevant rows below as acceptance cases for a browser lens, adapter,
endpoint client or public lens. A small reader need not implement every future
mode before it can be useful.

| Category | Case |
|---|---|
| references | a pinned citation still resolves to its retained evidence after the live page changes; a live-following reference preserves old context and surfaces ambiguous mapping |
| identity | two fetches of one URL with different content yield two casts of one page entity; an `uncertain-match` is surfaced, not resolved silently |
| external operations | committed inputs, provider identifiers and observed outcomes are retained as appropriate; a lost response can remain `unknown`; retry follows the provider contract and user intent |
| proposals | a local change to a proxy entity is distinct from the observed remote fact until the provider accepts it |
| taint | page-derived claims remain attributed; reading a cast never installs a skill or changes authority; model resistance to injected instructions is evaluated separately |
| overlays | private reading position, presence and provenance stay out of another viewer's projection; deliberately selected user-owned annotations can be exported |
| endpoint independence | every wrapped-tier verb works against a site with no endpoint |
| publishing | each live, static or provider-hosted output names its audience, content/revision scope and update policy; a dynamic public query is declared as a standing disclosure |
| export | the exported site contains the bytes and dependencies promised for its mode and states which remote sources may become unavailable |

---

## 11. Invariants

1. Agora holds only its side of the web; the remote stays authoritative for remote facts.
2. Pinned citations and live-following references are distinct contracts; neither silently retargets when identity or mapping is ambiguous.
3. Native browser controls and tools share semantic contracts; general guest automation is an explicitly broader capability, not an undisclosed second native browser model.
4. Outbound operations retain committed inputs and honest outcomes proportionate to consequence; local IDs do not establish provider-side deduplication.
5. Page content, metadata, and extractions are attributed claims and untrusted input.
6. Adapters mint one entity per source item, keep proposals distinct from observations, and declare a matching policy with an uncertain state.
7. External-tool effects and disclosures are classified at the trusted boundary from actual behavior, never inferred solely from a tool's self-description.
8. The object endpoint is optional; no feature depends on it.
9. Live projection, static release, exported files and provider-hosted artifacts are legitimate publication modes with explicit source, audience, retention and update semantics.
10. Browsing state is sensitive and private by default; deliberate exports include only the selected, authorized material.

---

## 12. Open decisions

- cast storage policy: full DOM snapshots versus readable text plus selectors; retention horizon for casts;
- locator scheme for page anchors under DOM drift (text-quote selectors, element paths, hybrid);
- the `.well-known/agora` discovery format and its relationship to schema.org and ActivityPub vocabularies;
- MCP bridge defaults: how unknown tools are classified and how `needs` are derived from adapter definitions;
- server-side public lens runtime and its sandbox;
- how visitor comments are offered to publishers, and spam handling at the membrane;
- the domain-to-room petname binding and what identity anchoring it requires;
- when a changed URL is a new page versus a moved one.

---

## 13. Glossary

**Adapter** — a component that turns a service into proxy entities; holds provider bindings and a matching policy.
**Cast (web)** — an immutable revision of a page's content at a fetch time; the target of all anchors.
**Endpoint** — a site's optional structured interface exposing entities, facet-defs, and a capability manifest.
**Materialization** — the HTML a site made of Agora serves to visitors without Agora.
**Page entity** — the object representing a page: remote-ref, casts, metadata, overlays, provenance.
**Proposal** — a local change to a proxy entity awaiting provider acceptance.
**Proxy entity** — an entity standing for a remote item, with the remote authoritative for remote facts.
**Public lens** — a lens bound to a room's public collection, rendering it for guests under the guest grant.
**Public membrane** — a room grant that admits everyone as a reader.

---

*The Constitution states the durable design commitments. The mechanisms here are
candidate applications of them, not current implementation claims or mandatory
prerequisites for a useful web workflow.*
