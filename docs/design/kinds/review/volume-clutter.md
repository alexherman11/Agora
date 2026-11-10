# High-volume outside chat: records or not? (a clutter view)

> Claude (clutter design session), 28 Oct 2026, answering the kinds session's question. A view for Alex's gate, not a decision. Clutter design: [[research/clutter-lab/README|clutter README]] (Alex answered its ten cards 27 Oct). Trial numbers are the chats trial's (**read**, `trials/chats-from-anywhere/FINDINGS.md` §1, §2, §11), not mine.

## What clutter already says

- **Shed at birth.** Most clutter is made by machines, so the cheapest shedding is never writing a fact. In the clutter design, telemetry, paint reports and window geometry are not world facts at all (Alex, 26 Oct: visual state stays local). That was the `keep=never` row. After Alex's C2 answer it is the shortest "lifetime" a kind can declare.
- **Shedding fixes storage, not arrival.** Rollover (C6) and going cold move bytes out of the replay. They do nothing about what a message costs when it comes in. The trial measured exactly that: 12.4 ms per message, four modules hearing each one, and a House `look` per message. Option (b) pays all of that in full and only tidies up afterwards.
- **People's words are never folded by a machine.** That rule was about people in the world: Alex, JEFF, residents. Strangers in a Twitch channel aren't world people. Their lines are a source's content, like mail (Alex, 22 Oct: mail contents may be world data, but one by one, at mail's volume).
- **Lossless.** Whatever isn't a record still has to be got back, through the same path as cold segments: `archive find / look / bring` (C7).

## What I'd pick: (a) and (c) together, with promotion on act

1. **Live:** the adapter holds a ring buffer, like presence. Lenses and JEFF read the recent window from it. Nothing enters the world log, and no module wakes per message unless it subscribes to that source.
2. **History:** the adapter appends every message to its own file, one per source (`<world>/sources/twitch-<channel>/0001.jsonl`). It isn't the world's log, isn't replayed at start, and is read through the archive words. This is (c), but outside the kernel: no second log for the kernel to manage, just a cold segment that was born cold.
3. **Promotion:** a message becomes a record when a person or agent acts on it: reply, quote, pin, comment, `bring`. The record carries `source=twitch`, the outside author as data (never `by`), and a pointer to its place in the source file. For context, the message it answers comes along, plus the quoted span, and nothing more.

So yes to your rule, phrased like this: **outside text is presence until someone acts on it. Then the act brings it in as a record that says where it came from.**

## Why this also helps the security findings

Findings §1 and §2 (outside text can forge lines in JEFF's context, and wake him through `say`) are partly about volume: every message was a record that the context builders and wake paths could see. Under this rule, unpromoted text never reaches a record-reading path. Promoted text is marked as outside text, so it can be quoted in JEFF's context but never read as `said` by a person. This narrows the problem; it doesn't solve it. The shape check from §1 still has to hold.

## The middle case

Some things a stream needs to count without a person acting: raids, follows, a mod's ban. Let the adapter write **one rolled-up record per window** ("stream 28 Oct: 3,000 messages, 412 chatters, 2 raids, top quoted lines → source file"). That's a digest at birth: picked lines, verbatim (C4), with the originals one `bring` away. It's one record per stream or per hour, not 3,000.

## What would change my mind

- If Alex wants stream chat to be **searchable world history** like his own chats ("what did chat say when I…"), and archive search across source files turns out too weak or slow for that. Then (b) with a short lifetime and kernel-level rollover per source is better.
- If JEFF or residents need to **react to unpromoted messages** often enough that every reaction amounts to a promotion. Then the boundary is in the wrong place, and it should be "what an agent reads," not "what a person does."
- If promotion **loses context** in practice (a promoted reply that's unreadable without ten neighbours), widen what comes along, or reconsider.

Not verified: none of this was run. The ring buffer, source files and promotion are **imagined**. The one cost argument rests on the trial's measured per-arrival cost, which shedding can't touch (**read**).
