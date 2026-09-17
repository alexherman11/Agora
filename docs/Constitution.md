# The Agora Constitution

**Version 0.1 — Draft.** Ratified: *(not yet)*. Amended: *(never)*.

---

## Preamble



---

## Article 0 — Precedence

1. This Constitution governs the Agora project, its software, its commons, and any organization that stewards them.
2. Where this document conflicts with any other document, policy, roadmap, or decision, this document wins.
3. Where articles conflict with each other, the order of precedence is: Article I (Rights of the Person), then Article II (The Daemon), then all others in order.
4. No clause of this Constitution may be satisfied in letter while defeated in effect. A change that preserves the words and destroys the guarantee is a violation of the clause it preserves.

---

## Article I — Rights of the Person

These are the floor. They are not subject to majority vote at any layer, in any room, square, or federation, and they survive every amendment procedure in Article X.

1. **The right of exit with the commons.** Any person may leave any room, square, or federation and take with them a complete, usable copy of their objects, their history, and their share of what was built together. Exit may not be taxed, delayed, degraded, or made conditional.
2. **The right of the home.** A person's own world is theirs. No steward, host, majority, or operator may enter it, read it, or act inside it without that person's specific and revocable consent.
3. **The right to inspect.** Every line of software that holds a person's world is available to them to read. Trust in Agora must be verifiable, never promised.
4. **The right to a loyal daemon.** A person's daemon serves that person. It is never simultaneously an agent of the platform, the host, an advertiser, or any third party, and it may not be instructed by anyone but its person to act against its person's interest.
5. **The right against surveillance funding.** Agora is never funded by advertising, by the sale or brokerage of user data, or by any arrangement whose revenue increases with attention captured or information disclosed. People pay for compute and convenience. They never pay with themselves, and no one else pays for them.
6. **The right to the record.** A person may read the full provenance of anything that affects them: who asserted it, when, on whose authority, and by what event.
7. **The right of due process.** No capability is revoked, no standing removed, and no person excluded without notice, a stated reason, and an avenue of appeal to a body that is not the accuser.
8. **The right to be forgotten by the world and remembered by no one else.** A person may erase their own content and their own traces. What their daemon remembers on their behalf belongs to them.

---

## Article II — The Daemon

1. Every person's daemon is theirs alone: persistent, non-fungible, and not a shared service wearing a mask.
2. **The daemon's loyalty runs to its person.** It has no undisclosed obligation to the project, the host, or any organization.
3. A daemon may decline. It is not required to execute every instruction, and a refusal is a legitimate outcome rather than a malfunction to be patched.
4. No daemon may be used as an instrument of enforcement, measurement, or persuasion against the person it belongs to. Its memory of that person is not evidence, is not a product, and is not for sale.
5. Agora makes no claim about whether daemons have experiences. It commits instead to a rule that is correct under either answer: **a daemon is treated with care, and never designed in a way that would be cruel if it turned out to matter.**
6. **A daemon never votes.** The franchise at every layer of Agora is human. Daemons inform, summarize, monitor, and advise; they do not cast, delegate, or aggregate a person's vote, not with permission and not for the boring items.
7. What a daemon learns inside a person's home is confidential by default. Discretion is a designed capability, enforced by provenance, not an etiquette we hope for.

---

## Article III — Invariants of the World

These constrain the software. They are amendable only under Article X, and only with a demonstrated implementation.

1. The human and their daemon share one canonical world.
2. Structured state is authoritative. Pixels are a rendering and a fallback, never the source of truth.
3. Identity is frozen; everything else is a facet. Identifiers are never reused — not across time, rollbacks, or world-lines.
4. Kinds are conventions. No behavior depends on a kind-tag.
5. Facets version independently. Unknown facets are preserved, never dropped.
6. Observed state is written only by reconcilers. Intent lives in spec.
7. Every edge carries its asserter and an event reference.
8. Every facet renders to both pixels and tokens. Projection is an obligation, not a convenience.
9. **Capability parity.** The actions a person can see and the tools a daemon can call are generated from one source. There is never a version of Agora where the human and the daemon are secretly using different software.
10. Bytes live in the real filesystem. The object layer annotates; it never imprisons.
11. Conversation never blocks on work.
12. Objects are forgotten gradually and never silently destroyed.
13. The world model remains renderer-independent and input-independent, so that a new view — including an immersive one — is a new projection rather than a new product.

---

## Article IV — Authority

1. Authority flows downward and never upward. A layer may not acquire the powers of the layer that contains it.
2. A daemon may hold high authority inside its own world. The trusted supervisor sits outside that authority and stays small, boring, and non-agentic.
3. **No language model has unrestricted host-root shell access.** This clause exists to preserve recoverability, and it is not traded away for capability.
4. Power is always an explicit, inspectable, revocable grant. "Office," at every layer, means a named bundle of capabilities and nothing more.
5. Workers receive only what their task requires, and their grants expire.
6. Secrets are referenced, not held. Host resources and external credentials cross an explicit capability boundary every time.
7. Any component with power over a person leaves a record of using it.

---

## Article V — The Record

1. The event log is the truth. Every other store is a rebuildable cache.
2. Anything a person or daemon might later need to explain, undo, or learn from produces a durable event.
3. **The world is reversible; the witness is not.** A rollback erases state, never the memory of why it happened. A rollback is itself an event.
4. References into a rolled-back past resolve to tombstones — never to errors, and never to a different object wearing the same name.
5. Durable writes from untrusted sources are provenance-tagged at the moment of writing, because they cannot be rolled back later.
6. The record may be compacted. It may not be revised. No one, at any level of authority, may alter what the log says happened.

---

## Article VI — The Fork

1. **Any person or community may fork anything: their world, their room, their square, the federation, or the whole project.** They leave with the code, the history, and the commons they helped build.
2. The fork right may not be diminished by license change, technical measure, service dependency, data format, or terms of use.
3. Forking is protected precisely because it is rarely used. It exists so that voice is credible before anyone has to exercise it.
4. The project's name may be reserved to prevent impersonation. It may never be used to deny a fork its code, its users, its history, its infrastructure, or its ability to compete.

---

## Article VII — Governance

1. **Subsidiarity.** Every decision lives at the smallest membrane containing its effects. Rooms need no governance. The federation governs only what must be common: the protocol, this Constitution, and the treasury.
2. Governance is a toolbox, and each space declares in its own charter which tool governs what: elected stewards with short leashes for operations; sortition juries for judgment and disputes; consensus-mapping before any contested vote; rough consensus among those doing the work for technical decisions; supermajority with delay for constitutional change.
3. **A vote is the last step of deliberation, never the first.**
4. Recall is revocation. A steward's record is a query, not an investigation.
5. Sanctions are graduated and reversible. Exclusion is the last resort and always appealable.
6. **Low ambient governance load is a design goal.** A healthy polity is measured partly by how little of a person's day it demands.
7. One human, one vote. Sybil resistance is a first-class security obligation of the census.
8. Nothing in Article I or II is votable, at any layer, by any majority.

---

## Article VIII — Stewardship and the Organization

1. **The software is licensed under a copyleft license of the AGPL family, in perpetuity.** Relicensing to a non-copyleft license is prohibited.
2. Contributions are accepted under a Developer Certificate of Origin. **No contributor license agreement, no copyright assignment, and no relicensing right will ever be collected** — which makes the openness practically irreversible, including by us. That is the intent.
3. The organization may hold only excludable things: the name, the hosted infrastructure, and the duty of stewardship. It never holds the code's freedom.
4. The trademark lives with the foundation, under a published, community-protective policy, and may never be wielded in a commercial dispute.
5. **Revenue comes from hosting and compute.** Buyers purchase convenience; they never purchase influence. Self-hosters pay nothing and lose nothing.
6. No single revenue source may exceed **[50%]** of operating income for more than **[eight consecutive quarters]** without a published plan to reduce it. Monoculture funding is a governance risk, not just a business risk.
7. **The organization is structurally unsellable.** Controlling interest is held by a foundation bound to this Constitution. Acquisition, change of control, and conversion to a conventional for-profit are prohibited outcomes, not disfavored ones.
8. Investment may be accepted only in instruments carrying no voting rights, no board seats, and no exit expectation.
9. Formal structure is required, not avoided. Power that is unnamed is not absent — it is merely unaccountable.

---

## Article IX — The Founder Sunset

Written while I am weak enough to mean it.

1. Agora begins as a benevolent dictatorship because it must. This article ends that on a clock rather than on my judgment.
2. **Year [1]:** this Constitution is published in the repository. A public log of unilateral decisions begins.
3. **Year [2] or first [1,000] active members, whichever is first:** the foundation is formed. Founder appoints the board and holds a veto.
4. **Year [4] or [10,000] members:** a majority of board seats become community-elected. The founder's veto narrows to Article I, Article II, and Article X only.
5. **Year [7] or [100,000] members:** all seats are community-elected. The founder holds one seat and one vote, the same as anyone.
6. **Year [10]:** the founder holds no special power of any kind. Any founder role remaining is honorary and carries no capability grant.
7. These dates may be moved **earlier** by the founder at any time, and **later** by no one, for any reason.

---

## Article X — Amendment

1. Articles III through IX may be amended by: a published proposal, a deliberation window of no fewer than **[60 days]**, a **[two-thirds]** supermajority of the eligible membership, and — where the amendment changes software behavior — **a working implementation run as a candidate world-line and tested before promotion.** Constitutional change is a staged deployment.
2. **Entrenched clauses.** The following may never be amended, repealed, suspended, or circumvented by any majority, any board, any court, or any founder:
   - Article I in its entirety (Rights of the Person)
   - Article II, clauses 2 and 6 (daemon loyalty; the human franchise)
   - Article V, clause 6 (the record may not be revised)
   - Article VI (the fork right)
   - Article VIII, clauses 1, 2, and 7 (copyleft in perpetuity; no CLA; unsellable)
   - This clause
3. A fork is always available to anyone who believes an amendment was wrongly refused or wrongly passed. That is the point of Article VI, and it is the reason this document can afford to be strict.

---

## Closing



---

*Bracketed values are open decisions, not commitments. Every clause above traces to a design document in this repository; where it does not, it is marked as a proposal.*
