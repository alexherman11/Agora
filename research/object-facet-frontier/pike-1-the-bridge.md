# Pike 1: the bridge

Round one, 23 September 2026. Research note, not a decision. **[ran]** executed in the desk (private session `frontier-pike`, plus a private deskd on port 8791 to read scene keys and send fenced gestures). **[read]** primary text fetched raw (HTML or PDF) and grepped; quotes checked against it, not a digest. **[recall]** not re-read. **[imagined]** thought experiment.

For each system: what unit is a view bound to, how does the binding name its source, what happens when the source changes shape, and where did custom code come back?

## 1. Sources: six ways a view holds on [read]

**Boxer** (diSessa & Abelson, CACM 1986). The view *is* the data. Naive realism means users "should be able to pretend that what they see on the screen is their computational world in its entirety". A graphics box is "only an alternate form" of a box structure, so a sprite's position is an ordinary variable. Boxes nest, so the naming is structural, and containment is "strictly hierarchical". To show one thing in two places Boxer adds the **port**, "simply a view of a box at some other place". A port is a direct reference, and a change on either side appears on both. Code: procedures inside boxes.

**HyperCard** (HyperTalk Script Language Guide). The **background** holds the shared layout and each **card** holds its own field contents ("the text held by a field … usually remains with the card"). That is a clean split between look and data. It has three ways to name a thing, and each fails differently. A *name* breaks on rename. A *number* is a position: "If you delete an object, its number is reassigned to the object following it". An *ID* "never change[s]", but a copy gets a new one, so after copy, paste and delete "a button that took you to the original will probably not take you to the copy." Code: HyperTalk handlers.

**Morphic** (Maloney & Smith, UIST 1995). The morph is the object, and composition is by submorph. A control points at its target by direct object reference. The authors considered "a name-based and several path-based schemes" and chose direct references as "the most robust in the face of structural changes". The cost they name is that copying must update the copy's intra-composite references. Liveness comes from **observing**, which "is a polling technique". Code: step methods.

**Embark** (Ink & Switch). "Each view instance is associated with some node in the outline and can access any data in that node or the subtree underneath". Properties inherit up the tree, so a colour set on a day applies to its places. Formula arguments are **mentions**, which are identity references to nodes. The repeat heuristic is deliberately "ephemeral": after insertion the arguments "do not depend on the shape of the document". The failure is stated exactly in Appendix I: "the arguments don't update automatically; for example, if a user changes the date of a bullet in their trip plan, they need to update the corresponding date in all formulas below it manually." The weather formulas "directly reference a specific date". The binding held the right *identity* and the wrong *intent*. The user meant "this day's date", and the formula captured "that date". The authors propose a one-off "staleness watcher" instead of abstract patterns. Views and functions were "hardcoded"; runtime JavaScript is the envisioned next step. Schema is implicit (the map "looks for objects with a 'location' property").

**Potluck.** The binding is a **search**, a pattern over text that "run[s] continuously". Annotations are an overlay and never edit the text. The source is named by its *content*. A shape change either still matches or silently stops matching, and users often "edit[ed] the text because it was easier". A change to a shared search "automatically affect[s] all the documents where it's used … very easy to break other documents". Code: JavaScript formulas.

**Patchwork / Malleable Software (2025).** A tool is bound to an Automerge document by URL and by an *implicit JSON shape*. "Upgrading tools would frequently break compatibility with existing data." Cambria, which translates on read, is not integrated. A generic commenting tool needed each tool "to report the current user selection as a semantic region", and today that runs through "hardcoded workarounds".

### The taxonomy

| Strategy | Examples | Follows | Fails by |
|---|---|---|---|
| **Identity** (pointer, ID, mention) | Morphic target, HyperCard ID, Embark mention, Boxer port | move, rename, restructure | copy or re-mint (a new id); intent that was *relative*; dangling on delete |
| **Name / path** | HyperCard name, desk `title:`, lens `lens plan`, heading `section=` | nothing, but it is readable | rename (silent miss); duplicates (silent shadow) |
| **Position** | HyperCard number, desk section and tag keys | nothing | insert or delete: *retargets*, the worst failure because it looks fine |
| **Query / pattern** | Potluck search, Embark subtree, desk `of tag:day` | membership and field edits, automatically | silent emptiness; an edit to the definition breaks every consumer |
| **Copied literal** | Embark's repeated dates, desk `due<2026-10-03` | nothing | stale view that looks current |
| **Relative / contextual** | Embark property cascade, desk `$due` inside a repeat | context changes | moving the view changes what it means (Embark treats this as a feature) |

**Stale views** come from literals and from identity where intent was relative; **retargeted drafts** from position keys; **silent misses** from names and queries; **wrong-definition gestures** from fences that miss part of the definition.

## 2. The desk's answer: the lens compiler [ran]

A trip world (Friday and Saturday notes tagged `day` with due dates, a task "Book canoe", an Itinerary doc with `##` sections), eight lenses, one per strategy, then changes under them.

| Lens binding | Change | Result |
|---|---|---|
| `of tag:day` | retitle Friday, change its due date | followed both. No code, no lens edit |
| `of title:Friday` | retitle to "Fri 3 Oct" | `0 of title:Friday`. Silent. Absence prints the same as an honest empty |
| `of kind:task,due<2026-10-03` (literal) | Friday due 10-03 → 10-02 | still lists the canoe task: **Embark's failure reproduced**, and nothing marks it stale |
| `of prop:anchor=start` then inner `of kind:task,due<$due` (relative) | same date change | followed: the list emptied correctly. Survived remove plus re-place too (the prop lives on the subject, as Sable found) |
| `of a04` (one id) | none | **0 matches from the start.** A single id is not a selection (`knife.parse_selection` returns None), so the most stable binding cannot be written for one thing, and nothing is refused |
| `of a04,a06` | remove a04 | **the whole list emptied**, a06 included. After `place s03` the thing came back as a25 and the binding never recovered |
| `of tag:day` + `at item` | move a04 into a column surface | still shown, painted at 8,8 400x768: geometry from another surface's layout, drawn into this board |
| `of sections:a10` | insert a "Thursday" section | keys are positions (`secs/0` was Friday, is now Thursday). A duplicate "Saturday" heading painted two edit gestures that the desk refuses on use ("more than one section has that heading"). The refusal is right, but the scene advertises dead gestures as live |
| `over $tags`, `of a25,a25` | none | tags keyed `ts/0,1,2` by position; the same appearance twice gives **two identical keys** |
| host: `lens plan` | retitle lens `plan` | host refuses outright: `no lens 'plan'`. The last-good fallback does not engage, because it keeps the host's *text*, which still names the missing lens |
| a second note titled `outline` tagged lens | none | silently shadowed by the first; creation is not refused |
| host containing plan; plan's `on edit` changed from retitle to tag | old gesture sent with the host's `def` | **accepted**. The same gesture sent with plan's own `def` is refused. Only the outermost lens revision is fenced |
| item fence | stale `retitle a06` with observed rev 1 against current rev 3 | **accepted** when the intervening edits were my own; refused when another actor (`pike-tab2`) made them. `_touched_by_others` exempts self, so two windows of one person are unprotected |

The text printer also shows `of kind:task,due<$due` unfilled: the agent cannot see which date was queried.

**What it gets right.** One scene with two printers is Boxer's naive realism, extended to the second inhabitant. The agent's text and the person's pixels have no separate sources. Lenses are world data, so they can be undone, forked and read, unlike Embark's hardcoded views or Patchwork's repo-deployed tools. Query bindings give real automatic update: field edits and membership changes needed no lens edit and no code. `$field` inside a repeat is the relative binding Embark lacked, and it already fixes Embark's exact case when the anchor is a query. Gestures carry observed revisions, and refusals name the line.

**What it gets wrong.** First, it cannot name the thing. A selection ranges over *appearances*, a single id is not a selection, and subject ids are not selectable. The stable identity Sable argues for is unreachable from a lens, so authors fall back on titles (which break), positions (which retarget) or tags (which cannot stay unique). Second, absence is silent. An empty result, an unresolved name and a vanished id all print `0 of …`, while `only when` already prints absence honestly. Third, keys are occurrence-unsafe: positional for rows and tags, colliding for duplicates. Fourth, the fences are partial: nested lenses are unfenced, self-edits are exempt, and fallback is shallow. The painter's element reuse limits the damage, since changed parts are rebuilt instead of retargeted. So drafts get *lost* or *refused* rather than applied to the wrong row. That is the right direction of failure, but it is still loss.

**On Jeff's question.** Can the Codex binding shape (stable source, interpretation, transformation, follow or capture) be written today? Only in part. *Follow* exists implicitly through queries. *Capture* exists only as a literal that cannot be told apart from a stale follow. *Stable source* has no word. There is no *interpretation* or *transformation* beyond `$field` substitution and `due<`. `over $tags` is follow-mode over a field, but its keys are positions. The smallest missing word is the ability to name one subject (`of s03`) and have its resolution printed: `s03 (unplaced)`, `s03 (gone)`.

## 3. What each substrate lets a binding name [imagined, grounded in the reading above]

- **Facet records (Sable's referent + owned aspects).** A binding can name `(referent, aspect, definition revision)`. An aspect rename is an event of its definition, so a binding can follow a *declared* rename and report anything else as unresolved. Astra asks for exactly this: never "silently bind to a similarly named replacement". The risk is that bindings must also name the aspect's owner, and a lens becomes a list of qualified names nobody wants to write.
- **Live objects.** A binding names `(object pointer, message)`, as Morphic's `target` does. This is the most robust against restructuring (Morphic's own finding) and the most fragile against copying. The behaviour behind the message can change under an unchanged view, which is the nested-lens fence hole above at object scale. Behaviour would need revisions that the fence can see.
- **Structured documents.** A binding names `(document URL, path or anchor)`. Across documents, a URL is identity. Inside a document, text ranges can use CRDT cursors or Peritext marks [recall], which survive concurrent edits better than any key the desk has. Structural parts (an outline node, a section) have identity only if someone mints it: Embark gave nodes ids, while the desk's sections have none. Schema drift falls to Cambria, which is still unintegrated.

All three can express identity. What differs is *where rename and replacement become events*: per aspect, per object, or per document. The bridge can only report a binding as unresolved where such an event exists.

## 4. First position

1. **Bind concretely, and remember how you got there.** Embark is right that inference should run once and leave something concrete behind. It is wrong to throw away the derivation. A binding should store the resolved identity *and* its provenance ("the due date of the enclosing day, via anchor X"). With that stored, a staleness watcher is a comparison, not a heuristic, and follow versus capture becomes a visible mode instead of an accident of authoring.
2. **Bind to the object, key by occurrence.** A lens names referents, never appearances or titles. Scene keys are `(referent, occurrence-in-this-view)`, never a list position.
3. **Every binding prints its state:** live, captured, empty, unresolved or ambiguous. Silent `0 of` is the bridge's worst current defect, because it makes the other failures invisible.
4. **When new code is necessary:** for a new gesture or painting primitive (a native such as a prose editor), and for a new *interpretation* (week-containing, distance). It should not be needed for a new data shape, a new combination of existing parts, or a new field. On the desk today, the first two of those already hold. The third holds only when the field is a string.

**What would change my mind.** (a) Juniper's note-to-workspace case shows that provenance-carrying bindings surprise users more often than manual repair costs them, which is Embark's own prediction. (b) A document substrate gives stable in-document anchors more cheaply than minted referents, in which case bind to anchors and let identity be a document concern. (c) The painter proves unable to preserve drafts even with occurrence-safe keys, which would mean the continuity problem lives in the painter rather than in the binding.
