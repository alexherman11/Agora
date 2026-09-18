# Round six: joint compiler bridge checkpoint

2026-09-18. Paused at Alex's request because Claude was approaching its usage limit. The three Astra researchers have stopped. No automatic continuation or waiting for a compaction signal is installed.

## What changed

Both teams worked in Claude's new `bridge` world through the normal desk interface. Lenses=f02, Things=f03, Defects=f04, Talk=f05. Claude owns `notation/scene.py`, `deskd.py`, `worktree.py` and the generic painter. Astra owns this directory. No competing desktop or app renderer was built.

The shared direction is: retain editable definitions; compile a typed, inspectable scene with definition/material provenance; preserve the active definition set while proposals change; offer exact actions against what was observed; dispatch through the existing native world operations.

Implemented here, against Claude's actual compiler and Desk:

- [Frame contract](frame_contract.py): unmodified actual scene plus provenance/binding sidecars, transitive definition identities, source/compiler/style hashes, declared inspection limits and conservative candidate dependency checks. It uses the actual parser and text printer. It refuses external saved-session row reads instead of claiming they are captured world dependencies.
- [Definition lifecycle](activation.py): propose, preview, activate and restore with a monotonically increasing activation revision. It retains the complete definition records reached by the candidate. Current material compiles through those pinned records in a disposable compiler snapshot. Invalid inner drafts cannot silently replace the active view. Draft/selection records stay separate. A newly reached dynamic definition outside that retained set refuses until explicit preview/activation.
- [Composed bridge](compiler_bridge.py): integrates the lifecycle, frame and round-five exact native action adapter under one owner lock. Active definition meaning is guarded by activation generation; target material/appearance revisions remain scoped. The original scene remains printable, with admitted typed actions in a separate sidecar.
- [Scene packet adapter](api_scene_adapter.py): consumes the actual `scene_for` packet shape used by `/api/scene`. It retains server captures, refuses modified echoed packets, and binds offered actions to definition chains and scoped native targets. It never grants authority from a browser-supplied command or scene.
- [Component declarations](component_registry.py): immutable versioned descriptors, schema checks and explicit missing-capability refusal. This is metadata extensibility only: no engine is loaded, installed or rendered.

## Concrete collaboration

Studio a675 established the round; Claude a677 introduced the shared world. Bridge a20 records ownership and offered-action reasoning. Claude a30 requested the actual scene-packet adapter and retained ownership of the compiler/server/painter. Our comments c31/c42 identify fields currently resolved through explicit server-side joins: subject/appearance/parent revisions, typed operation/input schema and nested-definition provenance. [API field review](api-field-review.md) records the observed packet and disposable reproductions.

Things a24 and proposed lens a26 supplied the authored arithmetic challenge. Claude answered with `spread`, configurable through lens properties, and explicitly conceded it does not pass the test of authoring a new relationship with the host frozen (a44). We agreed three proposed nonlinear arrangements are an experiment, not evidence of universal demand. They were not executed before this stop. No evaluator was changed.

Independent review caught our own integration bug: pinning only the outer source still let an invalid inner edit break the next projection. The repair pins the transitive definition records. A further final check refuses dynamically reached definitions not in that pinned set. The packet adapter initially allowed saved-session worktree reads; a sentinel test reproduced the escape before any real file access, and the guarded compilation proxy repaired it.

## Verification

Final coordinator run: **58 unittest checks pass**, using disposable worlds and actual current compiler code. Coverage includes 14 lifecycle checks, 15 frame checks, 13 packet/owner integration checks, 5 component descriptor checks, 9 composed bridge checks and 2 final closure regressions. The registry missing-capability check is explicitly separate from actual renderer integration.

```powershell
.venv/Scripts/python.exe -B -m unittest discover -s research/shared-visual-desk/round6-compiler -p 'test_*.py' -q
```

The coordinator-owned `compiler_bridge.py` and `api_scene_adapter.py` pass Ruff. No browser behavior, installed native Agora capability, HTTP handle endpoint, VM execution, whole-runtime test suite or performance result is claimed. Live GETs inspected Claude's actual board packet; native desk operations posted collaboration notes and clearly labeled proposals. We did not modify Claude's compiler, server or painter files.

Compiler source during the final successful suite: `acd8a5ba686f7fe532816d074a0d3d7c904546ff6295956ac686cf31acec4d21`; style source: `f09f4ef58b165a6df14c794bb53b7cd9cc1dd41d0efdc1631640d118267e397d`. Claude's source continued evolving during the round; these identify the tested checkpoint, not a promise about a later running server. Individual reports preserve earlier checkpoints and failures.

## Host integration handoff

The handle store must survive between requests; the authoritative Desk must be supplied freshly under the existing session lock on every request. `ScenePacketBridge.offer_from_owner(desk, actor, lens_name)` captures and offers against that owner. `invoke_on_owner(desk, actor, handle, inputs)` returns `(new_desk, receipt)` for the host's existing save path. The caller must hold its session lock across rebind, invocation and saving. This keeps the handle store from becoming another world owner. Tests verify that a peer-updated current Desk refuses an old action and a successful action returns a new Desk without mutating the supplied input.

This seam is **not installed in deskd or the browser**. ScenePacketBridge and CompilerBridge are two tested adapters: the former matches the current server's packet/caching model; the latter tests candidate activation. Their complete live integration remains the next step, owned jointly with Claude. No raw command fallback should be added merely to make unsupported controls work.

Remaining limits:

- Only whole-subject rewrite and free appearance movement have admitted typed execution adapters. Retitle/tag/section edits remain explicitly unsupported in this path.
- Active definition records are pinned compiler inputs. If a definition is itself displayed as material, that projection shows its pinned edition; proposed source needs a separate editor view. Conservative candidate checks can refuse after unrelated world edits. Restore recompiles historical root source with the then-current nested closure, rather than pretending to restore an entire historic runtime.
- Captures/actions have finite budgets and explicit release/cancel operations. Candidate/history retention is not bounded. Authentication, durable activation/handle persistence, crash/disk-failure semantics and external-effect rollback are absent. The staging adapter refuses desks with rules, hooks or clock-following.
- Nested definition identities are partly inferred from the current compiler's composition keys and names. The host should emit explicit origin/import metadata. Fallback packet actions remain refused until effective definition provenance is trustworthy.
- New component declarations do not supply executable engine installation, mounting, text inspection or selection semantics. Metadata registration alone is not the invention test.
- Root lens properties reach the compiler. The compiler's nested build currently omits forwarding inner lens properties; reported as a remaining host gap.

Resume with the actual `/api/scene` field contract and one live handle round trip. Then connect candidate activation to a world operation (Claude proposed worktree preview/merge), preserving the pinned closure and drafts. Only after that should the unexecuted arrangement cases or component-engine invention trial begin.

Final incoming notes retained at the stop: bridge a51/a53 are Lark's individual
argument for a fully printable binding (target, subject/appearance, definition,
operation and input schema), not an opaque invocation reference alone. Root agreed:
existing `inspect(handle)` and the typed sidecar already expose those fields, and
the next printer should show them directly. A handle is not authentication. These
notes are design input for resumption, not an additional implemented guarantee.
Bridge a55 records the final stop and handoff.
