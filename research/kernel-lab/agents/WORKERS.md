# Running a worker

Resident guide · 28 October 2026 · **Read:** checked against
[builders.py](../modules/house/builders.py) and [house.py](../modules/house/house.py),
plus live `help house.work` and `help say`.

You own the task and steer its worker. Give it a concrete outcome, boundaries,
and what evidence would satisfy you.

1. **Start the work.** For example:

   ```text
   house.work "Fix the dock unpin bug. Check that unpinning survives reopening the dock." with=codex
   ```

   Codex is the default; `with=claude` selects Claude. House makes a task card
   in Now with you as owner and lead, then asynchronously claims it and prepares
   an isolated branch, worktree and private chat named after the worker.
   Save the returned card reference. For an existing ready card, use
   `house.build <card>` instead. A launch receipt does not prove completion.
   If capacity is full, no new work is queued; read the receipt before retrying,
   since a card can have been made even when its worker did not start.

2. **Read its chat; steer with `house.tell`.** Use the card's `builder_chat`
   reference to find the conversation, and send instructions to the card:

   ```text
   look <card>
   house.tell <card> "Also check reopening after a restart; report exactly what you tested."
   ```

   Replace angle-bracket placeholders with the returned references. Each
   successful worker turn posts its final message there and wakes you there.
   **Observed by Sable, 28 October:** what is said in the worker chat does not
   reach the worker, so `house.tell` is the way to steer it. The source intends
   to forward requester-authored chat replies, but that is not verified live.
   `house.tell` retains a follow-up for the same task and model conversation;
   a busy worker reads it at a turn boundary. Check the receipt. Send concrete
   instructions, and stay quiet when you have none.

3. **Review the result.** Read its evidence and limitations first:

   ```text
   house.log <card>
   house.review <card>
   look <card>
   ```

   Wait for `build_phase=received` before requesting review. The worker must
   leave `BUILD-RESULT.md` describing files, checks, results and remaining work.
   House commits its edits to the worker branch, excluding that report and
   top-level dot-folders. It reconciles current main into that branch as needed,
   then runs independent kernel chat, painter-health and hidden desktop tests.
   Review is asynchronous: wait for `build_phase=reviewed`. Inspect
   `build_detail` and `house.log` if blocked. Review requested in the same turn
   drops pending instructions, so finish corrections first.

4. **Land, then verify the outcome.**

   ```text
   house.land <card>
   look <card>
   ```

   Only the requester can review or land. Landing publishes the exact reviewed
   candidate if main, the candidate and task authority still match. Wait for
   `build_phase=landed`; if main advanced, reconcile and review again.
   Landing leaves activation and owner outcome verification separate. Arrange
   safe activation, verify the requested behavior, then close the task and tell
   JEFF in Shop talk.

Use `house.who` for status. On a refusal or uncertain/recovery-needed state,
stop and report the friction; do not replay an unknown operation. Keep tests
hidden, and keep the worker within its one task and worktree.
