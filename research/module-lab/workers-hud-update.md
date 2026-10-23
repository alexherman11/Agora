# Workers now routes inside the HUD

Updated 22 October 2026 after the 22:31 request. **Ran:** the normal fenced
desk API changed only the Workers shortcut routing and the bundle guide.
The saved Workers action is `do view a11301`; its host-window action is absent.
Modules still dispatches `host window composition-workshop`. All seven dock
appearances retain their identities and order. No backend swap, house restart,
native launch or test-window opening was requested during this correction.

**Ran:** fresh live scenes for home-dock, crew-observatory and
composition-workshop compiled without refusal. The action-bearing Workers node
has the HUD action above. The existing world view verb and home-viewer lens
provide navigation and Back. This verifies the installed route and live target,
not a new native visual/click acceptance test. Alex had already confirmed the old
separate-window behavior. The new in-HUD pixels and Back gesture were not exercised.

The first verification assertion selected label nodes rather than their parents;
it failed to find an action for that reason. The corrected read-only check
inspected the action-bearing parent and passed. No mutation was repeated.

## Correction: our installer over-applied the fullscreen guard

The previous report below incorrectly told Alex to leave Windows Search before
a dock-property edit. That was unnecessary. Our task-owned installer had added
`guard_context.read().admitted` before every world mutation. The desk API itself
has no such requirement. We removed that check only from this ordinary-edit
installer. The actual GUI-test/gaming guards and reload script remain unchanged.

**Read:** guard_context.py describes house observations for sandbox admission.
It was introduced for guarded hidden-desktop testing and process ownership,
following the charter's no-visible-test-windows / nothing-while-gaming rules.
The implementation combines a system-wide SHQueryUserNotificationState result
with a separately observed foreground process. State 2 plus searchhost.exe was
refused because Search is not in the explicit nongame list. This does not prove
Search itself was fullscreen. The sampler does not check that window's bounds,
visibility, minimization or DWM cloaking, or attribute the global state to it.

Keep facts separate: global notification status, foreground identity, admitted
effect. An ordinary reversible world-property edit needs no desktop-input gate;
an actual native test still needs the applicable admission and ownership rules.
No guard implementation, allowlist, security setting or user app was changed.

## Separate source/main mismatch and resolution order

**Ran/read:** main is 09ef253; its tree lacks capability_modules.py,
module_examples.py, data_graphics.py and sources/modules.py, crew.py, charts.py.
The running backend has those working-tree modules and live lenses use them.
We activated the world before those dependencies had landed. That was an
integration sequencing error, not a regression introduced by the blocked tasks.

**Read:** landing.py judges a candidate from committed main beside a current
world copy. Its cache key is world name plus commit, not world revision. The
saved baseline for main is at event e29374; later candidate judgments at e29415,
e29475 and e29652 add the three unsupported module/crew lens failures. The
baseline does not contain those failures. Thus the refusal comparison attributes
the newer world's unmet dependencies to otherwise unrelated candidates.

The supported preservation route is already progressing: the handoff document
was applied through house brings at 22:41:44 UTC, with matching raw/committed/
received SHA256. Later waiting is receiver ownership for its next provenance
transfer, not proof of a stuck process. No forced lock removal or parallel
landing is appropriate. The assigned integration worker should finish its
bounded turn, let the queued house transfer run, preserve the exact source slice,
review/test it, and request ordinary judging under its existing authority. Once
that dependency actually lands, the retained dependent candidates can revalidate
against main and be judged. No manual main commit or new permission is needed
for that already commissioned house route. This worker did not run it.

`evidence/integration-source-manifest.json` supplies the exact current source,
regression and fixture paths and raw hashes. The seven required runtime files
include both lexical row-field compiler fixes. charts.py is a related extension;
crew/modules import data_graphics directly. Do not transfer only selector files.
The fixture also needs both dashboard styles, the crew lens and module_preview.
Preserve peer ownership and verify world source pins after any line-ending change.

**Still pending:** actual dependency landing; numeric worker-label fix activation;
new native in-HUD visual acceptance. No operation has an uncertain outcome or
pending approval. The label fix is tested on disk, not claimed live. Last affected
suite remains 139 passed, 5 subtests passed; it was not rerun in this diagnostic.

Evidence: workers-hud-receipts-v3.json and workers-hud-verification.json.
The route can be reversed with a fresh fenced prop edit restoring the previous
window property, but no rollback was executed. Preserve all supporting objects.

---

## Superseded checkpoint (retained as history)

# Workers HUD routing update — 22 October 2026

Alex confirmed that the installed Workers button opened its own native window,
then explicitly requested that Workers open inside the HUD for now (22:31 UTC).
That resolves the previous native-open uncertainty for the old behavior. It
does not verify the new in-HUD behavior, which has not yet been activated.

## Completed source work

- `sources/crew.py`: legacy `builder-1` / `builder-2` now display `Worker 1` /
  `Worker 2`; Codex labels remain `Codex 1`; absent or empty labels show Worker.
- `test_crew.py`: numeric/empty/Codex label cases and manifest routing regression.
- `integration_bundle.py`: Workers uses `opens="@crew@"`, resolved to the created
  crew lens reference before installing dock props. Modules retains its existing
  `window=composition-workshop` behavior. The guide describes the HUD exception.
- No geometry, launcher, host, compiler or painter edits were made. The window
  sizing investigation stopped when the newer instruction superseded it.

**Ran:** combined affected suite: `139 passed, 5 subtests passed in 4.13s`.
**Ran:** Ruff: `All checks passed!`. Tests used the isolated task-owned fixture
directory; no live world or house was touched by tests.

## Live work pending

Existing Workers appearance a11303 still has `window=crew-observatory`.
Target a11301 is the installed crew-observatory lens. The existing world `view`
verb and `home-viewer` already render a lens within the HUD and provide Back.
The prepared normal command is:

```text
do prop a11303 opens=a11301 window=""
```

This preserves the appearance, glyph, order and all other dock items. It selects
home-dock's `do view` action and removes its host-window action. The accompanying
guide edit is prepared. Neither command has executed.

The first preflight incorrectly expected tags in `look :1`; its exact receipt
showed the unchanged target but omitted tags. That check was corrected before
any mutation. The next attempt stopped at the fullscreen guard. The backend
replacement for the label fix also stopped before requesting `/door/swap`.
Latest guard observation: issuer PID 61096, `foreground_exe=searchhost.exe`,
`full_screen=true`, `admitted=false`; Search is not in the current nongame list.
This is Agora's existing foreground guard, not a network or policy-review denial.
No alternate route, guard-list change, permission expansion or repeated swap was
attempted. All HTTP operations have known outcomes; no request is pending.

Resume only on a fresh admitted observation: inspect current receipt/world
before applying the prepared route once, then use the guarded backend swap to
activate the tested label fix. Verify the Workers DOM action is `do view` with no
`data-host`, click it through the live HUD browser equivalent, verify dashboard
content and Back, and record native visual limits separately. The smallest
current unblock is leaving the Windows Search overlay; no new permission is
needed. Native automation remains unavailable (`apps: []`).

Task-owned operation files:
`route_workers_hud.py`, `workers-hud-receipts.json`,
`workers-hud-receipts-v2.json`, `activate_worker_label.py`.
The two receipt files have no successful mutation. The activation script wrote
no activation receipt because it refused before its first API request.

Current source SHA256:

- crew.py: `90D5F6A7C0888CF30396D965F3CE6AF9BF92862C1A1119C2F35879D444C765C8`
- test_crew.py: `E4F8ED2E2444BA566FCCD3CC8E452C55E46A28EDDFEB2C2B1DAD29357A18E1DC`
- integration_bundle.py: `0C2EA7F4EDBB6543524AD3D6B850C5A690924562BAD06105F19BAF5E0A504AFF`

Unchanged launcher/painter SHA256:

- lens_window.py: `5CB7C3485B3342FCF6958A8CFA944C7EAD5E5F53C67A4347CCA52721EC3D9E2C`
- lens.js: `4EFE985033B835F9BD74257DDEF7754E80E1A95AEC612B3FDF2429F7838B0325`
