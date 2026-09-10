# Runtime guide

**Implementation companion for Agora3 0.1.** This document describes the current
local runtime and its actual package protocol. [[Native Development]] describes
the broader design; [[Implementation Status]] owns verification evidence and
remaining work. Examples here use the implemented operations, not the more
ambitious illustrative APIs elsewhere in the design.

## Where execution happens

The Python host serves the canonical native world, authenticated gateway,
conversation, package registry and independent recovery interface. The current
journal and derived objects share a host SQLite database; native replay never
runs package code. A dedicated VirtualBox Linux VM executes installed Python and
root shell commands. A separate candidate VM is reset for builds and exercises.
Neither uses shared host folders or a forwarded SSH agent.

JEFF's Codex SDK/account adapter currently runs on the host, with Astra inference
provided through the person's OpenAI account. The model has native discovery and
invocation tools, plus the runtime's clock helper. It has no ambient Codex shell,
app tools, host filesystem or account-token access. The SDK manages sign-in;
Agora does not extract OAuth tokens. A fully guest-resident agent orchestrator is
not implemented yet. “Living in Agora” currently means acting in the shared world
and its guest through this adapter.

The editable human orientation is
[jeff.md](../../src/agora3/prompts/jeff.md), restored from Alex's original wording.
Current environment guidance lives separately in
[runtime.md](../../src/agora3/prompts/runtime.md). The adapter loads the unchanged
authored text first, then the labelled guidance, including on the first resumed
turn. See [prompt provenance](../../src/agora3/prompts/README.md).
`AGORA_JEFF_MODEL` defaults to
`gpt-6-astra`; `AGORA_JEFF_REASONING` defaults to `high`. `AGORA_CODEX_BIN` can select
a compatible Codex executable. An unavailable requested model fails explicitly;
the harness does not substitute another. `AGORA_JEFF_LOGIN=device` selects the
SDK's device-code login; the default uses its browser login.

## Discovery and ordinary native changes

JEFF calls `agora_discover {}` for the live gateway schemas and
`agora_invoke {"name": operation, "arguments": arguments}` to invoke one. The
operation `tools.list {}` also returns installed package actions, including their
package and installation revision. Their existence does not depend on an open
view. Discovery and invocation work again immediately after installation in the
same turn.

`world.get {"id": ...}` returns an object's revision, facets and provenance.
`world.query` filters by a list of required facet types. It returns `items`,
`watermark`, `complete` and `next_after`. Follow the cursor with the same filters
and direction when incomplete. Ordering is by object ID; `reverse: true` reverses
that ordering. Each page is coherent; pages with different watermarks are not a
single frozen snapshot. This is a paginated query, not a subscription service.

`world.transact` patches facets atomically. Every object change includes its
current `expected_revision`; zero creates an object. Supplying a facet replaces
that facet's value; `null` detaches it. A stale revision or invalid facet rejects
the entire transaction. The current implementation versions the containing object;
independent revisions for individual facets remain a design direction.

An application can define a facet without editing platform source. This is an
exact `agora_invoke` argument envelope:

```json
{
  "name": "schema.define",
  "arguments": {
    "type": "alex.counter.state",
    "schema": {
      "type": "object",
      "properties": {"value": {"type": "integer"}},
      "required": ["value"],
      "additionalProperties": false
    },
    "expected_revision": 0
  }
}
```

The implementation supports bounded JSON schemas, generic JSON projection and
register replacement. It does not load remote references or executable schema
validators. Updating a schema checks existing instances; it does not silently
migrate incompatible data. `schema.list {}` returns the supported built-in and
application definitions. `core.*` and `agora.*` are reserved namespaces.

Create the example counter through the same gateway:

```json
{
  "name": "world.transact",
  "arguments": {
    "changes": [{
      "id": "counter-main",
      "expected_revision": 0,
      "facets": {
        "core.title": {"text": "Counter"},
        "alex.counter.state": {"value": 0}
      }
    }]
  }
}
```

## A complete Python package

`package.save` accepts `id`, `expected_revision`, `files` and `manifest`. `files`
is a map from relative filenames to their complete text. A save replaces the
package's source/manifest; read the current package before revising it and retain
files you want to keep. It does not install the revision.

For package `alex.counter`, this is a complete manifest:

```json
{
  "name": "Counter",
  "description": "A reusable increment action over native counter objects.",
  "runtime": "python-1",
  "actions": {
    "increment": {
      "entry": "counter.py:increment",
      "description": "Increment an existing counter by one.",
      "input_schema": {
        "type": "object",
        "properties": {"id": {"type": "string"}},
        "required": ["id"],
        "additionalProperties": false
      },
      "output_schema": {
        "type": "object",
        "properties": {"value": {"type": "integer"}},
        "required": ["value"],
        "additionalProperties": false
      }
    }
  },
  "skills": {"counter": "skills/counter.md"}
}
```

Retain this complete handler as `files["counter.py"]`:

```python
def increment(arguments, context):
    obj = next(
        (item for item in context["objects"] if item["id"] == arguments["id"]),
        None,
    )
    if obj is None:
        raise ValueError("Counter not found; create a native counter first.")
    if "alex.counter.state" not in obj["facets"]:
        raise ValueError("The target needs an alex.counter.state facet.")
    value = obj["facets"]["alex.counter.state"]["value"] + 1
    return {
        "result": {"value": value},
        "changes": [
            {
                "id": obj["id"],
                "expected_revision": obj["revision"],
                "facets": {"alex.counter.state": {"value": value}},
            }
        ],
    }
```

Also retain `files["skills/counter.md"]`, for example:

```markdown
Use tools.list to discover alex.counter's installed revision. Invoke increment
with the target object's id and that revision. Read current state after a conflict.
Do not repeat a successful increment merely because its result was unexpected.
```

The handler receives JSON-compatible `arguments` and `context`. Context contains
`objects`, the snapshot's `watermark`, and a `candidate` boolean. It has no
injected host gateway callback. This example returns JSON `result` and optional `changes`
using the `world.transact` change shape. Input/output schemas are validated; all
proposed native changes are validated and committed together through the gateway.
An installed invocation checks that its input watermark and installation are
still current at commit. Unrelated intervening world edits can therefore require
a retry in this initial implementation.

## Save, build, exercise, install, invoke

Use the returned values, rather than guessing receipt IDs or revisions:

| Operation | Arguments and meaning |
|---|---|
| `package.save` | `id: "alex.counter"`, `expected_revision: 0`, the two source files and manifest above. Returns the new source object. |
| `package.build` | `id: "alex.counter"`, `expected_revision: 1`. Returns `build`, `digest` and diagnostics. |
| `candidate.exercise` | `package: "alex.counter"`, `candidate: build`, `action: "increment"`, `args: {"id": "counter-main"}`. Tests the proposed write in a disposable copy. |
| `package.install` | `id: "alex.counter"`, `build`, `expected_revision: 0` for the first installation. |
| `tools.list` | Read the installed action and its installation `revision`. |
| `action.invoke` | `package: "alex.counter"`, `revision` from discovery, `action: "increment"`, `args: {"id": "counter-main"}`. Runs and commits the native change. |

These are three distinct identities: the editable source object's revision, an
immutable build receipt ID/digest, and the installation object's revision.
`expected_revision` on save/build refers to source; on install/restore it refers
to installation. `revision` on action invocation pins installation. Editing
source does not change the currently installed action.

A Python build compiles supplied `.py` files in the candidate Linux VM. The receipt retains the
exact source and manifest; it does not freeze installed guest dependencies or
produce a hermetic compiled artifact. It does not prove runtime imports or
behavior. Exercise the candidate before installing. Installation currently checks
source/build/base-installation consistency; successful candidate evidence is not
an enforced prerequisite.

Candidate execution uses a disposable **native-world copy** and a separate
candidate VM. Before each build/exercise the host restores that VM's configured
baseline snapshot; after execution it powers the VM off. The yard is required to
have a different machine identity and no live bridge configuration. Its response
includes `result`, `proposed_changes`, `candidate: true` and `native_writes: 0`.
Candidate code can alter its test machine; those changes do not become edits to
the live guest. Resetting a VM does not undo effects on outside systems, and this
runtime does not claim network isolation. Verification evidence belongs in
[[Implementation Status]].

`package.restore` installs an earlier retained build as a new installation
revision, preserving application data. Its source need not match the latest edit.
This restores executable presentation/behavior, not the guest filesystem or a
previous version of all world data.

## Skills, interfaces and guest files

The running application can connect a native bridge to the live guest. Once its
status is connected, a guest program can discover and invoke native operations:

```python
import agora_native

inventory = agora_native.call("tools.list", {})
counter = agora_native.call("world.get", {"id": "counter-main"})
```

The host provisions this Python client and a revocable guest credential, and
transports requests through pinned SSH. Calls still enter the authenticated
native gateway. The bridge has no account/model or protected recovery endpoints.
Use `guest.status` to inspect the bridge and yard state; use independent host
recovery to reconnect after a guest restart or authority change.

This enables guest programs to build packages and compose other installed
actions. Unlike returning a `changes` batch, separate `agora_native.call` writes
commit separately; a later exception does not undo earlier successful calls.
Do not mix direct writes with stale proposed changes from the original snapshot.
Candidate code receives no live bridge credential and should use the supplied
snapshot and returned changes for isolated tests. Installed programs share the
live guest's broad authority; this is not per-package isolation or attribution.

Skills are retained package files explicitly named in `manifest.skills`.
`skills.list` returns instructions from installed builds with package and
installation revision. JEFF can retrieve them through tools; the harness does
not automatically turn arbitrary files or notes into system instructions.
Skills guide action within the person's instructions and current authority.
Editing a skill takes effect through saving, building and installing its package.

The initial browser runtime accepts a self-contained HTML entry with inline
JavaScript/CSS. Its manifest uses `runtime: "browser-1"` and
`ui: {"entry": "index.html", "mount": "shell"}`. The mounted shell is the native
package `agora.shell`, including the desk and conversation panel. The host loads
its installed HTML into a sandboxed frame. Other browser packages can be stored;
there is not yet a general multi-application mounting system.

An authored frame requests native operations through
`parent.postMessage({agora:true, id, method, args}, '*')` and receives
`{agora:true, id, result}` or `{agora:true, id, error}`. Match responses by `id`
and verify `event.source === parent`. The host keeps the operator token outside
the frame and forwards only admitted operations. Use the existing shell's
request helper and `prepare-reload`/`reload-ready` handshake when changing it;
save drafts and pending edits before acknowledging replacement. Browser builds
only validate source/manifest shape. They do not test actual interactions.

Each Python package invocation is unpacked into a fresh temporary guest directory
which becomes its working directory and is removed afterward. Files written
relative to that directory are scratch data. For a persistent guest workspace,
use an explicit directory such as `/root/agora-work` through `guest.execute` or
authored guest code. Such files survive invocation cleanup but are independent
of native-world replay. Reusable code should be retained as native package source;
guest software installation currently changes the shared mutable machine.

## Current limits and a repeatable proof

- Native actions receive at most 1,000 objects, including runtime objects. A larger
  world is refused rather than silently supplied as a partial action snapshot.
- Packages hold 1–100 text source files, up to 1 MB per file and 2 MB in total,
  and at most 50 exported Python actions. Python build/action execution currently
  has a 30-second limit; `guest.execute` accepts a 1–120-second limit.
- There is no package dependency resolver, frozen guest environment, asset server
  or per-package permission isolation yet. Cross-package invocation can use the
  connected native client and `action.invoke`, but dependency resolution and
  automatic version pinning across such calls remain the package author's work.
- JEFF accepts one conversation turn at a time. Server execution is asynchronous
  so the interface remains responsive, but multiple concurrent agent tasks,
  persistent worker jobs and automatic notification-driven wakeups are not built.
- Conversation records and ordinary native collections persist. A separate witness
  memory system, durable facet bindings/dependency evaluation and autonomous
  worker agents are not implemented. They remain [[Native Development]] targets.

From the repository root, with dependencies installed, an existing account sign-in
and the live Linux VM running with a configured candidate yard, explicitly run:

```console
uv run python scripts/probe_authoring.py
```

This starts a **live Astra call** and executes its newly authored Python inside
the configured guest. It creates a new native world under `local/acceptance`, asks
JEFF to author the counter without supplying its implementation, checks a
candidate made no native writes, and checks two installed increments yield two
with valid replay. `--machine` selects the live machine configuration; `--yard`
selects the candidate configuration, defaulting to `yard.json` beside it.
`--output` selects a new evidence directory. Existing output directories are refused.

The command writes `trace.jsonl` and `report.json`, including ordinary provider
failure evidence. It does not start or replace a native bridge: installed actions
use the existing live guest while their proposed changes target the probe world.
A host sentinel is checked, and `guest.execute` is refused for this particular
proof; neither is a proof that arbitrary guest-root code is pure.
The existing runtime inventory test separately checks the actual Codex tool
surface using local simulated inference. Test evidence and live authorship
evidence should remain distinct.

## Chat activity snapshots

`chat.status` includes `activity: {id, started_at, messages, tool}`. Each message
has `{id, text, phase, complete}`; phase distinguishes commentary and final_answer.
Text is a complete bounded snapshot, not a delta the polling client must append.
`tool` is null or `{name, started_at, running}`; timestamps are Unix seconds.
A new request creates a new activity ID. Snapshots contain at most 100 messages
and one million text characters in total. They omit tool arguments/results.

While running, display commentary and streamed final text. After completion,
replace the streamed final with the durable conversation message. Retain current
commentary separately from final-answer history; snapshots are transient, cleared
on the next request or process restart. The diagnostic `events` tail is not a
reliable text stream. Raw reasoning is not part of this contract.
