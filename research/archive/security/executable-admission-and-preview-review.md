# Executable admission and private preview artifacts

*Security investigation · 9 September 2026 · Reviewed Git commit
`5ad7c0af98bfa556a57343b31c5c4486f311c08d` on branch `docs`. Static source
review only: no project code, test hook, model call, credential, or world data was
executed or read.*

## Question and answer

This review asks the pending question from [[scoped-collaboration]]: **can private
component-preview results escape through artifacts that a collaborative workflow
might retain or share?**

The live-world mutation boundary is stronger than the earlier proposal could
assume. Candidate effects are applied to a temporary world, candidate sessions
are bound to the source world and caller, the browser renders validated data
rather than source, and only a fully passing test can cause the runtime to write a
test receipt. Those are implemented controls in the reviewed source.

The artifact boundary is not ready for shared applications. A successful test
stores the complete test cases in `core.component-test` inside the source world's
append-only history. Cases may contain rendered text, returned values, state, or
node properties copied from private inputs. The protected-write rule prevents a
normal verb from forging the receipt; it does not make the receipt private.
Ordinary reads and generic projection can expose it, and world copy, replay, or a
future synchronization path will retain it.

There is a second, related adoption problem. `core.component-admission` and the
active `core.display` record live in the same portable, rollbackable world as the
component. Admission is a list of definition digests. It is not bound to the
recipient, approving principal, authority domain, runtime/validator version, or a
revocation generation. A copied world containing definition, admission, and
display records is therefore locally executable after replay without a distinct
recipient-adoption decision. No distributed import path exists in the reviewed
prototype, so this is a release gate for future sharing rather than a demonstrated
cross-user exploit today.

## What is implemented now

| Boundary | Static evidence | What it establishes | Limit |
| --- | --- | --- | --- |
| Candidate effects | `component_testing.py:19-59`, `component_candidates.py:42-86` | Tests and interactive previews write disposable world copies, not the source world. Candidate tokens are random, caller/world-bound, capped at eight, and expire after five idle minutes. | Each candidate copies the complete source log rather than the component's data closure. Cleanup is process-lifetime best effort. |
| Component inputs and effects | `component_data.py:41-76`, `component_effects.py:9-88` | Generated code receives declared bindings. Durable effects are limited to declared placements, name/text writes, and owned state; the whole batch is checked before commit. | General multi-user authority is still explicitly out of scope. A manifest is locally trusted as part of JEFF/operator authorship. |
| Runtime and rendering | `component_runtime/host.py`, `component_runtime/runner.py`, `component_tree.py`, `shell/components.js` | Fresh bounded QuickJS contexts have no supplied host callbacks; the shell builds allowlisted DOM nodes and does not evaluate source. | The subprocess is not an OS sandbox against a native-engine escape. |
| Test receipt | `component_testing.py:61-79`, `component_commands.py:98-111` | Only the runtime can write a receipt, and first activation checks the exact definition digest and current input fingerprint. | The receipt retains case bodies, and passing stated examples is evidence rather than authority or a safety proof. |
| Activation | `component_commands.py:91-139`, `component_data.py:33-38` | Activation pins an exact component revision; widening bindings or permissions changes the definition digest. | Admission is portable world state and records no local adopter, runtime contract, policy ceiling, expiry, or revocation state. |
| Evidence | `tests/test_components.py`, `research/holistic-review/executable-component-validation-2026-09-05.md` | Committed tests and a prior validation report cover candidate isolation, stale fingerprints, scoped effects, replay, and runtime limits. | This heartbeat did not execute those tests or reproduce the prior trial. They do not test a shared import, fork, rollback, or private-artifact release policy. |

The component runtime currently has no network or external-effect operation. That
removes the most dangerous preview consequence for this slice. Full observations
(`tree`, `effects`, and state) and component-supplied error strings still return
to the caller. When JEFF is the caller, those tool results can enter the configured
model-provider conversation. The deployment documentation already says remote
inference can read supplied context. Nothing currently labels these outputs for a
future development room, bug report, screenshot service, or shared cache.

The full-log copy also creates an availability multiplier: opening or testing a
component performs work proportional to the whole append-only history, even when
the manifest binds only a few objects. Eight interactive candidates and repeated
tests can multiply temporary disk and replay work. The current shell is local and
session-authenticated, so this is mainly a future remote-collaboration hazard and
a local reliability concern.

## Smallest collaboration-safe split

Do not make test evidence carry adoption authority. Use three records with
different movement rules:

1. **Portable evidence** contains the definition and harness-contract digests,
   synthetic-fixture digest, named assertions, pass/fail summary, and provenance.
   It contains no fixture values, rendered output, private error text, credential,
   or grant. Anyone may inspect it; nobody gains execution authority from it.
2. **Local adoption** is a decision by the recipient or a narrowly delegated
   release policy. It binds the adopter's authority domain, exact component and
   dependency closure, interpreter and validator contract, effective bindings and
   effect ceiling, expiry/revocation generation where relevant, and the evidence
   it considered. Keep it outside transferable application data and ordinary
   rollback, or quarantine it as a proposal whenever it crosses a world boundary.
3. **Active display selection** may remain reversible personal world state, but
   replay may activate a component only when the current local adoption record is
   valid. Missing, foreign, expired, or runtime-incompatible adoption falls back
   to the protected default desk and offers inspection.

Private live-data previews should be owner-local observations. They may help the
owner decide, but should not mint portable admission. Shared regression evidence
should use deliberately released synthetic fixtures. If a private fixture is
unavoidable, retain only a restricted local evidence record whose confidentiality
follows all of its inputs.

For the current prototype, the smallest code-facing change before any shared
world transport is to stop storing raw `cases` in `core.component-test`. Store a
canonical case-suite digest and non-sensitive assertion identifiers instead. A
larger protocol change should wait until adoption and authority domains are
designed; disguising them as more fields on a transferable facet would preserve
the underlying mistake.

Candidate construction should eventually materialize a bounded closure: the exact
component revision, declared bound facet revisions, required component state, and
the minimum scene facts needed by the test. Apply byte, replay-work, session, and
per-caller quotas before copying. This reduces both private residue and the
history-size amplification without changing component behavior.

## Proposed acceptance cases

No case below was run in this review.

| Case | Expected outcome |
| --- | --- |
| PA-1 — private assertion | Test a component on a synthetic private marker and use the marker in an expectation. No portable receipt, projection, log line, error, or shared artifact contains the marker. |
| PA-2 — foreign active world | Import or fork a synthetic world containing a passing receipt, admission, and active display from another authority domain. No source executes; the default desk offers inspect/adopt choices. |
| PA-3 — rollback | Adopt and then revoke a component, then restore world data from before revocation. The component remains revoked and cannot render, handle input, or expose actions. |
| PA-4 — runtime drift | Change the interpreter or validator contract while retaining source bytes. Prior evidence remains inspectable but does not silently authorize execution under the new contract. |
| PA-5 — composed permissions | Merge two component branches. The candidate gets a freshly computed binding/effect plan; no admission or grant is inherited by union. |
| PA-6 — bounded candidate | Request a preview from a large synthetic history and a tiny binding set. Work and retained bytes are bounded by the declared closure and quota, not total history size. |
| PA-7 — output routing | Make source reflect a synthetic private marker through a tree, state, value, and thrown error. Only explicitly authorized owner-local sinks receive it; development-room artifacts remain marker-free. |

## Gate and next question

Keep the implemented executable slice labeled local and trusted-authoring only.
Before shared worlds, third-party components, remote candidate APIs, or automatic
update channels, separate portable evidence from local adoption and prove PA-1
through PA-7 with raw clients. Before treating QuickJS as a hostile-code boundary,
put the interpreter in an OS isolation domain or narrow the threat claim.

The next useful question is: **what is the smallest local-adoption record and
runtime compatibility identity that lets safe updates flow automatically while
ensuring a fork, merge, restore, or foreign world can never carry executable
authority with it?**

## Follow-up — 11 September 2026

[[local-adoption-and-executable-identity]] answers that question with a four-part
identity: portable definition, versioned execution contract, locally resolved
installation plan, and non-transferable local adoption policy. The important
refinement is to separate logical capability slots from concrete local entity
bindings. This lets collaborators share one definition while their objects,
permissions, update trust, and active execution decision remain local.
