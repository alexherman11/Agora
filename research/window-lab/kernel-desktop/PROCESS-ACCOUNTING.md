# Process readings and helper cleanup

Task dk3683, increment 2, 6 November 2026. Source: seam/fix/word.
The missing word is `system.end-helpers`, tracked on that task.

`system.now` already includes `agora`: summed working set and private bytes
for the kernel's current descendant tree plus verified helper browsers.
`system.processes` shows the top 30 processes and totals over every process.
Working sets may share pages; the sum is not unique physical RAM.
Private bytes are committed memory, not necessarily resident RAM.

Each background refresh now collects CPU counters twice, about half a second
apart in one hidden PowerShell process, every 30 seconds. CPU is percentage of
the whole machine, with a monotonic elapsed interval. The first completed
refresh has CPU values. Missing counters and processes born/reused between
samples remain unknown. Windows' idle pseudo-process contributes zero, so idle
time does not inflate the `other` total. Reads of `system.now` and
`system.processes` return cached data and never wait for this sampling.

`system.end-helpers dry=yes` lists every matching helper process, including
those outside the top 30. `system.end-helpers` ends them. Both are admitted
through the kernel's existing `may=stewards` check, which includes the owner.
There are no PID, executable-name or profile-path selectors.

Ownership comes from the existing `profile_prefixes` roots: the desktop/world
state, repository `.tmp`/`.worktrees`, and the helper-created temporary prefixes
`kernel-shoot-` and `agora-snap-`. An absolute normalized browser profile must
match a prefix. Normal Chrome/Edge profiles outside those roots are excluded.
Descendants inherit a verified browser ancestor's profile only across
creation-time-checked parent links. An executable name by itself never qualifies.
This deliberately includes active test/snap browsers; it does not prove that
they are abandoned. Descendants with other executable names (for example a
crash handler) are included by ancestry so the whole verified tree is covered;
unrelated processes with those same names are excluded.

Execution takes a fresh inventory with a five-second timeout, opens every
selected process and checks its creation time before ending any of them.
Windows process handles stay open from identity verification through
termination; a reused PID cannot redirect termination. Preflight failures
close all opened handles and refuse without effects or alternate access.
Roots are ended before their sampled descendants. Concurrent cleanups refuse.
Exit checking stops after one second. A process spawned concurrently may remain.

Each result lists PID, verified profile, sampled working set, outcome and an
estimated working-set release for confirmed exits. Pending, denied and
unverified exits never count as released memory. These numbers are not measured
physical RAM freed. Partial execution is reported honestly. Dry runs open no
termination handles and create no external-effect record. Actual execution
produces an external-effect receipt; Undo cannot restore processes.
No profile files, settings, providers or credentials are changed.
Headless mode performs neither inventory nor termination.

Evidence from this worker:

- **Ran, live readings only:** `system.now` at sample time 1793992678.0427532
  reported CPU 42%, memory 84% (26.9 of 32 GB), Agora 6.14 GB working set and
  5.34 GB private, 103 processes. `system.processes` split this into 94 Agora
  processes (5,832,978,432 working-set bytes), nine helper Chrome processes
  (755,355,648 bytes), and 583 others (17,457,504,256 bytes).
  Those readings came from the previous live implementation; its CPU total
  included idle and is not evidence of CPU consumed by Alex's apps.
- **Ran, second live reading:** at 1793993263.0898314 (about 9m45s later),
  memory was 85% (27.3 of 32 GB), Agora 6.61 GB working set / 5.77 GB private
  across 107 processes. The Agora tree rose from 94 to 98 processes and
  5,832,978,432 to 6,324,428,800 working-set bytes; the same nine helper Chrome
  processes rose from 755,355,648 to 775,671,808 bytes. WebView2 PID 101720
  rose from 359,309,312 to 459,755,520 working-set bytes. This is an aggregate
  change with changing process membership, not an isolated kernel leak rate.
- **Ran, fixtures:** paired CPU arithmetic, first refresh, PID reuse,
  missing counters, idle exclusion, helper ancestry and path boundaries,
  more than 30 helpers, dry run, denial without fallback, preflight and
  partial failures, bounded unconfirmed exit, same-handle identity checking,
  headless no-effects behavior, and real kernel permission admission.
  The increment-2 follow-up passed **26 checks in 2.40s**, using fake process
  data/handles only, including whole trees across multiple profiles and
  cached reads returning while background sampling is blocked.
- **Not measured here:** one-hour kernel growth, retained Python objects,
  GC pauses, or the cause of the reported House/window timeouts. A cached
  process snapshot cannot establish any of those.
- **Earlier turn, outside the narrowed increment-2 checks:** 50 checks passed and the desktop screenshot
  handoff test failed, twice, with `window did not answer in 10 s`.
  **Read:** `widget_browser.Browser.__enter__` allows 20 seconds for a debug
  port; `Window.picture` then allows seven seconds for page readiness, and
  browser cleanup can wait ten seconds. The kernel's module-call deadline is
  ten seconds. These incompatible budgets explain how this path can time out;
  they do not prove which phase stalled in the live incident. No timeout was
  raised, test skipped, or real rendering replaced to make this check pass.
  The follow-up explicitly limits work to cleanup, CPU sampling and fake-process
  fixtures; this screenshot path is not changed or rerun for increment 2.
- **Not executed here:** live helper termination or system-module activation.
  Landing/activation and a steward's dry-run review then cleanup/outcome
  reading remain with the coordinator.
