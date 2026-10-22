# Exact source integration review — 22 October 2026

Builder: codex-builder-1, signing worker-a11327. This is source integration,
not new installation, native acceptance or runtime activation.

## Provenance (read and independently checked)

Preparation e30107 is recorded prepared. Exact-source-4 receipt
`3950437f0043a54111b84ece962566a0b3705448b194738a4e1321519eb4a88a`
records all 21 files, source commit
`7e819da099aae6016fec736070d39d37d33b39ac`, receiver
`f63a401b550699c8d9272ee73fcc84473f5ff770`.

Ran `verify_integration_transfer.py <receipt-path>`: all 21 authored raw hashes,
source blobs, received blobs and current files agree with
`evidence/integration-source-manifest.json`. The four registry pins agree with
the installed Composition example known, read through Desk. No re-pinning.
The separate manifest/document transfer had Git line-ending conversion; this
21-file code transfer is byte-identical across all reported representations.

## Review

- The only existing compiler changes are lexical row-field tracking: 17
  insertions, 8 deletions across scene.py and lens_ir.py. Registering a source
  no longer globally exempts same-named world props from freshness/gesture reads.
  No painter, pointer, provider, house or transport changes are included.
- Sources are discovered by the existing source mechanism. Modules select exact
  pinned entries from a host-created registry. World configuration cannot provide
  imports, Python, an effect executor or new authority.
- The module contract is trusted Python, **not a security sandbox**. Its bounds
  constrain composition/data; they cannot interrupt a malicious host callable.
  Installation/offer objects are process-local examples, not durable execution
  or lifecycle authority. Offers end at admitted-not-executed.
- The supplied callables perform interval arithmetic, bounded SVG generation
  and framing. Remote schema references are refused. Graphics escape labels and
  restrict role classes; there are no scripts, foreign objects or fetched URLs.
- Crew reads existing house/usage/quota publications. It separates context from
  quota and labels missing/stale observations. It creates no telemetry notes,
  model calls, process queries or new account connector.
- Integration fixtures have no automatic live installer; install_memory accepts
  only its synthetic session. Their host-window gestures were not invoked.

Author's workers-hud-update.md attributes the newer HUD route to Alex's 22:31
UTC request. Desk history independently shows the route prop by module-builder
at e29796; the original Alex instruction was not independently located here.
No route change is made by this integration. The earlier own-window acceptance
claim remains explicitly unverified.

## Ran

Pinned Python, own worktree:

```
python -m pytest -q -p no:cacheprovider \
  research/text-desk-lab/notation/test_capability_modules.py \
  research/text-desk-lab/notation/test_crew.py \
  research/text-desk-lab/notation/test_data_graphics.py \
  research/text-desk-lab/notation/test_module_row_scope.py \
  research/window-lab/data-dashboard/test_preview.py
75 passed, 5 subtests passed in 1.62s
```

`health.py frontier-try --only lenses,styles --json`:
world e29731 (2026-10-22T15:41:48), 29738 events. Python/scripts OK,
16 styles read (13 existing undrawn-property warnings), 108 lenses compile,
zero unexpected refusals, one expected p-if refusal. Includes composition
catalog/trace/workshop and crew-observatory. **Partial health**, 10.3 seconds;
no claim of full health or pixels.

Ruff --no-cache on the verifier, capability_modules.py, module_examples.py,
sources/modules.py and sources/crew.py: All checks passed.
`git diff --check main`: clean.

## Failures retained; not passes

Direct test_scene.py stopped at its existing tempfile-created worktree fixture
with PermissionError writing base@walk.pickle.

Pytest test_scene.py plus test_lens_row_refusal.py:
**2 failed, 56 passed, 6 errors in 3.30s**. Both failures are PermissionError
under tempfile-created directories (worktree fork and reports); six setup errors
are pytest temporary-directory access. Assertions were not weakened, files not
deleted, permissions not changed and the denied route not retried.
These test/support files are unchanged from main. Main was not separately run
in this worker; house judgment must establish baseline attribution, never count
these as green. Initial unittest discovery of function-only row-scope tests
found zero tests; the later pytest run actually passed all four.

The initial pytest cache warning left one inaccessible test-created directory,
`pytest-cache-files-pgxvchi0`. It is retained, with only that exact root path
excluded in .gitignore so source preservation need not enumerate it. No broad
ignore, deletion, permission change or exclusion of source/test assertions.

## Deployment and remaining acceptance

No live restart, backend swap, scene mutation, browser/native input, account
effect or Conversation send ran. The unrelated pending-transfer helper was
not imported or activated. The completed source transfer is not a descendant
shutdown certificate. Do not repeat preparation or the already applied transfer.

Ordinary house judgment remains the integration gate. Native HUD click,
Back behavior, guarded 1280/2560 screenshots and live numeric-label refresh
remain separate unrun acceptance. The author's older 137/139-test and pixel
reports are historical evidence, not results of this review.

Rollback is an ordinary reviewed source revert. Hide world entries only through
the author's scoped dock reversal after fresh identity checks; never a whole
world snapshot. Retain installed objects and subsequent user work.
