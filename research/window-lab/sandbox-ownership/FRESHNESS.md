# House screen-state sampling (a10644)

Source change: the live, non-fake frontier house owns one daemon sampler.
It samples at a one-second start cadence, with no concurrent observations.
An observation taking longer than that is followed immediately by the next.
The main loop supplies its latest `guard_nongame` string; the sampler does not
read or lock a world, wake a resident, or register any Windows wake timer.
Policy-read failure clears the cached allowlist. Shutdown signals and joins the
sampler (bounded four seconds); it is not a separately surviving process.

The fixed main-checkout output path, atomic replacement, timestamp-at-start,
dual-clock five-second freshness check and all admission policy stay unchanged.
A stalled native probe, OS scheduling delay or suspended machine can still make
a sample stale: readers must continue to refuse it. No fake fresh timestamp,
worker publication or policy fallback is added. Freshness alone is not admission.

Offline:

- `test_guard_context.py`: 20 tests passed, including independent publication
  while the main thread waits, live-frontier-only startup, shutdown, slow probes,
  failures, existing atomic publication and refusal policy.
- `test_house_restart.py`: 13 tests passed.

Full `health.py frontier-try` at e26902 finished in 303.7 s with failures;
this is not a clean health claim. Python/scripts, guard context, restart,
95 help notes and 103 compiled lenses passed. Failures included sandbox temp
permissions, unavailable door/browser/fixture cleanup, the textedit lock,
four reach assertions and other suite errors.
`test_followups` also refuses its old hash-bound staging manifest before tests:
its expected house hash is `40b9a403...`, while the unchanged HEAD is
`535e71a3...` (LF) / `4bd83434...` (CRLF), and the old cfg anchor already occurs
twice on HEAD. This pre-existing staged integration is left unchanged, not
silently re-approved against the new source. The other health failures have
not been established as baseline failures by a second broad run.

Read-only live measurement:

```
python research/window-lab/sample_guard_age.py
```

This performs exactly 20 reads, one second apart, prints wall/boot ages,
admitted/reason and bounded foreground metadata; it never launches a browser,
requests a run, writes a sample, or retries admission. Exit 1 means at least one
sample was not fresh; it does not mean every other sample admitted.

**Pre-landing baseline only**, 22 October 2026, live publisher PID 76620:
20 reads, 3 distinct observations, 6 admitted/fresh and 14 stale refusals.
Wall ages min 2.719882 s, median 7.231455 s, max 14.016350 s.
All reads reported pythonw.exe, verified HUD, state 2, Default desktop and
game unknown. The six admissions reflect the existing world policy; they
are not proof of no game or of an admitted browser run.

After the house lands and loads the new source, rerun this finite measurement.
Record its actual distribution and process identity; require all 20 wall/boot
ages in [0,5] before marking the live freshness acceptance complete. If it fails,
retain the refusal and diagnose the measured cause rather than raising the
ceiling. No post-landing/live improvement is claimed by the baseline above.
