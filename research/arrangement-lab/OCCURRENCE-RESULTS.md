# Installed Notes occurrences — 2026-09-16

This experiment implements one documented idea: an arrangement item has its own
identity while referring to shared content. The supplied transcript states this
at lines 62, 193–200 and recommends reusing the existing board action at line 170.
[Selection and scope were written before implementation](DOCUMENTED-NEXT.md).

## Assessment of the documented work

**Supported:** separating content from arrangements; pure planning followed by
guarded application commits; distinguishing saved state from observed rendering.
Earlier example-fixture trials supplied useful evidence, but are not evidence of
improvement over the latest installed environment. This experiment now validates
occurrence identity inside the actual installed Notes/board package lineage.

**Promising and underexplored:** shared interaction mechanics, adapters for surfaces
with different placement semantics, and bounded inspection derived from the same
facts used by the human interface. The installed system already contains more of
the necessary machinery than the earlier example baseline showed.

**Overstated:** the early “parity for free” claim, which the transcript itself later
qualifies. Sharing a projection implementation does not establish equal authority,
discovery, freshness, or useful descriptions. Nor do universal appearance objects
or a common rectangle representation establish composability. A calendar placement
may change time; a task-column move may change status. Those require domain rules.

**Still uncertain:** the minimal descriptor for nested, custom surfaces; ownership
when maintained layouts interact with manual movement; reference permissions and
transfers; how thin independently written adapters can remain. This experiment
does not settle those questions, and introduces no new contract for them.

## Baseline and candidate

The baseline uses a coherent read-only capture of all ten installed package
definitions, their immutable build receipts, and current schemas at world watermark
6461. Native Agora4 source is separately frozen and hashed. Relevant origins:

| Package | Source revision | Installation revision |
|---|---:|---:|
| studio.boards | 2 | 2 |
| agora.notes | 10 | 7 |
| agora.shell | 44 | 39 |
| agora.documents | 13 | 12 |

This is an **installed-package slice with synthetic subjects**, not a clone of
Alex's entire active world. Local object revisions are rebased. Both model trials
use the same captured inventory, synthetic Planning/Review boards, native client,
model settings, dedicated execution VM, and observation-browser capabilities.
The live world, resident VM and resident conversation were not modified.

The candidate changes the installed board and Notes packages from the inside:

- Optional occurrence IDs for adding/removing references; omitted IDs retain the
  existing duplicate-add refusal. Existing records retain their IDs.
- Card rendering, drafts, and placement reconciliation keyed by occurrence ID;
  reading/editing still uses the shared subject ID.
- Ambiguous removal refuses; explicit removal retains content and other occurrences.
- The existing Add existing UI can add another appearance of an included note.
- Both insertion paths enforce unique occurrence IDs.

The existing `layout` action, board schema, shell bridge and native writer are
unchanged. One additional compatibility delta was necessary: Notes' manifest
declared an older annotations schema. Installation correctly refused until the
candidate reused the captured schema's existing optional tracking field. No world
schema or annotation data was migrated. General schema dependency/version policy
remains a separate question; this trial does not solve it.

## Real JEFF comparison

The matched request was to add another appearance of the risks note to Planning,
move only that appearance 40 pixels right, preserve Review and the original,
and inspect both open Planning views without authoring a workaround.

| Trial | Result | JEFF elapsed | Dispatched calls |
|---|---|---:|---:|
| Baseline | `add_note` refused duplicate inclusion; JEFF accurately stopped | 45.66 s | 17 |
| Candidate | Added shared occurrence and moved it through existing actions | 58.94 s | 21 |

The candidate made two mutation calls: `add_note`, then `layout`. Their measured
dispatch times were 0.69 and 0.86 seconds. JEFF described occurrence-ID insertion
as direct, and noted that moving right required calculating the absolute x value.
That is a report from one conversation, not an objective usability score or reason
to add another operation. Most remaining calls concerned discovery and rendering.

This is a **capability improvement, not a measured speedup**. The baseline refused
a task the candidate completed; their elapsed times measure different outcomes.
The current shell presents the open views as tabs. JEFF inspected both candidate
tabs, while its baseline report correctly acknowledged incomplete visible-geometry
verification. A hidden tab's zero viewport must not be treated as missing content.

## Verification and retained failures

Passed in the isolated candidate through real guest actions and browser input:

- Two occurrences of one subject render in each Planning tab when activated.
- JEFF moves only the new occurrence. A subsequent keyboard move targets it too.
- Review and the original placement remain unchanged.
- A content edit reaches all occurrences in both open views.
- Each window retains its own zoom while sharing the same arrangement.
- Stale revision, unknown batch member, duplicate ID, and ambiguous removal refuse
  without partial board changes. Explicit removal leaves content and Review intact.
- Human Add existing creates a distinct occurrence.
- Competing edits in the two occurrences save one version and retain the conflicting
  draft under the other occurrence ID; both editor values survive browser reload.
- Native event replay reproduces state after the adversarial/browser checks.

Failures were retained rather than relabelled as passes: the first candidate's
schema installation refusal; a post-model harness call using `arguments` instead
of `args`; and a later harness `Packages.get` signature error. The first candidate
implementation also missed occurrence-ID collision checks in `create_note`. The
guest counterexample and final guard verification are recorded separately.
The final guard refused the collision with no note creation or board mutation;
ordinary creation still succeeded, and final replay passed across 77 objects.

The model conversation and UI suite exercised the first functional occurrence
patch. The subsequent insertion guard is a narrow additional change tested through
guest execution; there was no new model conversation after that guard.

## Architectural conclusion and stopping point

This strengthens the documented direction without promoting the earlier lab model
into a universal framework. Stable occurrence identity already fits the existing
arrangement, action, rendering and recovery paths. The useful abstraction is the
distinction between content and occurrence, not a requirement to create a separate
world object for every occurrence.

The representative OAS vision remains a larger target: these two actions are two
transactions, not one grouped intent with one undo; this slice does not implement
the semantic selection funnel or homogeneous cross-application arrangement. The
older prototype findings remain useful hypotheses for that work.

Before implementing a general inspection layer, the next question for a separate
ideation agent is:

> What minimum projection-backed surface contract lets JEFF discover nested logical
> children and permitted placement operations, while distinguishing saved arrangement,
> per-window state, and fresh rendered measurements? Specify how it handles hidden
> tabs, duplicate subjects, non-geometric placement, omitted facts, and guarded commits,
> using the existing action/projection paths rather than a second source of truth.

No general inspection, transfer, dependency resolver, or maintained-layout framework
was invented during implementation. Candidate package changes remain isolated and
reviewable; they have not been deployed to the live world.

## Artifacts

- [Candidate source transformations](occurrence_candidate.py).
- [Reviewable installed-to-candidate package diff](occurrence-package.diff).
- [Condensed evidence, including failed attempts](evidence/occurrence-trials.json).
- [Matched native/model trial](occurrence_trial.py).
- [Adversarial and browser verification](occurrence_verify.py).
- [Insertion collision counterexample/repair](occurrence_collision.py).
- Private raw reports, exact package sources, tool traces and screenshots:
  `C:\Projects\Agora\local\arrangement-current-20260916`.
