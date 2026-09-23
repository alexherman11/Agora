# Cross-branch WIP checkpoint — 16 September 2026

These commits preserve existing work. They do not deploy code, restart services,
merge branches, or assert that all recorded historical runtime results were rerun.

| Checkout | Branch | Commit | Scope |
|---|---|---|---|
| `C:/Projects/Agora4` | `agora4` | `3e8316c` | Live-update repairs, voice diagnostics, tests and documentation |
| `C:/Projects/Agora/worlds/docs-restoration/repo` | `agora4` in the Agora repository | `8842766` | UI selection, voice/JEFF context and tests |
| `C:/Users/Alex/.codex/worktrees/6b83/Agora` | `codex/wip-voice-investigation-20260916` | `e1e0b2e` | Voice investigation script and metadata-only evidence |
| `C:/Users/Alex/.codex/worktrees/702b/Agora` | `codex/wip-live-update-repair-20260916` | `7d52447` | Repair source, original package definitions, investigation and browser-test report |
| `C:/Projects/Agora` | `docs` | `7c472ba` | Previously committed arrangement and text-desk experiments |

The commit containing this note additionally preserves the pending docs, working
guidance, security research, conversational-capability proposal, Tessera prototype
and evidence, and local UI-selection restart helper/report. Existing authored
content is checkpointed without revision or endorsement of its design choices.

## Checks performed now

- Current Agora4: 26 focused application, voice and diagnostics tests passed.
- Older docs-restoration Agora4: 27 focused selection, agent and voice tests
  passed; 2 optional checks skipped.
- Staged Python and JSON in the runtime/investigation checkpoints parse.
- Both runtime checkpoints pass whitespace checks. Three captured JavaScript
  files in the live-update investigation retain their original extra EOF blank
  line rather than altering captured evidence.
- No live-model, browser, deployment or activation scripts were run for this
  checkpoint. Earlier test claims inside preserved reports remain historical.

## Files intentionally retained locally

- The live-update investigation's raw chat, view, board, document and status
  captures; its temporary `repair/test-world/` database, credentials and releases.
  These are local working data, not source to publish.
- Tessera's `evidence/*-live-events.jsonl` and `evidence/*.log` files. These are
  generated runtime traces, including a roughly 93 MB event log. Source, fixtures,
  final-state snapshots, checks and screenshots are included in the checkpoint.
- Ignored virtual environments, caches, worlds and credentials remain excluded.

All excluded files remain in place. Nothing was pushed. Agora3 and the
native-applications experiment worktree had no pending source changes when checked.
