# Native browser admission: Codex takeover, 21 October 2026

## Critical design guidance from Alex

Alex, directly in the Codex chat, 21 October 2026:

> the surface should be designed with the central goal of being as agora native as possible, and like you said, bringing as much of the web as possible into things agora understands
>
> ^ CRITICAL DESIGN GUIDANCE

Implementation interpretation (Codex; distinguish from Alex's verbatim words):
make the surface world-authored and operable through native verbs. Tabs,
workspaces, bookmarks, navigation targets and deliberately captured web content
should have meaningful Agora representations. The web engine supplies rendering
and session primitives. This applies to the current everyday-browser and
organization priorities, not only a later automation feature. Representation
must preserve source identity, attribution and freshness, distinguish live
external observations from saved native state, and keep private presentation and
account state private. Imported content is data, not host authority. Do not turn
every transient DOM node into a durable shared object or log ordinary private
navigation just to call it native. Exact representation contracts remain to be
designed against the existing window-owned state work.

## Ownership

Additional critical direction from Alex, directly in the same chat:

> and dont forget either that this browser is a browser for agora objects like notes and documents, as well as for native windows files and things. It is a first of its kind universal browser

Scope clarification: the product is a universal browser spanning Agora objects
(including notes and documents), websites, and Windows files/resources. Everyday
navigation and organization must be designed across those target types from the
start: one coherent tab/workspace/history model with appropriate renderers and
contextual actions. Web support extends this browser; it does not define a
separate product. A common representation does not imply identical permissions,
replay guarantees or available actions across native, filesystem and external
resources. Preserve those distinctions without forcing separate user workflows.
The novelty phrase above is Alex's product ambition, not a verified historical
claim. Specific Windows resource kinds and their adapters remain to be defined.

Alex asked Codex to take over the paused browser work. JEFF recorded Codex as
execution owner on the existing public-web commission; the original worker stays
paused. The separate diagnostics worker owns changes to the shared sandbox
harness. These helpers do not modify or invoke that harness's cleanup path.

## Ran

Read-only host reconciliation found no original probe process/profile match and
no remaining original test desktop. No cleanup action was performed. This is a
new observation, not a retroactive successful-cleanup claim for the old run.

`run_admission.py` starts `admission_probe.py` on a unique hidden desktop with
the existing Guard. The child uses native WinForms/WebView2 directly, a new
InPrivate profile, no pywebview bridge, no host objects, no debug port and no
public navigation. It starts initialization after the form is shown, records a
25-second deadline explicitly, and disposes itself normally. The parent never
kills a process or deletes evidence. It records source hashes and a post-exit
profile/name process inventory. Its game check covers named common game
processes; it is not a universal game detector.

Final retained run: `evidence/admission-20261021.json`.

- Engine: **155.0.4283.62**, initialization from 0.468 to 0.718 seconds.
- An inline top document and child document loaded successfully.
- Positive control: messaging enabled; both top and child canaries reached the
  native counters.
- Negative control: messaging disabled, a fresh document loaded; both calls
  returned normally but **zero messages** reached the counters in 500 ms.
- `pywebview` was absent in both documents. No host object was registered.
- Child readiness was `complete`; no timeout or process-failure event occurred.
- Child disposed/exited at 1.875 seconds. Parent wait succeeded, no windows
  remained, and the post-exit process query found zero matching processes.
- Guard passed: no sandbox window appeared on Alex's desktop or took focus;
  input desktop stayed Default, and no unsolicited cursor movement was observed.
- 21 deterministic browsing/receipt tests passed. Changed-source Ruff passed.

Earlier runs retained in `.tmp-agora` established initialization, then showed the
old test's incorrect assumptions. `chrome.webview` remains an object when
messaging is disabled. This runtime also does not throw from `postMessage` in
that state, despite the documented throw. A test requiring either absence or a
throw would falsely reject it. The useful evidence is a live positive control
followed by observed non-delivery, not JavaScript object shape.

## Limits and next step

**This is an offline message-channel check, not a usable public browser.**
The original worker's E_ABORT remains unexplained: execution context and
initialization lifecycle both differ. Do not claim a root-cause fix.

No actual host-object-call probe, redirect/frame/network containment, worker or
socket refusal, popup/permission/download refusal, public page, screenshot,
input/history journey, authenticated session or background subscription has
passed. The request filter currently returns 403 for intercepted resources;
the test does not claim that covers every network mechanism or engine bootstrap
traffic. The next fixture must establish those independently before enabling
public browsing. Keep the privileged HUD unchanged.

The Facebook bridge remains a later opt-in subscription on a private browser
session, with attributed, deduplicated imports and visible stale/login state.
No Facebook login, cookie access, import or external message occurred here.

## Reproduction

After current host/guard preconditions are checked, the pinned interpreter can
run `src/desktop/browsing/run_admission.py`. It always creates a new
receipt/profile/desktop; it does not retry or erase a failed run. A failure must
be inspected before another launch. The pure checks use unittest discovery in
this directory and do not launch anything.

No runtime module imports these helpers. Reversal is leaving them uninvoked;
there is no live feature switch, world migration, HUD restart or activation.
