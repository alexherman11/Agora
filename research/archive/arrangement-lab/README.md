# Arrangement mechanics lab

September 16, 2026. **Executable design hypothesis, not a shipped Agora capability.**

**Update after live trials:** [LIVE-TRIALS.md](LIVE-TRIALS.md) preserves seven real
JEFF runs, their failures and useful findings. They used the repository's example
applications rather than the latest installed world-authored packages. The
current-world comparison was withdrawn; the narrower experiments remain valid.
The runner now requires an explicit baseline classification and refuses an
installed-world comparison before starting any VM or model. The model-only
evidence and limits below describe the initial lab, not all subsequent work.

This lab pressure-tests the following product vision against the current Agora4
application/view model and the proposed application-owned arrangement architecture:

> You're on a call; the desk is forty appearances of chaos; you say "JEFF, OAS
> stuff on the left, the mail thread where I can see it, everything else out of
> my way." Three selections, tile/place/sink, one intent, one attribution, one undo.

The important result is that this can have a coherent implementation, but a
generic placement API plus atomic batches is insufficient. The missing foundation
is a shared contract for **addressed intent, bounded selection, proposal composition,
admission, and compensation**. Applications can retain different internal models.

No production code, live world, running service, browser tab, or existing experiment
was modified. The lab is in the writable Agora research workspace; it studies
`C:\Projects\Agora4`, not the older runtime in this checkout.

## Subsequent installed-package experiment

The later [occurrence experiment](OCCURRENCE-RESULTS.md) uses captured installed
world-authored packages, synthetic subjects, real JEFF, guest execution and browser
checks. Its [scope](DOCUMENTED-NEXT.md) was selected from Alex's supplied design
transcript before implementation. It supersedes neither the earlier evidence nor
its limitations. The sections below describe the original model-only experiment.

## Run and inspect

From `C:\Projects\Agora`, using a working Python 3.12+:

```powershell
python research\arrangement-lab\run_checks.py
python research\arrangement-lab\demonstrate.py
```

No third-party modules, network calls, models, VMs, or live databases are needed.
The existing Agora virtualenv launcher could not start its base interpreter in
this sandbox; the checks ran with the system Python 3.14 instead.

- [DESIGN.md](DESIGN.md): proposed mechanics, alternatives, and integration route.
- [model.py](model.py): in-memory journal, guarded proposals, joins, stages, undo.
- [planners.py](planners.py): exact-scope selection, free placement, tiling, stacking,
  and a separate reading-order adapter.
- [test_mechanics.py](test_mechanics.py): adversarial and invariant checks.
- [evidence/round-1-counterexamples.json](evidence/round-1-counterexamples.json):
  two deliberately failing tests against the first model, retained as evidence.
- [evidence/latest.json](evidence/latest.json): final check result and source hashes.
- [evidence/scenario.json](evidence/scenario.json): forty-appearance scene, accepted
  changes, a later content edit, and compensating undo.

## Evidence and its limits

The final suite contains 41 tests, including all 720 delivery permutations of six
compatible contributions and 500 seeded geometry cases. Permutation testing checks
this particular set, not every possible operator algebra. The geometry cases check
minimum size, bounds, and pairwise non-overlap, not typographic usability.

The tests exercise a forty-appearance arrangement in one event; duplicate subject
references; independent arrangements; reading order versus stacking; stale semantic
classification and membership; stale viewport observations; incompatible writes
and stacking constraints; simulated current authority; two racing commits; retry
deduplication after simulated recovery; replay; and undo after intervening edits.

Two failures were found after the initial 35 tests passed:

1. A failed tile contribution left earlier proposed placements committable if its
   exception was caught. Contributions now poison the incomplete builder on failure.
2. A batch could change tags that another operation had just used for selection.
   Non-overlapping writes and a shared snapshot did not prevent this dependency.
   The model now rejects undeclared cross-contribution read/write dependencies;
   explicit stages support intentional dataflow while preserving one final commit.

These are tests of code written by one author in this session. The adapters were
not independently authored, there was no blind third-party extension trial, and no
full browser interaction or production gateway integration was run. The earlier
Tessera work supplied useful hypotheses; its old results are not counted here.

The model's authority table assumes an already authenticated caller. It does not
implement a security sandbox, read authorization, arbitrary untrusted plugins,
actual process failure, durable SQLite transactions, or distributed atomicity.
Recovery is replay of an in-memory event list, not crash testing a storage engine.
Semantic selection is simulated with exact tags, not an implemented semantic funnel.
The maintained-placement case tests exclusive ownership and explicit detach, not
a running reactive layout engine. Spatial transforms other than identity are refused.

## Assessment

The proposed foundation is promising enough for a bounded Agora4 integration slice.
It is not sufficiently verified to become a universal framework or permanent schema.
The next proof should be the actual OAS scene through the existing native gateway
and human browser, including a refused batch, a lost-response retry, a subsequent
content edit, and one undo. A second independently implemented surface should then
exercise the same protocol without inheriting this lab's storage conventions.
