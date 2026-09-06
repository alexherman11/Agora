# Agora3

Agora is a computing environment that you and JEFF can reshape while using it.
Applications, interfaces, tools, skills and data definitions are native world
objects. A Linux workspace supplies general execution; a small protected host
preserves world history, authority and recovery.

This is a new codebase. The architecture and transition plan are documented;
the runtime is not implemented. Start with [the design index](docs/Start%20Here.md)
and [implementation status](docs/Implementation%20Status.md).

## Development

Python 3.12 or later and uv are the initial host development tools.

    uv sync --dev
    uv run agora3 --help
    uv run agora3 --version
    uv run python scripts/check_docs.py
    uv run ruff check .
    uv run ruff format --check .

The CLI currently identifies this development skeleton only. It does not create
a world, launch a VM, connect a model or change the machine.

[AGENTS.md](AGENTS.md) describes contribution boundaries.
[The transition plan](docs/Transition%20Plan.md) defines the first runnable slices.
[Decisions](DECISIONS.md) records choices and unresolved questions.
