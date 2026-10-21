# One home base (a6928)

`agora_start.py` uses `hud_lifecycle.py` for home-base reconciliation.
It never removes `hud.pid`.

- A failed, incomplete, malformed or raced process inventory is **unknown**.
  An unreadable/malformed PID record is unknown too. Recheck in five seconds.
- A live matching Python/Pythonw process blocks a start even if the PID file
  is missing or stale. Script paths are exact, including sibling checkouts of
  this repository; the world and door must match. A script mentioned in `-c`
  text is not a host. A venv launcher and interpreter count as one host.
- A keeper gap or a door whose backend has `up=false` resets the HUD miss count.
  Two confirmed misses at least five seconds apart, with a live keeper and
  backend, permit a start. A launch gets 30 seconds of startup grace.
- `hud.py` holds a named Windows mutex for its whole run, scoped to world and
  door (loopback aliases normalize together). A second instance exits 76 before
  touching the PID file, witnessed rows, keys or windows. A pre-mutex legacy host
  also blocks a start via the inventory check.
- With multiple hosts, retain the newest one with a responsive native window
  titled `Agora home base`. Recheck its identity and responsiveness before
  ending each extra. No confirmed healthy survivor means no cleanup.
  Here “healthy” means native-window responsiveness, not a painter assertion.
- Termination opens one process handle, compares the original creation FILETIME
  **and executable** on that handle, terminates through that same handle and
  waits for confirmation. Each duplicate attempt logs both identities and its
  result. There is no name-based or PID-only kill or `/T` tree kill.
- `hud.py --stop` uses the same verified identities. Unknown or unconfirmed stop
  returns 75; `hud_restart.py` respects this and does not launch. The capture
  child notices its dead parent within two seconds. Normal capture shutdown
  also verifies the identities of its own launcher/interpreter.
- New HUDs retry a previously unavailable Ctrl+Alt+J once a second. Thus a
  survivor can acquire the key when an older duplicate releases it. Legacy HUD
  processes do not acquire new code until restarted.

Default-world callers retain `state/hud.pid`. Other world/door combinations use
a separate hashed PID filename, so a copy cannot overwrite the default record.
PID removal on exit requires that the caller actually claimed the record and
still owns it.

## Verification, 20 Oct 2026

Ran in worker/a6928 with the pinned repository interpreter:

```
python research/window-lab/test_hud_lifecycle.py --demo
Ran 36 tests in 0.213s
OK
```

The copy demonstration printed:

```
t=00: first miss: no home base process; preserving hud pid and rechecking
t=02: unknown: process inventory or hud pid record unreadable; do nothing and recheck
t=04: unknown: keeper/desk restarting or not ready; home base left alone
t=06: first miss: no home base process; preserving hud pid and rechecking
t=11: two misses: no home base process for this world; starting hud (pid record preserved)
t=12: duplicate home base: keep 30 created=300; end 20 created=200: ended | home base running; hud pid record preserved
starts=['hud']; verified fake ends=[(20, 200)]; hud.pid=999 (preserved)
```

The inventories, process endings and start requests above are **fake**; PID-file
checks operate on fresh temporary copies under this worktree's ignored `state/`.
The tests execute the actual supervisor adapter and HUD entry/key functions with
stubbed dependencies. They cover PID reuse between observation and termination,
survivor death during cleanup, unrelated processes, stale and missing records,
incomplete inventory, keeper restart, launcher/interpreter pairs and hotkey retry.

Ran a **real Windows mutex** test using a fresh private name: one holder blocks
a second handle and a separate hidden Python process; after release, acquisition
succeeds. Ran the real Windows command-line parser on a quoted script path.
No real HUD, input hook, visible window, live process inventory or live process
termination was used. WMI inventory and native window-health/termination adapters
were verified with fakes; their end-to-end run on a sandbox desktop remains
unchecked. Existing running supervisors/HUDs need to restart to load this code;
this commission did not restart Alex's processes.

Read primary API contracts:

- [CreateMutexW](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-createmutexw):
  atomic creation and `ERROR_ALREADY_EXISTS`; retain and close our handle.
- [GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes):
  creation time is a FILETIME; retain its full precision for identity checks.
- [TerminateProcess](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-terminateprocess):
  termination is asynchronous; check the return and wait on the same handle.
- [CommandLineToArgvW](https://learn.microsoft.com/en-us/windows/win32/api/shellapi/nf-shellapi-commandlinetoargvw):
  native quoting rules and `LocalFree` for the returned buffer.
