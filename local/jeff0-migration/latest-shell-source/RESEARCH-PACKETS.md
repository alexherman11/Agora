# Research packets v1

Package ID `studio.packets` (native source object `agora.package.studio.packets`). Discover `tools.list` and use its current installation revision, NOT the package source revision.

## Native actions (all via action.invoke)
```
{"package":"studio.packets","revision":INSTALLATION_REVISION,"action":"export_packet","args":{"document_ids":["doc-review-alpha","doc-review-beta"]}}
{"package":"studio.packets","revision":INSTALLATION_REVISION,"action":"preview","args":{"packet_json":"EXPORTED_OR_PASTED_JSON","collection_name":"Research handoff","attempt_token":"handoff-unique-001"}}
{"package":"studio.packets","revision":INSTALLATION_REVISION,"action":"apply_import","args":{"attempt_id":"PREVIEW_RESULT.attempt_id","preview_revision":1,"checksum":"PREVIEW_RESULT.checksum"}}
{"package":"studio.packets","revision":INSTALLATION_REVISION,"action":"cancel","args":{"attempt_id":"PREVIEW_RESULT.attempt_id"}}
```
Arguments are strict objects, no additional properties. Export document_ids: 1–8 distinct strings ≤500 chars. Preview packet_json: string ≤2,097,152 chars AND UTF-8 bytes, collection_name: trimmed nonempty ≤120 chars, attempt_token: 8–128 ASCII letters/digits/underscore/hyphen. Apply attempt_id ≤100 chars, preview_revision positive integer, checksum 64 chars. Cancel attempt_id. Errors return result.ok=false/error/code with no proposed writes; gateway schema/snapshot/CAS refusals may instead be gateway errors.

Export returns packet_json, packet_id, checksum, counts and retains `studio.research-packet` on packet_id. Read with world.get. Export uses only selected native documents and their citation/history/source closure, never packages, chat, unrelated facets or proposals. No action in this package fetches URLs. Text is data, including Markdown that resembles executable code; it is never executed. UI previews use literal textContent.

Preview validates and creates only a `studio.packet-attempt`, not documents or a collection. Read result format/version/counts/titles/provenance/new_native_objects/mapping. Collection names must be new (casefold/trim comparison across all native collections). Apply revalidates the saved packet, preview revision/seal, deterministic mapping and name. All objects plus applied receipt are returned in ONE native transaction; expected_revision=0 on every new identity. A collision with any existing ID refuses the entire transaction, even if that unrelated object wasn't in the declared read set. Native query-membership/revision checks guard target races. Failed/cancelled attempts leave no half collection or documents. Existing source/document IDs in packet input are legitimate original provenance, NOT destination IDs, and are always remapped.

Attempt IDs are `packet-attempt-` + SHA256(ASCII token). Destination IDs are `packet-copy-` + the same 64 hex + `-documents-N`, `-sources-N`, `-citations-N`, `-history-N`, or `-collection`, indexed from 0. Reuse the SAME token/input to retry preview; reuse the SAME attempt/checksum to retry apply, including after reload or an uncertain response. Applied retries return original mapping and already_applied=true with no writes (even if the first preview revision is supplied). Different input/name under the same token refuses. Cancelled attempts cannot apply. A deliberately new copy requires a new token and unused collection name. A stale saved preview or newly occupied target name requires a fresh attempt. Cancel only marks the attempt; it never deletes applied copies.

## Format and checksum
Strict JSON object, no duplicate keys, NaN/Infinity, invalid Unicode, unknown properties, unsupported version, or non-JSON input. Top-level keys exactly:
`format, version, exported_at, documents, sources, citations, history, checksum`.
format = `agora.research-packet`; version = integer 1. All entity IDs are unique across all four arrays, local to the packet; nonempty strings ≤500 characters.

- documents: `{id,title,markdown,provenance}`; title ≤500, markdown ≤100000 characters.
- sources: `{id,source,provenance}`. source keys exactly identity, external_id, versions plus the version keys below. Only referenced sources allowed. Export includes each source's current snapshot and all snapshots needed by current AND historical citations; unrelated old source versions are intentionally not part of the packet.
- version keys: source_revision, content_hash, content, title, author, published, requested_url, final_url, retrieved_at. All nonempty strings; content ≤100000 characters, others ≤2048. versions includes the current revision/hash pair and all required evidence pairs. Each pair is unique. content_hash = lowercase SHA-256 of exact UTF-8 content bytes. Metadata/URLs/timestamps are retained as provenance and never fetched during export/import.
- citations: `{id,citation,provenance}`. citation keys exactly document_id, source_id, source_revision, content_hash, quoted_text, citation_markdown, created_at. IDs resolve within packet; revision/hash resolves an included source version, and nonblank quoted_text must be an exact substring of that evidence. quoted_text ≤20000, citation_markdown ≤100000, other fields ≤2048 chars. Editable Markdown need not still contain a citation: these are historical insertion records, not an assertion that an author hasn't edited the quote.
- history: `{id,citation_id,citation,original_proposal_id,replaced_at,provenance}`. citation_id resolves an exported citation; historical citation resolves the SAME document and retained source evidence. original_proposal_id is EXTERNAL historical provenance, not a packet reference or active proposal; no proposal content/status is exported. Import makes an inert `studio.packet-history-event` object for each history identity; citation-history.entries[].proposal_id points to that new event, not an original proposal. The original proposal ID remains explicitly recorded on the inert event. Old source IDs/document IDs in all snapshots are remapped. Attached studio.citation-history stays on the new citation object, compatible with existing review.
- provenance: 1–16 records `{original_id,native_revision,written_by}`; positive integer revision; strings ≤500. Imports store this in studio.packet-origin.chain; re-export appends the current native identity. This records claimed provenance, NOT verified authorship.

Overall checksum is SHA-256 of ASCII bytes of the entire top-level object EXCLUDING checksum, serialized in Python as:
```
json.dumps(value_without_checksum, sort_keys=True, ensure_ascii=True,
           separators=(',', ':'), allow_nan=False).encode('ascii')
```
This is the documented Python canonicalization (including its Unicode escaping), not a claim of RFC 8785 compatibility. Arrays keep order. Whitespace/key order in pasted JSON does not matter. Recomputing the overall checksum does not bypass relationship or source-content validation. Checksums detect inconsistency; anyone may recompute one, so they do not authenticate an author.

Bounds: 2 MiB UTF-8 packet; 1–8 documents; 0–16 sources; 0–64 citations; 0–64 history entries; 1–16 versions/source, ≤64 total versions. Maximum apply: 8+16+64+64+1 collection+1 attempt update =154 transaction changes (native cap 200). Native declared read snapshots cap at 1000 matching objects and refuse overflow, never silently truncate. No attachments, sharing/authentication, merge, general embedded Markdown link rewriting, or automatic old proposal application.

## Native schemas
See `schema.list`: new facets studio.research-packet, studio.packet-attempt, studio.packet-origin, studio.packet-history-event, studio.packet-collection, studio.packet-ui. Existing studio.document/core.title/core.text, studio.source, studio.citation, studio.citation-history, core.collection are reused without schema changes. Manifest input schemas are the authoritative machine-readable action contracts. `packet.py` implements the exact v1 structural/semantic validation above.

## Documents UI selectors
`#packets-open` opens/reaches `#packets-area` in `#docs-packets`. Export checkboxes: `[data-packet-document="doc-review-alpha"]`, `[data-packet-document="doc-review-beta"]`; `#packets-export`; `#packets-retained`, `#packets-load`; `#packets-json`, `#packets-copy` (select then Ctrl+C/device copy); `#packets-name`; `#packets-preview`, `#packets-summary`, `#packets-status`, `#packets-attempt`; `#packets-apply`, `#packets-cancel`, `#packets-new-attempt`; `#packets-collections`, `[data-packet-open="NEW_DOCUMENT_ID"]`. `#docs-citation-evidence`, `#packets-evidence` display current and historical citations for the selected editor document. Existing #docs-list/#docs-editor and sources/review controls remain unchanged. Packet draft (JSON/name/token/selection/attempt/open state) persists in shell.packet-ui, drained by safe shell update. Changing input disables apply until a new valid preview; cancel the old preview then use New copy / attempt. Packet controls alone are busy-disabled; editor/navigation/chat remain available.

Imported source refresh uses studio.research.refresh_source with the imported source_id and an explicitly supplied URL. That action compares external identity then updates only the selected native source object, retaining its versions. This refresh does fetch by explicit request; packet operations never do.
