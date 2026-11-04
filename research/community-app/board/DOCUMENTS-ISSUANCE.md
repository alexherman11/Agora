# Seabright Documents: final source and held issuance proposal

Existing task dk1614 / parent dk1498. Proposal for JEFF; **nothing below has
been issued, created, published as runtime source or activated**. `L` is a
placeholder for a separately approved real root, never an invented world id.
The original DELIVERY-RESOLUTION.md and world draft dk1630 remain unchanged.

## Source ready for independent review

The five Documents words now validate the complete library selection before
calling the files provider. Each module in the caller chain must independently
hold an applicable grant admitting that same selection. Aliases use the bound
word. Grants outside the call's location or with an unauthorized issuer cannot
donate scope. An unscoped overlapping grant retains its existing union
semantics: issuance must audit all active grants and aliases.

Each Documents call carries a separate kernel-owned context. Provider reads
allow only plain `rows document-library/document-folder/document-entry/file/post`.
Rows and text are filtered before delivery to the provider. Metadata needs
visible, inherited, same-group ancestry; unrelated libraries, legacy metadata,
hidden/cyclic parents, unrelated files and posts are withheld. Unattached files
are limited to the caller-owned upload targeted by this call; indexed files
and visible post attachments retain their original visibility. Attached
Documents files must belong to this library, even when another library shares
the group. This is a per-call boundary, not a revocation of the existing
provider's independent conversion/rows authority or Board's existing grants.

Provider answers are separately limited at atomic kernel admission to metadata
in the selected library, including when the provider has overlapping library
grants. No attachment, upload mutation, library creation or generic post
delegation is admitted through this path. Name/parent edits preserve ordinary
caller ownership checks. No legacy migration is automatic.

Recovered documents.py keeps dk1561's corrected named library and positional
target declarations. Its folder/entry answers now add `within=L`.
files.py again offers all five Documents words alongside unchanged conversion.
install.py still declares only `rows file-result` for the provider: no broad
make/set installer change. Recovered assets/templates and historical hidden
tests are included for review; the legacy documents_install.py is explicitly
**not** the production deployment contract and must not be replayed.

## Exact held creation and issuance decisions

| Action / principal | Exact proposed words and scope | Existing authority / resolver / evidence |
| --- | --- | --- |
| Create one root as existing issuer Alex dk2, or a separately authorized steward | Proposed contract: `make kind=document-library name=seabright-documents title="Seabright Documents" sees=group in=dk313`. Recheck visible roots before creation; stop on ambiguity. Record resulting real identity as L and its revision, one group dk313, visibility and owner. No widget/draft reset. | JEFF dk1665 names Seabright Documents and Research & documents dk313, but explicitly withholds identity/creation until reviewed contract. Root lookup still returned zero. General dk1703 capacity direction covers this source work, not root creation. JEFF resolves; authorized steward executes separately. |
| Existing provider **files dk288** | One additional grant: words **`make set`**, only **`kind:document-folder,document-entry;library:L`**. No new rows, look, attach, upload or wildcard grant. | Active Alex-issued dk289 is only `rows file-result`, where dk1; it does not cover metadata writes. dk1632 rejects broad make/set; dk1665 holds source/security review and all grants. JEFF resolves exact scope after House review; Alex dk2/existing authorized issuer issues separately. |
| Existing Board widget **seabright-board dk368** | One additional grant: words **`files.browse files.folder files.store files.rename files.move`**, only **`library:L`**. This enforces both browse selection and write-call selection. No `files.*` execution grant, no extra Board make/set. | Active Alex-issued dk446, where dk1, contains none of these five words and no covering files wildcard. dk369 is revoked. dk1665 requires this boundary; source review does not authorize issuance. JEFF resolves; authorized issuer executes separately. |
| Existing Board widget **dk368**, event refresh only | Separate proposed subscription words **`hear:attach hear:files.* hear:file-result`**. These are event subscriptions, not execution permission or a library-filtered grant. Evaluate necessity/data exposure before authorizing; not required to review the provider increment. | Missing from dk446; no current authorization. Board already has `hear:component hear:component-action`. JEFF resolves subscriptions separately, preserving current widget and draft. |
| Proposed standalone Documents widget | **No target identity and no issuance proposed in this increment.** Do not replay legacy installer GRANTS. | dk1561/r3366 execution-confirmed missing `hear:component hear:component-action`; dk1632/dk1665 retain hold. JEFF alone resolves a later exact widget/authority contract. |
| Map on existing Board dk368 | Prior held five reads **`map.layers map.tile map.find map.where map.place`**; no issuance in this increment. | dk1563/r3332/r3376 and JEFF dk1632; existing fixture correction is preserved. Resolver JEFF/authorized issuer. |

All grants above would currently store `where=dk1` under the existing grant
word. Adding `in=dk313` is not an enforced grant boundary. `library:L` supplies
the reviewed identity boundary; never issue it before L exists and the final
source implementing it has separately passed review/publication.

## Exact recovery evidence

Read coordinator evidence, not an old substitute:
`C:/Users/Alex/Documents/Codex/2026-10-22/task-3/world-workers-oct27/documents-published-admission-20261029.json`
and its companion .txt. Candidate
`30f97d32b0593df03444899bb612d79914773e71`, stable=true, historical result
**1 failed, 5 passed in 18.18s**. Failure was narrowed widget readiness missing
`hear:component hear:component-action`; complete UI acceptance remained held.

All three retained files in original worker
`kernel-dk1561-f5d565884a` matched the manifest's exact SHA256 before recovery:

| File | Original corrected SHA256 |
| --- | --- |
| DOCUMENTS-HANDOFF.md | a502714b28b39a900550bf79eb7aec8052c6b0c4326de3be62defd24043c127d |
| documents.py | 11c03b19d622292eb7a50569bd9a7d1f761a942ab0241086d8daa22f1cfa891c |
| test_documents_ui.py | dd3086e8c5b560de4d8d73dabe6a71578fa8b729539c5ca9a23f48c2f4c39672 |

The handoff is recovered byte-for-byte. documents.py is adapted as above.
test_documents_ui.py now gives only its private fixture provider the exact
metadata/library grant and expects the new outer refusal. Its complete
picker/drop/preview/nesting assertions and subscription hold remain.
DOCUMENTS-RECOVERY.json records original verification and final source hashes.

## Review, activation and user verification are separate

Ran memory-only tests with pinned Python: **37 passed in 0.16s**. These cover
outer dispatch, bound aliases, overlapping grants, issuer/location eligibility,
caller chains, hidden roots/parents/files, ancestry/cycles/group boundaries,
provider read refusals, metadata write shapes, caller file ownership and
existing kind/fields/unscoped semantics. They use no disk fixtures/processes.
Existing persisted-world tests gained hidden-parent/file/group cases but were
not run. No denied fixture operation was retried or relocated.

House must independently run persisted-world admission, real published provider
and existing-grant regression checks on this exact source before accepting the
kernel increment. Then JEFF decides the creation/issuance contract above.
Publication and any runtime reload remain separately held; do not stop/restart
anything, replay installers or treat bounded source review as activation.
Original executor lifecycle evidence is still unavailable; refusal #386/#387
only records wrong-target house.stop refusals, not a resolution of that hold.

Calendar/asks read-only evidence remains Board lens dk366 revision 3413 and
channel routing dk310/dk319; prior empty reads are not native owner acceptance.
Original child next actions were reconciled to their existing continuations,
not marked end-to-end Done. No Board lens/calendar/asks changes here.

Design records identify planned website `https://seabright.example.org/`
as the signed-in web entry. The intended deployed separate public demo is still
**unknown**. No private world data was copied. Native versus site visual parity
and native owner verification remain separate unverified outcomes.
