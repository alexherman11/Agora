**Agora: a holistic assessment of the design, implementation, and path ahead**

Review date: September 4, 2026. Working tree based on `80a43dadd7220a61e49d67b999087286b17b9709`, branch `docs`.

**Agora has a credible central idea and a promising small implementation. Its largest risk is allowing the elegance of its explanation to substitute for evidence that the environment is useful, dependable, and easier to change.** I would continue the project. I would repair the current foundation, bring real use and comparative evaluation forward, and loosen several architectural commitments. I would not restart it or abandon the social ambition.

I understand the intention as a computing environment that belongs to its person: ordinary things persist independently of applications; the human and JEFF can refer to the same things; JEFF can reshape tools and surroundings when asked; useful work survives changing software and machines; and people can bring selected parts of their lives into shared places without surrendering their homes. The room is an important destination. The personal environment has to be worth inhabiting along the way.

The most compelling promise is continuity through change. The same document can acquire a better view without becoming a different document. A reference can survive an edit. A failed attempt can remain understandable. A shared object can have different personal views. A tool can disappear without taking its user's work with it. Those benefits matter even when JEFF is unavailable. They also give JEFF better material to reason with.

The least convincing promise is that making everything an object, placing a model beside it, and drawing one security boundary makes the hard integration problems largely disappear. It gives those problems a place to be addressed. It does not solve identity matching, safe execution, compatible schemas, conflicting intentions, trust, or social governance by itself.

**This assessment separates working behavior, demonstrated defects, and proposals.** I read the complete current design vault, current kernel and clients, tests, build contract, working instructions, and decision log. I also read the substantive current object, whole-OS, memory, and security research dossiers and the executable object counterexamples. Superseded documents were inspected for history; representative retired `attempt1/` code and tests were inspected for lessons. This is not a line-by-line re-audit of every archived implementation. Generated metadata, lockfiles, and illustrative datasets were inspected as supporting material, not treated as running systems.

I ran the current suite: **72 tests passed**, with one dependency deprecation warning. The existing 14 object-design counterexamples also passed under Python 3.12.10; they remain toy models, not production validation. Ruff's lint and format checks each flag the already-present comment at `kernel/store.py:116`; I left it unchanged. I added only this review and its disposable-world evidence harness. Existing edits in the decision log, design index, store, and security research were preserved.

No live model comparison, real browser attack, power-loss test, multi-device deployment, or room trial was performed. No personal worlds, credentials, or remote compute were used. The new [probe harness](<C:/Projects/Agora/research/holistic-review/review_probes.py>) and [recorded results](<C:/Projects/Agora/research/holistic-review/probe-results.json>) make the implementation findings reproducible. Several risks had already been identified statically in the [M1 security review](<C:/Projects/Agora/research/security/m1-choke-point-review.md>); this review supplies runtime evidence for several of them and considers the broader direction.

**The parts I would protect are concrete and unusually well aligned.**

- **Identity independent of presentation.** The newer object reference distinguishes subjects, occurrences, memberships, representations, and views carefully. Repeated queue entries and a single recording need different identities; two views of a document usually do not. That precision prevents real user-facing mistakes.
- **A shared action boundary.** Human controls and agent tools drawing on the same operations is a powerful constraint. Derived tools, instructive refusals, and explicit provenance can make an agent both more capable and easier to understand.
- **Replay as an executable obligation.** Keeping a recoverable record and testing reconstruction is much stronger than merely saying that the system has history. Pure replay must remain separate from external execution.
- **Projection as evidence selection.** Giving both the human and JEFF attributed facts, including uncertainty and omissions, is better than maintaining unrelated interpretations for each client. Selection should remain inspectable and purpose-sensitive.
- **Desired state separated from observations and irreversible operations.** The revised reference material is particularly good here. A requested server, a server last observed running, and a submitted payment are different kinds of information.
- **A small JEFF implementation.** The current agent loop is readable and replaceable. Keeping elaborate planning and memory scaffolding out of it helps reveal what the environment contributes.
- **Real exit and model-independent use as product requirements.** Export, generic inspection, retained content, replaceable providers, and ordinary controls belong in the earliest useful experience.
- **Rooms as company and shared place.** The strongest social insight is the persistent corner of a world that two people make their own. Preserve that motivation alongside collaboration and civic aspirations.

The M1 restart made the active implementation small enough to reason about. That was useful. The earlier attempt also contains lessons worth retaining: an application lock, conditional updates, richer event linkage, and tests for stale writes. Recover the invariants when needed; do not restore the whole implementation merely because it already existed.

**The current green suite does not yet justify trusting the foundational guarantees.** The following findings come from the checked-out implementation. “Repair now” means before using it for work whose loss would matter, not that the prototype needs production infrastructure immediately.

| Priority | Finding and evidence | Smallest useful response |
|---|---|---|
| Repair now | **Concurrent store reads can violate replay equality.** Two `sync()` calls can read the same cursor and both apply the same event. The probe schedules that legal interleaving, then serializes the actual SQL applications: one logged event produces cached facet revision 2, while rebuild produces revision 1. See [store.py:41](<C:/Projects/Agora/kernel/store.py:41>) and [store.py:124](<C:/Projects/Agora/kernel/store.py:124>). | Serialize the cursor-read/application operation, make replay application reject duplicates, and define ownership of the world writer. Separate reads should observe coherent snapshots. Account for CLI and shell processes as well as threads. |
| Repair now | **Text edits can be silently lost.** Two `TextDoc` instances open the same revision. One prepends `A `; the other appends ` B`. After both flush, only the second edit remains. Replay agrees with the loss. See [text.py:111](<C:/Projects/Agora/kernel/text.py:111>) and [verbs.py:52](<C:/Projects/Agora/kernel/verbs.py:52>). | Initially enforce a single editing session or reject stale flushes with an expected revision. For actual concurrent editing, preserve and merge CRDT history through an authorized text operation. Full snapshot replacement is not collaborative text semantics. |
| Repair now | **Anchors can fail after an ordinary reopen.** Create an anchor in a new plain-text facet without first editing it, close, reopen, resolve: the native library raises `BaseException` because the cursor's IDs were never persisted. Replacing text through plain `attach` can produce the same failure for an older anchor. See [text.py:58](<C:/Projects/Agora/kernel/text.py:58>), [text.py:132](<C:/Projects/Agora/kernel/text.py:132>), and [text.py:147](<C:/Projects/Agora/kernel/text.py:147>). | Persist the text identity/history needed by an exported anchor. Define replacement separately from CRDT editing. Unresolvable positions must return an explicit historical result through the wrapper. Do not solve this with a blanket catch of every `BaseException`. |
| Repair now | **An accepted scene can make perception unusable.** Placing the desk inside itself is accepted. Both the desk tree and JEFF's projection then raise `RecursionError`. See [verbs.py:83](<C:/Projects/Agora/kernel/verbs.py:83>), [project.py:47](<C:/Projects/Agora/kernel/project.py:47>), and [scene.py:20](<C:/Projects/Agora/kernel/scene.py:20>). | Bound traversal and render repeated references explicitly. Decide whether containment cycles are legal, then validate through both `place` and generic scene attachment. Ordinary reference graphs need not be globally acyclic. |
| Repair now | **Recovery can silently discard acknowledged history.** A malformed complete middle line is skipped without an error; rebuild then differs from the previously materialized state. A torn multibyte UTF-8 tail instead fails before torn-line recovery runs. See [events.py:82](<C:/Projects/Agora/kernel/events.py:82>). | Parse complete records at byte boundaries. Distinguish a recoverable incomplete tail from corruption in committed history. Stop with an instructive recovery error rather than pretending a damaged middle record never existed. Validate event versions and required structure. |
| Before personal or untrusted input | **The shell trusts claimed actors and accepts an unauthenticated mutation request.** A TestClient POST carrying `Origin: https://example.invalid`, `Content-Type: text/plain`, and actor `claimed-owner` returned 200 and recorded that actor. This verifies server behavior, not browser exploitability. See [server.py:56](<C:/Projects/Agora/shell/server.py:56>). | Bind actor identity to a server-established session. Add appropriate origin/host checks and authenticated mutation handling. Loopback binding is useful, but the request body cannot authenticate its author. |
| Before personal or untrusted input | **Imports read arbitrary host paths before the authorization stubs and before all validation has succeeded.** A later-invalid mint leaves an imported blob behind. A text path import accepts 1,000,001 characters despite the one-million-character text limit. See [verbs.py:39](<C:/Projects/Agora/kernel/verbs.py:39>) and [verbs.py:179](<C:/Projects/Agora/kernel/verbs.py:179>). | Authorize a bounded import source before opening it, enforce size while reading, validate the resolved body, then commit. Stage effects so refusal does not leave durable imported content behind. |
| Before broader use | **A refused `place` can still mutate the world.** On an uninitialized desk, invalid mode creates the desk and then raises an error. One event was added. See [verbs.py:94](<C:/Projects/Agora/kernel/verbs.py:94>). | Perform validation before initialization that writes, or make explicit initialization a separate operation. The failure invariant must include the empty-world case. |
| Before broader use | **The stated projection budget is not the final rendered budget.** At budget 12 the probe produces 18 tokens under the implementation's own estimator after omissions and separators are included. A valid 100-character name can render an empty icon label. See [project.py:47](<C:/Projects/Agora/kernel/project.py:47>) and [project.py:82](<C:/Projects/Agora/kernel/project.py:82>). | Budget the complete representation, reserve an identity/qualification envelope, and provide a useful label fallback. This finding does not depend on which model tokenizer is ultimately chosen. |
| Before a growing daily world | **A no-op store synchronization still reads the full event log.** In the probe, each of two no-op syncs reads all 5,209 characters of a 30-event log. Projection performs many store reads, and the change stream polls repeatedly. See [events.py:82](<C:/Projects/Agora/kernel/events.py:82>) and [server.py:94](<C:/Projects/Agora/shell/server.py:94>). | Track a validated byte position, synchronize once per coherent read, and invalidate projections by revision. Measure actual bytes read and latency. This is separate from the deliberately deferred incremental render-tree feature. |

SQLite serializing individual API calls does not make a sequence of application operations atomic. Its documented threading guarantees concern calls on connection objects; the probe deliberately avoids relying on simultaneous SQL execution. The current comment claiming that synchronization plus SQLite serialization makes the shared handle safe is therefore too strong. [SQLite threading documentation](https://www.sqlite.org/threadsafe.html).

There are additional static concerns to address alongside those repairs. The shell dispatches concurrent chat requests into one agent's mutable history. That needs a simple queue or session boundary and cancellation semantics. Malformed tool input does not consistently become an instructive refusal: some shapes reach attribute access or file/native-library errors that the agent does not handle. Blob staging uses a shared digest-based temporary filename, and log append has no world-level writer protocol. Those are reasons for focused interleaving and fault-injection checks, not evidence that every possible failure was reproduced here.

The comment already present at [store.py:116](<C:/Projects/Agora/kernel/store.py:116>) asks a valid question. When a file destination is supplied, `rebuild()` removes it before the replacement has succeeded. Build and validate a sibling replacement, then switch it into use, preserving the prior copy on failure. The default in-memory rebuild does not have that destructive behavior.

The tests should be extended where a different execution path invalidates the stated invariant. Current anchor tests reopen after an edit has caused persistence. Atomic tests initialize the desk first. Projection tests count selected facts rather than all rendered text. Replay tests cover ordinary order and an ASCII torn tail, while the “tail” test checks applied events rather than bytes read. These are understandable early omissions. They also explain why 72 passing tests and several foundational failures can coexist.

I would not add tests for every implementation detail. Add invariants for duplicate application, stale edits, reopen-without-edit, bounded cyclic references, failed initialization, and corruption classification. Then exercise acknowledged operations across injected failures. Correctness under a sequential happy path is a useful start; recovery and concurrency are central claims here.

**Some of the most useful simplification is in the rules, rather than in the code.**

The three axioms are excellent design pressures, but their literal wording will eventually cause friction:

| Current pressure | Preserve | Relax or clarify |
|---|---|---|
| Events are the truth; everything else is a cache | Reconstruct accepted durable state from retained evidence. | The record proves what was recorded, not that a claim was true or a remote effect happened. Recovery also needs referenced payloads and compatible reducers. Live observations, external files, and disposable indexes have different authority. |
| One write path | One enforceable command protocol, validation policy, and audit boundary. | This need not remain one Python file forever. Pure helpers and domain handlers can sit behind the same gateway. A second unguarded route is the failure; a second source file is not. |
| JEFF is a client | No privileged implementation shortcuts, and explicit capabilities. | The normal client can have powerful, scoped build/file/runtime adapters. Denying it necessary tools does not make the experiment more scientific. Conversely, later granting world-root changes the security claim. |
| Tiny modules and four verbs | Small understandable responsibilities and deliberate scope. | Line limits are useful warnings, not a correctness metric. Four generic verbs are an experiment, not a universal user interface. A semantically necessary text edit, conditional update, or grouped operation can reduce complexity even while adding an API. |
| Additive schema forever | Old data stays recoverable and changes are explicit. | Define versioned interpretation and compatibility, including deliberate refusal by an older client. Preserving bytes is different from safely operating on unknown semantics. |

The event-sourcing commitment also does not require a hand-built JSONL storage engine forever. Keeping the present log is reasonable while it stays simple. If locking, framing, indexing, and recovery become a disproportionate burden, compare it with a transactionally stored immutable event table and explicit portable exports. Either can preserve event truth and one command boundary. This is a future tradeoff to measure, not a recommendation to rewrite M1 now.

Make the durability promise precise. A user-facing “saved” indication must correspond to recoverable work. Human activity history can group a burst even if recovery data is persisted more frequently. The requirement not to log keystrokes as human events should not prevent a separate crash-recovery mechanism. Similarly, fresh runtime observations can be a volatile layer with explicit validity; they need not be silently written into supposedly replay-derived durable tables.

The present file import also needs honest terminology. My probe edited an imported `core.text` facet and found the original source and captured blob unchanged. That is a useful imported snapshot. It is not a live two-way file binding. The later object reference already distinguishes native, external-file, and remote authority. Carry that distinction into the actual API and labels before adding watchers or writeback.

**The root/client choice needs resolution before self-modification grows around it.**

M1 gives JEFF a deliberately narrow client interface. The Security Addendum later gives JEFF root over objects, the world log, applications, workers, and its memory, while protecting outward effects at a host boundary. These are different trust models. They can both be legitimate experiments, but they do not support the same assurances.

Under the latter model, a world-root daemon can alter internal evidence, bypass internal facet policies, read internal private material, and change the code that presents internal results. An external broker can still protect credentials, host resources, spending ceilings, and independently recorded crossings. It cannot infer that data is safe to publish merely because the daemon labeled it public. Once the same compromised process can read private information and use an allowed outbound channel, destination limits alone do not establish confidentiality.

The existing [scoped-collaboration research](<C:/Projects/Agora/research/security/scoped-collaboration.md>) and [composed-export model](<C:/Projects/Agora/research/security/composed-export-model.md>) explain this well: safety has to survive the entire workflow. A private reader plus a permitted publisher can leak, even if each individual tool has a narrow schema. Private preview logs, errors, generated code, and screenshots can also carry information into a shared artifact.

My preferred direction is a capable ordinary JEFF with mediated access to the live world, plus broad freedom inside disposable development candidates. Protect the minimal journal, authenticated identity, current authority, and effect receipts from code being developed inside those candidates. Give JEFF enough scoped file/build/test capabilities to do real work; keep their boundaries enforceable. This does not require reviving all seven earlier compartments. Define boundaries from actual secrets, mutation rights, and output destinations.

If world-root remains the preferred experiment, state the weaker promise plainly: internal integrity relies on JEFF and world code being trusted; the host boundary constrains specified external effects. Do not simultaneously advertise internal records or private overlays as protected against that same root authority.

Also separate attribution from instruction authority. [jeff/context.py:24](<C:/Projects/Agora/jeff/context.py:24>) interpolates the desk directly into the system prompt. Imported names and descriptions remain data even when JEFF imported them itself. Keep source content in a clearly separated data/tool context and retain its source lineage rather than treating the last writer as the entire provenance story. That improves prompt discipline; it does not prove resistance to injection. Actual action boundaries must still hold when the model follows a bad suggestion.

Trust should not be one global ranking. Who authored a statement, whether it is a verified observation, who may read it, and what action it authorizes are independent questions. Two private rooms do not fit neatly into one low-to-high privacy ladder. Audience sets and destination-specific projections are a better starting point than a scalar “trust level.”

**JEFF changing the environment should become an early, small, complete experience.**

The current four verbs cannot demonstrate most of the intended malleability. They can create data and place it. They cannot yet build a useful new lens, wire controls, install behavior, or prove that a changed environment remains usable after restarting. That is an intentional M1 limit. The next demonstration should cross it deliberately.

For example: “Make my notes readable as a compact list, with a preview when I select one.” JEFF should inspect existing objects and available views, reuse a suitable component if possible, create a bounded candidate if necessary, show the working result, and install it within the authority already granted by the request. Existing notes retain their identities and history. The person can adjust it, undo the installation, reopen tomorrow, or keep working with the model disabled. A second request should modify the same view successfully without a developer rescuing the repository.

That loop has several kinds of change with different costs:

| Requested change | Sensible default |
|---|---|
| Layout, theme, bindings, filters over existing controls | Ordinary reversible data edits. |
| A personal lens using an existing sandbox and capabilities | Generate minimal metadata and checks, preview it, and adopt within the user's standing authorization. |
| New executable behavior or a data migration | A bounded candidate, explicit preconditions, resource limits, and a tested recovery path. |
| New access, publication, spending, or physical effect beyond current authority | Show the concrete additional authority and obtain it before acting. |
| Sharing or standardizing a reusable package | Signed/pinned artifacts, compatibility fixtures, dependencies, maintenance expectations, and an explicit release decision. |

The Extensions reference already distinguishes ordinary writes from vocabulary changes. Its remaining burden is too high for a one-off lens: registry search, rationale templates, candidate conformance, and human approval at local admission. That can be useful packaging machinery, but most of it should be generated or deferred until reuse. Requiring the user to approve every harmless local capability change also conflicts with the Addendum's generous standing delegation. An explicit request to make a concrete view should normally authorize that view within the current boundaries.

Separate code adoption, data migration, and authority expansion. A code rollback does not undo an external effect, and restoring older software must not silently restore old data over current work. A candidate evaluated against revision 12 should not overwrite revision 14 because its screenshot looked good. These are compact, valuable contracts for the self-modification loop.

Do not force ordinary development through a novel substitute for every file tool. A confined project adapter can expose builds, tests, patches, and artifacts through the same command boundary while retaining conventional source files and version control. That lets the experiment test whether object context and continuity help JEFF, rather than whether it can survive artificial deprivation of normal engineering tools.

**The first useful shell is part of the evidence, not decoration to add after the evidence.**

The current shell is intentionally a thin demonstration. It renders nodes and sends chat, but it does not provide the reading, selection, editing, or recovery experience needed to judge the larger project. “The shell never interprets” should prohibit hidden domain rules, not eliminate interaction design. Keyboard focus, selection, spatial layout, accessibility, and clear feedback are necessary client responsibilities.

Build a stable default place with a readable inspector or document view, ordinary navigation, direct edits, obvious selection, and visible results of JEFF's actions. Show what JEFF is working on, and provide stop/cancel. The user should be able to continue when the provider is slow or unavailable. Starting from a blank world should be a choice; otherwise the user must become a platform designer before getting any value.

Retain stable spatial arrangements while attention changes. Let salience influence suggested context, emphasis, or a separate attention list. If the desk itself constantly rearranges around a heat score, it can destroy the spatial memory that makes a place useful. Pins, recent explicit attention, active operations, and the current selection are enough to start. Attention, execution budget, retention, and urgency should remain separate.

The shared selection principle should also permit different purposes. A visual label, a screen-reader description, a document body, and an agent's action context have different needs. Use one policy for access and evidence selection, with purpose-sensitive results and an immutable identity/qualification envelope. A twelve-token label should not determine whether JEFF can find an object at all.

Keep reference-based M1 navigation as a deliberate test condition. Its absence of global listing is not a bug. Once ordinary use requires search, add a deterministic, scoped discovery capability through the same public interface, informed by recorded friction. Making useful objects invisible to preserve a four-tool count would weaken the eventual environment.

The human does not need to learn “cast,” “stamp,” “residency,” and “projection” before performing familiar actions. Preserve precise internal semantics, then present context-appropriate language such as “share this version,” “share live updates,” “make a separate copy,” and “open the original.” Complexity can be represented precisely without being exposed at every interaction.

**The decisive experiment should happen before Agora accumulates the full proposed spine.**

The roadmap says M1 exists to test whether the object environment makes the same model more capable than a filesystem. Its acceptance script establishes plumbing, while the comparative “brutal test” appears after reconcilers, host brokers, root access, and a security drill. That sequencing risks spending months building the explanation before testing its distinctive benefit. See [Agora Spec §22](<C:/Projects/Agora/docs/Agora Spec.md:453>) and [the scripted acceptance test](<C:/Projects/Agora/tests/test_acceptance.py:23>).

The fake client is appropriate for deterministic integration tests. It is not evidence that a real model understood an unfamiliar environment, resolved a reference, or outperformed a competent alternative. The acceptance test also does not simulate killing all processes at arbitrary points. Keep it, but state what it establishes.

I would start with roughly a dozen small tasks spanning ordinary use, continuity, and malleability. This is a suggested initial experiment size, not a statistical sufficiency claim. Include importing and reopening notes; changing a name without losing a reference; resuming at a highlighted passage; using the same media item twice in a queue; correcting an old interpretation; recovering interrupted work; and making then revising a personal view. Avoid spending another month designing a comprehensive benchmark before running the first comparison.

Compare three conditions:

1. Deterministic Agora controls with the model unavailable, to establish the substrate's own value.
2. The same model using a competent conventional environment: normal file/search/build tools, persistent notes, and ordinary task history.
3. Object-aware JEFF with the same source material, comparable authority, and the same model and resource budget.

The conventional baseline should be strong. If Agora receives carefully structured relationships that nobody supplies to the baseline, measure the cost of producing and maintaining them and separate that benefit from the runtime interface. If a simple textual index with stable IDs performs equally well, that is valuable evidence about which part of Agora matters. Do not give only JEFF extra hidden instructions, task-specific schemas, or manually repaired state.

Record completion, wrong-target actions, lost work, unnecessary questions, recovery effort, latency, model cost, and the human's repair time. Count setup and ongoing annotation as costs. Evaluate the actual resulting world, not just a model judge's opinion of JEFF's explanation. Repeat representative tasks, keep some tasks out of development, and record failures instead of retuning the test around them.

Set the desired improvement before the run. The aim is a meaningful reduction in effort or mistakes at acceptable cost, not a claim that every object-aware task must beat every file task. A result might show that explicit references and inspectable history account for most of the gain, while graph reasoning adds little. That would support simplifying the implementation, not abandoning continuity.

Everyday breadth matters, but it should arrive as small contrasting examples. A reader, a queue, and one simulated external operation will expose different semantic pressures. A coding demo alone cannot validate a whole computing environment. Conversely, implementing complete mail, calendar, browser, and media applications before learning from those examples would be excessive.

**Memory should begin by helping JEFF resume correctly, with evidence the person can inspect.**

The newer [operating-system memory proposal](<C:/Projects/Agora/research/graph-memory/operating-system-memory.md>) moves in the right direction. It asks whether memory opens the right object, passage, occurrence, or working state. That is more useful than merely making JEFF sound as though it remembers. The [evaluation plan](<C:/Projects/Agora/research/graph-memory/evaluation.md>) also correctly separates native links, inferred links, retrieval, and summaries.

Start with explicit references, recent meaningful operations, user pins, source-backed briefings, and ordinary lexical retrieval. Preserve native relations that tools already know: this output came from these inputs at these revisions; this highlight refers to this passage; this failed operation had this observed result. They are cheaper and more reliable than having a model rediscover the relationships from prose later.

Then test whether inferred associations improve a task. Keep the inference distinct from its evidence, with a way to correct or retract it. Do not build a dedicated graph engine, elaborate spreading activation, continuous consolidation, or personal model training merely because these fit the witness metaphor. The research does not establish that any of them is necessary for Agora. A graph can be a useful representation without requiring a graph database or a graph-based retrieval algorithm for every question.

Memory surviving a world restore is useful only if it remembers which branch and revision an experience belonged to. “That object failed” and “that version failed under those conditions” are very different memories. A record that a restored future once existed should not silently make its observations current. Retraction, expiry, privacy, and deletion must affect downstream summaries and indexes too.

Keep personal erasable memory out of trained weights initially. User-visible memory records make correction, export, provider replacement, and selective forgetting much more tractable. A persistent personality can provide continuity, but it should not make factual disagreement uncorrectable or make the person dependent on one model vendor. Give the user a clear distinction between remembered evidence, inferred preferences, and JEFF's current judgment.

Background cognition also needs economics. A tiny task that causes repeated summaries, graph maintenance, embeddings, and reflection can become more expensive than the work it supports. Measure usefulness per background action. Let explicit budgets, cancellation, and quiet periods stop work; do not make low salience the only way a process ends.

**Use reconcilers where convergence is the real problem, and keep ordinary computation ordinary.**

The spec/status split is worth keeping. It prevents a requested process from masquerading as a running process, and it gives restarted resources an honest path back to useful state. Freshness, incarnation, bounded retries, and explicit unknown outcomes are strong requirements.

The reference overextends the uniform mechanism, though. It says a reconciler writes exactly one status family and nothing else, then describes conflict creation, derived index updates, collection membership, lifecycle proposals, and system-authority salience. It also excludes freshness refreshes from events while the broader design calls every durable table replay-derived. These can be reconciled, but they need a stated model rather than exceptions hidden in implementations. See [Reconcilers](<C:/Projects/Agora/docs/Reference/Reconcilers.md:83>).

Separate three responsibilities: a controller manages an external or long-lived resource; a pure derivation computes a cache; and a command proposes or commits a durable state change. They can share scheduling and observation infrastructure without all pretending to be the same object lifecycle. A runtime helper can own conflict records if controllers are truly restricted to status. Volatile freshness can live outside durable replay state. Keep dependency graphs for triggering separate from the actual scheduling/ownership policy when necessary.

For scarce resources, prefer a clear current owner and an understandable waiting or refusal policy. Turning every competing headphone or port request into a conflict entity that stops both parties can punish the person already using the resource and provide an easy denial-of-service path. Conflict objects are valuable for ambiguity that deserves inspection. They should not replace basic resource arbitration.

Starting a process idempotently does not make the program's internal behavior idempotent. A restarted process can send an email or repeat a purchase. The receiving broker must check each effect, including its current authority, operation identity, and arguments. A controller that notices revocation “on the next pass” cannot be the only protection if the pass is blocked or stale work is already running.

For JEFF workers, begin with a small task record: target and input revisions, allowed operations and outputs, state, budget, cancellation, and a completion receipt. Reject stale completion that would overwrite newer work. That provides practical reliability without introducing an independent planning or memory framework for every worker.

**The web should expose its real uncertainty instead of inheriting reassuring labels.**

The page/cast/anchor distinction is useful, as is treating the provider as authoritative for remote facts. Existing browsers and adapters can carry much of the implementation burden. A new browser engine or comprehensive replacement application is not needed to establish the object model's value.

The `page.fill` proposal is safe as written only if it really edits a separate local draft. Filling the actual live page through CDP or simulated typing can invoke page code that observes values and sends them elsewhere. Likewise, following a link crosses a network boundary even if its primary user-facing role is navigation. MDN documents the input events that live controls expose; the confidentiality consequence here is an inference about arbitrary page handlers. [MDN input-event documentation](https://developer.mozilla.org/en-US/docs/Web/API/Element/input_event).

Make that separation explicit in the adapter contract. Prepare values privately; dispatch to a live page only within the appropriate disclosure authority. An effect class should describe multiple relevant properties where necessary, rather than forcing every operation into one exclusive enum. “View” does not imply offline, and “local process” does not imply no network effects.

The promise that a double-submitted order cannot happen is too strong. Agora can prevent specified automatic retries, bind one operation ID to frozen arguments, and report an uncertain outcome. It cannot make an arbitrary website deduplicate requests simply by assigning a local ID. Nor can it infer whether two separately requested submissions were intended as one. Provider support and explicit verification determine the remaining guarantee. The object reference and earlier counterexamples are already more careful on this point than the web prose.

Also distinguish provider resource identity from connection identity. The web/MCP mapping proposes a resource incarnation from the server session. A server reconnect should not by itself make a persistent remote issue or document a new resource. Record adapter/session observations separately and use the provider's durable identity and version semantics where available.

For publishing, make “working version” and “published version” explicit. A collection can be the authoritative working source while a selected, pinned release controls what outsiders see. This preserves malleability without making each private edit immediately public or requiring a separate opaque CMS.

**Rooms should prove shared presence and selective sharing before they attempt a society.**

The emotional motivation in the Rooms essay is stronger than some of its technical claims. A persistent shelf, familiar surroundings, an unfinished shared object, and the option to work quietly near somebody are a coherent product. That deserves direct testing. It should not be swallowed by task assignment, agent coordination, or productivity metrics.

Start with two people, a small shared surface, one shared document or artifact, separate personal views, a deliberate way to point something out, and optional presence. Test whether they actually return to it and miss it when it is absent. A centrally served prototype can test this experience before offline replication exists, provided its privacy and availability limits are explicit. The eventual protocol can be more ambitious.

Presence needs more care than hiding document text. Repeated signals about attention, activity times, applications, or who is present can reveal intimate information even without content. Make presence voluntary, coarse by default, and easy to pause. Do not infer that a relationship, household, class, or workplace is a permanently trusting group. Do not make “on entering the room” automatically activate a microphone, camera, or other physical device merely because an old room configuration said so.

There are at least three user intentions behind bringing something into a room: sharing one version, sharing future updates to selected material, and letting other people edit. Present those choices through familiar controls, and ensure the implementation does not casually share private overlays, history, linked content, or derivative summaries along with the visible item.

Your private JEFF knowing your life is not a reason for a room agent to receive the same context. A useful default is a room execution context that sees only room-authorized inputs. The private assistant can prepare a proposed contribution locally, then send a specifically selected output. That boundary needs to cover generated artifacts and diagnostic output, not just tool arguments. This is where the composed-export research becomes a product requirement.

Build leaving, blocking, ownership transfer where appropriate, and understandable retention before broad invitations. The right to fork is important, but a usable copy does not transfer friendships, continuing participation, or the right to retain everybody else's private history. Dissolving a room cannot guarantee both universal erasure and an unlimited full-history fork for every former member.

The docs already acknowledge the erasure/record/fork conflict. The remaining work is to choose a policy users can understand: what another participant receives, what they may keep, what controlled replicas remove, and what cannot be recalled from someone else's copy. Modern group protocols can exclude a removed member from new group secrets; that is different from forcing a recipient to forget previously obtained information. [MLS, RFC 9420](https://www.rfc-editor.org/rfc/rfc9420.html).

Avoid making all sharing depend on solving universal identity, human census, democratic delegation, or federated governance. Trusted invitations with clear recovery and membership semantics are enough for the first room. Public communities will need moderation, abuse handling, rate limits, and appeals; a pleasant household room will not validate those requirements.

**Multiple devices introduce a protocol, not just another place to copy the world directory.**

There is a useful distinction between one logical authority and one physical copy. Agora can retain stable object identity and a canonical interpretation while storing replicas. It cannot keep assuming one local JSONL sequence is a sufficient synchronization protocol for offline writers, different versions, and partially shared histories.

The following progression keeps the questions separable:

| Situation | What must become explicit |
|---|---|
| One person, one device, several local clients | Serialized mutation, coherent reads, conditional writes, crash recovery. |
| One person, two devices | Device identity, enrollment/revocation, offline proposals, conflict presentation, encrypted transfer, selective content, lost-device recovery. |
| Two people sharing selected objects | Membership authority, private overlays, audience-filtered projections, causal authorship, retention, and revocation limits. |
| A room with shared execution | Ownership and fencing for resources; one responsible executor for a particular external effect. |
| Independent hosts or federation | Version negotiation, abuse boundaries, invitations and identity across operators, resource quotas, failure handling, and exit from an unavailable host. |

Text convergence does not establish validity for coupled constraints, permission changes, or external actions. Use merge where independent edits genuinely compose; use conditional proposals, transactions, or a designated authority where an invariant requires coordination. Offline devices can continue many content edits while presenting authority-sensitive operations as pending until revalidated. That is a more honest experience than pretending every action can be equally available offline.

Do not impose one global total order over every home and room. Local histories, shared-object causality, and coordinated effect authorities can have different scopes. Establish world-qualified references and branch/version interpretation before real sharing; there is no need to freeze a universal protocol now.

A “lend” also needs an availability contract. If a room merely holds a live reference to an object on a sleeping laptop, the item may be unavailable. Choose explicitly between local cached copies, a reachable custodian, and a reference that can show stale/offline state. Avoid quietly turning the relay into the sole indispensable authority while advertising independent homes.

Phones and constrained devices should be able to hold selected data and run useful views without cloning every process or the entire VM. A desktop or service can own a long-running job; the phone can inspect its observed status and issue authorized requests. Device differences include input, accessibility, battery, background execution, and intermittency. A renderer-independent model helps, but VR or mobile interaction is not merely a coordinate transform.

Local-first research is a relevant precedent because it explicitly places ownership, offline work, and collaboration together and discusses their tradeoffs. It supports Agora's direction; it does not validate Agora's as-yet-unbuilt synchronization or authority protocol. [Ink & Switch, Local-first software](https://www.inkandswitch.com/essay/local-first/).

Before calling distribution real, perform a clean-machine recovery with the original host, registry, and model provider unavailable. Reconstruct useful content, references, required schema information, and fallback views from the export. Test selective sharing as well as whole-world backup. Retained blobs, encryption keys, decoder versions, and ownership records matter as much as the event file.

**Governance and ownership should support the product without freezing its mechanisms prematurely.**

The Constitution's values give the project a reason to exist: individual agency, exit, non-extractive incentives, and constraints on founders and hosts. Preserve those commitments. The draft's exact institutional mechanisms, numerical thresholds, and technical entrenchments need more room to evolve than the rights themselves.

Treating every change to a `core.*` facet as a constitutional amendment binds ordinary engineering too tightly to governance. Some stable protocol semantics deserve careful compatibility review. A schema detail need not have the same amendment process as the person's right to export or revoke authority. Separate rights, technical compatibility, package admission, and community policy.

The essays also contain claims that deserve qualification: a system cannot be declared capture-proof because it uses sortition, incapable of betrayal because it has a boundary, or democratically safe because an agent never casts the final vote. Agents can shape agendas, select evidence, write summaries, and frame choices before a human votes. Civic use needs inspectable sources, meaningful dissent, independent perspectives, and a way to participate without adopting one agent's framing.

Do not turn ordinary membership into an obligation to understand platform governance. Low governance burden is a worthwhile explicit goal already present in the extension docs. Test whether people can meaningfully refuse, leave, and understand decisions before building more sophisticated collective mechanisms. A fork is an exit mechanism; it is not a complete substitute for fair treatment within a community.

The repository has no tracked license or contribution-policy file in the inspected tree. A constitutional commitment to the AGPL family is not the same artifact as a concrete license grant and contribution process. Before accepting outside contributions or presenting public distribution terms, choose the actual license/version, include its text and notices, and document contributions. GNU's own application guidance describes these concrete steps. [GNU license application guidance](https://www.gnu.org/licenses/gpl-howto.en.html).

Claims about being unsellable or immune to a later change in stewardship need actual institutional arrangements and appropriate legal review. Copyleft, copyright ownership, governance charters, trademarks, hosting assets, and credential custody are different concerns. The review does not establish that a particular legal structure satisfies the draft Constitution.

Hosting and compute are plausible services to charge for. Their sustainability is untested. Measure idle background cost, active inference cost, storage/egress, adapter maintenance, and support burden. Give people understandable budgets and useful operation when the paid model is off. Speculative revenue caps and founder-transition thresholds should remain provisional until they can be assessed against an actual organization and workload.

Compatibility maintenance may become a larger burden than initial code generation. A model can generate an adapter quickly; somebody still owns failures when a provider changes, a package becomes unavailable, or an old lens sees newer data. Pin released artifacts, supply compatibility fixtures, support generic fallback/export, and make the support horizon explicit. “Promotion never breaks anyone” is an aspiration that needs a much narrower testable contract.

**The documentation is thoughtful, but its confidence and duplication now need management.**

The status labels separating specification from implementation are useful, and the newer research is often admirably careful. The problem is less a lack of caveats than inconsistent caveats across documents. A reference can carefully preserve unknown outcomes while an essay says duplicate orders cannot happen. The architecture can promise internal integrity while another document trusts root with the record. Several decisions marked resolved are still unresolved at the enforcement or product level.

Add a lightweight status to consequential claims: implemented and tested; chosen but not implemented; experiment to compare; or aspiration. Link a guarantee to its evidence and boundary. Record an explicit supersession when changing direction. Avoid another grand rewrite: remove repeated architectural declarations from essays where they look like competing specifications, and let essays retain their motivations.

This is my disposition of the current vault:

| Document | What I would preserve | What needs attention |
|---|---|---|
| Start Here | The authority map and implementation-status distinction. | Link guarantees to current evidence; make unresolved choices visible even when a high-level direction is selected. |
| Constitution | Ownership, exit, agency, accountable stewardship. | Separate rights from provisional implementation and institutional machinery; settle actual erasure and shared-history promises. |
| Agora Spec | The integrated view of objects, actions, perception, and recoverable work. | Resolve root/client promises; move comparison and useful interaction earlier; qualify broad causal claims about predecessors. |
| Objects and Facets | The strongest current semantic document: identity, occurrences, binding authority, scope, preservation versus validity. | Resist turning every useful distinction into mandatory core fields; implement contrasting everyday examples to test it. |
| Reconcilers | Desired/observed separation, freshness, bounded work, uncertainty. | Narrow the universal mechanism; reconcile status-only writes, conflicts, caches, and volatile freshness. |
| Security | Threat boundaries, raw-client drills, explicit conflicts and deployment limitations. | Turn selected requirements into actual enforcement and adversarial tests; avoid treating metadata conventions as isolation. |
| Security Addendum | Generous useful delegation and a protected external boundary. | “Without loss” overstates the simplification; world-root weakens internal guarantees and confidentiality composition. |
| Extensions | Discoverability, reusable bundles, compatibility evidence, explicit authority. | Make personal experimentation cheap; distinguish packaging from permission; soften constitutional coupling and universal migration promises. |
| The Web | Provider authority, local overlays, frozen casts, anchored evidence. | Make live-page disclosure and provider-dependent operation semantics explicit; avoid session-based resource re-identification. |
| Facets in Everyday Use | Grounded examples that explain the system through ordinary life. | Let implementation feedback revise these examples; avoid having the agent invent a schema for every small variation. |
| Object Use Cases | Breadth across consumption, communication, recurrence, media, files, and devices. | Use it to choose contrasting small tests, not as a simultaneous application backlog. |
| Rooms | Company, persistent place, personal views, selective togetherness. | Sharing is more than event replication; privacy and exit need concrete behavior before optimistic social conclusions. |
| Democracy | A serious interest in member agency and resisting concentrated control. | Separate ideals from empirical political claims; human voting alone does not neutralize agent influence. |
| Ownership | Incentive alignment, portable work, sustainable services. | Replace categorical organizational guarantees with concrete license, contribution, custody, and stewardship arrangements. |

The memory research supplies good hypotheses and an evaluation structure, not an implementation requirement. The security export research supplies important constraints to adopt before sharing. The object counterexamples are useful tests of reasoning; their 14 passing results should never be added to a production confidence score. The retired code is a source of lessons, not an obligation to restore features.

There is also a process risk: generating another convincing document is easier than observing whether someone returns to the environment tomorrow. The repository now has enough conceptual coverage to build informative experiments. New prose should primarily settle a concrete ambiguity, explain a measured result, or record a decision. This review should not become another architecture to obey mechanically.

**I would organize the next work around evidence that earns the next commitment.**

These are proposed checkpoints, not a replacement constitution or a calendar. Some work can overlap; each checkpoint has a reason to exist and a way to expose a wrong assumption.

| Next commitment | Small demonstration | Evidence needed to proceed |
|---|---|---|
| Trust the local foundation | Repair replay/application ordering, text persistence and stale writes, anchors, recursion, refusal effects, and basic request/import boundaries. | Focused invariant and failure tests pass; accepted state and retained content survive the declared recovery cases. |
| Inhabit the environment | A useful default desk, selected object, reader/editor, direct controls, history, and stop/cancel. | You use it repeatedly without developer rescue and can do useful work with JEFF unavailable. |
| Trust the claimed object advantage | Run the first controlled everyday and continuity comparisons with a competent baseline. | A measured benefit survives counting setup, correction, latency, and cost. Failures identify which mechanisms to change. |
| Let JEFF reshape it | Create and revise one personal lens over existing data; preserve identities; undo and reopen it. | A complete user request succeeds within stated authority; candidate failures and stale inputs cannot damage current work. |
| Let the world maintain resources or act outside itself | One local resource and one fake external service with injected crashes, lost receipts, cancellation, and revocation. | Replay never re-executes an effect; uncertainty is visible; stale workers are fenced. Then validate a real adapter's own guarantees. |
| Carry work between devices | Two personal devices, selected content, one offline edit conflict, and one lost-device recovery. | The user can explain what is current, pending, unavailable, and recoverable; ordinary local work survives disconnection. |
| Invite another person | One small room with deliberate sharing, independent views, optional presence, and a tested departure. | Both people choose to return; private material stays private under adversarial inputs; retention and availability match what the UI promises. |
| Distribute beyond the experiment | Install, update, roll back software over current data, export, restore on a clean machine, and survive provider/host loss. | Compatibility, operability, authority boundaries, support responsibility, and actual license terms are reviewable. |
| Grow public communities and federation | Multiple independently operated groups with realistic abuse and coordination cases. | Existing rooms have demonstrated demand, workable moderation, sustainable operations, and interoperable contracts. |

The order between an early centrally served room experience and personal offline synchronization can be chosen by what you most want to learn. Do not confuse proving the room's emotional value with proving a distributed protocol. Likewise, a pure personal lens can precede a general process runtime if its sandbox is already adequate. The point is to isolate uncertainty rather than build every dependency in the grand plan first.

I would deliberately defer a custom compositor, VR, public census and democratic machinery, universal ontology mediation, broad extension standardization, elaborate heat propagation, personal fine-tuning, and a large reconciler catalog. Preserve their requirements where they constrain today's formats or boundaries. Defer their implementations until they solve an observed problem.

**Three actions stand out as the best next use of effort:** repair and test the current persistence/anchor/perception failures; make a small daily environment that both you and JEFF can operate; and run the first real comparison while adding one reversible personal-lens change. Those steps test the heart of Agora without reducing it to a coding assistant or requiring a miniature civilization first.

What would change my assessment? If ordinary use shows that references and history rarely help, and most tasks still require falling back to opaque applications, the general object layer may need a narrower role. If the small object world measurably improves continuity and lets useful new views compose cheaply, then the larger platform earns investment. If two people choose to spend time in a room even without advanced agents, the social direction has independent value. These outcomes should be allowed to reshape the roadmap.

Agora is worth continuing because its proposed benefits are specific enough to test. The next phase should make the experience and its failures concrete enough that the architecture has to answer to them.

---

To reproduce the new evidence from this checkout, run `uv run python research/holistic-review/review_probes.py`. It uses disposable synthetic worlds and prints observations; it is a review harness, not an all-green regression suite. The concurrency case forces a particular legal interleaving. Corruption cases deliberately damage only temporary fixtures. The HTTP case uses FastAPI TestClient. The stored results describe this working tree and will naturally differ after fixes.
