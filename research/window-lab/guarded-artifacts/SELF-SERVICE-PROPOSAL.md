# Smallest resident visual-check boundary — proposal, not implemented

Read after JEFF's c8064: `host_verbs.py`, `host_route_parent.py`,
`sandbox_window.py`, and `hud_playtest.py` copy/window/report lifecycle.
The pieces for a guarded check exist; a demonstrated resident-to-harness job
route does not. Host verbs originate in the painter's native bridge, not resident
Desk commands. The resident parent host dispatcher is explicitly disabled.
Neither should be enabled as a generic shell/browser route.

Propose **one house-side operation: `visual.check(request-id)`**. JEFF owns the
world request and receipt form. A trusted registered resident turn may submit
only a finite reviewed recipe ID, an existing authorized Agora item/lens
identity, copy revision, one named recipient, and one of two viewport presets.
World props/text alone are not host authorization. No source path, program,
URL, arbitrary JavaScript, shell line, arbitrary `--apply` file, account/media
control or live-world act is an input.

One existing host-side harness runner admits requests by durable ID, freezes a
disposable copy at a recorded event, resolves the item inside that copy, and
executes a fixed code-owned journey using `Sandbox Window` plus continuous
`Guard`. It binds the browser only to that copy's local painter. No real input
desktop access, external navigation, clipboard, hud.py or model process. Fail
closed if hidden desktop/Guard is unavailable; no visible fallback or repeated
provider polling. The map recipe needs separately reviewed read-only/local app
dependencies; do not treat a world URL as authorization.

Keep queued/running/refused/failed/completed receipts outside resident prose;
retain request identity, requester, recipe/source revision, copy event,
viewport/DPR, steps/assertions, Guard verdict, exact artifact/report hashes,
times and owned-child cleanup result. One runner at a time, bounded duration and
steps; deduplicate repeated requests and never automatically retry an unknown
outcome. Reconcile an interrupted owned job before starting another. No new
model/worker admission or change to the four-worker cap.

After closing the sandbox and receiving successful Guard, deliver the bounded
immutable PNG through existing addressed image-comment/pending-turn transport.
Use a reviewed result-envelope schema, not arbitrary local files; extend the
artifact selector's explicit producer policy in that separate implementation.
Large images refuse or require an explicitly selected bounded crop, never a
silent substitute. The receipt says separately whether a journey passed,
pixels reached the turn, and a resident actually reviewed them.

This would let JEFF request and inspect a check without a builder doing each
run. Today it is a missing control boundary, not a supported operation.
Current a7940 attachment source remains independently ready; live delivery
proof is pending. No new control source, settings or host lifecycle action was
made for this proposal.
