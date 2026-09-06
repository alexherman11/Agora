# Agora3

Agora is a general-purpose operating environment shared by a person and JEFF:
ordinary things keep their identity while the ways of viewing and using them can
change. A Linux workspace supplies general execution; native objects, applications
and history make that work understandable and portable.

Start with [the documentation index](docs/Start%20Here.md),
[the Constitution](docs/Constitution.md), and
[the master specification](docs/Agora%20Spec.md).
[Native Development](docs/Reference/Native%20Development.md) connects the Linux VM,
native packages and the experience of asking JEFF to create new capabilities.

The current code is a new scaffold, not a running OS. See
[Implementation Status](docs/Implementation%20Status.md).

## Development

Python 3.12 or later and uv are the initial host development tools.

    uv sync --dev
    uv run agora3 --help
    uv run agora3 --version
    uv run python scripts/check_docs.py
    uv run ruff check .
    uv run ruff format --check .

The CLI identifies the scaffold only. It does not create a world, launch a VM or
connect a model.

[AGENTS.md](AGENTS.md) covers contribution practice.
[Decisions](DECISIONS.md) records architectural choices and their reasons.
