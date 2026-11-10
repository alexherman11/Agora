# Evidence and limits — Claude runway proposal

Local read-only analysis, 20 October 2026. All times Pacific (UTC−07:00).
No new model call, account/credential access, private-message inspection, host
action, configuration change or wake-policy change.

## Sources and completeness

**Read:** house.py `Resident.log` writes structured `at/kind/data` receipts under
the main checkout's `src/text-desk/notation/house-state/frontier`.
Only those receipts were scanned. Source files read: usage.py, plan_usage.py,
house.py, workshop.py, charter.py and the quota/compaction portions located in
codex_resident.py. No exported conversation log was grepped. The audit emits
numeric metadata, model/tool names and coarse actor classes; never text, tool
arguments, prompts or reasoning.

**Ran:** fixed day selection `[20 Oct 00:00, 20 Oct 16:52)` found 39 active
receipt folders. Earliest selected record was 10:43:42. This is not proof of no
earlier activity. The scan skipped 90 malformed JSON lines across all scanned
history; their dates/content are unknown. Files were read live to fixed time
cutoffs, not frozen together. Direct Claude Code/Codex app sessions outside the
house are not covered; their possible contribution to account quota is unknown.
Folder counts are not concurrent workers or unique people.

The more useful interval is `[12:11:26, 14:01:07)`: 25 active folders, bounded by
the reset reading and last exhausted reading. This is an observation interval,
not every request in the provider's five-hour accounting window.

## Plan observations

**Ran:** CLI `rate_limit_event.unifiedWindows`:

| Allowance reset | First observation | First 100% observation |
|---|---|---|
| 12:10 | 10:43:49, 32% | 11:07:03 |
| 17:10 | 12:11:26, 0% | 14:00:53 |

Second interval: 109 minutes 27 seconds between observed 0% and 100%.
Weekly use rose from 12% to 20% over those observations. These are reported
account values, not an attribution to the process that received the event.
Repeated limit events are not requests.

**Read live Usage surface during this audit:** Claude still showed 100%
five-hour / 20% weekly as of 14:01; Codex showed 40% for its reported seven-day
window as of 16:51. Neither is a token-to-quota conversion.

## Recorded Claude input, noon interval

**Ran:** per-message input counters; repeated assistant IDs within each actor
class are deduplicated using component maxima:

| Receipt owner | Unique assistant IDs | Cache reads | Cache creation | Largest observed input context |
|---|---:|---:|---:|---:|
| JEFF | 61 | 40,225,121 | 731,177 | 732,536 |
| Other residents | 14 | 8,434,200 | 2,585,572 | 956,962 |
| Workers/builders | 688 | 278,796,525 | 1,521,279 | 821,637 |

Total cache reads: 327,455,846. These represent repeated provider-reported input
work, not unique source text, new tokens, billed money or a quota percentage.
Assistant message IDs are not independently verified HTTP request IDs.
Subagent messages remain attributed to their owning worker receipt folder.
Missing-ID assistant events are excluded; no estimate is filled in.

**Ran:** cumulative result-counter positive differences separately sum to
25,165 output tokens for JEFF, 15,078 for other residents, 131,981 for workers.
Do not add result input deltas to the message table: they overlap. Result
counters accumulate over sessions; summing raw result snapshots would grossly
overcount. Two worker session/model series lacked initial baselines and four
numeric counter decreases were skipped in this interval. Interrupted turns
can lack a closing result. Nonmonotonic series, missing baselines and incomplete
turns prevent treating these diagnostic differences as a consumption total or
lower bound. Preliminary assistant output counters are not output totals.
No monetary value or hidden-reasoning text is used.

## Retries, wakes, rules, context and model choice

**Ran, whole selected day, mixed providers:** worker receipts have 97 start,
23 resume and 50 set-down records; JEFF has 10 starts and 6 restarts; other
residents have 41 starts and 35 restarts. These are lifecycle records, not
97 paid requests or proof of wasted work. Recorded compact-boundary events:
27 workers, 1 JEFF; recorded API-retry events: 3 workers, 1 JEFF.
Compaction counts include Codex; they cannot all be charged to Claude.

**Read:** current source prevents blindly redelivering an already delivered
pending turn into the same saved conversation. Worker card comments from
others and addressed calls can enter `Workshop.heard`; waiting workers with
new heard lines can be taken again. That permits unnecessary coordination
turns, but this audit does not classify message contents or prove how many
finished-card wakes were avoidable. No measured idle-spin rate is available.

**Read:** standing rules are mandatory; this task's startup receipt says 434
words. Current starts cache charter text for ordinary resumes; compaction
refreshes it. Do not weaken the rules to save tokens. No separate measured
quota cost exists for charter/protocol injection.

**Ran/read:** noon result receipts name Sonnet for JEFF and Opus for workers
and other residents. Whole-day worker receipts also include one Haiku result.
These names describe receipts, not current routing or relative plan weights.
Large cached contexts and frequent worker tool use support targeted retrieval
and short reusable handoffs; they do not establish that any source read was
unnecessary. Broad health repetition, verbose reports, stale-status loops and
courtesy wakes are review targets, not quantified causes from this audit.
No token total was computed for Codex's different cumulative usage stream.

## Proposed measurement after approval

**Imagined:** over ordinary work, record deduplicated usage deltas plus
work completed, retries, compactions and avoidable wakes. Prefer changed-section
retrieval, concise test summaries and durable short handoffs; retain exact
evidence and mandatory landing checks. Compare with similar work, not an
uncontrolled before/after quota slope. Do not promise a savings percentage.
Model tiering and automatic wake batching require separate approval and
quality/lost-instruction checks. Shared unordered pool and maximum four stay.

## Reproduction and checks

Run with the pinned interpreter from the assigned worktree:

```
src/desktop/token-proposal/audit.py C:/Projects/Agora4/src/text-desk/notation/house-state/frontier --out src/desktop/token-proposal/receipts-day.json
src/desktop/token-proposal/audit.py C:/Projects/Agora4/src/text-desk/notation/house-state/frontier --begin 2026-10-20T12:11:26-07:00 --end 2026-10-20T14:01:07-07:00 --out src/desktop/token-proposal/receipts-reset-window.json
src/desktop/token-proposal/test_audit.py
```

**Ran:** 2 synthetic audit tests, OK: cumulative-vs-snapshot counting, duplicate
message handling, missing baseline/reset handling, limit extraction and no
message-text emission. Initial fixture run hit Windows' epoch-local-time
conversion error; UTC-aware timestamp conversion fixed it, then both passed.
The two JSON artifacts contain aggregates only. No browser, visual review
control test or live model benchmark ran. Full health is unnecessary for these
unwired analysis artifacts; no runtime source was changed.
