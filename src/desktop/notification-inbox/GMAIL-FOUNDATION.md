# Gmail foundation and Google Messages — disabled, 20 October 2026

For Alex: Gmail can become a quiet headers-only connection after the private
reader is isolated and reviewed. One **Connect Gmail** button can start the
guided consent journey then; it cannot work safely today. Google Messages
remains **Not connected**. Its supported web app is a separate human destination,
not a verified inbox API. Nothing was connected or paired here.

## Review before implementation

Architecture review was posted on the commission at event e14468 before source
implementation. Read: the existing inbox proposal, notify.py, host_route_parent.py
and repository listener searches. Existing toast history concerns Agora's own
sender identity, not all apps' notifications. The host-route module explicitly
has no deployed private storage/channel; parent provenance does not isolate mail.
Public Desk actor claims and world props are not authorization.

This change supplies `gmail_fake.py`, an offline protocol reference restricted
to a scripted exchange, and tests. There is no HTTP implementation, OAuth
listener, token file, secret input, preview UI, host wiring or enable option.
`live_request` always reports disabled, including for claimed Alex/JEFF callers.
The fake's Python fields, guard arguments and object checks are NOT security.
No real account data may be put into this harness.

### Concrete deployment prerequisites, not implemented

The maintainer must first establish a reader security principal/container whose
memory, storage and IPC are inaccessible to builder and model processes,
including unsandboxed processes running as Alex. Same-user DPAPI, an ignored
directory or a bearer secret readable by that user does not establish this.
This card cannot establish such a boundary without a separately reviewed
deployment/security change, which is outside its authorization.

Review the host-private human UI as a separate trusted client, with verified
process identity and a private authenticated channel to that reader. Workers,
remote pages, public HTTP/headerless localhost clients, world verbs and model
output must have no account-read or grant endpoint. Do not give JEFF mail-reading
authority by recognizing his name. Connection consent originates in the human UI
and binds the intended connection and scope; queued requests are cancelled on
disconnect/session replacement. Replay and cross-session requests must fail.

Only after those reviews: add a narrow HTTP adapter in that isolated reader;
allow Google authorization/token/revocation and Gmail metadata endpoints with
TLS checks, response limits, timeouts and no redirects to arbitrary origins.
Bind an ephemeral exclusive loopback socket *before* opening the system browser.
Use its actual port, exact callback path/host, expiring one-use state and PKCE
S256. Never log callbacks, headers, token responses or provider error bodies.
PKCE prevents code interception from becoming token access; it does not
authenticate a local application that asks to read accounts.

Token/cache encryption and retention live inside that boundary, with crash-safe
disconnect/revocation receipts. Private UI renders headers as plain untrusted
text, never HTML, commands or model instructions; no external images. It gets
no arbitrary tool/host capability. Counts leave through a fixed schema-only
publisher, with no content events/model wakes. A later real IPC/storage review
must include cross-principal, forged-peer, replay, crash and filesystem tests.
The fake tests here cannot replace those.

## Exact phase-one protocol

Request only `https://www.googleapis.com/auth/gmail.metadata`. No identity,
readonly/body, modify or send scope. Google classifies metadata as restricted.
Publishing requires review of verification obligations; server storage or
transmission can require a security assessment. A maintainer must assess any
applicable exception rather than promise automatic approval.
[Scope documentation](https://developers.google.com/workspace/gmail/api/auth/scopes).

Use `users.messages.list(userId=me, labelIds=[INBOX])`, bounded pages, then
`users.messages.get(format=metadata, metadataHeaders=[From,Subject,Date])`.
Retain only those headers, internal date and the Inbox/Unread label state.
Unread comes from `UNREAD`; a message leaving Inbox drops from a complete
snapshot. No `q` parameter: the metadata scope forbids it.
[List](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/list),
[get](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/get).

The reference stages a complete Inbox snapshot before committing it. A failed
page leaves the previous count marked delayed, not falsely empty. It stops after
100 pages; large mailboxes need a later reviewed continuation/delta strategy.
Repeated identities update once; local dismiss survives a refresh, Undo restores
it, and neither changes remote unread. Disconnect purges items and dismissals;
reconnect starts fresh, with no resurrection of cached headers. A future durable
dedupe design must specify retention separately.

The fake models a 300-second OAuth attempt, duplicate-parameter/host/path/state
rejection and consume-before-exchange. Expiry refresh uses the refresh token;
scope expansion or invalid tokens fail closed. Permission loss clears private
state and needs explicit reconnect, not an automatic browser prompt. Transient
errors back off; 403 rate-limit reasons differ from permission denial.
Disconnect stops local reads immediately; a failed/offline revocation remains
visibly pending, not falsely revoked.
[Desktop OAuth, PKCE and revocation](https://developers.google.com/identity/protocols/oauth2/native-app).

## Guided setup and reversal, for JEFF

Maintainer prerequisites: reviewed isolation and UI/IPC; Gmail-enabled project;
desktop OAuth registration and allowed consent/test-user configuration; reviewed
publishing/verification; app registration provisioned privately without chat.
None was created or inspected here.

Future human journey:

1. **Connections → Connect Gmail** opens “Headers only: sender, subject, date and
   unread status. No body, sending or mailbox changes.” Continue is disabled with
   the concrete missing prerequisite while deployment is incomplete.
2. Once prepared and authorized, Continue opens Google's system-browser account
   choice, sign-in/MFA and consent. Agora never asks for passwords or pasted codes.
3. The private callback returns **Connected · Headers only**; the world gets only
   counts/status. Private previews remain unavailable until their separate review.

One click starts the journey; Google consent and MFA cannot be removed. External
OAuth clients in Testing receive seven-day refresh tokens for these scopes, so
Testing is not a durable unattended connection. Production tokens can also be
revoked/expire; show Reconnect, never silently broaden access.
[Refresh-token expiration](https://developers.google.com/identity/protocols/oauth2#expiration).

Pause stops work. Disconnect clears private display/cache immediately and requests
provider revocation only under a permitted awake/no-game guard; failure says
“Disconnected here · Google access removal pending.” Offer Google's account
permissions UI through an explicit human action. No automatic sign-out or device
unpair. Reversal today: retain disabled status; house can revert these standalone
files without changing world inbox content or current runtime.

## Exact world contract for JEFF to stage

No active lens, connection object or grant was changed. Reuse world notes/lenses
for internal notices; external mail rows do not go into the shared world.

| Field | Allowed value/meaning |
| --- | --- |
| schema, source | `1`, `gmail` |
| state | `disabled`, `disconnected`, `connecting`, `connected`, `delayed`, `permission-lost` |
| unread_count | Nonnegative integer or null; remote unread within Inbox, including locally dismissed |
| visible_count | Nonnegative integer or null; local non-dismissed Inbox items |
| last_sync | Last complete snapshot epoch or null; stale counts labelled delayed |
| retry_at | Next permitted attempt epoch or null; not a wake timer |
| revocation | `none` or `pending`; none does not prove global sign-out |
| permissions, previews | `headers-only`, `unavailable` |

The constant disabled refusal can additionally give a fixed non-provider reason.
No account address, account label, item/thread ID, subject, sender, cursor,
callback URL, provider error string or token is permitted. No private item links
in shared lenses: only named **Connections** / **Gmail inbox** human actions.
Do not let editing these fields control or authenticate the reader.
Until deployment, stage `state=disabled`, both counts null, timestamps null.
The fake connected projection is fixture output, not evidence of connection.

An existing awake host pass could eventually schedule bounded sync; it must first
observe awake, unlocked and game-clear from trusted host state. Unknown, asleep,
locked or gaming does no fetch, refresh, consent, revoke or notification work.
Local disconnect may still purge immediately. No wake timers, services, push
subscription, power-policy changes or per-message model turns are introduced.

## Google Messages: supported primitives, not a deployed route

Google documents Messages for web with account/device pairing and a browser
unread indicator. It does not document an inbox ingestion API on that page.
Inference: it is a valid later **Open Messages** destination with explicit consent,
not evidence Agora can ingest SMS/RCS or history. No UI scraping/session import.
[Google's setup and unpair instructions](https://support.google.com/messages/answer/7611075?hl=en).

Two possible future notification-only bridges:

- **Android companion:** Android's `NotificationListenerService` is a supported
  primitive for posted/removed notifications. It requires a separately built,
  reviewed companion, user-enabled notification access, an app allowlist and
  authenticated encrypted device pairing to an isolated PC receiver. It observes
  notifications, not the Google Messages database or guaranteed conversation
  history. Redaction/disabled notifications can withhold content; no notification
  removal or reply action should be forwarded.
  [Android API](https://developer.android.com/reference/android/service/notification/NotificationListenerService).
- **Windows listener:** `UserNotificationListener` requires a manifest capability
  and human access request from a UI thread. It could observe consented mirrored
  toasts only if a later test proves Google Messages reaches that notification
  stream. A per-app filter narrows retention, not the OS-wide grant. Phone Link
  has not been established as a supported Agora integration endpoint.
  [Windows API](https://learn.microsoft.com/en-us/windows/apps/develop/notifications/app-notifications/notification-listener).

Recommend **Unavailable pending bridge review**, not another pairing request now.
Future guided setup must separately explain the broad notification permission,
obtain install/pairing/OS-consent authorization, let Alex select Google Messages,
and verify one explicitly consented notification before claiming connection.
Never silently install a companion, enable access, change battery settings or
read Phone Link databases. Disconnect Agora forwarding separately from device
unpair/OS permission removal; show each remaining permission truthfully.

## Evidence and limits

Ran: 17 fake tests; no socket/server/account API, profile read, device enumeration,
notification access request, browser consent, install or host restart. Read-only
capability check: pinned Python has no `winrt` projection; Windows.UI.winmd and
Windows.Foundation.winmd exist. No listener implementation/manifest found in
searched repository Python/C#/XML/appxmanifest files. These checks do not prove a
listener is usable/authorized or establish what is installed on the phone.

Ran versus read source references are above. Imagined: isolated deployment,
future UI/IPC and companion bridge. Real connection, token lifecycle, preview
UI isolation and guarded screenshots are **not run here**; require separate
review/consent and a browser-capable run. No whole-system/privacy guarantee.
