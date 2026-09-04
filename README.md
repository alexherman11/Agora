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

`AGORA_WORLD` picks the world directory, `AGORA_ACTOR` who you are, and
`ANTHROPIC_API_KEY` (with `AGORA_JEFF_MODEL`) lets JEFF answer in the chat
panel. The shell also reads a `.env` file at start; copy `.env.example` and
fill it in. To route JEFF through OpenRouter, set `ANTHROPIC_BASE_URL` to
`https://openrouter.ai/api` and use a provider-style model id such as
`anthropic/claude-haiku-4.5`. On Windows use `agora.cmd` or `.\agora.cmd`.
