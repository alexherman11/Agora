# Prior art for reading through a shape

> Prior-art review for shape-reads.md draft 1, by a research agent for Claude, 28 Oct 2026.
> - **Reviews:** [[shape-reads]] (`docs/design/kinds/shape-reads.md`), with `trials/FRICTION.md` sections 1, 2, 5 and 6 and `fresh-words-reach-kinds.md` as background.
> - **Labels:**
>   - **read**: I fetched and read the source at the link. Where a claim came only from a search engine's summary of a page, it says "(search excerpt)".
>   - **recall**: from memory, not checked today.
>   - **imagined**: my design inference or proposal.
> - **What I did:** read the sources and two passages of kernel code (`kinds.py:38-56`, `227-240`). I ran nothing against Agora.

## 1. Ink & Switch, Project Cambria (bidirectional lenses between schema versions)
Sources: the essay <https://www.inkandswitch.com/cambria/> and the repo <https://github.com/inkandswitch/cambria-project>.
- **The operators (read, essay):**
  - `rename`, `convert` (value maps), `wrap`/`head` (scalar ↔ array), `in` (apply a lens inside a field), `hoist`, `remove`, and `add` with a default.
  - One spec yields both directions.
  - The lenses act on JSON Patch *edits*, not whole documents (the edit lenses of Hofmann, Pierce and Wagner).
  - Versions form a graph, and translation follows the shortest path.
  - I believe the repo also has `plunge` and `map` (**recall**; the essay doesn't name them).
- **Translate on read (read):** "Data translations in decentralized systems should be performed on read, not on write."
  - Translating on write "struggled to handle new schemas getting added later on."
  - Each write is recorded in the *writer's* schema, and readers translate lazily.
- **Value conversion is where the guarantees break (read):**
  - `convert` "allows a developer to define separate forward and backward mappings", so it "can't guarantee a useful consistency relation."
  - Their example: `todo` and `doing` both map back to an unchecked box, with `default: false`. That round trip is lossy by construction.
- **Scalar ↔ array (read):** this has no clean answer. Old clients see only the first assignee, and the essay explores six write-back strategies, none ideal.
  - Nullability also blocks converting a non-nullable field into an array.
- **Missing data (read):** Reverse translations that need data the old format never held "require application logic outside of the lens system."
  - **Named trade-off (read):** "consistency" (both sides see an equivalent world), "conservation" (no one operates on data they can't observe) and "predictability" (local intent is preserved). Their conclusion: "there are limits to interoperability."
- **Not covered, and not shipped (read):**
  - Lens coverage is incomplete for "sorting, filtering, array splitting and merging, and **date formats**."
  - The team's own tracker was "too unstable to be our only system of record."
  - The README says Cambria "is still immature software, and isn't yet ready for production use."
- **For the draft (imagined):**
  - Cambria solved renames and left dates and value maps open. The draft's `time` type takes on the part Cambria deferred.
  - Cambria kept the writer's intent (its schema) on every write. The draft records only the real facts written.

## 2. Palantir Foundry Ontology interfaces
- **The owner declares the mapping (read, [implement an interface](https://palantir.com/docs/foundry/interfaces/implement-interface/)):**
  - An object type "must declare a mapping of existing object properties onto the required interface properties"; "if an interface property is marked as optional, mapping may be skipped."
  - Shared properties present on both sides "will be automatically mapped."
  - Required link and action constraints must each be satisfied by a concrete link or action type.
- **Interfaces are explicit and abstract (read, [overview](https://www.palantir.com/docs/foundry/interfaces/interface-overview/)):**
  - An object type *implements* an interface. There is no structural matching.
  - Interfaces can extend several parents. They can't be instantiated, and each instance is of a concrete type.
- **Actions on interfaces route edits through the mapping (read, [actions on interfaces](https://www.palantir.com/docs/foundry/action-types/actions-on-interfaces)):**
  - A Modify rule takes an "interface reference" parameter, and edits name *interface* properties.
  - Rules can't touch type-specific properties.
  - "Submission criteria apply uniformly across all object types that implement the interface."
  - A rule that changes a primary key fails, and so does a link action when a type has several concrete links for one constraint.
  - Action logs aren't supported for interface actions.
- **Types check; they don't convert (read):**
  - [Shared properties](https://www.palantir.com/docs/foundry/object-link-types/shared-property-overview/) share metadata, not data: "the underlying object data is not."
  - [Value types](https://www.palantir.com/docs/foundry/object-link-types/value-types-overview) are "semantic wrappers around a field type", described only as enforcing validation (regex, enum, range: [constraints](https://palantir.com/docs/foundry/object-link-types/value-type-constraints/)).
  - Values that fail validation make the object type "fail to index" (search excerpt of the same docs).
- **Parsing happens at ingest (recall):** typed pipelines and datasets parse values, and the ontology never parses a string into a date at read time.
- **For the draft (imagined):** This is the most production-proven cross-type system here, and it differs from the draft in two ways:
  - the *implementer* (the data's owner) declares the mapping, where Agora's *reader* guesses through spellings;
  - parsing happens at ingest, not on read.

  Its interface actions are the precedent for writing through a mapping automatically. The editor never names the concrete property.

## 3. Apple Shortcuts content graph, and Power Automate
- **Silent, automatic coercion (read, [Shortcuts guide](https://support.apple.com/guide/shortcuts/apd4618db957/ios), [Content Graph engine](https://support.apple.com/is-is/guide/shortcuts/the-content-graph-engine-apda4856024a/2.1/ios/12.0)):**
  - The content graph "automatically converts that content to the appropriate type". A calendar event passed to Show Directions yields only its location.
  - "Shortcuts assumes what you want to accomplish, and determines how to get there."
  - A View Content Graph action exists so you can see what happened.
- **Newer, owner-declared conversions (read, [IntentValueRepresentation](https://developer.apple.com/documentation/appintents/intentvaluerepresentation), iOS 26.4):**
  - An app's entity declares *export-only, import-only, or bidirectional* conversion to system values (`IntentPerson`, `PlaceDescriptor`).
  - So read-only conversion is first-class.
- **Where users get surprised (read, user reports):**
  - Dr. Drang found that a date parse failure silently fell back to the current date: "I don't understand the reversion to the current date when the parsing fails" ([leancrew](https://leancrew.com/all-this/2020/09/a-bug-that-isnt-and-an-error-that-is/)).
  - An Apple Community thread reports that Dutch "mrt" made a date action return today (search excerpt, [thread](https://discussions.apple.com/thread/256264885)). The date parsing depends on locale.
- **Power Automate (search excerpts of community blogs, not Microsoft docs):**
  - Parse JSON is strict: a null in a string field fails with "Invalid type. Expected String but got Null".
  - Users loosen the schema to `["string","null"]`. Changing the type to `any` made the field unreadable downstream ([Manuel Gomes](https://manueltgomes.com/microsoft/power-platform/powerautomate/how-to-solve-the-invalid-type-error/)).
  - Picking a field that comes from an array silently wraps the action in "Apply to each" ([Tom Riha](https://tomriha.com/stop-power-automate-flow-from-adding-apply-to-each-automatically/)). That's an implicit change of multiplicity.
- **For the draft (imagined):** The worst surprises are:
  - a silent fallback on a failed parse;
  - a parse that depends on something outside the value (locale);
  - a silent change of multiplicity.

  The draft's `unread` avoids the first. The draft says nothing about multiplicity (`assignee=Alex,Bea`).

## 4. JSON-LD type coercion, schema.org consumers, and the Postel's law critique
- **JSON-LD coercion labels; it doesn't parse (read, [JSON-LD 1.1](https://www.w3.org/TR/json-ld11/)):**
  - `@type` in a term definition makes a string a typed value. "Type coercion only takes place on string values, not for values which are maps" (§4.2.1 note).
  - I found no lexical validation in §4.2.
  - RDF says an ill-typed literal has "no literal value", but "Implementations MUST accept ill-typed literals and produce RDF graphs from them" ([RDF 1.1 Concepts](https://www.w3.org/TR/rdf11-concepts/) §3.3).
  - So the data stays, and no value is claimed. That is the draft's `unread`.
- **Scoped contexts (read, JSON-LD §1.4, §1.7):** a term means different things in different scopes, and `@protected` stops a context from being overridden.
  - This is the mechanism for the draft's homonym argument (`at` is a place in one vocabulary and a screen point in another).
- **schema.org is lenient on purpose (read, [data model](https://schema.org/docs/datamodel.html)):**
  - "some data is better than none."
  - Consumers "are not obliged to treat unexpected structures as errors."
  - Text where a Thing is expected is accepted.
  - Its `DateTime` is ISO 8601 with an optional `Z` or offset ([DateTime](https://schema.org/DateTime)).
- **Google's event rules (read, [Event docs](https://developers.google.com/search/docs/appearance/structured-data/event)):**
  - Dates are ISO 8601, and a date alone "means the date regardless of the timezone".
  - "If no timezone is provided, Google uses the timezone of the event's location."
  - Midnight placeholders are "likely wrong unless the event was meant to start at midnight."
  - Errors surface to the owner in Search Console ("The time or date is incorrect").
- **Membership vs reach at web scale (read, [policies](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)):** "Items that are missing required properties are not eligible for rich results." The page stays indexed; the feature is withheld.
- **RFC 9413 on Postel's law (read, [RFC 9413](https://www.rfc-editor.org/rfc/rfc9413.html)):**
  - "ignoring faulty or ambiguous input is almost always the incorrect solution" (§2.1).
  - Tolerance causes protocol decay and "bug-for-bug" de facto standards (§4). "No implementation can hope to avoid having to trade correctness for interoperability indefinitely" (§4.1).
  - It recommends "virtuous intolerance": well-specified fatal errors that make faults visible (§5.1).
  - Workarounds are fine if documented with an end state and a removal plan (§5).
- **HTML5's answer (search excerpt, [Hickson, 2006](https://lists.w3.org/Archives/Public/public-whatwg-archive/2006Dec/0277.html)):** every error has an explicitly specified recovery, so leniency is identical in every implementation.
  - A closed set of kernel types with one implementation is in this family. That lowers the risk of the decay RFC 9413 describes, though not to zero.

## 5. "Parse, don't validate" (Alexis King)
Source: [lexi-lambda.github.io](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/) (read).
- **Parse vs validate:** a validator returns "the type that contains no information". A parser returns a refined value that carries the proof forward.
- **Shotgun parsing:** checks scattered through processing let invalid data be partly acted on before a late check fails.
  - That is Agora today: the kernel checks *presence*, then the module re-reads raw facts and crashes on format (calendar trial).
- **"Push the burden of proof upward as far as possible, but no further."** Parse at the boundary, once.
- **Denormalized copies drift.** Keep one source of truth, or confine the duplication behind one trusted module.
- **For the draft (imagined):**
  - "Fits means reads", with the reading handed to the module as `thing`, is exactly this pattern. The check and the use can no longer disagree. This is the draft's strongest idea and the evidence backs it.
  - "But no further" supports not typing kinds strictly (question 1).
  - King's boundary is ingest, though. The draft parses on every read, because facts are never changed. That's defensible (Cambria, RDF), but then the parse must be a pure function of its inputs, and the cache must know all of them (risk 3 below).
- **Two spellings are a denormalized copy (read, code):** today `Need.met` takes the first non-empty spelling silently (`kinds.py:48-56`), and `filled` fills the shape's name only when it's empty (`kinds.py:233`). A thing saying both `start` and `starts`, with different values, reads as whichever comes first, and nobody is told.

## 6. Schema evolution: Avro, Protobuf, GraphQL
- **Avro resolution (read, [spec 1.12](https://avro.apache.org/docs/1.12.0/specification/)):**
  - Fields are "matched by name". A writer-only field is ignored. A reader-only field takes the reader's default, and with no default "an error is signalled."
  - Promotions only widen: int→long/float/double, long→float/double, float→double, string↔bytes.
  - An enum symbol the reader lacks takes the reader's `default`, or is an error.
- **Avro aliases are the reader's (read):**
  - "Aliases function by re-writing the writer's schema using aliases from the reader's schema." Implementations "may optionally" support them.
  - The draft's `title|name|summary` is an Avro reader alias. This is good precedent.
  - Avro resolves once per *writer schema*, though, not per record. It has no case where two spellings are present on one record.
- **Avro logical types (read):**
  - Unknown or invalid logical types are ignored, and the underlying type is used.
  - Avro keeps `timestamp-millis` (UTC instant) and `local-timestamp-millis` ("no time zone reference") as *different* types.
- **Protobuf (read, [proto3](https://protobuf.dev/programming-guides/proto3/), [ProtoJSON](https://protobuf.dev/programming-guides/json/)):**
  - Identity is the field number, so renames are safe in binary and unsafe in JSON and TextFormat, where you reserve old names.
  - ProtoJSON parsers accept both the lowerCamelCase/`json_name` and the original name, but printers emit one. That's alias on read, one name on write.
  - Timestamps: "Offsets other than "Z" are also accepted", but output is "always … Z-normalized". A Timestamp is an instant, and any offset is discarded.
  - Integer narrowing truncates silently. Wire-compatible changes are advised against for schemas used outside your organization.
- **GraphQL (read, [Oct 2021 spec](https://spec.graphql.org/October2021/)):**
  - An implementing type "must include a field of the same name for every field" of the interface: no aliasing in the schema. Return types are covariant.
  - Input coercion is strict (Int: "only integer input values are accepted").
  - Result coercion may convert only without loss. 1.0→1 is fine, and 1.2 to Int is a field error.
  - Mapping from storage names lives in each type's resolvers, as code (**recall**).
- **For the draft (imagined):** Every production evolution system has:
  - reader-side aliases or stable ids;
  - only widening implicit conversions;
  - an *error*, never a silent lossy conversion;
  - a declared default or an error for an absent field.

  None parses free-form strings into dates on read. The draft's type table is closest to GraphQL's "convert only without loss" rule. That's the right rule, and the writes in §3.4 should be held to it too.

## 7. Date and time interoperability
- **iCalendar (read, [RFC 5545](https://www.rfc-editor.org/rfc/rfc5545.html)):**
  - Three DATE-TIME forms: floating, UTC (`Z`), and local with `TZID`. "The form of date and time with UTC offset MUST NOT be used" (§3.3.5).
  - Floating times SHOULD be read "as being fixed to whatever time zone the "ATTENDEE" is in at any given moment" (§3.3.5).
  - Basic format only: "no separator characters" (§3.3.4). `TZID` "MUST NOT be applied to DATE properties."
  - A DATE DTSTART is an anniversary or all-day event, and its DTEND "MUST be specified as a DATE value also". DTEND is non-inclusive, and a DATE with no end lasts one day (§3.6.1).
  - `GEO` is "two SEMICOLON-separated FLOAT values", latitude then longitude (§3.8.1.6).
- **CalDAV (read, [RFC 4791](https://www.rfc-editor.org/rfc/rfc4791.html)):**
  - For queries, floating values use the request's time zone, then the calendar's `calendar-timezone`, or else "the time zone of their choice" (§7.3).
  - §8.1 lists legal client actions that "degrade interoperability", including "the start/end time values can be translated from the original time zone to another time zone" ([text](https://icalendar.org/CalDAV-Access-RFC-4791/8-1-client-to-client-interoperability.html)).
- **Google Calendar API (read, [events reference](https://developers.google.com/workspace/calendar/api/v3/reference/events)):**
  - All-day events use `date` (`yyyy-mm-dd`).
  - `dateTime` needs an offset unless `timeZone` is given, so there's no floating timed event.
  - `timeZone` is *required* for recurring events: it "specifies the time zone in which the recurrence is expanded."
  - `end` is exclusive.
- **Offsets aren't zones (read, [RFC 9557](https://www.rfc-editor.org/rfc/rfc9557.html)):**
  - An offset alone is "unsuitable for performing local-time operations", and zone rules change (§1.2, §3.4).
  - It adds `2026-11-23T15:00-08:00[America/Los_Angeles]`, with `!` marking a critical tag.
- **Temporal keeps them apart (read, [docs](https://tc39.es/proposal-temporal/docs/)):**
  - Its types are `Instant`, `ZonedDateTime`, `PlainDate`, `PlainDateTime`, `PlainTime` and more.
  - Separate classes "prevent bugs caused by incorrectly assuming 0, UTC, or the local time zone". Fixed offsets are "discouraged."
- **Coordinate order (read):** GeoJSON positions are "longitude and latitude … precisely in that order" ([RFC 7946](https://www.rfc-editor.org/rfc/rfc7946.html) §3.1.1). `geo:` URIs are latitude/longitude ([RFC 5870](https://www.rfc-editor.org/rfc/rfc5870.html) §2).
- **For the draft (imagined):**
  - The canonical `time` "carries its offset" (§3.2). That collapses four distinctions every calendar standard keeps (date, floating, zoned, instant) into two (date, offset).
  - Writing that canonical form into an iCal `dtstart` is invalid iCalendar, which is the trial's failure again.
  - Resolving a floating time to an offset at read time is the zone translation RFC 4791 §8.1 warns against.
  - And refusing floating times when no zone is known blocks a calendar that could emit them perfectly well as floating.

## 8. Bidirectional transformation and lens theory
Source: Foster, Greenwald, Moore, Pierce and Schmitt, *Combinators for Bi-Directional Tree Transformations*, TOPLAS ([pdf](https://www.cis.upenn.edu/~bcpierce/papers/lenses-toplas-final.pdf)); read §3 and §10.
- **A lens is `get: C → A` and `put: A × C → C` (Def. 3.1).** Put takes the *old concrete source*, so it can restore what the view hides.
- **The laws (Def. 3.2), quoted as stated:**
  - **GetPut:** `put(get c, c) ⊑ c`. If you put back an unchanged view, you "must get back exactly c."
  - **PutGet:** `get(put(a, c)) ⊑ a`. Put "must capture all of the information contained in the abstract view."
  - Optional **PutPut** gives "very well behaved" lenses. They drop it because `map`, `flatten`, `merge` and conditionals fail it "for reasons that seem pragmatically unavoidable."
- **Totality matters (Def. 3.3 and note 3):** "well-behavedness is rather trivial in the absence of totality". An undefined put is vacuously lawful, so the work is making put defined wherever it's needed.
- **Oblivious lenses (Def. 3.7, Lemma 3.9):** a put that ignores the old source is lawful only if `get` is a *bijection*.
  - "Write canonical whatever the old form was" is an oblivious put. Date formats aren't a bijection (`20261106` and `2026-11-06` read the same), so it breaks GetPut.
- **Create:** for parts of the view with no concrete counterpart, put "fills in" defaults (§2, the default URL example).
- **Quotient lenses (search excerpt, [ICFP 2008 abstract](https://www.icfpconference.org/icfp2008/accepted/96.html)):** Foster, Pilkiewicz and Pierce relax the laws to hold "modulo equivalence relations chosen by the programmer", through *canonizers* tracked in types.
  - That's the theory behind "canonical form": a canonizer. The equivalence must be one the *owner app* honours. The iCal adapter does not treat `2026-11-06` as `20261106`.

## 9. Writing back through a view (the view update problem)
- **Two classical positions (read, via Foster et al. §10):**
  - Bancilhon and Spyratos (1981): a translation is reasonable only if it leaves a fixed *complement* (everything the view hides) unchanged. Then there is at most one translation.
  - Gottlob, Paolini and Zicari's "dynamic views" are more permissive.
  - Well-behaved lenses correspond to dynamic views, and very well behaved ones to constant-complement translators.
  - Dayal and Bernstein's "exactly performing an update" is roughly PutGet. Their answer to an unreasonable update is to *let the translation fail*.
- **Keller's criteria (read, Foster et al. §10):**
  - "No database side effects: only update tuples in the underlying database that appear somehow in the view."
  - No unnecessary changes.
  - Replacements that can't be simplified.
- **Hegner's open and closed views (read, Foster et al. §10):** open is for users who know they're editing through a view; closed is for users kept isolated from the base. He adds *monotonicity* as a further condition.
- **PostgreSQL, as practice (read, [CREATE VIEW](https://www.postgresql.org/docs/current/sql-createview.html)):**
  - A view is automatically updatable only over one base relation, with no aggregates, DISTINCT, set operations and so on.
  - "A column is updatable if it is a simple reference to an updatable column of the underlying base relation; otherwise the column is read-only, and an error will be raised."
  - `WITH CHECK OPTION` rejects writes that would make the row leave the view.
  - Anything else needs `INSTEAD OF` triggers, where "the notion of reasonableness is left entirely to the programmer" (Foster et al.).
- **For the draft (imagined):** Write-through is safe exactly where Postgres says so:
  - **Safe:** a spelling rename is a simple column reference.
  - **Updatable only with a lawful inverse:** a typed value is a computed column, so its write needs the inverse to obey GetPut and PutGet.
  - **Read-only:** values from a hop (a person by name, a point from a place id, a zone from the nearest place) are joins.
  - **Re-check after the write:** the draft has no `CHECK OPTION`. After a write through the shape, the thing should still read under the word.

---

## What this means for the draft

### The draft's open questions

**Q1. Is "membership is has, reach is reads" right? Yes, with two conditions.**
- **The evidence:** this is the pattern with the most support (read):
  - RDF must accept ill-typed literals but gives them no value.
  - Google keeps the page indexed but withholds the rich result.
  - Avro falls back to the underlying type when a logical type is invalid.
  - GraphQL errors at the field, not the document.

  Palantir is the counterexample (failing values block indexing). But Palantir owns its ingest, and Agora takes foreign things as they come.
- **Condition 1 (RFC 9413, Search Console):**
  - **The rule:** unread must reach someone who can fix it, or tolerance decays into permanent fuzz.
  - **Proposal (imagined):**
    - `rows unread` (or `kinds <thing>`) lists them;
    - a kind shows its unread count;
    - a thing's maker gets one plain notice, not one per refusal.
- **Condition 2:** lists show the raw value marked as unread, never a blank or a guess. Shortcuts' fallback to today is the cautionary case.

**Q2. Should a module's answer lines get `through=` automatically? Yes, for the thing it was handed. I disagree with the draft here.**
- **The evidence:**
  - **Palantir:** interface actions name interface properties, and the platform routes them to each type's mapped property; the editor never names the concrete one (read).
  - **The module only knows the shape's names.** Writing those names raw onto the handed thing creates a second spelling, which is a denormalized copy (King).
  - **That breaks the owner app:** the House's `status=paused` beside `state` is exactly this.
  - **Fix 6's note doesn't help here:** it lets the raw write through with a note (FRICTION.md, fix 6), and a module has no one reading the note.
- **Proposal (imagined):**
  - Answer lines whose target is the handed thing default to `through=<called word>`. An explicit opt-out writes raw, and the record shows which.
  - **If Alex prefers explicitness:** make it a *refusal*, not a note, when a module answer writes a shape name onto the handed thing while that thing spells it otherwise.
  - **Why a refusal is fine for modules:** they're code and can be fixed. That's RFC 9413's virtuous intolerance, and unlike fix 6, there's no person at a prompt being blocked.

**Q5. Is "canonical when unsure" safe for the owner app? No.**
- **Four sources say so:**
  1. **GetPut:** putting back an unchanged value must leave the thing unchanged. "Canonical regardless" is an oblivious put, lawful only for bijections (Lemma 3.9), and date forms aren't one.
  2. **RFC 5545 forbids the offset form.** Canonical `…T15:00-08:00` written into `dtstart` is invalid iCalendar.
  3. **RFC 4791 §8.1** names translating start and end times to another zone as degrading interoperability.
  4. **Writing a datetime into a DATE-valued `dtstart`** turns an all-day event into a midnight one. That's Google's "likely wrong" placeholder.
- **Proposal (imagined):**
  - Each type's read returns `(value, form)`, and its write is `write(value, form)`.
  - Any form the reader accepts must be writable. If it can't be, stop accepting it.
  - If the new value can't be expressed in the existing form without loss, the write *refuses* and says why. Dayal and Bernstein let such translations fail; GraphQL raises an error rather than lose information. Examples: a datetime into a DATE, a zone into a floating value, a fraction into an integer.
  - The canonical form is used only to *create*: when the aspect is absent, or the old value was unread and so has no form. It is always said.

**Q6. Where should types live? On the need is defensible, but not alone.**
- **For the draft's choice:** the reader declares, like Avro reader schemas and JSON-LD contexts, and JSON-LD's scoped contexts exist for exactly the `at` homonym (read).
- **Three changes (imagined):**
  - **(a) Repeated on every word, the types will drift.** Kinds carry typed needs (`event needs="title start|starts|dtstart:time"`), and words inherit them through `acts_on`, which already exists. That's JSON-LD's shared contexts and Palantir's shared properties.
  - **(b) Fold the board's `field_types` into the kind's typed needs.** Two type systems for one aspect are another denormalized copy.
  - **(c) Let the owner declare too.** A kind may type its own aspects (`window … at:screen`), and the owner's type vetoes a reader's guess.
    - That's Palantir's implementer-declared mapping and Apple's owner-declared conversions.
    - It's also the only fix the prior art offers for `at=45,60` passing as a place (friction 6). Reader-side types can't catch it.

### The biggest risks the prior art predicts
1. **Lossy write-back corrupts the owner's data.**
   - **What goes wrong:** forms change, zones are translated, all-day becomes timed, and lists are cut to one element.
   - **The evidence:** Cambria's hardest problems were exactly these, and it never shipped them. RFC 4791 §8.1 and RFC 5545 §3.3.5 name the calendar cases.
2. **One `time` type is too coarse, and its canonical form throws away the zone.**
   - **The evidence:** every serious system keeps date, wall-clock (floating), zoned and instant apart: Temporal, RFC 9557, iCalendar, Avro's local vs UTC timestamps, and Google requiring `timeZone` for recurrence.
   - **What goes wrong:** collapsing them at read time breaks floating events (medicine at 8am), recurring events across DST, and faithful iCal output.
3. **Readings that depend on more than the thing.**
   - **The dependencies:**
     - `person` by unique name depends on who else exists;
     - `point` from a place id, and floating times from the nearest place's `timezone`, depend on other things;
     - everything depends on the reader's sight.
   - **What breaks:**
     - The draft's cache key, `(thing, rev, shape)` in §5, is therefore wrong.
     - Readings flip when a second Alex appears. Shortcuts' locale-dependent dates are the cautionary case.
     - A reading assembled with the *caller's* sight could hand a module data its own grant excludes.
   - **The rule (imagined):** read as the caller narrowed to the module, the way mid-call `see` lines already run (`kernel.py:1677` per the draft).

### Concrete changes I'd make (all imagined)
1. **Split `time` by kind, keeping one type name.** The canonical value is tagged as one of:
   - `date` (`2026-11-06`);
   - `local`, i.e. floating (`2026-11-23T15:00`);
   - `zoned` (`2026-11-23T15:00-08:00[America/Los_Angeles]`, the RFC 9557 form);
   - `instant` (`…Z`).

   Reading never resolves a floating time. A need that must have an instant says `start:instant`, and only then does the place's `timezone` apply, with the zone used recorded in `read`. A calendar word can then write `VALUE=DATE`, floating, or `TZID` faithfully.
2. **Make form-preserving writes a lens.**
   - **The shape:** `read → (value, form)` and `write(value, form)`.
   - **The tests:** property tests of GetPut and PutGet for every (type, form) pair, run over the trial corpus. The eight calendar formats are the first fixture.
   - **On loss:** refuse; never write canonical over an existing form.
3. **Write through only what is a simple column.**
   - **Writable:** spelling renames, and typed values with a lawful inverse.
   - **Read-only through a shape:** hop values (person by name, point from a place id) in v1.
   - **Re-read after every `set … through=`:** the value must read back equal (PutGet), and the thing must still fit the word (Postgres's `CHECK OPTION`).
4. **Report spelling conflicts.** When several spellings are present and they disagree once typed, that's `unread: {start: "conflict: start=… dtstart=…"}`, not first-wins (`kinds.py:48-56`). A write through refuses until the conflict is settled.
5. **No ambiguous forms in the default readers.**
   - **`time`:** an 8-digit number is both a basic ISO date (`20261106`) and plausible epoch seconds. Read epoch only where the owner declares it.
   - **`point`:** accept only latitude-first forms (`lat,lon`, `geo:`, iCal's `;`). A GeoJSON-order pair in range (Italy's `10.5,45.2`) would silently land in Somalia, and no range check can catch it.
6. **Say what a typed need does with a list** (`assignee=Alex,Bea`). Make it unread, or require a `list` marker, rather than take the first element. Cambria explored six write-back strategies here and found none ideal, and Power Automate shows what happens when a tool loops implicitly.
7. **Record the intent with the write.** Keep the real fact written (as the draft says), and add `through=`, the canonical value, and the form used. That's Cambria's lesson about the writer's schema, and it lets undo, the hearing, and later readers see both.
8. **Default `through=` for module answers on the handed thing** (Q2 above).
9. **Fix the cache and the sight.**
   - **The key:** `(thing, rev, shape, reader)` plus the revs of anything a reading hopped to. Or ship v1 without hops: no person-by-name, no point-from-id, no zone from the place (questions 3 and 4 then wait).
   - **The sight:** a module's `thing` is read as the caller narrowed to the module.

### Where the evidence supports the draft as written
- **"Fits means reads", one function handed to the module:** parse, don't validate. This is the core, and it's right.
- **A small, closed, deterministic set of types in the kernel:** the HTML5 approach to leniency, which avoids RFC 9413's drift between implementations.
- **Reader-declared spellings:** Avro aliases. The thing's facts are never changed by a reading: RDF and Cambria's translate-on-read.
- **`read`/`unread` provenance:** what Shortcuts needed a debugging action for. Make it visible in `look`, not only to code.
- **Value meaning (friction 2) stays out:** this matches Cambria, whose `convert` is exactly where its guarantees broke.

### What would change my mind
- **A rerun of the trials with GetPut and PutGet tests passes for every form in the corpus,** with canonical fallback never reached. Then Q5's refusal rule is moot in practice, though I'd still keep it as the guard.
- **Floating and recurring times are vanishingly rare in Alex's world** (count `dtstart` values without `Z` or `TZID`, and `rrule`s). Then the time split could wait. Reading still must not turn floating into an offset.
- **Owners in practice declare types on their kinds,** making reader-side types redundant. Then types belong on the kind or the aspect (Q6's alternative), not the need.

## Not verified
- **Palantir:** I didn't find its rule for type compatibility between interface and object properties ("compatible" is undefined in the pages I read). The "fail to index" claim comes from a search excerpt.
- **Apple and Microsoft:** I found no official Apple doc on Shortcuts' failure modes, and no official Microsoft doc for the Power Automate claims; those are user reports and blogs.
- **Papers I read only second-hand:**
  - Bancilhon and Spyratos, Dayal and Bernstein, Keller, and Hegner, only through Foster et al.'s related work;
  - Quotient lenses, only through the abstract.
- **JSON-LD lexical validation:** I inferred its absence from §4.2 and RDF Concepts §3.3. I didn't read the expansion algorithm.
- **Agora code:** apart from `kinds.py:38-56` and `227-240`, the code references are the draft's, not mine.
