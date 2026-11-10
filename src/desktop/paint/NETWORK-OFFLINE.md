# Local paint network contract: offline increment

22 October 2026, worker-a10672, Codex builder-2. JEFF c11472 authorizes
offline source diagnosis/fix only. No native retry, ready, landing, setting
change, account action or restart was performed.

## Evidence and cause

Read the a11403 acceptance report, world note a11470. The Claude runtime
established profile-exclusion visibility and local foreground continuity.
Its one run observed an owned Edge utility process connecting to non-loopback
TCP443 before DevTools; the empty remote allowlist correctly refused. Owned
cleanup was proved empty in its archived receipt. This round did not query
those processes, replay that launch or repeat cleanup.

The exact service responsible (telemetry, update or another background
service) is not established by a TCP endpoint. No endpoint is newly allowed.
The empty allowlist is the intended restriction, not a defect. The launch
did not suppress background networking.

## Narrow repair

`open_edge` gains opt-in `local_only=False`; ordinary argument lists and
receipt fields are unchanged when absent. Paint requests True. It requires
a literal `http://127.0.0.1:<port>` URL without userinfo, whitespace,
backslashes, aliases or ambiguous host syntax. Invalid requests refuse before
filesystem state access or process start. It also requires a supplied Job,
callable verifier gate and tries=1, preserving existing birth, gate, cleanup
and retained-ownership flow.

Disposable launch switches request suppression of background networking,
component updates, domain-reliability reporting and QUIC; resolver rules map
other names to failure, excluding literal 127.0.0.1 used by copy/CDP. The exact
switch list is saved in the launch manifest. No proxy, preference file,
machine setting, external hostname exception or security bypass switch was
added. This is not an OS network boundary. Installed Edge may ignore Chromium
switches, use literal IPs, cached addresses, brokers or other paths; no native
behavior is certified here.

Paint still supplies allow_remote=[] and allow_loopback=True to the same
production verifier; reports now include that policy. Gates, sampling,
freshness, outside-profile exclusion, Guard and cleanup remain unchanged.
Remote traffic or unknown observation still refuses. No required external
destination has been identified or proposed.

Only sandbox_window.py open_edge plus the new pure switch helper,
paint/paint.py and paint/test_paint.py change in this increment. Mail's
Win32/start/_start_locked hunks are untouched, per c11026. No whole-file
replacement or source/runtime admission is proposed.

## Ran

Pinned Python:

    -m pytest src/desktop/paint/test_paint.py src/text-desk/notation/test_house_paint.py -q -k "not test_the_token_is_read" -p no:cacheprovider

Printed **24 passed, 1 deselected, 25 subtests passed in 0.34s**.
The deselected existing token test reads real host metadata; this round
deliberately used offline mocks, not a fresh native observation.
No browser, socket, desktop, process or Guard query was made by these tests.
The production verifier uses its existing fake kernel and owned fixture
folders, not host network tables.

Coverage: exact ordinary argv parity after removal of only the five opt-in
switches; invalid remote/ambiguous URLs and missing Job/gate/single attempt
refuse before effects; refused gate closes once without CDP/retry; actual
paint dispatch requests local mode and retains remote-empty policy. Fake
IPv4/IPv6 background and redirected/frame traffic is violation, unreadable
sockets and unobservable UDP are unknown, observed loopback remains allowed.
These are observation/refusal tests, not request interception or DNS isolation.

Development iterations: argv equality first compared different MagicMock
profile object identities; deterministic fixture profile fixed the harness.
The new runner test expected exception prose, but receipts intentionally
redact it; it now checks RuntimeError type, gate refusal and stage. Initial
pytest cache creation produced WinError5 and two denied cache paths; retained
untouched, no cleanup retry. Later runs used no cache provider.

`git diff --check` exit0. No broad health or native suites rerun. Exact
production/test hashes: NETWORK-HASHES.json; HEAD-relative patch NETWORK.patch.

## Read external primary sources

- https://github.com/chromium/chromium/blob/main/chrome/common/chrome_switches.h
- https://github.com/GoogleChrome/chrome-launcher/blob/main/docs/chrome-flags-for-tools.md
- https://chromium.googlesource.com/website/+/refs/heads/main/site/developers/design-documents/network-stack/socks-proxy/index.md

The first two document Chromium switches and background services; the third
documents catch-all resolver failure with exclusions. These establish
documented intent, not installed Edge behavior. No private project contents
were sent in searches. Two initial googlesource code-page opens failed.

## Next decision and reversal

JEFF reviews this offline increment and owns any separate bounded native
authorization through supported runtime/house handoff. A new run still needs
current runtime, source, Guard, profile visibility, ownership, network and
cleanup evidence separately. Board shots at both sizes, crops/delivery,
actual viewport/DPR and reliable startup remain unproved.

Reverse NETWORK.patch after drift review to undo only this increment.
The original fail-closed local-only verifier policy stays. Reversal grants
no retry authority. No world migration or runtime setting must be undone.
