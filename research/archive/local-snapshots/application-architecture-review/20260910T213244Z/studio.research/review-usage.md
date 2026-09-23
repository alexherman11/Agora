# Source refresh and explicit citation review

## Native invocation
Call tools.list / discover to obtain the current studio.research installation revision R.
Invoke action.invoke {"package":"studio.research","revision":R,"action":ACTION,"args":ARGS}.
Do not pin the source revision as the installation revision.

Actions:
- import_source {"url":"http://127.0.0.1:8860/sources/orchard"} (existing importer; new identities allowed)
- refresh_source {"source_id":"source-4cb145483e82fc393af71968cd3d1c3a","url":"http://127.0.0.1:8860/sources/coast?version=3"}
  Only changes the selected retained source. Rejects different identity; retains all previous version evidence. Does not write a document/citation.
- prepare {"citation_id":"citation-review-alpha","excerpt":"The team counted fourteen tide pools along the eastern path."}
  Returns ok/proposal_id/proposal and persists the preview. Requires citation older/different from current retained revision/hash, original evidence and a unique exact Markdown location. Blank/non-source excerpts refused.
- apply {"proposal_ids":["proposal-...","proposal-..."]}
  Max 50 selections. Revalidates every proposal before returning any changes. Updates document text + citation provenance/history + proposal status in ONE native transaction. Applied IDs are skipped on repeats, without new writes. Dismissed or ambiguous/duplicate citation proposals refuse.
- dismiss {"proposal_ids":["proposal-..."]}
  Persists dismissed status only; no document/citation edits. Repeats are harmless; applied proposals cannot be dismissed.

Errors: result.ok=false with code/error and no changes for domain errors. Native stale-dependency/CAS refusals may be gateway errors instead; never present either as success. A stale batch requires renewed review: dismiss affected proposals, inspect current text, prepare again. Preserve intervening edits.
Current-source metadata/hash/quote is checked at apply too; refreshing again may require new review. Revision labels are opaque, not monotonic integers.

## Workflow and UI selectors
Documents retains the existing editor, autosave, per-document queues, Ctrl+B / Ctrl+S and safe-update drain.
Source selection/URL: #sources-list, #sources-url. #sources-import remains the original importer.
Review: #docs-review. #review-refresh fetches the selected source from Source URL without locking ordinary editing.
#review-source-text is current retained raw text (readonly); #review-current-meta shows current revision/attribution.
#review-citation lists outdated citations across all documents for the selected source.
#review-old shows old quotation/attribution/revision/hash.
Select a substring in #review-source-text and #review-use, or type an exact excerpt into #review-excerpt.
#review-prepare saves preview only. No prechecked proposals, no implicit approval.
#review-proposals article[data-proposal-id="ID"] contains old and proposed quotation/attribution.
input[data-proposal-id="ID"] checks a pending proposal.
#review-apply atomically applies selected proposals across documents; #review-dismiss cancels selected proposals.
#review-status reports loading/errors/success; #docs-status reports editor save state.
While applying, only target-document editor/title are briefly readonly after flushing their saves. Refresh does not lock editors.
Prepared proposals and excerpt survive reload; checkbox approvals deliberately reset on reload.
Resolved proposal evidence is in the expandable historical section.
#docs-review-open is the Documents toolbar shortcut; #review-to-sources returns to source/URL controls.
All controls use native labels/buttons/textarea/select/checkbox keyboard behavior and wrapping mobile layouts.

## Native facet schemas (schema.list is authoritative)
All are JSON objects with required listed fields and no additional properties unless noted.
- studio.source (existing): identity,external_id,title,author,published,requested_url,final_url,source_revision,retrieved_at,content_hash,content: strings; versions: array of version snapshot objects (existing schema permits generic objects).
  Version snapshots contain revision/hash/content/title/author/published/URLs/retrieval time. Hash is SHA-256 UTF-8 content.
- studio.citation (existing): document_id,source_id,source_revision,content_hash,quoted_text,citation_markdown,created_at: strings.
  Current explicit provenance; historical insertions remain unchanged unless approved by apply.
- studio.citation-proposal: citation_id,document_id,source_id,created_at,resolved_at: strings;
  document_revision,citation_revision: integers >=1;
  old_citation,proposed_citation: full studio.citation-shaped objects;
  status: prepared|applied|dismissed. resolved_at is empty while prepared.
- studio.citation-history: entries: array of {citation: full old studio.citation-shaped object, proposal_id: string, replaced_at: string}.
  Added alongside the current citation at application; existing entries preserved.
- studio.review-ui at shell.review-ui: citation:string, excerpt:string (max 20000); durable pre-preparation draft.
- studio.sources-ui at shell.sources-ui (existing): url,excerpt,source:string; preserved existing source draft.
- Documents stay core.title/core.text with studio.document {"format":"markdown"}. No second editor data model.

## Reads, limits, and tests
refresh_source reads arg_ids=[source_id]; import_source reads studio.source query only; dismiss reads arg_ids=[proposal_ids].
prepare reads union of studio.source/studio.citation/studio.document.
apply adds studio.citation-proposal. Native validates revisions + query membership atomically.
Unrelated archive/note/chat/native changes do not invalidate these declared inputs. A maximum of 1000 matched objects is an honest runtime limit; overflow refuses. Cross-research-collection concurrent changes may still refuse prepare/apply. See REVIEW-VERIFICATION.md for real overlap timestamps, verification and limitations.
No approximate span replacement, scraping framework, durable worker or background refresh schedule is installed.


Portable packet sources: refresh_source now matches external identity and writes ONLY the explicitly selected native source_id, including remapped imported copies. The original canonical source is not edited. Existing current/history/proposal schema and review behavior is unchanged.
