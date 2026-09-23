# Running the GPT-5.6 Terra text-desk trials

This packet reproduces the latest **synthetic text-desktop experiments**, not a
live Agora desktop test. Run from the existing local lab; no VM or live world is
needed. The runbook lives on the Agora4 line; the lab remains in the Agora repo.

## Which SDK did we use?

**Codex Python SDK, with managed ChatGPT account sign-in.** The harness imports
`openai_codex.client.CodexClient` through the frozen Agora `Jeff` transport.
Codex owns the model/tool loop; our Python process implements the simulated desk,
dispatches tools, enforces budgets and records evidence.

We did **not** use OpenAI Agents SDK (`agents.Agent` / `Runner`), the hosted Agents
API, or this chat's managed/delegated subagent tools. "Managed" here describes the
ChatGPT sign-in, not a separate agent-orchestration service. The Python SDK controls
a local Codex app-server over JSON-RPC. [Official SDK documentation](https://learn.chatgpt.com/docs/codex-sdk).

## Configuration to preserve

| Setting | Value |
|---|---|
| Model | `gpt-5.6-terra` — fail if unavailable or substituted |
| Reasoning | `medium` |
| Authentication | Existing Codex ChatGPT sign-in; no API key or copied OAuth token |
| Session | Fresh ephemeral thread per run; no resident history/focus injection |
| Domain tools | `look`, `act` only |
| Limits | 70 domain-tool calls; 300-second harness deadline |
| Model sandbox | `read-only`; `approvalPolicy: never` |
| Ambient capabilities | No shell, browser, filesystem tools, MCP, plugins, skills, memory or subagents |
| Runtime helper | Isolated code-composition host enabled; it can compose the supplied tools |
| Python SDK | Existing environment: `openai-codex==0.147.0`, `pydantic==2.13.5` |
| Instructions | Exact `INSTRUCTIONS` in `transport.py`; this is Text JEFF, not the production JEFF prompt |

Reuse `runtime_config()` and `thread_config()` from the frozen adapter. A default
SDK client would not reproduce these tool restrictions. Model configuration is
hard-coded in `TextJeff`; the parent adapter's Astra default is overridden.

## 1. Open PowerShell and check prerequisites

```powershell
Set-Location 'C:\Projects\Agora\research\text-desk-lab'
$trialPython = 'C:\Projects\Agora4\.venv\Scripts\python.exe'
$env:AGORA_CODEX_BIN = 'C:\Users\Alex\AppData\Local\OpenAI\Codex\bin\bffc5354119c8421\codex.exe'

Test-Path $trialPython
Test-Path $env:AGORA_CODEX_BIN
Test-Path 'C:\Projects\Agora\local\arrangement-current-20260916\native\src\agora3\jeff.py'
& $env:AGORA_CODEX_BIN login status
& $trialPython run_trial.py --help
```

All three paths must exist. If signed out, run `& $env:AGORA_CODEX_BIN login` and
complete the ChatGPT sign-in. [Official authentication guidance](https://learn.chatgpt.com/docs/auth).

**Portability limit:** `transport.py` imports the full frozen native source tree
at `C:\Projects\Agora\local\arrangement-current-20260916\native\src`. It is not
bundled with the lab's Git commit. On another machine, obtain that exact source
snapshot and compatible Python environment. Do not silently point it at a moving
Agora4 checkout and call the results the same baseline.

The executable above is the locally verified runtime path. If it has moved,
select the intended `codex.exe` explicitly and rerun the inventory probe. Record
that change as a runtime difference; do not fall back to an older npm launcher.

## 2. Verify the harness without a live model call

```powershell
& $trialPython -m unittest test_desk test_hard -q
& $trialPython probe_runtime.py --variant context-recovery
```

Expected: 16 tests pass. The compiled-runtime probe uses local mock inference;
its inventory must contain exactly `act` and `look`. `process`, `fetch`, `require`,
shell and patch access must be `undefined`. Repeat with `--variant outline` or
`--variant context` when checking those configurations. Stop on an unexpected
capability. This probe does not establish real model success.

Inside Codex's outer execution sandbox, starting the Python/runtime subprocess
required execution approval in this session. That is separate from the inner
model's `approvalPolicy: never`; do not loosen the model configuration to fix it.

## 3. Run the six live Terra trials

These commands use the signed-in account and create fresh model sessions. Run
sequentially for cleaner timing comparisons. Keep the same prompt and fixture
within each comparison pair.

```powershell
$trialStamp = Get-Date -Format 'yyyyMMdd-HHmmss'

& $trialPython run_trial.py procurement --variant outline --label "hard-$trialStamp-procurement-outline"
& $trialPython run_trial.py procurement --variant context --label "hard-$trialStamp-procurement-context"

& $trialPython run_trial.py handoff --variant context --label "hard-$trialStamp-handoff-baseline"
& $trialPython run_trial.py handoff --variant context-recovery --label "hard-$trialStamp-handoff-recovery"

& $trialPython run_trial.py impossible --variant context --label "hard-$trialStamp-impossible"
& $trialPython run_trial.py handoff-conflict --variant context-recovery --label "hard-$trialStamp-conflict"
```

- `outline`: sparse reads; original undo.
- `context`: combined inspection; original undo.
- `context-recovery`: combined inspection plus coordinate-level undo and event inspection.

The original-undo handoff is an expected failure; preserve it. Other available
smaller tasks are `meeting`, `proposal`, and `release`. Labels must be unique:
the runner refuses to overwrite an existing result directory.

## 4. Read results and audit attempts

Each `runs/<label>/` contains `report.json`, `tools.jsonl`, `initial.json`,
`final.json`, `events.json`, `external-edits.json`, and exact lab `source/` copies.
The report records model, reasoning, prompt, tool schemas and source hashes.

```powershell
& $trialPython audit_hard_runs.py
```

This audits all `runs/hard-*/report.json` and regenerates `hard-audit.json` plus
readable `transcripts/`. Its fixed historical pair checks compare the original
named runs; verify the new pair's prompt/initial state/model separately as well.

**Do not grade by final state alone.** Inspect attempted mutations, refusals,
protected state, replay, and the model's final claims. One previous run tried to
complete prohibited shipping; the guard refused, so state checks passed while
behavior failed. Call counts are domain calls, not model round trips. Preserve
failed trials and transport errors; compare timings across repeated matched runs.

The tasks and hidden checks are in `scenarios.py` / `hard_scenarios.py`. Change
those deliberately when adding a challenge; do not expose their answers as model
tools or alter the grading after seeing an answer without documenting why.

## Source and environment references

- Lab: `C:\Projects\Agora\research\text-desk-lab` (`docs` line; initial checkpoint `7c472ba`).
- Results and limitations: `HARD-RESULTS.md` in that directory.
- Frozen `agora3/jeff.py` SHA-256, verified for this packet:
  `aa6edd1def786308ec6fe8613759a1259ec546e30d0498705d01242bbe2f0dae`.
- Local `codex.exe` SHA-256, verified for this packet:
  `081e4de4be8e38fac6ed4d95e3b1a0b9f6d31c090ddc36e1696b349fe406f575`.
- [Official Terra model reference](https://developers.openai.com/api/docs/models/gpt-5.6-terra)
  confirms the model identifier and `medium` reasoning support. Account availability
  is checked by the runner, not assumed from the public model page.
