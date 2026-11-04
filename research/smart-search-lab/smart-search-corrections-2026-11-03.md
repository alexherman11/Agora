# Smart search corrections and interim evidence window

Correction candidate for JEFF/House, 3 November 2026. Supersedes earlier activation proposals. **Semantic activation held; parent task incomplete.** Read only developer-facing aggregate review dk1740, not the evaluator worktree or sealed holdout.

## Three corrections

1. **Broker admission:** `generate(..., admission=...)` invokes search's admission callback under the existing nonblocking inference lock immediately before the generation POST. Search checks gaming, resident-model/memory safety and finally fresh last-input telemetry. Missing, invalid or ambiguous idle telemetry fails closed; less than 30 seconds idle fails closed. No queue, prewarm, budget reset or model setting change. Other broker operations retain their existing behavior. No real telemetry or inference was sampled during these corrections.
2. **Explicit filters:** semantic API requires `confirmed=yes filters=<JSON-list>`. Missing confirmation yields no suggestions and no inference. Supported named filters remain local/offline/last_week/decision; unsupported requirements cannot be certified. An explicitly empty list means relevance suggestions and unverified evidence only, not satisfaction of arbitrary requirements in prose. Model-extracted spans are incomplete suggestions; additional suggestions require confirmation and withhold results. Schema validation never establishes constraint completeness. A future semantic surface must expose these choices and unsupported-requirement abstention before activation; the old `search.js` does not and remains an uninstalled draft.
3. **Provenance abstention:** no independent capability validator exists in this slice. All capability metadata is unverified, including nonempty `search_evidence`, apparent references, processing/network facts and download/decision metadata. Every hard-filter request abstains, even when the model omits the requested requirement. No inference is spent on that currently unsatisfiable contract. This deliberately removes the old apparent capability guarantee instead of treating a string as authorization or independent evidence.

The bounded meaning-based candidate path remains in the held broker draft. Its synthetic contract test accepts a relevance suggestion without shared query words; model quality is still untested. This correction is not an alias catalogue substitute. The durable goal remains semantic discovery across permitted sources, with a reviewed provenance validator and a usable confirmation design still required.

## Separately reviewable interim

Installer now selects **lexical.js**, titled **Apps and World text search**. It contains no model calls, semantic follow-up or capability certificate. Its sole result gesture is View evidence; the lens has only `window.open thing $id`. Enter submits quoted query data to the existing kernel `search`, limit 50, then filters supported visible Apps/World kinds. It discloses that post-filtered retrieval is incomplete and that Files, Email and Web are disconnected.

Each click uses the painter's uncached `api.rows('rows any')`, matches visible identity, revision and kind, rejects forgotten/unavailable rows, and submits that exact revision fence. A query edit, cleanup or stale response cannot complete an older action. It never launches an app or executes query text. Draft query/source selection persists; existing launcher is untouched.

Memory availability, model readiness or a setting cannot enable semantics in this window: its code has no model route and its requested grants contain none. Enabling semantics requires a separately reviewed source and authority change.

## Ran versus unrun

- **Ran:** pinned Python `-B research/smart-search-lab/check_corrections.py`: `Ran 11 tests in 0.006s`, `OK`. These new in-memory tests exercise admission failure/lock release, no queueing, telemetry thresholds/unavailability, confirmation before budget/inference, provenance abstention, and the held semantic plumbing with mocked generation.
- **Ran:** `node research/smart-search-lab/check_lexical_surface.mjs`: `LEXICAL SURFACE CONTRACTS: 12/12 passed (mock rows/actions; no browser or inference)`. Covers quoted submission, disclosure, supported kinds, stale/revoked/forgotten/different-source clicks, fresh reads with revision fences, edits/cleanup and read failure.
- **Ran:** offline installer argument capture and digest generation, pinned Python `-B research/smart-search-lab/record_correction_manifest.py`, exit 0. No real Door, world authoring or grant changes.
- **Read only, not rerun:** dk1740 reports the previous candidate's independent 40-case state suite at 37 passed/3 failed; private semantic holdout entirely unrun; zero inference. These corrections need independent review and do not inherit that candidate's pass counts.
- **Unrun:** actual inference, current resource telemetry, cross-principal/per-field broker validation, live host/browser action behavior, activation and rollback. Previous denied pytest default-temp/quota/cache paths were not retried, relocated or repaired. Existing feature test expectations were updated for the new abstention contract but that pytest suite was not rerun.

Historical gates remain evidence only: builder snapshot `2026-11-03T04:49:11.098229Z`: idle 0s, 4.5 GiB free, loaded [], gaming reasons [], unsafe. Developer-facing review reports `2026-11-03T05:30:41.629346Z`: idle 121s, 6.1 GiB free, loaded [], gaming reasons [], unsafe below 8 GiB cold boundary. Neither is current telemetry. No poll or inference retry in this round.

## Exact review and activation contract

`correction-manifest.json` records every changed source/test file hash, requested grants and canonical offline-authored fact digests. Key hashes:

| Artifact | SHA-256 |
|---|---|
| Interim component code/review | `1f2873c462e24d45989f7133cad32ddbe844e708dd4d56c2cea6a10227d7937c` |
| Evidence-only lens text | `ed1ed2de5a6c7d83b06496b382a3c7e4d1bc8137629d24f4e8f001c7e9884f7a` |
| Installer file | `f2e4d3aa77db3a098b1c2e22e51d2774871f0156360df1fa92756d7c464e9056` |
| Generated widget code | `0e05c6ee58a3d11eeb3953d7065aec613c9f61e2f02ad09b0a44eb97ed3bd0f3` |

JEFF coordinates fresh House review of those bytes, including actual caller-filtered lexical/permission/host-click checks in its supported hidden environment without retrying worker-denied fixtures. No new worker. Retain painter health/recovery restrictions to its own reviewed lens; review that restriction with the generated widget. Source tests alone cannot prove host authority.

Only after separate lexical approval: House serially lands; JEFF authors via existing authorized Door, checks these digests against authored bytes, reviews the component, then explicitly activates **only** this window widget with exactly:

`window.surface rows look look-view history components help component-health component-action search window.open hear:make hear:set hear:forget hear:undo hear:component hear:component-action`

No model grant, generic write/native/file/network/account authority or shell grant change. No adoption/restart of model module. Then author one button named `smart-search-button`: taskbar, search icon, label Apps and World text search, `window.open smart-search`. No test click. Off affects only this widget and entry. Any dependency-byte drift requires new digests/review. Old candidate hashes approve no variant.

JEFF owns separate semantic review, new prompt/corpus/source freeze before independent evaluation, provenance/confirmation design and any later safe idle inference opportunity through existing broker authority. Old freeze/evidence files remain historical and must not be overwritten or presented as the corrected candidate's measurements.
