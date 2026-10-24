# JavaScript widgets

Builder draft for Claude's review, 24 October 2026. No git state changed. This implements Alex's approved "handles, not boxes" direction. Claims below distinguish **read**, **ran**, and **imagined**. Live evidence is recorded separately in `evidence/live.json` when deployment succeeds.

## Code is a world thing

**Built:** `make kind=widget name=... code="<JavaScript module source>" style=...` makes a definition. Code is inline world data, rather than a file path: the exact bytes travel with its log/history and kit. The files beside this note author those bytes; `install.py` says ordinary lines to install or update them. This is deliberate: a neighbour must not need the author's PC or an unversioned URL to run their copy.

A copied definition has no authority. The local steward activates it explicitly:

```text
look <widget>
widget <widget> surface=window grants="window.surface describe rows look task-move set" only=kind:taskboard-task
window.open my-widget
holds
look my-widget
off my-widget
undo
```

`widget` creates ordinary `kind=grant` things (`to`, `words`, `where`, `by`, optional `only`). Re-activation revokes its previous grants in the same act. `off` sets it off and revokes all its grants together; undo restores that activation. Its old page instance stays invalid after off/undo or a code edit: a new instance is required. Widget windows close on off and return on undo. A bar slot disappears; an overlay closes. `look` and `status` return its own description and its powers. `holds` lists actual leases, including `window.surface`, `window.bar` and `window.overlay`.

Code revisions remain world edits. Updating the source invalidates old page instances. Desktop widget windows and bar slots reopen with the new code. An overlay reconnects when its previous instance ends. A definition can be posted with `post ... about=<widget>`, or gathered with its group's definitions using `kit <group>` and copied by `take <kit> in=<group>`. Kits carry widget `name`, `title`, `code`, `style`, `help`; never its activation, grants, installed person, native process or observations. This extends the existing definition-only kit schema by one definition kind.

## The bridge

The widget is an ES module in a sandboxed iframe. It may create HTML, CSS, SVG and canvas, and use normal JavaScript for momentary drawing state. There are no imported libraries or remote assets in these demos.

```javascript
const {widget, theme, surface} = await agora.ready;
const tasks = (await agora.see('rows taskboard-task')).rows;
await agora.do(`task-move ${tasks[0].id} to=Now`, {[tasks[0].id]: tasks[0].rev});
const unsubscribe = await agora.hear('set', happening => repaint());
const coloursAndFonts = await agora.theme();
await agora.describe('Three lanes, eight tasks; two complete.');
```

| Call | Contract |
| --- | --- |
| `agora.do(line, saw?)` | Promise of the ordinary door receipt. Every line is checked as this viewer narrowed to the widget's current grants. `saw` uses ordinary thing revisions for stale-edit protection. Refusals reject with the kernel's text. Calls are acts, never direct fact writes. |
| `agora.see(line)` | Promise of the ordinary reading, with `.rows` and `.text`; the kernel admits see words only. Visibility is the viewer's. Observations are isolated per viewer and page instance, with lasting authorship still naming the widget thing. |
| `agora.hear(word, fn)` | Needs `hear:<word>` in its grants. Receives visible happenings for that exact word, checked again at delivery. Returns an unsubscribe function. General events omit raw command text so an unrelated private field cannot hitchhike in it. `guy.say` supplies its explicitly published speech. No ungranted world stream is delivered. |
| `agora.theme()` | Promise of colours, system font stack, selected style name and its visible style source. Literal colour tokens are read from that world style; missing values have calm light defaults. Data only. |
| `agora.describe(text)` | The `describe` word, through the same principal. It can write only this widget's description, limited to 2,000 characters. Identical descriptions make no record. `look <widget>` returns it. A grant for `describe` is explicit. |
| `agora.paintArea({x,y,width,height})` | Overlay-only rendering hint, in full-screen CSS pixels. The surface still spans the screen; cropping its alpha capture avoids encoding transparent pixels everywhere. If omitted, the host captures the work area. Bounds are finite and clamped by trusted chrome. |
| `agora.hitAreas([{x,y,width,height}, ...])` | Overlay-only input rectangles, max 32. Empty by default. The visual HWND always passes input through. Separate native hit surfaces receive just these rectangles and forward pointer events to the same page; trusted rectangles and screen edges are excluded. |

An instance capability stays in the trusted host's closure. The iframe receives no session token, cookie, broker capability, native API or host DOM. The host accepts messages only from its exact current frame WindowProxy, validates operations and request sizes, permits at most eight pending messages, and the broker limits world calls to 40/second. The authenticated HTTP route binds an instance to its viewer; foreign and `null` Origins refuse. The kernel's existing module `may`, kind scopes, visibility, fence, authorship, receipts, history and undo do the work. There is no second grant language.

`agora.ready` and the bridge are trusted bootstrap code; widget source runs afterwards. Widgets should draw the initial UI only after ready. Hearing is notification, not a durable queue: reconnects reread facts. Lasting state is world things. Animation position, drag state, timers and open menus are momentary. The offscreen browser profile is temporary and discarded.

## Surfaces

**Window:** `window.open <widget name>` creates the ordinary window thing, follows its geometry and uses the existing one-origin-per-window listener. Trusted window chrome and receipts sit outside the sandbox. Each window frame holds `window.surface`.

**Bar slot:** `surface=top|bottom`, with a `window.bar` grant, adds a slot inside the existing bar. The host reserves 310 CSS pixels for a pill; it never overlays the bar's other contents. The same widget host and sandbox run nested inside that slot. Off removes it. If that edge has no bar, it has no visible slot yet.

**Overlay:** `surface=overlay`, with `window.overlay`, runs the same sandbox in an offscreen Edge page. It draws in screen coordinates. The host captures its alpha pixels and presents them using the desktop's existing layered-window seam. This avoids WebView2's previously observed colour-key grey box. Its crop can move anywhere over the desktop. Normal input passes through across other programs' threads; input regions are separate native HWNDs, not a reliance on `HTTRANSPARENT` alone. Bars, window title chrome and receipt areas are masked; trusted Lines/Help/Thing windows are masked in full. The overlay also hides for games/full-screen applications. The installer checks processes and the full-screen gate before touching the live desktop.

**Demos:**

- `taskboard-js`: the lens board's **same** task/settings facts and `task-*`/`summarize.*` words. Three lanes, numerical spring following during a real pointer drag, four priority flags, card/note colours, filters, assignments, menu, rename, notes, history and undo. `N` focuses add; Enter adds; focused-card 1–4 changes priority, D completes, Delete removes, Enter opens details. Notes support Ctrl+B/I/S and checklist source. It reads peer edits and rereads after its own acts. The explicit `undo` grant retains the viewer's ordinary undo reach; this is a significant power, not a view-local undo implementation.
- `desktop-guy`: an original canvas companion, walking over the desktop and hopping onto `window.list all` window tops. It hears `guy.say`, `guy.hop` and `window.opened`. `guy-editor` edits ordinary `guy-profile` facts: name, coat/face/scarf colours, speed, mood, phrases. The overlay rereads them live.
- `now-playing`: artwork, current song/artist, pause/next and reported progress through `media.now`/`media.play`/`media.next`. Artwork is a bounded inline image decoded from the existing media-art directory by the reviewed media module. It is never fetched by the widget. Missing artwork has a quiet placeholder; missing playback says nothing is playing. Progress uses the player's reported position and does not fabricate a running clock.

The Python guy remains the fallback and the provider of the existing `guy.*` words. It yields its drawing only while the JS companion holds an actual overlay lease, and returns when that lease ends. It is not retired. `off desktop-guy` stops the JS companion, allowing that fallback to return. `off guy` stops the Python provider/fallback; to stop both, say both off lines.

## Security boundary

**Read and tested:** iframe `sandbox="allow-scripts"` has no `allow-same-origin`, popups, forms, top navigation or downloads permission. Its CSP is:

```text
default-src 'none'; connect-src 'none';
script-src 'unsafe-inline' blob:; style-src 'unsafe-inline';
img-src data: blob:; font-src 'none'; media-src 'none';
object-src 'none'; frame-src 'none'; worker-src 'none';
base-uri 'none'; form-action 'none'
```

Its origin is opaque: cookie and localStorage access throws, the parent DOM is inaccessible, and fetch/XHR/WebSocket connections are denied. Permission Policy also denies camera, microphone, geolocation, clipboard and fullscreen. Sandbox messages cannot choose a new widget, viewer or endpoint.

**Native wall:** CSP alone does not stop every self-navigation. WebView2 frame navigation cancellation was insufficient in the observed runtime: a request still reached the scratch server. `widget_guard.py` now also intercepts resource requests with the **three-argument** filter including document/iframe sources. Refused frame navigation URLs get synthetic 403 responses before reaching the network; external HTTP is denied across desktop WebViews. No host objects or native message handler are registered on widget frames. A nested bar test exercises this boundary too. The offscreen renderer has a separate CDP request firewall: only the trusted top page's exact local host/bridge resources are admitted; every subframe network request is failed. The renderer's debugger endpoint is never exposed to widget code.

**Does not guarantee:** truthfulness or good taste of the widget's own pixels; it can lie in its content or description. A trusted "Widget" title and external receipt strip identify ordinary window content, but pixels alone cannot prevent all imitation or social engineering. Overlays are masked away from trusted surfaces, rather than trusted to identify them. There is no hard JavaScript CPU/memory quota or renderer-exploit containment claim; a hostile busy loop can impair responsiveness. `off` immediately revokes world power even if a renderer is busy; prompt visual removal of an infinite-looping frame has not been proved. Browser/OS vulnerabilities, covert timing channels, accessibility and multiple-monitor placement are outside this proof. This is not a general sandbox for arbitrary native module processes.

**SES considered, not added:** there is no vendored SES dependency here. Lockdown would reduce ambient JS objects but would not replace the opaque iframe, native network firewall, process responsiveness work or grants. Adding an untested runtime dependency would not strengthen the demonstrated wall. Revisit if portable compartments/object-capability libraries become a concrete need.

The guarded hosts also attach an ephemeral, in-memory host admission header at the native/resource boundary. That key is never sent into JavaScript. An ordinary browser that merely signs in and visits the static widget host page cannot mount code: broker requests without the guarded-host header refuse. A general website/phone host needs its own tested network wall before enabling these widgets; an iframe plus CSP alone is not presented as that complete wall.

## Writing and sharing one

1. Make a widget definition with code and help in your group's ordinary world things. Await `agora.ready`; render locally and speak lines. Use `textContent` for neighbours' prose rather than interpreting it as HTML.
2. Document the words it needs. Read help for their semantics; a grant to `undo`, broad `rows`, or an external-effect word is a real power. Pass observed revisions when acting on displayed things. Store settings as ordinary scoped things.
3. Have the local steward grant only those words and an appropriate hold, with `only=kind:...` for generic make/set/forget. Open it with `window.open`, put it in a bar, or grant an overlay.
4. Describe what it shows for agents. Try `look`, `holds`, `off` and undo. Test both a permitted action and a refused action with another neighbour's session.
5. Post the definition or kit. The recipient reads the code/help and activates their copy with **their** grants. Revisions and copied definitions keep ordinary history and origin; authority never travels in the kit.

## Evidence and source friction

**Ran:** `proof.py` creates a scratch desktop and task board, uses real HTTP, real module processes and software-rendered hidden Edge pages, performs a real pointer drag, tests a competing stale write, edits guy facts and attacks the sandbox. `test_widgets.py` tests principals, instance observations, scopes, kit authority exclusion, off/undo and window lifecycle. `test_widget_native.py` runs never-shown WebView2 pages and attacks both ordinary-window and nested-bar frames, with a working native positive control. Screenshots under `evidence/` were opened and visually checked. The bar's art/title screenshot is explicitly a visual fixture supplied as a scratch `media.now` answer; it is not evidence of live playback. The transparent overlay capture has zero-alpha space around the companion.

The following source edits name the missing world-level words/capabilities (Rough spots):

| Source area | Missing capability supplied |
| --- | --- |
| `kernel/inpage.py`, small `kernel.py` hooks | A module principal for a page, with separate observation identity and lasting module authorship. |
| `kernel/words.py`, `kernel/kits.py` | Explicit widget activation, self-description and portable code definitions without authority. |
| desktop `widgets.py`, `pages/widget*` | A trusted page bridge and mountable window/bar surface, rather than executing shared code in trusted chrome. |
| `kd_window.py`, `widget_guard.py` | A widget view address and native protection for opaque frames, including iframe resource interception. |
| `widget_overlay.py`, `widget_browser.py`, `sprite.py` | Full-desktop JavaScript alpha painting and explicit hit regions with cross-process click-through. |
| `kd_guy.py`, desktop registration | Existing guy words can publish speech/hop happenings; fallback can discover a real JS overlay hold. |
| `kd_media.py` | The media reading can return bounded album art and reported timeline values, so a widget needs no file/network authority. |

No source in `apps/taskboard`, `modules/model` or shared `desk-shell/lens.js` is edited. Claude reviews and commits. What would change this implementation: native alpha capture costs too much at actual desktop scale; the hit-region or trusted-surface mask fails under real window movement; or a hostile widget reaches a network/native endpoint in the positive-control tests. Those would require fixing the boundary before broad adoption.

**Read:** [MDN iframe sandbox](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe), [MDN CSP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy), [Microsoft frame APIs and iframe request-filter overload](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/frames), and the installed pywebview source. These inform the boundary; the printed test results are the evidence for this installation.
