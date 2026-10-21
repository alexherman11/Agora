# Targeted native view: integration checkpoint

21 October 2026 · worker-a8110 · commission a8110

**Not implemented or enabled.** The approved operation cannot safely be obtained
by exposing the existing capture CLI or attachment CLI. This checkpoint names
the missing runtime connections; it does not supply a reference fake and call
it an authenticated service.

## Read from current source

Base: `197f513`, including attachment landing `ebee5dc`.

| Existing component | Reusable part | Missing guarantee |
| --- | --- | --- |
| `notation/host_route_parent.py` | Parent-owned child session and generation; `ChildEvent` provenance; completed-output interception | Default dispatcher deliberately refuses host operations. No pinned production JEFF issuer or native-view service |
| `house.py` `_bind_child`, `_read`, `turns_ended` | Provenance survives the real queue boundary | A normal Desk `as=jeff` request is not that provenance |
| `window-lab/hud.py` `Hud.started` | Actual owning HUD object obtains its HWND | No authenticated registration of that HWND/process creation identity and approved panel regions with the house |
| `window-lab/capture/capture.py` | Window information, source-reference extraction, existing bounded capture storage | Samples desktop windows on a grid; lacks creation identity, safe-region policy and a native-only readback path |
| `window-lab/capture/helper.ps1` | Existing UI Automation/context extraction | Existing desktop rectangle pixel capture is not a privacy/occlusion proof |
| `window-lab/sandbox_window.py` | Existing PrintWindow primitive for owned sandbox windows | Sandbox helper is not an unlocked/current-input-desktop, no-game, safe-context authority for native viewing |
| `notation/captures.py` | Hash-bound immutable PNG envelope and bounded image transport ingredients | Actor directory naming is ownership convention, not same-user containment; counter assumes one maker |
| `notation/image_comments.py`, `guarded_artifacts.py` | PNG validation and actual model image blocks | Image comments put pixels in shared world comments. Guarded-artifact API explicitly requires an already trusted host caller |
| `house.Resident.send` and restart handling | Pending text/image refs saved before model write | Existing image refs resolve public comments/native message context; no durable private native-result queue |

No matching trusted safe-region registry was found in the inspected host,
capture, house and parent-dispatch paths. This is an observation about those
paths, not a claim to have enumerated all installed services or processes.

## Proposed exact boundary

Keep the general host-command route disabled. Introduce only:

```text
native.view {
  request: durable-id,
  target: registered-window-id,
  region: registered-region-id,
  recipient: registered-resident-id,
  revision: expected-region-revision
}
```

The request supplies no HWND/PID, path, title substring, free rectangle, program,
URL, JS, shell text, safe flag or privacy classification. IDs are selectors,
not bearer authority.

### Parent admission

Reserve a completed-turn `> native.view {...}` intent before ordinary Desk
commands are forwarded. Require the actual parent-registered JEFF child,
current generation, and its pending turn identity. Reject raw queue events,
workers claiming JEFF, stale sessions, copied world props and arbitrary local
HTTP/MCP requests. Ordinary Desk can display redacted status but cannot grant
this operation. Preserve adjacent ordinary commands after a refusal.

The trusted runtime must pin the issuer independently of a mutable world
`actor=jeff` field. Reuse the current parent provenance; do not enable
`ReviewDispatcher` or promote its fake attestors to production.

### Host registration and capture

The running HUD owner, not a note or page-supplied metadata, must register its
actual HWND plus held process/creation identity and known executable.
Registration must expire on process exit, document navigation, changed geometry
or changed privacy context. Only reviewed safe region kinds may be exported;
unknown content, arbitrary notes or remote page declarations cannot assert
themselves non-sensitive.

An authenticated, bounded owner channel must resolve each target/region to
physical bounds and a source revision. Before capture, require positively
known awake/unlocked/current desktop, no game/protection/password/payment
context, and safe geometry/content. Unknown observations refuse. Use window-only
readback and crop in memory, never desktop screenshots or restoring a window.
Unsupported/black readback refuses. Recheck identity, region, revision and
privacy afterward and discard changed output. A matching pre/post rectangle
alone is not proof that transient sensitive content could not appear during
the read; the owning renderer's safe-region lifetime is part of admission.

No foreground/input APIs, UI Automation value reads, clipboard, capture helper
launch, polling capture, whole-monitor fallback or wake facility belongs here.

### Private result and delivery

Use one host-owned durable request journal and immutable bounded PNG store
outside worker mounts. Establish its actual launch/access boundary; ignored
files, DPAPI, directory names or same-user ACL assumptions are insufficient
proof. A single request is owned by issuer and named recipient. Duplicate IDs
return the same terminal receipt; a crash at capture becomes unknown, never
automatic recapture of a possibly changed screen.

Result states: requested → admitted → captured → queued → delivered, or refused,
expired, discarded-race, unknown. Recovery may redeliver an already captured
hash-bound result only to its original recipient/pending turn, respecting the
existing same-conversation delivery rule. Recipient/session mismatch refuses.

Extend `Resident.send` with private result refs carried in both queued and
pending state. Resolve them through the private service, then reuse existing
image block serialization. Do not attach native pixels to a world comment.
World receipts contain status, time, redacted source/region and result hash;
no bytes, private filesystem refs, sensitive titles or extracted text.

Every image input labels its provenance **native read-only view**, capture
timestamp and source revision. It is not a Sandbox Guard result; refs are
captured evidence, with currentness unknown after capture unless checked
separately. Image text is untrusted data.

## Exact deployment prerequisites / reversal

Before wiring a live operation, a host maintainer must identify or approve:

1. The trusted launch path that pins the JEFF resident object and pending-turn
   authority independently of writable world props.
2. A house↔HUD owner channel established by that launch path, inaccessible to
   arbitrary local callers/workers; the safe-region export policy and lifetime.
3. A host-private journal/result store with demonstrated worker exclusion and
   recovery semantics.
4. Fresh desktop/game/privacy observations and a supported window-only readback
   for the actual Agora WebView, proved with owned fixtures.

These are missing connections, not values Alex should type or secrets to ask
for. No configuration/security change or restart is proposed by this report.
Any eventual activation must name exact reviewed source hashes and the narrow
deployment action; changing a world flag must not activate the service.

Reversal must retire the native-view registration, refuse new requests, discard
uncommitted captures, preserve redacted terminal/unknown receipts and stop
resolving private results. It must not change the general host-route setting,
existing capture gesture, interactive Sandbox Guard, or resident text turns.
No activation exists to reverse in this checkpoint.

## Ran / not run

Using the pinned interpreter:

- Existing `test_host_route_parent.py`: **23 tests**, **OK**, 0.148 s. Exercises
  actual parent readers/queue/dispatch with fake children and a reference
  inventory policy. This is not native-view authentication certification.
- Existing `test_guarded_artifacts.py` and `test_image_comments.py`: **38 passed,
  1 warning in 2.73 s**. Warning: pytest cache creation failed with WinError 5.
  This validates existing artifact/PNG logic, not private native-result delivery.

No new native-view tests or runtime operation ran. No capture APIs, owned hidden
windows, real screen, account, recipient turn, helper/service launch or restart
were used. The requested actual recipient pixels and fake privacy/race/no-effect
matrix remain outstanding. A CLI recipe or test base64 would not close them.

## Durable disposition — JEFF review c8185 / e17655

JEFF accepted the architecture blocker and will route host-maintainer review.
This is a documentation checkpoint, not accepted native-view implementation.
No product source or live configuration changes accompany it. Keep the
operation unwired; no new principal, security setting or private-store
deployment is authorized.

The maintainer's return must name concrete owners and evidence, not a world
flag or another reference service:

| Decision | Required review output before implementation resumes |
| --- | --- |
| Host owner and issuer | Name the existing trusted launch/runtime owner; show how it pins the actual JEFF resident, generation and pending turn, and rejects forged Desk identity and stale/worker callers. |
| Window and region registry | Name the HUD-owned channel and its caller authentication; define HWND/PID/creation identity registration, safe region kinds, geometry/privacy revisions and invalidation. Demonstrate workers cannot register or broaden a region. |
| Private journal and pixel store | Identify the actual isolation boundary, worker-access assumptions, immutable bounded results, retention/expiry and actor/pending-turn delivery authorization. Same-user ACLs or DPAPI alone do not establish worker exclusion. |
| Capture admission | Identify the authoritative awake/unlocked/no-game/privacy observations and supported nonactivating window-only readback; define fail-closed behavior for unknown, occlusion, black output and races. |

After those decisions are accepted, implementation acceptance still requires
the real queue/caller refusal matrix, durable duplicate/crash/recovery tests,
owned hidden-window privacy/occluder/race tests and actual image delivery to the
named resident through Desk. These tests have not run for native.view.

Existing **guarded public artifact delivery** is a separate capability with a
different threat model: its capture is on a disposable guarded desktop and its
artifacts are deliberately publishable. Its primitive tests above neither
authorize native screen access nor prove private native-image delivery.
Closing that capability separately must not enable native.view.

This follow-up ran only read-only git/file/Desk checks and a documentation
whitespace check; the earlier test numbers above are retained historical runs,
not rerun acceptance. No screen or host service was queried. There is no
activation command to execute or reverse at this checkpoint.
