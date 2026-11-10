# Card review suites

`house.review` and `house.land` run the fixed House baseline and the card's
`test_suites` fact. This is a JSON list; no source edit is needed to select a
different card's tests. The owner/lead sets it using the existing `set` word.

Example value:

```json
[
  {"name":"WM suite","runner":"pytest","paths":["src/desktop/agora-wm"],"timeout":600},
  {"name":"Hidden native and Agora real drag","runner":"python","paths":["src/desktop/agora-wm/hidden_real_drag.py"],"timeout":180,"desktop":true}
]
```

In Lines, quote the entire JSON value and escape its interior quotes, for example:

```text
set <card> test_suites="[{\"name\":\"WM suite\",\"runner\":\"pytest\",\"paths\":[\"src/desktop/agora-wm\"]}]"
```

Runners are `pytest`, `python` and `node`. Python uses the House's pinned
interpreter. `paths` contains one or more pytest files/directories, or exactly
one Python/Node script. Paths must exist within the candidate worktree;
absolute paths, traversal, pytest selectors/options and shell commands are
rejected. Optional `timeout` defaults to 600 seconds. Empty or absent
`test_suites` retains baseline-only behavior. An invalid definition blocks review.

The House runs these processes itself, outside the coding worker's sandbox.
`desktop: true` checks the existing gaming gate before launching; the script
must also own a guarded hidden desktop and stop if gaming starts. It does not
grant permission to use the visible desktop. The real-drag script uses the
existing sandbox job ownership, cleanup receipts, hidden window guard and
gaming gate.

Each suite has a durable receipt with its name, runner, argv, candidate commit,
status, exit code, log path/hash and artifact directory. Timeouts, spawn errors
and gaming blocks leave failure receipts too. A failed suite does not suppress
the other suites. No publication occurs unless all pass. Owner review and
landing messages include the suite results; landing receipts include them
structurally. Each review uses fresh evidence directories. Changed card
definitions invalidate a saved review, including when a previously reviewed
card acquires its first suite.

During `house.land`, House settings `landing_timeout` bounds the entire attempt
and `landing_wait_timeout` bounds queue/Git/publication lock waits. A steward
can request `house.land-cancel <card>`. Overall timeout or cancellation stops
the attempt and preserves completed and interrupted suite receipts; it does
not continue to subsequent suites. Reviews do not hold the import/publication
lock. See `BUILDERS.md` for receipts, restart recovery and OS-denial limits.

The hidden real-drag check creates a disposable kernel world, an ordinary
captioned Win32 window and a production `GuiScreen` Agora lens window. Mouse
down/move/up go only to those hidden HWND queues, including Agora's production
drag strip. Real OS move-loop events feed the manager. It checks continued
visibility/liveness, intermediate neighbour positions, coloured preview-border
pixels, the final landing, mouse-to-movement latency and WM tick latency.
Artifacts include both traces, captured preview/after images, the visible
desktop guard verdict and cleanup receipt.

This check deliberately has no fallback to `SetWindowPos` motion or synthetic
drag events during a gesture. If Windows' native move loop cannot be driven
with queued messages on a hidden desktop, it fails with that diagnosis.
The House must establish that on the host; unit tests of the assertions are
not evidence that the real gesture passed. It never uses `SendInput`,
`SetCursorPos` or `SwitchDesktop`.
