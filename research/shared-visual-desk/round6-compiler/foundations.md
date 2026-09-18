# Foundations R6: one reusable semantic-frame adapter

2026-09-18. Own files: `frame_contract.py`, `test_frame_contract.py`, this report. This is host/runtime bridge work for the shared Claude integration, not a new app, renderer, grammar or authoritative world. Claude owns the compiler, painter and server; the coordinator owns composed integration. STOP from the coordinator ends this work.

## Public contract

```python
compile_frame(desk, definition_id, *, source=None, actor=None) -> frame
check_frame(desk, frame) -> {"ok": bool, "reasons": [str], "diagnostics": [dict]}
dependency_signature(desk) -> {"scope": str, "digest": str, "world_event_count": int}
```

Compilation failures raise `FrameRefusal`, carrying `code` and structured `diagnostics`. The definition ID anchors an existing lens subject. A `source` override compiles a candidate without rewriting that subject; the frame separately records candidate `source_sha256` and the world's `observed_source_sha256`. Consequently an edited candidate can remain valid while its anchor still contains the old authored source.

The caller holds its world-owner lock while capturing/compiling and while checking/activating. This module does not invent a second owner or acquire an unrelated lock. It deep-copies the supplied desk for compilation, leaves the caller's world and seen state unchanged, and compares dependency signatures before/after. That comparison detects observed drift; it is not a substitute for the caller's lock or a general ABA/history proof.

The frame contains:

- The **unmodified actual compiler scene**, including original `acts` command templates. These remain compatible with the existing printer. They are inspection data here, not execution grants.
- A `bindings` sidecar keyed by scene-node key: separate subject and appearance revisions, parent identity/revision/layout, material item, definition chain and source provenance.
- Definition revision and source hashes; exact actual scene-compiler bytes and style-file hashes; a conservative world dependency signature.
- An inspection payload from **the actual `scene.to_text`**, with declared row sources, node count and explicit limitations. This is logical scene inspection, not a measured viewport report.
- A content-derived `frame_id` to detect accidental changes to a retained frame. It is not a signature or client authority; callers must retain/trust their own frame data.

The actual compiler source is loaded from exact host-file bytes for each compile, avoiding stale `sys.modules` code while Claude edits the compiler concurrently. Loading this trusted host implementation uses Python's normal compilation/execution machinery in an isolated module namespace; authored lens text is still parsed only by Claude's parser. No authored Python, JavaScript or CSS is executed by this adapter. Source/style hashes are checked again after compilation. Other loaded Desk implementation dependencies remain the host's pinning responsibility.

## Explicitly conservative dependencies versus scoped action bindings

The candidate dependency signature covers the Desk snapshot, event journal, actor label, per-actor reader state, handles/aliases and last-created identifiers. It includes unselected material because selection membership can change. An unrelated subject edit therefore invalidates a retained candidate for activation. This is deliberately broader than the correct admission policy for a previously offered content action.

Root's typed action bridge must use the material/definition dependencies appropriate to that action: moving one occurrence should not by itself expire an unchanged subject-text action; a new unrelated subject should not expire it either. `check_frame` must not become a whole-world action gate merely because it is convenient to call. This distinction was agreed with root and Editing before integration.

`bindings[key]` currently has this shape:

```text
appearance: {id, revision} | null
subject: {id, revision} | null
parent: {id, revision, layout} | null
material_item: compiler item | null
definition_chain: [{id, revision, source_sha256}, ...]  # outer to inner
provenance: {definition, part, source_lines, precision}
identity: {key, scope, continuity}
```

Definitions composed through the compiler's new `lens` form need **all contributing definition revisions**, not just the outer lens revision. A nested definition can change what an old gesture means while its outer lens and target subject are unchanged. The adapter now records an outer-to-inner chain and a frame definition manifest. Root was notified that the action bridge must retain/check that chain or explicitly refuse those actions until integrated.

## Which fields are observed, resolved or inferred

This distinction is essential for Claude's requested integration rather than a parallel platform:

| Field | Current origin | Limitation / requested upstream field |
|---|---|---|
| Scene nodes, keys, text, boxes, actions, cuts | Actual Claude compiler output | Preserved, not reimplemented |
| Subject/appearance/parent revisions | Resolution against the same captured Desk snapshot | Request these as explicit compiler/server bindings so the consumer need not reconstruct them |
| Outer definition | Supplied authoritative lens ID + captured subject | Actual `/api/scene` already adds `scene.def`; API integration should prefer and validate that declaration |
| Nested definition chain | Actual `node.lens`, compiler-generated nested-root key and actual `find_lens` lookup | This is adapter inference; request explicit per-node definition identity/revision/chain from Claude |
| Source lines | Actual parser's part names/line numbers, within the resolved definition | Multiple matching names produce candidate lines; this is deliberately not claimed as exact node provenance |
| Read dependencies | Conservative snapshot digest | Not an exact compiler read trace or minimal invalidation set |
| Visible pixels, local drafts, focus, scroll | Not produced here | Retain server `views`/observed reports separately; do not fabricate measurements from logical layout |

The candidate compiler intentionally calls `build`, not the caching `scene_for` wrapper. A candidate should fail instead of silently returning last-good source. It therefore does not claim to reproduce the entire `/api/scene` packet's fallback or measured-view behavior. Root's `api_scene_adapter.py` is the separate integration boundary for a trusted server packet matching the owned snapshot; it should keep `scene.def`, observed metadata and view reports intact. None of this authorizes treating a caller-supplied scene as an action capability.

## External row sources and bounds

Current `scene.rows` can read saved worktree session files. Those are outside the in-memory dependency snapshot. This adapter **explicitly refuses worktrees rows**, including a dynamically interpolated source and a worktrees source reached through a nested lens. The static check reuses the actual parsed definition; a narrow delegated Desk wrapper refuses `_session` access used by the current compiler before it enumerates those files. This is a boundary against the inspected compiler path, not a security sandbox against arbitrary future host code.

Other row sources remain actual compiler behavior. The frame warns that `events` currently provides the last 20 journal entries; its row count is not a full journal count. Dynamic selections are identified as conservatively covered rather than pretending to have an exact read trace. Positional row/tag keys may rebind; appearance-bound node continuity is a stronger guarantee than positional continuity.

Limits: candidate source 64 KiB, encoded dependency/frame data 8 MiB, metadata depth 64 and at most 1,500 admitted frame nodes. The actual compiler also has a 1,500-node expansion budget. The adapter's post-build limit counts generated cut/absence nodes too. These do not establish a hard CPU-time sandbox for the compiler's parser or its recursive reference analysis. The fixed code is trusted host machinery; untrusted plugin execution and production resource isolation remain outside this component.

## Actual checks

Executed:

```powershell
python -B research/shared-visual-desk/round6-compiler/test_frame_contract.py
```

**15 tests passed.** The test runner verified the compiler/style files stayed identical before and after the final suite:

```text
scene.py                         acd8a5ba686f7fe532816d074a0d3d7c904546ff6295956ac686cf31acec4d21
desk-shell/style/calm.style      f09f4ef58b165a6df14c794bb53b7cd9cc1dd41d0efdc1631640d118267e397d
```

The compiler changed several times during this collaborative round. Earlier successful suites used `7aa777d4...` and `6ee4dd9d...`; the full hash above identifies the final recorded run, not a claim that source has stopped changing. Each returned frame also carries its own exact hash.

Coverage: actual scene/printer reuse without caller mutation; two appearances with a shared subject; candidate source override; conservative invalidation from unrelated material; definition revision and unbumped text drift; mocked compiler/style generation mismatch without changing source files; structured invalid-lens refusal; static/dynamic external row refusal; event-tail disclosure; reader-state dependency; retained-frame mutation detection; current duplicate/cycle refusal; nested definition origin/chain; nested external-source refusal. All fixtures are fresh and in memory. No saved sessions, browser, HTTP endpoint, native runtime installation or live-world action was used for these tests.

## Collaboration and remaining work

Editing consumes this API for candidate activation/restoration and keeps view/draft state separate. I reviewed `activation.py`: defensive copies, dependency recheck, monotonic activation revisions and definition-only restoration match the agreed boundary. I raised the retention question: per-frame bounds do not bound an unlimited number of candidates/history entries; explicit discard and a maximum outstanding count are preferable to silent eviction if this becomes a running owner.

Media independently pressures action/lifecycle composition. I reviewed its descriptor registry and support the explicit `declared-not-loaded` and `executable: false` results. Schema validity and package identity are not installed-engine evidence or invocation authority. This adapter deliberately does not invent a component loader to make that missing layer disappear.

Root composes this frame with the existing two-operation prepared-action experiment and an activation generation. Keeping typed actions in a sidecar preserves original scene/text compatibility, repairing round five's concrete incompatible-packet problem. That composed behavior belongs to root's integration tests; this report does not claim it from the 15 frame checks.

Own team desk note **a154/s153** records the component and the important inferred fields. Root remains the liaison with Claude's `bridge` surface. The contribution is a reusable candidate-frame contract over their compiler, with clear seams for upstream metadata and authoritative invocation. It is not a competing compiler, a finished interface platform or a final desktop.

## Bounded completion review, 2026-09-18

The actual compiler acquired `build(..., props=None)` during this round. The adapter now forwards the root definition's captured props into that existing parameter. The fifteenth test verifies that authored `spread x 20 step $spacing to 440` with `spacing=75` produces x coordinates 20 and 95, changes no caller world state, and becomes stale after the prop changes. This is reuse of Claude's named layout primitive, not a new formula operator or second layout engine. The inspected actual nested-lens build call still omits the inner definition's props; nested prop forwarding is an upstream limitation, not silently supplied by this adapter.

I independently reviewed and reran Editing's repaired activation module: **14 lifecycle checks passed**. It now retains complete transitive definition records reached during candidate compilation, verifies source hashes/revisions, and overlays them only onto a disposable copy of current material when compiling an active view. This preserves a working nested interface after its proposed world source is edited into an invalid state. Root definition props work through that same retained-record input. No authoritative world record is overwritten by this overlay.

That compilation input is explicitly synthetic: its dependency digest describes current material plus pinned active definitions, not an assertion that the authoritative world currently contains those definition editions. If a lens subject itself appears as material in the view, the overlay also shows its pinned record there; a proposed-source editor must expose the current world record separately. Active-definition generation and scoped material-target revision are different guards. Comparing a pinned inner definition revision with its deliberately newer proposed source would incorrectly disable newly offered active actions.

The closure is the set of definitions actually reached when compiling the candidate, not a statically complete import manifest. A later material change can make a dynamic nested name select an additional definition; consumers must refuse a newly reached unpinned definition if they promise frozen active meaning, or disclose that resolution policy. I sent this precise boundary to root for the final integration decision. Historical `restore` still recompiles the historical root source against current nested definitions; it does not restore an entire historical dependency closure. Candidate/history retention remains unbounded, and no production persistence, authentication, compiler process isolation or arbitrary component engine is established by these checks.

The requested three-arrangement comparison was assessed against the unchanged round-three evaluator but not implemented before the user's stop direction. Static inspection found no floor/modulo, trigonometry, sorting, reduction or timestamp parser. A bounded piecewise wrapping grid, numeric-time compressed timeline and status/progress/urgency lanes were proposed; those are **unexecuted proposals**, not evidence of new authoring capability. Named grid/timeline/lane primitives remain credible alternatives. No arrangement fixture files or new operators were added.
