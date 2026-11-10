# Preserved prepare conflict review — offline only

22 October 2026, worker-a9231 / codex-builder-2. This is continuation
review of the existing candidate, not independent acceptance. Earlier
implementation is attributed to codex-builder-1 in OFFLINE-BINDING-a9231.md;
this standing builder also carries earlier design/review context.

## Preservation and exact reconciliation

Read the actual e28822 prepare receipt, including its receiver checkpoint:
base f337dfd5ee59e6dbae8c2bb4fdf95f758de19d30, checkpoint
3ac1a7249568dbaee45f9ecf3f50b763beb230f0, captured main/MERGE_HEAD
09ef2530ec848cbbcf0afc5d0934737095c3cc69.
No second prepare, merge replay, import, patch application or receipt edit.

Ran SHA256 checks: the cumulative patch remains
06e135f4d69a9b4a69952c271864a3342b9dc4fad58f5161c0201a8ced269065.
All eight output hashes and all five declared base hashes in the original
manifest match. The three absent base entries are new files in that manifest.
Original enumeration design fixture remains
4126f827881dc7e96a19885085f51e7c404a063a061b27759754878fa4e19de6.
The manifest raw SHA256 is
29527e4582f808ca059b25a9384bf53f77fb20b27053dcf50a0700bda2bdfae2;
its LF-normalized SHA256 is
338cdd88908c310c96255bd81e3510e7d4709348aad648eeb20167caa69080bf,
exactly the receipt's committed representation. Neither artifact was changed.

Resolved only the ten reported conflict blocks by plain file edits:

* guard_context.py: retain main's threading import and independent Publisher.
  Result is byte-equal to captured main, SHA256
  04c251f01663e768e6de94a46b4dc4a8ffde1d17279d60ecba7221363632568f.
* native_run_verify.py: retain candidate EnumerationIncomplete, Toolhelp
  completion checks, desktop callback/BOOL/error checks and bounded error
  propagation. Surrounding merged main code retained. Result is byte-equal
  to preserved HEAD, SHA256
  428744339fd0972fb1eefac5f87f3615f5487b27332e2d3934a4e4009340a39f.
  Against captured main the entire delta is 47 added/14 removed lines,
  limited to those enumeration/error-reporting hunks.

Observed main at review was a89d3b5a8d5f9db7f31e1a0e6566b41794fa0706.
Read-only diff from captured main to that main has no changes in browsing/,
guard_context.py or native_run_verify.py. This is not a new whole-main merge
or whole-system compatibility certification. Existing staged merge inventory
is preserved. The index still records the two unmerged paths until supported
house staging; file conflict markers are resolved.

## Exact source review

Read HostFence, EngineFence, orchestration, report envelope and child handshake
bytes. Candidate PID is measured against retained handles, ancestry and Job,
not adopted from a receipt. Token/profile/desktop/root/host/Job binding,
report rereads and independent engine fencing remain. RLock serializes sampler
checks; failed closes retain handles and closed fences cannot reopen.
This is correlation against accidental reuse, not same-user authentication.
Disk image hashing is not mapped-image attestation.

Read the complete verifier delta: false/partial enumeration and failed
callbacks refuse even with error zero; successful empty enumeration remains
distinct. Error is captured before cleanup. ERROR_NO_MORE_FILES is completion
only for Toolhelp. Admission policy, must_prove and snapshot limits unchanged.
Main's Publisher cadence and fail-closed publication remain unchanged.

## Ran

Pinned interpreter, only offline test entry points:

| Command suffix | Printed result |
| --- | --- |
| `-m unittest discover -s src/desktop/browsing -p test*.py` | Ran 93 tests in 1.546s; OK |
| `src/text-desk/notation/test_guard_context.py` | Ran 20 tests in 1.916s; OK |
| `src/desktop/test_native_run_verify.py` | Ran 51 tests in 0.303s; OK (skipped=1) |

The skipped shared test is the fixture symlink privilege case; no privilege
change attempted. Guard tests exercise the real Publisher using mocked
publication and stub house/native boundaries, not a live house.
Browser orchestration uses fake native/runtime boundaries.

Six candidate browser Python files: Ruff All checks passed.
Shared verifier Ruff: 151 failures (149 E501, 1 I001, 1 B905).
The captured-main verifier has exactly the same count/distribution, measured
with the same Ruff stdin filename/config; this is not a lint pass or a claim
that every diagnostic is identical. git diff --check exited 0.

## Remaining gates and reversal

REVIEWED_HOST_IMAGES remains empty. No process inventory/query, native
initialization, browser launch, full native health, public request, screenshot,
cleanup of historical runtime, ready or activation occurred this round.
Retained parent identity cannot authorize the descendant interpreter; exact
effective image/birth provenance and separately scoped native permission are
still missing. Snapshot privacy/containment limits remain.

Pause for Rowan's exact-byte review and next scoped decision. The previous
reports, fixture, patch, manifest and receipts remain preserved. Nothing was
activated to reverse. Do not apply/reverse the cumulative patch or reset the
pending merge; future source staging/reversal must preserve main's Publisher
and all unrelated staged main changes.

## Finalized merge readback, 22 October

The earlier unmerged-index statement above is historical. Read current HEAD:
`d7cb13d51e81a18abd8f3904b0482d6c5fbe9618`, with exactly the original parents
`3ac1a7249568dbaee45f9ecf3f50b763beb230f0` and
`09ef2530ec848cbbcf0afc5d0934737095c3cc69`.
Coordinator c12729 reports supported finalization without import replay.
Tracked working tree is clean. The preserved report and new read-only
verification utility are untracked, as is the untouched supplied session copy.

Ran `verify_preserved_a9231.py`: all eight output hashes and five base hashes
match; no mismatches; cumulative patch and guard hashes remain exactly those
listed above. This utility reads files and Git objects only.
Observed main `3319834323223536c6c96e6ae21844512af4d6ed` has no changes since
captured main in browsing/, guard_context.py or native_run_verify.py.
This is scoped compatibility evidence, not whole-main integration.

Reran offline suites on finalized HEAD:
browser 93 tests OK in 1.910s; guard 20 tests OK in 1.241s; verifier 51 tests
OK in 0.351s, one skipped. `git diff --check` exits zero.
Earlier 151 shared-verifier lint failures remain recorded, not waived.
This continuation is not independent review.

The named `browser-reviewed-merge-finalization.json` receipt could not be found
at the assumed house-state/frontier path or by exact filename search in the
main house-state and desktop trees. Commit parents and reviewed source
hashes independently agree with c12729, but the receipt itself has NOT been
verified. Rowan/coordinator must supply its exact supported location or attach
its bounded contents before claiming complete receipt verification.
No new prepare, import, ready or native action was requested.

## Minimal separate host-owner request

Request a bounded read-only identification round, not a launch grant:

1. Resolve the named installed launcher and underlying interpreter using
   nonsecret installation metadata; record canonical executable paths and file
   SHA256s. Do not derive approval from child receipts or basenames. Do not run
   an interpreter to discover itself under this read-only grant.
2. Through the existing retained Job/birth owner only, reconcile the named
   historical fixture's exact root and effective-host identities: creation
   time, measured parent chain, image path, retained-handle liveness and Job
   membership. No global process-content query, adoption, termination or
   fallback replacement. If its retained ownership is unavailable, report
   unknown and stop that reconciliation.
3. JEFF/host owner explicitly reviews the exact allowable interpreter images
   for a later single fixture. Keep REVIEWED_HOST_IMAGES empty until that
   approval is recorded; disk hashes are not mapped-image attestation.

Unknown today: actual effective installed interpreter identity, whether the
historical runtime survives, complete retained ownership, native API behavior
and independent containment. Even an approved inventory does not authorize
browser launch: the single local message fixture requires its own fresh Guard,
retained Job and scoped native permission. It cannot certify public-web
containment. The public page remains gated on independent containment evidence
and its separate explicit permission.

## Receipt and approved metadata readback, 22 October, resumed builder-1

This supersedes only the missing-receipt statement above. Read the exact
coordinator-supplied file:
`C:\Users\Alex\Documents\Codex\2026-10-22\task-3\continuity\browser-reviewed-merge-finalization.json`.
Its SHA256 is
`16de50cce113fb7a6b1cbdce6d2f01e295bf87119260433e8690119b4f6ebcb8`,
matching c12798. Its committed result, two original parents and two reviewed
source hashes match this checkout. The receipt records preservation of all
97 indexed paths; this round independently verified the eight manifest outputs
and five bases, not every one of those 97 paths.

Ran the preserved read-only checker again: eight outputs, five bases,
`mismatches: []`; cumulative patch SHA256 remains
`06e135f4d69a9b4a69952c271864a3342b9dc4fad58f5161c0201a8ced269065`.
Observed main `c60a1423d252e94fdd26a2ea7a2d021b2e948d0a` has no scoped
changes since captured main in browsing/, guard_context.py or
native_run_verify.py. No unmerged paths or tracked worktree edits.
The 93/20/51 suite results above are the preceding finalized-HEAD run, not
fresh executions this round. No full health run or independent certification.
The 151 baseline verifier lint failures remain failures.

Source disposition: supplied finalization evidence now agrees; no new scoped
source mismatch was found. The preserved candidate can be considered by Rowan
for source judging under that evidence boundary. No ready, prepare, import,
judging or deployment was requested.

### Installation candidates: read under JEFF c12788, not admitted

Read `.venv/pyvenv.cfg`: CPython 3.12.10, uv 0.12.7, home
`C:\Users\Alex\AppData\Local\Programs\Python\Python312`.
Configuration SHA256:
`2295244a86d9da306b7d0e9048fecfcf6b554eea08dd643f3ab5ca9041ea3212`.
Resolved paths and read file metadata/hashes only:

| Candidate | Bytes | SHA256 |
| --- | ---: | --- |
| `C:\Projects\Agora4\.venv\Scripts\python.exe` | 274424 | `0b471133e110cfb53a061cad528ce8e517d7b9ac41a0a396c39ad795a487fc14` |
| `C:\Users\Alex\AppData\Local\Programs\Python\Python312\python.exe` | 104952 | `4d6f5f81a4bca11191c4c7c6b43632694d0a4ce74e068619d8fdc161d469859a` |

Both file versions report 3.12.10. These paths and their immediate named
installation directories showed no link/reparse indication in the inspected
metadata. This is disk evidence, not mapped-image attestation or approval.
No interpreter was launched for self-identification. REVIEWED_HOST_IMAGES
remains empty; the runner still refuses before native imports when empty.

### Historical enrolled family: retained receipts, not fresh liveness

Read the existing admit-5405bafb8ee3 fixture's launch, receipt and source JSON;
their hashes remain, respectively:
`8cd2578d73d09d820c2d16c141c0ebbe7b68c01f44ba6ff07d7586184fc92b46`,
`d4a25218d4ff7928693148193f7841eec2ce02632527724b6f97e5538af4cf14`,
`8fbbcc2a92ed3631d777bf9450e519cea69f8ad2548a234a460e84a1b36ae4d8`.
Closed receipt
`admit-5405bafb8ee3.closed-1792687609254233900.json` hashes to
`e448cca261c827ad5c4925e9ed956f64dc8cec74c56b1d433367dd26ebca8a74`.

The receipt binds Job `8cc4ed8e9b2d411689cef169d2daca02`, creator
99168/134371612087798754, suspended root 96436/134371612090425561
and hidden desktop `WinSta0\agora-sandbox-admit-5405bafb8ee3`.
Its measured cleanup goes from three members (29228, 85796, 96436)
to active=0 and pids=[], with closure recorded as proven empty.
External delegation is explicitly unknown, not covered by this closure.

The historical verifier reports effective fixture child
29228/134371612090668135, parent 96436, basename python.exe.
Its full image path/hash is not supplied. Creator metadata naming the base
interpreter does not identify this descendant. The fixture's required engine
report was missing; family brokered/between-samples coverage was not proven.
These historical observations do not establish current global absence.

Read sandbox_job.py: ownership lives in the originating process's `_LIVE`
scope and non-inheritable unnamed Job handle; snapshot validates owner PID.
There is no supported cross-process retained-owner endpoint or receipt-to-handle
adoption path here. Therefore fresh liveness/ancestry/Job reconciliation through
the retained owner is unavailable in this worker. No PID/global query,
handle reopening, adoption, termination or replacement was attempted.

Next owner: Rowan/JEFF to review the exact candidate file identities and decide
the separately scoped retained-host/native admission path. Do not infer a live
allowlist from installation metadata or a global runtime certificate from a
closed enrolled Job. A separately admitted local fixture still does not prove
public-web containment. No browser, network, screen, process or activation
effect occurred in this round; all old receipts and artifacts remain intact.
