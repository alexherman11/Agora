# Model kernel gaps and Rough spots

Read from kernel.py, words.py and modules.py; no kernel or lens.js edits made.

* **Missing word capability: offer fair-use metadata.** `on_offer` stores may and
  undo but ignores once. Registration therefore uses steward `word-set` after
  publication. Module-side default is 60 daily attempts until that is done.
* **Missing fair-use reading for see calls.** Kernel once counts live do records;
  see calls have no records. Model reads its dictionary policy inside each call
  and persists daily attempt counts in its own module home. This counts failed
  and undone attempts honestly and prevents restart/undo from buying free GPU
  work. It currently supports `at most N per day per person`, matching the
  kernel's existing daily grammar. Hourly policies need a kernel enhancement;
  they are not claimed here.
* **Missing call-scoped do delegation.** Module answer lines may contain kernel
  acts only; a module cannot return `model.summarize` as a nested line, and verb
  notes cannot have dotted names. The small `model.preview` see word prepares
  the same quoted summary data, for the existing summarize adapter to admit in
  its own one undoable act. Only model performs inference. Preview has its own
  attempt policy and shares the canonical summarize quota. A true call-scoped
  do delegation word could remove this bridge.
* **Missing explicit rev in look rows.** Generic look and posts' look rows do not
  supply rev, and post look omits custom fields. Model first looks at the target,
  then reads rows of that visible kind and selects the target. It sends only the
  selected target and explicitly requested board-kind rows to Ollama.
* **Kernel ten-second call deadline.** One generation has a seven-second socket
  timeout and concurrency is refused politely, not queued. Board batches are
  atomic and have a 6.5-second start budget; slow/large batches can refuse after
  spending inference work. A deadline/cancellation field in SHAPE 11 would make
  module orchestration more precise. No long soak or cancellation guarantee is
  claimed.

Source edits supply the missing world capability **caller-scoped local model
inference**. The three applications, the rule, chip, settings and quotas are
world definitions. This local note is the Rough spots handoff to Claude; no live
Board/Rough spots card was written, as live changes belong to his review step.
