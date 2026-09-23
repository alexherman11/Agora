# Application Experiment

**Implemented on `experiment/native-applications` and merged into `agora4`, September 10, 2026.**

The experiment separates an application release, its open appearances, and the
objects it operates on. It preserves the combined experimental runtime at commit
`d8a7415` and adds a browser application slice in an isolated worktree/world. After
the initial prototype, Alex authorized migrating the existing resident as JEFF0.
The migration preserves the old journal and authored work while installing the
new desktop and applications in a new canonical world.
The Agora4 integration preserves that world and its durable conversation in place;
its launcher now loads the merged Agora4 source. The restored design vault remains
the design reference, and Alex's original JEFF orientation is retained verbatim
in `src/agora3/prompts/jeff.md`, with environment guidance in `runtime.md` beside it.

## What the experiment establishes

Notes and Documents can show and edit one native object through separately
installed browser packages. Opening a document does not copy or convert it.
`core.title` and `core.text` carry shared content; `text.format` declares plain
text or Markdown. The application's `accepts` declaration describes facet
compatibility, rather than requiring an application-specific document marker.

Each open appearance is a separate protected native object carrying its subject,
package/build binding, bounds, retained UI state, open status and scoped lease.
Closing, moving or refreshing it does not change the content object's revision.
Two appearances of one application are independent, just as appearances of two
different applications are. The September 12 live-update repair automatically
adopts compatible installed releases in open views after retaining each browser's
draft. An explicit Update control remains available to retry blocked updates.
Compatible refresh keeps the subject-bound lease so another browser can finish
retaining its draft; close, reopen and uninstall still revoke/renew leases.

An authored generic desktop discovers installed applications and hosts each in
an opaque-origin iframe. It contains no Notes/Documents case. Common editor code
provides save/flush, revision-bound selection, change notification, extension
state and facet updates. A small annotation extension uses this public contract
in both applications. The release builder vendors that common source into each
independently retained package; there is no runtime shared-global dependency.

This replaces several implicit dependencies with small explicit contracts. It
does not establish that the same contract suffices for every future application.
Existing native discussions now consume that contract. A non-text application and
further extraction of research/packet surfaces remain useful next experiments.

## Implemented contract

Application manifests use `runtime: browser-1`, `ui.mount: application` and an
`application` object with protocol `agora.application/1`. Required fields are
`accepts`, `read_facets`, `write_facets`, `size`, `create`, and `schemas`.
Definitions in `application_schema.py` are the exact admitted shapes. Browser
assets use the retained ordered JS/CSS assembly introduced in the combined
runtime. No candidate guest is necessary for these browser-only builds.

The native operation registry derives these operations for human/JEFF clients:

| Operation | Effect |
|---|---|
| `application.list` | Discover enabled applications and retained views. |
| `application.open` | Bind a compatible subject, or atomically create a subject and view. |
| `application.surface` | Resolve the view's pinned HTML and scoped context. |
| `application.request` | Validate current authority, enabled installation, open state and lease, then dispatch a bounded data request. |
| `application.position` | Retain appearance bounds independently of content. |
| `application.close` / `application.reopen` | Retain state and revoke/renew the view lease. |
| `application.refresh` | Adopt installed code for one view; refuse implicit grant expansion. |
| `application.uninstall` | Disable the installation and close/revoke its views in one transaction, preserving content, schemas and drafts. |
| `application.export` / `application.import` | Transfer a self-contained source release through existing package save/build/install. |

A child frame receives only four data methods: `read`, `transact`, `state.get`
and `state.set`. Reads/writes are restricted to its bound subject and admitted
facets. A transaction contains exactly one subject change and requires its native
revision. UI state belongs to that appearance and is capped at 1 MB. Native writes
still pass through authenticated `Gateway.commit` and the event journal; app
attribution is recorded alongside the caller. Parent routing checks the sending
frame, and leases are checked again at the native gateway.

The child receives no operator token, generic world query, guest execution or
application-management method. Its sandbox permits scripts only. The protected
host accepts requests from the authored desktop, not a nested child pretending
to be that desktop. Existing recovery and revocation remain above the authored
surface. These checks are a browser application boundary, not a new multi-user
grant system or a security boundary for root-capable Python guest packages.

Change signals prompt bounded subject reads; they are not a new query-subscription
engine. The editor preserves local selection during background refresh. Revision
conflicts keep the draft with explicit Use my draft / Use saved text actions.
Close/update flushes freeze input while the frame confirms retention. Retention
does not require resolving a content conflict first. Each tab also keeps its own
retained view state in the protected host's session storage; native state remains
the durable fallback. This prevents an observation browser's clean state from
overwriting another tab's conflicting draft during remount. These local copies
survive reload within the tab, not closing it or clearing browser storage.

The host waits up to 20 seconds for shell draft retention (application flushes
have a 12-second deadline), reports the failure reason, and retries pending
publication after 10 seconds using the latest installed shell. Frames that never
completed the application ready/init handshake have received no subject context;
they do not block replacement of the shell. Running applications must acknowledge
retention before replacement. Ordinary shell polls run every 1.5 seconds and
application polls every 2.5 seconds; these are not a real-time delivery guarantee.
Broken initialized applications, unresolved storage failures and expanded grants
can still block updates and must remain visible rather than discard edits.

## Distribution and lifecycle

The `agora.application-bundle/1` envelope contains `source` (ID, files, manifest)
and its `sha256`. Import cannot replace `agora.shell`. Source revision checks
prevent unnoticed replacement of a locally changed package. Export uses the
installed build's source, rather than an uninstalled working revision. The digest
is an integrity check, not a signature or trusted publisher identity.

Schema definitions accompany the release. Installation admits new schemas or
requires exact equality with existing definitions; incompatible changes are
refused. Schema and installation changes commit together. Failed import can
leave a saved source/build candidate, while the old installation stays active.
There is no dependency resolution, package provenance service, schema migration
engine or atomic transaction spanning all import staging steps.

Removing an app disables its installation and retains its source/build history.
It never deletes documents, annotations, schemas or view drafts. Reimport can
reopen the same retained views. General data export and uninstall garbage
collection are outside this slice. Existing research-packet data export is a
different operation from application distribution.

## Verification and evidence

- Full Python suite: **145 passed, 2 optional cases skipped**. Thirteen original native
  tests cover scope, refusal atomicity, revisions, drafts, installation/schema
  compatibility, refresh/revocation, removal/reimport, portable fresh-world
  installation, malformed manifests and open-view limits. Replay equivalence is
  checked across the lifecycle cases. Five subsequent tests cover protected
  resident continuity and subject-linked discussion authority, including stale
  selection revisions and failed-resume preservation.
- Both optional real Codex runtime inventory cases passed separately with a local mock
  model, including a new process resuming an existing thread: native
  discovery/invocation and clock/composition remained the effective
  capability surface. This is not a live model-authoring claim.
- Final real Edge run: **16 browser checks passed**, using actual text/selection
  input, cross-app updates, annotation reuse, retained conflict drafts, one-view
  updates, actual download/upload, remove/reimport, reload and a narrow viewport.
  It also exercised child-frame scope refusals and parent DOM isolation, with no
  page JavaScript errors. Headless Edge did not take over the user's browser.
- A separate migrated-world run passed **12 browser checks**: visible JEFF0
  transcript, carried-over live Markdown, actual typing and undo, selection staged
  without sending, existing discussion identities/original anchors, new discussion
  creation, migrated new-thread/reply drafts and a reply on an existing thread.
- Ruff lint/format and whitespace checks pass. The clean demonstration world is
  separate from the mutation-heavy browser test worlds.

Reproduce native checks with `python -m pytest`; the optional inventory uses
`AGORA_CODEX_BIN` as documented by its test. Browser acceptance lives in
`scripts/test_applications_browser.cjs` and expects a newly prepared world served
by `scripts/application_demo.py`. It intentionally refuses the active Desk port.
Set `PLAYWRIGHT_MODULE` when Playwright is provided outside the repository.

Local retained evidence is in `local/application-browser-evidence-v4/` and
`local/resident-migration-browser/` (reports, screenshots and exported bundle).
It is not committed along with private worlds.
The launcher and runnable source are in the repository; start at
[the example README](../../examples/native-applications/README.md).

## Limits and next questions

This is a trusted first-party extraction. It now hosts the resident conversation,
live Markdown, and existing `studio.comment-thread` discussions through a separate
extension using public editor methods. Native `studio.document` Markdown is
recognized; a contradictory `text.format` refuses editing. Both releases declare
`agora.text/1`, UTF-16 selection units, source-edit semantics and supported operations.
`text.annotations` remains a separate small example; it does not rewrite old
discussions. Both anchor mechanisms preserve revision/hash and quote/context
evidence; ambiguous relocation remains unresolved rather than selecting a wrong
passage. Existing citation, packet and research data/tools survive, but their old
specialized UI has not all been ported.

Text uses revision-checked replacement, not a CRDT merge. The example assumes one
live browser owner per retained appearance; cross-tab editing of the same view
state is not coordinated. Abrupt browser termination can still lose input newer
than the last persisted draft. A cooperative flush protocol cannot make arbitrary
application code truthful or responsive.

Limits are 32 open views, 1,000 retained views and a 200-object desktop listing.
Queries/list refreshes are intentionally simple. The desktop has no full library
search, dependency manager, accessibility audit or keyboard workflow assessment
beyond the exercised controls. External preview navigation is disabled. Current
text applications declare explicit formats, but the generic compatibility rule
checks facets rather than value-level predicates.

The authored desktop retains broad local authority; the browser-app boundary does
not constrain a compromised desktop or the existing root guest. Imported code
is not evaluated on the host, but this is not proof against every browser escape,
network side channel or denial of service. Initial prototype acceptance used no
VM or live model. The subsequent resident handoff reuses the existing VM and
performs live continuity checks, separately from application-security evidence.
A separate execution design is needed
before bundling backend programs under equivalent per-app authority.

## Resident handoff and persistence

`scripts/migrate_resident.py` uses SQLite's consistent backup API, then adds native
events through the authenticated gateway. It refuses an existing destination and
verifies an identical original event prefix and every old object's identity/value.
Only the desktop's source and installation advance; their prior revisions remain
in history. The actual handoff retained 1,280 events, 1,135 objects, 30 messages
and 54 discussions. Existing unfinished discussion drafts are attached to retained
Documents views, including closed ones. An older observation-browser composer is
kept in a separately labelled unsent recovery object, never sent automatically or
used to replace a newer native composer.

The protected `agora.agent.resident` record names JEFF0, pins an owner-world path,
references the authored `jeff0.continuity` checkpoint and binds the exact durable
Codex thread/provider/model. New service instances resume this binding. A failed
resume or model mismatch refuses; neither silently resets the conversation.
The previous runtime used an ephemeral model thread, so its hidden internal
context is unavailable. The retained native transcript and authored checkpoint
bootstrap the first persistent session. Subsequent model context is retained by
the managed runtime; native journal backup alone is not a portable backup of that
runtime's conversation storage. Model/runtime changes must recheck effective tools,
including resumed sessions and their per-turn empty environment configuration.

The live handoff and an idle service restart both completed successfully. The
same saved thread ID remained bound, JEFF0 recalled the check phrase from the
preceding exchange without a new history bootstrap, and he confirmed readiness
after restart. These two handoff/check turns added four native conversation
messages. They were read-only checks of existing work, not live app-authoring tests.

The local canonical JEFF0 service reuses the existing guest and candidate VM
configurations; migration does not reset or clone their files. The former launcher
forwards to the canonical service and the old service refuses direct restart, so
ordinary launching does not accidentally create another JEFF0 from the archive.
Never launch an archived copy as the continuing resident without an explicit
transfer. Source, native state, guest files and managed model history have separate
storage and recovery responsibilities.
