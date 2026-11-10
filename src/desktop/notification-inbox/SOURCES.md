# Read evidence, 20 Oct 2026

Read code, not live user configuration:

- `src/desktop/notify.py`: outgoing PowerShell/WinRT toasts; `history()`
  reads that sender's own toast history, not an inbox for other applications.
  Ten-minute freshness, optional sound, Windows quiet-state limitations.
- `src/text-desk/notation/house.py`, `House.toasts`: frontier/keeper/real
  house gate, remembered line IDs and receipts. No inbound email/phone adapter.
- Live `home-notices` and four `Notice Alex` rules: internal landed/asking/review/
  design notes plus unanswered calls; focus timer holds the glance. Current open
  removes an internal notice; call-dismiss advances a shared event watermark.
  A richer inbox must not copy that watermark into remote read semantics.
- `src/codex/desk_notifier.py`: agent-mention delivery to a Codex
  thread, not consent for reading Alex's personal channels. Do not reuse its
  model delivery for incoming phone/email.
- `src/desktop/spotify_connect.py`, token-path code in `spotify_like.py`:
  explicit browser/PKCE precedent. No token/config files were opened or functions
  invoked; the ignored JSON store is not a proven isolated credential vault.
- Source-name/text searches found no Gmail, Graph mail, IMAP, Phone Link or
  UserNotificationListener connector in the inspected Python integration paths.
  No matching connector world object was found. This does not establish which
  accounts/apps/devices Alex has, nor whether he has consented to another system.

Read official documentation; proposals in PLAN.md are inferences, not API tests:

- [Gmail scopes](https://developers.google.com/workspace/gmail/api/auth/scopes):
  metadata is restricted and excludes message bodies; deployment verification.
- [Google desktop OAuth](https://developers.google.com/identity/protocols/oauth2/native-app):
  registration, browser/loopback, PKCE and public-client constraints.
- [Google token expiration](https://developers.google.com/identity/protocols/oauth2#expiration):
  external Testing refresh tokens generally expire after seven days for mail.
- [Gmail message listing](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/list):
  metadata scope disallows q; label filtering is available.
- [Gmail message get](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/get):
  metadata format/header selection, not a guarantee of body/snippet availability.
- [Microsoft Graph permissions](https://learn.microsoft.com/en-us/graph/permissions-reference):
  delegated Mail.ReadBasic permits basic mail, excludes body/preview/attachments;
  personal accounts supported. No write/send scopes proposed.
- [Microsoft auth-code flow](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow):
  native-client PKCE, registration and consent.
- [Graph message](https://learn.microsoft.com/en-us/graph/api/resources/message):
  message state/webLink/delta concepts; real per-scope behavior remains untested.
- [Windows notification listener](https://learn.microsoft.com/en-us/windows/apps/develop/notifications/app-notifications/notification-listener):
  manifest capability, UI-thread consent, broad OS access and revocation.
- [Phone Link setup](https://support.microsoft.com/en-us/windows/apps/phonelink/phone-link-requirements-and-setup):
  Android/iPhone setup and permissions, iPhone Bluetooth pairing. Not an Agora API.
- [Phone Link message limitations](https://support.microsoft.com/en-us/windows/apps/phonelink/troubleshooting-for-messages-in-the-phone-link):
  device/app restrictions and incomplete iPhone history.
- [Apple manual mail setup](https://support.apple.com/en-gb/102525):
  IMAP and app-specific password; not a password-free OAuth journey established here.
- [Windows DPAPI](https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata):
  per-user encryption caveats; not same-user process containment.

Ran: repository status/log/search/read commands and static fixture/document
validation only. No account APIs, private configuration, device discovery,
notification history, installs, settings, consent prompts or GUI tests.
