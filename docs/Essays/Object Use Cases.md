# Object use cases and principles for a whole OS

*Reasoning companion to [[Objects and Facets]] (and its predecessor, [[Agora Objects (superseded)]]), [[Facets in Everyday Use]], and [[Agora Spec]]. The obligations in §16 are what the reference must exercise before the base protocol freezes. These are proposed semantics and thought experiments, not observations of a running OS. Developed without new web research. They broaden the earlier idea-to-prototype assessment rather than replacing one favored workflow with another.*

## 1. What would count as a stable object model?

Stability means a person can correctly predict what a reference and an operation will affect, even after the environment changes. The same test applies whether the subject is a song, a message, a file, or a printer.

The OS need not retain every implementation object forever. It must preserve the identities and state it has promised to retain, be explicit about expiry and loss, and avoid silently substituting a different subject. That is a stronger practical requirement than merely issuing unique IDs.

Four tests should guide each case:

1. **Reference:** What exactly does “this” designate: subject, revision, view, collection occurrence, resource role, or activity?
2. **Authority:** Who supplies each value, and who can change or disclose it?
3. **Continuity:** Which changes should preserve the reference, and which create a different subject?
4. **Effect:** What happens when the operation is repeated, interrupted, applied offline, or restored from history?

No universal project object, workflow stage, or derivation chain is required. Received, unchanged, and merely consumed subjects are first-class.

## 2. Reading an unchanged document for years

**Ordinary use.** A user downloads an appliance manual, reads a section, bookmarks it, and returns eighteen months later. Nothing is being created beyond a little personal state.

The manual has a content revision and source provenance. Reading position and bookmarks belong to the user, while each bookmark refers to a document revision and region. The download's status belongs to an activity; the saved local bytes are a materialization. The reader window is a view.

**Pressure.** The manufacturer replaces the PDF at the same URL. A newly downloaded file cannot silently replace the cited edition in an old bookmark. A live “latest manual” reference and a reference to the retained edition should behave differently. The system may offer an upgrade and anchor mapping; the old citation must remain meaningful or explicitly unavailable.

**Principle.** Reading a subject is a complete use case. A meaningful object does not need to change or accumulate agent annotations. Storage retention should depend on what was saved and promised, not how recently JEFF thought about it.

**Open choice.** Whether a normal bookmark pins content or follows a live document needs a visible default and a way to choose. A shared citation should carry its revision semantics across export.

## 3. Listening, queues, and output devices

**Ordinary use.** The user plays an album, inserts the same song twice in a queue, pauses, and resumes with headphones.

At least three referents exist: the recording, each queue entry, and the playback session. A device reference is separate again. “Remove this” from a queue acts on an entry; “delete the download” acts on a local materialization; “pause” acts on the session.

**Pressure.** The selected entry is removed while it is playing. It is reasonable to let the current playback finish, but only if the session retains its own content reference; otherwise deletion of a list entry could unexpectedly tear down the audio stream. The queue contract must specify where “next” now points. A numeric index cannot safely identify the current entry after reordering.

**Pressure.** The local recording is unavailable but a remote search returns a song with the same title. This is not enough to establish the same recording or edition. Offer an alternative rather than silently substituting it. Content identity, catalog identity, and a user's semantic grouping are distinct.

**Pressure.** Headphones disconnect during a call. A default-device role may resolve to speakers, while an explicitly selected physical device no longer resolves. That distinction determines whether the system pauses or redirects private audio. “Always continue somewhere” is not a universal recovery policy.

**Principle.** Persistence preserves the queue and position; resumption policy determines whether sound starts. High-rate sample and decoder state belong to the media subsystem. The object model supplies references, controls, and coarse observations without mediating every sample.

## 4. Communication, drafts, and delivery

**Ordinary use.** A message arrives, the user reads it, writes a reply, attaches a photo, and sends.

The incoming message has authenticated source metadata where available, a conversation relationship, and a captured or remote content revision. Local unread, mute, and notification state are scoped to the participant. Attachment occurrences retain the context in which a file was received, even if their bytes are deduplicated.

**Pressure.** The photo is edited after the send button is pressed. The send operation must use the frozen attachment revision that was selected for submission; a live attachment reference could disclose later edits without a new sending decision.

**Pressure.** The service accepts the message, then the connection fails before the acknowledgment reaches Agora. “Pending” is not equivalent to “not sent.” Retrying needs a service-supported operation identity or another reliable verification path. Otherwise display uncertain delivery and provide an explicit recovery action.

**Pressure.** The same remote message is observed through two devices. An account-scoped provider binding should identify the existing item. A copy forwarded into a different conversation is a different occurrence with different provenance, even if the body is identical.

**Principle.** Shared content, local participation state, and delivery facts have different authorities. A message's unread marker should not cause content revision churn, and a local delete must not pretend to retract a remote delivery.

**Open choice.** Draft-to-message identity can be modeled either as one subject transitioning through explicit revisions or as linked draft/message subjects. The contract must preserve references and frozen submissions in either case. The OS should not force every domain to choose the same transition model.

## 5. A conversation, call, and device lease

**Ordinary use.** The user opens a conversation, joins a call, views a shared document, and closes the conversation panel.

The conversation is long-lived. The call is an activity with participants, media routes, and current grants. The microphone and camera are resources whose use must be inspectable independently of the panel. A shared document remains its own subject.

**Pressure.** Closing the panel should not accidentally decide the call's lifetime. If the product chooses “closing this window ends the call,” expose that as an explicit UI behavior; do not infer it from object containment. A call may be controlled from several surfaces.

**Pressure.** Reboot restores the conversation layout. It must not silently rejoin the call, activate devices, or make a historical camera observation look current. A call record can be preserved while active device leases expire.

**Principle.** Display containment does not imply runtime ownership. Every ongoing use of a sensitive resource needs an authoritative activity record and current indication, even when no large window is visible.

## 6. Calendars, recurring occurrences, and time

**Ordinary use.** The user creates a weekly appointment, moves one week's occurrence, then changes the time of future occurrences.

The recurrence definition, each individually addressed occurrence, and each reminder delivery need distinguishable identity. An occurrence can have a stable domain key without being eagerly materialized as a top-level entity for every week in the distant future.

**Pressure.** The user changes time zones. “09:00 at the destination” and “the same instant shown locally” are different intents. Store the domain's actual time semantics: instant, civil time with zone, floating local time, or all-day date as appropriate. A timestamp alone cannot express them all.

**Pressure.** Moving an occurrence changes its displayed time but should not break a note attached to that occurrence. Re-keying solely by the new displayed timestamp loses continuity. An occurrence's anchor in a recurrence and its scheduled time must be distinct.

**Pressure.** “Edit future occurrences” can change the recurrence topology. Explicitly preserve or remap existing addressed occurrences and exceptions; do not create an unbounded number of identities or quietly retarget old ones. Cancellation is not erasure of past attendance or delivered reminders.

**Pressure.** The device wakes after a reminder was due. Policy might deliver one catch-up notification, mark it missed, or suppress it after a grace period. Reconstructing the reminder object must not itself emit another notification.

**Principle.** Time is part of a domain contract, not a generic scalar with a universal merge rule. History needs both when an observation was recorded and what interval or occurrence it describes.

## 7. Photos, edits, collections, and sharing

**Ordinary use.** The user imports a photo, crops it, adds a caption, places it in two albums, and shares it.

The photo may retain original content plus a non-destructive edit recipe. Album membership is distinct from photo identity. A derived thumbnail follows a particular content/edit revision. A private annotation must not be included just because the image is shared.

**Pressure.** “Share this photo” could mean share the visible edited rendition, the original, a selected revision, or a live editable object. A share operation must specify that choice and its audience. Live sharing is not the right default for every attachment.

**Pressure.** Two photos have identical bytes because one was received from a friend after originally being taken by the user. Content storage can deduplicate them without erasing the receipt's context. Consolidation should preserve source occurrences and must not combine previously separate permissions automatically.

**Pressure.** The user erases the photo but a search embedding, thumbnail, or JEFF summary still reveals it. Retention and deletion must follow derived dependencies. Conversely, removing one album entry is not an erasure request.

**Principle.** Source, edit, rendition, occurrence, and subject identity are different choices. A “same-as” suggestion is not a license to merge them all.

## 8. Browsing and addresses that change meaning

**Ordinary use.** A user opens a tab, navigates between pages, bookmarks one, downloads a file, and closes the tab.

A tab has session identity and navigation state. The current remote page is a resource observation. A bookmark references an address or a saved subject with declared live/pinned semantics. A captured page is a retained revision; a download is an activity producing or updating a local resource.

**Pressure.** The URL stays constant while the page changes. A bookmark can reasonably follow the address, but an annotation or quotation may require a snapshot. The OS must not imply that a URL is an immutable content identity.

**Pressure.** The tab navigates while JEFF is acting on “this form.” The operation must remain bound to the document/navigation revision and origin it inspected. Stable tab identity does not authorize acting on a new page that appeared in the same tab.

**Pressure.** Restoring a tab replays a purchase or form submission. Restore the view and safe navigation state; do not replay submitted actions merely because they were in session history. Retaining a form draft and retaining evidence of a submission are different things.

**Principle.** Stable containers can intentionally change their current subject. The references to container and subject must not be interchangeable.

## 9. Files, folders, copies, and storage volumes

**Ordinary use.** The user renames a document, moves it between folders, copies it onto removable storage, and edits it with a conventional application.

A subject has one or more file bindings. Folder membership describes the storage namespace; a semantic collection can be different. A mounted volume has identity distinct from its temporary mount path. Access authority comes through a resource grant, not the string spelling the path.

**Pressure.** An editor saves by replacing a file. Treating every replacement as a new subject would break references during ordinary editing. Treating every new file at an old path as the old subject would be equally wrong. The adapter needs operation evidence, file identity where useful, and an explicit reconciliation policy. When continuity cannot be established, expose uncertainty rather than assert a perfect heuristic.

**Pressure.** Copying creates two files. Did the user request another materialization of the same subject, an independent editable duplicate, or a pinned export? Those choices have different edit propagation and permissions. Familiar “duplicate” should normally establish independent editing, while explicit synchronization may preserve one logical subject. Record the chosen relationship.

**Pressure.** A removable drive disconnects. Its files become unavailable; they are not deleted from history. Another drive mounted at the same path must not inherit their identities. A placeholder should report where its bytes are expected without pretending the data is still local.

**Principle.** Filesystem interoperability requires ongoing identity reconciliation. An object ID plus a path does not solve it. Full historical reconstruction also requires captured bytes; metadata cannot reconstruct uncaptured edits.

## 10. Devices, roles, settings, and physical effects

**Ordinary use.** The user selects a default printer, prints a document, changes audio volume, and plugs in a new display.

Physical resources have device identity evidence and expiring observations. Preferences refer either to a concrete device or a role with a defined resolution rule. Effective settings are derived from explicit scopes and precedence, such as session override over user default. The exact precedence must be visible and inspectable; it is not a universal rule assumed for every setting.

**Pressure.** Changing the default printer after submission must not retarget a queued job unless the user explicitly requests that change. A print operation pins both the document revision and its actual device target at the relevant commitment boundary.

**Pressure.** A device is replaced by a newer model at the same address. The user's role preference can be deliberately rebound, but an old device reference must not silently designate new hardware or transfer trust. Hardware identity may be uncertain; a namespaced address is evidence, not an unconditional identity proof.

**Pressure.** The requested brightness is 80 but the device reports 60 or cannot be contacted. Preserve requested and observed/effective values separately. The UI can show pending or unsupported behavior without changing the saved intent into an invented observation.

**Principle.** An object's stable identity does not promise perpetual reachability, unchanged capabilities, or automatic trust in replacements. Resource observations and grants need a current incarnation.

## 11. Contacts, people, and source disagreement

**Ordinary use.** The user sees the same person through a phone contact, an email address, and a conversation.

A personal contact record is a set of attributed claims and bindings, not authoritative ownership of a human identity. Sources can disagree about names or addresses. A user's local nickname can coexist with a provider-supplied display name without overwriting it.

**Pressure.** Two contacts have the same display name. A semantic guess must not merge their message history, select a recipient, or transfer access. “Send this to Alex” needs a resolved destination and account context, not merely a high similarity score.

**Pressure.** A source address changes owners. A historical message remains attributed to its original observed source context; future routing requires current identity evidence. The UI must not rewrite history merely because today's contact lookup returns another name.

**Principle.** Identity claims about the outside world have provenance and validity intervals. Agora's stable record ID must not be confused with proof of the external referent.

## 12. Notifications, clipboard, and temporary things

**Ordinary use.** The user receives a notification, dismisses it, copies text, and pastes it elsewhere.

A notification presentation is not the message, appointment, or job it concerns. Dismissal changes notification state; it need not delete or mark the underlying item complete. A clipboard entry can contain a snapshot, a live reference, or both with explicit paste behavior.

**Pressure.** The clipboard contains a live reference to a private object. Pasting into a shared conversation must not grant live access accidentally. A paste operation should select a permitted representation or explicitly create a share, honoring source restrictions.

**Pressure.** A password or temporary code is copied. “Everything is a persistent object” would be a harmful default if it made all clipboard history permanent, searchable, or available to JEFF. Transient data needs explicit expiry and exclusion policies. Creating an identifiable ephemeral item does not imply indefinite retention of its payload.

**Pressure.** A notification is replayed on another device after dismissal. Whether dismissal is per-device or per-person must be part of its contract. The system cannot infer the intended synchronization scope from the word “dismissed.”

**Principle.** Stability includes stable promises about expiry. The world should retain meaningful subjects deliberately, not become a compulsory recording of every interaction.

## 13. Large domain models and applications

**Ordinary use.** The user edits a video, uses a spreadsheet, plays a game, or works in a CAD application.

The application exposes useful subjects and operations while keeping efficient domain state. A video has timeline elements and media references; a spreadsheet has stable cell/row or named-range anchors according to its model; a game has sessions and saves. The OS does not need one global entity for every frame, formula evaluation, or simulated particle.

**Pressure.** A cell moves or a video clip is split. An external comment needs the domain's anchor mapping, not an assumed global offset. A generic viewer may show a fallback while specialized editing remains unavailable.

**Pressure.** A table lens displays aggregated data. Editing its displayed number may not have a unique inverse update to the underlying rows. Read-only composition is legitimate; a write-through lens needs an explicit inverse operation and conflict policy.

**Pressure.** The original application is uninstalled. Retained content must remain exportable, with metadata and any available fallback representation. If editable semantics require an absent handler, say so. Generic inspectability must not be misrepresented as full-fidelity editing in every application.

**Principle.** Whole-OS stability comes from interoperable boundaries, not universal internal representation. A small shared protocol can coexist with rich domain-specific formats and algorithms.

## 14. Across every case: updates, outages, and competing work

**Pressure: an extension changes.** A photo tool learns a new edit format while another installed tool still understands only the older one. A newer signature or sharing constraint may also affect what edits are safe. Preserving opaque bytes is necessary but insufficient. The operation gate must understand the admitted dependency and critical-requirement envelope; unsupported editing is restricted while independent operations, such as changing private reading position, can continue.

Updating implementation and changing the meaning of an action are different changes. A new handler cannot reinterpret an approved frozen attachment as a live share just because both use an `entity_id` argument. Bind actions to versioned semantic contracts, and assess compatibility and authority again when those semantics change.

**Pressure: an application is restored.** The user rolls back a failed application update after another participant has edited shared content. The old program may no longer understand the new format. Restoring the preview's old data would erase unrelated work. Keep software adoption, data migration, and historical restoration distinct; supply compatible interpretation or disclose the limitation. A migration needs a recoverable commitment boundary and must preserve unrelated facets.

**Pressure: two devices reconnect.** Both have changed a playlist while offline, or one has moved an appointment after the other's reminder was queued. Each domain needs explicit conflict and delivery rules. A single-writer initial implementation is reasonable if it states what disconnected devices may do: view cached data, retain local proposals, or create a branch. It must not advertise general convergence it has not implemented. Current authority is checked when delayed actions are submitted; retaining a local proposal does not preserve an expired grant.

**Pressure: a provider stalls or the index is damaged.** Showing a local document title should not wait indefinitely for a remote facet provider. Retained data can be shown as cached; missing data can be shown as missing. Pause, mute, and inspect-current-resource controls need a direct path independent of JEFF and semantic search. Reference resolution, remote fetching, and invoking behavior are separate operations with different failure modes.

**Pressure: the world is large.** A million objects, a large video, and several busy adapters must not require a full graph scan on every interaction. Queries and subscriptions need bounded work, explicit revision/freshness context, backpressure, and resynchronization after missed changes. A thumbnail worker exhausting memory must not take away basic device controls. Efficient internals, resource isolation, and degraded operation are architectural obligations, not optimizations to assume later.

**Principle.** Stability is a promise about behavior under change and failure. It needs versioned contracts, bounded resource use, and compatible recovery paths in addition to persistent identifiers.

## 15. What these cases change in the earlier proposal

### Identity splitting is not the only answer to scope

The earlier assessment recommended separate identities when permissions or lifetimes differ. That was too coarse. A person's reading position and another person's annotation can be private scoped facets over the same document; they need not create separate document identities. Split when there is a separate independently addressable subject. Use scoped state when the referent is shared but perspective differs.

### Reconciliation is one action family

The earlier emphasis on service specs made recovery look like rebuilding running projects. Most recovery is more varied: restore a view, retain a draft, mark a source offline, keep a queue paused, refresh device observations, and avoid repeating external deliveries. Every resumable activity needs explicit rules about what survives and what may restart.

### The minimum useful registry is a set of contracts, not a universal vocabulary

The OS needs to distinguish identity, revisions, scope, authority, effects, and dependencies. It does not need one universal schema for all recordings, medical appointments, drawings, or games. Domain packages can define these while conforming to the common envelope and action boundaries. Standard contracts should emerge where interoperability is demonstrably useful.

### A useful OS is not defined only by cross-tool creation

Two tools editing the same data remains a valuable test, but successful consumption and maintenance are equally important. A user should benefit when they never write code, never build a custom lens, and rarely ask JEFF to create anything. Predictable reading, listening, communication, device use, and retrieval are product outcomes in their own right.

### Meaning can stay incomplete

The OS does not need JEFF to produce a complete explanation of every subject before it can be stored or used. An unknown recording can still play through a known media contract; an untitled file can still be copied; an unfamiliar facet can still be preserved. Uncertain semantic identity should remain uncertain without blocking unrelated safe operations.

## 16. Cross-domain obligations before freezing the base protocol

| Obligation | Cases that must exercise it |
|---|---|
| Live versus pinned references | Updated manual, sent attachment, queued print job, saved web page |
| Occurrence identity | Repeated playlist entry, recurring appointment, forwarded attachment |
| Scoped state | Reading position, unread marker, layout, default-device preference |
| Subject versus activity | Recording/playback, conversation/call, document/print, file/download |
| Source reconciliation | File replacement, repeated mail import, provider updates, removable media |
| Honest unavailability | Offline recording, disconnected printer, expired remote access, missing codec |
| No replayed effects | Messages, calls, print jobs, reminder deliveries, form submissions |
| Non-destructive organization | Albums, playlist reorder, folders, saved-query views |
| Controlled expiry and erasure | Clipboard, notifications, caches, derived summaries, private annotations |
| Domain-specific anchors | Document highlights, spreadsheet references, video timeline comments |
| No privilege through equivalence | Contact merge, alternate media source, replacement device, shared reference |
| Useful without JEFF | Reading, playing, local search, direct device controls, basic export |
| Compatible software evolution | New facet with an old editor, failed migration, restored application over newer data |
| Bounded failure and resource use | Stalled provider, failed index, missed subscription updates, competing background work |
| Honest disconnected behavior | Cached views, pending proposals, concurrent playlist changes, stale reminders and grants |

Start with a few small implementations spanning these different pressures. Do not require full versions of every application before learning anything. Conversely, do not let a successful coding demo stand in for these independent tests.

An initial demonstrator could include a document reader with annotations, a queue/player, a conversation with a simulated delivery service, an appointment/reminder model, and a device/job simulator. Real file rename/replace tests and a model-off mode should accompany them. The simulator cases must remain labeled; they do not establish provider compatibility, device safety, or real-world timing behavior.

Even this broader demonstrator validates only part of Agora. Scheduling, drivers, networking, storage durability, accessibility, software distribution, account integration, and recovery remain substantial work. The object model should give those systems dependable boundaries, without absorbing their mechanisms into a universal database or claiming their work is already done.

The strongest general principle is: **preserve what the user meant to refer to, make the scope of change explicit, and report what the system actually knows.** Facets are useful when they support those obligations without making everyday use feel like database administration.
