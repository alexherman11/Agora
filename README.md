# Agora3

Agora is a general-purpose operating environment shared by a person and JEFF:
ordinary things keep their identity while the ways of viewing and using them can
change. A Linux workspace supplies general execution; native objects, applications
and history make that work understandable and portable.

Start with [the documentation index](docs/Start%20Here.md),
[the unratified values statement](docs/Constitution.md), and
[the vision and present structure](docs/Agora%20Spec.md).
[Native Development](docs/Reference/Native%20Development.md) connects the Linux VM,
native packages and the experience of asking JEFF to create new capabilities.

The first runtime includes a durable native world, an editable desk and chat,
JEFF through managed OpenAI-account sign-in, and native Python packages executed
inside a dedicated Linux VM. A second VM resets before candidate execution.
See [Implementation Status](docs/Implementation%20Status.md) for verified behavior
and [Runtime Guide](docs/Reference/Runtime%20Guide.md) for the implemented API.

## Development

Python 3.12 or later, uv, OpenSSH, and VirtualBox are required on the host.
The setup recipe creates **new Agora3 VMs**; it does not adopt an existing machine.

    uv sync --dev
    uv run python scripts/setup_guest.py --world worlds/dev --port 22333 --start
    uv run python scripts/setup_yard.py --world worlds/dev --port 22334
    uv run agora3 --world worlds/dev serve --port 8790

Open the local launch link printed by `serve`. Its fragment is a local operator
credential; keep it private. Use **Sign in with OpenAI** if the managed account is
not already signed in. The tested Astra runtime is Codex 0.153.4; an explicitly
configured `AGORA_CODEX_BIN` wins over executable discovery. OAuth tokens stay in
the managed host credential path and are never copied into the guest.

The main guest has broad root access and NAT networking. The host retains native
history, current authority and recovery. `guest.execute` is real Linux execution;
there is no fallback that executes authored code on Windows. The separate yard
has no live world token and resets to its clean baseline for each candidate.

## Checks

    uv run pytest -q
    uv run python scripts/check_docs.py
    uv run ruff check .
    uv run ruff format --check .
    uv run agora3 --world worlds/dev verify

The live authoring probe makes an actual Astra request using your account and
executes in the configured Linux machines. Invoke it deliberately:

    uv run python scripts/probe_authoring.py --machine worlds/dev/machine.json

JEFF's accepted draggable shell and its authored tests are retained verbatim in
`examples/jeff-authored-notes`. The current development world already runs that
native revision. To install the example in another local world:

    uv run python scripts/install_package.py examples/jeff-authored-notes --id agora.shell --world worlds/dev

This uses source/save/build/install operations, preserving existing application
data. The supplied shell remains a simpler baseline so future authorship can be
tested with dragging absent. The exported package's tests are a retained artifact
with their own browser fixture, separate from the platform regression suite.

Use the independent **Recovery** link if the authored interface fails. It can
restore the supplied shell without restoring old note data, revoke development
access, reconnect the native guest client, or power off the main VM. From another
terminal, `uv run agora3 --world worlds/dev stop` revokes native access and powers
off the main guest. Stopping a model turn does not undo completed changes or kill
every independent guest process.

This is an early development environment, with one foreground JEFF turn at a time.
Memory retention domains, computed facet bindings, background agent delegation,
shared rooms and device distribution remain open directions. Code lives in `src/agora3`;
private world databases and VM files remain ignored by Git.

[AGENTS.md](AGENTS.md) covers contribution practice.
[Decisions](DECISIONS.md) records architectural choices and their reasons.

## Development through use

The documentation now separates vision and current structure from speculative
future machinery. [Review Coverage](docs/Review%20Coverage.md) maps the September
9 commitment review to the revision. [The isolated presentation experiment](experiments/visual-presentation/README.md)
retains initial evidence and the repaired review package; it does not activate
that package in the main world. Future experiments will compare candidate
machinery on increasingly realistic native application work.
