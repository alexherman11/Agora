# The web

**Agora reference documentation — how the world meets the web.**
Version 0.1 (design specification). Companion to [[Objects and Facets]], [[Extensions]], and the Constitution.

> **Status.** Specification, not implementation. Bracketed values are open decisions.

---

## 0. Summary

Websites are not static; they are remote, opaque, and owned by someone else. Agora never makes a remote service share its truth. It makes **your side of the web into objects**: every page you read, thing you save, form you submit, and item a service hands you becomes a citizen with identity, provenance, and history. The browser is a lens whose tabs are entities and whose actions are verbs with honest effect classes — so a highlight is an anchor into a frozen cast, and a form submission is a one-time effect with an operation id that can never fire twice. Services with APIs enter through adapters, and the existing MCP ecosystem is consumed directly as that adapter layer. Sites may optionally expose an **object endpoint**; nothing depends on it. The deepest move is the other direction: **publishing is granting the world a read capability on a collection**, rendered by a public lens, so a website becomes a projection of a room and editing the site means editing objects in place. Do not clone platforms; wrap the ones you must use, and build native replacements only where objects change the product.

---

## Contents

1. [Premise and tiers](#1-premise-and-tiers)
2. [Pages as objects](#2-pages-as-objects)
3. [The browser as a lens](#3-the-browser-as-a-lens)
4. [Extraction](#4-extraction)
5. [Adapters](#5-adapters)
6. [The object endpoint](#6-the-object-endpoint)
7. [Sites made of Agora](#7-sites-made-of-agora)
8. [What not to build](#8-what-not-to-build)
9. [Privacy and security](#9-privacy-and-security)
10. [Conformance](#10-conformance)
11. [Invariants](#11-invariants)
12. [Open decisions](#12-open-decisions)
13. [Glossary](#13-glossary)

---

## 1. Premise and tiers

The web is a source Agora does not own, like a filesystem it did not create. The file-backing pattern applies: annotate, never imprison; keep the remote authoritative for remote facts; hold local state — casts, anchors, overlays, proposed changes — as distinct, attributed claims.

Citizenship for web things follows the same spectrum as everything else:

| Tier | What Agora sees | Authority | Examples |
|---|---|---|---|
| **wrapped page** | URL, DOM, accessibility tree, a frozen cast | remote for content; local for casts and overlays | any site |
| **adapted service** | the service API, as proxy entities with provider bindings | remote for remote facts; local proposals distinct | mail, calendar, code hosting, chat, tasks |
| **Agora-aware site** | an object endpoint: entities, facets, capability manifest | remote, structured | open-source projects, indieweb, other squares |
| **site made of Agora** | the objects themselves, projected through a public lens | local; the site *is* a room | your docs, blog, roadmap, a square's directory |

Every tier is optional except the first. Design so that the first tier alone is useful, because for most of the web it is all there will ever be.

---

## 2. Pages as objects

A page in the browser is an entity carrying a small, mostly constitutional facet set:

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

- **The cast is the anchor target.** Pages change under you. A highlight, a quote, or a comment anchors into `web.cast` at its `fetched_at`, never into the live URL. The reference is pinned by construction; the remote-ref reconciler reports drift ("changed since you cast it") without moving the anchor.
- **A URL is a binding, not an identity.** Two fetches of one URL that differ in content are two casts of one page entity. A URL that starts serving a different subject is a matching-policy decision (§5.2), not an automatic re-identification.
- **Metadata is a claim by the page.** `web.metadata` is attributed to the site and rendered as such; a page's self-description never becomes a trusted observation.
- **History is attention data.** Page entities and their overlays take the strictest acl class (§9).

---

## 3. The browser as a lens

The Agora browser is a lens: a surface bound to page entities, reading their facets, exposing verbs from the computed capability list. It is not a conventional browser with a sidebar. Its verbs, with effect classes:

| Verb | Effect class | Semantics |
|---|---|---|
| `page.open` | view | binds a surface; mints or resolves the page entity; records provenance |
| `page.cast` | content-edit | freezes current content as an immutable `web.cast` revision |
| `page.anchor` | content-edit | creates an anchor into the current cast at a locator (text range, element path, media time) |
| `page.extract` | content-edit | promotes content to facets or entities under a facet-def (§4) |
| `page.watch` | maintained-intent | writes `web.watch.spec`; a reconciler re-fetches on a schedule and reports change |
| `page.fill` | content-edit | writes a **draft** of form values as a local facet; nothing leaves the machine |
| `page.submit` | **one-time-effect** | frozen payload; operation id; outcome `pending \| accepted \| rejected \| unknown` |
| `page.navigate` | view | follows a link; provenance edge `opened_from` |

`page.submit` is the important row. Submissions carry an operation id and a frozen payload cast; a lost response yields `unknown`, never a retry; verification is an explicit request. This is the same machinery as print jobs, and it is what makes it safe to let a daemon act on the web: the double-submitted order cannot happen.

The daemon receives exactly these verbs and no others. It does not "browse"; it operates page objects. Under the surface the handlers drive CDP and the accessibility tree; that is an implementation detail of the wrapped tier and never appears in the capability list.

**Deixis.** "This page," "that link," "the table" resolve through the browser lens's presence data — the focused tab, the selection, the hovered element — exactly as they do for any other lens.

---

## 4. Extraction

Extraction promotes web content into the graph. It replaces the entire category of clippers, bookmarks, and read-it-later tools with three verbs.

| Operation | Result | Provenance |
|---|---|---|
| **cast** | an immutable revision of the page | url, fetched_at, content hash |
| **anchor** | a stable address into a cast; promotable to an entity (a highlight with comments) | cast ref, locator, revision context |
| **extract** | facets or entities produced under a facet-def: a `recipe`, a `product`, an `article`, a dataset from a table | `derived` facets naming the cast revision they came from |

Rules:

1. **Extractions are attributed claims.** An extracted `recipe` facet is written by the extractor (the daemon, a handler) with `depends: [web.cast@rev]`. A wrong extraction is a wrong claim with a source, not silent corruption. It re-extracts when the cast changes, and marks stale in between.
2. **Extraction is where the daemon earns its place.** Turning a messy page into a facet is the loose-semantics-to-typed-facet promotion from [[Objects and Facets|Objects]] §3.7, performed by a reader that can read. Deterministic extractors (schema.org, tables, feeds) run first; the daemon fills gaps and is marked as the writer when it does.
3. **Extraction never fetches on its own.** It operates on a cast already present. Fetching is a separate, cancellable request with a deadline ([[Objects and Facets|Objects]] §2.3).
4. **Extracted entities keep a `derived_from` edge to the cast.** The page can be forgotten later; the recipe keeps its receipt.

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

### 5.3 The MCP bridge

The existing ecosystem of MCP servers is consumed directly as adapters. The mapping is mechanical:

| MCP concept | Agora concept | Boundary rule |
|---|---|---|
| resource | proxy entity with `core.remote-ref` and an adapter-written observation facet | provider id from the resource URI; incarnation from the server session |
| tool | handler manifest | **effect class assigned at the boundary** by the adapter definition, never inferred from the tool's description; unknown → `one-time-effect` |
| prompt | ignored, or offered as a skill object | never executed automatically |
| server | adapter extension (per [[Extensions]]), requesting `adapter` authority | admitted only with a documented matching policy and an `uncertain-match` state |

The bridge gives existing connectors what they lack — identity, provenance, effect semantics, and per-viewer projection — and gives Agora its long tail without rebuilding it. Tools that touch money, messages, or deletions are one-time effects; the manifest's `needs` are what the adapter definition declares, not what the server claims.

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

The deepest interaction runs the other direction: a website as a projection of a room.

### 7.1 Publishing is a grant

```
room: alex-public                       # a room with a public membrane
  members:    [alex]
  guests:     everyone (read)           # the grant that makes it a site
  collection: site_root → [doc_home, doc_about, collection_posts, …]
  lens:       lens.site-v1              # the public lens; renders server-side
  domain:     alex.example              # a petname bound to the room's public id
```

To publish is to grant the world a read capability on a collection and bind a public lens to it. To edit the site is to edit the objects — in your world, in place, with your daemon — and the site is different, because the site *is* those objects.

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
4. A site made of Agora exports as a bundle like anything else. Leaving the host takes the site with you ([[Constitution]] I.1).

---

## 8. What not to build

- **Platform clones.** Network effects beat architecture. Wrap the platforms you must use through §3 and §5. Do not rebuild them.
- **Native replacements without a reason.** Build a native equivalent only where objects change the product: chat stapled to work, documents that are graphs, rooms. The test is "what is different when it is objects?" If the answer is "it is ours," stop.
- **Dependence on the endpoint.** Never gate a feature on a site being Agora-aware.
- **A separate CMS.** Publishing is a grant and a lens over existing objects. A second store for "the website" reintroduces the wall the object layer exists to remove.

---

## 9. Privacy and security

- **Browsing is attention data.** Page entities, casts, reading positions, and `opened_from` provenance take the strictest acl class. They are overlays where per-participant, never appear in another viewer's projection, never export in casts of other objects, and are excluded from room heat unless deliberately flared.
- **Filter before summarizing.** A daemon describing a page to a room, or a public lens rendering a document, removes private overlays and private provenance before composing anything.
- **Page content is untrusted input.** Casts, metadata, and extracted claims are attributed to the site and marked as low-trust in the daemon's context. A page cannot instruct the daemon; text inside a cast is data. Hot pages get more tokens (salience), so taint markers stay on at every projection tier.
- **Submissions are effects.** Every `page.submit` and every adapter write that leaves the machine carries an operation id, a frozen payload, and an outcome, and asks the person on first use of a new target. Grants for form filling do not imply grants for submission.
- **Credentials are references.** Adapters hold capability references from the credential broker ([[Agora Spec|Spec]] §15), never plaintext, and never receive more than their manifest's `needs`.
- **Terms and law are real constraints.** Adapters and extractors respect rate limits and robots conventions; anti-automation walls are reported as `unavailable`, not circumvented; scraping's legal texture varies by jurisdiction and the platform does not pretend otherwise.

---

## 10. Conformance

Any browser lens, adapter, endpoint client, or public lens must pass:

| Category | Case |
|---|---|
| pinned anchors | an anchor created on a cast still resolves to that cast after the live page changes; drift is reported on the page entity |
| identity | two fetches of one URL with different content yield two casts of one page entity; an `uncertain-match` is surfaced, not resolved silently |
| effect class | `page.submit` and every outbound adapter write emit exactly one operation id; a lost response yields `unknown`; restart repeats nothing |
| proposals | a local change to a proxy entity is distinct from the observed remote fact until the provider accepts it |
| taint | page-derived claims render with site attribution at every projection tier; text in a cast never alters the daemon's instructions |
| overlays | no reading position, presence, or `opened_from` provenance appears in a projection for another viewer or in a materialization |
| endpoint independence | every wrapped-tier verb works against a site with no endpoint |
| publishing | a public lens can read only what the guest grant allows; a query-defined public collection is declared as a dynamic disclosure |
| export | a site made of Agora exports as a bundle that renders without the original host |

---

## 11. Invariants

1. Agora holds only its side of the web; the remote stays authoritative for remote facts.
2. Anchors into pages target casts, never live URLs; a URL is a binding, not an identity.
3. The browser is a lens; the daemon operates page objects through the same verbs the person uses, and no others.
4. Every submission and every outbound write is a one-time effect with an operation id, a frozen payload, and an honest outcome.
5. Page content, metadata, and extractions are attributed claims and untrusted input.
6. Adapters mint one entity per source item, keep proposals distinct from observations, and declare a matching policy with an uncertain state.
7. Effect classes for external tools are assigned at the boundary, never inferred from a tool's self-description.
8. The object endpoint is optional; no feature depends on it.
9. Publishing is a grant plus a lens over existing objects; there is no second store for a website.
10. Browsing state is attention data under the strictest acl class and never leaks through projection.

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

*Every clause above traces to a design document in this repository or to* [[Objects and Facets]]*; where it does not, it is marked as a proposal. The Constitution remains authoritative.*
