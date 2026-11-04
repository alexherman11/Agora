# Search interim rejected: projected-label dependency correction

For JEFF/House independent re-review. **Prior lexical interim rejected by independent review dk1757, as reported by JEFF. No feature approval, landing or activation. Semantic acceptance remains held; parent incomplete.** Generic House passed metadata is not feature approval.

## Corrected dependency

`research/kernel-lab/kernel/words.py`, inside `search()` only:

- Result labels now use the caller-visible projected title/label/name/word, then the constant **Untitled result**. Removed the raw `k.name(t)` fallback and the label helper's identity argument.
- Related-view `shown in …` snippets use that same projected-only label. A private view name cannot reappear through a child result's snippet.
- Related-kind expansion now also requires `a.get("kind") == kd` in the caller-visible projection. The raw kind index alone cannot establish a related match when the kind field is private.

No other kernel function was edited. Text matching and ordinary snippets continue to consume only projected fields.

## Secondary-path audit

| Path | Read/corrected evidence |
|---|---|
| Direct labels and text receipt | Both use the projected label helper; text receipt renders the resulting row, without raw label lookup. |
| Body snippets | Join `SEARCH_TEXT` fields only from `visible()` / `k.shown`; private text does not enter matching or snippet construction. |
| Related view label | Uses the corrected helper; synthetic regression covers a view matched by kind with all its naming fields private. |
| Related view expansion | Reads projected view text; requires visible child kind and naming fields. Private lens text cannot cause expansion. |
| `find <words>` | Existing `rows()` dispatch enters the same corrected search function before generic row formatting. Synthetic alias regression exercises it. |
| Kind, lane/status and ordering | Search uses the projected row for display/filter/rank values. Private kind cannot justify related classification. IDs/revisions remain identifiers/fences, not fallback names. |
| Interim component | Installer, evidence-only lens and `lexical.js` unchanged. UI renders returned search name/snippet as text and uses the previously reviewed fresh identity/revision check. No new UI execution claim. |
| Separate `board.search` | Read `research/community-app/board/board.py`: post title/text and document/file labels come through its rows/file-read transport; document label has a neutral Document default. This separate route was not executed, changed or approved here. |

This is a search-path correction, not a claim that every label renderer or every projected/derived field throughout Agora has been audited.

## New synthetic regression, not denied-fixture retries

Added `research/smart-search-lab/check_search_projection.py`. It runs real `Kernel.shown`, `search` and `find` functions on synthetic `State` objects with two principals. It never calls persistent `Kernel.__init__`, creates a world/keep/seal/account, uses a temp fixture, opens a browser or reads evaluator fixtures. `k.name` is wrapped so any raw fallback is detectable.

**Ran before correction:** pinned Python `-B research/smart-search-lab/check_search_projection.py`: `Ran 8 tests in 0.007s`, `FAILED (failures=6)`. These reproduced private direct/alias/view labels and raw-kind related expansion. They were assertion failures, not denied operations.

**Ran after correction:** same new in-memory regression: `Ran 8 tests in 0.004s`, `OK`. Coverage includes private searchable fields, safe fallback, visible labels, related snippets, private lens text/kind/name, revocation, forgotten records and inherited document-parent privacy. No evaluator sealed data was accessed; no denied filesystem test was rerun or relocated.

Existing UI/broker contract counts remain historical. No actual broker inference, grants, activation, host click or generic full-suite validation was performed.

## Frozen re-review input

`projection-review-manifest.json` freezes the corrected whole kernel dependency, projection/parser/history/store dependencies, unchanged interim component/lens/installer, exact painter/widget inputs, prior interim manifest and new regression/freezer. It records exact raw bytes plus normalized UTF-8/LF hashes for House reconciliation. Previous manifests remain unchanged.

| Artifact | SHA-256 |
|---|---|
| Corrected `kernel/words.py` | `5e18883922ef9032853906e197a5eafb5c939cdf37e28040193e00c063dbe982` |
| Prior `correction-manifest.json` | `24582891fad56ba40b135be0acb020b73527d46f17b9bade0938fd913d0cb256` |
| Interim component, unchanged | `1f2873c462e24d45989f7133cad32ddbe844e708dd4d56c2cea6a10227d7937c` |
| Evidence lens, unchanged | `ed1ed2de5a6c7d83b06496b382a3c7e4d1bc8137629d24f4e8f001c7e9884f7a` |
| Generated widget, recomputed unchanged | `0e05c6ee58a3d11eeb3953d7065aec613c9f61e2f02ad09b0a44eb97ed3bd0f3` |

Ran pinned Python `-B research/smart-search-lab/freeze_projection_review.py`, exit 0. It verified unchanged interim hashes and recomputed the generated-widget code hash without a Door or live authoring. `git diff --check` exited 0.

## Board/Documents overlap and next action

`kernel/words.py` is a shared dependency: its `rows/find/search` words serve Board/Documents and the interim. The correction touches only search's label/related expansion block. `kernel/kernel.py`'s `shown()` and inherited `visibility_of` handling, `community-app/board/board.py`, Documents/file processing and adjacent generic kernel words were left intact. The regression includes document-parent privacy, but does not approve those features.

JEFF/House must reconcile this shared dependency serially with Board/Documents work; preserve their changes. If that reconciliation changes frozen bytes, freeze the reconciled candidate and independently re-review it. No merge, landing or activation is authorized in this round.

**Parent next action:** obtain independent feature re-review of the corrected kernel dependency together with the frozen lexical interim. Prior rejection remains the approval state until that review passes. No grants, model adoption or inference. The parent semantic discovery goal remains open.
