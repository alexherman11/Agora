# Security

The purpose of Agora's protection boundary is to let people and JEFF change the
environment substantially while preserving control, privacy and recovery. This
note distinguishes the current boundary from future mechanisms.

## Current boundary

The protected service admits authenticated native operations, validates schemas
and revisions, and appends durable events. Its keep stores current authority and
credentials outside native history. Revocation and commit use the same locking
discipline. Authored facets cannot forge protected runtime records.

The current development profile gives broad authority inside a dedicated Linux
VM. Package labels do not isolate root-capable programs from each other. The
guest cannot rewrite protected host files, account credentials, native authority
or independent recovery through the native bridge. A separate yard resets for
candidate execution and lacks the live native connection. There is no host-shell
fallback for authored guest code. [[Runtime Guide]] gives exact operations.

The editable shell receives a message bridge rather than operator credentials.
The parent supplies stop and recovery independently. JEFF's managed account
adapter is currently host-side, but its model tools are native discovery and
invocation with the runtime clock/composition facility. This is not a claim that
the whole agent orchestrator lives in the guest or that every availability and
input-spoofing attack is solved.

These are current authority and recovery choices, not a permanent commitment to
one hypervisor, process, programming language or universal evaluator. Trusted
bounded interpreters and isolated authored runtimes can have different locations.
Actual isolation and budgets matter; a pure-looking function signature is not a
sandbox, and property tests are not proofs of all possible behavior.

## Content, authority and effects

Imported text, tags, package descriptions, model output and observations are
data, not grants. Processing content does not give it new authority. Current
caller identity and delegation determine admitted effects. Useful classification
can affect a view without fabricating capability or permission.

One authorized request or standing delegation can cover several development
steps. A specific one-effect approval binds that effect; a standing grant covers
its declared work until expiry, limits or revocation apply. Do not invent repeated
approval prompts for ordinary edits already authorized by the person.

Human and agent controls can share action contracts while having different
principals and different projections. A local gesture need not be a public native
verb, and an advanced agent action need not have its own button. Both depend on
the actual installed capability registry at the semantic boundary.

## Recovery and evidence

Replay restores native records without running programs, sending messages or
repeating model calls. Historical state cannot restore revoked authority. Current
standing policy may authorize resumption; forks and duplicated workloads need
their own scope and resource consideration. Restoring package code, native data,
VM files and external reality remain distinct operations.

Logs should retain useful accepted actions and diagnostic evidence without
pretending that every frame or private payload must be permanent. Corrections,
retention and erasure are part of the design space. An append-only native journal
does not by itself implement witness memory, general deletion or external backup.

## Integrations and future boundaries

Describe relevant disclosure, resources and external effects, including compound
actions. Retry semantics come from the actual adapter: a one-time delivery,
idempotent update and repeatable observation are different. A response timeout
can leave an uncertain outcome; a receipt is not automatic deduplication.

Private annotations and overlays stay private by default, while intentional
exports can include selected user-owned content. Exporting content does not copy
executable grants or silently expand an audience. Minimize unrelated information
in projections and action inputs; generic inspectors can precede rich views.

Finer package isolation, multiple people, confidential integrations, device access,
federation and shared rooms may need additional boundaries. Add and test them
when the corresponding capability exists. Do not claim a planned manifest or
threat diagram already enforces them, or require a complete future security
framework before a useful local application can be developed.
