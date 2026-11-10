# One local observation — identity refusal, Job empty

22 October, worker-a9231 / codex-builder-1. Rowan c10805 releases exactly one
local-only observation after freshness c2fef2a / a10711. No public page, retry,
policy change, legacy cleanup, account action, host activation or restart.

## Preconditions and exact execution

Read live charter, collaboration guidance, documentation index/verifier topic,
a9231 through c10805, c10398/c10651 and freshness evidence a10711.
Read preserved ADMISSION-TAKEOVER, run/probe/policy/Job orchestration and reports.
Ran git status/log/diff: receiver f337dfd, prior integration checkpoint795151d;
four Python modifications and three reports remained. No reconstruction, reset,
other-worktree copy or merge. No production source changed in this round.

World query at approximately 09:47 listed this as the only working browser
continuation; parent a8247 remained paused. This is scheduler evidence, NOT proof
that every legacy host process is absent. The explicit c10398/c10805 boundary
uses a fresh independently enrolled Job; legacy ownership remains unknown.

Reran pinned interpreter unittest discovery:

```
C:/Projects/Agora4/.venv/Scripts/python.exe -m unittest discover -s src/desktop/browsing -p test_admission*.py
Ran 48 tests in 0.723s
OK
```

git diff --check: exit0.

Exactly one native command, no separate polling/retry:

```
C:/Projects/Agora4/.venv/Scripts/python.exe src/desktop/browsing/run_admission.py
```

Tool reported exit1 and printed:

```
receipt_directory: C:\Projects\Agora4\.worktrees\a9231\src\desktop\.tmp-agora\admit-5405bafb8ee3-fd6d5ab765ef46f6a20692d38876a2e4
offline_message_boundary_passed: False
job_closure: proven empty
```

The receipt timestamp is 1792687609.0379927 (22 October 09:46:49 PDT).
Initial/runtime guard admitted under existing policy; last recorded age 0.747s,
foreground chrome.exe, game null. Unknown game is not proof of game absence.
No worker observation publication or policy override.

## Observed refusal

Parent launcher birth PID **96436**, image argument the pinned venv python.exe,
created134371612090425561. Fixture receipt reports **29228**, desktop
agora-sandbox-admit-5405bafb8ee3, phase importing at elapsed0.000s.
The parent refuses exactly **child receipt PID mismatch** before admitting engine
or scripts. No engine-request report exists in this result; no engine is admitted.

Verifier measured three members of Job8cc4ed8e9b2d411689cef169d2daca02:

| PID | Role | Measured explanation |
| --- | --- | --- |
| 96436 | python process | matching retained launcher birth |
| 29228 | python process | parent96436, created after it |
| 85796 | console host | parent96436, created after it |

Inference, not proved root cause: the venv executable may be a redirector whose
child runs the script. The actual evidence establishes a measured descendant,
not why Python used that topology. Do not switch interpreters or weaken the PID
check to arbitrary Job membership.

Small proposed next source boundary for review: retain the root birth anchor,
separately admit the effective fixture host by a held kernel handle and measured
creation/image/ancestry to that root in the SAME live Job, then bind all child and
engine envelopes to that pinned host. Test unknown/unrelated Job members, PID
reuse, stale/changed host, wrong image, changed token and failed provenance.
Not implemented or authorized by this report; no further native attempt.

## Independent observations and unknowns

- Family **unknown**: actual engine report required and never supplied.
- Windows **unknown**: hidden desktop enumeration returned FileNotFoundError
  winerror18. This is a separate verifier observation; do not silently reinterpret
  it as an empty desktop or attribute it to the PID mismatch.
- Network **observed** across2 samples, requested0.1s, largest gap0.157s,
  no remote endpoints. All between-sample/UDP/broker/hostname/URL limits remain.
- Writes **observed** for named roots/install snapshots/I/O. Profile added/changed
  lists empty; owned receipt.json added, launch.json changed; watched source
  counts all zero. Does not prove no transient/unscanned/attributable/brokered writes.
- No initialized WebView2 version or native SDK/profile result in this run.
- allow_interaction=false; message boundary false; adversarial containment not
  certified. No screenshots, input/history journey or public rendering.

## Cleanup, distinct from acceptance

The existing shared close ran inside the retained Job scope, not an ad-hoc helper
or PID kill. Closure receipt matches the same Job descriptor, cleanup_complete=true,
before active3 [29228,85796,96436], after active0/pids[], remaining_pids[].
job_closure is **proven empty for this enrolled Job only**.
runtime_closure is still **unknown: external delegation not certified**.
No legacy process adopted, queried or cleaned.

Guard code0: alex: untouched; foreground/focus/cursor/input desktop were polled
every20ms, input desktop stayed Default, no sandbox window became foreground
or showed there, and no unsolicited cursor movement observed. This is sandbox
Guard provenance, not native capture of Alex's screen.

One attempted read of the ordinary active manifest path returned not found;
the preserved .closed receipt above is the actual closure evidence. No cleanup
was repeated and no artifacts deleted.

## Preserved receipt hashes and next owner

Run folder: src/desktop/.tmp-agora/admit-5405bafb8ee3-fd6d5ab765ef46f6a20692d38876a2e4

- launch.json SHA256 8CD2578D73D09D820C2D16C141C0EBBE7B68C01F44BA6FF07D7586184FC92B46
- receipt.json SHA256 D4A25218D4FF7928693148193F7841EEC2CE02632527724B6F97E5538AF4CF14
- source.json SHA256 8FBBCC2A92ED3631D777BF9450E519CEA69F8AD2548A234A460E84A1B36AE4D8
- ../agora-sandbox/admit-5405bafb8ee3.closed-1792687609254233900.json:
  E448CCA261C827AD5C4925E9ED956F64DC8CEC74C56B1D433367DD26EBCA8A74

source.json records exact unchanged native source:
run_admission81ea8a31..., probe4159eaa0..., job98821bd6...,
shared verifierd51e1188..., sandbox_jobc8e64ab3..., sandbox_window1f158a3a...,
sandbox_birth6857f088... (full values retained in the run).
Prior diagnosis/report hashes remain historical evidence.

Rowan/JEFF review this refusal and assign the narrow effective-host binding and
window-enumeration diagnosis before any new run. No native success, ready,
landing, lifecycle activation or one-click live capability claimed. Existing
prototype stays dormant; reversal requires no runtime action. Preserve all
eight source/report edits through the house before replacing this checkout.
