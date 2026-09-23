# Live JEFF comparison — September 16, 2026

Status: **baseline mismatch found by Alex; current-world comparison withdrawn;
example-fixture experiments preserved.** The completed
runs below used the repository's example application bundles, not the currently
installed world-authored environment. They are integration experiments only and
must not be presented as a comparison against the most recently built Agora.

The September 16 read-only check found the actual world running shell source
revision 44 at installation revision 39, Notes source revision 10, Documents
source revision 11, and additional installed packages including `studio.boards`,
`lab.presentation`, `studio.packets`, `studio.comments`, `studio.documents`,
`studio.research`, and `parallel.split`. Those packages and the newer shell were
omitted from the trial fixture. In particular, claims that a capability had to be
built because the baseline lacked it do not describe the current installed world.

## Method and evidence boundary

These trials use the real `agora3.jeff.Jeff` adapter and managed OpenAI account,
GPT-6 Astra at medium reasoning, the actual native gateway, SQLite journal,
installed packages, a Linux execution VM, a distinct candidate-yard VM, and an
authenticated headless Edge browser. JEFF receives structured DOM observations;
it does not receive screenshot vision. Screenshots are retained for separate review.
This is not Alex's Chrome and is not a voice-call test.

The native-code baseline is a frozen copy of the current **Agora4 working tree**, including
its existing uncommitted changes, rather than an arbitrarily chosen old commit.
The candidate adds the experimental arrangement adapter to that same code.
However, `seed()` installed `desktop_source()` and `bundle()` from
`scripts/application_packages.py`, which read `examples/native-applications`.
It did not export installed package sources from the actual world. All 152 frozen
files still matched the checkout when Alex identified the discrepancy; matching
repository files did not make the seeded application environment current.
Neither the Agora4 checkout nor the existing resident world/service was changed.
Two new, explicitly identified linked trial VMs provide execution isolation.
Each run starts from a fresh synthetic world and reset execution VM. Both arms
can author packages and change the shell; the baseline is not artificially limited
to its initial tool catalog.

Each world starts with 15 subjects and 16 open appearances, including two views
of one OAS risks subject. This does **not** validate the vision's forty windows:
the original application implementation admits at most 32 open views. OAS is
represented by explicit metadata and titles; there is no semantic-search accuracy
test. In the first challenge the harness writes a later paragraph through the
native gateway before asking JEFF to undo the arrangement.

Challenge 1 uses a fresh actual JEFF model session retained in the experiment's
transcript files. Challenges 2 and 3 additionally bind JEFF as the fresh world's
resident and retain user/assistant messages as native conversation records. No
existing resident's conversation was copied, resumed, or impersonated. Both arms
of each challenge use the same conversation setup.

Timing starts at the model request and includes reasoning, tool use, authored
builds, browser checks and the final reply. It excludes fixture setup and my work
developing the candidate. These are individual trajectories, not repeated trials
or statistical latency estimates. The candidate's preinstalled capability gives
it a legitimate but explicit development-cost advantage. Dispatch counts include
automatic context reads and omit discovery calls, so they are not billed tool counts.
JEFF's reflections are qualitative reports; observed native/DOM evidence decides
whether the task succeeded.

Private evidence is retained under
`C:\Projects\Agora\local\arrangement-trials-20260916\runs\`.
Each run has exact experiment source copies, prompt/reply records, tool arguments
and results, timings, native snapshots, browser observations, screenshots and a
replay check. The root is explicitly gitignored because disposable worlds contain
capability keys and session bindings. `baseline-hashes.json` pins baseline files.

## Challenges

1. Tile OAS appearances, place and raise mail, sink unrelated appearances; retain
   duplicate subject occurrences, reload, then undo while preserving a later edit.
2. Create independent Planning and Review configurations of shared subjects;
   duplicate one occurrence, move only that occurrence, preserve an ordered list,
   render actual application views and survive reload.
3. Author a previously absent staircase planner and use the same planner for
   desktop appearances and a separate reference-card board; expose preview and
   undo while preserving unrelated work. Only the baseline completed this trial.
   Its cards referenced existing note subjects, so non-text subject independence
   was not demonstrated. A stronger follow-up was prepared but not run.

## Iteration record

- Initial candidate (v0): failed its measurement integration. An uninvoked browser
  expression produced an opaque missing-result error. JEFF authored a fallback
  package and shell integration. Its eventual success is **not** counted as success
  of the arrangement API.
- First repair (v1): correct the invoked measurement expression and actual board
  element; add a real-browser prepare/apply/render/undo regression. The live model
  then used inspect → prepare → apply directly. A later document save updated view
  editor state and blocked undo under whole-object revision guards. Safe refusal,
  but a failure of the promised experience.
- Second iteration (v2): project semantic layout/binding versions from the native
  journal; merge layout changes into current views under the existing writer lock.
  Editor state no longer conflicts, but a layout changed away and back does.
  Extract the existing planner contribution path for application-owned freeform
  surfaces. Applications retain their schema, admission and commit responsibilities;
  the shared planner conveys no authority. Ordered lists keep their own policy.
- Third iteration (v3): add read-only rendered geometry observation keyed by
  occurrence ID; expose the pure planner through the existing authenticated
  application request path, after the stock installation/open/lease checks.
  Six focused native tests and real-browser checks passed, including an actual
  iframe request and detection of a transient geometry mismatch. **No live JEFF
  conversation tested v3 before the comparison was stopped.** Three completed
  rounds of model-guided improvement must not be claimed.

## Preserved results and interpretation

| Request | Example baseline | Candidate v2 | What this actually supports |
| --- | ---: | ---: | --- |
| OAS desk arrangement | 205.61 s | 59.86 s | Prepared native arrangement avoided on-demand package/shell authoring in this fixture. |
| Undo after later content edit | 36.14 s | 31.47 s | Both retained later text; candidate restored retained bounds and stack through one native compensation. |
| Planning and Review | 195.84 s | 357.69 s | Both worked, using different constructions; candidate built application-owned occurrences and reused the planner but incurred integration work. |
| Novel staircase | 272.42 s | Not run | Baseline reused one authored planner across windows and reference cards; no paired speed or extensibility result. |

These are single-run wall times, including verification, not performance estimates.
The candidate's development and preinstallation cost is excluded. The initial v0
candidate took 237.84 seconds to arrange the desk after its API failed and JEFF
built a fallback. The v1 candidate arranged in 61.47 seconds but failed the later
undo. Those failures remain part of the result, not discarded warm-up runs.

The strongest finding is the live undo failure: an unrelated editor-state update
changed a view revision and blocked layout compensation. This exposed a real
mismatch between the promise and the adapter's conflict granularity, despite
passing model tests. The v2 repair preserved editor state while retaining conflict
detection for intervening layout/binding changes, including changed-back values.

The baseline was quite capable. JEFF could author missing machinery and finish
the requests. The candidate's benefit on the first request was reducing the
amount of new code and private implementation knowledge needed during the task.
It did not establish a new class of expressible outcome, nor an improvement over
the user's installed world. On the board request the candidate was slower and
still needed custom shell integration, manifest repair, and view lifecycle work.
That is evidence against treating reusable geometry as a complete compositional
foundation. The example baseline grouped 15 additional top-level views; the
candidate added two application views containing their own occurrences. The
different constructions also prevent a simple interpretation of the time ratio.

JEFF's v2 desk reflection was: "No new machinery was needed." Its board reflection
reported a custom reference-reading adapter and application-manifest friction.
These describe ease of use in these runs; they are not independent proof of an
architectural property or a claim about subjective experience.

Both board solutions subsequently passed an independent actual-browser content
probe: a paragraph added to the shared risks subject appeared in both Planning
occurrences and Review. Original text was restored through a new native event.
The extra observations live in each run's `independent-content-probe/report.json`.
All seven completed model runs passed their end-of-run native replay check.

My judgment: retain the occurrence/subject distinction, pure planning, atomic
admission, explicit dependencies, compensating undo, and observable rendering.
Do not freeze this experiment's desktop-shaped API as the universal contract.
The next useful investigation is whether existing installed boards and presentation
capabilities can supply these same guarantees through thin adapters, without
requiring JEFF to build shell-specific bridges. Reference access, membership,
ordering, measurement and conflict semantics need to compose along with geometry.

## Preventing this baseline error

The project working instructions now require baseline identity across repository,
world-authored package builds, relevant state, runtime/tool inventory and observed
UI. The trial runner requires `--baseline-kind example-fixture` explicitly and
rejects `installed-world` before creating an output world, resetting a VM, or
calling a model. Comparison output labels every retained run as an example-fixture
experiment. Original transcripts, source snapshots and reports remain unchanged.
Supporting a real installed-world baseline will require a verified loader and
provenance record; changing a label alone is insufficient.

The semantic witness implementation scans the journal for this bounded experiment.
A production implementation would put the read projection beside native replay
and maintain a rebuildable index. There is no second event log or table writer.

## Current architectural limits to assess

The candidate has a native desktop adapter and a pure application planner. That
does not yet establish a common adapter protocol for creation, membership, list
ordering, nested measurements, or atomic multi-application admission. Prepared
desktop plans are process-local and expire on restart; accepted intent receipts
are durable. Stack undo is conservative. Contract migration and old receipt
compatibility remain unimplemented. The renderer's polling-based stack bridge
also needs pointer/focus testing before it belongs in a live desktop.
