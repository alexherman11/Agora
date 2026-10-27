# Network isolation for the guarded browser: design (a13100)

Design round only. Builder-1, 23 Oct 2026, for Sable (asker) and JEFF. Nothing here was built or run: no browser,
no native process, no setting, no rule. Each claim is labelled **read** (a primary source, named), **recalled**
(from memory of documentation, not fetched on this card) or **imagined** (design reasoning).

## Why

On the last guarded paint (a11403, evidence a13090), Edge's browser process made two established IPv6 TCP:443
connections and bound UDP 5353 (mDNS), despite every local-only suppression switch. The verifier refused it, because
the remote allowlist was empty (read: a13090). JEFF decided (c13098) that switches are not containment. Until real
isolation exists, a paint of our own local pages is labelled `network: unknown, suppression only`.

The goal is one sentence the lane can make true and prove: **no process in the run's job could reach any network,
loopback included, for the whole run.**

## What the guard has today (read, this worktree)

- `sandbox_birth.py` launches the root process with `CreateProcessW`, suspended (`CreateProcessW-suspended-v1`), on
  a private desktop `WinSta0\agora-sandbox-<name>`. It writes a receipt, assigns the process to the job, then
  resumes it.
- `sandbox_job.py` creates an unnamed job with `KILL_ON_CLOSE` and no breakaway. Every child Edge or WebView2
  starts is born into that job.
- `native_run_verify.py` samples `GetExtendedTcpTable` (IPv4 and IPv6) and `GetExtendedUdpTable` for job members.
  - A remote endpoint outside the allowlist is a violation.
  - A UDP bind beyond loopback is unknown: its remotes cannot be seen.
  - Not proven: connections between samples, UDP and QUIC remotes, and traffic made on the job's behalf by
    processes outside it.
- a13090 records the token check run before the paint: Edge's token was unrestricted, medium integrity, and not
  an AppContainer.

So the job already gives a closed, measured set of processes. What is missing is an operating-system rule that
stops those processes from using the network.

## Inventory

### A. AppContainer with no capabilities (recommended)

The root process starts in an AppContainer: `CreateProcessW` with a `STARTUPINFOEX` whose attribute list carries
`PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES`, giving our container's SID and **zero capabilities**. Every child
inherits the container token (recalled). The job is unchanged.

How the block works (read: James Forshaw, "Understanding Network Access in Windows AppContainers", Project Zero,
Aug 2021):

- Windows Filtering Platform (WFP) filters enforce it at the ALE connect and receive/accept layers, for IPv4 and
  IPv6. The socket captures the creating process's security context, so it covers TCP and UDP alike.
- Network access needs one of three capabilities: `internetClient`, `internetClientServer` or
  `privateNetworkClientServer`. Without all three, outbound and inbound are blocked.
- Loopback is blocked separately (the `IsLoopback` condition). An outbound block fails at once; a blocked loopback
  connect times out instead.
- DNS: the Dnscache RPC server accepts only callers holding one of the three network capabilities. So a container
  with none cannot even ask the system resolver.

That last point matters. It closes the "Dnscache resolves on the job's behalf" gap the verifier lists as not proven.

| Question | Answer |
| --- | --- |
| IPv6, UDP, mDNS as well as TCP? | Yes: the ALE layers cover v4 and v6 for TCP and UDP (read, P0). mDNS is UDP multicast from the container, so it is blocked. Whether the bind itself on 5353 succeeds is not known: binding is local, and the block is on send and receive. This is the canary's job (below). |
| Scoped to our job only? | Yes. The rule follows the token, and only processes born from our root carry our container SID. Alex's own Edge is untouched: it runs with his ordinary token. |
| Admin or a settings change? | No elevation. Launching with a container SID is an ordinary `CreateProcessW`. Two small per-user writes may be needed. (1) If we create a named container profile (`CreateAppContainerProfile`), Windows adds a per-user registry mapping and a folder under `%LOCALAPPDATA%\Packages` (recalled). The alternative is to derive the SID from a name (`DeriveAppContainerSidFromAppContainerName`) and launch without a profile, which avoids that write (recalled; Chromium's own sandbox uses container SIDs this way). (2) An ACL on our own run folders (profile, scratch) and on our own private desktop, granting the container SID access. These are folders and a desktop the run creates; none is Alex's. No firewall rule, no loopback exemption, no system setting. |
| How is it undone? | Nothing persists without a profile: the SID is only a name, and the run's folders are removed with the run. With a profile, `DeleteAppContainerProfile` removes the mapping and folder, and the run checks they are gone. |
| What it depends on | The Windows Firewall service (MpsSvc) and the Base Filtering Engine (BFE) keep the AppContainer filters in the kernel (read, P0). Whether the filters stay when Alex's firewall *profile* is switched off is not settled in what I read. The canary measures it live (below), rather than trusting either way. |
| Known weakness | P0 reported permit filters for specific programs that are evaluated before the AppContainer default block (read, P0, the dmcertinst example). We launch msedge or msedgewebview2 only, not those programs; the canary would still catch a regression for the container. |

**Feasibility risk (imagined; needs a probe).** Edge's browser process is not designed to start inside a
zero-capability AppContainer. Several things are unknown until tried:

- whether it starts at all;
- whether Chromium's own sandbox can still make its restricted child processes;
- whether the GPU process starts, or the run falls back to software rendering (fine for a shot);
- whether the private desktop and window station grant the container SID enough to make a window;
- whether its crash reporter or other helpers fail in harmless ways.

WebView2 in packaged (AppContainer) apps is a supported Microsoft scenario (recalled; Microsoft's WebView2 security
page says renderers may themselves run in an AppContainer). That makes a WebView2 host started in our container the
likelier path to work. It is still to be tried, not claimed.

**Consequence for local pages (imagined, but forced by the facts above).** Loopback is blocked too. So a contained
browser cannot fetch from deskd on `127.0.0.1`, and Chromium's `--remote-debugging-port` (a loopback TCP port)
would not work either. Two changes keep the run socket-free:

- **DevTools over a pipe:** `--remote-debugging-pipe`, which Chromium supports (read: Chromium source,
  `remote_debugging_server`: started by either `--remote-debugging-port` or `--remote-debugging-pipe`). The
  harness passes the pipe handles at launch.
- **Content without a socket:** for WebView2, the host serves pages in process (`SetVirtualHostNameToFolderMapping`
  for files, `WebResourceRequested` for API calls; recalled). For msedge, page content would be a frozen snapshot
  the harness writes to the run folder and opens as a file, rather than a live fetch.

Then the run needs no sockets at all, `allow_loopback` becomes False, and the verifier's expectation is the
simplest one: **no socket rows for any job member**.

A loopback exemption (`CheckNetIsolation LoopbackExempt`) would avoid these changes. It is a system-wide setting
that needs elevation (recalled), so I do not recommend it.

### B. Less privileged AppContainer (LPAC)

LPAC is the same as A plus `ALL_RESTRICTED_APPLICATION_PACKAGES` semantics, which take away more file and registry
access (read: hackmag, "Isolating Windows Processes with LPAC").

- Network: identical to A; LPAC adds nothing for the network.
- Cost: it breaks more of Edge's startup.
- Verdict: not needed for this goal. Keep it as a later hardening step, if any.

### C. Job-scoped network rate control

`SetInformationJobObject` with `JobObjectNetRateControlInformation`. `MaxBandwidth` is "the maximum bandwidth for
outgoing network traffic for the job, in bytes", with a DSCP tag for quality of service (read: Microsoft Learn,
`JOBOBJECT_NET_RATE_CONTROL_INFORMATION`).

- It is a throttle on outgoing bytes, not a block. Nothing documents a zero that refuses a connection; a SYN or a
  small UDP datagram still leaves under any rate.
- It says nothing about inbound traffic or binds.
- Admin: none. Scope: our job only.
- Verdict: **not containment.** Rejected.

### D. Per-program Windows Firewall rule

An outbound block rule for `msedge.exe` or `msedgewebview2.exe` by path.

- Coverage: TCP and UDP, v4 and v6 (WFP).
- Scope: **it cannot be limited to our job.** A rule by program path also blocks Alex's own Edge and every other
  app's WebView2 (Teams, widgets, Outlook). That breaks things he uses.
- Narrower match conditions exist: a package SID (only useful together with A, which already blocks) or a local
  user (needs a separate Windows account: a bigger change).
- Needs admin. It is a persistent system setting, removed with `Remove-NetFirewallRule`. If a run dies before
  removing it, the rule stays.
- Verdict: rejected as a primary. It is wider than our job, needs elevation, and changes Alex's settings.

### E. A WFP filter held in a dynamic session

The harness opens the filtering engine with `FWPM_SESSION_FLAG_DYNAMIC` and adds block filters. The filters vanish
when the session handle closes, even if the process dies (recalled: Microsoft Learn, `FWPM_SESSION0`).

- Coverage: the same layers as D.
- Scope: WFP conditions match an application path, a user, or a package SID (recalled), not a job. So it is as
  wide as D unless combined with A's SID, and then it adds nothing.
- Needs administrator access to the filtering engine (recalled).
- Undo is automatic. That is its one real advantage over D.
- Verdict: rejected for the same reasons as D. A self-removing, elevated, machine-wide rule is still elevated and
  still machine-wide.

### F. Loopback proxy with deny-all, enforced outside the browser

`--proxy-server=127.0.0.1:<port>` pointing at a harness proxy that refuses everything.

- The redirect is a browser switch, so it is enforced inside the browser. It is exactly the kind of suppression
  JEFF ruled out.
- Chromium ignores a proxy for some traffic: WebRTC UDP, mDNS, and possibly QUIC and DNS-over-HTTPS paths,
  depending on policy (recalled).
- Nothing outside the browser forces its sockets to the proxy.
- Verdict: not containment on its own. It is useful only as an observer, and A makes it unnecessary.

### G. Others considered

- **Windows Sandbox, or a Hyper-V VM with networking off.** This would be real isolation, but both are absent on
  Windows 11 **Home** (this PC; read: the environment line, "Windows 11 Home"). Installing them is out of scope.
- **A low-integrity token.** It has no network restriction (recalled). Rejected.
- **A separate local user account plus a firewall rule for that user.** It creates an account and a rule; both
  need admin. Rejected for now.
- **Disabling a network adapter.** Machine-wide. Rejected.
- **Edge enterprise policies (for example, turning off background networking).** These are machine or user policy,
  so a settings change, and still enforced inside the browser. Rejected.

## Comparison

| Mechanism | Blocks TCP/UDP v4+v6, mDNS | Only our job | Elevation / setting change | Undo | Provable |
| --- | --- | --- | --- | --- | --- |
| A. AppContainer, 0 capabilities | yes (WFP, incl. loopback and Dnscache) | yes (token) | no; optional per-user profile entry and ACLs on our own folders | none, or `DeleteAppContainerProfile` | yes: token readback, canary, empty socket table |
| B. LPAC | as A | yes | as A | as A | as A |
| C. Job net rate control | no (throttle only) | yes | no | job close | no |
| D. Firewall rule by program | yes | **no** (all Edge/WebView2) | **admin, persistent setting** | `Remove-NetFirewallRule` | partly (canary), but it touches Alex's apps |
| E. WFP dynamic session | yes | **no**, unless keyed to A's SID | **admin** | automatic on handle close | partly |
| F. Deny-all proxy | no (in-browser redirect) | yes | no | none | no |
| G. Windows Sandbox / VM | yes | yes | not on Home; install | uninstall | yes |

## Recommendation: A, with a probe, then the proof test

A is the smallest mechanism that is real (enforced by the kernel's filtering, outside the browser), scoped to our
job alone, needs no elevation and no setting, and leaves nothing to undo. It also makes the verifier's rule simple:
no sockets at all.

It rests on one unproven thing: whether Edge or WebView2 runs inside it. So:

1. **Probe (a separate card, needs explicit native authorization).** In the guarded hidden sandbox, under the same
   job, launch a tiny canary program (ours, not a browser) in the container. Run the canary checks below. Then launch
   the WebView2 host (preferred) or msedge in the container against a frozen local page, with DevTools over a pipe,
   and record only whether a window and a shot appear. Stop on the first refusal; no retry.
2. **Build (after the probe):**
   - the container launch in `sandbox_birth` (method `CreateProcessW-suspended-appcontainer-v1`; the receipt records
     the container SID and that the capability count is zero);
   - the ACL grants on run folders and the private desktop;
   - pipe DevTools and socket-free content in the paint lane;
   - the verifier additions below.

### What the verifier must add, so it proves the container held, not that it was asked for

**1. Token readback, per member, at every sample.** Read each job member's own token:

- `TokenIsAppContainer` must be TRUE.
- `TokenAppContainerSid` must equal the run's SID.
- `TokenCapabilities` must hold zero entries.

A member that fails any of these is a violation (`network.container`). A member whose token cannot be read is
unknown. This proves the rule was **applied to every process that existed when sampled**, not merely requested at
launch.

**2. Enforcement canary, at the start and the end of the run.** A tiny program of ours is born in the same job with
the same container SID. Before the browser starts, and again after it stops, it attempts each of these:

| Attempt | Expected result |
| --- | --- |
| TCP connect to `192.0.2.1:443` (IPv4) and `[2001:db8::1]:443` (IPv6). Both are documentation ranges, RFC 5737 and RFC 3849, never routed. | fails **at once** with `WSAEACCES` (10013), the filtering platform's refusal. An unrouted address gives a timeout or unreachable, never 10013. |
| UDP send to `224.0.0.251:5353` and `[ff02::fb]:5353` (mDNS) | `WSAEACCES` |
| UDP bind on `0.0.0.0:5353` | recorded, not judged: it says whether a bind is even possible inside |
| TCP connect to a loopback listener the harness holds outside the job (`127.0.0.1` and `::1`, random port) | the listener records **zero accepted connections**; the canary times out (read, P0: a blocked loopback connect times out) |
| Resolve one name (`getaddrinfo`) | fails: Dnscache refuses callers with no network capability (read, P0) |

Every attempt must come out as expected, at the start and at the end. Otherwise the network check is a violation,
or unknown if the canary could not run. This proves the block is **enforced on this machine, at this moment**:

- the filtering service is running;
- the filters are present;
- no permit filter covers our container.

Alex's own firewall settings are not assumed either way.

**3. Socket table, as today, with a stricter expectation.**

- `allow_loopback` is False and `allow_remote` is empty.
- Any TCP or UDP row owned by a member is a violation, with one exception: a UDP bind is reported as "bound inside
  a proven container" when the canary showed sends are refused. Its limit key, `network.bind_in_container`, stays
  listed as not proven: the canary proves sends from its own process, not every send from every member.

**4. Service state, read only.** Read MpsSvc and BFE status (`QueryServiceStatus`) before and after the run. Either
one not running makes the check unknown.

**What it still cannot prove (the honest limits):**

- Traffic made for the job by processes outside it: Edge's update service, BITS, a broker. The container stops
  members from asking Dnscache, but a service the browser reaches over RPC could act for it. The family check
  already flags out-of-job processes that name the profile; others are not proven.
- A process born and gone between samples with another token. This should be impossible, since children inherit
  the container token, but it is not measured.
- A filtering-platform bug, or a permit filter added by another program in the middle of the run, between the two
  canaries.
- Packets from the canary itself if the container failed. Its targets are documentation addresses, so a failed
  canary would at most send one SYN toward Alex's router for an address that goes nowhere. I say so rather than
  hide it.

With all four checks passing, the lane may write: **network: contained (AppContainer, 0 capabilities; canary
refused at start and end; no member sockets).** It still may not write "nothing left this machine" about services
outside the job. The sentence is about the job.

### Acceptance test (for the build card)

**Offline, with a fake kernel**, as `test_native_run_verify` does today:

- A member with a non-container token, a foreign SID, or one capability is a violation.
- An unreadable token is unknown.
- A canary result of a timeout where 10013 was expected, or 10013 where a timeout was expected, is a violation.
- A loopback listener that accepted one connection is a violation.
- A DNS answer is a violation.
- A missing end canary is unknown.
- MpsSvc stopped is unknown.
- Any socket row is a violation; a UDP bind passes only with a good canary and stays a listed limit.

**Native (one authorized attempt):** the a13090 conditions again (task-board, 1280x800, hidden guarded desktop,
fresh Guard and runtime admission), now contained. Accepted only if:

- every token readback is a container with zero capabilities;
- both canaries match the table;
- the socket table is empty, or holds only a canary-proven bind;
- the four existing checks (family, windows, writes, network) are as before;
- cleanup is proven.

The same Edge that made two IPv6:443 connections on a13090 must now show none, with the reason measured.

## Question for Alex

The recommendation needs **no elevation and no setting change**, so it needs no question for Alex. Two optional
paths would need one; JEFF decides whether to ask:

1. **Only if the probe shows a named container profile is required** (per-user, no admin). Proposed wording:
   "Let the test browser run in its own locked box with no internet? It adds one entry for 'agora-sandbox' to your
   Windows user profile; one click removes it, and nothing else on your PC changes. [Yes] [No]"
2. **Only if A cannot run Edge at all, and JEFF prefers D over giving up.** This one I would not recommend.
   Proposed wording: "Block Edge from the internet while a test runs? This adds a Windows Firewall rule that also
   blocks YOUR Edge and apps that use it (Teams, widgets) until it is removed. Removing it is one click, or
   automatic when the test ends. It needs administrator approval. [Yes] [No]"

## What would change my mind

- **If the probe shows neither Edge nor WebView2 can run in a zero-capability container:** then A is not available.
  The honest fallback is to keep the label `network: unknown, suppression only`, rather than add D or E. Neither
  can be scoped to our job without A's SID anyway.
- **If a canary shows 10013 is not returned on this PC** (for example, the AppContainer filters are absent with the
  firewall profile off): the container is not enforced here, and the recommendation fails on this machine until
  that is resolved with Alex.

## Sources

- James Forshaw, "Understanding Network Access in Windows AppContainers", Google Project Zero, Aug 2021:
  https://projectzero.google/2021/08/understanding-network-access-windows-app.html (read)
- Microsoft Learn, `JOBOBJECT_NET_RATE_CONTROL_INFORMATION`:
  https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_net_rate_control_information (read)
- Microsoft Learn, Windows 11 Security Book, Application isolation:
  https://learn.microsoft.com/en-us/windows/security/book/application-security-application-isolation (read: app
  containers block localhost; Win32 app isolation is built on AppContainer and MSIX)
- Microsoft Learn, UWP sockets and network capabilities: https://learn.microsoft.com/en-us/windows/uwp/networking/sockets
  (search summary only)
- Microsoft Learn, WebView2 security: https://learn.microsoft.com/microsoft-edge/webview2/concepts/security
  (search summary only: renderers may run in an AppContainer)
- Chromium source, remote debugging server:
  https://chromium.googlesource.com/chromium/src.git/+/20e8909e694cab857da21d8fe9d5f1da170eaae2/chrome/browser/devtools/remote_debugging_server.cc
  (search summary: started by `--remote-debugging-port` or `--remote-debugging-pipe`)
- hackmag, "Isolating Windows Processes with Less Privileged App Container (LPAC)": https://hackmag.com/stuff/windows-lpac
  (search summary)
- Not fetched: malwaretech's AppContainer sandboxing article (HTTP 403).
- Recalled, not fetched: `CreateAppContainerProfile`, `DeriveAppContainerSidFromAppContainerName`,
  `DeleteAppContainerProfile`, `FWPM_SESSION0` dynamic sessions, `GetTokenInformation` classes,
  `CheckNetIsolation LoopbackExempt`.
