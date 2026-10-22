# Enrolled sandbox families (a9868)

This is an opt-in in-process launcher capability, not a background owner,
cross-process authority channel, browser admission or legacy-runtime adoption.
Existing standalone CLI behavior remains direct-child-only and unknown for
whole-engine closure. No HOUSE_FILES, provider, guard policy or service changes.

Use from a harness that already has scoped run authorization and performs the
world-owned `guard_context.read()` admission and revalidation:

```python
with sandbox_window.Guard(name, name) as guard:
    # Revalidate fresh admitted house context immediately before effects.
    with sandbox_window.job_scope(name) as family:
        try:
            pid = sandbox_window.start(name, absolute_argv, job=family)
            # Drive only the authorized fixture on its hidden desktop.
        finally:
            result = sandbox_window.close(name, quiet=True)
            # Inspect result/receipt; refusal is not closure or retry permission.
```

The caller must retain the context through cleanup. `run_hidden`/`open_edge`,
separate CLI invocations, existing browser and mail harnesses do not yet opt in.
Consumers must adapt the lifetime deliberately; no implicit keeper is launched.
The bounded fake example is `check_sandbox_job_guarded.py`. Never rerun it without
a new explicit authorization; this card's single attempt is complete.

## What is owned

An unnamed, non-inheritable Job Object handle is held by the creating process.
Only KILL_ON_JOB_CLOSE is set; neither breakaway flag is allowed. Start records
the creator's native birth, job receipt ID, executable/profile/hidden desktop
intent before CreateProcessW. The child is created suspended with handle
inheritance disabled and no CREATE_BREAKAWAY_FROM_JOB. Assignment and membership
confirmation precede the durable complete birth receipt and ResumeThread.
The receipt UUID identifies evidence; it is not a reopenable kernel name.

Cleanup holds the existing per-name launch/cleanup lock, requires the same live
scope and matching root birth/job receipts, queries job PID-list/accounting,
persists intent, terminates only that job, and observes list empty AND active=0
within three seconds. Success archives the manifest, returning `receipt`.
`cleanup_complete=true` means this enrolled job was observed empty.
`runtime_closure` remains unknown for external delegation. Unknown/pending
termination is not automatically replayed; an empty observation can reconcile.
No OpenJobObject, taskkill, parent-tree sweep, new owner service, WMI inventory
or PID-based adoption is used.

Process crash closes the handle as a kernel backstop, but is not a durable
empty observation: surviving receipts remain pending/unknown and cannot
reopen/adopt the job. This does not promise power-loss durability. A job is not
a same-user security principal or a hostile-code sandbox.

Assignment/persistence failure never resumes the suspended thread or falls back
to an outside-job kill. If assignment failed, its suspended birth may remain
uncontained: retain unknown evidence for explicit host-owner reconciliation,
do not retry or claim KILL_ON_JOB_CLOSE covered an unassigned child.

Default CreateProcess descendants inherit membership; nested-job constraints
may refuse assignment. Processes created by an external broker/WMI, reused
engines, and pre-existing runtimes are outside this new job's boundary. Job
emptiness alone cannot prove their absence. Native WebView2/mail admission
requires its own evidence of engine membership/delegation and reconciliation
of retained legacy manifests. This fake is not WebView2 acceptance.

## Evidence

Offline commands (pinned repository Python):

* `research/window-lab/test_sandbox_job.py`: 19 tests, fake kernel/clock/processes;
  actual launcher and close functions exercised, not OS effects.
* `research/window-lab/test_sandbox_birth.py`: 12 tests.
* `research/window-lab/test_sandbox_receipts.py`: 29 tests; updated fake callee
  accepts the explicit job keyword, legacy locking/cleanup checks retained.
* `research/text-desk-lab/notation/test_guard_context.py`: 16 tests.
* `-m py_compile` on job, launcher and guarded checker.

ONE real run on 21 Oct: `check_sandbox_job_guarded.py`, exit 0.
Child 98952, fixture grandchild 90800; job ID
b05814f9f9b94f0f8772f45c07c5dd63. Kernel membership also included 60040 and
78884: their roles were not measured; no claim about their executable or parent.
Job before cleanup: 4 members/active=4/total=4. After job termination:
members=[]/active=0/total=4. The accounting `terminated` field printed 0; the
closure proof is the empty PID list plus active=0, not that counter.
Complete suspended birth and assigned=true preceded resume_result=1.
No second attempt, browser, mail, network, UI, screen capture or input.

The live house's fresh allowlist snapshots admitted the attempt with
foreground_exe=chatgpt.exe, full_screen=true, raw game=null (policy admission,
not a measured absence of games). Guard code=0, but local foreground unavailable:
**Alex-screen continuity unknown**. Snapshot admission is not continuous
screen proof. Original complete report and archive are retained under
`.tmp-agora/agora-sandbox/job-a9868-b7176d8721*`; the committed evidence copy is
`evidence/fake-20261021.json`, with source hashes inside.

Sources read:

* https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects
* https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject
* https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-terminatejobobject

No consumer activation on this card. Ordinary source landing is authorized;
new invocations load it, existing harnesses are not restarted. Reversal is to
remove an opt-in at the consumer while no run is active; retain all receipts
and do not downgrade old job manifests to legacy/direct-child cleanup.
