# House source handoffs

Implemented by `preserved_work.py` and `Workshop.bring` (a9421).
This imports source for review; it never lands the imported branch on main,
starts a model, applies a research patch, or establishes runtime/host ownership.

On the receiving card set `brings` to a JSON string:

```json
{"source":"a8796","paths":["research/voice-delivery/"],"request":"voice-review-1"}
```

`source` is an existing card or `main`. `paths` are explicit repository-relative
files, or research directory packages. A source card can also use `@preserved`:
the source's current modified/untracked, nonignored files, excluding copied
session worlds. This is useful when the keeper is several related hot-file
edits plus a research package. Main always requires explicit paths.
Use a new `request` value for an intentional new snapshot after a successful
handoff. Leaving a completed request in place is idempotent.
An optional `"after":"a9551"` waits for that receiving card's actual completed
receipt and matching Git ancestry, allowing the lead's delivery order to remain
explicit without resuming either worker. A status prop alone is insufficient.

The house processes this before normal admission, even for paused cards,
without changing their paused state. It reserves both card process leases
and shares the existing landing lock. A process still alive, a held lease,
landing in progress, unsafe receiver inputs, staged source index, wrong branch,
missing input, linked path or merge in progress holds the request. It never
stops a worker to obtain a lease. A waiting receiver does not consume a model
slot. A missing receiver worktree is created by the house on its existing
worker branch, or a fresh branch from current house HEAD.
Current Codex adapters hold card leases; legacy Claude starts do not. A saved
unleased runtime with no parent-owned, known exited process handle holds for
ownership reconciliation. A missing lease alone never proves that runtime
gone. This is a capability limitation, not provider-based task eligibility.

Only source/code artifacts are eligible: no sessions, house state, .git,
.env variants, private/credential directories, ignored files or linked paths.
Limit: 200 files / 32 MiB. This is a repository handoff, not a secure account
reader or cross-process authentication service. It does not certify package
contents as safe to execute.

## Preservation and conflict policy

Before importing, the house checkpoints the stopped receiver's own dirty and
untracked nonignored source on its existing worker branch, under the same card
lease and landing lock. Session copies are excluded; private/linked inputs,
unmerged files and unsupported entries hold rather than being blindly committed.
The receiver inventory is bounded to 200 paths / 32 MiB, including any staged
version. Deleted files and rename sides are recorded explicitly. If partial
staging exists, the existing index is committed first and the final worktree
second, retaining both versions in history. Hooks and signing are disabled.
The durable receipt records raw worktree hashes, staged hashes, committed blob
hashes, checkpoint commits and deletions. An exact inventory comment is posted
on the receiving card before source delivery proceeds. Confirmation reads the
house-authored structured request key and complete checkpoint/hash inventory,
not the exact rendered comment or its position. New comments use forward-slash
receipt paths. Already-posted legacy inventories are reusable when their JSON
inventory and request-specific receipt filename match, even if the desk decoded
a Windows directory escape into a newline. Failure to confirm holds delivery;
retry reuses matching evidence without reposting or repeating commits.

An idle source worker's selected files are committed on its own branch; other
uncommitted files remain in place. Git hooks/signing are not run by that commit.
Main inputs reuse **landing.hand**, the recording half of `landing.py --files`,
with its separate Git index. The full CLI would land on main; handoffs
deliberately do not call that half. Main files, HEAD and index remain untouched.

A projection commit contains only selected source paths on the source/receiver
common base. This prevents accidentally importing unrelated source commits or
held deployments. Git `merge-tree --write-tree` checks a three-way merge in
objects before the incoming merge changes the receiver. A conflict leaves its
checkpointed HEAD, index and files unchanged; its own checkpoint and the source
preservation commit stay available. Successful merges
advance only the receiving worker branch with a merge receipt commit. Ignored
receiver files are protected too; they are not disposable.

Receipts live in the existing house state directory:
`brings/<recipient>-<request-sha256>.json`. Card props `brings_status` and
`brings_receipt` expose outcome/location, and one quiet card comment records
successful source/receiver commits. Identical holds are not repeatedly posted.
No unrelated notices or resident wakes are sent.

The manifest records source raw-byte SHA256/size, committed Git blob SHA256/size,
received Git blobs and received worktree bytes, source/receiver revisions and
UTC capture time. Git's normal line-ending/filter handling can make these hashes
differ; they are deliberately separate. A clean three-way auto-merge may also
combine receiver edits with source text. Consumers must check their required
artifact hashes, not treat import success as independent review or exact raw
byte equality. Binary patch artifacts should be hash-checked before review.
The existing main-new-file admission check accepts only files in a completed
import receipt whose receiving commit is still in the worker's ancestry.
Other missing-file holds and shared-source warnings are retained.

A durable `receiver-preserving` receipt precedes receiver commits; interruption
in that phase holds for inspection and never repeats an uncertain commit.
`receiver-preserved` records the completed checkpoint, before card reporting and
delivery. It can resume only with the checkpoint in ancestry and a clean receiver.
A durable `planned` receipt precedes receiver fast-forward. If the house dies
afterward, ancestry reconciles that receipt without another preservation commit.
If the result is not in the receiver ancestry, or source preservation was
interrupted, the house holds rather than guessing or replaying. The maintainer
inspects the receipt and Git state before issuing a new request. Atomicity
across source and receiver is not claimed: a refused merge may have checkpointed
the receiver and preserved the source, while importing nothing.

To abandon a held request, clear `brings`; nothing is deleted or rolled back.
To reverse a successful import, review/revert its receipt merge on the receiving
branch through the house's normal source path. Do not reset either worktree.

## Deployment / evidence

`workshop.py` and the new imported module belong in `HOUSE_FILES`; loading this
integration needs an ordinary house deployment. Alex explicitly allows that
for a9421. This does not authorize activation of any transferred candidate.
No new service, transport, host executor, grant or OS setting is introduced.

Run `test_preserved_work.py` with the pinned interpreter. It uses isolated real
Git repositories/worktrees plus fake house state and a fixture-only process
lease holder. No source input from another live worktree is read by the tests.
Existing `test_builders.py` and `test_house_merge.py` cover ordinary admission,
limits, process preservation and landing behavior. Offline tests are not live
delivery receipts; check each consumer's real house receipt after deployment.

## Requested deliveries, in lead-approved order

1. Voice safety review: source a8796 `research/voice-delivery/` to a9551.
   Transfer artifacts only; never apply the contained patch to house.py.
2. Browser continuation: six explicitly named main-checkout admission files to
   a9231 (ADMISSION-TAKEOVER.md, admission_probe.py, run_admission.py,
   admission_result.py, test_admission_result.py,
   evidence/admission-20261021.json under research/window-lab/browsing).
3. Panel activation: a8138 `@preserved` plus
   `research/window-lab/browsing/tabs/window/` to a9352. Hot-file conflicts hold
   instead of replacing newer viewer/menu/Markdown/tiling behavior.

All three receivers remain paused. Their leads review source/hash receipts and
separate host/runtime/browser prerequisites before resuming.
