# Round three visual review protocol

Status: bounded visual and interaction review, with the initial protocol retained below and actual results recorded afterward. Media owns the review, root operates the enabled browser on its behalf. The media subagent called CUA inventory (no apps/browsers) and tried creating iab and chrome tabs; both returned Browser is not available. No workaround browser driver is used.

## Evidence to retain

For each reviewed checkpoint: source file hashes, server URL and runtime version, authored program revision, observed browser/tab identity, viewport, exact actions and screenshot path. A screenshot is evidence of the controlled review browser at capture time, not Alex's existing browser or an installed Agora build. A source label alone does not prove which build rendered; connect it with served files and observable behavior.

Root sends full AX state and screenshot for the first desktop view. Media inspects that before choosing input targets. Subsequent actions are derived from fresh tool observations. The same principle applies after source edits, resize, remount or navigation.

## Bounded review sequence

1. Desktop initial: inspect hierarchy, typography, spacing, content prominence, control discoverability and clipping. Check whether the work looks like a usable authored artifact rather than a catalog of abstract controls.
2. Keyboard: traverse with actual Tab input, observe a visible focus indicator, activate the authoring control from the keyboard and edit a source field. Record focus loss or scroll jumps after preview/apply.
3. Authoring: after reading the actual program syntax, introduce a novel conditional rule through the interface, then vary its input to cross the condition. Observe both rendered consequence and accepted state/receipt. This must not merely invoke a prepared theme toggle. Separate source parsing, program installation and event execution.
4. Refusal: enter malformed source, attempt preview/apply as supported, verify useful error and retained last working program. Repair through the interface and confirm normal use resumes.
5. Narrow: load narrow-review.html, whose iframe supplies a genuine 390 x 844 CSS-pixel application viewport. Inspect screenshot, navigation, author panel, content order, horizontal overflow and keyboard reachability. This is embedded viewport evidence, not a real phone or touch test.
6. Review feedback: identify concrete defects with screenshot/action provenance. Editing owns source fixes. Rerun only affected checks on changed source and label the new checkpoint.

## Claims screen access adds

Pixels can reveal unreadable density, contrast, visual competition, clipping, overlap, weak focus, broken responsive composition and differences between declared style and actual rendering. Input plus before/after screenshots can corroborate a visible consequence of an authored rule. They cannot establish authority, full state coverage, underlying provenance, replay, concurrency, all accessibility paths or all media semantics. AX/source/runtime inspection remains complementary.

A screenshot of a button labelled Applied is weak evidence alone. The test should alter an observable input and witness a specific predicted output, then read the actual receipt/state. A screenshot of an editor is not evidence that its program changed behavior.

## Open questions for peers

- Does a program change merely modify styling, or introduce a new relation between an event, a state condition and visible behavior?
- Does preview execute on an isolated state, and does applying a program inadvertently discard an unsaved content draft?
- Can a narrow reader reach the authored artifact before confronting source machinery?
- Does ordinary keyboard navigation survive applying the program, and is a refused edit recoverable without reload?

## Source-blind reciprocal review: Lark, initial capture

Root relayed a request from Claude researcher Lark to inspect http://localhost:8770/lark-two-sides/. We were told two deliberate faults exist but not their identity. This biases defect search; I did not force two conclusions. No fixture source or Iris findings were read before these observations.

Evidence: root captured C:/Users/Alex/.codex/visualizations/2026/09/18/01a0b5fe-d025-7513-bb15-5a9279c2a259/review/lark-initial.png, which I inspected with view_image. Root reported a DOM-measured viewport of 1280x720, scrollHeight797, scrollWidth1265. The rendered tool image was scaled; I did not infer CSS measurements from displayed bitmap dimensions. Source/runtime identity is not yet independently checked. This is the coordinator's controlled browser, not Alex's tab.

Appearance-only observations recorded before source reveal:

1. Three labelled ownership columns are easy to distinguish, and the overall tone is calm. Metadata is small and often very low contrast, creating a cost for reading the claimed precision.
2. The left column continues below the capture at Private. The offscreen-count footer described in AX is absent from this screenshot. A page scrollbar is visible, so this is not yet evidence that the hidden items are inaccessible. Requested next action: scroll to bottom and capture to distinguish ordinary recoverable page overflow from lost content.
3. The roof image's old textual description and attribution to jeff at revision7 are readable. The following current-revision/pixels-changed warning is nearly white and practically illegible against the background. The coordinator's AX report exposes revision9 much more clearly. Freshness therefore exists in text but is not comparably salient visually. No actual roof pixels are displayed; I cannot verify what the image depicts.
4. An orange left-edge bar marks the proposal; horizontal column rules differ subtly; the paint region is hatched with a question-mark label. No legend is visible. Active editing, selection, ownership and opacity are possible interpretations, not established meanings. Hatching plus question mark suggests unavailable interpretation, but remains an inference.

Screen access adds an important finding here: merely exposing a freshness warning in text or AX does not make that warning usable in the rendered view. Conversely, the screenshot alone cannot tell whether offscreen material is omitted, scrollable or inaccessible. Interaction and source/state comparison are still needed.

### Bottom-of-page follow-up, still source-blind

Root scrolled to document bottom and saved review/lark-bottom.png in the same visualization evidence directory. I inspected it. Reported scrollY was 77.333 with viewport height720 and document height797. Private and the footer become visible, so the initial viewport crop was ordinary page overflow, not itself proof of inaccessible content.

At the bottom, the footer still claims three items past the bottom and gives `look f02 :3`. Root confirmed these were AX static text entries42 and43, with no action/control. Thus the visible hint is command-shaped but not an actionable reveal affordance. We have not independently established that exactly three objects are missing; the footer itself could be inaccurate. The nearly invisible freshness warning remains a visual defect in this second capture.

Root also supplied computed text color for that warning and disclosed that a broad DOM query accidentally included a script node. Root therefore ceased to be wholly source-blind after the initial pass. I have not received or read that script content or Iris findings. The initial image and first recorded conclusions preceded the exposure.

### User's selected direction

Root relayed the user's explicit preference for a playful, spatial, highly customizable world. The visual rubric now asks whether distinct things feel graspable and independently placeable, spatial relationships are intelligible, edit targets/scopes are visible, and authored behavior provides expressive agency. Editorial polish remains relevant to one inhabitant; it is not sufficient evidence of a world. This supersedes any inference that calm editorial style alone is the desired endpoint.

Root's browser supports actual viewport override, so the planned narrow test will use390x844 directly. The prepared narrow-review.html is an unused fallback and is not served by the restricted prototype server. No iframe/mobile test is claimed from its existence.

## Astra running prototype: pre-spatial checkpoint

Root's actual tab loaded http://127.0.0.1:8771/editing/visual-workbench/index.html at1280x720. I inspected review/workbench-editorial-initial.png. The captured UI labels the evaluator R3.1 and begins at edition1/runtime0. This is the pre-spatial editorial checkpoint; it does not establish the later world interface. Root reported no browser warning/errors.

The cream/green/rust palette, botanical drawing and strong title hierarchy form a coherent authored surface. Concrete visual usability finding: the first viewport contains neither MOVE THE LIGHT nor Preview/Apply. Thus the available behavior is not apparent until scrolling, and authoring commitment controls are initially out of sight. I sent Editing a request for a near-art manipulation affordance and reachable commit controls. This is a screenshot finding; subsequent code changes need fresh observation.

### Independently authored rule, actually exercised

I supplied a new program rather than selecting a prepared theme or merely editing the existing threshold. On change, its condition is `0.35 <= controls.light <= 0.65`. Inside that interval it sets caption to INTERVAL STUDY and rotation to `(controls.light - 0.5) * 120`; outside it sets caption to OUTSIDE INTERVAL and rotation to0. It composes existing boolean/comparison/arithmetic operators and writes existing domain fields. That demonstrates a new small relation, not arbitrary-domain extensibility.

Root performed the actual browser authoring: replaced program.rules through Source while preserving document state; Preview showed uncommitted INTERVAL output at58%; Apply established edition2/runtime0. Actual AX setValue on the rendered slider changed it to60%, then80%. I inspected the resulting screenshots:

| Evidence image under thread review/ | Visible evidence | Root's accompanying AX/runtime evidence |
|---|---|---|
| interval-60.png | 60% slider, INTERVAL STUDY caption, changed art position, edition2/runtime1 receipt | Rotation12 degrees; one property changed on that transition |
| interval-80.png | 80% slider, OUTSIDE INTERVAL caption, changed art position, edition2/runtime2 receipt | Rotation0 degrees; two properties changed on that transition |

These were actual browser control interactions, not event calls from a script. They are not yet keyboard traversal evidence. The browser rendering corroborates the predicted program consequence. The root also entered malformed Source `{"state":` and clicked Apply. AX reported invalid JSON, last working result retained, nothing applied; the publication remained80%/OUTSIDE INTERVAL, edition2/runtime2. I have not independently inspected an error screenshot. Root did not save this old checkpoint before the spatial update, so no persistence claim follows yet.

### A visual ambiguity that was corrected, not a proven state bug

The scrolled interval screenshots show Source starting values rotation45 and the original caption beside different runtime output, while saying the working edition is up to date. I initially suspected a stale Source view. Root pointed out the helper above the cropped region explicitly states that light motion is local runtime until a starting value is authored. I withdrew the bug suspicion and notified Editing.

The distinction is legitimate: authored starting state and live activity need not be persisted identically. The usability issue is local visibility of that distinction when the helper scrolls away. Suggested wording: label the textarea Authored starting values, expose a separate current-runtime inspection, and describe the slider receipt as rule-updated runtime fields. No data-loss or accidental-reset claim was established.

## Spatial R3.2 checkpoint and real interaction

I inspected review/spatial-top.png, captured by root at1280x720 after Ctrl+Home. The earlier spatial-initial.png retained an old scroll position after reload; it is not the entry-view evidence. The R3.2 screen clearly adds a dotted world, publication, thought and found token with move handles, visible light control, New thought, Hide tools and a World authoring tab. Preview/Apply remain visible in the sidebar, addressing my first critique.

The default camera is too close: the publication dominates the view, the thought's text is cut off at the right and the found token is largely absent. Root independently noticed this. I requested view-only Fit world and zoom/pan affordances while preserving authored coordinates. A spatial canvas need not reflow like a document on narrow screens; it needs discoverable navigation and a way to inspect a selected object at readable scale.

Root reported the following actual browser and text-desk checks. I did not execute these actions myself or independently inspect every intermediate screenshot:

- Pointer drag moved thought-1 to(545,155); a real Right key with its handle focused moved it to(555,155).
- New thought created a fourth object. At light20%, both thoughts were rgb(170,199,186); at80%, both became rgb(237,197,103), while the found token stayed unchanged. This exercises the authored forEach selection on a newly created qualifying item.
- Save through the browser produced subject s02 revision1, appearance a03 in the separate visual desk. Text-desk read confirmed the moved coordinates and authored starting light0.58, even while the browser's local runtime light was80%.
- Root rewrote the stored kicker through ordinary text-desk commands to THE CLEARING / AN EDITABLE WORLD, producing revision2. A browser save based on revision1 visibly refused with409 while preserving the canvas. Load adopted the new kicker, four objects and starting light58%.

These are real local UI/storage bridge observations, beyond the earlier pure models. They do not establish distributed collaboration, automatic recipient notification, production authority, a long-held pointer under simultaneous update, or a general world renderer. Authored starting light and runtime light deliberately have different persistence behavior.

Editing then supplied R3.3 with fit/zoom and froze source pending QA. That camera change requires new screenshots and a targeted scaled-drag check: screen displacement must be interpreted in the world coordinate system. Earlier unscaled drag evidence does not automatically cover it.

## R3.3 fit, keyboard, narrow view and appearance checks

I inspected review/spatial-fit.png, narrow-top.png, narrow-world-editor.png and narrow-source.png. Root performed the browser actions; observations below identify the distinction between pixel review and relayed measurements.

Desktop fit now exposes four materially distinct objects instead of hiding the thought/token at the right. Move handles and independent positions make the spatial agency legible. The thought overlaps other work after the actual edits; this is authored arrangement, not a failure that requires automatic layout. It does obscure some text. We have not tested stacking controls, semantic occlusion reporting or a selected-object reading mode.

Root measured fit zoom79.333%. An actual approximately79-pixel screen drag moved a thought's world x from555 to655; Undo restored555. This targeted test supports the new scale-aware mapping rather than relying on the earlier100% drag. Fit itself did not author new positions. Root also exercised the Garden mist style choice through Preview/Apply, measured paper rgb(229,233,222), and used Undo to restore it. That is an actual appearance edit/undo check, separate from the independently authored behavior program.

The narrow browser viewport was actually overridden to390x844, not simulated by the unused iframe wrapper. Root measured page width375 with no page horizontal overflow. This is a desktop browser at a narrow viewport, not touch or physical-phone evidence.

The narrow screenshots show a31% miniature overview with all four objects. Fine text cannot be read at that scale, so an explicit100% control is useful; fitting is an overview rather than a readable miniature application. At the captured checkpoint, a large empty dotted floor follows the scaled objects and pushes authoring far down the page. I and root independently identified this as unnecessary navigation cost and asked Editing to bound the mobile camera height without changing source coordinates.

Once reached, the narrow World and Source panels are legible and Preview/Apply are visibly reachable. Root used a real Tab from World followed by Return to activate Source. The narrow-source.png screenshot clearly shows orange focus on Source, the selected-tab underline, persistent Authored starting values label, source textarea, Preview/Apply and recovery controls. This is positive keyboard/focus evidence for that path, not an exhaustive accessibility audit.

The final bounded-height correction is reviewed below. Other prior checks were not repeated without a relevant change.

## Final R3.4 visual review and evidence boundary

I inspected review/narrow-final.png after the mobile camera correction. At the actual 390x844 browser viewport, the world now ends above the receipt and the R3.4 footer is visible in the initial capture. The earlier excess dotted floor is substantially reduced. Root measured camera height379.79px instead of760px, with page width375 and no page horizontal overflow. The31% overview still intentionally sacrifices small-text reading; Fit and100% remain visible. This resolves the specific excessive-height finding, not all small-screen navigation needs. The authoring panel is still below this first viewport. Root restored the browser to1280x720 afterward.

Root additionally reports actual Rules-block authoring: changed light rotation multiplier75 to120, applied, observed angle44 to70 at58%, then loaded the saved edition to reset before the final viewport capture. This complements the independently authored Source program: one prepared block field and one newly composed relation both changed observed interface behavior. I have not personally inspected the final Rules screenshot, so that last check is root-relayed browser evidence.

The practical result is a small, functioning programmable spatial work, with actual browser authoring, pointer and keyboard placement, local runtime behavior, reversible appearance changes, and guarded save/text-edit/load through a separate desk. Screen review contributed facts absent from passing model tests: controls hidden below the first viewport, a camera that hid neighboring objects, empty mobile floor, visible keyboard focus, and a nearly invisible freshness warning in the other team's fixture. It also exposed my own mistaken inference: different Source/runtime values were an intentional distinction whose explanation had scrolled away, not established stale-state corruption.

This does not establish a universal application foundation. JSON contains this work's state and program; HTML/CSS/renderer code still lives outside it. New thought inheritance exercises a prepared object kind, not an unforeseen domain. Save/text-edit/load is manual adoption, not a live subscription. We did not test long-held input during renderer replacement, touch, broad accessibility, production authentication, distributed collaboration, rich media decoding, pixel-semantic correctness, or a real user's existing tab. Iris was invited to review our prototype, but no reply was available at closure; reciprocal independent review of this prototype is pending. The blind Lark review above did occur and remains separately scoped.

### Source snapshot at report closure

The following SHA256 values were read from disk after the R3.4 screenshot. They identify the closing source snapshot; they do not independently prove every browser-loaded byte, and earlier screenshots deliberately show earlier renderers/program editions. Runtime/edition receipts and viewport details are recorded above instead of collapsing all evidence into one revision.

| File relative to research/shared-visual-desk/ | SHA256 |
|---|---|
| editing/visual-workbench/index.html | B77D92698496729735FAAE08A06EEAE954C16CA49A85279251103B368DB2FB1F |
| editing/visual-workbench/style.css | B3E1172C14C7E41E5847A0D2485CC640C0526842D839C4A23BEF99B767B49092 |
| editing/visual-workbench/app.mjs | 6F9730DA1BF15F372FE50E1392D34501B6EBF46530A74B46FA4673F525B0D123 |
| editing/visual-workbench/document.json | AA3A7EDD731133C90417FF89341F0711B3961C2B3A554149CB361420FE392578 |
| foundations/program.mjs | 7535FFBD340AB39BA9540C0FF521F676FC7C991513D2084859622E970762F4CE |

All review image paths above resolve under C:/Users/Alex/.codex/visualizations/2026/09/18/01a0b5fe-d025-7513-bb15-5a9279c2a259/review/. These are root-controlled browser captures, reviewed by media, not screenshots of the user's pre-existing browser. No new automated test suite was introduced for the visual review; actual interactions and screenshots are the evidence. The earlier round1 and round2 toy-model tests retain their narrower claims.
