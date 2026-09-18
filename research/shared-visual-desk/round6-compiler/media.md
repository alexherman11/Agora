# Media R6: independent compiler-bridge checks and extension seam

This is an in-memory research result over the actual experimental Desk and Claude scene compiler. No live session, HTTP server, browser, renderer, native package installation or rich media engine was changed or exercised by these tests. The user subsequently requested closure after the pending owner-integration checks. Those checks and the nested-definition regression are complete; this report retains the earlier checkpoints and adds the final bounded result below.

## First composed checkpoint

Ran with the repository environment, from C:/Projects/Agora4:

    .venv/Scripts/python.exe -B research/shared-visual-desk/round6-compiler/test_bridge_contract.py
    .venv/Scripts/python.exe -B research/shared-visual-desk/round6-compiler/test_component_registry.py

Eight bridge-contract checks and five registry checks passed. Seven of the eight bridge checks compose actual Desk operations, frame capture, candidate activation and typed action handles; the eighth deliberately checks the separate registry boundary and must not be counted as an installed/rendered component.

The composed checks establish:

- Exact code text, quotes, leading/trailing whitespace, newlines, dollar metacharacters and empty replacement reach a real in-memory Desk rewrite unchanged.
- Successful definition activation makes an earlier offered action refuse, even if its material target remains unchanged.
- Two appearances share one subject. Moving the first leaves the second unchanged; rewriting through the second changes their shared material.
- Invalid candidate compilation preserves the last active frame and exact stored draft/selection state.
- A candidate compiled before a later material edit refuses activation. It cannot silently pin an old world into the new active view.
- Restoring historical definition source revalidates and preserves current material and stored draft; it does not replay previous edits.
- Transport handles live outside the content-hashed semantic frame. The original semantic frame validates; modifying its scene content makes integrity validation refuse.

These are not claims of visible draft recovery, selection rebasing or browser focus/IME continuity. The lifecycle retains local state by value. If a new definition removes a selected scene key, retained selection data may no longer resolve; no automatic rebase or visible recovery is implemented here. Frame hashes detect accidental content changes, not hostile authentication forgery.

An early test run used normal PATH Python314 and failed to import jsonschema, while a different execution environment had it. Commands above pin the actual repository interpreter and its native schema dependencies. The missing compiler-file freeze prerequisite initially failed before Foundations produced frame_contract.py; it was not converted into a skipped or vacuous pass.

## Minimal extension hook implemented

component_registry.py is a descriptor registry, not a second scene grammar, renderer or engine loader. A JSON descriptor names immutable id/version plus pinned implementation package/revision/export; material schema; typed action input schemas/effect categories; and inspection schema. It reuses current agora3.schemas validation. It accepts no callable and performs no action effects. Returned descriptors and proposals are defensive copies.

Public methods:

- register(descriptor) returns id/version/digest; a different descriptor cannot overwrite that version.
- inspect(reference) returns descriptor, digest, declared-not-loaded status and executable:false.
- resolve(instance declarations) validates material and identities, refusing missing capabilities explicitly.
- validate_action(reference, name, arguments) preserves exact typed arguments and returns a validated-not-executed proposal.

A second, different schema family for a timed clip is registered after an exact-text descriptor and resolves through the same code. Registry and actual frame_contract.py hashes are identical before and after that test. This proves an open descriptor namespace and typed validation reuse. It does NOT prove new rendering, media playback, package installation, domain semantics or compiler syntax extension. CompilerBridge currently has no component-declaration parameter and does not mount these components. Missing-capability refusal occurs at the separate registry boundary before a proposal is attempted.

The smallest future connection is an explicit component reference in a definition or sidecar, resolved against installed exports and retained in candidate/frame dependencies. A missing export must remain a named diagnostic. The component's renderer and domain operations may be reusable engines; their lifecycle, typed action contract and inspection coverage must be pinned. No new Photoshop, codec or text editor engine is required to prove that bridge seam. Metadata registration alone must never be presented as that proof.

## Updated Claude source: repaired and still open

Read scene.py and lens.js again during the joint work. They are changing concurrently; findings name paths and behavior rather than pretending the round-five hashes still describe current code.

Repairs or additions visible in source:

- Quote/backslash/newline escaping and callback replacement address the prior quote and dollar-replacement corruption paths.
- Gesture requests carry observed item revision and definition provenance rather than prepending a fresh look.
- Unsupported drop is refused by the parser rather than silently admitted.
- Parser checks now address duplicate names, recursive parts, unknown roles/placeholders, quote-aware separators and scene-node budget.
- The painter retains unchanged keyed elements instead of always replacing the whole tree, and reports measured clamp, box overflow and out-of-view facts as viewer observations. Source inspection is not evidence that these measurements/focus preservation worked in our browser.
- scene_for now retains last-good source after a successful compile and rebuilds it when a later definition refuses. Thus the earlier unconditional blank-picture criticism is no longer correct on that cached-success path.

Still visible in the inspected painter: edit uses trim and only sends truthy values, so leading/trailing whitespace and empty deletion remain unsupported by that old route; drag has no pointercancel handler; click binds a div listener without a keyboard semantic-control contract. The typed bridge tests prove an alternative exact-input route, not that the running painter uses it.

A new source concern was sent to root: the successful scene_for path stamps scene.def, whereas its broken/last-good path rebuilds and returns a scene without the same definition provenance. Last-good actions need an explicit active-definition identity or a visible refusal; they should not acquire authority from the currently invalid source or lose their guard. Nested lens chains also need dependency capture. This is a source concern pending adapter tests, not a live observed failure.

## Server packet and client input are different trust boundaries

The next adapter must consume the actual /api/scene shape without treating browser-supplied scene/line/target/revision fields as authority. It should join an authoritative capture to retained node/definition bindings under the same owner lock, or issue handles only for internally retained packet identities. A tampered command line or target must refuse even when an attacker preserves the node key and revision fields. Additional metadata can remain inspectable but cannot select a new operation.

Retitle and tag can be small adapters to existing native verbs with exact typed argument schemas. A new free-form command-template fallback would reopen the ambiguity the prepared-action layer removed. A typed registry declaration can describe an action but does not authorize its execution.

Initial inspected source checkpoint hashes:

| File | SHA256 |
|---|---|
| component_registry.py | 0C09CC916A4AA013D09D6EC26C808864CF620799289E13CCEDA6AA5E93D4EB20 |
| test_component_registry.py | 385A644F32D9FFD4A02B11AA3D68BFABF0D4353FEB68F83FFB948208EEF86943 |
| test_bridge_contract.py | 212EC551A0E9C49D3DDB69B4FF6278019BDC1F82B01F8ABD035FF4F3FA623BDB |
| frame_contract.py | E363D1BE575B01618BC71316C2232C22AF59EC3D29AC9D5034805B8CAE034CA2 |
| activation.py | 858A007D55D07FB0384DC1CD6CD9482A7637C022E8EB04713CCA4BAB520FD07D |
| compiler_bridge.py | A674F3A2C664C70F529BFE0CA64B593FCC82DA8B131303218D799814CD2B60A0 |

These hashes identify that test checkpoint. Subsequent collaborative source updates require their own checks; no live-runtime identity follows from a source hash.

## Actual scene-packet adapter checkpoint

Added test_api_scene_adapter.py against root's ScenePacketBridge. It calls actual scene_for to obtain the current /api/scene packet shape, retains that authoritative capture internally, then offers handles. No HTTP requests or active saved sessions are involved. Ten independent checks pass:

1. Exact literal code and empty text reach the native rewrite operation.
2. Echoed packet changes to command line, material item or revision cannot mint handles.
3. Unknown capture and different actor label refuse. This is attribution/binding enforcement, not authentication.
4. Material changed after capture prevents offering the old capture.
5. A nested definition changed after minting invalidates the outer view's action.
6. A last-good fallback scene remains inspectable but cannot offer actions without a supported provenance contract.
7. External worktree rows refuse before any saved-session enumeration.
8. A never-valid definition cannot borrow the last-good source of another lens.
9. A dynamically chosen nested lens (`lens $title`) receives the same definition-change guard.
10. The original capture is single-use; an echoed packet is optional because the host retains its own.

Command:

    .venv/Scripts/python.exe -B research/shared-visual-desk/round6-compiler/test_api_scene_adapter.py

A real adapter defect was reproduced during review: capture passed a raw Desk copy into scene_for, bypassing the conservative frame adapter's external-session guard. A fake worktree.SESSIONS.glob raised a sentinel before any real filesystem enumeration. The first run reached that sentinel. Root changed capture to use the guarded compilation proxy and retained its last-good cache explicitly; the same test then passed. No real private session or pickle was read by this experiment.

First-invalid compilation still propagates the compiler's exception-shaped refusal in this in-memory API. No HTTP error shape, endpoint installation or transport authentication is claimed. Captures and handles have finite budgets; callers must release abandoned captures/frames. Definitions/material are checked before minting, and offered actions retain scoped target guards plus definition/compiler identity afterward. Raw command strings are inspection data; the client cannot turn them into authority.

The registry remains independent. An implementation package reference is only declared metadata here; no installed implementation hash is verified, and validate_action output is not an invocation grant. Foundations independently reviewed and agreed with that distinction. Team checkpoint a156 records the composed tests and repaired external-row issue.

## Final owner integration and active-definition closure

The final requested local runs passed: nine checks in test_bridge_contract.py and thirteen in test_api_scene_adapter.py. The separate registry suite passed five checks at its recorded checkpoint. Root owns the final combined run and its source identities; these independent counts are not an HTTP or browser integration claim.

The three added owner-handoff checks establish that a handle offered against one Desk refuses when invocation receives a peer-updated current Desk; a successful invocation returns a distinct staged Desk while leaving the input Desk's material, events and reader state unchanged; and a new owner with rules, hooks or follow behavior refuses before staging. The initial synthetic-rule test compared a full snapshot containing an intentionally invalid rule sentinel, so snapshot serialization failed before testing the adapter. The test now compares material/node/event records directly. This corrected a fixture, not production behavior.

The ninth bridge check exercises the public offer path after a nested lens becomes invalid. A previously active Outer/Inner closure is retained, a later material edit remains visible, a new candidate refuses, and an unsaved local draft/selection plus activation revision stay unchanged. The authoritative invalid Inner source is not rolled back. This verifies the repaired distinction between pinned active definition code and current material. Stored selection values still do not prove visible selection recovery, focus or IME continuity.

Commands, from C:/Projects/Agora4:

    .venv/Scripts/python.exe -B research/shared-visual-desk/round6-compiler/test_bridge_contract.py
    .venv/Scripts/python.exe -B research/shared-visual-desk/round6-compiler/test_api_scene_adapter.py
    .venv/Scripts/python.exe -B research/shared-visual-desk/round6-compiler/test_component_registry.py

The host integration remains an in-memory adapter contract: the real server must hold its session lock through rebinding, invocation and persistence of the returned Desk. Tests do not establish crash recovery or atomic disk persistence, and accepted handles can be consumed before an external save succeeds. Retitle/tag actions and component mounting remain unsupported. The component registry remains inspectable declaration/validation only, with no loaded engine or installation evidence.

Work stopped after these requested checks and this report. No live world, Claude source, browser, native runtime or Git index was changed by this reviewer.
