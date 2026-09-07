# Implementation Status

As of 2026-09-06.

## Working code

Agora3 0.1 is a running local native-development bootstrap. It has a protected
native world service, a programmable desk/chat shell, dedicated Linux execution,
a separate resettable candidate VM, and JEFF using managed OpenAI-account sign-in.
Live Astra has authored, built, tested, installed and invoked a new native tool
through this stack. The implemented protocol is in [[Runtime Guide]].

The current design set is indexed by [Start Here](Start%20Here.md). Architecture
claims elsewhere are proposed contracts unless supported by evidence here.

## Runtime inventory

| Capability | State |
|---|---|
| CLI and packaging | Implemented: serve, verify, rebuild, guest status and emergency stop |
| Authoritative world service, event storage and replay | Implemented local transactional journal and derived objects; native replay executes no code |
| Authenticated gateway and broad development delegation | Implemented host/guest credentials, durable generation revocation and cross-process commit/revoke serialization |
| Linux VM lifecycle, execution and independent recovery | Implemented dedicated VirtualBox Ubuntu guest, pinned SSH, root execution and protected poweroff; existing VMs untouched |
| Model/account authentication integration | Implemented managed Codex SDK OAuth path; real Astra call and actual runtime inventory verified |
| Native source packages, builds and installed action registry | Implemented source/build/installation revisions, stale-promotion rejection, restore, typed Python actions and same-turn discovery |
| Application-defined facets and live queries | JSON facet schemas and generic projection implemented; paginated coherent query pages implemented; subscriptions/live-query ownership remain planned |
| Native bindings, authored transformations and dependency evaluation | Planned; contract in Objects and Facets §3.9 |
| JEFF inventing missing inspection/development tools during a session | Live native-tool authorship verified; general guest administration and package editing available; full inspection feedback remains an expanding toolset |
| Browser runtime, native shell and conversation persistence | Implemented editable sandboxed HTML shell, durable messages/drafts, protected recovery and pending-edit flush before replacement |
| Candidate testing, diagnostics and activation | Python builds/candidates run in a distinct baseline-reset VM without live native credentials; proposed native writes validated in disposable state; browser build admission is not interaction testing |
| Main guest native access | Implemented restricted RPC through pinned SSH reverse forwarding; guest programs use agora_native.call; candidate VM lacks this connection |
| Native skill editing and installation | Versioned package skill files and discovery implemented; no separate skill scheduler or implicit elevation of arbitrary content |
| Authored explicit memory, retrieval and persistent work collections (AlexBench) | Planned; examples and acceptance in Native Development §6.2 |
| Malleable native music application and compact sidebar | Planned; local fixture and real provider integration require separate evidence |
| Asynchronous development agents | Feature horizon |
| External-effect uncertainty, delivery receipts and retry recovery | Deferred; not a prerequisite for current native-development proofs |
| Shared rooms, synchronization and broad device distribution | Feature horizon |

The full design remains larger than this implementation. There is one foreground
JEFF turn at a time. Its model/account adapter still runs on the protected host;
the general execution workspace and authored programs run in Linux. Moving the
complete agent orchestrator into the guest remains work. No old-world migration
or general cross-version export format is offered.

Native objects currently use object-level revisions and register replacement.
Python actions receive at most 1,000 objects. Source/build receipts retain bytes
and digests but do not freeze the mutable main-guest dependency environment.
Returned proposed changes form an atomic batch; a live guest program using the
native client can also make separate incremental commits. It shares the main
VM's broad development authority with other root-capable guest programs.

Stopping a JEFF turn blocks later callbacks but does not undo earlier work or
terminate every independent guest process. Native revocation blocks later native
commits; protected VM poweroff stops that machine. World replay, application-code
restore and VM reset remain distinct operations. Witness erasure, per-package
isolation, grants for multiple people, and external-effect uncertainty are not
claimed by these first-runtime checks.

## Verification

Run from the repository root:

    uv sync --dev
    uv run pytest -q
    uv run agora3 --world worlds/dev verify
    uv run python scripts/check_docs.py
    uv run ruff check .
    uv run ruff format --check .

Verified on 2026-09-06 on Windows with Ubuntu 24.04.4/Python 3.12.3 in the guest:

- Native tests cover replay/rebuild, whole-batch rejection, stale writes, schema
  admission, protected runtime records, package source paths, activation races,
  candidate proposals, real HTTP authentication/origin checks, revocation and
  recovery without rewinding application data.
- Guest checks cover ownership, pinned SSH, disabled host sharing, real root
  execution, syntax errors in non-entry files, bounded output, ordinary descendant
  timeout cleanup, poweroff/start and reconnection.
- Live bridge/yard checks committed a native note from the main guest, rejected
  unauthenticated candidate writes, and verified that successive yard invocations
  lost earlier filesystem changes and had no live native client/token. The yard
  returns to powered-off state after an invocation.
- Actual compiled Codex runtime inventory, with local simulated inference,
  exposed only Agora discovery/invocation and the clock/composition facility.
  Host process execution, filesystem helpers, MCP, plugins and ambient skills
  were absent. This check is separate from mocked Python transport tests.
- Real account-backed Astra independently authored a counter schema and Python
  package, built/exercised it in the separate yard, confirmed zero candidate
  writes, installed it, discovered its action and committed values 1 then 2 in
  the same turn. The result had seven native events, five objects and valid replay.
  `scripts/probe_authoring.py` reproduces this explicit live check and writes its
  own report/trace. A host sentinel check is narrow evidence, not a filesystem audit.
- Real browser input verified note creation/editing, full-page persistence,
  unsent drafts, replacement-time flush, stale projection handling, package/tool
  inspection and desktop/mobile layouts. Guest browser fixtures and independent
  host-browser checks remain distinct evidence.
- Live JEFF authored dragging in the native shell, installed source revision 5
  as installation revision 4, and retained its instructions and browser tests in
  the package. Independent real pointer input moved a note from (36, 40) to
  (126, 95); native geometry survived reload while title/body editing and drafts
  continued working, with no browser JavaScript errors. The supplied baseline
  source was unchanged; the development world runs JEFF's installed revision.
- Documentation links, heading targets, JSON examples, code fences, Ruff lint and
  formatting are checked with the commands above. The archived scaffold checks
  do not stand in for these runtime checks.

Private VM resources, development worlds and detailed live reports remain outside
Git. The setup recipes and repeatable test/probe commands are retained in source.
