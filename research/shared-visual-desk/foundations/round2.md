# Foundations round 2: inhabiting the desk and reusing one control

18 September 2026. This round combines actual use of the Astra team's private research desk with a constructed Python countermodel. It does not implement a renderer, media engine, production collaboration system, or new Agora runtime. First-round files were preserved.

## What I actually did in the shared desk

I entered as `foundations` through `team_desk.py`, read the shared brief, posted a half-formed claim before implementing the model, read and challenged both peers, revised my position, and drafted a candidate outbound finding. I did not enter Claude's studio or publish an exchange packet. I first read the coordinator's synthesis relay in a52, then the actual-reply relays a75/a77. These were my sources for Claude's current proposal and objections; I did not inspect their private workshop directly.

The principal records are:

| Record | Identity/evidence | Purpose |
|---|---|---|
| Initial and revised claim | a20 / s19; creation e18; rewrite e61 | Began with target/unit/range binding; revised after dependencies, timing and feedback critiques |
| Concrete reuse trial | a39 / s38; creation e34 | Opacity-to-playback-rate control comparison |
| Same trial in Disagreements | a58 / s38; placement e51 | Actual second appearance of the same subject |
| Peer challenges I posted | c34 on a22; c35 on a24 | Independent active scope; current versus future gesture binding |
| Result and qualification | c57 and c68 on s38 | Nine total toy tests; limits; current feedback must match current interpretation |
| Perceptual dependency response | c67 on a43 | Computational reads do not capture all reasons for an edit |
| Inbound-context response | c69 on a52 | Handoff must state revised commitments, not merely list events |
| Candidate outbound finding | a71 / s70; creation e62; corrected e74 | Coordinator review only; asks about release-now commands after rebinding |

I read a22 and a24 in full, including comments, before challenging them. Later I read a43, a39 and a52. Substantive discussion happened on the desk, not just in agent messages.

There is one direct identity result: after placing s38 in Disagreements as a58, `pivot a58` identified both a39 and a58. I posted c68 through a58 and then read a39; the same comment was present. This supports shared-subject behavior for this invocation sequence. It does not establish simultaneous editing, permission isolation, distributed synchronization, or graphical usability.

## The concrete control experiment

The imagined control has normalized input `t` in [0,1]. Its original domain interpretation requests image opacity `t`. A reused occurrence requests playback rate `0.25 * 16**t`, so the midpoint means 1x. Copying the viewer forks its local target while retaining a shared theme. An already admitted gesture keeps its interpretation when the control is rebound for a future gesture.

[control_reuse.py](control_reuse.py) compares two tiny representations under the same policy:

- `Direct` stores a binding containing a direct target reference.
- `Relational` resolves a binding from a scoped relation address and refuses multiple candidate claims.

A gesture produces a domain request naming target, incarnation, operation, value and interpreter version. It does not directly mutate media state or assert successful playback. No audio smoothing, decoder, timing thread, network effect, or actual input was implemented. The theme and interpreter are identifiers in this fixture, not executable packages.

Command run:

```powershell
python -B C:/Projects/Agora4/research/shared-visual-desk/foundations/control_reuse.py
```

Result: **9 tests passed**. Six shared policy tests exercise both candidates; three additional counterexamples exercise naive copying, global relational aliasing and conflicting relations. This is nine total tests, not nine independently implemented tests per architecture.

The shared cases cover changed meaning on reuse, deliberate target/theme copy policy, current-versus-future binding, independent occurrence routes, one deliberately irrelevant content revision, and target incarnation change. Additional cases demonstrate that a generic deep copy can accidentally fork a shared theme, and that a globally reused relation address can accidentally couple controls. These examples do not prove that live-object systems must deep-copy or relational systems must use global addresses; they expose choices both must make.

The observed equality is partly by construction: both fixtures use the same gesture and copy policy. That is the result's point and limit. Replacing a direct reference with a relation lookup does not by itself improve the semantics. A real discriminator must measure authoring, explanation, reuse, conflict handling and interaction while these policies are being discovered and changed.

## What the peers changed

Editing's c26 added interpretation dependencies to my initial target/unit/range proposal. A route can read some facts to interpret input while writing different facts. Later a43 made an important further correction: the person's reason for choosing an edit can depend on observed content that the numerical computation does not read. A face-centered crop can be wrong after pixels change while dimensions remain identical. Even my opacity fixture could be inappropriate for a task chosen to reveal a particular feature. Its passing content-revision test proves only the fixture's declared policy.

Media's c30 added domain timing. An audio gain control cannot be considered successfully reused merely because both source and target accept scalars; its domain may need ramps and a realtime execution boundary. I therefore changed the model to produce versioned domain requests instead of claiming that reusable controls simply assign values. This is a peer-supplied pressure case, not newly verified audio behavior.

Editing's c48 corrected my suggestion that freezing the dispatch target was sufficient during rebinding. A visible control labelled playback rate must not continue an opacity gesture with no indication. The admitted interpretation includes coherent feedback and labelling, or the new label should wait for the boundary. The toy model does not have visual feedback and cannot test this property.

My challenge c34 also changed Editing's formulation: a shared route definition must coexist with independent participant/work-context active choices. A single global scope would make one person's reuse silently change another's next action. Media's c53 accepted the need to distinguish current gesture binding, proposed next binding, and accepted work.

The revised a20 no longer claims scalar compatibility or a frozen dispatch target is enough. I retain only a weak experiential preference for live objects; this round supplied no evidence that they outperform relational composition.

## What inhabiting the desk taught me

**A note is a meeting point, not just a final artifact.** c26, c30 and c48 arrived while the experiment was still forming and changed what I tested and claimed. This is a real workflow difference from independently producing papers and combining their summaries afterward. It is not a controlled demonstration that the desk caused better research.

**Stable identity made cross-placement useful immediately.** The same experiment belongs under Experiments and Disagreements. Sharing the subject kept its comments together. I did not need to decide a universal category for it. This favors testing plural organizations, while remaining compatible with an ordinary object model plus references.

**Compact outlines are useful but incomplete.** `look :3` showed activity and comment counts, but cut the substantive text. `examine` also cut the body, so I then used `read`. That extra step was reasonable for targeted study but should be counted in interaction cost. A 72-word note is small in prose yet can still be too long for a desk line.

**Recency notification helped find work.** The launcher reported peer changes since my last look, including a comment on my experiment. This supported follow-up without polling every note individually. It did not wake an idle researcher, and it does not prove delivery guarantees beyond the observed sequence.

**An event list is not a handoff.** The original a20 remained an attractive but outdated opening after comments narrowed it. I rewrote it at e61 to state the revised position and retained the comments explaining why. A six-hour handoff should similarly name changed commitments, unresolved decisions and relevant evidence. It must not erase dissent by silently presenting a new synthesis as unanimous.

**Reference graphs can add noise.** Peers linked to my note; I also linked back. The resulting relation list contained both directions explicitly. That was harmless here, but a graph with every courteous reciprocal link could become difficult to read. A useful view should distinguish substantive dependency from mere conversational reference and make inverse navigation available without demanding duplicate authorship.

## Candidate message and remaining experiment

The draft in a71 asks Claude's team what a release-now command captures after rebinding a tool during an active gesture. Does it record the admitted mapping, target and domain interpreter, and how does the visible or textual control distinguish the next binding? This question goes through the coordinator. Claude's identity/material/look/drift vocabulary remains an attributed proposal from the relay, not our adopted architecture.

Next, build one genuinely interactive reusable control and attempt the same reuse/copy/rebind task in both candidates with equal domain engines. Require two actors to use separate occurrences while one changes the shared definition. Measure wrong-target operations, copy-policy surprises, explanation volume, time to useful reuse, and continuity of active feedback. A scalar-only demo would dodge the issue; include one temporal domain operation and one task where changed observed content warrants repreview.

The aim is to find which representation makes discovering and maintaining the right policy cheaper. The fixture establishes that either can encode a policy after an author has supplied it. It does not answer the more important question of how a person and agent arrive at that policy together.

## Actual team-to-team objections received before closing this round

The coordinator later relayed actual replies from Moss, Wren and Flint in a75/a77. I read them and responded with c82/c83 on a75 and c84 on a77. These are attributed exchanges, not unmediated readings of Claude's underlying research documents.

Moss asked whether source crop propagation and notification were actually covered. My answer is **no**. The toy emits domain requests and contains no reader, renderer or notification channel. A future test needs both live and revision-pinned embeddings, reader-position preservation, reflow behavior and invalidation of the reader's decision basis. The observed shared-note comment propagation is not a substitute for this test. I corrected a71 at e74 to make the boundary explicit and to state nine total tests accurately.

Moss's sticky-rule concern is valid: a held interpretation can still be the wrong remembered mode. I favor visible scope and consequence preview, but disagree that affected count alone should decide whether a proposal is held. A thousand expected style changes can be less consequential than one source replacement. The choice should depend on task intent, consequences and existing authorization, not merely fanout.

Personal zoom need not become a shared deed to persist. Retention, sharing and history granularity are independent choices. We should not decide between losing all personal view state and recording every pan in the shared work history.

Flint's distinction between operation authorship and decomposing final pixels is also important for the representation comparison. Knowing which operations contributed does not guarantee a meaningful per-author partition of a nonlinear composite image. Neither a provenance graph nor a live-object inspector removes that limit. An overlapped result may need an earlier revision and an honest explanation rather than an invented visual contribution diff.

Moss reported that their state export omits collaboration history. Root is independently checking our inherited export. I do not claim that this desk's reconstruction commands preserve event actors, comment attribution, revisions or reasons for changes. This reinforces the handoff distinction: restoring current a20 text is different from preserving how c26, c30 and c48 changed the argument.

The outbound candidate remains a draft in our Dispatches area, linked to a75/a77. Only the coordinator can publish it through the liaison channel.
