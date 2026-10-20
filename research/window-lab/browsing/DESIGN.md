# Browsing inside Agora — staged architecture, 20 October 2026

For Alex: one viewer with tabs for your desk, websites and files you choose.
Back goes through that tab's pages. Opening something never makes it the topic
of your chat. Sites that cannot work here get a plainly labelled **Open in
browser** choice. No accounts or browser data are connected by this proposal.

Status: JEFF accepted round 1 on the commission for an inactive controller,
fixtures and staged world chrome. This is round 2, not an enabled browser.
The navigation experiment is not imported by the HUD. The layout preview does
not display remote or device content. No host, engine, server or active lens
source was changed.

## What exists (read)

| Surface | Actual behavior | Consequence |
| --- | --- | --- |
| Live `home-viewer`, read on the commission | One `viewing`, one `back`, `with`, search and pins; Back swaps two values | Preserve today's selection until migration; not a real stack |
| `names/view.verb`, `home-search/apply.py` | Names/search write that state | Route all entry points through the future controller, not just the address bar |
| `desk-shell/lens.js` | Agora names use nearest `on link`; HTTP Markdown links call `window.open` | Modifier/new-tab handling needs a single routing contract; do not steal editor Ctrl-click or explicit chat-context gestures |
| `scene.page_source`, `desk-shell/page.js` | Lens or server-path preview, direct child DOM access, trusted same-origin | Keep it for trusted Agora previews; do not broaden it to arbitrary HTTP URLs |
| `hud.py` | `js_api=Api(self)`, host/media/bring/hide; persistent `hud-webview` storage | Never navigate the privileged HUD into remote content |
| Installed pywebview 6.2.1 `platforms/edgechromium.py` | Popup handling opens externally or navigates current view; bridge injection after navigation; download handler may show a save dialog; request event edits headers | Existing wrapper is not a ready browser containment layer. High-level callbacks are insufficient proof of cancellable navigation and full request coverage |
| `deskd.py`, `door.py` | Browser foreign-Origin/Fetch-Site checks; headerless local clients accepted without authentication | Preserve checks. Do not call them a complete capability boundary, and never let remote views navigate to the trusted server |
| `hud-equal/webview_page.py` and `webview_drag.py` | Guarded native WebView2 fixture window and copy-only drag harness | Reuse the testing pattern later; this is not a reusable isolated tab host |
| `scripts_mirror.py` | Explicit script-note/file synchronization, including write-back; copies must not touch real files | Do not reuse as file browsing permission, automatically mirror selected content into the world, or broaden its file scope |

The CSP specification makes frame restrictions the site's choice; native top-level
content avoids iframe frame-ancestor denial but does not guarantee every site,
DRM, extension or authentication flow works. Never strip CSP/X-Frame-Options,
ignore certificate errors, disable engine sandbox/site isolation, or proxy a
site through Agora to make it appear same-origin.

## Chosen structure (proposed)

```text
World lens: trusted tab chrome, names, bounded panel, explicit controls
       | typed user intent; never shell text
Parent navigation controller + PRIVATE tab/history store
       + Agora renderer: existing trusted lens host, own origin/authority
       + Web renderer: separate unprivileged native WebView2 content controls
       + File reader: explicitly selected file, host-private handle grant
```

These are distinct content surfaces behind one viewer, not one privileged
WebView with its URL repeatedly replaced. Use the existing installed WebView2
engine through an audited adapter. Prototype native child-controller placement,
focus and z-order before choosing a pywebview extension versus a small native
host. Do not install a replacement engine or launch a helper in this stage.
Profiles separate cookies/storage; they do not isolate same-user processes or
authorize access to Agora. The web adapter gets no `js_api`, host objects,
MCP/Desk credential, world snapshot, local path grants or automation endpoint.
Avoid a generic remote `postMessage` bridge altogether.

Chrome is a world lens so JEFF can change its arrangement. Engine lifecycle,
private persistence, authenticated intent delivery and file selection need
source. A shared world prop is not permission to navigate a privileged engine.
Only verified user gestures in trusted chrome drive the host; world edits from
an agent may propose a link but must not silently open it.

## Address and navigation contract

| Target | Canonical private address | Display |
| --- | --- | --- |
| Agora | `agora://<world>/item/<stable-ref>?lens=<name>#<anchor>`, or `/lens/<name>` | Named object/lens and world; names clickable |
| Web | Parsed HTTP(S) URL, normalized scheme/host, no userinfo | Actual committed origin/location, no forged title as origin |
| Local | `local://selection/<opaque-reference>` | Chosen basename and “This device”; reveal full path only deliberately |

These are application addresses, not OS protocol registrations. No association
changes. Names resolve inside the selected world and must be unambiguous. IDs
remain internal. Unknown protocols, raw drive/UNC/device paths and `file:`,
`javascript:`, `data:`, shell or app-launch addresses never execute. In the
location bar a local path may offer **Choose this file**, but does not read it.
An Agora deep link from a site is an explicit boundary-crossing request:
show a named confirmation in trusted chrome; never auto-honor script navigation.
Local deep links require an existing user-selected grant or reselection.

Each tab has a stable key, entries, cursor, entry-specific scroll/zoom, current
renderer and a pending navigation generation. Begin shows loading without
rewriting the committed location. Completion commits the final address once;
redirects do not add intermediate entries. Location changes on commit, title
changes cannot spoof it. Failures preserve the last good page and show the
failed destination privately with Retry/Back; an empty tab shows a real error.
Superseded/closed-tab completions cannot resurrect pages. Stop cancels the
pending generation; restart adds a new host-session nonce so old events cannot
match fresh generations.

New navigation after Back truncates Forward. Reload keeps the current entry;
redirected reload updates its address. Same-document fragment/pushState entries
are recorded from native navigation/history events; replaceState replaces one
entry. Native entries retain engine history keys. Do not call Navigate(oldURL)
and claim it restored a POST page or a live SPA. Adapter must synchronize native
GoBack/GoForward with mixed-kind history and suppress duplicate commits, including
script navigations. An unavailable native entry after restart becomes a
restorable-location entry, not a promise to restore live DOM/forms.

Switching tabs preserves live views while resources allow. Discarded views keep
reading position and show “Reloaded” when reconstructed; never serialize forms,
passwords or arbitrary DOM. File handle grants expire on close/restart/revoke;
saved placeholders prompt reselection. Closing an ordinary tab selects its
nearest neighbor and offers session-only Reopen closed tab, excluding expired
file authority.

The optional private **History** log is distinct from the per-tab Back stack.
Back traversal does not create a second visit. Record commit time, title,
origin/target and visit reason only under Alex's chosen retention; first stage
keeps this log off. Do not publish full URLs, query secrets, local paths or
reading positions into the shared world. The experiment's snapshot is a
private-store representation, not a world-prop schema; it is in-memory only.
No automatic fetching of restored tabs until the viewer is shown and active.

Normal clicks navigate the selected tab. Middle-click or explicit **Open in new
tab** opens another. Reserve Ctrl-click on Agora document content for explicit
chat attachment where that contract applies; offer context menu/new-tab button
instead of assigning conflicting meanings. Browser modifiers may follow browser
conventions in the web surface. Ctrl+L focuses location, Alt+Left/Right traverse,
Ctrl+R reloads (confirm form resubmission), Ctrl+T/W opens/closes a tab and
Ctrl+Tab changes tabs. No global hooks; shortcuts are local to focused viewer
and must not consume composer editing, IME or game input. Escape stops loading
only in viewer focus. Long content scrolls inside its panel, not the HUD;
many tabs use a compact overflow menu. No looping loading animation.

Chat context is a different capability: navigation, Back, tab selection, search,
pop-outs and reload never write `about`, `context`, `quote`, `reply_to`,
`reviewing`, composer or draft fields. Only the explicit attachment/comment
gesture may do that; a selected-text comment retains its source. Verify this
against the real composer on a copy before routing existing links.

## Required security gate before any remote renderer is enabled

1. Authenticate trusted-data requests and host intents using a reviewed
   parent-owned channel/bootstrap. Header absence, body `as`, world props and
   loopback presence are not identity. Do not send the credential into remote
   controls, URLs, world state or logs. Retain foreign-origin protections and
   reject unexpected Host/Origin values. Review static/media endpoints too.
2. Block remote top-level and frame navigation to Agora, all file/local/custom
   schemes, loopback, link-local, private-network and special-use destinations.
   Cover subresources, redirects at every hop, workers/service workers,
   WebSockets/WebRTC, popups, prefetch and downloads, not just address parsing.
   Unreviewed request mechanisms remain unavailable. No remote Local Network
   Access permission. Alternative IP encodings, IPv4-mapped IPv6, DNS rebinding,
   mixed public/private DNS answers and proxy resolution must fail closed.
3. A DNS preflight is insufficient: verify the actual connection destination.
   Determine which installed WebView2 APIs can enforce the policy without
   disabling engine protections. If they cannot, narrow unsupported capabilities
   or return a reviewed architecture blocker; do not sell URL filtering as
   network containment. No OS firewall/security/policy edits under this card.
4. Trusted origin is never a destination in a remote control; a top-level GET
   to localhost otherwise changes origin and can read its own subsequent APIs.
   Separate profiles and same-origin policy alone do not solve that.
5. Remote text remains untrusted display content, never tool instructions,
   grants, selected local content or automatic chat context. The site cannot
   use an Agora renderer as a fetch/proxy service.

`request_policy.py` is an executable specification with fixture DNS answers,
not an interceptor. Its tests cover intended refusals, not the connection,
engine hooks, origin isolation or authentication. Those remain acceptance gates.

## Files and web features

Local selection: host file chooser only after a deliberate press. Canonicalize
the actual opened Windows handle, verify final path/type, reject UNC/network,
device namespace, alternate data streams and unsupported/executable content.
Do not follow a replacement pathname after checking it: retain the selected
handle/identity, or require reselection after change. Reparse/symlink targets
must resolve to the exact deliberately chosen local file and be shown before
granting access; initial support can refuse them. No directory enumeration.
Relative links/images in files do not grant neighboring-file access.

Initially support bounded read-only text, images and PDF using inert readers.
HTML/SVG/active documents require a separate untrusted surface with scripts/
external requests disabled and no file-origin authority; show unsupported until
that is proven. Never serve a whole folder or map it into the trusted origin.
Opaque local refs are lookup keys, not proof of consent or portable bearer URLs.

| Feature | Initial policy; later deliberate action |
| --- | --- |
| Sessions | New dedicated web profile, no Edge/Chrome/HUD cookie or password import. Persistent site login only after scoped consent; no sign-in trial now. Cookies stay engine-private; no cookie APIs exposed to residents |
| Downloads | Cancel before any save dialog in initial stage. Later show origin/name/type and one-click consent/chooser. Never auto-open or execute; dangerous files require separate explicit approval |
| Uploads | Deny initially. Later a site-scoped chooser for exact files; selection for an Agora local tab is not upload consent; no directory/drop upload by default |
| Permissions | Deny camera/mic/location/notifications/clipboard read/filesystem/payment/automatic downloads by default. Origin-specific visible prompts/revocation before supporting each |
| Popups | Intercept, preserve opener isolation, no external launch or foreground theft. User-initiated HTTP(S) may become a tab after review; script popups denied. OAuth popup/account flow not tested |
| External protocols | Deny, including app installers and `mailto:`; no shell fallback. “Open in browser” is explicit HTTP(S) only, no automatic fallback or settings changes |
| TLS / auth / DRM / extensions | Keep engine checks. Show useful unsupported/error with explicit fallback; no certificate bypass, automatic credential prompt, extension install or claim of full browser parity |
| External send / purchase / settings | Agents do not perform them. Normal Alex interaction remains his action; automation must obtain its own scoped consent and cannot use this viewer as an execution broker |

No background timers that wake the machine. While asleep/in a game, no engine
creation, restore/fetch, permission prompts, downloads, popup/external actions or
agent navigation. Unknown guard state fails closed. Do not auto-resume deferred
external actions; re-present them after a deliberate viewer action. Review
background web workers/audio separately before enabling persistent sessions.

## Incremental delivery and reversal

1. **This stage:** isolated controller, fixture request policy, parsed static
   world chrome, architecture and exact stage manifest. Existing entry points
   remain untouched. No browser, file reads, host activation or real accounts.
2. **JEFF world round:** create only the manifest's named fixture objects in
   Study. Compare at Alex's scale on a guarded copy. Review menu/keyboard/context
   conflicts with tiling, dock and explicit-chat-context owners. No actual sites.
3. **Source follow-up:** authenticated intent/data boundary + audited native
   unprivileged content adapter and request policy; independent security review.
   Then actual local adversarial fixtures: malicious page attempts fetch/form/
   navigation/iframe/subresource/worker requests to a fake trusted service and
   local files; assert service sees zero unauthorized reads/mutations. Test
   redirects, popups, worker/socket cases, DNS rebinding and unknown guards.
4. **Navigation integration:** controller-backed Agora tabs first; migrate
   current viewing/lens as first entry, preserve pins/drafts; switch one route
   at a time with exact check-then-replace live passages supplied by JEFF.
   Then selected local files and finally enabled web capability after review.
5. **Scoped real acceptance:** guarded browser-capable run, no Alex screen,
   no real sends/account sign-in. External browsing/sign-in only with new scope.

The manifest creates inactive new objects only. Reversal changes their `stage`
to `withdrawn` and removes only the `lens` tag on the new preview. No deletion,
active `home-viewer` replacement, pins/dock edits or actor state migration.
Later production migration must save exact live viewer/route passages and
private state before switching; rollback restores that snapshot without
touching composer/drafts. No guessed stale replacements are supplied here.

## Evidence and acceptance limits

Ran commands/results are in EVIDENCE.md. Fixture tests cover model stacks,
mixed typed targets, location redirect/reload semantics, saved reading state,
late-event refusal, protocol/path refusals and policy classification.
They do not read a device file, prove a security boundary, render a website,
restore a real native history entry, exercise keyboard focus, touch the live
composer or provide visual acceptance. No external browsing or account calls.
Real layout shots: not run here; needs a browser-capable guarded run.

## Primary sources read

- https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/security
  — origin validation, untrusted messages and removal/restriction of host objects.
- https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/overview-features-apis
  — native navigation/history, request, permissions, downloads and popup APIs.
- https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/multi-profile-support
  — profile data separation, not a host capability boundary.
- https://pywebview.flowrl.com/api/ — `js_api` exposure and window API.
- https://www.w3.org/TR/CSP3/#directive-frame-ancestors — framing restrictions
  and their relationship to X-Frame-Options (working draft, not final standard).
- Installed 6.2.1 engine source, not website API promises, establishes the
  current wrapper behavior listed above.

These sources informed the proposal. The actual installed engine's complete
API coverage, native child composition, background suspension and connection
destination enforcement remain unverified deployment prerequisites.
