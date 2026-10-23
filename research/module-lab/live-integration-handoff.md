# Live Workers and module integration

Updated 22 October 2026, 22:25 UTC, Greame. **Installed in the live desk.**
Workers and Modules were added to Alex's existing dock. The five earlier dock
appearances retain their identities and order. Native click-to-own-window
acceptance remains unverified; that limitation is explicit below.

## What ran

- The same approved localhost API path now works. The serving backend was
  replaced once through `/door/swap`, under a fresh admitted fullscreen guard.
  The replacement reported success. No house restart was requested by this worker.
- Before/after that swap: house PID 58720 in both snapshots; **261 recorded
  session identity hashes, zero changed**. A later snapshot has PID 61096 and
  two changed worker identity hashes (`worker-a10692`, `worker-a11161`). This
  worker did not issue that house restart or change those identities; concurrent
  work continues. The preservation claim is specifically the swap comparison,
  not a claim that the entire running system remained frozen all evening.
- Ordinary fenced commands created one scoped resource surface, ten persistent
  style/lens/config/guide notes, and two dock notes. Each mutation checked the
  existing guard; no direct session save or whole-world replacement was used.
- Workers was installed as soon as its own live lens compiled, before completing
  module examples. All four installed lenses compile against the live desk.
- Hidden browser verification of the actual live API/painter, **480x640**:
  seven residents, three working-or-waiting workers out of eleven reported,
  eight inactive workers, queue two, and three separate quota observations at
  the captured instant. Actual values refreshed with the same row count; an
  expanded worker fold remained open while context changed from 35.8% to 38%.
  Document width was 480, no horizontal overflow. All SVG rectangles reported
  `rx=0, ry=0`. Inactive and task-detail folds worked. Missing inactive-worker
  context displayed unknown rather than zero.
- Live module workshop shows union of overlapping intervals = **8 hours**, two
  nested frame modules, a retained stale result, and explicit unknown for the
  missing-source example. Trace exposes frame1, frame0, view, measure, graphic
  with exact pins and input/output hashes. These inputs are labelled synthetic.
- Regression result remains **137 passed in 3.25s**, with Ruff passing and the
  frozen-world reuse check passing as recorded below. Post-install source hashes
  match the tested foundation/compiler/painter/graphics versions; no additional
  source change was needed during activation.

## Installed identities (operator evidence)

| Object | Ref |
|---|---|
| Capability workshop resources | f11296 |
| crew-terminal-style / crew-observatory | a11299 / a11301 |
| Workers dock appearance | a11303 |
| composition-workshop-style | a11305 |
| Known / stale / missing configurations | a11307 / a11309 / a11311 |
| composition-workshop / catalog / trace | a11313 / a11315 / a11317 |
| Crew and capabilities guide | a11319 |
| Modules dock appearance | a11321 |
| Rough spots source-work record | a11325 |
| Board integration task, status=review | a11327 |

Existing dock refs, preserved in order: a5567, a5569, a5571, a5573, a10959.
The visible labels are Workers and Modules; ids are not displayed in these UI
entries. No existing home-dock lens, layout, style or dock item was edited.

## Access diagnosis and exact limits

**Correction of the earlier report below:** the Windows socket-access failure
was not an explicit policy/reviewer rejection. Default command execution had a
low-integrity AppContainer token; the supported `require_escalated` execution
had a medium-integrity, non-AppContainer restricted token, still not elevated.
The identical local API read succeeded through that approved path. This isolates
the practical access condition to sandbox confinement; the exact Windows filter
rule/errno was not instrumented. No admin elevation, firewall change, security
setting change, alternate mutation route or live transport bypass was used.

Installation briefly stopped at the guard while fullscreen OBS was reported
unsafe; no create had been sent. It resumed only after a fresh observation
admitted Chrome. Two application-grammar errors were also reconciled as
known-not-executed (empty created/events): title selection and properties on a
surface create. Surface properties are now a separate normal prop command.
The successful receipt is `live-install-receipts-v4.json`. No request remains
pending or of uncertain mutation outcome.

**Still unverified:** actual native HUD click opening its own native window,
and compact native default window geometry. Available CUA inventory has browser
tabs only (`apps: []`), with native computer APIs disabled. The computer-use
skill's separate native runtime was unavailable. Browser clicking Workers and
the workshop host-window link yielded no observable popup and no error; this
does not prove native success or establish an Agora native failure. The live
DOM binds Workers to `window crew-observatory`, and direct navigation renders
that exact live target. Native acceptance needs one click on the installed
Workers entry in Alex's real HUD using a supported native observation lane.
Do not mark that check passed from the DOM alone. No permissions are pending.

A recursive diagnostic search accidentally included exported logs before the
scope mistake was noticed. It was stopped; further searches were restricted to
named source files. No exported transcript content was used as architecture or
activation evidence, and no session pickle was directly inspected.

## Rollback and boundaries

Reversible hiding: freshly read and match the two dock appearances, then move
only a11303 and a11321 into f11296 using normal fenced `do move ... into=...`.
Keep their style/lens/config objects for inspection and re-adoption. Do not
restore a whole-world snapshot, remove other workers' items, or undo source
indiscriminately. This rollback is documented, not executed against the live UI.

The installed module runtime executes reviewed trusted Python; it is **not an
untrusted-code sandbox**. No complete effect executor is implemented: typed
action requests stop at admitted-not-executed preflight. No live migration,
audience-authored code execution, automatic module source install, paid model
call, credential/security expansion, commit or push was performed. Draft world
configuration is not authority to execute arbitrary code. Stateless activation
and rollback are supported; unsupported migration/state rollback is refused.

Evidence: `evidence/backend-activation.json`,
`evidence/live-install-receipts-v4.json`, `evidence/live-verification.json`,
`evidence/live-integration-records.json`, `evidence/live-workers-480.png`,
`evidence/live-dock.png`, and `evidence/live-modules.png`.

---

## Historical preparation report — superseded by the verified installation above

The following is retained as history. Its statements that API access and world
installation were blocked are no longer current; its description of an explicit
denial is corrected above.


# Live integration preparation — activation blocked

22 October 2026, Greame. Alex authorized live integration and then explicitly
requested a **Workers** entry in the bottom bar. It has **not been added**. The
dashboard and composition examples have **not been installed into the live desk**
by this worker. No live command, reload or native-window action was attempted in
this integration turn.

## Access blocker

The earlier read-only POST to `http://127.0.0.1:8794/api/do`, session `frontier`,
actor `module-builder`, line `read "Rough spots"`, failed with:

> An attempt was made to access a socket in a way forbidden by its access permissions.

That request was denied/not executed. The parent explicitly prohibited routing
around this denial and allowed a retry only after materially relevant evidence
known to resolve it. The new integration and Workers-label authorizations do not
demonstrate restored socket access. Therefore the endpoint was **not retried**,
no alternate transport was used for live mutation, and no uncertain live request
exists to reconcile. Current endpoint reachability remains unverified.

Independent reads used the existing locked `export_docs.load` snapshot loader and
published house/usage files. They did not save a world or dispatch live commands.
The live charter was read again. This is not an alternative installation route.

## Prepared source and world content

- `notation/sources/crew.py`: a read-only adapter on the existing source ABI.
  Reads `house.json`, `plan-usage.json`, `witnessed:usage`, and actual world names.
  It has no writer, daemon, network request, callback or model call.
- `module-lab/crew-live.lens`: compact terminal layout, same roles and graphics,
  direct observed rows instead of recreated telemetry notes. Stable `rid` values
  follow resident corners and commission cards; repeated updates do not assign
  identity by position. Source selectors are scoped, with no global watch tags.
- `module-lab/integration_bundle.py`: ten persistent note definitions, exact
  current module pins, and two proposed bottom-bar notes. The fixture installer
  only accepts a new `crew-integration-memory` desk and refuses title collisions.
  It is not a live installer or a transport around the blocked API.
- `notation/test_crew.py`: twelve integration regressions, including real scene
  compilation and stable worker-fold keys after same-count updates and insertion.

The proposed bottom-bar note is `title=Workers glyph=▤ window=crew-observatory`.
The Modules note opens `composition-workshop`. Both use the existing `home-dock`
window property and host window gesture. They do not modify `home-dock`, remove
existing entries, change panel layout, or open the Viewer. The live read found
one Alex dock, `f5565`. Re-resolve it and inspect its current children before any
eventual installation; this snapshot is not authority to overwrite an item.

The four candidate lenses are `crew-observatory`, `composition-workshop`,
`composition-catalog`, and `composition-trace`. The composition examples are
explicitly synthetic (ready/stale/missing) and do not pretend to measure real
work. The dashboard's Studio link was replaced with Composition workshop, so
there is no unresolved Studio dependency.

## Observation semantics

Context joins witnessed usage to the actual resident/commission key; an absent
measurement or capacity remains unknown. A zero is displayed only when measured.
The last context model is prefixed `~` when configured worker model is absent.
Usage publication age is not token measurement age; the latter stays unknown.
Account quotas remain separate provider reports, with as-of and reset evidence;
expired/future-dated windows become unknown. Invalid percentages produce errors,
not clamped measurements. A stopped usage producer returns unavailable through
the existing witnessed reader. Retained observations become stale at the house's
existing 30-second threshold. Stale activity is not shown as currently working.
Malformed group publications produce unknown telemetry.

Working and waiting workers both remain visible; the count labels them active
and the evidence explains that definition. The initial preflight read seven
residents, one working worker, two waiting workers and ten inactive entries.
The final refresh read seven residents, two working workers, one waiting worker
and eleven inactive entries, with actual commission titles. It compiled three
quota observations separately. It found no
collisions among the ten candidate note titles. Evidence is a point-in-time
observation, not proof of current activity at a later time.

The adapter uses existing scene invalidation: house changes, witnessed-file
changes, world changes and minute ticks. It adds no instantaneous time-expiry
notification. Publication freshness is not proof of permission or delivery.

## Verification

**Ran:** final combined affected suite: **137 passed in 3.25s**. This includes
the twelve new tests and existing module, row-scope, graphics, scene, row-refusal
and dashboard preview checks. **Ran:** Ruff on the three new Python files:
`All checks passed!`. **Ran:** frozen-world reuse check:

```text
76 changes over the frozen worlds' lenses, each lens built kept and whole after each (1 s)
instances kept 430, made 62 (87% kept)
all passed
```

The first combined run was obstructed by filesystem permissions: existing tests
write scratch worlds into the repository sessions directory, and pytest's
default temp directory was not writable. It printed 35 failed, 94 passed and
6 errors. A focused diagnostic confirmed the scratch-path PermissionError.
The successful run copied only the existing probe fixture into a new task-owned
directory, redirected `deskd.SESSIONS` there and set pytest/tempfile scratch there.
It did not change or relax assertions, edit existing tests, or touch live sessions.
Ruff's initial cache write was also denied; the read-only `--no-cache` run passed.

`evidence/integration-preflight.json` records the compiled in-memory scenes,
observed rows, manifest and source hashes. The earlier foundation, compiler,
graphics and painter hashes still match their verified versions. No peer-owned
file or shared runtime file was edited in this integration turn.

## Admission, rollback and remaining checks

Before activation, obtain evidence that the supported local API access is
restored. Do not route around the denial or delegate a bypass. Then re-read the
live inventory, workers and source versions. Source discovery happens at process
startup; if needed use the existing guarded, healthy backend replacement path,
preserving in-flight calls and refusing unsafe fullscreen/reload conditions.
The house itself needs no change for this adapter. No reload request was made.

Install only new bundle-owned notes through ordinary fenced world commands.
Check each receipt; after an uncertain write inspect the result before retrying.
Record created identities and content hashes. Add Workers to Alex's existing dock
only after the target lens compiles. Preserve every existing bottom-bar item.
Record source work in Rough spots through the supported API when admitted.

Rollback should remove only the new dock appearances, or move them to the bundle's
own storage surface, after matching their recorded identity and current contents.
Keep the new lens/config notes available for inspection; do not restore a whole
world snapshot or erase subsequent resident work. No source rollback is needed to
hide these read-only lenses. Exact module pins must not be silently replaced.

Still **pending/unverified**: API admission, actual world installation, Workers
entry visibility, the real bottom-bar click opening a native compact lens, live
480x640 layout/fold retention, live same-count refresh, guarded reload/resumption
if required, Board logging and an executed rollback. No new UI screenshot or
live end-to-end success is claimed. No commit, push, credential/security change,
paid API call, broad migration or external publication was made.
