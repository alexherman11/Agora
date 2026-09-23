# Design commitments

**Living design charter · September 10, 2026.**

This note names the commitments that give Agora continuity while its architecture
changes. It is deliberately shorter than the design references and more durable
than the current runtime. The [[Constitution]] states the moral direction;
[[Agora Spec]] tells the whole-system story; [[Implementation Status]] and
[[Runtime Guide]] say what exists.

Agora needs both freedom and memory. Freedom without commitments lets the project
become an ordinary agent platform by accident. Commitments without room to test
alternatives turn an early theory into a prison. The rule here is:

> Preserve the ends that make Agora worth building. Treat mechanisms as hypotheses
> until evidence and use earn them a narrower contract.

## What should survive architectural change

### A person has a home, not an account inside somebody else's machine

The person directs their environment and can understand, stop, recover, export
and leave it. Private work is not payment for access to JEFF. Authority is granted,
bounded and revocable; content, labels and model output cannot manufacture it.

### JEFF is a collaborator, not platform instrumentation

JEFF has continuity, a recognizable identity and a relationship with the person.
His loyalty runs to that person rather than an advertiser, host or hidden operator.
He may explain, question and decline. He is treated with care, and his knowledge
of the person is private by default. The implementation may use many models,
processes or memories without making those components separate masters.

### The environment becomes more capable through use

A request made during ordinary work can reveal a missing capability. JEFF and the
person should be able to build, test, keep, revise, reuse and remove that capability
without waiting for the platform repository to anticipate it. A useful default
environment comes first; customization is an opportunity, not an entrance fee.

### Recovery remains outside what is being rewritten

Authored applications, the shell and JEFF's working environment may change
substantially. Dependable stop, authority and recovery controls remain reachable
without their cooperation. No model receives unrestricted power over the boundary
that must recover from it.

### Meaning survives changes of view

A document is not its window. A recording is not its player. A conversation is
not a call. A person should be able to recognize the same subject across views,
sessions, tools and revisions, while copies, occurrences, activities, locations
and representations remain distinguishable when the difference matters.

### The system reports what it actually knows

Accepted intent, current observation, completed effect and uncertain outcome are
not collapsed into success. Important changes retain useful authorship and
provenance. Replay does not repeat external effects. Passing a narrow test never
becomes evidence for an untested whole-system claim.

### Ordinary use matters as much as invention

Agora should be pleasant for reading, writing, listening, watching, browsing,
communicating, organizing and making things. It must not become only a benchmark
in which a large model repeatedly builds demonstrations. Direct controls,
inspectability, recovery and export remain useful when JEFF or a model is absent.

### Shared places preserve privacy, consent and exit

A room should feel like a place people can return to, not a screen share with a
longer lifetime. Shared presence need not expose private content. Bringing work
into a room does not merge lives or authority. Leaving should be understandable,
and people should retain what they are entitled to without carrying away another
person's private overlays or credentials.

### Openness must resist capture in practice

People should be able to inspect the machinery trusted with their lives and move
their work elsewhere. The project should not depend on surveillance, behavioral
advertising or deliberate technical lock-in. Licenses, governance and operating
structures must eventually make these values real; prose alone does not.

## What is not fixed by this charter

None of the following is part of Agora's soul merely because one design document
once chose it:

- a universal heat or attention field;
- one facet schema, merge taxonomy, query language or storage encoding;
- one log topology for every local and shared subject;
- one reconciler model for every activity;
- one presentation engine, solver, coordinate system or operator vocabulary;
- a rule that every value, gesture or internal function becomes a native object;
- one copy/fork/publish ontology for every domain;
- one VM, hypervisor, programming language, model provider or process topology;
- ephemeral workers, a single executive loop or one permanent memory layout;
- a fixed approval ladder for work already covered by standing authority;
- one publishing architecture or a prohibition on familiar application forms;
- a predetermined federation, voting system, legal entity, revenue threshold or
  founder timetable.

These remain available designs. Some may become strong contracts in a particular
runtime or domain. None becomes universal merely through elegance.

## Status vocabulary

Documents use these meanings:

| Label | Meaning |
|---|---|
| **Constitutional value** | A project-level end that a replacement must preserve in effect. It is not a claim of present enforcement or legal ratification. |
| **Chosen direction** | The architecture currently being pursued. It can change through an explicit decision and better evidence. |
| **Current contract** | Behavior implemented or relied upon now. Exact APIs belong in [[Runtime Guide]] and evidence in [[Implementation Status]]. |
| **Design hypothesis** | A mechanism worth testing. Alternatives are welcome when they preserve the relevant commitments. |
| **Worked example** | Concrete reasoning, not a required schema or build order. |
| **Evidence** | A dated observation with a stated scope. It supports only what was exercised. |
| **Prototype lineage** | A contract or observation from another implementation line, preserved because it informs the design. It is not the current runtime API unless explicitly revalidated. |
| **Open question** | An unresolved choice. Absence of a choice is not permission to invent a guarantee. |

In older long-form passages, words such as “must” and “never” describe the safety
property or the proposed contract being discussed. They do not silently promote
every illustrative schema or mechanism into a constitutional rule. When that
reading would still be ambiguous, revise the passage rather than deleting its
argument.

## The change test

A substantially different architecture is welcome when it can answer:

1. Can the person still direct, inspect, stop, recover and leave?
2. Does JEFF remain the person's recognizable collaborator rather than another
   principal's instrument?
3. Can capability grow from use without platform special cases for every request?
4. Are authority, provenance, observation and uncertain effects still honest?
5. Do subjects remain understandable across views, revisions and tools?
6. Is ordinary direct use still good when no model is available?
7. Can private and shared life coexist without accidental disclosure or capture?
8. What evidence distinguishes the proposal from an attractive diagram?

A design that answers these well may replace almost any mechanism in the current
references. A design that cannot answer them has not earned the name Agora merely
because it uses objects, facets, agents or an event log.
