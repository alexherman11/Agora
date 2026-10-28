# Bar failures: investigation for owner review

Codex builder, 27 October 2026. Source proposal; not activated or accepted.
This inventory covers the available task cards and checked-in repair records,
not an exhaustive reconstruction of every outage. No exported transcripts or
session pickles were searched.

| When / primary record (read) | What broke and why | State in this checkout |
| --- | --- | --- |
| 24 Oct, task dk170; README.md, “Window stream connection pools” | Six HTTP/1 event streams exhausted the shared origin's six connections. Lines and new window/page requests queued indefinitely. SharedWorker was unavailable in embedded WebView2, so its native-stream fallback did not fix this. | Already repaired: `kdesk.WindowOrigins` gives each live window a listener and native connection pool. Historical README evidence: fifteen hidden browser windows, fifteen origins, Lines help 17.0 ms. That is prior evidence, not rerun here. |
| 27 Oct, SHELL.md rough spots 15–17; painter/ISOLATION.md amendment | Minimized/hidden renderers were throttled, then reported as hung, exited or reaped. Duplicate/serialized plan compilation and hidden periodic replanning amplified load. | Existing visibility-aware watchdog/recovery, longer instance lifetime, narrower admission and reduced replanning. No new painter change here. A real authored/component failure can still stop a part; this is distinct from unsigned navigation. |
| 27 Oct, SHELL.md rough spot 18 | Clicking the screen-sized wallpaper put it in front. Separate fullscreen checks mistook it for a game, hiding both bars and closing the WM gate. | Existing shared `gaming_gate.is_desktop` and `Agora.Desktop` mark; wallpaper subsequently moved to a rendered Windows wallpaper. Historical repair evidence is documented there. |
| 27 Oct, `GuiScreen.open.loaded` comment and implementation | A newly shown frameless bar briefly looked like an ordinary app; WM could tile/move the dock before tool-window styling. | Existing early `WS_EX_TOOLWINDOW`, removal of `WS_EX_APPWINDOW`, followed by AppBar placement. Early style exceptions are still swallowed; stronger native failure reporting remains a follow-up. No global WM changes here. |
| 27 Oct, task dk976 history events dk991/dk993/dk999 | Lines pin selected JEFF chat because icon family doubled as launcher identity; focus used a native WM key where an Agora window id was required. Map opening was folded into that investigation. | Existing exact launcher matching and Agora-id focus adapters. This looked like dock failure but is separate from bar painting/sign-in. |
| 27 Oct 15:34–15:53, task dk1020 | After restart, top bar, dock, map and JEFF chat opened unsigned or blank; later Lines worked. Which failed changed between restarts. Manual sign-in worked; repeated restarts eventually recovered. | This change addresses the shared cookie profile described below. Native acceptance is blocked, not proven. |

## New source finding and repair

**Read:** pinned pywebview `platforms/edgechromium.py`: `EdgeChrome.__init__`
constructs default `CoreWebView2CreationProperties`, enables private mode,
then initializes the core. Each successful `on_webview_ready` calls
`CookieManager.DeleteAllCookies()` before loading its URL. Every view had the
same default profile, including the hidden anchor.

**Inference:** during concurrent startup a later initialization can erase a
sibling's HttpOnly session between `/dev/signin` and `/desk/window-origin`.
Opening a later view can also invalidate an already-open page's requests.
Per-window ports isolate connection pools but cannot isolate host-scoped cookies.
This explains the moving subset of failures; direct native reproduction has
not completed in this worker.

`window_profiles.install()` assigns a fresh WebView2 `ProfileName` to each
creation-properties instance. `GuiScreen.start` installs it before the anchor
and widget guard. Profiles share the existing environment/user-data folder but
have independent cookies. Existing private mode, sign-in redirects, token
selection, HttpOnly cookies, door checks and guard are retained. No retries,
credential changes, persistent sign-in or source changes to pywebview.

Rough spots/source-edit log: the missing world handle is independent native
window session lifetime. World words cannot repair a cookie jar erased by the
native host; the fix belongs in the host adapter, not a lens redesign.

## Validation and remaining work

**Ran:** pinned Python `-m unittest test_window_profiles -v`: **3 tests in
0.005s, OK**. These check factory uniqueness/idempotence, failure when the
profile API is unavailable, and the installed runtime's constructor/private
cookie-clear seam. They do not prove native WebView2 behavior.

**Ran, blocked:** `-m unittest test_window_signin -v`: **1 test in 150.309s,
FAILED (failures=1)**: guarded hidden fixture timed out; ownership receipt
retained under `research/window-lab/.tmp-agora/agora-sandbox/`.
No forced cleanup or retry. Initial fixture errors were corrected (Promise
callback handling and module-running lookup); the revised native test was not
rerun after access failures.

**Ran, blocked:** the two existing `test_kdesk.DesktopTest` tests for
off/undo and distinct/reused/protected origins: **2 tests in 0.007s,
FAILED (errors=2)**. Both fail creating disposable world directories under
Windows Temp with WinError 5. A separate file listing encountered access denied
on a temporary fixture directory. Those exact actions were stopped; neither
ACL changes nor alternate-path retries were attempted.

The hidden test is prepared to open top/dock/Help/Lines concurrently, verify
authenticated reads, initialize a late blank native view and recheck all four,
then repeat after two disposable window-module restarts. It checks native
profile uniqueness, private mode, HttpOnly cookies and that every view remains
hidden, under the sandbox's foreground/input guard. `--shared` is its optional
negative-control child mode; not run here.

Before landing: complete that native test in an authorized test environment,
including its shared-profile negative control; rerun affected desktop/stream
and native widget-guard checks. Review profile compatibility and resource cost.
Do not declare acceptance from the three adapter tests. After owner review and
landing, the next coordinated window-host restart activates the adapter; this
worker did not restart the live desktop. Auth failures, invalid lenses and native
initialization failures still need clearer per-window reporting. Keep this card
open for review.
