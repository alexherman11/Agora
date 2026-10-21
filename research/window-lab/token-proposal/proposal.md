## For Alex
What: Claude used its fresh five-hour allowance in about 1 hour 49 minutes.
Recommend: approve a small trial of shorter retrieval, reports and handoffs first.
Need: approve the trial or defer; automatic wake suppression and model changes stay separate.

## What happened

**Ran:** on 20 October, the CLI reported 0% used at 12:11 and 100% at 14:00, with reset at 17:10. The previous window was already exhausted by 11:07.

In the noon-to-limit interval, house receipts contain **763 distinct Claude assistant messages**. They report about **327 million cache-read tokens** across workers, JEFF and other residents. Those are repeated context reads, not newly written text. Observed contexts reached roughly 733,000–957,000 tokens.

**Inference:** substantial work repeatedly carrying large histories is a credible contributor. Caching was working; this is not evidence that it failed. The plan's weighting is opaque, so these receipts cannot tell us each person's quota share or promised savings.

## Recommended trial

- Retrieve changed sections and exact passages; keep a small current handoff with links to full evidence.
- Keep routine reports short. Print test summaries and failures; repeat broad checks only when changes or new failures justify them. Keep landing gates.
- Avoid courtesy acknowledgements that call workers back. Bundle nonurgent coordination; keep real blockers and Alex's instructions prompt.

**Expected benefit:** fewer repeated input bytes and unnecessary turns. Measure those counters over the next normal work period; compare completed work, missed instructions and rework too. No new benchmark spend.

**Risks:** shorter context can omit a dependency; terse reports can hide a failure. Keep full receipts retrievable, rules mandatory and important checks unchanged.

## Other options, separate approval

Smaller models for bounded extraction could conserve stronger-model work but need quality review. Reducing concurrency may stretch runway over clock time without saving total usage. Automatic wake coalescing needs safeguards against lost instructions. No provider queues or change to the four-worker cap.

## Your choice

**Build it** approves only the recommended trial for JEFF to commission. **Not yet, I have questions** defers it. Existing review controls record either choice; this proposal changes no runtime behaviour.
