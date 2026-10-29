# Prior art for value meaning

> Prior-art research for value meaning (friction 2), by a research agent for Claude, 28 Oct 2026.
> - **Background:** I read `trials/FRICTION.md` §2, `trials/tasks-rebuilt/FINDINGS.md` findings 5–6, [[shape-reads]] draft 2 (§6, producer spellings) and [[shape-reads-prior-art]]. This file doesn't repeat what that review covered (Cambria's `convert`, Palantir, lens laws).
> - **Labels:**
>   - **read**: I fetched and read the source at the link. "(search excerpt)" means I saw only a search engine's summary of the page.
>   - **recall**: from memory, not checked today.
>   - **imagined**: my own inference or design.
> - **What I did:** read the sources below and two passages of Agora code (`modules/house/builders.py:24-43`, `kernel/next_steps.py:15`). I ran nothing against Agora.

## In short

**Proven**
- **Owner-declared categories.** Every major tracker lets owners make custom values, and each value's owner assigns it, when it is created, to one member of a small fixed set the platform holds:
  - Jira: 3 categories + "No Category";
  - Linear: 5 types users can pick, plus 2 the system owns;
  - Notion: 3 groups.
  Cross-project queries use the category (JQL `statusCategory`). (read)
- **Meaning as read-only predicates.** OSLC Change Management states the problem exactly: knowing every status value "does not reveal the semantics of a state".
  - **The answer:** each server translates its own statuses into standard read-only boolean predicates (`closed`, `inProgress`, …).
  - Writing a predicate gets 409 Conflict; state changes go through actions. (read)
- **Explicit "no mapping".** FHIR ConceptMap has `noMap` and an `unmapped` mode, and says "Mappings are one way". (read)

**Failed, or known to fail**
- **Too few categories.** Jira's three can't say "cancelled", and Jira ends up with three disagreeing notions of done:
  - the category;
  - the Resolution field;
  - the rightmost board column.
  Atlassian has called this "not a bug" since 2021. (read)
- **Growing a fixed set breaks consumers.** Linear added a Duplicate type in 2026, and its own UI then listed duplicates in "active buckets" until a fix. (read)
- **Spellings within one vendor.** Jira's own default filter used the wrong spelling of a category (`"New"`). GitHub spells "not planned" three ways across REST, GraphQL and search. (read)
- **Sync tools map in the connection.** Their failures (read):
  - case-sensitive lookups;
  - unmapped values passed through raw;
  - many-to-one reverse writes that pick "the first value listed";
  - echo loops;
  - transitions that "silently fail".
- **Inventing values on write.** A Notion page write with an unknown select name adds a new option to the schema. Status writes refuse instead. (read)

---

## 1. Status groups in work trackers

### Jira
- **Three fixed categories (read, [statusCategory KB](https://support.atlassian.com/jira/kb/how-to-search-using-statuscategory-statuscategorychangeddate-function-with-jql/)):**
  - The admin page shows "ToDo, Inprogress, and Done as the three status categories."
  - JQL `statusCategory` supports only `IN, NOT IN, =, !=`.
  - `statusCategoryChangedDate()` says when an issue entered its current category.
- **The owner declares the category when the value is made (read, Jira Cloud OpenAPI `swagger-v3.v3.json`):**
  - `StatusCreate` has `required: ["name","statusCategory"]`.
  - Its enum is `TODO | IN_PROGRESS | DONE`.
- **Four spellings of one category (read):**
  - A live `/rest/api/3/statuscategory` returns:
    - `{1, "undefined", "No Category"}`;
    - `{2, "new", "To Do"}`;
    - `{4, "indeterminate", "In Progress"}`;
    - `{3, "done", "Done"}`.
    ([developer community post](https://community.developer.atlassian.com/t/bad-documentation-for-rest-api-3-statuscategory/78565)).
  - The official example response shows keys `in-flight` and `completed` with ids 1 and 9, which don't exist. The poster asks for "one sentence, that the categories are fixed".
  - So the same category is spelled `To Do` (name), `new` (key), `TODO` (write enum) and `2` (id).
- **Jira's own filter used the wrong spelling (read, [JRACLOUD-78014](https://jira.atlassian.com/browse/JRACLOUD-78014)):**
  - The default "My Open Issues" filter shipped `statusCategory in ("New", "In Progress")`, and "'New' is not a valid status category".
  - It was fixed in December 2021.
- **Who may change it, and how far a change reaches (read, [rename a status](https://support.atlassian.com/jira-cloud-administration/docs/rename-a-status-in-a-workflow/)):**
  - A space admin or app admin can change a category along with the name.
  - "this will affect all spaces that use the workflow".
  - "Updating a status won't notify the teams that use it."
  - **Team-managed spaces:** a category change on a shared status updates "all your space's workflows that use the status". To change one workflow only, copy the status ([team-managed statuses](https://support.atlassian.com/jira-software-cloud/docs/create-edit-and-delete-statuses-in-team-managed-projects/)).
- **Three notions of "done" that disagree (read):**
  - **Resolution** ([KB](https://support.atlassian.com/jira/kb/best-practices-on-using-the-resolution-field-in-jira-cloud/)):
    - "Jira considers that the lifecycle of an issue has come to an end when the "Resolution" field has a value."
    - The "resolved" series of reports (Created vs Resolved) uses it.
    - A resolution literally named "Unresolved/None" makes the issue "seen as resolved". A placeholder value reads as present.
    - The KB lists "Open Issues" returning Done-category issues as a symptom of misconfiguration.
  - **Rightmost board column** ([KB](https://support.atlassian.com/jira/kb/done-or-resolved-work-items-are-shown-as-incomplete-when-closing-sprints/)):
    - Closing a sprint counts as complete only "work items set to a status that is mapped to the rightmost column".
    - The status category and resolution don't matter.
  - **Atlassian's answer** ([JSWCLOUD-15106](https://jira.atlassian.com/browse/JSWCLOUD-15106)):
    - In 2021: "Though not ideal in some cases, the behaviour in-product today is not a bug."
    - It became a suggestion to "allow you to specify which status category is considered done on a board and in existing reports".
    - It is still "Gathering Interest", with 49 votes.
  - **No cancelled category:** cancelled work is Done with a resolution such as "Won't Do" (recall, for the default resolution names).

### Linear
Source: Linear's published SDK schema ([schema.graphql](https://github.com/linear/linear/blob/master/packages/sdk/src/schema.graphql)), downloaded today.
- **The type is a string with a known set (read):**
  - `WorkflowState.type` is `String!`, documented as "One of "triage", "backlog", "unstarted", "started", "completed", "canceled", "duplicate"."
  - It is not a GraphQL enum.
- **Users pick five; the system owns two (read):** `WorkflowStateCreateInput.type`: "Valid values: backlog, unstarted, started, completed, canceled. The type determines how the state is treated in workflow progression and reporting." `triage` and `duplicate` are therefore system-owned.
- **The type drives behaviour (read):**
  - An Issue has `startedAt`, `completedAt` ("moved into completed state"), `canceledAt` and `autoClosedAt`.
  - A Team has `autoCloseStateId`, `markedAsDuplicateWorkflowState` and `defaultIssueState`.
  - States belong to a team, can be `inheritedFrom` a parent team, and are ordered "within their type group".
- **Projects use a different set (read):** `ProjectStatusType` is `backlog, canceled, completed, paused, planned, started`. Projects can be paused; issues have no paused type.
- **From the docs (search excerpt, [configuring workflows](https://linear.app/docs/configuring-workflows); the page is client-rendered and I couldn't fetch its text):**
  - The default order is Backlog > Todo > In Progress > Done > Canceled.
  - The categories' order is fixed.
  - A status can be removed "as long as at least one status exists in each category".
  - Duplicate is system-managed and can't be renamed.
- **Adding a type broke a consumer: Linear's own (read, [changelog, 21 May 2026](https://linear.app/changelog/2026-05-21-project-slack-channels)):**
  - "Duplicate issues now use a dedicated status type".
  - In the same post, a fix: "Duplicate issues now appear in the canceled section in focus-grouped issue lists instead of active buckets."

### Notion
- **Three fixed groups (read, [status guide](https://www.notion.com/help/guides/status-property-gives-clarity-on-tasks)):** you "can't change the three main categories" (To-do, In progress, Complete). Options are added under them.
- **How the API places options (read, [property object](https://developers.notion.com/reference/property-object), [schema updates](https://developers.notion.com/reference/update-property-schema-object)):**
  - Status has `options` and `groups`, and each group lists its `option_ids`.
  - "Use `group` to place an option in `To-do`, `In progress`, or `Complete`."
  - "A new option uses `To-do` if that group exists". That's a declared default category for an option nobody placed.
- **Same vendor, opposite write rules (read, [page property values](https://developers.notion.com/reference/page-property-values)):**
  - **Select:** "A new option name adds an option to the schema if your connection can write to the parent data source." The write invents a value.
  - **Status:** "A page write does not create a new status option or set its group." The write refuses.
- **Matching (read, schema updates):** "Names match without regard to case or surrounding spaces, so `high` keeps the existing `High` option."

### GitHub
- **Two-level state (read, [REST issues](https://docs.github.com/en/rest/issues/issues#update-an-issue)):**
  - `state` is `open | closed`.
  - `state_reason` is `completed | not_planned | duplicate | reopened | null`, and it's "Ignored unless state is changed".
  - A bad value gets 422 "Validation failed".
- **Different spellings by channel (read):**
  - **GraphQL:** `IssueState` is `OPEN | CLOSED`, and `IssueStateReason` is `COMPLETED | DUPLICATE | NOT_PLANNED | REOPENED` ([GraphQL issues](https://docs.github.com/en/graphql/reference/issues)).
  - **Search:** `reason:complete` or `reason:"not planned"` ([changelog, 19 May 2022](https://github.blog/changelog/2022-05-19-the-new-github-issues-may-19th-update/)).
  - So one vendor spells one value three ways.
- **A reason added to an existing closed set (read, same changelog):**
  - `state_reason` arrived in 2022.
  - The post doesn't say what issues closed earlier received. I believe it's `null` (recall).
  - `reopened` is a reason on an *open* issue. The reason records the last transition, not the current state.
- **Projects: a separate Status field, coupled by workflows (read, [built-in automations](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations), [changelog, 25 Apr 2024](https://github.blog/changelog/2024-04-25-github-issues-projects-auto-close-issue-project-workflow/)):**
  - "set the status to Done when an issue is closed".
  - Auto-close closes issues "when their project status is changed to "Done"" or "any custom status you define".
  - It's on by default for new projects, and "anyone with write or admin access" can enable it on existing ones.
  - Which close reason it writes isn't stated.
- **A rename (search excerpt, community report):** after "Done" was renamed "Deployed", 'Item closed' still moved items to the status originally named Done. The coupling follows the option's identity, not its label.

### Other task vocabularies
- **Microsoft To Do (read, [todoTask](https://learn.microsoft.com/en-us/graph/api/resources/todotask)):** `notStarted, inProgress, completed, waitingOnOthers, deferred`. That's two kinds of held, and no cancelled.
- **Google Tasks (read, [tasks](https://developers.google.com/workspace/tasks/reference/rest/v1/tasks)):** status is only `needsAction` or `completed`, plus `deleted` and `hidden` flags.
- **Trello (read, [object definitions](https://developer.atlassian.com/cloud/trello/guides/rest-api/object-definitions/)):**
  - There's no status. `closed` is "Whether the card is closed (archived)", and `dueComplete` is a boolean.
  - The lane is `idList`.
  - Here "closed" means archived, not done.
- **Asana (recall):** a `completed` boolean with `completed_at`. Sections act as lanes, and status-like custom fields are separate.
- **Canvas (read, [submissions](https://canvas.instructure.com/doc/api/submissions.html)):**
  - The submission's `workflow_state` is `submitted, unsubmitted, graded, pending_review`.
  - Separate booleans: `missing`, `late`, `excused`.
  - The meaning sits on the *submission*, a different object from the assignment.

### What the trackers show (imagined from the above)
- **Everyone converged on two levels:**
  - free values, owned by the workflow's owner;
  - each value declared into a tiny fixed set held by the platform;
  - cross-cutting features (JQL, timestamps, auto-close, reports) keyed on the set, never on labels.
- **The set's size is the hard part.**
  - **Three is too few:** Jira can't say cancelled, so meaning leaks into a second field and reports disagree.
  - **Splitting closed works:** Linear separates completed from canceled; FHIR (§3) goes further.
- **Held is the least standard.** It's present in MS To Do (two kinds), FHIR `on-hold` and Linear *projects* (`paused`). It's absent from Jira, Linear issues, GitHub, iCalendar and Google Tasks.
- **Every set grew** (GitHub reason 2022, Linear duplicate 2026). Consumers that switched on the flat value broke.

## 2. Sync tools that translate values

### Unito
Sources: [map fields](https://guide.unito.io/how-to-map-fields), [statuses and sections](https://docs.unito.io/how-to-map-statuses-and-sections/) (read).
- **Mapping:** values are paired per flow with the gear icon, and "+" groups several values into one.
- **Automatic matching:** "Unito will do some smart mapping on behalf of the customer if the names are similar between tools."
- **Reverse of a group:** "Unito will always prioritize the first value listed in a grouped set of statuses."
- **A group may be preserved:**
  - The grouped example's two-value side "will only change from Incomplete to Complete" if the other is "marked closed, rejected or resolved".
  - That suggests a value already inside the group is kept, but the page doesn't say so outright (imagined reading).
- **Unmapped:** "If you don't map them, Unito will automatically set statuses according to a flow's rules."
- **One-way:** an edit at the destination is overwritten the next time the source changes.

### Getint
Source: [N-to-1](https://docs.getint.io/getintio-platform/workflows/mapping-multiple-statuses-to-one-n-to-1-in-getint) (read).
- **Reverse of a group:** the first mapped status is the default, and "the source side will always use this default status when syncing values back". **Set Default** changes it.
- **Transitions can refuse:** "The destination status might not allow incoming transitions from all mapped source statuses."
- **Unmapped:** treated as a configuration error; the fix is to add the status.
- **Not stated:** whether a value already inside the group is kept.

### Exalate
Source: [GitHub status sync](https://docs.exalate.com/docs/github-status-sync) (read).
- **A script on each side:** "You need to configure the mapping between statuses on both sides."
  - GitHub → Jira: `["open":"To Do","closed":"Done"]`.
  - Jira → GitHub: the reverse map, written separately.
- **Unmapped values pass through raw:** `issue.setStatus(statusMap[remoteStatusName] ?: remoteStatusName)`.
  - The community's guard is "only apply statuses that are on the mapping" ([thread](https://community.exalate.com/t/ignoring-statuses-in-the-status-map/4467)).
- **A case bug (read, [thread](https://community.exalate.com/t/how-do-i-two-way-sync-status-between-jira-and-github/4796)):** the GitHub → Jira direction failed until "the words "Open" and "Closed" needed to start with a lowercase letter". The staff script in the same thread uses capitalised keys.
- **Newer helper (search excerpt):** `Status.receive(...)` takes a `workflowMapping` and `useRemoteStatusByDefault`.
- **Lost reasons (imagined):** the documented map covers `state` only, so GitHub's `state_reason` is lost both ways.

### Zapier
Source: [lookup table](https://help.zapier.com/hc/en-us/articles/8496305146765) (read).
- The key column "is case-sensitive".
- The optional fallback is "a value to be used if there is no matching key". But "the fallback value is only used when there are existing values but no matches": a blank input yields nothing.

### Jira's own git integration
Source: [smart commits](https://support.atlassian.com/jira-software-cloud/docs/process-issues-with-smart-commits/) (read).
- **Commands name workflow transitions.** A command "only considers the part of a transition name before the first space".
- **Silent failure:** "If any other fields have been set as required the transition command will silently fail."
- **Other failures:** the commit still lands and an email is sent.

### Loops
Source: [Atlassian developer community](https://community.developer.atlassian.com/t/avoiding-endless-loops-on-jira-issue-events/70447) (read).
- **The cause:** a synced write "triggers an issue event within Jira, which will spawn another message".
- **The fixes offered:**
  - flag self-generated events;
  - "ignoring an update if it doesn't change anything".
- **The platform:** suppression was spiked but hasn't shipped.

### What sync tools show (imagined from the above)
- **The map lives in the connection:** one per pair and per direction, so N×M by construction.
- **Four tools, four unmapped behaviours, none of them "unknown":**
  - raw pass-through (Exalate);
  - a fallback constant (Zapier);
  - "flow rules" (Unito);
  - a configuration error (Getint).
- **Many-to-one reverse uses a declared default.** That's lossy unless the write is skipped when the target already holds a value from the group. "Skip a no-op" is also the loop fix.
- **Writes go through the target's own transitions,** which may refuse, sometimes silently.

## 3. Standards

### iCalendar
Source: [RFC 5545 §3.8.1.11](https://www.rfc-editor.org/rfc/rfc5545#section-3.8.1.11) (read).
- **Values per component:**
  - VEVENT: `TENTATIVE | CONFIRMED | CANCELLED`;
  - VTODO: `NEEDS-ACTION | COMPLETED | IN-PROCESS | CANCELLED`;
  - VJOURNAL: `DRAFT | FINAL | CANCELLED` ("journal is removed").
- **One token, different questions:** a VEVENT's values are about *certainty*; a VTODO's are about *progress*.
- **The set is closed:** `statvalue` has no `iana-token` or `x-name` alternative (`CLASS` has both). So `STATUS:PAUSED` is invalid, and iCalendar has no held.
- **Case:** §2 says "All names of properties, property parameters, enumerated property values and property parameter values are case-insensitive". §3.1 adds "all other property values are case-sensitive, unless otherwise stated."
- **Related properties:** `COMPLETED` (a UTC datetime) and `PERCENT-COMPLETE` (0–100, each assignee's own part).

### iTIP
Source: [RFC 5546 §3.2.5](https://www.rfc-editor.org/rfc/rfc5546#section-3.2.5) (read).
- **Cancelling:** STATUS "MUST be set to CANCELLED to cancel the entire event". When uninviting attendees, it "MUST NOT be included".
- **Instances:** one instance is cancelled through `RECURRENCE-ID`, and `SEQUENCE` is incremented.
- **Not covered:** §3.2.5 doesn't say whether an attendee's client deletes the event or marks it cancelled.

### Google Calendar API
Source: [events](https://developers.google.com/workspace/calendar/api/v3/reference/events) (read).
- **Spelling:** `confirmed | tentative | cancelled`, lower case, where the RFC says `CANCELLED`.
- **Two meanings, by context:**
  - "cancelled" means "The event is cancelled (deleted)".
  - For exceptions of a recurring event, it means "this instance should no longer be presented to the user".
  - "All other cancelled events represent deleted events. Clients should remove their locally synced copies."
- **Other clients (recall, unverified):** Outlook keeps a cancelled meeting, prefixed "Canceled:", until the user removes it.

### SKOS
Source: [SKOS Reference §10](https://www.w3.org/TR/skos-reference/#mapping) and Appendix A (read).
- **The match properties:**
  - **`exactMatch`:** "a high degree of confidence"; transitive and symmetric.
  - **`closeMatch`:** "sufficiently similar that they can be used interchangeably" in some applications. It is deliberately *not* transitive, "to avoid the possibility of "compound errors" when combining mappings across more than two concept schemes".
  - **`broadMatch` and `narrowMatch`:** hierarchical, and inverses of each other.
  - **`relatedMatch`:** associative.
- **Rules:**
  - `exactMatch` is disjoint with `broadMatch` and `relatedMatch` (S46).
  - By convention, mappings link concepts "in different concept schemes".
  - "applications must be able to cope with cycles".
- **A concept scheme** is "an aggregation of one or more SKOS concepts", with one `prefLabel` per language (S14). Unique notations are a convention only.
- **For Agora (imagined):**
  - An owner's value relates to a shared concept by `exactMatch` or `broadMatch`.
  - A question about a concept *narrower* than the mapped one has no answer from the mapping (unknown).
  - Chains are safe only through exact matches.

### schema.org
- **Event status (read, [EventStatusType](https://schema.org/EventStatusType)):** EventCancelled, EventMovedOnline, EventPostponed, EventRescheduled, EventScheduled.
- **Action status (read, [ActionStatusType](https://schema.org/ActionStatusType)):** Active, Completed, Failed, Potential, under `StatusEnumeration`.
- **What Google does with them (read, [event structured data](https://developers.google.com/search/docs/appearance/structured-data/event)):**
  - **Absence:** "If you don't use this field, Google understands the `eventStatus` to be `EventScheduled`". The consumer declares what absence means.
  - **On change:** "DON'T remove the startDate".
  - **Rescheduling:** `previousStartDate` requires EventRescheduled.
  - **Spelling:** examples use full URLs (`https://schema.org/EventCancelled`).
- **Postponed is held, for events (imagined).**
- **Leniency (read, [data model](https://schema.org/docs/datamodel.html)):** type associations are "closer to 'guidelines' than to formal rules".

### Wikidata: values as items
- **Values are items (read, [data types](https://www.wikidata.org/wiki/Help:Data_type)):** an Item value is a "Link to an item". Strings are for text that doesn't "need to be translated".
- **Labels don't identify (read, [labels](https://www.wikidata.org/wiki/Help:Label)):**
  - Labels are per language, and a label "does not need to be unique".
  - Only the label and description *pair* must be unique.
- **Merges keep references working (read, [redirects](https://www.wikidata.org/wiki/Help:Redirects)):**
  - A merge leaves a redirect.
  - Statements aren't switched at once, so that a merge can be undone; a bot relinks them "within a few days".
  - Ids are never reused.
- **Constraints advise; they don't block (read, [constraints](https://www.wikidata.org/wiki/Help:Property_constraints_portal), [one-of](https://www.wikidata.org/wiki/Help:Property_constraints_portal/One_of)):**
  - One-of and similar constraints are "hints, not firm restrictions".
  - Violations show on the entity's page and in database reports.
  - A "mandatory" status marks the severe ones.
- **The lesson (imagined):** identity is separate from the label, so case and language become display questions.

### OSLC Change Management 3.0 (OASIS): the closest prior art
Sources: [spec §2.9](https://docs.oasis-open-projects.org/oslc-op/cm/v3.0/os/change-mgt-spec.html), [vocabulary](https://docs.oasis-open-projects.org/oslc-op/cm/v3.0/os/change-mgt-vocab.html) (read).
- **The problem it names:** "different CM servers may use different properties (or even a set of properties) and different values to represent the change request's state. Even providing access to meta data does not help because knowing all possible state values does not reveal the semantics of a state."
- **Its answer, state predicates:**
  - They are "single-value often read-only Boolean properties … that allow servers to translate their specific status string values into a standard boolean state predicate value".
  - **Example:** `status="BeingInvestigated"` gives `closed=false, inProgress=true, fixed=false, approved=false, reviewed=false, verified=false`.
  - "An attempt to update read-only predicates SHOULD be answered with a 409 Conflict".
  - "Predicates MUST be queryable".
  - State changes go through OSLC Actions (CM-41).
- **Version 3.0 adds `oslc_cm:state`:**
  - Standard individuals: Closed, Inprogress, Fixed, Approved, Reviewed, Verified.
  - "Servers MAY define additional individuals".
  - The string `oslc_cm:status` is deprecated.
- **What it misses:**
  - There is no cancelled and no held. Closed is "Completely done, no further fixes or fix verification is needed", so done and dropped are both "closed".
  - Even its own vocabulary drifts in case: the predicate is `inProgress`, the individual `Inprogress`, its label `inprogress`.
- **Adoption (recall):** IBM Jazz/ELM and a few bridges; not Jira, GitHub or Linear.

### HL7 FHIR
- **TaskStatus (read, [TaskStatus](https://hl7.org/fhir/R5/codesystem-task-status.html)):** draft, requested, received, accepted, rejected, ready, cancelled ("The task was not completed"), in-progress, on-hold ("started but work has been paused"), failed, completed, entered-in-error. The code system is case-sensitive.
- **Case rules (read, [CodeSystem.caseSensitive](https://hl7.org/fhir/R5/codesystem-definitions.html)):**
  - "If this value is missing, then it is not specified whether a code system is case sensitive or not."
  - "When the rule is not known, Postel's law should be followed: produce codes with the correct case, and accept codes in any case."
- **ConceptMap (read, [R5](https://hl7.org/fhir/R5/conceptmap.html)):**
  - **Direction:** "Mappings are one way - from the source to the target system. In many cases, the reverse mappings are valid, but this cannot be assumed".
  - **Relationships:** `related-to, equivalent, source-is-narrower-than-target, source-is-broader-than-target, not-related-to`. Broader and unrelated maps need comments.
  - **No mapping:** `noMap = true` says explicitly that no target exists.
  - **Unmapped values:** `unmapped.mode` is `use-source-code | fixed | other-map`, "the "default" to be applied when there is no target concept mapping specified".
  - **Context:** `dependsOn` handles "multiple mappings depending on the values of other elements".
- **businessStatus (recall):** FHIR Task also has a free `businessStatus` beside `status`, so a domain's own states sit beside the shared lifecycle.

## 4. Case and normalisation

| System | How values compare | Known by |
|---|---|---|
| iCalendar | enumerated values case-insensitive; other values case-sensitive | read, RFC 5545 §2, §3.1 |
| FHIR | each code system declares `caseSensitive`; when unknown, write the correct case and accept any case | read |
| Notion select (schema updates) | case and surrounding spaces ignored | read |
| Zapier lookup | case-sensitive keys | read |
| Exalate | Groovy map, exact match; users hit it | read (community) |
| GitHub | REST `closed`/`not_planned`; GraphQL `CLOSED`/`NOT_PLANNED`; search `reason:"not planned"` | read |
| Jira category | `To Do` / `new` / `TODO` / `2`; its own filter shipped `"New"` | read |
| Google Calendar | `cancelled`, vs the RFC's `CANCELLED` | read |
| Wikidata | identity by Q-id; labels are free text | read |

**Lessons:**
- **One vendor, several spellings.** A vendor ships several spellings of one value across its channels. Comparing labels breaks even inside one vendor (read: GitHub, Jira).
- **Identities work; labels display.** The systems that work compare identities (Jira category id, Linear type key, Wikidata Q-id, OSLC URI) and use labels only for display (read).
- **Fold when comparing, write the owner's spelling.** When labels must be matched, compare case-insensitively but write in the owner's spelling.
  - iCalendar lets producers differ in case.
  - FHIR says "produce codes with the correct case".
  - Notion folds case and spaces when matching.
  (read; the rule is imagined)
- **Locale-free folding (recall):** locale-sensitive case mapping (the Turkish dotted and dotless i) differs from locale-free case folding. Use locale-free folding (Python `str.casefold`), or ASCII-only folding for codes.
- **Folding needs a collision check (imagined).** A vocabulary where `Done` and `done` mean different things can't be folded. FHIR's case-sensitive code systems allow that in principle, so the check belongs where the vocabulary is declared.

## 5. Where should the mapping live?

### What the evidence shows
- **On the producer, into a fixed hub, at the moment the value is made:**
  - **Where it's used:**
    - Jira (category required on create);
    - Linear (type required);
    - Notion (group, with To-do as the default);
    - OSLC (the server computes its predicates);
    - schema.org (the publisher picks the enumeration value);
    - Palantir interfaces and App Intents (previous review).
  - **Cost:** N+M.
  - This is the pattern with production proof (read).
- **On a shared hub vocabulary with published maps:**
  - **Concept schemes and code systems:** SKOS concept schemes; FHIR code systems plus ConceptMaps, each with a publisher "responsible for the release and ongoing maintenance".
  - **The canonical data model (read, [EIP](https://www.enterpriseintegrationpatterns.com/patterns/messaging/CanonicalDataModel.html)):**
    - "design a Canonical Data Model that is independent from any specific application".
    - With 6 applications that's 30 translators direct versus 12 through the model.
    - **Its stated costs:** "an additional level of indirection"; it "seems complicated if only a small number of applications participate".
- **In each consumer:**
  - **Where:** sync tools, Zapier/Make lookups, Exalate scripts.
  - **Cost:** N×M; each map drifts on its own, and the owner never sees it.
  - **Agora today does this (read, code):**
    - `builders.py:25` has `HELD = {'yes','true','1','paused','held','blocked','cancelled','canceled'}`.
    - `next_steps.py:15` has `HELD = {"paused","cancelled","trashed","permission","permission-held","unknown"}`.
    - They disagree, and neither has `closed`, `not_planned` or `COMPLETED`. That's the trial's 507 closed-but-buildable issues.

### Governance
- **The platform fixes the hub.** Users can't add categories (Jira, Notion, Linear). New concepts come from the vendor, rarely, and they broke consumers (read: GitHub 2022, Linear 2026).
- **The workflow's owner places values** (space admin, team admin, database editor). Changes propagate everywhere, silently: "won't notify the teams that use it" (read).
- **Consumer maps belong to whoever built the connection;** the vocabulary's owner never sees them (imagined, from §2).
- **Wikidata advises rather than blocks.** It keeps constraints advisory and makes violations visible to editors and in reports (read).

---

## What this means for Agora

### The trial's values under the recommended mechanism (imagined)

| Value seen in the trials | Concept | Notes |
|---|---|---|
| Tracker `status=Done` | done | |
| GitHub `state=closed` + `state_reason=completed` | done | |
| GitHub `closed` + `not_planned` | dropped | |
| GitHub `closed` + `duplicate` | duplicate (a kind of dropped) | |
| GitHub `closed`, no reason | closed | `done?` is unknown |
| iCal VTODO `COMPLETED` | done | |
| iCal VTODO `CANCELLED` | dropped | |
| iCal VEVENT `CANCELLED` | dropped | Google's "deleted" and "skip this instance" are both dropped *for that thing* |
| iCal VEVENT `TENTATIVE` | open | certainty is a different question, not a life stage |
| Canvas submission `submitted`, `graded`, `pending_review` | done | on the *submission*: "due soon" reads my submission through a bond, not a value on the assignment (friction 4) |
| Alex's cards `lane=Done` | done | the lane is a thing (dk79-style), so it can carry the meaning itself (B below) |
| The House's `status=paused` | held | an overlay by another actor (point 6 below) |

### Recommended: life concepts held by the kernel; meanings declared by each vocabulary's owner; read as three-valued questions (imagined)

1. **A small hierarchy the kernel holds and versions**, like Jira's categories, Linear's types and Notion's groups, but split where they proved too coarse:
   ```
   open      not-started · active · held
   closed    done · dropped (duplicate)
   unknown
   ```
   - **Why this shape:**
     - Linear's unstarted/started/completed/canceled;
     - FHIR's `on-hold`, and MS To Do's waiting and deferred, for held;
     - Jira's three is too few, and OSLC lacks cancelled.
   - **Growth:** the hierarchy grows only by adding *narrower* concepts under existing ones. Then a word asking `closed?` keeps working when `duplicate` arrives, which is the Linear lesson.
   - **Candidates the evidence shows but the trials don't need:** `failed`, `rejected`, `entered-in-error` (FHIR); `postponed` (schema.org) under held.
2. **The owner declares meanings, on its kind,** where draft 2 §6 already put producer spellings. For example:
   ```
   gh-issue        means="state: open=open closed=closed; state_reason: completed=done not_planned=dropped duplicate=duplicate"
   ical-todo       means="status: NEEDS-ACTION=not-started IN-PROCESS=active COMPLETED=done CANCELLED=dropped"
   ical-event      means="status: TENTATIVE=open CONFIRMED=open CANCELLED=dropped"
   issue           means="status: Backlog=not-started Now=active Paused=held Done=done Cancelled=dropped"
   ```
   - The most specific aspect wins: `state_reason` refines `state`.
   - This is N+M. It sits with the people who know the vocabulary, as in Jira, Linear and OSLC.
3. **Words ask questions,** `done?`, `closed?`, `dropped?` and `held?`. Each answers **yes / no / unknown**, with the aspect and raw value that decided it in the reading's provenance.
   - **The rule (from SKOS's broad/narrow):**
     - yes if the value's concept is the one asked or narrower;
     - no if it's disjoint;
     - unknown if it's broader, or unmapped.
   - **The builder** starts only on `open? = yes` and `held? = no`, so unknown refuses. Paid work never starts on a guess.
   - **"Due soon"** skips `done? = yes` and shows unknown with a mark.
   - **Lists filter on the question,** and case and spelling stop mattering to readers (the 24/37 trial).
4. **Matching declared values:**
   - compare with locale-free case folding and trimmed spaces;
   - the declaration refuses two values that fold together but mean different things;
   - the raw value is always kept in the reading.
5. **Writes never write the concept.** `move <thing> to=done` goes through the owner's declaration:
   - **(a) Already there:** if the thing already answers `done? = yes`, write nothing.
     - That's GetPut, from the lens laws in the earlier review.
     - It removes Unito's and Getint's lossy "first value listed" rewrites, and it is the "ignore an update that doesn't change anything" loop fix.
   - **(b) Declared write:** else, if the owner declared a write for `done` (e.g. `writes="done: state=closed state_reason=completed"`), write those facts in the owner's spelling and case.
     - Prefer the owner's own word when there is one (`issue.close`); dispatch already prefers it.
     - This is Getint's "Set Default", made explicit and visible.
   - **(c) Otherwise refuse,** naming what the vocabulary can say: "gh-issue can't say held; it says open, or closed (completed, not planned, duplicate)".
     - `status=paused` to GitHub is refused.
     - The precedents: iCalendar's closed grammar, OSLC's 409, Notion's status writes.
   - **(d) Never invent a value** (Notion select is the cautionary case), **and never fall back to the raw name** (Exalate's `?: remoteStatusName`).
6. **Held is often another actor's overlay.** The House pausing a task isn't the Tracker's lifecycle.
   - When the owner can't say held, the House writes its *own* hold fact (who held it, and why).
   - `held?` reads the owner's value *or* any hold overlay.
   - That fixes the trial's `status=paused` → "set lane=paused" advice without writing into another app's vocabulary. (FHIR's `businessStatus` beside `status` is the nearest precedent, recall.)
7. **Many-to-one and unmapped values:**
   - **Many-to-one:** reading many values into one concept is lossless; writing follows 5(a)–(c).
   - **One-to-many:** where an owner's value is broader than the question (Jira Done with no resolution asked `dropped?`), the answer is unknown, never a guess.
   - **Unmapped:**
     - **The answer:** unknown, counted, and told once to the kind's owner. The precedents: Wikidata's constraint reports, and the earlier review's unread notice.
     - **An optional default:** the owner may declare one (FHIR `unmapped.mode=fixed`), which the basis shows.
     - **What absence means:** declared too, like Google's absent `eventStatus` = scheduled; unknown by default.
8. **Governance uses the existing kind rules.** Changing a value's meaning (moving `Paused` from held to dropped) changes what words do.
   - Treat it like narrowing: check the words that act on the kind, record it, and tell their owners.
   - Jira's silent propagation is the case to avoid.

### Alternative B: values as things (imagined; the trial's option (c))
**The design:** each vocabulary value is a world thing carrying `means=<concept>`, and kinds point at their value things. This is the Wikidata pattern, and Alex's lanes already are things.
- **For:**
  - a value can be renamed without breaking anything, and merges redirect;
  - members can see values, discuss them and annotate them.
  - Reading was correct in the trial (ran there: 528 ms for 2,174 cards).
- **Against:**
  - every read hops through another thing, which draft 2 removed from the kernel for cache and sight reasons;
  - it makes many small things;
  - it still needs the hub concepts.
- **Best use:** as A's storage later, or for vocabularies Alex edits by hand (lanes).

### Alternative C: consumer-side maps (imagined; today's option (a), plus per-word sets or SKOS-style pairwise maps)
**The design:** each app brings its own words, and each cross-app reader keeps its own value sets, or vocabularies are mapped pairwise.
- **For:** no kernel change, and it's local.
- **Against:**
  - it's N×M;
  - Agora already has two disagreeing HELD sets;
  - every sync-tool failure in §2 applies;
  - `closeMatch` doesn't compose across three vocabularies.

**Worth naming too: normalise at import (EIP's canonical model at the edge).** It's fine for read-only feeds. It fails for two-way apps, whose own code needs their own values left intact.

### What would change my mind
- **If owners don't declare,** because most vocabularies arrive as loose notes with no kind of their own (draft 2 §8), A has nowhere to live. Then B (value things anyone can annotate) or C.
- **If the hub creeps:** real words need more than about ten concepts, or separate branches per domain (an event's certainty against a task's progress). Then one hub is wrong, and per-domain concept schemes linked SKOS-style are better.
- **If unknown dominates:** a rerun shows a large share of task-like things answering unknown to the questions words actually ask. Then refusing on unknown blocks real work, and owner defaults become required, not optional.
- **If meanings often depend on context** (Google's two "cancelled"s; Canvas's state on the submission), a flat value-to-concept map isn't enough. It needs FHIR's `dependsOn`, or bonds.
- **If every producer is an Agora-written adapter,** normalising at import is simpler.

## Not verified
- **Linear docs:** the pages are client-rendered and I couldn't fetch their text. The Linear claims are from its published SDK schema (read) and from search excerpts of the docs.
- **Jira:** the category keys come from a developer-community post showing a live response, not from official docs (whose example is wrong). The default resolution names (e.g. "Won't Do") are recall.
- **Unito and Getint:** neither says whether a value already inside a group is preserved on reverse sync.
- **Search excerpts only:**
  - Exalate's `Status.receive`;
  - the GitHub "Done renamed Deployed" report.
- **Calendar clients:** how Outlook and Apple show CANCELLED is recall. I didn't read RFC 5546 beyond §3.2.5.
- **Recall:**
  - OSLC adoption;
  - Asana fields;
  - FHIR `businessStatus`;
  - GitHub's null reason on issues closed before 2022.
- **Agora:** I ran nothing and counted nothing in Alex's world. The mapping table above is on paper.
