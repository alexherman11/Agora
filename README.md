# Agora

An object-oriented computing environment layered over stock Linux, with an
integrated AI agent called JEFF. Entities carry typed facets; verbs are the only
way anything changes; an append-only event log is the source of truth.

| Read | For |
|---|---|
| [`docs/Start Here.md`](docs/Start%20Here.md) | the design vault: Constitution, Spec, references, essays |
| [`BUILD_PROMPT.md`](BUILD_PROMPT.md) | what Milestone One is, its acceptance script, and its scope |
| [`AGENTS.md`](AGENTS.md) | how to work on the code without fighting the design |
| [`DECISIONS.md`](DECISIONS.md) | settled questions, one dated line each, and the friction log |

Layout (M1): `kernel/` · `cli.py` · `shell/` · `jeff/` · `tests/` · `worlds/`
(gitignored). `research/` holds review dossiers and archived drafts.

## Running

```bash
uv sync                                  # Python 3.12, Loro, FastAPI, the Anthropic SDK
uv run pytest                            # the whole suite, acceptance script included
./agora init                             # worlds/default, with an empty desk
uv run python -m shell.server            # http://127.0.0.1:8787
./agora log                              # every event, with its actor
./agora project <entity> --budget 60     # an entity at a token budget
./agora rebuild                          # derive a fresh store from the log and compare
```

`AGORA_WORLD` picks the world directory and `AGORA_ACTOR` who you are. The shell
reads `.env` at start; copy `.env.example`. The example selects Astra through your
OpenAI account: `AGORA_JEFF_PROVIDER=openai-account`, `AGORA_JEFF_MODEL=gpt-6-astra`,
and `AGORA_CODEX_BIN` pointing to a current Codex executable (verified: 0.153.4).
Your existing Codex ChatGPT sign-in is reused; otherwise use **Sign in with OpenAI**
beside JEFF. This path needs no API key. Reasoning defaults to `medium`.
Restart the server after changing settings. On Windows use `agora.cmd` or `.\agora.cmd`.

Direct API billing remains available with `AGORA_JEFF_PROVIDER=openai-agents` and
`OPENAI_API_KEY`. That adapter uses the OpenAI Agents SDK; the account-backed
adapter uses the Codex Python SDK because Codex owns ChatGPT OAuth and token refresh.

Existing configurations without `AGORA_JEFF_PROVIDER` retain the Anthropic
backend. To keep it explicitly, set `AGORA_JEFF_PROVIDER=anthropic` with
`ANTHROPIC_API_KEY` and the appropriate model ID. OpenRouter's Anthropic-compatible
route uses `ANTHROPIC_BASE_URL=https://openrouter.ai/api` and a model such as
`anthropic/claude-sonnet-4.5`. These credentials are separate from the direct OpenAI
route. See [Astra Harness](docs/Reference/Astra%20Harness.md) for the integration
and verification status.


## Personal lenses

The first extension is a compact notes list with a preview of the selected note.
Start the shell, add notes, and ask JEFF: “Make my notes readable as a compact list,
with a preview when I select one.” JEFF can author, preview, and activate a stored
lens using the public tools. Definitions are inspectable; activation pins a revision;
the default desk and previous display remain recoverable. The view works without
the model. The chat panel is an intended future participant in this display system;
it remains protected shell code in the current implementation.

See `docs/Reference/Personal Lenses.md` for the implemented contract and
`docs/Agora Spec.md` §22 for the unordered feature horizon. `agora call VERB JSON`
provides CLI access to every registered operation, including `preview_lens`,
`activate_lens`, and historical `read`.

The browser establishes a local session; direct mutation requests need its token
and cannot supply their own actor. File imports default to `WORLD/imports/`.
`AGORA_IMPORT_ROOTS` explicitly adds sources (separated by `;` on Windows, `:` on
Linux). A file path supplied directly at the trusted terminal authorizes that file.
Imports capture snapshots; edits do not write back to the original source file.


## Executable capabilities

JEFF can now author executable components as world objects: new UI behavior,
computation over bound objects, persistent component state, and named actions
that appear in his current session. Ask “Can you make it so I can click and drag
the notes around?” The platform supplies input and scoped effects; JEFF must
write and test the behavior. Follow-up changes revise the stored program.

Candidates run against disposable state. Activation pins a tested revision;
Default desk and restoration remain available. Programs run in fresh, bounded
QuickJS contexts in a separate process, without filesystem/network APIs or
browser DOM access. This is a local experimental runtime, not a hardened OS
sandbox. Chat composition and distributed execution remain future directions.

Read [Executable Components](docs/Reference/Executable%20Components.md) for the
contract and limits. Real-provider trials are recorded in
[the validation report](research/holistic-review/executable-component-validation-2026-09-05.md),
including model authoring failures; runtime support alone is not a guarantee
that every configured model can successfully implement a request.
