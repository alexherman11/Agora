# a6498 acceptance handoff — 20 October 2026

Source is prepared on `worker/a6498` for house landing under JEFF c6757/c6760;
live acceptance is explicitly deferred to his host-side run after landing.
No settings outside the runtime locks have been changed, and neither lock
has changed. No sign-in profile, credentials, account or live-model turn was used.

The original missing-installation failure has already been repaired in the
starting checkout: both locks name the retained main-checkout executable
`local/codex-residents/runtime/896a0166b774037a/codex.exe`, version
`codex-cli 0.163.0-alpha.10.2`, SHA-256
`f6dbf48cb70f62649c645f26c87dc9bf84cc36986202dfad8e12fb5b8ca70312`.
The existing file's hash matches. The installed app has the same installation
directory suffix. The new checker attempted recertification and refused safely.

## Source prepared

- `runtime_pin.py`: shared startup gate; newest installed candidate discovery;
  retained exact bytes; forward same-major version policy; resident/Sol/Astra
  mock probe matrix; exact tool-schema comparison and resident protocol/model
  checks; OS lease; transactional two-lock publication with crash recovery;
  previous-lock history and checked rollback; visible world receipts and
  idempotent Alex-only failure notifications, with a durable retry queue.
  Before candidate execution, resolved source must be updater-installed and
  retained bytes must have a valid OpenAI OpCo, LLC Authenticode signature.
  Retained old pins require an identical source still in the updater folder;
  missing old installations prevent automatic rollback, without bypassing trust.
- `codex_resident.py`, `codex_worker.py`: normal startup uses the gate; candidate
  probes use the same configuration builders with their own empty profiles.
  Worker record routing reads the existing MCP configuration because workshop
  deliberately keeps `DESKD=off` in worker shells. No launcher setting changed.
- `probe_support.py`, `probe_runtime.py`, `probe_worker.py`: inherited-ACL UUID
  scratch directories; empty `CODEX_HOME`; no sign-in or API-key override;
  stand-in Desk with the real schema, unable to access any world; loopback
  inference; child job cleanup; mandatory enabled assertions. Automatic probe
  subprocesses ignore Python environment overrides. Probe output cannot
  overwrite the locks, catalogs or reviewed inventories.
- `test_runtime_pin.py`: fake binaries and inventories, real cross-process lease,
  fake loopback house API, plus rejection and recovery cases.

Catalog checks allow only the pinned bytes or their exact Git CRLF/LF checkout
conversion; the pre-existing pins otherwise reject this LF worktree.

## Ran

Pinned interpreter: `C:/Projects/Agora4/.venv/Scripts/python.exe`.

- `local/run-pin-tests.py`: **48 passed in 6.70s** across the new tests,
  `test_worker.py` and `test_transport.py`. This ignored, worktree-local runner
  supplies inherited-ACL `tmp_path` fixtures for the two existing tests.
  Native pytest's system-temp fixture failed before those two tests could run;
  an earlier ordinary run reported 26 passed and 2 setup errors. With local
  fixtures all assertions and cleanup passed.
- Changed-file Ruff: **All checks passed!**
- Read-only `Get-AuthenticodeSignature` on
  `C:/Users/Alex/AppData/Local/OpenAI/Codex/bin/896a0166b774037a/codex.exe`:
  status 0 (Valid), publisher `OpenAI OpCo, LLC`. No candidate execution.
- Explicit test evidence: `test_changed_tool_schema_refuses_and_notifies_once`,
  `test_tool_addition_refuses`, `test_missing_binary_refuses`,
  `test_corrupt_hash_does_not_bless_same_version`,
  `test_corrupt_pinned_binary_cannot_approve_itself`,
  `test_major_jump_refuses_before_probes`,
  `test_benign_update_repins_both_and_keeps_previous`,
  `test_previous_pin_is_reversible_but_reprobed`.
- Publisher/source tests refuse unsigned, mismatched and unexpected publishers,
  outside-bin candidates and signature-time mutation before version/probes.
  `test_checker_opens_only_empty_probe_homes_with_real_home_present` guards
  Python file opens under the real user home, configured Codex home and local
  profile, plus a fake signed-in home with a fake auth sentinel. All four child
  launch environments point only to separate empty homes. Native subprocesses
  are stand-ins in this test; opaque native IO is not audited or claimed.
- `git diff --check`: exit 0.
- Final source `probe_runtime.py`, including the child job, `-E`, explicit
  retained binary and scratch output: **PASS: no tools, no system/developer
  prompt, completed text reaches the house protocol**. Actual request model
  was `gpt-6-astra`, tools/instructions null, one user message, completed
  translated reply `> look` / `> rest`. This was mock inference, not a live turn.
- Full `runtime_pin.py --recheck`: printed
  `Runtime candidate: codex-cli 0.163.0-alpha.10.2`, then refused at the Sol worker
  mock probe. The actual command event said:
  `Failed to create unified exec process: CreateRestrictedToken failed: 87`,
  exitCode -1. This was a `-NoProfile` PowerShell fixture write, not an account
  operation. Repeated standalone worker checks had already found the same
  token-creation failure. No sandbox flag was weakened.
- `runtime_pin.py` without recheck: accepted the existing healthy pin and
  printed its existing version/hash. Its notice queue could not flush because
  this standalone builder has `DESKD=off`.
- `git diff` for both lock files: empty. Neither reviewed inventory changed.

The real refusal diagnostic is preserved at
`local/codex-residents/pin-checker/last-probe-failure.txt`; the pending notification
is beside it. The checker did not deliver a live notification or wake residents.
The fake house API test verified role lookup, receipts, stable gesture IDs and
`to=nobody`; live delivery remains unchecked.

Visible notes: **Runtime pins** (`role=runtime-pins`) in the Handbook and
**Runtime updates lack a verified re-pin gate (a6498)** in Rough spots.
The Runtime pins introduction is not a successful checker receipt.

## Finish in a worker-capable environment

1. After house landing, run the landed checker outside the nested
   Codex builder token, using its existing approved Desk MCP configuration for
   the record route. `runtime_pin.py --recheck --mcp-config <existing-config>`
   changes no persistent setting. A same-byte recertification keeps the existing
   retained binary path. Do not manually edit the locks to bypass a failed probe.
   IMPORTANT: healthy-pin startup skips probes. The current locks are healthy,
   so an ordinary adapter start alone will not perform this recertification.
   An explicit `--recheck` is required. Verify source Authenticode/provenance
   and the full mock matrix before any success claim.
2. All three mock probes and exact inventories must pass. Inspect the generated
   Runtime pins verification/publication receipts and previous-lock snapshot.
   The Astra worker probe was not reached in the failed full run.
3. After landing, use the house to run one harmless real Codex resident turn and
   one harmless `gpt-6-astra` worker turn. This has not been attempted here.
   Do not copy credentials into this worktree or modify the account/profile.
4. Watch the first live record/notice: it must address nobody and wake no
   residents. Then update pending evidence in README, Rough spots, Handbook and
   the card. Source-ready now does not claim those live acceptance checks.
   The Handbook's exported markdown was not edited directly.

No browser/visual test is needed for this transport-only change. Full health,
the entire repository suite and live notification delivery were not run.

Two empty pytest-cache directories created by the first pytest run cannot be
removed with this sandbox token (WinError 5):
`pytest-cache-files-7qx7m4r6` and `pytest-cache-files-nwwfsxzw` at this worktree
root. An empty-directory removal was attempted after verifying both paths were
inside the worktree. No ACL or permission setting was changed to bypass it.
Git status warns about these directories; they contain no tracked change.
