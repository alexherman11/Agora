# Candidate and active definitions around the actual compiler

Editing, Astra team, round six, 2026-09-18.

**Implemented in a disposable in-memory adapter:** candidate preview and activation are separate; a refused candidate leaves the previous active source/frame and exact per-view local data intact. Successful activation and restoration advance a monotonic revision. Restoration recompiles historical source against current world state, rather than replaying old material or actions. Fourteen focused tests pass using Foundations' frame contract and Claude's actual current scene compiler.

## Scope and API

Owned files are `activation.py`, `test_activation.py`, and this report. No Claude compiler, painter, style or app file was edited. This is a lifecycle experiment, not a new world owner, installed package lifecycle, persistent desk operation or rendered desktop.

```python
lifecycle = DefinitionLifecycle(desk, definition_id)
candidate = lifecycle.propose(source, expected_active_revision=0)
result = lifecycle.activate(candidate["candidate_id"], expected_active_revision=0)
lifecycle.set_view_state("editor/alex", {"draft": exact_text, "selection": selection})
result = lifecycle.restore(historical_revision=1, expected_active_revision=2)
```

`definition_id` is an existing subject tagged lens. The source supplied to propose is an override compiled against that subject's observed revision; it does not rewrite the native lens note. `activation_revision`, `active_source`, `active_frame` and `view_states` are exposed; frame and view reads are defensive copies. `snapshot()` returns the active state and retained historical revision IDs. Candidate preview values are also copies, so editing a returned preview cannot alter what will activate.

The caller owns the Desk and must hold its owner lock around operations. `set_desk(desk)` lets root's bridge rebind the same lifecycle after its existing typed-action owner atomically swaps a Desk. The lifecycle does not copy or write another authoritative world. Candidate and active records are private in-process data and add no native world events. There is no persistence or restart recovery in this class. Foundations' source review identified a further bound: pending valid candidates and historical sources accumulate without a session retention budget or explicit discard operation. Per-frame bounds do not bound retained session memory. That limitation is left explicit while root integrates the stable API; this is not a production lifecycle service.

Optional compiler/checker callbacks allow a future composing adapter to add explicit dependency contracts. The defaults are Foundations' `compile_frame` and `check_frame`. Callbacks are trusted read-only Python, not authored code in a sandbox. We do not promise rollback if an injected callback produces external effects. Media's component metadata registry is separate in this slice; no component engine activation is claimed here.

## Exact lifecycle behavior

1. Propose checks the expected active revision, calls the actual compiler through frame_contract, then validates the resulting frame again. A valid candidate retains source, source hash, base activation revision and compiled frame. Refusal returns diagnostics and preserves active/local state.
2. Activate checks caller revision, candidate existence, candidate base revision and current frame dependencies. Only then does it replace the active definition and advance the activation revision. Successful candidates are consumed. It does not refresh a stale candidate silently.
3. Restore finds historical source, recompiles it against the current Desk/compiler and activates the new candidate. A to B to A therefore produces revisions 1, 2, 3. A request from revision 1 does not become valid because the source text looks like A again. Failed recompilation leaves B active.
4. Per-view draft, selection and composition data live in a separate map and are never changed by propose/activate/restore. The caller explicitly updates them through `set_view_state`.

The frame checker pins the anchor definition revision/source, compiler/style hashes and a deliberately conservative world snapshot. Unrelated world changes can invalidate a candidate; this is stricter than a fine-grained action dependency policy. Root's separate action-envelope integration decides which individual offered actions can survive unrelated changes.

An active frame is the snapshot that was activated. It is not automatically a fresh material observation after later world edits. `compile_active(actor=None)` now builds a fresh frame from CURRENT material through the entire PINNED active definition closure. Candidate capture retains each actual definition record named by the compiled frame, including source, title, tags, properties and revision; it checks that record against the frame identity. The root record uses the candidate source override. `active_definition_records` exposes defensive copies.

Compilation substitutes these records only in a disposable copy of the owned Desk, then calls the same actual compiler wrapper. No authoritative subject or event is overwritten. The returned frame's dependency digest describes that explicit compilation snapshot; it must not be mislabeled as an unmodified current-world digest. Root attaches active-projection context outside the hashed semantic frame. Definitions shown as material in this projection display their pinned record, so candidate-source editing requires a separately labeled view. Other material text and appearance state remain current.

This repair followed an independently reproduced integration failure: an admitted ordinary edit to nested lens source could break the next CompilerBridge offer without any activation-revision change. Merely retaining the root source was insufficient. The revised tests show that invalid inner authoring leaves the active projection usable with fresh material; valid inner text/handler changes remain unapplied until deliberate new activation. Historical restore still recompiles historical ROOT source against the CURRENT dependency closure, validating it before a new activation. It does not silently restore old native definition documents.

Action guards may conservatively refuse an action from the pinned display if its definition's current authored record has changed. Display continuity and permission to execute are distinct; the repair does not silently renew an action against a new definition.

## What preservation does and does not establish

Tests preserve exact strings including whitespace, quotes, newlines and dollar syntax, plus selection offsets and a composition marker. This is storage continuity. A new definition may remove the selected node or make a draft's target inaccessible; the adapter does not rebase selection, repair semantic targets, prove browser focus, retain actual IME machinery or decide a migration policy. Keeping the data is necessary but not sufficient for usable interaction continuity.

No browser or installed-renderer behavior is inferred from the Python tests. In particular, the lifecycle does not patch Claude's current painter into a preview/activate flow. Native-world durable activation, a recovery route outside a broken renderer, capability installation and renderer/package pinning remain integration questions. The mechanism is intentionally smaller than those contracts.

## Executed checks

```powershell
python -B research/shared-visual-desk/round6-compiler/test_activation.py
```

Fourteen tests pass:

- Invalid first candidate retains no-active state and exact local work.
- Syntax error, missing role and recursive candidate each preserve the last-good definition and local state.
- Successful A then B activation changes no material or world events and leaves local work intact.
- Mutating public preview/frame/local-state copies cannot forge retained values.
- Intervening material change invalidates a candidate without restoring or overwriting that change.
- Editing the native anchor lens invalidates a candidate.
- Restore recompiles historical A against fresh material, advances revision, and refuses both stale-caller and stale-candidate ABA routes.
- Controlled unavailable-compiler refusal during restore leaves the current active state intact.
- Controlled compiler/style-check refusal leaves active and local state intact.
- Rebinding the owner's Desk observes the new world and refuses a candidate from the old state.
- Invalid revision types, unknown history and consumed candidates refuse.
- A broken nested definition leaves active compilation usable, with fresh material and exact local work preserved.
- A valid nested definition's changed text and handler are adopted only after deliberate new activation.
- Copies of pinned definition records cannot alter retained source or properties.

The unavailable compiler/checker tests are explicitly controlled injected refusals, not deletion or replacement of live host files. Invalid grammar, missing role, recursion, material edits, anchor edits, actual compilation and restoration are exercised against the real current compiler and normal ephemeral Desk operations.

Five host files are hashed before and after every bounded test-suite execution, with an assertion that they match within the run. Claude is concurrently developing them, so successive test runs can legitimately have different hashes. Latest passing run observed:

| Source relative to notation | SHA256 |
|---|---|
| scene.py | 7de3d1f04396723b69961ba73ab761ea49184a4845eb2045a842913c71680be1 |
| desk-shell/lens.js | 9f78be923de8af2c7b1a547328dab1464881d44155d341c7092bdab7ca10d1ff |
| desk-shell/lens.html | 455b6fc2194bfdde4c8e0432308eddcfa0773b2e018f0ea53e7e6a7d060d9f57 |
| desk-shell/style/style.js | b5f68d26b37d423d4fab60bb528591e6e23a071c3b725ecee7ef08b84c83e482 |
| desk-shell/style/calm.style | 1e5695ed6f579b1ee93de91e9b3c88b8948f672362812ed6a93a5f886681f4dd |

## Shared research and remaining question

The API was agreed with root, Foundations and Media before implementation. Foundations supplies the actual compiler wrapper, source loading, conservative dependency pin and frame inspection; this file duplicates none of its parser or scene schema. Media is independently attacking boundary behavior. Root composes this lifecycle with existing typed action dispatch, retaining one owner lock.

Under the explicitly authorized joint bridge session, astra-editing read Defects and posted a22/s21: candidate refusal must retain active definition and local work. That note asks which ordinary desk operation should activate a validated definition, with recovery still available when the renderer is broken. It is a proposal and executable evidence, not a silently installed durable authority. The user subsequently instructed the team to finish the current closure repair and tests, then stop without waiting for another signal. That bounded repair is complete; no further feature work is planned.


### Final closure repair verification

The final bounded run passed all 14 lifecycle tests, including old-versus-new nested handler retention. Root owns the final composed-bridge verification. Host files again matched before and after this run; Claude's concurrent updates mean the earlier source table remains a historical test observation rather than a claim of the final server generation. No lifecycle or bridge changes were installed into Claude's runtime by this agent.
