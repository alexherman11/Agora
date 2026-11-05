# Incomplete round 1 evidence

Captured 4 November 2026 in worker worktree kernel-dk2599-6cf36a9cb0.
See [the audit](../../ROUND1-AUDIT-20261104.md).

| File | Meaning |
| --- | --- |
| calendar-baseline.txt | Hidden calendar attempt: four setup checks, then browser startup failure |
| calendar/calendar-proof.json | Those four checks only; empty screenshot list, not a UI acceptance result |
| browser-stderr.txt | Exact Windows IPC access denial from one diagnostic with unchanged browser flags |
| world-checks.txt | Aggregate pytest harness failure, including inaccessible temporary directory; not a successful suite |
| calendar-world.txt | Direct existing calendar world probe: 24 checks, exit 0 |
| asks-world.txt | Direct existing asks world probe: `ASKS PROBE OK`, exit 0 |
| documents-world.txt | Published document arguments probe passed, exit 0; no browser |

No screenshots were produced tonight. Archived images reviewed in the audit were
not copied or relabelled as new before/after captures. No UI fixes, landing,
activation, resident verification or second round are represented by this folder.
