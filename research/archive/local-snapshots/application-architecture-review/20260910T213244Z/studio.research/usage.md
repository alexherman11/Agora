# Research Sources
Import through tools.list / live discovery, then invoke the installed revision:
action.invoke {"package":"studio.research","action":"import_source","revision":2,"args":{"url":"http://127.0.0.1:8860/sources/coast"}}
Discover again after installation; never assume revision 2 stays current.
The guest fetches HTTP(S) JSON with id/title/author/published/revision/content (nonempty strings), max 1 MiB response / 100,000 text characters and 12-second timeout. No accounts or credentials are used.
ok:false contains useful error and proposes no writes. Conflicting concurrent writes are refused by native CAS; retry import.
Identity is final URL origin + external id, not URL path: /slow and /coast reuse one source.
studio.source retains latest metadata plus immutable content/revision/hash snapshots in versions. SHA-256 hashes UTF-8 text. Old snapshots remain when a source changes.
Documents Sources UI uses this exact action. Select raw source text and Use selected text, or paste an exact substring into Excerpt; Insert quotation appends readable Markdown (never replaces existing document text). It queues studio.citation with document_id/source_id/source_revision/content_hash/quoted_text/citation_markdown/created_at in the editor's existing 550ms save path; document and citations commit together. Citation records are historical insertions, not a maintained assertion that an editable quote remains in the document.
Errors retain editor and excerpt drafts. Imports do not block editing/navigation/chat. Source URL, source selection and excerpt are native drafts in shell.sources-ui / studio.sources-ui; canonical sources/citations are native data.

The importer now declares a studio.source-only read query. Unrelated native writes no longer invalidate it. The inherited UI retains a one-retry fallback for native snapshot refusals. Native agents may retry the same import on that refusal, after checking current state; identity remains stable. Continuous unrelated writes may exhaust the retry. Tests: python3 -m unittest -v test_import.py (fixture service required; simulated context only, no native writes).


Explicit citation review is installed. See review-usage.md and REVIEW-VERIFICATION.md for actions, schemas, selectors, real tests and limits.
