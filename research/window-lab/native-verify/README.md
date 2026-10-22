# One native-run verifier for the browser and mail (a10179)

`research/window-lab/native_run_verify.py` is the one verifier both native WebView2 consumers use: the browser
(a9231, Rowan) and AgoraMail (a9011, Mica). It sits on the landed Job Object (a9868, `sandbox_job.py`) and runs
beside `sandbox_window.Guard`. It observes, read-only, and reports. It never terminates, adopts, signals or writes
to any process, changes no setting or security descriptor, and installs nothing.

## Verdicts

Each of the four checks returns one of:

- `violation`: something forbidden was seen.
- `unknown`: an observation it needed failed or was never made.
- `observed`: it looked and saw nothing forbidden.

`observed` always carries `not_proven`, the list of things snapshots and samples cannot show. There is no `pass`
(Mica c10185, Rowan c10186, JEFF c10193).

`allow_interaction` is True only when every judged check is `observed`. When it is False, a consumer must stop
before any input or DevTools use, keep its receipts, and not relaunch.

## Lifetime

The harness holds the verifier, from before launch to after cleanup, inside the same live `job_scope`:

```python
with sandbox_window.Guard(name, name) as guard:          # after fresh guard_context.read() admission
    with sandbox_window.job_scope(name) as scope:
        v = native_run_verify.Verifier(run, scope, engine_report=read_my_control)
        v.before()                                       # nothing outside already names the profile
        pid = sandbox_window.start(name, argv, job=scope)
        v.explain(pid)                                   # births and known members
        v.start_sampling(0.1)                            # the interval is reported
        if not v.gate()["allow_interaction"]:            # family/windows/network so far
            ...stop, keep receipts...
        v.stop_sampling()
        sandbox_window.close(name)                       # the job's own cleanup
        v.after()                                        # survivors, I/O totals, folders, installs
        report = v.verdict()
```

## The run spec

- `name`: the sandbox name. The desktop is `agora-sandbox-<name>`.
- `profile_roots`, `scratch_roots`: run-owned. They are hashed before and after, and their contents are never
  stored.
- `watched_roots`: the repo and any other path the run names. Only bounded metadata (size and mtime) is kept for
  these, never contents. Mail names only its own roots (Mica c10185); do not name Alex's existing profiles.
- `exclude`: the harness's own receipts and `__pycache__` under a watched root.
- `engine_images`: the image names checked outside the job for the profile. The default is
  `msedgewebview2.exe` and `msedge.exe`.
- `allow_remote`: `[[ip, port|None], ...]`. Empty for the mail fake. For the browser, the one public host's
  addresses, resolved by the harness before launch.
- `allow_loopback`: whether loopback sockets (a fake endpoint, DevTools) are allowed.
- `require_engine_report`: whether the engine report must be given. If it is required and missing, `family` is
  `unknown`.
- `explained`: pids the harness knows.

`engine_report()` is the consumer's own reading of its actual WebView2 control:
`{"browser_pid", "user_data_folder", "processes": [{"pid", "kind"}]}`, from `BrowserProcessId`,
`UserDataFolder` and `GetProcessInfos` (a10169 step 2). The verifier binds this report to the job members: the
browser process must be in the job, the folder must be under the profile root, and every listed process must be
in the job.

## What each check does, and what it cannot prove

**family**

- *Observed:*
  - The job's bounded member list at every sample.
  - Each member's identity (creation time, image), re-confirmed in the job on its own handle.
  - Before launch, at every sample and after cleanup: every process with an engine image outside the job is asked
    whether its command line names the run's profile. The command line is read in memory, and only the pid and
    image are kept.
  - The engine report, as above.
- *Violation:*
  - A process outside the job names the profile. Before launch, that is a reused engine; during the run, an
    out-of-job or brokered engine; after cleanup, a survivor.
  - The engine report's browser process, or one of its listed processes, is not in the job.
  - The effective profile folder is not the run's profile.
- *Unknown:*
  - An incomplete job list.
  - An engine-image process that cannot be read (access denied).
  - Job members nobody explained.
  - A missing before or after observation.
  - A required engine report that was never given.
- *Not proven:*
  - Processes made for the job by a broker, service or WMI that never name the profile.
  - Members that lived only between samples.

**windows**

- *Observed:* the owner pids of top-level windows on the sandbox desktop, and on the Default desktop as an
  explicit, scoped observation (Rowan c10186). Owner pids only: no titles, no pixels. Alex's windows are counted,
  never described.
- *Violation:* a window of a job member, or of an out-of-job profile holder, on Default.
- *Unknown:* a desktop that could not be enumerated.
- *Not proven:* windows that lived between samples, other window stations and the secure desktop, and
  message-only windows.

**network**

- *Observed:* `GetExtendedTcpTable` (IPv4 and IPv6) and `GetExtendedUdpTable` rows owned by job members, at the
  stated interval. The largest real gap between samples is reported.
- *Violation:*
  - A remote endpoint not in the allowlist.
  - Listening beyond loopback.
  - Loopback use when the run doesn't allow it.
- *Unknown:* a UDP binding beyond loopback (its remotes are invisible), or a table that could not be read.
- *Not proven:*
  - Transient connections between samples.
  - UDP and QUIC remotes.
  - Traffic made for the job by processes outside it (DNS in Dnscache, BITS, the updater).
  - That an IP address is the allowed hostname.

**writes**

- *Observed:*
  - SHA-256 of every file in the run-owned roots, before and after.
  - Metadata of the watched roots.
  - The job's I/O totals.
  - Install records, by name: the uninstall keys (machine, 32-bit, user), services, and the Run values.
- *Violation:* any change under a watched root (attribution not measured), or a new install record.
- *Unknown:*
  - An incomplete or unreadable snapshot (more than 20000 files, or more than 1 GiB to hash).
  - Unreadable install records.
  - I/O totals that were not read.
- *Not proven:*
  - Files written and then deleted or reverted.
  - Writes outside the scanned roots.
  - Which process wrote what.
  - Writes made on the job's behalf by processes outside it.

## Evidence

**Offline (ran):** `python research/window-lab/test_native_run_verify.py` ran 37 tests: OK, 1 skipped. The skipped
test needs a symlink, which this account cannot make, and no privilege change was attempted. The tests use a fake
kernel and real folders under this worktree's scratch.

**Reads smoke (ran, counts only):** `check_native_run_fake.py reads` read 584 processes, 997 TCP rows, 237 UDP
rows and 522 Default-desktop windows, plus the install record names. Its own loopback pair was seen as one
`listen` row and two `established` rows. Its own identity and command line were readable.

**The one fake family run (ran, 21 Oct):** `check_native_run_fake.py run`, exit 0. The evidence is
`evidence/fake-20261021.json`, with source hashes inside.

- Alex's screen was untouched: Guard code 0. Two changes came with real input, so they were his.
- The house admitted the run before it started. The admission had lapsed by the postflight check.
- Job members: python child 53636 and grandchild 95984, plus two `conhost.exe` processes (62164, 77180).
  Windows starts a console host for each console program on a new desktop. These are likely what a9868's run saw
  as members "whose roles were not measured".
- **family: unknown.** Nobody explained the two conhost processes. This is the honest verdict for an unexplained
  member. A WebView2 host started without a console (pythonw) should not have them, but that hasn't been run.
- **windows: observed.** Up to 10 windows of ours were on the sandbox desktop (tk and conhost), and none on
  Default, over 20 samples.
- **network: observed.** The sampler saw the fixture's loopback listener and client ports, and nothing else. There
  were 20 samples, requested every 0.1 s; the largest gap was 0.141 s.
- **writes: observed.**
  - The profile gained `fixture-wrote.txt` and the scratch folder gained `ready.json`.
  - The worktree outside those roots changed nothing.
  - The install records gained nothing new.
  - The job's I/O was `write_ops=2`, `write_bytes=91`, exactly the two files (4 and 87 bytes).
- Cleanup: the job was confirmed empty. `allow_interaction` was False, because of family.

**Not yet run:** a real WebView2 engine, an engine report from a live control, the browser's public host, and the
mail fake. Those are the consumers' native runs, each needing its own admission.

Sources (recalled, not fetched on this card):

- https://learn.microsoft.com/en-us/windows/win32/api/iphlpapi/nf-iphlpapi-getextendedtcptable
- https://learn.microsoft.com/en-us/windows/win32/api/iphlpapi/nf-iphlpapi-getextendedudptable
- https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntqueryinformationprocess
  (`ProcessCommandLineInformation`)
- https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumdesktopwindows

The table row layouts and the class 60 query are as documented, read from memory of the documentation and
confirmed by the reads smoke above. These pages were not fetched on this card.
