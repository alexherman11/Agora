# Citation review: verified integration
Isolated Agora world, 2026-09-10. All scratch stayed under /root/agora-bootstrap/review.
Installed native extensions augment the inherited Documents editor and studio.research importer; no platform/host edits.

## Live browser + native checks
- Candidate Python: blank/non-source prepare refused without writes; real HTTP revision-3 refresh returned one proposed source change and preserved revisions 1/2. Candidate UI rendered without script errors or horizontal overflow. Its draft-write refusal was expected (read-only candidate), not a live failure.
- Selected coastal source refreshed from /sources/slow?version=3 in live Documents. Browser trace: refresh-start 03:37:29.998Z; first editor input 03:37:30.759Z; save committed 03:37:31.339Z; refresh-success 03:37:31.819Z. Native events: alpha editor save 240; unrelated review-concurrency-probe write 241; source refresh 242. No stale-snapshot retry was needed. This establishes actual overlap, not an inferred concurrency claim. No other archive data was read into these actions.
- HTTP 503 /sources/broken showed an error, created no source revision, and retained editor, source evidence, review draft and chat draft. Wrong-source orchard URL was refused for selected coastal source. Original importer still succeeded from the UI with orchard, preserving its revision-1 evidence.
- Blank action input and non-source UI replacement were rejected, with no proposal or document write.
- Prepared preview was visibly old revision 1 vs proposed revision 3, including quotations and attribution. UI dismissal retained a dismissed proposal and did not modify documents/citations.
- Two prepared proposals survived real reload; excerpt and original unsent chat draft survived.
- Genuine browser intervening author edit advanced alpha to revision 3 (event 253). Applying its stale proposal together with beta's valid proposal returned conflict; alpha retained the author edit, beta stayed revision 1/event 222, both citations stayed revision 1/event 222, both proposals stayed prepared. No partial batch.
- Dismissed stale batch and prepared again. UI applied two new proposals. Both documents, both citations (including old-history entries), and both proposal statuses committed at the SAME event 259. Only citation spans changed; original paragraphs and author edit remained.
- Native repeat apply returned applied=[] and already_applied=[both IDs], transaction=null. No duplicate quotations.
- At 390px: no horizontal overflow or script errors; editor was usable, Ctrl+B formatted a selected test phrase and Ctrl+S persisted it. The temporary keyboard test text was then removed through the editor. Review source-text selection, Use selected source text, and keyboard Enter on Prepare created a real pending preview. Reload retained it.
- Original Field guide / Trip plan, note facets, presentation rules, citation evidence and unsent chat draft are checked separately against focused starting snapshots. Only the two requested review documents were updated, with explicit verification paragraphs in alpha; unrelated probe is a new isolated core.text object.

## Independent review left ready
Pending: proposal-ed3ea020-a444-44b7-9020-d794ee8cfe5b
Field guide, citation-679e827e-a1a4-473f-901c-2de3e2e12502, old revision 1 vs current revision 3.
Read its saved old/proposed previews, check only that proposal, then Apply or Dismiss.
This has NOT been applied; Field guide remains unchanged.

## Repeatable tests
test_review.py + existing test_import.py run against real fixture HTTP and disposable in-memory object contexts, not live documents.
Coverage: atomic two-document success; original evidence; repeat apply; blank/non-source; cancellation; document/citation/source conflicts; duplicate/ambiguous locations; wrong identity/HTTP failures; importer identity/hash/reimport, malformed payloads and version retention.
Run within an authorized guest scratch directory containing these retained package files:
python3 -m unittest -v test_review.py test_import.py
Live assertions above are distinct from these source-only tests.

## Friction and next improvement
- Registry package.list includes full source-bearing package records; use focused package.get, summarize locally. Initial package.list output was unexpectedly large.
- Schema dialect rejects uniqueItems; actions deduplicate proposal IDs themselves. package.install expected_revision is the INSTALLATION revision, not source revision; inspect agora.installation.<package>. Initial mistaken pins were safely refused, then corrected.
- Browser interaction returns before an async action finishes; tests must await status/native records rather than interpreting click completion as a committed transaction.
- Source revisions are opaque strings: "outdated" means revision/hash differs from current retained source, not numeric sorting.
- Prepare/apply use declared unions of research facet collections; refresh uses the selected source ID alone, importer the source collection, dismiss only requested proposal IDs. Non-research changes cannot invalidate them. Research collection actions refuse beyond 1000 matching objects; they do not truncate. Concurrent changes to another object in those declared research collections can still refuse prepare/apply; re-review/retry manually, never auto-rebase document writes.
- Whole citation Markdown must occur exactly once. Edited, missing, duplicated or overlapping citation blocks require manual review, not approximate replacement.
- Proposals/history/versions are retained native records, preserved by these actions; they are not access-controlled immutable storage against arbitrary authorized world.transact.
- Next machinery: relationship-aware declared reads (selected proposals -> referenced citations/documents/sources) to narrow apply's dependency set and avoid collection-sized guards. UI still uses filtered polling, not durable subscriptions.

