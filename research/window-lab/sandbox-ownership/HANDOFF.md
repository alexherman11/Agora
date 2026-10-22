# Suspended direct-child ownership checkpoint

## Current: landed and one real direct-child run completed, 21 October 21:39

READ house c9796 and local history: policy landed6b9aaea, source checkpoint
2f9a162. Tracked tree clean before the attempt. JEFF c9804 authorised ONE run.
RAN check_sandbox_birth_guarded.py exactly once, exit0. No retry.

House schema-v2 preflight and postflight both admitted the world-listed
chatgpt.exe foreground on Default under the explicit non-game rule.
Raw notification_state=2/full_screen=true/game=null stayed in the receipt.
Issuer PID31124; observed_at1792643967.8946886; uptime_ms275348687.

Manifest complete: child PID92092, native creation FILETIME134371175695230930;
parent PID93600, creation134371175692197682; both images the base Python312
python.exe. Requested desktop WinSta0\agora-sandbox-birth-a9388-85fb297c11;
profile the unique birth-a9388-85fb297c11-fake-profile scratch path.
The owner/launch-intent copies match, method CreateProcessW-suspended-v1,
resume_result=1. READ persist_then_resume: complete ownership is written
before ResumeThread; the offline sequencing tests cover that ordering.

Verified direct-child cleanup: status ended, wait0, same PID/creation,
scope "recorded direct child only". The command succeeded because this
narrow claim passed. Its close receipt still says ok=false / cleanup
incomplete, cleanup_complete=false, remaining_pids=null and runtime_closure
"unknown: no reconciled child ownership boundary". Those are intentional
whole-runtime limits, not proof of a surviving child or a closed runtime.
Retained scratch manifest/profile were not deleted or reset.

Guard code0, but the worker could not see Alex's foreground. The report says
"unknown Alex-screen continuity"; do not call it an untouched-screen proof.
No browser, page/network, account, input, capture or native mail run.
This direct-child success does NOT admit native browser/mail or delegated
engine cleanup. JEFF/host owner still owns that separate boundary and the
missing retained browser package. Previously read mail owners=[]/denied
metadata remains unknown. The two known browser package paths were again
absent in this assigned checkout; no process-absence inference.

Exact original report and manifest copied together into LIVE-20261021.json
(SHA2566b98f8d2292e9733a9d4e9bc835f19f2cc8dd638b584af9942f74b8ad8fa90a2),
including original-byte hashes. CHECKS.json links the evidence and preserves
all earlier failures. No source or test changes in this round; offline
counts below are from the preceding source round, not freshly rerun.
Historical "staged/unverified" checkpoints below are superseded only for
this direct-child proof, not retained/delegated runtime closure.

## World-owned non-game policy, JEFF c9725 — staged, not live

The house now passes its current `guard_nongame` setting into each observation.
There is no executable allowlist in code and no worker-configurable input.
Exact comma-separated basenames are normalized case-insensitively; malformed
policy grants no exception. The observation includes that policy snapshot.
Schema v2 rejects observations from the previous publisher.

State 5 still requires a known executable/foreground, Default desktop and
explicit clear facts. State 2 (full-screen application) can instead pass
JEFF's explicit non-game rule when the foreground basename is listed.
The raw full_screen=true and game=null facts remain unchanged in its receipt;
admitted=true is a policy conclusion, not a measured absence of games.
Game state 3, presentation state 7, unknown states, failed image query,
foreground changes, stale/future/clock-inconsistent observations and locked
or other desktops still refuse. No auto-retry or polling for admission.

The `pythonw.exe` entry means this HUD only: a hidden, read-only CIM query
targets just the foreground PID (three-second timeout), binding its creation
time and image to native identity before/after the query, then reuses the
existing HUD script/world/door matcher. No process inventory, title/content
publication, HUD restart or PID-only record trust. Failure refuses the
exception. Observation age starts before this query; notification state,
foreground PID/window and input desktop are checked again afterward.

RAN offline: test_guard_context.py, 16 tests in 0.148s, OK, including
world setting propagation through the real house-loop seam, actual observer
with fake Win32, policy removal, exact names, HUD scope/birth/denial,
mid-query game/lock changes and freshness refusals.
test_sandbox_birth.py: 12 tests in 0.044s, OK.
Diagnostics recipe: 29 tests in 0.130s OK, startup fakes and 10 Guard cases
passed; OFFLINE ONLY, no probe invoked.
Exact source hashes are stored under world_nongame_increment in CHECKS.json.

This stages house.py/guard_context.py, so ordinary landing/house refresh is
required and authorised. No live attempt has run under this policy. After a
confirmed landing, JEFF permits ONE bounded fake-only attempt, stopping on
any refusal. Browser/mail, legacy and delegated-child gates remain unchanged.
Reversal: remove the relevant world allowlist entries to withdraw full-screen
exceptions (existing snapshots expire within five seconds), or revert the
source normally. Preserve every unknown receipt.

## Latest post-diagnostic attempt, 21 October approximately 21:27

READ: house receipt c9712 and local history confirm diagnostic landing
172e94a; tracked tree was clean. JEFF c9663 authorised one attempt after
landing. RAN check_sandbox_birth_guarded.py exactly once; it refused before
Guard, desktop or child creation. No retry or cleanup followed.

The fixed house observation reported issuer_pid=5380,
observed_at=1792643237.4421554, uptime_ms=274618234,
notification_result=0, notification_state=2, foreground_known=true,
foreground_exe="chatgpt.exe", input_desktop="Default", full_screen=true,
game=null, admitted=false. Reader reason: house observation
stale/unknown/unsafe. The diagnostic names the foreground executable; it
does not identify every program contributing to notification state or
establish game-clear admission. No HUD exception applies.

Receipt: research/window-lab/.tmp-agora/agora-sandbox/
birth-a9388-5b2240325d-check.json. child_started=false,
browser_launched=false, runtime_closure=unknown. CHECKS.json retains its
exact contents. Live returned-handle identity, resume and cleanup remain
unverified. No browser/mail test is admitted. No suites rerun: this round
changes evidence only; prior offline results below are historical.

NEXT owner JEFF: resolve the safe-context/admission policy before explicitly
authorising another attempt. Do not poll until safe or infer that a
non-game-looking executable clears game=null. Retained-runtime and delegated
engine ownership gaps are unchanged. The earlier "prepared/not live" text
below describes historical checkpoints; both source increments have landed.

## Executable-name increment, JEFF c9663

Prepared provider diagnostic: QueryFullProcessImageNameW on only the foreground
PID with PROCESS_QUERY_LIMITED_INFORMATION; publish executable basename only.
No process enumeration, command line, title, document content or image path is
published. Denial returns unknown; handle always closes; a changed foreground
window discards the name and refuses. No live query/run was performed here.

RAN test_guard_context.py: 12 tests in 0.647s, OK; git diff --check passed.
Fakes verify basename-only redaction, denied image reads, and no accidental
HUD/game exemption for pythonw.exe/python.exe/agora_start.exe.

Important incomplete policy seam: hud_lifecycle.pid_path/read_pid and hud.py
use a PID-only hud.pid record. No saved creation/image-bound HUD registration
was found. The native lifecycle matcher identifies hud.py via full scoped
script arguments and fresh process metadata; using it would require a further
reviewed scoped identity query, not accepting the basename as identity.
An unrelated Python program or reused PID must not become our HUD by name.
Accordingly this increment records the name but does not yet enable a HUD
exception; notification state 2 still has game=null and refuses.

JEFF's approved sequence is offline tests, ordinary landing/house refresh,
then one bounded fake attempt. Its receipt can expose the actual foreground
basename, even if admission still refuses. The exact remaining decision is
how the house verifies this HUD's creation-bound identity and game-clear
condition. No HUD restart/new runtime registration was attempted or assumed.
Lifecycle consequence: guard_context.py is already a HOUSE_FILES member;
ordinary house refresh is explicitly allowed by c9663.

## Post-landing authorised attempt, 21 October approximately 21:07

READ: house landing receipt c9639 and local git history confirm e6516ee landed;
the current branch includes 3013b37 (house-preserved source), e6516ee and
9801c83. Tracked tree was clean before this attempt. JEFF c9647 authorised
exactly one bounded fake run and required stopping on any refusal.

RAN check_sandbox_birth_guarded.py once. It refused BEFORE Guard/desktop/child
creation. The actual fixed-path house observation was read:
issuer_pid=31056, observed_at=1792642041.30146, uptime_ms=273422093,
notification_result=0, notification_state=2, foreground_known=true,
input_desktop=Default, full_screen=true, game=null, admitted=false.
The reader reported "house observation stale/unknown/unsafe"; regardless of
age, this record explicitly refuses due to full-screen/unknown game state.
No inference that the foreground is the HUD or a game is supported.
Worker-local notification state was also 2.

Receipt: research/window-lab/.tmp-agora/agora-sandbox/
birth-a9388-11c93a4e96-check.json. child_started=false,
browser_launched=false, runtime_closure=unknown. No retry, process query,
cleanup, input, capture or browser/mail launch followed.

This proves the deployed provider produced a readable nonempty observation
with known foreground; it does NOT prove safe admission, child manifest,
cleanup or Alex-screen continuity. JEFF owns the next safe-context decision.
Prior retained-runtime and delegated-child reconciliation gates remain.

READ landing health receipt: scene 58 passed; house reported existing
test_artifact_view (11 errors), test_followups integration-base drift naming
house.py, and test_host_route_parent (21 errors). Not independently rerun or
attributed in this round; do not call full main health green.

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
