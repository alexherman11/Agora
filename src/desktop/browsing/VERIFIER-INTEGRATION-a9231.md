# Shared verifier integration checkpoint — 22 October

Source only, worker-a9231 / codex-builder-1, receiver f337dfd.
Prior nine-file integration remains preserved in house checkpoint795151d.
No ready, landing, browser launch, host query, cleanup, public page or activation.

## Built

The parent now requires an injected shared verifier; absence refuses before any
native scope. `before` precedes suspended birth; measured root birth is added
before sampling. The engine fence and shared interaction gate both precede the
child admission file. Sampling stops before shared Job cleanup; `after` and the
final verdict run while the Job is still held. Verification failures are retained
as unknown and cannot turn cleanup into a containment claim.

The child prepares an actual-control report from BrowserProcessId,
Environment.UserDataFolder and Environment.GetProcessInfos before requesting
admission. Parent callback checks its fixture token/host/engine envelope. This
JSON coordination is not authenticated same-user exclusion; kernel provenance
remains the shared verifier's job. Native SDK compatibility remains untested.

Consumer policy conservatively requires `family.brokered` and `writes.unscanned`
to be proved. This is a conservative interpretation of required containment,
not a previously accepted decision that sampled observations suffice. These are
documented permanent limits of this snapshot verifier: brokered processes that
do not name the profile and writes outside scanned roots are not certified.
Even ideal observed family/windows/network evidence cannot open its gate with
the first requirement. Do not launch merely to rediscover that deterministic
refusal, remove requirements silently, or claim this is a native test result.

Rowan/JEFF must decide whether the bounded offline fixture may explicitly accept
these observational limits, or whether a stronger containment boundary is
required. No new service/security mechanism is proposed here. Public-page
admission remains separate and is not authorized by that narrower decision.

## Ran / read / not run

- Read the live charter and latest c10398/e25453; shared verifier source/README
  and guidance. Transferred verifier remains unchanged, SHA256
  d51e118898dde4d952d88a3af904382e44e7f03800ce3b8f5015b1e7e96f8c7c.
- Ran pinned Python unittest discovery `-s src/desktop/browsing
  -p test_admission*.py`: **Ran 44 tests in 0.600s; OK**.
- New offline tests cover verifier lifetime order, absent verifier, before/after
  failure, gate refusal without a content-admission file, envelope forgery, and
  the delivered real verdict implementation's permanent-limit refusal under
  ideal mocked observations. Fakes are not native containment certification.
- Ran py_compile for all four changed Python files: exit0.
- Ran git diff --check: exit0.
- Shared verifier's own test file was not transferred; not rerun. No whole-health
  result claimed. No native attempt or fresh host guard query was needed after
  the deterministic policy blocker; no native closure or screenshot exists.
- Legacy process ownership remains UNKNOWN and untouched; parent stays paused.

## Raw source hashes

All paths below are under src/desktop/browsing:

```
admission_job.py 0e3943e7a8d378f63480204ade71b15b81dbc79117e835e4476f89728109cf0b
admission_probe.py 4159eaa0d26313d7b5448fd540c15bdb3562be1e9a3ba518022c3b4e209f7912
run_admission.py 03fe08b73ef44d7773ed9f6c4efa102eed4428d1f5ebff483867cc99d2318e18
test_admission_job.py 2ddff867c2e429648cced79aa6234b93db351bbf54c06b01e211ba38f544a429
```

Four Python files plus this report are staged worktree edits, not landed.
Reversal is to decline those five files against receiver f337dfd through the
house; preserve historical source, manifests and reports. Shared modules,
HOUSE_FILES, world chrome, runtime settings and live layout are unchanged.
