# Facets in everyday use

An Agora object is a stable subject: a document, a recording, a conversation, an appointment, a photo, or a device. A **facet** describes one aspect of that subject. Different tools can work with compatible aspects while the subject keeps its identity.

The point is continuity throughout ordinary computer use. Most objects do not begin as ideas or become programs. Listening to an album, receiving a message, reading a manual, and choosing a printer are central cases. Building software is another supported case.

[[Agora Objects]] defines the contracts. [[Object Use Cases]] explores the difficult boundaries. This document explains what those contracts should feel like in practice; it does not claim that a bag of metadata supplies the implementation automatically.

## 1. Start with a photo

You receive a photo and save it. Agora gives the subject a stable identity. Its facets might describe:

- the original image and its content revision;
- the file or remote source that supplies it;
- a title and caption;
- edits such as a crop, with their relationship to the original;
- attributed descriptions or tags;
- operations supported by installed, authorized tools.

You can see it in an album, search results, and an editor. Those are representations of the photo, not three new photos. Add a caption and the photo remains the same subject. Change its filename and its links should still work.

Album membership is a separate relationship. Removing the photo from an album removes that membership. Deleting a thumbnail removes a cache. Closing the editor closes a view. Erasing the photo is a different operation that must explain what happens to its retained content and references.

The basic idea is simple: **the thing, its properties, the places it appears, and the things happening to it are related but distinct.** Facets describe aspects of the thing; they do not erase those distinctions.

## 2. Labels help people; contracts determine behavior

A conventional “photo” profile might combine image content, source information, and descriptive metadata. A “document” profile might combine structured content and annotations. These profiles provide useful defaults without imposing a universal class hierarchy.

A `kind-tag` is a label, not executable truth. Labeling a recording “document” should not make its bytes readable as text or grant permission to edit them. A tool asks whether the relevant facet contract is present, supported, current, and authorized.

Facets still have types. An image editor needs to understand its image data. A calendar needs precise schedule semantics. “No entity class hierarchy” does not mean “any tool can correctly edit anything.”

A user or JEFF can add a new annotation vocabulary without redesigning the entire OS. Introducing a new machine-interpreted behavior also requires a compatible handler, validation, and permission. New meaning and new power are different changes.

## 3. A song is not a player

Consider a recording in a playlist. The recording carries media information and source bindings. The playlist contains ordered entries that reference recordings. The playback session carries current position, requested output, and observed playback state.

The same recording may occur twice in a playlist. Each entry needs its own identity so “move the second one” does not move both. The playlist can survive closing the player. Pausing playback leaves the recording untouched.

The requested output may be your headphones while the observed state is “connecting.” If the headphones disappear, the system follows your fallback policy; it must not assume that playing a private call through speakers is an equivalent result.

After restart, the system can remember the queue and position without automatically playing sound. Persistence means preserving useful state, not repeating every previous activity.

The useful result is continuity: the recording, its place in the queue, and the player cooperate while keeping their own meanings.

## 4. A document is not its reader window

You open a manual, highlight a paragraph, and stop on page 12. Later you open it from a search result and continue reading.

The manual's content revision is shared document state. Your reading position is scoped to you. The highlight points to a particular region of a particular revision. The reader's size and position belong to its view. JEFF can understand which manual you mean without treating your page position as a change to the manual itself.

If a new edition changes page boundaries, the old highlight must not silently attach to unrelated text. The system can retain the old anchor, offer a verified mapping, or ask you to reattach it. Keeping an entity ID stable does not make every position inside its content stable automatically.

Two tools can inspect the same content. Concurrent editing requires compatible edit and conflict contracts; sharing an ID alone does not make it safe. A preview can remain read-only without being a second-class object representation.

## 5. A conversation is not a call, and a schedule is not a delivery

A conversation may contain years of messages. An active call is a session within that context. Closing the conversation view must not silently end the call unless that is the explicit action; reopening it must not start the microphone.

Your unread marker is personal. A message's sender and delivery observations are different shared or provider-supplied facts. An editable draft and the frozen payload submitted for sending need distinguishable version semantics. Correcting the draft later cannot change what was already sent.

An appointment has a schedule. A recurring appointment has occurrences and exceptions. A reminder refers to an occurrence and has its own delivery history. Moving Friday's occurrence does not mean moving the whole series. Restoring yesterday's desktop must not notify everyone again or resend yesterday's messages.

Facets let these pieces cooperate. They do not make external events reversible.

## 6. Intent and observation are useful where the activity calls for them

Some activities involve maintaining a desired state:

```text
download intent: obtain this content revision in this allowed location
download observation: 60% received; source temporarily unavailable

playback intent: paused at this recording and position
playback observation: output connected; no audio playing
```

The user or JEFF requests intent through authorized operations. An adapter or reconciler reports observations with their source, time, and version context. It can try to close the gap within its permissions and resource limits.

This `spec`/`status` pattern is useful for maintained resources. It is not the universal lifecycle of every object or a promise that every requested outcome will occur. A photo needs no process spec. Printing a page needs a submitted-job record and uncertain-outcome handling; blindly repeating “one printed copy should exist” could waste paper after an acknowledgment is lost.

Human task status such as “in review” is another domain's content, not privileged runtime observation merely because the field is called `status`.

## 7. Applications supply lenses and operations

An Agora-native application can provide:

1. **Lenses** for viewing compatible content: a reader, calendar, gallery, media player, or device panel.
2. **Operations** for acting on it: annotate, crop, reorder, reschedule, play, or print.
3. **Facet definitions and adapters** where its domain needs additional data or connections to resources.

An application can still be a coherent, carefully designed experience. The object system does not require every app to become an interchangeable generic form or every document to reveal all its internals to every tool.

Installing a compatible image tool can make more operations available on existing images. It does not grant that tool unrestricted access to every image. Sharing a tool offers discovery or installation; activation and permissions remain explicit. Removing the tool should preserve the data and expose a safe fallback, even if specialized editing is no longer available.

Legacy software can participate through files, accessibility, application APIs, or an opaque window. A wrapper records what it actually knows and can do. It cannot recover an unsaved buffer the application never exposed, or claim semantic control of a format it cannot interpret. Partial integration is useful and should be labeled honestly.

Native apps need not own the only usable representation of their data. A documented export, retained payloads, and compatible readers make that independence concrete.

An update also has to preserve established meanings. A tool that previously shared a frozen photo cannot start sharing future edits under the same old action contract. If an older tool cannot safely edit a newer facet, keeping it read-only is better than silently dropping the new meaning. Updating or restoring the tool must not silently restore old user data along with it.

## 8. Human controls and JEFF's tools share an operation contract

The “Move occurrence” control in a calendar and JEFF's reschedule tool should invoke the same semantic operation. They should agree on target identity, affected scope, argument validation, conflicts, and recorded results.

That does not require identical permissions for every caller. Nor does it mean that a discovered action is guaranteed to work later. The system checks current access, versions, resources, and handler availability when it runs.

An action descriptor is a description of a supported operation. A grant is permission to cause an effect. An object cannot grant itself authority by adding a facet that says “approved.” The same applies to software-generated summaries or suggested actions.

Direct controls remain essential. You should be able to pause music, inspect a file, or adjust a view without needing JEFF to interpret a sentence or approve each ordinary interaction.

## 9. Objects can be described at different levels of detail

A visual view might show a title, thumbnail, or full document. JEFF likewise needs a compact description or a detailed record depending on the task. The platform assembles these projections from permitted facets and trusted framing.

```text
Short: Travel itinerary, revision 3, available offline; your position is page 4.
Expanded: Include permitted highlights, source, and newer-revision availability.
Detailed: Include the selected content and relevant history within access and budget.
```

The description must preserve consequential distinctions. “Print outcome unknown” must not become “printed” because space is short. A claim that a photo depicts a certain person remains an attributed claim. A shared projection must not include private annotations merely because they are attached to the same subject.

Unknown facets can use a generic visual/text inspector. Their payload survives until a compatible tool is available; reading them does not automatically execute new code. When there is too little room to describe a subject honestly, the system should signal omitted detail and fetch more when needed.

## 10. What stability should feel like

| User action or change | Expected continuity |
|---|---|
| Rename or move a document | Existing subject references survive; the binding updates. |
| Open it in another application | Another view, with the same chosen content revision. |
| Lose the network | Known identity and permitted local data remain; remote state is marked unavailable or stale. |
| Remove a playlist entry | That occurrence disappears; the recording and other entries remain. |
| Disconnect a device | Its record survives; operations requiring it become unavailable. |
| Restore the desktop | Views and safe preferences may return; old sends, calls, and print jobs are not repeated. |
| Remove an extension | Data survives with declared limits on remaining inspection and editing. |
| Leave something untouched for years | Age alone does not delete it or invalidate its identity. |

Creating software uses these same rules. A note can gain executable behavior when that behavior belongs to the same subject and is authorized. A separate program can instead reference the note. Neither path defines what all objects are for.

**The promise of facets is that ordinary things remain coherent as the ways we use them change.** That promise depends on stable references, explicit scopes, compatible operations, and honest failure states—not on every object growing into something more elaborate.
