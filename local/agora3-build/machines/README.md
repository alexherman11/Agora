# Dedicated Agora3 Linux guest

The first machine recipe creates a new VirtualBox guest from Canonical's Ubuntu
24.04 cloud image. It never adopts an existing VM. The protected host runs the
native gateway, canonical log and recovery; authored Python executes as root in
the guest. The broad development profile is one guest trust domain, with NAT
network access. It does not isolate packages from each other.

## Create and boot

Install VirtualBox and OpenSSH on the host, then run from the repository root:

```powershell
uv sync --dev
uv run python scripts/setup_guest.py --world worlds/dev --start
uv run python scripts/setup_yard.py --world worlds/dev --port 22334
```

The recipe downloads a pinned image, verifies its SHA256, creates a uniquely named
`Agora3-…` VM, gives it 1 CPU, 2 GiB RAM and a 16 GiB disk, and writes
`worlds/dev/machine.json`. Image bytes, disks, keys and serial logs stay under
ignored `local/guest/`; machine configuration and keys are never native objects.
An existing machine configuration causes setup to refuse reprovisioning. Yard
setup creates a second, distinct guest and captures a stopped clean snapshot.
Running yard setup again inspects an existing valid configuration without
replacing or resetting either VM. Two running guests use 2 CPUs and 4 GiB RAM in
total; the candidate guest is powered off between invocations.

The checksum is from Canonical's HTTPS [release checksum list](https://cloud-images.ubuntu.com/releases/noble/release-20260826/SHA256SUMS).
The pinned [VMDK release](https://cloud-images.ubuntu.com/releases/noble/release-20260826/)
is `ubuntu-24.04-server-cloudimg-amd64.vmdk`, SHA256
`fb3ba097a9013d759fa13ab22d2b4118bd55452c617ca3758a55303eea96de6e`.
This verifies against the published HTTPS checksum; detached GPG verification is
not implemented by the setup script.

[Cloud-init NoCloud](https://docs.cloud-init.io/en/latest/reference/datasources/nocloud.html)
initializes `jeff` with passwordless sudo and a dedicated SSH key. A host key is
generated before boot, provisioned into the seed ISO and pinned in `known_hosts`.
No SSH key scanning or trust-on-first-use acceptance occurs. Password login, root
login, shared folders, shared clipboard, drag-and-drop, USB and agent forwarding
are disabled. SSH is forwarded only on `127.0.0.1:22333`; use `--port` for another
available host port. NAT provides outbound networking and is not an egress filter
or a guarantee that other network services are unreachable.

The seed contains the guest's private host key and should remain in the ignored
machine directory. The guest receives no host login key, canonical world files,
model credentials or shared host filesystem. The provisioned SSH host identity is
not an assertion that software inside a root-controlled guest remains unchanged.

## Host supervision and execution

```python
from agora3.guest import Guest

guest = Guest("worlds/dev/machine.json")
guest.status()                  # VM lifecycle status; does not promise SSH readiness
guest.start()                   # starts this configured, Agora3-marked VM headlessly
guest.execute("id; python3 --version")
guest.stop()                    # host recovery: power off even when SSH is broken
```

`execute` returns stdout, stderr, exit code and an output-truncation flag. It is
explicit guest execution, not a native replayable operation. There is no host
fallback when the guest is missing, stopped or inaccessible. Execution refuses
changed clipboard/sharing settings. Lifecycle operations require an Agora3
ownership marker and a valid configured UUID; a VM name alone is insufficient.

The first boot normally takes about half a minute. Check `serial.log` in the
machine directory if SSH is unavailable. VM status reports that the machine is
running separately from whether a command has successfully reached Linux.

Host recovery powers off the VM without trusting a guest process. This can lose
unflushed guest filesystem writes; it does not change the protected native log.
Native replay does not start the VM or rerun guest commands. The yard uses a clean
baseline snapshot; coordinated restore of a live workspace remains future work.

## Python package action protocol

```python
result = guest.run(
    {"main.py": "def main(arguments, context): return {'result': arguments['x'] + 24}"},
    "main.py:main",
    {"x": 3},
    {"objects": [], "watermark": 0},
)
assert result == {"result": 27}
```

The transport validates relative paths, sends source plus JSON arguments/context,
and compiles every `.py` file inside the guest before invoking the named function.
Imports between supplied files work. The function returns JSON; ordinary Python
prints go to diagnostics instead of corrupting the result channel. Source is
never evaluated by the host. Input context is a serialized snapshot: mutating it
in the guest cannot mutate the protected native world. Returned proposed changes
require validation and a conditional commit through the native gateway.

Installed actions use the live guest and a fresh temporary source directory.
Guest root can install programs, touch other guest files, use the network and
inspect other live guest processes. GNU `timeout` terminates the ordinary process
group and its descendants; root can deliberately detach processes or alter its
own tools, so hard recovery is the protected VM power-off. Host output is streamed
into bounded buffers.

## Native access and disposable candidates

`NativeBridge(gateway)` starts a separate loopback HTTP listener and a pinned SSH
reverse forward into the live VM, on guest `127.0.0.1:18790`. The guest's
`/run/agora/config.json` contains its current native development token; model
credentials and host authority are never provisioned. Guest Python can use:

```python
import agora_native

objects = agora_native.call("world.query", {"facets": ["core.text"]})
```

The listener exposes the native registry through authenticated dispatch, including
package tools and actions. It has no host recovery, chat or system endpoints.
Tokens are checked against current durable authority; revocation blocks old
tokens, and resuming requires reconnecting the bridge. No bearer is returned in
status or command output. NativeBridge.close stops its SSH process and listener.
The HTTP listener limits requests and responses to 4 MB, 16 concurrent workers and timed socket
reads. This is an operator-started connection, not a guest-managed host service.

`Yard("worlds/dev/yard.json", main_guest)` uses a separate VM whose clean baseline
has no live native token, mount, client or reverse tunnel. Every build/candidate
run powers it off, restores that baseline, boots it, executes supplied source and
powers it off again. Invocations sharing a yard serialize across host processes.
Missing yard configuration or a reference to the main VM is a refusal; there is
no live-guest or host fallback. This separation is necessary because root in the
live VM can read its own native token. Merely hiding that token from an action's
environment would not isolate a candidate.

The yard returns proposed native changes for disposable-data validation; it does
not receive live-world authority. It still has NAT network access, so this does
not claim that arbitrary external requests can be undone or prevented. Its
Python/dependency environment starts from the pinned base image on each run;
additional reproducible dependency recipes remain future work.

## Evidence and limits

On 2026-09-06 a dedicated guest booted as Ubuntu 24.04.4 LTS with Python 3.12.3.
Pinned SSH returned `uid=0(root)` and Linux. A multi-file authored action returned
JSON containing a result and proposed native changes. An invalid unused Python
file was rejected before entry execution. A timed-out shell child was terminated.
Host power-off, headless restart and pinned SSH reconnection also succeeded. An
initial 2-CPU configuration stalled once during restart; the tested recipe uses
1 CPU and only 2 SATA controller ports. This is a local compatibility choice,
not an established diagnosis of the hypervisor behavior.

`tests/test_guest.py` tests missing and malformed configuration, source traversal,
no host execution fallback, pinned SSH options, ownership checks, sharing refusal,
invalid output and recovery independent of SSH keys. These mock the transport;
they are not evidence of a boot or a successful model session. The live checks
above were run against the actual VM. A live native bridge also committed a note
from guest Python into the protected log as actor `guest`. Two yard invocations
each found no main token or client, could not perform an unauthenticated live
write, and saw no filesystem marker from the previous invocation. The yard was
powered off afterward. Bridge/yard tests separately cover HTTP authentication,
route restrictions, revocation and fail-closed lifecycle behavior. No guest
desktop, browser, model process or general service manager is implied.
