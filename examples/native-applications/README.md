# Independent applications experiment

Notes and Documents are separate, portable browser applications that can open
the same native text object. A generic desktop hosts them without importing their
source or naming either application in its implementation. This is the runnable
slice on branch `experiment/native-applications`, isolated from the active Desk.

Run [Open Application Experiment.cmd](../../Open%20Application%20Experiment.cmd)
on this machine. It starts or reuses its own world on port **8872**, then opens a
browser. It neither starts a guest VM/model turn nor replaces another server.
The PowerShell launcher accepts `-NoOpen`, `-Port`, and `-Python`; it uses a local
repository virtual environment or this machine's existing Agora3 environment.
For another checkout, install the dependencies in `pyproject.toml` first.

Try these workflows:

1. Edit the shared field notes in either application. Both views refer to one
   object; Markdown is an explicit content format.
2. Select text and expand Annotations. The same extension uses the shared editor
   contract in both applications, without reaching into the other application's
   DOM. Anchors are revision-bound and conservatively relocated.
3. Open another view of an object. Each appearance keeps its own draft, selection,
   position and installed build. Conflicting edits expose a retained draft and an
   explicit choice; they do not silently overwrite the incoming text.
4. Export Notes, remove it, then import the downloaded `.agora-app.json`. The
   document and saved views remain. Reopen a closed Notes view on that same object.
5. Install a revised application. Existing views stay pinned until their own
   Update button is used. Other applications and sibling views remain running.

`desktop/` is the generic host. `notes/` and `documents/` are independent entry
points. `shared/` contains one authored editor/extension implementation copied
into each self-contained release by `scripts/application_packages.py`; this is
deliberate vendoring, not a dependency resolver. Documents also carries pinned
Marked/DOMPurify source and its notices for a sanitized Markdown preview.

The demo's portable releases are in `worlds/application-demo/releases/`. They
contain source, a manifest and a SHA-256 digest, never the world, drafts or
credentials. The digest detects corruption; it is not publisher authentication.

See [Application Experiment](../../docs/Reference/Application%20Experiment.md)
for the implemented protocol, evidence and limits. This is a focused application
boundary prototype; the existing research, citation, packet and discussion UI has
not been ported into it.
