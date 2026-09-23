# Tessera research protocol

Question: can three independent GPT-5.6 builders produce a functioning program by
contributing structured declarations, without a coordinator integrating their code?

Coordinator owns interpreter, generic renderer, baseline fixtures and acceptance
tests. Builders own only declarations. Initial submissions are preserved by hash
before evaluation. Generic interpreter repairs and builder self-repairs count and
are reported. Passing syntax is insufficient: exercise composed behaviors and UI.

Trial 1: shared notes/research workspace. Notes: create/edit/archive; tasks:
completion, priority and derived progress on the SAME items; library: URLs, search
and references on the SAME items. All three extend shared note cards.

After each success: display the prototype and increase the challenge. Planned
escalations: shared-command reactions and cross-record invariants; overlapping
program edits and stale live edits; a substantially different application domain.
Future trials are adjusted to actual observed friction, not declared passed early.

Measure: module/claim counts, authoring overlap, first-submission acceptance,
coordinator edits to builder files (must be zero), delivery permutations,
functional workflows, invalid-operation atomicity, live browser behavior, failures.

Theory references (background, not a novelty proof):
* User-supplied essay on contribution sets and concern-typed composition.
* CALM/Bloom: https://bloom-lang.net/calm/
* BloomL: https://www2.eecs.berkeley.edu/Pubs/TechRpts/2012/EECS-2012-167.html
* Invariant confluence: https://arxiv.org/abs/1402.2237

Working disagreement: set-union convergence is not semantic correctness. Ordering
all handlers can hide lost intent. We instead join proposed effects and validate
the whole candidate. This localizes, but does not eliminate, coordination.
