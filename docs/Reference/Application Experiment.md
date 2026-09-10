# Application Experiment

**Implemented on `experiment/native-applications`, September 10, 2026.**

The experiment separates an application release, its open appearances, and the
objects it operates on. It preserves the combined experimental runtime at commit
`d8a7415` and adds a browser application slice in an isolated worktree/world. The
existing improved Desk on port 8870 and its active JEFF work are not its targets.

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
different applications are. Installing new code does not replace open frames;
each view adopts it explicitly after retaining its draft.

An authored generic desktop discovers installed applications and hosts each in
an opaque-origin iframe. It contains no Notes/Documents case. Common editor code
provides save/flush, revision-bound selection, change notification, extension
state and facet updates. A small annotation extension uses this public contract
in both applications. The release builder vendors that common source into each
independently retained package; there is no runtime shared-global dependency.

This replaces several implicit dependencies with small explicit contracts. It
does not establish that the same contract suffices for every future application.
The next useful test is a non-text application and then migration of an existing
research feature onto the editor contract.

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
does not require resolving a content conflict first.

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

- Full Python suite: **140 passed, 1 optional test skipped**. Thirteen added native
  tests cover scope, refusal atomicity, revisions, drafts, installation/schema
  compatibility, refresh/revocation, removal/reimport, portable fresh-world
  installation, malformed manifests and open-view limits. Replay equivalence is
  checked across the lifecycle cases.
- The optional real Codex runtime inventory passed separately with a local mock
  model: native discovery/invocation and clock/composition remained the effective
  capability surface. This is not a live model-authoring claim.
- Final real Edge run: **16 browser checks passed**, using actual text/selection
  input, cross-app updates, annotation reuse, retained conflict drafts, one-view
  updates, actual download/upload, remove/reimport, reload and a narrow viewport.
  It also exercised child-frame scope refusals and parent DOM isolation, with no
  page JavaScript errors. Headless Edge did not take over the user's browser.
- Ruff lint/format and whitespace checks pass. The clean demonstration world is
  separate from the mutation-heavy browser test worlds.

Reproduce native checks with `python -m pytest`; the optional inventory uses
`AGORA_CODEX_BIN` as documented by its test. Browser acceptance lives in
`scripts/test_applications_browser.cjs` and expects a newly prepared world served
by `scripts/application_demo.py`. It intentionally refuses the active Desk port.
Set `PLAYWRIGHT_MODULE` when Playwright is provided outside the repository.

Local retained evidence is in `local/application-browser-evidence-v2/` (report,
screenshots and exported bundle). It is not committed along with private worlds.
The launcher and runnable source are in the repository; start at
[the example README](../../examples/native-applications/README.md).

## Limits and next questions

This is a focused two-application prototype, not a replacement for the current
research Desk. Citations, packets, comment replies, JEFF chat and existing
`studio.*` data migrations have not been ported. The annotation example introduces
`text.annotations`; it does not claim compatibility with the old comments schema.
Its anchors use revision/hash plus UTF-16 ranges and quote/context evidence;
ambiguous relocation remains unresolved rather than selecting a wrong passage.

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
network side channel or denial of service. No VM was started and no live model
turn was invoked to validate this slice. A separate execution design is needed
before bundling backend programs under equivalent per-app authority.
