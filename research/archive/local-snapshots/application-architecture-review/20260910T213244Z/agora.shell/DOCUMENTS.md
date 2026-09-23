# Documents
Native core.title/core.text content with studio.document marker. UI selection/open state is shell.documents-ui / studio.documents-ui. Per-document serialized saves debounce 550 ms, drain on switch and safe package reload. Conflicting native content is refused, not overwritten; copy local edits before manual reload. Ctrl+B formats selection, Ctrl+S saves. Uses the existing vendored Marked/DOMPurify allowlist. documents.js/css are editable module sources inlined into index.html for the self-contained browser-1 entry.

Research extension: Sources controls sources-url/import/list/preview/text/use/excerpt/quote. Native facets studio.source and studio.citation. Importer package studio.research; see its installed research-sources skill. Citation writes join document save transaction; imports are independent. Recent workspace event diagnostics record real browser edit/navigation/import/save timestamps (last 50; not durable).

On a gateway stale-input-snapshot refusal the UI retries import once, without retrying document writes. Ongoing editing can exhaust that retry; the UI keeps drafts and asks for a manual retry. This runtime currently invalidates action snapshots on unrelated writes.

Source URL/excerpt/selection drafts persist natively as shell.sources-ui / studio.sources-ui (250ms serialized CAS, drained before import and safe update). Browser localStorage is not relied upon: the installed sandbox did not retain those drafts across reload. Native source content remains separate.


Citation review: retained native studio.citation-proposal + studio.citation-history, installed studio.research refresh_source/prepare/apply/dismiss actions. See studio.research/review-usage.md and REVIEW-VERIFICATION.md. Review UI reuses the current editor save queues, drains before apply and safe update, preserves drafts and does not auto-apply. Refresh now uses declared source-only reads; the previous runtime-global invalidation note above is superseded for the revised importer/review actions.

Research packets: RESEARCH-PACKETS.md. Async native preview/apply, native packet drafts, 1–8 document selection, imported collection navigator and literal citation/history display. Existing editor/source/review writers retained.


Round 5: comments use the existing stable editor and save queue. Native actions are studio.comments; threads are studio.comment-thread. UI captures an exact saved UTF-16 range before create/reanchor, retains per-document/per-thread drafts in shell.comment-ui, and refuses locally stale captures as well as gateway stale native revisions. Comments are literal text, not mentions/notifications/authentication. documents.js and documents.css now assemble through manifest ui.scripts/ui.styles markers; no manual inlining step. See native Document doc-r5-handoff and installed anchored-comments/research-packets skills.
