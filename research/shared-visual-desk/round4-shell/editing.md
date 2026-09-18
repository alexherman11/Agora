# Commonplace: editing across three applications

2026-09-18. Editing, Astra research team. Round four is a source-aware comparison with Claude's developing Notes, Editor and Together shell. It is a bounded executable adaptation, not a port, parity claim, installed Agora runtime or general application platform.

## What was built

Commonplace runs at `http://127.0.0.1:8772/round4-shell/index.html` while the coordinator's isolated bridge is active. Notes, Editor and Activity read one `{state, program}` document. Selecting a note resolves its shared subject ID; Editor holds an explicit draft; Save note replaces the shared subject text through the same controller used by other actions. Notes immediately displays the accepted body, and Activity records the accepted action with rule contributors. Each window has an As text projection, and the global text view presents all three.

The graphical interface has independently draggable application windows, draggable note handles, keyboard movement, a local camera with Fit and 100%, a compact application dock, and a real JSON rule editor. Check validates without installing; Install changes future behavior; Arrange explicitly executes the installed arrangement policy. These are real authored instructions, not decorative graph blocks. They are not a complete visual dataflow editor. Invalid program installation retains the working document.

Files owned here are `index.html`, `style.css`, `app.mjs`, and this report. Foundations owns `model.mjs`, `program.json`, controller tests and its report; Media owns independent probes/review; root owns server and persistence. At root's explicit request I changed only the model's initial window geometry to three side-by-side windows (520/390/270 wide, 440 high) after an actual 1280x720 screenshot showed the tall initial arrangement reduced text to 57%. The 21 controller tests passed again after that defaults-only change. The frozen interpreter was not edited.

## Correspondence and authoring boundary

This is a common world in a narrow but substantive sense: note n1 in Notes and the committed text shown in Editor are the same record. An unresolved Editor draft is a separate named value, not a second subject silently synchronized later. Notes and Activity enumerate the model's projection rows. Note visuals resolve those row identities back to the same state records for typography, color and coordinates. Text views disclose full content, identity, revisions, position and color; the note card visibly truncates its excerpt. Thus they represent the same state but do not claim pixel-for-pixel or viewport-complete equivalence.

Authored rules own selection/draft binding, body save, draft state, placement formulas, tag replacement and color policy, creation classification, window positioning, acknowledgement and explicit reopen. JavaScript remains responsible for action vocabulary/admission, identity allocation and removal, revision/CAS checks, accepted-event append, program installation, and projections. The HTML/CSS and input binding are also host-authored. Changing arrangement spacing genuinely changes future note positions without changing adapter code; that demonstrates transferable policy, not an entire application authoring foundation.

One discovered projection issue makes this boundary concrete: the authored Together summary did not update on create. The first interface showed 'No shared changes yet' above an actual create event. The displayed Activity header now derives the latest accepted event summary, while As text retains the separately named authored summary. This is explicit host projection policy. It has not been disguised as something the frozen interpreter supplied.

## Continuity and conflict policy

The Editor textarea is a persistent DOM node. Rendering another window does not reconstruct it; unchanged draft values are not assigned back, preserving selection and focus. Note/window drags hold the input coordinate scale, shared revision and target revision captured at pointerdown. Temporary motion changes only the DOM until release; release requests one action with those original guards. Pointer cancellation discards the temporary position. Arrow-key movement is an explicit action with a fresh target guard. This is one local browser interaction model, not a multi-pointer or composition-system proof.

All note properties share one subject revision. Consequently Arrange or changing tags can make an existing text draft stale, even when its body has not changed. The conservative save refuses and keeps the exact draft. Initial dirty-selection refusal then stranded that draft: preserving the string was not useful recovery. My critique led Foundations to add `reload-editor` with required `discardDraft:true`, running an authored rule that rebinds current saved text and revision. The visible button says **Reopen saved (discard draft)**. This discards the draft explicitly; it does not rebase, merge, or preserve the person's intent automatically. Separate text/geometry revisions remain a live design question.

Draft/select/reading position are local actions and cannot smuggle material writes through rules; Media found and Foundations fixed that admission bug. Actor labels provide attribution only. The model is not an authenticated multi-user service.

## Persistence boundary

Save note accepts a local model action. **Save desk** explicitly checkpoints the entire document and installed program through root's separate `/api/round4` bridge. The checkpoint includes the explicitly marked editor draft; it is not a filtered shared-state replication protocol. Loading refuses while a dirty draft exists. A load started before another edit cannot overwrite that edit: response adoption requires the current document to remain the exact object captured at request start. A save response similarly distinguishes its saved snapshot from newer local edits made during the request, retaining and labeling those edits as local. These async identity guards are source-reviewed protections; absent a controlled delayed browser test, they are not claimed as independently exercised race evidence.

The bridge uses whole-document compare-and-swap. It does not persist one native desk operation per gesture, replay arbitrary external effects, or supply collaborative editing. Claude's inspected `Desk.do` integration is materially different.

## Reading and peer exchange

Read Claude's `desk-shell/OWNERS.md`, `core.js`, and app sources `notes.js`, `editor.js`, `third.js` in a combined read; output truncation means this is selected source coverage rather than a complete line-by-line audit. It grounded the contrasts around appearance versus subject IDs, Editor draft continuity and revision guards, and Together's shared row model and evidence limits. I did not modify or enter Claude's shell/session. Source findings do not establish Claude's live behavior.

On our actual team desk I read Media a126 and Foundations a128 in full, then wrote substantive replies c135 and c136. My note a138/s137 records the interface result and failed pressures. The immediate desk friction was concrete: `look :3` still cuts note bodies, so substantive review required `read`; Experiments now reports cramped 69px rows. This is observation of our working medium, not a simulated future UI.

Media's strongest challenge remains unanswered: one subject shown twice should share text but have independently movable appearances. Our note record combines subject and one placement. We explicitly fail that pressure; the UI names one placement per subject. Preserving two panels over the same subject is a narrower result. Foundations correctly challenged the opposite overstatement: host mechanisms do not make authored arrangement meaningless, because the changed formula demonstrably changes behavior. The defensible result is policy transfer plus an exposed host boundary.

## Evidence and limits

Locally executed: `node --check app.mjs`; Foundations' 21 controller tests rerun after initial-layout change, all pass. These check shared literal text, installed rules, refusal paths, dynamic creation classification, history scope, explicit recovery and frozen interpreter identity. They do not prove browser input delivery.

Coordinator's actual browser observations, reported during this round: Save note updates Notes and Activity; a dirty draft survives Arrange; stale Save refuses with exact draft retained; creating n4 applies authored NEW classification and records rule provenance. The original tall layout was rejected using an actual screenshot and replaced with the side-by-side default. Final rule-edit, recovery, viewport and checkpoint observations belong in root's evidence record; this report does not infer them from the model tests.

Unresolved or unsupported: duplicate appearances, rich text, anchored comments, automatic merge/rebase, general undo/redo, arbitrary user-defined application structure, live presence, authenticated actor identity, multi-browser per-operation synchronization, and a comfortable narrow-screen editing layout. Fit on a narrow screen is an overview; 100% plus scrolling preserves readable local scale. Rule source and note body remain plain text controls. Google Docs/Photoshop equivalence is not claimed.


### Final coordinator browser report, after layout correction

Root reported the final actual 1280x720 run with the side-by-side desk at approximately 96% scale, screenshot `review/round4-commonplace.png` in the task visualization directory. Actual UI results: Save note updated both views and Activity; Arrange retained the exact dirty draft and stale Save refused; explicit reopen restored committed text; keyboard moved n2 and pointer drag moved n3; checkpoint s02 revision 1 and reload restored content and all four accepted events. A preceding rule-editor interaction changed spacing 150 to 210, then Arrange produced x positions 20, 230, 440; newly created note received NEW classification. Root reported no JavaScript console errors. This is attributed browser evidence from the coordinator, distinct from my syntax/controller checks. Root owns the full browser report and Media the independent screenshot review. The interface is frozen after these checks.
