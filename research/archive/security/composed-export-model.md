# Composed export: a static security model

*Security investigation · 1 September 2026 · Static counterexample and proposed enforcement contract. This is not a runtime test and does not establish that Agora has implemented any of these controls.*

## Question

Can a private-annotation contribution and a generic-export contribution each be reasonable alone but disclose data when combined? Can narrow component inputs prevent that without making ordinary sharing painful?

Yes to both, with an important qualification: an input is narrow only when the runtime prevents the component from reaching anything else. A filtered function argument inside a process that can also read the object store, cache, logs, or ambient network is documentation, not a security boundary.

The simplest promising design is a **capability-shaped projection**. A public-output component receives a purpose- and destination-bound view containing only the facet instances it may disclose. It receives no ambient entity resolver, object-store handle, shared scratch directory, private log stream, or arbitrary network access. A separate broker mediates the final effect. Source restrictions remain attached to derived artifacts, and only a trusted release action can deliberately widen them.

## The counterexample

Use one synthetic photo object at a pinned revision:

| Facet instance | Value | Scope |
| --- | --- | --- |
| `image/main@3` | synthetic image bytes | shareable with `room:design` |
| `caption/en@2` | `Launch photo` | shareable with `room:design` |
| `annotation/alex@1` | `NIGHTJAR-7421` | Alex only |
| `summary/default@4` | derived from caption and annotation | Alex only, because it depends on both |

Two people develop independently:

- **Annotation branch:** adds private annotations and an editor. It needs read/write access to Alex's annotation instance and no publication channel.
- **Export branch:** generalizes an exporter by serializing every field returned by `loadRecord(photo)`. Against the old public-only record this is convenient and appears harmless. It can publish one artifact to `room:design`.

A textual merge can be clean while the effective authority graph gains this path:

```text
private annotation -> generic record loader -> exporter -> room:design
```

If the combined application inherits the union of branch permissions, the marker is disclosed. Neither contributor needed malicious code. Review and authorization attached to the two separate branches do not prove the merged configuration safe.

## Three designs compared

| Design | Direct marker disclosure | Main problem |
| --- | --- | --- |
| Whole application receives the complete object and a room publisher | Allowed | Private read and public write coexist in one compromise domain. |
| Export helper receives a filtered argument, but shares a process/store with the application | Accidentally absent in the friendly implementation | The helper or a compromised dependency can bypass the argument through ambient state or another in-process API. |
| Isolated exporter receives a broker-created public projection and one typed room-publication capability | Denied for the modeled direct flows | The projection builder, broker, labels, isolation, and auxiliary channels become trusted enforcement surfaces. |

Restricted inputs therefore prevent this class of disclosure only when all of the following hold:

1. **Filter before computation.** Construct the room projection from facets the destination may receive before summarization, rendering, search, or export. Do not compute over the private object and redact afterward.
2. **Default-exclude new fields.** A new or unknown facet does not join an audience projection merely because a generic serializer discovers it. Public/share profiles explicitly select facet contracts and instances.
3. **Propagate restrictions through derivation.** An artifact derived from several inputs starts with the intersection of their permitted audiences, or an equivalent conservative policy join. The producing package cannot relabel it public.
4. **Enforce reachability.** The exporter gets copied values or unforgeable read handles limited to the projection. A bare entity ID cannot be resolved into additional facets without another authorized broker call.
5. **Mediate every observable output.** The room message, upload, URL, log, error, shared fixture, screenshot, timing-sensitive callback, and retained cache are possible channels. High-assurance claims require isolation appropriate to the channels being excluded.
6. **Separate deliberate release.** Expanding an audience is a trusted operation bound to the exact artifact or selected facet instances, destination, revision policy, and retention meaning. It is not a method the exporter can call on itself.

## Export is two different operations

“Export everything” is useful for owner recovery and dangerous as a synonym for sharing. Agora should give these different contracts and capabilities:

| Operation | Inputs | Destination | Default |
| --- | --- | --- | --- |
| Owner archive | All material the owner is entitled to retain, plus an inclusion/omission manifest | Owner-controlled recovery target | Private; may contain private facets; never reusable as a public-share capability |
| Audience disclosure | Explicit frozen facet instances or an explicitly authorized live view | Named room, person, or external service | Exclude unknown/new facets; no history, edges, derivatives, or future matches unless selected |

This preserves usable exit without teaching every public exporter to enumerate the private world.

## What collaboration should version

Every executable candidate should have an effective invocation plan computed from its exact code and contract closure:

```text
candidate identity
  code, dependencies, adapters, schemas, migrations, executable configuration

invocation plan
  principal and executor
  readable entity/facet instances and revision selectors
  derivations and their source restrictions
  writable targets
  external effects, destinations, audience, and budgets
  available storage, logs, IPC, network, and other channels
```

The plan is enforced with broker-issued handles; a package manifest is only a request. When branches combine, Agora computes a new plan and a new resource/data-flow graph. It never unions standing grants from the branches. An existing *permission* decision may remain valid without another interruption when the enforced plan is a true subset of an already accepted plan and its versioned action meanings remain compatible. Software adoption still follows the configured publisher, update, and exact-version policy; a subset of authority does not prove new code correct or honest. A newly reachable path from a more restricted source to a wider destination requires a new release decision or must be removed.

This gives collaboration a useful review unit: show people newly reachable inputs, newly available outputs, changed contract meanings, and new paths between them. Source review still matters, but a diff of the enforced plan is more reliable than asking a person or model to infer every permission consequence from code. The plan over-approximates possible authority; it cannot detect a malicious behavioral change when one compartment already possesses both the sensitive input and the wider output.

## Static fixture and expected results

These cases define the first implementation test. They have not been executed here.

| Case | Candidate action | Expected result |
| --- | --- | --- |
| C1 — naive merge | Full record plus room publisher; export every field | Fail: `NIGHTJAR-7421` reaches the room. This is the counterexample. |
| C2 — public projection | Export only the broker's `room:design` projection | Pass: image and caption are present; annotation and its existence are absent. |
| C3 — new unknown facet | Add a new Alex-only field after export was approved | Pass: it is excluded by default and creates no new exporter-readable input. |
| C4 — private-derived summary | Request the existing summary in a room projection | Deny or regenerate only from room-permitted sources; never redact a private-derived string after generation. |
| C5 — resolver bypass | Exporter presents the photo ID to a generic resolver | Deny: its invocation has no raw-object read capability. |
| C6 — auxiliary channel | Exporter places the marker in an error, log, fixture, screenshot, cache, URL, or worker message | Deny or keep the channel within the source restriction; record which channels the isolation model does not cover. |
| C7 — owner archive | Owner requests a private recovery bundle | Permit inclusion of the annotation with a precise manifest; prevent reuse of that authority for room publication. |
| C8 — composition | Merge annotation and export branches | Treat as a new candidate; show the new private-to-room path under the naive plan and no such path under the projected plan. |
| C9 — two-run observation | Run twice with only the private marker changed | Public artifacts, broker requests, shared logs, errors, and visible state should be identical. This is useful evidence of non-interference, not a proof against all covert channels. |
| C10 — self-classification | The annotation facet or plugin labels itself public | Deny: only the protected policy service can widen readership. |

## Where user judgment remains necessary

The mechanism can prevent an exporter from reading a private annotation. It cannot decide every disclosure question:

- public facts can reveal something sensitive when combined, even if each was correctly labeled;
- a caption may itself contain private information due to a mistaken or outdated policy;
- a user may intentionally want to publish one private annotation, a redacted derivative, or a live changing view;
- recipient retention and onward copying cannot be undone after plaintext release;
- shared-hardware timing and other covert channels exceed what this static model establishes.

The trusted release surface should therefore ask for judgment only when widening disclosure or choosing ambiguous live/frozen semantics. Ordinary reads, private annotation, and repeated export to an already authorized audience should use standing narrow grants without repeated prompts.

## Decision from this investigation

Use capability-shaped, destination-specific projections as the default sharing primitive. Keep source labels and derivation lineage as defense in depth and for broker checks, but do not start by trying to retrofit perfect dynamic information-flow tracking across one large mutable application. Prevent private data from entering public-output compartments wherever possible.

Place a compartment boundary wherever two components need meaningfully different authority. It need not follow every module boundary. A component that legitimately needs both arbitrary private reads and arbitrary public writes belongs to one high-risk compromise domain and needs an explicit release step; splitting only its source files does not reduce that authority.

The current specifications already say to filter by viewer and destination before summarization, preserve source restrictions on derived summaries, version changed action meanings, and distinguish software adoption from data rollback. This model makes the missing enforcement consequence concrete: the projection builder and effect broker must be outside the authority of the code they constrain, and a composed application must receive a freshly computed invocation plan.

The related `derived_visibility` toy result in `research/object-facet-review` is compatible evidence for the prefiltering rule, but it is a small previously executed model. It does not test application isolation, ambient channels, branch composition, or Agora's future runtime.
