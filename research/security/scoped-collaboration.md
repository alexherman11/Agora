# Scoped tools and collaborative applications

Working proposal · 31 August 2026 · Captures the two follow-on design discussions after the initial [Security Model](<C:/Projects/Agora/Security Model.md>).

This document extends the threat model; it does not adopt a protocol, select a runtime, or claim an experiment has succeeded. The current [object contract](<C:/Projects/Agora/Agora Objects.md>) remains broader than software creation: the same principles must work for documents, recordings, calendars, devices, and other ordinary OS subjects.

## 1. Four distinct decisions

Contributing an implementation, experimenting with it, adopting it, and granting authority are separate operations. A contributor can offer a useful change without becoming trusted to operate other people's computers. Receiving an application or a branch supplies code and requirements, not the sender's approvals, credentials, jobs, or access to objects.

Permissions attach to execution instances and precisely bounded standing policies. They are not an automatic property of having installed a package. An action descriptor states requirements; the protected authority service decides which requirements an actual invocation may satisfy.

The owner may preauthorize routine work. The design should not turn every local read, volume change, or tentative edit into a confirmation dialog. Extra deliberation belongs where the audience, affected resources, destructive power, persistence, or external consequences expand.

## 2. Scope an invocation to its actual work

For a user-selected trimming operation, a possible grant is:

| Dimension | Example boundary |
| --- | --- |
| Input | Video/audio content from a particular clip revision and selected interval |
| Other metadata | No private annotations, source conversation, unrelated tracks, or directory access |
| Output | A new private candidate clip with derivation provenance |
| Mutation | No overwrite of the original; a separate scoped commit can adopt an edit |
| Communication | No network, room messages, or calls to other agents |
| Retention | No plugin-controlled state surviving the invocation; retained results follow owner policy |
| Resources | Bounded compute, memory, output, and duration |

This constrains consequences, not artistic quality or truthfulness. A hostile trimmer can still produce a bad clip. A grant must be enforced by isolated execution and mediated resource access, not by trusting the description of the tool.

Use actual facet instances, content revisions, occurrence IDs, and subobject selectors where needed. “Edit this use of the recording” is not “edit every occurrence” or “modify the original recording.” A saved query is not a frozen set: define whether a grant applies to selected members or to an explicitly authorized dynamic view. A source path or familiar device address does not prove identity.

Prefer proposed changes over direct mutation when the task allows it. The commit operation checks affected identities, read dependencies, expected revisions, validity, and current authority. A valid content edit does not automatically authorize executable behavior that a reconciler could subsequently interpret.

Permission explanations should be generated from the enforced configuration by trusted UI. The package may explain why it wants access but may not supply the authoritative account of what it has. JEFF invokes the tool under the task's rights; untrusted results cannot enlarge them or borrow unrelated standing permissions.

## 3. Treat the whole workflow as a disclosure boundary

A private reader plus a public publisher can leak information even if each individual tool obeys its grant. Restrict the path between them.

Start conservatively: every output of an opaque computation may depend on everything that invocation could read. Preserve the relevant source restrictions on generated documents, code, images, logs, prompts, and cached results. The computation cannot declare its own output public. A wider release requires the relevant owner's authorization; one person cannot waive another source owner's restrictions merely because both inputs were readable.

Separate public retrieval, private analysis, and external publication when possible. A public fetcher can use the network but cannot inspect private inputs. The private analysis stage can combine selected private data with fetched material but cannot communicate externally. Publication is a separate authorized effect on a particular result and destination.

Network “read access” is still an output channel: a query, URL, or request timing can disclose information. Shared storage, plugin messages, and development telemetry can also carry results. Within one unrestricted process heap, module boundaries do not enforce confidentiality; use actual isolation where components are mutually untrusted.

These rules primarily constrain application data/control flows. They do not prove immunity to covert channels, sandbox defects, deceptive output, or a user manually publishing a result that conceals information. Minimize input access and make those limits explicit.

## 4. Universal version control needs several kinds of history

Patchwork explores live editing, lightweight branches, and organizing changes after the fact. That fluidity is useful for development. Retroactively moving executable changes to another branch cannot undo a disclosure that already happened. [Patchwork version-control notebook](https://www.inkandswitch.com/patchwork/notebook/2024-version-control/).

| History | Meaning of adopting a change |
| --- | --- |
| Application implementation, dependencies, adapters, schemas | Use this exact executable configuration. |
| User documents and application state | Incorporate these particular data changes. |
| Permissions and trust policy | Authorize these effects on these resources. |
| External-action record | Retain evidence of an attempt or outcome; never replay it as a command. |

These histories can share an interface and reference one another while obeying different merge, retention, and activation rules. Permission proposals may themselves branch, but checking out old policy does not restore its authority. Code adoption does not import another user's grants or dispatch effects accumulated during previews.

People can collaborate on shared data using different application configurations when their data/operation contracts remain compatible. A shared document does not imply a single mandatory interface version. Some changes to common invariants or formats will still need coordinated transition; version control cannot remove every need for agreement.

## 5. Combinations are new candidates

Consider a base application with only public research metadata. One contributor adds private annotations. Another independently generalizes export to serialize every field in a record. Each change may be reasonable in its original context; their clean textual merge may disclose annotations.

Evaluate the composed candidate rather than inheriting a blanket approval from its branches. Do not union branch permissions. Give the exporter only an authorized public projection so that additional private fields remain outside its input boundary. Compare the resulting resource/data-flow graph as well as source text.

A security comparison can reliably report enforced changes such as a newly reachable input, destination, handler, migration, or grant request. It cannot reliably prove every behavior of arbitrary code. AI explanations and test observations are evidence, not authorization or complete behavioral proofs.

Adopt exact executable dependency graphs, including adapters, schemas, migrations, generated code, and executable configuration. A dependency named “latest” must be resolved before the execution snapshot is accepted. Evidence identifies the configuration it examined. A merge, rebase, or dependency replacement creates a new configuration requiring assessment under the adopter's policy.

The Progressions experiment illustrates the maintenance cost of adapters that depend on implementation details: changing an underlying tool can invalidate its wrapper even when the change seems small. Pinning and compatibility matter for both behavior and security. [Progressions](https://www.inkandswitch.com/patchwork/notebook/progressions/).

Not every update requires a new human approval. A constrained declarative layout can follow edits live; an isolated preview can follow experimental code; a publisher can remain on a deliberately adopted version. Delegated release channels may operate within an owner's permission ceiling. Unchanged permissions bound damage but do not prove benevolent behavior within that ceiling. Arbitrary renderer code is executable, even when its author calls the change cosmetic.

## 6. Trying a version must isolate its consequences

A preview has an exact executable configuration, a chosen data branch/revision, bounded inputs, and a specific effect policy. A source-control branch alone is not a sandbox.

Private previews must not synchronize private-derived console logs, screenshots, fixtures, generated tests, branch descriptions, or errors to a development room. A contributor who may edit code does not thereby gain the right to observe executions on another person's private data. Share synthetic fixtures for collaborative tests; explicitly release selected private-derived artifacts only when appropriate.

Use test services or inspectable proposed effects for external integrations. Adopting an email implementation does not send messages emitted during its experiments. Restore and fork preserve current revocations and effect outcomes rather than copying usable leases.

Adopting code also must not replace collaborators' current data with the preview snapshot. Commit particular data changes with read/version preconditions and domain merge rules. Migrations need explicit compatibility and recovery semantics; restoring old code is not an inverse migration. Personal variants can coexist where contracts permit; incompatible writers must not silently damage data.

## 7. Distributed authority remains a research choice

The initial threat model's single authorization writer per room is one conservative starting option, not a requirement for all state. Keyhive explores causal access control, including disconnected collaboration and concurrent revocation. Evaluate those semantics and their verification requirements against Agora's intended operations. [Keyhive notebook](https://www.inkandswitch.com/keyhive/notebook/).

Offline development, accepting shared edits, enlarging permissions, and committing external effects have different requirements. No design can instantly notify a disconnected device or revoke already copied plaintext. State the chosen rules and failure behavior instead of treating either centralization or decentralization as a security proof.

## 8. Questions and experiments

The first investigation now has a [static composed-export model](<C:/Projects/Agora/research/security/composed-export-model.md>). It shows the dangerous clean merge, compares whole-application access with a capability-shaped public projection, separates owner archive from audience disclosure, and defines ten implementation cases. Its main conclusion is that a narrow argument is not a permission boundary: the exporter must be unable to reach the raw store or auxiliary output channels, the projection must be filtered before derivation, and the merged candidate must receive a freshly computed invocation plan rather than the union of branch grants. No Agora runtime test has been run.

The next investigation should trace private preview artifacts into collaborative development surfaces: logs, errors, screenshots, generated fixtures, summaries, caches, and synchronized worker messages. Use synthetic data and a fake publishing service when suitable isolation is available. Evaluate the actual boundaries, not only whether a reviewer spots malicious text.

Compare whole-application isolation with smaller independent components. Measure denied effects, unintended disclosure, retained user work, recovery, review effort, and user interruptions. More components may reduce authority per component but increase dependency and compatibility complexity.

Acceptance tests T21–T24 in [Security Model](<C:/Projects/Agora/Security Model.md>) cover the new scenarios. T25 extends the same precision to ordinary OS actions. None has been run against an Agora runtime. Compartment granularity, adoption policy, exact wire protocols, and confidentiality enforcement remain open.
