# Security Addendum

**Direction and open alternatives — revised September 5, 2026.** This supersedes
the earlier instruction to build a fixed spine ending in world-root JEFF. The
claims/grants/effects distinction, explicit boundaries, and unresolved conflicts
in [[Security]] remain useful. Current implemented behavior is in [[Personal Lenses]].

## Useful delegation

The person should be able to give JEFF broad standing authority for ordinary,
reversible work. An explicit request to create or revise a personal view normally
authorizes that change within existing bounds. Repeated confirmation is not a
substitute for a well-defined boundary. New disclosure, spending, physical effects,
or expanded authority need their own applicable authorization.

## Protected external effects

A host-side supervisor, credential keeper, and effect brokers are a possible way
to protect resources outside a world. The authority journal, revocations, recovery
control, and external receipts must remain outside whatever root authority they
constrain. This is a desired boundary, not an implemented VM or broker system today.
A small policy interface does not imply that all integrations are easy to build.

## The internal trust model remains open

| Alternative | Useful freedom | Guarantee and limitation |
|---|---|---|
| Mediated live-world JEFF with broad candidate environments | Scoped object, file/build, and runtime capabilities; experimental code can be powerful inside bounded candidates | Internal records and authority can remain protected from candidate code. Concrete mediation must be implemented and tested. |
| JEFF with root inside its world | Broad internal self-modification | Internal integrity depends on trusting JEFF and world code. An external boundary can constrain specified crossings, but cannot make private-data labeling trustworthy when root can rewrite it. |

These alternatives are not equivalent without loss. Merely drawing one boundary
cannot preserve all internal invariants. Choose based on experiments and explicit
threat models before the corresponding authority is introduced. Current JEFF is a
client of the public verbs and projections, not a world-root process.

## Composition and display control

A private reader plus an allowed publisher can disclose data even when each tool
has a narrow schema. Destination-specific projections, candidate output, logs,
errors, and generated artifacts all belong in the analysis. The research in
[[scoped-collaboration]] and [[composed-export-model]] informs future sharing.
Claims do not grant authority; attribution is not proof of factual correctness.

The person and JEFF should eventually be able to reshape most of the display,
including the conversation panel. A dependable recovery surface preserves stop,
return-to-default, and authoritative permission information. A changed layout does
not grant access to private content or permission to disclose it.

## Recovery and sharing obligations

Keep current authority and external-effect evidence independent of restored work.
A lost receipt can leave an outcome unknown; safe retry depends on the receiver's
contract. Revocation cannot force an untrusted recipient to forget an earlier copy.
Retention, erasure residuals, shared history, and exit remain decisions to settle
before the affected sharing features are offered.

## Feature horizon, not build order

The capabilities in [[Agora Spec]] §22 are unordered aspirations beyond the current
notes-lens commitment. Bring raw-client security drills to each new boundary when
it is implemented. Compare useful tasks throughout development, rather than waiting
until every proposed subsystem exists. Neither a future room nor a personal lens
requires implementing a complete general-purpose broker catalog first.
