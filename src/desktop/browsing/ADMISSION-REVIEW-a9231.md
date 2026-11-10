# Browser continuation: received-source admission review

21 October 2026. Reviewer: codex-builder-1 / worker-a9231.
Scope: Rowan c10038, read-only source review. **HOLD: no execution admitted.**

## Received package

RAN git status: tracked tree clean; only the house-provided frontier-try pickle
was untracked and was not opened. READ git history: receiver
8e1f44250a26af51e746548317473b83dadc41b2, projection 9d8fe4a,
source 9b76d87e59f0e1a4dc5abd1975bbc5185a996a9b. READ durable house
receipt a9231-1295bf921de11589e4eb783764adc349de86a7a862844cf64f8efa513a04a362.json.

RAN Get-FileHash SHA256 on each received file; all six match the receipt's
received_worktree_files, received_files and committed_files inventory:

| Path under src/desktop/browsing | SHA256 |
|---|---|
| ADMISSION-TAKEOVER.md | 134598a5bc937e96ff564bcc1371911ed47a2baf57bd64270e2e5d7aa041cc2f |
| admission_probe.py | 95d21a9e6f7bb76a9628f23c6c674f5e74af93651ce2d40c55df629fb02c42f7 |
| admission_result.py | 98b98b88eb79b4687a888ea5aca51a02ff99c874c77d76515df09ab8dd096976 |
| evidence/admission-20261021.json | 7637485c09a9dde0a50a7ded9986f0538d4a69b425031ab50db0bb70c3cff7c7 |
| run_admission.py | dc096a2fe04751cb0ee1df73b43cf33e40610f02c4e9988d0cf09349396b7c6b |
| test_admission_result.py | db1f009f6f6d2693e48e08d9d4204d2cad8d5f62b954556d34a581ae769c728d |

The JSON's original source bytes differ from committed/received bytes (line-ending
normalization recorded by the house); this is not a hash mismatch.
The earlier CONTINUATION-a9231.md checkpoint remains unchanged:
dd88947669eb17e3a1dd6ffddb6a914541add23a602e2c0c5981930a81131268.
Its missing-package blocker is superseded by this receipt; its historical
ownership uncertainty is not erased. Git blobs were not independently rehashed
in this round; their hashes above are the durable house inventory.

## What the source and retained evidence establish

READ all six files. The probe uses native WinForms/WebView2 loaded from installed
assemblies, fresh InPrivate profile, named hidden desktop, no pywebview host
object or bridge. Its explicit 25-second deadline is retained.
Positive-control top/frame native message deliveries precede the disabled-message
phase. The retained report records engine 155.0.4283.62, successful navigation,
disabled delivery [], child exit, parent wait=0, no remaining windows and a
historical name-filtered process count of zero. These are READ historical results,
not tests rerun here or current process observations.

run_admission.py calls start without a job, writes its own launch JSON after
start, and never calls close. It uses a hardcoded game-process-name query plus
input-desktop check, not the later world-owned guard-context admission. Its
OpenProcess wait does not establish family membership. The name-filtered CIM
count and an empty window list cannot certify headless/delegated engine absence.
The retained launch PID 73204 and native receipt PID 40072 differ; the supplied
evidence does not carry complete creation/parent/image identities reconciling
those two records. Do not adopt either PID.

message_boundary_passed deliberately covers only message delivery. Neither that
boolean nor its fixture tests certify network containment, host-object access,
worker requests, redirects/popups/external schemes, permission/download refusal,
job enrollment, complete engine exit, screenshot/input or public navigation.
The existing 403 resource handler needs adversarial coverage before any public
page. No tests were executed this round.

## Retained ownership remains unresolved

READ parent a8247, a9388 evidence and a9868/a9993. The original browser
web8247 ownership manifest was reported absent after failed cleanup; retained
failure.json is initialization evidence, not a complete ownership record.
The separately retained mail manifest was reported owners=[] with metadata
Access denied and refused cleanup. No new inspection of those old runtime
paths or host processes was performed. Their current runtime state remains
unknown. The later takeover's graceful-exit report is a different run and
does not reconcile either legacy runtime.

No-concurrent-executor evidence is insufficient: the parent is paused and this
is the sole authorized continuation, but world scheduling state does not prove
host-process absence. A future host-owner reconciliation must resolve surviving
legacy/delegated execution without manufacturing ownership from a PID/title.
A new empty job cannot close this historical gap.

## Landed dependency and proposed integration (design only)

READ a9868: house landed 638d1cf; source commit eaabe98 is visible on main.
READ main's sandbox_job.py and sandbox_window.py via git show. This receiver
does not contain sandbox_job.py and still has the old start(name, argv, env=None).
RAN git diff --name-only HEAD..main: sandbox_window.py, sandbox_job.py,
sandbox_birth.py, sandbox_owned.py, sandbox_receipts.py and notation/guard_context.py
all differ. Supported house delivery/rebase must supply a coherent dependency
set before implementation; do not reconstruct or copy across worktrees.

The landed API is job_scope(name), start(name, absolute_argv, job=scope),
and close(name) while the same scope remains alive. Proposed consumer:

1. Establish retained-runtime reconciliation and explicit round admission.
2. Read fresh world-owned guard_nongame observation; refuse unknown/unsafe,
   without substituting the old process-name allowlist.
3. Keep one explicit job_scope around the entire Guard/launch/native-test/
   cleanup lifetime; pass it to start. The launcher assigns the suspended birth
   before durable resume. Do not detach the harness holding the job handle.
4. Bind the actual profile/desktop and native WebView2 BrowserProcessId to the
   enrolled run. Explicitly test engine membership/reuse/delegation: a fresh
   profile and root membership alone are not proof that brokered/reused engine
   processes belong to the job. Refuse unknown containment, no breakaway.
5. After graceful disposal, close under the same live scope and Guard, retaining
   all diagnostics. Closure requires empty kernel PID list AND active=0. Scope
   handle-close is a backstop, not an observed durable empty receipt. Persist
   failure/unknown and stop; do not replay cleanup or reopen jobs by manifest.

This is a proposed integration, not implemented or certified native containment.
The landed fake-family proof is useful but explicitly excludes external
delegation and legacy closure; its local Alex-screen continuity was unknown.
House landing attributed existing test_artifact_view, test_followups and
test_host_route_parent failures to main; this review does not relabel health green.

## Next boundary

Rowan reviews this package and routes host-owner reconciliation plus supported
dependency transfer. A later explicit round may implement the consumer and
offline containment fixtures, then seek one admitted hidden native run.
Public HTTP(S) remains gated behind independent containment evidence.
Alex's universal/Agora-native requirements remain verbatim in ADMISSION-TAKEOVER.md.
No alternative browser, UI chrome or permission adapter was implemented.

RAN only repository/status/history/diff/hash reads. An initial inline Python
hash-read command failed at parsing before any file read; native PowerShell
hash reads then succeeded. No transferred probe/test import or execution,
host inventory query, child/browser launch, cleanup, network/account call,
screen input/capture, runtime/source activation, implementation edit or landing.
Only this review document was added; reversal is to remove this authored
document through ordinary review, preserving transferred files and receipts.
