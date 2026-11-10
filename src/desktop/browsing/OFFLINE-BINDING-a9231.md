# Offline identity and enumeration increment — awaiting review

22 October 2026. Worker-a9231 / codex-builder-1. Rowan c11115, JEFF m11114,
Mica c11113 authorize this bounded offline implementation only.
No native query, launch, cleanup, interpreter hash probe, prepare, ready,
activation, public page, policy or security change occurred.

## Changed capability

Browser-specific HostFence holds measured process handles, distinct from the
launcher's birth. A candidate effective interpreter needs an explicitly
reviewed path/file-hash entry, a bounded measured parent chain back to the exact
launcher birth, nondecreasing creation times, unchanged handles, and membership
in the retained Job. Every intermediate interpreter also needs a reviewed image.
An arbitrary Job member or reported PID cannot establish this relationship.
Rechecks detect parent, birth, image, file hash and Job changes. Failure closes
read-only handles, never adopts/replays/terminates a candidate.

The initial importing receipt supplies a candidate only. The parent measures
it and publishes one host binding. The child waits at most ten seconds before
importing the engine, echoes the binding on later receipts/requests, and checks
the parent's engine response before navigation. Repeated pending importing
receipts can remain pending; they cannot authorize an engine report.
Host, root, token, named desktop, fresh profile and Job bindings are checked at
each envelope boundary. The report callback requires these same actual fences,
re-reads envelopes for races, and pins engine identity independently.
Host/engine operations share a reentrant lock with sampling; closed fences
cannot reopen. False/failed handle closes retain the handle for reconciliation.
Existing shared family, privacy, guard and Job cleanup checks remain independent.

`REVIEWED_HOST_IMAGES` is intentionally empty; no CLI/environment/receipt can
populate it. The runner refuses before native initialization when it is empty.
The injected run boundary independently refuses absent host configuration
before Job/child creation. Synthetic inventories exist only in tests.
File SHA256 is evidence about the file at the measured image path; it is not a
measurement of bytes mapped into a running process. These accidental-reuse
fences/file messages are not authentication or same-user worker containment.

Shared verifier change is limited to enumeration and bounded error reporting:
clear ctypes last-error before calls, capture errors before cleanup, reject
false/partial desktop scans or callback failures even if error is zero, and
preserve true empty/populated completion. Only Toolhelp completion accepts
ERROR_NO_MORE_FILES. Other Toolhelp errors reject partial snapshots. The
receipts retain API/error/visited/callback metadata without titles/content.
No change to must_prove, limits, admission policy or verdict semantics.

## Separate candidate identity/provenance

Read ONLY retained receipts from the prior admitted run, not live processes:

| Role | Recorded evidence | Not established |
| --- | --- | --- |
| Launcher | PID96436, creation134371612090425561; owner image `c:\projects\agora4\.venv\scripts\python.exe`, Job8cc4ed8e9b2d411689cef169d2daca02 | No new identity/hash observation |
| Possible effective host | PID29228, creation134371612090668135; measured parent96436; image basename python.exe, same Job | Full image path/hash and interpreter role cause are not established by the retained public verdict |
| Parent Job creator | Recorded PID99168 with its own birth/image | Not evidence that the effective child uses that image |

Thus no exact effective-interpreter entry is proposed as approved. Venv
redirection and stale Toolhelp error remain hypotheses. The former run's
verified empty-Job receipt does not establish current process absence. Existing
brokered-family/unscanned-write and other snapshot limits remain unproved.

## Ran and negative results

Pinned Python:
`-m unittest discover -s src/desktop/browsing -p test*.py`
printed **Ran 93 tests in 1.336s; OK**.
This includes actual injected orchestration with direct and descendant hosts,
the real shared Job/birth receipt code using fake native APIs, navigation and
request-policy suites. No real Windows libraries/engine were initialized.

Refusal cases exercised: empty reviewed inventory before native initialization;
missing run configuration before Job creation; unknown/denied/out-of-Job host;
wrong image/hash; unrelated member; missing/cyclic/too-deep/ambiguous ancestry;
birth order, changed parent/root/host/Job/hash/membership; replacement or ended
host; forged initial binding; wrong token/profile/desktop/host/binding; raced
report reread; forged receipt; engine birth race/replacement; closed-fence
reopen; exception/false close result preserving handles. Existing cleanup,
deadline, guard, persistence and unknown-verdict refusal tests still run.

Enumeration fixtures cover success empty/populated, stale error on success,
false+zero, false+18, false+partial, failed/throwing callback, preserved original
error across cleanup, and empty/populated Toolhelp completion vs unexpected
zero/5. Those are synthetic source-path results; actual winerror18 cause is
still unknown.

Six changed browser Python files: full Ruff check **All checks passed**.
Shared verifier full lint remains **151 failures**, exactly the baseline count
and code distribution:149 E501,1 I001,1 B905. It is not relabelled a lint pass.
`git diff --check`: exit0. No full health/native/painted acceptance was run.

The original six-case design fixture is preserved byte-for-byte as
ENUMERATION-DESIGN-BASELINE-a9231.txt, SHA256
4126f827881dc7e96a19885085f51e7c404a063a061b27759754878fa4e19de6.
Its executable counterpart now asserts the candidate's fail-closed behavior.
Prior reports and retained runtime receipts were not rewritten or deleted.

## Exact source inventory, scope and reversal

OFFLINE-BINDING-a9231.patch is the **cumulative eight-file source/test artifact**
against checkpoint f337dfd5ee59e6dbae8c2bb4fdf95f758de19d30, including earlier
preserved runtime/guard/verifier changes; it is not represented as this round
alone. SHA256:
06e135f4d69a9b4a69952c271864a3342b9dc4fad58f5161c0201a8ced269065.

OFFLINE-BINDING-a9231.manifest.json records exact base blob/output SHA256 and
byte counts for every path; SHA256:
29527e4582f808ca059b25a9384bf53f77fb20b27053dcf50a0700bda2bdfae2.
No files in house/provider/transport or live worlds are included.

Owned hunks: admission_job (HostFence/envelopes/engine/run checks), probe
(bounded handshake/echo/response checks), runner (empty inventory/refusal and
single fenced report consumer), browser tests; shared native_run_verify
(enumeration/error metadata only). Mica confirmed no overlapping Mail edits.

Nothing is active to reverse. Do not apply or reverse the cumulative patch in
this preserved tree: doing so could remove earlier work. It is an exact review
artifact, not an approved deployment command. Preserve all staged files through
house checkpointing; any future integration/reversal must be separately scoped
to its then-current base and must retain earlier reports/receipts.

Next: Rowan reviews the staged bytes and shared compatibility. Installed
interpreter inventory, native timing, real host-chain proof, engine handshake,
privacy containment, screenshots and public navigation remain untested and
unapproved. Keep paused; no prepare, ready or runtime attempt.
