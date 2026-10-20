# Notification inbox — proposal, not connected

20 Oct 2026 · worker-a7227 · for JEFF to take to Alex. All examples are invented.
No connector is enabled, implemented or account-tested by this commission.

## For Alex

Make the bell one quiet inbox: things that need you first, everything else below.
Click a named item to open its source; dismissing it only tidies Agora.
Start with existing Agora notices, then connect email read-only.
Phone messages need a separate permission and device-specific setup.
Email and Phone stay visibly **Not connected** until their own consent succeeds.

One question for JEFF to route: **Which email service, and Android or iPhone with which messaging app?**

## One inbox, existing world shape

Keep the top-right bell: unread count and one short “needs you” line, no private
preview by default. Clicking opens a bounded Notifications panel, not a growing
popover. Light theme, clickable names, All / Needs you / Dismissed filters,
Connections button; pagination and “Next page” keep content within the panel.
No whole-HUD scrolling, animation, sound or new toast by default.
No auto-open or focus changes.

Reuse ordinary notes and props on an inbox surface, rendered by world lenses.
JEFF can stage this shape without changing the active home-notices lens.
Do not give external fixtures role=notice: today's lens treats every non-landed
notice as asking Alex and removes notices on open. Those rules cannot express
external read state or permissions. Adapt existing internal notices through a
world lens; do not duplicate the same event into the toast chat.

Each inbox record has:

| Field | Meaning |
| --- | --- |
| source, connection | Provider and opaque local account handle; display a chosen account label |
| source_key, revision | Stable provider item identity and change token; private for external items |
| sender, summary, time | Display name, supplied subject or permission-limited excerpt, source timestamp |
| local_state | new / seen / dismissed; separate from provider state |
| provider_unread | true / false / unknown, with observed_at; never inferred from local dismissal |
| action_state | needs-you / informational / resolved / unknown; mail defaults informational |
| priority | quiet by default; only Alex's explicit source rules promote it |
| target | Typed internal reference or opaque provider-open handle, not executable text |
| sync_state | current / delayed / disconnected / permission-lost, with last successful sync |

Summary means subject/excerpt, not an agent-generated reading of messages.
Display missing fields as unavailable. Do not call an unseen message “read.”

Upsert by (connection, source_key); revision updates the same record. Dismissal
survives replay and reconnect; a genuinely new message has a new key. Thread
grouping is presentation, not loss of individual identities. Never merge phone
and email just because sender, words or timestamps look alike. If the same email
also arrives as a Windows toast without a provable identity, suppress that
mirrored app when its direct connector is selected.

Opening marks only Agora's item seen, and only after an explicit press.
“Dismiss in Agora” hides locally; Undo restores it. Neither changes the provider.
“Mark read in email” is absent in phase one: it would need a new write scope and
separate action consent. Opening the provider app may itself mark read according
to that app; say this in the Open action's description. Do not automate it.
Keep the original genuine document/reply links for internal notices.
Provider URLs must be allowlisted HTTPS links; never run incoming notification
commands or replay toast action arguments. Fall back to the named app/inbox
when there is no supported item link, visibly “Open inbox,” not “Open message.”

## Connection flows and prerequisites

These are future button journeys, not working buttons today. “One click” starts
the guided flow; provider sign-in, MFA and consent remain the user's own steps.
The maintainer prepares registration and callbacks; Alex is never given shell
commands or asked to paste credentials into chat.

| Choice | Exact proposed journey | What must exist first |
| --- | --- | --- |
| Outlook / Microsoft 365 | Connections → Connect Outlook → permission sheet → Continue → Microsoft account chooser/sign-in/consent → return showing account label, Basic mail, last sync, Disconnect | Reviewed native public-client registration with correct personal/tenant audience and loopback redirect; auth-code PKCE. Delegated Mail.ReadBasic plus offline_access for background refresh. Organization policy may require admin approval: show Pending, never bypass it. |
| Gmail / Workspace | Connections → Connect Gmail → permission sheet → Continue → Google's browser chooser/sign-in/consent → return showing Headers only, last sync, Disconnect | Gmail-enabled Cloud project, desktop OAuth client, consent configuration and appropriate publishing/verification arrangement; PKCE and loopback. gmail.metadata gives labels/headers, not bodies: show sender/subject, no body preview. |
| Android phone messages | Connections → Phone → Android → explain supported channel → Open Phone Link setup if not already paired → user follows pairing/phone permission prompts → separately consent to Agora's Windows notification access → choose mirrored apps → preview test with invented content | Compatible phone/PC and consented Phone Link pairing, plus a reviewed packaged notification-listener bridge. Must prove the desired app actually emits accessible Windows notifications. Until then label Experimental / unavailable; not message-history sync. |
| iPhone messages | Connections → Phone → iPhone → explain limitations → user follows Phone Link Bluetooth pairing and phone notification/message permissions → separate Agora listener consent → choose Phone Link → explicit later acceptance test | Compatible PC Bluetooth/phone and the same bridge. No promise of complete iMessage/SMS history or arbitrary app coverage. iPhone/PC connection limits what Phone Link sees. If toast forwarding fails, offer Open Phone Link only. |
| iCloud Mail / another provider | Connections → provider information → Unsupported for now / Open provider website after an explicit press | Apple's documented manual IMAP path needs an app-specific password; not this password-free connection design. Other services need their own reviewed OAuth/API route. Never scrape an existing mail/browser profile or silently fall back to passwords. |

Microsoft basic-mail consent excludes body/preview/attachments and has no send
permission. Gmail metadata remains a restricted scope, not a trivial approval:
verification obligations depend on deployment; external Testing tokens expire
after seven days. Do not sell a testing client as a permanent connection.
Use label IDs for Inbox/Unread filtering: Gmail metadata cannot use the q search
parameter. Broader preview/body access is a later, separately explained choice.

Windows listener consent covers other apps' notifications at OS level; a local
app allowlist narrows what Agora retains but does NOT narrow that OS grant.
This is a wider permission than connecting a specific mailbox. Recheck access
on every read, distinguish denied/disconnected from “nothing new,” and do not
retry consent silently. Phone Link is a user app, not a verified Agora API:
the reviewed documentation does not establish a supported integration endpoint.
Do not read its databases, UI-scrape messages, or use Android debugging tools.

## Privacy and operation boundary

Connections default disabled. A world property saying “connected” grants nothing.
The future connector must verify its own scoped consent and authenticated caller;
workers/world scripts must not be able to turn account access on with a prop edit.
No send, reply, delete, remote dismissal or mark-read endpoint in phase one.

External sender/subject/IDs can be private too. Keep them, sync cursors and OAuth
tokens outside the shared world, git, exports, transcripts and model prompts.
Project only counts/status by default; explicit “show private previews” needs a
reviewed host-private UI path. World's ordinary notes have no demonstrated
account privacy boundary: real external summaries must not be stored there.
Use the world schema as the interface, internal notices and fake demonstrations.
Sharing any external item with JEFF is a separate explicit action showing exactly
what text will be shared; importing does not authorize model access.

Proposed storage: app-private directory with reviewed inherited access controls,
per-user Windows DPAPI token/cache encryption, no plaintext logs, redacted errors.
DPAPI protects at rest, not against every process running as Alex; ignoring a file
in git is not security. A maintainer must verify storage/caller isolation before
real accounts. Existing Spotify's ignored JSON token store is precedent for a
flow, not evidence that this stronger boundary already exists.

Connections show permissions, account label, last success, Pause and Disconnect.
Disconnect immediately disables fetching and display; local token/cache removal
and provider revocation get separate truthful receipts. If revocation cannot be
completed offline, say “Disconnected here; provider access removal pending” and
offer the provider's account-permissions page. Do not claim global sign-out or
unpair Phone Link automatically. Purge private local records on disconnect;
no content tombstones in the shared world. Retain only minimal private dedupe
markers within the consented retention period, never resurrect cached previews.

Use the existing awake host loop with bounded backoff/delta cursors, not new wake
timers, services or cloud webhooks. Suspend connector activity while gaming,
locked or guard state unknown; stage no prompt/banner, and do not launch apps.
After ordinary wake, sync once then quietly catch up; no backlog toast storm.
Do not keep either device awake or modify Phone Link battery/power settings.
No inbox event wakes residents/models. Human-approved share/action is separate.

## What can happen next

Now, world-only by JEFF: staged internal-notice panel, count, filters, pagination,
local seen/dismiss/Undo behavior and Connections showing Not connected.
Keep current notices working; do not silently migrate/remove their state.

After Alex chooses provider/device and accepts the interface: commission a narrow
connector/storage/private-reader implementation, then review it before enabling.
Consent flows and a phone bridge require source/packaging; they cannot be safely
implemented by editing a lens. Installation/pairing/OS permission changes, OAuth,
first account reads and any external effects each need scoped authorization.

Fake acceptance journeys are in fixtures.json: replay, dismiss vs remote unread,
updated items, independent accounts, permission loss, unknown game guard and
sleep catch-up. They are proposed cases, not execution results.
Visual acceptance: not run here; needs a guarded browser-capable copy. No real
account/device inspection, OS notification read, OAuth, send or test toast ran.
