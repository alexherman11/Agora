# Board builder verification — 26 October 2026

**Ran:** pinned interpreter, scratch kernels on ephemeral loopback ports, hidden
browser pages, real separate stdio processes. No live desktop restart, live
board installation or git state changes. This evidence awaits Claude's review.

Final combined command:

```text
C:/Projects/Agora4/.venv/Scripts/python.exe -B -m pytest research/kernel-lab/tests research/kernel-lab/modules/model/test_model.py research/community-app/board/test_contracts.py -q
94 passed, 46 subtests passed in 116.75s (0:01:56)
```

Final board proof command:

```text
C:/Projects/Agora4/.venv/Scripts/python.exe -B research/community-app/board/proof.py --model
BOARD: 62/62 checks passed; 32 people; 409 posts (82 replies); 14 simulated days.
```

The concise BOARD line is formatted from the same printed JSON in
`proof-run.txt`/`evidence.json`. Full evidence includes model answer, first-attempt
inference success, photo GPS checks, conversion undo, private-member positive
control and revocation, personal document hiding, final replay, and timings.

| Existing proof | Printed successful result | Evidence here |
|---|---|---|
| Council night | 21 of 21 checks passed | regressions/council/council-night.json |
| Hidden Hunt | 16 of 16 checks passed | regressions/hunt/hunt-evidence.json |
| Kits | 21 of 21 checks passed, plus unchanged Council scenario | regressions/kits/kits.json |
| BYO agent | 25 of 25 checks passed | regressions/agent/byo-agent.json; also rerun by final tests |
| Web host | 20 checks passed | regressions/web.txt and regressions/web/web-host.json |
| Local model | LOCAL MODEL: 27/27 checks passed | regressions/model.txt and regressions/model/local-model.json |
| Summarize | Ran 7 tests; OK | regressions/summarize.txt |
| Taskboard proof.py/proof_v2.py (same acceptance function) | 34 of 34 checks passed; ten-minute run, 619.27 seconds | regressions/taskboard.txt and regressions/taskboard/evidence/v2-proof.json |
| Widgets | 23 of 23 widget checks passed | regressions/widgets.txt |
| Pixel guy | PIXEL GUY PROOF: 11 checks passed | regressions/pixel-guy.txt |
| Painter contract | 11 of 11 contract checks passed | regressions/painter-contract.txt |
| Painter purpose | 9 of 9 purpose checks passed; BASELINE JS 11 / 11 | regressions/painter-purpose.txt |
| Painter isolation | 17 of 17 isolation/handle checks passed | regressions/painter-isolation.txt |
| Painter board | 28 of 28 component checks passed | regressions/painter.txt |

Both the default hidden variants and their assertions ran. Native-only optional
variants and fresh-agent tweak trials were not run. No visible native test
window was opened. The full taskboard triage was run once through proof.py's
re-export of proof_v2.run; its duplicate scheduled invocation was cancelled
after that passed. The already completed distinct proofs were retained.

**Ran, static:** Ruff F checks on the board folder and the two new kernel
modules: `All checks passed!`. No broad style rewrites of shared kernel files.

Earlier failures are not the final result:

- The realistic scenario found that once counted only outer module records.
  The general counter now counts component entries and in-flight steps; a
  contract test proves all-or-nothing refusal and undo restoring quota.
- An initial attempt to reserve make kind=post broke an existing private-draft
  web proof. The final implementation retains that syntax while applying its
  scoped post policy; web host and the combined suite pass.
- The real-model proof's first cold runs reached its six-second automatic-card
  wait before a summary appeared. Warm runs passed all 27 original assertions.
  The board proof can retry an offline-labelled read at most twice only after
  model.status confirms an available backend. No model service was restarted,
  model downloaded, or offline message counted as inference success.
- A concurrent painter builder updated HOW-TO-BUILD-HERE, leaving the genesis
  text stale. Two guide consistency tests failed. The genesis guide field was
  synced to that current document, preserving every other field; targeted and
  final combined runs passed. The painter guide prose itself was not rewritten.

Some earlier failed-run text/result files remain for diagnosis. This file and
the final successful logs above supersede those attempts; they are not claims
about a live installed build. No factual reliability claim is made for model
summaries or suggested alt text.
