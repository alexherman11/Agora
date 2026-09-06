# Implementation Status

As of 2026-09-06.

## Working code

The repository contains a Python package skeleton, an installable CLI with help
and version output, development tooling and a local documentation link checker.
The CLI version is 0.0.0. It does not start a world, VM, UI or model session.

The current design set is indexed by [Start Here](Start%20Here.md). Architecture
claims elsewhere are proposed contracts unless supported by evidence here.

## Runtime inventory

| Capability | State |
|---|---|
| CLI skeleton and packaging | Implemented; verification recorded below |
| Authoritative world service, event storage and replay | Planned |
| Authenticated gateway and broad development delegation | Planned |
| Linux VM lifecycle, execution and independent recovery | Planned |
| Model/account authentication integration | Planned |
| Native source packages, builds and installed action registry | Planned |
| Application-defined facets and live queries | Planned |
| Browser runtime, native shell and conversation persistence | Planned |
| Candidate testing, diagnostics and activation | Planned |
| Native skill editing and installation | Planned |
| Asynchronous development agents | Feature horizon |
| Shared rooms, synchronization and broad device distribution | Feature horizon |

No runtime tests or demonstrations are implied by the documentation. Import/export
formats must be specified before a data migration is offered.

## Verification

Run from the repository root:

    uv sync --dev
    uv run agora3 --help
    uv run agora3 --version
    uv run python scripts/check_docs.py
    uv run ruff check .
    uv run ruff format --check .

Verified on 2026-09-06 with Python 3.12.10 on Windows:

- Dependency installation and editable package build succeeded.
- CLI help, default invocation and version output succeeded.
- All 278 local links and heading targets in 18 Markdown documents resolve,
  including Obsidian wiki-links. Code fences are closed and JSON examples parse.
- The documentation checker passed eight positive/negative fixtures covering
  missing links, missing headings, ambiguous names, malformed JSON and fences.
- The illustrative JavaScript handler passes syntax checking; its proposed
  runtime APIs are not implemented or exercised.
- Ruff lint and formatting checks passed.

These checks validate the scaffold and local documentation targets. They do not
exercise a world, agent, VM or authored application.

Domain tests will accompany actual domain implementation. Replay, atomicity,
boundary enforcement, recovery and real interface input are required evidence
for the corresponding proofs in [[Native Development]] §9 and [[Agora Spec]] §22.
