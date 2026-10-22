# Grouped action sources

Source implementation for a9377, reviewed contract a9434/c9439.
Consumer rollout, production policy installation and lifecycle actions are separate.

```text
rows actions:<recipient>:<policy> counted=yes
rows actions:<recipient>:<policy> counted=no
rows action-reasons:<recipient>:<policy>:<group-key>
rows action-reasons:<recipient>:<policy>:<group-key> eligible=yes
```

Use a person id or unambiguous person reference for recipient, and a note id for
policy. There is no default recipient. Both sources project the same evaluator;
one evaluation is shared within `scene.still`, with defensive row copies and no
cache across builds. Groups use canonical subject/surface identities and bound
person ids, never titles or appearance ids. Keys are opaque.

Required policy props:

| Prop | Value |
| --- | --- |
| `action_recipient` | Person id, or name bound at the event that authored this prop |
| `action_designs` | World selection of eligible designs |
| `action_reviews` | World selection of eligible reviews; overlap is intentional |
| `action_group_later` | World selection of explicitly deferred whole targets |
| `action_review_later` | World selection of deferred review reasons only |

Use the literal `none` for an empty selection. Missing/blank required props,
unknown policy/recipient, malformed selectors and plain title strings refuse.
Optional `action_design_label` and `action_review_label` default to `design` and
`review`. Optional `action_question_news` is a world selection of question parents
or targets that are news (e.g. closed cards); default `none`. This selection never
excludes a permission. Consumer policy authors must supply their closed-card
selection; the source contains no production design/review/closed-card predicate.

Rowan's staged policy uses `prop:action_defer=later` for whole-target Later and
`prop:review=later` for review-only Later. They are distinct. Review deferral never
defers a sibling reason. A group is Later only through the explicit group selector.
Overlapping design/review membership yields one group and two reasons.

Group fields: `key target title later reason_count counted uncertainty recipient item`.
Reason fields: `request_key kind source asker recipient asker_source recipient_source resolution_state
resolution_evidence later eligible uncertainty key target label asker_label
recipient_label item`. `asker` and `recipient` are person ids; readable labels are
separate. `reason_count` counts eligible unresolved reasons. Resolved, excluded
news and uncertain reasons remain inspectable; there is no clear operation.
Unknown/uncertain rows are diagnostic, never counted as Alex's duty. In mixed
groups, a known permission still counts even if another reason is diagnostic.

Alex's consumers must filter **groups with `counted=yes`**, and their open reason
lists with **`eligible=yes`**. A resident diagnostic lens can read `counted=no` or
all reasons of any group. An unresolved reason excluded as news remains open,
with empty resolution evidence; exclusion is not resolution.

Use actual lens `each` syntax (the round-one sketch omitted it):

```text
root : column, of actions:alex:POLICY counted=yes as group, each card
card : column
  title : text "$group.title"
  reasons : column, of action-reasons:alex:POLICY:$group.key eligible=yes as reason, each detail
detail : text "$reason.label — $reason.resolution_state"
```

Counters can use `count actions:alex:POLICY counted=yes later=no` (or `later=yes`)
on a non-repeating part. No production lens is changed here.

## Evidence and legacy typing

Chat roots use `mark=ask request_kind=question|permission`. Comment storage only
retains its own `mark`, so the original asker can classify the exact comment by
replying under `id=<root>` with `mark=question|permission`. The original asker can
likewise classify an untyped chat root with an exact threaded reply carrying
`request_kind=question|permission`. First authored valid type is retained; a typed
permission cannot become a question to acquire a weaker ending rule. Untyped
legacy roots are diagnostic until classified; the source never reads their prose
to infer a permission or an answer.

Ordinary questions resolve on a reply from the event-time recipient threaded to
that exact root. A reply to another root, an unthreaded later line, or a reply
from someone else does not resolve it. Alternatively the original asker can
reply with `mark=answered evidence=<exact-thread-reply-id>`; the evidence must
belong to this root. An asker's own `resolve id=<comment-root> line="<evidence>"`
also supplies an exact asker mark. The evidence field returns that reply/mark id,
not the old `sayings.answered` result (which is never read).

Typed permission chats resolve only on an exact threaded reply carrying
`resolution=accept|decline` by the original recipient, or `resolution=withdraw`
by the original asker. Comment equivalents are exact replies marked
`accept|decline|withdraw`. These are authored evidence, not a new action UI or an
authority grant. Generic replies, answered marks and comment resolve do not end
permissions. Native requests use their own authorized accept/decline/withdraw
events. Acceptance answers the request, even though its resulting promise remains
open. Confirm, report, release, parent closure and offer answers are not permission
answers. Undone events are ignored.

Native target/recipient come from original ask arguments; chat targets come only
from explicit about/context or chat talk_of, otherwise the root itself. Comments
are explicitly attached to their subject. Invalid authored targets become
diagnostic, never title matches. Event-time person binding preserves predecessors.
Design/review provenance walks retained before-images to the current membership
activation, without mutating the world. Reopening has a fresh reason key.
Unavailable before-images or comment-dependent eligibility without full snapshots
produce unknown-asker diagnostics rather than invented provenance. No archive
files or session worlds are opened by the evaluator.

Native request identity fallback (a9693, Juniper c9707): when the referenced
ask origin is absent from retained history, stored `to` and `asked_by` may
supply recipient and asker. An existing person id remains that identity; a name
resolves only if it has had exactly one bearer in the persons index. Missing or
ambiguous identities remain diagnostic. An undone origin is not absent history.
A retained native ask always wins, even with missing/invalid `to` or author.
For a migrated request whose retained origin is a legacy `prop` event without
a `to` argument, only the recipient uses this stored fallback; the asker stays
event-derived. If that event names an `awaiting` recipient, its event-time
identity must agree with the stored recipient, otherwise the row is uncertain
and neither recipient is selected. No other retained origin admits fallback.
Native reasons expose `recipient_source=event|stored` and
`asker_source=event|stored`, including diagnostic rows; these fields describe
identity provenance, not consent. Other reason kinds do not use these fields.
Group rows remain aggregates: inspect `action-reasons` for provenance.
Fallback never resolves a request or changes permission enforcement; only its
own recipient's accept/decline or original asker's withdraw is terminal.

## Checks

`test_action_queue.py` builds only in-memory synthetic worlds. It covers the
contract's grouping, evidence, authority, Later/news, diagnostics, identity,
nested source/count equivalence and read-only requirements, plus ordinary stale
refusals preserving viewer/draft records. Full synthetic consumer texts are
retained and restored with exact inverse edits. These checks do not certify
production consumer rollout, real browser geometry or lifecycle activation.
