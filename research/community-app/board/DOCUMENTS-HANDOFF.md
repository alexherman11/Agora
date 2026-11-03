# Documents

Builder draft, updated 29 October 2026. Baseline review and four offline tests
passed per the coordinator; hidden UI acceptance remains pending.

`documents_install.install_documents(door)` installs a standalone Documents lens,
widget and taskbar entry without opening a window. Install the board channels
first. Install/reload the `files` module from `install.modules()` so it offers
the additional words with `rows file-result make set` grants. Imports have no
live effects. Nothing starts a phone service or network listener.

`documents.lens` is the shared arrangement. It uses five reusable, discoverable
components: `document-library`, `document-toolbar`, `document-upload`,
`document-list`, `document-entry`, plus the existing `file` and `table`.
The `file.target` setting allows an entry to point to its file without pretending
that the entry is itself an uploaded file.

## Board integration

The routing worker owns the board. This change does not edit `board.lens`.
Its Documents route needs this part, under its route condition:

```text
documents : column, of tag:document-library, prop:name=seabright-documents as library, each documents-view
```

The host must also append the shared template declarations returned by
`documents_install.templates()` to its lens text. These are the same declarations
used standalone; do not fork them. The current arrangement language has named
templates, rather than cross-lens includes, so the routing line alone cannot
import them. Grant the host widget `files.*` (the existing board already grants
upload, attach, file-read, make and set). Initial view keys are
`documentsFolder=""` and `documentsOpen=""`. Watch `hear:attach`,
`hear:files.*` and `hear:file-result` alongside the existing make/set watchers.

## Behavior and extension

Folders and entries are ordinary world things, scoped to the library's channel.
Moving a folder validates its destination and ancestors; cycles and crossing
libraries refuse. Kernel admission checks who may change the entry.
Entries carry names independently of immutable upload records.

Picker and drop use the same upload function. Conversion uses `files.convert`
through the existing upload door. New uploads start private. The UI creates an
entry owned by the uploader, then uses ordinary `attach` to share it with the
entry's channel. If the attach fails, Finish sharing retries that explicit action;
the private original is retained. No file is deleted.

Files already attached to posts in Research & documents appear at the library
root. Filing one creates an index entry without reattaching it, so its original
post link and permission inheritance survive. Its named From post disclosure
shows the visible source post text; this does not open a separate board thread.
A file whose source becomes hidden disappears from browsing and file-read
checks current visibility again.

`phone` is an empty authored slot next to upload and listing. A future phone
uploader can feed the same store/attach flow. This work creates no endpoint,
QR token, listener, camera request or new transport.

Each component declares named parts. Examples:

```text
personal-view seabright-documents documents-view.title="Our research"
personal-view seabright-documents tools.labels.ui="{\"newfolder\":\"New folder\"}"
personal-style seabright-documents target=document-entry padding="16px"
personal-style seabright-documents target=document-upload.drop background="#edf3ed"
```

Colours, spacing and widths use `documents-*` tokens with light defaults.
Preview reuses the file component: photos, extracted document text, tables,
audio/video and downloadable originals. PDF graphics remain outside its reach.
Close the window to stop viewing; the ordinary widget off switch also applies.

## Review

`test_documents.py` covers the upload-folder-find workflow, renaming and moving,
cycle/cross-library refusal, visibility of post attachments, and member write
admission. `test_documents_ui.py` uses the existing hidden driver for actual
drop/picker byte transport, converted preview, nested compilation and personal
handles.

`test_published_document_word_arguments` independently starts the real files
module in the private fixture and routes all five document words through the
authenticated door. It checks named-library browse/create, positional
store/rename/move, missing-target refusal and invalid-library refusal without
opening a browser. Direct `call()` tests do not exercise published admission.

- Baseline checks: the coordinator reports normal House review passed the
  current-main candidate `30f97d32b0593df03444899bb612d79914773e71`.
  This is not feature UI acceptance.
- Feature checks: the coordinator's supported per-command run in private
  worktree scratch reported **1 failed, 4 passed in 9.20s**. The four offline
  documents tests passed. The UI test failed during setup, before upload,
  because `install()` stored a verb referring to unpublished `board.feed`.
- Correction (read/static): the UI fixture now starts both modules from
  `install.modules()` and waits for each offer through the scratch host before
  calling `install()`. This follows `proof.Proof`'s module readiness barrier;
  `ui_live.py` likewise waits for board publication before installing stored
  lines. All drop, picker, preview, nesting and personal-handle assertions remain.
- Subsequent feature run (retained synthetic output read): **1 failed, 4 passed
  in 27.47s**. Module startup passed; the UI reached `Page(...)` but its frame
  body remained empty while waiting for the uploader. `/door/stream` and favicon
  requests were blocked by the hidden browser guard. Those logs do not establish
  causation and the guard was not changed.
- Startup blocker (read/static, not browser-confirmed): `painter.js` awaits
  `make`, `set`, `forget`, `undo`, `component`, `component-action` subscriptions
  before its first `refresh()`. Documents' existing widget grants omit
  **`hear:component hear:component-action`**. The broker calls
  `Principal.hears()` and refuses absent subscriptions. Working writing, map and
  board installers include both. This source path can stop the initial render
  before any document component mounts.
- Added early UI fixture checks for installed gallery parts, the compiled plan's
  expected counts, stopped/quarantined/untrusted components, the browse reading,
  and required subscriptions under the widget's own `Principal`. This reports
  the setup/authority blocker before a generic browser timeout. The actual
  drop/picker/preview/nesting/personal assertions remain unchanged.
- Authority action stopped: this follow-up prohibits new grants. Neither the
  widget grant specification nor any live grant was changed. The coordinator
  must authorize the exact missing hear capabilities before their addition.
  Whether the readiness assertion reaches and reports them is still pending. These two
  capabilities subscribe to component review/recovery happenings; they add no
  file, native, network or mutation permission.
- UI remains pending. No new execution was attempted in the worker sandbox.

Earlier diagnostic run (coordinator-reported): **1 failed in 10.87s**. It
failed before creating the `Principal`: `accounts["alex"]` raised `KeyError`.
The painter fixture's `"alex"` signer maps through its existing LocalEntry
session to account `"desktop:alex"`. The diagnostic now resolves `f.token`
with `f.d.entry.check`, then maps that session's account to its existing person,
as the authenticated door does. It asserts this is the fixture person session;
it creates no account or agent and changes no authority.

Latest readiness run (coordinator-reported): **1 failed in 10.34s**. The existing
account mapping, component trust/health and lens compilation now pass.
`Principal.run("files.browse library=...", mode="see")` refuses with “needs a
thing, by its id,” before subscription checks.

Narrow correction (source review only): kernel `takes_id()` treats any literal
`<id>` in a usage declaration as a positional-target requirement.
`library=<id>` therefore wrongly required a positional target for `files.browse`
and `files.folder`. Conversely, `<entry|folder>` did not declare a target for
rename/move, so admission would clear a parsed id. Document declarations now use
`library=<library>` for named arguments and `<id>` for the positional file/entry
in store/rename/move. No global admission code changed. The module's existing
viewer-visible library lookup, parent/cycle checks, caller-narrowed reads and
ordinary make/set admission are unchanged.

Added the real published-word regression above; retained the narrowed browse
readiness check and complete picker/drop/preview/nested/personal acceptance
test. Neither this correction nor the new regression has been run by the worker.
The coordinator should run the published regression and readiness/feature test
through supported per-command approval. The diagnostic has **not yet reached
`Principal.hears`**. Missing `hear:component` and `hear:component-action` remains
a source hypothesis, not execution-confirmed. UI acceptance is pending; any
separate authority gate remains for the coordinator.

The original worker run was blocked by WinError 5 during pytest fixture setup.
No previously denied operation was retried, and no tests were executed by the
worker for this correction. No live install, new grants or lifecycle repair was
performed.
