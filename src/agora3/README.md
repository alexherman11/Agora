# Agora3 native runtime (retained, not active)

This package is the earlier native runtime. It is kept, not developed; the active work is the text desk under `research/text-desk-lab/notation/`. These notes moved here from the repository's AGENTS.md on 25 September 2026, unchanged. Paths in "First runtime boundaries" are relative to this folder.

Documents labeled **prototype lineage** describe another implementation branch.
Preserve their evidence and lessons, but never infer a current API or working
guarantee from them; translate through Runtime Guide and Implementation Status.

## Architecture boundaries

- Authoritative native-world changes enter one authenticated verb gateway and
  append durable events. Materialized tables and indexes are derived.
- Guest root applies to the Linux workspace. It does not control host credentials,
  the authoritative world service, host files or recovery.
- Arbitrary guest files, processes and external systems are not covered by the
  native-world replay guarantee. Model them as resources with observed status.
- Replay restores recorded state; it never executes programs, sends messages,
  invokes models, restarts jobs or repeats external effects.
- Applications, UI, tools, schemas and skills are versioned packages/objects.
  JEFF develops them through native operations. A guest-machine execution
  capability supports experimentation without making opaque commands native facts.
- Derive human actions and JEFF's tools from one installed-capability registry.
  Visibility of a lens does not determine whether its tools exist.
- Missing domain tools should be authorable during use, including inspectors and
  development tools. Prefer reusable native capabilities for familiar work, with
  executable packages and guest instrumentation available for invention. Invention
  tests start with the relevant tool absent; reuse and incremental-development
  tests preserve existing tools and work.
- Native applications must remain usable and well designed after customization.
  Verify actual interaction, legibility, keyboard/focus behavior and continuity,
  not only schemas or successful builds. Smaller-agent use without source access
  is a separate evidence question, not an untested claim or a gate on every edit.
- The shell, including chat, is programmable. Independent host recovery remains
  available when the authored shell fails.
- Broad operator-selected development delegation is the initial direction.
  Do not build a detailed multi-user permission system before it is useful.
  Do preserve caller identity, effective delegation and the host/guest boundary.
- Worker topology is open. Explore asynchronous machinery when it serves the
  authorized task; preserve task identity, progress, cancellation and evidence.
  Vision prose alone does not authorize unrelated work or external effects.

## Implementation practice

Prefer small runnable vertical slices. Keep host services and guest programs
separate in imports and deployment. Build the minimum host machinery necessary
for general capability; avoid new platform cases for individual UI requests.

Do not copy an implementation merely because it once worked. Reuse algorithms or
sections of prose when their contract remains appropriate, and verify them here.

Before calling a slice complete, update Implementation Status with the actual
checks and remaining limitations. For storage changes, verify replay equivalence,
failure atomicity and compatibility. For UI changes, test actual input delivery.
For runtime changes, enumerate effective tools and test the intended boundary.

Do not claim a running VM, successful model call or browser behavior from static
configuration or scripted model output. Source and dependency versions must be
pinned for execution. Credentials and private worlds are never committed.

The repository now has a runnable first native-development slice. The implemented
API is documented in `docs/Reference/Runtime Guide.md`; other proposed operations
remain design options unless Implementation Status records their evidence.

## First runtime boundaries

- `world.py` owns the durable SQLite event journal and rebuildable object cache.
  `Gateway.commit` is the authenticated native write path; helpers receive that
  callback. Do not write projection tables directly outside replay/rebuild tests.
- `gateway.py` validates operations and schema admission. Its protected keep is
  read durably under `locking.py`'s cross-process lock. Revoke and commit cannot
  race through cached authority. Never rebind an authenticated request to a newer
  authority generation after checking its token.
- `packages.py` retains source/build/installation identities. Application facet
  schemas use bounded JSON validation and generic projection. Kernel/runtime
  facets require dedicated operations; ordinary facet writes cannot forge them.
- `guest.py` executes only inside the configured dedicated Linux VM. `yard.py`
  resets a distinct VM for builds/candidates. Never run a candidate in the live
  credentialed guest as a fallback. `bridge.py` exposes native operations only;
  host recovery and model/account methods are not on that listener.
- `jeff.py` is the host-side managed model transport and native dispatch adapter.
  The broad execution workspace is Linux; the complete agent orchestrator has
  not moved into the guest. Its only model tools are generic native discovery and
  invocation, plus the runtime clock/composition helper. Verify actual runtime
  inventory after changing its SDK/runtime/configuration, not only Python mocks.
- `builtin/shell/index.html` is the supplied native package source. The live shell
  comes from its installed native revision. `host/` is the independent parent and
  recovery UI. The iframe receives a message bridge, never operator credentials.
  Flush pending native edits before replacing a live shell.
- `prompts/jeff.md` preserves Alex's original orientation verbatim. Do not rewrite
  his text without his direction. Maintain current environment guidance separately
  in `prompts/runtime.md`; verify both reach the first resumed model turn.
  Authored skills remain versioned package content, separate from this prompt.

Run `uv run pytest -q`, documentation checks, and Ruff for this runtime. VM and
live-model probes are separate, explicit checks with real resource use. Preserve
the distinction between a mocked transport test, a real compiled-runtime inventory,
a real guest action, and successful live model authorship.
