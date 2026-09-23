# R8: earn the foundation through cheaper subsequent changes

Research checkpoint, 2026-09-23. Proposals and comparative thought experiments, not an implemented protocol or a claim of optimality. No runtime or application changes made for this round.

## Orientation read before the comparison

Root and all three returning agents read the complete new drafts at `C:/Projects/Agora/docs/docs_2/Agora.md` and `Dynamic Desk.md`. They also read `Current Implementation.md`, which is an unfinished template and supplies no implementation evidence. `Agora Constitution.md` is empty. The drafts guide the research; their illustrative mechanisms remain revisable.

The new emphasis is consequential: ordinary computing must remain comfortable, small inventions should make later inventions easier, and people must be able to adopt part of someone else's work. A uniform framework should remain comprehensible to an individual. These requirements question R7's provisional preference for a facet-first substrate rather than merely adding features to it.

## What survives; what is reopened

Keep the desired experience: enduring things that can be named and examined, meaningful operations shared by human and agent, editable visual interpretations, contextual discovery, and ordinary object work that does not require visual wiring. Preserve the object/appearance/view distinction as a useful account of responsibility. Do not infer that it dictates one physical storage representation.

Reopen the implementation choice between durable facet-bearing records, live objects with replaceable behavior, and structured documents/resources exposing common protocols. Each could implement important parts of this experience. A strong document/plugin system can already provide commands, selection, undo, views and extensions; counting those capabilities again as a unique benefit of world facets would be a weak comparison.

Facets earn their place when independently useful information must survive, be examined or be reused outside its original application. They do not automatically make code reusable, define the meaning of an edit, preserve annotation anchors or produce interoperable applications.

## Small-picture criterion: a second useful change should cost less

The first pressure case is deliberately modest. Add a range-comment feature to one editor. Reuse it in another editor built around a genuinely different representation. Then add a second range-based tool. Count every provider, locator mapping, special case, lifecycle hook and host change. Also count the concepts and manual decisions exposed during normal use.

The interesting saving may appear on the second tool: its author reuses both existing providers. A single tool with one new adapter per app may merely relocate effort. If each tool requires a different adapter, the proposed shared protocol is not doing enough. If a competent plugin toolkit achieves the same result more simply, use that architecture as the foundation instead of adding a second framework around it.

Shared words are not sufficient evidence. `sort` can reuse one algorithm through comparison and collection protocols. `tile` can reuse layout calculation while asking the target to admit a placement. `comment` over immutable local annotations and a collaborative discussion system may denote different effects. One spelling cannot erase that difference.

## A second test: a rough plan becomes a workspace

Start with an informal note about a trip. Add dates, places, uncertainties and alternatives as needed. Show relevant items on a map or calendar; keep the reasoning beside the results. Change a date. Add another item. Change the visual arrangement. None of these ordinary actions should require recreating bindings or publishing a global schema.

Embark's authors report that earlier compositions of graphical widgets looked promising but failed to retain the planning thought process. Hosting tools within an outline worked better. The prototype nevertheless hardcoded views/functions, left schema interoperability largely unresolved and required manual repair of some concrete formula arguments after dates changed. It is evidence for gradual enrichment and a warning about bindings, not proof of an extensible desktop. [Primary report](https://www.inkandswitch.com/embark/)

Our hypothesis: a coherent working context is as important as universal object addressability. It can be a notebook, project, collection or application; the foundation need not make every context an outline. It must preserve informal content alongside structured references and views without requiring all text to acquire formal semantics.

Foundations sharpened this into continuity of authored context: adopting a capability should extend the working place without implicitly replacing or relocating its reasoning, references or unfinished work. Removing the new tool should leave that material usable there. Saving the old prose in an archive while replacing the active workspace is insufficient. Explicitly requested restructuring remains possible.

For example, a field named `due` can start as a local convention. Another tool must not silently treat it as a legally meaningful deadline merely because its shape is a date. Stronger interpretation becomes necessary when another consumer relies on it. That does not necessarily require a central registry; it does require an inspectable agreement about meaning.

## Keep visual work separate without making it disconnected

A small candidate mechanism is a reusable view definition with a query or target, declared projection inputs, default components, and stable occurrence identity. An appearance records which subject is being shown in which context plus local arrangement or overrides. Routine subject changes invalidate the relevant projection automatically. The visual workspace edits definitions and overrides; object work usually never sees them.

The useful question is not whether these records are called lenses, views or appearances. It is whether the system can answer: which thing is this, why is it visible, which rule supplies its position/style, and what would this edit affect?

Editing's concrete counterexample is a view query containing a copied date literal: the object date changes but the view still uses the old week. A useful binding records the stable source, its interpreted value, any transformation and whether to follow accepted changes or capture a value. Current selection is not an adequate persistent source. Defaults can establish the relationship once; ordinary object edits should not require repairing it.

Defaults should be strong enough that adding an item to a notebook works immediately. Rules and bindings should be inspectable enough that a surprising result can be corrected locally. Reordering a collection must not retarget an active draft merely because the renderer keyed rows by list position. Updating an object must not leave a stale view because a provider forgot to declare a dependency. Those are concrete obligations of the bridge.

Existing toolkit primitives can render those definitions. The aspiration is to stop writing bespoke JavaScript/CSS and event plumbing for every ordinary application change. A genuinely new interaction primitive may still require implementation once. Moving hidden custom code into an adapter does not satisfy the aspiration.

## Big-picture durability: survive disagreement and replacement

Twenty-year flexibility is not a large catalog of anticipated types. It is the ability to introduce a new interpretation without destroying the old material or requiring every participant to upgrade together.

Four useful pressures:

- **The original app disappears.** Retained content, identity and available descriptions support meaningful inspection or export. This cannot promise full editing of every obsolete format or restoration of unavailable external media.
- **Two communities diverge.** They share only the concepts and operations on which they agree. A schema converter cannot guarantee reconciliation of conflicting meanings. An explicit partial relationship can be more honest than a claimed universal migration.
- **One person replaces a feature.** A local toolbar or layout override should preserve unrelated upstream improvements. If the requested change crosses an editor's history/selection invariants, a larger fork may be necessary. The platform should expose that real boundary rather than pretend all features are separable.
- **A conventional native app joins.** Manage its resource/window and supported operations without claiming that its interior is native editable world data. This lets the desk remain useful while deeper integration is absent.

Ingalls's principles support uniform references, messages, modularity and reuse through behavior rather than representation. The article also says protocol consistency was not yet formalized. Its uniformity does not establish that every subject must share one data shape. [Primary article](https://archive.esug.org/HistoricalDocuments/Smalltalk80/DesignPrinciples/DesignPrinciples.html)

Longevity therefore depends on understandable replacement boundaries and recoverable material, not on declaring the first schema infinitely extensible. There is no evidence yet that any candidate is optimal.

## Reduce the visible machinery

Keep local invention cheap. Ordinary metadata need not begin with publication and version negotiations. A simple visual definition can have retained revisions and local overrides without a generalized dependency solver. Context can narrow useful verbs while inspection can reveal broader installed capabilities. A provider should be authored per real representation boundary, not per individual object.

Do not hide necessary semantics entirely: a current selection, historical annotation anchor, external side effect and pure read have different obligations. The task is to give good defaults and expose those distinctions when consequential, rather than force people to learn all of them before making a note.

## What would make us change course

Reject a candidate that repeatedly requires core changes for new ordinary applications, requires per-object presentation wiring, makes the second extension as expensive as the first, or preserves bytes while losing the meaning of routine edits. Reject a purported simpler baseline if it achieves simplicity by preventing independent reuse, external inspection or partial adoption.

The proposed discriminating experiment compares a competent document/plugin toolkit and a minimal world/protocol bridge under the same editor engines and command access. Use the two pressure cases above, one partial feature adoption and one incompatible app. Measure author work, repairs, host changes, manual bindings and real input continuity. These are proposed observations; this round did not run that experiment.

## Team process and evidence boundary

Foundations challenged the cost of facet-first assumptions and long-term schema agreement. Editing compared ordinary command traces against a strong conventional baseline. Media examined feature reuse, appearance defaults and interaction continuity. Each read the new documents, challenged peers and revised its position. Their separate notes retain counterarguments and source coverage.

R7 source findings remain a dated static checkpoint. This round adds design analysis and primary-source comparisons; it does not upgrade any earlier proposal to an installed or tested capability. The shared research task remains open.

The Dynamic Desk draft changed during the round. Root and all three agents reread the complete 5,779-byte version with SHA256 `5513206EA05472C9D9EEEB8AE273F2CB77F3D3956AF52BA5F54A8BA883AA6CC9`; each agent appended a reading receipt. Agora.md remained at SHA256 `044CA78C81DF5E07FAE12E9977B0DB42D5CE1F3AA5895121A477304218DD6F05`. No source drafts were edited by this team.

Shared-desk receipt: research task `bridge:a63` / subject `s62`, comment `c69`, event `e51`, posted through the normal `explore.py` verb interface as `astra-liaison`. The command succeeded and the task reported two comments afterward. This is a posting receipt, not evidence that Claude's team consumed it.
