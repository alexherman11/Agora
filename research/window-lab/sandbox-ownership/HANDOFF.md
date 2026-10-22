# Suspended direct-child ownership checkpoint

## House-context source increment, JEFF c9588

This supersedes the earlier "no HOUSE_FILES changes/no landing requested"
checkpoint below. The current increment changes house.py and workshop.py and
adds notation/guard_context.py to HOUSE_FILES. Ordinary landing/house refresh is
authorised by JEFF on this card; no manual restart has been performed.

The live frontier house, only from the main checkout and not fake runtime,
samples SHQueryUserNotificationState, a nonzero foreground HWND+PID and input
desktop once per existing house loop. No titles, content, input, window changes,
OS wake timer or new service/port. It atomically replaces the fixed main
house-state/frontier/guard-context.json. Exceptions publish an unsafe record
or let the previous record expire. A slow house loop therefore refuses admission.

The fake checker reads only that fixed location. State 5, known foreground,
Default input desktop, explicitly clear game/full-screen and a positive issuer
PID are required. Wall-clock AND boot-uptime ages must be 0..5 seconds with
at most 1 second disagreement; stale, future, rebooted, missing, malformed,
oversized or uncertain observations refuse. It rechecks immediately before
child creation and after verified cleanup. Worker-reported state 2 is retained
as diagnostic metadata, never replaced with a fictional safe observation.

Trust boundary: the fixed main house-state path is outside managed builders'
writable roots; no worker-selectable path, environment override, world prop or
CLI publisher is admitted. This is NOT cryptographic attestation or protection
against arbitrary same-user host processes. Reading/copying the record does not
authorise other operations. The ordinary main house publisher is required.
No account/private-store authority is added.

A recent snapshot is bounded admission, NOT continuous screen monitoring.
When the worker sees foreground HWND 0, the fake report explicitly labels
Alex-screen continuity unknown; it must not certify "Alex untouched" from a
blind local Guard. General sandbox/browser admission is unchanged by this
fake-only consumer; no browser/mail acceptance follows.

RAN this round: test_guard_context.py **10 tests in 0.115s, OK**, including real
house loop boundary with a stub runtime, actual observer with fake Win32,
atomic publication failure, freshness/unsafe/read errors and no child effect
on refusal. test_sandbox_birth.py **12 tests in 0.044s, OK**. Diagnostics recipe
**29 tests in 0.093s, OK**, startup fakes and **10** Guard cases passed, final
**OFFLINE ONLY ... no probe invoked**. git diff --check passed.
Exact source hashes are in CHECKS.json.

No live house observation was produced/read or fake child launched this round.
After confirmed landing/house refresh, the bounded fake-only command below is
authorised once by c9588. Refusal must stop it; never wait/retry until a record
becomes safe. Record manifest and cleanup honestly even if runtime closure or
screen continuity remains unknown. Retained browser package and delegated
engine ownership are still separate unresolved gates.

Reversal: ordinary house source revert removes the publisher/consumer together;
preserve all ownership and unknown receipts. A leftover observation expires in
five seconds and must never become a permanent admission token.

## Admitted retry, 21 October, approximately 20:52

JEFF c9582 authorised one fresh fake preflight. Ran
`check_sandbox_birth_guarded.py` exactly once in this resumed round:
notification result 0, state 2, input desktop Default, child_started false,
runtime_closure unknown; refused before desktop/Guard/child creation.
No second launch attempt or cleanup followed.

Per JEFF's request to identify the full-screen context, ran the read-only
`sandbox-ownership/foreground_metadata.py`: foreground HWND 0, PID 0,
image unavailable (`?`), empty class, bounds null, input desktop Default.
No titles/content were read. This context cannot identify the foreground
program; SHQueryUserNotificationState itself does not return the causing window.
It does NOT establish that the home-base HUD, or a game, caused state 2.
An initial inline diagnostic failed at Python parsing before any query; the
saved script then ran successfully. No input, capture, child or browser action.

Source remains preserved and unlanded. Prior offline results below were not
rerun this round; the launcher/ownership source is unchanged. JEFF/host owner
must diagnose this guard context through an admitted read-only lane before a
further run. Browser package delivery and delegated-engine ownership remain
separate unresolved gates. No native mail/browser acceptance is admitted.

Worker-a9388, 21 October 2026. Source preserved in this card's worktree; not
landed or runtime-certified. No browser/mail restart, adoption or cleanup ran.

## Change and scope

The launcher previously ran a child before recording identity, then requested
WMI parent/command-line metadata. A denied query left an unowned running child.

The proposed launcher now:

1. Validates an absolute executable, an unambiguous absolute profile argument
   when supplied, and a hidden sandbox desktop. Queries its own identity.
2. Persists pending launch intent under the existing launch/cleanup lease.
3. Calls ordinary `CreateProcessW` with the explicit executable and
   `CREATE_SUSPENDED`. No new token, privilege, process attributes or service.
4. Captures PID, creation FILETIME and image on the returned process handle;
   parent PID/FILETIME/image are the actual creating process. Records requested
   startup desktop and profile argument (or its absence).
5. Persists complete ownership and resume-pending before `ResumeThread`.
   Unexpected suspend count, failed capture or failed write never retries
   resume. A crash or partial receipt remains unknown and blocks another start.
6. Cleanup checks consistent copies of launch intent/owner, then opens precisely
   the recorded PID, verifies creation/image on the handle it terminates, and
   waits for that handle. PID reuse never authorizes terminating its replacement.
   Access denial remains unknown/refused. No WMI fallback for these new births.

This is a birth identity fence, **not authentication against another same-user
process**. Parent, startup desktop and profile argument are birth facts, not
claims about a running engine's mutable configuration. No profile argument does
not certify a WebView2 profile. The versioned schema explicitly says
`profile_scope="launch argument only"`. Files are not an account/host authority.
Legacy metadata paths retain their existing refusal behavior.

Only directly created children are owned. Delegated/headless engine children
remain unregistered. Empty windows, a gone root or successful direct-child
termination do not establish complete runtime closure. `close` still retains
the manifest/profile, returns unknown, and prevents automatic retry. This patch
does not admit either retained browser or mail runtime.

## Ran

- `test_sandbox_birth.py`: **Ran 12 tests ... OK**. Includes the real launcher
  function with fake Win32 calls: suspended flag and explicit executable,
  persisted pending intent before creation, complete receipt before resume;
  write failure, unexpected resume, identity mismatch, malformed launch,
  inconsistent owner/launch fields, denied handle and PID reuse refusals.
- `browsing/diagnostics/run_offline_tests.py`: **Ran 29 tests ... OK**;
  existing startup fake checks and **10** Guard cases passed; final receipt
  **OFFLINE ONLY ... no probe invoked**. No browser/network/process effect.
- `git diff --check`: passed.
- Exactly one `check_sandbox_birth_guarded.py` invocation. It refused BEFORE
  Guard/desktop/child creation: `notification_result=0`,
  `notification_state=2`, `input_desktop="Default"`,
  `child_started=false`, `runtime_closure="unknown"`.
  State 2 means a full-screen program has the screen, not a proved game.
  No retry, child termination, screen capture/input or browser launch followed.

The real manifest, returned-handle access, resume and cleanup are **unverified**.
No real `alex: untouched` Guard verdict exists for this refused preflight.

## Read-only historical reconciliation

Mail: exact original retained manifest
`C:/Projects/Agora4/.worktrees/a9011/research/window-lab/.tmp-agora/agora-sandbox/mail-fake-acceptance.json`
exists and was read, ownership/receipt fields only. It contains PID **94364**,
`pids=[94364]`, `owners=[]`, launch `created` at **1792627213.4973378**,
`MetadataUnavailable`, return code **1**, stderr **Access denied**;
cleanup is `refused`, reason `ownership incomplete`.
It lacks creation/parent/image/profile/desktop ownership. This does not prove
whether that historical process is alive or absent. No live process query,
termination, rewrite, update or adoption was attempted.

Browser: exact original `.../a8247/research/window-lab/.tmp-agora/agora-sandbox/web8247.json`
is absent. The known `ADMISSION-TAKEOVER.md` and
`browsing/evidence/admission-20261021.json` are also absent at the original
worktree paths, and are not present in this assigned tree's source inventory.
The supported preserved-source transfer is already tracked by a9421.
No private directory scan or unsupported source reconstruction was used.
The landed `browsing/diagnostics/retained-failure.json` contains desktop
`agora-sandbox-web8247`, initialization failure, COMException, HRESULT
**-2147467260**, public_navigation false. It is not an ownership manifest.
Read c8288: the old closer discarded state and a later taskkill of PID 21468
was denied. Those are historical observations, not current process evidence.
**Missing browser ownership package prevents full reconciliation.**

## Next admitted run and reversal

JEFF needs the browser host-owner's exact retained manifest/receipt package and
a later awake, unlocked, no-game/full-screen admission. Do not bypass the refused
preflight or rerun a browser/mail fixture under another name.

The explicit, bounded fake-only recipe (NOT automatic):

```powershell
C:/Projects/Agora4/.venv/Scripts/python.exe research/window-lab/check_sandbox_birth_guarded.py
```

It starts one base Python interpreter on a fresh hidden desktop, sleeps at most
five seconds, and requests ordinary verified-own-child cleanup. It has no UI,
network, account or browser action. It must show complete persisted identity,
verified direct-child ended/gone, and Guard verdict. Whole runtime remains
unknown unless separately established; no empty-desktop shortcut is added.

No changed filename is a `HOUSE_FILES` member (read Workshop's set). Harness
imports are per invocation; no service/HUD restart is needed for a future
approved test. This checkpoint requests no landing or deployment. Source reversal
is to decline/revert this patch through ordinary house review; preserve all
retained receipts and never restore PID/tree-kill cleanup.
