# How much of Agora are we reinventing?

18 September 2026. A comparison of the text-desk lab (`src/text-desk/notation`) against the
Agora design vault (`docs/`) and runtime (`src/agora3`), asked by Alex. Sources read: `docs/Agora Spec.md`,
`docs/Constitution.md`, `docs/Design Commitments.md`, `docs/Implementation Status.md`, `DECISIONS.md`,
the lab's `HANDOFF-shared-visual-desk.md`, `design-studio/00-handoff-architecture-and-challenge.md`,
`design-studio/SYNTHESIS.md`, `desk-shell/OWNERS.md`, `world.py`, `desk_moo.py`, `desk_knife.py`,
`deskd.py`, and `research/shared-visual-desk/synthesis.md`. Not every Agora reference doc was read in
full. Where a concept is not stated in the docs read, it is marked unknown, not absent.

## 1. Concept map

| Agora concept (doc, section) | Text-desk equivalent (file) | Status |
|---|---|---|
| JEFF, one-JEFF invariant (Spec §7; Constitution II.1) | `world.me = "jeff"`, one owner plus visitors (world.py; HANDOFF §6) | Partly. Nothing refuses a second concurrent "jeff"; it is a plain string, not a protected resident binding. |
| Worldlines / branching (`World(branch, revision)`, Spec §11) | None; one `World`, one pickle per session | Absent. |
| Claims vs grants vs effects (Spec §3, §12; Security) | Not modeled; verbs mutate directly | Absent. |
| Refuse-stale / epoch fencing (Spec §21.18; `expected_revision` in `src/agora3/world.py`) | `World.fence` (world.py:299) per object, extended to selections; the "seen fence" adds a per-actor-seen check | Converged, finer-grained. Agora fences per write; the lab also fences on whether this actor has looked lately, undescribed in the read docs. |
| Event log / evidence discipline (Spec §11, §21.9-12; Constitution IV) | `World.events`: actor, day, verb, undo; `why <id>` traces causation | Converged for the local case. In-memory list in a pickle vs. a SQLite journal with atomic transactions. Both separate intent from external effects. |
| Undo / causality (Spec §21.11) | `World.undo` restores prior state from a stored inverse; refuses if superseded or external | Converged: one small, tested mechanism for a stated principle. |
| Rules / automation, maintained intent (Spec §10, Reconcilers) | `rule when <selection> do <verb>`, `rule on <verb> do <verb>` | Partly. Event-triggered handlers, not a spec-vs-status reconciler; no blocked/conflict vocabulary. |
| Surfaces / UI shell, "desktop is the shell" (Spec §5) | `Surface`/`Appearance`, `desk-shell/` | Converged as ambition, early as implementation, built independently. |
| Notes/tasks first form | `kind: note, task`; Flint's Notes app | Converged. |
| Permissions / ownership between people (Constitution I.1; Security) | Lark's `reach` (mine/ours/world), `warm`/`claim`/`veil`/`bench` | New mechanism for a problem Agora's read docs leave open (one person and JEFF only). Rooms.md may cover more; unread, unknown. |
| Transport (Spec §14; `http_transport.py`, `gateway.py`) | `deskd.py`: bare `http.server`, one lockfile per session, unauthenticated `?as=` actor | Diverged in mechanism, same shape. Agora has a Principal/generation model over `ProcessLock`; the lab has no authentication. |
| Object/facet model (Spec §4, Objects and Facets) | `Subject`: kind, title, text, tags, due, comments, props, rev | Partly. Agora's facets are typed, versioned, overlaid per person; the lab's `props` bag is untyped and flat, no overlays beyond a reading-position sketch. |
| Verb registry / manifest (Spec §6) | `moo.REGISTRY`, kind chains, `examine` lists applicable verbs | Converged in shape, thinner: no effect-class or grant vocabulary. |
| Text projection of every app (Spec §21.2) | `text(ctx)` law in `desk-shell/OWNERS.md` | Converged, enforced more strictly day to day than anything cited in the docs read. |

## 2. Reinvention

The lab rebuilt, independently, several things Agora's docs already select or implement:

- **Revision-fenced writes.** The gateway already requires `expected_revision` per object in an atomic
  transaction. `World.fence` is the same idea at a smaller scale, plus a per-actor "seen" check the cited
  Agora docs do not describe: Agora fences per write, the lab also fences per actor's last look.
- **Event log as evidence.** Spec §11 already describes an append-only, replayable, actor/day-framed
  journal close in spirit to `world.py`'s `_event`. The lab's version is a throwaway in-memory list pickled
  to disk, no schema versioning, no crash recovery; Agora's is durable SQLite. Same idea, a much smaller
  instance built for fast iteration rather than production durability.
- **Undo via inverse operations.** Agora states replay reconstructs state and never repeats external effects
  (Constitution IV.2; Spec §21.11-12). `World.undo` is one concrete, tested mechanism for that principle.
- **A shell that is authored, hot-swappable content.** Spec §5 and §16 already call for exactly this.
  `desk-shell/`'s dock, windows, and `style/calm.style` are a small real instance, apparently discovered
  without reference to the Spec text.
- **A verb/handler registry keyed by kind.** Spec §6 already specifies manifest-registered handlers with
  `applies_to` facet requirements. `moo.REGISTRY` plus `KIND_CHAIN` is a smaller version, missing effect
  classification and grants.

None of this is wasted. The lab's versions are cheap and stress-tested against real sessions (the
seen-fence-on-container bug, the group bug, the boot-guard finding). Agora's versions are architecturally
more complete but, per `Implementation Status.md`, largely unexercised at the multi-actor, live-editing
granularity the lab has already run many real sessions against.

## 3. Genuinely new

Not described in the Agora docs read for this report:

- **Honesty marks on uncertain or perceptual claims**: `=` measured, `~` described at a revision, `?` opaque
  with extent, `!` stale (Lark, `lark-two-inhabitants.md`). Design Commitments discusses reporting what is
  known, but names no per-fact notation like this.
- **The seen fence per actor**, separate from the object-revision fence. Agora's stale-write check is
  object-level; no "has this actor looked lately" concept appears in the docs read.
- **The eyes protocol** (`iris-how-i-look.md`): a disciplined method for a screenshot-capable observer to
  report truthfully to a text-only agent, with blind prediction, `~` provenance for observed facts, and
  disagreements filed rather than silently resolved. Spec §21.2 says pixels are fallback perception, but
  specifies no reconciliation protocol between a sighted report and the textual record.
- **In-desk rule authoring as the scripting language**, with `why <id>` as a live audit trail and rules
  chaining through ordinary verbs. Agora's Reconcilers reference may cover related ground; not read in full,
  so unknown how concretely.
- **Warmth, reach, claim, veil, bench**: a co-presence etiquette vocabulary for two inhabitants sharing one
  world (Lark, round two). Finer than anything in Constitution Article VI as read here; Rooms may anticipate
  the problem differently, unknown.
- **One selection language shared by every command**: `?words`, `kind:`, `tag:`, `in:`, `age>`, used
  uniformly by verbs, rules, views, find and table. The docs read specify no single grammar used everywhere
  like this.
- **The holding/bulk distinction** (Flint, round two): a holding has desk identity but content living
  elsewhere; bulk material will never be enumerated and query is its only reading axis. Loosely related to
  "references say what they mean" (Spec §4), but more operational about what a text projection must refuse
  to claim.

## 4. Conflicts

- **No claim/grant/effect separation.** Spec §3 and §21.17 forbid claim-to-grant and claim-to-effect
  crossings everywhere. The lab has none: any actor who can see a thing can create, rewrite or delete it,
  limited only by the seen fence, which checks staleness, not authorization. Round four's own open list
  ("rules with owner= and reach=") confirms this is unresolved, not merely unwritten here.
- **Actor identity is an unauthenticated string.** `deskd.py`'s `Session` takes `actor` from a query
  parameter with no check, against Constitution II.2 and Article III.4's requirement that authority be
  explicit, inspectable and revocable, and the gateway's `Principal`-with-generation contrast case. Fine
  among trusted collaborators, not compatible with Agora's authority model unchanged.
- **One mutable world, no branch dimension.** Spec §11 treats `World(branch, revision)` as standing
  vocabulary; the lab's "session" names a pickle file, not a world-line. An unaddressed gap more than a
  contradiction, since Agora also leaves branching mechanics open.
- **Durability.** Constitution I.8 and Article IV.4-5 expect explicit retention and recovery contracts. The
  lab's session state is an unversioned pickle, with at least one stray `.pickle` under `sessions/` outside
  normal version control. Acceptable as a prototype shortcut, not to carry forward unchanged.

## 5. A fold-in path

1. **Keep the notation, replace the storage.** Treat `world.py`'s Subject/Appearance/Surface shapes as a
   UI-facing schema, backed by `agora3.world.World` (the SQLite journal) and `agora3.gateway.Gateway`'s
   `expected_revision`-checked `mutate`, instead of the in-memory pickle. Each desk verb becomes a thin
   translation into one gateway transaction, so the command language survives while durability comes from
   the real journal.
2. **Replace the session pickle with installed application state.** `deskd.py`'s load-mutate-save cycle
   under a lockfile maps onto `agora3.applications.Applications` plus `agora3.locking.ProcessLock`, which
   already give subject-bound appearances, installation identity, and a real reentrant lock.
3. **Replace `deskd.py`'s bare HTTP layer with `agora3.http_transport` and the gateway's Principal model.**
   This adds authentication and revocation in place of `?as=alex`, which the Constitution requires before
   the desk can safely hold more than the current trusted pair.
4. **Add a minimal claim/grant/effect boundary before opening the desk further.** Classify each verb in
   `moo.REGISTRY` by Agora's effect vocabulary, and gate cross-actor writes (acting on the other side, per
   Lark's `reach`) through a real grant check rather than the seen fence alone. This resolves the conflict in
   section 4 instead of deferring it.
5. **Land the desk as the first authored lens under `agora3.applications`, using `text(ctx)` as its
   contract.** The desk-shell's law already matches Agora's invariant that structured state is authoritative
   and pixels are fallback. Package `desk-shell/` as an installed application, source and manifest and
   digest, the way the Application Experiment did for Notes/Documents, so the desk becomes a concrete
   instance of "the desktop is the shell" instead of a parallel prototype confined to `research/`.

Steps 1 and 3 are prerequisites for step 4, and step 4 should land before the desk serves anyone beyond the
current one-owner-plus-visitors setup, since that is where the missing claim/grant boundary stops being a
design placeholder and becomes a real risk.
