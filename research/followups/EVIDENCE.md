# Source-only evidence — 21 October 2026

Production integration remains **deployment-blocked and unwired**. JEFF accepted
the isolated engine/actual staged integration-test scope in c8458. No live
obligation was attached and no model/process/browser was started for acceptance.

## Ran

Pinned interpreter: `C:/Projects/Agora4/.venv/Scripts/python.exe`.

- `research/text-desk-lab/notation/test_followups.py`:
  **Ran 22 tests in 0.966s — OK**.
- `research/text-desk-lab/notation/test_calls.py`: **all passed**.
- `research/followups/staging.py`: both baseline hashes matched; both patched
  whole-file sources parsed. This command only prints/checks.
- Python AST checks for all added Python files: pass. Source/document trailing
  whitespace: `[]`. Unified-diff blank context lines intentionally carry a space.
- `git diff --check`: no output; `git diff --name-only`: no output. All source
  additions are new files; existing production files remain unchanged.

The 22 deterministic tests cover:

1. Busy recipient, coalescing, exact source facts, no duplicate send.
2. `want=rest` deferral versus ordinary resident rest.
3. Restart recovery of queues, excluding stopped time, no repeated written batch.
4. Unknown pipe outcome and attempted-at-crash recovery without replay.
5. One bounded deadline escalating an unavailable outside-session handoff.
6. Acknowledgment settling only its own obligation, not task or other obligation.
7. Forged acknowledgment refusal and older receipt not swallowing newer facts.
8. Stale revision, nonissuer and invalid finite deadline refusal.
9. Attach and transition arriving before the next observation pass.
10. Explicit stopped-time exclusion with fake clock.
11. Read-only pending/receipts through the actual staged Desk parser.
12. Actual staged `House.step`, busy then resting, sending once.
13. Revision validation from the real event's undo provenance, including direct
    property bypass of the convenience command.
14. Production files inert and distinct from the in-memory patched code.
15. History replacement freezing this mechanism while ordinary work still works.
16. Corrupt journal retained without silently resetting the baseline.
17. Deadline acknowledgment leaving underlying work unfinished.
18. Derived rule request refusal, then subsequent material event still consumed.
19. Exact delivery, blocker and admission property transitions.
20. Failed journal persistence preventing the pipe write.
21. Malformed request not skipping a subsequent quota event.
22. Undo retaining historical receipt facts while projecting actual current state.

These use a real in-memory world and mutation parser, the complete staged
`House.step`, and real `Resident.send` with an in-memory pipe/durable temporary
pending state. Clocks and runtime lifecycle are fake. Process/network tripwires
are installed in each test. No stand-in is claimed as a model acknowledgment.

## Exact prepared source

SHA-256 of bytes in this worktree:

| File | SHA-256 |
|---|---|
| `notation/followups.py` | `94e1fb4708e1a26690b598078bee060b16f9067b9fa571cd95d975d5089abf48` |
| `notation/test_followups.py` | `0b7429c5ac8ef5cdda1cd991f0799379c77de37be7820779080d175e5e62654c` |
| `followups/staging.py` | `ffc49fefa5e333c890b07bd166e33c85a9af27c7468be83c7af6c954d6e65d6f` |
| `followups/integration.json` | `18d1fd082ae4b639cb223cd8c31e7bccc825b582c57ed2a955643e01d1b91e76` |
| `followups/integration.patch` | `6a44f9eb0350c7aa6d18ea741abb6628d71b1b47afa9a9c8f0a04f27cd5c660a` |

The staged, normalized whole-file SHA-256 values printed by `staging.py`:

- `house.py`: `81c37886c414c4b4738fb015ac9beafec488f33970b960e936b9930c7664655c`
- `desk.py`: `ec5a689d01c2987bd269ca3be8409d9558442f475c23cba21e92a8b92144a030`

These are **not installed source hashes**. `integration.json` holds the exact
unmodified baseline byte hashes. Later drift must be reviewed and rebased.

## Read; not ran

Read current live charter, incident cards and exact source/knock events, plus
House/Resident/Workshop/listener/Desk mutation paths. Causal findings are in
README and c8453. No missed delivery inferred from silence.

Read Microsoft's
[QueryUnbiasedInterruptTime contract](https://learn.microsoft.com/en-us/windows/win32/api/realtimeapiset/nf-realtimeapiset-queryunbiasedinterrupttime)
for sleep exclusion. Tests injected the clock; no actual suspend/resume test.

Not run: full health, live resident/model/listener delivery, actual house restart,
real Windows sleep/deadline observation, browser/desktop checks or live Desk
follow-up commands. No changed runtime API exists yet, so no Handbook passage
was changed to claim one. The deployment/reversal and separate minimal lifecycle
gate design are in README. That lifecycle gate remains unimplemented.
