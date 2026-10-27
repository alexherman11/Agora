# Integration preflight — 22 October, c10796

Reviewed candidate remains inactive and byte-identical; no production source or
world policy applied. HEAD25b7caa, current main09ef253. Full integration/health
must follow the supported prepare receipt, not run on this older base.

Ran pinned Python test_candidate.py: 16 tests OK, 0.603s.
Ran replay.py: fixed718-record interval e26500–e27216, transition notices13→9,
captured other-route comparison48→50; zero captured questions, six human-route
events. Transition assertions pass; other-route figures retain the original
captured comparison's evidence limits. git diff --check exit0.

Hashes:

| File | HEAD/base SHA256 | current main SHA256 |
| --- | --- | --- |
| house.py | 535e71a34f28f26badaaf0a74e3ea0bdb1574ad38b121d813ded6cd35c9d3d59 | 9ec463f3552eb30dd7b15684823c1dc089d2cae7f189a71bab4119921b61a390 |
| task_flow.py | ce9c8676c896ddca7eda3aa1a476f94dd73741ba45c788283a858ad1236f944f | same |
| rooms.py | d5f9bc7a78f795ab3bd97f992b9c7b20835efe362fda3800b836d34ab985d3a0 | same |
| resident_continuity.py | cd3dde7ccf05b27c1899d736d3014520378b6f4b114dae47d52abeb8d8480b0f | same |

Read main's house diff: independent guard sampler lifecycle at House.run,
outside reviewed news()/routing hunks. Ten paths changed overall, including
grid-fill painter/tests and guard source/tests/docs. No semantic overlap found
in inspected wake hunks; do not replace whole main house with candidate output.
No claim about unlanded voice-safety work in another worktree.

Correction to initial investigation: the continuity file is
resident_continuity.py, not continuity.py. An initial git show of the nonexistent
short name failed128; corrected path above was then hashed against both refs.

Preserved candidate.patch raw SHA256:
ff3323ba3ba8515f7c92c9c1b2885a7a228de656c7000d0a0a7b9670b544c714.
Manifest raw:
b1cf2780706a1540feee2ec22b116b693a42cf89c7b15c1048b68c562749a37b.
Captured metadata raw:
d0144ceb41225764a412b60ef1ed6d7ac4090e3c3023390bccc3960889a6da42.
Original manifest/stage/patch left unchanged.

Next: commission=prepare, house checkpoints all research/task-wakes artifacts
and merges main under its serialization, no judgment/landing/restart. After its
actual receipt revalidate original reviewed hunks against the merged sources;
preserve guard and concurrent safety changes. Stop on semantic overlap. Then
apply only reviewed routing/queue changes, test actual save-failure/reload joint
inbox/receipt persistence, policy-off compatibility, captured replay and full
health. Report failures truthfully and return to Ibis BEFORE ready.

This preflight is not integrated-current-main acceptance. No live wake, model,
Conversation write, policy enable, ready, landing or restart performed.
